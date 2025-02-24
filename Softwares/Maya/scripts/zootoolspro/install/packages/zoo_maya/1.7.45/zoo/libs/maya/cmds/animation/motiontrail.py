"""Code for animation motion trails

Example:

.. code-block:: python

    from zoo.libs.maya.cmds.animation import motiontrail
    motiontrail.createMotionTrailsSel(nameAsObject=True, trailDrawMode=1, showFrames=False, showFrameMarkers=True,
                                      frameMarkerSize=2, frameMarkerColor=(0.0, 1.0, 1.0), keyframeSize=0.1,
                                      selectOriginal=True, replaceOld=True)


"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.mel as mel

from zoovendor import six
from zoo.core.util import classtypes

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import namehandling, filtertypes

KEY_DOTS_DEFAULT = True
VISIBILITY_DEFAULT = True
FRAME_CROSSES_DEFAULT = True
FRAME_SIZE_DEFAULT = False
PAST_FUTURE_DEFAULT = True
FRAME_NUMBERS_DEFAULT = False
LIMIT_BEFORE_AFTER_DEFAULT = False
FRAME_MARKER_COL_DEFAULT = (0.0, 1.0, 1.0)


def moTrailShapes(scene=True, selected=True):
    """If both flags are true then, return the selected motion trail shape nodes.
    If no nodes are found in the selection, then return all nodes in the scene.

    :param scene: Return all mo trails in the scene?
    :type scene: bool
    :param selected: Return selected mo trails?
    :type selected: bool
    :return: the motrail shape nodes found.
    :rtype: list(str)
    """
    if not selected and scene:
        return cmds.ls(type="motionTrailShape")
    elif not scene:  # not scene and not selected
        return list()
    # Else selected is True
    sel = cmds.ls(selection=True, long=True)
    if not sel:
        if scene:
            return cmds.ls(type="motionTrailShape")
        return list()
    moTrials = cmds.listRelatives(sel, type="motionTrailShape")
    if moTrials:
        return moTrials
    elif scene:
        return cmds.ls(type="motionTrailShape")
    return list()  # moTrails was None and scene == False


def toggleDisplaySetting(attr, valueOne=1, valueTwo=0, transform=False, scene=True, selected=True, message=True):
    """Toggles the display of motion trails from selection or if nothing selected then the whole scene.

    attrs can be:

        "visibility": bool (transform=True)
        "trailDrawMode": int (1-2)
        "showFrames": bool (numbers)
        "showFrameMarkers": bool (crosses)
        "frameMarkerSize": float (0.01 - 2.0)  (crosses size)
        "keyframeSize": float (0.01 - 2.0) (white dots)

    :param attr: A supported attribute name on the motion trail
    :type attr: str
    :param valueOne: The first (largest) value to set in the toggle
    :type valueOne: float, int, bool
    :param valueTwo: The second (smallest) value to set in the toggle
    :type valueTwo: float, int, bool
    :param scene: Affect all motion paths in the scene if none selected?
    :type scene: bool
    :param selected: Affect selected motion paths as a priority?
    :type selected: bool
    :param message: Report messages to the user?
    :type message: bool
    """
    mTShapes = moTrailShapes(scene=scene, selected=selected)
    if not mTShapes:
        if message:
            output.displayWarning("No motion tails found")
        return None

    # Motion trails found get current value ------------
    if transform:
        mTTransform = cmds.listRelatives(mTShapes[0], parent=True)[0]
        curValue = cmds.getAttr(".".join([mTTransform, attr]))
    else:
        curValue = cmds.getAttr(".".join([mTShapes[0], attr]))

    # Toggle values ----------------
    if valueOne == curValue:
        newValue = valueTwo
        newToggleState = False
    else:
        newValue = valueOne
        newToggleState = True

    # Set values ---------------
    for mTShape in mTShapes:
        if transform:
            mTTransform = cmds.listRelatives(mTShape, parent=True)[0]
            cmds.setAttr(".".join([mTTransform, attr]), newValue)
        else:
            cmds.setAttr(".".join([mTShape, attr]), newValue)
    return newToggleState


def deleteMotionTrails(scene=True, selected=False, message=True):
    """Deletes selected or all motion trails in the scene.

    :param scene: Delete all in the scene?
    :type scene: bool
    :param selected: Delete selected?  Priority
    :type selected: bool
    """
    mTShapes = moTrailShapes(scene=scene, selected=selected)
    if not mTShapes:
        output.displayWarning("No motion trails where found in the scene to delete.")
        return
    cmds.delete(cmds.listRelatives(mTShapes, parent=True))
    if message:
        output.displayInfo("Success: Motion trails deleted")


def selectMotionTrails(message=True):
    """Selects all motion trails in the scene.
    """
    mTShapes = moTrailShapes(scene=True, selected=False)
    if not mTShapes:
        output.displayWarning("No motion trails where found in the scene.")
        return
    cmds.select(cmds.listRelatives(mTShapes, parent=True), replace=True)
    if message:
        output.displayInfo("Success: Motion trails deleted")


def objectFromMoTrailShp(motionTrailShp):
    """Returns the object that the motionTrailShape is connected to.

    :param motionTrailShp: A motionTrailShp node
    :type motionTrailShp: str
    :return object: An object that the trail is connected to
    :rtype object: str
    """
    objList = cmds.listConnections('{}.transformToMove'.format(motionTrailShp), d=False, s=True)
    if objList:
        return objList[0]
    return ""


def moTrailFromMoTrailShp(motionTrailShp):
    """Returns the motionTrail node (not shape) from the motion trail shape node.

    :param motionTrailShp: A motionTrailShp node
    :type motionTrailShp: str
    :return: A motionTrail node (not the shape node)
    :rtype: str
    """
    nodeList = cmds.listConnections('{}.frames'.format(motionTrailShp), d=False, s=True)
    if nodeList:
        return nodeList[0]
    return ""


def rebuildMotionTrail(motionTrailShapes, nameAsObject=True, selectOriginal=True, replaceOld=True,
                       suffixNameFrames=False, message=True):
    """Rebuilds motion trails from motion trail shape node list.

    :param motionTrailShapes: A list of motion trail handle shape nodes
    :type motionTrailShapes: list(str)
    :param nameAsObject: Auto names the new trails based off the selection names eg "pCube1_mTrailHdl"
    :type nameAsObject: bool
    :param selectOriginal: Select the original objects after building? If False selects motion transforms instead.
    :type selectOriginal: bool
    :param replaceOld: Will delete any old motionTrails related to the current selection, so will rebuild and won't add.
    :type replaceOld: Bool
    :param suffixNameFrames: adds a suffix with keyframes in out. eg _1_to_120
    :type suffixNameFrames: Bool
    :param message: Report a message to the user?
    :type message: bool
    :return: matching lists... moTrailTransforms, moTrailHandleShapes, moTrailList, moTrailObjList
    :rtype: list(str), list(str), list(str), list(str)
    """
    objList = list()
    for shape in motionTrailShapes:
        obj = objectFromMoTrailShp(shape)
        objList.append(obj)

    # Get display values of the first motion trail ------------------------------
    firstTrail = motionTrailShapes[0]
    trailDrawMode = cmds.getAttr("{}.trailDrawMode".format(firstTrail))
    showFrames = cmds.getAttr("{}.showFrames".format(firstTrail))
    showFrameMarkers = cmds.getAttr("{}.showFrameMarkers".format(firstTrail))
    keyframeSize = cmds.getAttr("{}.keyframeSize".format(firstTrail))
    frameMarkerColor = cmds.getAttr("{}.frameMarkerColor".format(firstTrail))[0]
    frameMarkerSize = cmds.getAttr("{}.frameMarkerSize".format(firstTrail))
    postFrame = cmds.getAttr("{}.postFrame".format(firstTrail))
    fadeInoutFrames = cmds.getAttr("{}.fadeInoutFrames".format(firstTrail))

    # Maya bad stuff returning floats as ints that error when you try to set with identical values.
    if keyframeSize == 0:
        keyframeSize = 0.1
    if frameMarkerSize == 0:
        frameMarkerSize = 0.1
    # Rebuild node -------------------
    moTrailTransforms, \
    moTrailHandleShapes, \
    moTrailList, \
    moTrailObjList = createMotionTrails(objList,
                                        nameAsObject=nameAsObject,
                                        trailDrawMode=trailDrawMode,
                                        showFrames=showFrames,
                                        showFrameMarkers=showFrameMarkers,
                                        frameMarkerSize=frameMarkerSize,
                                        frameMarkerColor=frameMarkerColor,
                                        keyframeSize=keyframeSize,
                                        selectOriginal=selectOriginal,
                                        replaceOld=replaceOld,
                                        suffixNameFrames=suffixNameFrames,
                                        limitFrames=postFrame)
    if message:
        output.displayInfo("Success: Motion Trails rebuilt for "
                           "objects: {}".format(namehandling.getShortNameList(moTrailObjList)))
    return moTrailTransforms, moTrailHandleShapes, moTrailList, moTrailObjList


def createMotionTrails(objs, nameAsObject=True, trailDrawMode=2, showFrames=False, showFrameMarkers=True,
                       frameMarkerSize=1.0, frameMarkerColor=(0.0, 1.0, 1.0), keyframeSize=1.0, selectOriginal=True,
                       replaceOld=True, suffixNameFrames=False, limitFrames=0.0):
    """Creates a motion trails from and object list and changes the display modes to suit.

    Default will create a moton trail with a new name matching the object.

        pCube1_mTrailHdl

    :param objs: A list of Maya objects
    :type objs: list(str)
    :param nameAsObject: Auto names the new trails based off the selection names eg "pCube1_mTrailHdl"
    :type nameAsObject: bool
    :param trailDrawMode: 0, constant, 1 alternating frames, 2 past future
    :type trailDrawMode: int
    :param showFrames: Show frame numbers?
    :type showFrames: bool
    :param showFrameMarkers: Show Frame Markers (crosses like handles)
    :type showFrameMarkers: bool
    :param frameMarkerSize: Size of the Markers (crosses)
    :type frameMarkerSize: float
    :param frameMarkerColor: Color of the Markers (crosses)
    :type frameMarkerColor: list(float)
    :param keyframeSize: Size of the white dots, less than 0.5 will be invisible.
    :type keyframeSize: float
    :param selectOriginal: Select the original objects after building? If False selects motion transforms instead.
    :type selectOriginal: bool
    :param replaceOld: Will delete any old motionTrails related to the current selection, so will rebuild and won't add.
    :type replaceOld: Bool
    :param suffixNameFrames: adds a suffix with keyframes in out. eg _1_to_120
    :type suffixNameFrames: Bool
    :param limitFrames: The amount of frames to limit either side, if 0.0 then there is no limit.
    :type limitFrames: int
    :return: matching lists... moTrailTransforms, moTrailHandleShapes, moTrailList, moTrailObjList
    :rtype: list(str), list(str), list(str), list(str)
    """
    oldMoTrailsDict = dict()
    moTrailTransforms = list()
    moTrailList = list()
    moTrailObjList = list()

    cmds.select(objs, replace=True)

    # List all existing motiontrails in the scene -----------------
    oldMoTrailShapes = cmds.ls(type="motionTrailShape")

    # Build object old motrail dict if potentially replacing old motion trails ----------
    if oldMoTrailShapes and replaceOld:
        for moTrailShape in oldMoTrailShapes:
            obj = objectFromMoTrailShp(moTrailShape)
            if obj:
                oldMoTrailsDict[obj] = moTrailShape

    # Build the trail mel doesn't return new trails? (sigh) -------------
    mel.eval('CreateMotionTrail;')  # Build the trail

    # Get the new motion trail shapes ---------------
    updatedTrailShapes = cmds.ls(type="motionTrailShape")
    moTrailHandleShapes = list(set(updatedTrailShapes).difference(oldMoTrailShapes))  # Take second list from first

    if not moTrailHandleShapes:  # No new shapes so return
        om2.MGlobal.displayWarning("Motion Trail not created")
        return list(), list(), list(), list()

    # Change display settings of trails, and find the transform and motrail nodes -------------------
    for i, motionTrailShp in enumerate(moTrailHandleShapes):  # Change to alternating display type
        cmds.setAttr("{}.trailDrawMode".format(motionTrailShp), trailDrawMode)
        cmds.setAttr("{}.showFrames".format(motionTrailShp), showFrames)
        cmds.setAttr("{}.showFrameMarkers".format(motionTrailShp), showFrameMarkers)
        cmds.setAttr("{}.keyframeSize".format(motionTrailShp), keyframeSize)
        cmds.setAttr("{}.frameMarkerSize".format(motionTrailShp), frameMarkerSize)
        cmds.setAttr("{}.frameMarkerColor".format(motionTrailShp),
                     frameMarkerColor[0],
                     frameMarkerColor[1],
                     frameMarkerColor[2],
                     type="double3")
        cmds.setAttr("{}.preFrame".format(motionTrailShp), limitFrames)
        cmds.setAttr("{}.postFrame".format(motionTrailShp), limitFrames)
        cmds.setAttr("{}.fadeInoutFrames".format(motionTrailShp), limitFrames)

        moTrailObjList.append(objectFromMoTrailShp(motionTrailShp))  # related object
        moTrailList.append(moTrailFromMoTrailShp(motionTrailShp))  # motrail node (not shape)
        moTrailTransforms.append(cmds.listRelatives(motionTrailShp, parent=True)[0])  # append transform, must exist

    # Delete the motion trail if match oldMoTrailsDict & objList -------------
    if replaceOld and oldMoTrailsDict and moTrailObjList:
        for obj in moTrailObjList:
            if obj:
                if obj in oldMoTrailsDict:
                    cmds.delete(cmds.listRelatives(oldMoTrailsDict[obj], parent=True))  # Match so delete

    # Auto rename -------------------------------------------
    if nameAsObject:
        for i, moTransform in enumerate(moTrailTransforms):
            obj = moTrailObjList[i]
            moTrailNode = moTrailList[i]
            suffix = ""
            if suffixNameFrames:
                startFrm = cmds.getAttr("{}.startTime".format(moTrailNode))
                endFrm = cmds.getAttr("{}.endTime".format(moTrailNode))
                suffix = "_{}_to_{}".format(str(int(startFrm)), str(int(endFrm)))
            if obj:
                if replaceOld:
                    pass
                shortObj = namehandling.getShortName(obj)
                motionTrail = cmds.rename(moTransform, "_mTrailHdl".join([shortObj, suffix]))
                moTrailTransforms[i] = motionTrail
                moTrailHandleShapes[i] = cmds.listRelatives(motionTrail, shapes=True, type="motionTrailShape")[0]
                moTrailNode = cmds.rename(moTrailNode, "_moTrail_".join([shortObj, suffix]))
                moTrailList[i] = moTrailNode

    # Select after building --------------------
    if selectOriginal:
        cmds.select(objs, replace=True)
    else:
        cmds.select(moTrailTransforms, replace=True)

    return moTrailTransforms, moTrailHandleShapes, moTrailList, moTrailObjList


def createMotionTrailsSel(nameAsObject=True, trailDrawMode=2, showFrames=False, showFrameMarkers=True,
                          frameMarkerSize=0.1, frameMarkerColor=(0.0, 1.0, 1.0), keyframeSize=1.0, selectOriginal=True,
                          replaceOld=True, suffixNameFrames=False, noSelRebuild=True, limitFrames=0.0,
                          message=True):
    """Creates a motion trail on the selected object and changes the display modes to suit.

    default will create a motion trail with a new name matching the object.

        pCube1_mTrailHdl

    :param nameAsObject: Auto names the new trails based off the selection names eg "pCube1_mTrailHdl_1_to_250"
    :type nameAsObject: bool
    :param trailDrawMode: 0, constant, 1 alternating frames, 2 past future
    :type trailDrawMode: int
    :param showFrames: Show frame numbers?
    :type showFrames: bool
    :param showFrameMarkers: Show Frame Markers (crosses like handles)
    :type showFrameMarkers: bool
    :param frameMarkerSize: Size of the Markers (crosses)
    :type frameMarkerSize: float
    :param frameMarkerColor: Color of the Markers (crosses)
    :type frameMarkerColor: list(float)
    :param keyframeSize: Size of the white dots, less than 0.5 will be invisible.
    :type keyframeSize: float
    :param selectOriginal: Select the original objects after building? If False selects motion transforms instead.
    :type selectOriginal: bool
    :param replaceOld: Will delete any old motionTrails related to the current selection, so will rebuild and won't add.
    :type replaceOld: Bool
    :param suffixNameFrames: adds a suffix with keyframes in out. eg _1_to_120
    :type suffixNameFrames: Bool
    :param noSelRebuild: If True and nothing is selected then try to rebuild all motion trails in the scene
    :type noSelRebuild: Bool
    :param limitFrames: The amount of frames to limit either side, if 0.0 then there is no limit.
    :type limitFrames: int
    :return: matching lists... moTrailTransforms, moTrailHandleShapes, moTrailList, moTrailObjList
    :rtype: list(str), list(str), list(str), list(str)
    """
    originalSel = cmds.ls(selection=True, long=True)
    if not originalSel:
        if not noSelRebuild:  # Then report warning.
            if message:
                om2.MGlobal.displayWarning("Please select an object to create a motion trail.")
            return list(), list(), list(), list()
        # noSelRebuild is True so try to rebuild the entire scene.
        allMoTShapes = cmds.ls(type="motionTrailShape")
        if not allMoTShapes:
            if message:
                om2.MGlobal.displayWarning("No motion trail shapes selected or in the scene to rebuild.")
            return list(), list(), list(), list()
        moTrailTransforms, \
        moTrailHandleShapes, \
        moTrailList, \
        moTrailObjList = rebuildMotionTrail(allMoTShapes,
                                            nameAsObject=nameAsObject,
                                            selectOriginal=selectOriginal,
                                            replaceOld=replaceOld,
                                            suffixNameFrames=suffixNameFrames,
                                            message=message)
        return moTrailTransforms, moTrailHandleShapes, moTrailList, moTrailObjList
    # There are selected nodes try to build --------------------
    moTrailTransforms, \
    moTrailHandleShapes, \
    moTrailList, \
    moTrailObjList = createMotionTrails(originalSel,
                                        nameAsObject=nameAsObject,
                                        trailDrawMode=trailDrawMode,
                                        showFrames=showFrames,
                                        showFrameMarkers=showFrameMarkers,
                                        frameMarkerSize=frameMarkerSize,
                                        frameMarkerColor=frameMarkerColor,
                                        keyframeSize=keyframeSize,
                                        selectOriginal=selectOriginal,
                                        replaceOld=replaceOld,
                                        suffixNameFrames=suffixNameFrames,
                                        limitFrames=limitFrames)

    if replaceOld:
        motionShapes = filtertypes.filterTypeReturnShapes(originalSel, children=False, shapeType="motionTrailShape")
        if motionShapes:
            newTransforms, \
            newHandleShapes, \
            newList, \
            newObjList = rebuildMotionTrail(motionShapes,
                                            nameAsObject=nameAsObject,
                                            selectOriginal=selectOriginal,
                                            replaceOld=replaceOld,
                                            suffixNameFrames=suffixNameFrames,
                                            message=message)
            moTrailTransforms += newTransforms
            moTrailHandleShapes += newHandleShapes
            moTrailList += newList
            moTrailObjList += newObjList
            if selectOriginal:  # For later selection
                moTrailTransforms = namehandling.getLongNameList(moTrailTransforms)  # long names for list removal
                originalSel = [x for x in originalSel if x not in moTrailTransforms]  # take away moTrailTransforms
                originalSel += moTrailTransforms

    if selectOriginal:
        cmds.select(originalSel, replace=True)
    else:
        cmds.select(moTrailTransforms, replace=True)

    if message:
        output.displayInfo("Success: Motion Trails built or "
                           "rebuilt: {}".format(namehandling.getShortNameList(moTrailTransforms)))

    return moTrailTransforms, moTrailHandleShapes, moTrailList, moTrailObjList


def createMotionTrailSelBools(keyDots_bool, crosses_bool, frameSize_bool, pastFuture_bool,
                              frameNumbers_bool, limitBeforeAfter_bool, limitFrames=8.0):
    """Main function for creating and rebuilding motion trails from UI or marking menu.

    Takes boolean (checkbox) values as its keyword arguments.

    :param keyDots_bool: Keyframe dots visibility
    :type keyDots_bool: bool
    :param crosses_bool: Every frame cross visibility
    :type crosses_bool: bool
    :param frameSize_bool: Small or Large size of the key and keyframe markers?
    :type frameSize_bool: bool
    :param pastFuture_bool: Set alternating display style or past/future
    :type pastFuture_bool: bool
    :param frameNumbers_bool: Visibility of the frame numbers display
    :type frameNumbers_bool: bool
    :param limitBeforeAfter_bool: limit the frame length before and after.
    :type limitBeforeAfter_bool: bool
    :param limitFrames: The amount of frames that will be limited.
    :type limitFrames: float
    :return: matching lists... moTrailTransforms, moTrailHandleShapes, moTrailList, moTrailObjList
    :rtype: list(str), list(str), list(str), list(str)
    """
    if keyDots_bool:
        keyframeSize = 3.0 if frameSize_bool else 1.0
    else:
        keyframeSize = 0.1
    return createMotionTrailsSel(nameAsObject=True,
                                 trailDrawMode=2 if pastFuture_bool else 1,
                                 showFrames=frameNumbers_bool,
                                 showFrameMarkers=crosses_bool,
                                 frameMarkerSize=3.0 if frameSize_bool else 0.1,
                                 frameMarkerColor=(0.0, 1.0, 1.0),
                                 keyframeSize=keyframeSize,
                                 selectOriginal=True,
                                 replaceOld=True,
                                 suffixNameFrames=False,
                                 noSelRebuild=True,
                                 limitFrames=limitFrames if limitBeforeAfter_bool else 0,
                                 message=True)


# ---------------------------
# RESET DISPLAY DEFAULTS
# ---------------------------


def resetMoTrialDefaultDisplay(scene=True, selected=True, message=True):
    """Resets the display settings of the selected or scene moTrail shape nodes in the scene

    :param scene: Return all mo trails in the scene?
    :type scene: bool
    :param selected: Return selected mo trails?
    :type selected: bool
    :return: the motrail shape nodes found.
    :rtype: list(str)
    """
    # Change display settings of trails, and find the transform and motrail nodes -------------------
    moTrailHandleShapes = moTrailShapes(scene=scene, selected=selected)
    for i, motionTrailShp in enumerate(moTrailHandleShapes):  # Change to alternating display type
        cmds.setAttr("{}.trailDrawMode".format(motionTrailShp), 2)
        cmds.setAttr("{}.showFrames".format(motionTrailShp), False)
        cmds.setAttr("{}.showFrameMarkers".format(motionTrailShp), True)
        cmds.setAttr("{}.keyframeSize".format(motionTrailShp), 1.0)
        cmds.setAttr("{}.frameMarkerSize".format(motionTrailShp), 0.1)
        cmds.setAttr("{}.frameMarkerColor".format(motionTrailShp), 0.0, 1.0, 1.0, type="double3")
        cmds.setAttr("{}.preFrame".format(motionTrailShp), 0)
        cmds.setAttr("{}.postFrame".format(motionTrailShp), 0)
        cmds.setAttr("{}.fadeInoutFrames".format(motionTrailShp), 0)
    if message:
        output.displayInfo("Success: Motion trail display settings reset.")
    return moTrailHandleShapes


# ---------------------------
# MOTION TRAIL - RETURN BOOLEAN DISPLAY STATES - UI & MARKING MENU
# ---------------------------


def createKeyframeTrackAttrs(mTShape):
    """On a single motion trail create the zoo tracker attributes for keyframe dot scale and visibility

    :param mTShape: A single motiontrail shape node.
    :type mTShape: str
    :return: Trackers were created.
    :rtype: bool
    """
    if cmds.attributeQuery("zooKeyframeSize", node=mTShape, exists=True):
        return False
    # Attributes don't exist so create and return defaults. ----------------------
    cmds.addAttr(mTShape, longName="zooKeyframeSize", attributeType='float')
    cmds.addAttr(mTShape, longName="zooKeyframeVis", attributeType='bool')
    val = cmds.getAttr("{}.keyframeSize".format(mTShape))
    if val < 0.5:
        size = 1.0
        vis = False
    elif val < 1.5:
        size = 1.0
        vis = True
    else:
        size = 3.0
        vis = True
    cmds.setAttr("{}.zooKeyframeSize".format(mTShape), size)
    cmds.setAttr("{}.zooKeyframeVis".format(mTShape), vis)
    return True


def keyframeTrackAttrs(mTShape):
    """On a single motion trail return the zoo tracker attributes for keyframe dot scale and visibility.

    :param mTShape: A single motiontrail shape node.
    :type mTShape: str
    :return: Returns the size and visibility of the keyframe dots attribute.
    :rtype: tuple(float, bool)
    """
    createKeyframeTrackAttrs(mTShape)
    size = cmds.getAttr("{}.zooKeyframeSize".format(mTShape))
    vis = cmds.getAttr("{}.zooKeyframeVis".format(mTShape))
    return size, vis


def keyDotsVisibility(moTShapes):
    """Returns the first found motion trail shape's keyframe dots visibility

    :param moTShapes: A list of motiontrail shape nodes.
    :type moTShapes: list(str)
    :return: Are the key dots visible or not?
    :rtype: bool
    """
    if not moTShapes:
        return KEY_DOTS_DEFAULT
    return keyframeTrackAttrs(moTShapes[0])[1]


def keyDotsSize(moTShapes):
    """Returns the first found motion trail shape's keyframe dots size, ignores visibility

    :param moTShapes: A list of motiontrail shape nodes.
    :type moTShapes: list(str)
    :return: The size of the key dots ignoring visibility, so ignoring the 0.1 values.
    :rtype: float
    """
    return keyframeTrackAttrs(moTShapes[0])[0]


def setKeyDotsVis(moTShapes, visible):
    """Sets the visibility of the key frame dots, annoying function that also takes into consideration the zoo scale \
    toggle small/large.

    The keyframeSize attribute doubles as visiblity (0.1) and scale larger sizes.  So its difficult for UI toggles.
    Zoo creates trackable attributes for monitoring keyframe dot scale and size independently.

    :param moTShapes: A list of motion trail handle shape nodes
    :type moTShapes: list(str)
    :param visible: keyframes dots are visible or invisible?
    :type visible: bool
    """
    if not moTShapes:
        return
    for mTShape in moTShapes:
        createKeyframeTrackAttrs(mTShape)  # creates attrs if they don't exist
        cmds.setAttr("{}.zooKeyframeVis".format(mTShape), visible)  # set the zoo tracker is attr
        if not visible:
            size = 0.1  # invisible
        else:
            size = cmds.getAttr("{}.zooKeyframeSize".format(mTShape))
        cmds.setAttr("{}.keyframeSize".format(mTShape), size)


def setKeyDotsSize(moTShapes, sizeBool):
    """Sets the scale of the keyframe dots, annoying function that also takes into consideration the zoo visibility \
    toggle on/off.

    The keyframeSize attribute doubles as visiblity (0.1) and scale larger sizes.  So its difficult for UI toggles.
    Zoo creates trackable attributes for monitoring keyframe dot scale and size independently.

    :param moTShapes: A list of motion trail handle shape nodes
    :type moTShapes: list(str)
    :param sizeBool: The keyframe dots are large if True and False if not.
    :type sizeBool: bool
    """
    if not moTShapes:
        return
    if sizeBool:
        size = 3.0
    else:
        size = 1.0
    for mTShape in moTShapes:
        createKeyframeTrackAttrs(mTShape)  # creates attrs if they don't exist
        cmds.setAttr("{}.zooKeyframeSize".format(mTShape), size)  # set the zoo tracker is attr
        vis = cmds.getAttr("{}.zooKeyframeVis".format(mTShape))
        if not vis:
            size = 0.1  # invisible
        cmds.setAttr("{}.keyframeSize".format(mTShape), size)  # large


def setVisibilityBool(moTShapes, visibility):
    """Sets the motion trail shapes

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :param visibility: show or hide the visibility of the motion trail transforms
    :type visibility: bool
    """
    for shape in moTShapes:
        cmds.setAttr("{}.visibility".format(cmds.listRelatives(shape, parent=True)[0]), visibility)


def setFrameCrossesBool(moTShapes, visibility):
    """Sets the motion trail shapes frame cross visibility.

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :param visibility: frame cross visibility on or off?
    :type visibility: bool
    """
    for shape in moTShapes:
        cmds.setAttr("{}.showFrameMarkers".format(shape), visibility)


def setFrameSizeBool(moTShapes, sizeBool):
    """Sets the motion trail shapes frame cross and keyframe dot size.

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :param visibility: frame cross and keyframe dot scale small or large
    :type visibility: bool
    """
    if sizeBool:
        val = 3.0
    else:
        val = 0.1
    for shape in moTShapes:
        cmds.setAttr("{}.frameMarkerSize".format(shape), val)
    setKeyDotsSize(moTShapes, sizeBool)


def setPastFutureBool(moTShapes, altPastBool):
    """Sets the motion trail shapes display type to be either alternating (False) or past future (True).

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :param altPastBool: display type to be either alternating (False) or past future (True)
    :type altPastBool: bool
    """
    if altPastBool:
        val = 2
    else:
        val = 1
    for shape in moTShapes:
        cmds.setAttr("{}.trailDrawMode".format(shape), val)


def setFrameNumbersBool(moTShapes, frameNumberVis):
    """Sets the motion trail shapes

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :param frameNumberVis:
    :type frameNumberVis:
    """
    for shape in moTShapes:
        cmds.setAttr("{}.showFrames".format(shape), frameNumberVis)


def setLimitBeforeAfterBool(moTShapes, limitBool, framesIn=8.0, framesOut=8.0):
    """Sets the motion trail shapes frame limit to be on or off.

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :param limitBool: Set the limit to be on or off (no limit)
    :type limitBool: bool
    :param framesIn: Set the pre frame number length
    :type framesIn: float
    :param framesOut: Set the post frame number length
    :type framesOut: float
    """
    valFade = 0
    if limitBool:
        valIn = framesIn
        valOut = framesOut
        if framesIn > 2.0:
            valFade = framesIn - 2.0
        if framesIn > 10.0:
            valFade = 8.0
    else:
        valIn = 0.0
        valOut = 0.0
        valFade = 0.0

    for shape in moTShapes:
        cmds.setAttr("{}.fadeInoutFrames".format(shape), valFade)
        cmds.setAttr("{}.preFrame".format(shape), valIn)
        cmds.setAttr("{}.postFrame".format(shape), valOut)


# ---------------------------
# MOTION PATH TOGGLES
# ---------------------------


def visibilityToggleValue(moTShapes):
    """Returns from the first found node, is the motion trail transform visible or not?

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :return: Is the motion trail transform visible or not.
    :rtype: bool
    """
    if not moTShapes:
        return VISIBILITY_DEFAULT
    transform = cmds.listRelatives(moTShapes[0], parent=True)[0]
    return cmds.getAttr("{}.visibility".format(transform))


def frameCrossesToggleValue(moTShapes):
    """Returns from the first found node, whether the frame crosses are visible or not.

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :return: Are the frame crosses visible or not?
    :rtype: bool
    """
    if not moTShapes:
        return FRAME_CROSSES_DEFAULT
    return cmds.getAttr("{}.showFrameMarkers".format(moTShapes[0]))


def frameSizeToggleValue(moTShapes):
    """Returns from the first found node, the size of the keyframe and key display size, big or small.

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :return: Are the key and keyframe display sizes big or small?
    :rtype: bool
    """
    if not moTShapes:
        return FRAME_SIZE_DEFAULT
    val = cmds.getAttr("{}.frameMarkerSize".format(moTShapes[0]))
    if val == 3.0:
        return True
    return False


def pastFutureToggleValue(moTShapes):
    """Returns from the first found node,

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :return:
    :rtype: bool
    """
    if not moTShapes:
        return PAST_FUTURE_DEFAULT
    val = cmds.getAttr("{}.trailDrawMode".format(moTShapes[0]))
    if val == 2:
        return True
    return False


def frameNumbersToggleValue(moTShapes):
    """Returns from the first found node, whether the frame numbers are visible or not.

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :return: Are the frame numbers visible or not?
    :rtype: bool
    """
    if not moTShapes:
        return FRAME_NUMBERS_DEFAULT
    return cmds.getAttr("{}.showFrames".format(moTShapes[0]))


def limitBeforeAfterToggleValue(moTShapes):
    """Returns from the first found node, whether the trail is limited in time.

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :return: Is the motion path limited in terms of time or not.
    :rtype: bool
    """
    if not moTShapes:
        return LIMIT_BEFORE_AFTER_DEFAULT
    val = cmds.getAttr("{}.fadeInoutFrames".format(moTShapes[0]))
    if val:
        return True
    return False


def keyFrameDotValue(moTShapes):
    """Returns from the first found node, whether the keyframe dots are visible or not.

    :param moTShapes: A list of motion trail shape nodes.
    :type moTShapes: list(str)
    :return: Are the key frame dots visible?
    :rtype: bool
    """
    if not moTShapes:
        return FRAME_SIZE_DEFAULT
    return cmds.getAttr("{}.keyframeSize".format(moTShapes[0]))


# ---------------------------
# MOTION PATH TRACK DATA ACROSS MULTIPLE UIS AND MARKING MENUS
# ---------------------------


@six.add_metaclass(classtypes.Singleton)
class ZooMotionTrailTrackerSingleton(object):
    """Used by the motion trail marking menu & UI, tracks data for motion trails between UIs and marking menus.

    Tracks the current motion trail shapes in the scene or selected.
    Tracks visibility settings of the motion trails.

    """

    def __init__(self):
        # Marking Menu ----------------
        self.markingMenuTriggered = False
        self.markingMenuMoShapes = None  # will be a list when used, must be None for init
        self.limitAmount = 8.0
        # Set default look of the trails from the scene or default values --------------
        moTShapes = moTrailShapes()
        if not moTShapes:
            # Default Marking Menu UI Toggles
            self.resetDisplayDefaults()
        else:
            self.keyDots_bool = keyDotsVisibility(moTShapes)
            self.crosses_bool = frameCrossesToggleValue(moTShapes)
            self.frameSize_bool = frameSizeToggleValue(moTShapes)
            self.pastFuture_bool = pastFutureToggleValue(moTShapes)
            self.frameNumbers_bool = frameNumbersToggleValue(moTShapes)
            self.limitBeforeAfter_bool = limitBeforeAfterToggleValue(moTShapes)

    def resetDisplayDefaults(self):
        """Resets all the display defaults."""
        self.keyDots_bool = KEY_DOTS_DEFAULT
        self.crosses_bool = FRAME_CROSSES_DEFAULT
        self.frameSize_bool = FRAME_SIZE_DEFAULT
        self.pastFuture_bool = PAST_FUTURE_DEFAULT
        self.frameNumbers_bool = FRAME_NUMBERS_DEFAULT
        self.limitBeforeAfter_bool = LIMIT_BEFORE_AFTER_DEFAULT
        self.limitAmount = 8.0


# ---------------------------
# CLONE OBJECTS FROM ANIMATION
# ---------------------------


def cloneObjFromAnimation(obj, startTime, endTime, objToFrame=1.0):
    """Creates objects from animation with snapshot, clones new objects.

    :param obj: A single object name, should be keys on translation
    :type obj: str
    :param startTime: The time start point to start creeating the curve
    :type startTime: float
    :param endTime: The time end point to end creating the curve
    :type endTime: float
    :param objToFrame: The amount of objects to frames, 1.0 is one obj per frame, 2.0 is one obj every 2 frames
    :type objToFrame: float
    """
    # snapNode is a snapshot node used to automatically duplicate the objects along the timeline
    snapNode = cmds.snapshot(obj, n="{}_snap".format(obj),
                             increment=objToFrame,
                             startTime=startTime,
                             endTime=endTime,
                             update='animCurve')[0]  # create snap node for geo trail
    # Rename objects -------------------------
    objList = cmds.listRelatives(snapNode, children=True)
    namehandling.renumberListSingleName(obj, objList, padding=2, renameShape=True, message=False)
    return snapNode, objList


def cloneObjsFromAnimation(objs, startTime, endTime, objToFrame=1):
    """Creates objects from animation with snapshot, clones new objects.

    :param objs: A list of objects (transforms) to create the CV curve.
    :type objs: list(str)
    :param startTime: The time start point to start creeating the curve
    :type startTime: float
    :param endTime: The time end point to end creating the curve
    :type endTime: float
    :param objToFrame: The amount of objects to frames, 1.0 is one obj per frame, 2.0 is one obj every 2 frames
    :type objToFrame: float
    """
    for obj in objs:
        cloneObjFromAnimation(obj, startTime, endTime, objToFrame=objToFrame)


def cloneObjsFromAnimationSelected(objToFrame=1):
    """Creates objects from animation with snapshot, clones new objects.

    :param objToFrame: The amount of objects to frames, 1.0 is one obj per frame, 2.0 is one obj every 2 frames
    :type objToFrame: float
    """
    selObjs = cmds.ls(sl=True, type='transform')
    if not selObjs:
        output.displayInfo("Nothing Selected, please select an animated object")
        return
    startTime = cmds.playbackOptions(query=True, min=True)
    endTime = cmds.playbackOptions(query=True, max=True)
    cloneObjsFromAnimation(selObjs, startTime, endTime, objToFrame=objToFrame)


# ---------------------------
# CV CURVE FROM OBJ
# ---------------------------


def cvCurveFromObjAnimation(obj, startTime, endTime, cvEveryFrame=1.0):
    """Creates a CV curve based on an animated object with keys per frame.

    Credit DELANO ATHIAS, cleaned up/faster code from:
        https://www.delanimation.com/tutorials-1/2020/1/2/generating-curves-from-motion-trails-in-maya

    :param obj: A single object name, should be keys on translation
    :type obj: str
    :param startTime: The time start point to start creeating the curve
    :type startTime: float
    :param endTime: The time end point to end creating the curve
    :type endTime: float
    :param cvEveryFrame: The amount of cvs per frame, 1.0 is one cv per frame, 2.0 is one CV every 2 frames
    :type cvEveryFrame: float
    """
    plane = cmds.polyPlane()[0]  # Plane geo needed for snapshot trail
    cmds.pointConstraint(obj, plane)
    cmds.select(plane, replace=True)  # Cube needs to be selected for the trail
    # snapNode is a snapshot node used to automatically duplicate the curves along the curve
    snapNode = cmds.snapshot(n="{}_snap".format(obj),
                             increment=cvEveryFrame,
                             startTime=startTime,
                             endTime=endTime,
                             update='animCurve')[0]  # create snap node for geo trail
    planeList = cmds.listRelatives(snapNode, children=True)
    cvCount = len(planeList) - 1
    # Create Curve -----------------------------------------------
    cvCurve = cmds.curve(degree=1, point=[(0, 0, 0), (0, 0, 1)])
    cvCurve = cmds.rebuildCurve(cvCurve,
                                constructionHistory=False,
                                rpo=True,
                                rebuildType=0,
                                endKnots=0,
                                spans=cvCount,
                                degree=1)  # Rebuild the curve with correct spans
    # Store cvs in a list ----------------------
    cmds.select(('{}.cv[0:*]'.format(cvCurve[0])), replace=True)
    cvs = cmds.ls(selection=True, flatten=True)
    # Match curve cvs to cubes ---------------------------
    for i, planeGeo in enumerate(planeList):
        wSpace = cmds.objectCenter(planeGeo, gl=True)  # Finds the center of the planeGeo in global space
        cmds.move(wSpace[0], wSpace[1], wSpace[2], cvs[i], worldSpace=True)
    # Cleanup ---------------------------------------------
    cmds.delete(cvCurve, constructionHistory=True)
    cmds.delete(plane, snapNode)
    # Make the curve smooth - 3 degrees -----------------------------
    cmds.rebuildCurve(cvCurve,
                      constructionHistory=False,
                      replaceOriginal=True,
                      rebuildType=0,
                      endKnots=0,
                      keepControlPoints=True,
                      keepEndPoints=True,
                      degree=3)


def cvCurveFromObjsAnimation(objs, startTime, endTime, cvEveryFrame=1):
    """Creates a CV curve based on an animated object with keys per frame.

    Credit DELANO ATHIAS, cleaned up code from
    https://www.delanimation.com/tutorials-1/2020/1/2/generating-curves-from-motion-trails-in-maya

    :param objs: A list of objects (transforms) to create the CV curve.
    :type objs: list(str)
    :param startTime: The time start point to start creeating the curve
    :type startTime: float
    :param endTime: The time end point to end creating the curve
    :type endTime: float
    :param cvEveryFrame: The amount of cvs per frame, 1.0 is one cv per frame, 2.0 is one CV every 2 frames
    :type cvEveryFrame: float
    """
    for obj in objs:
        cvCurveFromObjAnimation(obj, startTime, endTime, cvEveryFrame=cvEveryFrame)


def cvCurveFromObjAnimationSelected(cvEveryFrame=1):
    """Creates a CV curve based on an animated selected objects uses the time range and sets a CV per frame.

    Credit DELANO ATHIAS, cleaned up code from
    https://www.delanimation.com/tutorials-1/2020/1/2/generating-curves-from-motion-trails-in-maya

    :param cvEveryFrame: The amount of cvs per frame, 1.0 is one cv per frame, 2.0 is one CV every 2 frames
    :type cvEveryFrame: float
    """
    selObjs = cmds.ls(sl=True, type='transform')
    if not selObjs:
        output.displayInfo("Nothing Selected, please select an animated object")
        return
    startTime = cmds.playbackOptions(query=True, min=True)
    endTime = cmds.playbackOptions(query=True, max=True)
    cvCurveFromObjsAnimation(selObjs, startTime, endTime, cvEveryFrame=cvEveryFrame)
