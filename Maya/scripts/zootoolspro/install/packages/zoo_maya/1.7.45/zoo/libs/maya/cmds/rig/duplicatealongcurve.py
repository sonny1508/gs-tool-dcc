import math

from maya import cmds
from maya.api import OpenMaya as om2
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.objutils import namehandling, shapenodes, filtertypes
from zoo.libs.maya.cmds.rig import controls, splines
from zoo.libs.maya.cmds.rig.splines import WORLD_UP_SCENE



"""
Build Objects Along Spline
"""


class DuplicateAlongCurveCore(object):

    @classmethod
    def autoWorldUpVector(cls, splineCurve, upVectorName, controlScale=1.0):
        """Creates an arrow attaches it's grp to the start of the motion path with no follow/orientation for up vector"""
        upVArrow = controls.createControlCurve(folderpath="",
                                               ctrlName=upVectorName,
                                               curveScale=(controlScale, controlScale, controlScale),
                                               designName=splines.UPV_CONTROL,
                                               addSuffix=True,
                                               shapeParent=None,
                                               rotateOffset=(90.0, 0.0, 0.0),
                                               trackScale=True,
                                               lineWidth=-1,
                                               rgbColor=None,
                                               addToUndo=True)[0]
        shapenodes.translateObjListCVs([upVArrow], [0.0, 1.0, 0.0])
        upVGrp, upVArrow, grpUuid, objUuid = controls.groupInPlace(upVArrow, grpSwapSuffix=True)
        upVMoPath = cmds.pathAnimation(upVGrp,
                                       name="{}_moPath".format(upVectorName),
                                       curve=splineCurve,
                                       follow=False,
                                       fractionMode=True,
                                       startTimeU=0,
                                       endTimeU=1)
        cmds.cutKey(upVMoPath, time=(0, 1), clear=True, attribute="uValue")  # delete the keys
        return upVGrp, upVArrow, upVMoPath

    @classmethod
    def duplicateAlongCurve(cls, sourceObjects, splineCurve, multiplyObjects=5, deleteMotionPaths=False,
                            spacingWeight=0.0,
                            spacingStart=0.0, spacingEnd=1.0, rotationStart=(0, 0, 0), rotationEnd=(0, 0, 0),
                            scaleStart=(1.0, 1.0, 1.0), scaleEnd=(1.0, 1.0, 1.0), worldUpVector=(0, 1, 0),
                            follow=True, worldUpType=WORLD_UP_SCENE, group=True, instance=False,
                            upAxis="z", motionPName="moPth", worldUpObject="", followAxis="y",
                            fractionMode=True,
                            inverseFront=False, inverseUp=False, weightPosition=True, weightRotation=True,
                            weightScale=True, autoWorldUpV=False, message=False, duplicateSourceObjects=False, sourceGrp=False):
        """From the selection, object or objects and then a NURBS curve, places objects along a spline using motion paths, \
        added weighting kwarg for non-uniform spacing.

        This function will duplicate or instance the objectList by the multiplyObjects value.

        Can also use MASH but this will work on joints too. MASH only uses meshes.

        The options are mostly Maya's motionPath kwargs see:

            https://help.autodesk.com/cloudhelp/2016/ENU/Maya-Tech-Docs/CommandsPython/pathAnimation.html

        :param modifier:
        :type modifier: om2.MDGModifier
        :param sourceObjects: List of object/s in order to distribute along the curve, will be duplicated by multiplyObjects
        :type sourceObjects: list[zapi.DagNode]
        :param splineCurve: The NURBS spline transform node to distribute the objects along
        :type splineCurve: zapi.DagNode
        :param deleteMotionPaths: Deletes history so there are no motion paths returned
        :type deleteMotionPaths: bool
        :param spacingWeight: The spacing of the objects, 0.5 is uniform.  0.0 weights more towards the start 1.0 to end
        :type spacingWeight: float
        :param spacingStart: The spacing of the objects starts at this ratio along the curve
        :type spacingStart: float
        :param spacingEnd: The spacing of the objects ends at this ratio along the curve
        :type spacingEnd: float
        :param worldUpVector: The upVector for the joints
        :type worldUpVector: float
        :param group: Group all objects
        :type group: bool
        :param instance: Instance objects instead of duplicating?
        :type instance: bool
        :param follow: Objects will follow the curve
        :type follow: bool
        :param worldUpType: "scene", "object", "objectrotation", "vector", or "normal"
        :type worldUpType: str
        :param upAxis: This flag specifies which object local axis to be aligned a computed up direction. Default is z
        :type upAxis: str
        :param motionPName: The suffix name of the motion path example "obj_moPth"
        :type motionPName: str
        :param worldUpObject: Obj name if worldUpType "object" or "objectrotation". Default value is no up object, or world space.
        :type worldUpObject: str
        :param followAxis: Object local axis to be aligned to the tangent of the path curve. Default is y
        :type followAxis: str
        :param fractionMode: Calculate the position as a fraction of curve 0.0-1.0 or distance?
        :type fractionMode: bool
        :param inverseFront: Invert the follow axis?
        :type inverseFront: bool
        :return motionPathNodes: The motion path nodes created, a list of names
        :rtype motionPathNodes: list(str)
        :return objectList: A full list of objects stuck to the spline in the rig
        :rtype objectList: list(str)
        :return grp: The group containing the objects, if no group then will be ""
        :rtype grp: str
        :return splineCurve: The spline object
        :rtype splineCurve: str
        :return upVGrp: The name of the upVector grp if it was built otherwise ""
        :rtype upVGrp: str
        :return upVArrow: The name of the upVector control if it was built otherwise ""
        :rtype upVArrow: str
        :return upVMoPath: The name of the upVector motion path if it was built otherwise ""
        :rtype upVMoPath: str
        """
        if autoWorldUpV:  # build the arrow up vector at the start of the curve
            upVectorName = namehandling.nonUniqueNameNumber("{}_upV".format(splineCurve.fullPathName()))
            upVGrp, upVArrow, upVMoPath = DuplicateAlongCurveCore.autoWorldUpVector(splineCurve.fullPathName(),
                                                                                    upVectorName)
            worldUpObject = upVArrow
        else:
            upVGrp = ""
            upVArrow = ""
            upVMoPath = ""

        objectList = []
        origSourceObjects = list(sourceObjects)
        if multiplyObjects > 0:
            dupList = list(sourceObjects)

            # Create the new objects
            for x in range(multiplyObjects):
                objectList += cmds.duplicate(zapi.fullNames(dupList), instanceLeaf=instance, returnRootsOnly=True)

            cmds.showHidden(objectList)

        motionPathNodes = splines.objectsAlongSpline(objectList, splineCurve.fullPathName(),
                                                     deleteMotionPaths=deleteMotionPaths,
                                                     spacingWeight=spacingWeight,
                                                     spacingStart=spacingStart, rotationStart=rotationStart,
                                                     rotationEnd=rotationEnd, scaleStart=scaleStart, scaleEnd=scaleEnd,
                                                     spacingEnd=spacingEnd, worldUpVector=worldUpVector, follow=follow,
                                                     worldUpType=worldUpType, upAxis=upAxis, motionPName=motionPName,
                                                     worldUpObject=worldUpObject, followAxis=followAxis,
                                                     fractionMode=fractionMode,
                                                     inverseFront=inverseFront, inverseUp=inverseUp,
                                                     weightPosition=weightPosition,
                                                     weightRotation=weightRotation, weightScale=weightScale)


        if duplicateSourceObjects:
            dupSourceObjects = cmds.duplicate(sourceObjects, returnRootsOnly=True)
            sourceObjects = list(zapi.nodesByNames(dupSourceObjects))

        if sourceGrp:
            sourceGrp = cmds.group(name="{}_sourceObj_grp".format(splineCurve.fullPathName()), empty=True)
            cmds.hide(sourceGrp)
            cmds.parent(zapi.fullNames(sourceObjects) + [sourceGrp])

        objDagList = list(zapi.nodesByNames(objectList))  # return objects for hierarchy long renames
        grp = ""
        rigGrp = ""
        if group:  # group the objects and rig under a couple of groups
            if upVArrow:
                upVectorDagList = list(zapi.nodesByNames([upVGrp, upVArrow, upVMoPath]))
            grp = cmds.group(objectList, name="{}_objs_grp".format(splineCurve.fullPathName()))
            grpDagList = list(zapi.nodesByNames([grp]))

            # parent into main group
            rigGrp = cmds.group(name="{}_rig_grp".format(splineCurve.fullPathName()), empty=True)
            cmds.parent(grp, sourceGrp or zapi.fullNames(sourceObjects), splineCurve.fullPathName(), rigGrp)
            grp = zapi.fullNames(grpDagList)[0]
            if upVArrow:
                cmds.parent(upVGrp, rigGrp)
                upVGrp, upVArrow, upVMoPath = zapi.fullNames(upVectorDagList)

        cmds.hide(zapi.fullNames(origSourceObjects))
        # Set up the return code
        rigGrp = zapi.nodeByName(rigGrp) if rigGrp else None
        grp = zapi.nodeByName(grp) if grp else None
        sourceGrp = zapi.nodeByName(sourceGrp) if sourceGrp else None
        ret = {"sourceObjects": sourceObjects,
               "motionPathNodes": zapi.nodesByNames(motionPathNodes),
               "objectList": objDagList,
               "splineCurve": splineCurve,
               "group": grp,
               "rigGroup": rigGrp,
               "upVGrp": zapi.nodeByName(upVGrp),
               "upVArrow": zapi.nodeByName(upVArrow),
               "upVMoPath": zapi.nodeByName(upVMoPath)}

        if sourceGrp:
            ret["sourceGroup"] = sourceGrp

        if message:
            om2.MGlobal.displayInfo("Success: Motion path setup created.")

        return ret

    @classmethod
    def duplicateAlongCurveSelected(cls, multiplyObjects=5, deleteMotionPaths=False, spacingWeight=0.0,
                                    spacingStart=0.0,
                                    spacingEnd=1.0, rotationStart=(0, 0, 0), rotationEnd=(0, 0, 0),
                                    scaleStart=(1.0, 1.0, 1.0),
                                    scaleEnd=(1.0, 1.0, 1.0), worldUpVector=(0, 1, 0),
                                    follow=True, worldUpType=WORLD_UP_SCENE, group=True, instance=False,
                                    upAxis="z", motionPName="moPth", worldUpObject="", followAxis="y",
                                    fractionMode=True,
                                    inverseFront=False, inverseUp=False, weightPosition=True, weightRotation=True,
                                    weightScale=True, autoWorldUpV=False):
        """Same as objectsAlongSplineDuplicate() but for selection

        The selection is the objects to duplicate and then the curve transform last.

        See objectsAlongSplineDuplicate() for documentation
        """
        # selObjs = cmds.ls(selection=True)
        selObjs = list(zapi.selected())
        if not selObjs or len(selObjs) < 2:
            om2.MGlobal.displayWarning("Selection incorrect.  Please select an object or objects and a curve last")
            return
        splineCurve = selObjs[-1]
        if not filtertypes.filterTypeReturnTransforms([splineCurve.fullPathName()], children=False,
                                                      shapeType="nurbsCurve"):
            om2.MGlobal.displayWarning("The last selected object must be a NURBS curve")
            return
        del selObjs[-1]

        ret = DuplicateAlongCurveCore.duplicateAlongCurve(selObjs, splineCurve, multiplyObjects=multiplyObjects,
                                                          deleteMotionPaths=deleteMotionPaths,
                                                          spacingWeight=spacingWeight,
                                                          spacingStart=spacingStart, spacingEnd=spacingEnd,
                                                          rotationStart=rotationStart,
                                                          rotationEnd=rotationEnd, scaleStart=scaleStart,
                                                          scaleEnd=scaleEnd, worldUpVector=worldUpVector, follow=follow,
                                                          worldUpType=worldUpType, group=group, instance=instance,
                                                          upAxis=upAxis,
                                                          motionPName=motionPName, worldUpObject=worldUpObject,
                                                          followAxis=followAxis,
                                                          fractionMode=fractionMode, inverseFront=inverseFront,
                                                          inverseUp=inverseUp,
                                                          weightPosition=weightPosition, weightRotation=weightRotation,
                                                          weightScale=weightScale, autoWorldUpV=autoWorldUpV,
                                                          message=True)
        cmds.select(ret['splineCurve'].fullPathName())  # Select curve

        return ret



