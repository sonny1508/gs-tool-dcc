"""Shared helpers for the GS Pipeline addon.

Tool modules import from here instead of copying code between them:

  * Scene helpers: selection, Object Mode, auto smooth across 3.6 / 4.1+,
    folding duplicate materials an import created.
  * ToolLog: the short result log a tool draws at the bottom of its tab.
  * Remembered preferences: the Blender counterpart of the Maya tools' optionVars.
  * Registration: classes and tool modules, in order and back.

Only what more than one tool uses belongs here; a project's own helpers live in
its package (e.g. projects/hw3/payloads.py).
"""
from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import textwrap

import bpy

_LOG = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Scene helpers
# ----------------------------------------------------------------------------
def select_only(context, objects):
    """Select exactly ``objects`` (in Object Mode) and make the first one active."""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    if objects:
        context.view_layer.objects.active = objects[0]


def ensure_object_mode(context):
    if context.mode != 'OBJECT' and context.view_layer.objects.active is not None:
        bpy.ops.object.mode_set(mode='OBJECT')


def legacy_auto_smooth():
    """True on Blender 3.6, where auto smooth is a mesh setting (4.1+ replaced it with a modifier)."""
    return "use_auto_smooth" in bpy.types.Mesh.bl_rna.properties


def set_auto_smooth(context, objects, angle):
    """Blender's own Object > Shade Auto Smooth, so the result matches the menu entry exactly.

    Leaves ``objects`` selected, the first one active.
    """
    select_only(context, objects)
    if legacy_auto_smooth():
        # 3.6: Shade Auto Smooth is Shade Smooth with the mesh's auto smooth turned on.
        bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=angle)
    else:
        # 4.1+: adds (or updates) the "Smooth by Angle" modifier.
        bpy.ops.object.shade_auto_smooth(angle=angle)


def redraw_view3d():
    """Redraw every 3D View, so a tab picks up state changed outside its own draw."""
    wm = bpy.context.window_manager
    if wm is None:
        return
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def _ui_scale(context):
    # 0 when Blender runs without a window (background mode).
    return context.preferences.system.ui_scale or 1.0


def is_wide(context, width):
    """True when the sidebar is at least ``width`` px wide (at 1x UI scale).

    Blender can't hold the sidebar at a minimum width, so tabs use this to put
    settings side by side when there is room and stack them when there isn't.
    """
    region = context.region
    if region is None:
        return True
    return region.width >= width * _ui_scale(context)


# Blender's rename-on-collision suffix: "Material" -> "Material.001", "Material.002"...
_DUPLICATE_SUFFIX = re.compile(r"^(?P<base>.+)\.\d{3,}$")


def merge_duplicate_materials(new_materials):
    """Fold the 'name.001'-style copies an import just made back into the existing 'name'.

    ``new_materials`` are the materials the import created. Only those are
    folded, and only into a material that was already in the file: two the
    import brought in together ('Steel', 'Steel.001') are both kept. Returns
    how many were merged.
    """
    new_materials = list(new_materials)
    new = set(new_materials)
    merged = 0
    for material in new_materials:
        match = _DUPLICATE_SUFFIX.match(material.name)
        if not match:
            continue
        original = bpy.data.materials.get(match.group("base"))
        if original is None or original in new:
            continue
        material.user_remap(original)
        bpy.data.materials.remove(material)
        merged += 1
    return merged


@contextlib.contextmanager
def wait_cursor(context):
    """Show the wait cursor while a long action runs."""
    window = context.window
    if window is not None:
        window.cursor_set('WAIT')
    try:
        yield
    finally:
        if window is not None:
            window.cursor_set('DEFAULT')


# ----------------------------------------------------------------------------
# Result log
# ----------------------------------------------------------------------------
# Log levels, as in the Maya tools: ok = done as asked, warn = done but look at
# this, error = nothing done (the message says why). Blender can't colour label
# text, so the icon carries the level; error lines also draw in the alert colour.
LOG_ICONS = {"ok": 'CHECKMARK', "warn": 'ERROR', "error": 'CANCEL', "info": 'INFO'}
_REPORT_TYPES = {"warn": {'WARNING'}, "error": {'WARNING'}}

# Rough width of one character of UI text, in px at 1x scale, for wrapping.
_CHAR_WIDTH = 6.5


def plural(count, word, plural_word=None):
    """'1 part', '3 parts' (or ``plural_word``), for log lines."""
    return "{:,} {}".format(count, word if count == 1 else plural_word or word + "s")


class ToolLog:
    """The few result lines a tool shows at the bottom of its tab.

    Runtime only: empty in each new Blender session, cleared at the start of
    each action. Lines also go to the status bar through the operator, as a
    warning for warn / error (an ERROR report would open a pop-up).
    """

    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.lines = []

    def clear(self):
        self.lines.clear()

    def add(self, message, level="info", op=None):
        self.lines.append((level, message))
        if op is not None:
            op.report(_REPORT_TYPES.get(level, {'INFO'}), message)
        redraw_view3d()

    def draw(self, layout, context):
        box = layout.box()
        box.label(text="Log")
        self.draw_lines(box, context)

    def draw_lines(self, layout, context):
        """The lines (or the placeholder) without the box, for a log that draws more in it."""
        col = layout.column(align=True)
        region = context.region
        scale = _ui_scale(context)
        width =max(16, int(((region.width if region else 300) - 70 * scale) / (_CHAR_WIDTH * scale)))
        if not self.lines:
            col.enabled = False
            for part in textwrap.wrap(self.placeholder, width):
                col.label(text=part)
            return
        for level, message in self.lines:
            icon = LOG_ICONS.get(level, 'INFO')
            for part in textwrap.wrap(message, width) or [""]:
                row = col.row()
                row.alert = level == "error"
                row.label(text=part, icon=icon)
                icon = 'BLANK1'  # continuation lines line up under the text


# ----------------------------------------------------------------------------
# Remembered preferences
# ----------------------------------------------------------------------------
# Preferences that last between sessions (the Maya tools keep these in
# optionVars), in one JSON file in this Blender version's config folder. Keys
# are prefixed by the tool. Values a project spec defines don't belong here.
_PREFS_FILE = "gs_pipeline_prefs.json"
_prefs = None


def _prefs_path():
    return os.path.join(bpy.utils.user_resource('CONFIG'), _PREFS_FILE)


def _load_prefs():
    global _prefs
    if _prefs is None:
        try:
            with open(_prefs_path(), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            _prefs = data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            _prefs = {}
    return _prefs


def pref_get(key, default):
    value = _load_prefs().get(key, default)
    return value if isinstance(value, type(default)) else default


def pref_set(key, value):
    prefs = _load_prefs()
    if prefs.get(key) == value:
        return
    prefs[key] = value
    path = _prefs_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(prefs, fh, indent=2, sort_keys=True)
    except OSError as exc:
        _LOG.warning("GS Pipeline: could not save preferences to %s: %s", path, exc)


# ----------------------------------------------------------------------------
# Registration
# ----------------------------------------------------------------------------
def register_classes(classes):
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_classes(classes):
    """Unregister in reverse order. A class that never registered is skipped,
    so a half-finished register() can still be undone."""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass


def register_modules(modules):
    """register() each tool module (or package), in order."""
    for module in modules:
        module.register()


def unregister_modules(modules):
    for module in reversed(modules):
        module.unregister()
