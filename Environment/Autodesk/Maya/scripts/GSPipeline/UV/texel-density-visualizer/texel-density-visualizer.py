# Created by AreJustPolygons

import re
import ast
import sys
import math
import time
import bisect
import string
import textwrap
import operator
import colorsys
from array import array
from collections import Counter, defaultdict
from itertools import chain, repeat

import maya.cmds as cmds

import maya.api.OpenMaya as _om2

try:
    import maya.OpenMayaUI as _omui
except Exception:
    _omui = None
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance, getCppPointer
except Exception:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
        from shiboken2 import wrapInstance, getCppPointer
    except Exception:
        QtCore = QtGui = QtWidgets = None
        wrapInstance = getCppPointer = None

PREFIX = 'tdViz'
INVALID_COLOR = (1.0, 0.0, 1.0)
MIN_WORLD_AREA = 1e-8
MIN_UV_AREA = 1e-10
_INF = float('inf')

DEFAULT_RANGE_MANUAL = True
DEFAULT_RANGE_MIN = 2.5
DEFAULT_RANGE_MAX = 8.5

DEFAULT_PAIR_ANGLE = 15.0

SHADER_KINDS = ('flat', 'lambert', 'phong')
SHADER_LABELS = ('Flat', 'Lambert', 'Phong')
DEFAULT_SHADER = 'flat'
PHONG_SPECULAR = 0.35
PHONG_COSINE_POWER = 30.0

DISPLAY_MODES = ('fast', 'materials')
DISPLAY_LABELS = ('Fast', 'Materials')
DEFAULT_DISPLAY = 'fast'
COLOR_SET = PREFIX + '_texelDensity'
FAST_NAME = PREFIX + '_fast'
FAST_BASE_COLOR = (0.5, 0.5, 0.5)
FAST_CHANNEL = {'flat': 'None', 'lambert': 'Diffuse', 'phong': 'Diffuse'}
FAST_BLEND = 'Overwrite'
FAST_VIEW = (('displayRedColorChannel', True), ('displayGreenColorChannel', True),
             ('displayBlueColorChannel', True), ('displayColorAsGreyScale', False),
             ('displayAlphaAsGreyScale', False))

PIXEL_AXES = ('x', 'y', 'both')
PIXEL_OPS = ('less', 'more', 'equal', 'range')
PIXEL_OP_LABELS = ['Less than', 'More than', 'Equal to', 'Range  (min - max)']
PIXEL_EPS = 0.01
PIXEL_EQUAL_TOL = 0.5
DEFAULT_PIXEL_A = 64.0
DEFAULT_PIXEL_B = 128.0

DEFAULT_TARGET_TD = 5.12
TD_SCALE_EPS = 1e-6
TD_TOLERANCE = 0.005

LIVE_FAST_MS = 150
TIMING_SHOW = 0.8
TIMING_PRINT = 2.0

GRADIENT_NAMES = [
    'Rainbow  (red > yellow > green > cyan > blue)',
    'Direct  (red > blue)',
    'Three stop  (red > green > blue)',
]


def polygon_area_3d(pts):
    n = len(pts)
    if n < 3:
        return 0.0
    nx = ny = nz = 0.0
    for i in range(n):
        x1, y1, z1 = pts[i]
        x2, y2, z2 = pts[(i + 1) % n]
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    return 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)


def polygon_area_2d(uvs):
    n = len(uvs)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        u1, v1 = uvs[i]
        u2, v2 = uvs[(i + 1) % n]
        s += u1 * v2 - u2 * v1
    return abs(s) * 0.5


def texel_density_px_per_cm(uv_area, world_area_cm2, tex_w, tex_h):
    return math.sqrt((uv_area * float(tex_w) * float(tex_h)) / world_area_cm2)


def gradient_color(t, mode=0, invert=False):
    t = max(0.0, min(1.0, t))
    if invert:
        t = 1.0 - t
    if mode == 0:
        return colorsys.hsv_to_rgb(t * 2.0 / 3.0, 1.0, 1.0)
    if mode == 1:
        return (1.0 - t, 0.0, t)
    if t < 0.5:
        k = t * 2.0
        return (1.0 - k, k, 0.0)
    k = (t - 0.5) * 2.0
    return (0.0, 1.0 - k, k)


def collapse_ranges(ids):
    ids = sorted(ids)
    if not ids:
        return []
    runs = []
    start = prev = ids[0]
    for i in ids[1:]:
        if i == prev + 1:
            prev = i
            continue
        runs.append((start, prev))
        start = prev = i
    runs.append((start, prev))
    return runs


def _edge_counts(v_counts, v_ids, n_verts):
    cnt = Counter()
    if not v_ids:
        return cnt
    nxt = v_ids[1:]
    nxt.append(v_ids[0])
    pos = 0
    short = False
    for c in v_counts:
        pos += c
        if c < 3:
            short = True
        else:
            nxt[pos - 1] = v_ids[pos - c]
    if short:
        ids, nx, pos = [], [], 0
        for c in v_counts:
            if c >= 3:
                ids.extend(v_ids[pos:pos + c])
                nx.extend(nxt[pos:pos + c])
            pos += c
        v_ids, nxt = ids, nx
    step = 1 << 20
    for lo in range(0, len(v_ids), step):
        cnt.update([a * n_verts + b if a < b else b * n_verts + a
                    for a, b in zip(v_ids[lo:lo + step], nxt[lo:lo + step])])
    return cnt


_TICK_STEP = 1 << 16


def _pair_core(tf, tvs, tus, v_ids, uv_ids, pts, u_arr, v_arr, edge_cnt, n_verts,
               max_angle_deg=15.0, uv_eps=1e-5, tick=None):
    cos_lim = math.cos(math.radians(max(0.0, min(89.0, float(max_angle_deg))))) - 1e-9
    sqrt, acos = math.sqrt, math.acos
    count_of = edge_cnt.get
    n_tri = len(tf)

    def evaluate(c1, c2):
        t1, fa = divmod(c1, 3)
        t2 = c2 // 3
        s1, s2 = tvs[t1], tvs[t2]
        v1 = (v_ids[s1], v_ids[s1 + 1], v_ids[s1 + 2])
        v2 = (v_ids[s2], v_ids[s2 + 1], v_ids[s2 + 2])
        fb = fa + 1 if fa < 2 else 0
        fo = 3 - fa - fb
        ga, gb = v2.index(v1[fa]), v2.index(v1[fb])
        go = 3 - ga - gb

        q1, q2 = tus[t1], tus[t2]
        a1, a2 = uv_ids[q1 + fa], uv_ids[q2 + ga]
        if abs(u_arr[a1] - u_arr[a2]) > uv_eps or abs(v_arr[a1] - v_arr[a2]) > uv_eps:
            return None
        b1, b2 = uv_ids[q1 + fb], uv_ids[q2 + gb]
        if abs(u_arr[b1] - u_arr[b2]) > uv_eps or abs(v_arr[b1] - v_arr[b2]) > uv_eps:
            return None

        pf = (pts[v1[0]], pts[v1[1]], pts[v1[2]])
        pg = (pts[v2[0]], pts[v2[1]], pts[v2[2]])
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pf
        e1x, e1y, e1z = bx - ax, by - ay, bz - az
        e2x, e2y, e2z = cx - ax, cy - ay, cz - az
        nfx = e1y * e2z - e1z * e2y
        nfy = e1z * e2x - e1x * e2z
        nfz = e1x * e2y - e1y * e2x
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pg
        e1x, e1y, e1z = bx - ax, by - ay, bz - az
        e2x, e2y, e2z = cx - ax, cy - ay, cz - az
        ngx = e1y * e2z - e1z * e2y
        ngy = e1z * e2x - e1x * e2z
        ngz = e1x * e2y - e1y * e2x
        lf = sqrt(nfx * nfx + nfy * nfy + nfz * nfz)
        lg = sqrt(ngx * ngx + ngy * ngy + ngz * ngz)
        if lf < 1e-12 or lg < 1e-12:
            return None
        cosang = (nfx * ngx + nfy * ngy + nfz * ngz) / (lf * lg)
        if cosang < cos_lim:
            return None

        nax = nfx / lf + ngx / lg
        nay = nfy / lf + ngy / lg
        naz = nfz / lf + ngz / lg
        ln = sqrt(nax * nax + nay * nay + naz * naz)
        A, B = pf[fa], pf[fb]
        ex, ey, ez = B[0] - A[0], B[1] - A[1], B[2] - A[2]
        L = sqrt(ex * ex + ey * ey + ez * ez)
        if ln < 1e-9 or L < 1e-12:
            return None
        nax, nay, naz = nax / ln, nay / ln, naz / ln
        ux, uy, uz = ex / L, ey / L, ez / L
        vx = nay * uz - naz * uy
        vy = naz * ux - nax * uz
        vz = nax * uy - nay * ux
        O, G = pf[fo], pg[go]
        dfx, dfy, dfz = O[0] - A[0], O[1] - A[1], O[2] - A[2]
        dgx, dgy, dgz = G[0] - A[0], G[1] - A[1], G[2] - A[2]
        xf = dfx * ux + dfy * uy + dfz * uz
        yf = dfx * vx + dfy * vy + dfz * vz
        xg = dgx * ux + dgy * uy + dgz * uz
        yg = dgx * vx + dgy * vy + dgz * vz
        if yf * yg >= 0.0:
            return None
        x = xf + (yf / (yf - yg)) * (xg - xf)
        if not (1e-6 * L < x < L * (1.0 - 1e-6)):
            return None
        return acos(max(-1.0, min(1.0, cosang)))

    used = bytearray(n_tri)
    pairs = []

    def one_round(order, longest_only, skip):
        first = {}
        found = []
        tested = set()

        def offer(key, code):
            if count_of(key, 0) != 2 or (skip is not None and key in skip):
                return
            other = first.get(key)
            if other is None:
                first[key] = code
                return
            t1, t2 = other // 3, code // 3
            if t1 == t2:
                return
            tested.add(key)
            ang = evaluate(other, code)
            if ang is not None:
                found.append((ang, tf[t1], tf[t2], t1, t2))

        tol = 1.0 - 1e-9
        for c0 in range(0, len(order), _TICK_STEP):
            if tick is not None:
                tick('pairing', c0, len(order))
            for t in order[c0:c0 + _TICK_STEP]:
                s = tvs[t]
                a, b, c = v_ids[s], v_ids[s + 1], v_ids[s + 2]
                if longest_only:
                    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = pts[a], pts[b], pts[c]
                    dx, dy, dz = x0 - x1, y0 - y1, z0 - z1
                    l0 = sqrt(dx * dx + dy * dy + dz * dz)
                    dx, dy, dz = x1 - x2, y1 - y2, z1 - z2
                    l1 = sqrt(dx * dx + dy * dy + dz * dz)
                    dx, dy, dz = x2 - x0, y2 - y0, z2 - z0
                    l2 = sqrt(dx * dx + dy * dy + dz * dz)
                    lim = max(l0, l1, l2) * tol
                    w0, w1, w2 = l0 >= lim, l1 >= lim, l2 >= lim
                else:
                    w0 = w1 = w2 = True
                code = 3 * t
                if w0:
                    offer(a * n_verts + b if a < b else b * n_verts + a, code)
                if w1:
                    offer(b * n_verts + c if b < c else c * n_verts + b, code + 1)
                if w2:
                    offer(c * n_verts + a if c < a else a * n_verts + c, code + 2)
        found.sort()
        for _ang, _f, _g, i, j in found:
            if used[i] or used[j]:
                continue
            used[i] = used[j] = 1
            pairs.append((i, j))
        return tested

    tested = one_round(range(n_tri), True, None)
    alone = [t for t in range(n_tri) if not used[t]]
    if len(alone) > 1:
        one_round(alone, False, tested)
    return pairs


def pair_triangles(tris, edge_count, max_angle_deg=15.0, uv_eps=1e-5):
    faces = list(tris)
    pts, u_arr, v_arr, v_ids, uv_ids = {}, [], [], [], []
    for f in faces:
        vids, uvs, points = tris[f]
        for vid, uv, p in zip(vids, uvs, points):
            pts[vid] = p
            v_ids.append(vid)
            uv_ids.append(len(u_arr))
            u_arr.append(uv[0])
            v_arr.append(uv[1])
    top = max(v_ids) if v_ids else 0
    for a, b in edge_count:
        top = max(top, a, b)
    n_verts = top + 1
    counts = {}
    for (a, b), n in edge_count.items():
        counts[a * n_verts + b if a < b else b * n_verts + a] = n
    offsets = array('i', range(0, 3 * len(faces), 3))
    partner = {}
    for i, j in _pair_core(faces, offsets, offsets, v_ids, uv_ids, pts, u_arr, v_arr,
                           counts, n_verts, max_angle_deg, uv_eps):
        partner[faces[i]] = faces[j]
        partner[faces[j]] = faces[i]
    return partner


class IslandIndex(object):
    def __init__(self, analyses, shapes):
        self.analyses = analyses
        entries = []
        for s in shapes:
            a = analyses.get(s)
            if not a:
                continue
            for sid, td in a.get('shell_td', {}).items():
                if td == td and abs(td) < _INF:
                    entries.append((td, s, sid))
        entries.sort()
        self.entries = entries
        self.tds = [e[0] for e in entries]
        self.scale = 1.0
        self.disp = self.tds

    def __len__(self):
        return len(self.entries)

    def set_scale(self, scale):
        scale = float(scale)
        if scale != self.scale:
            self.scale = scale
            self.disp = self.tds if scale == 1.0 else [t * scale for t in self.tds]
        return self.disp

    def indices_for_values(self, lo, hi):
        return bisect.bisect_left(self.disp, lo), bisect.bisect_right(self.disp, hi)

    def islands(self, i0, i1):
        return [(s, sid) for _td, s, sid in self.entries[i0:i1]]


def _uvs_of_shell(analysis, shell_id):
    by_shell = analysis.get('_uv_by_shell')
    if by_shell is None:
        by_shell = defaultdict(list)
        for uv_id, sid in enumerate(analysis.get('uv_shell') or ()):
            by_shell[sid].append(uv_id)
        analysis['_uv_by_shell'] = by_shell
    return by_shell.get(shell_id, ())


def island_components(analyses, islands, target='faces'):
    per_shape = defaultdict(list)
    for s, sid in islands:
        a = analyses.get(s)
        if not a:
            continue
        if target == 'uvs':
            per_shape[s].extend(_uvs_of_shell(a, sid))
        else:
            per_shape[s].extend(a['shell_faces'].get(sid, ()))
    key = 'map' if target == 'uvs' else 'f'
    comps = []
    for s in sorted(per_shape):
        for lo, hi in collapse_ranges(per_shape[s]):
            comps.append('%s.%s[%d]' % (s, key, lo) if lo == hi
                         else '%s.%s[%d:%d]' % (s, key, lo, hi))
    return comps


def pixel_predicate(op, a, b=None):
    a = float(a)
    if op == 'less':
        lim = a - PIXEL_EPS
        return lambda s: s < lim
    if op == 'more':
        lim = a + PIXEL_EPS
        return lambda s: s > lim
    if op == 'equal':
        return lambda s: abs(s - a) <= PIXEL_EQUAL_TOL
    if op == 'range':
        b = a if b is None else float(b)
        lo, hi = min(a, b) - PIXEL_EPS, max(a, b) + PIXEL_EPS
        return lambda s: lo <= s <= hi
    raise ValueError('Unknown condition: %r' % (op,))


def match_pixels(width, height, axis, test):
    if axis == 'x':
        return test(width)
    if axis == 'y':
        return test(height)
    if axis == 'both':
        return test(width) and test(height)
    raise ValueError('Unknown axis: %r' % (axis,))


def island_pixel_sizes(analyses, tex_w, tex_h):
    out = []
    for s in sorted(analyses):
        a = analyses[s]
        faces = a.get('shell_faces') or {}
        for sid, box in sorted((a.get('shell_bbox') or {}).items()):
            if sid in faces:
                out.append((s, sid, (box[2] - box[0]) * tex_w, (box[3] - box[1]) * tex_h))
    return out


def islands_by_pixels(analyses, tex_w, tex_h, axis, op, a, b=None):
    if axis not in PIXEL_AXES:
        raise ValueError('Unknown axis: %r' % (axis,))
    test = pixel_predicate(op, a, b)
    sizes = island_pixel_sizes(analyses, tex_w, tex_h)
    matches = [(s, sid) for s, sid, w, h in sizes if match_pixels(w, h, axis, test)]
    stats = {'total': len(sizes), 'w_min': None, 'w_max': None, 'h_min': None, 'h_max': None}
    if sizes:
        ws = [e[2] for e in sizes]
        hs = [e[3] for e in sizes]
        stats.update(w_min=min(ws), w_max=max(ws), h_min=min(hs), h_max=max(hs))
    return matches, stats


def describe_pixel_condition(axis, op, a, b=None):
    what = {'x': 'width', 'y': 'height', 'both': 'width and height'}.get(axis, axis)
    if op == 'less':
        cond = '< %g px' % a
    elif op == 'more':
        cond = '> %g px' % a
    elif op == 'equal':
        cond = '= %g px (+/- %g)' % (a, PIXEL_EQUAL_TOL)
    else:
        b = a if b is None else b
        cond = 'between %g and %g px' % (min(a, b), max(a, b))
    return '%s %s' % (what, cond)


_COMP_RE = re.compile(r'^([^.\[\]]+)\.([A-Za-z]+)((?:\[[^\]]*\])+)$')
_INDEX_RE = re.compile(r'^\[(\d+)(?::(\d+))?\]$')


def parse_component(name):
    m = _COMP_RE.match(name)
    if not m:
        return None
    node, kind, index = m.groups()
    m = _INDEX_RE.match(index)
    if not m:
        return node, kind, None
    lo = int(m.group(1))
    hi = int(m.group(2)) if m.group(2) is not None else lo
    return node, kind, [(min(lo, hi), max(lo, hi))]


def selection_islands(analyses, spec):
    islands, skipped = [], 0
    for shape in sorted(spec):
        a = analyses.get(shape)
        if not a:
            continue
        sp = spec[shape]
        every = set(a.get('shell_faces') or ())
        if sp.get('whole'):
            touched = every
        else:
            touched = set()
            face_shell = a.get('face_shell') or ()
            for lo, hi in sp.get('faces') or ():
                touched.update(face_shell[lo:hi + 1])
            uv_shell = a.get('uv_shell') or ()
            for lo, hi in sp.get('uvs') or ():
                touched.update(uv_shell[lo:hi + 1])
            touched &= every
        valid = a.get('shell_td') or {}
        for sid in sorted(touched):
            if sid in valid:
                islands.append((shape, sid))
            else:
                skipped += 1
    return islands, skipped


def plan_texel_density(analyses, islands, target, overall=False):
    plan = {'entries': [], 'count': len(islands), 'avg': None, 'min': None, 'max': None}
    if not islands:
        return plan
    px = world = 0.0
    lo = hi = None
    boxes = []
    for s, sid in islands:
        a = analyses[s]
        px += a['shell_px'][sid]
        world += a['shell_world'][sid]
        d = a['shell_td'][sid]
        lo = d if lo is None or d < lo else lo
        hi = d if hi is None or d > hi else hi
        boxes.append(a['shell_bbox'][sid])
    avg = math.sqrt(px / world)
    plan.update(avg=avg, min=lo, max=hi)
    if overall:
        scale = target / avg
        pu = (min(b[0] for b in boxes) + max(b[2] for b in boxes)) * 0.5
        pv = (min(b[1] for b in boxes) + max(b[3] for b in boxes)) * 0.5
        plan['entries'] = [(s, sid, scale, pu, pv) for s, sid in islands]
    else:
        for (s, sid), b in zip(islands, boxes):
            plan['entries'].append((s, sid, target / analyses[s]['shell_td'][sid],
                                    (b[0] + b[2]) * 0.5, (b[1] + b[3]) * 0.5))
    return plan


def nice_ticks(lo, hi, max_ticks=6):
    span = hi - lo
    if not span > 0.0:
        return [lo]
    raw = span / max(1, max_ticks)
    mag = 10.0 ** math.floor(math.log10(raw))
    step = mag * 10.0
    for m in (1.0, 2.0, 2.5, 5.0, 10.0):
        if m * mag >= raw:
            step = m * mag
            break
    v = math.ceil(lo / step - 1e-9) * step
    ticks = []
    while v <= hi + step * 1e-9 and len(ticks) < 200:
        ticks.append(round(v, 10))
        v += step
    return ticks


def tick_label(value, step_hint):
    for d in range(0, 7):
        if abs(step_hint * 10 ** d - round(step_hint * 10 ** d)) < 1e-6:
            return '%.*f' % (d, value)
    return '%g' % value


def histogram_bins(sorted_vals, lo, hi, nbins):
    if nbins < 1 or not hi > lo:
        return [0] * max(0, nbins), 0, 0
    w = (hi - lo) / nbins
    idx = [bisect.bisect_left(sorted_vals, lo + w * i) for i in range(nbins + 1)]
    idx[0] = 0
    idx[-1] = len(sorted_vals)
    counts = [idx[i + 1] - idx[i] for i in range(nbins)]
    below = bisect.bisect_left(sorted_vals, lo)
    above = len(sorted_vals) - bisect.bisect_right(sorted_vals, hi)
    return counts, below, above


def bin_slice(sorted_vals, lo, hi, nbins, i):
    w = (hi - lo) / nbins
    i0 = 0 if i <= 0 else bisect.bisect_left(sorted_vals, lo + w * i)
    i1 = len(sorted_vals) if i >= nbins - 1 else bisect.bisect_left(sorted_vals, lo + w * (i + 1))
    return i0, i1


def robust_core(sorted_vals):
    n = len(sorted_vals)
    if n == 0:
        return None, None
    q1 = sorted_vals[int(0.25 * (n - 1))]
    q3 = sorted_vals[int(0.75 * (n - 1))]
    iqr = q3 - q1
    if iqr > 1e-12:
        return max(sorted_vals[0], q1 - 3.0 * iqr), min(sorted_vals[-1], q3 + 3.0 * iqr)
    return sorted_vals[int(0.01 * (n - 1))], sorted_vals[min(n - 1, int(math.ceil(0.99 * (n - 1))))]


def default_view(data_min, data_max, color_lo, color_hi, core_lo=None, core_hi=None):
    if data_min is None:
        lo, hi = color_lo, color_hi
    else:
        cl = data_min if core_lo is None else core_lo
        ch = data_max if core_hi is None else core_hi
        lo, hi = min(cl, color_lo), max(ch, color_hi)
        if hi - lo > 4.0 * max(ch - cl, 1e-9):
            lo, hi = cl, ch
    pad = (hi - lo) * 0.04
    lo, hi = lo - pad, hi + pad
    if lo < 0.0 <= (data_min if data_min is not None else color_lo):
        lo = 0.0
    if hi - lo < 1e-9:
        lo, hi = lo - 0.5, hi + 0.5
    return lo, hi


def _short_name(shape):
    parts = [p for p in shape.split('|') if p]
    if len(parts) > 1:
        return parts[-2]
    return parts[-1] if parts else shape


def _unit_label(scale):
    return 'px/m' if abs(scale - 100.0) < 1e-6 else 'px/cm'


def _islands(n):
    return '%d island%s' % (n, '' if n == 1 else 's')


def _seconds(x):
    return '%.1f s' % x if x >= 0.1 else '%d ms' % int(round(x * 1000.0))


def _where(err):
    here, found = globals(), None
    tb = getattr(err, '__traceback__', None)
    while tb is not None:
        if tb.tb_frame.f_globals is here:
            found = tb
        tb = tb.tb_next
    if found is None:
        return ''
    return ' [%s, line %d]' % (found.tb_frame.f_code.co_name, found.tb_lineno)


def timing_summary(res):
    t = res.get('timing')
    if not t:
        return '', ''
    labels = (('measure', 'measuring'), ('snapshot', 'snapshot'), ('shaders', 'materials'),
              ('assign', 'painting'), ('index', 'diagram'), ('refresh', 'viewport'))
    parts = ['%s %s' % (label, _seconds(t[k])) for k, label in labels if t.get(k, 0.0) >= 0.05]
    detail = 'Apply took %s' % _seconds(t.get('total', 0.0))
    if parts:
        detail += ': ' + ', '.join(parts)
    paint = res.get('paint')
    if paint:
        detail += '  (%s)' % _paint_note(paint)
    return _seconds(t.get('total', 0.0)), detail


def _meshes(n):
    return '%d mesh%s' % (n, '' if n == 1 else 'es')


def _paint_note(paint):
    fast = paint.get('fast', 0)
    if not fast:
        return '%s paint: %d of %d faces assigned, %d commands' % (
            paint['mode'], paint['changed'], paint['faces'], paint['calls'])
    text = '%s paint: %d of %d faces written as vertex colors on %s' % (
        paint['mode'], paint['written'], paint['fast_faces'], _meshes(fast))
    if paint.get('slow'):
        text += ', %d of %d faces assigned to materials on %s' % (
            paint['slow_changed'], paint['slow_faces'], _meshes(paint['slow']))
    return text + ', %d commands' % paint['calls']


def display_note(res):
    paint = res.get('paint') or {}
    fallback = paint.get('fallback') or []
    if not fallback:
        return '', ''
    why = {}
    for name, reason in fallback:
        why.setdefault(reason, []).append(name)
    detail = '; '.join('%s: %s' % (reason, ', '.join(names)) for reason, names in why.items())
    short = '%s on the Materials display' % _meshes(len(fallback))
    if len(why) == 1 and len(next(iter(why))) <= 40:
        short += ' (%s)' % next(iter(why))
    return short, '%s could not use the Fast display - %s' % (_meshes(len(fallback)), detail)


def analyze_mesh(shape, tex_w, tex_h, per_island=False, merge_tris=False, max_angle=15.0,
                 tick=None):
    sel = _om2.MSelectionList()
    sel.add(shape)
    fn = _om2.MFnMesh(sel.getDagPath(0))
    uv_set = fn.currentUVSetName()
    n_faces = fn.numPolygons
    n_uvs = fn.numUVs(uv_set)

    out = {
        'shape': shape, 'uv_set': uv_set, 'n_faces': n_faces, 'n_uvs': n_uvs,
        'density': [None] * n_faces,
        'min': None, 'max': None, 'avg': None,
        'valid': 0, 'invalid': n_faces, 'islands': 0, 'merged_pairs': 0,
        'shell_td': {}, 'shell_faces': {}, 'uv_shell': None,
    }
    if n_faces == 0 or n_uvs == 0:
        return out

    if tick is not None:
        tick('reading the mesh', 0, n_faces)
    pts = [(p.x, p.y, p.z) for p in fn.getPoints(_om2.MSpace.kWorld)]
    v_counts, v_ids = fn.getVertices()
    v_counts, v_ids = list(v_counts), list(v_ids)
    u_arr, v_arr = fn.getUVs(uv_set)
    u_arr, v_arr = list(u_arr), list(v_arr)
    uv_counts, uv_ids = fn.getAssignedUVs(uv_set)
    uv_counts, uv_ids = list(uv_counts), list(uv_ids)
    shell_of_uv = None
    try:
        _, shells = fn.getUvShellsIds(uv_set)
        shell_of_uv = list(shells)
    except Exception:
        if per_island:
            raise
    shell_ids = shell_of_uv if shell_of_uv is not None else [-1] * len(u_arr)
    n_shells = max(shell_ids) + 1 if shell_ids else 0

    tex_area = float(tex_w) * float(tex_h)
    sqrt = math.sqrt
    min_world, min_uv, inf = MIN_WORLD_AREA, MIN_UV_AREA, _INF
    dens = out['density']
    face_shell = [-1] * n_faces if per_island else None
    shell_faces = [None] * n_shells
    shell_px = [0.0] * n_shells
    shell_world = [0.0] * n_shells
    px_total = world_total = 0.0
    v_off = uv_off = 0

    do_merge = bool(merge_tris) and not per_island
    edge_cnt = _edge_counts(v_counts, v_ids, len(pts)) if do_merge else None
    tf, tvs, tus = array('i'), array('i'), array('i')
    tpx, tw = array('d'), array('d')

    for c0 in range(0, n_faces, _TICK_STEP):
        if tick is not None:
            tick('measuring', c0, n_faces)
        for f in range(c0, min(n_faces, c0 + _TICK_STEP)):
            vc, uc = v_counts[f], uv_counts[f]
            vs, us = v_off, uv_off
            v_off = vs + vc
            uv_off = us + uc
            if vc < 3 or uc < 3:
                continue
            sid = shell_ids[uv_ids[us]]
            if sid >= 0:
                members = shell_faces[sid]
                if members is None:
                    shell_faces[sid] = [f]
                else:
                    members.append(f)
            if vc == 3 and uc == 3:
                x0, y0, z0 = pts[v_ids[vs]]
                x1, y1, z1 = pts[v_ids[vs + 1]]
                x2, y2, z2 = pts[v_ids[vs + 2]]
                ex, ey, ez = x1 - x0, y1 - y0, z1 - z0
                fx, fy, fz = x2 - x0, y2 - y0, z2 - z0
                nx = ey * fz - ez * fy
                ny = ez * fx - ex * fz
                nz = ex * fy - ey * fx
                world = 0.5 * sqrt(nx * nx + ny * ny + nz * nz)
                i0, i1, i2 = uv_ids[us], uv_ids[us + 1], uv_ids[us + 2]
                u0, v0 = u_arr[i0], v_arr[i0]
                uv = 0.5 * abs((u_arr[i1] - u0) * (v_arr[i2] - v0) - (u_arr[i2] - u0) * (v_arr[i1] - v0))
            elif vc == 4 and uc == 4:
                x0, y0, z0 = pts[v_ids[vs]]
                x1, y1, z1 = pts[v_ids[vs + 1]]
                x2, y2, z2 = pts[v_ids[vs + 2]]
                x3, y3, z3 = pts[v_ids[vs + 3]]
                dx, dy, dz = x2 - x0, y2 - y0, z2 - z0
                ex, ey, ez = x3 - x1, y3 - y1, z3 - z1
                nx = dy * ez - dz * ey
                ny = dz * ex - dx * ez
                nz = dx * ey - dy * ex
                world = 0.5 * sqrt(nx * nx + ny * ny + nz * nz)
                i0, i1, i2, i3 = uv_ids[us], uv_ids[us + 1], uv_ids[us + 2], uv_ids[us + 3]
                uv = 0.5 * abs((u_arr[i2] - u_arr[i0]) * (v_arr[i3] - v_arr[i1])
                               - (v_arr[i2] - v_arr[i0]) * (u_arr[i3] - u_arr[i1]))
            else:
                world = polygon_area_3d([pts[i] for i in v_ids[vs:v_off]])
                uv = polygon_area_2d([(u_arr[i], v_arr[i]) for i in uv_ids[us:uv_off]])
            if not (min_world <= world < inf and min_uv <= uv < inf):
                continue
            px = uv * tex_area
            dens[f] = sqrt(px / world)
            px_total += px
            world_total += world
            if do_merge and vc == 3 and uc == 3:
                tf.append(f)
                tvs.append(vs)
                tus.append(us)
                tpx.append(px)
                tw.append(world)
            if sid >= 0:
                if face_shell is not None:
                    face_shell[f] = sid
                shell_px[sid] += px
                shell_world[sid] += world

    if do_merge and tf:
        merged = 0
        for i, j in _pair_core(tf, tvs, tus, v_ids, uv_ids, pts, u_arr, v_arr, edge_cnt,
                               len(pts), max_angle, tick=tick):
            dens[tf[i]] = dens[tf[j]] = sqrt((tpx[i] + tpx[j]) / (tw[i] + tw[j]))
            merged += 1
        out['merged_pairs'] = merged

    shell_density = {}
    for sid in range(n_shells):
        if shell_world[sid] > 0.0:
            shell_density[sid] = sqrt(shell_px[sid] / shell_world[sid])
    out['shell_td'] = shell_density
    out['shell_faces'] = dict((sid, shell_faces[sid]) for sid in shell_density)
    out['uv_shell'] = shell_of_uv
    out['islands'] = len(shell_density)
    if per_island:
        for f, sid in enumerate(face_shell):
            if sid >= 0:
                dens[f] = shell_density.get(sid)

    vals = [d for d in dens if d is not None]
    out['valid'] = len(vals)
    out['invalid'] = n_faces - len(vals)
    if vals:
        out['min'] = min(vals)
        out['max'] = max(vals)
        out['avg'] = sqrt(px_total / world_total) if world_total > 0.0 else None
    return out


def analyze_islands(shape, tex_w=None, tex_h=None):
    sel = _om2.MSelectionList()
    sel.add(shape)
    fn = _om2.MFnMesh(sel.getDagPath(0))
    uv_set = fn.currentUVSetName()
    n_faces = fn.numPolygons
    n_uvs = fn.numUVs(uv_set)
    measure = tex_w is not None and tex_h is not None
    out = {'shape': shape, 'uv_set': uv_set, 'n_faces': n_faces, 'n_uvs': n_uvs,
           'shell_faces': {}, 'face_shell': [-1] * n_faces, 'shell_bbox': {},
           'uv_shell': None, 'shell_px': {}, 'shell_world': {}, 'shell_td': {}}
    if n_faces == 0 or n_uvs == 0:
        return out

    u_arr, v_arr = fn.getUVs(uv_set)
    uv_counts, uv_ids = fn.getAssignedUVs(uv_set)
    _, shells = fn.getUvShellsIds(uv_set)
    u_arr, v_arr = list(u_arr), list(v_arr)
    uv_counts, uv_ids, shells = list(uv_counts), list(uv_ids), list(shells)
    if measure:
        pts = [(p.x, p.y, p.z) for p in fn.getPoints(_om2.MSpace.kWorld)]
        v_counts, v_ids = fn.getVertices()
        v_counts, v_ids = list(v_counts), list(v_ids)
        tex_area = float(tex_w) * float(tex_h)

    face_shell = out['face_shell']
    faces = defaultdict(list)
    shell_px = defaultdict(float)
    shell_world = defaultdict(float)
    uv_off = v_off = 0
    for f in range(n_faces):
        uc = uv_counts[f]
        uv_start = uv_off
        uv_off += uc
        if measure:
            vc = v_counts[f]
            v_start = v_off
            v_off += vc
        if uc < 3:
            continue
        sid = shells[uv_ids[uv_start]]
        if sid < 0:
            continue
        faces[sid].append(f)
        face_shell[f] = sid
        if measure and vc >= 3:
            world = polygon_area_3d([pts[i] for i in v_ids[v_start:v_off]])
            uv = polygon_area_2d([(u_arr[i], v_arr[i]) for i in uv_ids[uv_start:uv_off]])
            if MIN_WORLD_AREA <= world < _INF and MIN_UV_AREA <= uv < _INF:
                shell_px[sid] += uv * tex_area
                shell_world[sid] += world

    bbox = {}
    uv_by_shell = defaultdict(list)
    uv_shell = [-1] * len(u_arr)
    for uv in set(uv_ids):
        sid = shells[uv]
        if sid not in faces:
            continue
        uv_shell[uv] = sid
        uv_by_shell[sid].append(uv)
        u = u_arr[uv]
        v = v_arr[uv]
        b = bbox.get(sid)
        if b is None:
            bbox[sid] = [u, v, u, v]
            continue
        if u < b[0]:
            b[0] = u
        elif u > b[2]:
            b[2] = u
        if v < b[1]:
            b[1] = v
        elif v > b[3]:
            b[3] = v

    out['shell_faces'] = dict(faces)
    out['shell_bbox'] = dict((sid, tuple(b)) for sid, b in bbox.items())
    out['uv_shell'] = uv_shell
    out['_uv_by_shell'] = dict(uv_by_shell)
    if measure:
        out['shell_px'] = dict(shell_px)
        out['shell_world'] = dict(shell_world)
        out['shell_td'] = dict((sid, math.sqrt(px / shell_world[sid]))
                               for sid, px in shell_px.items() if shell_world[sid] > 0.0)
    return out


class _UndoOff(object):
    def __enter__(self):
        try:
            self._was = bool(cmds.undoInfo(query=True, state=True))
        except Exception:
            self._was = False
        if self._was:
            cmds.undoInfo(stateWithoutFlush=False)
        return self

    def __exit__(self, *exc):
        if self._was:
            cmds.undoInfo(stateWithoutFlush=True)
        return False


_OWN_NAME = re.compile(r'^(?:.*:)?%s_(?:step\d+|invalid|fast)(?:SG)?\d*$' % PREFIX)
_FACE_SUFFIX = re.compile(r'^\.f\[(\d+)(?::(\d+))?\]$')
_DEFAULT_NODES = frozenset(('initialShadingGroup', 'initialParticleSE', 'lambert1', 'particleCloud1'))


def _is_own_name(name):
    return bool(_OWN_NAME.match(name.split('|')[-1]))


def _node_uuid(node):
    try:
        found = cmds.ls(node, uuid=True)
    except Exception:
        return None
    return found[0] if found else None


def _shape_ident(shape):
    parent = None
    try:
        parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
        if parents:
            parent = _node_uuid(parents[0])
    except Exception:
        pass
    return {'uuid': _node_uuid(shape), 'parent': parent}


def _resolve_shape(path, ident):
    uid = (ident or {}).get('uuid')
    if not uid:
        return path if cmds.objExists(path) else None
    if cmds.objExists(path) and _node_uuid(path) == uid:
        return path
    found = []
    for flags in ({'long': True, 'allPaths': True}, {'long': True}):
        try:
            found = cmds.ls(uid, **flags) or []
            break
        except Exception:
            continue
    found = [f for f in found if '.' not in f.split('|')[-1]]
    if len(found) > 1:
        for f in found:
            try:
                parents = cmds.listRelatives(f, parent=True, fullPath=True) or []
            except Exception:
                continue
            if parents and _node_uuid(parents[0]) == ident.get('parent'):
                return f
    return found[0] if found else None


def _mesh_state(shape):
    try:
        sel = _om2.MSelectionList()
        sel.add(shape)
        fn = _om2.MFnMesh(sel.getDagPath(0))
        uv_set = fn.currentUVSetName()
        return uv_set, int(fn.numPolygons), int(fn.numUVs(uv_set))
    except Exception:
        return None


def _face_count(shape):
    state = _mesh_state(shape)
    if state is not None:
        return state[1]
    try:
        return int(cmds.polyEvaluate(shape, face=True) or 0)
    except Exception:
        return None


class _Progress(object):
    MIN_STEPS = 300

    def __init__(self, title, total):
        self.total = total
        self.on = False
        if total >= self.MIN_STEPS:
            try:
                cmds.progressWindow(title=title, progress=0, maxValue=total,
                                    status='0 / %d' % total, isInterruptable=True)
                self.on = True
            except Exception:
                pass

    def cancelled(self, done):
        if not self.on:
            return False
        try:
            if cmds.progressWindow(query=True, isCancelled=True):
                return True
            if done % 25 == 0:
                cmds.progressWindow(edit=True, progress=done,
                                    status='%d / %d' % (done, self.total))
        except Exception:
            self.on = False
        return False

    def close(self):
        if self.on:
            self.on = False
            try:
                cmds.progressWindow(endProgress=True)
            except Exception:
                pass


class Cancelled(ValueError):
    pass


class _Work(object):
    OPEN_AFTER = 1.0
    REFRESH = 0.12

    def __init__(self, title='Texel density'):
        self.title = title
        self.t0 = self._last = time.perf_counter()
        self.on = False
        self.broken = False

    def update(self, text, fraction):
        now = time.perf_counter()
        if self.broken or now - self._last < self.REFRESH or (not self.on and now - self.t0 < self.OPEN_AFTER):
            return
        self._last = now
        value = int(max(0.0, min(1.0, fraction)) * 1000)
        try:
            if not self.on:
                cmds.progressWindow(title=self.title, progress=value, maxValue=1000,
                                    status=text, isInterruptable=True)
                self.on = True
            elif cmds.progressWindow(query=True, isCancelled=True):
                raise Cancelled('Cancelled.')
            else:
                cmds.progressWindow(edit=True, progress=value, status=text)
        except Cancelled:
            raise
        except Exception:
            self.on = False
            self.broken = True

    def close(self):
        if self.on:
            self.on = False
            try:
                cmds.progressWindow(endProgress=True)
            except Exception:
                pass


def _style_material(mat, rgb, kind):
    if kind == 'flat':
        cmds.setAttr(mat + '.color', 0.0, 0.0, 0.0, type='double3')
        cmds.setAttr(mat + '.diffuse', 0.0)
        cmds.setAttr(mat + '.incandescence', rgb[0], rgb[1], rgb[2], type='double3')
    else:
        cmds.setAttr(mat + '.color', rgb[0], rgb[1], rgb[2], type='double3')
        cmds.setAttr(mat + '.diffuse', 1.0)
        if kind == 'phong':
            for attr, values, flags in (('.specularColor', (PHONG_SPECULAR,) * 3, {'type': 'double3'}),
                                        ('.cosinePower', (PHONG_COSINE_POWER,), {}),
                                        ('.reflectivity', (0.0,), {})):
                try:
                    cmds.setAttr(mat + attr, *values, **flags)
                except Exception:
                    pass


def _make_shader(name, rgb, kind=DEFAULT_SHADER, created=None):
    mat = cmds.shadingNode('phong' if kind == 'phong' else 'lambert', asShader=True, name=name)
    if created is not None:
        created.append(mat)
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + 'SG')
    if created is not None:
        created.append(sg)
    cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', force=True)
    _style_material(mat, rgb, kind)
    return mat, sg


def _recolor_material(mat, rgb, kind):
    cmds.setAttr(mat + ('.incandescence' if kind == 'flat' else '.color'), rgb[0], rgb[1], rgb[2], type='double3')


def _swap_material(sg, old_mat, name, rgb, kind, created):
    mat = cmds.shadingNode('phong' if kind == 'phong' else 'lambert', asShader=True, name=name)
    created.append(mat)
    cmds.connectAttr(mat + '.outColor', sg + '.surfaceShader', force=True)
    _style_material(mat, rgb, kind)
    cmds.delete(old_mat)
    if old_mat in created:
        created.remove(old_mat)
    space = old_mat.rpartition(':')[0]
    try:
        final = cmds.rename(mat, (space + ':' + name) if space else name)
    except Exception:
        return mat
    created[created.index(mat)] = final
    return final


def _bucket_codes(density, unit_scale, lo, span, steps):
    if span <= 0.0:
        mid = steps // 2 + 1
        return array('H', [0 if d is None else mid for d in density])
    top = steps - 1
    return array('H', [0 if d is None else
                       int(max(0.0, min(1.0, (d * unit_scale - lo) / span)) * top + 0.5) + 1
                       for d in density])


def _code_runs(ids, codes):
    runs = []
    prev, code, start = -2, 0, 0
    for f in ids:
        c = codes[f]
        if f != prev + 1 or c != code:
            if prev >= 0:
                runs.append((code, start, prev))
            start, code = f, c
        prev = f
    if prev >= 0:
        runs.append((code, start, prev))
    return runs


def _face_component(shape, first, last):
    return '%s.f[%d]' % (shape, first) if first == last else '%s.f[%d:%d]' % (shape, first, last)


ASSIGN_FAIL_LIMIT = 5
ASSIGN_CHUNK = 2000


def _assign_components(comps, sg, budget=ASSIGN_FAIL_LIMIT, chunk=ASSIGN_CHUNK, step=None, bad=None):
    failed = calls = 0
    todo = [comps[i:i + chunk] for i in range(0, len(comps), chunk)][::-1]
    while todo:
        part = todo.pop()
        calls += 1
        try:
            cmds.sets(part, edit=True, forceElement=sg)
        except Exception:
            if len(part) > 1:
                mid = len(part) // 2
                todo.append(part[mid:])
                todo.append(part[:mid])
                continue
            failed += 1
            if bad is not None:
                bad.append(part[0])
            if failed > budget:
                raise RuntimeError('The faces of %s could not take the override material '
                                   '(the mesh changed?) - press Apply again.'
                                   % _short_name(part[0].partition('.f[')[0]))
            continue
        if step is not None:
            step(len(part))
    return failed, calls


def _delete_nodes(names):
    alive = [n for n in names if cmds.objExists(n)]
    sgs = [n for n in alive if cmds.nodeType(n) == 'shadingEngine']
    others = [n for n in alive if n not in sgs]
    for n in sgs + others:
        try:
            if cmds.objExists(n):
                cmds.delete(n)
        except Exception:
            pass


class _FastError(Exception):
    pass


def _fast_reason(err):
    if isinstance(err, _FastError):
        return str(err)
    text = ' '.join(str(err).split()) or err.__class__.__name__
    return 'vertex color error: ' + text[:80]


def _mesh_fn(shape):
    sel = _om2.MSelectionList()
    sel.add(shape)
    return _om2.MFnMesh(sel.getDagPath(0))


def _fast_blocker(shape):
    try:
        if cmds.listConnections(shape + '.inMesh', source=True, destination=False):
            return 'construction history'
    except Exception:
        return 'history could not be read'
    try:
        if len(cmds.listRelatives(shape, allParents=True) or []) > 1:
            return 'instanced'
    except Exception:
        pass
    return None


def _has_history(shape):
    try:
        return bool(cmds.listConnections(shape + '.inMesh', source=True, destination=False))
    except Exception:
        return False


def _enum_name(shape, attr):
    plug = '%s.%s' % (shape, attr)
    try:
        return cmds.getAttr(plug, asString=True)
    except Exception:
        pass
    try:
        number = int(cmds.getAttr(plug))
        listed = str((cmds.attributeQuery(attr, node=shape, listEnum=True) or [''])[0]).split(':')
        return listed[number].strip() if 0 <= number < len(listed) else None
    except Exception:
        return None


def _set_enum(shape, attr, name):
    plug = '%s.%s' % (shape, attr)
    try:
        cmds.setAttr(plug, name, type='string')
        return True
    except Exception:
        pass
    try:
        listed = cmds.attributeQuery(attr, node=shape, listEnum=True) or []
        for i, entry in enumerate(str(listed[0]).split(':') if listed else []):
            if entry.strip().lower() == str(name).lower():
                cmds.setAttr(plug, i)
                return True
    except Exception:
        pass
    return False


def _vc_save(shape, fn):
    saved = {'colors': None, 'channel': _enum_name(shape, 'displayColorChannel'),
             'blend': _enum_name(shape, 'materialBlend'), 'current': None}
    try:
        saved['colors'] = bool(cmds.getAttr(shape + '.displayColors'))
    except Exception:
        pass
    try:
        current = fn.currentColorSetName()
        if current and current != COLOR_SET and current in list(fn.getColorSetNames()):
            saved['current'] = current
    except Exception:
        pass
    return saved


def _vc_view(shape, saved):
    view = saved.setdefault('view', {})
    for attr, want in FAST_VIEW:
        plug = '%s.%s' % (shape, attr)
        try:
            now = bool(cmds.getAttr(plug))
        except Exception:
            continue
        if now != want:
            try:
                cmds.setAttr(plug, want)
            except Exception:
                continue
            view.setdefault(attr, now)


def _vc_remove_set(shape, saved=None):
    try:
        fn = _mesh_fn(shape)
    except Exception:
        return False
    try:
        names = list(fn.getColorSetNames())
    except Exception:
        names = None
    if names is not None and COLOR_SET not in names:
        return False
    keep = (saved or {}).get('current')
    if keep and (names is None or keep in names):
        try:
            fn.setCurrentColorSetName(keep)
        except Exception:
            pass
    try:
        fn.deleteColorSet(COLOR_SET)
        return True
    except Exception:
        pass
    try:
        cmds.polyColorSet(shape, delete=True, colorSet=COLOR_SET)
        return True
    except Exception:
        return False


def _vc_cleanup(shape, info):
    saved = info.get('saved')
    if saved is None:
        return
    try:
        if not cmds.objExists(shape):
            return
    except Exception:
        return
    _vc_remove_set(shape, saved)
    for attr, key in (('displayColorChannel', 'channel'), ('materialBlend', 'blend')):
        if saved.get(key) is not None:
            _set_enum(shape, attr, saved[key])
    for attr, value in (saved.get('view') or {}).items():
        try:
            cmds.setAttr('%s.%s' % (shape, attr), value)
        except Exception:
            pass
    if saved.get('colors') is not None:
        try:
            cmds.setAttr(shape + '.displayColors', saved['colors'])
        except Exception:
            pass


def _vc_strip(shape):
    if not _vc_remove_set(shape):
        return
    try:
        left = list(_mesh_fn(shape).getColorSetNames())
    except Exception:
        left = None
    if not left:
        try:
            cmds.setAttr(shape + '.displayColors', False)
        except Exception:
            pass
    if _enum_name(shape, 'displayColorChannel') == 'None':
        _set_enum(shape, 'displayColorChannel', 'Diffuse')


def _vc_corner_ids(codes, counts):
    return array('i', chain.from_iterable(map(repeat, codes, counts)))


def _int_array(values):
    try:
        return _om2.MIntArray(values)
    except Exception:
        return _om2.MIntArray(list(values))


def _color_array(palette):
    colors = _om2.MColorArray()
    for r, g, b in palette:
        colors.append(_om2.MColor((r, g, b, 1.0)))
    return colors


def _vc_empty(fn):
    try:
        if fn.numColors(COLOR_SET):
            fn.clearColors(COLOR_SET)
    except Exception:
        pass


def _vc_problem(fn, codes, palette):
    try:
        names = list(fn.getColorSetNames())
    except Exception:
        names = None
    if names is not None and COLOR_SET not in names:
        return 'the color set was not created'
    try:
        stored = fn.getColors(COLOR_SET)
        if len(stored) < len(palette):
            return 'the palette was not stored'
        for k in (0, len(palette) - 1):
            got, want = stored[k], palette[k]
            if max(abs(got[0] - want[0]), abs(got[1] - want[1]), abs(got[2] - want[2])) > 1e-3:
                return 'the palette was stored with other colors'
    except Exception:
        pass
    try:
        n = len(codes)
        for f in sorted(set((0, n // 2, n - 1))):
            if fn.getColorIndex(f, 0, COLOR_SET) != codes[f]:
                return 'the colors were not assigned to the faces as written'
    except Exception:
        pass
    return None


def _vc_write(shape, codes, palette, kind, info):
    fn = _mesh_fn(shape)
    if fn.numPolygons != len(codes):
        raise _FastError('the mesh changed since it was measured')
    have = False
    if info.get('on'):
        try:
            have = COLOR_SET in list(fn.getColorSetNames())
        except Exception:
            have = False
    old = info.get('palette')
    fresh = not have or old is None or len(old) != len(palette)
    if fresh:
        if 'saved' not in info:
            info['saved'] = _vc_save(shape, fn)
        info.update(on=False, codes=None, palette=None, kind=None)
        _vc_remove_set(shape, info['saved'])
        fn.createColorSet(COLOR_SET, False)
        info['on'] = True
        _vc_empty(fn)
        fn.setCurrentColorSetName(COLOR_SET)
        cmds.setAttr(shape + '.displayColors', True)
        _set_enum(shape, 'displayColorChannel', FAST_CHANNEL.get(kind, 'Diffuse'))
        _set_enum(shape, 'materialBlend', FAST_BLEND)
        _vc_view(shape, info['saved'])
        info['kind'] = kind
    elif info.get('kind') != kind:
        _set_enum(shape, 'displayColorChannel', FAST_CHANNEL.get(kind, 'Diffuse'))
        info['kind'] = kind
    wrote = 0
    palette_written = fresh or old != palette
    if palette_written:
        fn.setColors(_color_array(palette), COLOR_SET)
        info['palette'] = list(palette)
    if info.get('codes') is None or info['codes'] != codes:
        counts = list(fn.getVertices()[0])
        ids = _vc_corner_ids(codes, counts)
        try:
            n_corners = int(fn.numFaceVertices)
        except Exception:
            n_corners = len(ids)
        if len(counts) != len(codes) or len(ids) != n_corners:
            raise _FastError('the mesh changed since it was measured')
        fn.assignColors(_int_array(ids), COLOR_SET)
        info['codes'] = codes
        wrote = len(codes)
    if wrote or palette_written:
        problem = _vc_problem(fn, info['codes'], palette)
        if problem:
            raise _FastError(problem)
        if _has_history(shape):
            raise _FastError('history appeared while writing')
        try:
            fn.updateSurface()
        except Exception:
            pass
    return wrote, fresh


class TexelDensityOverride(object):
    def __init__(self):
        self.active = False
        self.saved = {}
        self._ids = {}
        self._sg_ids = {}
        self._created = []
        self._locked = []
        self._gone = []
        self.last_report = None
        self._cache_key = None
        self._cache = {}
        self.island_index = None
        self._shown = None
        self._vtx = None

    @staticmethod
    def _meshes_under(node):
        try:
            pool = [node] + (cmds.listRelatives(node, allDescendents=True,
                                                fullPath=True) or [])
        except Exception:
            return []
        try:
            return cmds.ls(pool, type='mesh', long=True, noIntermediate=True) or []
        except Exception:
            return cmds.ls(pool, type='mesh', long=True) or []

    @staticmethod
    def shapes_from_nodes(nodes):
        shapes, seen = [], set()
        for n in nodes:
            base = n.split('.')[0]
            try:
                if not cmds.objExists(base):
                    continue
                longs = cmds.ls(base, long=True) or []
            except Exception:
                continue
            if not longs:
                continue
            for s in TexelDensityOverride._meshes_under(longs[0]):
                if s in seen:
                    continue
                try:
                    if cmds.getAttr(s + '.intermediateObject'):
                        continue
                except Exception:
                    pass
                seen.add(s)
                shapes.append(s)
        return shapes

    def _snapshot_all(self, shapes):
        result = dict((s, []) for s in shapes)
        transform_to_shapes = defaultdict(list)
        for s in shapes:
            parents = cmds.listRelatives(s, parent=True, fullPath=True) or []
            if parents:
                transform_to_shapes[parents[0]].append(s)

        sgs = set()
        for s in shapes:
            for sg in cmds.listConnections(s, type='shadingEngine') or []:
                sgs.add(sg)

        for sg in sgs:
            if _is_own_name(sg):
                continue
            members = cmds.sets(sg, query=True) or []
            if not members:
                continue
            for ln in cmds.ls(members, long=True) or []:
                node, dot, comp = ln.partition('.')
                suffix = (dot + comp) if comp else None
                if node in result:
                    result[node].append((sg, suffix))
                elif node in transform_to_shapes:
                    for s in transform_to_shapes[node]:
                        result[s].append((sg, suffix))
        return result

    def _capture_ids(self, shapes, analyses):
        self._ids = {}
        for s in shapes:
            ident = _shape_ident(s)
            a = analyses.get(s)
            ident['faces'] = a['n_faces'] if a else _face_count(s)
            self._ids[s] = ident
        self._sg_ids = {}
        for entries in self.saved.values():
            for sg, _suffix in entries:
                if sg not in self._sg_ids:
                    self._sg_ids[sg] = _node_uuid(sg)

    def _follow_paths(self):
        moved, gone = {}, []
        saved, ids = {}, {}
        for old, entries in self.saved.items():
            ident = self._ids.get(old) or {}
            new = _resolve_shape(old, ident)
            if new is None:
                gone.append(old)
            elif new in saved:
                continue
            else:
                if new != old:
                    moved[old] = new
                saved[new] = entries
                ids[new] = ident
        if not moved and not gone:
            return moved
        self.saved, self._ids = saved, ids
        if self._shown is not None:
            self._shown['codes'] = dict((moved.get(s, s), c) for s, c in self._shown['codes'].items()
                                        if moved.get(s, s) in saved)
        if self._vtx is not None:
            self._vtx['shapes'] = dict((moved.get(s, s), info) for s, info in self._vtx['shapes'].items()
                                       if moved.get(s, s) in saved)
        self._gone.extend(_short_name(g) for g in gone)
        old_cache, self._cache = self._cache, {}
        for old, a in old_cache.items():
            new = moved.get(old, old)
            if new in saved:
                self._cache[new] = a if new == old else dict(a, shape=new)
        key = self._cache_key
        if key is not None and not gone:
            self._cache_key = key[:-1] + (tuple(sorted(moved.get(s, s) for s in key[-1])),)
        else:
            self._cache_key = None
        self.island_index = None
        return moved

    def _lock(self, node):
        if node in _DEFAULT_NODES or node in self._locked:
            return
        try:
            if any(cmds.lockNode(node, query=True, lock=True)):
                return
            cmds.lockNode(node, lock=True)
            self._locked.append(node)
        except Exception:
            pass

    def _protect_originals(self):
        wanted = []
        for entries in self.saved.values():
            for sg, _suffix in entries:
                if sg not in wanted:
                    wanted.append(sg)
        for sg in wanted:
            if not cmds.objExists(sg):
                continue
            self._lock(sg)
            for plug in ('surfaceShader', 'volumeShader', 'displacementShader'):
                try:
                    sources = cmds.listConnections(sg + '.' + plug, source=True, destination=False) or []
                except Exception:
                    continue
                for src in sources:
                    self._lock(src)

    def _unprotect(self):
        for node in self._locked:
            try:
                if cmds.objExists(node):
                    cmds.lockNode(node, lock=False)
            except Exception:
                pass
        self._locked = []

    def _find_sg(self, sg):
        if cmds.objExists(sg):
            return sg
        uid = self._sg_ids.get(sg)
        if uid:
            try:
                found = cmds.ls(uid, long=True) or []
            except Exception:
                found = []
            if found:
                return found[0]
        return None

    @staticmethod
    def _restore_plan(entries, n_then, n_now=None):
        objects = [e for e in entries if e[1] is None]
        faces = [e for e in entries if e[1] is not None]
        if n_now is None:
            return objects + faces
        clipped, weight = [], {}
        for sg, suffix in faces:
            m = _FACE_SUFFIX.match(suffix)
            if not m:
                clipped.append((sg, suffix))
                continue
            lo = int(m.group(1))
            hi = int(m.group(2)) if m.group(2) is not None else lo
            weight[sg] = weight.get(sg, 0) + hi - lo + 1
            if lo < n_now:
                hi = min(hi, n_now - 1)
                clipped.append((sg, '.f[%d]' % lo if lo == hi else '.f[%d:%d]' % (lo, hi)))
        if not objects and weight:
            main = max(weight, key=weight.get)
            objects = [(main, None)]
            clipped = [e for e in clipped if e[0] != main]
        return objects + clipped

    def _foreign_shapes(self):
        found, own = set(), set(self.saved)
        for n in self._created:
            try:
                if not cmds.objExists(n) or cmds.nodeType(n) != 'shadingEngine':
                    continue
                members = cmds.sets(n, query=True) or []
                for item in cmds.ls(members, long=True) or []:
                    for s in self.shapes_from_nodes([item.partition('.')[0]]):
                        if s not in own:
                            found.add(s)
            except Exception:
                continue
        return found

    def _delete_td_nodes(self, keep=()):
        keep = set(keep)
        names = [n for n in self._created if n not in keep]
        try:
            names.extend(n for n in (cmds.ls(PREFIX + '_*') or [])
                         if _is_own_name(n) and n not in names and n not in keep)
        except Exception:
            pass
        _delete_nodes(names)
        self._created = [n for n in self._created if n in keep]

    def _restore_impl(self, keep_analysis=False):
        report = {'missing_sgs': [], 'edited': [], 'gone': [], 'foreign': 0}
        self._unprotect()
        self._follow_paths()
        self._fast_release_all()
        report['gone'] = list(self._gone)
        self._gone = []
        missing = set()
        for shape, entries in self.saved.items():
            ident = self._ids.get(shape) or {}
            n_then = ident.get('faces')
            n_now = _face_count(shape) if n_then is not None else None
            edited = n_now is not None and n_now != n_then
            if edited:
                report['edited'].append(_short_name(shape))
            restored = False
            for sg, suffix in self._restore_plan(entries, n_then, n_now if edited else None):
                sg_now = self._find_sg(sg)
                if sg_now is None:
                    missing.add(sg)
                    continue
                target = shape if suffix is None else shape + suffix
                try:
                    cmds.sets(target, edit=True, forceElement=sg_now)
                    restored = True
                except Exception:
                    pass
            if not restored and cmds.objExists('initialShadingGroup'):
                try:
                    cmds.sets(shape, edit=True, forceElement='initialShadingGroup')
                except Exception:
                    pass
        report['missing_sgs'] = sorted(missing)
        foreign = self._foreign_shapes()
        report['foreign'] = len(foreign)
        for s in foreign:
            _vc_strip(s)
        self._delete_td_nodes()
        self.saved, self._ids, self._sg_ids = {}, {}, {}
        self._shown = None
        self.active = False
        if not keep_analysis:
            self._cache_key = None
            self._cache = {}
            self.island_index = None
        self.last_report = report
        return report

    def restore(self):
        with _UndoOff():
            report = self._restore_impl()
        try:
            cmds.refresh(force=True)
        except Exception:
            pass
        return report

    def pause(self):
        if not self.active:
            return None
        with _UndoOff():
            self._follow_paths()
            shapes = list(self.saved)
            self._restore_impl(keep_analysis=True)
        try:
            cmds.refresh(force=True)
        except Exception:
            pass
        return shapes

    def reset_state(self):
        self.saved, self._ids, self._sg_ids = {}, {}, {}
        self._created, self._locked, self._gone = [], [], []
        self._shown = None
        self._vtx = None
        self.active = False
        self._cache_key = None
        self._cache = {}
        self.island_index = None

    def select_islands(self, islands, target='faces', mode='replace', base=None):
        islands = list(islands)
        shapes = sorted(set(s for s, _ in islands))
        for s in shapes:
            a = self._cache.get(s)
            if a is None or not cmds.objExists(s):
                raise ValueError('The analysed mesh is gone - press Apply again.')
            state = _mesh_state(s)
            if state is None:
                state = (a['uv_set'], _face_count(s), a.get('n_uvs'))
            uv_set, n_faces, n_uvs = state
            if (n_faces != a['n_faces'] or uv_set != a['uv_set']
                    or (a.get('n_uvs') is not None and n_uvs != a['n_uvs'])):
                raise ValueError('%s changed since the last Apply (faces, UV set or UVs) - '
                                 'press Apply again.' % _short_name(s))
            if target == 'uvs' and a.get('uv_shell') is None:
                raise ValueError('UV islands are not available for %s.' % _short_name(s))
        comps = island_components(self._cache, islands, target)
        base = list(base or [])
        if mode in ('add', 'remove') and not any('.' in n.split('|')[-1] for n in base):
            if mode == 'remove':
                raise ValueError('Nothing to remove from: select some faces or UVs first '
                                 '(only objects are selected).')
            mode = 'replace'
        with _UndoOff():
            if mode in ('add', 'remove'):
                cmds.select(base, replace=True)
                if comps:
                    if mode == 'add':
                        cmds.select(comps, add=True)
                    else:
                        cmds.select(comps, deselect=True)
            elif comps:
                cmds.select(comps, replace=True)
            else:
                cmds.select(clear=True)
        return len(comps)

    @staticmethod
    def select_by_pixels(shapes, tex_w, tex_h, axis, op, a, b=None,
                         target='faces', mode='replace'):
        if target not in ('faces', 'uvs'):
            raise ValueError('Unknown selection target: %r' % (target,))
        if mode not in ('replace', 'add', 'remove'):
            raise ValueError('Unknown selection mode: %r' % (mode,))
        shapes = [s for s in shapes if cmds.objExists(s)]
        if not shapes:
            raise ValueError('No valid polygon meshes to search.')
        tex_w = max(1, int(tex_w))
        tex_h = max(1, int(tex_h))

        analyses = dict((s, analyze_islands(s)) for s in shapes)
        matches, stats = islands_by_pixels(analyses, tex_w, tex_h, axis, op, a, b)
        comps = island_components(analyses, matches, target)
        res = dict(stats)
        res.update(matched=len(matches), components=len(comps), shapes=len(shapes),
                   uv_sets=sorted(set(an['uv_set'] for an in analyses.values())))

        if comps:
            if mode == 'remove':
                cmds.select(comps, deselect=True)
            else:
                replace = mode == 'replace'
                if not replace:
                    current = cmds.ls(selection=True, long=True) or []
                    replace = not any('.' in n.split('|')[-1] for n in current)
                if replace:
                    cmds.select(comps, replace=True)
                else:
                    cmds.select(comps, add=True)
        elif mode == 'replace':
            parents = []
            for s in shapes:
                for p in cmds.listRelatives(s, parent=True, fullPath=True) or []:
                    if p and p not in parents:
                        parents.append(p)
            if parents:
                cmds.select(parents, replace=True)
        return res

    @staticmethod
    def read_selection():
        spec = {}
        cache = {}
        first_path = {}

        def shapes_of(node):
            if node not in cache:
                cache[node] = TexelDensityOverride.shapes_from_nodes([node])
            return cache[node]

        def entry(shape):
            uid = _node_uuid(shape)
            if uid is not None:
                shape = first_path.setdefault(uid, shape)
            return spec.setdefault(shape, {'whole': False, 'faces': [], 'uvs': []})

        def add(node, kind, ranges):
            shapes = shapes_of(node)
            if not shapes:
                return
            e = entry(shapes[0])
            if ranges is None:
                e['whole'] = True
            else:
                e['faces' if kind == 'f' else 'uvs'].extend(ranges)

        convert = []
        for item in cmds.ls(selection=True, long=True) or []:
            parsed = parse_component(item)
            if parsed is None:
                for s in shapes_of(item):
                    entry(s)['whole'] = True
            elif parsed[1] in ('f', 'map'):
                add(*parsed)
            elif parsed[1] in ('vtx', 'e', 'vtxFace'):
                convert.append(item)
        if convert:
            try:
                around = cmds.polyListComponentConversion(convert, toFace=True) or []
            except Exception:
                around = []
            for item in around:
                parsed = parse_component(item)
                if parsed is not None and parsed[1] == 'f':
                    add(*parsed)
        return spec

    @staticmethod
    def _analyze_spec(spec, tex_w, tex_h):
        return dict((s, analyze_islands(s, tex_w, tex_h)) for s in spec if cmds.objExists(s))

    @staticmethod
    def measure_selection(spec, tex_w, tex_h):
        analyses = TexelDensityOverride._analyze_spec(spec, max(1, int(tex_w)), max(1, int(tex_h)))
        islands, skipped = selection_islands(analyses, spec)
        plan = plan_texel_density(analyses, islands, 1.0)
        return {'count': len(islands), 'skipped': skipped,
                'avg': plan['avg'], 'min': plan['min'], 'max': plan['max']}

    @staticmethod
    def set_texel_density(spec, tex_w, tex_h, target, overall=False):
        target = float(target)
        if not (0.0 < target < float('inf')):
            raise ValueError('The target texel density must be greater than 0.')
        tex_w = max(1, int(tex_w))
        tex_h = max(1, int(tex_h))
        analyses = TexelDensityOverride._analyze_spec(spec, tex_w, tex_h)
        if not analyses:
            raise ValueError('The selected meshes are gone.')
        islands, skipped = selection_islands(analyses, spec)
        plan = plan_texel_density(analyses, islands, target, overall)
        res = {'target': target, 'overall': bool(overall), 'count': len(islands),
               'skipped': skipped, 'avg': plan['avg'], 'min': plan['min'], 'max': plan['max'],
               'scale_min': None, 'scale_max': None, 'changed': 0, 'unchanged': 0,
               'failed': 0, 'error': None, 'after_avg': None, 'after_min': None,
               'after_max': None, 'deviation': None, 'cancelled': False,
               'edited_shapes': []}
        if not islands:
            return res
        scales = [e[2] for e in plan['entries']]
        res['scale_min'], res['scale_max'] = min(scales), max(scales)
        todo = [e for e in plan['entries'] if abs(e[2] - 1.0) > TD_SCALE_EPS]
        res['unchanged'] = len(islands) - len(todo)

        edited = set()
        if todo:
            if overall:
                by_shape = defaultdict(list)
                for s, sid, _scale, _pu, _pv in todo:
                    by_shape[s].append(sid)
                jobs = [(s, sids, todo[0][2], todo[0][3], todo[0][4])
                        for s, sids in sorted(by_shape.items())]
            else:
                jobs = [(s, [sid], scale, pu, pv) for s, sid, scale, pu, pv in todo]
            cmds.undoInfo(openChunk=True)
            progress = _Progress('Set texel density', len(jobs))
            try:
                for n, (shape, sids, scale, pu, pv) in enumerate(jobs):
                    if progress.cancelled(n):
                        res['cancelled'] = True
                        break
                    comps = island_components(analyses, [(shape, sid) for sid in sids], 'uvs')
                    try:
                        cmds.polyEditUV(comps, pivotU=pu, pivotV=pv, scaleU=scale, scaleV=scale)
                    except Exception as e:
                        res['failed'] += len(sids)
                        if res['error'] is None:
                            res['error'] = str(e)
                    else:
                        res['changed'] += len(sids)
                        edited.add(shape)
            finally:
                progress.close()
                cmds.undoInfo(closeChunk=True)
        res['edited_shapes'] = sorted(edited)

        after = dict(analyses)
        try:
            for s in edited:
                after[s] = analyze_islands(s, tex_w, tex_h)
            now = []
            for s, sid in islands:
                face = analyses[s]['shell_faces'][sid][0]
                nsid = after[s]['face_shell'][face]
                if nsid in after[s]['shell_td']:
                    now.append((s, nsid))
            measured = plan_texel_density(after, now, target, overall)
        except Exception:
            return res
        res.update(after_avg=measured['avg'], after_min=measured['min'], after_max=measured['max'])
        if measured['avg'] is not None:
            if overall:
                res['deviation'] = abs(measured['avg'] / target - 1.0)
            else:
                res['deviation'] = max(abs(measured['min'] / target - 1.0),
                                       abs(measured['max'] / target - 1.0))
        return res

    def apply(self, shapes, tex_w, tex_h, per_island, unit_scale, auto_range,
              manual_min, manual_max, steps, gradient, invert, reanalyze=True,
              merge_tris=False, max_angle=DEFAULT_PAIR_ANGLE, refresh=None,
              shader=DEFAULT_SHADER, rebuild=False, display=None):
        work = _Work()
        try:
            return self._apply(work, shapes, tex_w, tex_h, per_island, unit_scale, auto_range,
                               manual_min, manual_max, steps, gradient, invert, reanalyze,
                               merge_tris, max_angle, refresh, shader, rebuild, display)
        finally:
            work.close()

    def _apply(self, work, shapes, tex_w, tex_h, per_island, unit_scale, auto_range,
               manual_min, manual_max, steps, gradient, invert, reanalyze,
               merge_tris, max_angle, refresh, shader, rebuild, display):
        t_start = time.perf_counter()
        timing = dict.fromkeys(('measure', 'plan', 'snapshot', 'shaders', 'assign', 'index', 'refresh'), 0.0)
        shader = DEFAULT_SHADER if shader is None else str(shader).strip().lower()
        if shader not in SHADER_KINDS:
            raise ValueError('Unknown shader type "%s" - use one of: %s.' % (shader, ', '.join(SHADER_KINDS)))
        display = DEFAULT_DISPLAY if display is None else str(display).strip().lower()
        if display not in DISPLAY_MODES:
            raise ValueError('Unknown display mode "%s" - use one of: %s.' % (display, ', '.join(DISPLAY_MODES)))
        shapes = list(dict.fromkeys(shapes))
        refresh = list(refresh or ())
        restored = None
        if self.active:
            moved = self._follow_paths()
            shapes = [moved.get(s, s) for s in shapes]
            refresh = [moved.get(s, s) for s in refresh]
        shapes = [s for s in dict.fromkeys(shapes) if cmds.objExists(s)]
        if not shapes:
            if self.active:
                with _UndoOff():
                    self._restore_impl()
            raise ValueError('No valid polygon meshes to process.')
        tex_w = max(1, int(tex_w))
        tex_h = max(1, int(tex_h))
        steps = max(2, int(steps))
        unit = _unit_label(unit_scale)

        merging = bool(merge_tris) and not per_island
        key = (tex_w, tex_h, bool(per_island), merging,
               round(float(max_angle), 4) if merging else 0.0, tuple(sorted(shapes)))

        def measure(s, k):
            def tick(what, done, total):
                work.update('%s  %s  (%d of %d)' % (what.capitalize(), _short_name(s), k + 1, len(shapes)),
                            (k + done / float(max(1, total))) / len(shapes))
            return analyze_mesh(s, tex_w, tex_h, per_island, merge_tris, max_angle, tick=tick)

        t0 = time.perf_counter()
        try:
            if reanalyze or key != self._cache_key:
                analyses = dict((s, measure(s, k)) for k, s in enumerate(shapes))
                fresh = True
            else:
                analyses, fresh = dict(self._cache), False
                for k, s in enumerate(shapes):
                    a = analyses.get(s)
                    if a is None or s in refresh or _face_count(s) != a['n_faces']:
                        analyses[s] = measure(s, k)
                        fresh = True
        except Cancelled:
            raise Cancelled('Cancelled - nothing was changed.')
        timing['measure'] = time.perf_counter() - t0

        mins = [analyses[s]['min'] for s in shapes if analyses[s]['min'] is not None]
        maxs = [analyses[s]['max'] for s in shapes if analyses[s]['max'] is not None]
        no_valid = not mins
        if auto_range:
            if no_valid:
                lo, hi = 0.0, 1.0
            else:
                lo, hi = min(mins) * unit_scale, max(maxs) * unit_scale
        else:
            lo, hi = float(manual_min), float(manual_max)
            if not (abs(lo) < _INF and abs(hi) < _INF):
                raise ValueError('Manual range: Min and Max must be real numbers.')
            if hi <= lo:
                raise ValueError('Manual range: Max must be greater than Min.')
        span = hi - lo

        t0 = time.perf_counter()
        codes = dict((s, _bucket_codes(analyses[s]['density'], unit_scale, lo, span, steps)) for s in shapes)
        timing['plan'] = time.perf_counter() - t0

        with _UndoOff():
            try:
                if self.active and set(shapes) != set(self.saved):
                    restored = self._restore_impl()
                if not self.active:
                    t0 = time.perf_counter()
                    self.saved = self._snapshot_all(shapes)
                    self._capture_ids(shapes, analyses)
                    self.active = True
                    timing['snapshot'] = time.perf_counter() - t0
                paint = self._paint(shapes, codes, steps, gradient, invert, shader, rebuild, work, timing, display)
                if paint['mode'] == 'full':
                    self._protect_originals()
            except Cancelled:
                try:
                    self._restore_impl()
                except Exception:
                    pass
                raise Cancelled('Cancelled - the original materials were put back.')
            except Exception:
                try:
                    self._restore_impl()
                except Exception:
                    pass
                raise

        self._cache = analyses
        self._cache_key = key
        t0 = time.perf_counter()
        if fresh or self.island_index is None:
            self.island_index = IslandIndex(analyses, shapes)
        self.island_index.set_scale(unit_scale)
        timing['index'] = time.perf_counter() - t0
        t0 = time.perf_counter()
        try:
            cmds.refresh(force=True)
        except Exception:
            pass
        timing['refresh'] = time.perf_counter() - t0

        objects = []
        for s in shapes:
            a = analyses[s]
            objects.append({
                'name': _short_name(s), 'uv_set': a['uv_set'], 'faces': a['n_faces'],
                'invalid': a['invalid'], 'islands': a['islands'],
                'merged': a['merged_pairs'],
                'min': a['min'] * unit_scale if a['min'] is not None else None,
                'avg': a['avg'] * unit_scale if a['avg'] is not None else None,
                'max': a['max'] * unit_scale if a['max'] is not None else None,
            })
        timing['total'] = time.perf_counter() - t_start
        return {
            'range': (lo, hi), 'unit': unit, 'objects': objects, 'no_valid': no_valid,
            'invalid_total': sum(o['invalid'] for o in objects),
            'auto': bool(auto_range), 'per_island': bool(per_island), 'shader': shader,
            'display': paint['display'],
            'islands_total': len(self.island_index),
            'restored': restored,
            'timing': timing, 'paint': paint,
        }

    def _can_update(self, state, shapes, codes):
        if not state or not self.active:
            return False
        known = state['codes']
        if set(known) != set(shapes) or any(len(known[s]) != len(codes[s]) for s in shapes):
            return False
        return all(cmds.objExists(n) for n in list(state['sg'].values()) + list(state['mat'].values()))

    def _drop_bucket(self, state, code):
        for node in (state['sg'].pop(code, None), state['mat'].pop(code, None)):
            if node is None:
                continue
            try:
                if cmds.objExists(node):
                    cmds.delete(node)
            except Exception:
                pass
            if node in self._created:
                self._created.remove(node)
        state['color'].pop(code, None)

    def _fast_names(self):
        v = self._vtx or {}
        return [n for n in (v.get('sg'), v.get('mat')) if n]

    def _fast_release(self, shape):
        info = self._vtx['shapes'].pop(shape, None) if self._vtx else None
        if info is not None:
            _vc_cleanup(shape, info)

    def _fast_release_all(self):
        if self._vtx:
            for s in list(self._vtx['shapes']):
                self._fast_release(s)
        self._vtx = None

    def _fast_drop(self):
        names = self._fast_names()
        self._fast_release_all()
        _delete_nodes(names)
        self._created = [n for n in self._created if n not in names]

    def _paint(self, shapes, codes, steps, gradient, invert, shader, rebuild, work, timing, display=None):
        display = DEFAULT_DISPLAY if display is None else display
        top = float(steps - 1)
        palette = [INVALID_COLOR] + [gradient_color(k / top, gradient, invert) for k in range(steps)]

        if self._shown is None and self._vtx is None:
            self._delete_td_nodes()
        fast, fallback = [], []
        if display == 'fast':
            for s in shapes:
                if not len(codes[s]):
                    continue
                why = _fast_blocker(s)
                if why is None:
                    fast.append(s)
                else:
                    fallback.append((s, why))
        if self._vtx:
            staying = set(fast)
            for s in [s for s in self._vtx['shapes'] if s not in staying]:
                self._fast_release(s)

        rep = {'full': False, 'written': 0, 'calls': 0, 'failed': {}}
        if fast:
            rep = self._paint_fast(fast, codes, palette, shader, rebuild, work, timing)
            fallback.extend(rep['failed'].items())
        on_fast = [s for s in fast if s not in rep['failed']]
        on_set = set(on_fast)
        slow = [s for s in shapes if s not in on_set]

        mat = None
        if slow:
            mat = self._paint_materials(slow, codes, steps, gradient, invert, shader, rebuild, work, timing)
        elif self._shown is not None:
            self._delete_td_nodes(keep=self._fast_names())
            self._shown = None
        if not on_fast and self._vtx is not None:
            self._fast_drop()

        fast_faces = sum(len(codes[s]) for s in on_fast)
        slow_faces = sum(len(codes[s]) for s in slow)
        slow_changed = mat['changed'] if mat else 0
        return {
            'mode': 'full' if rep['full'] or (mat is not None and mat['mode'] == 'full') else 'incremental',
            'faces': fast_faces + slow_faces, 'changed': rep['written'] + slow_changed,
            'components': mat['components'] if mat else 0,
            'calls': rep['calls'] + (mat['calls'] if mat else 0),
            'failed': mat['failed'] if mat else 0,
            'display': 'materials' if not on_fast else ('fast' if not slow else 'mixed'),
            'fast': len(on_fast), 'slow': len(slow), 'fast_faces': fast_faces, 'slow_faces': slow_faces,
            'written': rep['written'], 'slow_changed': slow_changed,
            'fallback': [(_short_name(s), why) for s, why in fallback],
        }

    def _paint_fast(self, shapes, codes, palette, shader, rebuild, work, timing):
        v = self._vtx
        if v is not None and rebuild:
            self._fast_drop()
            v = None
        if v is None:
            v = self._vtx = {'sg': None, 'mat': None, 'kind': None, 'shapes': {}}
        full = False

        t0 = time.perf_counter()
        names = self._fast_names()
        if not (len(names) == 2 and all(cmds.objExists(n) for n in names)):
            try:
                names = names + [n for n in (cmds.ls(FAST_NAME + '*') or []) if _is_own_name(n) and n not in names]
            except Exception:
                pass
            _delete_nodes(names)
            self._created = [n for n in self._created if n not in names]
            v['mat'], v['sg'] = _make_shader(FAST_NAME, FAST_BASE_COLOR, shader, self._created)
            v['kind'] = shader
            for info in v['shapes'].values():
                info['assigned'] = False
            full = True
        elif v['kind'] != shader:
            v['mat'] = _swap_material(v['sg'], v['mat'], FAST_NAME, FAST_BASE_COLOR, shader, self._created)
            v['kind'] = shader
        timing['shaders'] += time.perf_counter() - t0

        t0 = time.perf_counter()
        failed, written, calls, todo = {}, 0, 0, []
        for k, s in enumerate(shapes):
            work.update('Writing vertex colors  %s  (%d of %d)' % (_short_name(s), k + 1, len(shapes)),
                        k / float(len(shapes)))
            info = v['shapes'].get(s)
            if info is None:
                info = v['shapes'][s] = {'assigned': False}
            try:
                n, fresh = _vc_write(s, codes[s], palette, shader, info)
            except Exception as e:
                failed[s] = _fast_reason(e)
                self._fast_release(s)
                continue
            written += n
            full = full or fresh
            if not info['assigned']:
                todo.append(s)
        if todo:
            bad = []
            _, c = _assign_components(todo, v['sg'], budget=len(todo), bad=bad)
            calls += c
            for s in todo:
                if s in bad:
                    failed[s] = 'the shared material could not be assigned'
                    self._fast_release(s)
                else:
                    v['shapes'][s]['assigned'] = True
        timing['assign'] += time.perf_counter() - t0
        return {'full': full, 'written': written, 'calls': calls, 'failed': failed}

    def _paint_materials(self, shapes, codes, steps, gradient, invert, shader, rebuild, work, timing):
        top = float(steps - 1)

        def color_of(code):
            return INVALID_COLOR if code == 0 else gradient_color((code - 1) / top, gradient, invert)

        def name_of(code):
            return PREFIX + '_invalid' if code == 0 else '%s_step%03d' % (PREFIX, code - 1)

        state = self._shown
        incremental = not rebuild and self._can_update(state, shapes, codes)
        if not incremental:
            self._delete_td_nodes(keep=self._fast_names())
            state = {'sg': {}, 'mat': {}, 'color': {}, 'kind': shader, 'codes': {}}
        sg_of, mat_of, color_at = state['sg'], state['mat'], state['color']

        t0 = time.perf_counter()
        todo = defaultdict(list)
        faces_total = changed = 0
        for s in shapes:
            new = codes[s]
            old = state['codes'].get(s) if incremental else None
            faces_total += len(new)
            ids = range(len(new)) if old is None else [f for f, (a, b) in enumerate(zip(old, new)) if a != b]
            changed += len(ids)
            for code, first, last in _code_runs(ids, new):
                todo[code].append(_face_component(s, first, last))
        timing['plan'] += time.perf_counter() - t0

        t0 = time.perf_counter()
        for code in sorted(sg_of):
            rgb = color_of(code)
            if state['kind'] != shader:
                mat_of[code] = _swap_material(sg_of[code], mat_of[code], name_of(code), rgb, shader, self._created)
                color_at[code] = rgb
            elif rgb != color_at[code]:
                _recolor_material(mat_of[code], rgb, shader)
                color_at[code] = rgb
        state['kind'] = shader
        for code in sorted(todo):
            if code not in sg_of:
                rgb = color_of(code)
                mat_of[code], sg_of[code] = _make_shader(name_of(code), rgb, shader, self._created)
                color_at[code] = rgb
        timing['shaders'] += time.perf_counter() - t0

        t0 = time.perf_counter()
        total = sum(len(v) for v in todo.values())
        done = [0]

        def step(n):
            done[0] += n
            work.update('Painting faces  (%d of %d components)' % (done[0], total), done[0] / float(max(1, total)))

        failed = calls = 0
        for code in sorted(todo):
            f, c = _assign_components(todo[code], sg_of[code], budget=ASSIGN_FAIL_LIMIT - failed, step=step)
            failed += f
            calls += c
        in_use = set()
        for s in shapes:
            in_use.update(set(codes[s]))
        for code in [c for c in sg_of if c not in in_use]:
            self._drop_bucket(state, code)
        timing['assign'] += time.perf_counter() - t0

        state['codes'] = codes
        self._shown = state if not failed else None
        return {'mode': 'incremental' if incremental else 'full', 'faces': faces_total, 'changed': changed,
                'components': total, 'calls': calls, 'failed': failed}


THEME = {
    'bg': '#232529',
    'bar': '#1e2023',
    'card': '#2c2f34',
    'card_hi': '#363940',
    'line': '#3c4048',
    'line_hover': '#59606b',
    'input': '#1a1c1f',
    'text': '#e8eaed',
    'muted': '#9aa1ab',
    'faint': '#69707b',
    'btn': '#3c4048',
    'btn_hover': '#484d56',
    'btn_press': '#31353b',
    'accent': '#63b8fa',
    'accent_hi': '#88ccff',
    'accent_lo': '#469fe6',
    'accent_ink': '#0b1a29',
    'track_off': '#4c515a',
    'scroll': '#464b54',
    'scroll_hover': '#5b626d',
    'error': '#ff8f89',
    'error_bg': '#3b2526',
    'error_line': '#7b3d3f',
}


def _mix(c1, c2, t):
    a = [int(c1[k:k + 2], 16) for k in (1, 3, 5)]
    b = [int(c2[k:k + 2], 16) for k in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def _qt_flag(group, name):
    scoped = getattr(QtCore.Qt, group, None)
    if scoped is not None and hasattr(scoped, name):
        return getattr(scoped, name)
    return getattr(QtCore.Qt, name)


def _event_xy(ev):
    try:
        p = ev.position()
    except AttributeError:
        p = ev.pos()
    return p.x(), p.y()


if QtWidgets is not None:
    class TexelHistogramWidget(QtWidgets.QWidget):
        PAD_L, PAD_R, PAD_T, PAD_B = 8, 8, 22, 36
        BAR_PX = 6
        HEIGHT = 170
        DEFAULT_MESSAGE = 'Press Apply to see the texel density of every UV island'
        HELP = ('Drag: select the islands in that texel density range\n'
                'Click: select the islands of one bar\n'
                'Shift+drag: add     Ctrl+drag: remove\n'
                'Right-click: clear the selection\n'
                'Mouse wheel: zoom     Middle-drag: pan     Double-click: show everything')

        def __init__(self, parent=None):
            QtWidgets.QWidget.__init__(self, parent)
            self.setMinimumHeight(self.HEIGHT)
            self.setFixedHeight(self.HEIGHT)
            policy = getattr(QtWidgets.QSizePolicy, 'Policy', QtWidgets.QSizePolicy)
            self.setSizePolicy(policy.Expanding, policy.Fixed)
            self.setMouseTracking(True)
            self.setCursor(_qt_flag('CursorShape', 'CrossCursor'))
            self.setToolTip(self.HELP)

            self._vals = []
            self._unit = 'px/cm'
            self._crange = None
            self._gradient = 0
            self._invert = False
            self._view = (0.0, 1.0)
            self._view_key = None
            self._zoomed = False
            self._sel = None
            self._sel_count = None
            self._sel_mode = 'replace'
            self._hover_x = None
            self._drag = None
            self._pan = None
            self._bins = None
            self._message = self.DEFAULT_MESSAGE

            self.on_press = None
            self.on_select = None
            self.on_clear = None
            self.on_double = None
            self.throttle_ms = 45

            self._timer = QtCore.QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self._flush)

        def sizeHint(self):
            return QtCore.QSize(380, self.HEIGHT)

        def minimumSizeHint(self):
            return QtCore.QSize(240, self.HEIGHT)

        def set_data(self, vals, unit, color_range, gradient, invert, message=None):
            same = vals is self._vals or vals == self._vals
            self._vals = vals
            self._unit = unit
            self._crange = color_range
            self._gradient = gradient
            self._invert = invert
            self._message = message if message is not None else self.DEFAULT_MESSAGE
            if not same:
                self._sel = None
                self._sel_count = None
            key = (unit, tuple(color_range) if color_range else None, len(vals))
            if key != self._view_key:
                self._view_key = key
                self._zoomed = False
            if not self._zoomed:
                self._view = self._auto_view()
            self._bins = None
            self.update()

        def clear_data(self, color_range=None, gradient=0, invert=False, message=None, unit=None):
            self.set_data([], unit or self._unit, color_range, gradient, invert, message)

        def set_selection(self, lo, hi, count=None, mode='replace'):
            self._sel = (lo, hi)
            self._sel_count = count
            self._sel_mode = mode
            self.update()

        def clear_selection(self):
            self._sel = None
            self._sel_count = None
            self._sel_mode = 'replace'
            self.update()

        def selection(self):
            return self._sel

        def view_range(self):
            return self._view

        def set_view(self, lo, hi):
            self._view = (lo, hi)
            self._zoomed = True
            self._bins = None
            self.update()

        def fit_all(self):
            self._zoomed = False
            if self._vals:
                lo, hi = self._vals[0], self._vals[-1]
            elif self._crange:
                lo, hi = self._crange
            else:
                lo, hi = 0.0, 1.0
            if self._crange:
                lo, hi = min(lo, self._crange[0]), max(hi, self._crange[1])
            pad = max(hi - lo, 1e-9) * 0.02
            lo = max(0.0, lo - pad) if lo >= 0.0 else lo - pad
            self._view = (lo, hi + pad if hi > lo else hi + 0.5)
            self._bins = None
            self.update()

        def _auto_view(self):
            n = len(self._vals)
            dmin = self._vals[0] if n else None
            dmax = self._vals[-1] if n else None
            if self._crange:
                clo, chi = self._crange
            elif n:
                clo, chi = dmin, dmax
            else:
                clo, chi = 0.0, 1.0
            core_lo, core_hi = robust_core(self._vals)
            return default_view(dmin, dmax, clo, chi, core_lo, core_hi)

        def _plot(self):
            return QtCore.QRect(self.PAD_L, self.PAD_T,
                                max(20, self.width() - self.PAD_L - self.PAD_R),
                                max(20, self.height() - self.PAD_T - self.PAD_B))

        def _nbins(self):
            return max(8, min(240, self._plot().width() // self.BAR_PX))

        def _x_to_v(self, x):
            pl = self._plot()
            lo, hi = self._view
            t = (x - pl.left()) / float(pl.width())
            return lo + max(0.0, min(1.0, t)) * (hi - lo)

        def _v_to_x(self, v):
            pl = self._plot()
            lo, hi = self._view
            return pl.left() + (v - lo) / (hi - lo) * pl.width()

        def _bin_at(self, x):
            pl = self._plot()
            n = self._nbins()
            return max(0, min(n - 1, int((x - pl.left()) / (pl.width() / float(n)))))

        def _get_bins(self):
            n = self._nbins()
            key = (self._view, n, len(self._vals))
            if self._bins is None or self._bins[0] != key:
                counts, below, above = histogram_bins(self._vals, self._view[0], self._view[1], n)
                self._bins = (key, counts, below, above)
            return self._bins[1], self._bins[2], self._bins[3]

        @staticmethod
        def _mode(mods):
            shift = bool(mods & _qt_flag('KeyboardModifier', 'ShiftModifier'))
            ctrl = bool(mods & _qt_flag('KeyboardModifier', 'ControlModifier'))
            if ctrl and not shift:
                return 'remove'
            return 'add' if shift else 'replace'

        def _drag_range(self):
            d = self._drag
            a, b = sorted((d['v0'], d['v1']))
            vlo, vhi = self._view
            i0 = 0 if a <= vlo else bisect.bisect_left(self._vals, a)
            i1 = len(self._vals) if b >= vhi else bisect.bisect_right(self._vals, b)
            return i0, i1, (float('-inf') if a <= vlo else a), (float('inf') if b >= vhi else b)

        def _bin_range(self, i):
            n = self._nbins()
            vlo, vhi = self._view
            w = (vhi - vlo) / n
            i0, i1 = bin_slice(self._vals, vlo, vhi, n, i)
            lo = float('-inf') if i <= 0 else vlo + w * i
            hi = float('inf') if i >= n - 1 else vlo + w * (i + 1)
            return i0, i1, lo, hi

        def _emit(self, i0, i1, lo, hi, mode, final):
            self._sel = (lo, hi)
            if self.on_select:
                self.on_select(i0, i1, lo, hi, mode, final)
            self.update()

        def _flush(self):
            if self._drag is not None and self._drag['moved']:
                i0, i1, lo, hi = self._drag_range()
                self._emit(i0, i1, lo, hi, self._drag['mode'], False)

        def mousePressEvent(self, ev):
            x, _y = _event_xy(ev)
            btn = ev.button()
            if btn == _qt_flag('MouseButton', 'LeftButton'):
                if not self._vals:
                    return
                mode = self._mode(ev.modifiers())
                v = self._x_to_v(x)
                self._drag = {'v0': v, 'v1': v, 'x0': x, 'mode': mode, 'moved': False}
                if self.on_press:
                    self.on_press(mode)
                self.update()
            elif btn == _qt_flag('MouseButton', 'MiddleButton'):
                self._pan = (x, self._view)
                self.setCursor(_qt_flag('CursorShape', 'ClosedHandCursor'))
            elif btn == _qt_flag('MouseButton', 'RightButton'):
                self.clear_selection()
                if self.on_clear:
                    self.on_clear()
            ev.accept()

        def mouseMoveEvent(self, ev):
            x, _y = _event_xy(ev)
            self._hover_x = x
            buttons = ev.buttons()
            if self._drag is not None and not (buttons & _qt_flag('MouseButton', 'LeftButton')):
                self._finish_drag(x)
            if self._pan is not None and not (buttons & _qt_flag('MouseButton', 'MiddleButton')):
                self._pan = None
                self.setCursor(_qt_flag('CursorShape', 'CrossCursor'))
            if self._drag is not None:
                d = self._drag
                d['v1'] = self._x_to_v(x)
                if not d['moved'] and abs(x - d['x0']) >= 3:
                    d['moved'] = True
                if d['moved']:
                    a, b = sorted((d['v0'], d['v1']))
                    self._sel = (a, b)
                    if not self._timer.isActive():
                        self._timer.start(int(self.throttle_ms))
            elif self._pan is not None:
                x0, (vlo, vhi) = self._pan
                dv = (x - x0) / float(self._plot().width()) * (vhi - vlo)
                self._view = (vlo - dv, vhi - dv)
                self._zoomed = True
                self._bins = None
            self.update()
            ev.accept()

        def _finish_drag(self, x):
            d = self._drag
            if d is None:
                return
            self._timer.stop()
            d['v1'] = self._x_to_v(x)
            if d['moved']:
                i0, i1, lo, hi = self._drag_range()
            else:
                i0, i1, lo, hi = self._bin_range(self._bin_at(d['x0']))
            self._drag = None
            self._emit(i0, i1, lo, hi, d['mode'], True)

        def mouseReleaseEvent(self, ev):
            x, _y = _event_xy(ev)
            btn = ev.button()
            if btn == _qt_flag('MouseButton', 'LeftButton') and self._drag is not None:
                self._finish_drag(x)
            elif btn == _qt_flag('MouseButton', 'MiddleButton'):
                self._pan = None
                self.setCursor(_qt_flag('CursorShape', 'CrossCursor'))
            ev.accept()

        def mouseDoubleClickEvent(self, ev):
            if self._vals and self.on_double:
                self.on_double()
            self.fit_all()
            ev.accept()

        def hideEvent(self, ev):
            self._timer.stop()
            self._drag = None
            self._pan = None
            QtWidgets.QWidget.hideEvent(self, ev)

        def wheelEvent(self, ev):
            x, _y = _event_xy(ev)
            steps = ev.angleDelta().y() / 120.0
            if steps == 0:
                return
            lo, hi = self._view
            full_lo = self._vals[0] if self._vals else lo
            full_hi = self._vals[-1] if self._vals else hi
            full_span = max(full_hi - full_lo, (self._crange[1] - self._crange[0]) if self._crange else 0.0, 1e-6)
            span = hi - lo
            new_span = span * (0.8 ** steps)
            new_span = max(full_span * 0.004, min(full_span * 6.0, new_span))
            c = self._x_to_v(x)
            t = (c - lo) / span if span > 0 else 0.5
            self._view = (c - t * new_span, c - t * new_span + new_span)
            self._zoomed = True
            self._bins = None
            self.update()
            ev.accept()

        def leaveEvent(self, ev):
            self._hover_x = None
            self.update()

        def _color(self, v):
            if not self._crange or not self._crange[1] > self._crange[0]:
                return QtGui.QColor(150, 150, 150)
            t = (v - self._crange[0]) / (self._crange[1] - self._crange[0])
            r, g, b = gradient_color(t, self._gradient, self._invert)
            return QtGui.QColor.fromRgbF(r, g, b)

        def _fmt(self, v):
            if v == float('-inf') or v == float('inf'):
                return '%s' % ('min' if v < 0 else 'max')
            return '%.3g' % v if abs(v) >= 100 else '%.2f' % v

        def paintEvent(self, ev):
            p = QtGui.QPainter(self)
            try:
                self._paint(p)
            finally:
                p.end()

        def _paint(self, p):
            W, H = self.width(), self.height()
            pl = self._plot()
            vlo, vhi = self._view
            font = p.font()
            font.setPixelSize(11)
            p.setFont(font)
            p.setRenderHint(getattr(QtGui.QPainter, 'RenderHint', QtGui.QPainter).Antialiasing, True)

            C = QtGui.QColor
            card, plot_bg = C(THEME['card']), C(THEME['input'])
            grid, text, dim, accent = C(THEME['line']), C(THEME['text']), C(THEME['muted']), C(THEME['accent'])
            white = C(255, 255, 255)
            p.fillRect(0, 0, W, H, card)
            plot_path = QtGui.QPainterPath()
            plot_path.addRoundedRect(QtCore.QRectF(pl), 7, 7)
            p.fillPath(plot_path, plot_bg)

            n_isl = len(self._vals)
            align_l = _qt_flag('AlignmentFlag', 'AlignLeft') | _qt_flag('AlignmentFlag', 'AlignVCenter')
            align_r = _qt_flag('AlignmentFlag', 'AlignRight') | _qt_flag('AlignmentFlag', 'AlignVCenter')
            align_c = _qt_flag('AlignmentFlag', 'AlignCenter')

            def vline(x, y0, y1):
                p.drawLine(QtCore.QPointF(x + 0.5, y0), QtCore.QPointF(x + 0.5, y1))

            plot_bottom = pl.bottom() + 1
            strip_y = plot_bottom + 5

            ticks = nice_ticks(vlo, vhi, max(2, pl.width() // 60))
            step = (ticks[1] - ticks[0]) if len(ticks) > 1 else 1.0
            p.save()
            p.setClipPath(plot_path)
            p.setPen(grid)
            for tv in ticks:
                vline(int(round(self._v_to_x(tv))), pl.top(), plot_bottom)
            p.restore()
            for tv in ticks:
                x = int(round(self._v_to_x(tv)))
                p.setPen(dim)
                vline(x, strip_y + 10, strip_y + 13)
                p.drawText(QtCore.QRect(x - 30, strip_y + 13, 60, 14), align_c, tick_label(tv, step))

            strip = QtGui.QPainterPath()
            strip.addRoundedRect(QtCore.QRectF(pl.left(), strip_y, pl.width(), 8), 4, 4)
            p.save()
            p.setClipPath(strip)
            x = pl.left()
            while x < pl.left() + pl.width():
                w = min(3, pl.left() + pl.width() - x)
                p.fillRect(x, strip_y, w, 8, self._color(self._x_to_v(x + w / 2.0)))
                x += 3
            p.restore()

            if n_isl == 0:
                p.setPen(dim)
                p.drawText(pl, align_c, self._message)
            else:
                counts, below, above = self._get_bins()
                nb = len(counts)
                bw = pl.width() / float(nb)
                cmax = max(counts) if counts else 0
                p.save()
                p.setClipPath(plot_path)
                p.setPen(_qt_flag('PenStyle', 'NoPen'))
                for i, c in enumerate(counts):
                    if c <= 0:
                        continue
                    h = max(3, int(round((pl.height() - 2) * c / float(cmax))))
                    x0 = pl.left() + int(round(i * bw))
                    x1 = pl.left() + int(round((i + 1) * bw))
                    centre = vlo + (i + 0.5) * (vhi - vlo) / nb
                    bar = QtGui.QPainterPath()
                    bar.addRoundedRect(QtCore.QRectF(x0, plot_bottom - h, max(1, x1 - x0 - 1), h + 4), 1.6, 1.6)
                    p.fillPath(bar, self._color(centre))
                p.restore()
                p.setPen(dim)
                p.drawText(QtCore.QRect(pl.left() + 8, pl.top() + 3, 80, 12), align_l, 'max %d' % cmax)

                p.setPen(white)
                p.setBrush(white)
                if below > 0:
                    cy = plot_bottom - 7
                    p.drawPolygon(QtGui.QPolygon([QtCore.QPoint(pl.left() + 3, cy),
                                                  QtCore.QPoint(pl.left() + 9, cy - 4),
                                                  QtCore.QPoint(pl.left() + 9, cy + 4)]))
                if above > 0:
                    cy = plot_bottom - 7
                    r = pl.left() + pl.width()
                    p.drawPolygon(QtGui.QPolygon([QtCore.QPoint(r - 3, cy),
                                                  QtCore.QPoint(r - 9, cy - 4),
                                                  QtCore.QPoint(r - 9, cy + 4)]))
                p.setBrush(_qt_flag('BrushStyle', 'NoBrush'))

            if self._crange:
                p.setPen(QtGui.QPen(C(255, 255, 255, 150), 1, _qt_flag('PenStyle', 'DashLine')))
                for v in self._crange:
                    if vlo <= v <= vhi:
                        vline(int(round(self._v_to_x(v))), pl.top(), strip_y + 8)

            if self._sel is not None:
                a, b = self._sel
                xa = pl.left() if a <= vlo else int(round(self._v_to_x(min(a, vhi))))
                xb = pl.left() + pl.width() if b >= vhi else int(round(self._v_to_x(max(b, vlo))))
                if xb < xa:
                    xa, xb = xb, xa
                xb = max(xb, xa + 1)
                tint = C(accent)
                tint.setAlpha(58)
                p.save()
                p.setClipPath(plot_path)
                p.fillRect(xa, pl.top(), xb - xa, pl.height(), tint)
                p.restore()
                p.fillRect(xa, plot_bottom, xb - xa, strip_y + 8 - plot_bottom, tint)
                p.fillRect(xa - 1, pl.top(), 2, strip_y + 8 - pl.top(), accent)
                p.fillRect(xb - 1, pl.top(), 2, strip_y + 8 - pl.top(), accent)

            if self._hover_x is not None and n_isl and self._drag is None:
                hx = max(pl.left(), min(pl.left() + pl.width(), int(self._hover_x)))
                p.setPen(C(255, 255, 255, 90))
                vline(hx, pl.top(), plot_bottom)

            p.setPen(text)
            p.drawText(QtCore.QRect(self.PAD_L, 0, W - 2 * self.PAD_R, self.PAD_T), align_l,
                       'Islands: %d   (%s)' % (n_isl, self._unit))
            info = ''
            if self._sel is not None:
                a, b = self._sel
                info = '%s - %s' % (self._fmt(a), self._fmt(b))
                if self._sel_count is not None:
                    word = {'add': '+%d added', 'remove': '-%d removed'}.get(self._sel_mode, '%d selected')
                    info = '%s   %s' % (word % self._sel_count, info)
            elif self._hover_x is not None and n_isl:
                i = self._bin_at(self._hover_x)
                counts, _bl, _ab = self._get_bins()
                nb = len(counts)
                w = (vhi - vlo) / nb
                lo_e = float('-inf') if i == 0 else vlo + i * w
                hi_e = float('inf') if i == nb - 1 else vlo + (i + 1) * w
                info = '%s - %s: %d islands' % (self._fmt(lo_e), self._fmt(hi_e), counts[i])
            p.setPen(accent if self._sel is not None else dim)
            p.drawText(QtCore.QRect(self.PAD_L, 0, W - 2 * self.PAD_R, self.PAD_T), align_r, info)


FOOTER_TEXT = 'A Tool by AreJustPolygons!'
CREATOR_URL = 'https://superhivemarket.com/creators/rfarencibia'
ROW_LABEL_W = 74


def _open_creator_page():
    try:
        if QtGui.QDesktopServices.openUrl(QtCore.QUrl(CREATOR_URL)):
            return True
    except Exception:
        pass
    try:
        cmds.launch(webPage=CREATOR_URL)
        return True
    except Exception:
        return False


def _safe_eval(text):
    text = text.strip()
    if len(text) > 200:
        return None
    try:
        tree = ast.parse(text, mode='eval')
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return None
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv}

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if (isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
                and not isinstance(node.value, bool)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = ev(node.operand)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](ev(node.left), ev(node.right))
        raise ValueError('not arithmetic')

    try:
        v = ev(tree)
    except (ValueError, ZeroDivisionError, OverflowError, RecursionError, MemoryError):
        return None
    return v if math.isfinite(v) else None


def _tip(text, width=62):
    if not text:
        return ''
    return '\n'.join('\n'.join(textwrap.wrap(line, width)) for line in text.split('\n'))


_QSS = string.Template('''
QWidget#TexelDensityVizUI { background: $bg; }
* { font-family: "Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", "Noto Sans", "DejaVu Sans", Arial, sans-serif; font-size: 12px; }
QLabel { color: $text; background: transparent; }
QLabel#rowLabel { color: $muted; }
QLabel#caption { color: $muted; }
QLabel#info { color: $muted; font-size: 11px; }
QLabel#footer { color: $faint; font-size: 11px; }
QScrollArea { background: transparent; border: none; }
QWidget#content { background: transparent; }
QWidget#bottom { background: $bar; border-top: 1px solid $line; }

QFrame#card { background: $card; border: 1px solid $line; border-radius: 11px; }
QFrame#status { background: $card; border: 1px solid $line; border-radius: 9px; }
QFrame#status[error="true"] { background: $error_bg; border: 1px solid $error_line; }
QFrame#status QLabel { color: $text; }
QFrame#status[error="true"] QLabel { color: $error; }

QLineEdit { background: $input; color: $text; border: 1px solid $line; border-radius: 8px; padding: 0 9px; min-height: 26px; selection-background-color: $accent; selection-color: $accent_ink; }
QLineEdit:hover { border: 1px solid $line_hover; }
QLineEdit:focus { border: 1px solid $accent; }
QLineEdit:disabled { background: $bar; color: $faint; border: 1px solid $line; }

QPushButton { background: $btn; color: $text; border: none; border-radius: 9px; padding: 0 14px; min-height: 30px; }
QPushButton:hover { background: $btn_hover; }
QPushButton:pressed { background: $btn_press; }
QPushButton:disabled { background: $card; color: $faint; }
QPushButton[variant="primary"] { background: $accent; color: $accent_ink; font-weight: bold; }
QPushButton[variant="primary"]:hover { background: $accent_hi; }
QPushButton[variant="primary"]:pressed { background: $accent_lo; }
QPushButton[variant="primary"]:disabled { background: $accent_dim; color: $faint; }
QPushButton[big="true"] { min-height: 40px; border-radius: 11px; font-size: 13px; }

QComboBox { background: $input; color: $text; border: 1px solid $line; border-radius: 8px; padding: 0 30px 0 10px; min-height: 26px; }
QComboBox:hover { border: 1px solid $line_hover; }
QComboBox:on { border: 1px solid $accent; }
QComboBox:disabled { color: $faint; background: $bar; }
QComboBox::drop-down { border: none; width: 0px; }
QComboBox::down-arrow { image: none; border: none; width: 0px; height: 0px; }
QComboBox QAbstractItemView { background: $card_hi; color: $text; border: 1px solid $line_hover; padding: 4px; outline: 0; selection-background-color: $accent; selection-color: $accent_ink; }
QComboBox QAbstractItemView::item { min-height: 26px; padding: 0 8px; border-radius: 5px; }
QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected { background: $accent; color: $accent_ink; }

QSlider { min-height: 22px; background: transparent; }
QSlider::groove:horizontal { height: 6px; background: $input; border: 1px solid $line; border-radius: 4px; }
QSlider::sub-page:horizontal { background: $accent; border-radius: 3px; }
QSlider::add-page:horizontal { background: transparent; }
QSlider::handle:horizontal { background: $text; border: 2px solid $accent; width: 10px; height: 10px; margin: -5px 0; border-radius: 7px; }
QSlider::handle:horizontal:hover { background: $accent_hi; }

QListWidget { background: $input; color: $text; border: 1px solid $line; border-radius: 9px; padding: 4px; outline: 0; }
QListWidget::item { padding: 4px 6px; border-radius: 5px; }
QListWidget::item:hover { background: $card_hi; }
QListWidget::item:selected { background: $accent_dim; color: $text; }

QScrollBar:vertical { background: transparent; width: 12px; margin: 2px 2px 2px 0; }
QScrollBar::handle:vertical { background: $scroll; border-radius: 4px; min-height: 30px; margin: 0 1px; }
QScrollBar::handle:vertical:hover { background: $scroll_hover; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; background: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 0 2px 2px 2px; }
QScrollBar::handle:horizontal { background: $scroll; border-radius: 4px; min-width: 30px; margin: 1px 0; }
QScrollBar::handle:horizontal:hover { background: $scroll_hover; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; border: none; background: none; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }

QToolTip { background: $bar; color: $text; border: 1px solid $line_hover; padding: 6px 8px; }
''')


def build_qss():
    t = dict(THEME)
    t['accent_dim'] = _mix(THEME['card'], THEME['accent'], 0.24)
    return _QSS.substitute(t)


if QtWidgets is not None:
    class _QtNames(object):
        _GROUPS = ('AlignmentFlag', 'CursorShape', 'MouseButton', 'KeyboardModifier', 'PenStyle',
                   'PenCapStyle', 'PenJoinStyle', 'BrushStyle', 'WindowType', 'FocusPolicy', 'Key',
                   'ScrollBarPolicy', 'TextElideMode', 'Orientation', 'WidgetAttribute')

        def __getattr__(self, name):
            for group in self._GROUPS:
                scoped = getattr(QtCore.Qt, group, None)
                if scoped is not None and hasattr(scoped, name):
                    return getattr(scoped, name)
            return getattr(QtCore.Qt, name)

    _Qt = _QtNames()
    _SP = getattr(QtWidgets.QSizePolicy, 'Policy', QtWidgets.QSizePolicy)
    _HINT = getattr(QtGui.QPainter, 'RenderHint', QtGui.QPainter)
    _SPACING = getattr(QtGui.QFont, 'SpacingType', QtGui.QFont)
    _ALIGN_L = _Qt.AlignLeft | _Qt.AlignVCenter
    _ALIGN_R = _Qt.AlignRight | _Qt.AlignVCenter
    _ALIGN_C = _Qt.AlignHCenter | _Qt.AlignVCenter

    def _qc(color, alpha=255):
        c = QtGui.QColor(color)
        if alpha != 255:
            c.setAlpha(alpha)
        return c

    def _antialias(p):
        p.setRenderHint(_HINT.Antialiasing, True)

    def _chevron(p, cx, cy, expanded, color, width=1.7):
        pen = QtGui.QPen(color, width)
        pen.setCapStyle(_Qt.RoundCap)
        pen.setJoinStyle(_Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(_Qt.NoBrush)
        if expanded:
            pts = [QtCore.QPointF(cx - 4, cy - 2), QtCore.QPointF(cx, cy + 2), QtCore.QPointF(cx + 4, cy - 2)]
        else:
            pts = [QtCore.QPointF(cx - 2, cy - 4), QtCore.QPointF(cx + 2, cy), QtCore.QPointF(cx - 2, cy + 4)]
        p.drawPolyline(QtGui.QPolygonF(pts))

    def _paint_logo(p, rect):
        _antialias(p)
        p.setPen(_Qt.NoPen)
        p.setBrush(_qc(THEME['accent']))
        p.drawRoundedRect(rect, rect.width() * 0.27, rect.width() * 0.27)
        pad = rect.width() * 0.2
        cell = (rect.width() - 2 * pad) / 3.0
        gap = cell * 0.16
        alphas = (255, 150, 255, 150, 255, 150, 255, 150, 255)
        for i, a in enumerate(alphas):
            r, c = divmod(i, 3)
            p.setBrush(_qc(THEME['accent_ink'], a))
            p.drawRoundedRect(QtCore.QRectF(rect.left() + pad + c * cell + gap / 2,
                                            rect.top() + pad + r * cell + gap / 2,
                                            cell - gap, cell - gap), cell * 0.18, cell * 0.18)

    def _logo_icon():
        pm = QtGui.QPixmap(64, 64)
        pm.fill(_qc('#000000', 0))
        p = QtGui.QPainter(pm)
        try:
            _paint_logo(p, QtCore.QRectF(4, 4, 56, 56))
        finally:
            p.end()
        return QtGui.QIcon(pm)

    class _BusyCursor(object):
        def __enter__(self):
            try:
                QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(_Qt.WaitCursor))
            except Exception:
                pass
            return self

        def __exit__(self, *exc):
            try:
                QtWidgets.QApplication.restoreOverrideCursor()
            except Exception:
                pass
            return False

    class Segmented(QtWidgets.QWidget):
        indexChanged = QtCore.Signal(int)
        HEIGHT = 30

        def __init__(self, labels, index=0, parent=None):
            QtWidgets.QWidget.__init__(self, parent)
            self._labels = list(labels)
            self._index = index
            self._hover = -1
            self._down = -1
            self.setMouseTracking(True)
            self.setFocusPolicy(_Qt.StrongFocus)
            self.setCursor(_Qt.PointingHandCursor)
            self.setSizePolicy(_SP.Expanding, _SP.Fixed)
            self.setFixedHeight(self.HEIGHT)

        def labels(self):
            return list(self._labels)

        def count(self):
            return len(self._labels)

        def index(self):
            return self._index

        def setIndex(self, index):
            if index is not None and not 0 <= index < len(self._labels):
                index = None
            if index != self._index:
                self._index = index
                self.update()

        def select(self, index):
            if (not self.isEnabled() or index is None or not 0 <= index < len(self._labels)
                    or index == self._index):
                return
            self._index = index
            self.update()
            self.indexChanged.emit(index)

        def sizeHint(self):
            fm = self.fontMetrics()
            return QtCore.QSize(sum(fm.horizontalAdvance(t) + 30 for t in self._labels) + 6, self.HEIGHT)

        def minimumSizeHint(self):
            fm = self.fontMetrics()
            widest = max([fm.horizontalAdvance(t) for t in self._labels] or [20])
            return QtCore.QSize((widest + 18) * max(1, len(self._labels)) + 6, self.HEIGHT)

        def _seg_rect(self, i):
            n = max(1, len(self._labels))
            inner = QtCore.QRectF(self.rect()).adjusted(3, 3, -3, -3)
            w = inner.width() / n
            return QtCore.QRectF(inner.left() + w * i, inner.top(), w, inner.height())

        def _index_at(self, x):
            n = len(self._labels)
            if n == 0:
                return -1
            w = (self.width() - 6) / float(n)
            i = int((x - 3) // w) if w > 0 else -1
            return i if 0 <= i < n else -1

        def mouseMoveEvent(self, ev):
            x, _y = _event_xy(ev)
            i = self._index_at(x)
            if i != self._hover:
                self._hover = i
                self.update()

        def mousePressEvent(self, ev):
            if ev.button() == _Qt.LeftButton:
                x, _y = _event_xy(ev)
                self._down = self._index_at(x)
                self.update()
            ev.accept()

        def mouseReleaseEvent(self, ev):
            if ev.button() == _Qt.LeftButton:
                x, _y = _event_xy(ev)
                i = self._index_at(x)
                down, self._down = self._down, -1
                if i >= 0 and i == down:
                    self.select(i)
                self.update()
            ev.accept()

        def leaveEvent(self, ev):
            self._hover = -1
            self.update()

        def keyPressEvent(self, ev):
            k = ev.key()
            if k in (_Qt.Key_Left, _Qt.Key_Up):
                self.select(max(0, (self._index if self._index is not None else 1) - 1))
            elif k in (_Qt.Key_Right, _Qt.Key_Down):
                self.select(min(len(self._labels) - 1, (self._index if self._index is not None else -1) + 1))
            else:
                QtWidgets.QWidget.keyPressEvent(self, ev)

        def changeEvent(self, ev):
            self.update()
            QtWidgets.QWidget.changeEvent(self, ev)

        def paintEvent(self, ev):
            p = QtGui.QPainter(self)
            try:
                _antialias(p)
                enabled = self.isEnabled()
                track = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
                p.setPen(QtGui.QPen(_qc(THEME['line']), 1))
                p.setBrush(_qc(THEME['input'] if enabled else THEME['bar']))
                p.drawRoundedRect(track, 9, 9)
                for i, text in enumerate(self._labels):
                    seg = self._seg_rect(i)
                    selected = (i == self._index)
                    p.setPen(_Qt.NoPen)
                    if selected:
                        shade = THEME['accent_lo'] if (i == self._down and enabled) else THEME['accent']
                        p.setBrush(_qc(shade, 255 if enabled else 90))
                        p.drawRoundedRect(seg, 7, 7)
                    elif enabled and (i == self._hover or i == self._down):
                        p.setBrush(_qc('#ffffff', 22 if i == self._hover else 36))
                        p.drawRoundedRect(seg, 7, 7)
                    font = QtGui.QFont(self.font())
                    font.setBold(selected)
                    p.setFont(font)
                    if selected:
                        p.setPen(_qc(THEME['accent_ink'], 255 if enabled else 140))
                    else:
                        p.setPen(_qc(THEME['text'] if enabled else THEME['faint']))
                    p.drawText(seg, _ALIGN_C, QtGui.QFontMetrics(font).elidedText(
                        text, _Qt.ElideRight, int(seg.width() - 8)))
            finally:
                p.end()

    class ToggleSwitch(QtWidgets.QAbstractButton):
        TW, TH = 34, 18

        def __init__(self, text='', checked=False, expanding=True, parent=None):
            QtWidgets.QAbstractButton.__init__(self, parent)
            self.setText(text)
            self.setCheckable(True)
            self.setChecked(checked)
            self.setCursor(_Qt.PointingHandCursor)
            self.setFocusPolicy(_Qt.StrongFocus)
            self._hover = False
            self._expanding = expanding
            self.setSizePolicy(_SP.Expanding if expanding else _SP.Fixed, _SP.Fixed)
            self.setFixedHeight(26)

        def sizeHint(self):
            tw = self.fontMetrics().horizontalAdvance(self.text())
            return QtCore.QSize(tw + (10 if self.text() else 0) + self.TW + 2, 26)

        def minimumSizeHint(self):
            return QtCore.QSize(self.TW + 2 + (60 if self.text() else 0), 26)

        def enterEvent(self, ev):
            self._hover = True
            self.update()

        def leaveEvent(self, ev):
            self._hover = False
            self.update()

        def paintEvent(self, ev):
            p = QtGui.QPainter(self)
            try:
                _antialias(p)
                enabled = self.isEnabled()
                on = self.isChecked()
                h = self.height()
                fm = self.fontMetrics()
                if self._expanding:
                    tx = self.width() - self.TW - 1
                else:
                    tx = fm.horizontalAdvance(self.text()) + (10 if self.text() else 0)
                ty = (h - self.TH) / 2.0
                if on:
                    track = _qc(THEME['accent_hi'] if self._hover else THEME['accent'])
                else:
                    track = _qc(THEME['line_hover'] if self._hover else THEME['track_off'])
                if not enabled:
                    track.setAlpha(90)
                p.setPen(_Qt.NoPen)
                p.setBrush(track)
                p.drawRoundedRect(QtCore.QRectF(tx, ty, self.TW, self.TH), self.TH / 2.0, self.TH / 2.0)
                kd = self.TH - 6
                kx = tx + self.TW - kd - 3 if on else tx + 3
                p.setBrush(_qc(THEME['accent_ink'] if on else '#e3e6ea', 255 if enabled else 120))
                p.drawEllipse(QtCore.QRectF(kx, ty + 3, kd, kd))
                if self.text():
                    p.setPen(_qc(THEME['text'] if enabled else THEME['faint']))
                    room = int(tx - 10) if self._expanding else self.width()
                    p.drawText(QtCore.QRectF(0, 0, max(0, room), h), _ALIGN_L,
                               fm.elidedText(self.text(), _Qt.ElideRight, max(0, room)))
            finally:
                p.end()

    class NumberField(QtWidgets.QLineEdit):
        valueChanged = QtCore.Signal(float)

        def __init__(self, value=0.0, decimals=3, minimum=-1e12, maximum=1e12, step=None,
                     suffix='', parent=None):
            QtWidgets.QLineEdit.__init__(self, parent)
            self._dec = int(decimals)
            self._min = float(minimum)
            self._max = float(maximum)
            self._step = float(step) if step else (1.0 if self._dec == 0 else 0.1)
            self._suffix = ''
            self._value = 0.0
            self._shown = ''
            self.setSuffix(suffix)
            self.setValue(value)
            self.editingFinished.connect(self._on_finished)

        def _fmt(self, v):
            return '%d' % int(round(v)) if self._dec == 0 else '%.*f' % (self._dec, v)

        def _clamp(self, v):
            v = max(self._min, min(self._max, float(v)))
            return float(int(round(v))) if self._dec == 0 else v

        def _parse(self, text):
            t = text.strip().replace(',', '.')
            if self._suffix and t.endswith(self._suffix):
                t = t[:-len(self._suffix)]
            v = _safe_eval(t)
            return None if v is None else self._clamp(v)

        def value(self):
            t = self.text()
            if t != self._shown:
                v = self._parse(t)
                if v is not None:
                    return int(v) if self._dec == 0 else v
            return int(self._value) if self._dec == 0 else self._value

        def setValue(self, v):
            self._value = self._clamp(v)
            self._shown = self._fmt(self._value)
            self.setText(self._shown)

        def commit(self, v=None):
            if v is None:
                v = self._parse(self.text())
                if v is None:
                    self.setText(self._shown)
                    return
            old = self._value
            self.setValue(v)
            if self._value != old:
                self.valueChanged.emit(self._value)

        def _on_finished(self):
            self.commit()

        def setRangeLimits(self, lo, hi):
            self._min, self._max = float(lo), float(hi)

        def setSuffix(self, suffix):
            self._suffix = suffix or ''
            width = self.fontMetrics().horizontalAdvance(self._suffix) + 6 if self._suffix else 0
            self.setTextMargins(0, 0, width, 0)
            self.update()

        def suffix(self):
            return self._suffix

        def _step_by(self, direction, mods):
            mult = 10.0 if mods & _Qt.ShiftModifier else (0.1 if mods & _Qt.ControlModifier else 1.0)
            cur = self.value()
            self.commit(round(cur + direction * self._step * mult, 9))

        def keyPressEvent(self, ev):
            if ev.key() in (_Qt.Key_Up, _Qt.Key_Down):
                self._step_by(1 if ev.key() == _Qt.Key_Up else -1, ev.modifiers())
                ev.accept()
                return
            QtWidgets.QLineEdit.keyPressEvent(self, ev)

        def wheelEvent(self, ev):
            if not self.hasFocus():
                ev.ignore()
                return
            steps = ev.angleDelta().y() / 120.0
            if steps:
                self._step_by(1 if steps > 0 else -1, ev.modifiers())
            ev.accept()

        def paintEvent(self, ev):
            QtWidgets.QLineEdit.paintEvent(self, ev)
            if not self._suffix:
                return
            p = QtGui.QPainter(self)
            try:
                p.setPen(_qc(THEME['muted'] if self.isEnabled() else THEME['faint']))
                r = self.rect().adjusted(0, 0, -9, 0)
                p.drawText(r, _ALIGN_R, self._suffix)
            finally:
                p.end()

    class _NoWheelSlider(QtWidgets.QSlider):
        def wheelEvent(self, ev):
            if self.hasFocus():
                QtWidgets.QSlider.wheelEvent(self, ev)
            else:
                ev.ignore()

    class SliderField(QtWidgets.QWidget):
        valueChanged = QtCore.Signal(float)

        def __init__(self, lo, hi, value, decimals=0, field_min=None, field_max=None, parent=None):
            QtWidgets.QWidget.__init__(self, parent)
            self._f = 10 ** int(decimals)
            self._quiet = False
            lay = QtWidgets.QHBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(10)
            self.slider = _NoWheelSlider(_Qt.Horizontal)
            self.slider.setRange(int(round(lo * self._f)), int(round(hi * self._f)))
            self.field = NumberField(value, decimals, lo if field_min is None else field_min,
                                     hi if field_max is None else field_max,
                                     step=1.0 if decimals == 0 else 0.5)
            self.field.setFixedWidth(64)
            lay.addWidget(self.slider, 1)
            lay.addWidget(self.field)
            self.setValue(value)
            self.slider.valueChanged.connect(self._on_slider)
            self.slider.sliderReleased.connect(self._on_released)
            self.field.valueChanged.connect(self._on_field)

        def value(self):
            return self.field.value()

        def setValue(self, v):
            self._quiet = True
            try:
                self.field.setValue(v)
                self.slider.setValue(int(round(self.field.value() * self._f)))
            finally:
                self._quiet = False

        def _on_slider(self, raw):
            if self._quiet:
                return
            v = raw / float(self._f)
            self.field.setValue(v)
            if not self.slider.isSliderDown():
                self.valueChanged.emit(self.field.value())

        def _on_released(self):
            if not self._quiet:
                self.valueChanged.emit(self.field.value())

        def _on_field(self, v):
            self._quiet = True
            try:
                self.slider.setValue(int(round(v * self._f)))
            finally:
                self._quiet = False
            self.valueChanged.emit(v)

    class StyledCombo(QtWidgets.QComboBox):
        def __init__(self, items, index=0, parent=None):
            QtWidgets.QComboBox.__init__(self, parent)
            self.setView(QtWidgets.QListView())
            self.addItems(list(items))
            self.setCurrentIndex(index)
            self.setCursor(_Qt.PointingHandCursor)
            self.setMinimumContentsLength(8)
            self.setSizeAdjustPolicy(
                getattr(QtWidgets.QComboBox, 'SizeAdjustPolicy', QtWidgets.QComboBox)
                .AdjustToMinimumContentsLengthWithIcon)
            self.setSizePolicy(_SP.Expanding, _SP.Fixed)

        def paintEvent(self, ev):
            QtWidgets.QComboBox.paintEvent(self, ev)
            p = QtGui.QPainter(self)
            try:
                _antialias(p)
                open_ = self.view().isVisible()
                color = _qc(THEME['accent'] if open_ else
                            (THEME['muted'] if self.isEnabled() else THEME['faint']))
                _chevron(p, self.width() - 16, self.height() / 2.0, True, color)
            finally:
                p.end()

        def wheelEvent(self, ev):
            if self.hasFocus():
                QtWidgets.QComboBox.wheelEvent(self, ev)
            else:
                ev.ignore()

    class GradientBar(QtWidgets.QWidget):
        BAR_H = 12

        def __init__(self, parent=None):
            QtWidgets.QWidget.__init__(self, parent)
            self._mode = 0
            self._invert = False
            self._labels = ('', '', '')
            self.setFixedHeight(self.BAR_H + 20)
            self.setSizePolicy(_SP.Expanding, _SP.Fixed)

        def set_gradient(self, mode, invert):
            self._mode, self._invert = mode, bool(invert)
            self.update()

        def set_labels(self, left, mid, right):
            self._labels = (left, mid, right)
            self.update()

        def labels(self):
            return self._labels

        def colors(self, n=5):
            return [gradient_color(i / float(n - 1), self._mode, self._invert) for i in range(n)]

        def paintEvent(self, ev):
            p = QtGui.QPainter(self)
            try:
                _antialias(p)
                w = self.width()
                bar = QtCore.QRectF(0, 0, w, self.BAR_H)
                grad = QtGui.QLinearGradient(0, 0, w, 0)
                n = 48
                for i in range(n + 1):
                    t = i / float(n)
                    r, g, b = gradient_color(t, self._mode, self._invert)
                    grad.setColorAt(t, QtGui.QColor.fromRgbF(r, g, b))
                path = QtGui.QPainterPath()
                path.addRoundedRect(bar, self.BAR_H / 2.0, self.BAR_H / 2.0)
                p.fillPath(path, QtGui.QBrush(grad))
                p.setPen(_qc(THEME['muted']))
                font = QtGui.QFont(self.font())
                font.setPixelSize(11)
                p.setFont(font)
                y = self.BAR_H + 3
                left, mid, right = self._labels
                p.drawText(QtCore.QRectF(0, y, w / 3.0, 16), _ALIGN_L, left)
                p.drawText(QtCore.QRectF(w / 3.0, y, w / 3.0, 16), _ALIGN_C, mid)
                p.drawText(QtCore.QRectF(2 * w / 3.0, y, w / 3.0, 16), _ALIGN_R, right)
            finally:
                p.end()

    class StatusBar(QtWidgets.QFrame):
        def __init__(self, parent=None):
            QtWidgets.QFrame.__init__(self, parent)
            self.setObjectName('status')
            self._error = False
            self.setProperty('error', False)
            lay = QtWidgets.QHBoxLayout(self)
            lay.setContentsMargins(28, 7, 12, 7)
            self._label = QtWidgets.QLabel('')
            self._label.setWordWrap(True)
            lay.addWidget(self._label)
            self.setMinimumHeight(36)

        def set_message(self, text, error=False, detail=None):
            error = bool(error)
            self._label.setText(text)
            self._label.setToolTip(_tip(text, 80) + ('\n\n' + _tip(detail, 80) if detail else ''))
            if error != self._error:
                self._error = error
                self.setProperty('error', error)
                for w in (self, self._label):
                    w.style().unpolish(w)
                    w.style().polish(w)
            self.update()

        def text(self):
            return self._label.text()

        def is_error(self):
            return self._error

        def paintEvent(self, ev):
            QtWidgets.QFrame.paintEvent(self, ev)
            p = QtGui.QPainter(self)
            try:
                _antialias(p)
                p.setPen(_Qt.NoPen)
                p.setBrush(_qc(THEME['error'] if self._error else THEME['accent']))
                p.drawEllipse(QtCore.QPointF(15, self.height() / 2.0), 3.5, 3.5)
            finally:
                p.end()

    class _CardHeader(QtWidgets.QWidget):
        clicked = QtCore.Signal()

        def __init__(self, title, collapsible, parent=None):
            QtWidgets.QWidget.__init__(self, parent)
            self._title = title
            self._collapsible = collapsible
            self._open = True
            self._hover = False
            self.setFixedHeight(38)
            self.setSizePolicy(_SP.Expanding, _SP.Fixed)
            if collapsible:
                self.setCursor(_Qt.PointingHandCursor)
                self.setMouseTracking(True)

        def set_open(self, value):
            self._open = bool(value)
            self.update()

        def mousePressEvent(self, ev):
            if self._collapsible and ev.button() == _Qt.LeftButton:
                self.clicked.emit()
            ev.accept()

        def enterEvent(self, ev):
            self._hover = True
            self.update()

        def leaveEvent(self, ev):
            self._hover = False
            self.update()

        def paintEvent(self, ev):
            p = QtGui.QPainter(self)
            try:
                _antialias(p)
                h = self.height()
                p.setPen(_Qt.NoPen)
                p.setBrush(_qc(THEME['accent']))
                p.drawRoundedRect(QtCore.QRectF(14, h / 2.0 - 6, 3, 12), 1.5, 1.5)
                font = QtGui.QFont(self.font())
                font.setPixelSize(11)
                font.setBold(True)
                font.setLetterSpacing(_SPACING.AbsoluteSpacing, 1.0)
                p.setFont(font)
                p.setPen(_qc(THEME['text']))
                p.drawText(QtCore.QRectF(26, 0, self.width() - 60, h), _ALIGN_L, self._title.upper())
                if self._collapsible:
                    _chevron(p, self.width() - 20, h / 2.0, self._open,
                             _qc(THEME['accent'] if self._hover else THEME['muted']))
            finally:
                p.end()

    class Card(QtWidgets.QFrame):
        toggled = QtCore.Signal(bool)

        def __init__(self, title, expanded=True, collapsible=True, parent=None):
            QtWidgets.QFrame.__init__(self, parent)
            self.setObjectName('card')
            self._title = title
            outer = QtWidgets.QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)
            self._head = _CardHeader(title, collapsible)
            self._head.clicked.connect(lambda: self.setExpanded(not self._expanded))
            outer.addWidget(self._head)
            self._body = QtWidgets.QWidget()
            self.body = QtWidgets.QVBoxLayout(self._body)
            self.body.setContentsMargins(14, 2, 14, 14)
            self.body.setSpacing(9)
            outer.addWidget(self._body)
            self._expanded = True
            self.setExpanded(expanded)

        def title(self):
            return self._title

        def isExpanded(self):
            return self._expanded

        def setExpanded(self, value):
            value = bool(value)
            changed = value != self._expanded
            self._expanded = value
            self._body.setVisible(value)
            self._head.set_open(value)
            if changed:
                self.toggled.emit(value)

    class _Header(QtWidgets.QWidget):
        def __init__(self, title, subtitle, parent=None):
            QtWidgets.QWidget.__init__(self, parent)
            self._title, self._subtitle = title, subtitle
            self.setFixedHeight(62)

        def paintEvent(self, ev):
            p = QtGui.QPainter(self)
            try:
                _antialias(p)
                w, h = self.width(), self.height()
                p.fillRect(0, 0, w, h, _qc(THEME['bar']))
                p.fillRect(0, h - 1, w, 1, _qc(THEME['line']))
                _paint_logo(p, QtCore.QRectF(16, 15, 32, 32))
                font = QtGui.QFont(self.font())
                font.setPixelSize(16)
                font.setBold(True)
                p.setFont(font)
                p.setPen(_qc(THEME['text']))
                p.drawText(QtCore.QRectF(60, 11, w - 70, 22), _ALIGN_L, self._title)
                font = QtGui.QFont(self.font())
                font.setPixelSize(11)
                p.setFont(font)
                p.setPen(_qc(THEME['muted']))
                p.drawText(QtCore.QRectF(60, 33, w - 70, 18), _ALIGN_L, self._subtitle)
            finally:
                p.end()

    def _form_row(layout, label, *items, **kw):
        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(kw.get('spacing', 8))
        lab = None
        if label is not None:
            lab = QtWidgets.QLabel(label)
            lab.setObjectName('rowLabel')
            lab.setFixedWidth(ROW_LABEL_W)
            row.addWidget(lab)
        for it in items:
            if isinstance(it, str):
                cap = QtWidgets.QLabel(it)
                cap.setObjectName('caption')
                row.addWidget(cap)
            elif isinstance(it, tuple):
                row.addWidget(it[0], it[1])
            else:
                row.addWidget(it)
        layout.addLayout(row)
        return lab, row

    def _info_label(text=''):
        lab = QtWidgets.QLabel(text)
        lab.setObjectName('info')
        lab.setWordWrap(True)
        return lab

    def _button(text, variant=None, big=False, tip=None):
        b = QtWidgets.QPushButton(text)
        if variant:
            b.setProperty('variant', variant)
        if big:
            b.setProperty('big', True)
        b.setCursor(_Qt.PointingHandCursor)
        if tip:
            b.setToolTip(_tip(tip))
        return b

    def _maya_main_window():
        if _omui is None or wrapInstance is None:
            return None
        try:
            ptr = _omui.MQtUtil.mainWindow()
            return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None
        except Exception:
            return None

    def _dark_title_bar(widget):
        if not sys.platform.startswith('win'):
            return False
        try:
            import ctypes
            from ctypes import wintypes
            fn = ctypes.windll.dwmapi.DwmSetWindowAttribute
            fn.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
            fn.restype = ctypes.c_long
            hwnd = int(widget.winId())

            def put(attr, value):
                v = ctypes.c_int(value)
                return fn(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))

            def colorref(hex_color):
                h = hex_color.lstrip('#')
                return int(h[4:6] + h[2:4] + h[0:2], 16)

            ok = put(20, 1) == 0 or put(19, 1) == 0
            put(35, colorref(THEME['bar']))
            put(36, colorref(THEME['text']))
            return bool(ok)
        except Exception:
            return False

    class TexelDensityVizUI(QtWidgets.QWidget):
        WIN = 'TexelDensityVizUI'

        def __init__(self, parent=None):
            QtWidgets.QWidget.__init__(self, parent)
            self.setObjectName(self.WIN)
            self.setWindowFlags(self.windowFlags() | _Qt.Window)
            self.setAttribute(_Qt.WA_StyledBackground, True)
            self.setWindowTitle('Texel Density Visualizer')
            try:
                self.setWindowIcon(_logo_icon())
            except Exception:
                pass
            self.core = TexelDensityOverride()
            self._unit_scale = 1.0
            self._cb_ids = []
            self.hist = None
            self._sel_base = None
            self._sel_scale = 1.0
            self._last_res = None
            self._title_done = False
            self._resume = None
            self._sel_before = None
            self._manual_pair = None
            self._px_scope = None
            self._live_gap = 0.0
            self._live_last = 0.0
            self._last_note = ''
            self._build()
            self.setStyleSheet(build_qss())
            self._live_timer = QtCore.QTimer(self)
            self._live_timer.setSingleShot(True)
            self._live_timer.timeout.connect(self._live_fire)
            self.setMinimumSize(430, 520)
            self.resize(480, self._start_height())
            self._register_callbacks()
            self._refresh_legend()
            self._sync_legend_labels()
            self._sync_preset()
            self._on_px_op_changed()
            self._update_hist()

        def _start_height(self):
            height = 940
            try:
                parent = self.parentWidget()
                screen = parent.screen() if parent is not None else None
                if screen is None:
                    screen = QtGui.QGuiApplication.primaryScreen()
                if screen is not None:
                    height = min(height, screen.availableGeometry().height() - 80)
            except Exception:
                pass
            return max(self.minimumHeight(), height)

        def _build(self):
            root = QtWidgets.QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)
            root.addWidget(_Header('Texel Density', 'Visualize  \u00b7  Select  \u00b7  Scale'))

            scroll = QtWidgets.QScrollArea()
            scroll.setObjectName('scroll')
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(_Qt.ScrollBarAlwaysOff)
            content = QtWidgets.QWidget()
            content.setObjectName('content')
            col = QtWidgets.QVBoxLayout(content)
            col.setContentsMargins(12, 12, 12, 12)
            col.setSpacing(10)
            scroll.setWidget(content)
            root.addWidget(scroll, 1)
            self.scroll = scroll

            def card(title, expanded=True):
                c = Card(title, expanded=expanded)
                col.addWidget(c)
                return c

            self.card_texture = c = card('Texture size')
            self.w_field = NumberField(2048, 0, 1, 1000000, step=64, suffix='px')
            self.h_field = NumberField(2048, 0, 1, 1000000, step=64, suffix='px')
            self.w_field.valueChanged.connect(self._on_w_changed)
            self.h_field.valueChanged.connect(self._on_h_changed)
            times = QtWidgets.QLabel('\u00d7')
            times.setObjectName('caption')
            _form_row(c.body, 'Size', (self.w_field, 1), times, (self.h_field, 1))
            self.preset_seg = Segmented(['256', '512', '1K', '2K', '4K', '8K'], None)
            self.preset_seg.indexChanged.connect(self._on_preset_index)
            _form_row(c.body, 'Presets', (self.preset_seg, 1))
            self.square_sw = ToggleSwitch('Square  (width = height)', True)
            self.square_sw.setToolTip(_tip('Typing a width also sets the height, and the other way round.'))
            _form_row(c.body, None, (self.square_sw, 1))

            self.card_measure = c = card('Measure')
            self.mode_seg = Segmented(['Per Face', 'Per UV Island'], 0)
            self.mode_seg.setToolTip(_tip(
                'Per Face: every polygon gets the density of its own area. '
                'Per UV Island: every UV island gets one density, the same for all its faces.'))
            self.mode_seg.indexChanged.connect(lambda i: self._on_param_changed())
            _form_row(c.body, 'Mode', (self.mode_seg, 1))
            self.unit_seg = Segmented(['px / cm', 'px / m'], 0)
            self.unit_seg.indexChanged.connect(lambda i: self._on_unit_changed())
            _form_row(c.body, 'Units', (self.unit_seg, 1))
            self.range_seg = Segmented(['Auto  (min / max)', 'Manual'], 1 if DEFAULT_RANGE_MANUAL else 0)
            self.range_seg.setToolTip(_tip(
                'Auto: red = lowest and blue = highest density of the selected meshes. '
                'Manual: you set the two values yourself.'))
            self.range_seg.indexChanged.connect(lambda i: self._on_range_mode())
            _form_row(c.body, 'Range', (self.range_seg, 1))
            self.min_field = NumberField(DEFAULT_RANGE_MIN, 3, -1e9, 1e9, step=0.1)
            self.max_field = NumberField(DEFAULT_RANGE_MAX, 3, -1e9, 1e9, step=0.1)
            self.min_field.setEnabled(DEFAULT_RANGE_MANUAL)
            self.max_field.setEnabled(DEFAULT_RANGE_MANUAL)
            self.min_field.valueChanged.connect(lambda v: self._on_param_changed())
            self.max_field.valueChanged.connect(lambda v: self._on_param_changed())
            _form_row(c.body, 'Min / Max', (self.min_field, 1), 'to', (self.max_field, 1))
            self.merge_sw = ToggleSwitch('One color per quad  (merge triangle pairs)', True)
            self.merge_sw.setToolTip(_tip(
                'Per Face mode: two triangles that are really one quad cut along a diagonal '
                '(flat, no UV seam, convex) get ONE color - the average density of the whole '
                'quad. Real quads / n-gons are never split.'))
            self.merge_sw.clicked.connect(lambda v=False: self._on_param_changed())
            c.body.addWidget(self.merge_sw)
            self.angle_slider = SliderField(1.0, 45.0, DEFAULT_PAIR_ANGLE, 1, 0.0, 89.0)
            self.angle_slider.setToolTip(_tip(
                'Max angle (degrees) between the two triangles for them to count as one quad.'))
            self.angle_slider.valueChanged.connect(lambda v: self._on_param_changed())
            _form_row(c.body, 'Pair angle', (self.angle_slider, 1))

            self.card_colors = c = card('Colors')
            self.grad_combo = StyledCombo(GRADIENT_NAMES, 0)
            self.grad_combo.currentIndexChanged.connect(lambda i: self._on_gradient_changed())
            _form_row(c.body, 'Gradient', (self.grad_combo, 1))
            self.grad_bar = GradientBar()
            c.body.addWidget(self.grad_bar)
            self.invert_sw = ToggleSwitch('Invert colors  (blue = low, red = high)', False)
            self.invert_sw.clicked.connect(lambda v=False: self._on_gradient_changed())
            c.body.addWidget(self.invert_sw)
            self.steps_slider = SliderField(8, 128, 64, 0, 2, 256)
            self.steps_slider.setToolTip(_tip('How many different colors are used between red and blue.'))
            self.steps_slider.valueChanged.connect(lambda v: self._on_param_changed())
            _form_row(c.body, 'Color steps', (self.steps_slider, 1))
            self.shader_seg = Segmented(list(SHADER_LABELS), SHADER_KINDS.index(DEFAULT_SHADER))
            self.shader_seg.setToolTip(_tip(
                'How the colors are shown. '
                'Flat: unlit - exactly the colors of the legend, whatever the lights do. '
                'Lambert: matte and lit by the lights of the viewport, so the shape of the surface '
                'stays visible. Phong: like Lambert, with a shiny highlight. '
                '(Lambert and Phong can look dark under "Use All Lights" when the scene has no light.)'))
            self.shader_seg.indexChanged.connect(lambda i: self._on_param_changed())
            _form_row(c.body, 'Shader', (self.shader_seg, 1))
            self.display_seg = Segmented(list(DISPLAY_LABELS), DISPLAY_MODES.index(DEFAULT_DISPLAY))
            self.display_seg.setToolTip(_tip(
                'How the colors get onto the meshes. '
                'Fast: they are written into the meshes as vertex colors - quick even on meshes with '
                'hundreds of thousands of faces. It needs a mesh without construction history; any other '
                'mesh is painted with Materials automatically, and the status line says which. '
                'Materials: one material per color step, assigned face by face - works on every mesh, '
                'but Maya is slow at it on very dense meshes.'))
            self.display_seg.indexChanged.connect(lambda i: self._on_param_changed())
            _form_row(c.body, 'Display', (self.display_seg, 1))
            self.live_sw = ToggleSwitch('Live update  (size / range / colors / mode / shader)', True)
            c.body.addWidget(self.live_sw)

            self.card_select = c = card('Select by texel density')
            self.hist = TexelHistogramWidget()
            self.hist.on_press = self._on_hist_press
            self.hist.on_select = self._on_hist_select
            self.hist.on_clear = self._on_hist_clear
            self.hist.on_double = self._on_hist_double
            c.body.addWidget(self.hist)
            self.hist_hint = _info_label('Drag: select    Shift: add    Ctrl: remove    Right-click: clear')
            c.body.addWidget(self.hist_hint)
            self.target_seg = Segmented(['Faces', 'UVs'], 0)
            self.target_seg.setToolTip(_tip(
                'What gets selected for the islands in the dragged range: their faces '
                '(visible in the viewport and the UV Editor) or their UVs.'))
            _form_row(c.body, 'Select', (self.target_seg, 1))
            self.sel_min = NumberField(DEFAULT_RANGE_MIN, 3, -1e9, 1e9, step=0.1)
            self.sel_max = NumberField(DEFAULT_RANGE_MAX, 3, -1e9, 1e9, step=0.1)
            tip = _tip('Min / max texel density of the islands to select. '
                       'Dragging in the diagram fills these in.')
            self.sel_min.setToolTip(tip)
            self.sel_max.setToolTip(tip)
            _form_row(c.body, 'Density', (self.sel_min, 1), 'to', (self.sel_max, 1))
            self.sel_btn = _button('Select', 'primary', tip='Select the islands whose texel density '
                                                             'is between these two values.')
            self.sel_clear_btn = _button('Clear', tip='Clear the selection.')
            self.sel_btn.clicked.connect(lambda v=False: self._on_select_range())
            self.sel_clear_btn.clicked.connect(lambda v=False: self._on_select_clear())
            _form_row(c.body, None, (self.sel_btn, 1), (self.sel_clear_btn, 1))

            self.card_pixel = c = card('Select by pixel size')
            self.px_axis_seg = Segmented(['X  (width)', 'Y  (height)', 'Both'], 2)
            self.px_axis_seg.setToolTip(_tip(
                'Which size of the island is tested, in pixels on the texture: X = width, '
                'Y = height, Both = width AND height must both pass. For "either": press '
                'Select with X, then Add with Y.'))
            _form_row(c.body, 'Axis', (self.px_axis_seg, 1))
            self.px_op_combo = StyledCombo(PIXEL_OP_LABELS, 0)
            self.px_op_combo.setToolTip(_tip(
                'Less than: size < n.   More than: size > n.   Equal to: within +/- 0.5 px of n '
                '(the same whole pixel count).   Range: from Min to Max, both included.'))
            self.px_op_combo.currentIndexChanged.connect(lambda i: self._on_px_op_changed())
            _form_row(c.body, 'Condition', (self.px_op_combo, 1))
            self.px_a = NumberField(DEFAULT_PIXEL_A, 2, 0, 1e9, step=8, suffix='px')
            self.px_b = NumberField(DEFAULT_PIXEL_B, 2, 0, 1e9, step=8, suffix='px')
            tip = _tip('n, in pixels. The second box is only used by Range.')
            self.px_a.setToolTip(tip)
            self.px_b.setToolTip(tip)
            self.px_to_lbl = QtWidgets.QLabel('to')
            self.px_to_lbl.setObjectName('caption')
            _form_row(c.body, 'Pixels', (self.px_a, 1), self.px_to_lbl, (self.px_b, 1))
            self.px_target_seg = Segmented(['Faces', 'UVs'], 0)
            self.px_target_seg.setToolTip(_tip(
                'What gets selected for the matching islands: their faces (visible in the '
                'viewport and the UV Editor) or their UVs.'))
            _form_row(c.body, 'Select', (self.px_target_seg, 1))
            self.px_select_btn = _button('Select', 'primary', tip=(
                'Select the matching islands of the selected meshes (replaces the current selection).'))
            self.px_add_btn = _button('Add', tip='Add the matching islands to the current selection.')
            self.px_remove_btn = _button('Remove', tip='Take the matching islands out of the current selection.')
            self.px_select_btn.clicked.connect(lambda v=False: self._on_px_select('replace'))
            self.px_add_btn.clicked.connect(lambda v=False: self._on_px_select('add'))
            self.px_remove_btn.clicked.connect(lambda v=False: self._on_px_select('remove'))
            _form_row(c.body, None, (self.px_select_btn, 1), (self.px_add_btn, 1), (self.px_remove_btn, 1))
            self.px_info = _info_label('Islands are measured with the Texture Size above')
            c.body.addWidget(self.px_info)

            self.card_set = c = card('Set texel density')
            self.td_field = NumberField(DEFAULT_TARGET_TD, 3, 0, 1e9, step=0.1, suffix=_unit_label(1.0))
            self.td_field.setToolTip(_tip(
                'The texel density the islands are scaled to, in the unit chosen under Units, '
                'measured with the Texture Size at the top.'))
            self.td_get_btn = _button('Get', tip=(
                'Read the texel density of the selection into Target (the average of the islands it touches).'))
            self.td_get_btn.clicked.connect(lambda v=False: self._on_td_get())
            _form_row(c.body, 'Target', (self.td_field, 1), self.td_get_btn)
            self.td_mode_seg = Segmented(['Per island', 'Selection average'], 0)
            self.td_mode_seg.setToolTip(_tip(
                'Per island: EVERY island gets exactly the Target density; each one is scaled around '
                'the center of its own UV box.   Selection average: the AVERAGE density of the whole '
                'selection becomes the Target. All islands are scaled by the same factor around the '
                'center of the selection, so the density differences between them stay.'))
            _form_row(c.body, 'Apply to', (self.td_mode_seg, 1))
            self.td_set_btn = _button('Set Texel Density on Selection', 'primary', tip=(
                'Scale the UV islands of the selected objects / faces / UVs to the Target density. '
                'A whole island is scaled as soon as any part of it is selected. One Ctrl+Z undoes '
                'it (press Apply afterwards to refresh the colors).'))
            self.td_set_btn.clicked.connect(lambda v=False: self._on_td_set())
            c.body.addWidget(self.td_set_btn)
            self.td_info = _info_label('Select objects, faces or UVs, then press Set')
            c.body.addWidget(self.td_info)

            self.card_results = c = card('Results per object', expanded=False)
            self.result_list = QtWidgets.QListWidget()
            self.result_list.setMinimumHeight(96)
            self.result_list.setMaximumHeight(150)
            self.result_list.setTextElideMode(_Qt.ElideRight)
            c.body.addWidget(self.result_list)

            col.addStretch(1)

            bottom = QtWidgets.QWidget()
            bottom.setObjectName('bottom')
            bottom.setAttribute(_Qt.WA_StyledBackground, True)
            bl = QtWidgets.QVBoxLayout(bottom)
            bl.setContentsMargins(12, 10, 12, 8)
            bl.setSpacing(8)
            self.status = StatusBar()
            self.status.set_message('Ready - select meshes and press Apply')
            bl.addWidget(self.status)
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(8)
            self.apply_btn = _button('Apply / Update on Selection', 'primary', big=True, tip=(
                'Applies the density override to the selected meshes. Also re-reads the UVs if the '
                'override is already active (press it again after you edit UVs).'))
            self.restore_btn = _button('Restore Original', big=True, tip=(
                'Puts the original materials back and deletes the override shaders.'))
            self.apply_btn.clicked.connect(lambda v=False: self._on_apply())
            self.restore_btn.clicked.connect(lambda v=False: self._on_restore())
            row.addWidget(self.apply_btn, 5)
            row.addWidget(self.restore_btn, 3)
            bl.addLayout(row)
            self.footer = QtWidgets.QLabel(
                'A Tool by <a href="%s" style="color:%s;">AreJustPolygons!</a>' % (CREATOR_URL, THEME['accent']))
            self.footer.setObjectName('footer')
            self.footer.setAlignment(_ALIGN_C)
            self.footer.setAccessibleName(FOOTER_TEXT)
            self.footer.setToolTip(_tip('Open the AreJustPolygons page on Superhive Market\n' + CREATOR_URL))
            self.footer.linkActivated.connect(self._on_footer_link)
            bl.addWidget(self.footer)
            root.addWidget(bottom)

        def _on_footer_link(self, *args):
            if not _open_creator_page():
                self.status.set_message('Could not open the web browser - the page is %s' % CREATOR_URL, True)

        def _register_callbacks(self):
            self._remove_callbacks()
            msg = _om2.MSceneMessage
            wanted = [(msg.kBeforeSave, self._on_before_save),
                      (msg.kAfterNew, self._on_scene_replaced),
                      (msg.kAfterOpen, self._on_scene_replaced)]
            for name, fn in (('kBeforeExport', self._on_before_export),
                             ('kAfterExport', self._on_after_export)):
                const = getattr(msg, name, None)
                if const is not None:
                    wanted.append((const, fn))
            for const, fn in wanted:
                try:
                    self._cb_ids.append(msg.addCallback(const, fn))
                except Exception:
                    pass

        def _remove_callbacks(self):
            for cb in self._cb_ids:
                try:
                    _om2.MMessage.removeCallback(cb)
                except Exception:
                    pass
            self._cb_ids = []

        def _on_before_save(self, *args):
            if not self.core.active:
                return
            try:
                report = self.core.restore()
                self._clear_result()
                text, problem = self._report_text(report)
                if text:
                    cmds.warning('Texel Density: ' + text)
                self._status('Override removed before saving - press Apply to resume'
                             + ('  |  ' + text if text else ''), error=problem)
                cmds.inViewMessage(amg='Texel density override <hl>removed</hl> before saving',
                                   pos='midCenter', fade=True, fadeStayTime=2000, fadeOutTime=500)
            except Exception:
                pass

        def _on_before_export(self, *args):
            if not self.core.active or self._resume is not None:
                return
            try:
                shapes = self.core.pause()
            except Exception:
                return
            if shapes:
                self._resume = shapes
                self._status('Override paused while Maya exports / autosaves - it comes back by itself')

        def _on_after_export(self, *args):
            shapes, self._resume = self._resume, None
            if not shapes:
                return
            try:
                self._run(shapes, reanalyze=False)
            except Exception:
                pass

        def _on_scene_replaced(self, *args):
            self.core.reset_state()
            self._resume = None
            try:
                self._clear_result()
                self._status('Scene changed - override state reset')
            except Exception:
                pass

        def _on_close(self):
            self._remove_callbacks()
            try:
                self._live_timer.stop()
            except (RuntimeError, AttributeError):
                pass
            self._resume = None
            try:
                self.core.restore()
            except Exception:
                pass

        def showEvent(self, ev):
            QtWidgets.QWidget.showEvent(self, ev)
            if not self._title_done:
                self._title_done = True
                _dark_title_bar(self)

        def closeEvent(self, ev):
            global _ui_instance
            self._on_close()
            if _ui_instance is self:
                _ui_instance = None
            QtWidgets.QWidget.closeEvent(self, ev)

        def _sync_preset(self):
            w, h = self.w_field.value(), self.h_field.value()
            sizes = (256, 512, 1024, 2048, 4096, 8192)
            self.preset_seg.setIndex(sizes.index(w) if w == h and w in sizes else None)

        def _on_w_changed(self, *args):
            if self.square_sw.isChecked():
                self.h_field.setValue(self.w_field.value())
            self._sync_preset()
            self._on_param_changed()

        def _on_h_changed(self, *args):
            if self.square_sw.isChecked():
                self.w_field.setValue(self.h_field.value())
            self._sync_preset()
            self._on_param_changed()

        def _on_preset_index(self, i):
            self._on_preset((256, 512, 1024, 2048, 4096, 8192)[i])

        def _on_preset(self, size):
            self.w_field.setValue(size)
            self.h_field.setValue(size)
            self._sync_preset()
            self._on_param_changed()

        def _manual_on(self):
            return self.range_seg.index() == 1

        def _on_range_mode(self, *args):
            manual = self._manual_on()
            if manual:
                if self._manual_pair is not None:
                    self.min_field.setValue(self._manual_pair[0])
                    self.max_field.setValue(self._manual_pair[1])
                    self._manual_pair = None
            elif self._manual_pair is None:
                self._manual_pair = (self.min_field.value(), self.max_field.value())
            self.min_field.setEnabled(manual)
            self.max_field.setEnabled(manual)
            self._on_param_changed()

        def _on_unit_changed(self, *args):
            new_scale = 100.0 if self.unit_seg.index() == 1 else 1.0
            if abs(new_scale - self._unit_scale) > 1e-9:
                factor = new_scale / self._unit_scale
                self.min_field.setValue(self.min_field.value() * factor)
                self.max_field.setValue(self.max_field.value() * factor)
                if self._manual_pair is not None:
                    self._manual_pair = (self._manual_pair[0] * factor, self._manual_pair[1] * factor)
                self.td_field.setValue(self.td_field.value() * factor)
                self.td_field.setSuffix(_unit_label(new_scale))
                self._unit_scale = new_scale
            if not self.core.active:
                self._clear_result()
            self._on_param_changed()

        def _on_gradient_changed(self, *args):
            self._refresh_legend()
            self._on_param_changed()

        def _on_param_changed(self, *args):
            if not self.core.active:
                self._sync_legend_labels()
                self._update_hist()
            elif self.live_sw.isChecked():
                self._schedule_live()

        def _schedule_live(self):
            if self._live_timer.isActive():
                return
            wait = self._live_gap - (time.time() - self._live_last)
            if wait > 0.0:
                self._live_timer.start(int(wait * 1000.0) + 1)
            else:
                self._live_fire()

        def _live_fire(self):
            if not (self.core.active and self.live_sw.isChecked()):
                return
            started = time.time()
            self._run(list(self.core.saved.keys()), reanalyze=False)
            took = time.time() - started
            self._live_gap = 0.0 if took * 1000.0 < LIVE_FAST_MS else min(2.0, took * 2.0)
            self._live_last = time.time()

        @staticmethod
        def _selection_info():
            sel = cmds.ls(selection=True, long=True) or []
            try:
                hil = cmds.ls(hilite=True, long=True) or []
            except Exception:
                hil = []
            comps_only = bool(sel) and all('.' in s.split('|')[-1] for s in sel)
            return sel + [h for h in hil if h not in sel], comps_only

        @staticmethod
        def _selected_nodes():
            return TexelDensityVizUI._selection_info()[0]

        @staticmethod
        def _explain_empty(nodes):
            if not nodes:
                return 'Nothing is selected - select one or more polygon meshes first'
            parts = []
            for n in nodes[:3]:
                base = n.split('.')[0]
                try:
                    parts.append('%s (%s)' % (base.split('|')[-1], cmds.nodeType(base)))
                except Exception:
                    parts.append(base.split('|')[-1])
            more = ' +%d more' % (len(nodes) - 3) if len(nodes) > 3 else ''
            for n in nodes:
                base = n.split('.')[0]
                try:
                    below = cmds.listRelatives(base, allDescendents=True, fullPath=True) or []
                    print('[TexelDensity] %s (%s) -> below it: %s' % (
                        base, cmds.nodeType(base),
                        ', '.join('%s (%s)' % (b.split('|')[-1], cmds.nodeType(b)) for b in below) or 'nothing'))
                except Exception as e:
                    print('[TexelDensity] could not inspect %s: %s' % (base, e))
            return 'No polygon mesh found in selection: %s%s' % (', '.join(parts), more)

        def _on_apply(self, *args):
            nodes, comps_only = self._selection_info()
            shapes = TexelDensityOverride.shapes_from_nodes(nodes)
            refresh = self.core.active and (not shapes or (comps_only and all(s in self.core.saved for s in shapes)))
            if refresh:
                shapes = list(self.core.saved.keys())
            if not shapes:
                msg = self._explain_empty(nodes)
                cmds.warning('Texel Density: ' + msg)
                self._status(msg, error=True)
                return
            if not (refresh and comps_only):
                self._hist_call('clear_selection')
            self._run(shapes, reanalyze=True, announce=True)

        @staticmethod
        def _report_text(report):
            if not report:
                return '', False
            parts, problem = [], False
            missing = report.get('missing_sgs') or []
            if missing:
                parts.append('%d original shading group%s no longer exist%s (%s%s): their faces got the '
                             'default material' % (len(missing), '' if len(missing) == 1 else 's',
                                                   's' if len(missing) == 1 else '', ', '.join(missing[:3]),
                                                   ' ...' if len(missing) > 3 else ''))
                problem = True
            edited = report.get('edited') or []
            if edited:
                parts.append('%s %s edited while the override was on: the materials were put back as well '
                             'as possible - please check %s' % (
                                 ', '.join(edited[:3]) + (' ...' if len(edited) > 3 else ''),
                                 'was' if len(edited) == 1 else 'were', 'it' if len(edited) == 1 else 'them'))
                problem = True
            foreign = report.get('foreign') or 0
            if foreign:
                parts.append('%d object%s made while the override was on now %s the default material' % (
                    foreign, '' if foreign == 1 else 's', 'has' if foreign == 1 else 'have'))
            gone = report.get('gone') or []
            if gone:
                parts.append('%s %s deleted while the override was on' % (
                    ', '.join(gone[:3]) + (' ...' if len(gone) > 3 else ''), 'was' if len(gone) == 1 else 'were'))
            return '; '.join(parts), problem

        def _on_restore(self, *args):
            report = self.core.restore()
            self._clear_result()
            text, problem = self._report_text(report)
            if text:
                cmds.warning('Texel Density: ' + text)
                self._status('Original materials restored.  Note: ' + text, error=problem)
            else:
                self._status('Original materials restored')
            cmds.inViewMessage(amg='Texel density <hl>deactivated</hl> - Materials restored',
                               pos='midCenter', fade=True, fadeStayTime=2000, fadeOutTime=500)

        def _gradient_index(self):
            return max(0, self.grad_combo.currentIndex())

        def _shader_kind(self):
            i = self.shader_seg.index()
            return SHADER_KINDS[i if i is not None and 0 <= i < len(SHADER_KINDS) else 0]

        def _display_mode(self):
            i = self.display_seg.index()
            return DISPLAY_MODES[i if i is not None and 0 <= i < len(DISPLAY_MODES) else 0]

        def _read_params(self):
            return {
                'tex_w': self.w_field.value(),
                'tex_h': self.h_field.value(),
                'per_island': self.mode_seg.index() == 1,
                'unit_scale': 100.0 if self.unit_seg.index() == 1 else 1.0,
                'auto_range': self.range_seg.index() == 0,
                'manual_min': self.min_field.value(),
                'manual_max': self.max_field.value(),
                'steps': int(self.steps_slider.value()),
                'gradient': self._gradient_index(),
                'invert': self.invert_sw.isChecked(),
                'merge_tris': self.merge_sw.isChecked(),
                'max_angle': float(self.angle_slider.value()),
                'shader': self._shader_kind(),
                'display': self._display_mode(),
            }

        def _run(self, shapes, reanalyze, announce=False, refresh=None):
            params = self._read_params()
            with _BusyCursor():
                try:
                    result = self.core.apply(shapes, reanalyze=reanalyze, refresh=refresh, **params)
                except Cancelled as e:
                    if not self.core.active:
                        self._clear_result()
                    self._status(str(e))
                    return
                except ValueError as e:
                    self._run_failed(str(e))
                    cmds.warning('Texel Density: %s' % e)
                    return
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self._run_failed('Error: %s' % e)
                    cmds.warning('Texel Density error: %s%s' % (e, _where(e)))
                    return

            self._show_result(result)
            if (result.get('timing') or {}).get('total', 0.0) >= TIMING_PRINT:
                print('[TexelDensity] ' + timing_summary(result)[1])
            note = display_note(result)[1]
            if note != self._last_note:
                self._last_note = note
                if note:
                    print('[TexelDensity] ' + note)
            text, problem = self._report_text(result.get('restored'))
            if text:
                cmds.warning('Texel Density: ' + text)
                self._status('%s  |  Before: %s' % (self.status.text(), text), error=problem)
            if announce:
                cmds.inViewMessage(
                    amg='Texel density <hl>activated</hl> - red = low, blue = high (magenta = no UVs)',
                    pos='midCenter', fade=True, fadeStayTime=2000, fadeOutTime=500)

        def _run_failed(self, msg):
            if not self.core.active:
                self._clear_result()
            self._status(msg, error=True)

        def _show_result(self, res):
            self._last_res = res
            unit = res['unit']
            lo, hi = res['range']
            self.result_list.clear()
            for o in res['objects']:
                if o['min'] is None:
                    line = '%s  (%s)  - NO VALID UVs  (%d faces)' % (o['name'], o['uv_set'], o['faces'])
                else:
                    line = '%s  (%s)  min %.3f | avg %.3f | max %.3f  -  %d faces' % (
                        o['name'], o['uv_set'], o['min'], o['avg'], o['max'], o['faces'])
                    if res['per_island']:
                        line += ', %d islands' % o['islands']
                    elif o['merged']:
                        line += ', %d tri-pairs merged' % o['merged']
                    if o['invalid']:
                        line += ', %d INVALID' % o['invalid']
                item = QtWidgets.QListWidgetItem(line)
                item.setToolTip(line)
                self.result_list.addItem(item)

            self.grad_bar.set_labels('%.3f %s' % (lo, unit), '%.3f' % ((lo + hi) * 0.5),
                                     '%.3f %s' % (hi, unit))
            if res['auto']:
                if self._manual_pair is None:
                    self._manual_pair = (self.min_field.value(), self.max_field.value())
                self.min_field.setValue(lo)
                self.max_field.setValue(hi)

            if res['no_valid']:
                self._status('No faces with valid UVs in the active UV set - everything is magenta',
                             error=True)
            else:
                msg = 'Range %.3f - %.3f %s (%s) | %d obj | %d islands | %d invalid' % (
                    lo, hi, unit, 'auto' if res['auto'] else 'manual',
                    len(res['objects']), res['islands_total'], res['invalid_total'])
                short, detail = timing_summary(res)
                if short and res['timing']['total'] >= TIMING_SHOW:
                    msg += ' | ' + short
                note, note_detail = display_note(res)
                if note:
                    msg += ' | ' + note
                    detail = '\n'.join(x for x in (detail, note_detail) if x)
                self._status(msg, detail=detail or None)
            self._update_hist(message='No UV islands with valid UVs in the active UV set')

        def _clear_result(self):
            self._last_res = None
            self._last_note = ''
            self._sel_base = None
            try:
                self.result_list.clear()
            except RuntimeError:
                pass
            self._sync_legend_labels()
            self._update_hist()

        def _sync_legend_labels(self):
            try:
                if self._manual_on():
                    lo, hi = self.min_field.value(), self.max_field.value()
                    unit = _unit_label(self._unit_scale)
                    self.grad_bar.set_labels('%.3f %s' % (lo, unit), '%.3f' % ((lo + hi) * 0.5),
                                             '%.3f %s' % (hi, unit))
                else:
                    self.grad_bar.set_labels('-', '', '-')
            except RuntimeError:
                pass

        def _refresh_legend(self):
            self.grad_bar.set_gradient(self._gradient_index(), self.invert_sw.isChecked())

        def _status(self, msg, error=False, detail=None):
            try:
                self.status.set_message(msg, error, detail)
            except RuntimeError:
                pass

        def _manual_range(self):
            if not self._manual_on():
                return None
            lo, hi = self.min_field.value(), self.max_field.value()
            return (lo, hi) if hi > lo else None

        def _update_hist(self, message=None):
            active = self.core.active
            idx = self.core.island_index if active else None
            has_islands = idx is not None and len(idx) > 0
            scale = idx.scale if has_islands else self._unit_scale
            h = self.hist
            if h is not None:
                try:
                    gradient = self._gradient_index()
                    invert = bool(self.invert_sw.isChecked())
                    res = self._last_res if active else None
                    if res is not None:
                        crange, unit = res['range'], res['unit']
                    else:
                        crange, unit = self._manual_range(), _unit_label(self._unit_scale)
                    if has_islands:
                        h.set_data(idx.disp, unit, crange, gradient, invert)
                    else:
                        h.clear_data(crange, gradient, invert, message, unit)
                except RuntimeError:
                    pass
            self._sync_sel_unit(scale)

        def _sync_sel_unit(self, scale):
            if abs(scale - self._sel_scale) < 1e-9:
                return
            f = scale / self._sel_scale
            self.sel_min.setValue(self.sel_min.value() * f)
            self.sel_max.setValue(self.sel_max.value() * f)
            self._sel_scale = scale

        def _hist_target(self):
            return 'uvs' if self.target_seg.index() == 1 else 'faces'

        @staticmethod
        def _enter_component_mode(target):
            try:
                if not cmds.selectMode(query=True, component=True):
                    cmds.selectMode(component=True)
                if target == 'uvs':
                    cmds.selectType(polymeshUV=True)
                else:
                    cmds.selectType(facet=True)
            except Exception:
                pass

        def _clamp_range(self, lo, hi):
            idx = self.core.island_index
            if idx is not None and len(idx):
                if lo == float('-inf'):
                    lo = idx.disp[0]
                if hi == float('inf'):
                    hi = idx.disp[-1]
            return lo, hi

        def _on_hist_press(self, mode):
            self._sel_base = None
            try:
                current = cmds.ls(selection=True, long=True) or []
            except Exception:
                current = []
            self._sel_before = current
            if mode != 'replace':
                self._sel_base = list(current)
            self._enter_component_mode(self._hist_target())

        def _on_hist_double(self):
            before, self._sel_before = self._sel_before, None
            self._sel_base = None
            if before is None:
                return
            try:
                with _UndoOff():
                    if before:
                        cmds.select(before, replace=True)
                    else:
                        cmds.select(clear=True)
            except Exception:
                pass
            self._hist_call('clear_selection')

        def _on_hist_select(self, i0, i1, lo, hi, mode, final):
            idx = self.core.island_index
            if idx is None or not self.core.active:
                return
            islands = idx.islands(i0, i1)
            started = time.time()
            try:
                self.core.select_islands(islands, self._hist_target(), mode=mode, base=self._sel_base)
            except ValueError as e:
                self._status(str(e), error=True)
                cmds.warning('Texel Density: %s' % e)
                self._hist_call('clear_selection')
                return
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._status('Selection error: %s' % e, error=True)
                return
            elapsed_ms = (time.time() - started) * 1000.0
            lo, hi = self._clamp_range(lo, hi)
            self._hist_call('set_selection', lo, hi, len(islands), mode)
            if self.hist is not None:
                try:
                    self.hist.throttle_ms = int(max(45, min(1500, elapsed_ms * 2.5)))
                except RuntimeError:
                    pass
            self.sel_min.setValue(lo)
            self.sel_max.setValue(hi)
            if final:
                unit = _unit_label(idx.scale)
                verb = {'add': 'Added', 'remove': 'Removed'}.get(mode, 'Selected')
                if islands:
                    self._status('%s %d of %d islands  (%.3f - %.3f %s)' % (
                        verb, len(islands), len(idx), lo, hi, unit))
                else:
                    self._status('No islands between %.3f and %.3f %s' % (lo, hi, unit))

        def _hist_call(self, name, *args):
            h = self.hist
            if h is None:
                return
            try:
                getattr(h, name)(*args)
            except RuntimeError:
                pass

        def _on_hist_clear(self):
            self._on_select_clear()

        def _on_select_clear(self, *args):
            self._sel_base = None
            try:
                self.core.select_islands([])
            except Exception:
                pass
            self._hist_call('clear_selection')
            self._status('Selection cleared')

        def _on_select_range(self, *args):
            idx = self.core.island_index
            if idx is None or not self.core.active or not len(idx):
                self._status('Press Apply first - there are no islands to select yet', error=True)
                return
            a = self.sel_min.value()
            b = self.sel_max.value()
            lo, hi = min(a, b), max(a, b)
            i0, i1 = idx.indices_for_values(lo, hi)
            self._sel_base = None
            self._enter_component_mode(self._hist_target())
            self._on_hist_select(i0, i1, lo, hi, 'replace', True)

        def _px_axis(self):
            i = self.px_axis_seg.index()
            i = 2 if i is None else i
            return PIXEL_AXES[max(0, min(len(PIXEL_AXES) - 1, i))]

        def _px_op(self):
            i = max(0, self.px_op_combo.currentIndex())
            return PIXEL_OPS[min(len(PIXEL_OPS) - 1, i)]

        def _on_px_op_changed(self, *args):
            is_range = self._px_op() == 'range'
            self.px_b.setEnabled(is_range)
            self.px_to_lbl.setEnabled(is_range)

        def _on_px_select(self, mode='replace'):
            nodes = self._selection_info()[0]
            shapes = TexelDensityOverride.shapes_from_nodes(nodes)
            if not shapes and self.core.active:
                shapes = list(self.core.saved.keys())
            scope = self._px_scope
            try:
                now = cmds.ls(selection=True, long=True) or []
            except Exception:
                now = []
            if scope and now == scope['selection'] and all(cmds.objExists(sh) for sh in scope['shapes']):
                shapes = list(scope['shapes'])
            if not shapes:
                msg = self._explain_empty(nodes)
                cmds.warning('Texel Density: ' + msg)
                self._status(msg, error=True)
                return
            axis, op = self._px_axis(), self._px_op()
            a = self.px_a.value()
            b = self.px_b.value()
            tex_w = max(1, int(self.w_field.value()))
            tex_h = max(1, int(self.h_field.value()))
            target = 'uvs' if self.px_target_seg.index() == 1 else 'faces'

            self._enter_component_mode(target)
            with _BusyCursor():
                try:
                    res = self.core.select_by_pixels(shapes, tex_w, tex_h, axis, op, a, b,
                                                     target=target, mode=mode)
                except ValueError as e:
                    self._status(str(e), error=True)
                    cmds.warning('Texel Density: %s' % e)
                    return
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self._status('Selection error: %s' % e, error=True)
                    cmds.warning('Texel Density error: %s%s' % (e, _where(e)))
                    return

            self._sel_base = None
            self._hist_call('clear_selection')
            try:
                self._px_scope = {'selection': cmds.ls(selection=True, long=True) or [],
                                  'shapes': list(shapes)}
            except Exception:
                self._px_scope = None
            total, n = res['total'], res['matched']
            if total:
                info = '%s  |  width %.1f - %.1f px  |  height %.1f - %.1f px' % (
                    _islands(total), res['w_min'], res['w_max'], res['h_min'], res['h_max'])
            else:
                info = 'No UV islands in the active UV set'
            self.px_info.setText(info)
            if not total:
                self._status('No UV islands found in the active UV set of the selected meshes',
                             error=True)
                return
            desc = describe_pixel_condition(axis, op, a, b)
            size = '%d x %d px texture' % (tex_w, tex_h)
            if not n:
                self._status('No island with %s  (%s, %s)' % (desc, _islands(total), size))
            else:
                verb = {'add': 'Added', 'remove': 'Removed'}.get(mode, 'Selected')
                self._status('%s %d of %s: %s  (%s)' % (verb, n, _islands(total), desc, size))

        def _td_context(self):
            spec = TexelDensityOverride.read_selection()
            if not spec:
                msg = 'Nothing to scale - select objects, faces or UVs of a polygon mesh first'
                cmds.warning('Texel Density: ' + msg)
                self._status(msg, error=True)
                return None
            return (spec, max(1, int(self.w_field.value())), max(1, int(self.h_field.value())))

        def _on_td_get(self):
            ctx = self._td_context()
            if ctx is None:
                return
            try:
                res = self.core.measure_selection(*ctx)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._status('Error: %s' % e, error=True)
                cmds.warning('Texel Density error: %s%s' % (e, _where(e)))
                return
            if res['avg'] is None:
                msg = 'No UV island with a valid area in the selection'
                self._status(msg, error=True)
                self.td_info.setText(msg)
                return
            k = self._unit_scale
            self.td_field.setValue(res['avg'] * k)
            info = 'Selection: %s | average %.3f | min %.3f | max %.3f %s' % (
                _islands(res['count']), res['avg'] * k, res['min'] * k, res['max'] * k, _unit_label(k))
            if res['skipped']:
                info += ' | %d skipped (no valid UV area)' % res['skipped']
            self.td_info.setText(info)
            self._status(info)

        def _on_td_set(self):
            ctx = self._td_context()
            if ctx is None:
                return
            k = self._unit_scale
            shown = self.td_field.value()
            if not shown > 0.0:
                msg = 'The target texel density must be greater than 0'
                self._status(msg, error=True)
                cmds.warning('Texel Density: ' + msg)
                return
            overall = self.td_mode_seg.index() == 1
            with _BusyCursor():
                try:
                    res = self.core.set_texel_density(ctx[0], ctx[1], ctx[2], shown / k, overall)
                except ValueError as e:
                    self._status(str(e), error=True)
                    cmds.warning('Texel Density: %s' % e)
                    return
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self._status('Error: %s' % e, error=True)
                    cmds.warning('Texel Density error: %s%s' % (e, _where(e)))
                    return
            if res['changed'] and self.core.active:
                self._run(list(self.core.saved.keys()), reanalyze=False, refresh=res['edited_shapes'])
            self._show_td_result(res, k)

        def _show_td_result(self, res, k):
            unit = _unit_label(k)
            n = res['count']
            target = res['target'] * k
            skipped = ' | %d skipped (no valid UV area)' % res['skipped'] if res['skipped'] else ''
            if res['after_avg'] is not None:
                info = 'Now: average %.3f | min %.3f | max %.3f %s' % (
                    res['after_avg'] * k, res['after_min'] * k, res['after_max'] * k, unit)
            else:
                info = 'Select objects, faces or UVs, then press Set'
            self.td_info.setText(info)

            dev = res['deviation']
            if not n:
                self._status('No UV island with a valid area in the selection' + skipped, error=True)
            elif res['failed']:
                msg = 'Could not scale %d of %s: %s' % (res['failed'], _islands(n), res['error'])
                self._status(msg, error=True)
                cmds.warning('Texel Density: ' + msg)
            elif res['cancelled']:
                self._status('Cancelled: %d of %s scaled  (Ctrl+Z undoes them)' % (res['changed'], _islands(n)))
            elif dev is not None and dev > TD_TOLERANCE:
                if res['overall']:
                    got = 'average %.3f' % (res['after_avg'] * k)
                else:
                    got = '%.3f - %.3f' % (res['after_min'] * k, res['after_max'] * k)
                msg = 'Measured %s %s afterwards instead of %.3f - the UVs did not scale as expected' % (
                    got, unit, target)
                self._status(msg, error=True)
                cmds.warning('Texel Density: ' + msg)
            elif not res['changed']:
                self._status('Already at %.3f %s - nothing to scale%s' % (target, unit, skipped))
            elif res['overall']:
                self._status('Selection average %.3f -> %.3f %s: %s scaled by x%.3f%s' % (
                    res['avg'] * k, target, unit, _islands(res['changed']), res['scale_min'], skipped))
            else:
                if abs(res['scale_max'] - res['scale_min']) < 5e-4:
                    factor = 'x%.3f' % res['scale_min']
                else:
                    factor = 'x%.3f - x%.3f' % (res['scale_min'], res['scale_max'])
                self._status('Set %s to %.3f %s  (scaled %s)%s' % (
                    _islands(res['count']), target, unit, factor, skipped))


_ui_instance = None


def _close_old_windows():
    global _ui_instance
    old, _ui_instance = _ui_instance, None
    if old is not None:
        try:
            old.close()
            old.deleteLater()
        except RuntimeError:
            pass
    app = QtWidgets.QApplication.instance()
    if app is not None:
        for w in app.topLevelWidgets():
            try:
                if w.objectName() == 'TexelDensityVizUI':
                    w.close()
                    w.deleteLater()
            except RuntimeError:
                pass


def show_texel_density_visualizer():
    global _ui_instance
    if QtWidgets is None or QtWidgets.QApplication.instance() is None:
        raise RuntimeError('The Texel Density Visualizer needs Maya with Qt (PySide6 / PySide2).')
    _close_old_windows()
    ui = TexelDensityVizUI(_maya_main_window())
    ui.setAttribute(_Qt.WA_DeleteOnClose, True)
    _ui_instance = ui
    ui.show()
    ui.raise_()
    ui.activateWindow()
    return ui


if __name__ == '__main__':
    show_texel_density_visualizer()
