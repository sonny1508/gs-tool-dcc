"""
GS File Transfer
This add-on provides tools for transferring files between Blender, Maya and 3ds Max.
"""

bl_info = {
    "name": "GS File Transfer",
    "author": "Sonny",
    "version": (1, 0),
    "blender": (3, 6, 21),
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
from bpy.props import StringProperty, EnumProperty
from bpy.types import Panel, Operator

def safe_path(path):
    """
    Make a path safe for file operations.
    """
    # Normalize the path to use forward slashes
    normalized = path.replace('\\', '/')
    return normalized

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
        username = getpass.getuser()
        
        # Construct temp directory path using original structure
        temp_dir = os.path.join("C:\\Users", username, "AppData\\Local\\Temp\\")
        local_export_path = os.path.join(temp_dir, "fileTransferFbx\\")
        
        if self.source_app == "maya":
            import_file = os.path.join(local_export_path, "maya_to_blender.fbx")
        elif self.source_app == "max":
            import_file = os.path.join(local_export_path, "max_to_blender.fbx")
        else:
            self.report({'ERROR'}, "Invalid source application")
            return {'CANCELLED'}
        
        print("Attempting to import: " + import_file)
        
        if os.path.exists(import_file):
            # Get current scene unit scale to properly scale the imported objects
            scene_unit_settings = context.scene.unit_settings
            unit_scale = scene_unit_settings.scale_length
            
            # Calculate scale factor based on current unit settings
            # FBX files from Max and Maya are in centimeters
            # If Blender is set to meters (1.0), we need to import at 0.01 scale
            # If Blender is set to centimeters (0.01), we keep the scale at 1.0
            scale_factor = unit_scale / 1.0 if unit_scale > 0 else 1.0
            
            # Import FBX with settings from reference and adjusted scale
            bpy.ops.import_scene.fbx(
                filepath=import_file,
                global_scale=scale_factor,  # Scale to match Blender's current unit
                use_custom_normals=True
            )
            
            # Set active object (from reference code)
            if len(bpy.context.selected_objects) != 0:
                bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
            
            # Apply rotation and scale after import (from reference)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            
            self.report({'INFO'}, f"Successfully imported from {import_file}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"File does not exist: {import_file}")
            return {'CANCELLED'}

# Export FBX operator
class EXPORT_OT_to_application(Operator):
    bl_idname = "gs.export_to_application"
    bl_label = "Export"
    bl_description = "Export FBX to another application"
    
    target_app: StringProperty(default="")
    
    def execute(self, context):
        username = getpass.getuser()
        
        # Construct temp directory path using original structure
        temp_dir = os.path.join("C:\\Users", username, "AppData\\Local\\Temp\\")
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
        
        # Check if any objects are selected
        if not context.selected_objects:
            self.report({'WARNING'}, "Please select objects to export!")
            return {'CANCELLED'}
        
        print("Attempting to export to: " + export_file)
        
        # Apply scale before export (as seen in reference code)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        # Get current scene unit scale and calculate scale factor to convert to centimeters
        scene_unit_settings = context.scene.unit_settings
        unit_scale = scene_unit_settings.scale_length
        
        # 0.01 = cm in Blender's unit system
        # If unit_scale is 0.01, we're already in centimeters
        # If it's 1.0, we're in meters and need to multiply by 100 to get to cm
        scale_factor = 1.0 / unit_scale if unit_scale > 0 else 1.0
        
        # Export selected objects as FBX with settings from reference
        bpy.ops.export_scene.fbx(
            filepath=export_file,
            use_selection=True,
            global_scale=scale_factor,  # Scale to ensure output is in centimeters
            object_types={'MESH'},
            use_mesh_modifiers=True,
            bake_anim=False,
            use_space_transform=True,  # To handle scene unit conversion correctly
            apply_scale_options='FBX_SCALE_ALL'  # Apply scaling to all transforms
        )
        
        self.report({'INFO'}, f"Successfully exported to {export_file}")
        return {'FINISHED'}

# Import from Server operator
class IMPORT_OT_from_server(Operator):
    bl_idname = "gs.import_from_server"
    bl_label = "Import from Server"
    bl_description = "Import FBX from server"
    
    def execute(self, context):
        scene = context.scene
        gs_props = scene.gs_file_transfer_props
        username = getpass.getuser()
        
        # Ensure the lists are populated
        if len(scene.gs_person_list_import) <= 0:
            populate_person_lists(scene)
            if len(scene.gs_person_list_import) <= 0:
                self.report({'ERROR'}, "Failed to populate person list")
                return {'CANCELLED'}
        
        app1 = gs_props.server_import_app.lower()
        app2 = "blender"
        
        # Get the selected person from the scrollable list
        gs_folder = scene.gs_person_list_import[scene.gs_person_index_import].name
        
        # Build the path with new folder structure (from original script)
        server_path = "\\\\192.168.1.10\\Temp\\File_Transfer\\"
        file_path = server_path + gs_folder + "\\" + gs_folder + "_" + app1 + "_to_" + app2 + "_" + username + ".fbx"
        
        print("Attempting to import from server: " + file_path)
        
        if os.path.exists(file_path):
            # Get current scene unit scale to properly scale the imported objects
            scene_unit_settings = context.scene.unit_settings
            unit_scale = scene_unit_settings.scale_length
            
            # Calculate scale factor based on current unit settings
            # FBX files from Max and Maya are in centimeters
            # If Blender is set to meters (1.0), we need to import at 0.01 scale
            # If Blender is set to centimeters (0.01), we keep the scale at 1.0
            scale_factor = unit_scale / 0.01 if unit_scale > 0 else 1.0
            
            # Import FBX with settings from reference and adjusted scale
            bpy.ops.import_scene.fbx(
                filepath=file_path,
                global_scale=scale_factor,  # Scale to match Blender's current unit
                use_custom_normals=True
            )
            
            # Set active object (from reference code)
            if len(bpy.context.selected_objects) != 0:
                bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
            
            # Apply rotation and scale after import (from reference)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            
            self.report({'INFO'}, f"Successfully imported from {file_path}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"File does not exist: {file_path}")
            return {'CANCELLED'}

# Export to Server operator
class EXPORT_OT_to_server(Operator):
    bl_idname = "gs.export_to_server"
    bl_label = "Export to Server"
    bl_description = "Export FBX to server"
    
    def execute(self, context):
        scene = context.scene
        gs_props = scene.gs_file_transfer_props
        username = getpass.getuser()
        
        # Ensure the lists are populated
        if len(scene.gs_person_list_export) <= 0:
            populate_person_lists(scene)
            if len(scene.gs_person_list_export) <= 0:
                self.report({'ERROR'}, "Failed to populate person list")
                return {'CANCELLED'}
        
        app1 = "blender"
        app2 = gs_props.server_export_app.lower()
        
        # Get the selected person from the scrollable list
        gs_folder = scene.gs_person_list_export[scene.gs_person_index_export].name
        
        # Build the path with new folder structure (from original script)
        server_path = "\\\\192.168.1.10\\Temp\\File_Transfer\\"
        file_path = server_path + username + "\\" + username + "_" + app1 + "_to_" + app2 + "_" + gs_folder + ".fbx"
        
        # Check if any objects are selected
        if not context.selected_objects:
            self.report({'WARNING'}, "Please select objects to export!")
            return {'CANCELLED'}
        
        print("Attempting to export to server: " + file_path)
        
        # Create export directory if it doesn't exist
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except:
                self.report({'ERROR'}, f"Failed to create directory: {dir_path}")
                return {'CANCELLED'}
        
        # Apply scale before export (as seen in reference code)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        # Get current scene unit scale and calculate scale factor to convert to centimeters
        scene_unit_settings = context.scene.unit_settings
        unit_scale = scene_unit_settings.scale_length
        
        # 0.01 = cm in Blender's unit system
        # If unit_scale is 0.01, we're already in centimeters
        # If it's 1.0, we're in meters and need to multiply by 100 to get to cm
        scale_factor = 0.01 / unit_scale if unit_scale > 0 else 1.0
        
        # Export selected objects as FBX with settings from reference
        bpy.ops.export_scene.fbx(
            filepath=file_path,
            use_selection=True,
            global_scale=scale_factor,  # Scale to ensure output is in centimeters
            object_types={'MESH'},
            use_mesh_modifiers=True,
            bake_anim=False,
            use_space_transform=True,  # To handle scene unit conversion correctly
            apply_scale_options='FBX_SCALE_ALL'  # Apply scaling to all transforms
        )
        
        self.report({'INFO'}, f"Successfully exported to {file_path}")
        return {'FINISHED'}

# Properties class
class GSFileTransferProperties(bpy.types.PropertyGroup):
    # Create properties for application selection only
    server_import_app: EnumProperty(
        name="App",
        items=[
            ("Blender", "Blender", ""),
            ("Maya", "Maya", ""),
            ("Max", "Max", "")
        ],
        default="Maya"  # Changed default to Maya since Blender to Blender doesn't make much sense
    )
    
    server_export_app: EnumProperty(
        name="App",
        items=[
            ("Blender", "Blender", ""),
            ("Maya", "Maya", ""),
            ("Max", "Max", "")
        ],
        default="Maya"  # Changed default to Maya since Blender to Blender doesn't make much sense
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
        username = getpass.getuser()
        
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
        
        # Import app dropdown
        import_row = server_box.row()
        import_row.prop(gs_props, "server_import_app", text="")
        
        # Import person dropdown with scroll UI - WITHOUT FILTER/SEARCH
        import_person_row = server_box.row()
        import_person_row.template_list(
            "GS_UL_PersonList", "server_import_person_list",
            scene, "gs_person_list_import",
            scene, "gs_person_index_import",
            rows=10,
            type='DEFAULT'  # Use DEFAULT type to hide the filter box
        )
        
        # Import button
        server_box.operator("gs.import_from_server", text="Import")
        
        server_box.separator()
        
        # Export app dropdown
        export_row = server_box.row()
        export_row.prop(gs_props, "server_export_app", text="")
        
        # Export person dropdown with scroll UI - WITHOUT FILTER/SEARCH
        export_person_row = server_box.row()
        export_person_row.template_list(
            "GS_UL_PersonList", "server_export_person_list",
            scene, "gs_person_list_export",
            scene, "gs_person_index_export",
            rows=10,
            type='DEFAULT'  # Use DEFAULT type to hide the filter box
        )
        
        # Export button
        server_box.operator("gs.export_to_server", text="Export")
        
        # User info
        user_row = layout.row()
        user_row.label(text="Current User: " + username)

# Function to populate person lists
def populate_person_lists(scene):
    """Populate the person lists with gs01-gs99"""
    # Clear existing items
    scene.gs_person_list_import.clear()
    scene.gs_person_list_export.clear()
    
    # Add gs01 through gs99
    for i in range(1, 100):
        gs_num = "{:02d}".format(i)
        gs_folder = "gs" + gs_num
        
        item_import = scene.gs_person_list_import.add()
        item_import.name = gs_folder
        
        item_export = scene.gs_person_list_export.add()
        item_export.name = gs_folder

# Handler to populate lists when a new blend file is loaded
@bpy.app.handlers.persistent
def load_handler(dummy):
    """Initialize person lists when a new file is loaded"""
    # This ensures we're in a proper context with scenes available
    for scene in bpy.data.scenes:
        populate_person_lists(scene)

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
    bpy.types.Scene.gs_person_list_import = bpy.props.CollectionProperty(type=GS_PersonItem)
    bpy.types.Scene.gs_person_index_import = bpy.props.IntProperty(default=0)
    bpy.types.Scene.gs_person_list_export = bpy.props.CollectionProperty(type=GS_PersonItem)
    bpy.types.Scene.gs_person_index_export = bpy.props.IntProperty(default=0)
    
    # Set up persistent handler for file loads
    bpy.app.handlers.load_post.append(load_handler)
    
    # Use a timer to populate lists after registration
    bpy.app.timers.register(populate_lists_timer, first_interval=1.0)

# Timer function to populate lists after registration
def populate_lists_timer():
    """Populate lists after a short delay to ensure proper context"""
    for scene in bpy.data.scenes:
        if len(scene.gs_person_list_import) == 0:
            populate_person_lists(scene)
    # Return None to not repeat the timer
    return None

# Unregistration function
def unregister():
    # Remove the load handler
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    
    # Unregister in reverse order
    del bpy.types.Scene.gs_person_list_export
    del bpy.types.Scene.gs_person_index_export
    del bpy.types.Scene.gs_person_list_import
    del bpy.types.Scene.gs_person_index_import
    del bpy.types.Scene.gs_file_transfer_props
    
    # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()