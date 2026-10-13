"""
gs_cleanup.core - no UI, all the actual work.

Duplicate materials
-------------------
Duplicates are found by name. Each material name is reduced to a *base* by
dropping its namespace, any "pasted__" prefixes and any trailing number suffix -
the forms left behind by copy / paste between scenes (material01 ->
pasted__material01 -> pasted__pasted__material01), by Blender (Material.001;
Maya names cannot hold a dot, so it arrives as Material_001 or
MaterialFBXASC046001), by Maya renaming a clash on import (Material1) and by
duplicating (Material_01 -> Material_02). Materials sharing a base,
case-insensitively, form a group.

Name matching on its own over-reports: a deliberately numbered series (Tire_01,
Tire_02) groups too. So each group also says whether it is *obvious* - one of
its members is literally the base name once any "pasted__" is dropped
(materialA next to materialA_001 or pasted__materialA). The UI pre-ticks only
those and leaves the rest for the artist to judge.

A pasted copy is the surest sign of all, so it is not left buried in a series
group. When a group has no member named the base but does hold pasted copies,
each original and its copies become a group of their own (Tire_01 with
pasted__Tire_01), and the rest of the series is set aside until the next Find -
merging a whole group would otherwise fold Tire_02 into Tire_01 as well.

Merging a group keeps one material and, for every other member:
  * moves everything assigned to it - whole objects, instances and per-face
    assignments - onto the kept material's shading group (sets -forceElement),
  * deletes it, its now-empty shading groups and their materialInfo nodes,
  * deletes the texture / utility nodes upstream of it that no longer feed
    anything (file, place2dTexture, bump2d ...). A node still used elsewhere,
    another material, a DAG object or anything default, referenced or locked is
    never deleted.

Default, referenced and locked materials can be kept but are never removed. The
whole merge, every group in it, is one undo chunk.
"""

import re
from collections import namedtuple

import maya.cmds as cmds

# Trailing number suffix plus any separators in front of it: _001, 1, _01_2,
# and FBXASC046001 (an FBX-escaped ".001").
_SUFFIX = re.compile(r"(?:(?:[._]|FBXASC046)*\d+)+$")

# Prefix Maya's paste gives every pasted node (renamingPrefix "pasted_" plus the
# joining underscore), once per paste: pasted__pasted__material01.
_PASTED = re.compile(r"^(?:pasted_+)+")

# Downstream nodes that do not count as "using" a texture node: Maya's own
# bookkeeping lists and the Hypershade / node editor layout.
_BOOKKEEPING_TYPES = frozenset((
    "defaultTextureList", "defaultRenderUtilityList", "defaultShaderList",
    "materialInfo", "nodeGraphEditorInfo", "hyperLayout", "hyperView",
))

# name, node type, number of objects using it, and why it cannot be deleted
# ("" when it can).
MaterialInfo = namedtuple("MaterialInfo", "name type objects protected")

# base name for display, members (MaterialInfo, keeper suggestion first),
# keeper (suggested material to keep), obvious (a member is named the base).
MaterialGroup = namedtuple("MaterialGroup", "base members keeper obvious")

# removed: deleted materials; skipped: (material, reason) pairs left alone;
# reassigned: objects moved to a kept material; cleaned: texture nodes deleted.
MergeResult = namedtuple("MergeResult", "removed skipped reassigned cleaned")


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def short_name(node):
    """`node` without its namespace."""
    return node.rsplit(":", 1)[-1]


def copy_name(material):
    """`material` without its namespace or "pasted__" prefixes - the name it was
    copied from."""
    leaf = short_name(material)
    return _PASTED.sub("", leaf) or leaf


def paste_count(material):
    """How many times `material` has been pasted (pasted__pasted__x -> 2)."""
    match = _PASTED.match(short_name(material))
    return match.group().count("pasted") if match else 0


def base_name(material):
    """`material` without its namespace, "pasted__" prefixes or trailing number
    suffix."""
    leaf = copy_name(material)
    return _SUFFIX.sub("", leaf) or leaf


def _default_nodes():
    return set(cmds.ls(defaultNodes=True) or [])


def protected_reason(node, default_nodes=None):
    """Why `node` must not be deleted, or "" if it may be."""
    if default_nodes is None:
        default_nodes = _default_nodes()
    if node in default_nodes:
        return "default node"
    if cmds.referenceQuery(node, isNodeReferenced=True):
        return "referenced"
    if cmds.lockNode(node, query=True, lock=True)[0]:
        return "locked"
    return ""


def distinct_objects(members):
    """Distinct objects behind set members ("pCube1.f[0:3]" -> "pCube1")."""
    return set(member.split(".")[0] for member in members)


# ---------------------------------------------------------------------------
# assignments
# ---------------------------------------------------------------------------
def shading_groups(material):
    """Shading groups that `material` is the surface shader of.

    Only surfaceShader counts as an assignment. A material plugged into some
    other slot (displacement, volume, a renderer override) does not own that
    shading group's objects, so they must not be moved on its behalf.
    """
    plugs = cmds.listConnections(material, source=False, destination=True,
                                 type="shadingEngine", plugs=True) or []
    groups = []
    for plug in plugs:
        node, attr = plug.split(".", 1)
        if attr == "surfaceShader" and node not in groups:
            groups.append(node)
    return groups


def assigned_members(material):
    """Everything assigned to `material`: objects, instances and face sets."""
    members = []
    for group in shading_groups(material):
        members.extend(cmds.sets(group, query=True) or [])
    return members


def _target_shading_group(material):
    """The shading group to assign `material` through, created if it has none."""
    existing = shading_groups(material)
    if existing:
        return existing[0]
    if not cmds.attributeQuery("outColor", node=material, exists=True):
        raise RuntimeError("{} has no outColor to drive a shading group".format(material))
    group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True,
                      name=short_name(material) + "SG")
    cmds.connectAttr(material + ".outColor", group + ".surfaceShader", force=True)
    return group


# ---------------------------------------------------------------------------
# finding duplicates
# ---------------------------------------------------------------------------
def _material_group(names, key, default_nodes):
    """MaterialGroup of `names`, whose members named `key` (case-insensitively,
    once namespace and "pasted__" are dropped) make it obvious."""
    roots = set(name for name in names if copy_name(name).lower() == key)
    members = [MaterialInfo(name, cmds.nodeType(name),
                            len(distinct_objects(assigned_members(name))),
                            protected_reason(name, default_nodes))
               for name in names]
    members.sort(key=lambda info: (not info.protected, info.name not in roots,
                                   paste_count(info.name), -info.objects,
                                   ":" in info.name, len(info.name), info.name))
    shortest = min(roots or names, key=len)
    return MaterialGroup(
        base=copy_name(shortest) if roots else base_name(shortest),
        members=members,
        keeper=members[0].name,
        obvious=bool(roots))


def find_duplicate_materials():
    """Group the scene's materials by base name; groups of two or more only.

    A group with no member named the base that holds pasted copies is replaced
    by one group per original and its copies (see the module docstring).

    Returns a list of MaterialGroup sorted by base name. The suggested keeper is
    a protected member if there is one (it cannot be removed anyway), then the
    member named the base, then the least pasted, then the one used by the most
    objects.
    """
    default_nodes = _default_nodes()
    by_base = {}
    for material in cmds.ls(materials=True) or []:
        if cmds.nodeType(material) == "shadingEngine":
            continue
        by_base.setdefault(base_name(material).lower(), []).append(material)

    groups = []
    for key in sorted(by_base):
        names = by_base[key]
        if len(names) < 2:
            continue
        if any(copy_name(name).lower() == key for name in names):
            groups.append(_material_group(names, key, default_nodes))
            continue
        by_copy = {}
        for name in names:
            by_copy.setdefault(copy_name(name).lower(), []).append(name)
        copies = [copy_key for copy_key in sorted(by_copy) if len(by_copy[copy_key]) > 1]
        if copies:
            groups.extend(_material_group(by_copy[copy_key], copy_key, default_nodes)
                          for copy_key in copies)
        else:
            groups.append(_material_group(names, key, default_nodes))
    return groups


# ---------------------------------------------------------------------------
# merging
# ---------------------------------------------------------------------------
def _is_texture_node(node):
    """True for texture / utility nodes - the only kind the orphan sweep deletes.

    DAG objects are excluded outright (a locator driving a ramp must survive),
    except place3dTexture, which is part of a 3D texture's network.
    """
    node_type = cmds.nodeType(node)
    if node_type == "place3dTexture":
        return True
    if cmds.objectType(node, isAType="dagNode"):
        return False
    classification = " ".join(cmds.getClassification(node_type) or [])
    return "texture" in classification or "utility" in classification


def _texture_network(material):
    """Texture / utility nodes upstream of `material`."""
    history = cmds.listHistory(material) or []
    return [node for node in history if node != material and _is_texture_node(node)]


def _has_consumers(node):
    downstream = cmds.listConnections(node, source=False, destination=True,
                                      skipConversionNodes=True) or []
    return any(other != node and cmds.nodeType(other) not in _BOOKKEEPING_TYPES
               for other in downstream)


def _delete_orphans(candidates, default_nodes):
    """Delete the `candidates` that feed nothing any more.

    Repeats until nothing changes, so a place2dTexture goes once the file node
    it fed has gone.
    """
    pending = [node for node in candidates
               if cmds.objExists(node) and not protected_reason(node, default_nodes)]
    deleted = []
    progress = True
    while progress:
        progress = False
        for node in list(pending):
            if not cmds.objExists(node):
                pending.remove(node)
            elif not _has_consumers(node):
                cmds.delete(node)
                pending.remove(node)
                deleted.append(node)
                progress = True
    return deleted


def _delete_material(material, keep, default_nodes):
    """Delete `material` and its emptied shading groups (+ their materialInfo)."""
    doomed = []
    for group in shading_groups(material):
        if (group in keep or protected_reason(group, default_nodes)
                or cmds.sets(group, query=True)):
            continue
        doomed.append(group)
        doomed.extend(cmds.listConnections(group, type="materialInfo") or [])
    doomed.append(material)
    # One at a time: deleting a shading group can take its materialInfo with it.
    for node in doomed:
        if cmds.objExists(node):
            cmds.delete(node)


def merge_materials(merges):
    """Fold duplicate materials into the material kept for each group.

    merges -- list of (keeper, [duplicates]) pairs

    A duplicate that is protected, gone, or fails is recorded in `skipped` and
    the rest carry on, so one bad material does not abort a big merge. Returns
    a MergeResult.
    """
    default_nodes = _default_nodes()
    removed, skipped, cleaned = [], [], []
    reassigned = 0
    network = set()

    cmds.undoInfo(openChunk=True, chunkName="gs_cleanupMergeMaterials")
    try:
        for keeper, duplicates in merges:
            if not cmds.objExists(keeper):
                skipped.extend((duplicate, "kept material {} no longer exists".format(keeper))
                               for duplicate in duplicates)
                continue
            keep = shading_groups(keeper)
            for duplicate in duplicates:
                if duplicate == keeper:
                    continue
                if not cmds.objExists(duplicate):
                    skipped.append((duplicate, "no longer exists"))
                    continue
                reason = protected_reason(duplicate, default_nodes)
                if reason:
                    skipped.append((duplicate, reason + " - cannot be removed"))
                    continue
                try:
                    members = assigned_members(duplicate)
                    if members:
                        target = _target_shading_group(keeper)
                        if target not in keep:
                            keep.append(target)
                        cmds.sets(members, edit=True, forceElement=target)
                        reassigned += len(distinct_objects(members))
                    network.update(_texture_network(duplicate))
                    _delete_material(duplicate, keep, default_nodes)
                    removed.append(duplicate)
                except Exception as exc:
                    skipped.append((duplicate, str(exc)))
        cleaned = _delete_orphans(sorted(network), default_nodes)
    finally:
        cmds.undoInfo(closeChunk=True)

    return MergeResult(removed, skipped, reassigned, cleaned)
