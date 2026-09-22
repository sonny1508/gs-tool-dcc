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


class S4EnvCheckToolPanel(bpy.types.Panel):
    bl_label = "S4 Env Check Tool"
    bl_idname = "S4_Env_Check"
    bl_space_type = 'VIEW_3D'
    bl_category = "S4 Environment"
    bl_region_type = 'UI'

    # Every check runs over the whole scene - nothing here reads the selection.
    CHECKS = (
        ("s4.envcheckscene", "Check Scene"),
        ("s4.envchecknames", "Check Names"),
        ("s4.envcheckattributes", "Check Attributes"),
        ("s4.envcheckmaterials", "Check Materials"),
        ("s4.envcheckuvs", "Check UVs"),
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        for idname, text in self.CHECKS:
            col.operator(idname, text=text)
        layout.label(text=ADDON_VERSION)

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
# Shared result list for every check tool. self.report() alone lands in the
# Info editor and is easy to miss when a scene has a handful of bad meshes
# among good ones, so checks write their per-object findings here, where the
# panel keeps the offenders on screen and can select them.
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
# Check plumbing
#
# Every check runs over the whole scene and writes its findings through
# CheckResults, so they all read the same in the log: a summary line, then any
# scene-wide rows, then one row per faulty object with its faults joined.
# ---------------------------------------------------------------------------

def plural(count, word, many=None):
    """ "1 mesh", "3 meshes" - `many` for words that do not just take an s."""
    return "%d %s" % (count, word if count == 1 else (many or word + "s"))


def scene_meshes(context):
    """Every mesh object in the scene, with edit-mode changes flushed back."""
    # Mesh data read in edit mode is stale until the mode is left.
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    return [obj for obj in context.scene.objects
            if obj.type == 'MESH' and obj.data is not None]


class CheckResults:
    """One check run's findings, written to the log in one go by publish()."""

    def __init__(self, check):
        self.check = check
        # obj name -> messages, in the order found. "" holds scene-wide rows.
        self.errors = {}
        self.warnings = {}

    def error(self, message, obj_name=""):
        self.errors.setdefault(obj_name, []).append(message)

    def warning(self, message, obj_name=""):
        self.warnings.setdefault(obj_name, []).append(message)

    def publish(self, operator, context, checked):
        """Replace this check's log rows and report. `checked` reads like "12 meshes"."""
        log_clear(context, check=self.check)

        failed = sum(1 for name in self.errors if name)
        summary = "%s checked, %d with errors" % (checked, failed)
        log_add(context, self.check, summary, status='INFO')

        for message in self.errors.get("", []):
            log_add(context, self.check, message, status='ERROR')
        for message in self.warnings.get("", []):
            log_add(context, self.check, message, status='WARNING')
        for status, rows in (('ERROR', self.errors), ('WARNING', self.warnings)):
            for obj_name, messages in rows.items():
                if obj_name:
                    log_add(context, self.check, " | ".join(messages), obj_name, status)

        if self.errors or self.warnings:
            operator.report({'WARNING'}, summary + " - see the S4 Env Log panel")
        else:
            operator.report({'INFO'}, summary)
        return {'FINISHED'}


class S4EnvCheckScene(bpy.types.Operator):
    bl_idname = "s4.envcheckscene"
    bl_label = "Check Scene"
    bl_description = ("Check scene units, unapplied scale on meshes and empties, "
                      "Principled BSDF materials and n-gons")
    bl_options = {'REGISTER', 'UNDO'}

    CHECK_NAME = "Scene"

    # Unit settings the pipeline exports with, as (property, required, label).
    UNIT_RULES = (
        ("system", 'METRIC', "Unit System must be Metric"),
        ("length_unit", 'METERS', "Length Unit must be Meters"),
    )

    # Scale is float data, so an exact != would flag values like 0.99999994
    # that Blender itself displays as 1.
    SCALE_TOLERANCE = 1e-5

    def check_units(self, scene, results):
        settings = scene.unit_settings
        for prop, want, label in self.UNIT_RULES:
            if getattr(settings, prop) != want:
                results.error(label)
        if not math.isclose(settings.scale_length, 1.0, abs_tol=self.SCALE_TOLERANCE):
            results.error("Unit Scale is %g, must be 1" % settings.scale_length)

    @staticmethod
    def principled_materials(obj, cache):
        """Names of this object's materials that use a Principled BSDF node.

        Only top-level nodes are read: the s4s group is built on a Principled
        BSDF internally, so descending into groups would flag every material.
        """
        found = []
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None:
                continue
            hit = cache.get(mat)
            if hit is None:
                tree = mat.node_tree if mat.use_nodes else None
                hit = cache[mat] = tree is not None and any(
                    node.type == 'BSDF_PRINCIPLED' for node in tree.nodes)
            if hit and mat.name not in found:
                found.append(mat.name)
        return found

    @staticmethod
    def ngon_count(mesh):
        """How many faces in the mesh have more than four corners."""
        count = len(mesh.polygons)
        if count == 0:
            return 0
        # foreach_get reads every face size in one call - a Python loop over
        # polygons is the slow part of this check on dense meshes.
        sizes = np.empty(count, dtype=np.int32)
        mesh.polygons.foreach_get("loop_total", sizes)
        return int((sizes > 4).sum())

    def execute(self, context):
        meshes = scene_meshes(context)
        # Empties are only checked for scale; everything else is mesh-only.
        objects = meshes + [obj for obj in context.scene.objects if obj.type == 'EMPTY']
        results = CheckResults(self.CHECK_NAME)

        self.check_units(context.scene, results)
        if not objects:
            results.warning("no meshes or empties in the scene")

        for obj in objects:
            if not all(math.isclose(s, 1.0, abs_tol=self.SCALE_TOLERANCE) for s in obj.scale):
                results.error("scale %s, apply it" % ", ".join(
                    "%g" % round(s, 4) for s in obj.scale), obj.name)

        cache = {}
        for obj in meshes:
            mats = self.principled_materials(obj, cache)
            if mats:
                results.error("Principled BSDF in %s" % " - ".join(mats), obj.name)
            ngons = self.ngon_count(obj.data)
            if ngons:
                results.error(plural(ngons, "n-gon"), obj.name)

        return results.publish(self, context, plural(len(objects), "object"))


class S4EnvCheckNames(bpy.types.Operator):
    bl_idname = "s4.envchecknames"
    bl_label = "Check Names"
    bl_description = ("Check every mesh is named SM_<file>[_N]_LODA/B/C, matches its "
                      "group, and that each group's LODs have no gaps")
    bl_options = {'REGISTER', 'UNDO'}

    CHECK_NAME = "Names"

    # Assets are named after the .blend file: "SM_<file>", optionally numbered
    # "SM_<file>_2" when one file holds several, then the LOD suffix.
    GROUP_PREFIX = "SM_"
    LOD_LETTERS = "ABC"

    # "<prefix>_LOD<letter>". The suffix is matched either case - the addon's
    # own "Add LODA" button writes upper case - but the prefix is exact.
    LOD_RE = re.compile(r"^(.+)_[Ll][Oo][Dd]([A-Za-z])$")

    def split_name(self, name):
        """(prefix, upper-case LOD letter) for a LOD-named mesh, else None."""
        match = self.LOD_RE.match(name)
        if match is None:
            return None
        return match.group(1), match.group(2).upper()

    def group_errors(self, group):
        """Faults across one empty's LOD children, as {child name: [messages]}."""
        letters = {}
        for child in group.children:
            if child.type != 'MESH':
                continue
            parts = self.split_name(child.name)
            if parts and parts[1] in self.LOD_LETTERS:
                letters.setdefault(parts[1], []).append(child.name)

        errors = {}
        for letter, names in letters.items():
            if len(names) > 1:
                # Names are unique, so only a case difference in the suffix
                # can give two meshes the same LOD.
                for name in names:
                    errors.setdefault(name, []).append("duplicate LOD%s" % letter)

        # LODs must run A, B, C with no gaps.
        if letters:
            last = self.LOD_LETTERS.index(max(letters))
            gaps = [l for l in self.LOD_LETTERS[:last] if l not in letters]
            if gaps:
                message = "group missing %s" % " - ".join("LOD" + l for l in gaps)
                for child in group.children:
                    if child.type == 'MESH':
                        errors.setdefault(child.name, []).append(message)

        return errors

    def execute(self, context):
        meshes = scene_meshes(context)
        results = CheckResults(self.CHECK_NAME)

        file_name = os.path.splitext(bpy.path.basename(bpy.data.filepath))[0]
        if file_name:
            prefix_re = re.compile(r"^%s(_\d+)?$" % re.escape(self.GROUP_PREFIX + file_name))
            prefix_label = "%s%s[_N]" % (self.GROUP_PREFIX, file_name)
        else:
            prefix_re = None
            results.warning("file not saved - SM_<file> prefix not checked")

        suffixes = " - ".join("_LOD" + l for l in self.LOD_LETTERS)
        group_cache = {}

        for obj in meshes:
            parts = self.split_name(obj.name)

            if parts is None:
                results.error("must end in %s" % suffixes, obj.name)
            else:
                prefix, letter = parts
                if letter not in self.LOD_LETTERS:
                    results.error("LOD%s not allowed, use %s" % (letter, suffixes), obj.name)
                if prefix_re is not None and not prefix_re.match(prefix):
                    results.error("must start with %s" % prefix_label, obj.name)

            group = obj.parent
            if group is None or group.type != 'EMPTY':
                continue
            if parts is not None and parts[0] != group.name:
                results.error("must start with %s, its group" % group.name, obj.name)

            if group not in group_cache:
                group_cache[group] = self.group_errors(group)
            for message in group_cache[group].get(obj.name, []):
                results.error(message, obj.name)

        return results.publish(self, context, plural(len(meshes), "mesh", "meshes"))


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
FLAG_VC_MULTIPLY = "use_vertexcolor_multiply"
FLAG_VC_AO = "use_vertexcolor_as_ao"


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
        meshes = scene_meshes(context)
        results = CheckResults(self.CHECK_NAME)
        if not meshes:
            results.warning("no meshes in the scene")

        cache = {}
        for obj in meshes:
            for message in self.check_object(obj, cache):
                results.error(message, obj.name)

        return results.publish(self, context, plural(len(meshes), "mesh", "meshes"))


class S4EnvCheckAttributes(bpy.types.Operator):
    bl_idname = "s4.envcheckattributes"
    bl_label = "Check Attributes"
    bl_description = ("Check each mesh's colour attribute is vertexcolor / Face Corner / "
                      "Byte Color, present only when its s4s shader uses vertex colour, "
                      "and that each material's customParameter_takeParamFromShaderNodeName is True")
    bl_options = {'REGISTER', 'UNDO'}

    CHECK_NAME = "Attributes"

    # The one colour attribute the pipeline accepts, and the format it must be
    # in. The colour values themselves are not checked.
    COLOR_NAME = "vertexcolor"
    COLOR_DOMAIN = 'CORNER'
    COLOR_TYPE = 'BYTE_COLOR'
    DOMAIN_LABELS = {'POINT': "Vertex", 'CORNER': "Face Corner"}
    TYPE_LABELS = {'FLOAT_COLOR': "Color", 'BYTE_COLOR': "Byte Color"}

    # Either flag ticked on any of the mesh's shaders means it needs the
    # attribute; both off everywhere means it must carry no colour attribute.
    VERTEXCOLOR_FLAGS = (FLAG_VC_MULTIPLY, FLAG_VC_AO)

    # Material custom property every material on a mesh must carry, set to True.
    TAKE_PARAM_PROP = "customParameter_takeParamFromShaderNodeName"

    def custom_prop_error(self, mat):
        """A message if the material's take-param property is not True, else None."""
        prop = self.TAKE_PARAM_PROP
        value = mat.get(prop)

        if value is None:
            return "%s missing" % prop

        # The property turns up in three forms that all mean True: a real
        # boolean, the int 1 from files older than boolean custom properties,
        # and the string "True" that pipeline-authored materials carry.
        if isinstance(value, str):
            if value.strip().lower() == "true":
                return None
        elif isinstance(value, (bool, int)) and value == 1:
            return None
        return "%s is %r, needs True" % (prop, value)

    def material_requirements(self, mat):
        """One material's demands, as (uses vertex colour, has the shader, errors)."""
        nodes = shader_nodes(mat)
        # A duplicated shader's flags are not read, so the mesh would otherwise
        # be measured against "no vertex colour" and possibly pass.
        errors = ["on %s, not %s" % (name, SHADER_GROUP) for name in stray_shader_names(mat)]
        needs = False

        error = self.custom_prop_error(mat)
        if error:
            errors.append(error)

        for node in nodes:
            for flag in self.VERTEXCOLOR_FLAGS:
                value, exists = shader_flag(node, flag)
                if not exists:
                    errors.append("shader has no %s" % flag)
                needs = needs or value

        return needs, bool(nodes), errors

    def check_object(self, obj, cache):
        """Every attribute rule against one mesh. Returns (errors, warnings)."""
        needs = False
        has_shader = False
        errors = []

        for slot in obj.material_slots:
            mat = slot.material
            if mat is None:
                continue

            result = cache.get(mat)
            if result is None:
                result = cache[mat] = self.material_requirements(mat)

            needs = needs or result[0]
            has_shader = has_shader or result[1]
            for message in result[2]:
                errors.append("%s: %s" % (mat.name, message))

        attrs = obj.data.color_attributes
        color = attrs.get(self.COLOR_NAME)

        stray = [attr.name for attr in attrs if attr.name != self.COLOR_NAME]
        if stray:
            errors.append("%s not allowed" % " - ".join(stray))

        if color is not None:
            if color.domain != self.COLOR_DOMAIN:
                errors.append("%s domain is %s, needs %s" % (
                    self.COLOR_NAME, self.DOMAIN_LABELS.get(color.domain, color.domain),
                    self.DOMAIN_LABELS[self.COLOR_DOMAIN]))
            if color.data_type != self.COLOR_TYPE:
                errors.append("%s type is %s, needs %s" % (
                    self.COLOR_NAME, self.TYPE_LABELS.get(color.data_type, color.data_type),
                    self.TYPE_LABELS[self.COLOR_TYPE]))

        warnings = []
        if needs:
            if color is None:
                errors.append("%s missing - shader uses vertex colour" % self.COLOR_NAME)
        elif has_shader:
            if color is not None:
                errors.append("%s not needed - vertex colour flags are off" % self.COLOR_NAME)
        else:
            # No s4s shader means no flags to say whether the attribute belongs,
            # so only its format was checked.
            warnings.append("no %s node - only the attribute format was checked" % SHADER_GROUP)

        return errors, warnings

    def execute(self, context):
        meshes = scene_meshes(context)
        results = CheckResults(self.CHECK_NAME)
        if not meshes:
            results.warning("no meshes in the scene")

        cache = {}
        for obj in meshes:
            errors, warnings = self.check_object(obj, cache)
            for message in errors:
                results.error(message, obj.name)
            for message in warnings:
                results.warning(message, obj.name)

        return results.publish(self, context, plural(len(meshes), "mesh", "meshes"))


class S4EnvCheckMaterials(bpy.types.Operator):
    bl_idname = "s4.envcheckmaterials"
    bl_label = "Check Materials"
    bl_description = ("Check each material's blend settings and s4s shader flags "
                      "against the object name and the textures actually assigned")
    bl_options = {'REGISTER', 'UNDO'}

    CHECK_NAME = "Materials"

    # The word in an object's name decides which of three render modes it is,
    # matched case-insensitively anywhere in the name - "Window_Glass_LODA" is
    # glass, "alphaFence" is alpha. Alpha and glass are both see-through but
    # they are not the same: glass keeps its backface culling and blends rather
    # than clipping, so they cannot share one rule.
    MODE_WORDS = (
        ('ALPHA', "alpha"),
        ('GLASS', "glass"),
    )
    MODE_OPAQUE = 'OPAQUE'

    # The properties checked, and what each mode requires of them - in the same
    # order, so a mode is read as one row.
    SETTING_PROPS = ("use_backface_culling", "blend_method", "shadow_method")
    MODE_SETTINGS = {
        'ALPHA':  (False, 'CLIP', 'CLIP'),
        'GLASS':  (True, 'BLEND', 'CLIP'),
        'OPAQUE': (True, 'OPAQUE', 'OPAQUE'),
    }

    # Both see-through modes require the shader's alpha flag; opaque is left
    # alone, since only the see-through cases have a stated requirement.
    MODES_NEEDING_ALPHA = ('ALPHA', 'GLASS')

    # How each mode and setting reads in the UI, for the log row.
    MODE_LABELS = {'ALPHA': "alpha", 'GLASS': "glass", 'OPAQUE': "opaque"}
    SETTING_LABELS = {
        False: "off", True: "on",
        'CLIP': "Alpha Clip", 'BLEND': "Alpha Blend", 'OPAQUE': "Opaque",
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

    def object_mode(self, obj):
        """Which render mode an object's name asks for, or None if ambiguous.

        A name carrying both words cannot be resolved - the two modes disagree
        on culling and on blending, so there is no safe reading. The name is
        the fault to fix, and the caller reports it instead of checking on.
        """
        name = obj.name.lower()
        matched = [mode for mode, word in self.MODE_WORDS if word in name]

        if len(matched) > 1:
            return None
        if matched:
            return matched[0]
        return self.MODE_OPAQUE

    def check_settings(self, mat, mode):
        """Blend/culling settings against what the object's name calls for."""
        errors = []
        for prop, want in zip(self.SETTING_PROPS, self.MODE_SETTINGS[mode]):
            got = getattr(mat, prop)
            if got != want:
                errors.append("%s is %s, needs %s (%s)" % (
                    prop, self.SETTING_LABELS.get(got, got),
                    self.SETTING_LABELS.get(want, want),
                    self.MODE_LABELS[mode]))
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

    def check_shader(self, mat, mode):
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
            if mode in self.MODES_NEEDING_ALPHA:
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

    def check_material(self, mat, mode):
        """Every rule against one material. Returns (errors, warnings)."""
        errors = self.check_settings(mat, mode)
        shader_errors, warnings = self.check_shader(mat, mode)
        return errors + shader_errors, warnings

    def execute(self, context):
        meshes = scene_meshes(context)
        results = CheckResults(self.CHECK_NAME)
        if not meshes:
            results.warning("no meshes in the scene")

        # One material serves many objects, so each (material, mode) pair is
        # only walked once - but the result is reported against every object
        # that uses it, since that is what the artist has to go and fix.
        cache = {}
        seen_modes = {}

        for obj in meshes:
            mode = self.object_mode(obj)

            if mode is None:
                # Ambiguous name: the alpha and glass rules contradict each
                # other, so there is nothing to check this object against.
                results.error("name has both %s - cannot tell which applies"
                              % " and ".join(word for _, word in self.MODE_WORDS), obj.name)
                continue

            materials = [slot.material for slot in obj.material_slots if slot.material]
            if not materials:
                results.warning("no material assigned", obj.name)
                continue

            for mat in materials:
                # The same material on, say, an alpha object and an opaque one
                # cannot satisfy both - a data problem in its own right, and
                # without flagging it the results look self-contradictory.
                seen_modes.setdefault(mat.name, set()).add(mode)

                key = (mat.name, mode)
                if key not in cache:
                    cache[key] = self.check_material(mat, mode)
                errors, warnings = cache[key]

                for message in errors:
                    results.error("%s: %s" % (mat.name, message), obj.name)
                for message in warnings:
                    results.warning("%s: %s" % (mat.name, message), obj.name)

        for mat_name in sorted(name for name, modes in seen_modes.items() if len(modes) > 1):
            modes = sorted(self.MODE_LABELS[m] for m in seen_modes[mat_name])
            results.warning("%s is on %s objects" % (mat_name, " and ".join(modes)))

        return results.publish(self, context, plural(len(meshes), "mesh", "meshes"))


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
    S4EnvCheckToolPanel,
    S4EnvLogEntry,
    S4ENV_UL_log,
    S4EnvLogSelectErrors,
    S4EnvLogSelectOne,
    S4EnvLogClear,
    S4EnvCheckScene,
    S4EnvCheckNames,
    S4EnvCheckAttributes,
    S4EnvCheckMaterials,
    S4EnvCheckUVs,
    S4EnvLODToolPanel,
    S4EnvUtilitiToolPanel,
    S4EnvLogPanel,
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

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
