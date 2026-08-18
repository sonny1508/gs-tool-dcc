bl_info = {
    "name": "S4 Vehicle Tools",
    "author": "Glenda Studio",
    "version": (1, 2),
    "blender": (3, 6, 10),
    "location": "Sidebar",
    "description": "Validates S4 assets requirements for uploading",
    "category": "Object",
}

import os

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup
from mathutils import Vector

ADDON_VERSION = "Version 1.2"

# Single source of truth for the blend file that ships the S4 custom shader
# node groups.
SHADER_BLEND_PATH = r"C:\Dev\PROJECTS\GTR\SOURCE_ART\BLENDER\SHADERS\S4_Vehicle_Shaders.blend"
TIRE_RIG_BLEND_PATH = r"C:\Dev\PROJECTS\GTR\SOURCE_ART\VEHICLES\_tires\tire_deformation_rig.blend"


# ---------------------------------------------------------------------------
# Scene layout constants
# ---------------------------------------------------------------------------

LOD_COLLECTIONS = ("LODA", "LODB", "LODC", "LODD", "CPIT")

# Parts every LOD of the wheel assembly has to ship.
_BRAKE_PARTS = [
    "CALIPER_LF", "CALIPER_LR", "CALIPER_RF", "CALIPER_RR",
    "DISC_LF", "DISC_LR", "DISC_RF", "DISC_RR",
]
_WHEEL_PARTS = [
    "TIRE_LF", "TIRE_LR", "TIRE_RF", "TIRE_RR",
    "WHEEL_LF", "WHEEL_LR", "WHEEL_RF", "WHEEL_RR",
]

# Object names are expected to read "<anything>_<part>_<collection>".
REQUIRED_MESHES = {
    "LODA": ["CHASSIS"] + _BRAKE_PARTS + _WHEEL_PARTS,
    "LODB": ["CHASSIS"] + _BRAKE_PARTS + _WHEEL_PARTS,
    "LODC": ["CHASSIS"] + _WHEEL_PARTS,
    "LODD": ["CHASSIS"],
    "CPIT": [
        "BODY", "BONNET", "BUMPER_F", "CHASSIS", "DISPLAY", "EXTANIM",
        "INTANIM", "INTERIOR", "STEERINGWHEEL", "WINDOWS",
    ],
}

# LOD pairs checked for parts that exist in the lower LOD but went missing
# in the higher one.
LOD_COMPLETENESS_PAIRS = (("LODA", "LODB"), ("LODB", "LODC"), ("LODC", "LODD"))

# Mesh part name -> armature bone it gets parented to on export.
BONE_MAPPING = {
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

ARMATURE_NAME = "Armature_LOD"
TIRE_DEFORM_COLLECTIONS = ("Tire Deformations", "Deformations")
TIRE_CORNERS = ("LF", "LR", "RF", "RR")

# Any object whose name contains one of these is a known-good vehicle part.
VALID_MESH_NAMES = (
    "BODY_LOD", "BONNET_LOD", "BUMPER_F_LOD", "BUMPER_LR_LOD",
    "BUMPER_RR_LOD", "CALIPER_LF_LOD", "CALIPER_LR_LOD", "CALIPER_RF_LOD",
    "CALIPER_RR_LOD", "CHASSIS_LOD", "DISC_LF_LOD", "DISC_LR_LOD",
    "DISC_RF_LOD", "DISC_RR_LOD", "DIVEPLANE_R1_LOD", "DIVEPLANE_L1_LOD", "INTERIOR_LOD",
    "LIGHTS_LOD", "STEERINGWHEEL_LOD", "TIRE_LF_LOD", "TIRE_LR_LOD", "TIRE_RF_LOD",
    "TIRE_RR_LOD", "WHEEL_LF_BLUR_LOD", "WHEEL_LF_LOD", "WHEEL_LR_BLUR_LOD", "WHEEL_LR_LOD",
    "WHEEL_RF_BLUR_LOD", "WHEEL_RF_LOD", "WHEEL_RR_BLUR_LOD", "WHEEL_RR_LOD", "WING_LOD", "BODY_CPIT",
    "BONNET_CPIT", "BUMPER_F_CPIT", "CHASSIS_CPIT", "DISPLAY_CPIT", "EXTANIM_CPIT", "INTANIM_CPIT",
    "INTERIOR2_CPIT", "INTERIOR_CPIT", "STEERINGWHEEL_CPIT", "TIRE_LF_CPIT", "TIRE_RF_CPIT", "WHEEL_LF_CPIT",
    "WHEEL_RF_CPIT", "WINDOWS_CPIT", "DRIVERNAME_CPIT", "WIPER_LOD", "DISC_LF_CPIT", "CALIPER_LF_CPIT", "DISC_RF_CPIT",
    "CALIPER_RF_CPIT", "LIGHTS_CPIT", "NEEDLE_TACH_CPIT", "NEEDLE_WATER_CPIT", "NEEDLE_OILT_CPIT", "GEARSHIFT_CPIT",
    "NEEDLE_OILP_CPIT", "NEEDLE_FUELP_CPIT", "GAUGE_GLASS_CPIT", "REARWING_CPIT", "PANEL_R_LOD", "PANEL_L_LOD", "MIRROR_R_LOD",
    "MIRROR_L_LOD",
)

# Materials that are allowed to keep a stock Principled BSDF.
PRINCIPLED_ALLOWED_MATERIALS = (
    "Dots Stroke", "LCDisplay", "VirtualMirror", "virtualmirror", "Master deform tire",
)

# Every S4 shader group that is a valid surface root for a material.
S4_SHADER_GROUPS = (
    "S4 Vehicle Glass Shader",
    "S4 Vehicle Bodywork Shader",
    "S4 Vehicle Basic Shader",
    "S4 Vehicle Tire Shader",
    "S4 Vehicle Wheels Shader",
    "S4 Vehicle LightGlass Shader",
    "str4_vehicleBodyworkShader",
)

DIRT_GROUP_NAME = "Dirt/Damage_Group"
DIRT_GROUP_INPUTS = {"dirt": 0, "dust": 1, "mud": 2, "deform": 3}
SPEED_NODE_GROUPS = ("SpeedNodeGroup", "SpeedNodeGroup.001", "SpeedNodeGroup.002")
LIGHTS_INPUT_INDEX = 33
LIGHT_MATERIAL_KEYWORDS = ("light", "interior", "cockpit")

VIEWPORT_DEFAULT_COLOR = (0.2392, 0.2392, 0.2392)
VIEWPORT_CHECK_COLOR = (1.0, 0.0, 0.815)


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def show_message_box(lines, title, icon):
    def draw(self, context):
        for line in lines:
            self.layout.label(text=line)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def add_item(collection, item_type, message):
    """Append one row to the check-result list shown in the validator panel."""
    item = collection.add()
    item.name = item_type
    item.type = item_type
    item.message = message


def iter_view3d_spaces():
    """Every 3D viewport space across every open window."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    yield space


def active_view3d_space(context):
    """The viewport the operator was run from, else the first one open."""
    space = context.space_data
    if space is not None and space.type == 'VIEW_3D':
        return space
    return next(iter_view3d_spaces(), None)


def purge_orphans():
    """Drop the datablocks left behind by linking a node group in."""
    try:
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=False)
    except RuntimeError as error:
        print(f"S4 Vehicle Tools: orphan purge skipped ({error})")


def clear_selection():
    for obj in bpy.context.selected_objects:
        obj.select_set(False)


# ---------------------------------------------------------------------------
# Shader value drivers (scene property update callbacks)
# ---------------------------------------------------------------------------

def iter_group_nodes(material, group_name):
    """Top level group nodes in `material` that instance `group_name`."""
    if not material.use_nodes or material.node_tree is None:
        return
    for node in material.node_tree.nodes:
        if node.bl_idname != 'ShaderNodeGroup':
            continue
        if node.node_tree is not None and node.node_tree.name == group_name:
            yield node


def set_dirt_group_input(input_index, value):
    """Push one Dirt/Damage_Group slider value onto every material using it."""
    for material in bpy.data.materials:
        material.use_nodes = True
        for node in iter_group_nodes(material, DIRT_GROUP_NAME):
            node.inputs[input_index].default_value = value


def wheel_speed(self, context):
    for group_name in SPEED_NODE_GROUPS:
        group = bpy.data.node_groups.get(group_name)
        if group is None:
            continue
        output = group.nodes.get("Group Output")
        if output is not None:
            output.inputs[0].default_value = self.wheel_speed


def dirt_value(self, context):
    set_dirt_group_input(DIRT_GROUP_INPUTS["dirt"], self.dirt_value)


def dust_value(self, context):
    set_dirt_group_input(DIRT_GROUP_INPUTS["dust"], self.dust_value)


def mud_value(self, context):
    set_dirt_group_input(DIRT_GROUP_INPUTS["mud"], self.mud_value)


def deform_value(self, context):
    """Drive both the body shape keys and the shader's deform input."""
    for collection_name in ("LODA", "LODB", "LODC", "CPIT"):
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            continue
        for obj in collection.all_objects:
            if obj.type != 'MESH' or not obj.data.shape_keys:
                continue
            for shape in obj.data.shape_keys.key_blocks:
                shape.value = self.deform_value

    set_dirt_group_input(DIRT_GROUP_INPUTS["deform"], self.deform_value)


def lights_value(self, context):
    for material in bpy.data.materials:
        if not any(keyword in material.name for keyword in LIGHT_MATERIAL_KEYWORDS):
            continue
        material.use_nodes = True
        for node in iter_group_nodes(material, "S4 Vehicle Basic Shader"):
            if len(node.inputs) > LIGHTS_INPUT_INDEX:
                node.inputs[LIGHTS_INPUT_INDEX].default_value = self.lights_value


def object_search_poll(self, object):
    return object.type in ('MESH', 'CURVE')


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def process_collection(collection_name):
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        return

    # Move object to export and remove suffix
    for obj in collection.objects:
        remove_suffix(obj, collection_name)
        for part_name, target_bone in BONE_MAPPING.items():
            if part_name in obj.name:
                parent_to_bone(obj.name, target_bone)
                break

    export_to_fbx(collection_name)

    # Reset objects to initial state
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
    armature_obj = bpy.data.objects[ARMATURE_NAME]
    if mesh_obj.parent_bone == bone_name:
        print(f"Warning: Bone {bone_name} already parented to armature.")
        return
    if armature_obj.pose.bones.get(bone_name) is None:
        print(f"Error: Bone {bone_name} not found in armature.")
        return

    # Parenting moves the mesh, so restore its world matrix afterwards.
    mesh_matrix = mesh_obj.matrix_world.copy()
    mesh_obj.parent = armature_obj
    mesh_obj.parent_type = 'BONE'
    mesh_obj.parent_bone = bone_name
    mesh_obj.matrix_world = mesh_matrix
    print(f"{mesh_name} parented to bone {bone_name}.")


def export_to_fbx(collection_name):
    export_dir = os.path.join(os.path.dirname(bpy.data.filepath), "ExportedFBX")
    os.makedirs(export_dir, exist_ok=True)

    clear_selection()
    for obj in bpy.data.collections[collection_name].all_objects:
        obj.select_set(True)

    armature_obj = bpy.data.objects[ARMATURE_NAME]
    bpy.context.view_layer.objects.active = armature_obj
    armature_obj.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    for bone in armature_obj.pose.bones:
        bone.bone.select = True

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
        use_active_collection=False,
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
        print(f"Error: {obj.name} does not end in {suffix}")


def add_suffix(obj, collection_name):
    suffix = "_" + collection_name
    if obj.name.endswith(suffix):
        print(f"Error: {obj.name} already ends in {suffix}")
    obj.name += suffix
    obj.data.update()


def missing_meshes(collection_name):
    """Required part suffixes that no object in `collection_name` matches."""
    collection = bpy.data.collections.get(collection_name)
    missing = []
    for part in REQUIRED_MESHES[collection_name]:
        suffix = f"_{part}_{collection_name}"
        found = collection is not None and any(
            obj.name.endswith(suffix) for obj in collection.objects
        )
        if not found:
            missing.append(f"{suffix} not found in {collection_name}")
    return missing


def find_missing_meshes(higher_collection_name, lower_collection_name):
    """Parts present in the lower LOD but absent from the higher one."""
    lower_collection = bpy.data.collections.get(lower_collection_name)
    higher_collection = bpy.data.collections.get(higher_collection_name)
    if lower_collection is None:
        print(f"Error: Collection {lower_collection_name} not found.")
        return []
    if higher_collection is None:
        print(f"Error: Collection {higher_collection_name} not found.")
        return []

    # Names are compared with the trailing "_LODx" removed.
    higher_names = {
        obj.name[:-5] for obj in higher_collection.all_objects if obj.type == 'MESH'
    }
    return [
        f"{obj.name[:-5]} present in {lower_collection_name} but not in {higher_collection_name}"
        for obj in lower_collection.all_objects
        if obj.type == 'MESH' and obj.name[:-5] not in higher_names
    ]


# ---------------------------------------------------------------------------
# Tire deformation helpers
# ---------------------------------------------------------------------------

def check_and_unlink_objects(object_array):
    """Give every object its own mesh data so deforms do not bleed across."""
    for index, mesh in enumerate(object_array):
        for other_mesh in object_array[index + 1:]:
            if mesh.data == other_mesh.data:
                other_mesh.data = mesh.data.copy()


def clear_old_armature_modifiers(mesh):
    for modifier in list(mesh.modifiers):
        if modifier.type == 'ARMATURE':
            mesh.modifiers.remove(modifier)


def tire_deform_collection():
    for name in TIRE_DEFORM_COLLECTIONS:
        collection = bpy.data.collections.get(name)
        if collection is not None:
            return collection
    return None


def position_tire_deform(corner, lod_a_tires):
    """Snap the deform rig for one corner onto its matching tire mesh."""
    context = bpy.context
    scene = context.scene
    deform_collection = bpy.data.collections["Tire Deformations"]

    for tire in lod_a_tires:
        if tire.type != 'MESH' or corner not in tire.name:
            continue

        # Park the 3D cursor on the tire, then snap the rig to the cursor.
        tire.select_set(True)
        selected = context.selected_objects
        assert len(selected)
        scene.cursor.location = sum(
            (obj.matrix_world.translation for obj in selected), Vector()
        ) / len(selected)
        tire.select_set(False)

        for obj in deform_collection.all_objects:
            if obj.type == 'ARMATURE' and corner in obj.name:
                obj.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')

                for area in context.screen.areas:
                    if area.type != 'VIEW_3D':
                        continue
                    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                    if region is None:
                        continue
                    with context.temp_override(area=area, region=region):
                        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
            obj.select_set(False)


def transfer_tire_weight(corner, lod_a_tires):
    context = bpy.context
    deform_collection = bpy.data.collections["Tire Deformations"]

    for tire in lod_a_tires:
        bpy.ops.object.select_all(action='DESELECT')
        if tire.type != 'MESH' or corner not in tire.name:
            continue

        tire.select_set(True)
        for rig in deform_collection.all_objects:
            if corner not in rig.name:
                continue
            for child in bpy.data.objects:
                if child.parent != rig:
                    continue
                child.select_set(True)
                context.view_layer.objects.active = tire
                bpy.ops.paint.weight_paint_toggle()
                bpy.ops.object.data_transfer(
                    use_reverse_transfer=True,
                    data_type='VGROUP_WEIGHTS',
                    vert_mapping='POLYINTERP_NEAREST',
                    layers_select_src='NAME',
                    layers_select_dst='ALL',
                    mix_mode='REPLACE',
                )
                bpy.ops.paint.weight_paint_toggle()


def addmodifier_linktire_deform(corner, lod_a_tires):
    context = bpy.context
    deform_collection = bpy.data.collections["Tire Deformations"]

    for tire in lod_a_tires:
        if tire.type != 'MESH' or corner not in tire.name:
            continue

        tire.select_set(True)
        context.view_layer.objects.active = tire
        bpy.ops.object.modifier_add(type='ARMATURE')
        modifier = context.object.modifiers["Armature"]
        for rig in deform_collection.all_objects:
            if rig.type == 'ARMATURE' and corner in rig.name:
                modifier.object = rig
                tire.select_set(False)


# ---------------------------------------------------------------------------
# Property groups and lists
# ---------------------------------------------------------------------------

class S4VehCheckResult(bpy.types.PropertyGroup):
    # name: StringProperty() -> Instantiated by default
    type: StringProperty()
    message: StringProperty()


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


class S4VEH_UL_check_results(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, "message", text=item.type, emboss=False, icon_value=icon)


# ---------------------------------------------------------------------------
# Panels
# ---------------------------------------------------------------------------

class S4VehPanel:
    """Shared sidebar placement for every S4 Vehicle panel.

    Subclasses must list this mix-in *before* bpy.types.Panel so these plain
    strings win the attribute lookup over Panel's own RNA properties.
    """
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "S4 Vehicle"


class ValidationToolMainPanel(S4VehPanel, bpy.types.Panel):
    bl_label = "S4 Veh Validator"
    bl_idname = "OBJECT_PT_Validation"

    def draw(self, context):
        scn = context.scene
        layout = self.layout

        layout.label(text="Run all check")

        layout.operator("mesh.initialcheck", text="Check Scene")

        if scn.checkResult_all:
            layout.template_list("S4VEH_UL_check_results", "", scn, "custom", scn, "custom_index")
            layout.operator("custom.clear_list", text="Clear and hide result box.")

        layout.label(text=ADDON_VERSION)


class ShaderToolPanel(S4VehPanel, bpy.types.Panel):
    bl_label = "S4 Shader Tool"
    bl_idname = "OBJECT_PT_Shader"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        column = layout.column(align=True)
        column.operator("mesh.basicshader", text="S4 Vehicle Basic Shader")
        column.operator("mesh.bodyworkshader", text="S4 Vehicle Bodywork Shader")
        column.operator("mesh.glassshader", text="S4 Vehicle Glass Shader")
        column.operator("mesh.lightglassshader", text="S4 Vehicle LightGlass Shader")
        column.operator("mesh.tireshader", text="S4 Vehicle Tire Shader")
        column.operator("mesh.wheelshader", text="S4 Vehicle Wheels Shader")

        layout.label(text="Other Node")
        column = layout.column(align=True)
        column.operator("mesh.dirtshader", text="S4 Vehicle Dirt/Damage")
        column.operator("mesh.speednode", text="S4 Wheel Speed")


class UtilitiesToolPanel(S4VehPanel, bpy.types.Panel):
    bl_label = "S4 Utilities Tool"
    bl_idname = "OBJECT_PT_Utilities"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        space = active_view3d_space(context)

        row = layout.row()
        row.alert = bool(space and space.shading.show_backface_culling)
        row.operator("mesh.backface", text="Toggle Backface Culling")

        row = layout.row()
        row.alert = any(s.overlay.show_wireframes for s in iter_view3d_spaces())
        row.operator("mesh.viewwireframe", text="Toggle Wireframe")

        layout.operator("mesh.viewportcol", text="Change Viewport Color")
        layout.operator("mesh.selngon", text="Select N-Gons Face")

        layout.label(text="Other Check:")
        column = layout.column()
        for prop_name in ("dirt_value", "dust_value", "mud_value", "deform_value",
                          "wheel_speed", "lights_value"):
            column.prop(scn, prop_name, slider=True)

        layout.label(text="Other tools")
        column = layout.column(align=True)
        column.operator("s4veh.setupscene", text="Setup S4 Scene")
        column.operator("s4veh.correctmat", text="Correct Duplicate Material")
        column.operator("s4veh.removeshapekey", text="Remove Shapekey")
        column.operator("s4veh.applylattice", text="Apply Lattice as Shapekey")
        column.operator("s4veh.keyshapekey", text="Keyframe for all Shapekey")


class TireDeformPanel(S4VehPanel, bpy.types.Panel):
    bl_label = "S4 Tire Deform Tool"
    bl_idname = "OBJECT_PT_TireDeform"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scn = context.scene
        layout = self.layout

        for label, prop_name in (("Tire RF", "tire_RF"), ("Tire RR", "tire_RR"),
                                 ("Tire LF", "tire_LF"), ("Tire LR", "tire_LR")):
            row = layout.row()
            row.label(text=label)
            row.prop(scn, prop_name, text="")

        column = layout.column(align=True)
        column.operator("mesh.createtiredeform", text="Create Tire Deform Objects")
        column.operator("mesh.applytireweight", text="Apply Weight")


class VertexAOPanel(S4VehPanel, bpy.types.Panel):
    bl_label = "S4 Vertex Ambient"
    bl_idname = "OBJECT_PT_VertexAO"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        column = self.layout.column(align=True)
        column.operator("mesh.bakevertexao", text="Bake Vertex AO")
        column.operator("mesh.exitbakevertexao", text="Restore Node Connection")


class S4VehLODRigging(S4VehPanel, bpy.types.Panel):
    bl_label = "S4 LOD Rigging"
    bl_idname = "S4Veh_LOD_Rig"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scn = context.scene
        layout = self.layout

        layout.label(text="Select Part Rig:")
        for label, prop_name in (("Body Base", "s4veh_body_base"),
                                 ("WHEEL LF", "s4veh_wheel_lf"),
                                 ("WHEEL LR", "s4veh_wheel_lr"),
                                 ("WHEEL RF", "s4veh_wheel_rf"),
                                 ("WHEEL RR", "s4veh_wheel_rr"),
                                 ("STEERINGWHEEL", "s4veh_steeringwheel")):
            row = layout.row()
            row.label(text=label)
            row.prop(scn, prop_name, text="")

        layout.operator("s4veh.riglod", text="Rig Vehicle")


class LODValidPanel(S4VehPanel, bpy.types.Panel):
    bl_label = "S4 LOD Validation"
    bl_idname = "OBJECT_PT_Lodcheck"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        layout.prop(context.scene.lod_holder, "lod_list", text="Select LOD")
        column = layout.column(align=True)
        column.operator("mesh.switchlod", text="Swap")
        column.operator("mesh.enablelod", text="Enable All LOD Viewport")


class ExportPanel(S4VehPanel, bpy.types.Panel):
    bl_label = "S4 Exporter"
    bl_idname = "MY_TEST_PANEL_PT"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        missing = []
        for collection_name in REQUIRED_MESHES:
            missing.extend(missing_meshes(collection_name))
        for message in missing:
            box.label(text=message, icon='ERROR')
        if not missing:
            box.label(text="All meshes present.", icon='CHECKMARK')

        lod_errors = []
        for higher, lower in LOD_COMPLETENESS_PAIRS:
            lod_errors.extend(find_missing_meshes(higher, lower))
        for message in lod_errors:
            box.label(text=message, icon='CANCEL')

        row = layout.row()
        if lod_errors:
            row.enabled = False
            row.operator("mesh.export_vehicle_operator", icon="CANCEL")
        else:
            box.label(text="LOD structure is valid.", icon='CHECKMARK')
            row.operator("mesh.export_vehicle_operator", icon="EXPORT")


# ---------------------------------------------------------------------------
# Validation operators
# ---------------------------------------------------------------------------

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
        if context.scene.custom:
            context.scene.custom.clear()
            context.scene.checkResult_all = False
            self.report({'INFO'}, "All items removed")
        else:
            self.report({'INFO'}, "Nothing to remove")
        return {'FINISHED'}


class InitialCheck(bpy.types.Operator):
    bl_idname = "mesh.initialcheck"
    bl_label = "Initial Check"
    bl_description = "Run through all check processes"

    def check_mesh_names(self, results):
        for collection in bpy.data.collections:
            if collection.name not in LOD_COLLECTIONS:
                continue
            for obj in collection.objects:
                if obj.type == 'ARMATURE' or "deformation" in obj.name:
                    continue
                if not any(valid in obj.name for valid in VALID_MESH_NAMES):
                    add_item(results, "Mesh Name", obj.name)

    def check_material_nodes(self, results):
        for material in bpy.data.materials:
            if any(allowed in material.name for allowed in PRINCIPLED_ALLOWED_MATERIALS):
                continue
            if not material.use_nodes or material.node_tree is None:
                add_item(results, "MaterialNode", f"{material.name} (no node tree)")
                continue
            if any(node.type == 'BSDF_PRINCIPLED' for node in material.node_tree.nodes):
                add_item(results, "MaterialNode", material.name)

    def check_uv_names(self, results):
        for collection in bpy.data.collections:
            if collection.name not in LOD_COLLECTIONS:
                continue
            for obj in collection.objects:
                if obj.type != 'MESH':
                    continue
                if any("UVMap" not in uv.name for uv in obj.data.uv_layers):
                    add_item(results, "UVChannel", obj.name)

    def check_ngons(self, results, scene):
        for obj in scene.objects:
            if obj.type != 'MESH':
                continue
            if any(len(polygon.vertices) > 4 for polygon in obj.data.polygons):
                add_item(results, "N-Gons mesh", obj.name)

    def check_units(self, results, scene):
        units = scene.unit_settings
        if units.scale_length != 1:
            add_item(results, "Unit Scale", "Unit Scale must be 1")
        if units.length_unit != "METERS":
            add_item(results, "Unit Scale", "Length Unit must be Meters")
        if units.system != "METRIC":
            add_item(results, "Unit System", "Unit System must be Metric")

    def execute(self, context):
        scene = context.scene
        scene.custom.clear()

        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            pass

        scene_objects = list(scene.objects)
        if not scene_objects:
            scene.checkResult_all = True
            show_message_box(["Scene in empty."], "S4 Validation", "ERROR")
            return {'FINISHED'}

        context.view_layer.objects.active = scene_objects[0]

        self.check_mesh_names(scene.custom)
        self.check_material_nodes(scene.custom)
        self.check_uv_names(scene.custom)
        self.check_ngons(scene.custom, scene)
        self.check_units(scene.custom, scene)

        scene.checkResult_all = True
        show_message_box(["Checking Finished."], "S4 Validation", "CHECKMARK")
        return {'FINISHED'}


class ExportVehicleOperator(bpy.types.Operator):
    bl_idname = "mesh.export_vehicle_operator"
    bl_label = "Export Vehicle"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for collection_name in ("LODA", "LODB", "LODC", "LODD"):
            process_collection(collection_name)
        print("Finished")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Shader generation operators
# ---------------------------------------------------------------------------

class ShaderNodeGroupOperator(bpy.types.Operator):
    """Links one S4 node group in from the shader library and drops an
    instance of it into the active material.

    Subclasses only supply `bl_idname`, `node_group_name` and `report_title`.
    """
    bl_label = "Generate Shader"
    bl_description = "Auto Generate S4 Custom Shader Node"
    bl_options = {'REGISTER', 'UNDO'}

    node_group_name = ""
    report_title = "S4 Shader"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.active_material is not None

    def import_node_group(self):
        if not os.path.isfile(SHADER_BLEND_PATH):
            show_message_box(
                ["S4 Shader source file not found:", SHADER_BLEND_PATH],
                self.report_title, "ERROR",
            )
            return False

        with bpy.data.libraries.load(SHADER_BLEND_PATH, link=True) as (data_from, data_to):
            if self.node_group_name in data_from.node_groups:
                data_to.node_groups = [self.node_group_name]

        if not data_to.node_groups or not data_to.node_groups[0]:
            show_message_box(["Failed to Generate Shader Node"], self.report_title, "ERROR")
            return False

        show_message_box(["Successfully Generate Shader Node"], self.report_title, "CHECKMARK")
        return True

    def execute(self, context):
        if not self.import_node_group():
            return {'CANCELLED'}

        nodes = context.object.active_material.node_tree.nodes
        group = nodes.new(type='ShaderNodeGroup')
        group.node_tree = bpy.data.node_groups[self.node_group_name]

        purge_orphans()
        return {'FINISHED'}


class BasicShader(ShaderNodeGroupOperator):
    bl_idname = "mesh.basicshader"
    node_group_name = "S4 Vehicle Basic Shader"
    report_title = "S4 Basic Shader"


class BodyworkShader(ShaderNodeGroupOperator):
    bl_idname = "mesh.bodyworkshader"
    node_group_name = "S4 Vehicle Bodywork Shader"
    report_title = "S4 Bodywork Shader"


class GlassShader(ShaderNodeGroupOperator):
    bl_idname = "mesh.glassshader"
    node_group_name = "S4 Vehicle Glass Shader"
    report_title = "S4 Glass Shader"


class LightGlassShader(ShaderNodeGroupOperator):
    bl_idname = "mesh.lightglassshader"
    node_group_name = "S4 Vehicle LightGlass Shader"
    report_title = "S4 Light Glass Shader"


class TireShader(ShaderNodeGroupOperator):
    bl_idname = "mesh.tireshader"
    node_group_name = "S4 Vehicle Tire Shader"
    report_title = "S4 Tire Shader"


class WheelShader(ShaderNodeGroupOperator):
    bl_idname = "mesh.wheelshader"
    node_group_name = "S4 Vehicle Wheels Shader"
    report_title = "S4 Wheel Shader"


class DirtShader(ShaderNodeGroupOperator):
    bl_idname = "mesh.dirtshader"
    node_group_name = DIRT_GROUP_NAME
    report_title = "S4 Dirt Shader"


class SpeedNode(ShaderNodeGroupOperator):
    bl_idname = "mesh.speednode"
    bl_label = "Generate Speed Node"
    node_group_name = "SpeedNodeGroup"
    report_title = "S4 SpeedNode"


# ---------------------------------------------------------------------------
# Viewport utility operators
# ---------------------------------------------------------------------------

class ToggleBackFace(bpy.types.Operator):
    bl_idname = "mesh.backface"
    bl_label = "Toggle Backface"
    bl_description = "Toggle Backface Culling For Checking"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        space = active_view3d_space(context)
        if space is None:
            self.report({'ERROR'}, "Make sure a 3D Viewport is open or visible in your screen!")
            return {'CANCELLED'}

        space.shading.show_backface_culling = not space.shading.show_backface_culling
        return {'FINISHED'}


class ToggleViewColor(bpy.types.Operator):
    bl_idname = "mesh.viewportcol"
    bl_label = "Toggle Viewport Color"
    bl_description = "Change Viewport Color for backface checking"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        gradients = context.preferences.themes[0].view_3d.space.gradients
        current = tuple(round(channel, 4) for channel in gradients.high_gradient)

        if current == VIEWPORT_DEFAULT_COLOR:
            gradients.background_type = 'SINGLE_COLOR'
            gradients.high_gradient = VIEWPORT_CHECK_COLOR
        else:
            gradients.high_gradient = VIEWPORT_DEFAULT_COLOR
        return {'FINISHED'}


class ToggleWireFrame(bpy.types.Operator):
    bl_idname = "mesh.viewwireframe"
    bl_label = "Toggle Viewport Wire Frame"
    bl_description = "Toggle Mesh Wireframe"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for space in iter_view3d_spaces():
            space.overlay.show_wireframes = not space.overlay.show_wireframes
        return {'FINISHED'}


class SelectNgon(bpy.types.Operator):
    bl_idname = "mesh.selngon"
    bl_label = "Select N-Gons"
    bl_description = "Select every face with more than four vertices"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        # Selection flags can only be set from object mode.
        bpy.ops.object.mode_set(mode='OBJECT')

        for polygon in context.active_object.data.polygons:
            polygon.select = len(polygon.vertices) > 4

        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# LOD operators
# ---------------------------------------------------------------------------

# Selection -> the pair of collections the Swap button flips between.
LOD_SWAP_PAIRS = {
    "A": ("LODA", "LODB"),
    "B": ("LODB", "LODC"),
    "C": ("LODC", "LODD"),
    "CP": ("CPIT", "LODA"),
}


class SwitchLOD(bpy.types.Operator):
    bl_idname = "mesh.switchlod"
    bl_label = "Swap LOD"
    bl_description = "Show one LOD collection at a time and flip between the selected pair"
    bl_options = {'REGISTER', 'UNDO'}

    def swap_lod(self, lod_sel, lod_next):
        collections = bpy.data.collections
        if lod_sel not in collections or lod_next not in collections:
            print('Missing collection')
            return

        selected_hidden = collections[lod_sel].hide_viewport
        collections[lod_sel].hide_viewport = not selected_hidden
        collections[lod_next].hide_viewport = selected_hidden

    def execute(self, context):
        primary, secondary = LOD_SWAP_PAIRS[context.scene.lod_holder.lod_list]

        # Everything outside the pair gets hidden first.
        for name in LOD_COLLECTIONS:
            if name in (primary, secondary):
                continue
            collection = bpy.data.collections.get(name)
            if collection is not None:
                collection.hide_viewport = True

        self.swap_lod(primary, secondary)
        return {'FINISHED'}


class EnableLOD(bpy.types.Operator):
    bl_idname = "mesh.enablelod"
    bl_label = "Enable All LOD Viewport"
    bl_description = "Un-hide every LOD collection in the viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for name in LOD_COLLECTIONS:
            collection = bpy.data.collections.get(name)
            if collection is not None:
                collection.hide_viewport = False
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Tire deform operators
# ---------------------------------------------------------------------------

class CreateTireDeform(bpy.types.Operator):
    bl_idname = "mesh.createtiredeform"
    bl_label = "Create Tire Deform Objects"
    bl_description = "Link the tire deformation rig in and bind it to the four tires"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return None not in (scene.tire_RF, scene.tire_RR, scene.tire_LF, scene.tire_LR)

    def execute(self, context):
        scene = context.scene
        tires = [scene.tire_RF, scene.tire_RR, scene.tire_LF, scene.tire_LR]

        for tire in tires:
            tire.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=True)

        if scene.frame_end != 65:
            scene.frame_start = 1
            scene.frame_end = 65

        if tire_deform_collection() is not None:
            show_message_box(
                ["Tire Deformation Exist, please cleanup first"],
                "Tire Deform Generate", "ERROR",
            )
            return {'FINISHED'}

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

        check_and_unlink_objects(tires)
        for tire in tires:
            clear_old_armature_modifiers(tire)

        with bpy.data.libraries.load(TIRE_RIG_BLEND_PATH) as (data_from, data_to):
            data_to.collections.append("Tire Deformations")
        context.scene.collection.children.link(bpy.data.collections["Tire Deformations"])

        for corner in TIRE_CORNERS:
            addmodifier_linktire_deform(corner, tires)
        for corner in TIRE_CORNERS:
            position_tire_deform(corner, tires)

        # Bake the offsets that snapping introduced back into the meshes.
        for tire in tires:
            tire.select_set(True)
            bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

        return {'FINISHED'}


class ApplyTireWeight(bpy.types.Operator):
    bl_idname = "mesh.applytireweight"
    bl_label = "Transfer Weight"
    bl_description = "Transfer the deform rig's vertex weights onto the tire meshes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if tire_deform_collection() is None:
            return False
        rig_names = {f"tire_deformation_rig {corner}" for corner in TIRE_CORNERS}
        found = {obj.name for obj in context.scene.objects} & rig_names
        return len(found) == len(rig_names)

    def execute(self, context):
        scene = context.scene
        tires = [scene.tire_RF, scene.tire_RR, scene.tire_LF, scene.tire_LR]

        for tire in tires:
            tire.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=True)

        for corner in TIRE_CORNERS:
            transfer_tire_weight(corner, tires)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Scene setup / vertex AO operators
# ---------------------------------------------------------------------------

class S4SetupRenderScene(bpy.types.Operator):
    bl_idname = "s4veh.setupscene"
    bl_label = "Setup Render Scene"
    bl_description = "Apply the standard S4 EEVEE render settings to this scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.render.engine = 'BLENDER_EEVEE'
        eevee = scene.eevee
        eevee.taa_render_samples = 128

        # Ambient Occlusion
        eevee.use_gtao = True
        eevee.gtao_distance = 200.0
        eevee.gtao_factor = 1
        eevee.gtao_quality = 0.25
        eevee.use_gtao_bent_normals = True
        eevee.use_gtao_bounce = True

        # Screen Space Reflections
        eevee.use_ssr = True
        eevee.use_ssr_halfres = False
        eevee.use_ssr_refraction = True
        eevee.ssr_quality = 1
        eevee.ssr_max_roughness = 0.758
        eevee.ssr_thickness = 10
        eevee.ssr_border_fade = 0.079
        eevee.ssr_firefly_fac = 0

        # Color Management
        scene.view_settings.view_transform = 'Filmic'
        return {'FINISHED'}


class BakeVertexAO(bpy.types.Operator):
    bl_idname = "mesh.bakevertexao"
    bl_label = "Bake Vertex AO"
    bl_description = "Switch the scene to a raw Cycles AO bake and start baking to vertex colours"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def assign_ambient_node(self, obj):
        """Wire an Ambient Occlusion node straight into each Material Output."""
        for material in obj.data.materials:
            if material is None:
                continue
            material.use_nodes = True
            nodes = material.node_tree.nodes

            output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
            if output is None:
                output = nodes.new("ShaderNodeOutputMaterial")

            ao_node = next((n for n in nodes if n.type == 'AMBIENT_OCCLUSION'), None)
            if ao_node is None:
                ao_node = nodes.new('ShaderNodeAmbientOcclusion')
                ao_node.location = (300, 600)
                ao_node.inputs[1].default_value = 1000

            material.node_tree.links.new(ao_node.outputs[0], output.inputs[0])

    def execute(self, context):
        scene = context.scene

        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.cycles.bake_type = 'COMBINED'
        scene.render.bake.target = 'VERTEX_COLORS'
        scene.cycles.adaptive_threshold = 0.001
        scene.cycles.samples = 4096
        scene.cycles.adaptive_min_samples = 1024
        scene.cycles.time_limit = 0

        # Bake the raw AO signal, no view transform baked into the colours.
        scene.display_settings.display_device = 'sRGB'
        scene.view_settings.view_transform = 'Raw'
        scene.view_settings.look = 'None'
        scene.view_settings.exposure = 0
        scene.view_settings.gamma = 1
        scene.sequencer_colorspace_settings.name = 'Linear'

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            obj.hide_render = False
            self.assign_ambient_node(obj)

        for space in iter_view3d_spaces():
            space.shading.type = 'SOLID'
            space.shading.light = 'FLAT'
            space.shading.color_type = 'VERTEX'

        bpy.ops.object.bake('INVOKE_DEFAULT', type='COMBINED')
        return {'FINISHED'}


class ExitVertexAO(bpy.types.Operator):
    bl_idname = "mesh.exitbakevertexao"
    bl_label = "Exit Vertex AO Mode"
    bl_description = "Restore EEVEE and reconnect each material's shader to its output"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.render.engine = 'BLENDER_EEVEE'
        context.scene.view_settings.view_transform = 'Filmic'

        for material in bpy.data.materials:
            material.use_nodes = True
            surface = None
            shader = None

            for node in material.node_tree.nodes:
                if node.bl_idname == 'ShaderNodeOutputMaterial':
                    surface = node.inputs['Surface']
                elif node.bl_idname == 'ShaderNodeGroup':
                    if node.node_tree is not None and node.node_tree.name in S4_SHADER_GROUPS:
                        shader = node.outputs['BSDF']
                elif node.bl_idname == 'ShaderNodeBsdfPrincipled':
                    shader = node.outputs['BSDF']

            if surface is not None and shader is not None:
                material.node_tree.links.new(shader, surface)

        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Material / shape key utility operators
# ---------------------------------------------------------------------------

class S4CorrectMat(bpy.types.Operator):
    bl_idname = "s4veh.correctmat"
    bl_label = "Correct Duplicate Material"
    bl_description = "Repoint every '.001' style duplicate material slot back at the base material"
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def remove_suffix(name):
        """Strip a numerical suffix like '.001' from a material name."""
        if len(name) > 4 and name[-4] == '.' and name[-3:].isdigit():
            return name[:-4]
        return name

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                if slot.material is None:
                    continue
                original_name = slot.material.name
                base_material = bpy.data.materials.get(self.remove_suffix(original_name))
                if base_material is not None and base_material is not slot.material:
                    slot.material = base_material
                    print(f"Replaced {original_name} with {base_material.name} on {obj.name}")
        return {'FINISHED'}


class S4RemoveShapekey(bpy.types.Operator):
    bl_idname = "s4veh.removeshapekey"
    bl_label = "Remove Shapekey Selected Object"
    bl_description = "Remove every shape key from the selected meshes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue
            shape_keys = obj.data.shape_keys
            if not shape_keys:
                continue
            # Removing from the end keeps the remaining indices valid.
            for index in reversed(range(len(shape_keys.key_blocks))):
                obj.shape_key_remove(shape_keys.key_blocks[index])
        return {'FINISHED'}


class S4ApplyLattice(bpy.types.Operator):
    bl_idname = "s4veh.applylattice"
    bl_label = "Apply Lattice as Shapekey Selected Object"
    bl_description = "Apply every modifier on the selected objects as a shape key"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        for obj in context.selected_objects:
            context.view_layer.objects.active = obj
            for name in [modifier.name for modifier in obj.modifiers]:
                bpy.ops.object.modifier_apply_as_shapekey(modifier=name, keep_modifier=False)
        return {'FINISHED'}


class S4VehKeyShapekey(bpy.types.Operator):
    bl_idname = "s4veh.keyshapekey"
    bl_label = "Keyframe for Shapekey"
    bl_description = "Key every shape key that sits at 0 on frame 1 and every one at 1 on frame 100"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def add_all_keyframe(self, obj):
        if obj.type != 'MESH' or not obj.data.shape_keys:
            return
        for key in obj.data.shape_keys.key_blocks:
            if key.value == 0.00:
                key.keyframe_insert("value", frame=1)
            elif key.value == 1.00:
                key.keyframe_insert("value", frame=100)

    def execute(self, context):
        for obj in context.selected_objects:
            self.add_all_keyframe(obj)
        context.scene.frame_set(context.scene.frame_current)
        return {'FINISHED'}


class S4VehLodRig(bpy.types.Operator):
    bl_idname = "s4veh.riglod"
    bl_label = "LOD Rigging"
    bl_description = "Build the export armature and place a bone on each wheel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return None not in (
            scene.s4veh_wheel_lf, scene.s4veh_wheel_lr,
            scene.s4veh_wheel_rf, scene.s4veh_wheel_rr,
            scene.s4veh_body_base, scene.s4veh_steeringwheel,
        )

    def add_child_bone(self, bone_name, parent_bone, wheel_mesh, armature_object):
        new_bone = armature_object.data.edit_bones.new(bone_name)
        new_bone.head = (0, 0, 0)
        new_bone.tail = (0, 40, 0)
        new_bone.parent = parent_bone
        new_bone.matrix = wheel_mesh.matrix_world
        return new_bone

    def execute(self, context):
        scene = context.scene
        wheel_LF = scene.s4veh_wheel_lf
        wheel_LR = scene.s4veh_wheel_lr
        wheel_RF = scene.s4veh_wheel_rf
        wheel_RR = scene.s4veh_wheel_rr
        steeringwheel = scene.s4veh_steeringwheel
        body_base = scene.s4veh_body_base

        for wheel in (wheel_LF, wheel_LR, wheel_RF, wheel_RR):
            wheel.select_set(True)
        steeringwheel.select_set(False)

        bpy.ops.object.mode_set(mode='OBJECT', toggle=True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        armature = bpy.data.armatures.new('Armature')
        armature.name = ARMATURE_NAME
        armature_object = bpy.data.objects.new('Armature', armature)
        context.collection.objects.link(armature_object)

        context.view_layer.objects.active = armature_object
        armature_object.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        armature_object.show_in_front = True
        armature_object.data.show_axes = True

        root_bone = armature_object.data.edit_bones.new('Root')
        root_bone.head = (0, 0, 0)
        root_bone.tail = (0, 40, 0)
        root_bone.matrix = body_base.matrix_world

        for bone_name, wheel in (
            ('PhysWheel_LF', wheel_LF), ('PhysWheel_LR', wheel_LR),
            ('PhysWheel_RF', wheel_RF), ('PhysWheel_RR', wheel_RR),
            ('FixedWheel_LF', wheel_LF), ('FixedWheel_LR', wheel_LR),
            ('FixedWheel_RF', wheel_RF), ('FixedWheel_RR', wheel_RR),
            ('SteeringWheel', steeringwheel),
        ):
            self.add_child_bone(bone_name, root_bone, wheel, armature_object)

        bpy.ops.object.mode_set(mode='OBJECT', toggle=True)
        bpy.ops.object.select_all(action='DESELECT')
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = [
    S4VehCheckResult,
    SwitchLODValue,
    S4VEH_UL_check_results,
    CUSTOM_OT_clearList,
    ValidationToolMainPanel,
    ShaderToolPanel,
    UtilitiesToolPanel,
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
    CreateTireDeform,
    S4SetupRenderScene,
    ApplyTireWeight,
    BakeVertexAO,
    ExitVertexAO,
    SwitchLOD,
    EnableLOD,
    SelectNgon,
    S4VehLodRig,
    S4CorrectMat,
    S4RemoveShapekey,
    S4ApplyLattice,
    S4VehKeyShapekey,
]


def scene_properties():
    """Every property this addon hangs off bpy.types.Scene.

    Built in one place so register and unregister can never drift apart.
    """
    def object_pointer(name, description):
        return PointerProperty(
            type=bpy.types.Object, poll=object_search_poll,
            name=name, description=description,
        )

    return {
        "custom": CollectionProperty(type=S4VehCheckResult),
        "custom_index": IntProperty(default=5),
        "checkResult_all": BoolProperty(
            name="Show check results", description="Result list is populated"),
        "wheel_speed": FloatProperty(
            name="Wheel Speed", description="Check wheel speed node",
            min=0.0, max=1.0, default=0.0, update=wheel_speed),
        "dirt_value": FloatProperty(
            name="Dirt Level", description="Adjust dirt value",
            min=0.0, max=1.0, default=0.0, update=dirt_value),
        "dust_value": FloatProperty(
            name="Dust Level", description="Adjust dust value",
            min=0.0, max=1.0, default=0.0, update=dust_value),
        "mud_value": FloatProperty(
            name="Mud Level", description="Adjust mud value",
            min=0.0, max=1.0, default=0.0, update=mud_value),
        "deform_value": FloatProperty(
            name="Deform Level", description="Adjust deformation value",
            min=0.0, max=1.0, default=0.0, update=deform_value),
        "lights_value": FloatProperty(
            name="Lights Intensity", description="Adjust lighting value",
            min=0.0, max=10.0, default=0.0, update=lights_value),
        "tire_RF": object_pointer("Tire RF", "Front Right Vehicle Tire Mesh"),
        "tire_RR": object_pointer("Tire RR", "Rear Right Vehicle Tire Mesh"),
        "tire_LF": object_pointer("Tire LF", "Front Left Vehicle Tire Mesh"),
        "tire_LR": object_pointer("Tire LR", "Rear Left Vehicle Tire Mesh"),
        "s4veh_wheel_lf": object_pointer("Pick Wheel LF", "Select LF Wheel"),
        "s4veh_wheel_lr": object_pointer("Pick Wheel LR", "Select LR Wheel"),
        "s4veh_wheel_rf": object_pointer("Pick Wheel RF", "Select RF Wheel"),
        "s4veh_wheel_rr": object_pointer("Pick Wheel RR", "Select RR Wheel"),
        "s4veh_steeringwheel": object_pointer("Pick SteeringWheel", "Select Steering Wheel"),
        "s4veh_body_base": object_pointer("Pick Body Part", "Select Body Base Mesh"),
        "lod_holder": PointerProperty(type=SwitchLODValue),
    }


# Names actually attached to bpy.types.Scene, so unregister only removes what
# register managed to add.
_registered_scene_props = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    for name, prop in scene_properties().items():
        setattr(bpy.types.Scene, name, prop)
        _registered_scene_props.append(name)


def unregister():
    while _registered_scene_props:
        name = _registered_scene_props.pop()
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
