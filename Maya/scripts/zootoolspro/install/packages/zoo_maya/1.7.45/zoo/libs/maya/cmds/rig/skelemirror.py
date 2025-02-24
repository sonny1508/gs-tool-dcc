"""This module mirrors a standard Maya skeleton with L/R live mirroring via nodes, for scale rotate and translate.

Can also turn on segment scale compensate.

The resulting skeleton can be useful for scaling to the correct proportions of a new mesh for skin transfers.

from zoo.libs.maya.cmds.rig import skelemirror
skelemirror.buildSkeleMirrorSel(nameConvention=("_L_", "_R_"), segmentScale=True, mirror=True)

"""
from maya import cmds
from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import namehandling


def buildSkeleMirrorSel(nameConvention=("_L_", "_R_"), segmentScale=True, mirror=True):
    """Mirrors a standard Maya skeleton with L/R live mirroring via nodes, for scale rotate and translate.

    The resulting skeleton can be useful for scaling to the correct proportions of a new mesh for skin transfers.


    :param nameConvention: Use the two values for search and replace while setting up the mirror table.
    :type nameConvention:  tuple(str)
    :param segmentScale: Turn on the segment scale compensate attribute for all joints?
    :type segmentScale: bool
    :param mirror: Mirror the left and right joints, left controls right if order is L/R here ("_L_", "_R_")
    :type mirror: bool

    :return: leftJnts, rightJnts, multiplyNodes
    :rtype: tuple(list(str), list(str), list(str))
    """
    leftJnts = list()
    rightJnts = list()
    multiplyNodes = list()

    jointList = cmds.ls(selection=True, type="joint")

    if not jointList:
        output.displayWarning("No joints found: Please select all joints in the skeleton.")
        return leftJnts, rightJnts, multiplyNodes

    if segmentScale:
        for jnt in jointList:
            cmds.setAttr("{}.segmentScaleCompensate".format(jnt), 1)

    # Build the mirror lists ----------------------------
    for jnt in jointList:
        if nameConvention[0] in jnt:
            rightJoint = jnt.replace(nameConvention[0], nameConvention[1])
            if cmds.objExists(rightJoint):
                leftJnts.append(jnt)
                rightJnts.append(rightJoint)

    if not leftJnts:
        output.displayWarning("No left and right joints have been found to live mirror")
        return leftJnts, rightJnts, multiplyNodes

    if not mirror:
        return leftJnts, rightJnts, multiplyNodes

    # Do the live mirror -----------------------------------
    for i, jnt in enumerate(leftJnts):
        # link rotate and scale
        cmds.connectAttr("{}.scale".format(jnt), "{}.scale".format(rightJnts[i]))
        cmds.connectAttr("{}.rotate".format(jnt), "{}.rotate".format(rightJnts[i]))
        # link translate and reverse
        multiNode = cmds.createNode('multiplyDivide',
                                    name='mult_{}'.format(namehandling.getShortName(jnt)))
        multiplyNodes.append(multiNode)
        cmds.connectAttr("{}.translate".format(jnt), "{}.input1".format(multiNode))
        cmds.connectAttr("{}.output".format(multiNode), "{}.translate".format(rightJnts[i]))
        parentList = cmds.listRelatives(jnt, parent=True)
        if parentList:
            if nameConvention[0] in parentList[0]:  # if the parent is also left (not middle)
                cmds.setAttr("{}.input2X".format(multiNode), -1.0)
                cmds.setAttr("{}.input2Y".format(multiNode), -1.0)
            else:
                cmds.setAttr("{}.input2X".format(multiNode), 1.0)
                cmds.setAttr("{}.input2Y".format(multiNode), 1.0)
            cmds.setAttr("{}.input2Z".format(multiNode), -1.0)

    output.displayInfo("Success: Mirror setup completed")

    return leftJnts, rightJnts, multiplyNodes
