"""GS File Transfer: FBX import / export with the studio settings, and the
runners the Local and Server buttons share."""
from __future__ import annotations

import math
import os

import bpy

from ...common import (
    ensure_object_mode,
    legacy_auto_smooth,
    merge_duplicate_materials,
    select_only,
    set_auto_smooth,
)
from .config import (INDIVIDUAL_MODE, LOCAL_DIR, LOCAL_DIR_INDIVIDUAL, LOCAL_STEM, FBXSettings,
                     safe_file_name)
from .smoothing_groups import fbx_supports_smoothing_groups, temporarily_filled_sharp_edges


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def individual_mode(context):
    """True when transfers go one FBX per mesh. Always False while the mode is shelved."""
    return INDIVIDUAL_MODE and context.scene.gs_file_transfer_props.export_mode == "INDIVIDUAL"


def individual_name(object_name, stem):
    """'<object>_<stem>.fbx', or plain '<object>.fbx' when ``stem`` is empty (local)."""
    name = safe_file_name(object_name)
    return f"{name}_{stem}.fbx" if stem else f"{name}.fbx"


def individual_pattern(stem):
    return f"*_{stem}.fbx" if stem else "*.fbx"


def individual_files(directory, stem):
    """Every '<object>_<stem>.fbx' in ``directory`` -- the per-object files of one transfer.

    With an empty ``stem`` the folder holds only one transfer (local), so that's every FBX in it.
    """
    suffix = f"_{stem}.fbx".lower() if stem else ".fbx"
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return []
    return [os.path.join(directory, name) for name in names if name.lower().endswith(suffix)]


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


def keep_imported_normals(objects):
    """Blender 3.6 only: stop auto smooth's angle from re-splitting the imported normals.

    3.6's FBX importer turns auto smooth on by itself (custom normals need it) at
    the default 30 deg, which facets smooth low-poly surfaces coming from Max.
    At 180 deg shading is left to the imported normals and sharp edges, which is
    what 4.1+ does when no Smooth by Angle modifier is added.
    """
    if not legacy_auto_smooth():
        return
    for obj in objects:
        if obj.data.use_auto_smooth:
            obj.data.auto_smooth_angle = math.pi


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
# FBX calls
# ---------------------------------------------------------------------------
def import_fbx_with_settings(filepath, context):
    bpy.ops.import_scene.fbx(
        filepath=filepath,
        global_scale=calculate_import_scale(context),
        **FBXSettings.IMPORT,
    )


def export_fbx_with_settings(filepath, context):
    """Export the selection. Returns how many sharp edges were filled in.

    The receiving application isn't known (transfer files are plain FBX), so the
    Smoothing Groups (3ds Max) toggle, off by default, alone decides whether 3ds Max smoothing groups go out.
    """
    gs_props = context.scene.gs_file_transfer_props
    settings = dict(FBXSettings.EXPORT)
    if gs_props.export_mesh_only:
        # Selected empties are skipped and meshes under them come out in world space.
        settings['object_types'] = {'MESH'}
    smoothing_groups = gs_props.export_smooth_groups and fbx_supports_smoothing_groups()
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
    ensure_object_mode(context)

    if individual_mode(context):
        files = individual_files(directory, stem)
        if not files:
            op.report({'ERROR'}, f"No {individual_pattern(stem)} files found in {directory}")
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


def _export_one(op, context, path):
    """Export the current selection to ``path``. Returns filled-edge count, or None on failure."""
    print("Attempting to export to: " + path)
    try:
        pre_process_export_objects(context)
        return export_fbx_with_settings(path, context)
    except Exception as e:
        op.report({'ERROR'}, f"Failed to export to {path}: {e}")
        return None


def run_export(op, context, directory, stem):
    """Export the selection as '<stem>.fbx' (All) or one '<object>_<stem>.fbx' per mesh (Individual)."""
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

    if individual_mode(context):
        # Clear out the previous per-object files of this same transfer, so the
        # receiver doesn't pick up objects from an older send. Other transfers'
        # files in a shared server folder are left alone; the local individual
        # folder holds only this one transfer, so it is emptied.
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
                path = os.path.join(directory, individual_name(obj.name, stem))
                result = _export_one(op, context, path)
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
        filled = _export_one(op, context, path)
        if filled is None:
            return {'CANCELLED'}
        message = f"Exported to {path}"

    if filled:
        message += f" ({filled} open sharp edge(s) closed for 3ds Max smoothing groups)"
    op.report({'INFO'}, message)
    return {'FINISHED'}


def local_location(context):
    """(folder, stem) of the local transfer: 'transfer.fbx' in LOCAL_DIR in Merge mode, or
    every '<object>.fbx' in LOCAL_DIR_INDIVIDUAL in Individual mode."""
    if individual_mode(context):
        return LOCAL_DIR_INDIVIDUAL, ""
    return LOCAL_DIR, LOCAL_STEM
