"""Helpers shared by the Asset Validation sections."""
from __future__ import annotations

import contextlib
import functools
from collections import namedtuple

import bpy
import numpy as np

from ... import common

# One button: operator name (gs_pipeline.av_<name>), label, tooltip, and the
# function it runs. run(context) does the work and returns (log level, message),
# or a log.Found when the button is a check; it raises ValidationError when the
# artist has to change something first.
Tool = namedtuple("Tool", "name label description run")

# Mesh collection holding each kind of element a check can find.
ELEMENTS = {'VERT': "vertices", 'EDGE': "edges", 'FACE': "polygons"}


class ValidationError(Exception):
    """Something the artist can put right (usually the selection): logged without a traceback."""


plural = common.plural      # the section modules import it from here


def selected_meshes(context, minimum=1):
    """The selected mesh objects, one of them active. Raises if there are fewer than ``minimum``."""
    meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
    if len(meshes) < minimum:
        raise ValidationError("Select a mesh first." if minimum == 1
                              else "Select at least {} meshes.".format(minimum))
    if context.view_layer.objects.active not in meshes:
        context.view_layer.objects.active = meshes[0]
    return meshes


def save_selection(context):
    return context.view_layer.objects.active, list(context.selected_objects)


def _alive(obj):
    try:
        return obj is not None and obj.name in bpy.data.objects
    except ReferenceError:      # removed since it was saved
        return False


def restore_selection(context, saved):
    """Put back a selection from save_selection(), in Object Mode."""
    active, selected = saved
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in selected:
        if _alive(obj):
            obj.select_set(True)
    if _alive(active):
        context.view_layer.objects.active = active


def clear_custom_normals(context, meshes):
    """Blender's Clear Custom Split Normals Data on each of ``meshes``, in Object
    Mode. Returns how many had some. Changes the active object: callers put the
    selection back."""
    cleared = 0
    for obj in meshes:
        if obj.data.has_custom_normals:     # False for a mesh shared with one just cleared
            context.view_layer.objects.active = obj
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
            cleared += 1
    return cleared


# ----------------------------------------------------------------------------
# Checks leave the scene as it was
# ----------------------------------------------------------------------------
def _component_state(mesh):
    """The select and hide flags of every vertex, edge and face of ``mesh`` (Object Mode)."""
    state = []
    for name in ELEMENTS.values():
        items = getattr(mesh, name)
        for flag in ("select", "hide"):
            values = np.empty(len(items), dtype=bool)
            items.foreach_get(flag, values)
            state.append((name, flag, values))
    return mesh, state


def _restore_component_state(saved):
    mesh, state = saved
    for name, flag, values in state:
        items = getattr(mesh, name)
        if len(items) == len(values):
            items.foreach_set(flag, values)


@contextlib.contextmanager
def _scene_kept(context):
    """Object Mode while a check runs, then everything put back as it was: the
    selected objects, the mode, and the selected and hidden vertices, edges and
    faces of the selected meshes."""
    active = context.view_layer.objects.active
    mode = active.mode if active is not None else 'OBJECT'
    selection = save_selection(context)
    tool_settings = context.tool_settings
    select_mode = tuple(tool_settings.mesh_select_mode)
    common.ensure_object_mode(context)      # writes Edit Mode changes into the meshes
    objects = set(context.selected_objects)
    if active is not None:
        objects.add(active)
    components = [_component_state(mesh)
                  for mesh in {obj.data for obj in objects if obj.type == 'MESH'}]
    try:
        yield
    finally:
        common.ensure_object_mode(context)
        for saved in components:
            _restore_component_state(saved)
        restore_selection(context, selection)
        tool_settings.mesh_select_mode = select_mode
        if mode != 'OBJECT' and _alive(active):
            try:
                bpy.ops.object.mode_set(mode=mode)
            except RuntimeError:        # can't go back (e.g. now hidden): stay in Object Mode
                pass


def check(run):
    """Make ``run`` a check: it reports what it found and leaves the scene as it
    was, whatever it selected or hid along the way to find it."""
    @functools.wraps(run)
    def checked(context):
        with _scene_kept(context):
            return run(context)
    return checked
