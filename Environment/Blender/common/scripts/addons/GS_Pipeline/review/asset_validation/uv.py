"""Asset Validation - UV checks and seams."""
from __future__ import annotations

import bmesh
import bpy

from ... import common
from ._shared import Tool, flagged, plural, restore_selection, save_selection, selected_meshes

TITLE = "UV"
ICON = 'UV'


def self_penetrating_uvs(context):
    """Faces whose UVs overlap other faces of the same mesh (active UV map).

    Blender's own UV > Select Overlap, run per mesh with UV sync selection on
    so it selects the mesh faces. (The old addon's own test counted faces that
    only share a corner as overlapping, so it flagged every face of a grid.)
    """
    meshes = [obj for obj in selected_meshes(context) if obj.data.uv_layers]
    if not meshes:
        return "warn", "None of the selected meshes has UVs."
    saved = save_selection(context)
    tool_settings = context.tool_settings
    sync = tool_settings.use_uv_select_sync
    count = 0
    common.ensure_object_mode(context)
    try:
        tool_settings.use_uv_select_sync = True
        for obj in meshes:
            common.select_only(context, [obj])
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.uv.select_overlap(extend=False)
            count += sum(1 for face in bmesh.from_edit_mesh(obj.data).faces if face.select)
            bpy.ops.object.mode_set(mode='OBJECT')
    finally:
        tool_settings.use_uv_select_sync = sync
        restore_selection(context, saved)
    return flagged(count, ("face with overlapping UVs", "faces with overlapping UVs"), 'FACE')


def missing_uvs(context):
    """Selected meshes with no UV map. They're left selected."""
    meshes = selected_meshes(context)
    missing = [obj for obj in meshes if not obj.data.uv_layers]
    common.ensure_object_mode(context)
    if not missing:
        return "ok", "All selected meshes have UVs."
    common.select_only(context, missing)
    return "warn", "{} with no UVs - selected.".format(plural(len(missing), "mesh", "meshes"))


def sharp_edges_to_seams(context):
    """Replace the seams with the sharp edges, then unwrap."""
    meshes = selected_meshes(context)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.mark_seam(clear=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    count = 0
    for obj in meshes:
        for edge in obj.data.edges:
            sharp = edge.use_edge_sharp
            edge.select = sharp
            if sharp:
                edge.use_seam = True
                count += 1

    bpy.ops.object.mode_set(mode='EDIT')
    if count:
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    if not count:
        return "warn", "No sharp edges to turn into seams."
    return "ok", "Marked {} as seams and unwrapped.".format(plural(count, "sharp edge"))


TOOLS = (
    Tool("self_penetrating_uvs", "Self Penetrating UVs",
         "Find faces whose UVs overlap others on the same mesh", self_penetrating_uvs),
    Tool("missing_uvs", "Missing UVs", "Find selected meshes with no UV map", missing_uvs),
    Tool("sharp_edges_to_seams", "Sharp Edges to UV Seams",
         "Replace the UV seams with the sharp edges and unwrap", sharp_edges_to_seams),
)
