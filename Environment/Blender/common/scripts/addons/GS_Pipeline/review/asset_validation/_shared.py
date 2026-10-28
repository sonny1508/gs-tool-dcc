"""Helpers shared by the Asset Validation sections."""
from __future__ import annotations

from collections import namedtuple

import bpy

# One button: operator name (gs_pipeline.av_<name>), label, tooltip, and the
# function it runs. run(context) does the work and returns (log level, message);
# it raises ValidationError when the artist has to change something first.
Tool = namedtuple("Tool", "name label description run")


class ValidationError(Exception):
    """Something the artist can put right (usually the selection): logged without a traceback."""


def plural(count, word, plural_word=None):
    return "{:,} {}".format(count, word if count == 1 else plural_word or word + "s")


def selected_meshes(context, minimum=1):
    """The selected mesh objects, one of them active. Raises if there are fewer than ``minimum``."""
    meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
    if len(meshes) < minimum:
        raise ValidationError("Select a mesh first." if minimum == 1
                              else "Select at least {} meshes.".format(minimum))
    if context.view_layer.objects.active not in meshes:
        context.view_layer.objects.active = meshes[0]
    return meshes


def clear_component_selection():
    """Deselect every vertex, edge and face of the selected meshes, ending in Object Mode."""
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


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


def flagged(count, what, select_mode=None):
    """Result of a check that selected what it found.

    Found something: Edit Mode, so the selection shows. Found nothing: Object
    Mode. ``what`` is (singular, plural), e.g. ("loose edge", "loose edges").
    """
    if count:
        bpy.ops.object.mode_set(mode='EDIT')
        if select_mode:
            bpy.ops.mesh.select_mode(type=select_mode)
        return "warn", "{} - selected.".format(plural(count, *what))
    bpy.ops.object.mode_set(mode='OBJECT')
    return "ok", "No {} found.".format(what[1])
