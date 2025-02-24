"""
Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.animation import animobjects
    animobjects.animSelection()

"""


import maya.cmds as cmds

from zoo.libs.maya.cmds.objutils import objhandling
from zoo.libs.utils import output


def filterAnimatedNodes(nodeList):
    """Filters a list returning a new list of nodes that have keyframes

    :param nodeList: Incoming list of nodes
    :type list:
    :return animNodeList: The filtered list
    :type list:
    """
    animNodeList = []
    for n in nodeList:
        if cmds.keyframe(n, query=True, keyframeCount=True, time=(-100000, 10000000)):
            animNodeList.append(n)
    return animNodeList


def getAnimatedNodes(selectFlag="all", select=True, message=True):
    """Selects nodes animated with keyframes.  Flag allows for three select options:

        1. "all" : All in scene
        2. "selected" : only selected
        3. "hierarchy" : search selected hierarchy

    :param selectFlag: "all", "selected", "hierarchy".  All in scene, only selected and search selected hierarchy
    :type selectFlag: str
    :param select: If True will select the objects
    :type select: bool
    :param message: if True will report a message
    :type message: bool

    :return animNodeList: The list of animated nodes
    :type animNodeList: list
    """
    nodeList, selectionWarning = objhandling.returnSelectLists(selectFlag=selectFlag)
    animNodeList = []
    if nodeList:
        animNodeList = filterAnimatedNodes(nodeList)
        if select:
            cmds.select(animNodeList, r=True)
    if message:
        if animNodeList:
            output.displayInfo('Success: Animated nodes: {}'.format(animNodeList))
        elif selectionWarning:
            output.displayWarning('Please select object/s')
        else:
            output.displayWarning('No animated nodes found')
    return animNodeList


def animSelection():
    """Returns the animation selection with the following information.

        (animCurves, objAttrs, selObjs)

        animCurves: The names of the curve nodes ["pCube1_translateX"]
        objAttrs: The names of the matching object.attributes of the channelbox selection ["pCube1.translateX"]
        selObjs: The names of the selected objects/nodes as per usual ["pCube1"]

    Note: If animation curves are selected ignores the channelbox selection.

    :return animationSelection: returns the tuple with (animCurves, channelBoxAttrs, selObjs)
    :rtype animationSelection: tuple(list(str), list(str), list(str))
    """
    objAttrs = list()
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return list(), list(), list()
    animCurves = cmds.keyframe(query=True, name=True, selected=True)
    # Check for anim curve selection ---------------------
    if animCurves:
        return animCurves, list(), selObjs
    channelBoxAttrs = cmds.channelBox('mainChannelBox', query=True, selectedMainAttributes=True) or \
                      cmds.channelBox('mainChannelBox', query=True, selectedHistoryAttributes=True)
    # Check for channel box selection ---------------------
    if channelBoxAttrs:
        for obj in selObjs:
            for attr in channelBoxAttrs:
                if cmds.attributeQuery(attr, node=obj, exists=True):
                    objAttrs.append(".".join([obj, attr]))
        return list(), objAttrs, selObjs
    # No channel box or animCurves selected so return all animation on objects
    animCurves = cmds.keyframe(query=True, name=True)
    return animCurves, list(), selObjs

