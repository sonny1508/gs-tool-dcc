"""GS File Transfer tool, integrated into the GS Pipeline 'File I/O' category.

Ported verbatim (logic-wise) from the standalone GS_File_Transfer addon, with the
panel ``draw`` body extracted into ``draw_file_transfer`` so the GS Pipeline menu
framework can render it under File I/O > GS File Transfer. Operators, properties,
the person list and the persistent load handler are unchanged.
"""
from __future__ import annotations

import csv
import getpass
import math
import os
import shutil
import tempfile

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy.types import Operator

# ===== GLOBAL FBX SETTINGS CONFIGURATION =====
username = getpass.getuser()
temp_dir = tempfile.gettempdir()


class FBXSettings:
    """Centralized FBX import/export settings configuration"""

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
        'object_types': {'MESH'},
        'use_mesh_modifiers': True,
        'use_mesh_modifiers_render': True,
        'mesh_smooth_type': 'OFF',
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


def safe_path(path):
    return path.replace('\\', '/')


def clean_directory(directory_path):
    if os.path.exists(directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')


def clear_normals_from_objects(objects):
    for obj in objects:
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
            bpy.ops.mesh.mark_sharp(clear=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()


def apply_auto_smooth_to_objects(objects, angle_degrees):
    """Apply auto smooth to a list of mesh objects (version-compatible)."""
    for obj in objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        # Blender 4.1+ removed mesh.use_auto_smooth / auto_smooth_angle.
        if hasattr(mesh, "use_auto_smooth"):
            mesh.use_auto_smooth = True
            mesh.auto_smooth_angle = math.radians(angle_degrees)
        else:
            # 4.1+ : emulate via the Smooth by Angle operator on the active object.
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            try:
                bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_degrees))
            except Exception:
                bpy.ops.object.shade_smooth()


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


def import_fbx_with_settings(filepath, context):
    scale_factor = calculate_import_scale(context)
    bpy.ops.import_scene.fbx(
        filepath=filepath,
        global_scale=scale_factor,
        use_custom_normals=FBXSettings.IMPORT['use_custom_normals'],
        use_image_search=FBXSettings.IMPORT['use_image_search'],
        use_alpha_decals=FBXSettings.IMPORT['use_alpha_decals'],
        decal_offset=FBXSettings.IMPORT['decal_offset'],
        use_anim=FBXSettings.IMPORT['use_anim'],
        anim_offset=FBXSettings.IMPORT['anim_offset'],
        use_subsurf=FBXSettings.IMPORT['use_subsurf'],
        use_custom_props=FBXSettings.IMPORT['use_custom_props'],
        use_custom_props_enum_as_string=FBXSettings.IMPORT['use_custom_props_enum_as_string'],
        ignore_leaf_bones=FBXSettings.IMPORT['ignore_leaf_bones'],
        force_connect_children=FBXSettings.IMPORT['force_connect_children'],
        automatic_bone_orientation=FBXSettings.IMPORT['automatic_bone_orientation'],
        primary_bone_axis=FBXSettings.IMPORT['primary_bone_axis'],
        secondary_bone_axis=FBXSettings.IMPORT['secondary_bone_axis'],
    )


def export_fbx_with_settings(filepath, context):
    scale_factor = calculate_export_scale(context)
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=FBXSettings.EXPORT['use_selection'],
        use_active_collection=FBXSettings.EXPORT['use_active_collection'],
        global_scale=scale_factor,
        apply_unit_scale=FBXSettings.EXPORT['apply_unit_scale'],
        apply_scale_options=FBXSettings.EXPORT['apply_scale_options'],
        use_space_transform=FBXSettings.EXPORT['use_space_transform'],
        bake_space_transform=FBXSettings.EXPORT['bake_space_transform'],
        object_types=FBXSettings.EXPORT['object_types'],
        use_mesh_modifiers=FBXSettings.EXPORT['use_mesh_modifiers'],
        use_mesh_modifiers_render=FBXSettings.EXPORT['use_mesh_modifiers_render'],
        mesh_smooth_type=FBXSettings.EXPORT['mesh_smooth_type'],
        use_subsurf=FBXSettings.EXPORT['use_subsurf'],
        use_mesh_edges=FBXSettings.EXPORT['use_mesh_edges'],
        use_tspace=FBXSettings.EXPORT['use_tspace'],
        use_custom_props=FBXSettings.EXPORT['use_custom_props'],
        add_leaf_bones=FBXSettings.EXPORT['add_leaf_bones'],
        primary_bone_axis=FBXSettings.EXPORT['primary_bone_axis'],
        secondary_bone_axis=FBXSettings.EXPORT['secondary_bone_axis'],
        use_armature_deform_only=FBXSettings.EXPORT['use_armature_deform_only'],
        armature_nodetype=FBXSettings.EXPORT['armature_nodetype'],
        bake_anim=FBXSettings.EXPORT['bake_anim'],
        bake_anim_use_all_bones=FBXSettings.EXPORT['bake_anim_use_all_bones'],
        bake_anim_use_nla_strips=FBXSettings.EXPORT['bake_anim_use_nla_strips'],
        bake_anim_use_all_actions=FBXSettings.EXPORT['bake_anim_use_all_actions'],
        bake_anim_force_startend_keying=FBXSettings.EXPORT['bake_anim_force_startend_keying'],
        bake_anim_step=FBXSettings.EXPORT['bake_anim_step'],
        bake_anim_simplify_factor=FBXSettings.EXPORT['bake_anim_simplify_factor'],
        path_mode=FBXSettings.EXPORT['path_mode'],
        embed_textures=FBXSettings.EXPORT['embed_textures'],
        batch_mode=FBXSettings.EXPORT['batch_mode'],
        use_batch_own_dir=FBXSettings.EXPORT['use_batch_own_dir'],
        use_metadata=FBXSettings.EXPORT['use_metadata'],
    )


def post_process_imported_objects(objects, context):
    gs_props = context.scene.gs_file_transfer_props
    if gs_props.clear_normals:
        clear_normals_from_objects(objects)
        print(f"Cleared normals and sharp edges from {len([o for o in objects if o.type == 'MESH'])} mesh objects")
    apply_auto_smooth_to_objects(objects, gs_props.auto_smooth_angle)
    print(f"Applied auto smooth ({gs_props.auto_smooth_angle}°) to {len([o for o in objects if o.type == 'MESH'])} mesh objects")
    if FBXSettings.TRANSFORM['apply_transform_on_import']:
        if len(bpy.context.selected_objects) != 0:
            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def pre_process_export_objects(context):
    if FBXSettings.TRANSFORM['apply_transform_on_export']:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


# ---------------------------------------------------------------------------
# Person list (shared scene collection)
# ---------------------------------------------------------------------------
class GS_PersonItem(bpy.types.PropertyGroup):
    name: StringProperty()


class GS_UL_PersonList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon="USER")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon="USER")


# ---------------------------------------------------------------------------
# Operators (unchanged logic)
# ---------------------------------------------------------------------------
class IMPORT_OT_from_application(Operator):
    bl_idname = "gs.import_from_application"
    bl_label = "Import"
    bl_description = "Import FBX from another application"

    source_app: StringProperty(default="")

    def execute(self, context):
        gs_props = context.scene.gs_file_transfer_props
        if gs_props.export_mode == "INDIVIDUAL":
            local_export_path = os.path.join(temp_dir, "fileTransferFbxIndividual\\")
            if self.source_app == "maya":
                import_pattern = "maya_to_blender"
            elif self.source_app == "max":
                import_pattern = "max_to_blender"
            else:
                self.report({'ERROR'}, "Invalid source application")
                return {'CANCELLED'}
            if not os.path.exists(local_export_path):
                self.report({'ERROR'}, f"Directory does not exist: {local_export_path}")
                return {'CANCELLED'}
            fbx_files = [f for f in os.listdir(local_export_path) if f.endswith('.fbx') and import_pattern in f]
            if not fbx_files:
                self.report({'ERROR'}, f"No {import_pattern} FBX files found in {local_export_path}")
                return {'CANCELLED'}
            imported_count = 0
            for fbx_file in fbx_files:
                import_file = os.path.join(local_export_path, fbx_file)
                if self.import_single_fbx(context, import_file):
                    imported_count += 1
            self.report({'INFO'}, f"Successfully imported {imported_count} FBX file(s)")
            return {'FINISHED'}
        else:
            local_export_path = os.path.join(temp_dir, "fileTransferFbx\\")
            if self.source_app == "maya":
                import_file = os.path.join(local_export_path, "maya_to_blender.fbx")
            elif self.source_app == "max":
                import_file = os.path.join(local_export_path, "max_to_blender.fbx")
            else:
                self.report({'ERROR'}, "Invalid source application")
                return {'CANCELLED'}
            if os.path.exists(import_file):
                if self.import_single_fbx(context, import_file):
                    self.report({'INFO'}, f"Successfully imported from {import_file}")
                    return {'FINISHED'}
                return {'CANCELLED'}
            self.report({'ERROR'}, f"File does not exist: {import_file}")
            return {'CANCELLED'}

    def import_single_fbx(self, context, import_file):
        try:
            print("Attempting to import: " + import_file)
            objects_before_import = set(bpy.context.scene.objects)
            import_fbx_with_settings(import_file, context)
            objects_after_import = set(bpy.context.scene.objects)
            imported_objects = list(objects_after_import - objects_before_import)
            post_process_imported_objects(imported_objects, context)
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import {import_file}: {str(e)}")
            return False


class EXPORT_OT_to_application(Operator):
    bl_idname = "gs.export_to_application"
    bl_label = "Export"
    bl_description = "Export FBX to another application"

    target_app: StringProperty(default="")

    def execute(self, context):
        gs_props = context.scene.gs_file_transfer_props
        if not context.selected_objects:
            self.report({'WARNING'}, "Please select objects to export!")
            return {'CANCELLED'}
        if gs_props.export_mode == "INDIVIDUAL":
            local_export_path = os.path.join(temp_dir, "fileTransferFbxIndividual\\")
            clean_directory(local_export_path)
            if not os.path.exists(local_export_path):
                try:
                    os.makedirs(local_export_path)
                    print("Created directory: " + local_export_path)
                except Exception:
                    self.report({'ERROR'}, f"Failed to create directory: {local_export_path}")
                    return {'CANCELLED'}
            selected_objects = context.selected_objects.copy()
            exported_count = 0
            for obj in selected_objects:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                safe_obj_name = "".join(c for c in obj.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                export_file = os.path.join(local_export_path, f"{safe_obj_name}_blender_to_{self.target_app}.fbx")
                if self.export_single_fbx(context, export_file):
                    exported_count += 1
                    print(f"Exported: {export_file}")
                else:
                    self.report({'WARNING'}, f"Failed to export {obj.name}")
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objects:
                obj.select_set(True)
            if selected_objects:
                context.view_layer.objects.active = selected_objects[0]
            self.report({'INFO'}, f"Successfully exported {exported_count} object(s) individually")
            return {'FINISHED'}
        else:
            local_export_path = os.path.join(temp_dir, "fileTransferFbx\\")
            if not os.path.exists(local_export_path):
                try:
                    os.makedirs(local_export_path)
                    print("Created directory: " + local_export_path)
                except Exception:
                    self.report({'ERROR'}, f"Failed to create directory: {local_export_path}")
                    return {'CANCELLED'}
            if self.target_app == "maya":
                export_file = os.path.join(local_export_path, "blender_to_maya.fbx")
            elif self.target_app == "max":
                export_file = os.path.join(local_export_path, "blender_to_max.fbx")
            else:
                self.report({'ERROR'}, "Invalid target application")
                return {'CANCELLED'}
            if self.export_single_fbx(context, export_file):
                self.report({'INFO'}, f"Successfully exported to {export_file}")
                return {'FINISHED'}
            return {'CANCELLED'}

    def export_single_fbx(self, context, export_file):
        try:
            print("Attempting to export to: " + export_file)
            pre_process_export_objects(context)
            export_fbx_with_settings(export_file, context)
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export to {export_file}: {str(e)}")
            return False


class IMPORT_OT_from_server(Operator):
    bl_idname = "gs.import_from_server"
    bl_label = "Import from Server"
    bl_description = "Import FBX from server"

    def execute(self, context):
        scene = context.scene
        gs_props = scene.gs_file_transfer_props
        if len(scene.gs_person_list) <= 0:
            populate_person_list(scene)
            if len(scene.gs_person_list) <= 0:
                self.report({'ERROR'}, "Failed to populate person list")
                return {'CANCELLED'}
        app1 = gs_props.server_target_app.lower()
        app2 = "blender"
        gs_folder = scene.gs_person_list[scene.gs_person_index].name
        if gs_props.export_mode == "INDIVIDUAL":
            server_path = "\\\\192.168.1.210\\Temp\\File_Transfer\\"
            server_dir = server_path + gs_folder + "\\"
            if not os.path.exists(server_dir):
                self.report({'ERROR'}, f"Server directory does not exist: {server_dir}")
                return {'CANCELLED'}
            import_pattern = f"{gs_folder}_{app1}_to_{app2}_{username}"
            fbx_files = [f for f in os.listdir(server_dir) if f.endswith('.fbx') and import_pattern in f]
            if not fbx_files:
                self.report({'ERROR'}, f"No {import_pattern} FBX files found in {server_dir}")
                return {'CANCELLED'}
            imported_count = 0
            for fbx_file in fbx_files:
                file_path = os.path.join(server_dir, fbx_file)
                if self.import_single_fbx_server(context, file_path):
                    imported_count += 1
            self.report({'INFO'}, f"Successfully imported {imported_count} FBX file(s) from server")
            return {'FINISHED'}
        else:
            server_path = "\\\\192.168.1.210\\Temp\\File_Transfer\\"
            file_path = server_path + gs_folder + "\\" + gs_folder + "_" + app1 + "_to_" + app2 + "_" + username + ".fbx"
            print("Attempting to import from server: " + file_path)
            if os.path.exists(file_path):
                if self.import_single_fbx_server(context, file_path):
                    self.report({'INFO'}, f"Successfully imported from {file_path}")
                    return {'FINISHED'}
                return {'CANCELLED'}
            self.report({'ERROR'}, f"File does not exist: {file_path}")
            return {'CANCELLED'}

    def import_single_fbx_server(self, context, file_path):
        try:
            print("Attempting to import from server: " + file_path)
            objects_before_import = set(bpy.context.scene.objects)
            import_fbx_with_settings(file_path, context)
            objects_after_import = set(bpy.context.scene.objects)
            imported_objects = list(objects_after_import - objects_before_import)
            post_process_imported_objects(imported_objects, context)
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import from server {file_path}: {str(e)}")
            return False


class EXPORT_OT_to_server(Operator):
    bl_idname = "gs.export_to_server"
    bl_label = "Export to Server"
    bl_description = "Export FBX to server"

    def execute(self, context):
        scene = context.scene
        gs_props = scene.gs_file_transfer_props
        if len(scene.gs_person_list) <= 0:
            populate_person_list(scene)
            if len(scene.gs_person_list) <= 0:
                self.report({'ERROR'}, "Failed to populate person list")
                return {'CANCELLED'}
        if not context.selected_objects:
            self.report({'WARNING'}, "Please select objects to export!")
            return {'CANCELLED'}
        app1 = "blender"
        app2 = gs_props.server_target_app.lower()
        gs_folder = scene.gs_person_list[scene.gs_person_index].name
        if gs_props.export_mode == "INDIVIDUAL":
            server_path = "\\\\192.168.1.210\\Temp\\File_Transfer\\"
            server_dir = server_path + username + "\\"
            if not os.path.exists(server_dir):
                try:
                    os.makedirs(server_dir)
                except Exception:
                    self.report({'ERROR'}, f"Failed to create directory: {server_dir}")
                    return {'CANCELLED'}
            selected_objects = context.selected_objects.copy()
            exported_count = 0
            for obj in selected_objects:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                safe_obj_name = "".join(c for c in obj.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                file_path = server_dir + safe_obj_name + "_" + username + "_" + app1 + "_to_" + app2 + "_" + gs_folder + ".fbx"
                if self.export_single_fbx_server(context, file_path):
                    exported_count += 1
                    print(f"Exported to server: {file_path}")
                else:
                    self.report({'WARNING'}, f"Failed to export {obj.name} to server")
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objects:
                obj.select_set(True)
            if selected_objects:
                context.view_layer.objects.active = selected_objects[0]
            self.report({'INFO'}, f"Successfully exported {exported_count} object(s) individually to server")
            return {'FINISHED'}
        else:
            server_path = "\\\\192.168.1.210\\Temp\\File_Transfer\\"
            file_path = server_path + username + "\\" + username + "_" + app1 + "_to_" + app2 + "_" + gs_folder + ".fbx"
            print("Attempting to export to server: " + file_path)
            dir_path = os.path.dirname(file_path)
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                except Exception:
                    self.report({'ERROR'}, f"Failed to create directory: {dir_path}")
                    return {'CANCELLED'}
            if self.export_single_fbx_server(context, file_path):
                self.report({'INFO'}, f"Successfully exported to {file_path}")
                return {'FINISHED'}
            return {'CANCELLED'}

    def export_single_fbx_server(self, context, file_path):
        try:
            pre_process_export_objects(context)
            export_fbx_with_settings(file_path, context)
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export to server {file_path}: {str(e)}")
            return False


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------
class GSFileTransferProperties(bpy.types.PropertyGroup):
    export_mode: EnumProperty(
        name="Export Mode",
        items=[
            ("ALL", "All", "Export all selected objects as one FBX file"),
            ("INDIVIDUAL", "Individual", "Export each selected object as separate FBX files"),
        ],
        default="ALL",
    )
    clear_normals: BoolProperty(
        name="Clear Normal",
        description="Clear all normal data and sharp edges from imported FBX files",
        default=False,
    )
    auto_smooth_angle: FloatProperty(
        name="Auto Smooth",
        description="Auto smooth angle for imported FBX files (in degrees)",
        default=180.0,
        min=0.0,
        max=180.0,
        step=1.0,
        precision=1,
    )
    server_target_app: EnumProperty(
        name="Target Software",
        items=[
            ("Blender", "Blender", ""),
            ("Maya", "Maya", ""),
            ("Max", "Max", ""),
        ],
        default="Maya",
    )


# ---------------------------------------------------------------------------
# Person list population + persistent handler
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


def populate_person_list(scene):
    """Populate the person list from the auto-deployment CSV (Host, User columns)."""
    scene.gs_person_list.clear()
    server_path = "\\\\192.168.1.210\\Pipeline\\Library\\Data\\Data_Computer_Auto.csv"
    try:
        with open(server_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header_row = next(reader, None)
            if header_row is None:
                raise ValueError("CSV file is empty")
            user_column_index = None
            for i, header in enumerate(header_row):
                if header.strip().lower() in ("user", "users"):
                    user_column_index = i
                    break
            if user_column_index is None:
                raise ValueError("No 'User' column found in CSV file")
            seen = set()
            for row in reader:
                if len(row) <= user_column_index:
                    continue
                user_name = _normalize_user(row[user_column_index])
                if user_name and user_name.lower() not in seen:
                    seen.add(user_name.lower())
                    item = scene.gs_person_list.add()
                    item.name = user_name
            print(f"Successfully loaded {len(scene.gs_person_list)} users from CSV")
    except Exception as e:
        print(f"Error reading user list from CSV: {e}")


@bpy.app.handlers.persistent
def load_handler(dummy):
    for scene in bpy.data.scenes:
        populate_person_list(scene)


def _populate_list_timer():
    for scene in bpy.data.scenes:
        if len(scene.gs_person_list) == 0:
            populate_person_list(scene)
    return None


# ---------------------------------------------------------------------------
# Draw (called by the GS Pipeline menu framework under File I/O > GS File Transfer)
# ---------------------------------------------------------------------------
def draw_file_transfer(layout, context):
    scene = context.scene
    gs_props = scene.gs_file_transfer_props

    mode_box = layout.box()
    mode_box.label(text="Mode")
    mode_row = mode_box.row()
    mode_row.prop(gs_props, "export_mode", expand=True)

    options_row = mode_box.row()
    split = options_row.split(factor=0.5)
    split.prop(gs_props, "clear_normals")
    auto_smooth_col = split.row()
    auto_smooth_col.label(text="Auto Smooth:")
    auto_smooth_col.prop(gs_props, "auto_smooth_angle", text="")

    layout.separator()

    box = layout.box()
    box.label(text="Local")
    row = box.row()
    col1 = row.column()
    col1.label(text="Maya")
    col1.operator("gs.import_from_application", text="Import").source_app = "maya"
    col1.operator("gs.export_to_application", text="Export").target_app = "maya"
    col2 = row.column()
    col2.label(text="Max")
    col2.operator("gs.import_from_application", text="Import").source_app = "max"
    col2.operator("gs.export_to_application", text="Export").target_app = "max"

    server_box = layout.box()
    server_box.label(text="Server")
    app_row = server_box.row()
    split = app_row.split(factor=0.5)
    split.label(text="Target Software:")
    split.prop(gs_props, "server_target_app", text="")
    person_row = server_box.row()
    person_row.template_list(
        "GS_UL_PersonList", "server_person_list",
        scene, "gs_person_list",
        scene, "gs_person_index",
        rows=8,
        type='DEFAULT',
    )
    button_row = server_box.row()
    button_row.operator("gs.import_from_server", text="Import")
    button_row.operator("gs.export_to_server", text="Export")

    user_row = layout.row()
    user_row.label(text="Current User: " + username)


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
    GS_UL_PersonList,
    IMPORT_OT_from_application,
    EXPORT_OT_to_application,
    IMPORT_OT_from_server,
    EXPORT_OT_to_server,
    GSFileTransferProperties,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gs_file_transfer_props = bpy.props.PointerProperty(type=GSFileTransferProperties)
    bpy.types.Scene.gs_person_list = bpy.props.CollectionProperty(type=GS_PersonItem)
    bpy.types.Scene.gs_person_index = bpy.props.IntProperty(default=0)
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)
    try:
        bpy.app.timers.register(_populate_list_timer, first_interval=1.0)
    except Exception:
        pass


def unregister():
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    for attr in ("gs_person_list", "gs_person_index", "gs_file_transfer_props"):
        if hasattr(bpy.types.Scene, attr):
            delattr(bpy.types.Scene, attr)
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
