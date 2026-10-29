"""MGP27 Kerb Height Checker: the sidebar tab, its settings and its buttons.

Select the kerbs (and the track, if the foot of the kerb is on a separate
mesh) and Check. Check selects the kerb-top vertices whose step is off spec;
Fix Selection moves the selected vertices onto it. How a step is measured and
fixed is in kerb_measure.py.
"""
from __future__ import annotations

import traceback

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty
from bpy.types import Operator, PropertyGroup

from ... import common
from ...panel import Tab
from .kerb_measure import KerbError, Settings, check_selection, fix_selection, select_vertices


# MGP27 kerb spec, in cm. Runtime-only settings: every Blender session starts
# on these (and Reset puts them back), so a value changed for one check never
# quietly sticks.
KERB_HEIGHT = 2.0
TOLERANCE = 0.05
SEARCH_RADIUS = 15.0
IGNORE_BELOW = 0.2


# Preferences remembered between sessions (not the spec values). Same names as
# the Maya tool's optionVars.
_PREF_PREFIX = "gs_mgp27_kerb_"

# Property group lives on the window manager (runtime only, never saved in a file).
PROP = "gs_mgp27_kerb"

# Sidebar widths (px at 1x): two number fields to a row, and buttons beside
# their label / the two actions side by side. Below these, things stack.
_TWO_COLUMN_WIDTH = 360
_ROOMY_WIDTH = 260

LOG = common.ToolLog("Select the kerbs, then Check Selection.")


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
def _remembered(name, default):
    """get / set for a property backed by a remembered preference.

    Module-level functions, not lambdas in the class body: Blender evaluates
    the (deferred) annotations where module names don't reach a lambda's body.
    """
    key = _PREF_PREFIX + name
    kind = type(default)

    def get(self):
        return kind(common.pref_get(key, int(default)))

    def set(self, value):
        common.pref_set(key, int(value))

    return get, set


_up_get, _up_set = _remembered("up", 2)
_ground_get, _ground_set = _remembered("ground_only", False)
_relative_get, _relative_set = _remembered("fix_relative", 1)


class GS_MGP27_KerbProps(PropertyGroup):
    # Remembered between sessions. The enum numbers are the values the Maya
    # tool stores: up 1 = Y, 2 = Z; fix_relative 1 = Relative, 0 = Absolute.
    up: EnumProperty(
        name="Up Axis",
        description="The axis kerb height is measured along",
        items=[("Z", "Z", "Kerb height is measured along Z", 2),
               ("Y", "Y", "Kerb height is measured along Y", 1)],
        get=_up_get, set=_up_set,
    )
    ground_only: BoolProperty(
        name="Measure along the ground",
        description="Ignore height when measuring the radius",
        get=_ground_get, set=_ground_set,
    )
    mode: EnumProperty(
        name="Mode",
        items=[("RELATIVE", "Relative",
                "Move the selection as one, so its highest vertex lands on the kerb height. "
                "Separate pieces move separately", 1),
               ("ABSOLUTE", "Absolute", "Move every selected vertex to exactly the kerb height", 0)],
        get=_relative_get, set=_relative_set,
    )

    # The MGP27 spec, in cm. Not remembered (see KERB_HEIGHT).
    height: FloatProperty(
        name="Height", description=f"Kerb height. MGP27 spec: {KERB_HEIGHT:g} cm",
        default=KERB_HEIGHT, min=0.1, max=20.0, step=10, precision=2,
    )
    tolerance: FloatProperty(
        name="Tolerance ±", description="How far off the height a kerb can be and still pass",
        default=TOLERANCE, min=0.001, max=1.0, step=1, precision=3,
    )
    radius: FloatProperty(
        name="Radius", description="How far from each vertex to look for the bottom of the kerb",
        default=SEARCH_RADIUS, min=1.0, max=100.0, step=100, precision=1,
    )
    ignore_below: FloatProperty(
        name="Ignore Under",
        description="Smaller drops count as track slope, not a kerb. "
                    "Raise it if sloped track gets flagged",
        default=IGNORE_BELOW, min=0.01, max=5.0, step=5, precision=2,
    )

    # Which off-spec vertices Check selects.
    select_high: BoolProperty(name="Too High", description="Select kerbs higher than spec", default=True)
    select_low: BoolProperty(name="Too Low", description="Select kerbs lower than spec", default=True)

    def settings(self):
        return Settings(height=self.height,
                        tolerance=self.tolerance,
                        radius=self.radius,
                        ignore_below=self.ignore_below,
                        up=1 if self.up == 'Y' else 2,
                        ground_only=self.ground_only)


def _props(context) -> GS_MGP27_KerbProps:
    return getattr(context.window_manager, PROP)


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------
def _plural(count, word, plural=None):
    return "{:,} {}".format(count, word if count == 1 else plural or word + "s")


def _vertices(count):
    return _plural(count, "vertex", "vertices")


def _run(op, context, function, *args):
    """Call ``function`` with a wait cursor; log its failure instead of raising."""
    try:
        with common.wait_cursor(context):
            return function(*args)
    except KerbError as exc:
        LOG.add(str(exc), "error", op)
    except Exception as exc:            # keep the panel alive, keep the traceback
        traceback.print_exc()
        LOG.add("Something went wrong: {}. Details in the System Console.".format(exc), "error", op)
    return None


class GS_OT_MGP27_KerbCheck(Operator):
    bl_idname = "gs_pipeline.mgp27_kerb_check"
    bl_label = "Check Selection"
    bl_description = ("Check the selected kerbs and select the vertices that are off spec. "
                      "If the kerb sits on a separate track mesh, select that too")
    bl_options = {'UNDO'}

    def execute(self, context):
        props = _props(context)
        select_high, select_low = props.select_high, props.select_low
        LOG.clear()
        if not (select_high or select_low):
            LOG.add("Tick Too High, Too Low or both.", "error", self)
            return {'CANCELLED'}
        settings = props.settings()
        result = _run(self, context, check_selection, context, settings, select_high, select_low)
        if result is None:
            return {'CANCELLED'}

        LOG.add("Checked {}, {} up.".format(_vertices(result.checked),
                                            "Y" if settings.up == 1 else "Z"), "info", self)
        if not result.on_step:
            LOG.add("No kerb steps found. Check the Up Axis, or select the track mesh too.",
                    "warn", self)
            return {'FINISHED'}
        if not (result.high or result.low):
            LOG.add("All on spec.", "ok", self)
            return {'FINISHED'}

        found = ", ".join(part for part in (
            "{:,} too high".format(len(result.high)) if result.high else "",
            "{:,} too low".format(len(result.low)) if result.low else "") if part)
        selected = (len(result.high) if select_high else 0) + (len(result.low) if select_low else 0)
        if selected == len(result.high) + len(result.low):
            LOG.add("{} - selected.".format(found), "warn", self)
        elif selected:
            LOG.add("{}. Selected the {:,} {}.".format(
                found, selected, "too high" if select_high else "too low"), "warn", self)
        else:
            LOG.add("{}. Nothing selected - tick {} to select them.".format(
                found, "Too Low" if select_high else "Too High"), "warn", self)
        return {'FINISHED'}


class GS_OT_MGP27_KerbFix(Operator):
    bl_idname = "gs_pipeline.mgp27_kerb_fix"
    bl_label = "Fix Selection"
    bl_description = "Move the selected vertices onto the kerb height, as set by Mode. Ctrl+Z undoes it"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = _props(context)
        settings = props.settings()
        relative = props.mode == 'RELATIVE'
        LOG.clear()
        result = _run(self, context, fix_selection, context, settings, relative)
        if result is None:
            return {'CANCELLED'}

        if result.moved and not relative:
            LOG.add("Fixed {} to {:g} cm.".format(_vertices(result.moved), settings.height), "ok", self)
        elif result.moved and len(result.offsets) == 1:
            offset = result.offsets[0]
            LOG.add("Moved {} {} {:.2f} cm. The highest is now at {:g} cm.".format(
                _vertices(result.moved), "up" if offset > 0 else "down", abs(offset),
                settings.height), "ok", self)
        elif result.moved:
            LOG.add("Moved {} in {:,} pieces. The highest of each is now at {:g} cm.".format(
                _vertices(result.moved), len(result.offsets), settings.height), "ok", self)
        if result.exact:
            LOG.add("{} already on spec.".format(_vertices(result.exact)), "info", self)
        if result.skipped:
            select_vertices(context, result.skipped)
            LOG.add("Couldn't fix {}: no kerb step found. They're selected.".format(
                _vertices(len(result.skipped))), "warn", self)
        return {'FINISHED'}


class GS_OT_MGP27_KerbResetSpec(Operator):
    bl_idname = "gs_pipeline.mgp27_kerb_reset_spec"
    bl_label = "Reset to Spec"
    bl_description = "Put Height, Tolerance, Radius and Ignore Under back to the MGP27 spec"

    def execute(self, context):
        props = _props(context)
        props.height = KERB_HEIGHT
        props.tolerance = TOLERANCE
        props.radius = SEARCH_RADIUS
        props.ignore_below = IGNORE_BELOW
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Draw (the panel calls it under Projects > MGP27)
# ---------------------------------------------------------------------------
def _scene_unit(scene):
    units = scene.unit_settings
    if units.system == 'NONE':
        name = "None"
    else:
        name = units.length_unit.replace("_", " ").title()
    if abs(units.scale_length - 1.0) > 1e-6:
        name += " × {:g}".format(units.scale_length)
    return name


def _section(layout, title, icon):
    box = layout.box()
    header = box.row()
    header.label(text=title, icon=icon)
    return box, header


def _labelled(layout, label, beside=True):
    """A label and a row for its buttons: beside it, or under it when the sidebar is narrow."""
    if beside:
        split = layout.split(factor=0.3)
        split.label(text=label)
        return split.row(align=True)
    col = layout.column(align=True)
    col.label(text=label)
    return col.row(align=True)


def draw_kerb_checker(layout, context):
    props = _props(context)
    # Number fields pair up when there is room for two; buttons sit beside
    # their label down to a narrower sidebar.
    columns = 2 if common.is_wide(context, _TWO_COLUMN_WIDTH) else 1
    roomy = common.is_wide(context, _ROOMY_WIDTH)

    box, _ = _section(layout, "Scene", 'SCENE_DATA')
    grid = box.grid_flow(row_major=True, columns=columns, even_columns=True)
    _labelled(grid, "Up Axis").prop(props, "up", expand=True)
    _labelled(grid, "Unit").label(text=_scene_unit(context.scene))

    box, header = _section(layout, "Kerb Spec (cm)", 'DRIVER_DISTANCE')
    header.operator("gs_pipeline.mgp27_kerb_reset_spec", text="", icon='LOOP_BACK', emboss=False)
    grid = box.grid_flow(row_major=True, columns=columns, even_columns=True)
    grid.prop(props, "height")
    grid.prop(props, "tolerance")

    box, _ = _section(layout, "Search (cm)", 'VIEWZOOM')
    grid = box.grid_flow(row_major=True, columns=columns, even_columns=True)
    grid.prop(props, "radius")
    grid.prop(props, "ignore_below")
    box.prop(props, "ground_only")

    # At the bottom, next to the buttons they change.
    box, _ = _section(layout, "Operations", 'TOOL_SETTINGS')
    _labelled(box, "Mode", roomy).prop(props, "mode", expand=True)
    select = _labelled(box, "Select", roomy)
    select.prop(props, "select_high", toggle=True)
    select.prop(props, "select_low", toggle=True)

    actions = layout.row() if roomy else layout.column()
    actions.scale_y = 1.6
    actions.operator("gs_pipeline.mgp27_kerb_check", text="Check Selection")
    actions.operator("gs_pipeline.mgp27_kerb_fix", text="Fix Selection")

    LOG.draw(layout, context)


# ============================================================================
# Tab (in projects/mgp27/__init__.py) and registration
# ============================================================================
TAB = Tab("Kerb Height Checker", draw_kerb_checker)

CLASSES = (
    GS_MGP27_KerbProps,
    GS_OT_MGP27_KerbCheck,
    GS_OT_MGP27_KerbFix,
    GS_OT_MGP27_KerbResetSpec,
)


def register():
    common.register_classes(CLASSES)
    setattr(bpy.types.WindowManager, PROP, PointerProperty(type=GS_MGP27_KerbProps))


def unregister():
    if hasattr(bpy.types.WindowManager, PROP):
        delattr(bpy.types.WindowManager, PROP)
    common.unregister_classes(CLASSES)
