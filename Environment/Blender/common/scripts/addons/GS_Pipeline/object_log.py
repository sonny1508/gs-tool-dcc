"""The Log a check-style tool shows at the bottom of its tab: message lines,
then a list of the objects with a problem.

    Log
      Found ...                       message lines (common.ToolLog)
      +--------------------------+
      | ! SM_Door has n-gons.    |    one row per problem, scrolling;
      | ! SM_Hood has n-gons.    |    clicking a row selects its object
      +--------------------------+
      [ Select Objects ] [...]        a subclass's own buttons go beside it
      2 objects in the log

A tool makes one at module level and registers it with its classes:

    LOG = ObjectLog("cm", "Pick a Scope, then press Check Names.")

    register():    ... LOG.register()
    unregister():  LOG.unregister() ...

    LOG.clear(context)                          at the start of an action
    LOG.add(message, level, op)                 a message line
    LOG.show(context, rows, op, clean)          a check's result
    LOG.draw(layout, context, columns)          the Log box

A tool that needs more subclasses it, as Asset Validation does for Select
Errors: add its operators to ``classes``, draw them in draw_buttons(), and
override clear() to drop what it keeps.

Each log has its own list on the window manager (gs_<id>_log, runtime only,
emptied when a file is opened) and its own Select Objects and row-click
operators (gs_pipeline.<id>_select_objects, gs_pipeline.<id>_select_log_row),
made here. The row type and the UIList are shared: the add-on registers them
once (register() below).

Rows name their objects rather than hold them, so the log outlives undo; a
renamed or deleted object is reported, not crashed on.
"""
from __future__ import annotations

import bpy
from bpy.props import CollectionProperty, IntProperty, StringProperty
from bpy.types import Operator, PropertyGroup, UIList

from . import common

# Rows the list shows before it scrolls. The artist can drag it taller.
_ROWS = 8


class GS_PG_LogRow(PropertyGroup):
    # name (every PropertyGroup has one): the object the row is about, "" when
    # there is none (something a check looked for and didn't find). The list's
    # filter searches it.
    text: StringProperty()                  # what the row says, also its tooltip
    level: StringProperty(default="warn")   # common.LOG_ICONS level


class GS_UL_ObjectLog(UIList):
    """One row per problem the last check found."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_prop, index):
        row = layout.row()
        row.alert = item.level == "error"
        row.label(text=item.text, icon=common.LOG_ICONS.get(item.level, 'INFO'))


# ---------------------------------------------------------------------------
# The operators each log gets (made per log in ObjectLog.__init__)
# ---------------------------------------------------------------------------
class _SelectObjects:
    bl_label = "Select Objects"
    bl_description = "Select every object in the log"
    bl_options = {'UNDO'}
    object_log = None

    @classmethod
    def poll(cls, context):
        return cls.object_log.can_select(cls, context)

    def execute(self, context):
        return self.object_log.select_objects(self, context)


class _SelectRow:
    """Run by clicking a row of the list (see ObjectLog._row_clicked)."""
    bl_label = "Select Object"
    bl_description = "Select the object in this row of the log"
    bl_options = {'UNDO', 'INTERNAL'}
    object_log = None

    def execute(self, context):
        return self.object_log.select_row(self, context, self.index)


class ObjectLog:
    """Message lines and a list of objects, as drawn at the bottom of a tab."""

    def __init__(self, ident, placeholder):
        self.id = ident
        self.messages = common.ToolLog(placeholder)
        self.prop = "gs_{}_log".format(ident)               # rows, on the window manager
        self.index_prop = self.prop + "_index"              # the clicked row
        self.checked = False        # a check has filled the list (maybe with nothing) since clear()
        self._counts = (0, 0)       # (objects, rows without one): kept for draw()
        self._on_load = None

        prefix = "GS_OT_{}_".format(ident.upper())
        self.select_objects_op = type(prefix + "SelectObjects", (_SelectObjects, Operator), {
            "bl_idname": "gs_pipeline.{}_select_objects".format(ident),
            "object_log": self,
        })
        self.select_row_op = type(prefix + "SelectLogRow", (_SelectRow, Operator), {
            "bl_idname": "gs_pipeline.{}_select_log_row".format(ident),
            "object_log": self,
            "__annotations__": {"index": IntProperty(options={'HIDDEN', 'SKIP_SAVE'})},
        })
        # A subclass adds its own operators here, before register().
        self.classes = [self.select_objects_op, self.select_row_op]

    # -- Filling it ---------------------------------------------------------
    def rows(self, context):
        return getattr(context.window_manager, self.prop)

    def add(self, message, level="info", op=None):
        """A message line."""
        self.messages.add(message, level, op)

    def clear_messages(self):
        """Clear the message lines only, keeping the list (for actions that don't check)."""
        self.messages.clear()

    def clear(self, context):
        """Empty the log: message lines and list."""
        self.messages.clear()
        self.checked = False
        self._counts = (0, 0)
        wm = context.window_manager
        getattr(wm, self.prop).clear()
        setattr(wm, self.index_prop, -1)
        common.redraw_view3d()

    def show(self, context, rows, op, clean, summary=None):
        """A check's result, in a log just cleared.

        ``rows`` are (object name, text, level): one list row each, name "" when
        there is no object to select. With none, the log says ``clean``
        instead. ``summary`` is the status bar line (default: the count under
        the list).
        """
        self.checked = True
        items = self.rows(context)
        for name, text, level in rows:
            item = items.add()
            item.name = name
            item.text = text
            item.level = level
        names = {item.name for item in items if item.name}
        self._counts = (len(names), sum(1 for item in items if not item.name))
        if not len(items):
            self.add(clean, "ok", op)
            return
        op.report({'WARNING'}, summary or self.count_text() + ".")
        common.redraw_view3d()

    def count_text(self):
        """'3 objects in the log' (', 2 missing' for rows with no object)."""
        objects, missing = self._counts
        text = "{} in the log".format(common.plural(objects, "object"))
        return text + ", {} missing".format(missing) if missing else text

    # -- Selecting ----------------------------------------------------------
    def can_select(self, op_class, context):
        """Poll for Select Objects: greys it out, with the reason."""
        if not self.checked:
            op_class.poll_message_set("Run a check first.")
            return False
        if not self._counts[0]:
            op_class.poll_message_set("Nothing to select.")
            return False
        return True

    def select_objects(self, op, context):
        layer = context.view_layer.objects
        names = list(dict.fromkeys(item.name for item in self.rows(context) if item.name))
        objects = [obj for obj in (layer.get(name) for name in names)
                   if obj is not None and obj.visible_get()]
        if not objects:
            op.report({'WARNING'}, "Objects are hidden or deleted.")
            return {'CANCELLED'}
        common.ensure_object_mode(context)
        common.select_only(context, objects)
        if len(objects) < len(names):
            op.report({'WARNING'}, "Some objects are hidden or deleted.")
        return {'FINISHED'}

    def select_row(self, op, context, index):
        rows = self.rows(context)
        if not 0 <= index < len(rows) or not rows[index].name:
            return {'CANCELLED'}
        name = rows[index].name
        obj = context.view_layer.objects.get(name)
        if obj is None:
            op.report({'WARNING'}, "{} is in an excluded collection.".format(name)
                      if name in bpy.data.objects else "{} not found.".format(name))
            return {'CANCELLED'}
        common.ensure_object_mode(context)
        if obj.visible_get():
            common.select_only(context, [obj])
            return {'FINISHED'}
        # Hidden: make it active, so it can still be renamed, and say why it can't be seen.
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = obj
        op.report({'WARNING'}, "{} is hidden.".format(name))
        return {'FINISHED'}

    def _row_clicked(self, wm, context):
        """A click on a row makes it the list's active row: select its object.

        Through the operator, so the click is an undo step like a click in the
        Outliner, and a missing object is reported in the status bar.
        """
        index = getattr(wm, self.index_prop)
        if 0 <= index < len(getattr(wm, self.prop)):
            run = getattr(bpy.ops.gs_pipeline, "{}_select_log_row".format(self.id))
            run('EXEC_DEFAULT', True, index=index)

    # -- Draw ---------------------------------------------------------------
    def draw_buttons(self, layout):
        """A subclass's own buttons, beside Select Objects."""

    def draw(self, layout, context, columns=1):
        """The Log box: message lines, the list, its buttons, how many objects it holds."""
        wm = context.window_manager
        box = layout.box()
        box.label(text="Log")
        if self.messages.lines or not len(self.rows(context)):
            self.messages.draw_lines(box, context)
        box.template_list("GS_UL_ObjectLog", self.prop, wm, self.prop, wm, self.index_prop,
                          item_dyntip_propname="text", rows=_ROWS, maxrows=_ROWS)
        grid = box.grid_flow(row_major=True, columns=columns, even_columns=True, align=True)
        grid.operator(self.select_objects_op.bl_idname)
        self.draw_buttons(grid)
        info = box.row()
        info.active = False
        info.label(text=self.count_text())

    # -- Registration (by the tool) -------------------------------------------
    def register(self):
        common.register_classes(self.classes)

        # bpy.props wants plain functions, not bound methods.
        def on_row_clicked(wm, context):
            self._row_clicked(wm, context)

        @bpy.app.handlers.persistent
        def clear_on_load(_dummy):
            self.clear(bpy.context)     # the rows named the last file's objects

        wm = bpy.types.WindowManager
        setattr(wm, self.prop, CollectionProperty(type=GS_PG_LogRow))
        setattr(wm, self.index_prop, IntProperty(default=-1, update=on_row_clicked))
        self._on_load = clear_on_load
        bpy.app.handlers.load_post.append(clear_on_load)

    def unregister(self):
        if self._on_load in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(self._on_load)
        self._on_load = None
        for attr in (self.index_prop, self.prop):
            if hasattr(bpy.types.WindowManager, attr):
                delattr(bpy.types.WindowManager, attr)
        common.unregister_classes(self.classes)


# ---------------------------------------------------------------------------
# Registration of the shared classes (by the add-on, before the tools)
# ---------------------------------------------------------------------------
CLASSES = (
    GS_PG_LogRow,
    GS_UL_ObjectLog,
)


def register():
    common.register_classes(CLASSES)


def unregister():
    common.unregister_classes(CLASSES)
