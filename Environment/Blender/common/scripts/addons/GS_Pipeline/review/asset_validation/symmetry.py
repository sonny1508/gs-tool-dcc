"""Asset Validation - Symmetry checks across X. Each one lists the meshes that break it."""
from __future__ import annotations

import bmesh
import bpy

from ... import common
from ._shared import Tool, check, selected_meshes
from .log import Found

TITLE = "Symmetry X"
ICON = 'MOD_MIRROR'

# World positions are matched rounded to this many decimals (Blender units).
_SYMMETRY_DECIMALS = 3


def _rounded(position):
    return tuple(round(value, _SYMMETRY_DECIMALS) for value in position)


def _mirrored_vertices(obj, vertices):
    """Indices of the ``vertices`` (of ``obj``) that have a partner mirrored across X.

    Sides are split on the object's local X; partners are matched on world
    position with X made positive.
    """
    matrix = obj.matrix_world
    positive = {}
    for vert in vertices:
        if vert.co.x >= 0:
            positive.setdefault(_rounded(matrix @ vert.co), []).append(vert.index)
    mirrored = set()
    for vert in vertices:
        if vert.co.x <= 0:
            position = matrix @ vert.co
            position.x = abs(position.x)
            partners = positive.get(_rounded(position))
            if partners:
                mirrored.update(partners)
                mirrored.add(vert.index)
    return mirrored


@check
def asymmetric_vertices(context):
    found = Found("asymmetric vertices", 'VERT')
    for obj in selected_meshes(context):
        vertices = obj.data.vertices
        mirrored = _mirrored_vertices(obj, vertices)
        found.add(obj, [vert.index for vert in vertices if vert.index not in mirrored])
    return found


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


@check
def asymmetric_faces(context):
    """Faces Blender's Select Mirror finds no partner for, on either side.

    Each side's unmirrored part is hidden in turn; revealing selects what was
    hidden. The check puts the artist's hidden and selected faces back after.
    """
    found = Found("asymmetric faces", 'FACE')
    for obj in selected_meshes(context):
        mesh = obj.data
        common.select_only(context, [obj])
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal(select=False)       # so only what this hides is revealed below
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        _select_unmirrored_side(bmesh.from_edit_mesh(mesh), mesh, lambda x: x >= 0)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        _select_unmirrored_side(bmesh.from_edit_mesh(mesh), mesh, lambda x: x <= 0)
        bpy.ops.mesh.reveal()
        found.add(obj, [face.index for face in bmesh.from_edit_mesh(mesh).faces if face.select])
        bpy.ops.object.mode_set(mode='OBJECT')
    return found


TOOLS = (
    Tool("asymmetric_vertices", "Asymmetric Vertices",
         "Find vertices that break symmetry across X", asymmetric_vertices),
    Tool("asymmetric_faces", "Asymmetric Faces",
         "Find faces that break symmetry across X", asymmetric_faces),
)
