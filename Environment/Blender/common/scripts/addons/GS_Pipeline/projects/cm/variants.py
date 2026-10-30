"""Showing one LOD and one version of each custom part, by hiding the rest.

Everything is worked out from object names (names.py) and parenting, fresh on
every click, so a renamed object counts as soon as the panel is used again:

  * An object's LOD is the _LOD<n> in its name, or else the nearest one
    above it: l_paddle under anchor_l_paddle_LOD0 is LOD0. An object with no
    LOD anywhere above it is left as it is. One with a LOD other than 0-2
    (a typo) shows only under All.
  * A custom part is the outermost object with _part_<X> in its name
    (anchor_hood_part_B_LOD0) and everything under it. It replaces the
    default object of the same name without _part_<X> (anchor_hood_LOD0) and
    everything under that, at the same LOD. So a part's meshes don't have to
    match the default ones (hood part C is carbon only). A part with no
    default version (a front splitter) is shown or not.
  * A chosen part with no version at the LOD on show shows the default there.

Hiding is Blender's own (the eye, H / Alt+H) in the current view layer. Alt+H
shows everything again; the next click in the panel puts the choice back.
"""
from __future__ import annotations

from collections import defaultdict

from . import names

# The LOD choice that shows every LOD.
ALL_LODS = -1

# A part's choice when it shows its default version (or nothing, without one).
DEFAULT = ""


class Slot:
    """A part that has custom versions (hood, front bumper...)."""

    def __init__(self, key):
        self.key = key                      # anchor_hood
        self.label = names.slot_label(key)  # Hood
        self.has_default = False            # False for a part with no default version
        self.parts = {}                     # part letter -> the LODs it exists at


class Found:
    """What a scan read from the scope."""

    def __init__(self):
        self.objects = []       # in scope and in this view layer
        self.lod = {}           # object -> its LOD (own or from above), or None
        self.version = {}       # object -> (slot key, part letter or DEFAULT, LOD of that version)
        self.slots = {}         # slot key -> Slot

    def sorted_slots(self):
        return sorted(self.slots.values(), key=lambda slot: slot.label)


def scope_objects(context, collection, view_layer_only=True):
    """The objects in ``collection`` and the collections inside it (the whole
    scene when None). By default only those in this view layer: an object in
    an excluded collection can't be hidden."""
    source = collection.all_objects if collection is not None else context.scene.objects
    if not view_layer_only:
        return list(source)
    layer = context.view_layer.objects
    return [obj for obj in source if layer.get(obj.name) is not None]


def _part_root(obj):
    """The outermost object, from ``obj`` up, with _part_<X> in its name; None if there is none."""
    root = None
    while obj is not None:
        if names.part_of(obj.name) is not None:
            root = obj
        obj = obj.parent
    return root


def _subtree(root, children):
    stack = [root]
    while stack:
        obj = stack.pop()
        yield obj
        stack.extend(children.get(obj, ()))


def scan(context, collection):
    """Read the LODs and custom parts in scope (``collection``, or the whole scene)."""
    found = Found()
    found.objects = scope_objects(context, collection)
    in_scope = set(found.objects)
    lods = found.lod

    def lod_of(obj):
        if obj not in lods:
            lod = names.lod_of(obj.name)
            if lod is None and obj.parent is not None:
                lod = lod_of(obj.parent)
            lods[obj] = lod
        return lods[obj]

    # Custom parts: each object under a part root belongs to that version.
    by_name = {obj.name: obj for obj in found.objects}
    default_roots = {}      # (slot key, LOD) -> the default object the parts replace
    for obj in found.objects:
        lod_of(obj)
        root = _part_root(obj)
        if root is None:
            continue
        key = names.slot_key(root.name)
        part = names.part_of(root.name)
        lod = lod_of(root)
        slot = found.slots.get(key)
        if slot is None:
            slot = found.slots[key] = Slot(key)
        slot.parts.setdefault(part, set()).add(lod)
        found.version[obj] = (key, part, lod)
        if (key, lod) not in default_roots:
            default_roots[(key, lod)] = by_name.get(names.default_name(root.name))

    # Their default versions: the default root and everything under it.
    children = defaultdict(list)
    for obj in context.scene.objects:
        if obj.parent is not None:
            children[obj.parent].append(obj)
    for (key, lod), default in default_roots.items():
        if default is None:
            continue
        found.slots[key].has_default = True
        for obj in _subtree(default, children):
            if obj in in_scope and obj not in found.version:
                found.version[obj] = (key, DEFAULT, lod)
    return found


def _shown_version(slot, chosen, lod):
    """The version ``slot`` shows at ``lod``: the chosen part where it has that LOD, else the default."""
    return chosen if chosen and lod in slot.parts.get(chosen, ()) else DEFAULT


def show(found, lod_choice, choices):
    """Show the LOD ``lod_choice`` (or ALL_LODS) and, for each part, the version
    in ``choices`` (slot key -> part letter, DEFAULT when missing); hide the rest.

    Objects with no LOD and no part are left as they are.
    """
    for obj in found.objects:
        lod = found.lod[obj]
        version = found.version.get(obj)
        if lod is None and version is None:
            continue
        visible = lod_choice == ALL_LODS or lod is None or lod == lod_choice
        if visible and version is not None:
            key, part, version_lod = version
            visible = part == _shown_version(found.slots[key], choices.get(key, DEFAULT), version_lod)
        if obj.hide_get() == visible:
            if not visible:
                obj.select_set(False)       # as H does
            obj.hide_set(not visible)


def missing_lod(found, lod_choice, choices):
    """The slots whose chosen part has no version at ``lod_choice``, so the default shows there."""
    if lod_choice == ALL_LODS:
        return []
    missing = []
    for slot in found.sorted_slots():
        chosen = choices.get(slot.key, DEFAULT)
        if chosen in slot.parts and lod_choice not in slot.parts[chosen]:
            missing.append(slot)
    return missing
