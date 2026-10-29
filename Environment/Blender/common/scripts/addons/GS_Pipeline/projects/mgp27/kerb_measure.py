"""MGP27 Kerb Height Checker - measuring and fixing kerb steps.

The Blender port of Maya's MGP27_Kerb_Height_Checker_UI.py: the measuring and
fixing here follow the Maya tool line for line; keep the two in step. The
sidebar tab and its settings are in kerb_checker.py.

Select the kerbs (and the track, if the foot of the kerb is on a separate
mesh) and Check. Check selects the kerb-top vertices whose step is off spec;
Fix Selection moves the selected vertices onto it.

How a step is measured
----------------------
Each vertex is compared with the vertices within the search radius of it. A
neighbour lower by at least "Ignore Under" is a step down; smaller drops
are camber, banking or noise.

  * No step down: the vertex is not on top of a kerb and is not checked.
  * Any step down within height +/- tolerance: on spec.
  * Otherwise it is off spec, and is measured against its *base*: the
    neighbour the surface falls to most steeply. That is the foot of the kerb
    wall, rather than a lower point further out on a cambered track.

Fix moves the selected vertices along the up axis, in one of two modes:

  * Relative: each connected piece of the selection moves as one. The vertex
    standing highest above its base lands at exactly the kerb height, and the
    rest keep their height relative to it, so the kerb keeps its shape.
    Vertices with no base of their own move with their piece.
  * Absolute: every vertex moves to exactly the kerb height above its own
    base, so each one passes the next Check. Vertices with no base are skipped.

Selected vertices are never used as each other's base. One Ctrl+Z undoes a Fix.

What gets checked: in Edit Mode with vertices selected (edges and faces count
as their vertices), only those are checked, and every other mesh in the
selection is only compared against. Otherwise every vertex of the selected
meshes is checked: meshes selected in Object Mode, directly or through a
parent, or in Edit Mode with nothing selected. Bases can be on any mesh in the
selection.

Heights and distances are in cm, whatever the scene's unit scale. Positions
are the mesh's own vertices (before modifiers), since those are what Fix moves.
"""
from __future__ import annotations

import bisect
import math
from collections import defaultdict, namedtuple

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from ... import common


# A step's steepness is drop / (ground distance + this, in cm). Keeps a sheer
# wall finite, and down a wall ranks the foot above vertices part way down.
STEEPNESS_SOFTEN = 0.5

# A Fix move smaller than this (cm) is skipped: the vertex is already exact.
MOVE_EPSILON = 1e-4


class KerbError(Exception):
    """Something the artist can put right (selection, settings): logged without a traceback."""


# up: 1 for Y up, 2 for Z up. ground_only: measure the search radius along the
# ground, so height difference does not count toward the distance.
Settings = namedtuple("Settings", "height tolerance radius ignore_below up ground_only")

# An off-spec (or fixed) vertex: its (object, vertex index), its base's, and
# how far above the base it is (was, for a Fix), in cm.
Step = namedtuple("Step", "top base drop")

# checked: vertices checked. on_step: checked vertices with a step down.
# high / low: [Step] off spec, worst first.
CheckResult = namedtuple("CheckResult", "checked on_step high low")

# moved: how many vertices moved. offsets: how far each piece moved, in cm
# (each vertex, in Absolute mode). exact: vertices already exactly on spec.
# skipped: (object, vertex index) of vertices with no step down to move against.
FixResult = namedtuple("FixResult", "moved offsets exact skipped")


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------
def _meshes_under(objects):
    """Mesh objects among ``objects`` and their visible descendants, in order."""
    meshes = {}
    for obj in objects:
        for node in (obj, *obj.children_recursive):
            if node.type == 'MESH' and (node is obj or node.visible_get()):
                meshes[node] = None
    return list(meshes)


def _selected_vertices(mesh):
    flags = [False] * len(mesh.vertices)
    mesh.vertices.foreach_get("select", flags)
    return {i for i, selected in enumerate(flags) if selected}


def read_selection(context):
    """
    The selection as {mesh object: vertex ids}. ids is a set for a mesh in Edit
    Mode with vertices selected, and None for a mesh selected whole.
    """
    picked = {obj: None for obj in _meshes_under(context.selected_objects)}
    if context.mode == 'EDIT_MESH':
        for obj in context.objects_in_mode_unique_data:
            if obj.type != 'MESH':
                continue
            obj.update_from_editmode()      # bring obj.data up to date with the edit mesh
            picked[obj] = _selected_vertices(obj.data) or None
    return picked


def select_vertices(context, vertices):
    """Replace the selection with ``vertices`` [(object, vertex id)], in vertex select mode."""
    by_object = defaultdict(list)
    for obj, vid in vertices:
        by_object[obj].append(vid)
    editing = set(context.objects_in_mode) if context.mode == 'EDIT_MESH' else set()
    if not set(by_object) <= editing:
        common.ensure_object_mode(context)
        common.select_only(context, list(by_object))
        context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.object.mode_set(mode='EDIT')
    else:
        context.tool_settings.mesh_select_mode = (True, False, False)
    bpy.ops.mesh.select_all(action='DESELECT')
    for obj, ids in by_object.items():
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        for vid in ids:
            bm.verts[vid].select = True
        bm.select_mode = {'VERT'}
        bm.select_flush_mode()
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)


# ---------------------------------------------------------------------------
# Measuring
# ---------------------------------------------------------------------------
def cm_per_unit(scene):
    """Centimetres in one Blender unit."""
    return 100.0 * (scene.unit_settings.scale_length or 1.0)


def _world_points(obj, scale):
    """[x0, y0, z0, x1, ...] world position of every vertex of ``obj``, in cm."""
    mesh = obj.data
    local = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", local)
    matrix = np.array(obj.matrix_world, dtype=np.float64)
    world = local.reshape(-1, 3).astype(np.float64) @ matrix[:3, :3].T + matrix[:3, 3]
    return (world * scale).ravel().tolist()


def _neighbours(mesh, members):
    """{vertex id: [vertex ids joined to it by an edge]}, for the vertices in ``members``."""
    flat = [0] * (len(mesh.edges) * 2)
    mesh.edges.foreach_get("vertices", flat)
    joined = defaultdict(list)
    for a, b in zip(flat[0::2], flat[1::2]):
        if a in members and b in members:
            joined[a].append(b)
            joined[b].append(a)
    return joined


class _Pool(object):
    """
    The vertices one Check or Fix works with, in cm: a and b are each vertex's
    two ground coordinates, h its height, vid its index on its mesh. tested
    holds the pool indices of the vertices to check or fix.

    Vertices are bucketed on the ground in cells one search radius wide, so a
    vertex's neighbours are all in its own cell and the eight around it. Each
    cell is sorted lowest first, so the scan for steps down stops at the first
    vertex that is not low enough - on flat track that is the first one.
    """

    def __init__(self, picked, settings, scale):
        self.settings = settings
        self.radius_sq = settings.radius * settings.radius
        self.cell = settings.radius
        self.objects = sorted(picked, key=lambda obj: obj.name)
        self.starts = []        # first pool index of each object's vertices
        self.a, self.b, self.h, self.vid = [], [], [], []
        self.tested = []

        ia, ib = (0, 2) if settings.up == 1 else (0, 1)
        ih = settings.up
        clouds = [_world_points(obj, scale) for obj in self.objects]

        # With components selected only they are tested, and nothing further
        # than one radius outside them can be a neighbour, so leave it out.
        partial = any(ids is not None for ids in picked.values())
        if partial:
            lo_a, lo_b, hi_a, hi_b = self._ground_box(picked, clouds, ia, ib)

        for obj, flat in zip(self.objects, clouds):
            start = len(self.h)
            self.starts.append(start)
            ga, gb, gh = flat[ia::3], flat[ib::3], flat[ih::3]
            if not partial:
                self.a.extend(ga)
                self.b.extend(gb)
                self.h.extend(gh)
                self.vid.extend(range(len(gh)))
                self.tested.extend(range(start, len(self.h)))
                continue
            ids = picked[obj] or set()
            near = [v for v, x, y in zip(range(len(gh)), ga, gb)
                    if lo_a <= x <= hi_a and lo_b <= y <= hi_b and v not in ids]
            keep = sorted(ids) + near
            self.a.extend([ga[v] for v in keep])
            self.b.extend([gb[v] for v in keep])
            self.h.extend([gh[v] for v in keep])
            self.vid.extend(keep)
            self.tested.extend(range(start, start + len(ids)))

        cell = self.cell
        grid = defaultdict(list)
        for i, (x, y) in enumerate(zip(self.a, self.b)):
            grid[(math.floor(x / cell), math.floor(y / cell))].append(i)
        for members in grid.values():
            members.sort(key=self.h.__getitem__)
        self.grid = dict(grid)

    def _ground_box(self, picked, clouds, ia, ib):
        """Ground bounds of the selected components, one search radius wider."""
        xs, ys = [], []
        for obj, flat in zip(self.objects, clouds):
            ids = picked[obj]
            if ids:
                xs.extend([flat[3 * v + ia] for v in ids])
                ys.extend([flat[3 * v + ib] for v in ids])
        margin = self.settings.radius
        return min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin

    def _object_index(self, i):
        return bisect.bisect_right(self.starts, i) - 1

    def name(self, i):
        """(object, vertex index) of pool vertex i."""
        return self.objects[self._object_index(i)], self.vid[i]

    def pieces(self):
        """The tested vertices, split into pieces joined by edges between them."""
        by_object = defaultdict(dict)       # object index -> {vertex id: pool index}
        for i in self.tested:
            by_object[self._object_index(i)][self.vid[i]] = i

        pieces = []
        for object_index, members in by_object.items():
            joined = _neighbours(self.objects[object_index].data, members)
            seen = set()
            for start in members:
                if start in seen:
                    continue
                seen.add(start)
                stack, piece = [start], []
                while stack:
                    vid = stack.pop()
                    piece.append(members[vid])
                    for other in joined.get(vid, ()):
                        if other not in seen:
                            seen.add(other)
                            stack.append(other)
                pieces.append(piece)
        return pieces

    def steps_down(self, i):
        """
        Yield (drop, ground distance, j) for every neighbour j of vertex i
        that is lower by at least ignore_below, within the search radius.
        """
        a, b, h = self.a, self.b, self.h
        x, y, top = a[i], b[i], h[i]
        ceiling = top - self.settings.ignore_below
        with_height = not self.settings.ground_only
        cx, cy = math.floor(x / self.cell), math.floor(y / self.cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in self.grid.get((cx + dx, cy + dy), ()):
                    z = h[j]
                    if z > ceiling:
                        break               # the rest of the cell is higher still
                    drop = top - z
                    ground_sq = (x - a[j]) * (x - a[j]) + (y - b[j]) * (y - b[j])
                    if ground_sq + (drop * drop if with_height else 0.0) > self.radius_sq:
                        continue
                    yield drop, math.sqrt(ground_sq), j

    def base_of(self, i, exclude=()):
        """(drop, j) for vertex i's steepest step down, or None if it has none."""
        best, best_score = None, -1.0
        for drop, ground, j in self.steps_down(i):
            if j in exclude:
                continue
            score = drop / (ground + STEEPNESS_SOFTEN)
            if score > best_score:
                best, best_score = (drop, j), score
        return best


def check(picked, settings, scale):
    """Measure the step at every tested vertex of ``picked`` (see read_selection)."""
    pool = _Pool(picked, settings, scale)
    low_ok = settings.height - settings.tolerance
    high_ok = settings.height + settings.tolerance

    on_step = 0
    high, low = [], []
    for i in pool.tested:
        has_step = on_spec = False
        for drop, _, _ in pool.steps_down(i):
            has_step = True
            if low_ok <= drop <= high_ok:
                on_spec = True
                break
        if not has_step:
            continue
        on_step += 1
        if on_spec:
            continue
        drop, j = pool.base_of(i)
        (high if drop > high_ok else low).append(Step(pool.name(i), pool.name(j), drop))

    high.sort(key=lambda step: -step.drop)
    low.sort(key=lambda step: step.drop)
    return CheckResult(len(pool.tested), on_step, high, low)


def fix(picked, settings, scale, relative=True):
    """
    Move the selected component vertices of ``picked`` onto the kerb height.

    Each piece moves by one offset, chosen so its vertex standing highest
    above its base lands at exactly the kerb height. Relative: a piece is a
    run of selected vertices joined by edges. Absolute: every vertex is a piece
    of its own, so each lands exactly.
    """
    pool = _Pool(picked, settings, scale)
    moving = set(pool.tested)
    drops = {}
    for i in pool.tested:
        base = pool.base_of(i, exclude=moving)
        if base is not None:
            drops[i] = base[0]

    moves, moved, skipped, exact = [], 0, [], 0
    for piece in (pool.pieces() if relative else [[i] for i in pool.tested]):
        piece_drops = [drops[i] for i in piece if i in drops]
        if not piece_drops:
            skipped.extend(pool.name(i) for i in piece)
            continue
        offset = settings.height - max(piece_drops)
        if abs(offset) < MOVE_EPSILON:
            exact += len(piece)
            continue
        moves.append(([pool.name(i) for i in piece], offset))
        moved += len(piece)
    _move_up(moves, settings.up, scale)
    return FixResult(moved, [offset for _, offset in moves], exact, skipped)


def _move_up(moves, up, scale):
    """Move each ([(object, vertex id)], offset in cm) along the world up axis.

    The objects are in Edit Mode, so the edit meshes are moved; the operator
    calling this makes it one undo step.
    """
    edits = {}
    for vertices, offset in moves:
        world = Vector((0.0, 0.0, 0.0))
        world[up] = offset / scale
        for obj, vid in vertices:
            edit = edits.get(obj)
            if edit is None:
                bm = bmesh.from_edit_mesh(obj.data)
                bm.verts.ensure_lookup_table()
                # World move -> local move, through the object's rotation and scale.
                edit = edits[obj] = (bm, obj.matrix_world.to_3x3().inverted_safe())
            bm, to_local = edit
            bm.verts[vid].co += to_local @ world
    for obj in edits:
        bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=False)


def check_selection(context, settings, select_high=True, select_low=True):
    """Check the selection and select the off-spec vertices of the kinds asked for."""
    picked = read_selection(context)
    if not picked:
        raise KerbError("Select the kerbs to check first.")
    result = check(picked, settings, cm_per_unit(context.scene))
    flagged = (result.high if select_high else []) + (result.low if select_low else [])
    if flagged:
        select_vertices(context, [step.top for step in flagged])
    return result


def fix_selection(context, settings, relative=True):
    """Fix the selected vertices; meshes selected whole are only used for bases."""
    picked = read_selection(context)
    if not any(ids is not None for ids in picked.values()):
        raise KerbError("Select the vertices to fix first.")
    return fix(picked, settings, cm_per_unit(context.scene), relative)
