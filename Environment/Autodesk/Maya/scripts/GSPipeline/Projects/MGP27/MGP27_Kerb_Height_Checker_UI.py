# -*- coding: utf-8 -*-
"""
MGP27 Kerb Height Checker - find kerb steps that are off the height spec, and fix them.

PySide2 (Maya 2022) / PySide6 (Maya 2026) window. GSPipeline runs this file
with __name__ == '__main__', which opens the window.

Select the kerbs (and the track, if the foot of the kerb is on a separate
mesh) and Check. Check selects the kerb-top vertices whose step is off spec;
Fix Selected moves the selected vertices onto it.

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

What gets checked: with components selected, only their vertices are checked,
and meshes selected whole are only compared against. With only meshes or
groups selected, every vertex is checked. Bases can be on any mesh in the
selection.

Heights and distances are in cm, whatever the scene's working unit.
"""

import bisect
import html
import math
import os
import sys
import traceback
from collections import defaultdict, namedtuple

import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.OpenMayaUI as omui

try:                                    # Maya 2025+
    from PySide6 import QtCore, QtWidgets
    from shiboken6 import wrapInstance
    QT_BINDING = "PySide6"
except ImportError:                     # Maya 2022-2024
    from PySide2 import QtCore, QtWidgets
    from shiboken2 import wrapInstance
    QT_BINDING = "PySide2"

# GSPipeline launches tools by exec'ing scripts, so _core is not on sys.path.
# Put it there once, the same way LOD Checker reaches gs_lod.
_CORE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '_core')
if _CORE not in sys.path:
    sys.path.append(_CORE)

import gs_style  # noqa: E402  (must follow the sys.path setup)

OBJECT_NAME = "MGP27KerbHeightCheckerWindow"
WINDOW_TITLE = "MGP27 Kerb Height Checker"

# MGP27 kerb spec, in cm. The window opens on these every time, so a value
# changed for one check never quietly sticks.
KERB_HEIGHT = 2.0
TOLERANCE = 0.05
SEARCH_RADIUS = 15.0
IGNORE_BELOW = 0.2

# A step's steepness is drop / (ground distance + this, in cm). Keeps a sheer
# wall finite, and down a wall ranks the foot above vertices part way down.
STEEPNESS_SOFTEN = 0.5

# A Fix move smaller than this (cm) is skipped: the vertex is already exact.
MOVE_EPSILON = 1e-4

UNDO_CHUNK = "mgp27FixKerbHeight"

# optionVars that remember preferences between sessions (not the spec values).
_OPT_PREFIX = "gs_mgp27_kerb_"


class KerbError(Exception):
    """Something the artist can put right (selection, settings): logged without a traceback."""


# up: 1 for Y up, 2 for Z up. ground_only: measure the search radius along the
# ground, so height difference does not count toward the distance.
Settings = namedtuple("Settings", "height tolerance radius ignore_below up ground_only")

# An off-spec (or fixed) vertex: its name, its base's name ("<shape>.vtx[n]"),
# and how far above the base it is (was, for a Fix), in cm.
Step = namedtuple("Step", "top base drop")

# checked: vertices checked. on_step: checked vertices with a step down.
# high / low: [Step] off spec, worst first.
CheckResult = namedtuple("CheckResult", "checked on_step high low")

# moved: how many vertices moved. offsets: how far each piece moved, in cm
# (each vertex, in Absolute mode). exact: vertices already exactly on spec.
# skipped: names of vertices with no step down to move against.
FixResult = namedtuple("FixResult", "moved offsets exact skipped")


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------
def _shape_path(dag):
    if dag.apiType() != om.MFn.kMesh:
        dag.extendToShape()
    return dag.fullPathName()


def read_selection():
    """
    The selection as {mesh shape: vertex ids}. ids is a set for a mesh with
    components selected (edges, faces and UVs count as their vertices) and None
    for a mesh selected whole, directly or through a group above it.
    """
    selection = cmds.ls(selection=True, long=True) or []
    objects = [node for node in selection if "." not in node]
    components = [node for node in selection if "." in node]

    picked = {}
    if objects:
        shapes = cmds.ls(objects, type="mesh", long=True, noIntermediate=True) or []
        shapes += cmds.listRelatives(objects, allDescendents=True, type="mesh",
                                     fullPath=True, noIntermediate=True) or []
        for shape in shapes:
            picked[shape] = None

    vertices = cmds.polyListComponentConversion(components, toVertex=True) if components else None
    if vertices:
        selection_list = om.MSelectionList()
        for name in vertices:
            selection_list.add(name)
        for i in range(selection_list.length()):
            dag, component = selection_list.getComponent(i)
            shape = _shape_path(dag)
            if picked.get(shape) is None:
                picked[shape] = set()
            picked[shape].update(om.MFnSingleIndexedComponent(component).getElements())
    return picked


# ---------------------------------------------------------------------------
# Measuring
# ---------------------------------------------------------------------------
def _cm_per_unit():
    """Centimetres in one of the scene's working units."""
    return om.MDistance(1.0, om.MDistance.uiUnit()).asCentimeters()


def _world_points(shape, scale):
    """[x0, y0, z0, x1, ...] world position of every vertex of `shape`, in cm."""
    flat = cmds.xform(shape + ".vtx[*]", query=True, translation=True, worldSpace=True) or []
    if scale != 1.0:
        flat = [value * scale for value in flat]
    return flat


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

    def __init__(self, picked, settings):
        self.settings = settings
        self.radius_sq = settings.radius * settings.radius
        self.cell = settings.radius
        self.shapes = sorted(picked)
        self.starts = []        # first pool index of each shape's vertices
        self.a, self.b, self.h, self.vid = [], [], [], []
        self.tested = []

        ia, ib = (0, 2) if settings.up == 1 else (0, 1)
        ih = settings.up
        scale = _cm_per_unit()
        clouds = [_world_points(shape, scale) for shape in self.shapes]

        # With components selected only they are tested, and nothing further
        # than one radius outside them can be a neighbour, so leave it out.
        partial = any(ids is not None for ids in picked.values())
        if partial:
            lo_a, lo_b, hi_a, hi_b = self._ground_box(picked, clouds, ia, ib)

        for shape, flat in zip(self.shapes, clouds):
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
            ids = picked[shape] or set()
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
        for shape, flat in zip(self.shapes, clouds):
            ids = picked[shape]
            if ids:
                xs.extend([flat[3 * v + ia] for v in ids])
                ys.extend([flat[3 * v + ib] for v in ids])
        margin = self.settings.radius
        return min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin

    def _shape_index(self, i):
        return bisect.bisect_right(self.starts, i) - 1

    def name(self, i):
        return "{}.vtx[{}]".format(self.shapes[self._shape_index(i)], self.vid[i])

    def pieces(self):
        """The tested vertices, split into pieces joined by edges between them."""
        by_shape = defaultdict(dict)        # shape index -> {vertex id: pool index}
        for i in self.tested:
            by_shape[self._shape_index(i)][self.vid[i]] = i

        pieces = []
        for shape_index, members in by_shape.items():
            selection_list = om.MSelectionList()
            selection_list.add(self.shapes[shape_index])
            vertex_it = om.MItMeshVertex(selection_list.getDagPath(0))
            seen = set()
            for start in members:
                if start in seen:
                    continue
                seen.add(start)
                stack, piece = [start], []
                while stack:
                    vid = stack.pop()
                    piece.append(members[vid])
                    vertex_it.setIndex(vid)
                    for other in vertex_it.getConnectedVertices():
                        if other in members and other not in seen:
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


def check(picked, settings):
    """Measure the step at every tested vertex of `picked` (see read_selection)."""
    pool = _Pool(picked, settings)
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


def fix(picked, settings, relative=True):
    """
    Move the selected component vertices of `picked` onto the kerb height.

    Each piece moves by one offset, chosen so its vertex standing highest
    above its base lands at exactly the kerb height. Relative: a piece is a
    run of selected vertices joined by edges. Absolute: every vertex is a piece
    of its own, so each lands exactly.
    """
    pool = _Pool(picked, settings)
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
    _move_up(moves, settings.up)
    return FixResult(moved, [offset for _, offset in moves], exact, skipped)


def _move_up(moves, up):
    """Move each ([vertices], offset in cm) along the up axis, as one undo step."""
    if not moves:
        return
    scale = 1.0 / _cm_per_unit()
    cmds.undoInfo(openChunk=True, chunkName=UNDO_CHUNK)
    try:
        for names, offset in moves:
            delta = [0.0, 0.0, 0.0]
            delta[up] = offset * scale
            cmds.move(delta[0], delta[1], delta[2], names, relative=True, worldSpace=True)
    finally:
        cmds.undoInfo(closeChunk=True)


def check_selection(settings, select_high=True, select_low=True):
    """Check the selection and select the off-spec vertices of the kinds asked for."""
    picked = read_selection()
    if not picked:
        raise KerbError("Select the kerbs to check first.")
    result = check(picked, settings)
    flagged = (result.high if select_high else []) + (result.low if select_low else [])
    if flagged:
        cmds.select([step.top for step in flagged], replace=True)
    return result


def fix_selection(settings, relative=True):
    """Fix the selected vertices; meshes selected whole are only used for bases."""
    picked = read_selection()
    if not any(ids is not None for ids in picked.values()):
        raise KerbError("Select the vertices to fix first.")
    return fix(picked, settings, relative)


# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
def _maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


def _opt_get(name, default):
    key = _OPT_PREFIX + name
    return cmds.optionVar(query=key) if cmds.optionVar(exists=key) else default


def _opt_set(name, value):
    cmds.optionVar(intValue=(_OPT_PREFIX + name, int(value)))


def _plural(count, word, plural=None):
    return "{:,} {}".format(count, word if count == 1 else plural or word + "s")


def _vertices(count):
    return _plural(count, "vertex", "vertices")


_UNIT_NAMES = {"mm": "Millimeter", "cm": "Centimeter", "m": "Meter", "km": "Kilometer",
               "in": "Inch", "ft": "Foot", "yd": "Yard", "mi": "Mile"}


def _scene_unit():
    unit = cmds.currentUnit(query=True, linear=True)
    return _UNIT_NAMES.get(unit, unit)


class KerbCheckerWindow(QtWidgets.QDialog):

    LOG_COLOURS = gs_style.LOG_COLOURS

    # Settings sit in two equal columns, each at least this wide. The window is
    # exactly two columns wide, so the second column starts mid-window.
    COLUMN_MIN_WIDTH = 240

    # Between a label and its field, and after the field before the next column.
    LABEL_SPACING = 10
    COLUMN_GAP = 24

    def __init__(self, parent=None):
        super(KerbCheckerWindow, self).__init__(parent or _maya_main_window())
        self.setObjectName(OBJECT_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setSizeGripEnabled(False)
        self._labels = []       # every settings label; all get one width
        self._columns = []      # (pair widget, field) for each half of a two-pair row
        self._build()
        self._load_settings()
        self._lock_size()

    def _lock_size(self):
        """Fix the window to its laid-out size - nothing in it needs more room."""
        self.layout().activate()
        self.setFixedSize(self.sizeHint())

    # -- layout -------------------------------------------------------------
    def _build(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        box = self._settings_box(root, "Scene")
        self.z_radio = QtWidgets.QRadioButton("Z")
        self.y_radio = QtWidgets.QRadioButton("Y")
        up_group = QtWidgets.QButtonGroup(self)
        for radio in (self.z_radio, self.y_radio):
            radio.setToolTip("The axis kerb height is measured along.")
            up_group.addButton(radio)
        self.unit_label = QtWidgets.QLabel(_scene_unit())
        self.unit_label.setToolTip("The scene's working unit. Kerb settings are always in cm.")
        self._add_row(box, ("Up Axis:", self._row(self.z_radio, self.y_radio)),
                      ("Unit:", self.unit_label))

        box = self._settings_box(root, "Kerb Spec")
        self.height_spin = self._spin(KERB_HEIGHT, 0.1, 20.0, 0.1, 2,
                                      "Kerb height. MGP27 spec: {:g} cm.".format(KERB_HEIGHT))
        self.tolerance_spin = self._spin(TOLERANCE, 0.001, 1.0, 0.01, 3,
                                         "How far off the height a kerb can be and still pass.")
        self.tolerance_spin.setPrefix(u"± ")
        self._add_row(box, ("Height:", self.height_spin), ("Tolerance:", self.tolerance_spin))

        box = self._settings_box(root, "Search")
        self.radius_spin = self._spin(SEARCH_RADIUS, 1.0, 100.0, 1.0, 1,
                                      "How far from each vertex to look for the bottom of the kerb.")
        self.ignore_spin = self._spin(IGNORE_BELOW, 0.01, 5.0, 0.05, 2,
                                      "Smaller drops count as track slope, not a kerb.\n"
                                      "Raise it if sloped track gets flagged.")
        self._add_row(box, ("Radius:", self.radius_spin), ("Ignore Under:", self.ignore_spin))
        self.ground_check = QtWidgets.QCheckBox("Measure along the ground")
        self.ground_check.setToolTip("Ignore height when measuring the radius.")
        self._add_row(box, ("", self.ground_check))

        # At the bottom, next to the buttons they change.
        box = self._settings_box(root, "Operations")
        self.relative_radio = QtWidgets.QRadioButton("Relative")
        self.relative_radio.setToolTip(
            "Move the selection as one, so its highest vertex lands on the kerb height.\n"
            "The rest keep their height relative to it. Separate pieces move separately.")
        self.absolute_radio = QtWidgets.QRadioButton("Absolute")
        self.absolute_radio.setToolTip("Move every selected vertex to exactly the kerb height.")
        mode_group = QtWidgets.QButtonGroup(self)
        mode_group.addButton(self.relative_radio)
        mode_group.addButton(self.absolute_radio)
        self.high_check = QtWidgets.QCheckBox("Too High")
        self.high_check.setChecked(True)
        self.high_check.setToolTip("Select kerbs higher than spec.")
        self.low_check = QtWidgets.QCheckBox("Too Low")
        self.low_check.setChecked(True)
        self.low_check.setToolTip("Select kerbs lower than spec.")
        self._add_row(box, ("Mode:", self._row(self.relative_radio, self.absolute_radio)),
                      ("Select:", self._row(self.high_check, self.low_check)))

        self._align_columns()

        action_row = QtWidgets.QHBoxLayout()
        action_row.setSpacing(8)
        check_button = self._big_button(
            "Check Selection",
            "Check the selected kerbs and select the vertices that are off spec.\n"
            "If the kerb sits on a separate track mesh, select that too.")
        gs_style.style_button(check_button, gs_style.STUDIO_RED)
        check_button.clicked.connect(self._on_check)
        action_row.addWidget(check_button, 1)
        fix_button = self._big_button(
            "Fix Selected",
            "Move the selected vertices onto the kerb height, as set by Mode.\n"
            "Ctrl+Z undoes it.")
        gs_style.style_button(fix_button, gs_style.STUDIO_ORANGE)
        fix_button.clicked.connect(self._on_fix)
        action_row.addWidget(fix_button, 1)
        root.addLayout(action_row)

        log_box = QtWidgets.QGroupBox("Log")
        log_layout = QtWidgets.QVBoxLayout(log_box)
        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Select the kerbs, then Check Selection.")
        # Room for the few lines a Check or Fix reports.
        self.log_view.setFixedHeight(self.log_view.fontMetrics().lineSpacing() * 4 + 12)
        log_layout.addWidget(self.log_view)
        root.addWidget(log_box)

    def _settings_box(self, root, title):
        """A group box of rows, each holding one or two label / field pairs."""
        box = QtWidgets.QGroupBox(title)
        rows = QtWidgets.QVBoxLayout(box)
        rows.setSpacing(6)
        root.addWidget(box)
        return rows

    def _add_row(self, rows, *pairs):
        """
        Add a row of (label text, field) pairs. In a row of two, each pair is
        one of the two equal columns; a pair on its own row may run longer.
        """
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(0)
        for text, field in pairs:
            label = QtWidgets.QLabel(text)
            label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            pair = QtWidgets.QWidget()
            pair_layout = QtWidgets.QHBoxLayout(pair)
            pair_layout.setContentsMargins(0, 0, 0, 0)
            pair_layout.setSpacing(self.LABEL_SPACING)
            pair_layout.addWidget(label)
            pair_layout.addWidget(field)
            pair_layout.addStretch(1)
            row.addWidget(pair)
            self._labels.append(label)
            if len(pairs) > 1:
                self._columns.append((pair, field))
        row.addStretch(1)
        rows.addLayout(row)

    def _align_columns(self):
        """
        Split every settings box into the same two equal columns.

        Every label gets the width of the longest, so the fields start on one
        line in each column. Every column gets the width of that label plus
        the widest field plus a gap, so the second column starts at the same
        place in every box: the middle of the window.

        Measured after polishing: Maya's style sheet only reaches the widgets
        then, and it changes their sizes.
        """
        self.ensurePolished()
        label_width = max(label.sizeHint().width() for label in self._labels)
        field_width = max(field.sizeHint().width() for _, field in self._columns)
        column_width = max(self.COLUMN_MIN_WIDTH,
                           label_width + self.LABEL_SPACING + field_width + self.COLUMN_GAP)
        for label in self._labels:
            label.setFixedWidth(label_width)
        for pair, _ in self._columns:
            pair.setFixedWidth(column_width)

    @staticmethod
    def _row(*widgets):
        row = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        for widget in widgets:
            layout.addWidget(widget)
        return row

    @staticmethod
    def _spin(value, low, high, step, decimals, tooltip):
        spin = QtWidgets.QDoubleSpinBox()
        spin.setDecimals(decimals)
        spin.setRange(low, high)
        spin.setSingleStep(step)
        spin.setValue(value)
        spin.setSuffix(" cm")
        spin.setMinimumWidth(100)
        spin.setToolTip(tooltip)
        return spin

    @staticmethod
    def _big_button(text, tooltip):
        button = QtWidgets.QPushButton(text)
        button.setToolTip(tooltip)
        button.setMinimumHeight(36)
        font = button.font()
        font.setBold(True)
        button.setFont(font)
        return button

    # -- settings -----------------------------------------------------------
    def _load_settings(self):
        (self.y_radio if _opt_get("up", 2) == 1 else self.z_radio).setChecked(True)
        self.ground_check.setChecked(bool(_opt_get("ground_only", 0)))
        (self.relative_radio if _opt_get("fix_relative", 1) else self.absolute_radio).setChecked(True)

    def _save_settings(self):
        _opt_set("up", 1 if self.y_radio.isChecked() else 2)
        _opt_set("ground_only", self.ground_check.isChecked())
        _opt_set("fix_relative", self.relative_radio.isChecked())

    def _settings(self):
        return Settings(height=self.height_spin.value(),
                        tolerance=self.tolerance_spin.value(),
                        radius=self.radius_spin.value(),
                        ignore_below=self.ignore_spin.value(),
                        up=1 if self.y_radio.isChecked() else 2,
                        ground_only=self.ground_check.isChecked())

    # -- log ----------------------------------------------------------------
    def log(self, message, level="info"):
        colour = self.LOG_COLOURS.get(level)
        if colour:
            self.log_view.appendHtml('<span style="color:{}">{}</span>'.format(
                colour, html.escape(message)))
        else:
            self.log_view.appendPlainText(message)

    def _run(self, function, *args):
        """Call `function` with a wait cursor; log its failure instead of raising."""
        self.log_view.clear()
        self._save_settings()
        self.unit_label.setText(_scene_unit())
        cmds.waitCursor(state=True)
        try:
            return function(*args)
        except KerbError as exc:
            self.log(str(exc), "error")
            cmds.warning(str(exc))
        except Exception as exc:            # keep the window alive, keep the traceback
            traceback.print_exc()
            self.log("Something went wrong: {}. Details in the Script Editor.".format(exc),
                     "error")
        finally:
            cmds.waitCursor(state=False)
        return None

    # -- actions ------------------------------------------------------------
    def _on_check(self):
        select_high, select_low = self.high_check.isChecked(), self.low_check.isChecked()
        if not (select_high or select_low):
            self.log_view.clear()
            self.log("Tick Too High, Too Low or both.", "error")
            return
        settings = self._settings()
        result = self._run(check_selection, settings, select_high, select_low)
        if result is None:
            return

        self.log("Checked {}, {} up.".format(_vertices(result.checked),
                                             "Y" if settings.up == 1 else "Z"))
        if not result.on_step:
            self.log("No kerb steps found. Check the Up Axis, or select the track mesh too.",
                     "warn")
            return
        if not (result.high or result.low):
            self.log("All on spec.", "ok")
            return

        found = ", ".join(part for part in (
            "{:,} too high".format(len(result.high)) if result.high else "",
            "{:,} too low".format(len(result.low)) if result.low else "") if part)
        selected = (len(result.high) if select_high else 0) + (len(result.low) if select_low else 0)
        if selected == len(result.high) + len(result.low):
            self.log("{} - selected.".format(found), "warn")
        elif selected:
            self.log("{}. Selected the {:,} {}.".format(
                found, selected, "too high" if select_high else "too low"), "warn")
        else:
            self.log("{}. Nothing selected - tick {} to select them.".format(
                found, "Too Low" if select_high else "Too High"), "warn")

    def _on_fix(self):
        settings = self._settings()
        relative = self.relative_radio.isChecked()
        result = self._run(fix_selection, settings, relative)
        if result is None:
            return

        if result.moved and not relative:
            self.log("Fixed {} to {:g} cm.".format(_vertices(result.moved), settings.height), "ok")
        elif result.moved and len(result.offsets) == 1:
            offset = result.offsets[0]
            self.log("Moved {} {} {:.2f} cm. The highest is now at {:g} cm.".format(
                _vertices(result.moved), "up" if offset > 0 else "down", abs(offset),
                settings.height), "ok")
        elif result.moved:
            self.log("Moved {} in {:,} pieces. The highest of each is now at {:g} cm.".format(
                _vertices(result.moved), len(result.offsets), settings.height), "ok")
        if result.exact:
            self.log("{} already on spec.".format(_vertices(result.exact)))
        if result.skipped:
            cmds.select(result.skipped, replace=True)
            self.log("Couldn't fix {}: no kerb step found. They're selected.".format(
                _vertices(len(result.skipped))), "warn")


def show():
    for widget in _maya_main_window().findChildren(QtWidgets.QDialog, OBJECT_NAME):
        widget.close()
        widget.deleteLater()
    window = KerbCheckerWindow()
    window.show()
    return window


if __name__ == "__main__":
    show()
