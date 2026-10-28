"""Asset Validation - Geometry checks. Each one selects what it finds."""
from __future__ import annotations

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from ... import common
from ._shared import (
    Tool,
    ValidationError,
    clear_component_selection,
    flagged,
    plural,
    restore_selection,
    save_selection,
    selected_meshes,
)

TITLE = "Geometry"
ICON = 'MESH_DATA'

# Vertex positions are compared rounded to this many decimals (Blender units).
_DUPLICATE_DECIMALS = 4


# ----------------------------------------------------------------------------
# Duplicate vertices
# ----------------------------------------------------------------------------
def duplicate_vertices(context):
    """Vertices at the same world position as an earlier one, on any selected mesh."""
    meshes = selected_meshes(context)
    clear_component_selection()
    seen = set()
    count = 0
    for obj in meshes:
        matrix = obj.matrix_world
        for vertex in obj.data.vertices:
            key = tuple(round(value, _DUPLICATE_DECIMALS) for value in matrix @ vertex.co)
            if key in seen:
                vertex.select = True
                count += 1
            else:
                seen.add(key)
    return flagged(count, ("duplicate vertex", "duplicate vertices"), 'VERT')


# ----------------------------------------------------------------------------
# Meshes overlap: coplanar faces of different meshes that overlap
# ----------------------------------------------------------------------------
# Faces count as coplanar when their normals are within this of (anti-)parallel
# (|dot| >= 0.99) and their planes within this distance (Blender units).
_PARALLEL_TOLERANCE = 0.01
_PLANE_TOLERANCE = 0.001
# Each face is shrunk this much (share of its size) toward its centre before the
# overlap test, so faces that only touch along an edge (modular pieces laid
# flush) don't count as overlapping.
_TOUCH_SHRINK = 1e-4


def _world_faces(obj):
    """[(face index, world vertices, world normal, plane offset d)] for every face of ``obj``."""
    matrix = obj.matrix_world
    normal_matrix = matrix.to_3x3().inverted_safe().transposed()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    faces = []
    keep = 1.0 - _TOUCH_SHRINK
    for face in bm.faces:
        verts = [matrix @ v.co for v in face.verts]
        normal = (normal_matrix @ face.normal).normalized()
        center = sum(verts, Vector()) / len(verts)
        verts = [center + (v - center) * keep for v in verts]
        faces.append((face.index, verts, normal, -center.dot(normal)))
    bm.free()
    return faces


def _point_in_polygon(point, polygon):
    """Ray casting point-in-polygon test, in 2D."""
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def _edges_cross(p1, p2, p3, p4):
    return _ccw(p1, p3, p4) != _ccw(p2, p3, p4) and _ccw(p1, p2, p3) != _ccw(p1, p2, p4)


def _faces_overlap(face1, face2):
    """True when two world-space faces lie on the same plane and overlap on it."""
    _, verts1, normal1, d1 = face1
    _, verts2, normal2, d2 = face2
    dot = normal1.dot(normal2)
    if abs(abs(dot) - 1.0) > _PARALLEL_TOLERANCE:
        return False
    if dot < 0:
        d2 = -d2        # facing the other way: same plane means opposite offset
    if abs(d1 - d2) > _PLANE_TOLERANCE:
        return False

    # Project both onto the plane and test in 2D.
    if abs(normal1.x) > abs(normal1.y):
        axis1 = Vector((-normal1.z, 0, normal1.x)).normalized()
    else:
        axis1 = Vector((0, -normal1.z, normal1.y)).normalized()
    axis2 = normal1.cross(axis1).normalized()
    flat1 = [(v.dot(axis1), v.dot(axis2)) for v in verts1]
    flat2 = [(v.dot(axis1), v.dot(axis2)) for v in verts2]

    if any(_point_in_polygon(p, flat2) for p in flat1):
        return True
    if any(_point_in_polygon(p, flat1) for p in flat2):
        return True
    edges1 = list(zip(flat1, flat1[1:] + flat1[:1]))
    edges2 = list(zip(flat2, flat2[1:] + flat2[:1]))
    return any(_edges_cross(a, b, c, d) for a, b in edges1 for c, d in edges2)


def meshes_overlap(context):
    """Faces of two different selected meshes that lie on top of each other."""
    meshes = selected_meshes(context, minimum=2)
    faces = [_world_faces(obj) for obj in meshes]
    found = {}      # object -> {face index}
    for a in range(len(meshes)):
        for b in range(a + 1, len(meshes)):
            for face1 in faces[a]:
                for face2 in faces[b]:
                    if _faces_overlap(face1, face2):
                        found.setdefault(meshes[a], set()).add(face1[0])
                        found.setdefault(meshes[b], set()).add(face2[0])

    clear_component_selection()
    if not found:
        return "ok", "No overlapping faces found between the selected meshes."
    for obj, indices in found.items():
        polygons = obj.data.polygons
        for index in indices:
            polygons[index].select = True
    context.view_layer.objects.active = next(iter(found))
    count = sum(len(indices) for indices in found.values())
    return flagged(count, ("overlapping face", "overlapping faces"), 'FACE')


# ----------------------------------------------------------------------------
# N-gons
# ----------------------------------------------------------------------------
def ngons(context):
    """Faces with five or more vertices. Only the meshes that have them stay selected."""
    meshes = selected_meshes(context)
    saved = save_selection(context)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')

    count = 0
    with_ngons = []
    for obj in meshes:
        found = 0
        for polygon in obj.data.polygons:
            polygon.select = len(polygon.vertices) > 4
            found += polygon.select
        if found:
            count += found
            with_ngons.append(obj)

    if count:
        common.select_only(context, with_ngons)
        bpy.ops.object.mode_set(mode='EDIT')
        return "warn", "{} - selected.".format(plural(count, "n-gon"))
    restore_selection(context, saved)
    return "ok", "No n-gons found."


# ----------------------------------------------------------------------------
# Loose geometry, zero-length edges
# ----------------------------------------------------------------------------
def _count_selected(meshes, elements):
    """Selected verts / edges / faces over the meshes in Edit Mode."""
    return sum(sum(1 for item in getattr(bmesh.from_edit_mesh(obj.data), elements) if item.select)
               for obj in meshes)


def _select_loose(select_mode):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type=select_mode)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_loose(extend=False)


def loose_vertices(context):
    meshes = selected_meshes(context)
    _select_loose('VERT')
    return flagged(_count_selected(meshes, "verts"), ("loose vertex", "loose vertices"), 'VERT')


def loose_edges(context):
    meshes = selected_meshes(context)
    _select_loose('EDGE')
    return flagged(_count_selected(meshes, "edges"), ("loose edge", "loose edges"), 'EDGE')


def zero_length_edges(context):
    meshes = selected_meshes(context)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bpy.ops.mesh.select_all(action='DESELECT')
    count = 0
    for obj in meshes:
        bm = bmesh.from_edit_mesh(obj.data)
        for edge in bm.edges:
            if edge.calc_length() == 0.0:
                edge.select_set(True)
                count += 1
        bmesh.update_edit_mesh(obj.data)
    return flagged(count, ("zero-length edge", "zero-length edges"), 'VERT')


# ----------------------------------------------------------------------------
# Concave / non-planar faces
# ----------------------------------------------------------------------------
# How far (Blender units) a vertex may sit off its face's plane.
_PLANARITY_TOLERANCE = 0.001


def _is_nonplanar(face):
    normal = face.normal
    offset = -normal.dot(face.verts[0].co)
    return any(abs(normal.dot(v.co) + offset) > _PLANARITY_TOLERANCE for v in face.verts)


def _is_concave(face):
    """True when the face, flattened onto its plane, turns the wrong way at any corner."""
    verts = [v.co for v in face.verts]
    count = len(verts)
    longest, x_base = 0.0, None
    for i in range(count):
        edge = verts[(i + 1) % count] - verts[i]
        if edge.length > longest:
            longest, x_base = edge.length, edge.normalized()
    if x_base is None:
        return False            # every edge zero-length: nothing to measure
    z_axis = face.normal.normalized()
    y_axis = z_axis.cross(x_base).normalized()
    x_axis = y_axis.cross(z_axis).normalized()
    flat = [Vector(((v - verts[0]).dot(x_axis), (v - verts[0]).dot(y_axis))) for v in verts]
    for i in range(count):
        edge1 = flat[(i + 1) % count] - flat[i]
        edge2 = flat[(i + 2) % count] - flat[(i + 1) % count]
        if edge1.x * edge2.y - edge1.y * edge2.x < 0:
            return True
    return False


def concave_faces(context):
    """Concave and non-planar faces (triangles are always fine)."""
    meshes = selected_meshes(context)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    concave = nonplanar = 0
    for obj in meshes:
        bm = bmesh.from_edit_mesh(obj.data)
        for face in bm.faces:
            if len(face.verts) <= 3:
                continue
            is_nonplanar = _is_nonplanar(face)
            is_concave = _is_concave(face)
            if is_concave or is_nonplanar:
                face.select_set(True)
                concave += is_concave
                nonplanar += is_nonplanar
        bmesh.update_edit_mesh(obj.data)

    if not (concave or nonplanar):
        bpy.ops.object.mode_set(mode='OBJECT')
        return "ok", "No concave or non-planar faces found."
    found = " and ".join(part for part in (
        "{:,} concave".format(concave) if concave else "",
        "{:,} non-planar".format(nonplanar) if nonplanar else "") if part)
    return "warn", "{} {} - selected.".format(found, "face" if concave + nonplanar == 1 else "faces")


# ----------------------------------------------------------------------------
# Overlapping (interior) faces, found by baking ambient occlusion
# ----------------------------------------------------------------------------
_AO_RESOLUTION = 1024
_AO_SAMPLES = 8
_AO_UV = "__TEMP_AO_UV__"
# A face is interior when more than this share of its pixels bake darker than _AO_DARK.
_AO_DARK = 0.05
_AO_DARK_SHARE = 0.8


def _lightmap_unwrap():
    """Give every face its own patch of the active UV map (smart project if that fails)."""
    try:
        bpy.ops.uv.lightmap_pack(PREF_CONTEXT='ALL_FACES', PREF_PACK_IN_ONE=True,
                                 PREF_NEW_UVLAYER=False, PREF_BOX_DIV=12, PREF_MARGIN_DIV=0.02)
    except (RuntimeError, TypeError):
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)


def _bake_material(name):
    """A material holding only an active image node, for the bake to write into."""
    material = bpy.data.materials.new(name=name + "_AO_BAKE_MAT")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    image = bpy.data.images.new(name=name + "_AO", width=_AO_RESOLUTION, height=_AO_RESOLUTION)
    node = nodes.new(type='ShaderNodeTexImage')
    node.image = image
    node.select = True
    nodes.active = node
    return material, image


_NOT_SWAPPED = object()


def _swap_materials(obj, material):
    """Put ``material`` in every slot, leaving face assignments alone.

    Returns what to hand _restore_materials. (Removing and re-adding slots, as
    the old addon did, put every face of a multi-material mesh on slot 1.)
    """
    if not obj.material_slots:
        obj.data.materials.append(material)
        return None
    saved = [slot.material for slot in obj.material_slots]
    for slot in obj.material_slots:
        slot.material = material
    return saved


def _restore_materials(obj, saved):
    if saved is None:
        obj.data.materials.pop()
        return
    for slot, material in zip(obj.material_slots, saved):
        slot.material = material


def _dark_pixels(image):
    """[y, x] -> True where the baked AO is dark."""
    pixels = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(pixels)
    width, height = image.size
    return pixels[0::4].reshape(height, width) < _AO_DARK


def _is_interior(dark, uvs):
    size = _AO_RESOLUTION - 1
    xs = [int(uv.x * size) for uv in uvs]
    ys = [int(uv.y * size) for uv in uvs]
    x0, x1 = max(0, min(min(xs), size)), max(0, min(max(xs), size))
    y0, y1 = max(0, min(min(ys), size)), max(0, min(max(ys), size))
    patch = dark[y0:y1 + 1, x0:x1 + 1]
    return patch.size > 0 and patch.mean() > _AO_DARK_SHARE


def _select_interior_faces(context, obj):
    """Bake AO on a throwaway UV map and select the faces that come out dark. Returns how many."""
    common.select_only(context, [obj])
    mesh = obj.data
    active_uv = mesh.uv_layers.active_index
    stale = mesh.uv_layers.get(_AO_UV)
    if stale is not None:
        mesh.uv_layers.remove(stale)
    mesh.uv_layers.active = mesh.uv_layers.new(name=_AO_UV)

    material = image = None
    saved = _NOT_SWAPPED
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        _lightmap_unwrap()
        bpy.ops.object.mode_set(mode='OBJECT')

        material, image = _bake_material(obj.name)
        saved = _swap_materials(obj, material)
        bpy.ops.object.bake(type='AO', pass_filter={'DIRECT', 'INDIRECT'},
                            width=_AO_RESOLUTION, height=_AO_RESOLUTION, margin=1)
        dark = _dark_pixels(image)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(mesh)
        layer = bm.loops.layers.uv.get(_AO_UV)
        count = 0
        for face in bm.faces:
            if _is_interior(dark, [loop[layer].uv for loop in face.loops]):
                face.select_set(True)
                count += 1
        bmesh.update_edit_mesh(mesh)
        return count
    finally:
        common.ensure_object_mode(context)
        if saved is not _NOT_SWAPPED:
            _restore_materials(obj, saved)
        if material is not None:
            bpy.data.materials.remove(material)
        if image is not None:
            bpy.data.images.remove(image)
        layer = mesh.uv_layers.get(_AO_UV)
        if layer is not None:
            mesh.uv_layers.remove(layer)
        if 0 <= active_uv < len(mesh.uv_layers):
            mesh.uv_layers.active_index = active_uv


def overlapping_faces(context):
    """Faces hidden inside the mesh (no light reaches them), found with a quick AO bake."""
    meshes = selected_meshes(context)
    saved = save_selection(context)
    common.ensure_object_mode(context)
    scene = context.scene
    engine = scene.render.engine
    if not hasattr(scene, "cycles"):
        raise ValidationError("Turn on the Cycles add-on first: this check bakes with it.")
    samples = scene.cycles.samples

    found_on = []
    count = 0
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = _AO_SAMPLES
    try:
        for obj in meshes:
            found = _select_interior_faces(context, obj)
            if found:
                count += found
                found_on.append(obj)
    finally:
        scene.render.engine = engine
        scene.cycles.samples = samples
        restore_selection(context, saved)

    if found_on:
        context.view_layer.objects.active = found_on[0]
    return flagged(count, ("interior face", "interior faces"), 'FACE')


TOOLS = (
    Tool("duplicate_vertices", "Duplicate Vertices",
         "Find vertices sharing a position", duplicate_vertices),
    Tool("meshes_overlap", "Meshes Overlap",
         "Find faces of two selected meshes lying on top of each other", meshes_overlap),
    Tool("ngons", "N-Gons", "Find faces with 5 or more vertices", ngons),
    Tool("loose_vertices", "Loose Vertices", "Find disconnected vertices", loose_vertices),
    Tool("loose_edges", "Loose Edges", "Find disconnected edges", loose_edges),
    Tool("zero_length_edges", "Zero Length Edges", "Find edges with zero length", zero_length_edges),
    Tool("concave_faces", "Concave Faces", "Find concave and non-planar faces", concave_faces),
    Tool("overlapping_faces", "Overlapping Faces",
         "Find faces hidden inside the mesh. Bakes ambient occlusion, so it takes a moment",
         overlapping_faces),
)
