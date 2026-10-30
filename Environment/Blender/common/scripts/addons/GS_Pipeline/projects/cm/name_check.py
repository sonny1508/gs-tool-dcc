"""Check Names: the CM naming rules (names.py) applied to the objects in Scope.

Two kinds of finding, errors first:

  * Essentials: the anchors and wheel meshes every CM car needs
    (names.ESSENTIAL_ANCHORS, names.WHEELS), each under the right parent.
  * Spelling, on every object, custom parts included: a _LOD number in
    capitals, 0 to 2, that matches the objects above it, the same part
    letter as the part it sits in, English letters, digits and _ only, no
    Blender .001.

Custom parts differ from car to car, so beyond spelling they aren't checked
against a list.

Rows are for artists: the object and what's wrong with it, nothing more.
"""
from __future__ import annotations

from collections import Counter, namedtuple

from . import names

# One finding, as an object_log row: the object it is about ("" when there is
# none, e.g. a missing anchor), the line the Log shows, and its log level.
Problem = namedtuple("Problem", "name text level")


def check(objects):
    """The naming problems among ``objects``: missing / misplaced essentials first."""
    by_name = {obj.name: obj for obj in objects}
    problems = list(_essentials(by_name))
    lod_memo, part_memo = {}, {}
    for obj in sorted(objects, key=lambda o: o.name):
        problems.extend(_spelling(obj, lod_memo, part_memo))
    return problems


# ---------------------------------------------------------------------------
# Essentials
# ---------------------------------------------------------------------------
def _essentials(by_name):
    for lods, anchor, parent in names.ESSENTIAL_ANCHORS:
        for lod in lods:
            name = names.with_lod(anchor, lod)
            parent_name = names.with_lod(parent, lod) if parent else None
            obj = by_name.get(name)
            if obj is None:
                yield Problem("", "{} is missing.".format(name), "error")
            elif parent_name and (obj.parent is None or obj.parent.name != parent_name):
                yield Problem(name, "{} should be under {}.".format(name, parent_name), "error")
    yield from _wheels(by_name)


def _wheels(by_name):
    found = {}      # (wheel part, LOD) -> [(car, name)]
    for name in by_name:
        wheel = names.wheel_of(name)
        if wheel is not None:
            car, part, lod = wheel
            found.setdefault((part, lod), []).append((car, name))
    # The car's short name (audi_r8) is whatever most wheel meshes start with.
    cars = Counter(car for hits in found.values() for car, _ in hits)
    car = cars.most_common(1)[0][0] if cars else "<car>"

    for part in names.WHEELS:
        for lod in names.WHEEL_LODS:
            hits = found.get((part, lod), [])
            if not hits:
                yield Problem("", "{} is missing.".format(
                    names.with_lod("{}_{}".format(car, part), lod)), "error")
            for _, name in hits[1:]:
                yield Problem(name, "{} is a duplicate wheel mesh.".format(name), "warn")
            for hit_car, name in hits:
                if hit_car != car:
                    yield Problem(name, "{} has wrong car name.".format(name), "warn")


# ---------------------------------------------------------------------------
# Spelling
# ---------------------------------------------------------------------------
def _expected(obj, read, memo):
    """The LOD or part letter (``read`` from a name) ``obj`` should have, going
    by the objects above it, or None.

    That is the parent's own, unless the parent is wrong itself: then what the
    parent should have had. So one wrong name (hood_carpaint_LOD14) is
    reported once, not again for each object under it.
    """
    if obj in memo:
        return memo[obj]
    value = None
    parent = obj.parent
    if parent is not None:
        above = _expected(parent, read, memo)
        own = read(parent.name)
        value = own if own is not None and (above is None or own == above) else above
    memo[obj] = value
    return value


def _cm_lod(name):
    """The LOD in ``name`` when it is one a CM car has (0-2), else None."""
    lod = names.lod_of(name)
    return lod if lod in names.LODS else None


def _character(name, ch):
    if ch == " ":
        return "{} has a space.".format(name)
    if not ch.isascii():        # looks English, isn't (a Cyrillic С)
        return "{} has non-English letter '{}'.".format(name, ch)
    return "{} has invalid character '{}'.".format(name, ch)


def _spelling(obj, lod_memo, part_memo):
    name = obj.name

    if names.duplicate_suffix(name):
        yield Problem(name, "{} has a duplicate suffix.".format(name), "warn")

    for ch in names.bad_characters(name):
        yield Problem(name, _character(name, ch), "warn")

    lod = names.lod_of(name)
    if lod is None:
        yield Problem(name, "{} has no LOD number.".format(name), "warn")
    else:
        if names.lod_misspelled(name):
            yield Problem(name, "{} has lowercase LOD.".format(name), "warn")
        expected = _expected(obj, _cm_lod, lod_memo)
        if lod not in names.LODS or (expected is not None and lod != expected):
            yield Problem(name, "{} has wrong LOD number.".format(name), "warn")

    part = names.part_of(name)
    if part is not None:
        if names.part_misspelled(name):
            yield Problem(name, "{} has misspelled part name.".format(name), "warn")
        expected = _expected(obj, names.part_of, part_memo)
        if expected is not None and part != expected:
            yield Problem(name, "{} has wrong part letter.".format(name), "warn")
