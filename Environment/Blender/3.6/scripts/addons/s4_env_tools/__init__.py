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


# Panel footer text, built from bl_info so the two can never drift apart.
ADDON_VERSION = "Version %s" % ".".join(str(n) for n in bl_info["version"])


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


def getmeshObjs():
    meshObjs = []
    objs = bpy.context.scene.objects
    for obj in objs:
        meshObjs.append(obj)

    return meshObjs

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

class ValidationS4EnvToolMainPanel(bpy.types.Panel):
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
        row11.label(text=ADDON_VERSION)

class S4EnvCheckToolPanel(bpy.types.Panel):
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
        row1.operator("s4.envcheckmaterials", text="Check Materials")

        row2 = layout.row()
        row2.operator("s4.envcheckuvs", text="Check UVs")

class S4EnvLODToolPanel(bpy.types.Panel):
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

class S4EnvUtilitiToolPanel(bpy.types.Panel):
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

class S4EnvInitialCheck(bpy.types.Operator):
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
        meshObjs = getmeshObjs()

        if len(meshObjs) != 0:
            bpy.context.view_layer.objects.active = meshObjs[0]

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

class S4EnvCorrectMat(bpy.types.Operator):
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
        
class S4EnvToggleViewColor(bpy.types.Operator):
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

class S4EnvToggleWireFrame(bpy.types.Operator):
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
        
class S4EnvSelectNgon(bpy.types.Operator):
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
    # CANCEL is the red cross, ERROR the yellow warning triangle - the icon is
    # what separates the two severities, since only alert rows can be recoloured.
    'ERROR': 'CANCEL',
    'WARNING': 'ERROR',
    'OK': 'CHECKMARK',
    'INFO': 'INFO',
}

# row.alert is Blender's only text tint, and it is red - so errors take it and
# warnings stay on default text behind their yellow triangle.
S4ENV_LOG_ALERT = {'ERROR'}

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
        row.alert = item.status in S4ENV_LOG_ALERT
        row.label(text="", icon=S4ENV_LOG_ICONS.get(item.status, 'DOT'))

        if item.obj_name:
            split = row.split(factor=0.45)
            split.label(text=item.obj_name)
            split.label(text=item.message)
            row.operator("s4.envlogselectone", text="", icon='RESTRICT_SELECT_OFF',
                         emboss=False).obj_name = item.obj_name
        else:
            row.label(text="%s: %s" % (item.check, item.message) if item.check else item.message)


class S4EnvLogPanel(bpy.types.Panel):
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


# ---------------------------------------------------------------------------
# s4s shader
#
# The UV check and the material check read the same node group, so its name and
# its socket names live here rather than on either operator - when the two kept
# their own copies they drifted, and a misspelt socket name is invisible: an
# absent socket reads as False, so the check quietly passes everything.
# ---------------------------------------------------------------------------

# Matched exactly. Appending a material from another file can bring in a second
# copy of the group as "basic_props_shader_s4s.001", and a material sitting on
# that copy is on a shader that can drift from the real one - so it is a fault
# to report, never a name to quietly accept.
SHADER_GROUP = "basic_props_shader_s4s"

# Socket names on that group. The colour flag is spelt the British way and the
# rest are not - that is how the group is authored, so it is not a typo to fix
# here. shader_flag() below raises on an unknown socket rather than reading it
# as off, which is what makes a wrong name show up instead of hiding.
FLAG_ALPHA = "use_alpha"
FLAG_BROAD_COLOUR = "use_broad_colour"
FLAG_EMISSIVE = "use_emissive"
FLAG_BROAD_EMISSIVE = "use_broad_emissive"
FLAG_LOGO = "use_logo"


def group_nodes(mat):
    """Every top-level group node in a material, as (node, group name)."""
    tree = mat.node_tree if mat.use_nodes else None
    if tree is None:
        return []
    return [(node, node.node_tree.name) for node in tree.nodes
            if getattr(node, "node_tree", None) is not None]


def shader_nodes(mat):
    """Group nodes sitting on the real s4s shader, in node order."""
    return [node for node, name in group_nodes(mat) if name == SHADER_GROUP]


def stray_shader_names(mat):
    """Names of near-miss copies of the s4s shader used by a material.

    These are the "basic_props_shader_s4s.001" duplicates an append leaves
    behind. Kept apart from shader_nodes() so they can be reported as the fault
    they are instead of counting as the shader.
    """
    return sorted({name for node, name in group_nodes(mat)
                   if name != SHADER_GROUP and name.startswith(SHADER_GROUP)})


def flag_on(inputs, name):
    """True if the named boolean socket exists and is ticked."""
    socket = inputs.get(name)
    return socket is not None and bool(socket.default_value)


def shader_flag(node, name):
    """Read a boolean socket, as (value, present).

    Unlike flag_on() this distinguishes "ticked off" from "no such socket", so
    the material check can report a shader that is missing the socket entirely
    instead of silently treating it as unticked.
    """
    socket = node.inputs.get(name)
    if socket is None:
        return False, False
    return bool(socket.default_value), True


class S4EnvCheckUVs(bpy.types.Operator):
    bl_idname = "s4.envcheckuvs"
    bl_label = "Check UVs 32x32"
    bl_description = "Check UV range, and that each mesh carries exactly the UV maps its shaders need"
    bl_options = {'REGISTER', 'UNDO'}

    CHECK_NAME = "UV Range"
    MIN_RANGE = -32
    MAX_RANGE = 32

    # The only UV map names the pipeline accepts. A mesh must carry exactly the
    # ones its shaders call for - no more, no fewer - and anything named outside
    # this list is wrong whatever the shaders say.
    UV_NAMES = ("UVMap00", "UVMap01", "UVMap02", "UVMap03")
    UV_NAME_SET = frozenset(UV_NAMES)

    # Requirements read off the s4s shader. Emissive wins outright - it calls for
    # three maps whatever the broad colour flag says - so broad is only worth
    # reading once emissive is ruled out. use_logo is independent of both and
    # decides UVMap03 on its own.
    EMISSIVE_FLAGS = (FLAG_EMISSIVE, FLAG_BROAD_EMISSIVE)
    LOGO_UV = "UVMap03"
    BASE_UVS = 1
    BROAD_UVS = 2
    EMISSIVE_UVS = 3

    def material_requirements(self, mat):
        """One material's demands, as (uv map count, needs the logo map)."""
        count = self.BASE_UVS
        logo = False

        for node in shader_nodes(mat):
            inputs = node.inputs
            logo = logo or flag_on(inputs, FLAG_LOGO)

            if count == self.EMISSIVE_UVS:
                continue  # already the strictest; only logo can still change
            if any(flag_on(inputs, f) for f in self.EMISSIVE_FLAGS):
                count = self.EMISSIVE_UVS
            elif flag_on(inputs, FLAG_BROAD_COLOUR):
                count = self.BROAD_UVS

        return count, logo

    def object_requirements(self, obj, cache):
        """What this object needs, as (uv map count, needs the logo map, strays).

        Materials disagree by design - the strictest wins, and any one of them
        asking for the logo map is enough to require it.

        `strays` names materials sitting on a duplicated copy of the shader.
        Their flags are not read, so without naming them here the mesh would be
        measured against the one-map default and quietly pass.
        """
        count = self.BASE_UVS
        logo = False
        strays = []

        for slot in obj.material_slots:
            mat = slot.material
            if mat is None:
                continue

            # One shader serves hundreds of objects, so each material is only
            # walked once per run.
            needs = cache.get(mat)
            if needs is None:
                needs = (self.material_requirements(mat) +
                         (tuple(stray_shader_names(mat)),))
                cache[mat] = needs

            if needs[0] > count:
                count = needs[0]
            logo = logo or needs[1]

            for name in needs[2]:
                entry = "%s on %s" % (mat.name, name)
                if entry not in strays:
                    strays.append(entry)

        return count, logo, strays

    @staticmethod
    def get_uv_bounds(uv_layer):
        """Min/max UV bounds for one layer, or None if it carries no loops."""
        count = len(uv_layer.data)
        if count == 0:
            return None

        # foreach_get pulls the whole layer in one call - a per-loop Python loop
        # is the slow part of this check on dense meshes.
        flat = np.empty(count * 2, dtype=np.float32)
        uv_layer.data.foreach_get("uv", flat)
        uvs = flat.reshape(-1, 2)

        return (float(uvs[:, 0].min()), float(uvs[:, 0].max()),
                float(uvs[:, 1].min()), float(uvs[:, 1].max()))

    def range_detail(self, uv_name, bounds):
        """Console-side description of a layer's range violations, or None."""
        min_u, max_u, min_v, max_v = bounds
        over = []
        if min_u < self.MIN_RANGE:
            over.append("U min %.2f" % min_u)
        if max_u > self.MAX_RANGE:
            over.append("U max %.2f" % max_u)
        if min_v < self.MIN_RANGE:
            over.append("V min %.2f" % min_v)
        if max_v > self.MAX_RANGE:
            over.append("V max %.2f" % max_v)

        if not over:
            return None
        # The panel column is narrow, so the numbers go to the console and the
        # row just names the layer.
        return "%s: %s outside +/-%d" % (uv_name, ", ".join(over), self.MAX_RANGE)

    def check_object(self, obj, cache):
        """Run every UV rule against one mesh. Returns a list of error strings."""
        count, logo, shader_strays = self.object_requirements(obj, cache)

        expected = set(self.UV_NAMES[:count])
        if logo:
            expected.add(self.LOGO_UV)

        present = set()
        spare = []
        stray = []
        out_of_range = []
        details = []

        # One pass over the layers the mesh actually has: each is either one the
        # shaders asked for - and then worth measuring - or one that should not
        # be on the mesh at all.
        for uv_layer in obj.data.uv_layers:
            uv_name = uv_layer.name

            if uv_name not in expected:
                if uv_name in self.UV_NAME_SET:
                    spare.append(uv_name)
                else:
                    stray.append(uv_name)
                continue

            present.add(uv_name)

            bounds = self.get_uv_bounds(uv_layer)
            if bounds is None:
                continue

            detail = self.range_detail(uv_name, bounds)
            if detail:
                out_of_range.append(uv_name)
                details.append(detail)

        missing = [name for name in sorted(expected) if name not in present]

        errors = []
        # Named first: on a duplicated shader the flags below were never read,
        # so every other finding on this mesh is measured against the default.
        for entry in shader_strays:
            errors.append("duplicate shader - %s" % entry)
        if missing:
            errors.append("%s missing" % " - ".join(missing))
        if spare:
            errors.append("%s not needed" % " - ".join(spare))
        if stray:
            errors.append("%s not allowed" % " - ".join(stray))
        if out_of_range:
            errors.append("%s out of range" % " - ".join(out_of_range))

        if missing or spare:
            details.append("shader needs %s" % ", ".join(sorted(expected)))
        if details:
            print("%s: %s" % (obj.name, " | ".join(details)))

        return errors

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

        cache = {}
        error_rows = []

        for obj in meshes:
            errors = self.check_object(obj, cache)
            if errors:
                error_rows.append((obj.name, " | ".join(errors)))

        # The summary heads the block the check just wrote.
        summary = "%d mesh%s checked, %d error%s" % (
            len(meshes), "" if len(meshes) == 1 else "es",
            len(error_rows), "" if len(error_rows) == 1 else "s")
        log_add(context, self.CHECK_NAME, summary, status='INFO')

        for obj_name, message in error_rows:
            log_add(context, self.CHECK_NAME, message, obj_name, 'ERROR')

        if error_rows:
            self.report({'WARNING'}, summary + " - see the S4 Env Log panel")
        else:
            self.report({'INFO'}, summary)

        return {'FINISHED'}


class S4EnvCheckMaterials(bpy.types.Operator):
    bl_idname = "s4.envcheckmaterials"
    bl_label = "Check Materials"
    bl_description = ("Check each material's blend settings and s4s shader flags "
                      "against the object name and the textures actually assigned")
    bl_options = {'REGISTER', 'UNDO'}

    CHECK_NAME = "Materials"

    # An object whose name carries either word is a see-through asset: it clips
    # its alpha and renders both faces. Matched case-insensitively anywhere in
    # the name, so "Window_Glass_LODA" and "alphaFence" both count.
    ALPHA_WORDS = ("alpha", "glass")

    # EEVEE settings, as (property, value when see-through, value when opaque).
    # Blender spells Alpha Clip 'CLIP' and Opaque 'OPAQUE' for both blend and
    # shadow, so one table covers all three properties.
    SETTINGS = (
        ("use_backface_culling", False, True),
        ("blend_method", 'CLIP', 'OPAQUE'),
        ("shadow_method", 'CLIP', 'OPAQUE'),
    )

    # How each setting reads in the UI, for the log row.
    SETTING_LABELS = {
        False: "off", True: "on",
        'CLIP': "Alpha Clip", 'OPAQUE': "Opaque",
    }

    # Texture node name prefix -> the shader flag it must agree with. An image
    # in the node means the flag is ticked; an empty node means it is not.
    # Matched exactly: node names are unique inside a node tree, so a second
    # node asking for "logo" is what Blender renames to "logo.001" - and that
    # misnaming is one of the things this check exists to catch, so accepting
    # it would defeat the point.
    TEXTURE_FLAGS = (
        ("broad_color", FLAG_BROAD_COLOUR),
        ("broad_emissive", FLAG_BROAD_EMISSIVE),
        ("emissive", FLAG_EMISSIVE),
        ("logo", FLAG_LOGO),
    )

    def is_alpha_asset(self, obj):
        name = obj.name.lower()
        return any(word in name for word in self.ALPHA_WORDS)

    def check_settings(self, mat, alpha):
        """Blend/culling settings against what the object's name calls for."""
        errors = []
        for prop, when_alpha, when_opaque in self.SETTINGS:
            want = when_alpha if alpha else when_opaque
            got = getattr(mat, prop)
            if got != want:
                errors.append("%s is %s, needs %s" % (
                    prop, self.SETTING_LABELS.get(got, got),
                    self.SETTING_LABELS.get(want, want)))
        return errors

    @staticmethod
    def near_miss(tree, name):
        """A node that looks like it was meant to be `name`, or None.

        Only ever used to make the error message actionable - a near miss never
        counts as the node being present, and never lets a check pass. The two
        shapes worth naming are Blender's ".001" suffix and a case or
        whitespace slip, because those are what a hand-built material produces.
        """
        wanted = name.lower()
        for node in tree.nodes:
            other = node.name
            if other == name:
                continue
            if other.strip().lower() == wanted or other.startswith(name + "."):
                return other
        return None

    def texture_state(self, mat):
        """Each texture slot's state, as {flag: (status, detail)}.

        status is 'ok' with detail True/False for whether an image is
        assigned, 'missing' with detail naming a near miss (or None), or
        'wrong_type' with detail naming the node type found instead.
        """
        state = {}
        errors = []
        tree = mat.node_tree

        for name, flag in self.TEXTURE_FLAGS:
            node = tree.nodes.get(name)

            if node is None:
                state[flag] = ('missing', self.near_miss(tree, name))
            elif node.type != 'TEX_IMAGE':
                state[flag] = ('wrong_type', node.type)
                errors.append("%s is a %s node, not an image texture"
                              % (name, node.type))
            else:
                state[flag] = ('ok', node.image is not None)

        return state, errors

    def check_shader(self, mat, alpha):
        """The s4s group's flags against the textures wired into the material."""
        groups = shader_nodes(mat)
        strays = stray_shader_names(mat)

        if not groups:
            if strays:
                # There is a shader here, just not the real one - a duplicated
                # copy that can drift, so it fails rather than being skipped.
                return ["on %s, not %s" % (" - ".join(strays), SHADER_GROUP)], []
            # Not an s4s material at all - the blend settings still applied,
            # but there is no shader here to carry flags.
            return [], ["no %s node" % SHADER_GROUP]

        errors = []
        if strays:
            errors.append("extra shader copy: %s" % " - ".join(strays))

        state, type_errors = self.texture_state(mat)
        errors.extend(type_errors)

        for node in groups:
            # Only see-through assets have a stated use_alpha requirement, so an
            # opaque material's alpha flag is left alone.
            if alpha:
                value, exists = shader_flag(node, FLAG_ALPHA)
                if not exists:
                    errors.append("shader has no %s" % FLAG_ALPHA)
                elif not value:
                    errors.append("%s is off" % FLAG_ALPHA)

            for name, flag in self.TEXTURE_FLAGS:
                status, detail = state[flag]
                value, exists = shader_flag(node, flag)

                if not exists:
                    errors.append("shader has no %s" % flag)
                    continue

                if status == 'wrong_type':
                    continue  # texture_state already reported it

                if status == 'missing':
                    found = " - found %s" % detail if detail else ""
                    if value:
                        errors.append("%s is on but there is no %s node%s"
                                      % (flag, name, found))
                    elif detail:
                        # Flag off and node absent would otherwise pass, but a
                        # near miss means the node is there under the wrong
                        # name, which is exactly what must not slip through.
                        errors.append("%s should be named %s" % (detail, name))
                    continue

                has_image = detail
                if value != has_image:
                    errors.append("%s is %s but %s %s" % (
                        flag, "on" if value else "off",
                        name, "has an image" if has_image else "has no image"))

        return errors, []

    def check_material(self, mat, alpha):
        """Every rule against one material. Returns (errors, warnings)."""
        errors = self.check_settings(mat, alpha)
        shader_errors, warnings = self.check_shader(mat, alpha)
        return errors + shader_errors, warnings

    def execute(self, context):
        meshes = [obj for obj in context.selected_objects
                  if obj.type == 'MESH' and obj.data is not None]

        if not meshes:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        log_clear(context, check=self.CHECK_NAME)

        # One material serves many objects, so each (material, alpha) pair is
        # only walked once - but the result is reported against every object
        # that uses it, since that is what the artist has to go and fix.
        cache = {}
        seen_as = {}

        error_rows = []
        warning_rows = []
        conflicts = []
        checked = 0

        for obj in meshes:
            alpha = self.is_alpha_asset(obj)
            materials = [slot.material for slot in obj.material_slots if slot.material]

            if not materials:
                warning_rows.append((obj.name, "no material assigned"))
                continue

            for mat in materials:
                checked += 1

                # The same material on an alpha object and an opaque one cannot
                # satisfy both - that is a data problem in its own right, and
                # without flagging it the results would look self-contradictory.
                if seen_as.setdefault(mat.name, alpha) != alpha:
                    if mat.name not in conflicts:
                        conflicts.append(mat.name)

                key = (mat.name, alpha)
                if key not in cache:
                    cache[key] = self.check_material(mat, alpha)
                errors, warnings = cache[key]

                for message in errors:
                    error_rows.append((obj.name, "%s: %s" % (mat.name, message)))
                for message in warnings:
                    warning_rows.append((obj.name, "%s: %s" % (mat.name, message)))

        summary = "%d mesh%s, %d material slot%s, %d error%s" % (
            len(meshes), "" if len(meshes) == 1 else "es",
            checked, "" if checked == 1 else "s",
            len(error_rows), "" if len(error_rows) == 1 else "s")
        log_add(context, self.CHECK_NAME, summary, status='INFO')

        for mat_name in conflicts:
            log_add(context, self.CHECK_NAME,
                    "%s is on both alpha and opaque objects" % mat_name,
                    status='WARNING')

        for obj_name, message in error_rows:
            log_add(context, self.CHECK_NAME, message, obj_name, 'ERROR')
        for obj_name, message in warning_rows:
            log_add(context, self.CHECK_NAME, message, obj_name, 'WARNING')

        if error_rows or conflicts:
            self.report({'WARNING'}, summary + " - see the S4 Env Log panel")
        else:
            self.report({'INFO'}, summary)

        return {'FINISHED'}


# LOD meshes end in LODA/LODB/LODC/..., optionally followed by Blender's duplicate
# suffix (".001"). Matching the suffix matters: DuplicateLODA below creates names
# like "Wall_LODB.001", which a plain endswith("LODB") would never see.
LOD_NAME_RE = re.compile(r"LOD([A-Z])(?:\.\d+)?$")


def lodOf(obj):
    """Return "LODA"/"LODB"/... for a LOD-named mesh, or None for anything else."""
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

class SwitchLOD(bpy.types.Operator):
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

        # Collect every LOD, not just the pair, so LODs outside the pair (LODC
        # when comparing A/B, LODA when comparing B/C, LODD...) get hidden too.
        tagged = {}
        for obj in context.scene.objects:
            lod = lodOf(obj)
            if lod:
                tagged.setdefault(lod, []).append(obj)

        if not tagged.get(target):
            other = pair[1] if target == pair[0] else pair[0]
            if tagged.get(other):
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

class EnableLOD(bpy.types.Operator):
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

class RenameLOD(bpy.types.Operator):
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

class DuplicateLODBase(bpy.types.Operator):
    """Copy the selected LOD meshes into the next LOD level.

    The source and destination letters are the only thing that separates one
    level from the next, so the subclasses below set SRC/DST and inherit the
    rest. Not registered itself - it carries no bl_idname.
    """
    bl_options = {'REGISTER', 'UNDO'}

    SRC = ""
    DST = ""

    def renamed(self, name):
        """Swap the trailing LOD letter, leaving any ".001" suffix in place."""
        return re.sub(r"%s(?=(?:\.\d{3})?$)" % self.SRC, self.DST, name)

    def execute(self, context):
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected:
            self.report({'WARNING'}, "No meshes selected")
            return {'CANCELLED'}

        # Blender's ".001" suffix is what tells the two cases apart: a suffixed
        # set was already instanced, so its copies share one mesh datablock,
        # while a bare "LODA" is a lone mesh and gets its own data.
        suffixed = re.compile(r"%s\.\d{3}$" % self.SRC)
        bare = re.compile(r"%s$" % self.SRC)

        new_objects = []

        if any(suffixed.search(obj.name) for obj in selected):
            shared_mesh_data = None

            for obj in selected:
                new_obj = obj.copy()
                if shared_mesh_data is None:
                    # The first object makes the copy the rest of the set shares.
                    shared_mesh_data = obj.data.copy()
                new_obj.data = shared_mesh_data

                context.collection.objects.link(new_obj)
                new_obj.name = self.renamed(obj.name)
                new_objects.append(new_obj)
                print("Duplicated %s -> %s (Instance)" % (obj.name, new_obj.name))

        elif any(bare.search(obj.name) for obj in selected):
            for obj in selected:
                if not bare.search(obj.name):
                    continue

                new_obj = obj.copy()
                new_obj.data = obj.data.copy()
                context.collection.objects.link(new_obj)
                new_obj.name = self.renamed(obj.name)
                new_objects.append(new_obj)
                print("Duplicated %s -> %s" % (obj.name, new_obj.name))

        if not new_objects:
            self.report({'WARNING'}, "No %s meshes in the selection" % self.SRC)
            return {'CANCELLED'}

        # Hand the new set back as the selection, ready for the next level.
        bpy.ops.object.select_all(action='DESELECT')
        for obj in new_objects:
            obj.select_set(True)

        self.report({'INFO'}, "Duplicated %d mesh%s to %s" % (
            len(new_objects), "" if len(new_objects) == 1 else "es", self.DST))
        return {'FINISHED'}


class DuplicateLODA(DuplicateLODBase):
    bl_idname = "s4.envlodaduplicate"
    bl_label = "Duplicate LODA to LODB"
    bl_description = "Copy the selected LODA meshes into a matching LODB set"

    SRC = "LODA"
    DST = "LODB"

class DuplicateLODB(DuplicateLODBase):
    bl_idname = "s4.envlodbduplicate"
    bl_label = "Duplicate LODB to LODC"
    bl_description = "Copy the selected LODB meshes into a matching LODC set"

    SRC = "LODB"
    DST = "LODC"

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
    S4EnvCheckMaterials,
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
