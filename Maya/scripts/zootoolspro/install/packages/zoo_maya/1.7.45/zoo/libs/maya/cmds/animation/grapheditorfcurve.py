"""

from zoo.libs.maya.cmds.animation import grapheditorfcurve
grapheditorfcurve.autoTangentCycleSel(0.0, 24.0, includeProxyAttrs=True, tangentType="auto")


"""

import maya.cmds as cmds
from zoo.libs.utils import output

from zoo.libs.maya.cmds.objutils import attributes
from zoo.libs.maya.cmds.animation import animobjects
from zoo.libs.maya.cmds.display import viewportmodes


def convertKeyIndexList(keyIndexList):
    """Converts a list(long, long) of keys to a format that cmds python can use list(set(int), set(int))

    Example:

        Converts [2L, 3L] to [(2,2), (3,3)]

    :param keyIndexList: A list of keyframe indices, usually [2L, 3L] as per querying Maya
    :type keyIndexList: list
    :return newKeyIndex:  A new list now in a format that the python command recognises [(2,2), (3,3)]
    :rtype objList: list(set)
    """
    newKeyIndex = list()
    for index in keyIndexList:
        newKeyIndex.append((int(index), int(index)))
    return newKeyIndex


def objFromFCurve():
    """Returns a list of objects connected to a graph curve

    :return objList: list of maya object/node names
    :rtype objList: list(str)
    """
    objList = list()
    curvesSelected = cmds.keyframe(query=True, name=True, selected=True)
    if curvesSelected:
        for curve in curvesSelected:
            objList.append(cmds.listConnections(curve, source=True)[0])
    return list(set(objList))


def selectObjFromFCurve(message=True):
    """Selects objects related to any selected curves in Maya's graph editor.

    :param message: report the message back to the user?
    :type message: bool
    :return objList: list of maya object/node names
    :rtype objList: list(str)
    """
    objList = objFromFCurve()
    if not objList:
        if message:
            output.displayWarning("Please select graph curves attached to an object/s.")
        return objList
    cmds.select(objList, replace=True)
    return objList


def jumpToSelectedKey(closestKey=10000000.0, closestGap=10000000.0, message=True):
    """Changes the current time in the graph editor (Maya timeline) to match to the closest selected keyframe

    :param closestKey: the default closest keyframe, should default to a very large number
    :type closestKey: float
    :param closestGap: the default closest gap between the closestKey and currentTime, should be very large
    :type closestGap: float
    :param message: report the message back to the user?
    :type message: bool
    :return closestKey: the closest keyframe found, will be None if null
    :rtype closestKey: float
    """
    currentTime = cmds.currentTime(query=True)
    selectedKeys = cmds.keyframe(query=True, selected=True)
    if not selectedKeys:
        if message:
            output.displayWarning("Please select keyframes in order to move the time slider.")
        return
    for key in selectedKeys:
        tempVal = abs(currentTime - key)  # get keyframe distance from current time to curr key, neg numbers become pos
        if tempVal < closestGap:  # then record this key as the closest key
            closestKey = key
            closestGap = tempVal
    if message:
        output.displayInfo("Time moved to frame {}.".format(closestKey))
    cmds.currentTime(closestKey)
    return closestKey


def moveKeysSelectedTime(message=True):
    """Moves the selected keys to the current time. The first keyframe matching, maintains the spacing of selection

    :param message: report the message back to the user?
    :type message: bool
    """
    currentTime = cmds.currentTime(query=True)
    selKeys = sorted(cmds.keyframe(query=True, selected=True))  # sort list ordered smallest to largest
    firstKey = selKeys[0]  # smallest number, first in timeline of the selection
    moveAmount = currentTime - firstKey  # difference between first key and current time
    cmds.keyframe(timeChange=moveAmount, relative=True, option='over')  # move
    if message:
        output.displayInfo("Selected keys moved by {} frames".format(moveAmount))


def animHold(message=True):
    """Creates a held pose with two identical keys and flat tangents intelligently from the current keyframes

    Functionality:

        - For each curve, finds the previous key and copies it to the next keyframe while flattening both tangents.
        - Will work on selected curves only as a priority if curves have been selected
        - If no curve/s are selected then use all default curves, does not need the Graph Editor open
        - Will check if the current attribute values differ from the current curve values (ie object has moved)
        - If finds a mismatch between current curve value and current actual value, then uses the current actual value

    Authors: Original .mel script by David Peers converted to python by Andrew Silke (also co-creator)

    :param message: report the message back to the user?
    :type message: bool
    """
    success = False
    curveAttrs = list()
    currentAttrVals = list()
    curveAttrVals = list()
    # ---------------
    # Check for any active curves/keyframe data on the current selection
    # ---------------
    curvesActive = cmds.keyframe(query=True, name=True)
    if not curvesActive:  # then bail no keys found
        if message:
            output.displayWarning("No Curves Active")
        return False
    # ---------------
    # Gather Keyframe Data
    # ---------------
    currentTime = cmds.currentTime(query=True)
    selCurves = cmds.keyframe(query=True, name=True, selected=True)
    if not selCurves:  # No selected curves so use the active curves instead
        selCurves = curvesActive
    timePlusOne = currentTime + 1
    lastKey = cmds.findKeyframe(time=(timePlusOne, timePlusOne), which="previous")
    for curve in selCurves:
        curveConnection = cmds.listConnections(curve, plugs=True, source=False)[0]
        curveAttrs.append(curveConnection)  # Attributes list ie pCube3_translateX
        currentAttrVals.append(cmds.getAttr(curveConnection))  # Current attr values, eg. actual obj position
        curveAttrVals.append(cmds.keyframe(curve, query=True, eval=True)[0])  # Current curve value at current frame
    # ---------------
    # Main Logic
    # ---------------
    for i, curve in enumerate(selCurves):
        isLastKey = cmds.keyframe(curve, time=(lastKey, lastKey), query=True, keyframeCount=True)
        if isLastKey == 1:  # then for this curve then there is a key on the frame 'lastKey'
            equivTest = abs(currentAttrVals[i] - curveAttrVals[i]) <= 0.001
            if not equivTest:  # Then there is an unkeyed change in the scene, so set first key to current position
                cmds.setKeyframe(curve, value=currentAttrVals[i], time=(lastKey, lastKey), inTangentType="linear",
                                 outTangentType="linear")
            # Find previous/next keys on the current curve
            lastKey = cmds.findKeyframe(curve, time=(timePlusOne, timePlusOne), which="previous")
            nextKey = cmds.findKeyframe(curve, time=(currentTime, currentTime), which="next")
            # Make the hold
            cmds.keyTangent(curve, time=(lastKey, lastKey), inTangentType="auto", outTangentType="auto")
            cmds.copyKey(curve, time=(lastKey, lastKey))
            cmds.pasteKey(curve, time=(nextKey, nextKey))
            cmds.keyTangent(curve, time=(nextKey, nextKey), inTangentType="auto", outTangentType="auto")
            # Report messages
            success = True
    if message and success:
        output.displayInfo("Animation hold has been created")
    else:
        output.displayWarning("No animation hold was created")
    return success


# ---------------
# Cycle Tools
# ---------------


def autoTangentCycleAttr(animCurve, firstFrame, lastFrame, tangentType="auto"):
    """Match the start and end frame tangents on a single curve for loop cycles.

    Uses "auto" tangents by default as if keys were present before and after the cycle.

    Can be other:
        "spline", "autoease", "automix", "autocustom"

    :param animCurve: An animation curve node "pCube1_rotateX" or obj.attribute "pCube1.rotateX"
    :type animCurve: str
    :param firstFrame: The first frame of the cycle eg. 0.0
    :type firstFrame: float
    :param lastFrame: The first frame of the cycle eg. 24.0
    :type lastFrame:  float
    :param tangentType: The default tangent type setting can be other "spline", "autoease", "automix", "autocustom" etc.
    :type tangentType: str

    :return success: Returns True is single curve's tangents was modified correctly.
    :rtype success: bool
    """
    recheck = False
    keys = cmds.keyframe(animCurve, time=(), query=True)

    if not keys:
        return False

    if not firstFrame in keys or not lastFrame in keys:  # Must have keys on the first and last frames
        return False

    # delete keys if before and after the start/end
    if keys[0] != firstFrame:
        cmds.cutKey(animCurve, time=(':{}'.format(str(firstFrame - .01)),))
        recheck = True
    if keys[-1] != lastFrame:
        cmds.cutKey(animCurve, time=('{}:'.format(str(lastFrame + .01)),))
        recheck = True
    if recheck:  # recheck the key list as keys have been deleted
        keys = cmds.keyframe(animCurve, time=(), query=True)

    # Keys are valid and tangents can be set -----------------------------------------
    negSpacing = lastFrame - keys[-2]
    posSpacing = keys[1] - keys[0]
    negKeyTime = firstFrame - negSpacing
    posKeyTime = keys[-1] + posSpacing

    # Create neg temp key
    cmds.copyKey(animCurve, time=(keys[-2],))
    cmds.pasteKey(animCurve, time=(negKeyTime,))

    # Create pos temp key
    cmds.copyKey(animCurve, time=(keys[1],))
    cmds.pasteKey(animCurve, time=(posKeyTime,))

    for i, frame in enumerate([firstFrame, lastFrame]):  # Set tangents on the first and last frames
        cmds.keyTangent(animCurve, time=(frame,), inTangentType=tangentType, outTangentType=tangentType)  # set auto
        inAngle = cmds.keyTangent(animCurve, time=(frame,), inAngle=True, query=True)[0]
        outAngle = cmds.keyTangent(animCurve, time=(frame,), outAngle=True, query=True)[0]

        if not i:  # Delete the neg key first time through
            cmds.cutKey(animCurve, time=(negKeyTime,))
        else:  # then delete the pos key
            cmds.cutKey(animCurve, time=(posKeyTime,))

        cmds.keyTangent(animCurve, time=(frame,), inAngle=inAngle, outAngle=outAngle)  # Set hardcode tangents

    return True


def autoTangentCycleObj(node, firstFrame, lastFrame, includeProxyAttrs=True, tangentType="auto"):
    """Match the start and end frame tangents on a single object for loop cycles.

    Uses "auto" tangents by default as if keys were present before and after the cycle.

    Can be other:
        "spline", "autoease", "automix", "autocustom"

    :param node: A maya object transform name
    :type node: str
    :param firstFrame: The first frame of the cycle eg. 0.0
    :type firstFrame: float
    :param lastFrame: The first frame of the cycle eg. 24.0
    :type lastFrame:  float
    :param includeProxyAttrs: Include animated proxy attributes?
    :type includeProxyAttrs: bool
    :param tangentType: The default tangent type setting can be other "spline", "autoease", "automix", "autocustom" etc.
    :type tangentType: str

    :return success: Returns True is single curve's tangents was modified correctly.
    :rtype success: bool
    """
    success = False
    # Returns the keyable channel box attributes on the object
    attrList = attributes.channelBoxAttrs(node, settableOnly=True, includeProxyAttrs=includeProxyAttrs)

    if not attrList:
        return False

    for attr in attrList:  # If attrs then loop on them
        if autoTangentCycleAttr(".".join([node, attr]), firstFrame, lastFrame, tangentType=tangentType):
            success = True

    return success


def autoTangentCycleCurveList(firstFrame, lastFrame, animCurveList, tangentType="auto"):
    """See documentation for autoTangentCycleAttr() this function iterates over a list.

    :param firstFrame: The first frame of the cycle eg. 0.0
    :type firstFrame: float
    :param lastFrame: The first frame of the cycle eg. 24.0
    :type lastFrame:  float
    :param animCurveList: An list of animation curve nodes ["pCube1_rotateX"] or obj.attributes ["pCube1.rotateX]
    :type animCurveList: list(str)
    :param tangentType: The default tangent type setting can be other "spline", "autoease", "automix", "autocustom" etc.
    :type tangentType: str
    :return success: success if one or more tangents were adjusted.
    :rtype success: bool
    """
    success = False
    for animCurve in animCurveList:
        if autoTangentCycleAttr(animCurve, firstFrame, lastFrame, tangentType=tangentType):
            success = True
    return success


def autoTangentCycleSel(firstFrame, lastFrame, tangentType="auto", message=True):
    """Match the start and end frame tangents on the selection for loop cycles.

    Selection priority is curves then channelbox attrs then object selection (all curves)

    Uses "auto" tangents by default as if keys were present before and after the cycle.

    Can be other:
        "spline", "autoease", "automix", "autocustom"

    :param firstFrame: The first frame of the cycle eg. 0.0
    :type firstFrame: float
    :param lastFrame: The first frame of the cycle eg. 24.0
    :type lastFrame:  float
    :param tangentType: The default tangent type setting can be other "spline", "autoease", "automix", "autocustom" etc.
    :type tangentType: str

    :return success: Returns True is single curve's tangents was modified correctly.
    :rtype success: bool
    """
    animCurves, objAttrs, selObjs = animobjects.animSelection()
    if not selObjs:
        if message:
            output.displayWarning("Nothing selected.  Please select objects, nodes, curves or channel box selection.")
        return
    if animCurves:
        success = autoTangentCycleCurveList(firstFrame, lastFrame, animCurves, tangentType=tangentType)
    elif objAttrs:
        success = autoTangentCycleCurveList(firstFrame, lastFrame, objAttrs, tangentType=tangentType)
    elif selObjs:
        if message:
            output.displayWarning("No animation found on the selected nodes/objects.")
        return
    if message:
        if success:
            output.displayInfo("Success: Tangents corrected on frames `{}` and `{}`".format(firstFrame, lastFrame))


# -------------------------------
# Graph Editor Window
# -------------------------------


def graphExpandConnections(expandConnections=False, message=True):
    """Expands or removes connections in the graph editor.

    Deselects, so the user forces the refresh as refresh is difficult.

    :param expandConnections:
    :type expandConnections:
    :param closeGraphs:
    :type closeGraphs:
    :return:
    :rtype:
    """
    cmds.select(deselect=True)
    graphEditors = viewportmodes.editorFromPanelType(scriptedPanelType="graphEditor")
    if graphEditors:
        for graphEditor in graphEditors:
            cmds.outlinerEditor(graphEditor, edit=True, expandConnections=expandConnections)
        if message:
            if expandConnections:
                expansion = "expanded"
            else:
                expansion = "collapsed"
            output.displayInfo("Success: Graph Editor connections `{}`".format(expansion))

