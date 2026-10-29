"""Asset Validation - Geometry checks. Each one lists the meshes with the problem."""
from __future__ import annotations

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from ... import common
from ._shared import Tool, ValidationError, check, selected_meshes
from .log import Found

TITLE = "Geometry"
ICON = 'MESH_DATA'

# Vertex positions are compared rounded to this many decimals (Blender units).
_DUPLICATE_DECIMALS = 4


# ----------------------------------------------------------------------------
# Duplicate vertices
# ----------------------------------------------------------------------------
@check
def duplicate_vertices(context):
    """Vertices at the same world position as an earlier one, on any selected mesh."""
    found = Found("duplicate vertices", 'VERT')
    seen = set()
    for obj in selected_meshes(context):
        matrix = obj.matrix_world
        duplicates = []
        for vertex in obj.data.vertices:
            key = tuple(round(value, _DUPLICATE_DECIMALS) for value in matrix @ vertex.co)
            if key in seen:
                duplicates.append(vertex.index)
            else:
                seen.add(key)
        found.add(obj, duplicates)
    return found


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


@check
def meshes_overlap(context):
    """Faces of two different selected meshes that lie on top of each other."""
    meshes = selected_meshes(context, minimum=2)
    faces = [_world_faces(obj) for obj in meshes]
    overlapping = [set() for _ in meshes]       # face indices, per mesh
    for a in range(len(meshes)):
        for b in range(a + 1, len(meshes)):
            for face1 in faces[a]:
                for face2 in faces[b]:
                    if _faces_overlap(face1, face2):
                        overlapping[a].add(face1[0])
                        overlapping[b].add(face2[0])

    found = Found("faces overlapping another mesh", 'FACE',
                  clean="No overlapping faces found between the selected meshes.")
    for obj, indices in zip(meshes, overlapping):
        found.add(obj, sorted(indices))
    return found


# ----------------------------------------------------------------------------
# N-gons
# ----------------------------------------------------------------------------
@check
def ngons(context):
    """Faces with five or more vertices."""
    found = Found("n-gons", 'FACE')
    for obj in selected_meshes(context):
        polygons = obj.data.polygons
        sizes = np.empty(len(polygons), dtype=np.int32)
        polygons.foreach_get("loop_total", sizes)
        found.add(obj, np.flatnonzero(sizes > 4))
    return found


# ----------------------------------------------------------------------------
# Loose geometry, zero-length edges
# ----------------------------------------------------------------------------
def _edge_vertices(mesh):
    """[edge index] -> (vertex index, vertex index)."""
    pairs = np.empty(len(mesh.edges) * 2, dtype=np.int32)
    mesh.edges.foreach_get("vertices", pairs)
    return pairs.reshape(-1, 2)


def _unused(count, used):
    """Indices in range(count) that ``used`` doesn't hold."""
    flags = np.ones(count, dtype=bool)
    flags[used] = False
    return np.flatnonzero(flags)


@check
def loose_vertices(context):
    """Vertices on no edge, as Blender's Select Loose finds them in vertex mode."""
    found = Found("loose vertices", 'VERT')
    for obj in selected_meshes(context):
        mesh = obj.data
        found.add(obj, _unused(len(mesh.vertices), _edge_vertices(mesh).ravel()))
    return found


@check
def loose_edges(context):
    """Edges on no face, as Blender's Select Loose finds them in edge mode."""
    found = Found("loose edges", 'EDGE')
    for obj in selected_meshes(context):
        mesh = obj.data
        loop_edges = np.empty(len(mesh.loops), dtype=np.int32)
        mesh.loops.foreach_get("edge_index", loop_edges)
        found.add(obj, _unused(len(mesh.edges), loop_edges))
    return found


@check
def zero_length_edges(context):
    """Edges whose two vertices sit at the same position. Found as their vertices,
    which show where an edge with no length can't."""
    found = Found("zero-length edges", 'VERT')
    for obj in selected_meshes(context):
        mesh = obj.data
        positions = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
        mesh.vertices.foreach_get("co", positions)
        positions = positions.reshape(-1, 3)
        edges = _edge_vertices(mesh)
        zero = np.all(positions[edges[:, 0]] == positions[edges[:, 1]], axis=1)
        found.add(obj, np.unique(edges[zero]))
    return found


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


@check
def concave_faces(context):
    """Concave and non-planar faces (triangles are always fine)."""
    found = Found("concave or non-planar faces", 'FACE')
    for obj in selected_meshes(context):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.normal_update()
        indices = []
        concave = nonplanar = False
        for face in bm.faces:
            if len(face.verts) <= 3:
                continue
            is_nonplanar = _is_nonplanar(face)
            is_concave = _is_concave(face)
            if is_concave or is_nonplanar:
                indices.append(face.index)
                concave |= is_concave
                nonplanar |= is_nonplanar
        bm.free()
        if indices:
            kinds = " and ".join(kind for kind, has in (("concave", concave),
                                                        ("non-planar", nonplanar)) if has)
            found.add(obj, indices, kinds + " faces")
    return found


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


def _interior_faces(context, obj):
    """Bake AO on a throwaway UV map; the indices of the faces that come out dark."""
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

        bm = bmesh.new()
        bm.from_mesh(mesh)
        layer = bm.loops.layers.uv.get(_AO_UV)
        interior = [face.index for face in bm.faces
                    if _is_interior(dark, [loop[layer].uv for loop in face.loops])]
        bm.free()
        return interior
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


@check
def overlapping_faces(context):
    """Faces hidden inside the mesh (no light reaches them), found with a quick AO bake."""
    meshes = selected_meshes(context)
    scene = context.scene
    engine = scene.render.engine
    if not hasattr(scene, "cycles"):
        raise ValidationError("Turn on the Cycles add-on first: this check bakes with it.")
    samples = scene.cycles.samples

    found = Found("interior faces", 'FACE')
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = _AO_SAMPLES
    try:
        for obj in meshes:
            found.add(obj, _interior_faces(context, obj))
    finally:
        scene.render.engine = engine
        scene.cycles.samples = samples
    return found


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
