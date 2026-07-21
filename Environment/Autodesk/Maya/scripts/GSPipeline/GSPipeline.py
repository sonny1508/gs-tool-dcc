# -*- coding: utf-8 -*-
"""
GSPipeline startup script (Maya 2022+ / Python 3).

Builds the GSPipeline menu and shelf from the explicit layout in tool_config.py.
Groups in the config become (possibly nested) submenus; tools become menu items
and shelf buttons. Nothing is inferred from filenames - the config is the source
of truth for which tools load, their names, and their icons.

Drop this and tool_config.py in a folder on Maya's script path; createMenuAndShelf()
runs automatically at import via executeDeferred().
"""

import os

import maya.cmds as cmds
import maya.utils

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(SCRIPT_DIR, "Icons")
DEFAULT_ICON = "pythonFamily.png"

MENU_LABEL = "GSPipeline"
MENU_ID = "gspipelineMenu"
SHELF_NAME = "GSPipeline"


def _is_group(entry):
    """A group is a (label, children) tuple; a tool is a dict."""
    return isinstance(entry, tuple)


def _resolve_icon(tool):
    icon = tool.get("icon")
    if not icon:
        return DEFAULT_ICON
    icon_path = os.path.join(ICONS_DIR, icon).replace("\\", "/")
    if not os.path.exists(icon_path):
        print("[GSPipeline] Icon not found: {} (using default)".format(icon))
        return DEFAULT_ICON
    return icon_path


def _build_command(tool):
    """Command string that launches a tool.

    Everything routes through gspipeline_telemetry.launch(), which records the
    launch and then dispatches. Keeping the dispatch logic in that module rather
    than inlined here means there is one place to instrument, and the baked
    command string stays short and path-independent.

    repr() is used for the literals so labels containing quotes or backslashes
    can't break the generated source.
    """
    return "import gspipeline_telemetry; gspipeline_telemetry.launch({0}, {1})".format(
        repr(tool["script"]), repr(tool["name"])
    )


def _build_menu(entries, parent):
    """Recursively populate a menu from config entries."""
    if not entries:
        cmds.menuItem(parent=parent, label="(empty)", enable=False)
        return
    for entry in entries:
        if _is_group(entry):
            label, children = entry
            submenu = cmds.menuItem(parent=parent, label=label, subMenu=True, tearOff=True)
            _build_menu(children, submenu)
        else:
            cmds.menuItem(
                parent=parent,
                label=entry["name"],
                command=_build_command(entry),
                # The command is a Python string, so say so explicitly rather
                # than relying on the default source type.
                sourceType="python",
            )


def _build_shelf(entries, shelf, first=True):
    """Recursively add shelf buttons, with a separator at every group boundary.

    `first` tracks whether the next button is the very first on the shelf, so we
    don't emit a leading separator. Returns the updated `first` flag.
    """
    for entry in entries:
        if _is_group(entry):
            children = entry[1]
            if not first:
                cmds.separator(parent=shelf, style="shelf", horizontal=False)
            first = _build_shelf(children, shelf, first)
        else:
            cmds.shelfButton(
                parent=shelf,
                label=entry["name"],
                annotation=entry["name"],
                image=_resolve_icon(entry),
                command=_build_command(entry),
                sourceType="python",
                width=35,
                height=35,
            )
            first = False
    return first


def _load_config():
    """Import tool_config from beside this script and return its TOOLS list."""
    import importlib
    import tool_config
    importlib.reload(tool_config)  # pick up edits without restarting Maya
    return tool_config.TOOLS


def createMenuAndShelf():
    try:
        config = _load_config()

        # ---- Menu ----
        if cmds.menu(MENU_ID, exists=True):
            cmds.deleteUI(MENU_ID, menu=True)
        menu = cmds.menu(MENU_ID, label=MENU_LABEL, parent="MayaWindow", tearOff=True)
        _build_menu(config, menu)

        # ---- Shelf ----
        if cmds.shelfLayout(SHELF_NAME, exists=True):
            cmds.deleteUI(SHELF_NAME, layout=True)
        shelf = cmds.shelfLayout(SHELF_NAME, parent="ShelfLayout")
        _build_shelf(config, shelf)

        print("[GSPipeline] Menu and shelf created.")

    except Exception as e:
        cmds.warning("[GSPipeline] Failed to create menu and shelf: {}".format(e))
        import traceback
        traceback.print_exc()


maya.utils.executeDeferred(createMenuAndShelf)
