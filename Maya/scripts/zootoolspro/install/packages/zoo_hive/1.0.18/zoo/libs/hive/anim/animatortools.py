"""Animator Hive Tools Misc

from zoo.libs.hive.anim import animatortools
animatortools.toggleControlPanelNodes()

"""

from maya import cmds

from zoo.libs.hive import api
from zoo.libs.maya.meta import base
from zoo.libs.maya import zapi


def selectControlPanelNodes(add=True):
    """Adds related control panel nodes to the selection, from the Hive rig current selection.
    """
    controlPanelNodes = list()
    for sel in zapi.selected():
        if not sel.hasAttribute(api.constants.ID_ATTR):
            continue
        for m in base.getConnectedMetaNodes(sel):
            if m.mClassType() != api.constants.RIG_LAYER_TYPE:
                continue
            controlPanelNodes.append(str(m.controlPanel()))
    if controlPanelNodes:
        if add:
            cmds.select(controlPanelNodes, add=True)
        else:
            cmds.select(controlPanelNodes, deselect=True)
        return True
    return False


def toggleControlPanelNodesSel():
    """Toggles the selection of the control panel nodes, if they are selected it will deselect them, if they are not
    """
    if not cmds.ls(selection=True):
        return
    controlPanelFound = False
    networkNodes = cmds.ls(selection=True, type="network")
    for node in networkNodes:
        if cmds.attributeQuery(api.constants.ID_ATTR, node=node, exists=True):
            if cmds.getAttr(".".join([node, api.constants.ID_ATTR])) == api.constants.CONTROL_PANEL_TYPE:
                controlPanelFound = True
    if controlPanelFound:
        selectControlPanelNodes(add=False)
    else:
        selectControlPanelNodes(add=True)
