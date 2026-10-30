"""The Log at the bottom of the Asset Validation tab.

The add-on's shared object_log.ObjectLog (message lines, a scrolling list of
objects, Select Objects, the count, clicking a row to select it), plus what a
check here has on top: Select Errors, which selects the vertices / edges /
faces the last check found, in Edit Mode.

A check returns a Found, and the tab hands it to LOG.show_found(): one row per
mesh with the problem, or a line saying it found nothing. Anything else (a
fix's result, an error) is a message line. The log is emptied at the start of
every action and when a file is opened.
"""
from __future__ import annotations

from collections import namedtuple

import bpy
import numpy as np
from bpy.types import Operator

from ... import common
from ...object_log import ObjectLog
from ._shared import ELEMENTS, plural


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
# The log
# ---------------------------------------------------------------------------
class ValidationLog(ObjectLog):
    """ObjectLog plus Select Errors, which needs the last Found's indices."""

    def __init__(self):
        super().__init__("av", "Select the meshes to check, then pick a check.")
        # The last check's Found, behind the rows. Runtime only, like the rows.
        self.found = None
        self.classes.append(GS_OT_AV_SelectErrors)

    def clear(self, context):
        self.found = None
        super().clear(context)

    def show_found(self, context, found, op):
        """A check's result, in a log just cleared: a row per mesh it flagged,
        or a line saying it found nothing."""
        self.found = found
        rows = [(item.name, "{} has {}.".format(item.name, item.problem), "warn")
                for item in found.flagged]
        self.show(context, rows, op, found.clean, found.summary())

    def draw_buttons(self, layout):
        layout.operator(GS_OT_AV_SelectErrors.bl_idname)


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


class GS_OT_AV_SelectErrors(Operator):
    bl_idname = "gs_pipeline.av_select_errors"
    bl_label = "Select Errors"
    bl_description = "Select, in Edit Mode, what the last check found on the objects in the log"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        if not LOG.can_select(cls, context):
            return False
        if not LOG.found.element:
            cls.poll_message_set("This check is about whole meshes: use Select Objects.")
            return False
        return True

    def execute(self, context):
        found = LOG.found
        element = found.element
        common.ensure_object_mode(context)
        objects = []
        for item in found.flagged:
            obj = context.view_layer.objects.get(item.name)
            # Indices only mean anything on the mesh as it was checked.
            if (obj is None or not obj.visible_get() or obj.type != 'MESH'
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
        if len(objects) < len(found.flagged):
            self.report({'WARNING'}, "Some objects changed since the check. Run it again for those.")
        return {'FINISHED'}


LOG = ValidationLog()


# ---------------------------------------------------------------------------
# Registration (by the tab, asset_validation/__init__.py)
# ---------------------------------------------------------------------------
def register():
    LOG.register()


def unregister():
    LOG.unregister()
