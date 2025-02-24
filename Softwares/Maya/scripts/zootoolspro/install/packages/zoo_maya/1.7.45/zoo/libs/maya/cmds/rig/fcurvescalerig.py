import maya.cmds as cmds
import maya.api.OpenMaya as om2


def fCurveProfileScaleJoints(name="hair"):
    """This function adds a function curve that acts as a profile scale for a joint chain.

    Used in the hair rig setup.

    Requires the joints to be all parented to world and y aligned as it takes the y pos of each joint to hookup to the \
    length.

    :param name: Prefix name of all nodes
    :type name: str
    :return curveNode: The animCurveTU node that is created, this is the function curve
    :rtype curveNode: str
    :return selJoints: The joints that the setup was applied to
    :rtype selJoints: list(str)
    :return frameCacheNodes: A list of all the frameCacheNodes created, these give the offset
    :rtype frameCacheNodes: list(str)
    """
    selJoints = cmds.ls(selection=True)
    frameCacheNodes = list()
    if not selJoints:
        om2.MGlobal.displayWarning("Please Select some joints")
        return

    curveNode = cmds.createNode("animCurveTU", name="{}_aCurveUU".format(name))

    # get the top most joint y, should be the first joint in the selection
    height = cmds.getAttr("{}.translateY".format(selJoints[0]))

    cmds.setKeyframe(curveNode, v=0, t=0, breakdown=0)
    cmds.setKeyframe(curveNode, v=1, t=height / 2, breakdown=0)
    cmds.setKeyframe(curveNode, v=0, t=height, breakdown=0)

    for i, jnt in enumerate(selJoints):
        frameCache = cmds.createNode("frameCache", name="{}_fCache_{}".format(name, i))
        varyTime = cmds.getAttr("{}.translateY".format(jnt))
        cmds.setAttr("{}.varyTime".format(frameCache), varyTime)
        cmds.connectAttr('{}.output'.format(curveNode), '{}.stream'.format(frameCache))
        cmds.connectAttr('{}.varying'.format(frameCache), '{}.scaleX'.format(jnt))
        cmds.connectAttr('{}.varying'.format(frameCache), '{}.scaleZ'.format(jnt))
        frameCacheNodes.append(frameCache)

    return curveNode, selJoints, frameCacheNodes
