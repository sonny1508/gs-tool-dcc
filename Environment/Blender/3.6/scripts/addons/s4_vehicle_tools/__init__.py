bl_info = {
    "name": "S4 Vehicle Tools",
    "author": "Glenda Studio",
    "version": (1, 1),
    "blender": (3, 6, 10),
    "location": "Sidebar",
    "description": "Validates S4 assets requirements for uploading",
    "category": "Object",
}

import bpy, math
import os
import numpy as np
from mathutils.bvhtree import BVHTree
from bpy.props import *
from mathutils import Matrix, Vector
from bpy.types import Panel, PropertyGroup, Scene, WindowManager

# Single source of truth for the blend file that ships the S4 custom shader
# node groups.
SHADER_BLEND_PATH = r"C:\Dev\PROJECTS\GTR\SOURCE_ART\BLENDER\SHADERS\S4_Vehicle_Shaders.blend"

meshes_to_check_CPIT = [
("CPIT", "_BODY_CPIT"),
("CPIT", "_BONNET_CPIT"),
("CPIT", "_BUMPER_F_CPIT"),
("CPIT", "_CHASSIS_CPIT"),
("CPIT", "_DISPLAY_CPIT"),
("CPIT", "_EXTANIM_CPIT"),
("CPIT", "_INTANIM_CPIT"),
("CPIT", "_INTERIOR_CPIT"),
("CPIT", "_STEERINGWHEEL_CPIT"),
("CPIT", "_WINDOWS_CPIT"),
]

meshes_to_check_LODA = [
("LODA", "_CHASSIS_LODA"),
("LODA", "_CALIPER_LF_LODA"),
("LODA", "_CALIPER_RF_LODA"),
("LODA", "_CALIPER_LR_LODA"),
("LODA", "_CALIPER_RR_LODA"),
("LODA", "_DISC_LF_LODA"),
("LODA", "_DISC_LR_LODA"),
("LODA", "_DISC_RF_LODA"),
("LODA", "_DISC_RR_LODA"),
("LODA", "_TIRE_LF_LODA"),
("LODA", "_TIRE_LR_LODA"),
("LODA", "_TIRE_RF_LODA"),
("LODA", "_TIRE_RR_LODA"),
("LODA", "_WHEEL_LF_LODA"),
("LODA", "_WHEEL_LR_LODA"),
("LODA", "_WHEEL_RF_LODA"),
("LODA", "_WHEEL_RR_LODA"),
]
meshes_to_check_LODB = [
("LODB", "_CHASSIS_LODB"),
("LODB", "_CALIPER_LF_LODB"),
("LODB", "_CALIPER_LR_LODB"),
("LODB", "_CALIPER_RF_LODB"),
("LODB", "_CALIPER_RR_LODB"),
("LODB", "_DISC_LF_LODB"),
("LODB", "_DISC_LR_LODB"),
("LODB", "_DISC_RF_LODB"),
("LODB", "_DISC_RR_LODB"),
("LODB", "_TIRE_LF_LODB"),
("LODB", "_TIRE_LR_LODB"),
("LODB", "_TIRE_RF_LODB"),
("LODB", "_TIRE_RR_LODB"),
("LODB", "_WHEEL_LF_LODB"),
("LODB", "_WHEEL_LR_LODB"),
("LODB", "_WHEEL_RF_LODB"),
("LODB", "_WHEEL_RR_LODB"),
]
meshes_to_check_LODC = [
("LODC", "_CHASSIS_LODC"),
("LODC", "_TIRE_LF_LODC"),
("LODC", "_TIRE_LR_LODC"),
("LODC", "_TIRE_RF_LODC"),
("LODC", "_TIRE_RR_LODC"),
("LODC", "_WHEEL_LF_LODC"),
("LODC", "_WHEEL_LR_LODC"),
("LODC", "_WHEEL_RF_LODC"),
("LODC", "_WHEEL_RR_LODC"),
]
meshes_to_check_LODD = [
("LODD", "_CHASSIS_LODD"),
]

mapping = {
    "CALIPER_LF": "FixedWheel_LF",
    "CALIPER_LR": "FixedWheel_LR",
    "CALIPER_RF": "FixedWheel_RF",
    "CALIPER_RR": "FixedWheel_RR",
    "DISC_LF": "PhysWheel_LF",
    "DISC_LR": "PhysWheel_LR",
    "DISC_RF": "PhysWheel_RF",
    "DISC_RR": "PhysWheel_RR",
    "TIRE_LF": "PhysWheel_LF",
    "TIRE_LR": "PhysWheel_LR",
    "TIRE_RF": "PhysWheel_RF",
    "TIRE_RR": "PhysWheel_RR",
    "WHEEL_LF": "PhysWheel_LF",
    "WHEEL_LR": "PhysWheel_LR",
    "WHEEL_RF": "PhysWheel_RF",
    "WHEEL_RR": "PhysWheel_RR",
    "STEERINGWHEEL": "SteeringWheel",
    "": "Root",
}

class globalVariables():
    bl_idname = "mesh.globalvariables"
    bl_label = "Global Variables"

    wrongPositions_Attachment = []
    wrongNames_Attachment = []
    wrongTransformObjs = {}
    wrongObjName = {}
    objectsWithKeys = []
    ResultMessage = "Hello World"
    meshObjs = []
    version = "Version 1.0"

def checkTransform(meshObjs):
    wrongPositionObjs = {}

    for meshObj in meshObjs:
        wrongValues = []
        if meshObj.type == 'MESH' and not "deformation" in meshObj.name:
            lx = meshObj.location[0]
            if lx != 0.0000:
                wrongValues.append("location X")

            ly = meshObj.location[1]
            if ly != 0.0000:
                wrongValues.append("location Y")

            lz = meshObj.location[2]
            if lz != 0.0000:
                wrongValues.append("location Z")

            rx = meshObj.rotation_euler[0]
            if rx != 0.0000:
                wrongValues.append("rotation X")

            ry = meshObj.rotation_euler[1]
            if ry != 0.0000:
                wrongValues.append("rotation Y")

            rz = meshObj.rotation_euler[2]
            if rz != 0.0000:
                wrongValues.append("rotation Z")

            sx = meshObj.scale[0]
            if sx != 1.000:
                wrongValues.append("scale X")

            sy = meshObj.scale[1]
            if sy != 1.000:
                wrongValues.append("scale Y")

            sz = meshObj.scale[2]
            if sz != 1.000:
                wrongValues.append("scale Z")

            if len(wrongValues) != 0:
                wrongPositionObjs[meshObj.name] = wrongValues
                print(meshObj.name, wrongValues)

    if len(wrongPositionObjs) != 0:
        return wrongPositionObjs
    else:
        return True


def checkUnusedData():
    unusedData = []

    datatypeList = [
        bpy.data.actions,
        bpy.data.armatures,
        #                bpy.data.brushes,
        bpy.data.cache_files,
        bpy.data.cameras,
        bpy.data.collections,
        bpy.data.curves,
        bpy.data.fonts,
        bpy.data.grease_pencils,
        bpy.data.images,
        bpy.data.lattices,
        bpy.data.libraries,
        bpy.data.lightprobes,
        bpy.data.lights,
        bpy.data.linestyles,
        bpy.data.masks,
        bpy.data.materials,
        bpy.data.metaballs,
        bpy.data.meshes,
        bpy.data.movieclips,
        bpy.data.node_groups,
        bpy.data.objects,
        bpy.data.paint_curves,
        bpy.data.palettes,
        bpy.data.particles,
        bpy.data.scenes,
        bpy.data.screens,
        bpy.data.shape_keys,
        bpy.data.sounds,
        bpy.data.speakers,
        #                bpy.data.texts,
        bpy.data.textures,
        bpy.data.volumes,
        bpy.data.window_managers,
        bpy.data.worlds,
        bpy.data.workspaces, ]

    for datatype in datatypeList:
        for bpy_data_iter in datatype:
            if bpy_data_iter.users == bpy_data_iter.use_fake_user:
                unusedData.append(bpy_data_iter)
                print(bpy_data_iter)

    results = []
    if len(unusedData) == 0:
        return True
    else:
        return False


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

    
###S4Export Part
def process_collection(collection_name):
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        # Move object to export and remove suffix
        for obj in collection.objects:
            remove_suffix(obj, collection_name)
            for part_name, target_bone in mapping.items():
                if part_name in obj.name:
                    parent_to_bone(obj.name, target_bone)
                    break
        #export collection
        export_to_fbx(collection_name)
        #Reset objects to initial state
        for obj in collection.objects:
            clear_bone_parent(obj)
            add_suffix(obj, collection_name)


def clear_bone_parent(obj):
    if obj.parent_type == 'BONE':
        mesh_matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.parent_type = 'OBJECT'
        obj.parent_bone = ''
        obj.matrix_world = mesh_matrix


def parent_to_bone(mesh_name, bone_name):
    mesh_obj = bpy.data.objects[mesh_name]
    armature_obj = bpy.data.objects["Armature_LOD"]
    bone_obj = armature_obj.pose.bones.get(bone_name)
    if mesh_obj.parent_bone is bone_name:
        print(f"Warning: Bone {bone_name} already parented to armature.")
        return
    if not bone_obj:
        print(f"Error: Bone {bone_name} not found in armature.")
        return
    # Save the mesh's current location and rotation
    mesh_matrix = mesh_obj.matrix_world.copy()
    # Set the mesh's location and rotation to the bone's location and rotation
    mesh_obj.parent = armature_obj
    mesh_obj.parent_type = 'BONE'
    mesh_obj.parent_bone = bone_name
    mesh_obj.matrix_world = mesh_matrix
    print(f"{mesh_name} parented to bone {bone_name}.")


def export_to_fbx(collection_name):
    # Get the current Blender file path
    file_path = bpy.data.filepath
    # Create the export directory if it doesn't exist
    export_dir = os.path.join(os.path.dirname(file_path), "ExportedFBX")
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    clear_selection()
    collection_obj = bpy.data.collections[collection_name]
    for obj in collection_obj.all_objects:
        obj.select_set(True)

    armature_name = "Armature_LOD"
    armature_obj = bpy.data.objects[armature_name]
    bpy.context.view_layer.objects.active = armature_obj
    armature_obj.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    for bone in armature_obj.pose.bones:
        bone.bone.select = True

    # Set the export settings
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(export_dir, f"{collection_name}.fbx"),
        check_existing=False,
        axis_forward='X',
        axis_up='Z',
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS',
        bake_space_transform=True,
        object_types={'ARMATURE', 'MESH'},
        use_mesh_modifiers=False,
        mesh_smooth_type='FACE',
        use_custom_props=False,
        add_leaf_bones=False,
        bake_anim=False,
        bake_anim_use_all_bones=False,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=False,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=1.0,
        use_batch_own_dir=True,
        batch_mode='OFF',
        use_metadata=True,
        path_mode='AUTO',
        embed_textures=False,
        use_selection=True,
        use_active_collection=False
    )
    
    clear_selection()
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"{collection_name} exported to {export_dir}.")


def remove_suffix(obj, collection_name):
    suffix = "_" + collection_name
    if obj.name.endswith(suffix):
        obj.name = obj.name[:-len(suffix)]
        obj.data.update()
    else:
        print("Error!")
    
    
def add_suffix(obj, collection_name):
    suffix = "_" + collection_name
    if obj.name.endswith(suffix):
        print("Error!")
    obj.name += suffix
    obj.data.update()


def check_mesh_in_collection(collection_name, mesh_name):
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        for obj in collection.objects:
            if obj.name.endswith(mesh_name):
                return (mesh_name + " found!", 'CHECKMARK')
    return (mesh_name + " not found in " + collection_name, 'ERROR')


def find_missing_meshes(higher_collection_name, lower_collection_name):
    lower_collection = bpy.data.collections.get(lower_collection_name)
    higher_collection = bpy.data.collections.get(higher_collection_name)
    if lower_collection is None:
        print(f"Error: Collection {lower_collection_name} not found.")
        return
    if higher_collection is None:
        print(f"Error: Collection {higher_collection_name} not found.")
        return
    errors = []
    for lower_obj in lower_collection.all_objects:
        if lower_obj.type == 'MESH':
            # Remove the last character of the mesh name to ignore suffixes
            lower_mesh_name = lower_obj.name[:-5]
            found = False
            for higher_obj in higher_collection.all_objects:
                if higher_obj.type == 'MESH':
                    higher_mesh_name = higher_obj.name[:-5]
                    if lower_mesh_name == higher_mesh_name:
                        found = True
                        break
            if not found:
                errors.append(f"{lower_mesh_name} present in {lower_collection_name} but not in {higher_collection_name}")
    return errors;

def clear_selection():
    for obj in bpy.context.selected_objects:
        obj.select_set(False)


### S4Export End

##Set wheel speed
def wheel_speed(self, context):
    for material in bpy.data.materials:
        material.use_nodes = True
        #if "Tire" in material.name or "tire" in material.name:
        for node in material.node_tree.nodes:
            name = ["SpeedNodeGroup", "SpeedNodeGroup.001", "SpeedNodeGroup.002"]
            for n in name:
                bpy.data.node_groups[n].nodes["Group Output"].inputs[0].default_value = self.wheel_speed

def dirt_value(self, context):               
    for mat in bpy.data.materials:
        mat.use_nodes = True
        material = mat.node_tree
        nodes = mat.node_tree.nodes
            
        for n in nodes:
            if n.bl_idname == 'ShaderNodeGroup':
                if n.node_tree.name == "Dirt/Damage_Group":
                    bpy.data.materials[mat.name].node_tree.nodes[n.name].inputs[0].default_value = self.dirt_value

def dust_value(self, context):               
    for mat in bpy.data.materials:
        mat.use_nodes = True
        material = mat.node_tree
        nodes = mat.node_tree.nodes
            
        for n in nodes:
            if n.bl_idname == 'ShaderNodeGroup':
                if n.node_tree.name == "Dirt/Damage_Group":
                    bpy.data.materials[mat.name].node_tree.nodes[n.name].inputs[1].default_value = self.dust_value

def mud_value(self, context):               
    for mat in bpy.data.materials:
        mat.use_nodes = True
        material = mat.node_tree
        nodes = mat.node_tree.nodes
            
        for n in nodes:
            if n.bl_idname == 'ShaderNodeGroup':
                if n.node_tree.name == "Dirt/Damage_Group":
                    bpy.data.materials[mat.name].node_tree.nodes[n.name].inputs[2].default_value = self.mud_value
                
def deform_value(self, context):
    collection_names = ["LODA", "LODB", "LODC","CPIT"]
    collections = bpy.data.collections if not collection_names else [col for col in bpy.data.collections if col.name in collection_names]
    mesh_shape = []
    for col in collections:
        for obj in [o for o in col.all_objects if o.type == 'MESH']:
            #for obj in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
            mesh = obj.data
            if mesh.shape_keys:
                mesh_shape.append(obj)
                for shape in obj.data.shape_keys.key_blocks:
                    shape.value = self.deform_value
                    
    for mat in bpy.data.materials:
        mat.use_nodes = True
        material = mat.node_tree
        nodes = mat.node_tree.nodes
            
        for n in nodes:
            if n.bl_idname == 'ShaderNodeGroup':
                if n.node_tree.name == "Dirt/Damage_Group":
                    bpy.data.materials[mat.name].node_tree.nodes[n.name].inputs[3].default_value = self.deform_value 

def lights_value(self, context):
    for mat in bpy.data.materials:
        mat.use_nodes = True
        material = mat.node_tree
        nodes = mat.node_tree.nodes
        if "light" in mat.name or "interior" in mat.name or "cockpit" in mat.name:   
            for n in nodes:
                if n.bl_idname == 'ShaderNodeGroup':
                    if n.node_tree.name == "S4 Vehicle Basic Shader":
                        bpy.data.materials[mat.name].node_tree.nodes[n.name].inputs[33].default_value = self.lights_value

                   
def object_search_poll(self, object):
    return object.type in ['MESH', 'CURVE']
    
def check_and_unlink_objects(object_array):
    for index, mesh in enumerate(object_array):
        for other_mesh in object_array[index+1:]:
            if mesh.data == other_mesh.data:
                other_mesh.data = mesh.data.copy()
                
def clear_old_armature_modifiers(mesh):
        for modifier in mesh.modifiers:
            if modifier.type == 'ARMATURE':
                mesh.modifiers.remove(modifier)
                
def position_tire_deform(t_name, lodA_all_tire):
    context = bpy.context
    scene = context.scene 

    deform_collection = bpy.data.collections["Tire Deformations"]
    for obj_A in lodA_all_tire:
        if obj_A.type == "MESH" and t_name in obj_A.name:
            bpy.context.scene.objects[obj_A.name].select_set(True)
            obs = context.selected_objects
            n = len(obs)
            assert(n)
            scene.cursor.location = sum([o.matrix_world.translation for o in obs], Vector()) / n
            bpy.context.scene.objects[obj_A.name].select_set(False)

            for obj in deform_collection.all_objects:
                if obj.type == "ARMATURE" and t_name in obj.name:
                    #print(obj.name)
                    bpy.context.scene.objects[obj.name].select_set(True)
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')
                
                    for area in bpy.context.screen.areas:
                        if area.type == 'VIEW_3D':
                            override = bpy.context.copy()
                            override['area'] = area
                            override['region'] = area.regions[4]
                            bpy.ops.view3d.snap_selected_to_cursor(override, use_offset=False)
                bpy.context.scene.objects[obj.name].select_set(False)
           
def transfer_tire_weight(t_name, lodA_all_tire):
    context = bpy.context
    scene = context.scene 

    deform_collection = bpy.data.collections["Tire Deformations"]
    for obj_A in lodA_all_tire:
        bpy.ops.object.select_all(action='DESELECT') #deselecting everything
        if obj_A.type == "MESH" and t_name in obj_A.name:
            bpy.context.scene.objects[obj_A.name].select_set(True) #selecting target
            for obj in deform_collection.all_objects:
                if t_name in obj.name:
                    for o in bpy.data.objects:
                        if o.parent == bpy.data.objects[obj.name]:
                            bpy.data.objects[o.name].select_set(True)
                            bpy.context.view_layer.objects.active = bpy.data.objects[obj_A.name] #setting target as active
                            bpy.ops.paint.weight_paint_toggle() #entering Weight Paint mode
                            bpy.ops.object.data_transfer(use_reverse_transfer=True, data_type='VGROUP_WEIGHTS', vert_mapping='POLYINTERP_NEAREST', layers_select_src='NAME', layers_select_dst='ALL', mix_mode='REPLACE') #transferring weights
                            bpy.ops.paint.weight_paint_toggle() #exit Weight Paint Mode
                            
def addmodifier_linktire_deform(t_name, lodA_all_tire):
    context = bpy.context
    scene = context.scene 

    deform_collection = bpy.data.collections["Tire Deformations"]
    for obj_A in lodA_all_tire:
        if obj_A.type == "MESH" and t_name in obj_A.name:
            bpy.context.scene.objects[obj_A.name].select_set(True) #selecting target
            bpy.context.view_layer.objects.active = obj_A
            bpy.ops.object.modifier_add(type="ARMATURE")
            bpy.context.object.modifiers["Armature"].name = "Armature"
            for obj in deform_collection.all_objects:
                if obj.type == "ARMATURE" and t_name in obj.name:
                    bpy.context.object.modifiers["Armature"].object = obj
                    bpy.context.scene.objects[obj_A.name].select_set(False) #deselect target

def transfer_vertex_ao(src_obj):
    context = bpy.context
    scene = context.scene 
    bpy.ops.object.modifier_add(type='DATA_TRANSFER')
    bpy.context.object.modifiers["DataTransfer"].object = src_obj
    bpy.context.object.modifiers["DataTransfer"].use_vert_data = True
    bpy.context.object.modifiers["DataTransfer"].data_types_verts = {'COLOR_VERTEX'}
    bpy.context.object.modifiers["DataTransfer"].vert_mapping = 'POLYINTERP_NEAREST'


    bpy.ops.object.datalayout_transfer(modifier="DataTransfer")

    bpy.ops.object.modifier_apply(modifier="DataTransfer")
    
                    

class CUSTOM_objectCollection(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    type: StringProperty()
    message: StringProperty()
    id: IntProperty()


class CUSTOM_OT_clearList(bpy.types.Operator):
    bl_idname = "custom.clear_list"
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


class MATERIAL_UL_matslots_example(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, "message", text=item.type, emboss=False, icon_value=icon)


class ValidationToolMainPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Veh Validator"
    bl_idname = "OBJECT_PT_Validation"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Vehicle"
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

        row = layout.row()
        row.label(text="Run all check")

        row1 = layout.row()
        row1.operator("mesh.initialcheck", text="Check Scene")
        
              
        if scn.checkResult_all == True:
            layout.template_list("MATERIAL_UL_matslots_example", "", scn, "custom", scn, "custom_index")

            row = layout.row()
            row.operator("custom.clear_list", text="Clear and hide result box.")

        row11 = layout.row()
        row11.label(text= globalVariables.version)
        
class ShaderToolPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Shader Tool"
    bl_idname = "OBJECT_PT_Shader"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Vehicle"
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}
   
    def draw(self, context):
        scn = context.scene
        layout = self.layout
     
        obj = context.object
        
        row3 = layout.row()
        row3.operator("mesh.basicshader", text="S4 Vehicle Basic Shader")
        row4 = layout.row()
        row4.operator("mesh.bodyworkshader", text="S4 Vehicle Bodywork Shader")
        row5 = layout.row()
        row5.operator("mesh.glassshader", text="S4 Vehicle Glass Shader")
        row5 = layout.row()
        row5.operator("mesh.lightglassshader", text="S4 Vehicle LightGlass Shader")
        row6 = layout.row()
        row6.operator("mesh.tireshader", text="S4 Vehicle Tire Shader")
        row7 = layout.row()
        row7.operator("mesh.wheelshader", text="S4 Vehicle Wheels Shader")
        row8 = layout.row()
        row8.label(text="Other Node")
        row9 = layout.row()
        row9.operator("mesh.dirtshader", text="S4 Vehicle Dirt/Damage")
        row10 = layout.row()
        row10.operator("mesh.speednode", text="S4 Wheel Speed")

###########################################################################################################

# Operator to link the selected material to the selected material slot of the active object
class MATERIAL_OT_link_external_to_slot(bpy.types.Operator):
    bl_idname = "material.link_external_to_slot"
    bl_label = "Link External Material to Slot"
    bl_description = "Link the selected external material to the selected material slot of the active object"
    
    material_name: bpy.props.StringProperty()

    def execute(self, context):
        filepath = SHADER_BLEND_PATH
        if not os.path.isfile(filepath):
            self.report({'ERROR'}, "File not found")
            return {'CANCELLED'}
        
        with bpy.data.libraries.load(filepath, link=True) as (data_from, data_to):
            if self.material_name in data_from.materials:
                data_to.materials = [self.material_name]
            else:
                self.report({'ERROR'}, f"Material {self.material_name} not found in the file")
                return {'CANCELLED'}

        material = data_to.materials[0]
        if material is None:
            self.report({'ERROR'}, f"Material {self.material_name} could not be loaded")
            return {'CANCELLED'}
        
        obj = context.active_object
        if obj is not None and obj.type == 'MESH':
            slot_index = obj.active_material_index
            if 0 <= slot_index < len(obj.material_slots):
                obj.material_slots[slot_index].material = material
                self.report({'INFO'}, f"Material {material.name} linked to slot {slot_index} of {obj.name}")
            else:
                self.report({'ERROR'}, f"Invalid material slot index: {slot_index}")
                return {'CANCELLED'}
        else:
            self.report({'ERROR'}, "No active mesh object")
            return {'CANCELLED'}
        
        return {'FINISHED'}

# Property Group to hold external material data
class ExternalMaterialItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()


# Panel to display external materials
class MATERIAL_PT_external_linker_panel(bpy.types.Panel):
    bl_label = "S4 Material Linker"
    bl_idname = "MATERIAL_PT_external_linker_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'S4 Vehicle'

    # def draw(self, context):
    #     layout = self.layout
    #     scene = context.scene

    #     col = layout.column()
    #     col.operator("material.load_external_materials", text="Load Materials")
        
    #     col.separator()
    #     col.label(text="Materials:")
        
    #     for mat in scene.external_materials:
    #         row = col.row()
    #         row.label(text=mat.name)
    #         op = row.operator("material.link_external_to_slot", text="Link")
    #         op.material_name = mat.name

#############################################################################################################

class UtilitiToolPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Utilities Tool"
    bl_idname = "OBJECT_PT_Utilities"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Vehicle"
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        scn = context.scene
        layout = self.layout
     
        obj = context.object
        
        row1 = layout.row()
        allmat = bpy.data.materials

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas: # iterate through areas in current screen
                if area.type == 'VIEW_3D':
                    for space in area.spaces: # iterate through spaces in current VIEW_3D area
                        if space.type == 'VIEW_3D': # check if space is a 3D view
                            if space.shading.type == 'SOLID':   
                                backface = bpy.context.space_data.shading.show_backface_culling
                            else:
                                for mat in allmat:
                                    backface = bpy.data.materials[mat.name].use_backface_culling
        if backface == False :
            row1.alert = False
        else:
            row1.alert = True
        row1.operator("mesh.backface", text="Toggle Backface Culling")
        
        row2 = layout.row()
        for area in bpy.context.workspace.screens[0].areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    if space.overlay.show_wireframes == True:
                        row2.alert = True
                    else:
                        row2.alert = False
        row2.operator("mesh.viewwireframe", text="Toggle Wireframe")
        
        row3 = layout.row()
        row3.operator("mesh.viewportcol", text="Change Viewport Color")
        
        row3 = layout.row()
        row3.operator("mesh.selngon", text="Select N-Gons Face")
        
        row4 = layout.row()
        row4.label(text="Other Check:")
        
        row5 = layout.row()
        row5.prop(scn, 'dirt_value', slider=True)
        
        row5 = layout.row()
        row5.prop(scn, 'dust_value', slider=True)
        
        row5 = layout.row()
        row5.prop(scn, 'mud_value', slider=True)
        
        row5 = layout.row()
        row5.prop(scn, 'deform_value', slider=True)
        
        row6 = layout.row()
        row6.prop(scn, 'wheel_speed', slider=True)
        
        row6 = layout.row()
        row6.prop(scn, 'lights_value', slider=True)
        
        row7 = layout.row()
        row7.label(text="Other tools")
        
        row3 = layout.row()
        row3.operator("s4veh.setupscene", text="Setup S4 Scene")
        
        row3 = layout.row()
        row3.operator("s4veh.correctmat", text="Correct Duplicate Material")
        
        row3 = layout.row()
        row3.operator("s4veh.removeshapekey", text="Remove Shapekey")
        
        row3 = layout.row()
        row3.operator("s4veh.applylattice", text="Apply Lattice as Shapekey")
        
        row3 = layout.row()
        row3.operator("s4veh.keyshapekey", text="Keyframe for all Shapekey")

class TireDeformPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Tire Deform Tool"
    bl_idname = "OBJECT_PT_TireDeform"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Vehicle"
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        scn = context.scene
        layout = self.layout
     
        obj = context.object
        
        row1 = layout.row()
        row1.label(text = "Tire RF")
        row1.prop(scn, 'tire_RF', text = "")

        row2 = layout.row()
        row2.label(text = "Tire RR")
        row2.prop(scn, 'tire_RR', text = "")

        row3 = layout.row()
        row3.label(text = "Tire LF")
        row3.prop(scn, 'tire_LF', text = "")

        row4 = layout.row()
        row4.label(text = "Tire LR")
        row4.prop(scn, 'tire_LR', text = "")
        
        row5 = layout.row()
        row5.operator('mesh.createtiredeform', text = "Create Tire Deform Objects")
        row6 = layout.row()
        row6.operator('mesh.applytireweight', text = "Apply Weight")
        
class VertexAOPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Vertex Ambient"
    bl_idname = "OBJECT_PT_VertexAO"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Vehicle"
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        scn = context.scene
        layout = self.layout
     
        obj = context.object
        
        row1 = layout.row()
        row1.operator('mesh.bakevertexao', text = "Bake Vertex AO")
        
        row1 = layout.row()
        row1.operator('mesh.exitbakevertexao', text = "Restore Node Connection")
        
        

class S4VehLODRigging(bpy.types.Panel, globalVariables):
    bl_label = "S4 LOD Rigging"
    bl_idname = "S4Veh_LOD_Rig"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Vehicle"
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        scn = context.scene
        layout = self.layout
     
        obj = context.object
        
        row1 = layout.row()       
        row1.label(text = "Select Part Rig:")
        
        row3 = layout.row()
        row3.label(text = "Body Base")
        row3.prop(scn, 's4veh_body_base', text = "")
        
        row3 = layout.row()
        row3.label(text = "WHEEL LF")
        row3.prop(scn, 's4veh_wheel_lf', text = "")
        
        row3 = layout.row()
        row3.label(text = "WHEEL LR")
        row3.prop(scn, 's4veh_wheel_lr', text = "")
        
        row3 = layout.row()
        row3.label(text = "WHEEL RF")
        row3.prop(scn, 's4veh_wheel_rf', text = "")
        
        row3 = layout.row()
        row3.label(text = "WHEEL RR")
        row3.prop(scn, 's4veh_wheel_rr', text = "")
        
        row3 = layout.row()
        row3.label(text = "STEERINGWHEEL")
        row3.prop(scn, 's4veh_steeringwheel', text = "")
        
        row4 = layout.row()
        row4.operator('s4veh.riglod', text = "Rig Vehicle")
        
class LODValidPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 LOD Validation"
    bl_idname = "OBJECT_PT_Lodcheck"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Vehicle"
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        lod_holder = scn.lod_holder
        
        row1 = layout.row()
        row1.prop(lod_holder, "lod_list", text="Select LOD")
        
        row2 = layout.row()
        row2.operator('mesh.switchlod', text = "Swap")
        
        row2 = layout.row()
        row2.operator('mesh.enablelod', text = "Enable All LOD Viewport")
           
             
class ExportPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Exporter"
    bl_idname = "MY_TEST_PANEL_PT"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "S4 Vehicle"
    bl_options = {"DEFAULT_CLOSED"}
        
    def draw(self, context):
        layout = self.layout        
        box = layout.box()
        
        error_messages = ""
        for mesh in meshes_to_check_LODA:
            result, icon = check_mesh_in_collection(*mesh)
            if icon == 'ERROR':
                error_messages = result
                box.label(text=result, icon='ERROR')
                
        for mesh in meshes_to_check_LODB:
            result, icon = check_mesh_in_collection(*mesh)
            if icon == 'ERROR':
                error_messages = result
                box.label(text=result, icon='ERROR')
                
        for mesh in meshes_to_check_LODC:
            result, icon = check_mesh_in_collection(*mesh)
            if icon == 'ERROR':
                error_messages = result
                box.label(text=result, icon='ERROR')
        
        for mesh in meshes_to_check_LODD:
            result, icon = check_mesh_in_collection(*mesh)
            if icon == 'ERROR':
                error_messages = result
                box.label(text=result, icon='ERROR')
        
        for mesh in meshes_to_check_CPIT:
            result, icon = check_mesh_in_collection(*mesh)
            if icon == 'ERROR':
                error_messages = result
                box.label(text=result, icon='ERROR')
        
        if not error_messages:
            box.label(text="All meshes present.", icon='CHECKMARK')
                
        lod_erros = []
        lod_erros.extend(find_missing_meshes("LODA", "LODB"))
        lod_erros.extend(find_missing_meshes("LODB", "LODC"))
        lod_erros.extend(find_missing_meshes("LODC", "LODD"))
        for error in lod_erros:
            box.label(text=error, icon='CANCEL')
        
        row = layout.row()
        if not lod_erros:
            box.label(text="LOD structure is valid.", icon='CHECKMARK')
            row.operator("mesh.export_vehicle_operator", icon="EXPORT")
        else:
            row.operator("mesh.export_vehicle_operator", icon="CANCEL", emboss=False).enabled = False
 
class ExportVehicleOperator(bpy.types.Operator, ExportPanel):
    bl_idname = "mesh.export_vehicle_operator"
    bl_label = "Export Vehicle"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        process_collection("LODA")
        process_collection("LODB")
        process_collection("LODC")
        process_collection("LODD")
        print("Finished")
        return {'FINISHED'} 


class InitialCheck(bpy.types.Operator, ValidationToolMainPanel, globalVariables):
    bl_idname = "mesh.initialcheck"
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

        if len(globalVariables.meshObjs) != 0:
            bpy.context.view_layer.objects.active = globalVariables.meshObjs[0]

            #        bpy.context.view_layer.objects.active = None
            
            colname = ["LODA", "LODB", "LODC", "LODD", "CPIT"]
            
            ##Check meshname
            MeshnameList = ["BODY_LOD", "BONNET_LOD", "BUMPER_F_LOD", "BUMPER_LR_LOD",
                            "BUMPER_RR_LOD", "CALIPER_LF_LOD", "CALIPER_LR_LOD", "CALIPER_RF_LOD",
                            "CALIPER_RR_LOD", "CHASSIS_LOD", "DISC_LF_LOD", "DISC_LR_LOD",
                            "DISC_RF_LOD", "DISC_RR_LOD", "DIVEPLANE_R1_LOD", "DIVEPLANE_L1_LOD", "INTERIOR_LOD",
                            "LIGHTS_LOD", "STEERINGWHEEL_LOD", "TIRE_LF_LOD", "TIRE_LR_LOD", "TIRE_RF_LOD",
                            "TIRE_RR_LOD", "WHEEL_LF_BLUR_LOD", "WHEEL_LF_LOD", "WHEEL_LR_BLUR_LOD", "WHEEL_LR_LOD",
                            "WHEEL_RF_BLUR_LOD", "WHEEL_RF_LOD","WHEEL_RR_BLUR_LOD", "WHEEL_RR_LOD", "WING_LOD", "BODY_CPIT",
                            "BONNET_CPIT","BUMPER_F_CPIT", "CHASSIS_CPIT", "DISPLAY_CPIT", "EXTANIM_CPIT", "INTANIM_CPIT",
                            "INTERIOR2_CPIT", "INTERIOR_CPIT", "STEERINGWHEEL_CPIT", "TIRE_LF_CPIT", "TIRE_RF_CPIT", "WHEEL_LF_CPIT",
                            "WHEEL_RF_CPIT", "WINDOWS_CPIT", "DRIVERNAME_CPIT", "WIPER_LOD", "DISC_LF_CPIT", "CALIPER_LF_CPIT", "DISC_RF_CPIT",
                            "CALIPER_RF_CPIT", "LIGHTS_CPIT", "NEEDLE_TACH_CPIT", "NEEDLE_WATER_CPIT", "NEEDLE_OILT_CPIT", "GEARSHIFT_CPIT",
                            "NEEDLE_OILP_CPIT", "NEEDLE_FUELP_CPIT", "GAUGE_GLASS_CPIT", "REARWING_CPIT", "PANEL_R_LOD", "PANEL_L_LOD", "MIRROR_R_LOD",
                            "MIRROR_L_LOD"]
            
            
            # Iterate through each collection
            for collection in bpy.data.collections:
                # Check if the collection name contains any of the specified substrings
                if any(col == collection.name for col in colname):
                    for meshObj in collection.objects:
                        if meshObj.type == 'ARMATURE' or "deformation" in meshObj.name:
                            continue
                        isCarname = False
                        for meshname in MeshnameList:
                            if meshname in meshObj.name:
                                isCarname = True
                                break
                        if isCarname:
                            continue
                        message = str(meshObj.name)
                        add_item(scn.custom, "Mesh Name", message)

            ##Check Material node type
            allmat = bpy.data.materials
            for mat in allmat:
                if "Dots Stroke" in mat.name or "LCDisplay" in mat.name or "VirtualMirror" in mat.name or "virtualmirror" in mat.name or "Master deform tire" in mat.name:
                    continue
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                for n in nodes:
                    if "Principled BSDF" in n.name:
                        message = str(mat.name)
                        add_item(scn.custom, "MaterialNode", message)
                        
            
            ##Check UVset name
            uvmesh = []
            # Iterate through each collection
            for collection in bpy.data.collections:
                # Check if the collection name contains any of the specified substrings
                if any(col == collection.name for col in colname):
                    for meshObj in collection.objects:
                        if meshObj.type == "MESH":
                            for u in meshObj.data.uv_layers:
                                if not "UVMap" in u.name:
                                    if not meshObj in uvmesh:
                                        uvmesh.append(meshObj)
            for o in uvmesh:
                message = str(o.name)
                add_item(scn.custom,"UVChannel", message)
            
            #Check N-gon mesh
            mesh_n_gon = []
            for meshngon in objs:
                if meshngon.type == "MESH":
                    for p in meshngon.data.polygons:
                        if len(p.vertices) > 4:
                            if not meshngon in mesh_n_gon:
                                mesh_n_gon.append(meshngon)
            for ngon_obj in mesh_n_gon:
                message = str(ngon_obj.name)
                add_item(scn.custom,"N-Gons mesh", message)
                
            ##Check Unit
            scale_unit = bpy.context.scene.unit_settings.scale_length
            leng_unit = bpy.context.scene.unit_settings.length_unit
            system_unit = bpy.context.scene.unit_settings.system
            
            if scale_unit != 1:
                message = "Unit Scale must be 1"
                add_item(scn.custom, "Unit Scale", message)
    
            if leng_unit != "METERS":
                message = "Length Unit must be Meters"
                add_item(scn.custom, "Unit Scale", message)

            if system_unit != "METRIC":
                message = "Unit System must be Metric"
                add_item(scn.custom, "Unit System", message)
                
            ##Finish check result
            scn.checkResult_all = True
            confmessage = ["Checking Finished."]
            ShowMessageBox(confmessage, "S4 Validation", "CHECKMARK")
            return {"FINISHED"}
            
        else:
            scn.checkResult_all = True
            confmessage = ["Scene in empty."]
            ShowMessageBox(confmessage, "S4 Validation", "ERROR")
            return {"FINISHED"}

class BasicShader(bpy.types.Operator, ShaderToolPanel, globalVariables):
    bl_idname = "mesh.basicshader"
    bl_label = "Generate Shader"
    bl_description = "Auto Generate S4 Custom Shader Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    def __init__(self):
        # Define the path to the blend file containing the custom node
        self.source_file = SHADER_BLEND_PATH  
    '''
    def import_file(self):
        # Check if the file exists
        if not os.path.isfile(self.source_file):
            self.report({'ERROR'}, "S4 Shader Source Node not found {}".format(self.source_file))
            return {'CANCELLED'}
        return {'FINISHED'}
    '''

    def instantiate_group(self, nodes, data_block_name):
        group = nodes.new(type='ShaderNodeGroup')
        group.node_tree = bpy.data.node_groups[data_block_name]
        return group

    def import_node_group(self, node_group_name):
        # Load the custom node group from the blend file
        with bpy.data.libraries.load(self.source_file, link=True) as (data_from, data_to):
            if node_group_name in data_from.node_groups:
                data_to.node_groups = [node_group_name]

        # Check if the node group was successfully loaded
        if not data_to.node_groups or not data_to.node_groups[0]:
            confmessage = ["Failed to Generate Shader Node"]
            ShowMessageBox(confmessage, "S4 Basic Shader", "ERROR")
            return {'CANCELLED'}

        # Report successful import
        confmessage = ["Successfully Generate Basic Shader"]
        ShowMessageBox(confmessage, "S4 Basic Shader", "CHECKMARK")
        return {'FINISHED'}

    def execute(self, context):
        # Import the custom node group
        self.import_node_group("S4 Vehicle Basic Shader")
        idx = bpy.context.object.active_material_index
        self.instantiate_group(bpy.context.object.material_slots[idx].material.node_tree.nodes, 'S4 Vehicle Basic Shader')
        
        #Orphans Purge
        override = bpy.context.copy()
        override["area.type"] = ['OUTLINER']
        override["display_mode"] = ['ORPHAN_DATA']
        bpy.ops.outliner.orphans_purge(override) 
        return {'FINISHED'}
        
class BodyworkShader(bpy.types.Operator, ShaderToolPanel, globalVariables):
    bl_idname = "mesh.bodyworkshader"
    bl_label = "Generate Shader"
    bl_description = "Auto Generate S4 Custom Shader Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    def __init__(self):
        # Define the path to the blend file containing the custom node
        self.source_file = SHADER_BLEND_PATH  
    
    def instantiate_group(self, nodes, data_block_name):
        group = nodes.new(type='ShaderNodeGroup')
        group.node_tree = bpy.data.node_groups[data_block_name]
        return group

    def import_node_group(self, node_group_name):
        # Load the custom node group from the blend file
        with bpy.data.libraries.load(self.source_file, link=True) as (data_from, data_to):
            if node_group_name in data_from.node_groups:
                data_to.node_groups = [node_group_name]

        # Check if the node group was successfully loaded
        if not data_to.node_groups or not data_to.node_groups[0]:
            confmessage = ["Failed to Generate Shader Node"]
            ShowMessageBox(confmessage, "S4 Bodywork Shader", "ERROR")
            return {'CANCELLED'}

        # Report successful import
        confmessage = ["Successfully Generate Shader Node"]
        ShowMessageBox(confmessage, "S4 Bodywork Shader", "CHECKMARK")
        return {'FINISHED'}

    def execute(self, context):
        # Import the custom node group
        self.import_node_group("S4 Vehicle Bodywork Shader")
        idx = bpy.context.object.active_material_index
        self.instantiate_group(bpy.context.object.material_slots[idx].material.node_tree.nodes, 'S4 Vehicle Bodywork Shader')
        
        #Orphans Purge
        override = bpy.context.copy()
        override["area.type"] = ['OUTLINER']
        override["display_mode"] = ['ORPHAN_DATA']
        bpy.ops.outliner.orphans_purge(override) 
        return {'FINISHED'}
        
class GlassShader(bpy.types.Operator, ShaderToolPanel, globalVariables):
    bl_idname = "mesh.glassshader"
    bl_label = "Generate Shader"
    bl_description = "Auto Generate S4 Custom Shader Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    def __init__(self):
        # Define the path to the blend file containing the custom node
        self.source_file = SHADER_BLEND_PATH  
    
    def instantiate_group(self, nodes, data_block_name):
        group = nodes.new(type='ShaderNodeGroup')
        group.node_tree = bpy.data.node_groups[data_block_name]
        return group

    def import_node_group(self, node_group_name):
        # Load the custom node group from the blend file
        with bpy.data.libraries.load(self.source_file, link=True) as (data_from, data_to):
            if node_group_name in data_from.node_groups:
                data_to.node_groups = [node_group_name]

        # Check if the node group was successfully loaded
        if not data_to.node_groups or not data_to.node_groups[0]:
            confmessage = ["Failed to Generate Shader Node"]
            ShowMessageBox(confmessage, "S4 Glass Shader", "ERROR")
            return {'CANCELLED'}

        # Report successful import
        confmessage = ["Successfully Generate Shader Node"]
        ShowMessageBox(confmessage, "S4 Glass Shader", "CHECKMARK")
        return {'FINISHED'}

    def execute(self, context):
        # Import the custom node group
        self.import_node_group("S4 Vehicle Glass Shader")
        idx = bpy.context.object.active_material_index
        self.instantiate_group(bpy.context.object.material_slots[idx].material.node_tree.nodes, 'S4 Vehicle Glass Shader')
        
        #Orphans Purge
        override = bpy.context.copy()
        override["area.type"] = ['OUTLINER']
        override["display_mode"] = ['ORPHAN_DATA']
        bpy.ops.outliner.orphans_purge(override) 
        return {'FINISHED'}
        
class LightGlassShader(bpy.types.Operator, ShaderToolPanel, globalVariables):
    bl_idname = "mesh.lightglassshader"
    bl_label = "Generate Shader"
    bl_description = "Auto Generate S4 Custom Shader Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    def __init__(self):
        # Define the path to the blend file containing the custom node
        self.source_file = SHADER_BLEND_PATH  
    
    def instantiate_group(self, nodes, data_block_name):
        group = nodes.new(type='ShaderNodeGroup')
        group.node_tree = bpy.data.node_groups[data_block_name]
        return group

    def import_node_group(self, node_group_name):
        # Load the custom node group from the blend file
        with bpy.data.libraries.load(self.source_file, link=True) as (data_from, data_to):
            if node_group_name in data_from.node_groups:
                data_to.node_groups = [node_group_name]

        # Check if the node group was successfully loaded
        if not data_to.node_groups or not data_to.node_groups[0]:
            confmessage = ["Failed to Generate Shader Node"]
            ShowMessageBox(confmessage, "S4 Light Glass Shader", "ERROR")
            return {'CANCELLED'}

        # Report successful import
        confmessage = ["Successfully Generate Shader Node"]
        ShowMessageBox(confmessage, "S4 Glass Shader", "CHECKMARK")
        return {'FINISHED'}

    def execute(self, context):
        # Import the custom node group
        self.import_node_group("S4 Vehicle LightGlass Shader")
        idx = bpy.context.object.active_material_index
        self.instantiate_group(bpy.context.object.material_slots[idx].material.node_tree.nodes, 'S4 Vehicle LightGlass Shader')
        
        #Orphans Purge
        override = bpy.context.copy()
        override["area.type"] = ['OUTLINER']
        override["display_mode"] = ['ORPHAN_DATA']
        bpy.ops.outliner.orphans_purge(override) 
        return {'FINISHED'}
        
class TireShader(bpy.types.Operator, ShaderToolPanel, globalVariables):
    bl_idname = "mesh.tireshader"
    bl_label = "Generate Shader"
    bl_description = "Auto Generate S4 Custom Shader Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    def __init__(self):
        # Define the path to the blend file containing the custom node
        self.source_file = SHADER_BLEND_PATH  
    
    def instantiate_group(self, nodes, data_block_name):
        group = nodes.new(type='ShaderNodeGroup')
        group.node_tree = bpy.data.node_groups[data_block_name]
        return group

    def import_node_group(self, node_group_name):
        # Load the custom node group from the blend file
        with bpy.data.libraries.load(self.source_file, link=True) as (data_from, data_to):
            if node_group_name in data_from.node_groups:
                data_to.node_groups = [node_group_name]

        # Check if the node group was successfully loaded
        if not data_to.node_groups or not data_to.node_groups[0]:
            confmessage = ["Failed to Generate Shader Node"]
            ShowMessageBox(confmessage, "S4 Tire Shader", "ERROR")
            return {'CANCELLED'}

        # Report successful import
        confmessage = ["Successfully Generate Shader Node"]
        ShowMessageBox(confmessage, "S4 Tire Shader", "CHECKMARK")
        return {'FINISHED'}

    def execute(self, context):
        # Import the custom node group
        self.import_node_group("S4 Vehicle Tire Shader")
        idx = bpy.context.object.active_material_index
        self.instantiate_group(bpy.context.object.material_slots[idx].material.node_tree.nodes, 'S4 Vehicle Tire Shader')
        
        #Orphans Purge
        override = bpy.context.copy()
        override["area.type"] = ['OUTLINER']
        override["display_mode"] = ['ORPHAN_DATA']
        bpy.ops.outliner.orphans_purge(override) 
        return {'FINISHED'}

class WheelShader(bpy.types.Operator, ShaderToolPanel, globalVariables):
    bl_idname = "mesh.wheelshader"
    bl_label = "Generate Shader"
    bl_description = "Auto Generate S4 Custom Shader Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    def __init__(self):
        # Define the path to the blend file containing the custom node
        self.source_file = SHADER_BLEND_PATH  
    
    def instantiate_group(self, nodes, data_block_name):
        group = nodes.new(type='ShaderNodeGroup')
        group.node_tree = bpy.data.node_groups[data_block_name]
        return group

    def import_node_group(self, node_group_name):
        # Load the custom node group from the blend file
        with bpy.data.libraries.load(self.source_file, link=True) as (data_from, data_to):
            if node_group_name in data_from.node_groups:
                data_to.node_groups = [node_group_name]

        # Check if the node group was successfully loaded
        if not data_to.node_groups or not data_to.node_groups[0]:
            confmessage = ["Failed to Generate Shader Node"]
            ShowMessageBox(confmessage, "S4 Wheel Shader", "ERROR")
            return {'CANCELLED'}

        # Report successful import
        confmessage = ["Successfully Generate Shader Node"]
        ShowMessageBox(confmessage, "S4 Wheel Shader", "CHECKMARK")
        return {'FINISHED'}

    def execute(self, context):
        # Import the custom node group
        self.import_node_group("S4 Vehicle Wheels Shader")
        idx = bpy.context.object.active_material_index
        self.instantiate_group(bpy.context.object.material_slots[idx].material.node_tree.nodes, 'S4 Vehicle Wheels Shader')
        
        #Orphans Purge
        override = bpy.context.copy()
        override["area.type"] = ['OUTLINER']
        override["display_mode"] = ['ORPHAN_DATA']
        bpy.ops.outliner.orphans_purge(override) 
        return {'FINISHED'}

class DirtShader(bpy.types.Operator, ShaderToolPanel, globalVariables):
    bl_idname = "mesh.dirtshader"
    bl_label = "Generate Shader"
    bl_description = "Auto Generate S4 Custom Shader Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    def __init__(self):
        # Define the path to the blend file containing the custom node
        self.source_file = SHADER_BLEND_PATH  
    
    def instantiate_group(self, nodes, data_block_name):
        group = nodes.new(type='ShaderNodeGroup')
        group.node_tree = bpy.data.node_groups[data_block_name]
        return group

    def import_node_group(self, node_group_name):
        # Load the custom node group from the blend file
        with bpy.data.libraries.load(self.source_file, link=True) as (data_from, data_to):
            if node_group_name in data_from.node_groups:
                data_to.node_groups = [node_group_name]

        # Check if the node group was successfully loaded
        if not data_to.node_groups or not data_to.node_groups[0]:
            confmessage = ["Failed to Generate Shader Node"]
            ShowMessageBox(confmessage, "S4 Dirt Shader", "ERROR")
            return {'CANCELLED'}

        # Report successful import
        confmessage = ["Successfully Generate Shader Node"]
        ShowMessageBox(confmessage, "S4 Dirt Shader", "CHECKMARK")
        return {'FINISHED'}

    def execute(self, context):
        # Import the custom node group
        self.import_node_group("Dirt/Damage_Group")
        idx = bpy.context.object.active_material_index
        self.instantiate_group(bpy.context.object.material_slots[idx].material.node_tree.nodes, 'Dirt/Damage_Group')
        
        #Orphans Purge
        override = bpy.context.copy()
        override["area.type"] = ['OUTLINER']
        override["display_mode"] = ['ORPHAN_DATA']
        bpy.ops.outliner.orphans_purge(override) 
        return {'FINISHED'}
        
class SpeedNode(bpy.types.Operator, ShaderToolPanel, globalVariables):
    bl_idname = "mesh.speednode"
    bl_label = "Generate Speed Node"
    bl_description = "Auto Generate S4 Custom Shader Node"
    bl_options = {'REGISTER', 'UNDO'}
    
    def __init__(self):
        # Define the path to the blend file containing the custom node
        self.source_file = SHADER_BLEND_PATH  
    
    def instantiate_group(self, nodes, data_block_name):
        group = nodes.new(type='ShaderNodeGroup')
        group.node_tree = bpy.data.node_groups[data_block_name]
        return group

    def import_node_group(self, node_group_name):
        # Load the custom node group from the blend file
        with bpy.data.libraries.load(self.source_file, link=True) as (data_from, data_to):
            if node_group_name in data_from.node_groups:
                data_to.node_groups = [node_group_name]

        # Check if the node group was successfully loaded
        if not data_to.node_groups or not data_to.node_groups[0]:
            confmessage = ["Failed to Generate Shader Node"]
            ShowMessageBox(confmessage, "S4 SpeedNode", "ERROR")
            return {'CANCELLED'}

        # Report successful import
        confmessage = ["Successfully Generate Shader Node"]
        ShowMessageBox(confmessage, "S4 SpeedNode", "CHECKMARK")
        return {'FINISHED'}

    def execute(self, context):
        # Import the custom node group
        self.import_node_group("SpeedNodeGroup")
        idx = bpy.context.object.active_material_index
        self.instantiate_group(bpy.context.object.material_slots[idx].material.node_tree.nodes, 'SpeedNodeGroup')
        
        #Orphans Purge
        override = bpy.context.copy()
        override["area.type"] = ['OUTLINER']
        override["display_mode"] = ['ORPHAN_DATA']
        bpy.ops.outliner.orphans_purge(override) 
        return {'FINISHED'}

class ToggleBackFace(bpy.types.Operator, UtilitiToolPanel, globalVariables):
    bl_idname = "mesh.backface"
    bl_label = "Toggle Backface"
    bl_description = "Toggle Backface Culling For Checking"
    bl_options = {'REGISTER', 'UNDO'}
    
    def backface_to_fail(self):
        space_shading = True
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas: # iterate through areas in current screen
                if area.type == 'VIEW_3D':
                    for space in area.spaces: # iterate through spaces in current VIEW_3D area
                        if space.type == 'VIEW_3D': # check if space is a 3D view
                            if space.shading.type == 'SOLID':
                                space_shading = True
                            if space.shading.type == 'MATERIAL':
                                space_shading = False
        area_type = 'VIEW_3D'
        areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]
        
        if len(areas) <= 0:
            raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")
        if space_shading == True:
            with bpy.context.temp_override(area=areas[0]):
                bpy.context.space_data.shading.show_backface_culling = False
               
        else:
            allmat = bpy.data.materials
            for mat in allmat:               
                bpy.data.materials[mat.name].use_backface_culling = False
    
    def execute(self, context):
        #turn all too false
        #self.backface_to_fail()
        
        space_shading = True
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas: # iterate through areas in current screen
                if area.type == 'VIEW_3D':
                    for space in area.spaces: # iterate through spaces in current VIEW_3D area
                        if space.type == 'VIEW_3D': # check if space is a 3D view
                            if space.shading.type == 'SOLID':
                                space_shading = True
                            if space.shading.type == 'MATERIAL':
                                space_shading = False
        area_type = 'VIEW_3D'
        areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]
        
        if len(areas) <= 0:
            raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")
        if space_shading == True:
            with bpy.context.temp_override(area=areas[0]):
                bpy.context.space_data.shading.show_backface_culling = not bpy.context.space_data.shading.show_backface_culling
                
        #else:
            #allmat = bpy.data.materials
            #for mat in allmat:               
                #bpy.data.materials[mat.name].use_backface_culling = not bpy.data.materials[mat.name].use_backface_culling
                
                  
        return {'FINISHED'}
        
class ToggleViewColor(bpy.types.Operator, UtilitiToolPanel, globalVariables):
    bl_idname = "mesh.viewportcol"
    bl_label = "Toggle Viewport Color"
    bl_description = "Change Viewport Color for backface checking"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        '''
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas: # iterate through areas in current screen
                if area.type == 'VIEW_3D':
                    for space in area.spaces: # iterate through spaces in current VIEW_3D area
                        if space.type == 'VIEW_3D': # check if space is a 3D view
                            space.shading.type = 'SOLID'
        '''
        area_type = 'VIEW_3D'
        areas  = [area for area in bpy.context.window.screen.areas if area.type == area_type]
        
        default_color = (0.2392,0.2392,0.2392)
        new_color = (1,0,0.815)
        current_color = str(bpy.context.preferences.themes[0].view_3d.space.gradients.high_gradient)
        
        if len(areas) <= 0:
            raise Exception(f"Make sure an Area of type {area_type} is open or visible in your screen!")

        with bpy.context.temp_override(area=areas[0]):
            if current_color == "<Color (r=0.2392, g=0.2392, b=0.2392)>":
                bpy.context.preferences.themes[0].view_3d.space.gradients.background_type = "SINGLE_COLOR"
                bpy.context.preferences.themes[0].view_3d.space.gradients.high_gradient = new_color
            else:
                bpy.context.preferences.themes[0].view_3d.space.gradients.high_gradient = default_color
                  
        return {'FINISHED'}

class ToggleWireFrame(bpy.types.Operator, UtilitiToolPanel, globalVariables):
    bl_idname = "mesh.viewwireframe"
    bl_label = "Toggle Viewport Wire Frame"
    bl_description = "Toggle Mesh Wireframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        for area in bpy.context.workspace.screens[0].areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    if space.overlay.show_wireframes == True:
                        space.overlay.show_wireframes = False
                    else:
                        space.overlay.show_wireframes = True            
        return {'FINISHED'}
        
class CreareTireDeform(bpy.types.Operator, TireDeformPanel, globalVariables):
    bl_idname = "mesh.createtiredeform"
    bl_label = "Toggle Viewport Wire Frame"
    bl_description = "Toggle Mesh Wireframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (((context.scene.tire_RF is not None   
            and context.scene.tire_RR is not None 
            and context.scene.tire_LF is not None 
            and context.scene.tire_LR is not None ))) 
    
    def execute(self, context):
        scene = context.scene
        C = bpy.context 
        D = bpy.data
        O = bpy.ops
        
        #Set variables for vehicle tire meshes
        tire_RF = scene.tire_RF
        tire_RR = scene.tire_RR
        tire_LF = scene.tire_LF
        tire_LR = scene.tire_LR
        
        #Select all tire meshes
        tire_RF.select_set(state=True)
        tire_RR.select_set(state=True)
        tire_LF.select_set(state=True)
        tire_LR.select_set(state=True)
        
        #Set object mode
        O.object.mode_set(mode='OBJECT', toggle=True)
        
        #Check tire deform data exist
        tiredeformFound = False
        for tireCol in bpy.data.collections:
            if tireCol.name == "Tire Deformations" or tireCol.name == "Deformations":
                tiredeformFound = True
                break
                
        #set scene frame
        if scene.frame_end != 65:
            scene.frame_start = 1
            scene.frame_end = 65  
        
        if tiredeformFound == False:
            #Set all object origins to geometry center
            O.object.origin_set(type='ORIGIN_GEOMETRY', center = 'BOUNDS')

            #making wheel mesh array

            wheel_mesh_array = [tire_RF, tire_RR, tire_LF, tire_LR]
            tire_name = ["LF", "LR", "RF", "RR"]

            #checking for linked meshes and unlinking them
            check_and_unlink_objects(wheel_mesh_array)
        
            #remove old armature modifiers from meshes
            for wheel in wheel_mesh_array:
                clear_old_armature_modifiers(wheel)
                #C.scene.objects[wheel.name].select_set(False) #Deselect mesh
                
            ##Create Tire Deform collection
            filepath = "C:\\Dev\\PROJECTS\\GTR\\SOURCE_ART\\VEHICLES\\_tires\\tire_deformation_rig.blend"

            with bpy.data.libraries.load(filepath) as (data_from, data_to):
                data_to.collections.append("Tire Deformations")
    
            collection = bpy.data.collections.get("Tire Deformations")
            bpy.context.scene.collection.children.link(collection)
            
            #create armature modifiers from meshes
            for n in tire_name:
                addmodifier_linktire_deform(n, wheel_mesh_array)
            
            #position tire mesh
            for name in tire_name:
                position_tire_deform(name, wheel_mesh_array)
               
            #Clear object position transformresult
            for wheel in wheel_mesh_array:
                C.scene.objects[wheel.name].select_set(True)
                O.object.transform_apply(location=True, rotation=False, scale=False)
                
        else:
            confmessage = ["Tire Deformation Exist, please cleanup first"]
            ShowMessageBox(confmessage, "Tire Deform Generate", "ERROR")
   
        return {'FINISHED'}
        
class ApplyTireWeight(bpy.types.Operator, TireDeformPanel, globalVariables):
    bl_idname = "mesh.applytireweight"
    bl_label = "Transfer Weight"
    bl_description = "Toggle Mesh Wireframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        amatireOb = []
        tiredeformFound = False
        for tireCol in bpy.data.collections:
            if tireCol.name == "Tire Deformations" or tireCol.name == "Deformations":
                for o in bpy.context.scene.objects:
                    if o.name == "tire_deformation_rig LF" or o.name == "tire_deformation_rig LR" or o.name == "tire_deformation_rig RF" or o.name == "tire_deformation_rig RR":
                        if not o in amatireOb:
                            amatireOb.append(o)
        if len(amatireOb) == 4:
            tiredeformFound = True
        return (((tiredeformFound == True))) 
    
    def execute(self, context):
        scene = context.scene
        C = bpy.context 
        D = bpy.data
        O = bpy.ops
        
        #Set variables for vehicle tire meshes
        tire_RF = scene.tire_RF
        tire_RR = scene.tire_RR
        tire_LF = scene.tire_LF
        tire_LR = scene.tire_LR
        
        #Select all tire meshes
        tire_RF.select_set(state=True)
        tire_RR.select_set(state=True)
        tire_LF.select_set(state=True)
        tire_LR.select_set(state=True)
        
        #Set object mode
        O.object.mode_set(mode='OBJECT', toggle=True)
        
        #making wheel mesh array

        wheel_mesh_array = [tire_RF, tire_RR, tire_LF, tire_LR]
        
        #transfer weight mesh
        tire_name = ["LF", "LR", "RF", "RR"]
        for name in tire_name:
            transfer_tire_weight(name, wheel_mesh_array)
        
   
        return {'FINISHED'}
        
class S4SetupRenderScene(bpy.types.Operator, VertexAOPanel, globalVariables):
    bl_idname = "s4veh.setupscene"
    bl_label = "Setup Render Scene"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        C = bpy.context 
        D = bpy.data
        O = bpy.ops
        
        #reparing render scene
        if not C.scene.render.engine == 'BLENDER_EEVEE':
            C.scene.render.engine = 'BLENDER_EEVEE'
            
        bpy.context.scene.eevee.taa_render_samples = 128
        #Ambient Occlusion
        bpy.context.scene.eevee.use_gtao = True
        bpy.context.scene.eevee.gtao_distance = 200.0
        bpy.context.scene.eevee.gtao_factor = 1
        bpy.context.scene.eevee.gtao_quality = 0.25
        bpy.context.scene.eevee.use_gtao_bent_normals = True
        bpy.context.scene.eevee.use_gtao_bounce = True

        
        #Screen Space Reflections
        bpy.context.scene.eevee.use_ssr = True
        bpy.context.scene.eevee.use_ssr_halfres = False
        bpy.context.scene.eevee.use_ssr_refraction = True
        bpy.context.scene.eevee.ssr_quality = 1
        bpy.context.scene.eevee.ssr_max_roughness = 0.758
        bpy.context.scene.eevee.ssr_thickness = 10
        bpy.context.scene.eevee.ssr_border_fade = 0.079
        bpy.context.scene.eevee.ssr_firefly_fac = 0
        
        #Color Manag
        bpy.context.scene.view_settings.view_transform = 'Filmic'
        
        
        return {'FINISHED'}

class BakeVertexAO(bpy.types.Operator, VertexAOPanel, globalVariables):
    bl_idname = "mesh.bakevertexao"
    bl_label = "Bake Vertex AO"
    bl_description = "Toggle Mesh Wireframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        isObj_selected = False
        sel_obj = bpy.context.selected_objects
        if sel_obj:
            isObj_selected = True
        return (((isObj_selected == True)))

    def assign_ambient_node(self, obj):
        for mat in obj.data.materials:
            mat.use_nodes = True
            material = mat.node_tree
            nodes = mat.node_tree.nodes

            #Find Output node
            material_output = None
            for node in nodes:
                if node.type == "OUTPUT_MATERIAL":
                    material_output = node
                    break
                
            # Perhaps the nodes hasn't been found then you'll have to create it
            if material_output is None:
                material_output = nodes.new("ShaderNodeOutputMaterial")
    

            #Find Ambient node
            group = None
            for ao_node in nodes:
                if ao_node.type == "AMBIENT_OCCLUSION":
                    group = ao_node
                    break
            if group is None:
                group = nodes.new('ShaderNodeAmbientOcclusion')
                group.location = (300, 600)
                group.inputs[1].default_value = 1000


            material.links.new(group.outputs[0], material_output.inputs[0])
    
    def execute(self, context):
        scene = context.scene
        C = bpy.context 
        D = bpy.data
        O = bpy.ops
        
        #reparing render scene
        if not C.scene.render.engine == 'CYCLES':
            C.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.device = 'CPU'
        if not C.scene.cycles.bake_type == 'COMBINED':
            C.scene.cycles.bake_type = 'COMBINED'
        if not C.scene.render.bake.target == 'VERTEX_COLORS':
            C.scene.render.bake.target = 'VERTEX_COLORS'
        bpy.context.scene.display_settings.display_device = 'sRGB'
        bpy.context.scene.view_settings.view_transform = 'Raw'
        bpy.context.scene.view_settings.look = 'None'
        bpy.context.scene.view_settings.exposure = 0
        bpy.context.scene.view_settings.gamma = 1
        bpy.context.scene.sequencer_colorspace_settings.name = 'Linear'
        if not C.scene.cycles.adaptive_threshold == 0.001:
            C.scene.cycles.adaptive_threshold = 0.001
        if not C.scene.cycles.samples == 4096:
            C.scene.cycles.samples = 4096
        if not C.scene.cycles.adaptive_min_samples == 1024:
            C.scene.cycles.adaptive_min_samples = 1024
        if not C.scene.cycles.time_limit == 0:
            C.scene.cycles.time_limit = 0
        
        #set vertex color
        for obj in bpy.context.selected_objects:
            if obj.type != 'MESH': 
                continue
            #if obj.data.color_attributes:
                #attrs = obj.data.color_attributes
                #for r in range(len(obj.data.color_attributes)-1, -1, -1):
                    #attrs.remove(attrs[r])
            if bpy.context.object.hide_render == True:
                bpy.context.object.hide_render = False
            #obj.data.color_attributes.new("Color", 'FLOAT_COLOR', 'POINT')
            #assign ambient node to selected objects
            self.assign_ambient_node(obj)
              
        #Change viewport shading
        my_areas = bpy.context.workspace.screens[0].areas
        for area in my_areas:
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.light = "FLAT"
                    space.shading.color_type = "VERTEX"
                    space.shading.type = 'SOLID'
      
        #Render
        bpy.ops.object.bake('INVOKE_DEFAULT', type='COMBINED')
        return {'FINISHED'}
        
class ExitVertexAO(bpy.types.Operator, VertexAOPanel, globalVariables):
    bl_idname = "mesh.exitbakevertexao"
    bl_label = "Exit Vertex AO Mode"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        C = bpy.context 
        D = bpy.data
        O = bpy.ops
        
        #reparing render scene
        if not C.scene.render.engine == 'BLENDER_EEVEE':
            C.scene.render.engine = 'BLENDER_EEVEE'
        bpy.context.scene.view_settings.view_transform = 'Filmic'
        
        #link default node
        list_shading_node = ['S4 Vehicle Glass Shader', 'S4 Vehicle Bodywork Shader', 
                            'S4 Vehicle Basic Shader', 'S4 Vehicle Tire Shader', 
                            'S4 Vehicle Wheels Shader', 'S4 Vehicle LightGlass Shader',
                            'str4_vehicleBodyworkShader'
                           ]
        material_output = None
        material_root = None
        for mat in D.materials:
            mat.use_nodes = True
            material = mat.node_tree
            nodes = mat.node_tree.nodes
            
            for n in nodes:
                if n.bl_idname == 'ShaderNodeOutputMaterial':
                    material_output = n.inputs['Surface']
                elif n.bl_idname == 'ShaderNodeGroup':
                    if n.node_tree.name in list_shading_node:
                        material_root = n.outputs['BSDF']
                elif n.bl_idname == 'ShaderNodeBsdfPrincipled':
                    material_root = n.outputs['BSDF']
            
            try:
                mat.node_tree.links.new(material_root,material_output)              
            except: 
                pass
                    
        return {'FINISHED'}
          
        
class SwitchLODValue(PropertyGroup):
    lod_list: EnumProperty(
        items=(
            ("A", "LODA", "Switch beween LODA and B"),
            ("B", "LODB", "Switch beween LODB and C"),
            ("C", "LODC", "Switch beween LODC and D"),
            ("CP", "CPIT", "Switch beween LODA and CPIT"),
        ),
        name="Select LOD to check",
        )

class SwitchLOD(bpy.types.Operator, LODValidPanel, globalVariables):
    bl_idname = "mesh.switchlod"
    bl_label = "Bake Vertex AO"
    bl_description = "Toggle Mesh Wireframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    def swap_lod(self, lod_sel, lod_next):
        lod_found = False
        all_coll = bpy.data.collections
        if lod_sel in all_coll and lod_next in all_coll:
            lod_found = True
        if lod_found == True:
            if bpy.data.collections[lod_sel].hide_viewport == True:
                bpy.data.collections[lod_sel].hide_viewport = False
                bpy.data.collections[lod_next].hide_viewport = True 
            else:
                bpy.data.collections[lod_sel].hide_viewport = True
                bpy.data.collections[lod_next].hide_viewport = False
        else:
            print('Missing collection')
    def execute(self, context):
        lod_sel = context.scene.lod_holder.lod_list
        lod_list = ['LODA', 'LODB','LODC','LODD', 'CPIT']
        if lod_sel == "A":
            for myCol in bpy.data.collections:
                for lod in lod_list:
                    if myCol.name == lod:
                        if lod == 'LODC' or lod == 'LODD' or lod == 'CPIT':
                            bpy.data.collections[lod].hide_viewport = True
            self.swap_lod('LODA', 'LODB')
        if lod_sel == "B":
            for myCol in bpy.data.collections:
                for lod in lod_list:
                    if myCol.name == lod:
                        if lod == 'LODA' or lod == 'LODD' or lod == 'CPIT':
                            bpy.data.collections[lod].hide_viewport = True
            self.swap_lod('LODB', 'LODC')
        if lod_sel == "C":
            for myCol in bpy.data.collections:
                for lod in lod_list:
                    if myCol.name == lod:
                        if lod == 'LODA' or lod == 'LODB' or lod == 'CPIT':
                            bpy.data.collections[lod].hide_viewport = True
            self.swap_lod('LODC', 'LODD')
        if lod_sel == "CP":
            for myCol in bpy.data.collections:
                for lod in lod_list:
                    if myCol.name == lod:
                        if lod == 'LODB' or lod == 'LODC' or lod == 'LODD':
                            bpy.data.collections[lod].hide_viewport = True
            self.swap_lod('CPIT', 'LODA') 
            
        return {'FINISHED'}

class EnableLOD(bpy.types.Operator, LODValidPanel, globalVariables):
    bl_idname = "mesh.enablelod"
    bl_label = "Bake Vertex AO"
    bl_description = "Toggle Mesh Wireframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        lod_list = ['LODA', 'LODB','LODC','LODD', 'CPIT']
        
        for myCol in bpy.data.collections:
            if myCol.name in lod_list:
                bpy.data.collections[myCol.name].hide_viewport = False
                 
        return {'FINISHED'}

class SelectNgon(bpy.types.Operator, UtilitiToolPanel, globalVariables):
    bl_idname = "mesh.selngon"
    bl_label = "Bake Vertex AO"
    bl_description = "Toggle Mesh Wireframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Go to object mode so that we can select
        bpy.ops.object.mode_set(mode = 'OBJECT')

        # Get active object
        obj = bpy.context.active_object
        if obj:
            # Select non quad faces (polygons)
            for p in obj.data.polygons:
                p.select = len(p.vertices) > 4

            # Go in edit mode to show the result    
            bpy.ops.object.mode_set(mode = 'EDIT')
                 
        return {'FINISHED'}

class S4CorrectMat(bpy.types.Operator, UtilitiToolPanel, globalVariables):
    bl_idname = "s4veh.correctmat"
    bl_label = "Correct Duplicate Material"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    def remove_suffix(self, name):
        # This function removes numerical suffixes like ".001", ".002", etc.
        if name[-4] == '.' and name[-3:].isdigit():
            return name[:-4]
        return name
    
    def execute(self, context):
        scene = context.scene
        C = bpy.context 
        D = bpy.data
        O = bpy.ops
        
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                # Iterate over the materials assigned to the object
                for i, mat_slot in enumerate(obj.material_slots):
                    if mat_slot.material:
                        original_name = mat_slot.material.name
                        # Check if the material has a numerical suffix
                        base_name = self.remove_suffix(original_name)
                
                        # Try to find the base material in the scene
                        base_material = bpy.data.materials.get(base_name)
                
                        if base_material:
                            # Replace the material in the slot with the base material
                            obj.material_slots[i].material = base_material
                            print(f"Replaced {original_name} with {base_material.name} on {obj.name}")
        
        return {'FINISHED'}

class S4RemoveShapekey(bpy.types.Operator, UtilitiToolPanel, globalVariables):
    bl_idname = "s4veh.removeshapekey"
    bl_label = "Remove Shapekey Selected Object"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        isObj_selected = False
        sel_obj = bpy.context.selected_objects
        if sel_obj:
            isObj_selected = True
        return (((isObj_selected == True)))
    
    def execute(self, context):
        scene = context.scene
        C = bpy.context 
        D = bpy.data
        O = bpy.ops
        
        # Get all selected objects
        selected_objects = C.selected_objects

        #Iterate through each selected object
        for obj in selected_objects:
            # Ensure we are working with a mesh object
            if obj.type == 'MESH':
                # Get the shape key data
                shape_keys = obj.data.shape_keys
                if shape_keys:
                    # Iterate through the shape keys from last to first and remove them
                    for index in reversed(range(len(shape_keys.key_blocks))):
                        obj.shape_key_remove(shape_keys.key_blocks[index])
        
        return {'FINISHED'}
        
class S4ApplyLattice(bpy.types.Operator, UtilitiToolPanel, globalVariables):
    bl_idname = "s4veh.applylattice"
    bl_label = "Apply Lattice as Shapekey Selected Object"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        isObj_selected = False
        sel_obj = bpy.context.selected_objects
        if sel_obj:
            isObj_selected = True
        return (((isObj_selected == True)))
    
    def execute(self, context):
        scene = context.scene
        C = bpy.context 
        D = bpy.data
        O = bpy.ops
        
        for ob in C.selected_objects:
            C.view_layer.objects.active = ob
            for name in [m.name for m in ob.modifiers]:
                O.object.modifier_apply_as_shapekey(modifier = name, keep_modifier=False)
        
        return {'FINISHED'}
        
class S4VehKeyShapekey(bpy.types.Operator, UtilitiToolPanel, globalVariables):
    bl_idname = "s4veh.keyshapekey"
    bl_label = "Keyframe for Shapekey"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        isObj_selected = False
        sel_obj = bpy.context.selected_objects
        if sel_obj:
            isObj_selected = True
        return (((isObj_selected == True)))
    
    def add_all_keyframe(self, obj):
        if obj.type != 'MESH': return

        blocks = obj.data.shape_keys.key_blocks
        if not blocks: return
        for k in blocks:
            if k.value == 0.00:
                frame = 1
                attr = "value"
                k.keyframe_insert(attr, frame=frame)
            if k.value == 1.00:
                frame = 100
                attr = "value"
                k.keyframe_insert(attr, frame=frame)
    
    def execute(self, context):
        scene = context.scene
        C = bpy.context 
        D = bpy.data
        O = bpy.ops
        
        for obj in C.selected_objects:
            self.add_all_keyframe(obj)
         
        C.scene.frame_set(C.scene.frame_current)
        
        return {'FINISHED'}

class S4VehLodRig(bpy.types.Operator, S4VehLODRigging, globalVariables):
    bl_idname = "s4veh.riglod"
    bl_label = "LOD Rigging"
    bl_description = "Toggle Mesh Wireframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    def add_child_bone(self, bone_name, parent_bone, wheel_mesh, armature_data):
        #Create a new bone
        new_bone = armature_data.data.edit_bones.new(bone_name)
        #Set bone's size
        new_bone.head = (0,0,0)
        new_bone.tail = (0,40,0)
        #Set bone's parent
        new_bone.parent = parent_bone
        #Set bone's location to wheel
        new_bone.matrix = wheel_mesh.matrix_world
        return new_bone
    
    @classmethod
    def poll(cls, context):
        return (((context.scene.s4veh_wheel_lf is not None   
            and context.scene.s4veh_wheel_lr is not None 
            and context.scene.s4veh_wheel_rf is not None
            and context.scene.s4veh_wheel_rr is not None
            and context.scene.s4veh_body_base is not None
            and context.scene.s4veh_steeringwheel is not None )))
    
    def execute(self, context):
        scene = context.scene
        C = bpy.context 
        D = bpy.data
        O = bpy.ops
        
        #Set variables for vehicle wheel meshes
        wheel_LF = scene.s4veh_wheel_lf
        wheel_LR = scene.s4veh_wheel_lr
        wheel_RF = scene.s4veh_wheel_rf
        wheel_RR = scene.s4veh_wheel_rr
        steeringwheel = scene.s4veh_steeringwheel
        bodybaselod = scene.s4veh_body_base
        
        #Select all part rig meshes
        wheel_LF.select_set(state=True)
        wheel_LR.select_set(state=True)
        wheel_RF.select_set(state=True)
        wheel_RR.select_set(state=True)
        steeringwheel.select_set(state=False)
        
        #Set object mode
        O.object.mode_set(mode='OBJECT', toggle=True)

        #Set all object origins to geometry center
        O.object.origin_set(type='ORIGIN_GEOMETRY', center = 'BOUNDS')

        #making rig part mesh array
        wheel_mesh_array = [wheel_LF, wheel_LR, wheel_RF, wheel_RR, steeringwheel]
        
        #Apply object transform
        O.object.transform_apply(location = False, rotation = True, scale = True)

        #Create armature object
        armature = D.armatures.new('Armature')
        bpy.data.armatures['Armature'].name = "Armature_LOD"
        armature.name = ('Armature_LOD')
        armature_object = D.objects.new('Armature', armature)
        
        #Link armature object to our scene
        C.collection.objects.link(armature_object)

        #Make armature variable
        armature_data = D.objects[armature_object.name]

        #Set armature active
        C.view_layer.objects.active = armature_data

        #Set armature selceted
        armature_data.select_set(state=True)

        #Set edit mode
        O.object.mode_set(mode='EDIT', toggle=False)

        #Set bones In front and show axis
        armature_data.show_in_front = True
        armature_data.data.show_axes = True
        
        #Add root bone
        root_bone = armature_data.data.edit_bones.new('Root')
        #Set its orientation and size
        root_bone.head = (0,0,0)
        root_bone.tail = (0,40,0)
        #Set its location to vehicle base mesh
        root_bone.matrix = bodybaselod.matrix_world

        #Add wheel bones to armature
        self.add_child_bone('PhysWheel_LF', root_bone, wheel_LF, armature_data)
        self.add_child_bone('PhysWheel_LR', root_bone, wheel_LR, armature_data)
        self.add_child_bone('PhysWheel_RF', root_bone, wheel_RF, armature_data)
        self.add_child_bone('PhysWheel_RR', root_bone, wheel_RR, armature_data)
        self.add_child_bone('FixedWheel_LF', root_bone, wheel_LF, armature_data)
        self.add_child_bone('FixedWheel_LR', root_bone, wheel_LR, armature_data)
        self.add_child_bone('FixedWheel_RF', root_bone, wheel_RF, armature_data)
        self.add_child_bone('FixedWheel_RR', root_bone, wheel_RR, armature_data)
        self.add_child_bone('SteeringWheel', root_bone, steeringwheel, armature_data)

        #Set object mode
        O.object.mode_set(mode='OBJECT', toggle=True)
        
        ##Select all part rig meshes
        wheel_LF.select_set(state=True)
        wheel_LR.select_set(state=True)
        wheel_RF.select_set(state=True)
        wheel_RR.select_set(state=True)
        steeringwheel.select_set(state=False)
        
        #Clear object position transformresult
        #for wheel in wheel_mesh_array:
            #C.scene.objects[wheel.name].select_set(True)
            #O.object.transform_apply(location=True, rotation=False, scale=False)
                
        #Deselect all objects
        O.object.select_all(action='DESELECT')
                 
        return {'FINISHED'}        

classes = [
    CUSTOM_objectCollection,
    CUSTOM_OT_clearList,
    MATERIAL_UL_matslots_example,
    ValidationToolMainPanel,
    ShaderToolPanel,
    UtilitiToolPanel,
    TireDeformPanel,
    VertexAOPanel,
    S4VehLODRigging,
    LODValidPanel,
    ExportPanel,
    ExportVehicleOperator,
    InitialCheck,
    BasicShader,
    BodyworkShader,
    GlassShader,
    LightGlassShader,
    TireShader,
    WheelShader,
    DirtShader,
    SpeedNode,
    ToggleBackFace,
    ToggleViewColor,
    ToggleWireFrame,
    CreareTireDeform,
    S4SetupRenderScene,
    ApplyTireWeight,
    BakeVertexAO,
    ExitVertexAO,
    SwitchLODValue,
    SwitchLOD,
    EnableLOD,
    SelectNgon,
    S4VehLodRig,
    S4CorrectMat,
    S4RemoveShapekey,
    S4ApplyLattice,
    S4VehKeyShapekey
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.custom = CollectionProperty(type=CUSTOM_objectCollection)
    bpy.types.Scene.custom_index = IntProperty(default=5)
    bpy.types.Scene.wheel_speed = bpy.props.FloatProperty(name = "Wheel Speed", description = "Check wheel speed node",min = 0.0, max = 1.0, default =  0.0, update=wheel_speed)
    bpy.types.Scene.dirt_value = bpy.props.FloatProperty(name = "Dirt Level", description = "Adjust dirt value",min = 0.0, max = 1.0, default =  0.0, update=dirt_value)
    bpy.types.Scene.dust_value = bpy.props.FloatProperty(name = "Dust Level", description = "Adjust dust value",min = 0.0, max = 1.0, default =  0.0, update=dust_value)
    bpy.types.Scene.mud_value = bpy.props.FloatProperty(name = "Mud Level", description = "Adjust mud value",min = 0.0, max = 1.0, default =  0.0, update=mud_value)
    bpy.types.Scene.deform_value = bpy.props.FloatProperty(name = "Deform Level", description = "Adjust deformation value",min = 0.0, max = 1.0, default =  0.0, update=deform_value)
    bpy.types.Scene.lights_value = bpy.props.FloatProperty(name = "Lights Intensity", description = "Adjust lighting value",min = 0.0, max = 10.0, default =  0.0, update=lights_value)
    bpy.types.Scene.tire_RF = bpy.props.PointerProperty(type=bpy.types.Object, poll = object_search_poll, name= "Tire RF", description = "Front Right Vehicle Tire Mesh")
    bpy.types.Scene.tire_RR = bpy.props.PointerProperty(type=bpy.types.Object, poll = object_search_poll, name= "Tire RR", description = "Rear Right Vehicle Tire Mesh")
    bpy.types.Scene.tire_LF = bpy.props.PointerProperty(type=bpy.types.Object, poll = object_search_poll, name= "Tire LF", description = "Front Left Vehicle Tire Mesh")
    bpy.types.Scene.tire_LR = bpy.props.PointerProperty(type=bpy.types.Object, poll = object_search_poll, name= "Tire LF", description = "Rear Left Vehicle Tire Mesh")
    bpy.types.Scene.s4veh_wheel_lf = bpy.props.PointerProperty(type=bpy.types.Object, poll = object_search_poll, name= "Pick Wheel LF", description = "Select LF Wheel")
    bpy.types.Scene.s4veh_wheel_lr = bpy.props.PointerProperty(type=bpy.types.Object, poll = object_search_poll, name= "Pick Wheel LR", description = "Select LF Wheel")
    bpy.types.Scene.s4veh_wheel_rf = bpy.props.PointerProperty(type=bpy.types.Object, poll = object_search_poll, name= "Pick Wheel RF", description = "Select LF Wheel")
    bpy.types.Scene.s4veh_wheel_rr = bpy.props.PointerProperty(type=bpy.types.Object, poll = object_search_poll, name= "Pick Wheel RR", description = "Select LF Wheel")
    bpy.types.Scene.s4veh_steeringwheel = bpy.props.PointerProperty(type=bpy.types.Object, poll = object_search_poll, name= "Pick SteeringWheel", description = "Select LF Wheel")
    bpy.types.Scene.s4veh_body_base = bpy.props.PointerProperty(type=bpy.types.Object, poll = object_search_poll, name= "Pick Body Part", description = "Select LF Wheel")
    bpy.types.Scene.lod_holder = bpy.props.PointerProperty(type=SwitchLODValue)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # del bpy.types.Scene.external_materials
    del bpy.types.Scene.custom
    del bpy.types.Scene.custom_index
    del bpy.types.Scene.wheel_speed
    del bpy.types.Scene.dirt_value
    del bpy.types.Scene.dust_value
    del bpy.types.Scene.mud_value
    del bpy.types.Scene.deform_value
    del bpy.types.Scene.lights_value
    del bpy.types.Scene.tire_RF
    del bpy.types.Scene.tire_RR
    del bpy.types.Scene.tire_LF
    del bpy.types.Scene.tire_LR
    del bpy.types.Scene.lod_holder
    del bpy.types.Scene.s4veh_wheel_lf
    del bpy.types.Scene.s4veh_wheel_lr
    del bpy.types.Scene.s4veh_wheel_rf
    del bpy.types.Scene.s4veh_wheel_rr
    del bpy.types.Scene.s4veh_steeringwheel
    del bpy.types.Scene.s4veh_body_base


if __name__ == "__main__":
    register()
