"""Code for duplicating objects.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.objutils import duplicates
    duplicates.duplicateToComponentsSel()

Author: Andrew Silke

"""

import maya.cmds as cmds

from zoo.libs.maya.cmds.objutils import shapenodes, matching
from zoo.libs.utils import output


def duplicateWithoutChildrenList(nodeList):
    """Duplicates nodes without their children

    :param nodeList: a list of Maya node names
    :type nodeList: list(str)
    :return duplicateList: A list of the duplicated nodes/objects
    :rtype duplicateList: list(str)
    """
    duplicateList = list()
    for node in nodeList:
        duplicateList.append(shapenodes.duplicateWithoutChildren(node))
    return duplicateList


def duplicateWithoutChildrenSelected(message=True):
    """Duplicates selected nodes without their children

    :return duplicateList: A list of the duplicated nodes/objects
    :rtype duplicateList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            output.displayWarning("No objects selected, please select object/s.")
        return
    return duplicateWithoutChildrenList(selObjs)


def duplicateToComponentCenter(objs, componentList):
    duplicates = list()
    components = cmds.ls(componentList, flatten=True)  # one component per list entry
    for comp in components:
        objs = cmds.duplicate(objs)
        duplicates += objs
        for obj in objs:
            matching.matchToCenterObjsComponents(obj, [comp])
    return duplicates


def duplicateToComponentsSel(objs, selectObjs=True, message=True):
    sel = cmds.ls(selection=True)
    if not sel:
        if message:
            output.displayWarning("No components have been selected, select verts, edges or faces")
        return
    duplicates = duplicateToComponentCenter(objs, sel)

    if selectObjs:
        cmds.select(duplicates, replace=True)
