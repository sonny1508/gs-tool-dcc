import maya.cmds as cmds
from zoo.libs.maya import zapi



def parentGroupControls(controlList, groupList, reverse=False, long=False):
    """Parents controls with groups into a simple hierarchy, zeroing the controls, can be reversed in order

    :param controlList: list of the controls
    :type controlList: list[zapi.DagNode]
    :param groupList: list of groups of the controls
    :type groupList: list[zapi.DagNode]
    :param reverse: If True reverse the parent hierarchy
    :type reverse: boolean
    :return controlList: A list of controls as zapi objects
    :rtype controlList: list[zapi.DagNode]
    :return groupList: A list of groups as zapi objects
    :rtype groupList: list[zapi.DagNode]
    """
    controlList = zapi.fullNames(controlList)
    groupList = zapi.fullNames(groupList)
    if reverse:
        controlList = list(reversed(controlList))
        groupList = list(reversed(groupList))
    for i, control in enumerate(controlList):
        if i:
            groupList[i] = (cmds.parent(groupList[i], controlList[i - 1]))[0]
            controlList[i] = (cmds.listRelatives(groupList[i], children=True, type="transform", fullPath=long))[0]
    if long:
        controlList = cmds.ls(controlList, long=True)
        groupList = cmds.ls(groupList, long=True)
    return list(zapi.nodesByNames(controlList)), list(zapi.nodesByNames(groupList))

