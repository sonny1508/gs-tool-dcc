"""Asset Validation - Normals checks and fixes."""
from __future__ import annotations

import math

import bpy

from ... import common
from ._shared import (
    Tool,
    ValidationError,
    check,
    clear_custom_normals,
    restore_selection,
    save_selection,
    selected_meshes,
)
from .log import Found

TITLE = "Normals"
ICON = 'NORMALS_FACE'

_AUTO_SMOOTH_ANGLE = math.radians(30.0)


def recalculate_normals(context):
    """Point every face outward, then go back to the selection and mode you were in."""
    meshes = selected_meshes(context)
    saved = save_selection(context)
    mode = context.view_layer.objects.active.mode
    common.ensure_object_mode(context)
    common.select_only(context, meshes)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    restore_selection(context, saved)
    if mode != 'OBJECT' and context.view_layer.objects.active is not None:
        bpy.ops.object.mode_set(mode=mode)
    return "ok", "Normals recalculated."


def smooth_shading(context):
    """Clear custom normals and shade smooth with 30 degree auto smooth."""
    meshes = selected_meshes(context)
    saved = save_selection(context)
    common.ensure_object_mode(context)
    clear_custom_normals(context, meshes)
    common.set_auto_smooth(context, meshes, _AUTO_SMOOTH_ANGLE)
    restore_selection(context, saved)
    return "ok", "Shaded smooth, auto smooth at 30°."


def face_orientation(context):
    """Show or hide the Face Orientation overlay in this 3D View."""
    space = context.space_data
    if space is None or space.type != 'VIEW_3D':
        raise ValidationError("Use this from the 3D View sidebar.")
    overlay = space.overlay
    overlay.show_face_orientation = not overlay.show_face_orientation
    return "info", "Face orientation {}.".format("shown" if overlay.show_face_orientation else "hidden")


@check
def custom_normals(context):
    """Selected meshes with Custom Split Normals Data (Mesh properties > Geometry Data)."""
    found = Found("custom split normals")
    for obj in selected_meshes(context):
        if obj.data.has_custom_normals:
            found.add(obj)
    return found


TOOLS = (
    Tool("recalculate_normals", "Recalculate Normals",
         "Make the normals of the selected meshes point outside", recalculate_normals),
    Tool("smooth_shading", "Apply Smooth Shading",
         "Clear custom normals and shade smooth with 30° auto smooth", smooth_shading),
    Tool("face_orientation", "Toggle Face Orientation",
         "Show or hide the Face Orientation overlay", face_orientation),
    Tool("custom_normals", "Check Custom Normals Data",
         "Find selected meshes with Custom Split Normals Data", custom_normals),
)
