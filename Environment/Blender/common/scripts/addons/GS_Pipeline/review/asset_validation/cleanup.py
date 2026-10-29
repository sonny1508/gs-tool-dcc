"""Asset Validation - Cleanup: deletes data an asset shouldn't ship with."""
from __future__ import annotations

import bpy

from ... import common
from ._shared import (
    Tool,
    ValidationError,
    clear_custom_normals,
    plural,
    restore_selection,
    save_selection,
    selected_meshes,
)

TITLE = "Cleanup"
ICON = 'TRASH'

# Object types Apply Transforms works on.
_TRANSFORMABLE = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE', 'LATTICE', 'EMPTY'}


def vertex_colors(context):
    """Delete every color attribute (vertex colors) of the selected meshes."""
    meshes = selected_meshes(context)
    common.ensure_object_mode(context)
    removed = 0
    for obj in meshes:
        colors = obj.data.color_attributes
        while len(colors):
            colors.remove(colors[0])
            removed += 1
    if not removed:
        return "ok", "No vertex colors found."
    return "ok", "Removed {}.".format(plural(removed, "vertex color layer"))


def vertex_groups(context):
    meshes = selected_meshes(context)
    removed = 0
    for obj in meshes:
        removed += len(obj.vertex_groups)
        obj.vertex_groups.clear()
    if not removed:
        return "ok", "No vertex groups found."
    return "ok", "Removed {}.".format(plural(removed, "vertex group"))


def custom_normals_data(context):
    """Clear Custom Split Normals Data from the selected meshes (the counterpart
    of Normals > Check Custom Normals Data)."""
    meshes = selected_meshes(context)
    saved = save_selection(context)
    common.ensure_object_mode(context)
    try:
        cleared = clear_custom_normals(context, meshes)
    finally:
        restore_selection(context, saved)
    if not cleared:
        return "ok", "No custom split normals found."
    return "ok", "Cleared custom split normals from {}.".format(plural(cleared, "mesh", "meshes"))


def unused_materials(context):
    """Delete material slots no face uses."""
    meshes = selected_meshes(context)
    saved = save_selection(context)
    common.ensure_object_mode(context)
    removed = 0
    for obj in meshes:
        if not obj.material_slots:
            continue
        used = {polygon.material_index for polygon in obj.data.polygons}
        context.view_layer.objects.active = obj
        for index in reversed(range(len(obj.material_slots))):
            if index not in used:
                obj.active_material_index = index
                bpy.ops.object.material_slot_remove()
                removed += 1
    restore_selection(context, saved)
    if not removed:
        return "ok", "No unused materials found."
    return "ok", "Removed {}.".format(plural(removed, "unused material"))


def cameras(context):
    """Delete every camera object in the file."""
    found = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
    for obj in found:
        bpy.data.objects.remove(obj)
    if not found:
        return "ok", "No cameras found."
    return "ok", "Removed {}.".format(plural(len(found), "camera"))


def apply_transforms(context):
    """Apply location, rotation and scale to the selected objects."""
    saved = save_selection(context)
    targets = [obj for obj in context.selected_objects
               if obj.type in _TRANSFORMABLE and obj.library is None]
    if not targets:
        raise ValidationError("Select the objects to apply transforms to first.")
    common.ensure_object_mode(context)
    common.select_only(context, targets)
    try:
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    finally:
        restore_selection(context, saved)
    return "ok", "Transforms applied."


TOOLS = (
    Tool("vertex_colors", "Vertex Colors",
         "Delete all vertex colors of the selected meshes", vertex_colors),
    Tool("vertex_groups", "Vertex Groups",
         "Delete all vertex groups of the selected meshes", vertex_groups),
    Tool("clear_custom_normals", "Custom Normals Data",
         "Clear Custom Split Normals Data from the selected meshes", custom_normals_data),
    Tool("unused_materials", "Unused Materials",
         "Delete material slots no face of the selected meshes uses", unused_materials),
    Tool("cameras", "Cameras", "Delete every camera in the file", cameras),
    Tool("apply_transforms", "Apply Transforms",
         "Apply location, rotation and scale to the selected objects", apply_transforms),
)
