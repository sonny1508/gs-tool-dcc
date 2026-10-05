# -*- coding: utf-8 -*-
"""
Shared LOD-group layer for GSPipeline tools.

Why this module exists
----------------------
Maya's Edit > Level of Detail > Level of Detail Group builds one group from the
selection *in selection order*, so a scene of ten assets means ten careful
selections, and project tools grew their own hard-coded copies of it (HW3's
createLodGroup only knows LODA..LODF and a single "Car_LOD_Group").

Here the grouping comes from the names instead, for any number of assets at once:

    Tree_LOD0  Tree_LOD1  Tree_LOD2  Rock_LOD0  Rock_LOD1

        Tree (lodGroup)              Rock (lodGroup)
          LOD_0 | Tree_LOD0            LOD_0 | Rock_LOD0
          LOD_1 | Tree_LOD1            LOD_1 | Rock_LOD1
          LOD_2 | Tree_LOD2

The node layout is the one Maya's own setup builds (lodUtils.mel and
performSetupLod*.mel, identical in 2022 and 2026): a lodGroup holding one LOD_<n>
transform per level, output[n] wired to LOD_<n>.lodVisibility, the view camera
connected, thresholds seeded the same way, and worldSpace on. Two deliberate
differences:

  * every level's Display is Show, not Use LOD, so all levels stay visible
    while artists work; and
  * a lodGroup that already has the asset's name is updated in place - each
    level present in the selection replaces that level's old content, other
    levels are left alone, and missing levels are added.

Pure maya.cmds - deliberately no pymel (it does not ship with Maya 2026).

Usage
-----
    import gs_lod

    gs_lod.build_lod_groups()                 # from the current selection
    group = gs_lod.lod_group_of(node)         # nearest lodGroup at/above node
    for index, slot in gs_lod.levels(group):  # index = displayLevel[] index
        ...
"""

import collections
import re

import maya.cmds as cmds

__all__ = [
    'USE_LOD', 'SHOW', 'HIDE', 'SLOT_PREFIX',
    'short_name', 'uuid_of', 'path_of',
    'parse_lod_name', 'lod_group_of', 'find_lod_groups', 'levels',
    'build_lod_groups',
]


# lodGroup.displayLevel[] enum.
USE_LOD, SHOW, HIDE = 0, 1, 2

# Maya names the per-level transforms LOD_0, LOD_1, ... (lodRoot() in lodUtils.mel).
SLOT_PREFIX = "LOD_"

# <asset>_LOD<level>, with an optional underscore before the level. The level is
# a number (Tree_LOD0, Tree_LOD_12) or one capital letter with A as level 0
# (Tree_LODA), the older studio convention. "_LOD" is case-sensitive.
_LOD_NAME = re.compile(r"^(?P<base>.+)_LOD_?(?P<level>\d+|[A-Z])$")

_OUTPUT_PLUG = re.compile(r"^(?:output|out)\[(\d+)\]$")

# Seed values Maya's own setup uses (lodUtils.mel).
_FIRST_PERCENTAGE = 64.0


def _default_log(message, level="info"):
    if level in ("warn", "error"):
        cmds.warning(message)
    else:
        print(message)


# ============================================================================
# NAMES AND LOOKUPS
# ============================================================================

def short_name(path):
    return path.rsplit("|", 1)[-1]


def uuid_of(path):
    return cmds.ls(path, uuid=True)[0]


def path_of(uuid):
    """Long name for a UUID, or None once the node is gone."""
    paths = cmds.ls(uuid, long=True)
    return paths[0] if paths else None


def _parent(path):
    parents = cmds.listRelatives(path, parent=True, fullPath=True)
    return parents[0] if parents else None


def _children(path):
    """Child transforms in outliner order (shapes left out)."""
    children = cmds.listRelatives(path, children=True, fullPath=True) or []
    return [child for child in children if not cmds.objectType(child, isAType="shape")]


def parse_lod_name(name):
    """(base, level) for a name like Tree_LOD2 or Tree_LODC, else None."""
    match = _LOD_NAME.match(short_name(name))
    if not match:
        return None
    level = match.group("level")
    return match.group("base"), int(level) if level.isdigit() else ord(level) - ord("A")


def lod_group_of(node):
    """The lodGroup at or nearest above node, or None."""
    paths = cmds.ls(node, long=True)
    path = paths[0] if paths else ""
    while path:
        if cmds.nodeType(path) == "lodGroup":
            return path
        path = path.rpartition("|")[0]
    return None


def find_lod_groups(name):
    """Every lodGroup whose short name is name."""
    return [group for group in cmds.ls(type="lodGroup", long=True) or []
            if short_name(group) == name]


def _output_index(group, child):
    """Index of the group's output[] plug driving child, or None if unwired."""
    plugs = cmds.listConnections(child + ".lodVisibility", source=True, destination=False,
                                 plugs=True, fullNodeName=True) or []
    for plug in plugs:
        node, _, attr = plug.partition(".")
        match = _OUTPUT_PLUG.match(attr)
        if match and cmds.ls(node, long=True) == [group]:
            return int(match.group(1))
    return None


def levels(group):
    """
    [(index, slot)] for every level of a lodGroup, ordered by index.

    index is the output[] / displayLevel[] index the slot is wired to - what
    the lodGroup actually switches on - falling back to outliner position for
    a child that is not wired.
    """
    found = []
    for position, child in enumerate(_children(group)):
        index = _output_index(group, child)
        found.append((position if index is None else index, child))
    return sorted(found)


# ============================================================================
# BUILD
# ============================================================================

def build_lod_groups(nodes=None, log=None):
    """
    Put LOD-named transforms into one lodGroup per asset name.

    nodes defaults to the selected transforms. log(message, level) receives the
    report; level is info / ok / warn / error. Returns the lodGroups created or
    updated (long names) and leaves them selected. The whole build is one undo
    step.
    """
    log = log or _default_log
    if nodes is None:
        nodes = cmds.ls(selection=True, long=True, transforms=True) or []

    by_base, skipped = _sort_by_base(nodes)
    if skipped:
        log("Skipped, no _LOD<n> in the name: {}".format(
            ", ".join(short_name(node) for node in skipped)), "warn")
    if not by_base:
        log("Nothing to group. Select meshes named like Asset_LOD0, Asset_LOD1, ...", "warn")
        return []

    # Everything selected is protected from the "replace old content" step,
    # whichever level or asset it belongs to, so a mesh that currently sits in
    # the wrong slot gets moved rather than deleted.
    protected = set(uuid for by_level in by_base.values()
                    for uuids in by_level.values() for uuid in uuids)

    built = []
    cmds.undoInfo(openChunk=True, chunkName="gs_lod_build")
    try:
        for base, by_level in by_base.items():
            group = _build_one(base, by_level, protected, log)
            if group:
                built.append(uuid_of(group))
    finally:
        cmds.undoInfo(closeChunk=True)

    # Resolve at the end: building a later group can move an earlier one
    # (an asset nested inside another asset's mesh).
    groups = [path for path in (path_of(uuid) for uuid in built) if path]
    if groups:
        cmds.select(groups, replace=True)
    return groups


def _sort_by_base(nodes):
    """({base: {level: [uuid]}} in selection order, [skipped paths])."""
    by_base = collections.OrderedDict()
    skipped = []
    for node in nodes:
        parsed = parse_lod_name(node)
        if not parsed or cmds.nodeType(node) == "lodGroup":
            skipped.append(node)
            continue
        base, level = parsed
        by_base.setdefault(base, {}).setdefault(level, []).append(uuid_of(node))
    return by_base, skipped


def _build_one(base, by_level, protected, log):
    existing = find_lod_groups(base)
    if len(existing) > 1:
        log("{}: {} LOD groups already have this name - rename all but one, then run "
            "again.".format(base, len(existing)), "error")
        return None

    if existing:
        group = existing[0]
        old_levels = levels(group)
        old_count = old_levels[-1][0] + 1 if old_levels else 0
        verb = "Updated"
        if not cmds.listConnections(group + ".cameraMatrix", source=True, destination=False):
            _connect_camera(group, cmds.getAttr(group + ".useScreenHeightPercentage"), log)
    else:
        incoming = [path_of(uuid) for uuids in by_level.values() for uuid in uuids]
        group = _create_group(base, _common_parent(incoming), log)
        old_count = 0
        verb = "Created"

    slots = _ensure_slots(group, max(by_level))
    _seed_thresholds(group, old_count, len(slots))

    log("{} {} ({} levels)".format(verb, short_name(group), len(slots)), "ok")
    for level in sorted(by_level):
        _fill_slot(slots[level], by_level[level], protected, log)

    empty = [short_name(slot) for slot in slots if not _children(slot)]
    if empty:
        log("    Empty: {}".format(", ".join(empty)), "warn")
    return group


def _common_parent(paths):
    """
    Where a new lodGroup goes: under the parent its meshes share, so the scene
    hierarchy is kept - but at world when they don't share one, or when that
    parent is a lodGroup or one of its LOD_<n> slots.
    """
    parents = set(_parent(path) for path in paths)
    if len(parents) != 1:
        return None
    parent = parents.pop()
    if parent is None or cmds.nodeType(parent) == "lodGroup":
        return None
    grandparent = _parent(parent)
    if grandparent and cmds.nodeType(grandparent) == "lodGroup":
        return None
    return parent


def _create_group(base, parent, log):
    kwargs = {"name": base, "skipSelect": True}
    if parent:
        kwargs["parent"] = parent
    group = cmds.ls(cmds.createNode("lodGroup", **kwargs), long=True)[0]
    if short_name(group) != base:
        log("{}: that name is already taken here, so Maya named the LOD group "
            "'{}'.".format(base, short_name(group)), "warn")

    use_percentage = _threshold_type() == 1
    cmds.setAttr(group + ".useScreenHeightPercentage", use_percentage)
    # Maya turns this on by default so parenting the group stays correct.
    cmds.setAttr(group + ".worldSpace", True)
    _connect_camera(group, use_percentage, log)
    return group


def _threshold_type():
    """Maya's own LOD Group option: 0 = distance, 1 = screen height % (factory)."""
    if cmds.optionVar(exists="lodThresholdType"):
        return cmds.optionVar(q="lodThresholdType")
    return 1


def _view_camera():
    """Shape of the focused viewport's camera, else persp; perspective only."""
    candidates = []
    panel = cmds.getPanel(withFocus=True)
    if panel and cmds.getPanel(typeOf=panel) == "modelPanel":
        candidates.append(cmds.modelPanel(panel, q=True, camera=True))
    candidates.append("persp")

    for camera in candidates:
        if not camera or not cmds.objExists(camera):
            continue
        if cmds.objectType(camera, isAType="camera"):
            shapes = cmds.ls(camera, long=True)
        else:
            shapes = cmds.listRelatives(camera, shapes=True, type="camera", fullPath=True) or []
        if shapes and not cmds.getAttr(shapes[0] + ".orthographic"):
            return shapes[0]
    return None


def _connect_camera(group, use_percentage, log):
    # Maya's setup wires the current camera the same way; an orthographic view
    # falls back to persp here instead of building Maya's ortho matrix network.
    camera = _view_camera()
    if not camera:
        log("{}: no perspective camera found, LOD group left without one.".format(
            short_name(group)), "warn")
        return
    cmds.connectAttr(camera + ".worldMatrix[0]", group + ".cameraMatrix", force=True)
    if use_percentage:
        cmds.connectAttr(camera + ".focalLength", group + ".focalLength", force=True)


def _ensure_slots(group, highest_level):
    """
    LOD_0..LOD_<n> under the group as a list indexed by level, n being the
    larger of highest_level and the group's existing top level. Missing levels
    are created empty, so LOD_3 always holds the _LOD3 mesh even when there
    is no _LOD2. Every level is wired, ordered, and set to Show.
    """
    by_index = {}
    for index, slot in levels(group):
        by_index.setdefault(index, slot)

    count = max(highest_level, max(by_index) if by_index else -1) + 1
    for index in range(count):
        if index not in by_index:
            slot = cmds.createNode("transform", name="{}{}".format(SLOT_PREFIX, index),
                                   parent=group, skipSelect=True)
            by_index[index] = cmds.ls(slot, long=True)[0]
    slots = [by_index[index] for index in range(count)]

    # Outliner order follows level order, any stray non-level children last.
    for slot in reversed(slots):
        cmds.reorder(slot, front=True)

    # Wire explicitly rather than trusting what parenting connected, so a
    # level added to an existing group cannot end up on the wrong index.
    for index, slot in enumerate(slots):
        source = "{}.output[{}]".format(group, index)
        target = slot + ".lodVisibility"
        if not cmds.isConnected(source, target):
            cmds.connectAttr(source, target, force=True)
        cmds.setAttr("{}.displayLevel[{}]".format(group, index), SHOW)
    return slots


def _seed_thresholds(group, old_count, count):
    """
    Thresholds for the levels added since old_count, seeded like Maya's own
    setup (lodUtils.mel). A group of n levels has n-1 thresholds; existing ones
    are left as the artist set them.
    """
    first = max(0, old_count - 1)
    if first >= count - 1:
        return

    if cmds.getAttr(group + ".useScreenHeightPercentage"):
        # 64% for the first switch, halving for each one after.
        attr = group + ".percentageThreshold"
        for index in range(first, count - 1):
            if index == 0:
                value = _FIRST_PERCENTAGE
            else:
                value = cmds.getAttr("{}[{}]".format(attr, index - 1)) * 0.5
            cmds.setAttr("{}[{}]".format(attr, index), value)
        return

    # Distance: the first threshold scaled off the current camera distance so
    # the middle level shows now, then (index + 1)^2 times that.
    attr = group + ".threshold"
    if first == 0:
        distance = cmds.getAttr(group + ".distance")
        highest = count - 1
        if highest == 1:
            nearest = 2 * distance
        else:
            m = (highest - 2) // 2
            nearest = distance / (m * m + 3 * m + 2.5)
        cmds.setAttr(attr + "[0]", nearest)
        first = 1
    nearest = cmds.getAttr(attr + "[0]")
    for index in range(first, count - 1):
        cmds.setAttr("{}[{}]".format(attr, index), (index + 1) ** 2 * nearest)


def _fill_slot(slot, uuids, protected, log):
    """Replace a level's content with the incoming meshes."""
    label = short_name(slot)

    # Two selected meshes with one name would collide inside the slot, and
    # Maya would rename the second by bumping its number - Tree_LOD2 into
    # Tree_LOD3. Keep the first.
    incoming, names = [], set()
    for path in (path_of(uuid) for uuid in uuids):
        name = short_name(path)
        if name in names:
            log("    {}: more than one '{}' selected, kept the first.".format(label, name), "warn")
            continue
        names.add(name)
        incoming.append(path)

    # Old content goes first, so a new Tree_LOD2 never lands next to an old
    # Tree_LOD2 and gets renamed. Selected meshes, and anything holding one,
    # are never deleted.
    selected = [path for path in (path_of(uuid) for uuid in protected) if path]
    replaced = [child for child in _children(slot)
                if uuid_of(child) not in protected
                and not any(path.startswith(child + "|") for path in selected)]
    if replaced:
        try:
            cmds.delete(replaced)
        except RuntimeError as error:
            log("    {}: could not remove the old content ({}), level left as it "
                "was.".format(label, error), "error")
            return

    for path in incoming:
        if _parent(path) == slot:
            continue
        try:
            cmds.parent(path, slot)
        except RuntimeError as error:
            log("    {}: could not move {} in ({}).".format(label, short_name(path), error), "error")

    message = "    {}: {}".format(label, ", ".join(short_name(path) for path in incoming))
    if replaced:
        message += "  (replaced {})".format(", ".join(short_name(path) for path in replaced))
    log(message)
