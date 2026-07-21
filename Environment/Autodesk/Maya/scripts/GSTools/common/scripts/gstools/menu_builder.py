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


def _shelf_command(tool_id):
    """Build the `-dragMenuCommand` callback for a menu item.

    When an artist Ctrl+Shift+drags a menu item to their shelf, Maya's
    menuItemToShelf copies the item's `-command` onto the new shelfButton *as
    text* - but our command is a live Python closure, which has no source, so the
    query returns its repr ("<function ... _run at 0x...>") and the shelf button
    is dead.

    `-dragMenuCommand` is Maya's sanctioned hook for exactly this: for a
    python-sourceType item, Maya *calls* this callback at drag time and bakes its
    return value into the shelf as the button's command string. We return a
    self-contained launch line:
      - it depends only on `gstools` being importable, and launch() runs
        ensure_paths() itself, so it self-bootstraps in a fresh session;
      - tool_id is a stable key, so the button survives module renames/refactors;
      - source="shelf" keeps menu vs shelf launches distinguishable in telemetry.
    """
    def _drag(*_args):
        return 'import gstools; gstools.launch("%s", "shelf")' % tool_id
    return _drag


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
        # dragMenuCommand feeds Ctrl+Shift+drag-to-shelf; sourceType applies to
        # both callbacks and MUST be "python" or Maya treats the dragged text as
        # MEL. See _shelf_command for the full rationale.
        "dragMenuCommand": _shelf_command(item["id"]),
        "sourceType": "python",
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
