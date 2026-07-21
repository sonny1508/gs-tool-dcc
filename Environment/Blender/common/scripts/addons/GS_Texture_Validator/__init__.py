bl_info = {
    "name": "GS Texture Path Validator",
    "author": "Glenda Studio",
    "version": (1, 1),
    "blender": (3, 6, 10),
    "location": "Sidebar",
    "category": "Object",
}

import bpy, math, addon_utils
import numpy as np
from mathutils.bvhtree import BVHTree
from bpy.props import *
from mathutils import Matrix, Vector
from bpy.types import Panel, PropertyGroup, Scene, WindowManager


class globalVariables():
    bl_idname = "gs.globalvariables"
    bl_label = "Global Variables"

    wrongPositions_Attachment = []
    wrongNames_Attachment = []
    wrongTransformObjs = {}
    wrongObjName = {}
    objectsWithKeys = []
    ResultMessage = "Hello World"
    meshObjs = []
    version = "Version 1.0"

def ShowMessageBox(message, title, icon):
    def draw(self, context):
        for line in message:
            self.layout.label(text=line)

    bpy.context.window_manager.popup_menu(draw, title= title, icon= icon)


def add_item(collection, itemname, message):
    item = collection.add()
    item.name = itemname
    item.type = itemname
    item.message = message


def remove_item(collection, itemname):
    for i in collection.keys():
        if i == itemname:
            collection.remove(collection.find(itemname))

    if len(collection) == 0:
        bpy.context.scene.checkResult_all = False


def getmeshObjs():
    meshObjs = []
    objs = bpy.context.scene.objects
    for obj in objs:
        meshObjs.append(obj)

    return meshObjs

def check_mesh_in_collection(collection_name, mesh_name):
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        for obj in collection.objects:
            if obj.name.endswith(mesh_name):
                return (mesh_name + " found!", 'CHECKMARK')
    return (mesh_name + " not found in " + collection_name, 'ERROR')
                         

class CUSTOM_gsobjectCollection(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    type: StringProperty()
    message: StringProperty()
    id: IntProperty()


class CUSTOM_gsOT_clearList(bpy.types.Operator):
    bl_idname = "custom.gs_clear_list"
    bl_label = "Clear List"
    bl_description = "Close the error report panel"

    @classmethod
    def poll(cls, context):
        return bool(context.scene.custom)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        if bool(context.scene.custom):
            context.scene.custom.clear()
            context.scene.checkResult_all = False
            self.report({'INFO'}, "All items removed")
        else:
            self.report({'INFO'}, "Nothing to remove")
        return {'FINISHED'}


class MATERIAL_gs_matslots_example(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, "message", text=item.type, emboss=False, icon_value=icon)

class ValidationgsToolMainPanel(bpy.types.Panel, globalVariables):
    bl_label = "GS Texture Path Validation Tool"
    bl_idname = "GS_Texture_Path"
    bl_space_type = 'VIEW_3D'
    bl_category = "GS Texture Path Validation Tool"
    bl_region_type = 'UI'
    

    bpy.types.Scene.checkResult_Transform = BoolProperty(name = "Boolean", description = "None")
    bpy.types.Scene.checkResult_UnusedData = BoolProperty( name = "Boolean", description = "None")
    bpy.types.Scene.checkResult_all = BoolProperty( name = "Boolean", description = "None")
    
    def initSceneProperties(scn):
        scn.checkResult_Transform = True
        scn.checkResult_UnusedData = True
        scn.checkResult_all = False
        return

    def draw(self, context):
        scn = context.scene
        layout = self.layout
     
        obj = context.object

        row1 = layout.row()
        row1.operator("gs.imagecheck", text="Get All Texture Path")
        
              
        if scn.checkResult_all == True:
            layout.template_list("MATERIAL_gs_matslots_example", "", scn, "custom", scn, "gscustom_index")

            row = layout.row()
            row.operator("custom.s4_clear_list", text="Clear and hide result box.")

        row11 = layout.row()
        row11.label(text= globalVariables.version)
        

class gsInitialCheck(bpy.types.Operator, ValidationgsToolMainPanel, globalVariables):
    bl_idname = "gs.imagecheck"
    bl_label = "Initial Check"
    bl_description = "Run through all check processes"

    def execute(self, context):
        if bool(context.scene.custom):
            context.scene.custom.clear()

        #        if len(globalVariables.meshObjs) == 0:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        #        bpy.ops.object.mode_set(mode='OBJECT')
        scn = context.scene
        objs = bpy.context.scene.objects
        #path = context.scene.texture_folder
        globalVariables.meshObjs = getmeshObjs()
        
        #reload shader path to standard path
        
        if len(globalVariables.meshObjs) != 0:
            bpy.context.view_layer.objects.active = globalVariables.meshObjs[0]

            #        bpy.context.view_layer.objects.active = None
            imagelist = []
            for obj in objs:
                if obj.type == 'MESH':
                    if not obj.material_slots:
                        continue
                    for s in obj.material_slots:
                        if s.material and s.material.use_nodes:
                            for n in s.material.node_tree.nodes:
                                try:
                                    if n.type == 'TEX_IMAGE':
                                        imagename = n.image.name
                                        if imagename not in imagelist:
                                                message = n.image.filepath
                                                #if "//Textures" not in message and "C:\Dev\PROJECTS\GTR\SOURCE_ART\VEHICLES" not in message:
                                                add_item(scn.custom, imagename, message)
                                                imagelist.append(imagename)
                                except:
                                    pass
                                    
                
            ##Finish check result
            scn.checkResult_all = True
            confmessage = ["Checking Finished."]
            ShowMessageBox(confmessage, "GS Texture Path Validation", "CHECKMARK")
            return {"FINISHED"}
            
        else:
            scn.checkResult_all = True
            confmessage = ["Scene in empty."]
            ShowMessageBox(confmessage, "GS Texture Path Validation", "ERROR")
            return {"FINISHED"}


classes = [
    CUSTOM_gsobjectCollection,
    CUSTOM_gsOT_clearList,
    MATERIAL_gs_matslots_example,
    ValidationgsToolMainPanel,   
    gsInitialCheck
    
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.custom = CollectionProperty(type=CUSTOM_gsobjectCollection)
    bpy.types.Scene.gscustom_index = IntProperty(default=5)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.custom
    del bpy.types.Scene.gscustom_index


if __name__ == "__main__":
    register()