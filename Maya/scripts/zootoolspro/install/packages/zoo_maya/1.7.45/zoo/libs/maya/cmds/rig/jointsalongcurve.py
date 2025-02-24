from maya import cmds as cmds
from maya.api import OpenMaya as om2
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.meta import metajointscurve
from zoo.libs.maya.cmds.objutils import filtertypes, namehandling, joints
from zoo.libs.maya.cmds.rig.splines import objectsAlongSplineDuplicate
from zoo.libs.maya.cmds.rig import axis
from zoo.libs.maya.meta import base

"""
Joints Along A Spline
"""


def jointsAlongACurve(splineCurve, jointCount=30, jointName="joint", spacingWeight=0.0, spacingStart=0.0,
                      spacingEnd=1.0, secondaryAxisOrient="yup", fractionMode=True, numberPadding=2, suffix=True,
                      buildMetaNode=False, reverseDirection=False, hideCurve=False, message=True):
    """Given a spline curve build joints along the curve, parent and orient them into an FK chain.

    :param splineCurve: The name of the transform node of the curve
    :type splineCurve: str
    :param jointCount: The number of joints to build in the chain
    :type jointCount: int
    :param jointName: The base name of the joints to be created
    :type jointName: str
    :param spacingWeight: The weighting of the spacing, causes more joints to be sqashed to one end or another 0.0 - 1.0
    :type spacingWeight: float
    :param spacingStart: The start of the curve where the joint chain will start usually 0.0 (start)
    :type spacingStart: float
    :param spacingEnd: The end of the curve where the joint chain will start usually 1.0 (end)
    :type spacingEnd: float
    :param secondaryAxisOrient: this axis of the joints orients in what direction?  Default is "yup"
    :type secondaryAxisOrient: str
    :param fractionMode: calculates in real world coords based on the curve, is affected by the spacing on the CVs.
    :type fractionMode: bool
    :param numberPadding: Pad the joint names with numbers and this padding.  ie 2 is 01, 02, 03
    :type numberPadding: int
    :param suffix: Add a joint suffix "jnt" to the end of the joint names ie "joint_01_jnt"
    :type suffix: bool
    :param buildMetaNode: builds the meta node for tracking and altering the joints later
    :type buildMetaNode: bool
    :param reverseDirection: reverses the curve while building, the reverses it back after build
    :type reverseDirection: bool
    :param hideCurve: hides the incoming curve splineCurve
    :type hideCurve: bool
    :param message: return any messages to the user?
    :type message: bool

    :return jointList: A list of joint string names
    :rtype jointList: list(str)
    """
    if secondaryAxisOrient == joints.AUTO_UP_VECTOR_WORDS_LIST[0]:  # is "Auto"
        upAxis = axis.autoAxisBBoxObj(splineCurve, secondaryAxis=True)  # Result will be "+y" or "+z"
        index = joints.AUTO_UP_VECTOR_POSNEG_LIST.index(upAxis)
        secondaryAxisOrient = joints.AUTO_UP_VECTOR_WORDS_LIST[index]  # now fixed to "yup" or "zup"
    if jointCount < 1:
        jointCount = 1
    jointList = list()
    if fractionMode:  # Normalize values
        if spacingStart < 0.0:
            spacingStart = 0.0
        if spacingEnd > 1.0:
            spacingEnd = 1.0
    buildCurve = splineCurve
    if reverseDirection:  # Reverse the direction of the curve
        buildCurve = cmds.reverseCurve(splineCurve, replaceOriginal=False)[0]
    for n in range(jointCount):  # create joints
        cmds.select(deselect=True)
        if suffix:
            n = "_".join([jointName, str(n + 1).zfill(numberPadding), filtertypes.JOINT_SX])
        else:
            n = "_".join([jointName, str(n + 1).zfill(numberPadding)])
        jointList.append(cmds.joint(name=namehandling.nonUniqueNameNumber(n)))
    # Place joints on the curve
    objectsAlongSplineDuplicate(jointList, buildCurve, multiplyObjects=0, deleteMotionPaths=True,
                                spacingWeight=spacingWeight, spacingStart=spacingStart, spacingEnd=spacingEnd,
                                follow=False, group=False, fractionMode=fractionMode, weightPosition=True,
                                weightRotation=False, weightScale=False, autoWorldUpV=False, message=False)
    # Parent the joints to each other
    jntDagList = list(zapi.nodesByNames(jointList))  # objects to api dag objects for names
    for n in range(1, len(jointList)):
        cmds.parent(jointList[n], jointList[n - 1])
    jointList = zapi.fullNames(jntDagList)  # back to long names
    # Orient joints
    if len(jointList) > 1:
        joints.alignJoint(jointList, secondaryAxisOrient=secondaryAxisOrient, children=False, freezeJnt=True,
                          message=False)
        joints.alignJointToParent(jointList[-1])  # orient last joint to parent
    if reverseDirection:  # Delete reverse direction curve
        cmds.delete(buildCurve)
    if buildMetaNode:  # Builds the network meta node on all joints and the curve
        name = namehandling.nonUniqueNameNumber("{}_joints_meta".format(splineCurve))
        metaNode = metajointscurve.ZooJointsCurve(name=name)
        metaNode.connectAttributes(list(zapi.nodesByNames(jointList)),
                                   zapi.nodeByName(splineCurve))
        metaNode.setMetaAttributes(jointCount, jointName, spacingWeight, spacingStart, spacingEnd, secondaryAxisOrient,
                                   fractionMode, numberPadding, suffix, reverseDirection)
    if hideCurve:
        cmds.hide(splineCurve)
    if message:
        om2.MGlobal.displayInfo("Success: Joints created and oriented along `{}`.".format(splineCurve))
    return jointList


def jointsAlongACurveSelected(jointCount=30, jointName="joint", spacingWeight=0.0, spacingStart=0.0,
                              spacingEnd=1.0, secondaryAxisOrient="yup", fractionMode=True, numberPadding=2,
                              suffix=True, buildMetaNode=True, reverseDirection=False):
    """Given a selected spline curve build joints along the curve, parent and orient them into an FK chain.

    :param jointCount: The number of joints to build in the chain
    :type jointCount: int
    :param jointName: The base name of the joints to be created
    :type jointName: str
    :param spacingWeight: The weighting of the spacing, causes more joints to be sqashed to one end or another 0.0 - 1.0
    :type spacingWeight: float
    :param spacingStart: The start of the curve where the joint chain will start usually 0.0 (start)
    :type spacingStart: float
    :param spacingEnd: The end of the curve where the joint chain will start usually 1.0 (end)
    :type spacingEnd: float
    :param secondaryAxisOrient: this axis of the joints orients in what direction?  Default is "yup"
    :type secondaryAxisOrient: str
    :param fractionMode: calculates in real world coords based on the curve, is affected by the spacing on the CVs.
    :type fractionMode: bool
    :param numberPadding: Pad the joint names with numbers and this padding.  ie 2 is 01, 02, 03
    :type numberPadding: int
    :param suffix: Add a joint suffix "jnt" to the end of the joint names ie "joint_01_jnt"
    :type suffix: bool
    :param buildMetaNode: builds the meta node for tracking and altering the joints later
    :type buildMetaNode: bool
    :param reverseDirection: reverses the curve while building, the reverses it back after build
    :type reverseDirection: bool

    :return jointListList: A list of a list of joint string names
    :rtype jointListList: list(list(str))
    """
    selObjs = cmds.ls(selection=True)
    curveTransforms = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="nurbsCurve")
    if not curveTransforms:
        om2.MGlobal.displayWarning("Selection incorrect.  Please a curve type object.")
        return
    if len(curveTransforms) > 1:  # multiple curves found build a joint chain on each curve, names are different
        jointListList = list()
        uniqueName = namehandling.nonUniqueNameNumber(jointName)
        for i, curve in enumerate(curveTransforms):
            jointName = "_".join([uniqueName, str(i + 1).zfill(numberPadding)])
            jointList = jointsAlongACurve(curve, jointCount=jointCount, jointName=jointName,
                                          spacingWeight=spacingWeight,
                                          spacingStart=spacingStart, spacingEnd=spacingEnd,
                                          secondaryAxisOrient=secondaryAxisOrient,
                                          fractionMode=fractionMode, numberPadding=numberPadding,
                                          buildMetaNode=buildMetaNode, reverseDirection=reverseDirection)
            jointListList.append(jointList)
        return jointListList
    # Else only one curve found
    jointList = jointsAlongACurve(curveTransforms[0], jointCount=jointCount, jointName=jointName,
                                  spacingWeight=spacingWeight,
                                  spacingStart=spacingStart, spacingEnd=spacingEnd,
                                  secondaryAxisOrient=secondaryAxisOrient,
                                  fractionMode=fractionMode, numberPadding=numberPadding, suffix=suffix,
                                  buildMetaNode=buildMetaNode, reverseDirection=reverseDirection)
    return [jointList]


def deleteSplineJoints(relatedObjs, message=False):
    """Deletes all joints and the meta node setup related to the selection

    :param relatedObjs: any maya nodes by name, should be joints or curves related to joint setup
    :type relatedObjs: str
    :param message: report the message to the user
    :type message: bool
    """
    metajointscurve.deleteSplineJoints(list(zapi.nodesByNames(relatedObjs)), message=message)


def deleteSplineJointsSelected(message=True):
    """Deletes all joints and the meta node setup related to the selection

    :param message: report the message to the user
    :type message: bool
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        om2.MGlobal.displayWarning("Please select a joint or curve related to the spline joint setup")
        return
    metajointscurve.deleteSplineJoints(list(zapi.nodesByNames(selObjs)), message=message)


def rebuildSplineJointsSelected(jointCount=30, jointName="joint", spacingWeight=0.0, spacingStart=0.0,
                                spacingEnd=1.0, secondaryAxisOrient="yup", fractionMode=True, numberPadding=2,
                                suffix=True, buildMetaNode=True, reverseDirection=False, message=True,
                                renameMode=False):
    """Deletes all joints and the meta node setup related to the selection and then rebuilds it as per the kwargs

    See jointsAlongACurve() for documentation

    :param renameMode: If True will use the incoming name to build the new setup.  If False will use the existing name
    :type renameMode: bool
    """
    lastJointList = list()
    selNodes = zapi.selected()
    if not selNodes:
        if message:
            om2.MGlobal.displayWarning("Please select a joint or curve related to the spline joint setup")
        return
    metaNodes = base.findRelatedMetaNodesByClassType(selNodes, metajointscurve.ZooJointsCurve.__name__)
    if not metaNodes:
        if message:
            om2.MGlobal.displayWarning("No `{}` related setups found connected to "
                                       "objects".format(metajointscurve.META_TYPE))
        return

    for metaNode in metaNodes:
        curve = metaNode.getCurveStr()
        if not curve:  # no curve so bail
            continue
        jointList = metaNode.getJointsStr()
        if not renameMode:  # get the previous name
            jointName = metaNode.getMetaJointName()
        if jointList:
            metaNode.deleteJoints()
            metaNode.delete()
        jointList = jointsAlongACurve(curve, jointCount=jointCount, jointName=jointName, spacingWeight=spacingWeight,
                                      spacingStart=spacingStart, spacingEnd=spacingEnd,
                                      secondaryAxisOrient=secondaryAxisOrient,
                                      fractionMode=fractionMode, numberPadding=numberPadding, suffix=suffix,
                                      buildMetaNode=buildMetaNode, reverseDirection=reverseDirection, message=message)
        lastJointList.append(jointList[-1])
        if message:
            om2.MGlobal.displayInfo("Success: Joints rebuilt on `{}`".format(curve))
    if len(metaNodes) > 1:  # select all last joints
        cmds.select(lastJointList, add=True)

    return lastJointList


def splineJointsAttrValues(message=True):
    """Returns all the attribute (usually related to the UI) settings from the jointsOnCurve meta node

    Finds related meta node from selected objects either the joints or curves

    :param message: report messages to the user
    :type message: bool
    """
    selNodes = zapi.selected()
    if not selNodes:
        if message:
            om2.MGlobal.displayWarning("Please select a joint or curve related to the spline joint setup")
        return dict()
    metaNodes = base.findRelatedMetaNodesByClassType(selNodes, metajointscurve.ZooJointsCurve.__name__)
    if not metaNodes:
        if message:
            om2.MGlobal.displayWarning("No `{}` related setups found connected to "
                                       "objects".format(metajointscurve.META_TYPE))
        return dict()
    return metaNodes[-1].getMetaAttributes()
