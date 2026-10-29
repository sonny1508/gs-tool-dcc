"""The Log at the bottom of the Asset Validation tab.

A check returns a Found, and the tab hands it to show(): one row per mesh with
the problem, in a list that scrolls, with the number of objects under it.
Clicking a row selects that object. Select Objects selects every object in the
list; Select Errors, for a check that finds vertices / edges / faces, selects
those in Edit Mode.

Anything else (a fix's result, an error, a check that found nothing) is a short
message line above the list.

Rows name their objects rather than hold them, so the log outlives undo. It is
emptied at the start of every action and when a file is opened.
"""
from __future__ import annotations

from collections import namedtuple

import bpy
import numpy as np
from bpy.props import CollectionProperty, IntProperty, StringProperty
from bpy.types import Operator, PropertyGroup, UIList

from ... import common
from ._shared import ELEMENTS, plural

# Rows the list shows before it scrolls. The artist can drag it taller.
_ROWS = 8

MESSAGES = common.ToolLog("Select the meshes to check, then pick a check.")

# The last check's Found, behind the rows: Select Errors needs its indices.
# Runtime only, like the rows.
_found = None


# ---------------------------------------------------------------------------
# What a check found
# ---------------------------------------------------------------------------
# One mesh a check flagged: its object's name, what it has ("overlapping UVs"),
# and for a check that finds elements, their indices and how many of that
# element the mesh had when checked.
Flagged = namedtuple("Flagged", "name problem indices count")


class Found:
    """What a check found: the meshes with the problem and, on each, the
    vertices / edges / faces (``element``) that have it.

    ``element`` is None when the problem is the whole mesh (no UVs, custom
    normals): there is nothing inside it to select.
    """

    def __init__(self, problem, element=None, clean=None):
        self.problem = problem
        self.element = element
        self.clean = clean or "No {} found.".format(problem)
        self.flagged = []

    def add(self, obj, indices=None, problem=None):
        """Flag ``obj``. A check that finds elements flags it only when ``indices`` holds any."""
        count = 0
        if self.element:
            if indices is None or not len(indices):
                return
            indices = np.asarray(indices, dtype=np.int64)
            count = len(getattr(obj.data, ELEMENTS[self.element]))
        self.flagged.append(Flagged(obj.name, problem or self.problem, indices, count))

    def summary(self):
        """One line for the status bar, e.g. "Overlapping UVs on 3 meshes"."""
        return "{}{} on {}.".format(self.problem[:1].upper(), self.problem[1:],
                                    plural(len(self.flagged), "mesh", "meshes"))


# ---------------------------------------------------------------------------
# Filling the log (called by the tab's operators)
# ---------------------------------------------------------------------------
def clear(context):
    """Empty the log: messages, rows and what the last check found."""
    global _found
    _found = None
    MESSAGES.clear()
    wm = context.window_manager
    wm.gs_av_log.clear()
    wm.gs_av_log_index = -1
    common.redraw_view3d()


def add(message, level="info", op=None):
    """A message line above the list."""
    MESSAGES.add(message, level, op)


def show(context, found, op):
    """A check's result, in a log just cleared: a row per mesh it flagged, or a
    line saying it found nothing."""
    global _found
    _found = found
    if not found.flagged:
        MESSAGES.add(found.clean, "ok", op)
        return
    rows = context.window_manager.gs_av_log
    for item in found.flagged:
        row = rows.add()
        row.name = item.name
        row.text = "{} has {}.".format(item.name, item.problem)
    op.report({'WARNING'}, found.summary())
    common.redraw_view3d()


@bpy.app.handlers.persistent
def _clear_on_load(_dummy):
    clear(bpy.context)      # the rows named the last file's objects


# ---------------------------------------------------------------------------
# Selecting what's in the log
# ---------------------------------------------------------------------------
def _scene_object(context, name):
    """The object called ``name`` if it is still in this view layer and visible, else None."""
    obj = context.view_layer.objects.get(name)
    return obj if obj is not None and obj.visible_get() else None


def _select_elements(mesh, element, indices):
    """Select exactly the ``element``s at ``indices`` of ``mesh``, in Object Mode.

    Entering Edit Mode and setting the select mode to ``element`` then shows
    them, with their vertices and edges.
    """
    for name in ELEMENTS.values():
        items = getattr(mesh, name)
        items.foreach_set("select", np.zeros(len(items), dtype=bool))
    items = getattr(mesh, ELEMENTS[element])
    flags = np.zeros(len(items), dtype=bool)
    flags[indices] = True
    items.foreach_set("select", flags)


def _can_select(cls, elements):
    """Poll: is there something in the log to select? Greys the button out, with the reason."""
    if _found is None:
        cls.poll_message_set("Run a check first.")
        return False
    if not _found.flagged:
        cls.poll_message_set("The last check found nothing.")
        return False
    if elements and not _found.element:
        cls.poll_message_set("This check is about whole meshes: use Select Objects.")
        return False
    return True


class GS_OT_AV_SelectObjects(Operator):
    bl_idname = "gs_pipeline.av_select_objects"
    bl_label = "Select Objects"
    bl_description = "Select every object in the log"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return _can_select(cls, elements=False)

    def execute(self, context):
        objects = [obj for obj in (_scene_object(context, item.name) for item in _found.flagged)
                   if obj is not None]
        if not objects:
            self.report({'WARNING'}, "The objects in the log were deleted or hidden.")
            return {'CANCELLED'}
        common.ensure_object_mode(context)
        common.select_only(context, objects)
        if len(objects) < len(_found.flagged):
            self.report({'WARNING'}, "Some objects in the log were deleted or hidden.")
        return {'FINISHED'}


class GS_OT_AV_SelectErrors(Operator):
    bl_idname = "gs_pipeline.av_select_errors"
    bl_label = "Select Errors"
    bl_description = "Select, in Edit Mode, what the last check found on the objects in the log"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return _can_select(cls, elements=True)

    def execute(self, context):
        element = _found.element
        common.ensure_object_mode(context)
        objects = []
        for item in _found.flagged:
            obj = _scene_object(context, item.name)
            # Indices only mean anything on the mesh as it was checked.
            if (obj is None or obj.type != 'MESH'
                    or len(getattr(obj.data, ELEMENTS[element])) != item.count):
                continue
            _select_elements(obj.data, element, item.indices)
            objects.append(obj)
        if not objects:
            self.report({'WARNING'}, "The objects changed since the check. Run it again.")
            return {'CANCELLED'}
        common.select_only(context, objects)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type=element)
        if len(objects) < len(_found.flagged):
            self.report({'WARNING'}, "Some objects changed since the check. Run it again for those.")
        return {'FINISHED'}


class GS_OT_AV_SelectLogRow(Operator):
    """Run by clicking a row of the list (see _on_row_clicked)."""
    bl_idname = "gs_pipeline.av_select_log_row"
    bl_label = "Select Object"
    bl_description = "Select the object in this row of the log"
    bl_options = {'UNDO', 'INTERNAL'}

    index: IntProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        if _found is None or not 0 <= self.index < len(_found.flagged):
            return {'CANCELLED'}
        name = _found.flagged[self.index].name
        obj = _scene_object(context, name)
        if obj is None:
            self.report({'WARNING'}, "{} was deleted or hidden.".format(name))
            return {'CANCELLED'}
        common.ensure_object_mode(context)
        common.select_only(context, [obj])
        return {'FINISHED'}


def _on_row_clicked(wm, context):
    """A click on a row makes it the list's active row: select its object.

    Through the operator, so the click is an undo step like a click in the
    Outliner, and a missing object is reported in the status bar.
    """
    index = wm.gs_av_log_index
    if 0 <= index < len(wm.gs_av_log):
        bpy.ops.gs_pipeline.av_select_log_row('EXEC_DEFAULT', True, index=index)


# ---------------------------------------------------------------------------
# Draw
# ---------------------------------------------------------------------------
class GS_PG_AV_LogRow(PropertyGroup):
    # name (every PropertyGroup has one) is the object's name: the list's filter searches it.
    text: StringProperty()      # what the row says, also its tooltip


class GS_UL_AV_Log(UIList):
    """One row per object the last check flagged."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_prop, index):
        layout.label(text=item.text, icon=common.LOG_ICONS["warn"])


def draw(layout, context, columns):
    """The Log box: message lines, the list, its buttons, and how many objects it holds."""
    wm = context.window_manager
    count = len(wm.gs_av_log)
    box = layout.box()
    box.label(text="Log")
    if MESSAGES.lines or not count:
        MESSAGES.draw_lines(box, context)
    box.template_list("GS_UL_AV_Log", "gs_av_log", wm, "gs_av_log", wm, "gs_av_log_index",
                      item_dyntip_propname="text", rows=_ROWS, maxrows=_ROWS)
    grid = box.grid_flow(row_major=True, columns=columns, even_columns=True, align=True)
    grid.operator(GS_OT_AV_SelectObjects.bl_idname)
    grid.operator(GS_OT_AV_SelectErrors.bl_idname)
    info = box.row()
    info.active = False
    info.label(text="{} in the log".format(plural(count, "object")))


# ---------------------------------------------------------------------------
# Registration (by the tab, asset_validation/__init__.py)
# ---------------------------------------------------------------------------
CLASSES = (
    GS_PG_AV_LogRow,
    GS_UL_AV_Log,
    GS_OT_AV_SelectObjects,
    GS_OT_AV_SelectErrors,
    GS_OT_AV_SelectLogRow,
)


def register():
    common.register_classes(CLASSES)
    bpy.types.WindowManager.gs_av_log = CollectionProperty(type=GS_PG_AV_LogRow)
    bpy.types.WindowManager.gs_av_log_index = IntProperty(default=-1, update=_on_row_clicked)
    if _clear_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_clear_on_load)


def unregister():
    if _clear_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_clear_on_load)
    for attr in ("gs_av_log_index", "gs_av_log"):
        if hasattr(bpy.types.WindowManager, attr):
            delattr(bpy.types.WindowManager, attr)
    common.unregister_classes(CLASSES)
