"""
pymel_nitro -- a PyMEL-shaped facade over maya.cmds + maya.api.OpenMaya.

WHY THIS EXISTS
---------------
PyMEL is not shipped with Maya 2026+. NitroPoly used PyMEL as little more than
"cmds with a vector library bolted on": of its ~230 pymel calls, all but a
handful are command wrappers whose signatures are identical in maya.cmds, and
every single PyNode is created only to immediately ask it for .getPosition().

So rather than rewrite NitroPoly (2000 lines) or vendor PyMEL itself (~40k
lines of version-fragile API scraping that breaks on every Maya release), this
module reproduces the exact slice of PyMEL that NitroPoly touches, built on
APIs that are identical from Maya 2022 through 2026.

NitroPoly.py itself changes by two import lines. Nothing else.

ONE PATH, EVERY VERSION
-----------------------
This shim is used in ALL Maya versions -- deliberately -- and never falls back
to real PyMEL even where PyMEL exists. A shim that only engaged on 2026 would
mean the code path artists exercise daily (2022-2025, real PyMEL) is not the
code path that ships to 2026, and 2026 would be permanently under-tested.
One implementation, tested by everyone, every day.

SCOPE
-----
Exactly what NitroPoly needs. This is not a general PyMEL replacement; adding
to it is fine, assuming it already covers something is not.

Compatible with Maya 2022 - 2026 (Python 3.7+).
"""

import numbers
import re

import maya.cmds as cmds
import maya.api.OpenMaya as om2


# ---------------------------------------------------------------------------
# pymel.core.datatypes
# ---------------------------------------------------------------------------

def _xyz(value):
    """Coerce anything vector-shaped (Vector, list, tuple, MVector) to 3 floats."""
    if isinstance(value, Vector):
        return value.x, value.y, value.z
    try:
        return float(value[0]), float(value[1]), float(value[2])
    except (TypeError, IndexError, KeyError):
        return float(value.x), float(value.y), float(value.z)


class Vector(object):
    """Minimal stand-in for pymel.core.datatypes.Vector.

    Pure Python on purpose. maya.api's MVector looks like a free win but its
    operator semantics differ in ways that bite here: sum() cannot seed with
    int 0, and MPoint carries a w component that scalar multiplication scales
    along with everything else. Doubles are doubles, and this costs nothing at
    the per-selection scale NitroPoly works at.
    """

    __slots__ = ("x", "y", "z")

    def __init__(self, *args):
        if not args:
            x = y = z = 0.0
        elif len(args) == 1:
            x, y, z = _xyz(args[0])
        elif len(args) == 3:
            x, y, z = args
        else:
            raise ValueError("Vector() takes 0, 1 or 3 arguments, got %d" % len(args))
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    # -- sequence protocol ---------------------------------------------------
    def __getitem__(self, i):
        return (self.x, self.y, self.z)[i]

    def __len__(self):
        return 3

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __repr__(self):
        return "%s(%r, %r, %r)" % (type(self).__name__, self.x, self.y, self.z)

    # -- arithmetic ----------------------------------------------------------
    def __add__(self, other):
        ox, oy, oz = _xyz(other)
        return Vector(self.x + ox, self.y + oy, self.z + oz)

    def __radd__(self, other):
        # sum() seeds its accumulator with int 0; keep sum([Vector, ...]) working.
        if isinstance(other, numbers.Number) and other == 0:
            return Vector(self)
        return self.__add__(other)

    def __sub__(self, other):
        ox, oy, oz = _xyz(other)
        return Vector(self.x - ox, self.y - oy, self.z - oz)

    def __rsub__(self, other):
        ox, oy, oz = _xyz(other)
        return Vector(ox - self.x, oy - self.y, oz - self.z)

    def __mul__(self, other):
        if isinstance(other, numbers.Number):
            return Vector(self.x * other, self.y * other, self.z * other)
        return NotImplemented

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, numbers.Number):
            return Vector(self.x / other, self.y / other, self.z / other)
        return NotImplemented

    __div__ = __truediv__

    def __neg__(self):
        return Vector(-self.x, -self.y, -self.z)

    # -- vector math ---------------------------------------------------------
    def dot(self, other):
        ox, oy, oz = _xyz(other)
        return self.x * ox + self.y * oy + self.z * oz

    def cross(self, other):
        ox, oy, oz = _xyz(other)
        return Vector(self.y * oz - self.z * oy,
                      self.z * ox - self.x * oz,
                      self.x * oy - self.y * ox)

    def length(self):
        return (self.x * self.x + self.y * self.y + self.z * self.z) ** 0.5

    def normal(self):
        n = self.length()
        if n == 0.0:
            return Vector(0.0, 0.0, 0.0)
        return Vector(self.x / n, self.y / n, self.z / n)

    normalize = normal


class Point(Vector):
    """pymel distinguishes Point from Vector; NitroPoly never relies on the
    difference, so Point is a Vector that reports a different name."""
    __slots__ = ()


# Free functions. These must accept raw lists too: viewPlanar feeds them
# straight out of cmds.xform and cmds.camera without wrapping.

def length(v):
    return Vector(v).length()


def dot(a, b):
    return Vector(a).dot(b)


def cross(a, b):
    return Vector(a).cross(b)


def normal(v):
    return Vector(v).normal()


class Matrix(object):
    """4x4 row-major matrix, enough for the three-plane intersection in setFlow.

    Matrix * Vector uses the column-vector convention (M . v), matching pymel:
    the caller builds a matrix whose *rows* are three plane normals and solves
    inverse(A) . d for the intersection point.
    """

    __slots__ = ("rows",)

    def __init__(self, *args):
        if not args:
            self.rows = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
        elif len(args) == 16:
            vals = [float(v) for v in args]
            self.rows = [vals[i * 4:i * 4 + 4] for i in range(4)]
        elif len(args) == 1:
            src = args[0]
            if isinstance(src, Matrix):
                self.rows = [list(row) for row in src.rows]
            else:
                flat = list(src)
                if len(flat) == 4 and hasattr(flat[0], "__len__"):
                    self.rows = [[float(v) for v in row] for row in flat]
                elif len(flat) == 16:
                    self.rows = [[float(v) for v in flat[i * 4:i * 4 + 4]]
                                 for i in range(4)]
                else:
                    raise ValueError("cannot build a Matrix from %r" % (src,))
        else:
            raise ValueError("Matrix() takes 0, 1 or 16 arguments, got %d" % len(args))

    def __getitem__(self, i):
        return self.rows[i]

    def __repr__(self):
        return "Matrix(%r)" % (self.rows,)

    def inverse(self):
        """Gauss-Jordan with partial pivoting.

        Returns identity when singular, which is what MMatrix::inverse does and
        therefore what this code saw under pymel. setFlow depends on that: it
        distance-checks the resulting point and discards nonsense rather than
        expecting an exception.
        """
        n = 4
        aug = [list(self.rows[i]) + [1.0 if i == j else 0.0 for j in range(n)]
               for i in range(n)]
        for col in range(n):
            pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
            if abs(aug[pivot][col]) < 1e-12:
                return Matrix()
            aug[col], aug[pivot] = aug[pivot], aug[col]
            d = aug[col][col]
            aug[col] = [v / d for v in aug[col]]
            for row in range(n):
                if row == col:
                    continue
                f = aug[row][col]
                if f:
                    aug[row] = [a - f * b for a, b in zip(aug[row], aug[col])]
        return Matrix(*[v for row in aug for v in row[n:]])

    def __mul__(self, other):
        if isinstance(other, Matrix):
            out = []
            for i in range(4):
                for j in range(4):
                    out.append(sum(self.rows[i][k] * other.rows[k][j]
                                   for k in range(4)))
            return Matrix(*out)
        x, y, z = _xyz(other)
        v = (x, y, z, 1.0)
        res = [sum(self.rows[i][k] * v[k] for k in range(4)) for i in range(4)]
        w = res[3]
        if w and abs(w - 1.0) > 1e-12:
            return Vector(res[0] / w, res[1] / w, res[2] / w)
        return Vector(res[0], res[1], res[2])


class _Datatypes(object):
    """The ``dt`` namespace: pymel.core.datatypes."""

    Vector = Vector
    Point = Point
    Matrix = Matrix
    length = staticmethod(length)
    dot = staticmethod(dot)
    cross = staticmethod(cross)
    normal = staticmethod(normal)


datatypes = _Datatypes()


# ---------------------------------------------------------------------------
# PyNode
# ---------------------------------------------------------------------------

_INDEX_RE = re.compile(r"\[(\d+)(?::(\d+))?\]")


class Component(str):
    """A component/node name that also answers the PyNode methods NitroPoly calls.

    Subclassing str is the whole trick. NitroPoly freely mixes PyNode and plain
    string usage on the same values: ``sel[0].split(".")[0]`` a few lines from
    ``sel[0].indices()[0]``, set() arithmetic between pymel results and cmds
    results, dict keys, string concatenation. As a str subclass this hashes and
    compares identically to a plain name, passes straight into cmds, and still
    carries the methods.
    """

    __slots__ = ()

    # -- geometry ------------------------------------------------------------
    def getPosition(self, space="preTransform"):
        world = str(space).lower() in ("world", "transform")
        # cmds.pointPosition rather than the API on purpose: it reports in the
        # current linear unit, matching the cm dance NitroPoly does around its
        # math. MFnMesh.getPoint would always report internal centimetres.
        try:
            if world:
                return Point(cmds.pointPosition(str(self), w=True))
            return Point(cmds.pointPosition(str(self), l=True))
        except RuntimeError:
            pos = cmds.xform(str(self), q=True, t=True, ws=world, os=not world)
            return Point(pos[:3])

    def setPosition(self, pos, space="preTransform"):
        world = str(space).lower() in ("world", "transform")
        x, y, z = _xyz(pos)
        cmds.move(x, y, z, str(self), a=True, ws=world, os=not world)

    def getNormal(self, space="preTransform"):
        space_id = (om2.MSpace.kWorld
                    if str(space).lower() in ("world", "transform")
                    else om2.MSpace.kObject)
        sel = om2.MSelectionList()
        sel.add(self.node())
        dag = sel.getDagPath(0)
        dag.extendToShape()
        return Vector(om2.MFnMesh(dag).getPolygonNormal(self.index(), space_id))

    # -- naming --------------------------------------------------------------
    def node(self):
        return str(self).split(".")[0]

    def name(self):
        return str(self)

    def index(self):
        match = _INDEX_RE.search(str(self))
        if not match:
            raise ValueError("%r carries no component index" % str(self))
        return int(match.group(1))

    def indices(self):
        match = _INDEX_RE.search(str(self))
        if not match:
            return []
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        return list(range(start, end + 1))


def PyNode(name):
    if isinstance(name, Component):
        return name
    return Component(str(name))


def _flatten(items):
    """Flatten nested sequences to a flat list of names, dropping Nones.

    pymel accepts arbitrarily nested lists wherever it takes objects; cmds
    raises on them. Strings are leaves, not sequences.
    """
    out = []
    for item in items:
        if item is None:
            continue
        if isinstance(item, str) or not hasattr(item, "__iter__"):
            out.append(item)
        else:
            out.extend(_flatten(item))
    return out


def _wrap(result):
    """Wrap cmds output in Component without disturbing its shape.

    None is preserved deliberately: NitroPoly tests ``filterExpand(...) is
    None`` to detect the current component mode, so collapsing None to [] would
    invert that logic everywhere.
    """
    if result is None:
        return None
    if isinstance(result, (list, tuple)):
        return [Component(item) if isinstance(item, str) else item
                for item in result]
    if isinstance(result, str):
        return Component(result)
    return result


# ---------------------------------------------------------------------------
# pymel.core
# ---------------------------------------------------------------------------

# Commands whose cmds signature is identical but whose pymel return value is
# PyNodes. Wrapped so results keep answering .getPosition() / .indices().
_WRAPPED_RETURNS = frozenset((
    "ls",
    "filterExpand",
    "polyListComponentConversion",
    "polySelect",
    "polySelectSp",
    "listRelatives",
))


class _PymelCore(object):
    """The ``pm`` namespace.

    Anything not overridden below falls through to maya.cmds unchanged, which
    covers the ~180 call sites where pymel was only ever a nicer import name:
    select, currentUnit, polyEvaluate, xform, setAttr, undo, warning,
    polySplit, polyConnectComponents and friends.
    """

    PyNode = staticmethod(PyNode)
    datatypes = datatypes

    def __init__(self):
        self._cache = {}

    def __getattr__(self, name):
        try:
            return self._cache[name]
        except KeyError:
            pass
        fn = getattr(cmds, name)
        if name in _WRAPPED_RETURNS:
            inner = fn

            def fn(*args, **kwargs):
                return _wrap(inner(*args, **kwargs))

            fn.__name__ = name
        self._cache[name] = fn
        return fn

    # -- overrides where cmds and pymel genuinely differ ---------------------
    def selected(self, **kwargs):
        kwargs.setdefault("sl", True)
        return _wrap(cmds.ls(**kwargs))

    def select(self, *args, **kwargs):
        """pymel flattens nested lists and tolerates empty ones; cmds does neither.

        bevelModifier hands select() a list of edge *groups* (a list of lists),
        which cmds rejects outright, and several call sites pass a set-difference
        that can come back empty.
        """
        if not args:
            return cmds.select(**kwargs)
        flat = _flatten(args)
        if not flat:
            # Deselecting/toggling nothing is a no-op; selecting nothing clears.
            if any(kwargs.get(k) for k in ("d", "deselect", "tgl", "toggle",
                                           "add", "af", "addFirst")):
                return None
            return cmds.select(clear=True)
        return cmds.select(*flat, **kwargs)

    def move(self, *args, **kwargs):
        """pymel accepts move(obj, vector); cmds only accepts move(x, y, z, obj)."""
        if args and not isinstance(args[0], numbers.Number):
            objects, target = args[:-1], args[-1]
            x, y, z = _xyz(target)
            return cmds.move(x, y, z, *objects, **kwargs)
        return cmds.move(*args, **kwargs)


core = _PymelCore()
