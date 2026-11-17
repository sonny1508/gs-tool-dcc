# -*- coding: utf-8 -*-
"""
GSPipeline startup script (Maya 2022+ / Python 3).

Builds the GSPipeline menu and shelf from the explicit layout in tool_config.py.
Groups in the config become (possibly nested) submenus; tools become menu items
and shelf buttons, and a tool with a "hotkey" gets that shortcut. Nothing is
inferred from filenames - the config is the source of truth for which tools
load, their names, their icons and their shortcuts.

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

# Shared with GSTools' own hotkeys (GS_Spread's Alt+S), so studio shortcuts sit
# in one set. Maya_Default is locked, so it is cloned into this one when current.
HOTKEY_SET = "GSTools"
HOTKEY_CATEGORY = "GSPipeline"


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


def _build_command(script):
    """Command string that launches a tool script.

    Python files are run with __name__ == '__main__' so tools guarded by
    `if __name__ == "__main__":` fire, while tools that build their UI at
    module level also work. MEL files are sourced.
    """
    abs_path = os.path.join(SCRIPT_DIR, script).replace("\\", "/")
    if abs_path.lower().endswith(".mel"):
        return "import maya.mel as mel; mel.eval('source \"{0}\";')".format(abs_path)
    return (
        "with open(r'{0}', encoding='utf-8') as _f: "
        "exec(compile(_f.read(), r'{0}', 'exec'), "
        "{{'__name__': '__main__', '__file__': r'{0}'}})"
    ).format(abs_path)


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
                command=_build_command(entry["script"]),
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
                command=_build_command(entry["script"]),
                width=35,
                height=35,
            )
            first = False
    return first


def _tools(entries):
    """Every tool dict in the config, depth first."""
    for entry in entries:
        if _is_group(entry):
            for tool in _tools(entry[1]):
                yield tool
        else:
            yield entry


def _parse_hotkey(text):
    """'Ctrl+Shift+G' -> (key, ctrl, alt). Shift is an upper-case key, as in Maya's own set."""
    parts = [part.strip().lower() for part in text.split("+")]
    key = parts[-1]
    modifiers = set(parts[:-1])
    unknown = modifiers - {"ctrl", "alt", "shift"}
    if not key or unknown:
        raise ValueError("can't read hotkey '{}'".format(text))
    if "shift" in modifiers:
        key = key.upper()
    return key, "ctrl" in modifiers, "alt" in modifiers


def _ensure_editable_hotkey_set():
    current = cmds.hotkeySet(query=True, current=True)
    if current and current != "Maya_Default":
        return current
    if not cmds.hotkeySet(HOTKEY_SET, exists=True):
        cmds.hotkeySet(HOTKEY_SET, source=current or "Maya_Default", current=True)
    else:
        cmds.hotkeySet(HOTKEY_SET, edit=True, current=True)
    return HOTKEY_SET


def _bind_hotkey(tool):
    key, ctrl, alt = _parse_hotkey(tool["hotkey"])
    ident = "GSPipeline_" + "".join(c if c.isalnum() else "_" for c in tool["name"])
    name_command = ident + "NameCommand"
    annotation = tool["name"]

    # The set first: the clash check below reads the current set.
    hotkey_set = _ensure_editable_hotkey_set()

    # Leave a key the artist has bound to something else alone. `hotkey -query
    # -name` reads this exact chord in the current set. (The first version asked
    # hotkeyCheck instead, and Ctrl+Shift+G never got bound - most likely it
    # answered for Ctrl+G, Group.)
    taken = cmds.hotkey(key, query=True, name=True, ctrlModifier=ctrl, altModifier=alt)
    if taken and not taken.startswith(name_command):
        cmds.warning("[GSPipeline] {} is already bound to '{}' in hotkey set '{}'; {} has no "
                     "shortcut.".format(tool["hotkey"], taken, hotkey_set, tool["name"]))
        return

    # default=True keeps it out of the user's saved runtime commands, so it is
    # made fresh each session; on a menu rebuild within the session it already exists.
    if not cmds.runTimeCommand(ident, query=True, exists=True):
        cmds.runTimeCommand(ident, command=_build_command(tool["script"]), commandLanguage="python",
                            category=HOTKEY_CATEGORY, annotation=annotation, default=True)
    # `hotkey -name` binds a nameCommand, which wraps the runtime command. Bind
    # whatever name Maya actually gave it.
    name_command = cmds.nameCommand(name_command, annotation=annotation, command=ident,
                                    sourceType="mel") or name_command
    cmds.hotkey(keyShortcut=key, ctrlModifier=ctrl, altModifier=alt, name=name_command)
    print("[GSPipeline] {} bound to {} (hotkey set '{}').".format(
        tool["name"], tool["hotkey"], hotkey_set))


def _bind_hotkeys(config):
    for tool in _tools(config):
        if not tool.get("hotkey"):
            continue
        try:
            _bind_hotkey(tool)
        except Exception as e:
            cmds.warning("[GSPipeline] Could not bind {} for {}: {}".format(
                tool["hotkey"], tool["name"], e))


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

        # ---- Hotkeys ---- (each failure is warned about on its own)
        _bind_hotkeys(config)

    except Exception as e:
        cmds.warning("[GSPipeline] Failed to create menu and shelf: {}".format(e))
        import traceback
        traceback.print_exc()


maya.utils.executeDeferred(createMenuAndShelf)
