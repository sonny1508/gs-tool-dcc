from __future__ import annotations

import json
import logging
import os

import maya.cmds as cmds

temp_dir = os.environ["TEMP"]
_UE_ROOT = os.path.join(temp_dir, "GSApplication", "unreal-engine")
MAT_ROOT  = os.path.join(_UE_ROOT, "mat-ins")
TEX_ROOT  = os.path.join(_UE_ROOT, "textures")

_HW3_ROOT = os.path.join(temp_dir, "GSApplication", "3dsmax", "hw3_tools")
MESH_ROOT = os.path.join(_HW3_ROOT, "mesh")
IO_ROOT   = os.path.join(_HW3_ROOT, "io")

WINDOW_ID = "HW3_Tools_Win"

_MAYA_DEFAULT_MATERIALS = {"particleCloud1", "shaderGlow1", "defaultColorMgtGlobals"}
_COLOR_ATTR_MAP = {
    "lambert": "color",
    "blinn": "color",
    "phong": "color",
    "phongE": "color",
    "anisotropic": "color",
    "standardSurface": "baseColor",
    "aiStandardSurface": "baseColor",
    "usdPreviewSurface": "diffuseColor",
}
_NORMAL_ATTR_MAP = {
    "lambert": "normalCamera",
    "blinn": "normalCamera",
    "phong": "normalCamera",
    "phongE": "normalCamera",
    "anisotropic": "normalCamera",
    "standardSurface": "normalCamera",
    "aiStandardSurface": "normalCamera",
}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff", ".exr", ".hdr", ".bmp"}
_LOG = logging.getLogger(__name__)


def _get_color_attr(material: str) -> str:
    return _COLOR_ATTR_MAP.get(cmds.nodeType(material), "color")


def _get_normal_attr(material: str) -> str | None:
    return _NORMAL_ATTR_MAP.get(cmds.nodeType(material))


def _list_scene_materials() -> list[str]:
    return [m for m in (cmds.ls(materials=True) or []) if m not in _MAYA_DEFAULT_MATERIALS]


def _find_upstream_node_by_type(start_attr: str, node_type: str) -> str | None:
    pending = list(
        cmds.listConnections(
            start_attr,
            source=True,
            destination=False,
            plugs=False,
        )
        or []
    )
    seen: set[str] = set()
    while pending:
        src = pending.pop(0)
        if src in seen:
            continue
        seen.add(src)
        if cmds.nodeType(src) == node_type:
            return src
        pending.extend(
            cmds.listConnections(
                src,
                source=True,
                destination=False,
                plugs=False,
            )
            or []
        )
    return None


def _find_connected_file_node(material: str, color_attr: str) -> str | None:
    return _find_upstream_node_by_type(f"{material}.{color_attr}", "file")


def _resolve_texture_path(ue_path: str, root: str) -> str | None:
    dot_idx = ue_path.rfind(".")
    if dot_idx != -1:
        ue_path = ue_path[:dot_idx]
    local = os.path.join(root, ue_path.lstrip("/").replace("/", os.sep))
    candidates = []
    for ext in sorted(_IMAGE_EXTS, key=str.lower):
        candidates.append(local + ext)
        upper_ext = ext.upper()
        if upper_ext != ext:
            candidates.append(local + upper_ext)
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def _load_json_materials() -> list[dict]:
    result = []
    try:
        for fname in os.listdir(MAT_ROOT):
            if fname.lower().endswith(".json"):
                fpath = os.path.join(MAT_ROOT, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    if not isinstance(data, dict):
                        _LOG.warning("Skipping material JSON %s: expected object payload", fpath)
                        continue
                    result.append(data)
                except (OSError, ValueError) as exc:
                    _LOG.warning("Skipping material JSON %s: %s", fpath, exc)
    except OSError as exc:
        _LOG.warning("Unable to list material JSON root %s: %s", MAT_ROOT, exc)
    result.sort(key=lambda row: row.get("name", "").lower())
    return result


def _load_textures() -> list[dict]:
    json_results = []
    image_results = []
    try:
        for fname in os.listdir(TEX_ROOT):
            fpath = os.path.join(TEX_ROOT, fname)
            ext = os.path.splitext(fname)[1].lower()
            if ext == ".json":
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    if not isinstance(data, dict):
                        _LOG.warning("Skipping texture JSON %s: expected object payload", fpath)
                        continue
                    resolved = _resolve_texture_path(data.get("path", ""), TEX_ROOT)
                    if resolved:
                        json_results.append(
                            {
                                "name": data.get("name", os.path.splitext(fname)[0]),
                                "path": resolved,
                            }
                        )
                    else:
                        _LOG.warning(
                            "Texture metadata %s could not be resolved for %s",
                            fpath,
                            data.get("name", os.path.splitext(fname)[0]),
                        )
                except (OSError, ValueError) as exc:
                    _LOG.warning("Skipping texture JSON %s: %s", fpath, exc)
            elif ext in _IMAGE_EXTS:
                image_results.append({"name": os.path.splitext(fname)[0], "path": fpath})
    except OSError as exc:
        _LOG.warning("Unable to list texture root %s: %s", TEX_ROOT, exc)
    results = json_results if json_results else image_results
    results.sort(key=lambda row: row["name"].lower())
    return results


def _predict_maya_rename(name: str) -> str:
    split_at = len(name)
    while split_at > 0 and name[split_at - 1].isdigit():
        split_at -= 1
    if split_at == len(name):
        return name + "1"
    prefix = name[:split_at]
    num_str = name[split_at:]
    return prefix + str(int(num_str) + 1).zfill(len(num_str))


def _find_mat_textures(mat_data: dict) -> tuple[str | None, str | None]:
    bc_path = None
    n_path = None
    textures = mat_data.get("textures", {})
    if not isinstance(textures, dict):
        _LOG.warning("Material textures payload is malformed: expected object at key 'textures'")
        return bc_path, n_path
    for tex_key, tex_info in textures.items():
        if not isinstance(tex_info, dict):
            _LOG.warning(
                "Material texture entry %s is malformed: expected object payload",
                tex_key,
            )
            continue
        if not tex_info.get("exported", False):
            continue
        tex_name = tex_info.get("name", "")
        path = _resolve_texture_path(tex_info.get("path", ""), MAT_ROOT)
        if path is None:
            _LOG.warning(
                "Exported material texture %s could not be resolved from %s",
                tex_name or "<unnamed>",
                tex_info.get("path", ""),
            )
        upper = tex_name.upper()
        if upper.endswith("_BC"):
            bc_path = path
        elif upper.endswith("_N"):
            n_path = path
    return bc_path, n_path


def _get_selected_mesh_shapes() -> list[str]:
    shapes: list[str] = []
    for obj in cmds.ls(selection=True, long=True) or []:
        if cmds.nodeType(obj) == "mesh":
            shapes.append(obj)
        else:
            children = cmds.listRelatives(
                obj,
                shapes=True,
                type="mesh",
                fullPath=True,
                noIntermediate=True,
            ) or []
            shapes.extend(children)
    return shapes


def _get_material_sg(mat: str) -> str | None:
    ignore = {"initialShadingGroup", "initialParticleSE"}
    sgs = [sg for sg in (cmds.listConnections(mat, type="shadingEngine") or []) if sg not in ignore]
    return sgs[0] if sgs else None


def _get_selected_materials_from_selection() -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for shape in _get_selected_mesh_shapes():
        sgs = cmds.listConnections(shape, type="shadingEngine") or []
        for sg in sgs:
            shaders = cmds.listConnections(
                f"{sg}.surfaceShader",
                source=True,
                destination=False,
            ) or []
            for shader in shaders:
                if shader not in seen:
                    seen.add(shader)
                    result.append(shader)
    return result


def _ensure_place2d_for_file(file_node: str) -> str:
    existing = cmds.listConnections(
        f"{file_node}.uvCoord",
        source=True,
        destination=False,
        plugs=False,
    ) or []
    for node in existing:
        if cmds.nodeType(node) == "place2dTexture":
            return node

    place = cmds.shadingNode("place2dTexture", asUtility=True, name=f"{file_node}_place2d")
    attrs = [
        "coverage",
        "translateFrame",
        "rotateFrame",
        "mirrorU",
        "mirrorV",
        "stagger",
        "wrapU",
        "wrapV",
        "repeatUV",
        "offset",
        "rotateUV",
        "noiseUV",
        "vertexUvOne",
        "vertexUvTwo",
        "vertexUvThree",
        "vertexCameraOne",
        "outUV",
        "outUvFilterSize",
    ]
    for attr in attrs:
        src = f"{place}.{attr}"
        if attr == "outUV":
            cmds.connectAttr(src, f"{file_node}.uvCoord", force=True)
        elif attr == "outUvFilterSize":
            cmds.connectAttr(src, f"{file_node}.uvFilterSize", force=True)
        else:
            cmds.connectAttr(src, f"{file_node}.{attr}", force=True)
    return place


def _apply_uv_values(place_node: str, r: float, g: float, b: float, a: float) -> None:
    cmds.setAttr(f"{place_node}.repeatU", r)
    cmds.setAttr(f"{place_node}.repeatV", g)
    cmds.setAttr(f"{place_node}.offsetU", b)
    cmds.setAttr(f"{place_node}.offsetV", 1.0 - g - a)


def _assign_uv_link(file_node: str, mesh: str, uv_set: str) -> None:
    if not mesh or not uv_set:
        return
    try:
        cmds.uvLink(texture=f"{file_node}.uvCoord", uvSet=f"{mesh}.uvSet[{uv_set}].uvSetName")
    except Exception:
        _LOG.warning(
            "Failed to assign uvLink for %s on %s using uv set %s",
            file_node,
            mesh,
            uv_set,
            exc_info=True,
        )
        raise


def _ensure_color_texture(material: str, texture_path: str) -> tuple[str, str]:
    color_attr = _get_color_attr(material)
    file_node = _find_connected_file_node(material, color_attr)
    if file_node is None:
        file_node = cmds.shadingNode(
            "file",
            asTexture=True,
            isColorManaged=True,
            name=f"{material}_bc_file",
        )
        cmds.connectAttr(f"{file_node}.outColor", f"{material}.{color_attr}", force=True)
    cmds.setAttr(f"{file_node}.fileTextureName", texture_path, type="string")
    place_node = _ensure_place2d_for_file(file_node)
    return file_node, place_node


def _ensure_normal_texture(material: str, texture_path: str) -> tuple[str | None, str | None]:
    normal_attr = _get_normal_attr(material)
    if not normal_attr or not cmds.attributeQuery(normal_attr, node=material, exists=True):
        return None, None

    bump_sources = cmds.listConnections(
        f"{material}.{normal_attr}",
        source=True,
        destination=False,
        plugs=False,
    ) or []
    bump_node = next((node for node in bump_sources if cmds.nodeType(node) == "bump2d"), None)
    file_node = None
    if bump_node:
        file_node = _find_upstream_node_by_type(f"{bump_node}.bumpValue", "file")

    if file_node is None:
        file_node = cmds.shadingNode(
            "file",
            asTexture=True,
            isColorManaged=True,
            name=f"{material}_n_file",
        )
    if bump_node is None:
        bump_node = cmds.shadingNode("bump2d", asUtility=True, name=f"{material}_n_bump")

    cmds.setAttr(f"{file_node}.fileTextureName", texture_path, type="string")
    cmds.setAttr(f"{file_node}.colorSpace", "Raw", type="string")
    cmds.setAttr(f"{bump_node}.bumpInterp", 1)
    cmds.connectAttr(f"{file_node}.outAlpha", f"{bump_node}.bumpValue", force=True)
    cmds.connectAttr(f"{bump_node}.outNormal", f"{material}.{normal_attr}", force=True)
    place_node = _ensure_place2d_for_file(file_node)
    return file_node, place_node


def _assign_material_network(
    material: str,
    bc_path: str | None,
    n_path: str | None,
    r: float,
    g: float,
    b: float,
    a: float,
    mesh: str,
    uv_set: str,
) -> None:
    if bc_path:
        bc_file, bc_place = _ensure_color_texture(material, bc_path)
        _apply_uv_values(bc_place, r, g, b, a)
        _assign_uv_link(bc_file, mesh, uv_set)
    if n_path:
        n_file, n_place = _ensure_normal_texture(material, n_path)
        if n_file and n_place:
            _apply_uv_values(n_place, r, g, b, a)
            _assign_uv_link(n_file, mesh, uv_set)


def _update_existing_material_network(
    material: str,
    texture_path: str,
    r: float,
    g: float,
    b: float,
    a: float,
    mesh: str,
    uv_set: str,
) -> None:
    file_node = _find_connected_file_node(material, _get_color_attr(material))
    if not file_node:
        raise RuntimeError("No connected file node found for update.")
    place_node = _ensure_place2d_for_file(file_node)
    cmds.setAttr(f"{file_node}.fileTextureName", texture_path, type="string")
    _apply_uv_values(place_node, r, g, b, a)
    _assign_uv_link(file_node, mesh, uv_set)


def _safe_material_reuse(pre_import_mats: set) -> int:
    current = set(cmds.ls(materials=True) or [])
    new_mats = list(current - pre_import_mats)
    reused = 0
    for imp_mat in new_mats:
        original = None
        for existing in pre_import_mats:
            name = existing
            for _ in range(10):
                name = _predict_maya_rename(name)
                if name == imp_mat:
                    original = existing
                    break
            if original:
                break
        if not original:
            continue
        imp_sg = _get_material_sg(imp_mat)
        orig_sg = _get_material_sg(original)
        if not imp_sg or not orig_sg:
            continue
        objs = cmds.sets(imp_sg, q=True) or []
        if not objs:
            continue
        try:
            cmds.sets(objs, edit=True, forceElement=orig_sg)
            for node in (imp_sg, imp_mat):
                if cmds.objExists(node):
                    try:
                        cmds.delete(node)
                    except Exception:
                        pass
            reused += 1
        except Exception:
            pass
    return reused


def _import_fbx_with_material_reuse(fbx_path: str) -> bool:
    if not os.path.isfile(fbx_path):
        cmds.warning("Hotwheel Tools: file not found")
        return False
    if not cmds.pluginInfo("fbxmaya", q=True, loaded=True):
        try:
            cmds.loadPlugin("fbxmaya")
        except Exception:
            pass
    pre = set(cmds.ls(materials=True) or [])
    try:
        cmds.file(
            fbx_path,
            i=True,
            type="FBX",
            ignoreVersion=True,
            mergeNamespacesOnClash=False,
            namespace=":",
        )
    except Exception as exc:
        cmds.warning(f"Hotwheel Tools: import failed: {exc}")
        return False
    _safe_material_reuse(pre)
    return True


def _run_group_by_layer_name() -> bool:
    try:
        import maya.mel as mel

        mel.eval(
            """
string $skipLayers[] = {
    "defaultLayer",
    "Source_Modules"
};

string $layers[] = `ls -type displayLayer`;

for ($layer in $layers)
{
    int $skip = 0;

    for ($skipLayer in $skipLayers)
    {
        if ($layer == $skipLayer)
        {
            $skip = 1;
            break;
        }
    }

    if ($skip)
        continue;

    string $members[] = `editDisplayLayerMembers -q $layer`;

    if (size($members) == 0)
        continue;

    string $grp = ($layer + "_GRP");

    if (!`objExists $grp`)
        group -em -name $grp;

    for ($obj in $members)
    {
        if (`objExists $obj`)
        {
            parent $obj $grp;
        }
    }
}
"""
        )
        return True
    except Exception as exc:
        cmds.warning(f"Hotwheel Tools: group by layer failed: {exc}")
        return False


def _reset_persp_clip_planes() -> bool:
    try:
        import maya.mel as mel

        mel.eval(
            """
setAttr "persp.nearClipPlane" 1;
setAttr "persp.farClipPlane" 100000;
"""
        )
        return True
    except Exception as exc:
        cmds.warning(f"Hotwheel Tools: reset persp clip failed: {exc}")
        return False


def _load_fbx_list() -> dict:
    result: dict = {}
    try:
        for fname in sorted(os.listdir(MESH_ROOT), key=str.lower):
            if fname.lower().endswith(".fbx"):
                result[os.path.splitext(fname)[0]] = os.path.join(MESH_ROOT, fname)
    except Exception:
        pass
    return result


def UI():
    if cmds.window(WINDOW_ID, exists=True):
        cmds.deleteUI(WINDOW_ID, window=True)

    win = cmds.window(
        WINDOW_ID,
        title="HW3 Tools",
        widthHeight=(570, 530),
        sizeable=True,
        resizeToFitChildren=False,
    )

    tabs = cmds.tabLayout(innerMarginWidth=6, innerMarginHeight=6)

    ue_col = cmds.columnLayout(adjustableColumn=True, parent=tabs)
    main_row = cmds.rowLayout(
        numberOfColumns=2,
        columnWidth2=(320, 220),
        columnAttach=[(1, "both", 2), (2, "both", 2)],
        adjustableColumn=1,
        parent=ue_col,
    )

    left_col = cmds.columnLayout(adjustableColumn=True, parent=main_row)
    cmds.rowLayout(
        numberOfColumns=3,
        adjustableColumn=1,
        columnAttach=[(1, "left", 0), (2, "right", 2), (3, "right", 0)],
        parent=left_col,
    )
    cmds.text(label="Material :", align="left", font="boldLabelFont")
    refresh_json_btn = cmds.button(label="Refresh", height=22)
    clear_mat_btn = cmds.button(label="Clear", height=22, backgroundColor=(0.65, 0.20, 0.20))
    cmds.setParent("..")

    mat_json_list = cmds.textScrollList(height=110, allowMultiSelection=False, parent=left_col)
    cmds.separator(height=6, style="in", parent=left_col)

    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1,
        columnAttach=[(1, "left", 0), (2, "right", 0)],
        parent=left_col,
    )
    cmds.text(label="UV - ScaleOffset", font="boldLabelFont", align="left")
    reset_uv_btn = cmds.button(label="Reset", height=22)
    cmds.setParent("..")
    cmds.separator(height=2, style="none", parent=left_col)

    uv_fields: dict[str, str] = {}
    for label, default in zip(("R", "G", "B", "A"), (1.0, 1.0, 0.0, 0.0)):
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(30, 100), parent=left_col)
        cmds.text(label=label, align="right", width=28)
        uv_fields[label] = cmds.floatField(value=default, precision=4, step=0.1)
        cmds.setParent("..")

    cmds.separator(height=6, style="in", parent=left_col)

    cmds.rowLayout(
        numberOfColumns=3,
        adjustableColumn=1,
        columnAttach=[(1, "left", 0), (2, "right", 2), (3, "right", 0)],
        parent=left_col,
    )
    cmds.text(label="Textures:", align="left", font="boldLabelFont")
    refresh_tex_btn = cmds.button(label="Refresh", height=22)
    clear_tex_btn = cmds.button(label="Clear", height=22, backgroundColor=(0.65, 0.20, 0.20))
    cmds.setParent("..")
    cmds.separator(height=2, style="none", parent=left_col)

    tex_list = cmds.textScrollList(height=110, allowMultiSelection=False, parent=left_col)
    cmds.separator(height=6, style="none", parent=left_col)
    assign_btn = cmds.button(
        label="Assign",
        height=36,
        backgroundColor=(0.20, 0.60, 0.30),
        parent=left_col,
    )
    cmds.setParent("..")

    right_col = cmds.columnLayout(adjustableColumn=True, parent=main_row)
    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1,
        columnAttach=[(1, "left", 0), (2, "right", 0)],
        parent=right_col,
    )
    cmds.text(label="Maya Material:", align="left", font="boldLabelFont")
    refresh_btn = cmds.button(label="Refresh", height=22)
    cmds.setParent("..")

    mat_list = cmds.textScrollList(height=390, allowMultiSelection=True, parent=right_col)
    cmds.separator(height=4, style="none", parent=right_col)
    cmds.rowLayout(
        numberOfColumns=2,
        columnAttach=[(1, "right", 4), (2, "both", 2)],
        adjustableColumn=2,
        parent=right_col,
    )
    cmds.text(label="UV Set:", align="right")
    uv_menu = cmds.optionMenu(enable=False)
    cmds.menuItem(label="(no mesh)")
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")

    mod_col = cmds.columnLayout(adjustableColumn=True, parent=tabs)
    src_frame = cmds.frameLayout(
        label="Source Modules I/O",
        collapsable=True,
        collapse=False,
        marginWidth=4,
        marginHeight=4,
        parent=mod_col,
    )
    src_inner = cmds.columnLayout(adjustableColumn=True, parent=src_frame)
    cmds.rowLayout(
        numberOfColumns=3,
        adjustableColumn=1,
        columnAttach=[(1, "left", 0), (2, "right", 2), (3, "right", 0)],
        parent=src_inner,
    )
    cmds.text(label="FBX Mesh:", align="left", font="boldLabelFont")
    refresh_fbx_btn = cmds.button(label="Refresh", height=22)
    clear_fbx_btn = cmds.button(label="Clear", height=22)
    cmds.setParent("..")
    fbx_list = cmds.textScrollList(height=160, allowMultiSelection=True, parent=src_inner)
    cmds.separator(height=6, style="in", parent=src_inner)
    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1,
        columnAttach=[(1, "both", 2), (2, "both", 2)],
        parent=src_inner,
    )
    export_src_btn = cmds.button(label="Export Source Modules", height=30)
    import_src_btn = cmds.button(label="Import Source Modules", height=30)
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.separator(height=8, style="none", parent=mod_col)

    fio_frame = cmds.frameLayout(
        label="File I/O",
        collapsable=False,
        marginWidth=4,
        marginHeight=4,
        parent=mod_col,
    )
    fio_inner = cmds.columnLayout(adjustableColumn=True, parent=fio_frame)
    sync_btn = cmds.button(
        label="Sync Building Scene",
        height=36,
        backgroundColor=(0.20, 0.45, 0.65),
        parent=fio_inner,
    )
    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1,
        columnAttach=[(1, "both", 2), (2, "both", 2)],
        parent=fio_inner,
    )
    import_temp_btn = cmds.button(label="Import", height=30)
    export_sel_btn = cmds.button(label="Export Selected", height=30)
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")

    _sj_id: list[int | None] = [None]
    _cached_shapes: list[str] = []
    _json_mats: list[dict] = []
    _json_texs: list[dict] = []
    _selected_tex: list[str] = [""]
    _json_uv: list[float] = [1.0, 1.0, 0.0, 0.0]
    _selecting: list[bool] = [False]
    _fbx_paths: list[dict] = [{}]

    def _populate_materials() -> None:
        cmds.textScrollList(mat_list, edit=True, removeAll=True)
        mats = _list_scene_materials()
        if not mats:
            cmds.textScrollList(mat_list, edit=True, append="(no materials)")
            return
        for mat_name in mats:
            cmds.textScrollList(mat_list, edit=True, append=mat_name)

    def _refresh_materials(*_) -> None:
        _populate_materials()
        _refresh_assign_btn()

    def _refresh_json(*_) -> None:
        _json_mats.clear()
        _json_mats.extend(_load_json_materials())
        cmds.textScrollList(mat_json_list, edit=True, removeAll=True)
        for mat_data in _json_mats:
            cmds.textScrollList(mat_json_list, edit=True, append=mat_data.get("name", "???"))
        _refresh_assign_btn()

    def _refresh_textures(*_) -> None:
        _json_texs.clear()
        _json_texs.extend(_load_textures())
        cmds.textScrollList(tex_list, edit=True, removeAll=True)
        for entry in _json_texs:
            cmds.textScrollList(tex_list, edit=True, append=entry["name"])
        _selected_tex[0] = ""
        _refresh_assign_btn()

    def _on_json_mat_select(*_) -> None:
        if _selecting[0]:
            return
        _selecting[0] = True
        try:
            cmds.textScrollList(tex_list, edit=True, deselectAll=True)
            _selected_tex[0] = ""
            selected_indexes = cmds.textScrollList(mat_json_list, query=True, selectIndexedItem=True)
            if not selected_indexes:
                _refresh_assign_btn()
                return
            index = selected_indexes[0] - 1
            if not (0 <= index < len(_json_mats)):
                _refresh_assign_btn()
                return
            uv_vec = _json_mats[index].get("vectors", {}).get("UV - ScaleOffset") or {}
            _json_uv[:] = [
                uv_vec.get("r", 1.0),
                uv_vec.get("g", 1.0),
                uv_vec.get("b", 0.0),
                uv_vec.get("a", 0.0),
            ]
            for key, value in zip(("R", "G", "B", "A"), _json_uv):
                cmds.floatField(uv_fields[key], edit=True, value=value)
            _refresh_assign_btn()
        finally:
            _selecting[0] = False

    def _on_tex_select(*_) -> None:
        if _selecting[0]:
            return
        _selecting[0] = True
        try:
            cmds.textScrollList(mat_json_list, edit=True, deselectAll=True)
            _selected_tex[0] = ""
            selected_indexes = cmds.textScrollList(tex_list, query=True, selectIndexedItem=True)
            if not selected_indexes:
                _refresh_assign_btn()
                return
            index = selected_indexes[0] - 1
            if 0 <= index < len(_json_texs):
                _selected_tex[0] = _json_texs[index]["path"]
            _refresh_assign_btn()
        finally:
            _selecting[0] = False

    def _on_selection_changed(*_) -> None:
        for item in cmds.optionMenu(uv_menu, query=True, itemListLong=True) or []:
            cmds.deleteUI(item)
        shapes = _get_selected_mesh_shapes()
        _cached_shapes.clear()
        _cached_shapes.extend(shapes)
        if not shapes:
            cmds.menuItem(label="(no mesh)", parent=uv_menu)
            cmds.optionMenu(uv_menu, edit=True, enable=False)
        else:
            shape = shapes[0]
            try:
                uv_sets = cmds.polyUVSet(shape, query=True, allUVSets=True) or ["map1"]
                active = (cmds.polyUVSet(shape, query=True, currentUVSet=True) or ["map1"])[0]
            except Exception:
                uv_sets = ["map1"]
                active = "map1"
            for uv_name in uv_sets:
                cmds.menuItem(label=uv_name, parent=uv_menu)
            cmds.optionMenu(uv_menu, edit=True, enable=True, value=active)

        assigned = _get_selected_materials_from_selection()
        cmds.textScrollList(mat_list, edit=True, deselectAll=True)
        list_items = cmds.textScrollList(mat_list, query=True, allItems=True) or []
        for mat_name in assigned:
            if mat_name in list_items:
                cmds.textScrollList(mat_list, edit=True, selectItem=mat_name)
        _refresh_assign_btn()

    def _on_close(*_) -> None:
        if _sj_id[0] is not None:
            try:
                cmds.scriptJob(kill=_sj_id[0], force=True)
            except Exception:
                pass
        _sj_id[0] = None

    def _is_update_mode() -> bool:
        path = _selected_tex[0]
        selected = cmds.textScrollList(mat_list, query=True, selectItem=True) or []
        material = selected[0] if selected else ""
        if not path or not material or material == "(no materials)" or not cmds.objExists(material):
            return False
        file_node = _find_connected_file_node(material, _get_color_attr(material))
        if file_node is None:
            return False
        existing = (cmds.getAttr(f"{file_node}.fileTextureName") or "").replace("\\", "/")
        return existing == path.replace("\\", "/")

    def _refresh_assign_btn(*_) -> None:
        if _is_update_mode():
            cmds.button(assign_btn, edit=True, label="Update", backgroundColor=(0.20, 0.50, 0.70))
        else:
            cmds.button(assign_btn, edit=True, label="Assign", backgroundColor=(0.20, 0.60, 0.30))

    def _on_assign(*_) -> None:
        mat_selected = cmds.textScrollList(mat_json_list, query=True, selectIndexedItem=True) or []
        tex_selected = cmds.textScrollList(tex_list, query=True, selectIndexedItem=True) or []
        if not mat_selected and not tex_selected:
            cmds.warning("Hotwheel Tools: select a Material or a Texture first.")
            return

        selected_materials = cmds.textScrollList(mat_list, query=True, selectItem=True) or []
        material = selected_materials[0] if selected_materials else ""
        if not material or material == "(no materials)" or not cmds.objExists(material):
            cmds.warning("Hotwheel Tools: no valid Maya material selected - click Refresh.")
            return

        r = cmds.floatField(uv_fields["R"], query=True, value=True)
        g = cmds.floatField(uv_fields["G"], query=True, value=True)
        b = cmds.floatField(uv_fields["B"], query=True, value=True)
        a = cmds.floatField(uv_fields["A"], query=True, value=True)
        uv_set = cmds.optionMenu(uv_menu, query=True, value=True)
        mesh = _cached_shapes[0].split("|")[-1] if _cached_shapes and uv_set and uv_set != "(no mesh)" else ""

        try:
            if mat_selected:
                index = mat_selected[0] - 1
                if not (0 <= index < len(_json_mats)):
                    return
                bc_path, n_path = _find_mat_textures(_json_mats[index])
                if not bc_path and not n_path:
                    cmds.warning("Hotwheel Tools: no textures found in material JSON.")
                    return
                _assign_material_network(material, bc_path, n_path, r, g, b, a, mesh, uv_set)
                cmds.inViewMessage(
                    assistMessage=f"Material assigned to <hl>{material}</hl>",
                    position="midCenter",
                    fade=True,
                )
                return

            path = _selected_tex[0]
            if not path or not os.path.isfile(path):
                cmds.warning("Hotwheel Tools: no texture selected or file not found.")
                return

            if _is_update_mode():
                _update_existing_material_network(material, path, r, g, b, a, mesh, uv_set)
                cmds.inViewMessage(
                    assistMessage=f"UV updated on <hl>{material}</hl>",
                    position="midCenter",
                    fade=True,
                )
                return

            _assign_material_network(material, path, None, r, g, b, a, mesh, uv_set)
            cmds.inViewMessage(
                assistMessage=f"Texture assigned to <hl>{material}</hl>",
                position="midCenter",
                fade=True,
            )
        except Exception as exc:
            cmds.warning(f"Hotwheel Tools: assign failed: {exc}")

    def _on_clear_mat(*_) -> None:
        if cmds.confirmDialog(
            title="Clear Material folder",
            message="Delete all files in:\n" + MAT_ROOT,
            button=["OK", "Cancel"],
            defaultButton="Cancel",
            cancelButton="Cancel",
        ) != "OK":
            return
        import shutil

        for entry in os.listdir(MAT_ROOT):
            full = os.path.join(MAT_ROOT, entry)
            try:
                if os.path.isfile(full) or os.path.islink(full):
                    os.remove(full)
                elif os.path.isdir(full):
                    shutil.rmtree(full)
            except Exception as exc:
                cmds.warning(f"Hotwheel Tools: could not delete {full}: {exc}")
        _refresh_json()

    def _on_clear_tex(*_) -> None:
        if cmds.confirmDialog(
            title="Clear Textures folder",
            message="Delete all files in:\n" + TEX_ROOT,
            button=["OK", "Cancel"],
            defaultButton="Cancel",
            cancelButton="Cancel",
        ) != "OK":
            return
        import shutil

        for entry in os.listdir(TEX_ROOT):
            full = os.path.join(TEX_ROOT, entry)
            try:
                if os.path.isfile(full) or os.path.islink(full):
                    os.remove(full)
                elif os.path.isdir(full):
                    shutil.rmtree(full)
            except Exception as exc:
                cmds.warning(f"Hotwheel Tools: could not delete {full}: {exc}")
        _refresh_textures()

    def _on_reset_uv(*_) -> None:
        for key, value in zip(("R", "G", "B", "A"), _json_uv):
            cmds.floatField(uv_fields[key], edit=True, value=value)

    def _refresh_fbx(*_) -> None:
        _fbx_paths[0] = _load_fbx_list()
        cmds.textScrollList(fbx_list, edit=True, removeAll=True)
        for name in _fbx_paths[0]:
            cmds.textScrollList(fbx_list, edit=True, append=name)

    def _on_clear_fbx(*_) -> None:
        selected = cmds.textScrollList(fbx_list, query=True, selectItem=True) or []
        if selected:
            if cmds.confirmDialog(
                title="Clear FBX",
                message=f"Delete {len(selected)} selected file(s)?",
                button=["OK", "Cancel"],
                defaultButton="Cancel",
                cancelButton="Cancel",
            ) != "OK":
                return
            for name in selected:
                path = _fbx_paths[0].get(name, "")
                try:
                    if path and os.path.isfile(path):
                        os.remove(path)
                except Exception:
                    pass
        else:
            if cmds.confirmDialog(
                title="Clear FBX",
                message="Delete all FBX files?",
                button=["OK", "Cancel"],
                defaultButton="Cancel",
                cancelButton="Cancel",
            ) != "OK":
                return
            try:
                for entry in os.listdir(MESH_ROOT):
                    full = os.path.join(MESH_ROOT, entry)
                    if os.path.isfile(full):
                        try:
                            os.remove(full)
                        except Exception:
                            pass
            except Exception:
                pass
        _refresh_fbx()

    def _on_export_source_modules(*_) -> None:
        selected = cmds.ls(selection=True, long=True) or []
        if not selected:
            cmds.warning("Hotwheel Tools: select at least one object to export.")
            return
        os.makedirs(MESH_ROOT, exist_ok=True)
        exported = 0
        for obj in selected:
            name = obj.split("|")[-1]
            fbx_path = os.path.join(MESH_ROOT, name + ".fbx")
            cmds.select(obj, replace=True)
            try:
                cmds.file(fbx_path, force=True, exportSelected=True, type="FBX export")
                exported += 1
            except Exception as exc:
                cmds.warning(f"Hotwheel Tools: failed to export {name}: {exc}")
        if selected:
            cmds.select(selected, replace=True)
        _refresh_fbx()
        if exported:
            cmds.inViewMessage(
                assistMessage=f"Exported {exported} object(s)",
                position="midCenter",
                fade=True,
            )

    def _on_sync_building_scene(*_) -> None:
        fbx_path = r"D:\Temp\HW\temp_building_scene.fbx"
        if _import_fbx_with_material_reuse(fbx_path):
            _run_group_by_layer_name()
            _reset_persp_clip_planes()
            cmds.inViewMessage(
                assistMessage="Building scene synced",
                position="midCenter",
                fade=True,
            )

    def _on_import_temp(*_) -> None:
        fbx_path = r"D:\Temp\HW\temp.fbx"
        if _import_fbx_with_material_reuse(fbx_path):
            cmds.inViewMessage(assistMessage="Imported", position="midCenter", fade=True)

    def _on_export_selected(*_) -> None:
        import maya.mel as mel

        selected = cmds.ls(selection=True, long=True) or []
        if not selected:
            cmds.warning("Hotwheel Tools: select at least one object to export.")
            return
        export_path = r"D:\Temp\HW\temp.fbx"
        os.makedirs(r"D:\Temp\HW", exist_ok=True)
        try:
            mel.eval("FBXExportInstances -v true")
            mel.eval("FBXExportTriangulate -v false")
            cmds.file(export_path, force=True, exportSelected=True, type="FBX export")
            cmds.inViewMessage(
                assistMessage="Exported selected",
                position="midCenter",
                fade=True,
            )
        except Exception as exc:
            cmds.warning(f"Hotwheel Tools: export failed: {exc}")

    def _on_import_source_modules(*_) -> None:
        selected = cmds.textScrollList(fbx_list, query=True, selectItem=True) or []
        if not selected:
            cmds.warning("Hotwheel Tools: select FBX file(s) to import.")
            return
        imported = 0
        for name in selected:
            fbx_path = _fbx_paths[0].get(name, "")
            if not fbx_path or not os.path.isfile(fbx_path):
                continue
            if _import_fbx_with_material_reuse(fbx_path):
                imported += 1
        if imported:
            cmds.inViewMessage(
                assistMessage=f"Imported {imported} file(s)",
                position="midCenter",
                fade=True,
            )

    cmds.button(refresh_json_btn, edit=True, command=_refresh_json)
    cmds.button(clear_mat_btn, edit=True, command=_on_clear_mat)
    cmds.button(refresh_tex_btn, edit=True, command=_refresh_textures)
    cmds.button(clear_tex_btn, edit=True, command=_on_clear_tex)
    cmds.button(reset_uv_btn, edit=True, command=_on_reset_uv)
    cmds.button(refresh_btn, edit=True, command=_refresh_materials)
    cmds.button(assign_btn, edit=True, command=_on_assign)
    cmds.textScrollList(mat_json_list, edit=True, selectCommand=_on_json_mat_select)
    cmds.textScrollList(tex_list, edit=True, selectCommand=_on_tex_select)
    cmds.textScrollList(mat_list, edit=True, selectCommand=_refresh_assign_btn)

    cmds.button(refresh_fbx_btn, edit=True, command=_refresh_fbx)
    cmds.button(clear_fbx_btn, edit=True, command=_on_clear_fbx)
    cmds.button(export_src_btn, edit=True, command=_on_export_source_modules)
    cmds.button(import_src_btn, edit=True, command=_on_import_source_modules)
    cmds.button(sync_btn, edit=True, command=_on_sync_building_scene)
    cmds.button(import_temp_btn, edit=True, command=_on_import_temp)
    cmds.button(export_sel_btn, edit=True, command=_on_export_selected)

    _sj_id[0] = cmds.scriptJob(event=["SelectionChanged", _on_selection_changed])
    cmds.window(win, edit=True, closeCommand=_on_close)

    _refresh_json()
    _refresh_textures()
    _populate_materials()
    _on_selection_changed()
    _refresh_assign_btn()
    _refresh_fbx()

    cmds.tabLayout(tabs, edit=True, tabLabel=[(ue_col, "Materials"), (mod_col, "Modelling")])
    cmds.showWindow(win)

UI()