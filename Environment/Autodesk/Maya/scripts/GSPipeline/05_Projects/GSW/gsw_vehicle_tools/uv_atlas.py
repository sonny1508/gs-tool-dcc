# -*- coding: utf-8 -*-
"""UV Atlas - move UV shells between the 64x64 atlas grid and tile (0,0).

Gather  brings every shell of the selected meshes back to tile (0,0).
Split   sends every shell out to the tile its vertex colour set maps to,
        per data/uv_tile_map.csv.

A shell is tagged by whichever colour set its vertices are actually assigned
in, so one mesh carrying several colour sets fans out across several tiles.

Both operations are all-or-nothing: if any shell fails validation, nothing
moves and every problem is listed at once.

Only the map1 UV set is touched. maya.cmds + maya.api.OpenMaya only, no pymel.
"""

import csv
import math
import os
import traceback

import maya.api.OpenMaya as om
import maya.cmds as cmds

from gsw_vehicle_tools.main_window import ErrorLog

if int(cmds.about(apiVersion=True) / 10000) >= 2025:
    from PySide6 import QtWidgets
else:
    from PySide2 import QtWidgets

LABEL = "UV Atlas"

UV_SET = "map1"
GRID_SIZE = 64          # tiles 0..63 on both axes
EPS = 1e-5              # float slack for tile-border comparisons
BATCH = 10000           # components per polyEditUV call

# Sentinel handed to getFaceVertexColors for face-vertices with no colour in a
# set. Real colours never carry a negative alpha, so alpha < 0 means unassigned.
UNSET_COLOR = om.MColor((-1.0, -1.0, -1.0, -1.0))

TILE_MAP_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "uv_tile_map.csv")


# --------------------------------------------------------------------------
# tile map
# --------------------------------------------------------------------------

def load_tile_map():
    """Read the colour-set -> tile CSV.

    Returns (mapping, error) where mapping is {name: (u, v)} and error is a
    message string, or None if the file read cleanly.
    """
    if not os.path.isfile(TILE_MAP_FILE):
        return {}, "Tile map not found: {}".format(TILE_MAP_FILE)

    mapping = {}
    try:
        with open(TILE_MAP_FILE, "r") as handle:
            for line_no, row in enumerate(csv.reader(handle), start=1):
                if not row or not row[0].strip() or row[0].strip().startswith("#"):
                    continue
                name = row[0].strip().lower()
                if name == "color_set_name":
                    continue  # header
                if len(row) < 3:
                    return {}, "Tile map line {}: expected name,tile_u,tile_v".format(line_no)
                try:
                    tile_u = int(row[1].strip())
                    tile_v = int(row[2].strip())
                except ValueError:
                    return {}, "Tile map line {}: tile_u/tile_v must be whole numbers".format(line_no)
                if not (0 <= tile_u < GRID_SIZE and 0 <= tile_v < GRID_SIZE):
                    return {}, "Tile map line {}: tile ({}, {}) is outside 0..{}".format(
                        line_no, tile_u, tile_v, GRID_SIZE - 1)
                if name in mapping:
                    return {}, "Tile map line {}: '{}' is listed more than once".format(
                        line_no, name)
                mapping[name] = (tile_u, tile_v)
    except Exception as exc:
        return {}, "Tile map could not be read: {}".format(exc)

    if not mapping:
        return {}, "Tile map is empty - no colour set names have been mapped yet."
    return mapping, None


# --------------------------------------------------------------------------
# scene inspection
# --------------------------------------------------------------------------

def selected_meshes():
    """Mesh shapes under the current selection, groups included."""
    selection = cmds.ls(selection=True, long=True) or []
    found = []
    for node in selection:
        if cmds.nodeType(node) == "mesh":
            found.append(node)
        found.extend(cmds.listRelatives(
            node, shapes=True, fullPath=True, type="mesh") or [])
        found.extend(cmds.listRelatives(
            node, allDescendents=True, fullPath=True, type="mesh") or [])

    meshes = []
    for mesh in found:
        if mesh in meshes:
            continue
        if cmds.getAttr(mesh + ".intermediateObject"):
            continue
        meshes.append(mesh)
    return sorted(meshes)


class Shell(object):
    """One UV shell: its UV ids, its tile, and the colour sets it sits in."""

    def __init__(self, index):
        self.index = index
        self.uv_ids = []
        self.u_min = self.v_min = float("inf")
        self.u_max = self.v_max = float("-inf")
        self.color_sets = set()

    def add(self, uv_id, u, v):
        self.uv_ids.append(uv_id)
        self.u_min = min(self.u_min, u)
        self.u_max = max(self.u_max, u)
        self.v_min = min(self.v_min, v)
        self.v_max = max(self.v_max, v)

    def tile(self):
        """(u, v) tile, or None if the shell straddles a border or is off-grid.

        A shell spanning exactly [1.0, 2.0] belongs to tile 1; one spanning
        [1.4, 2.3] belongs to no tile.
        """
        tile_u = int(math.floor(self.u_min + EPS))
        tile_v = int(math.floor(self.v_min + EPS))
        if self.straddles():
            return None
        if not (0 <= tile_u < GRID_SIZE and 0 <= tile_v < GRID_SIZE):
            return None
        return tile_u, tile_v

    def straddles(self):
        tile_u = int(math.floor(self.u_min + EPS))
        tile_v = int(math.floor(self.v_min + EPS))
        return (self.u_max > tile_u + 1.0 + EPS
                or self.v_max > tile_v + 1.0 + EPS)


def _mesh_fn(mesh_path):
    selection = om.MSelectionList()
    selection.add(mesh_path)
    return om.MFnMesh(selection.getDagPath(0))


def _face_vertex_to_uv(fn):
    """Return (mapping, face_counts).

    mapping is flat face-vertex index -> UV id, or -1 where the face has no
    UVs. getFaceVertexColors() is indexed by face-vertex in the same order as
    getVertices(), so this is what bridges colour assignments to UV shells.
    """
    vert_counts, vert_ids = fn.getVertices()
    uv_counts, uv_ids = fn.getAssignedUVs(UV_SET)

    mapping = [-1] * len(vert_ids)
    vert_offset = 0
    uv_offset = 0
    for face in range(len(vert_counts)):
        count = vert_counts[face]
        uv_count = uv_counts[face] if face < len(uv_counts) else 0
        if uv_count == count:
            for corner in range(count):
                mapping[vert_offset + corner] = uv_ids[uv_offset + corner]
        vert_offset += count
        uv_offset += uv_count
    return mapping, vert_counts


def analyze_mesh(mesh_path, with_colors):
    """Return (shells, error) for one mesh. error is a message or None."""
    fn = _mesh_fn(mesh_path)

    if UV_SET not in fn.getUVSetNames():
        return [], "has no '{}' UV set".format(UV_SET)

    u_values, v_values = fn.getUVs(UV_SET)
    if not len(u_values):
        return [], "has no UVs in '{}'".format(UV_SET)

    _, shell_ids = fn.getUvShellsIds(UV_SET)

    shells = {}
    for uv_id in range(len(u_values)):
        shell_id = shell_ids[uv_id]
        shell = shells.get(shell_id)
        if shell is None:
            shell = shells[shell_id] = Shell(shell_id)
        shell.add(uv_id, u_values[uv_id], v_values[uv_id])

    ordered = [shells[key] for key in sorted(shells)]

    if not with_colors:
        return ordered, None

    color_sets = fn.getColorSetNames()
    if not color_sets:
        return ordered, "has no vertex colour set"

    fv_to_uv, face_counts = _face_vertex_to_uv(fn)
    for color_set in color_sets:
        colors = fn.getFaceVertexColors(colorSet=color_set, defaultUnsetColor=UNSET_COLOR)
        face_vertex = 0
        for face in range(len(face_counts)):
            for corner in range(face_counts[face]):
                color = colors[face_vertex]
                uv_id = fv_to_uv[face_vertex]
                face_vertex += 1

                if uv_id < 0 or color.a < 0.0:
                    continue        # no UV, or the unset sentinel

                shell = shells[shell_ids[uv_id]]
                if color_set in shell.color_sets:
                    continue

                # Maya reports the unset face-vertices of a partly painted
                # vertex as (0,0,0) rather than the sentinel, so pure black
                # is ambiguous - settle it against the colour index.
                if (color.r == 0.0 and color.g == 0.0
                        and color.b == 0.0 and color.a == 0.0):
                    if fn.getColorIndex(face, corner, color_set) < 0:
                        continue

                shell.color_sets.add(color_set)

    return ordered, None


# --------------------------------------------------------------------------
# moving UVs
# --------------------------------------------------------------------------

def shell_components(mesh_path, uv_ids):
    """UV component strings for a shell, consecutive ids collapsed to ranges."""
    ordered = sorted(uv_ids)
    components = []
    start = previous = ordered[0]
    for uv_id in ordered[1:]:
        if uv_id == previous + 1:
            previous = uv_id
            continue
        components.append(_component(mesh_path, start, previous))
        start = previous = uv_id
    components.append(_component(mesh_path, start, previous))
    return components


def _component(mesh_path, start, end):
    if start == end:
        return "{}.map[{}]".format(mesh_path, start)
    return "{}.map[{}:{}]".format(mesh_path, start, end)


def apply_moves(moves, chunk_name):
    """moves: {(du, dv): [component strings]}. One undo chunk for the lot.

    polyEditUV rather than MFnMesh.setUVs: the om2 write is not undoable, and
    a Gather that cannot be undone is a one-way trip.
    """
    cmds.undoInfo(openChunk=True, chunkName=chunk_name)
    try:
        for (delta_u, delta_v), components in moves.items():
            if delta_u == 0 and delta_v == 0:
                continue
            for index in range(0, len(components), BATCH):
                cmds.polyEditUV(
                    components[index:index + BATCH],
                    relative=True,
                    uValue=delta_u,
                    vValue=delta_v,
                    uvSetName=UV_SET,
                )
    finally:
        cmds.undoInfo(closeChunk=True)


class Result(object):

    def __init__(self):
        self.errors = []        # list of (message, [targets])
        self.mesh_count = 0
        self.shell_count = 0

    def fail(self, message, targets=None):
        self.errors.append((message, targets or []))


def _short(mesh_path):
    return mesh_path.split("|")[-1]


def _describe_tile_error(mesh_path, shell):
    if shell.straddles():
        return "{}: shell {} straddles a tile border (u {:.3f}-{:.3f}, v {:.3f}-{:.3f})".format(
            _short(mesh_path), shell.index,
            shell.u_min, shell.u_max, shell.v_min, shell.v_max)
    return "{}: shell {} is outside the 0..{} grid (u {:.3f}-{:.3f}, v {:.3f}-{:.3f})".format(
        _short(mesh_path), shell.index, GRID_SIZE - 1,
        shell.u_min, shell.u_max, shell.v_min, shell.v_max)


# --------------------------------------------------------------------------
# operations
# --------------------------------------------------------------------------

def gather():
    """Move every shell of the selection back to tile (0, 0).

    Positional only - colour set tagging is not checked, since tagging happens
    later in the workflow.
    """
    result = Result()
    meshes = selected_meshes()
    if not meshes:
        result.fail("Nothing selected - select the meshes to gather.")
        return result

    moves = {}
    for mesh_path in meshes:
        shells, error = analyze_mesh(mesh_path, with_colors=False)
        if error:
            result.fail("{}: {}".format(_short(mesh_path), error), [mesh_path])
            continue

        result.mesh_count += 1
        for shell in shells:
            tile = shell.tile()
            if tile is None:
                result.fail(
                    _describe_tile_error(mesh_path, shell),
                    shell_components(mesh_path, shell.uv_ids),
                )
                continue
            result.shell_count += 1
            delta = (-tile[0], -tile[1])
            moves.setdefault(delta, []).extend(
                shell_components(mesh_path, shell.uv_ids))

    if result.errors:
        return result

    apply_moves(moves, "GSW Gather UVs")
    return result


def split():
    """Move every shell out to the tile its colour set maps to."""
    result = Result()
    meshes = selected_meshes()
    if not meshes:
        result.fail("Nothing selected - select the meshes to split.")
        return result

    tile_map, map_error = load_tile_map()
    if map_error:
        result.fail(map_error)
        return result

    moves = {}
    for mesh_path in meshes:
        shells, error = analyze_mesh(mesh_path, with_colors=True)
        if error:
            result.fail("{}: {}".format(_short(mesh_path), error), [mesh_path])
            continue

        result.mesh_count += 1
        for shell in shells:
            components = shell_components(mesh_path, shell.uv_ids)

            tile = shell.tile()
            if tile is None:
                result.fail(_describe_tile_error(mesh_path, shell), components)
                continue

            if not shell.color_sets:
                result.fail(
                    "{}: shell {} has no vertex colour assignment".format(
                        _short(mesh_path), shell.index),
                    components,
                )
                continue
            if len(shell.color_sets) > 1:
                result.fail(
                    "{}: shell {} is assigned in several colour sets ({})".format(
                        _short(mesh_path), shell.index,
                        ", ".join(sorted(shell.color_sets))),
                    components,
                )
                continue

            name = list(shell.color_sets)[0]
            target = tile_map.get(name.strip().lower())
            if target is None:
                result.fail(
                    "{}: shell {} colour set '{}' is not in the tile map".format(
                        _short(mesh_path), shell.index, name),
                    components,
                )
                continue

            result.shell_count += 1
            delta = (target[0] - tile[0], target[1] - tile[1])
            moves.setdefault(delta, []).extend(components)

    if result.errors:
        return result

    apply_moves(moves, "GSW Split UVs")
    return result


# --------------------------------------------------------------------------
# panel
# --------------------------------------------------------------------------

class UVAtlasPanel(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(UVAtlasPanel, self).__init__(parent)

        blurb = QtWidgets.QLabel(
            "Gather brings the selected meshes' UV shells back to tile 0,0.\n"
            "Split sends them out across the {0}x{0} atlas by vertex colour "
            "set name.".format(GRID_SIZE)
        )
        blurb.setWordWrap(True)

        gather_button = QtWidgets.QPushButton("Gather UVs to 0,0")
        gather_button.setMinimumHeight(40)
        gather_button.clicked.connect(self.on_gather)

        split_button = QtWidgets.QPushButton("Split UVs by Colour Set")
        split_button.setMinimumHeight(40)
        split_button.clicked.connect(self.on_split)

        self.log = ErrorLog("Errors")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(blurb)
        layout.addWidget(gather_button)
        layout.addWidget(split_button)
        layout.addWidget(self.log)

    def on_gather(self):
        self._run(gather, "Gathered")

    def on_split(self):
        self._run(split, "Split")

    def _run(self, operation, verb):
        try:
            result = operation()
        except Exception as exc:
            traceback.print_exc()
            self.log.set_errors([("{}: {}".format(type(exc).__name__, exc), [])])
            self.log.set_status("The operation failed - see the Script Editor.", True)
            return

        if result.errors:
            self.log.set_errors(result.errors)
            self.log.set_status(
                "{} problem(s) found. Nothing was moved.".format(len(result.errors)),
                True)
            return

        self.log.set_errors([])
        self.log.set_status("{} {} shell(s) across {} mesh(es).".format(
            verb, result.shell_count, result.mesh_count))


def build(parent=None):
    return UVAtlasPanel(parent)
