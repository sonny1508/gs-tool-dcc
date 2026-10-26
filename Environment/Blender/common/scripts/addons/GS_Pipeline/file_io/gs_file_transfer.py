"""GS File Transfer tool, integrated into the GS Pipeline 'File I/O' category.

Moves FBX files between Blender, Maya and 3ds Max, either through this machine's
temp folder (Local) or through the studio share (Server). The panel is the
import / export settings side by side, then a Local and a Server section, each
with one software picker and an Import and Export button.

File names are a contract with the Maya and 3ds Max sides of GS File Transfer
(``<source>_to_<target>.fbx`` and the per-object / per-user variants built in
the operators below). Change them in all three tools or not at all.
"""
from __future__ import annotations

import contextlib
import csv
import getpass
import math
import os
import re
import tempfile
import threading
from collections import deque

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy.types import Operator

# ===== GLOBAL FBX SETTINGS CONFIGURATION =====
username = getpass.getuser()
temp_dir = tempfile.gettempdir()

LOCAL_DIR = os.path.join(temp_dir, "fileTransferFbx")
LOCAL_DIR_INDIVIDUAL = os.path.join(temp_dir, "fileTransferFbxIndividual")
SERVER_DIR = r"\\192.168.1.210\Temp\File_Transfer"
# Combined into one user list. Same format: a header row with a 'User' column.
USER_CSVS = (
    r"\\192.168.1.210\Pipeline\Library\Data\Data_Computer_Update.csv",
    r"\\192.168.1.210\Pipeline\Library\Data\Data_Computer_Manual.csv",
)

# (token used in transfer file names, label shown in the panel). The tokens are
# shared with the Maya and 3ds Max tools -- don't rename them.
APPS = (
    ("maya", "Maya"),
    ("max", "3ds Max"),
    ("blender", "Blender"),
)
APP_LABELS = dict(APPS)
APP_ITEMS = [(token, label, "") for token, label in APPS]
THIS_APP = "blender"


class FBXSettings:
    """Centralized FBX import/export settings configuration.

    IMPORT and EXPORT keys are passed straight through to the FBX operators, so
    every key must be a real parameter of bpy.ops.import_scene.fbx /
    bpy.ops.export_scene.fbx.
    """

    IMPORT = {
        'use_custom_normals': True,
        'use_image_search': True,
        'use_alpha_decals': False,
        'decal_offset': 0.0,
        'use_anim': True,
        'anim_offset': 1.0,
        'use_subsurf': False,
        'use_custom_props': True,
        'use_custom_props_enum_as_string': True,
        'ignore_leaf_bones': False,
        'force_connect_children': False,
        'automatic_bone_orientation': False,
        'primary_bone_axis': 'Y',
        'secondary_bone_axis': 'X',
    }

    EXPORT = {
        'use_selection': True,
        'use_active_collection': False,
        'apply_unit_scale': True,
        'apply_scale_options': 'FBX_SCALE_ALL',
        'use_space_transform': True,
        'bake_space_transform': False,
        'object_types': {'MESH', 'EMPTY'},  # empties carry the hierarchy; narrowed to meshes by Mesh Only
        'use_mesh_modifiers': True,
        'use_mesh_modifiers_render': True,
        'mesh_smooth_type': 'OFF',  # switched to 'SMOOTH_GROUP' for 3ds Max when enabled
        'use_subsurf': False,
        'use_mesh_edges': False,
        'use_tspace': False,
        'use_custom_props': False,
        'add_leaf_bones': True,
        'primary_bone_axis': 'Y',
        'secondary_bone_axis': 'X',
        'use_armature_deform_only': False,
        'armature_nodetype': 'NULL',
        'bake_anim': False,
        'bake_anim_use_all_bones': True,
        'bake_anim_use_nla_strips': True,
        'bake_anim_use_all_actions': True,
        'bake_anim_force_startend_keying': True,
        'bake_anim_step': 1.0,
        'bake_anim_simplify_factor': 1.0,
        'path_mode': 'AUTO',
        'embed_textures': False,
        'batch_mode': 'OFF',
        'use_batch_own_dir': True,
        'use_metadata': True,
    }

    SCALE = {
        'use_auto_scale': True,
        'manual_import_scale': 1.0,
        'manual_export_scale': 1.0,
    }

    TRANSFORM = {
        'apply_transform_on_import': True,
        'apply_transform_on_export': True,
    }


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def transfer_stem(source_app, target_app):
    """'<source>_to_<target>', the core of every transfer file name."""
    return f"{source_app}_to_{target_app}"


def safe_file_name(name):
    cleaned = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return cleaned or "object"


def individual_files(directory, stem):
    """Every '<object>_<stem>.fbx' in ``directory`` -- the per-object files of one transfer."""
    suffix = f"_{stem}.fbx".lower()
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return []
    return [os.path.join(directory, name) for name in names if name.lower().endswith(suffix)]


def select_only(context, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    if objects:
        context.view_layer.objects.active = objects[0]


def ensure_object_mode(context):
    if context.mode != 'OBJECT' and context.view_layer.objects.active is not None:
        bpy.ops.object.mode_set(mode='OBJECT')


def calculate_import_scale(context):
    if not FBXSettings.SCALE['use_auto_scale']:
        return FBXSettings.SCALE['manual_import_scale']
    unit_scale = context.scene.unit_settings.scale_length
    return unit_scale / 1.0 if unit_scale > 0 else 1.0


def calculate_export_scale(context):
    if not FBXSettings.SCALE['use_auto_scale']:
        return FBXSettings.SCALE['manual_export_scale']
    unit_scale = context.scene.unit_settings.scale_length
    return 1.0 / unit_scale if unit_scale > 0 else 1.0


# ---------------------------------------------------------------------------
# Import post-processing
# ---------------------------------------------------------------------------
def clear_normals_from_objects(context, objects):
    """Strip custom normals and sharp edges, leaving plain smooth shading."""
    for obj in objects:
        select_only(context, [obj])
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
        bpy.ops.mesh.mark_sharp(clear=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.shade_smooth()


def _legacy_auto_smooth():
    """True on Blender 3.6, where auto smooth is a mesh setting (4.1+ replaced it with a modifier)."""
    return "use_auto_smooth" in bpy.types.Mesh.bl_rna.properties


def set_auto_smooth(context, objects, angle):
    """Blender's own Object > Shade Auto Smooth, so the result matches the menu entry exactly."""
    select_only(context, objects)
    if _legacy_auto_smooth():
        # 3.6: Shade Auto Smooth is Shade Smooth with the mesh's auto smooth turned on.
        bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=angle)
    else:
        # 4.1+: adds (or updates) the "Smooth by Angle" modifier.
        bpy.ops.object.shade_auto_smooth(angle=angle)


def keep_imported_normals(objects):
    """Blender 3.6 only: stop auto smooth's angle from re-splitting the imported normals.

    3.6's FBX importer turns auto smooth on by itself (custom normals need it) at
    the default 30 deg, which facets smooth low-poly surfaces coming from Max.
    At 180 deg shading is left to the imported normals and sharp edges, which is
    what 4.1+ does when no Smooth by Angle modifier is added.
    """
    if not _legacy_auto_smooth():
        return
    for obj in objects:
        if obj.data.use_auto_smooth:
            obj.data.auto_smooth_angle = math.pi


# Blender's rename-on-collision suffix: "Material" -> "Material.001", "Material.002"...
_DUPLICATE_SUFFIX = re.compile(r"^(?P<base>.+)\.\d{3,}$")


def merge_duplicate_materials(new_materials):
    """Fold 'name.001'-style copies an import just created back into an existing 'name'.

    Only materials the import created are touched -- anything already in the file,
    a deliberate 'name.001' included, is left alone. Returns how many were merged.
    """
    merged = 0
    for material in new_materials:
        match = _DUPLICATE_SUFFIX.match(material.name)
        if not match:
            continue
        original = bpy.data.materials.get(match.group("base"))
        if original is None or original == material:
            continue
        material.user_remap(original)
        bpy.data.materials.remove(material)
        merged += 1
    return merged


def post_process_imported_objects(context, objects):
    gs_props = context.scene.gs_file_transfer_props
    meshes = [obj for obj in objects if obj.type == 'MESH']
    if gs_props.clear_normals and meshes:
        clear_normals_from_objects(context, meshes)
        print(f"Cleared normals and sharp edges from {len(meshes)} mesh objects")
    if meshes:
        if gs_props.set_auto_smooth:
            set_auto_smooth(context, meshes, gs_props.smooth_angle)
        else:
            keep_imported_normals(meshes)
    # The steps above leave only the last mesh selected; put the whole import
    # back, both for the artist and because transform_apply works on the selection.
    select_only(context, objects)
    if FBXSettings.TRANSFORM['apply_transform_on_import'] and objects:
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


# ---------------------------------------------------------------------------
# Export: 3ds Max smoothing groups
# ---------------------------------------------------------------------------
def fbx_supports_smoothing_groups():
    """True when this Blender's FBX exporter can write 3ds Max smoothing groups.

    The 'SMOOTH_GROUP' smoothing mode exists in 4.5 and 5.2 but not in 3.6, whose
    exporter only offers normals / face / edge smoothing.
    """
    try:
        prop = bpy.ops.export_scene.fbx.get_rna_type().properties["mesh_smooth_type"]
    except (AttributeError, KeyError, RuntimeError):
        return False
    return "SMOOTH_GROUP" in prop.enum_items.keys()


# Sharp-edge fill tuning. Angles are the dihedral angle between an edge's two faces.
_FOLLOW_CREASE = 0.35     # ~20 deg: a fold this strong is always the way to go
_FALLBACK_CREASE = 0.26   # ~15 deg: a weaker fold, taken only when no edge loop carries on straight
_MIN_STRAIGHTNESS = 0.2   # cosine between incoming and outgoing direction to count as "straight on"
_MAX_WALK = 1000          # safety cap on edges added from a single dead end


def _smooth_inside(edge):
    """A plain two-face edge that smoothing flows across."""
    faces = edge.link_faces
    return len(faces) == 2 and edge.smooth and faces[0].smooth and faces[1].smooth


def _splits_smoothing(edge):
    """Marked sharp, on a border, non-manifold, or beside a flat face. Loose wire edges don't count."""
    return len(edge.link_faces) > 0 and not _smooth_inside(edge)


def _next_sharp_edge(vert, incoming, candidates):
    """Pick the edge that best continues the sharp line arriving at ``vert`` along ``incoming``."""
    crease_edge, crease = None, -1.0
    for edge in candidates:
        angle = edge.calc_face_angle()
        if angle > crease:
            crease_edge, crease = edge, angle
    if crease > _FOLLOW_CREASE:
        return crease_edge

    # No strong fold: carry on along the edge loop, skipping edges that share a
    # face with the incoming edge (those turn the corner instead of continuing).
    heading = vert.co - incoming.other_vert(vert).co
    if heading.length > 1e-6:
        heading.normalize()
        beside = {edge for face in incoming.link_faces for edge in face.edges}
        ahead = [edge for edge in candidates if edge not in beside] or candidates
        straight_edge, straightness = None, -2.0
        for edge in ahead:
            out = edge.other_vert(vert).co - vert.co
            if out.length > 1e-6:
                dot = heading.dot(out.normalized())
                if dot > straightness:
                    straight_edge, straightness = edge, dot
        if straightness > _MIN_STRAIGHTNESS:
            return straight_edge

    return crease_edge if crease >= _FALLBACK_CREASE else None


def find_sharp_fill_edges(mesh):
    """Indices of the edges the smoothing-group export would mark sharp on ``mesh``. ``mesh`` is not modified.

    A 3ds Max smoothing group is a region of faces, so a hard edge only survives
    the trip if it separates two regions. A sharp edge that stops mid-surface has
    the same region on both sides and comes out smooth in Max. Each such dead end
    is walked onward -- along a crease if there is one, otherwise straight along
    the edge loop -- until it meets another sharp edge or a border.
    """
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.index_update()
        bm.edges.index_update()

        # How many smoothing-splitting edges meet at each vertex; exactly one is a dead end.
        splits = [0] * len(bm.verts)
        for edge in bm.edges:
            if _splits_smoothing(edge):
                for vert in edge.verts:
                    splits[vert.index] += 1

        added = []
        dead_ends = deque(vert for vert in bm.verts if splits[vert.index] == 1)
        while dead_ends:
            vert = dead_ends.popleft()
            if splits[vert.index] != 1:
                continue  # already closed by an earlier walk
            incoming = next(edge for edge in vert.link_edges if _splits_smoothing(edge))
            for _ in range(_MAX_WALK):
                candidates = [edge for edge in vert.link_edges if _smooth_inside(edge)]
                edge = _next_sharp_edge(vert, incoming, candidates) if candidates else None
                if edge is None:
                    break
                edge.smooth = False  # BMesh copy only; the caller marks the real mesh
                added.append(edge.index)
                for end in edge.verts:
                    splits[end.index] += 1
                vert, incoming = edge.other_vert(vert), edge
                if splits[vert.index] > 1:
                    break  # reached another hard edge or a border: the line is closed
        return added
    finally:
        bm.free()


def _sharp_fill_for_object(obj, depsgraph):
    """Edge indices into ``obj.data`` that close the object's dead-end sharp edges.

    Reads the evaluated mesh when its topology matches the base mesh, so sharp
    edges coming from modifiers such as Smooth by Angle count; otherwise
    (Mirror, Subdivision...) falls back to the base mesh.
    """
    mesh = obj.data
    obj_eval = obj.evaluated_get(depsgraph)
    evaluated = obj_eval.to_mesh()
    try:
        same_topology = (
            (len(evaluated.vertices), len(evaluated.edges), len(evaluated.polygons))
            == (len(mesh.vertices), len(mesh.edges), len(mesh.polygons))
        )
        return find_sharp_fill_edges(evaluated if same_topology else mesh)
    finally:
        obj_eval.to_mesh_clear()


@contextlib.contextmanager
def temporarily_filled_sharp_edges(context, objects, enabled=True):
    """Fill in open-ended sharp edges on ``objects`` for the duration of the block, then take it back out.

    Yields the number of edges added. The fill goes onto the real meshes so the
    FBX exporter (which evaluates modifiers itself) sees it, and is removed
    afterwards so the artist's scene is left exactly as it was.
    """
    filled = []  # (mesh, edge indices, whether the mesh already had a sharp_edge attribute)
    try:
        if enabled:
            depsgraph = context.evaluated_depsgraph_get()
            seen = set()
            for obj in objects:
                if obj.type != 'MESH' or obj.data in seen or obj.data.library is not None:
                    continue
                mesh = obj.data
                seen.add(mesh)
                indices = _sharp_fill_for_object(obj, depsgraph)
                if not indices:
                    continue
                filled.append((mesh, indices, "sharp_edge" in mesh.attributes))
                for index in indices:
                    mesh.edges[index].use_edge_sharp = True
                mesh.update()
        yield sum(len(indices) for _mesh, indices, _had in filled)
    finally:
        for mesh, indices, had_attribute in filled:
            for index in indices:
                mesh.edges[index].use_edge_sharp = False
            if not had_attribute:
                attribute = mesh.attributes.get("sharp_edge")
                if attribute is not None:
                    try:
                        mesh.attributes.remove(attribute)
                    except RuntimeError:
                        pass
            mesh.update()


# ---------------------------------------------------------------------------
# FBX calls
# ---------------------------------------------------------------------------
def import_fbx_with_settings(filepath, context):
    bpy.ops.import_scene.fbx(
        filepath=filepath,
        global_scale=calculate_import_scale(context),
        **FBXSettings.IMPORT,
    )


def export_fbx_with_settings(filepath, context, target_app):
    """Export the selection for ``target_app``. Returns how many sharp edges were filled in."""
    gs_props = context.scene.gs_file_transfer_props
    settings = dict(FBXSettings.EXPORT)
    if gs_props.export_mesh_only:
        # Selected empties are skipped and meshes under them come out in world space.
        settings['object_types'] = {'MESH'}
    smoothing_groups =(target_app == "max" and gs_props.export_smooth_groups
                        and fbx_supports_smoothing_groups())
    if smoothing_groups:
        settings['mesh_smooth_type'] = 'SMOOTH_GROUP'
    # Closing open-ended sharp edges is part of exporting smoothing groups, not
    # a separate choice: without it those hard edges silently come out soft in Max.
    with temporarily_filled_sharp_edges(context, list(context.selected_objects),
                                        enabled=smoothing_groups) as filled:
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            global_scale=calculate_export_scale(context),
            **settings,
        )
    return filled


def pre_process_export_objects(context):
    if FBXSettings.TRANSFORM['apply_transform_on_export']:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


# ---------------------------------------------------------------------------
# Transfer runners, shared by the local and server operators
# ---------------------------------------------------------------------------
def _import_one(op, context, path):
    """Import one FBX and post-process it. Returns merged-material count, or None on failure."""
    gs_props = context.scene.gs_file_transfer_props
    objects_before = set(context.scene.objects)
    materials_before = set(bpy.data.materials)
    print("Attempting to import: " + path)
    try:
        import_fbx_with_settings(path, context)
    except Exception as e:
        op.report({'ERROR'}, f"Failed to import {path}: {e}")
        return None

    merged = 0
    if gs_props.merge_materials:
        merged = merge_duplicate_materials([m for m in bpy.data.materials if m not in materials_before])

    imported = [obj for obj in context.scene.objects if obj not in objects_before]
    try:
        post_process_imported_objects(context, imported)
    except Exception as e:
        op.report({'WARNING'}, f"Imported {os.path.basename(path)}, but post-processing failed: {e}")
    return merged


def run_import(op, context, directory, stem):
    """Import '<stem>.fbx' (All) or every '<object>_<stem>.fbx' (Individual) from ``directory``."""
    gs_props = context.scene.gs_file_transfer_props
    ensure_object_mode(context)

    if gs_props.export_mode == "INDIVIDUAL":
        files = individual_files(directory, stem)
        if not files:
            op.report({'ERROR'}, f"No *_{stem}.fbx files found in {directory}")
            return {'CANCELLED'}
    else:
        path = os.path.join(directory, stem + ".fbx")
        if not os.path.isfile(path):
            op.report({'ERROR'}, f"File does not exist: {path}")
            return {'CANCELLED'}
        files = [path]

    imported, merged = 0, 0
    for path in files:
        result = _import_one(op, context, path)
        if result is not None:
            imported += 1
            merged += result
    if not imported:
        return {'CANCELLED'}

    message = f"Imported {imported} FBX file(s)" if len(files) > 1 else f"Imported {files[0]}"
    if merged:
        message += f", merged {merged} duplicate material(s)"
    op.report({'INFO'}, message)
    return {'FINISHED'}


def _export_one(op, context, path, target_app):
    """Export the current selection to ``path``. Returns filled-edge count, or None on failure."""
    print("Attempting to export to: " + path)
    try:
        pre_process_export_objects(context)
        return export_fbx_with_settings(path, context, target_app)
    except Exception as e:
        op.report({'ERROR'}, f"Failed to export to {path}: {e}")
        return None


def run_export(op, context, directory, stem, target_app):
    """Export the selection as '<stem>.fbx' (All) or one '<object>_<stem>.fbx' per mesh (Individual)."""
    gs_props = context.scene.gs_file_transfer_props
    ensure_object_mode(context)
    selected = list(context.selected_objects)
    meshes = [obj for obj in selected if obj.type == 'MESH']
    if not meshes:
        op.report({'WARNING'}, "Please select meshes to export!")
        return {'CANCELLED'}
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        op.report({'ERROR'}, f"Failed to create directory: {directory}")
        return {'CANCELLED'}

    if gs_props.export_mode == "INDIVIDUAL":
        # Clear out the previous per-object files of this same transfer, so the
        # receiver doesn't pick up objects from an older send. Other transfers'
        # files in the folder are left alone.
        for stale in individual_files(directory, stem):
            try:
                os.remove(stale)
            except OSError as e:
                print(f"Failed to delete {stale}. Reason: {e}")

        active = context.view_layer.objects.active
        exported, filled = 0, 0
        try:
            # Meshes only: a hierarchy can't span separate files, and a file
            # holding a lone empty would only clutter the receiver's scene.
            for obj in meshes:
                select_only(context, [obj])
                path = os.path.join(directory, f"{safe_file_name(obj.name)}_{stem}.fbx")
                result = _export_one(op, context, path, target_app)
                if result is None:
                    op.report({'WARNING'}, f"Failed to export {obj.name}")
                    continue
                exported += 1
                filled += result
        finally:
            select_only(context, selected)
            context.view_layer.objects.active = active
        message = f"Exported {exported} object(s) individually"
    else:
        path = os.path.join(directory, stem + ".fbx")
        filled = _export_one(op, context, path, target_app)
        if filled is None:
            return {'CANCELLED'}
        message = f"Exported to {path}"

    if filled:
        message += f" ({filled} open sharp edge(s) closed for 3ds Max smoothing groups)"
    op.report({'INFO'}, message)
    return {'FINISHED'}


def _local_dir(context):
    mode = context.scene.gs_file_transfer_props.export_mode
    return LOCAL_DIR_INDIVIDUAL if mode == "INDIVIDUAL" else LOCAL_DIR


# ---------------------------------------------------------------------------
# Person list (shared scene collection, the search source for the User field)
# ---------------------------------------------------------------------------
class GS_PersonItem(bpy.types.PropertyGroup):
    name: StringProperty()


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------
class IMPORT_OT_from_application(Operator):
    bl_idname = "gs.import_from_application"
    bl_label = "Import"
    bl_description = "Import what another application exported on this machine"
    bl_options = {'UNDO'}

    source_app: StringProperty(default="")

    @classmethod
    def description(cls, context, properties):
        label = APP_LABELS.get(properties.source_app, "another application")
        stem = transfer_stem(properties.source_app, THIS_APP)
        return f"Import what {label} last exported on this machine ({stem}.fbx)"

    def execute(self, context):
        if self.source_app not in APP_LABELS:
            self.report({'ERROR'}, "Invalid source application")
            return {'CANCELLED'}
        return run_import(self, context, _local_dir(context), transfer_stem(self.source_app, THIS_APP))


class EXPORT_OT_to_application(Operator):
    bl_idname = "gs.export_to_application"
    bl_label = "Export"
    bl_description = "Export the selection for another application on this machine"
    bl_options = {'UNDO'}

    target_app: StringProperty(default="")

    @classmethod
    def description(cls, context, properties):
        label = APP_LABELS.get(properties.target_app, "another application")
        stem = transfer_stem(THIS_APP, properties.target_app)
        return f"Export the selection for {label} to import on this machine ({stem}.fbx)"

    def execute(self, context):
        if self.target_app not in APP_LABELS:
            self.report({'ERROR'}, "Invalid target application")
            return {'CANCELLED'}
        return run_export(self, context, _local_dir(context),
                          transfer_stem(THIS_APP, self.target_app), self.target_app)


def _server_user_or_report(op, gs_props):
    other = gs_props.server_user.strip()
    if not other:
        op.report({'ERROR'}, "Pick a user first")
    return other


class _NeedsServer:
    """Mixin: the operator is unavailable until the share has been found reachable."""

    @classmethod
    def poll(cls, context):
        if ServerStatus.online:
            return True
        cls.poll_message_set("Still checking the server" if ServerStatus.online is None
                             else "Can't reach the server")
        return False


class IMPORT_OT_from_server(_NeedsServer, Operator):
    bl_idname = "gs.import_from_server"
    bl_label = "Import from Server"
    bl_description = "Import what the selected user sent you"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        gs_props = context.scene.gs_file_transfer_props
        other = gs_props.server_user or "the selected user"
        return f"Import what {other} sent you from {APP_LABELS[gs_props.server_app]}"

    def execute(self, context):
        gs_props = context.scene.gs_file_transfer_props
        other = _server_user_or_report(self, gs_props)
        if not other:
            return {'CANCELLED'}
        # <sender>_<app>_to_blender_<me>.fbx, sitting in the sender's folder
        stem = f"{other}_{transfer_stem(gs_props.server_app, THIS_APP)}_{username}"
        return run_import(self, context, os.path.join(SERVER_DIR, other), stem)


class EXPORT_OT_to_server(_NeedsServer, Operator):
    bl_idname = "gs.export_to_server"
    bl_label = "Export to Server"
    bl_description = "Send the selection to the selected user"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        gs_props = context.scene.gs_file_transfer_props
        other = gs_props.server_user or "the selected user"
        return f"Send the selection to {other}, to import in {APP_LABELS[gs_props.server_app]}"

    def execute(self, context):
        gs_props = context.scene.gs_file_transfer_props
        other = _server_user_or_report(self, gs_props)
        if not other:
            return {'CANCELLED'}
        target_app = gs_props.server_app
        # <me>_blender_to_<app>_<receiver>.fbx, sitting in my own folder
        stem = f"{username}_{transfer_stem(THIS_APP, target_app)}_{other}"
        return run_export(self, context, os.path.join(SERVER_DIR, username), stem, target_app)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------
class GSFileTransferProperties(bpy.types.PropertyGroup):
    export_mode: EnumProperty(
        name="Mode",
        items=[
            ("MERGE", "Merge", "Transfer all selected objects as one FBX file"),
            ("INDIVIDUAL", "Individual", "Transfer each selected object as its own FBX file"),
        ],
        default="MERGE",
    )

    # --- Import ---
    clear_normals: BoolProperty(
        name="Clear Normal Data",
        description="Strip custom normals and sharp edges from imported meshes, "
                    "leaving plain smooth shading",
        default=False,
    )
    merge_materials: BoolProperty(
        name="Merge Materials",
        description="When the import duplicates a material because its name is taken "
                    "(Material.001, Material.002...), use the existing Material instead",
        default=True,
    )
    set_auto_smooth: BoolProperty(
        name="Set Auto Smooth",
        description="Run Blender's Shade Auto Smooth on imported meshes. "
                    "Off keeps the shading the FBX came with",
        default=False,
    )
    smooth_angle: FloatProperty(
        name="Angle",
        description="Maximum angle between face normals that will be considered as smooth",
        subtype='ANGLE',
        default=math.radians(30.0),
        min=0.0,
        max=math.pi,
    )

    # --- Export ---
    export_mesh_only: BoolProperty(
        name="Mesh Only",
        description="Export only the selected meshes, leaving out the empties (nulls) that "
                    "hold the hierarchy. Meshes keep their position in the world",
        default=False,
    )
    export_smooth_groups: BoolProperty(
        name="Export Smoothing Groups",
        description="When exporting to 3ds Max, turn your sharp edges into smoothing groups. "
                    "In Max, tick 'Import Smoothing Groups'. Needs Blender 4.5 or newer",
        default=True,
    )

    # --- Local / Server ---
    local_app: EnumProperty(
        name="Software",
        description="The application on this machine you are transferring with",
        items=APP_ITEMS,
        default="maya",
    )
    server_app: EnumProperty(
        name="Software",
        description="The application the other artist is using",
        items=APP_ITEMS,
        default="maya",
    )
    server_user: StringProperty(
        name="User",
        description="The artist you are sending to or receiving from. Click and type to search",
        default="",
    )


# ---------------------------------------------------------------------------
# Server status + user list
# ---------------------------------------------------------------------------
def _normalize_user(raw):
    """Turn a raw CSV user value into a bare studio username.

    The auto-deployment CSV writes entries like ``GLENDASTUDIO01\\son.ha.01`` and
    may append a status tag such as `` (locked)``. We want just ``son.ha.01``:
      * drop everything up to and including the last domain backslash, and
      * strip any trailing parenthesised status tag.
    """
    if not raw:
        return ""
    name = raw.strip()
    # Drop the domain prefix (everything through the last backslash).
    name = name.rsplit("\\", 1)[-1]
    # Remove a trailing status tag like "(locked)".
    paren = name.find("(")
    if paren != -1:
        name = name[:paren]
    return name.strip()


def _read_users(csv_path):
    """Usernames from one deployment CSV: any column order, header 'User' (or 'Users')."""
    # utf-8-sig: the Update CSV starts with a BOM.
    with open(csv_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader, None)
        if header is None:
            raise ValueError("CSV file is empty")
        column = next((i for i, name in enumerate(header) if name.strip().lower() in ("user", "users")), None)
        if column is None:
            raise ValueError("No 'User' column found in CSV file")
        return [_normalize_user(row[column]) for row in reader if len(row) > column]


def read_user_list():
    """Every user from all USER_CSVS, de-duplicated and sorted. An unreadable file is skipped."""
    users = {}
    for path in USER_CSVS:
        try:
            for name in _read_users(path):
                if name:
                    users.setdefault(name.lower(), name)
        except Exception as e:
            print(f"Error reading user list from {path}: {e}")
    names = sorted(users.values(), key=str.lower)
    print(f"Loaded {len(names)} users from {len(USER_CSVS)} CSV files")
    return names


class ServerStatus:
    """Whether the share is reachable, and the user list read from it.

    The check runs on a worker thread: an unreachable UNC path can block for tens
    of seconds, and Blender must not freeze while it does. The result is applied
    on the main thread by a timer, because bpy data can't be touched from another
    thread. ``online`` is None while a check is running.
    """
    online = None
    users = []
    _thread = None
    _result = {}

    @classmethod
    def check(cls):
        if cls._thread is not None and cls._thread.is_alive():
            return
        cls.online = None
        cls._result = {}
        cls._thread = threading.Thread(target=cls._probe, args=(cls._result,), daemon=True)
        cls._thread.start()
        if not bpy.app.timers.is_registered(_apply_server_check):
            bpy.app.timers.register(_apply_server_check, first_interval=0.2, persistent=True)

    @staticmethod
    def _probe(result):
        # Worker thread: file system only, never bpy.
        result["online"] = os.path.isdir(SERVER_DIR)
        result["users"] = read_user_list()


def fill_user_lists():
    """Copy the known users into the window manager list that the User search reads."""
    for wm in bpy.data.window_managers:
        people = wm.gs_person_list
        people.clear()
        for name in ServerStatus.users:
            people.add().name = name


def _redraw_view3d():
    wm = bpy.context.window_manager
    if wm is None:
        return
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def _apply_server_check():
    if ServerStatus._thread.is_alive():
        return 0.2
    ServerStatus.online = ServerStatus._result.get("online", False)
    ServerStatus.users = ServerStatus._result.get("users", [])
    if not ServerStatus.online:
        print(f"GS File Transfer: can't reach {SERVER_DIR}, Server section disabled")
    fill_user_lists()
    _redraw_view3d()
    return None


@bpy.app.handlers.persistent
def load_handler(_dummy):
    fill_user_lists()     # a newly opened file starts with an empty list
    ServerStatus.check()  # and the server may have come (or gone) since


class GS_OT_check_server(Operator):
    bl_idname = "gs.check_server"
    bl_label = "Check Server"
    bl_description = "Check the server connection again and reload the user list"

    def execute(self, context):
        ServerStatus.check()
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Draw (called by the GS Pipeline menu framework under File I/O > GS File Transfer)
# ---------------------------------------------------------------------------
def _draw_settings(layout, gs_props):
    box = layout.box()
    mode_row = box.split(factor=0.3)
    mode_row.label(text="Mode")
    mode_row.row(align=True).prop(gs_props, "export_mode", expand=True)

    columns = box.split(factor=0.5)
    import_col = columns.column()
    import_col.label(text="Import", icon='IMPORT')
    import_col.prop(gs_props, "clear_normals")
    import_col.prop(gs_props, "merge_materials")
    import_col.prop(gs_props, "set_auto_smooth")
    angle_row = import_col.row()
    angle_row.enabled = gs_props.set_auto_smooth
    angle_row.prop(gs_props, "smooth_angle")

    export_col = columns.column()
    export_col.label(text="Export", icon='EXPORT')
    export_col.prop(gs_props, "export_mesh_only")
    smoothing = export_col.row()
    smoothing.enabled = fbx_supports_smoothing_groups()  # greyed out in Blender 3.6
    smoothing.prop(gs_props, "export_smooth_groups")


def _draw_transfer_buttons(layout, import_op, export_op):
    row = layout.row()
    row.scale_y = 1.3
    imp = row.operator(import_op, text="Import", icon='IMPORT')
    exp = row.operator(export_op, text="Export", icon='EXPORT')
    return imp, exp


def draw_file_transfer(layout, context):
    scene = context.scene
    gs_props = scene.gs_file_transfer_props

    _draw_settings(layout, gs_props)

    local = layout.box()
    local.label(text="Local", icon='HOME')
    local.prop(gs_props, "local_app")
    imp, exp = _draw_transfer_buttons(local, "gs.import_from_application", "gs.export_to_application")
    imp.source_app = gs_props.local_app
    exp.target_app = gs_props.local_app

    server = layout.box()
    header = server.row()
    header.label(text="Server", icon='WORLD')
    header.operator("gs.check_server", text="", icon='FILE_REFRESH', emboss=False)
    online = ServerStatus.online
    if online is None:
        server.label(text="Checking the server...", icon='TIME')
    elif not online:
        server.label(text="Can't reach the server", icon='ERROR')

    body = server.column()
    body.enabled = bool(online)
    people = context.window_manager.gs_person_list
    body.prop_search(gs_props, "server_user", context.window_manager, "gs_person_list", icon='USER')
    if online and len(people) == 0:
        body.label(text="User list unavailable", icon='ERROR')
    body.prop(gs_props, "server_app")
    _draw_transfer_buttons(body, "gs.import_from_server", "gs.export_to_server")

    layout.label(text="Current User: " + username)


# ---------------------------------------------------------------------------
# Group descriptor (consumed by file_io/__init__.py)
# ---------------------------------------------------------------------------
GROUP = {
    "id": "GS_FILE_TRANSFER",
    "label": "GS File Transfer",
    "tabs": [
        {"label": "GS File Transfer", "draw": draw_file_transfer},
    ],
}

CLASSES = (
    GS_PersonItem,
    IMPORT_OT_from_application,
    EXPORT_OT_to_application,
    IMPORT_OT_from_server,
    EXPORT_OT_to_server,
    GS_OT_check_server,
    GSFileTransferProperties,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gs_file_transfer_props = bpy.props.PointerProperty(type=GSFileTransferProperties)
    # Runtime-only (window manager data isn't saved), shared by every scene.
    bpy.types.WindowManager.gs_person_list = bpy.props.CollectionProperty(type=GS_PersonItem)
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)
    ServerStatus.check()


def unregister():
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    if bpy.app.timers.is_registered(_apply_server_check):
        bpy.app.timers.unregister(_apply_server_check)
    if hasattr(bpy.types.WindowManager, "gs_person_list"):
        del bpy.types.WindowManager.gs_person_list
    if hasattr(bpy.types.Scene, "gs_file_transfer_props"):
        del bpy.types.Scene.gs_file_transfer_props
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
