"""CM tab (Projects > CM): choose what's on show in a CM car file, and check its names.

    Scope         the collection to work on (empty: the whole scene), Reload,
                  and Check Names, which artists run first
    LOD           All, LOD0, LOD1, LOD2
    Custom Parts  show the default or a custom version of each part that has
                  them: every part at once, or one at a time in the list
    Log           object_log.ObjectLog: what the last button did, what Check
                  Names found

What counts as a LOD or a custom part, and what a part replaces, is in
variants.py; the naming rules are in names.py and name_check.py.

The choices (Scope, LOD, each part's version) live on the scene, so they are
saved with the file, like the hiding they cause. The custom parts differ from
file to file, so the buttons and list for them are read from the scene when
a file opens, on Reload and on every LOD / part click.
"""
from __future__ import annotations

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import Operator, PropertyGroup, UIList

from ... import common
from ...object_log import ObjectLog
from ...panel import Tab
from . import name_check, names, variants

# Property group on the scene, saved with the .blend.
PROP = "gs_cm"

# Rows the part list shows before it scrolls.
_PART_ROWS = 10

LOG = ObjectLog("cm", "Pick a Scope, then press Check Names.")


# ---------------------------------------------------------------------------
# Choices (on the scene)
# ---------------------------------------------------------------------------
_ALL = "ALL"
_LOD_ITEMS = [(_ALL, "All", "Show all LODs")] + [
    (str(lod), "LOD{}".format(lod), "Show LOD{} only".format(lod)) for lod in names.LODS]


def _on_scope(props, context):
    _read(context)


def _on_lod(props, context):
    # The button's own undo step (a scene property) takes in the hiding too.
    LOG.clear_messages()
    found = _read(context)
    if _nothing_in_scope(None, found):
        return
    LOG.add("Showing all LODs." if props.lod == _ALL else "Showing LOD{}.".format(props.lod), "ok")
    _show(None, context, found)


class GS_CM_Choice(PropertyGroup):
    # name (every PropertyGroup has one): the part, as variants.Slot.key (anchor_hood)
    part: StringProperty()      # the custom part on show, "" for the default


class GS_CM_Props(PropertyGroup):
    scope: PointerProperty(
        type=bpy.types.Collection, name="Scope",
        description="Collection to work on. Empty: whole scene",
        update=_on_scope,
    )
    lod: EnumProperty(name="LOD", items=_LOD_ITEMS, default=_ALL, update=_on_lod)
    choices: CollectionProperty(type=GS_CM_Choice)
    # Set once the panel has hidden anything in this file. Reload then puts
    # the choices back on what it finds; before that it only reads.
    applied: BoolProperty()


def _props(context) -> GS_CM_Props:
    return getattr(context.scene, PROP)


def _lod(props):
    """The LOD on show as a number, variants.ALL_LODS for All."""
    return variants.ALL_LODS if props.lod == _ALL else int(props.lod)


def _choices(props):
    """Part choices as {slot key: part letter}, the default when missing."""
    return {choice.name: choice.part for choice in props.choices}


def _set_choice(props, key, part):
    choice = props.choices.get(key)
    if choice is None:
        choice = props.choices.add()
        choice.name = key
    choice.part = part


# ---------------------------------------------------------------------------
# The part list (on the window manager, read from the scene)
# ---------------------------------------------------------------------------
# Enum identifier for the default version. Part letters are letters.
_DEFAULT_ID = "DEFAULT"

# Dropdown items per (has default, parts), kept for the session: Blender
# doesn't copy the strings an enum items callback returns, so they must stay alive.
_items_cache = {}


def _version_items(has_default, parts):
    key = (has_default, parts)
    items = _items_cache.get(key)
    if items is None:
        items = [(_DEFAULT_ID, "Default" if has_default else "None", "", 0)]
        for number, part in enumerate((p for p in parts.split(",") if p), 1):
            items.append((part, "Part " + part, "", number))
        _items_cache[key] = items
    return items


def _version_enum_items(row, context):
    return _version_items(row.has_default, row.parts)


def _version_get(row):
    choice = getattr(bpy.context.scene, PROP).choices.get(row.name)
    chosen = choice.part if choice is not None and choice.part else _DEFAULT_ID
    for identifier, _, _, number in _version_items(row.has_default, row.parts):
        if identifier == chosen:
            return number
    return 0        # the chosen part is gone (renamed): the default


def _version_set(row, value):
    for identifier, _, _, number in _version_items(row.has_default, row.parts):
        if number == value:
            part = variants.DEFAULT if identifier == _DEFAULT_ID else identifier
            _set_choice(getattr(bpy.context.scene, PROP), row.name, part)
            return


def _version_changed(row, context):
    # Through the operator, so the change is an undo step.
    bpy.ops.gs_pipeline.cm_show_part('EXEC_DEFAULT', True, slot=row.name)


class GS_CM_PartRow(PropertyGroup):
    # name: the part, as variants.Slot.key (anchor_hood)
    label: StringProperty()         # Hood
    parts: StringProperty()         # its custom parts, "A,B,C"
    has_default: BoolProperty()     # False for a part with no default version
    version: EnumProperty(
        name="Version", description="Part version to show",
        items=_version_enum_items, get=_version_get, set=_version_set, update=_version_changed,
    )


class GS_UL_CM_Parts(UIList):
    """One row per part with custom versions: its name and which version is on show."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_prop, index):
        split = layout.split(factor=0.5)
        split.label(text=item.label)
        split.prop(item, "version", text="")


# The list's active row: always none. Its rows aren't selectable, so a click
# on one does nothing and nothing highlights.
def _no_active_row(_wm):
    return -1


def _ignore_row_click(_wm, _value):
    pass


def _read(context):
    """Scan the scope and refresh the part list. Returns the scan."""
    found = variants.scan(context, _props(context).scope)
    rows = context.window_manager.gs_cm_parts
    rows.clear()
    for slot in found.sorted_slots():
        row = rows.add()
        row.name = slot.key
        row.label = slot.label
        row.parts = ",".join(sorted(slot.parts))
        row.has_default = slot.has_default
    common.redraw_view3d()
    return found


@bpy.app.handlers.persistent
def _read_on_load(_dummy):
    context = bpy.context
    if context.scene is None or context.view_layer is None:
        return
    _read(context)


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------
def _show(op, context, found):
    """Hide / show the scope by the scene's choices; log a chosen part with no
    version at the LOD on show."""
    props = _props(context)
    lod = _lod(props)
    choices = _choices(props)
    variants.show(found, lod, choices)
    props.applied = True
    missing = variants.missing_lod(found, lod, choices)
    if len(missing) == 1:
        LOG.add("{} part {} has no LOD{}.".format(missing[0].label, choices[missing[0].key], lod),
                "warn", op)
    elif missing:
        LOG.add("{} have no LOD{}.".format(common.plural(len(missing), "chosen part"), lod), "warn", op)


def _nothing_in_scope(op, found):
    if found.objects:
        return False
    LOG.add("Nothing in Scope.", "error", op)
    return True


class GS_OT_CM_Reload(Operator):
    bl_idname = "gs_pipeline.cm_reload"
    bl_label = "Reload"
    bl_description = "Re-read names after renaming"
    bl_options = {'UNDO'}

    def execute(self, context):
        LOG.clear_messages()
        found = _read(context)
        if _nothing_in_scope(self, found):
            return {'CANCELLED'}
        if found.slots:
            LOG.add("Found {}.".format(common.plural(len(found.slots), "custom part")), "ok", self)
        else:
            LOG.add("No custom parts found.", "ok", self)
        if _props(context).applied:
            _show(self, context, found)
        return {'FINISHED'}


class GS_OT_CM_SetParts(Operator):
    bl_idname = "gs_pipeline.cm_set_parts"
    bl_label = "Show Part"
    bl_options = {'UNDO'}

    part: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})      # "" for the default

    @classmethod
    def description(cls, context, properties):
        if not properties.part:
            return "Show all default parts"
        return "Show part {} where there is one".format(properties.part)

    def execute(self, context):
        props = _props(context)
        LOG.clear_messages()
        found = _read(context)
        if _nothing_in_scope(self, found):
            return {'CANCELLED'}
        slots = [slot for slot in found.slots.values() if not self.part or self.part in slot.parts]
        if not slots:
            LOG.add("No part {} found. Press Reload.".format(self.part)
                    if self.part else "No custom parts found.", "error", self)
            return {'CANCELLED'}
        for slot in slots:
            _set_choice(props, slot.key, self.part)
        LOG.add("Showing part {}.".format(self.part) if self.part else "Showing default parts.", "ok", self)
        _show(self, context, found)
        return {'FINISHED'}


class GS_OT_CM_ShowPart(Operator):
    """Run by changing a part's version in the list (see _version_changed)."""
    bl_idname = "gs_pipeline.cm_show_part"
    bl_label = "Show Part Version"
    bl_options = {'UNDO', 'INTERNAL'}

    slot: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        props = _props(context)
        LOG.clear_messages()
        # Scan without rebuilding the list: this runs from one of its rows.
        found = variants.scan(context, props.scope)
        if _nothing_in_scope(self, found):
            return {'CANCELLED'}
        slot = found.slots.get(self.slot)
        part = _choices(props).get(self.slot, variants.DEFAULT)
        if slot is not None:
            version = "part " + part if part else "default" if slot.has_default else "none"
            LOG.add("{}: {}.".format(slot.label, version), "ok", self)
        _show(self, context, found)
        return {'FINISHED'}


class GS_OT_CM_CheckNames(Operator):
    bl_idname = "gs_pipeline.cm_check_names"
    bl_label = "Check Names"
    bl_description = "Check object names. Run this first"

    def execute(self, context):
        LOG.clear(context)
        objects = variants.scope_objects(context, _props(context).scope, view_layer_only=False)
        if not objects:
            LOG.add("Nothing in Scope.", "error", self)
            return {'CANCELLED'}
        LOG.show(context, name_check.check(objects), self, "All names OK.")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Draw (the panel calls it under Projects > CM)
# ---------------------------------------------------------------------------
def _section(layout, title, icon):
    box = layout.box()
    box.label(text=title, icon=icon)
    return box


def _greyed(layout, text):
    row = layout.row()
    row.active = False
    row.label(text=text)


def _parts_button(row, rows, choices, part, text):
    """A global part button, pressed when every part it applies to shows it."""
    keys = [r.name for r in rows if not part or part in r.parts.split(",")]
    pressed = bool(keys) and all(choices.get(key, variants.DEFAULT) == part for key in keys)
    op = row.operator(GS_OT_CM_SetParts.bl_idname, text=text, depress=pressed)
    op.part = part


def draw_vehicle(layout, context):
    props = _props(context)
    wm = context.window_manager

    box = _section(layout, "Scope", 'OUTLINER_COLLECTION')
    row = box.row(align=True)
    row.prop(props, "scope", text="")
    row.operator(GS_OT_CM_Reload.bl_idname, text="", icon='FILE_REFRESH')
    if props.scope is None:
        _greyed(box, "Empty: whole scene")
    row = box.row()
    row.scale_y = 1.4
    row.operator(GS_OT_CM_CheckNames.bl_idname, icon='SORTALPHA')

    box = _section(layout, "LOD", 'MOD_DECIM')
    row = box.row(align=True)
    row.scale_y = 1.3
    row.prop(props, "lod", expand=True)

    box = _section(layout, "Custom Parts", 'PRESET')
    rows = wm.gs_cm_parts
    if len(rows):
        choices = _choices(props)
        letters = sorted({part for r in rows for part in r.parts.split(",") if part})
        row = box.row(align=True)
        row.scale_y = 1.3
        _parts_button(row, rows, choices, variants.DEFAULT, "Default")
        for letter in letters:
            _parts_button(row, rows, choices, letter, letter)
        box.template_list("GS_UL_CM_Parts", "gs_cm_parts", wm, "gs_cm_parts", wm, "gs_cm_parts_index",
                          rows=min(len(rows), _PART_ROWS), maxrows=_PART_ROWS)
    else:
        _greyed(box, "No custom parts found. Press Reload.")

    LOG.draw(layout, context)


# ============================================================================
# Tab (in projects/cm/__init__.py) and registration
# ============================================================================
TAB = Tab("Vehicle", draw_vehicle)

CLASSES = (
    GS_CM_Choice,
    GS_CM_Props,
    GS_CM_PartRow,
    GS_UL_CM_Parts,
    GS_OT_CM_Reload,
    GS_OT_CM_SetParts,
    GS_OT_CM_ShowPart,
    GS_OT_CM_CheckNames,
)


def register():
    common.register_classes(CLASSES)
    setattr(bpy.types.Scene, PROP, PointerProperty(type=GS_CM_Props))
    bpy.types.WindowManager.gs_cm_parts = CollectionProperty(type=GS_CM_PartRow)
    bpy.types.WindowManager.gs_cm_parts_index = IntProperty(get=_no_active_row, set=_ignore_row_click)
    if _read_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_read_on_load)
    LOG.register()


def unregister():
    LOG.unregister()
    if _read_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_read_on_load)
    for attr in ("gs_cm_parts_index", "gs_cm_parts"):
        if hasattr(bpy.types.WindowManager, attr):
            delattr(bpy.types.WindowManager, attr)
    if hasattr(bpy.types.Scene, PROP):
        delattr(bpy.types.Scene, PROP)
    common.unregister_classes(CLASSES)
