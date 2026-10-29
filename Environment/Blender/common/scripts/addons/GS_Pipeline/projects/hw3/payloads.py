"""HW3 pipeline payloads: where the external exporters (Unreal Engine, 3ds Max)
leave their JSON and FBX files, and reading them.

The external pipeline writes the same payloads whichever DCC reads them, so the
folder layout and data schema here mirror the Maya HW3 tool exactly.
"""
from __future__ import annotations

import json
import logging
import os

import bpy

from ... import common

_LOG = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Roots (identical layout to the Maya HW3 tool)
# ----------------------------------------------------------------------------
_TEMP_DIR = os.environ.get("TEMP") or os.environ.get("TMP") or os.path.expanduser("~")

_UE_ROOT = os.path.join(_TEMP_DIR, "GSApplication", "unreal-engine")
MAT_ROOT = os.path.join(_UE_ROOT, "mat-ins")
TEX_ROOT = os.path.join(_UE_ROOT, "textures")

_HW3_ROOT = os.path.join(_TEMP_DIR, "GSApplication", "3dsmax", "hw3_tools")
MESH_ROOT = os.path.join(_HW3_ROOT, "mesh")
IO_ROOT = os.path.join(_HW3_ROOT, "io")

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff", ".exr", ".hdr", ".bmp"}


# ----------------------------------------------------------------------------
# Texture / material JSON loading (mirrors the Maya helpers)
# ----------------------------------------------------------------------------
def resolve_texture_path(ue_path: str, root: str) -> str | None:
    """Resolve a /Game/... style UE path to a real file under ``root``."""
    if not ue_path:
        return None
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


def _read_json(path: str, what: str) -> dict | None:
    """The JSON object in ``path``, or None (logged) if it can't be read or isn't an object."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        _LOG.warning("Skipping %s JSON %s: %s", what, path, exc)
        return None
    if not isinstance(data, dict):
        _LOG.warning("Skipping %s JSON %s: expected object payload", what, path)
        return None
    return data


def list_json_materials() -> list[dict]:
    """{"name", "path"} for every material-instance JSON in MAT_ROOT, by name.

    ``path`` is the JSON file itself: picking a row reads just that file again
    (load_json_material), rather than the whole folder.
    """
    result: list[dict] = []
    try:
        names = os.listdir(MAT_ROOT)
    except OSError as exc:
        _LOG.warning("Unable to list material JSON root %s: %s", MAT_ROOT, exc)
        return result
    for fname in names:
        if fname.lower().endswith(".json"):
            fpath = os.path.join(MAT_ROOT, fname)
            data = _read_json(fpath, "material")
            if data is not None:
                result.append({"name": data.get("name", "???"), "path": fpath})
    result.sort(key=lambda row: row["name"].lower())
    return result


def load_json_material(path: str) -> dict | None:
    """The material-instance JSON a Material list row points at, or None if it's gone."""
    if not path or not os.path.isfile(path):
        return None
    return _read_json(path, "material")


def load_textures() -> list[dict]:
    json_results: list[dict] = []
    image_results: list[dict] = []
    try:
        names = os.listdir(TEX_ROOT)
    except OSError as exc:
        _LOG.warning("Unable to list texture root %s: %s", TEX_ROOT, exc)
        names = []
    for fname in names:
        fpath = os.path.join(TEX_ROOT, fname)
        ext = os.path.splitext(fname)[1].lower()
        if ext == ".json":
            data = _read_json(fpath, "texture")
            if data is None:
                continue
            name = data.get("name", os.path.splitext(fname)[0])
            resolved = resolve_texture_path(data.get("path", ""), TEX_ROOT)
            if resolved:
                json_results.append({"name": name, "path": resolved})
            else:
                _LOG.warning("Texture metadata %s could not be resolved for %s", fpath, name)
        elif ext in _IMAGE_EXTS:
            image_results.append({"name": os.path.splitext(fname)[0], "path": fpath})
    results = json_results if json_results else image_results
    results.sort(key=lambda row: row["name"].lower())
    return results


def find_mat_textures(mat_data: dict) -> tuple[str | None, str | None]:
    """Return (base_color_path, normal_path) for the exported textures of a material JSON."""
    bc_path = None
    n_path = None
    textures = mat_data.get("textures", {})
    if not isinstance(textures, dict):
        _LOG.warning("Material textures payload is malformed: expected object at key 'textures'")
        return bc_path, n_path
    for tex_key, tex_info in textures.items():
        if not isinstance(tex_info, dict):
            _LOG.warning("Material texture entry %s is malformed: expected object payload", tex_key)
            continue
        if not tex_info.get("exported", False):
            continue
        tex_name = tex_info.get("name", "")
        path = resolve_texture_path(tex_info.get("path", ""), MAT_ROOT)
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


def load_fbx_list() -> dict:
    """Map of stem -> full path for every .fbx in the source-module mesh folder."""
    result: dict = {}
    try:
        for fname in sorted(os.listdir(MESH_ROOT), key=str.lower):
            if fname.lower().endswith(".fbx"):
                result[os.path.splitext(fname)[0]] = os.path.join(MESH_ROOT, fname)
    except OSError:
        pass
    return result


# ----------------------------------------------------------------------------
# Image loading helper (de-duplicates images by absolute path)
# ----------------------------------------------------------------------------
def load_image(path: str, is_data: bool = False):
    """Load (or reuse) an image datablock for ``path``.

    ``is_data`` marks the colorspace as Non-Color (used for normal maps).
    """
    norm = os.path.normpath(path)
    for img in bpy.data.images:
        try:
            if img.filepath and os.path.normpath(bpy.path.abspath(img.filepath)) == norm:
                _set_colorspace(img, is_data)
                return img
        except Exception:
            continue
    img = bpy.data.images.load(path, check_existing=True)
    _set_colorspace(img, is_data)
    return img


def _set_colorspace(img, is_data: bool) -> None:
    try:
        img.colorspace_settings.name = "Non-Color" if is_data else "sRGB"
    except Exception:
        # Some builds name the raw space differently; ignore if unavailable.
        pass


# ----------------------------------------------------------------------------
# FBX import with material reuse + collection grouping
# ----------------------------------------------------------------------------
def _import_fbx(fbx_path: str) -> list:
    """Import an FBX and return the list of newly added objects."""
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=fbx_path)
    except Exception as exc:  # pragma: no cover - depends on runtime FBX addon
        _LOG.warning("GS Pipeline: FBX import failed for %s: %s", fbx_path, exc)
        raise
    after = set(bpy.data.objects)
    return [obj for obj in after - before]


def import_fbx_with_material_reuse(fbx_path: str) -> list | None:
    """Import an FBX, then collapse freshly-imported duplicate materials.

    Blender suffixes name clashes with ``.001`` etc. on import. We treat
    ``Foo.001`` as a duplicate of an existing ``Foo`` and remap every user of
    the duplicate back onto the original, then purge the duplicate. This is the
    Blender analogue of the Maya ``_safe_material_reuse`` rename-walk.
    """
    if not os.path.isfile(fbx_path):
        _LOG.warning("GS Pipeline: file not found: %s", fbx_path)
        return None

    pre_mats = set(bpy.data.materials)
    new_objects = _import_fbx(fbx_path)
    common.merge_duplicate_materials([m for m in bpy.data.materials if m not in pre_mats])
    return new_objects


# Layers that should never become their own collection (mirrors the Maya skip list).
_SKIP_GROUP_NAMES = {"defaultLayer", "Source_Modules", "Scene Collection"}


def group_imported_by_collection(objects: list) -> int:
    """Group freshly imported objects into collections by their root empty.

    3ds Max layers/groups arrive in the FBX as parent empties. Each top-level
    empty becomes a collection named ``<empty>_GRP`` (mirroring the Maya
    ``_GRP`` group), and the mesh descendants are linked into it. Objects with
    no qualifying group root are left in the active collection.
    """
    if not objects:
        return 0

    imported = set(objects)
    grouped = 0

    def _root_group(obj):
        node = obj
        last_empty = None
        while node is not None and node in imported:
            if node.type == "EMPTY" and node.name not in _SKIP_GROUP_NAMES:
                last_empty = node
            node = node.parent
        return last_empty

    collections: dict[str, bpy.types.Collection] = {}
    for obj in objects:
        if obj.type not in {"MESH", "EMPTY"}:
            continue
        root = _root_group(obj)
        if root is None:
            continue
        grp_name = f"{root.name}_GRP"
        coll = collections.get(grp_name)
        if coll is None:
            coll = bpy.data.collections.get(grp_name)
            if coll is None:
                coll = bpy.data.collections.new(grp_name)
                bpy.context.scene.collection.children.link(coll)
            collections[grp_name] = coll
        # Move obj into the group collection (unlink from any current ones).
        for existing in list(obj.users_collection):
            existing.objects.unlink(obj)
        coll.objects.link(obj)
        grouped += 1

    return grouped


# ----------------------------------------------------------------------------
# FBX export parameter compatibility (3.6 - 4.5)
# ----------------------------------------------------------------------------
def export_selected_fbx(filepath: str) -> None:
    """Export current selection to FBX with broad version compatibility."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    kwargs = dict(
        filepath=filepath,
        use_selection=True,
        object_types={"MESH", "EMPTY"},
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        bake_anim=False,
    )
    try:
        bpy.ops.export_scene.fbx(**kwargs)
    except TypeError:
        # Strip any kwargs not understood by this Blender's exporter and retry.
        bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True, bake_anim=False)
