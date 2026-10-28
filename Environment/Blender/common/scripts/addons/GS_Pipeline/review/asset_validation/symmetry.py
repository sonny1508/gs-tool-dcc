"""Asset Validation - Symmetry checks across X. Each one selects what it finds."""
from __future__ import annotations

import bmesh
import bpy

from ... import common
from ._shared import Tool, flagged, selected_meshes

TITLE = "Symmetry X"
ICON = 'MOD_MIRROR'

# World positions are matched rounded to this many decimals (Blender units).
_SYMMETRY_DECIMALS = 3


def _rounded(position):
    return tuple(round(value, _SYMMETRY_DECIMALS) for value in position)


def _mirrored_vertices(obj, bm):
    """Indices of the vertices that have a partner mirrored across X.

    Sides are split on the object's local X; partners are matched on world
    position with X made positive.
    """
    matrix = obj.matrix_world
    positive = {}
    for vert in bm.verts:
        if vert.co.x >= 0:
            positive.setdefault(_rounded(matrix @ vert.co), []).append(vert.index)
    mirrored = []
    for vert in bm.verts:
        if vert.co.x <= 0:
            position = matrix @ vert.co
            position.x = abs(position.x)
            partners = positive.get(_rounded(position))
            if partners:
                mirrored.extend(partners + [vert.index])
    return mirrored


def _one_at_a_time(context, meshes):
    """Yield each mesh alone in Edit Mode; ends in Object Mode with ``meshes`` selected."""
    for obj in meshes:
        common.select_only(context, [obj])
        bpy.ops.object.mode_set(mode='EDIT')
        yield obj
        bpy.ops.object.mode_set(mode='OBJECT')
    common.select_only(context, meshes)


def asymmetric_vertices(context):
    meshes = selected_meshes(context)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    count = 0
    for obj in _one_at_a_time(context, meshes):
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        for index in _mirrored_vertices(obj, bm):
            bm.verts[index].select = True
        bpy.ops.mesh.select_all(action='INVERT')
        count += sum(1 for vert in bmesh.from_edit_mesh(obj.data).verts if vert.select)
    return flagged(count, ("asymmetric vertex", "asymmetric vertices"), 'VERT')


def _select_unmirrored_side(bm, mesh, on_side):
    """Select one side, add its mirror, then hide everything that isn't the unmirrored rest."""
    for vert in bm.verts:
        if on_side(vert.co.x):
            vert.select = True
    bmesh.update_edit_mesh(mesh)
    bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
    bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='VERT')
    bpy.ops.mesh.select_mirror(extend=True)
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.hide(unselected=False)


def asymmetric_faces(context):
    meshes = selected_meshes(context)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    count = 0
    for obj in _one_at_a_time(context, meshes):
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        before = sum(1 for face in bm.faces if face.select)
        _select_unmirrored_side(bm, mesh, lambda x: x >= 0)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        _select_unmirrored_side(bmesh.from_edit_mesh(mesh), mesh, lambda x: x <= 0)
        bpy.ops.mesh.reveal()
        after = sum(1 for face in bmesh.from_edit_mesh(mesh).faces if face.select)
        count += max(0, after - before)
    return flagged(count, ("asymmetric face", "asymmetric faces"), 'FACE')


TOOLS = (
    Tool("asymmetric_vertices", "Asymmetric Vertices",
         "Find vertices that break symmetry across X", asymmetric_vertices),
    Tool("asymmetric_faces", "Asymmetric Faces",
         "Find faces that break symmetry across X", asymmetric_faces),
)
