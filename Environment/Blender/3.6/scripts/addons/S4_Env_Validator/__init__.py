bl_info = {
    "name": "S4 Env Validator",
    "author": "Glenda Studio",
    "version": (1, 1),
    "blender": (3, 6, 10),
    "location": "Sidebar",
    "description": "Validates S4 environment assets requirements for uploading",
    "category": "Object",
}

import bpy, math, addon_utils
import bmesh
import os, re
import numpy as np
from bpy.props import *
from bpy.types import Panel, PropertyGroup, Scene


class globalVariables():
    bl_idname = "s4env.globalvariables"
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

def check_mesh_in_collection(collection_name, mesh_name):
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        for obj in collection.objects:
            if obj.name.endswith(mesh_name):
                return (mesh_name + " found!", 'CHECKMARK')
    return (mesh_name + " not found in " + collection_name, 'ERROR')
                         

class CUSTOM_S4envobjectCollection(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    type: StringProperty()
    message: StringProperty()
    id: IntProperty()


class CUSTOM_S4envOT_clearList(bpy.types.Operator):
    bl_idname = "custom.s4env_clear_list"
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


class MATERIAL_S4env_matslots_example(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, "message", text=item.type, emboss=False, icon_value=icon)

class ValidationS4EnvToolMainPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Env Validator"
    bl_idname = "S4_Env_Validator"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Environment"
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
        row1.operator("s4.envcheck", text="Check Scene")
        
              
        if scn.checkResult_all == True:
            layout.template_list("MATERIAL_S4env_matslots_example", "", scn, "custom", scn, "s4envcustom_index")

            row = layout.row()
            row.operator("custom.s4_clear_list", text="Clear and hide result box.")

        row11 = layout.row()
        row11.label(text= globalVariables.version)

class S4EnvCheckToolPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Env Check Tool"
    bl_idname = "S4_Env_Check"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Environment"
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}
   
    def draw(self, context):
        scn = context.scene
        layout = self.layout
     
        obj = context.object
        
        row1 = layout.row()
        row1.operator("s4.envcheckuvs", text="Check UVs")

class S4EnvLODToolPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Env LOD Tool"
    bl_idname = "S4_Env_LOD"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Environment"
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}
   
    def draw(self, context):
        scn = context.scene
        layout = self.layout
        lod_holder = scn.lod_holder

        row1 = layout.row()
        row1.prop(lod_holder, "lod_list", text="Select LOD")

        row2 = layout.row()
        row2.operator('mesh.switchlod', text="Swap")

        row2 = layout.row()
        row2.operator('mesh.enablelod', text="Unhide All")
        row3 = layout.row()
        row3.operator("s4.envlodrename", text="Add LODA to selected mesh")
        row3 = layout.row()
        row3.operator("s4.envlodaduplicate", text="Duplicate LODA to LODB")
        row3.operator("s4.envlodbduplicate", text="Duplicate LODB to LODC")

class S4EnvUtilitiToolPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Env Utilities Tool"
    bl_idname = "S4_Env_Utilities"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Environment"
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        scn = context.scene
        layout = self.layout
     
        obj = context.object
        
        row1 = layout.row()
        row1.operator("s4.envcorrectmat", text="Correct Duplicate Material")
        
        row2 = layout.row()
        for area in bpy.context.workspace.screens[0].areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    if space.overlay.show_wireframes == True:
                        row2.alert = True
                    else:
                        row2.alert = False

        row2.operator("s4.envviewwireframe", text="Toggle Wireframe")
        
        row3 = layout.row()
        row3.operator("s4.envviewportcol", text="Change Viewport Color")
        
        row3 = layout.row()
        row3.operator("s4.envselngon", text="Select N-Gons Face")

class S4EnvInitialCheck(bpy.types.Operator, globalVariables):
    bl_idname = "s4.envcheck"
    bl_label = "Initial Check"
    bl_description = "Run through all check processes"

    def execute(self, context):
        if bool(context.scene.custom):
            context.scene.custom.clear()

        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        scn = context.scene
        objs = bpy.context.scene.objects
        globalVariables.meshObjs = getmeshObjs()

        if len(globalVariables.meshObjs) != 0:
            bpy.context.view_layer.objects.active = globalVariables.meshObjs[0]

            ##Check Material node type
            allmat = bpy.data.materials
            for mat in allmat:
                if not "Dots Stroke" in mat.name:
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    for n in nodes:
                        if "Principled BSDF" in n.name:
                            message = str(mat.name)
                            add_item(scn.custom, "MaterialNode", message)
                          
            ##Check UVset name
            uvmesh = []
            for meshObj in objs:
                if meshObj.type == "MESH":
                    for u in meshObj.data.uv_layers:
                        if not "UVMap" in u.name:
                            if not meshObj in uvmesh:
                                uvmesh.append(meshObj)
            for o in uvmesh:
                message = str(o.name)
                add_item(scn.custom,"UVMap", message)
            
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

            ##Check Scale Transform
            for obj in objs:
                # Check if the object is a mesh
                if obj.type == 'MESH':
                    # Check if the scale transformation is not (1, 1, 1)
                    print(obj.name, obj.scale)
                    if obj.scale[0] != 1.0 and obj.scale[1] != 1.0 and obj.scale[2] != 1.0:
                        message = str(obj.name)
                        add_item(scn.custom, "Scale Mesh", message)
                if obj.type == 'EMPTY':
                    # Check if the scale transformation is not (1, 1, 1)
                    print(obj.name, obj.scale)
                    if obj.scale[0] != 1.0 and obj.scale[1] != 1.0 and obj.scale[2] != 1.0:
                        message = str(obj.name)
                        add_item(scn.custom, "Scale Group", message)

            #Check naming structure
            # Get the Blender file name (without extension)
            blender_file_name = os.path.splitext(bpy.path.basename(bpy.data.filepath))[0]

            # The expected naming prefix for Empty objects
            empty_prefix = f"SM_{blender_file_name}"

            # Regex pattern to check for the Empty naming structure with an optional suffix
            empty_pattern = re.compile(rf"^{re.escape(empty_prefix)}(_\d+)?$")

            # Suffixes for meshes parented to Empties
            mesh_suffixes = ["_loda", "_lodb", "_lodc", "_lodd", "_lode"]

            # Iterate through all objects in the scene
            for obj in bpy.data.objects:
                if obj.type == 'EMPTY':  # Check if the object is an Empty
                    # Check if the Empty object's name matches the expected structure
                    if not empty_pattern.match(obj.name):
                        message = str(obj.name)
                        add_item(scn.custom, "Group name", message)

                    # Process child meshes of the Empty
                    child_meshes = [child for child in obj.children if child.type == 'MESH']
                    for i, child in enumerate(child_meshes):
                        # Determine the expected mesh name
                        if i < len(mesh_suffixes):
                            expected_mesh_name = f"{obj.name}{mesh_suffixes[i]}"
                        else:
                            # Handle cases where there are more meshes than predefined suffixes
                            expected_mesh_name = f"{obj.name}_lod{i + 1}"

                        # Check if the mesh name matches the expected structure
                        if child.name != expected_mesh_name:
                            message = str(child.name)
                            add_item(scn.custom, "Mesh name", message)


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

class S4EnvCorrectMat(bpy.types.Operator, globalVariables):
    bl_idname = "s4.envcorrectmat"
    bl_label = "Correct Material"
    bl_description = "Correct Duplicate Material"
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
        
class S4EnvToggleViewColor(bpy.types.Operator, globalVariables):
    bl_idname = "s4.envviewportcol"
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

class S4EnvToggleWireFrame(bpy.types.Operator, globalVariables):
    bl_idname = "s4.envviewwireframe"
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
        
class S4EnvSelectNgon(bpy.types.Operator, globalVariables):
    bl_idname = "s4.envselngon"
    bl_label = "Select Ngons"
    bl_description = "Select all non-quad faces on the active mesh"
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

class S4EnvCheckUVs(bpy.types.Operator, globalVariables):
    bl_idname = "s4.envcheckuvs"
    bl_label = "Check UVs"
    bl_description = "Check UV range and attributes"
    bl_options = {'REGISTER', 'UNDO'}

    def get_uv_bounds(self, obj):
        """Get the min/max UV bounds for UVMap00."""
        if obj is None or obj.type != 'MESH':
            return None
        
        mesh = obj.data
        
        if "UVMap00" not in mesh.uv_layers:
            return None
        
        uv_layer = mesh.uv_layers["UVMap00"]
        
        min_u = float('inf')
        max_u = float('-inf')
        min_v = float('inf')
        max_v = float('-inf')
        
        for uv_data in uv_layer.data:
            u, v = uv_data.uv.x, uv_data.uv.y
            min_u = min(min_u, u)
            max_u = max(max_u, u)
            min_v = min(min_v, v)
            max_v = max(max_v, v)
        
        return {
            "min_u": min_u,
            "max_u": max_u,
            "min_v": min_v,
            "max_v": max_v
        }

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        min_range = -32
        max_range = 32
        
        for obj in selected_objects:
            bounds = self.get_uv_bounds(obj)
            
            if bounds is None:
                self.report({'WARNING'}, f"{obj.name}: No UVMap00 found")
                continue
            
            min_u, max_u = bounds["min_u"], bounds["max_u"]
            min_v, max_v = bounds["min_v"], bounds["max_v"]
            
            # Check if out of range
            issues = []
            
            if min_u < min_range:
                issues.append(f"U min: {min_u:.2f} (exceeds by {min_range - min_u:.2f})")
            if max_u > max_range:
                issues.append(f"U max: {max_u:.2f} (exceeds by {max_u - max_range:.2f})")
            if min_v < min_range:
                issues.append(f"V min: {min_v:.2f} (exceeds by {min_range - min_v:.2f})")
            if max_v > max_range:
                issues.append(f"V max: {max_v:.2f} (exceeds by {max_v - max_range:.2f})")
            
            if issues:
                self.report({'WARNING'}, f"{obj.name}: {' | '.join(issues)}")
            else:
                self.report({'INFO'}, f"{obj.name}: UV bounds [{min_u:.2f}, {max_u:.2f}] x [{min_v:.2f}, {max_v:.2f}] - OK")
        
        return {'FINISHED'}

# LOD meshes end in LODA/LODB/LODC, optionally followed by Blender's duplicate
# suffix (".001"). Matching the suffix matters: DuplicateLODA below creates names
# like "Wall_LODB.001", which a plain endswith("LODB") would never see.
LOD_NAME_RE = re.compile(r"LOD([ABC])(?:\.\d+)?$")


def lodOf(obj):
    """Return "LODA"/"LODB"/"LODC" for a LOD-named mesh, or None for anything else."""
    if obj.type != 'MESH':
        return None
    match = LOD_NAME_RE.search(obj.name)
    return "LOD" + match.group(1) if match else None


def setHidden(context, obj, hidden):
    """Hide/show an object through every visibility flag an artist can trip over."""
    obj.hide_viewport = hidden
    obj.hide_render = hidden
    # hide_set is the eye icon, which hide_viewport does not override. Objects
    # outside the active view layer have no eye to set.
    if obj.name in context.view_layer.objects:
        obj.hide_set(hidden)


class SwitchLODValue(PropertyGroup):
    lod_list: EnumProperty(
        items=(
            ("A", "LODA", "Switch beween LODA and B"),
            ("B", "LODB", "Switch beween LODB and C"),
        ),
        name="Select LOD to check",
        )
    shown: StringProperty(
        name="Shown LOD",
        description="Which LOD the Swap button last made visible",
        default="",
        )

class SwitchLOD(bpy.types.Operator, globalVariables):
    bl_idname = "mesh.switchlod"
    bl_label = "Swap LOD"
    bl_description = "Toggle viewport visibility between the two LODs of the selected pair"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        holder = context.scene.lod_holder
        pair = ("LODA", "LODB") if holder.lod_list == "A" else ("LODB", "LODC")

        # Flip to the other half of the pair. Reading the stored state instead of
        # sampling object visibility means a single manually hidden mesh can no
        # longer invert the swap direction.
        target = pair[1] if holder.shown == pair[0] else pair[0]

        tagged = {pair[0]: [], pair[1]: []}
        for obj in context.scene.objects:
            lod = lodOf(obj)
            if lod in tagged:
                tagged[lod].append(obj)

        if not tagged[target]:
            other = pair[1] if target == pair[0] else pair[0]
            if tagged[other]:
                self.report({'WARNING'}, f"No {target} meshes in the scene - nothing to swap to")
            else:
                self.report({'WARNING'}, f"No {pair[0]} or {pair[1]} meshes in the scene")
            return {'CANCELLED'}

        # Only LOD meshes are touched. Everything else in the file keeps whatever
        # visibility the artist gave it.
        for lod, objects in tagged.items():
            for obj in objects:
                setHidden(context, obj, lod != target)

        holder.shown = target
        self.report({'INFO'}, f"Showing {target} ({len(tagged[target])} meshes)")
        return {'FINISHED'}

class EnableLOD(bpy.types.Operator, globalVariables):
    bl_idname = "mesh.enablelod"
    bl_label = "Unhide All Objects"
    bl_description = "Unhide every mesh and empty, and reset the LOD swap state"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        count = 0
        for obj in context.scene.objects:
            if obj.type in {'MESH', 'EMPTY'}:
                setHidden(context, obj, False)
                count += 1

        context.scene.lod_holder.shown = ""
        self.report({'INFO'}, f"Unhid {count} objects")
        return {'FINISHED'}

class RenameLOD(bpy.types.Operator, globalVariables):
    bl_idname = "s4.envlodrename"
    bl_label = "Add LODA to name"
    bl_description = "Append _LODA to the name of every selected mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get all selected mesh objects
        selected_meshes = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

        for obj in selected_meshes:
            name = obj.name
            match = re.search(r"\.\d+$", name)  # Check if the name ends with ".001", ".002", etc.

            if match:
                new_name = name[:match.start()] + "_LODA" + match.group()
            else:
                new_name = name + "_LODA"

            obj.name = new_name
            print(f'Renamed "{name}" to "{obj.name}"')

        if not selected_meshes:
            print("No meshes selected")

        return {'FINISHED'}

class DuplicateLODA(bpy.types.Operator, globalVariables):
    bl_idname = "s4.envlodaduplicate"
    bl_label = "Duplicate LODA to LODB"
    bl_description = "Copy the selected LODA meshes into a matching LODB set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        def duplicate_selected_meshes():
            selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

            if not selected_objects:
                print("No meshes selected.")
                return

            # Check if any selected object ends with "LODA.xxx" or only "LODA"
            ends_with_loda_xxx = any(re.search(r"LODA\.\d{3}$", obj.name) for obj in selected_objects)
            ends_with_loda = any(re.search(r"LODA$", obj.name) for obj in selected_objects)

            new_objects = []

            if ends_with_loda_xxx:
                # If any selected mesh ends with "LODA.xxx", duplicate all together as instances
                shared_mesh_data = None  # This will store the shared instance

                for obj in selected_objects:
                    new_obj = obj.copy()
                    if shared_mesh_data is None:
                        # First object creates a new mesh data copy
                        shared_mesh_data = obj.data.copy()
                    new_obj.data = shared_mesh_data  # Share mesh data among new objects

                    bpy.context.collection.objects.link(new_obj)

                    # Rename "LODA.xxx" → "LODB.xxx"
                    if re.search(r"LODA\.\d{3}$", obj.name):
                        new_name = obj.name.replace("LODA.", "LODB.")
                    else:
                        new_name = obj.name.replace("LODA", "LODB")

                    new_obj.name = new_name
                    new_objects.append(new_obj)

                    print(f"Duplicated {obj.name} -> {new_obj.name} (Instance)")

            elif ends_with_loda:
                # If a selected object ends only with "LODA", duplicate it individually (not as an instance)
                for obj in selected_objects:
                    if re.search(r"LODA$", obj.name):
                        new_obj = obj.copy()
                        new_obj.data = obj.data.copy()  # Create separate mesh data
                        bpy.context.collection.objects.link(new_obj)

                        new_name = obj.name.replace("LODA", "LODB")  # Rename "LODA" → "LODB"
                        new_obj.name = new_name

                        new_objects.append(new_obj)
                        print(f"Duplicated {obj.name} -> {new_obj.name}")

            # Select all newly created objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in new_objects:
                obj.select_set(True)

            print("All duplicated meshes are now selected.")

        # Run the function
        duplicate_selected_meshes()

        return {'FINISHED'}

class DuplicateLODB(bpy.types.Operator, globalVariables):
    bl_idname = "s4.envlodbduplicate"
    bl_label = "Duplicate LODB to LODC"
    bl_description = "Copy the selected LODB meshes into a matching LODC set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        def duplicate_selected_meshes():
            selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

            if not selected_objects:
                print("No meshes selected.")
                return

            # Check if any selected object ends with "LODB.xxx" or only "LODC"
            ends_with_loda_xxx = any(re.search(r"LODB\.\d{3}$", obj.name) for obj in selected_objects)
            ends_with_loda = any(re.search(r"LODB$", obj.name) for obj in selected_objects)

            new_objects = []

            if ends_with_loda_xxx:
                # If any selected mesh ends with "LODA.xxx", duplicate all together as instances
                shared_mesh_data = None  # This will store the shared instance

                for obj in selected_objects:
                    new_obj = obj.copy()
                    if shared_mesh_data is None:
                        # First object creates a new mesh data copy
                        shared_mesh_data = obj.data.copy()
                    new_obj.data = shared_mesh_data  # Share mesh data among new objects

                    bpy.context.collection.objects.link(new_obj)

                    # Rename "LODA.xxx" → "LODB.xxx"
                    if re.search(r"LODB\.\d{3}$", obj.name):
                        new_name = obj.name.replace("LODB.", "LODC.")
                    else:
                        new_name = obj.name.replace("LODB", "LODC")

                    new_obj.name = new_name
                    new_objects.append(new_obj)

                    print(f"Duplicated {obj.name} -> {new_obj.name} (Instance)")

            elif ends_with_loda:
                # If a selected object ends only with "LODA", duplicate it individually (not as an instance)
                for obj in selected_objects:
                    if re.search(r"LODB$", obj.name):
                        new_obj = obj.copy()
                        new_obj.data = obj.data.copy()  # Create separate mesh data
                        bpy.context.collection.objects.link(new_obj)

                        new_name = obj.name.replace("LODB", "LODC")  # Rename "LODB" → "LODC"
                        new_obj.name = new_name

                        new_objects.append(new_obj)
                        print(f"Duplicated {obj.name} -> {new_obj.name}")

            # Select all newly created objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in new_objects:
                obj.select_set(True)

            print("All duplicated meshes are now selected.")

        # Run the function
        duplicate_selected_meshes()

        return {'FINISHED'}

classes = [
    CUSTOM_S4envobjectCollection,
    CUSTOM_S4envOT_clearList,
    MATERIAL_S4env_matslots_example,
    ValidationS4EnvToolMainPanel,
    S4EnvCheckToolPanel,
    S4EnvCheckUVs,
    S4EnvLODToolPanel,
    S4EnvUtilitiToolPanel,
    S4EnvInitialCheck,
    S4EnvCorrectMat,
    S4EnvToggleViewColor,
    S4EnvToggleWireFrame,
    S4EnvSelectNgon,
    SwitchLODValue,
    SwitchLOD,
    EnableLOD,
    RenameLOD,
    DuplicateLODA,
    DuplicateLODB
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.custom = CollectionProperty(type=CUSTOM_S4envobjectCollection)
    bpy.types.Scene.s4envcustom_index = IntProperty(default=5)
    bpy.types.Scene.lod_holder = bpy.props.PointerProperty(type=SwitchLODValue)


def unregister():
    # Drop the Scene properties before the classes they point at. The other way
    # round leaves Blender holding a PointerProperty to a de-registered struct,
    # which is why the panel needed an addon disable/re-enable to come back.
    del bpy.types.Scene.lod_holder
    del bpy.types.Scene.s4envcustom_index
    del bpy.types.Scene.custom

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
