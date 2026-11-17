"""LOD Check (Review > LOD Check): show one LOD of an asset at a time, by hiding the rest.

The CM tab's LOD switching (projects/cm/vehicle.py) for any asset, not just CM
cars, and over LOD0 to LOD6:

    Scope    the collection to work on (empty: the whole scene), and Reload
    LOD      Naming: Numbers (Tree_LOD0) or Letters (Tree_LODA, A being LOD0),
             then All or one LOD
    Log      what the last click did

Shortcuts, with the mouse over a 3D View: Alt + Numpad 0-6 shows that LOD,
Alt + Numpad * shows all, using this tab's Scope and Naming even while
another tab is on screen (the result also goes to the status bar). Numpad
keys alone are Blender's view keys; Alt + Numpad 0-* is free in 3.6, 4.5 and
5.2. The keys are in Preferences > Keymap, where an artist can change them.

An object's LOD is the _LOD<n> / _LOD<X> in its name (the last one; not always
at the end: door_LOD0_handle), else the nearest one above it, so everything
under Tree_LOD1 is LOD1. Objects with no LOD anywhere above them are left as
they are. A LOD past LOD6 / LODG shows only under All. "LOD" may be in any
case; a letter must be a capital, so a word like "_lods" is never read as one.

Hiding is Blender's eye (H / Alt+H) in the current view layer, as in CM. The
choices are on the scene (gs_lod_check), saved with the file like the hiding;
each button's own undo step takes in the hiding it causes.
"""
from __future__ import annotations

import re

import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from bpy.types import Operator, PropertyGroup

from .. import common
from ..panel import Group, Tab

# Property group on the scene, saved with the .blend.
PROP = "gs_lod_check"

# The LODs the buttons offer.
LODS = tuple(range(7))

# Sidebar width (px at 1x) from which the buttons say LOD0 rather than 0.
_LONG_LABELS_WIDTH = 380

LOG = common.ToolLog("Pick a Scope and a Naming, then a LOD.")


# ---------------------------------------------------------------------------
# Reading names
# ---------------------------------------------------------------------------
NUMBERS, LETTERS = "NUMBERS", "LETTERS"

# _LOD0, _LOD0_highlight, _LOD0.001 (as CM reads them).
_TOKENS = {
    NUMBERS: re.compile(r"_(?i:LOD)(\d+)(?=$|[_.])"),
    LETTERS: re.compile(r"_(?i:LOD)([A-Z])(?=$|[_.])"),
}


def _level(naming, token):
    return int(token) if naming == NUMBERS else ord(token) - ord("A")


def lod_of_name(name, naming):
    """The LOD in ``name`` (its last token) as a number, A being 0; None without one."""
    matches = _TOKENS[naming].findall(name)
    return _level(naming, matches[-1]) if matches else None


def lod_label(lod, naming):
    """LOD2 or LODC."""
    return "LOD" + (str(lod) if naming == NUMBERS else chr(ord("A") + lod))


def scan(objects, naming):
    """{object: its LOD, or None} for ``objects``: its own, else the nearest above it."""
    lods = {}

    def lod_of(obj):
        if obj not in lods:
            lod = lod_of_name(obj.name, naming)
            if lod is None and obj.parent is not None:
                lod = lod_of(obj.parent)
            lods[obj] = lod
        return lods[obj]

    return {obj: lod_of(obj) for obj in objects}


def show(lods, choice):
    """Show the LOD ``choice`` (None: all) and hide the other LODs. Objects with no LOD are left alone."""
    for obj, lod in lods.items():
        if lod is None:
            continue
        visible = choice is None or lod == choice
        if obj.hide_get() == visible:
            if not visible:
                obj.select_set(False)       # as H does
            obj.hide_set(not visible)


# ---------------------------------------------------------------------------
# Choices (on the scene)
# ---------------------------------------------------------------------------
_ALL = "ALL"
_LOD_ITEMS = [(_ALL, "All", "Show all LODs")] + [
    (str(lod), str(lod), "Show {} / {} only".format(lod_label(lod, NUMBERS), lod_label(lod, LETTERS)))
    for lod in LODS]

_NAMING_ITEMS = [
    (NUMBERS, "Numbers", "Names end in LOD0, LOD1, LOD2..."),
    (LETTERS, "Letters", "Names end in LODA, LODB, LODC... (LODA is LOD0)"),
]


def _on_lod(props, context):
    _apply(None, context)


def _on_naming(props, context):
    # What's on show follows the new naming, once the panel has hidden anything.
    LOG.clear()
    if props.applied:
        _apply(None, context)


class GS_LODCheck_Props(PropertyGroup):
    scope: PointerProperty(
        type=bpy.types.Collection, name="Scope",
        description="Collection to work on. Empty: whole scene",
    )
    naming: EnumProperty(name="Naming", items=_NAMING_ITEMS, default=NUMBERS, update=_on_naming)
    lod: EnumProperty(name="LOD", items=_LOD_ITEMS, default=_ALL, update=_on_lod)
    # Set once the panel has hidden anything in this file. Reload and Naming
    # then put the choice back on what they find; before that they only read.
    applied: BoolProperty()


def _props(context) -> GS_LODCheck_Props:
    return getattr(context.scene, PROP)


def _apply(op, context):
    """Hide / show the scope by the scene's choices, and log what happened."""
    props = _props(context)
    LOG.clear()
    objects = common.scope_objects(context, props.scope)
    if not objects:
        LOG.add("Nothing in Scope.", "error", op)
        return False
    lods = scan(objects, props.naming)
    if not _any_lod(op, objects, lods, props.naming):
        return False

    choice = None if props.lod == _ALL else int(props.lod)
    show(lods, choice)
    props.applied = True
    if choice is None:
        LOG.add("Showing all LODs.", "ok", op)
    else:
        label = lod_label(choice, props.naming)
        LOG.add("Showing {}.".format(label), "ok", op)
        if choice not in lods.values():
            LOG.add("Nothing at {} in Scope.".format(label), "warn", op)

    past = sum(1 for lod in lods.values() if lod is not None and lod > LODS[-1])
    if past:
        LOG.add("{} past {} show under All only.".format(
            common.plural(past, "object"), lod_label(LODS[-1], props.naming)), "warn", op)
    return True


def _any_lod(op, objects, lods, naming):
    """False, with the reason in the log, when nothing in scope has a LOD in this naming."""
    if any(lod is not None for lod in lods.values()):
        return True
    other = LETTERS if naming == NUMBERS else NUMBERS
    if any(lod is not None for lod in scan(objects, other).values()):
        LOG.add("No {} names in Scope, but there are {} ones: switch Naming to {}.".format(
            lod_label(0, naming), lod_label(0, other), other.title()), "error", op)
    else:
        LOG.add("No LOD names in Scope.", "error", op)
    return False


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------
class GS_OT_LODCheck_Reload(Operator):
    bl_idname = "gs_pipeline.lod_check_reload"
    bl_label = "Reload"
    bl_description = "Re-read names after renaming"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = _props(context)
        if props.applied:
            return {'FINISHED'} if _apply(self, context) else {'CANCELLED'}

        # Nothing hidden by the panel yet: only read.
        LOG.clear()
        objects = common.scope_objects(context, props.scope)
        if not objects:
            LOG.add("Nothing in Scope.", "error", self)
            return {'CANCELLED'}
        lods = scan(objects, props.naming)
        if not _any_lod(self, objects, lods, props.naming):
            return {'CANCELLED'}
        found = sorted(set(lod for lod in lods.values() if lod is not None))
        LOG.add("Found {}.".format(", ".join(lod_label(lod, props.naming) for lod in found)), "ok", self)
        return {'FINISHED'}


class GS_OT_LODCheck_Show(Operator):
    """Run by the shortcuts: the same as pressing a LOD button in the tab."""
    bl_idname = "gs_pipeline.lod_check_show"
    bl_label = "LOD Check: Show LOD"
    bl_options = {'UNDO'}

    lod: StringProperty(name="LOD", description="ALL, or 0 to 6", options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        if properties.lod == _ALL:
            return "Show all LODs (LOD Check)"
        if properties.lod not in _LOD_IDS or context is None or context.scene is None:
            return "Show one LOD (LOD Check)"
        return "Show {} only (LOD Check)".format(lod_label(int(properties.lod), _props(context).naming))

    def execute(self, context):
        if self.lod not in _LOD_IDS:
            self.report({'WARNING'}, "No LOD '{}'. Use ALL or 0 to 6.".format(self.lod))
            return {'CANCELLED'}
        props = _props(context)
        if props.lod != self.lod:
            props.lod = self.lod        # its update shows / hides
        else:
            _apply(None, context)
        LOG.report(self)
        return {'CANCELLED'} if LOG.has_errors() else {'FINISHED'}


# Shortcuts: Alt + Numpad 0-6 for a LOD, Alt + Numpad * for all, in any 3D View.
_LOD_IDS = [identifier for identifier, _, _ in _LOD_ITEMS]
_KEYS = [(_ALL, 'NUMPAD_ASTERIX')] + [(str(lod), 'NUMPAD_{}'.format(lod)) for lod in LODS]
_keymap_items = []


# ---------------------------------------------------------------------------
# Draw (the panel calls it under Review > LOD Check)
# ---------------------------------------------------------------------------
def _section(layout, title, icon):
    box = layout.box()
    box.label(text=title, icon=icon)
    return box


def draw_lod_check(layout, context):
    props = _props(context)

    box = _section(layout, "Scope", 'OUTLINER_COLLECTION')
    row = box.row(align=True)
    row.prop(props, "scope", text="")
    row.operator(GS_OT_LODCheck_Reload.bl_idname, text="", icon='FILE_REFRESH')
    if props.scope is None:
        row = box.row()
        row.active = False
        row.label(text="Empty: whole scene")

    box = _section(layout, "LOD", 'MOD_DECIM')
    row = box.row(align=True)
    row.prop(props, "naming", expand=True)
    long_labels = common.is_wide(context, _LONG_LABELS_WIDTH)
    row = box.row(align=True)
    row.scale_y = 1.3
    row.prop_enum(props, "lod", _ALL)
    for lod in LODS:
        label = lod_label(lod, props.naming)
        row.prop_enum(props, "lod", str(lod), text=label if long_labels else label[3:])

    col = box.column(align=True)
    col.active = False
    # Short enough for a 220 px sidebar.
    col.label(text="Alt+Numpad 0-6: {}-{}".format(
        lod_label(LODS[0], props.naming), lod_label(LODS[-1], props.naming)), icon='INFO')
    col.label(text="Alt+Numpad *: All LODs", icon='BLANK1')

    LOG.draw(layout, context)


# ---------------------------------------------------------------------------
# Group (in review/__init__.py) and registration
# ---------------------------------------------------------------------------
GROUP = Group("LOD_CHECK", "LOD Check", (Tab("LOD Check", draw_lod_check),))

CLASSES = (
    GS_LODCheck_Props,
    GS_OT_LODCheck_Reload,
    GS_OT_LODCheck_Show,
)


def register():
    common.register_classes(CLASSES)
    setattr(bpy.types.Scene, PROP, PointerProperty(type=GS_LODCheck_Props))
    _keymap_items[:] = common.register_keymap_items([
        ("3D View", 'VIEW_3D', GS_OT_LODCheck_Show.bl_idname, key, {"alt": True}, {"lod": lod})
        for lod, key in _KEYS])


def unregister():
    common.unregister_keymap_items(_keymap_items)
    if hasattr(bpy.types.Scene, PROP):
        delattr(bpy.types.Scene, PROP)
    common.unregister_classes(CLASSES)
