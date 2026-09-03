bl_info = {
    "name": "S4 Env Tools",
    "author": "Glenda Studio",
    "version": (1, 2),
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
            row.operator("custom.s4env_clear_list", text="Clear and hide result box.")

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

# ---------------------------------------------------------------------------
# Validator log
#
# Shared result list for every check tool. Individual checks used to speak only
# through self.report(), which lands in the Info editor and is easy to miss when
# a multi-object selection has a handful of bad meshes among good ones. Checks
# now write their per-object findings here instead, so the panel keeps the
# offenders on screen and can push them back into the selection.
# ---------------------------------------------------------------------------

S4ENV_LOG_ICONS = {
    'ERROR': 'ERROR',
    'WARNING': 'ERROR',
    'OK': 'CHECKMARK',
    'INFO': 'INFO',
}

# Statuses that count as "something to look at", i.e. what the select button grabs.
S4ENV_LOG_PROBLEMS = {'ERROR', 'WARNING'}


class S4EnvLogEntry(bpy.types.PropertyGroup):
    """One row of the validator log."""
    check: StringProperty(name="Check", default="")
    obj_name: StringProperty(name="Object", default="")
    message: StringProperty(name="Message", default="")
    status: EnumProperty(
        name="Status",
        items=(
            ('INFO', "Info", "Summary line for a check"),
            ('OK', "Ok", "Object passed the check"),
            ('WARNING', "Warning", "Object could not be checked properly"),
            ('ERROR', "Error", "Object failed the check"),
        ),
        default='INFO',
        )


def log_clear(context, check=None):
    """Drop log rows: all of them, or only the ones a given check wrote.

    Per-check clearing is what lets several tools share one panel - re-running
    the UV check replaces its own rows without wiping another check's results.
    """
    log = context.scene.s4env_log
    if check is None:
        log.clear()
    else:
        for i in reversed(range(len(log))):
            if log[i].check == check:
                log.remove(i)
    context.scene.s4env_log_index = 0


def log_add(context, check, message, obj_name="", status='ERROR'):
    """Append a row. Leave obj_name empty for a check-wide summary line."""
    entry = context.scene.s4env_log.add()
    entry.check = check
    entry.obj_name = obj_name
    entry.message = message
    entry.status = status
    return entry


def selectObjects(context, names):
    """Replace the selection with the named objects. Returns (selected, missing, unhidden)."""
    # Selection only applies in object mode, and there may be no active object
    # to switch the mode of.
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass

    objects = context.view_layer.objects
    for obj in objects:
        try:
            obj.select_set(False)
        except RuntimeError:
            pass

    selected, missing, unhidden = [], [], []
    for name in names:
        obj = objects.get(name)
        if obj is None:
            # The log outlives the objects it describes - a mesh can be renamed
            # or deleted between the check and the click.
            missing.append(name)
            continue

        # A hidden object cannot be selected at all, so a flagged mesh that the
        # LOD swap put away would silently drop out of the selection.
        if obj.hide_get() or obj.hide_viewport:
            setHidden(context, obj, False)
            unhidden.append(name)

        obj.select_set(True)
        selected.append(obj)

    if selected:
        objects.active = selected[0]

    return selected, missing, unhidden


class S4ENV_UL_log(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)
        row.alert = item.status in S4ENV_LOG_PROBLEMS
        row.label(text="", icon=S4ENV_LOG_ICONS.get(item.status, 'DOT'))

        if item.obj_name:
            split = row.split(factor=0.45)
            split.label(text=item.obj_name)
            split.label(text=item.message)
            row.operator("s4.envlogselectone", text="", icon='RESTRICT_SELECT_OFF',
                         emboss=False).obj_name = item.obj_name
        else:
            row.label(text="%s: %s" % (item.check, item.message) if item.check else item.message)


class S4EnvLogPanel(bpy.types.Panel, globalVariables):
    bl_label = "S4 Env Log"
    bl_idname = "S4_Env_Log"
    # Last panel in the category, and deliberately no DEFAULT_CLOSED - check
    # results are useless if the artist has to go looking for them.
    bl_order = 100
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Environment"
    bl_region_type = 'UI'

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        log = scn.s4env_log

        if not len(log):
            layout.label(text="No check results yet", icon='INFO')
            return

        layout.template_list("S4ENV_UL_log", "", scn, "s4env_log", scn, "s4env_log_index",
                             rows=min(max(len(log), 3), 12))

        problems = sum(1 for entry in log if entry.status in S4ENV_LOG_PROBLEMS and entry.obj_name)

        row = layout.row()
        row.enabled = problems > 0
        row.operator("s4.envlogselecterrors", icon='RESTRICT_SELECT_OFF',
                     text="Select %d Flagged Object%s" % (problems, "" if problems == 1 else "s"))

        layout.operator("s4.envlogclear", text="Clear Log", icon='TRASH')


class S4EnvLogSelectErrors(bpy.types.Operator):
    bl_idname = "s4.envlogselecterrors"
    bl_label = "Select Flagged Objects"
    bl_description = "Clear the selection, then select every object the log flagged"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(entry.status in S4ENV_LOG_PROBLEMS and entry.obj_name
                   for entry in context.scene.s4env_log)

    def execute(self, context):
        # Dedupe: several checks can flag the same mesh for different reasons.
        names = []
        for entry in context.scene.s4env_log:
            if entry.status in S4ENV_LOG_PROBLEMS and entry.obj_name and entry.obj_name not in names:
                names.append(entry.obj_name)

        selected, missing, unhidden = selectObjects(context, names)

        if not selected:
            self.report({'WARNING'}, "None of the flagged objects are in the scene any more")
            return {'CANCELLED'}

        message = "Selected %d flagged object%s" % (len(selected), "" if len(selected) == 1 else "s")
        if unhidden:
            message += ", unhid %d" % len(unhidden)
        if missing:
            message += ", %d no longer in the scene" % len(missing)
        self.report({'INFO'}, message)
        return {'FINISHED'}


class S4EnvLogSelectOne(bpy.types.Operator):
    bl_idname = "s4.envlogselectone"
    bl_label = "Select Object"
    bl_description = "Clear the selection, then select just this object"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: StringProperty(name="Object", default="")

    def execute(self, context):
        selected, missing, unhidden = selectObjects(context, [self.obj_name])

        if missing:
            self.report({'WARNING'}, "%s is no longer in the scene" % self.obj_name)
            return {'CANCELLED'}

        self.report({'INFO'}, "Selected %s%s" % (self.obj_name, " (unhidden)" if unhidden else ""))
        return {'FINISHED'}


class S4EnvLogClear(bpy.types.Operator):
    bl_idname = "s4.envlogclear"
    bl_label = "Clear Log"
    bl_description = "Empty the validator log"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        log_clear(context)
        return {'FINISHED'}


class S4EnvCheckUVs(bpy.types.Operator, globalVariables):
    bl_idname = "s4.envcheckuvs"
    bl_label = "Check UVs 32x32"
    bl_description = "Check UV range and attributes"
    bl_options = {'REGISTER', 'UNDO'}

    CHECK_NAME = "UV Range"
    MIN_RANGE = -32
    MAX_RANGE = 32

    def get_uv_bounds(self, obj):
        """Get the min/max UV bounds for UVMap00, or None if the mesh has no usable one."""
        uv_layer = obj.data.uv_layers.get("UVMap00")
        if uv_layer is None or len(uv_layer.data) == 0:
            return None

        # foreach_get pulls the whole layer in one call - a per-loop Python loop
        # is the slow part of this check on dense meshes.
        flat = np.empty(len(uv_layer.data) * 2, dtype=np.float32)
        uv_layer.data.foreach_get("uv", flat)
        uvs = flat.reshape(-1, 2)

        return {
            "min_u": float(uvs[:, 0].min()),
            "max_u": float(uvs[:, 0].max()),
            "min_v": float(uvs[:, 1].min()),
            "max_v": float(uvs[:, 1].max()),
        }

    def execute(self, context):
        # Only real geometry carries UVs; empties, lights and curves in the
        # selection are skipped rather than reported as failures.
        meshes = [obj for obj in context.selected_objects
                  if obj.type == 'MESH' and obj.data is not None]

        if not meshes:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Replace this check's own rows only, so results from other checks stay.
        log_clear(context, check=self.CHECK_NAME)
        start = len(context.scene.s4env_log)

        failed = 0
        no_uvs = 0

        for obj in meshes:
            bounds = self.get_uv_bounds(obj)

            if bounds is None:
                log_add(context, self.CHECK_NAME, "No usable UVMap00", obj.name, 'WARNING')
                no_uvs += 1
                continue

            min_u, max_u = bounds["min_u"], bounds["max_u"]
            min_v, max_v = bounds["min_v"], bounds["max_v"]

            issues = []

            if min_u < self.MIN_RANGE:
                issues.append("U min %.2f (over by %.2f)" % (min_u, self.MIN_RANGE - min_u))
            if max_u > self.MAX_RANGE:
                issues.append("U max %.2f (over by %.2f)" % (max_u, max_u - self.MAX_RANGE))
            if min_v < self.MIN_RANGE:
                issues.append("V min %.2f (over by %.2f)" % (min_v, self.MIN_RANGE - min_v))
            if max_v > self.MAX_RANGE:
                issues.append("V max %.2f (over by %.2f)" % (max_v, max_v - self.MAX_RANGE))

            if issues:
                log_add(context, self.CHECK_NAME, " | ".join(issues), obj.name, 'ERROR')
                failed += 1
            else:
                print("%s: UV bounds [%.2f, %.2f] x [%.2f, %.2f] - OK"
                      % (obj.name, min_u, max_u, min_v, max_v))

        summary = "%d mesh%s checked, %d out of +/-%d range, %d without UVMap00" % (
            len(meshes), "" if len(meshes) == 1 else "es", failed, self.MAX_RANGE, no_uvs)
        log_add(context, self.CHECK_NAME, summary, status='INFO')
        # The summary reads as a heading, so move it above the rows it counts.
        context.scene.s4env_log.move(len(context.scene.s4env_log) - 1, start)

        if failed or no_uvs:
            self.report({'WARNING'}, summary + " - see the S4 Env Log panel")
        else:
            self.report({'INFO'}, summary)

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
    S4EnvLogEntry,
    S4ENV_UL_log,
    S4EnvLogSelectErrors,
    S4EnvLogSelectOne,
    S4EnvLogClear,
    S4EnvCheckUVs,
    S4EnvLODToolPanel,
    S4EnvUtilitiToolPanel,
    S4EnvLogPanel,
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
    bpy.types.Scene.s4env_log = CollectionProperty(type=S4EnvLogEntry)
    bpy.types.Scene.s4env_log_index = IntProperty(default=0)


def unregister():
    # Drop the Scene properties before the classes they point at. The other way
    # round leaves Blender holding a PointerProperty to a de-registered struct,
    # which is why the panel needed an addon disable/re-enable to come back.
    del bpy.types.Scene.s4env_log_index
    del bpy.types.Scene.s4env_log
    del bpy.types.Scene.lod_holder
    del bpy.types.Scene.s4envcustom_index
    del bpy.types.Scene.custom

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
