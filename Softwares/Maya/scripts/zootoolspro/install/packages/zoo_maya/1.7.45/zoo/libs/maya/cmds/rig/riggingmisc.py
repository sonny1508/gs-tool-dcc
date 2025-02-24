"""Module for assorted rigging related functions

Examples:

Example use:

.. code-block:: python

    # Unlock and unhide all nodes in a hierarchy.
    from zoo.libs.maya.cmds.rig import riggingmisc
    riggingmisc.markCenterPivot(name="")

    # Unlock and unhide all nodes in a hierarchy.
    from zoo.libs.maya.cmds.rig import riggingmisc
    riggingmisc.unlockUnhideAll()

 Author: Andrew Silke

"""

from maya import cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import namehandling, locators

TEMP_PIVOT_PREFIX = "tempPivot_loc"


def markCenterPivot(name=""):
    """Creates a locator with display handles on at the center pivot of the selection.

    Uses a cluster to mark the center point and then deletes it.

    :return locator:  The newly created locator
    :rtype locator: str
    """
    if not name:
        name = "{}_01".format(TEMP_PIVOT_PREFIX)
    return locators.createLocatorAndMatch(name=name, handle=True, locatorSize=0.1, message=True)


def deleteAllCenterPivots():
    """Deletes all the pivot locators in the scene named "tempPivot_loc"
    """
    pivots = cmds.ls("{}*".format(TEMP_PIVOT_PREFIX))
    pivLocators = list()
    for pivot in pivots:
        shapes = cmds.listRelatives(pivot, shapes=True)
        if not shapes:
            continue
        if cmds.nodeType(shapes[0]) == "locator":
            pivLocators.append(pivot)
    if pivLocators:
        cmds.delete(pivLocators)
        output.displayInfo("Success: Pivot locators deleted `{}`".format(pivLocators))


def bakeNamespaces():
    """replaces a namespace `:` character with `_` on an object selection list:

        ["rig:polyCube1", "rig:polyCube2"] becomes ["rig_polyCube1", "rig_polyCube2"]
    """
    namehandling.bakeNamespacesSel()


def selectionHighlightList(objs, highlight=True, message=True):
    """Turns on or off selection highlight for an object list.  Attribute selectionChildHighlighting

    If True then highlighting is on, if False then children are not highlighted when selected.

    Maya preferences must be set to "Use Object Highlight Setting":

        Windows > Settings Preferences > preferences > Settings > Selection > Selection Child Highlighting

    :param objs: A list of Maya objects transforms or shapes.
    :type objs: list(str)
    :param highlight: If True then highlighting is on, if False then children are not highlighted when selected.
    :type highlight: bool
    :param message: report a message to the user
    :type message: bool
    """
    for obj in objs:
        cmds.setAttr('{}.selectionChildHighlighting'.format(obj), highlight)
    if message:
        state = "off"
        if highlight:
            state = "on"
        output.displayInfo("Success: Selection highlighting {} `{}`".format(state, objs))


def selectionHighlightSelected(highlight=True):
    """Turns on or off selection highlight for an object list.  Attribute selectionChildHighlighting

    If True then highlighting is on, if False then children are not highlighted when selected.

    See selectionHighlightList() for more information.

    :param highlight: If True then highlighting is on, if False then children are not highlighted when selected.
    :type highlight: bool
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        output.displayWarning("Nothing selected, please select object/s.")
        return
    selectionHighlightList(selObjs, highlight=highlight)


def unlockUnhideAll():
    """Unlocks and unhides everything selected"""
    cmds.select(hierarchy=True, replace=True)
    nodes = cmds.ls(selection=True, long=True)
    cmds.lockNode(nodes, lock=False)
    for node in nodes:
        try:
            cmds.setAttr('{0}.hiddenInOutliner'.format(node), False)
        except:
            pass
        try:
            cmds.setAttr('{0}.visibility'.format(node), True)
        except:
            pass
    for node in cmds.ls(long=True, type='transform'):
        cmds.setAttr('{0}.intermediateObject'.format(node), False)
    for node in cmds.ls(long=True, type='joint'):
        cmds.setAttr('{0}.drawStyle'.format(node), 0)

