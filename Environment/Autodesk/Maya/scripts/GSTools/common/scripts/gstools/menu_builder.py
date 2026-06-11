"""
GSTools - Menu builder

Builds the "GSTools" main-window menu from menu_config.MENU. Every menu item's
command is a Python callable that routes through gstools.launch(id, "menu"), so
the menu carries no tool logic and every click is telemetered.
"""
import logging

import maya.cmds as cmds
import maya.mel as mel

import gstools
from gstools import menu_config

logging.basicConfig()
logger = logging.getLogger("gstools.menu_builder")
logger.setLevel(logging.INFO)

MENU_NAME = "gsToolsMenu"
MENU_LABEL = "GSTools"


def _main_window():
    return mel.eval('$gsTmpMainWin = $gMainWindow')


def _menu_command(tool_id):
    """Build the click callback for a menu item.

    Maya invokes a menuItem's Python `-command` with an extra boolean arg (the
    item's state), so the callback must accept and ignore it; otherwise it would
    reach launch() as a 3rd positional arg and raise a TypeError.
    """
    def _run(*_args):
        return gstools.launch(tool_id, "menu")
    return _run


def _add_item(item):
    """Create a single menuItem (or divider) for `item`."""
    if item.get("divider"):
        if item.get("label"):
            cmds.menuItem(divider=True, dividerLabel=item["label"])
        else:
            cmds.menuItem(divider=True)
        return

    label = item["label"]
    if item.get("type") == "special" and item.get("action") == "version":
        label = "%s: %s" % (label, gstools.PACKAGE_VERSION)

    kwargs = {
        "label": label,
        "annotation": item.get("annotation", ""),
        "command": _menu_command(item["id"]),
    }
    if item.get("icon"):
        kwargs["image"] = item["icon"]
    if item.get("enabled") is False:
        kwargs["enable"] = False
    cmds.menuItem(**kwargs)


def build_menu():
    """(Re)build the GSTools menu. Returns the menu name."""
    if cmds.menu(MENU_NAME, exists=True):
        cmds.deleteUI(MENU_NAME, menu=True)

    cmds.menu(MENU_NAME, label=MENU_LABEL, parent=_main_window(), tearOff=True)

    for category in menu_config.MENU:
        cmds.menuItem(subMenu=True, tearOff=True,
                      label=category["label"], image=category.get("icon", ""))
        for item in category.get("items", []):
            _add_item(item)
        cmds.setParent("..", menu=True)

    logger.info("GSTools menu built (%s).", MENU_LABEL)
    return MENU_NAME
