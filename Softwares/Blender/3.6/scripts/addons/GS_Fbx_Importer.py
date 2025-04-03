bl_info = {
    "name": "GS Blender Autodesk FBX Transfer",
    "author": "Glenda Studio",
    "version": (1, 0),
    "blender": (3, 00, 0),
    "location": "Sidebar",
    "description": "Import/Export FBX ",
    "warning": "",
    "wiki_url": "",
    "category": "Development",
}

import bpy, math, addon_utils
import os
import glob
import numpy as np
import mathutils
import tempfile
from mathutils.bvhtree import BVHTree
from bpy.props import *
from mathutils import Matrix, Vector
from bpy.types import Panel, PropertyGroup, Scene, WindowManager, Operator

# Global variables as a module-level dictionary
GS_globals = {
    "wrongPositions_Attachment": [],
    "wrongNames_Attachment": [],
    "wrongTransformObjs": {},
    "wrongObjName": {},
    "objectsWithKeys": [],
    "ResultMessage": "Hello World",
    "meshObjs": [],
    "version": "Version 1.0"
}

class GSImporterMainPanel(Panel):
    bl_label = "Blender Maya/3DsMax Transfer"
    bl_idname = "VIEW3D_PT_gs_fbx_importer"  # Fixed: proper unique ID 
    bl_space_type = 'VIEW_3D'
    bl_category = "FBX Import Tool"
    bl_region_type = 'UI'

    def draw(self, context):
        scn = context.scene
        layout = self.layout
     
        obj = context.object
        
        row3 = layout.row()
        row3.operator("mesh.gsimportfbx", text="Import")
        row4 = layout.row()
        row4.operator("mesh.gsexportfbx", text="Export Selected")
        
class GSimportfbx(Operator):  # Fixed: Inherits from Operator, not Panel
    bl_idname = "mesh.gsimportfbx"
    bl_label = "FBX Import"
    bl_description = "Import FBX Tool"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        temppath = tempfile.gettempdir()
        fbxpath = temppath + '/MeshTransfer.fbx'
        #Import FBX
        if not os.path.isfile(fbxpath):
            self.report({'ERROR'}, f"Import FBX File Not Found")
            return {'FINISHED'}
        
        try:
            # Parameters specific to Blender 3.6
            bpy.ops.import_scene.fbx(
                filepath=fbxpath,
                use_manual_orientation=False,
                global_scale=1.0,
                bake_space_transform=False,
                use_custom_normals=True,
                use_image_search=False,
                use_alpha_decals=False,
                decal_offset=0.0,
                use_anim=True,
                anim_offset=1.0,
                use_subsurf=False,
                use_custom_props=True,
                use_custom_props_enum_as_string=True,
                ignore_leaf_bones=False,
                force_connect_children=False,
                automatic_bone_orientation=False,
                primary_bone_axis='Y',
                secondary_bone_axis='X',
                use_prepost_rot=True,
                axis_forward='-Z',
                axis_up='Y'
            )
            
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            return {'CANCELLED'}  # Fixed: Return CANCELLED on error
            
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        return {'FINISHED'}

class GSexportfbx(Operator):  # Fixed: Inherits from Operator, not Panel
    bl_idname = "mesh.gsexportfbx"
    bl_label = "FBX Export"
    bl_description = "Export FBX Tool"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        temppath = tempfile.gettempdir()
        fbxpath = temppath + '/MeshTransfer.fbx'
        
        sel_obj = bpy.context.selected_objects
        if not sel_obj:
            self.report({'ERROR'}, f"No Mesh Selected")
            return {'FINISHED'}
            
        try:
            bpy.ops.export_scene.fbx(filepath = fbxpath, use_selection=True)
            self.report({'INFO'}, f"Mesh Exported")
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}  # Fixed: Return CANCELLED on error
            
        return {'FINISHED'}
        
classes = [
    GSImporterMainPanel,
    GSimportfbx,
    GSexportfbx
]

def register():
    for cls in classes:  # Fixed: Use the classes list to register
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):  # Fixed: Unregister in reverse order
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()