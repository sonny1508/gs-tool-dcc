"""Shared helpers for the GS Pipeline addon.

Tool modules import from here instead of copying code between them:

  * Scene helpers: selection, Object Mode, auto smooth across 3.6 / 4.1+.
  * ToolLog: the short result log a tool draws at the bottom of its tab.
  * Remembered preferences: the Blender counterpart of the Maya tools' optionVars.
  * HW3 payload loaders. The external pipeline (Unreal Engine exporter + 3ds Max
    exporter) writes the same JSON/FBX payloads regardless of which DCC consumes
    them, so the folder layout and data schema here mirror the Maya HW3 tool exactly.
"""
from __future__ import annotations

import contextlib
import json
import logging
import os
import textwrap

import bpy

_LOG = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Scene helpers
# ----------------------------------------------------------------------------
def select_only(context, objects):
    """Select exactly ``objects`` (in Object Mode) and make the first one active."""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    if objects:
        context.view_layer.objects.active = objects[0]


def ensure_object_mode(context):
    if context.mode != 'OBJECT' and context.view_layer.objects.active is not None:
        bpy.ops.object.mode_set(mode='OBJECT')


def legacy_auto_smooth():
    """True on Blender 3.6, where auto smooth is a mesh setting (4.1+ replaced it with a modifier)."""
    return "use_auto_smooth" in bpy.types.Mesh.bl_rna.properties


def set_auto_smooth(context, objects, angle):
    """Blender's own Object > Shade Auto Smooth, so the result matches the menu entry exactly.

    Leaves ``objects`` selected, the first one active.
    """
    select_only(context, objects)
    if legacy_auto_smooth():
        # 3.6: Shade Auto Smooth is Shade Smooth with the mesh's auto smooth turned on.
        bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=angle)
    else:
        # 4.1+: adds (or updates) the "Smooth by Angle" modifier.
        bpy.ops.object.shade_auto_smooth(angle=angle)


def redraw_view3d():
    """Redraw every 3D View, so a tab picks up state changed outside its own draw."""
    wm = bpy.context.window_manager
    if wm is None:
        return
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def _ui_scale(context):
    # 0 when Blender runs without a window (background mode).
    return context.preferences.system.ui_scale or 1.0


def is_wide(context, width):
    """True when the sidebar is at least ``width`` px wide (at 1x UI scale).

    Blender can't hold the sidebar at a minimum width, so tabs use this to put
    settings side by side when there is room and stack them when there isn't.
    """
    region = context.region
    if region is None:
        return True
    return region.width >= width * _ui_scale(context)


@contextlib.contextmanager
def wait_cursor(context):
    """Show the wait cursor while a long action runs."""
    window = context.window
    if window is not None:
        window.cursor_set('WAIT')
    try:
        yield
    finally:
        if window is not None:
            window.cursor_set('DEFAULT')


# ----------------------------------------------------------------------------
# Result log
# ----------------------------------------------------------------------------
# Log levels, as in the Maya tools: ok = done as asked, warn = done but look at
# this, error = nothing done (the message says why). Blender can't colour label
# text, so the icon carries the level; error lines also draw in the alert colour.
LOG_ICONS = {"ok": 'CHECKMARK', "warn": 'ERROR', "error": 'CANCEL', "info": 'INFO'}
_REPORT_TYPES = {"warn": {'WARNING'}, "error": {'WARNING'}}

# Rough width of one character of UI text, in px at 1x scale, for wrapping.
_CHAR_WIDTH = 6.5


class ToolLog:
    """The few result lines a tool shows at the bottom of its tab.

    Runtime only: empty in each new Blender session, cleared at the start of
    each action. Lines also go to the status bar through the operator, as a
    warning for warn / error (an ERROR report would open a pop-up).
    """

    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.lines = []

    def clear(self):
        self.lines.clear()

    def add(self, message, level="info", op=None):
        self.lines.append((level, message))
        if op is not None:
            op.report(_REPORT_TYPES.get(level, {'INFO'}), message)
        redraw_view3d()

    def draw(self, layout, context):
        box = layout.box()
        box.label(text="Log")
        col = box.column(align=True)
        region = context.region
        scale = _ui_scale(context)
        width =max(16, int(((region.width if region else 300) - 70 * scale) / (_CHAR_WIDTH * scale)))
        if not self.lines:
            col.enabled = False
            for part in textwrap.wrap(self.placeholder, width):
                col.label(text=part)
            return
        for level, message in self.lines:
            icon = LOG_ICONS.get(level, 'INFO')
            for part in textwrap.wrap(message, width) or [""]:
                row = col.row()
                row.alert = level == "error"
                row.label(text=part, icon=icon)
                icon = 'BLANK1'  # continuation lines line up under the text


# ----------------------------------------------------------------------------
# Remembered preferences
# ----------------------------------------------------------------------------
# Preferences that last between sessions (the Maya tools keep these in
# optionVars), in one JSON file in this Blender version's config folder. Keys
# are prefixed by the tool. Values a project spec defines don't belong here.
_PREFS_FILE = "gs_pipeline_prefs.json"
_prefs = None


def _prefs_path():
    return os.path.join(bpy.utils.user_resource('CONFIG'), _PREFS_FILE)


def _load_prefs():
    global _prefs
    if _prefs is None:
        try:
            with open(_prefs_path(), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            _prefs = data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            _prefs = {}
    return _prefs


def pref_get(key, default):
    value = _load_prefs().get(key, default)
    return value if isinstance(value, type(default)) else default


def pref_set(key, value):
    prefs = _load_prefs()
    if prefs.get(key) == value:
        return
    prefs[key] = value
    path = _prefs_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(prefs, fh, indent=2, sort_keys=True)
    except OSError as exc:
        _LOG.warning("GS Pipeline: could not save preferences to %s: %s", path, exc)


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


def load_json_materials() -> list[dict]:
    result: list[dict] = []
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


def load_textures() -> list[dict]:
    json_results: list[dict] = []
    image_results: list[dict] = []
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
                    resolved = resolve_texture_path(data.get("path", ""), TEX_ROOT)
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
    _reuse_duplicate_materials(pre_mats)
    return new_objects


def _reuse_duplicate_materials(pre_mats: set) -> int:
    """Remap newly imported ``Name.NNN`` materials onto their pre-existing base."""
    import re

    current = set(bpy.data.materials)
    new_mats = list(current - pre_mats)
    suffix_re = re.compile(r"^(.*)\.\d{3}$")
    reused = 0
    for mat in new_mats:
        match = suffix_re.match(mat.name)
        if not match:
            continue
        base_name = match.group(1)
        original = bpy.data.materials.get(base_name)
        if original is None or original is mat or original in new_mats:
            continue
        try:
            mat.user_remap(original)
            bpy.data.materials.remove(mat)
            reused += 1
        except Exception:
            _LOG.warning("GS Pipeline: could not reuse material %s", mat.name, exc_info=True)
    return reused


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
