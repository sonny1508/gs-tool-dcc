"""GS File Transfer: exporting 3ds Max smoothing groups.

A hard edge only survives as a smoothing-group border if it closes a region,
so open-ended sharp edges are walked onward for the length of the export.
"""
from __future__ import annotations

import contextlib
from collections import deque

import bmesh
import bpy


# What fbx_supports_smoothing_groups() found; None until the exporter could be asked.
_supports_smoothing_groups = None


def fbx_supports_smoothing_groups():
    """True when this Blender's FBX exporter can write 3ds Max smoothing groups.

    The 'SMOOTH_GROUP' smoothing mode exists in 4.5 and 5.2 but not in 3.6, whose
    exporter only offers normals / face / edge smoothing. The tab asks on every
    redraw, so the answer is kept once the exporter has given one; while the FBX
    add-on isn't loaded it's False and asked again next time.
    """
    global _supports_smoothing_groups
    if _supports_smoothing_groups is None:
        try:
            prop = bpy.ops.export_scene.fbx.get_rna_type().properties["mesh_smooth_type"]
        except (AttributeError, KeyError, RuntimeError):
            return False
        _supports_smoothing_groups = "SMOOTH_GROUP" in prop.enum_items.keys()
    return _supports_smoothing_groups


# Sharp-edge fill tuning. Angles are the dihedral angle between an edge's two faces.
_FOLLOW_CREASE = 0.35     # ~20 deg: a fold this strong is always the way to go
_FALLBACK_CREASE = 0.26   # ~15 deg: a weaker fold, taken only when no edge loop carries on straight
_MIN_STRAIGHTNESS = 0.2   # cosine between incoming and outgoing direction to count as "straight on"
_MAX_WALK = 1000          # safety cap on edges added from a single dead end


def _smooth_inside(edge):
    """A plain two-face edge that smoothing flows across."""
    faces = edge.link_faces
    return len(faces) == 2 and edge.smooth and faces[0].smooth and faces[1].smooth


def _splits_smoothing(edge):
    """Marked sharp, on a border, non-manifold, or beside a flat face. Loose wire edges don't count."""
    return len(edge.link_faces) > 0 and not _smooth_inside(edge)


def _next_sharp_edge(vert, incoming, candidates):
    """Pick the edge that best continues the sharp line arriving at ``vert`` along ``incoming``."""
    crease_edge, crease = None, -1.0
    for edge in candidates:
        angle = edge.calc_face_angle()
        if angle > crease:
            crease_edge, crease = edge, angle
    if crease > _FOLLOW_CREASE:
        return crease_edge

    # No strong fold: carry on along the edge loop, skipping edges that share a
    # face with the incoming edge (those turn the corner instead of continuing).
    heading = vert.co - incoming.other_vert(vert).co
    if heading.length > 1e-6:
        heading.normalize()
        beside = {edge for face in incoming.link_faces for edge in face.edges}
        ahead = [edge for edge in candidates if edge not in beside] or candidates
        straight_edge, straightness = None, -2.0
        for edge in ahead:
            out = edge.other_vert(vert).co - vert.co
            if out.length > 1e-6:
                dot = heading.dot(out.normalized())
                if dot > straightness:
                    straight_edge, straightness = edge, dot
        if straightness > _MIN_STRAIGHTNESS:
            return straight_edge

    return crease_edge if crease >= _FALLBACK_CREASE else None


def find_sharp_fill_edges(mesh):
    """Indices of the edges the smoothing-group export would mark sharp on ``mesh``. ``mesh`` is not modified.

    A 3ds Max smoothing group is a region of faces, so a hard edge only survives
    the trip if it separates two regions. A sharp edge that stops mid-surface has
    the same region on both sides and comes out smooth in Max. Each such dead end
    is walked onward -- along a crease if there is one, otherwise straight along
    the edge loop -- until it meets another sharp edge or a border.
    """
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.index_update()
        bm.edges.index_update()

        # How many smoothing-splitting edges meet at each vertex; exactly one is a dead end.
        splits = [0] * len(bm.verts)
        for edge in bm.edges:
            if _splits_smoothing(edge):
                for vert in edge.verts:
                    splits[vert.index] += 1

        added = []
        dead_ends = deque(vert for vert in bm.verts if splits[vert.index] == 1)
        while dead_ends:
            vert = dead_ends.popleft()
            if splits[vert.index] != 1:
                continue  # already closed by an earlier walk
            incoming = next(edge for edge in vert.link_edges if _splits_smoothing(edge))
            for _ in range(_MAX_WALK):
                candidates = [edge for edge in vert.link_edges if _smooth_inside(edge)]
                edge = _next_sharp_edge(vert, incoming, candidates) if candidates else None
                if edge is None:
                    break
                edge.smooth = False  # BMesh copy only; the caller marks the real mesh
                added.append(edge.index)
                for end in edge.verts:
                    splits[end.index] += 1
                vert, incoming = edge.other_vert(vert), edge
                if splits[vert.index] > 1:
                    break  # reached another hard edge or a border: the line is closed
        return added
    finally:
        bm.free()


def _sharp_fill_for_object(obj, depsgraph):
    """Edge indices into ``obj.data`` that close the object's dead-end sharp edges.

    Reads the evaluated mesh when its topology matches the base mesh, so sharp
    edges coming from modifiers such as Smooth by Angle count; otherwise
    (Mirror, Subdivision...) falls back to the base mesh.
    """
    mesh = obj.data
    obj_eval = obj.evaluated_get(depsgraph)
    evaluated = obj_eval.to_mesh()
    try:
        same_topology = (
            (len(evaluated.vertices), len(evaluated.edges), len(evaluated.polygons))
            == (len(mesh.vertices), len(mesh.edges), len(mesh.polygons))
        )
        return find_sharp_fill_edges(evaluated if same_topology else mesh)
    finally:
        obj_eval.to_mesh_clear()


@contextlib.contextmanager
def temporarily_filled_sharp_edges(context, objects, enabled=True):
    """Fill in open-ended sharp edges on ``objects`` for the duration of the block, then take it back out.

    Yields the number of edges added. The fill goes onto the real meshes so the
    FBX exporter (which evaluates modifiers itself) sees it, and is removed
    afterwards so the artist's scene is left exactly as it was.
    """
    filled = []  # (mesh, edge indices, whether the mesh already had a sharp_edge attribute)
    try:
        if enabled:
            depsgraph = context.evaluated_depsgraph_get()
            seen = set()
            for obj in objects:
                if obj.type != 'MESH' or obj.data in seen or obj.data.library is not None:
                    continue
                mesh = obj.data
                seen.add(mesh)
                indices = _sharp_fill_for_object(obj, depsgraph)
                if not indices:
                    continue
                filled.append((mesh, indices, "sharp_edge" in mesh.attributes))
                for index in indices:
                    mesh.edges[index].use_edge_sharp = True
                mesh.update()
        yield sum(len(indices) for _mesh, indices, _had in filled)
    finally:
        for mesh, indices, had_attribute in filled:
            for index in indices:
                mesh.edges[index].use_edge_sharp = False
            if not had_attribute:
                attribute = mesh.attributes.get("sharp_edge")
                if attribute is not None:
                    try:
                        mesh.attributes.remove(attribute)
                    except RuntimeError:
                        pass
            mesh.update()
