"""
rename_building_textures.py  (v6)
---------------------------------
Maya, cmds only.

Pass 0 - materials
    metalPaintedClean03_02_mat  ->  metalPaintedClean03_mat
    ...but only when no other material shares the prefix before the first
    underscore. If metalPaintedClean03_01_mat also exists, the index is doing
    real work and both names are left alone. Removal only: a material that has
    no index (brick03_mat) is never given one.

Pass 1 - deduplicate file nodes by texture path
    One `file` node per unique image, shared by every material that uses it.
    Redundant nodes and their orphaned place2dTexture nodes are deleted.

Pass 2 - rename keepers to the image name
    .../sharedTextures/snow_specular.png  ->  snow_specular

Pass 3 - colour space
    Any image whose name contains a RAW_KEYWORDS entry ("normal") is set to the
    colour config's raw space, with ignoreColorSpaceFileRules so Maya's rules
    don't revert it on reload.

DRY_RUN is False. The whole run is one undo chunk, but save first anyway.
"""

import os
import maya.cmds as cmds


# ---------------------------------------------------------------- config ----

SHADER_FILE = "buildingShader.ogsfx"   # None = every GLSLShader in the scene
DRY_RUN = False

# ---- materials ----
RENAME_MATERIALS = True
MATERIAL_SUFFIX = "mat"          # trailing token that marks a material name
REQUIRE_NUMERIC_INDEX = True     # only strip middle tokens that are pure digits
PREFIX_SCOPE_ALL_MATERIALS = True  # compare prefixes against every material,
                                   # not just the buildingShader ones
RENAME_SHADING_GROUPS = False    # also rename <old>SG -> <new>SG

# ---- textures ----
DEDUPLICATE = True
RENAME = True
STRIP_EXTENSION = True

PARAM_BLACKLIST = ["envMap"]
PATH_WHITELIST = []              # e.g. ["bin/data"] to ignore off-tree textures

REPORT_ORPHAN_FILE_NODES = True

# ---- colour space ----
SET_RAW_COLORSPACE = True
RAW_KEYWORDS = ["normal"]
RAW_MATCH_FILENAME_ONLY = True
RAW_COLORSPACE = "Raw"
IGNORE_COLORSPACE_FILE_RULES = True

COMPARE_ATTRS = ["colorSpace", "alphaIsLuminance", "invert", "filterType",
                 "colorGain", "colorOffset", "alphaGain", "alphaOffset",
                 "uvTilingMode"]
COMPARE_PLACEMENT = ["repeatU", "repeatV", "offsetU", "offsetV", "rotateUV",
                     "wrapU", "wrapV", "mirrorU", "mirrorV"]


# --------------------------------------------------------------- helpers ----

def find_shaders(effect_filter):
    nodes = []
    for node_type in ("GLSLShader", "glslShader"):
        try:
            nodes.extend(cmds.ls(type=node_type) or [])
        except RuntimeError:
            pass
    seen, unique = set(), []
    for n in nodes:
        if n not in seen:
            seen.add(n)
            unique.append(n)
    if not effect_filter:
        return unique

    needle = effect_filter.replace("\\", "/").lower()
    keep = []
    for n in unique:
        fx = ""
        if cmds.attributeQuery("shader", node=n, exists=True):
            fx = cmds.getAttr(n + ".shader") or ""
        if needle in fx.replace("\\", "/").lower():
            keep.append(n)
    return keep


def split_ns(name):
    if ":" in name:
        ns, leaf = name.rsplit(":", 1)
        return ns, leaf
    return "", name


def name_prefix(name):
    return split_ns(name)[1].split("_")[0]


# ------------------------------------------------- pass 0: material names ---

def rename_materials(shaders):
    """Strip a redundant index token from material names. Never adds one.

    Returns (updated shader list, report lines, counters dict).
    """
    lines = ["-- materials " + "-" * 58]
    counts = {"renamed": 0, "kept": 0, "clashed": 0, "failed": 0}

    if PREFIX_SCOPE_ALL_MATERIALS:
        try:
            pool = cmds.ls(materials=True) or list(shaders)
        except RuntimeError:
            pool = list(shaders)
    else:
        pool = list(shaders)

    by_prefix = {}
    for m in pool:
        by_prefix.setdefault(name_prefix(m), []).append(m)

    updated = []
    for shader in shaders:
        ns, leaf = split_ns(shader)
        parts = leaf.split("_")

        # needs at least prefix + index + suffix to have anything to remove
        if len(parts) < 3 or parts[-1] != MATERIAL_SUFFIX:
            updated.append(shader)
            counts["kept"] += 1
            continue

        middle = parts[1:-1]
        if REQUIRE_NUMERIC_INDEX and not all(p.isdigit() for p in middle):
            updated.append(shader)
            counts["kept"] += 1
            lines.append("   KEEP   %-34s middle %r is not an index"
                         % (shader, "_".join(middle)))
            continue

        prefix = parts[0]
        siblings = [m for m in by_prefix.get(prefix, []) if m != shader]
        if siblings:
            updated.append(shader)
            counts["kept"] += 1
            lines.append("   KEEP   %-34s shares prefix with %s"
                         % (shader, ", ".join(siblings[:3])
                            + ("..." if len(siblings) > 3 else "")))
            continue

        target_leaf = "%s_%s" % (prefix, MATERIAL_SUFFIX)
        target = "%s:%s" % (ns, target_leaf) if ns else target_leaf

        if cmds.objExists(target):
            updated.append(shader)
            counts["clashed"] += 1
            lines.append("   CLASH  %-34s %s already exists, left alone"
                         % (shader, target))
            continue

        if DRY_RUN:
            counts["renamed"] += 1
            updated.append(shader)
            lines.append("   RENAME %-34s -> %s" % (shader, target))
            continue

        try:
            sg = None
            if RENAME_SHADING_GROUPS:
                sgs = cmds.listConnections(shader, type="shadingEngine") or []
                sg = sgs[0] if sgs else None

            new = cmds.rename(shader, target_leaf)
            counts["renamed"] += 1
            lines.append("   RENAME %-34s -> %s" % (shader, new))
            updated.append(new)

            if sg and cmds.objExists(sg):
                sg_ns, sg_leaf = split_ns(sg)
                if sg_leaf.startswith(leaf):
                    sg_target = sg_leaf.replace(leaf, target_leaf, 1)
                    if not cmds.objExists(sg_target):
                        try:
                            new_sg = cmds.rename(sg, sg_target)
                            lines.append("   RENAME %-34s -> %s"
                                         % (sg, new_sg))
                        except Exception as exc:
                            lines.append("   FAIL   %s (SG): %s" % (sg, exc))
        except Exception as exc:
            counts["failed"] += 1
            updated.append(shader)
            lines.append("   FAIL   %s: %s" % (shader, exc))

    return updated, lines, counts


# ------------------------------------------------------ texture helpers -----

def texture_links(shader):
    """[(param, fileNode, path), ...] for every file node feeding this shader."""
    links = []
    conns = cmds.listConnections(shader, connections=True, plugs=True,
                                 source=True, destination=False) or []
    for i in range(0, len(conns) - 1, 2):
        dst_plug, src_plug = conns[i], conns[i + 1]
        node = src_plug.split(".")[0]
        if not cmds.attributeQuery("fileTextureName", node=node, exists=True):
            continue
        param = dst_plug.split(".", 1)[-1].split("[")[0]
        if param in PARAM_BLACKLIST:
            continue
        path = cmds.getAttr(node + ".fileTextureName") or ""
        if PATH_WHITELIST:
            low = path.replace("\\", "/").lower()
            if not any(w.lower() in low for w in PATH_WHITELIST):
                continue
        links.append((param, node, path))
    return links


def norm_path(path):
    if not path:
        return ""
    p = path.replace("\\", "/").strip()
    while "//" in p[2:]:
        p = p[:2] + p[2:].replace("//", "/")
    return p.rstrip("/").lower()


def image_name(path):
    if not path:
        return None
    base = os.path.basename(path.replace("\\", "/").rstrip("/"))
    if not base:
        return None
    if STRIP_EXTENSION:
        stem, ext = os.path.splitext(base)
        if ext:
            base = stem
    return base


def placement_of(node):
    p = cmds.listConnections(node, source=True, destination=False,
                             type="place2dTexture") or []
    return p[0] if p else None


def settings_diff(dupe, keeper):
    diffs = []
    for attr in COMPARE_ATTRS:
        pa, pb = "%s.%s" % (dupe, attr), "%s.%s" % (keeper, attr)
        if not (cmds.objExists(pa) and cmds.objExists(pb)):
            continue
        try:
            if cmds.getAttr(pa) != cmds.getAttr(pb):
                diffs.append(attr)
        except RuntimeError:
            pass

    pa, pb = placement_of(dupe), placement_of(keeper)
    if pa and pb:
        for attr in COMPARE_PLACEMENT:
            qa, qb = "%s.%s" % (pa, attr), "%s.%s" % (pb, attr)
            if not (cmds.objExists(qa) and cmds.objExists(qb)):
                continue
            try:
                if cmds.getAttr(qa) != cmds.getAttr(qb):
                    diffs.append("place2d." + attr)
            except RuntimeError:
                pass
    elif bool(pa) != bool(pb):
        diffs.append("place2dTexture presence")
    return diffs


def merge_into(duplicate, keeper):
    conns = cmds.listConnections(duplicate, connections=True, plugs=True,
                                 source=False, destination=True) or []
    for i in range(0, len(conns) - 1, 2):
        src, dst = conns[i], conns[i + 1]
        if cmds.nodeType(dst.split(".")[0]) in ("defaultTextureList",
                                                "defaultRenderUtilityList",
                                                "nodeGraphEditorInfo",
                                                "hyperLayout"):
            continue
        attr = src.split(".", 1)[-1]
        try:
            cmds.disconnectAttr(src, dst)
        except RuntimeError:
            pass
        cmds.connectAttr("%s.%s" % (keeper, attr), dst, force=True)

    placement = placement_of(duplicate)
    cmds.delete(duplicate)
    if placement and cmds.objExists(placement):
        if not (cmds.listConnections(placement, source=False,
                                     destination=True) or []):
            cmds.delete(placement)


def orphan_file_nodes():
    ignore = ("defaultTextureList", "defaultRenderUtilityList",
              "nodeGraphEditorInfo", "hyperLayout", "shaderGlow")
    orphans = []
    for f in cmds.ls(type="file") or []:
        outs = cmds.listConnections(f, source=False, destination=True) or []
        if not [o for o in outs if cmds.nodeType(o) not in ignore]:
            orphans.append(f)
    return orphans


# --------------------------------------------------------- colour space -----

def resolve_raw_space(preferred):
    try:
        names = cmds.colorManagementPrefs(query=True, inputSpaceNames=True) or []
    except Exception:
        return preferred
    if not names:
        return preferred
    if preferred in names:
        return preferred
    for n in names:
        if n.lower() == preferred.lower():
            return n
    for n in names:
        if "raw" in n.lower():
            return n
    return None


def wants_raw(path):
    target = os.path.basename(path.replace("\\", "/")) \
        if RAW_MATCH_FILENAME_ONLY else path
    return any(k.lower() in target.lower() for k in RAW_KEYWORDS)


def set_raw(node, space):
    flag = node + ".ignoreColorSpaceFileRules"
    if IGNORE_COLORSPACE_FILE_RULES and cmds.objExists(flag):
        if not cmds.getAttr(flag):
            cmds.setAttr(flag, True)
    cmds.setAttr(node + ".colorSpace", space, type="string")


# ------------------------------------------------------------------ run -----

def run():
    shaders = find_shaders(SHADER_FILE)
    if not shaders:
        cmds.warning("No GLSLShader matching %r found." % (SHADER_FILE,))
        return

    merged = renamed = clashed = kept = failed = warns = 0
    raw_set = raw_ok = 0
    lines = []
    mat_counts = {"renamed": 0, "kept": 0, "clashed": 0, "failed": 0}

    cmds.undoInfo(openChunk=True, chunkName="renameBuildingTextures")
    try:
        # ---- pass 0: material names ----------------------------------------
        if RENAME_MATERIALS:
            shaders, mat_lines, mat_counts = rename_materials(shaders)
            lines.extend(mat_lines)

        # ---- gather --------------------------------------------------------
        groups, order = {}, []
        for shader in shaders:
            for param, node, path in texture_links(shader):
                key = norm_path(path)
                if not key:
                    continue
                if key not in groups:
                    groups[key] = {"path": path, "nodes": [], "users": []}
                    order.append(key)
                g = groups[key]
                if node not in g["nodes"]:
                    g["nodes"].append(node)
                g["users"].append("%s.%s" % (shader, param))

        # ---- pass 1: merge duplicates by path ------------------------------
        for key in order:
            g = groups[key]
            desired = image_name(g["path"])
            nodes = [n for n in g["nodes"] if cmds.objExists(n)]
            if not nodes:
                continue

            keeper = None
            for n in nodes:
                if n == desired:
                    keeper = n
                    break
            if keeper is None:
                keeper = nodes[0]
            g["keeper"] = keeper

            if not DEDUPLICATE or len(nodes) < 2:
                continue

            lines.append("")
            lines.append("-- %s   (%d nodes, %d slots)"
                         % (desired, len(nodes), len(g["users"])))
            for n in nodes:
                if n == keeper:
                    continue
                diffs = settings_diff(n, keeper)
                if diffs:
                    warns += 1
                    lines.append("   WARN   %s differs from keeper: %s"
                                 % (n, ", ".join(diffs)))
                if DRY_RUN:
                    merged += 1
                    lines.append("   MERGE  %s -> %s" % (n, keeper))
                    continue
                try:
                    merge_into(n, keeper)
                    merged += 1
                    lines.append("   MERGE  %s -> %s" % (n, keeper))
                except Exception as exc:
                    failed += 1
                    lines.append("   FAIL   %s: %s" % (n, exc))

        # ---- pass 2: rename keepers ----------------------------------------
        if RENAME:
            lines.append("")
            lines.append("-- texture renames " + "-" * 52)
            for key in order:
                g = groups[key]
                keeper = g.get("keeper")
                if not keeper or not cmds.objExists(keeper):
                    continue
                desired = image_name(g["path"])
                if not desired:
                    failed += 1
                    lines.append("   FAIL   %s has no image name" % keeper)
                    continue
                if keeper == desired:
                    kept += 1
                    continue

                if DRY_RUN:
                    if cmds.objExists(desired):
                        clashed += 1
                        lines.append("   CLASH  %s -> %s<n>  (name in use)"
                                     % (keeper, desired))
                    else:
                        renamed += 1
                        lines.append("   RENAME %s -> %s" % (keeper, desired))
                    continue

                try:
                    new = cmds.rename(keeper, desired)
                    g["keeper"] = new
                    if new == desired:
                        renamed += 1
                        lines.append("   RENAME %s -> %s" % (keeper, new))
                    else:
                        clashed += 1
                        lines.append("   CLASH  %s -> %s  (wanted %s; another "
                                     "node holds it)" % (keeper, new, desired))
                except Exception as exc:
                    failed += 1
                    lines.append("   FAIL   %s: %s" % (keeper, exc))

        # ---- pass 3: colour space ------------------------------------------
        if SET_RAW_COLORSPACE:
            space = resolve_raw_space(RAW_COLORSPACE)
            lines.append("")
            lines.append("-- colour space " + "-" * 55)
            if not space:
                lines.append("   SKIP   no space matching %r in the active "
                             "colour config" % RAW_COLORSPACE)
            else:
                if space != RAW_COLORSPACE:
                    lines.append("   note   using %r (config's raw space)"
                                 % space)
                for key in order:
                    g = groups[key]
                    keeper = g.get("keeper")
                    if not keeper or not cmds.objExists(keeper):
                        continue
                    if not wants_raw(g["path"]):
                        continue
                    try:
                        current = cmds.getAttr(keeper + ".colorSpace")
                    except RuntimeError:
                        current = None
                    if current == space:
                        raw_ok += 1
                        continue
                    if DRY_RUN:
                        raw_set += 1
                        lines.append("   RAW    %-34s %s -> %s"
                                     % (keeper, current, space))
                        continue
                    try:
                        set_raw(keeper, space)
                        raw_set += 1
                        lines.append("   RAW    %-34s %s -> %s"
                                     % (keeper, current, space))
                    except Exception as exc:
                        failed += 1
                        lines.append("   FAIL   %s colorSpace: %s"
                                     % (keeper, exc))
    finally:
        cmds.undoInfo(closeChunk=True)

    print("-" * 78)
    print("rename_building_textures v6  [%s]"
          % ("DRY RUN - nothing modified" if DRY_RUN else "APPLIED"))
    print("shaders matched: %d    unique images: %d" % (len(shaders), len(order)))
    print("\n".join(lines))
    print("-" * 78)
    print("materials  renamed: %d   left alone: %d   clashes: %d   failed: %d"
          % (mat_counts["renamed"], mat_counts["kept"],
             mat_counts["clashed"], mat_counts["failed"]))
    print("textures   merged: %d   renamed: %d   clashes: %d   already ok: %d   "
          "warnings: %d   failed: %d"
          % (merged, renamed, clashed, kept, warns, failed))
    print("colour space set to raw: %d   already raw: %d" % (raw_set, raw_ok))
    if REPORT_ORPHAN_FILE_NODES:
        orphans = orphan_file_nodes()
        print("file nodes driving nothing: %d%s"
              % (len(orphans),
                 ("   e.g. " + ", ".join(orphans[:5])) if orphans else ""))
    print("-" * 78)


if __name__ == "__main__":
    run()