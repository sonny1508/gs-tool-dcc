"""
GS File Transfer
This add-on provides tools for transferring files between Blender, Maya and 3ds Max.
"""

bl_info = {
    "name": "GS File Transfer",
    "author": "Sonny",
    "version": (1, 4), # fixed temp directory, changed to global variable so that it works for the current user
    "blender": (3, 6, 10),
    "location": "View3D > Sidebar > GS Tools",
    "description": "Tool for transferring files between Blender, Maya and 3ds Max",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

import bpy
import os
import socket
import getpass
import shutil
import math
import tempfile
from bpy.props import StringProperty, EnumProperty, BoolProperty, FloatProperty
from bpy.types import Panel, Operator

# ===== GLOBAL FBX SETTINGS CONFIGURATION =====
# Edit these settings to control all FBX import/export behavior

username = getpass.getuser()
temp_dir = tempfile.gettempdir()

class FBXSettings:
    """Centralized FBX import/export settings configuration"""
    
    # ===== IMPORT SETTINGS =====
    IMPORT = {
        # Basic Import Settings
        'use_custom_normals': True,
        'use_image_search': True,
        'use_alpha_decals': False,
        'decal_offset': 0.0,
        
        # Animation Settings
        'use_anim': True,
        'anim_offset': 1.0,
        
        # Mesh Settings
        'use_subsurf': False,
        
        # Custom Properties
        'use_custom_props': True,
        'use_custom_props_enum_as_string': True,
        
        # Armature Settings
        'ignore_leaf_bones': False,
        'force_connect_children': False,
        'automatic_bone_orientation': False,
        'primary_bone_axis': 'Y',
        'secondary_bone_axis': 'X',
    }
    
    # ===== EXPORT SETTINGS =====
    EXPORT = {
        # Selection Settings
        'use_selection': True,
        # 'use_visible': False,
        'use_active_collection': False,
        
        # Scale and Transform Settings
        'apply_unit_scale': True,
        'apply_scale_options': 'FBX_SCALE_ALL',
        'use_space_transform': True,
        'bake_space_transform': False,
        
        # Object Types (as set for enum flag)
        'object_types': {'MESH'},
        
        # Mesh Settings
        'use_mesh_modifiers': True,
        'use_mesh_modifiers_render': True,
        'mesh_smooth_type': 'OFF',
        'use_subsurf': False,
        'use_mesh_edges': False,
        'use_tspace': False,
        # 'use_triangles': False,
        
        # Custom Properties
        'use_custom_props': False,
        
        # Armature Settings
        'add_leaf_bones': True,
        'primary_bone_axis': 'Y',
        'secondary_bone_axis': 'X',
        'use_armature_deform_only': False,
        'armature_nodetype': 'NULL',
        
        # Animation Settings
        'bake_anim': False,
        'bake_anim_use_all_bones': True,
        'bake_anim_use_nla_strips': True,
        'bake_anim_use_all_actions': True,
        'bake_anim_force_startend_keying': True,
        'bake_anim_step': 1.0,
        'bake_anim_simplify_factor': 1.0,
        
        # Path and Texture Settings
        'path_mode': 'AUTO',
        'embed_textures': False,
        
        # Batch Settings
        'batch_mode': 'OFF',
        'use_batch_own_dir': True,
        
        # Metadata
        'use_metadata': True,
    }
    
    # ===== SCALE SETTINGS =====
    SCALE = {
        # Auto-scale calculation based on scene units
        'use_auto_scale': True,
        
        # Manual scale factors (used when use_auto_scale = False)
        'manual_import_scale': 1.0,
        'manual_export_scale': 1.0,
    }
    
    # ===== TRANSFORM SETTINGS =====
    TRANSFORM = {
        # Apply transforms before/after import/export
        'apply_transform_on_import': True,   # Apply rotation and scale after import
        'apply_transform_on_export': True,   # Apply scale before export
    }

# ===== END OF GLOBAL SETTINGS CONFIGURATION =====

def safe_path(path):
    """Make a path safe for file operations."""
    normalized = path.replace('\\', '/')
    return normalized

def clean_directory(directory_path):
    """Clean all files in the specified directory."""
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
    """Clear custom normals and sharp edges from a list of mesh objects."""
    for obj in objects:
        if obj.type == 'MESH':
            # Set object as active and select it
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            
            # Enter edit mode to clear normals and sharp edges
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            
            # Clear custom normals
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
            
            # Clear all sharp edges (mark all edges as smooth)
            bpy.ops.mesh.mark_sharp(clear=False)
            
            # Return to object mode
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Set all faces to smooth shading
            bpy.ops.object.shade_smooth()

def apply_auto_smooth_to_objects(objects, angle_degrees):
    """Apply auto smooth to a list of mesh objects."""
    for obj in objects:
        if obj.type == 'MESH':
            # Enable auto smooth and set the angle
            obj.data.use_auto_smooth = True
            obj.data.auto_smooth_angle = math.radians(angle_degrees)

def calculate_import_scale(context):
    """Calculate the appropriate scale factor for import based on global settings"""
    if not FBXSettings.SCALE['use_auto_scale']:
        return FBXSettings.SCALE['manual_import_scale']
    
    # Auto scale based on scene unit settings
    scene_unit_settings = context.scene.unit_settings
    unit_scale = scene_unit_settings.scale_length
    return unit_scale / 1.0 if unit_scale > 0 else 1.0

def calculate_export_scale(context):
    """Calculate the appropriate scale factor for export based on global settings"""
    if not FBXSettings.SCALE['use_auto_scale']:
        return FBXSettings.SCALE['manual_export_scale']
    
    # Auto scale based on scene unit settings
    scene_unit_settings = context.scene.unit_settings
    unit_scale = scene_unit_settings.scale_length
    return 1.0 / unit_scale if unit_scale > 0 else 1.0

def import_fbx_with_settings(filepath, context):
    """Import FBX using global settings configuration"""
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
        secondary_bone_axis=FBXSettings.IMPORT['secondary_bone_axis']
    )

def export_fbx_with_settings(filepath, context):
    """Export FBX using global settings configuration"""
    scale_factor = calculate_export_scale(context)
    
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=FBXSettings.EXPORT['use_selection'],
        # use_visible=FBXSettings.EXPORT['use_visible'],
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
        # use_triangles=FBXSettings.EXPORT['use_triangles'],
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
        use_metadata=FBXSettings.EXPORT['use_metadata']
    )

def post_process_imported_objects(objects, context):
    """Apply post-processing to imported objects"""
    scene = context.scene
    gs_props = scene.gs_file_transfer_props
    
    # Clear normals and sharp edges if enabled by user
    if gs_props.clear_normals:
        clear_normals_from_objects(objects)
        print(f"Cleared normals and sharp edges from {len([obj for obj in objects if obj.type == 'MESH'])} mesh objects")
    
    # Apply auto smooth with user-specified angle
    apply_auto_smooth_to_objects(objects, gs_props.auto_smooth_angle)
    print(f"Applied auto smooth ({gs_props.auto_smooth_angle}°) to {len([obj for obj in objects if obj.type == 'MESH'])} mesh objects")
    
    # Apply transforms if enabled in global settings
    if FBXSettings.TRANSFORM['apply_transform_on_import']:
        if len(bpy.context.selected_objects) != 0:
            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

def pre_process_export_objects(context):
    """Apply pre-processing before export"""
    if FBXSettings.TRANSFORM['apply_transform_on_export']:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Custom property class for person items
class GS_PersonItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()

# List class for scrollable gs person list
class GS_UL_PersonList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon="USER")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon="USER")

# Import FBX operator
class IMPORT_OT_from_application(Operator):
    bl_idname = "gs.import_from_application"
    bl_label = "Import"
    bl_description = "Import FBX from another application"
    
    source_app: StringProperty(default="")
    
    def execute(self, context):
        scene = context.scene
        gs_props = scene.gs_file_transfer_props
        
        # Check export mode to determine which folder to import from
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
            
            # Find all matching FBX files
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
            # Original "All" mode behavior
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
                else:
                    return {'CANCELLED'}
            else:
                self.report({'ERROR'}, f"File does not exist: {import_file}")
                return {'CANCELLED'}
    
    def import_single_fbx(self, context, import_file):
        """Import a single FBX file using global settings"""
        try:
            print("Attempting to import: " + import_file)
            
            # Store currently selected objects to know what was imported
            objects_before_import = set(bpy.context.scene.objects)
            
            # Import FBX using global settings
            import_fbx_with_settings(import_file, context)
            
            # Get newly imported objects
            objects_after_import = set(bpy.context.scene.objects)
            imported_objects = list(objects_after_import - objects_before_import)
            
            # Apply post-processing
            post_process_imported_objects(imported_objects, context)
            
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import {import_file}: {str(e)}")
            return False

# Export FBX operator
class EXPORT_OT_to_application(Operator):
    bl_idname = "gs.export_to_application"
    bl_label = "Export"
    bl_description = "Export FBX to another application"
    
    target_app: StringProperty(default="")
    
    def execute(self, context):
        scene = context.scene
        gs_props = scene.gs_file_transfer_props
        
        # Check if any objects are selected
        if not context.selected_objects:
            self.report({'WARNING'}, "Please select objects to export!")
            return {'CANCELLED'}
        
        if gs_props.export_mode == "INDIVIDUAL":
            # Individual export mode
            local_export_path = os.path.join(temp_dir, "fileTransferFbxIndividual\\")
            
            # Clean the directory before exporting
            clean_directory(local_export_path)
            
            # Create the directory if it doesn't exist
            if not os.path.exists(local_export_path):
                try:
                    os.makedirs(local_export_path)
                    print("Created directory: " + local_export_path)
                except:
                    self.report({'ERROR'}, f"Failed to create directory: {local_export_path}")
                    return {'CANCELLED'}
            
            # Store original selection
            selected_objects = context.selected_objects.copy()
            exported_count = 0
            
            # Export each object individually
            for obj in selected_objects:
                # Clear selection and select only current object
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                # Generate filename based on object name and target app
                safe_obj_name = "".join(c for c in obj.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                export_file = os.path.join(local_export_path, f"{safe_obj_name}_blender_to_{self.target_app}.fbx")
                
                if self.export_single_fbx(context, export_file):
                    exported_count += 1
                    print(f"Exported: {export_file}")
                else:
                    self.report({'WARNING'}, f"Failed to export {obj.name}")
            
            # Restore original selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objects:
                obj.select_set(True)
            if selected_objects:
                context.view_layer.objects.active = selected_objects[0]
            
            self.report({'INFO'}, f"Successfully exported {exported_count} object(s) individually")
            return {'FINISHED'}
        else:
            # Original "All" mode behavior
            local_export_path = os.path.join(temp_dir, "fileTransferFbx\\")
            
            # Create the directory if it doesn't exist
            if not os.path.exists(local_export_path):
                try:
                    os.makedirs(local_export_path)
                    print("Created directory: " + local_export_path)
                except:
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
            else:
                return {'CANCELLED'}
    
    def export_single_fbx(self, context, export_file):
        """Export selected objects to a single FBX file using global settings"""
        try:
            print("Attempting to export to: " + export_file)
            
            # Apply pre-processing
            pre_process_export_objects(context)
            
            # Export FBX using global settings
            export_fbx_with_settings(export_file, context)
            
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export to {export_file}: {str(e)}")
            return False

# Import from Server operator
class IMPORT_OT_from_server(Operator):
    bl_idname = "gs.import_from_server"
    bl_label = "Import from Server"
    bl_description = "Import FBX from server"
    
    def execute(self, context):
        scene = context.scene
        gs_props = scene.gs_file_transfer_props
        
        # Ensure the list is populated
        if len(scene.gs_person_list) <= 0:
            populate_person_list(scene)
            if len(scene.gs_person_list) <= 0:
                self.report({'ERROR'}, "Failed to populate person list")
                return {'CANCELLED'}
        
        app1 = gs_props.server_target_app.lower()
        app2 = "blender"
        
        # Get the selected person from the scrollable list
        gs_folder = scene.gs_person_list[scene.gs_person_index].name
        
        if gs_props.export_mode == "INDIVIDUAL":
            # For individual mode, look for multiple files in a pattern
            server_path = "\\\\192.168.1.210\\Temp\\File_Transfer\\"
            server_dir = server_path + gs_folder + "\\"
            
            if not os.path.exists(server_dir):
                self.report({'ERROR'}, f"Server directory does not exist: {server_dir}")
                return {'CANCELLED'}
            
            # Look for files matching the pattern
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
            # Original "All" mode behavior
            server_path = "\\\\192.168.1.210\\Temp\\File_Transfer\\"
            file_path = server_path + gs_folder + "\\" + gs_folder + "_" + app1 + "_to_" + app2 + "_" + username + ".fbx"
            
            print("Attempting to import from server: " + file_path)
            
            if os.path.exists(file_path):
                if self.import_single_fbx_server(context, file_path):
                    self.report({'INFO'}, f"Successfully imported from {file_path}")
                    return {'FINISHED'}
                else:
                    return {'CANCELLED'}
            else:
                self.report({'ERROR'}, f"File does not exist: {file_path}")
                return {'CANCELLED'}
    
    def import_single_fbx_server(self, context, file_path):
        """Import a single FBX file from server using global settings"""
        try:
            print("Attempting to import from server: " + file_path)
            
            # Store currently selected objects to know what was imported
            objects_before_import = set(bpy.context.scene.objects)
            
            # Import FBX using global settings
            import_fbx_with_settings(file_path, context)
            
            # Get newly imported objects
            objects_after_import = set(bpy.context.scene.objects)
            imported_objects = list(objects_after_import - objects_before_import)
            
            # Apply post-processing
            post_process_imported_objects(imported_objects, context)
            
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import from server {file_path}: {str(e)}")
            return False

# Export to Server operator
class EXPORT_OT_to_server(Operator):
    bl_idname = "gs.export_to_server"
    bl_label = "Export to Server"
    bl_description = "Export FBX to server"
    
    def execute(self, context):
        scene = context.scene
        gs_props = scene.gs_file_transfer_props
        
        # Ensure the list is populated
        if len(scene.gs_person_list) <= 0:
            populate_person_list(scene)
            if len(scene.gs_person_list) <= 0:
                self.report({'ERROR'}, "Failed to populate person list")
                return {'CANCELLED'}
        
        # Check if any objects are selected
        if not context.selected_objects:
            self.report({'WARNING'}, "Please select objects to export!")
            return {'CANCELLED'}
        
        app1 = "blender"
        app2 = gs_props.server_target_app.lower()
        
        # Get the selected person from the scrollable list
        gs_folder = scene.gs_person_list[scene.gs_person_index].name
        
        if gs_props.export_mode == "INDIVIDUAL":
            # Individual export mode for server
            server_path = "\\\\192.168.1.210\\Temp\\File_Transfer\\"
            server_dir = server_path + username + "\\"
            
            # Create export directory if it doesn't exist
            if not os.path.exists(server_dir):
                try:
                    os.makedirs(server_dir)
                except:
                    self.report({'ERROR'}, f"Failed to create directory: {server_dir}")
                    return {'CANCELLED'}
            
            # Store original selection
            selected_objects = context.selected_objects.copy()
            exported_count = 0
            
            # Export each object individually
            for obj in selected_objects:
                # Clear selection and select only current object
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                # Generate filename based on object name
                safe_obj_name = "".join(c for c in obj.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                file_path = server_dir + safe_obj_name + "_" + username + "_" + app1 + "_to_" + app2 + "_" + gs_folder + ".fbx"
                
                if self.export_single_fbx_server(context, file_path):
                    exported_count += 1
                    print(f"Exported to server: {file_path}")
                else:
                    self.report({'WARNING'}, f"Failed to export {obj.name} to server")
            
            # Restore original selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objects:
                obj.select_set(True)
            if selected_objects:
                context.view_layer.objects.active = selected_objects[0]
            
            self.report({'INFO'}, f"Successfully exported {exported_count} object(s) individually to server")
            return {'FINISHED'}
        else:
            # Original "All" mode behavior
            server_path = "\\\\192.168.1.210\\Temp\\File_Transfer\\"
            file_path = server_path + username + "\\" + username + "_" + app1 + "_to_" + app2 + "_" + gs_folder + ".fbx"
            
            print("Attempting to export to server: " + file_path)
            
            # Create export directory if it doesn't exist
            dir_path = os.path.dirname(file_path)
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                except:
                    self.report({'ERROR'}, f"Failed to create directory: {dir_path}")
                    return {'CANCELLED'}
            
            if self.export_single_fbx_server(context, file_path):
                self.report({'INFO'}, f"Successfully exported to {file_path}")
                return {'FINISHED'}
            else:
                return {'CANCELLED'}
    
    def export_single_fbx_server(self, context, file_path):
        """Export selected objects to server using global settings"""
        try:
            # Apply pre-processing
            pre_process_export_objects(context)
            
            # Export FBX using global settings
            export_fbx_with_settings(file_path, context)
            
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export to server {file_path}: {str(e)}")
            return False

# Properties class
class GSFileTransferProperties(bpy.types.PropertyGroup):
    # Export mode selection (All or Individual)
    export_mode: EnumProperty(
        name="Export Mode",
        items=[
            ("ALL", "All", "Export all selected objects as one FBX file"),
            ("INDIVIDUAL", "Individual", "Export each selected object as separate FBX files")
        ],
        default="ALL"
    )
    
    # Clear normals toggle
    clear_normals: BoolProperty(
        name="Clear Normal",
        description="Clear all normal data and sharp edges from imported FBX files",
        default=False
    )
    
    # Auto smooth angle
    auto_smooth_angle: FloatProperty(
        name="Auto Smooth",
        description="Auto smooth angle for imported FBX files (in degrees)",
        default=180.0,
        min=0.0,
        max=180.0,
        step=1.0,
        precision=1
    )
    
    # Server application settings
    server_target_app: EnumProperty(
        name="Target Software",
        items=[
            ("Blender", "Blender", ""),
            ("Maya", "Maya", ""),
            ("Max", "Max", "")
        ],
        default="Maya"
    )

# Panel class for UI
class GS_PT_FileTransferPanel(Panel):
    bl_label = "GS File Transfer"
    bl_idname = "GS_PT_FileTransferPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GS File Transfer'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        gs_props = scene.gs_file_transfer_props
        
        # Global Export Mode Section
        mode_box = layout.box()
        mode_box.label(text="Mode")
        mode_row = mode_box.row()
        mode_row.prop(gs_props, "export_mode", expand=True)
        
        # Clear Normal toggle and Auto Smooth input aligned with Mode columns
        options_row = mode_box.row()
        split = options_row.split(factor=0.5)
        split.prop(gs_props, "clear_normals")
        auto_smooth_col = split.row()
        auto_smooth_col.label(text="Auto Smooth:")
        auto_smooth_col.prop(gs_props, "auto_smooth_angle", text="")
        
        # Add separator for visual clarity
        layout.separator()
        
        # Local section
        box = layout.box()
        box.label(text="Local")
        
        # Create a row for Maya and Max sections
        row = box.row()
        
        # Maya column
        col1 = row.column()
        col1.label(text="Maya")
        col1.operator("gs.import_from_application", text="Import").source_app = "maya"
        col1.operator("gs.export_to_application", text="Export").target_app = "maya"
        
        # Max column
        col2 = row.column()
        col2.label(text="Max")
        col2.operator("gs.import_from_application", text="Import").source_app = "max"
        col2.operator("gs.export_to_application", text="Export").target_app = "max"
        
        # Server section
        server_box = layout.box()
        server_box.label(text="Server")
        
        # Target software selection with proper alignment
        app_row = server_box.row()
        split = app_row.split(factor=0.5)
        split.label(text="Target Software:")
        split.prop(gs_props, "server_target_app", text="")
        
        # Single shared person dropdown with scroll UI
        person_row = server_box.row()
        person_row.template_list(
            "GS_UL_PersonList", "server_person_list",
            scene, "gs_person_list",
            scene, "gs_person_index",
            rows=8,
            type='DEFAULT'
        )
        
        # Import and Export buttons in a row
        button_row = server_box.row()
        button_row.operator("gs.import_from_server", text="Import")
        button_row.operator("gs.export_to_server", text="Export")
        
        # User info
        user_row = layout.row()
        user_row.label(text="Current User: " + username)

# Function to populate person list
def populate_person_list(scene):
    """Populate the person list from server CSV file"""
    import csv
    
    # Clear existing items
    scene.gs_person_list.clear()
    
    server_path = "\\\\192.168.1.210\\Pipeline\\Library\\Data\\Data_Users.csv"
    
    try:
        with open(server_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Find the "users" column
            header_row = next(reader, None)
            if header_row is None:
                raise ValueError("CSV file is empty")
            
            users_column_index = None
            for i, header in enumerate(header_row):
                if header.strip().lower() == "users":
                    users_column_index = i
                    break
            
            if users_column_index is None:
                raise ValueError("No 'users' column found in CSV file")
            
            # Read all subsequent rows and extract users from the users column
            for row in reader:
                if len(row) > users_column_index:
                    user_name = row[users_column_index].strip()
                    if user_name:  # Only add non-empty user names
                        item = scene.gs_person_list.add()
                        item.name = user_name
            
            print(f"Successfully loaded {len(scene.gs_person_list)} users from CSV")
    
    except Exception as e:
        print(f"Error reading user list from CSV: {e}")

# Handler to populate list when a new blend file is loaded
@bpy.app.handlers.persistent
def load_handler(dummy):
    """Initialize person list when a new file is loaded"""
    for scene in bpy.data.scenes:
        populate_person_list(scene)

# Classes to register
classes = (
    GS_PersonItem,
    GS_UL_PersonList,
    IMPORT_OT_from_application,
    EXPORT_OT_to_application,
    IMPORT_OT_from_server,
    EXPORT_OT_to_server,
    GSFileTransferProperties,
    GS_PT_FileTransferPanel
)

# Registration function
def register():
    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Create the scene properties
    bpy.types.Scene.gs_file_transfer_props = bpy.props.PointerProperty(type=GSFileTransferProperties)
    bpy.types.Scene.gs_person_list = bpy.props.CollectionProperty(type=GS_PersonItem)
    bpy.types.Scene.gs_person_index = bpy.props.IntProperty(default=0)
    
    # Set up persistent handler for file loads
    bpy.app.handlers.load_post.append(load_handler)
    
    # Use a timer to populate lists after registration
    bpy.app.timers.register(populate_list_timer, first_interval=1.0)

# Timer function to populate list after registration
def populate_list_timer():
    """Populate list after a short delay to ensure proper context"""
    for scene in bpy.data.scenes:
        if len(scene.gs_person_list) == 0:
            populate_person_list(scene)
    # Return None to not repeat the timer
    return None

# Unregistration function
def unregister():
    # Remove the load handler
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    
    # Unregister in reverse order
    del bpy.types.Scene.gs_person_list
    del bpy.types.Scene.gs_person_index
    del bpy.types.Scene.gs_file_transfer_props
    
    # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

# This allows you to run the script directly from Blender's Text editor
if __name__ == "__main__":
    register()