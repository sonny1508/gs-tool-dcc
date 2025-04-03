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
from bpy.types import Panel, PropertyGroup, Scene, WindowManager

class globalVariables():
    bl_idname = "GSFBXimporter.globalvariables"
    bl_label = "Global Variables"

    wrongPositions_Attachment = []
    wrongNames_Attachment = []
    wrongTransformObjs = {}
    wrongObjName = {}
    objectsWithKeys = []
    ResultMessage = "Hello World"
    meshObjs = []
    version = "Version 1.0"

class GSImporterMainPanel(bpy.types.Panel, globalVariables):
    bl_label = "Blender Maya/3DsMax Transfer"
    bl_idname = ""
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
        
class GSimportfbx(bpy.types.Operator, GSImporterMainPanel, globalVariables):
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
            bpy.ops.import_scene.fbx(filepath = fbxpath, use_existing_materials=True, use_image_search = False)
            
        except:
            pass
            
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        return {'FINISHED'}

class GSexportfbx(bpy.types.Operator, GSImporterMainPanel, globalVariables):
    bl_idname = "mesh.gsexportfbx"
    bl_label = "FBX Export"
    bl_description = "Export FBX Tool"
    bl_options = {'REGISTER', 'UNDO'}
    
 
    def execute(self, context):
        temppath = tempfile.gettempdir()
        fbxpath = temppath + '/MeshTransfer.fbx'
        #Import FBX
        sel_obj = bpy.context.selected_objects
        if not sel_obj:
            self.report({'ERROR'}, f"No Mesh Selected")
            return {'FINISHED'}
            
        bpy.ops.export_scene.fbx(filepath = fbxpath, use_selection=True)
        self.report({'INFO'}, f"Mesh Exported")
        return {'FINISHED'}
        
classes = [
        GSImporterMainPanel,
        GSimportfbx,
        GSexportfbx
]


def register():
    bpy.utils.register_class(GSImporterMainPanel)
    bpy.utils.register_class(GSimportfbx)
    bpy.utils.register_class(GSexportfbx)

def unregister():
    bpy.utils.unregister_class(GSImporterMainPanel)
    bpy.utils.unregister_class(GSimportfbx)
    bpy.utils.unregister_class(GSexportfbx)

if __name__ == "__main__":
    register()
