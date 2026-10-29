"""HW3 Materials tab: put Unreal material-instance and texture data onto the
active material, as a Principled BSDF network matching the Maya tool's."""
from __future__ import annotations

import os
import shutil

import bpy
from bpy.types import Operator

from ... import common
from ...panel import Tab
from . import payloads
from .props import _fill_collection, _props


# ============================================================================
# Material network construction (Principled BSDF parity with the Maya network)
# ============================================================================
def _ensure_material_nodes(mat) -> tuple:
    """Return (node_tree, principled) for a material, enabling nodes if needed."""
    if not mat.use_nodes:
        mat.use_nodes = True
    nt = mat.node_tree
    principled = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if principled is None:
        principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
        output = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if output is None:
            output = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return nt, principled


def _find_input_source_node(socket):
    """Return the node feeding ``socket`` (first link), or None."""
    if socket.is_linked and socket.links:
        return socket.links[0].from_node
    return None


def _ensure_mapping(nt, image_node, tag: str):
    """Ensure a Mapping + TexCoord pair drives ``image_node`` 's Vector input."""
    vec_in = image_node.inputs["Vector"]
    mapping = _find_input_source_node(vec_in)
    if mapping is None or mapping.type != "MAPPING":
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.name = f"{tag}_mapping"
        mapping.label = f"{tag} Mapping"
        nt.links.new(mapping.outputs["Vector"], vec_in)
    tex_coord = _find_input_source_node(mapping.inputs["Vector"])
    if tex_coord is None or tex_coord.type != "TEX_COORD":
        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])
    return mapping


def _apply_uv_values(mapping, r: float, g: float, b: float, a: float) -> None:
    """Replicate Maya's place2dTexture repeat/offset math on a Mapping node.

    Maya:  repeatU=r, repeatV=g, offsetU=b, offsetV=1-g-a
    Blender Mapping scale is the tiling; location is the offset.
    """
    mapping.inputs["Scale"].default_value[0] = r
    mapping.inputs["Scale"].default_value[1] = g
    mapping.inputs["Location"].default_value[0] = b
    mapping.inputs["Location"].default_value[1] = 1.0 - g - a


def _ensure_color_texture(nt, principled, texture_path: str):
    base_in = principled.inputs["Base Color"]
    image_node = _find_input_source_node(base_in)
    if image_node is None or image_node.type != "TEX_IMAGE":
        image_node = nt.nodes.new("ShaderNodeTexImage")
        nt.links.new(image_node.outputs["Color"], base_in)
    image_node.image = payloads.load_image(texture_path, is_data=False)
    mapping = _ensure_mapping(nt, image_node, "BC")
    return image_node, mapping


def _ensure_normal_texture(nt, principled, texture_path: str):
    normal_in = principled.inputs["Normal"]
    normal_map = _find_input_source_node(normal_in)
    if normal_map is None or normal_map.type != "NORMAL_MAP":
        normal_map = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(normal_map.outputs["Normal"], normal_in)
    image_node = _find_input_source_node(normal_map.inputs["Color"])
    if image_node is None or image_node.type != "TEX_IMAGE":
        image_node = nt.nodes.new("ShaderNodeTexImage")
        nt.links.new(image_node.outputs["Color"], normal_map.inputs["Color"])
    image_node.image = payloads.load_image(texture_path, is_data=True)
    mapping = _ensure_mapping(nt, image_node, "N")
    return image_node, mapping


def _assign_material_network(mat, bc_path, n_path, r, g, b, a) -> None:
    nt, principled = _ensure_material_nodes(mat)
    if bc_path:
        _, bc_map = _ensure_color_texture(nt, principled, bc_path)
        _apply_uv_values(bc_map, r, g, b, a)
    if n_path:
        _, n_map = _ensure_normal_texture(nt, principled, n_path)
        _apply_uv_values(n_map, r, g, b, a)


def _find_base_color_image(mat):
    if not mat.use_nodes or mat.node_tree is None:
        return None
    principled = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if principled is None:
        return None
    node = _find_input_source_node(principled.inputs["Base Color"])
    if node is not None and node.type == "TEX_IMAGE":
        return node
    return None


# ============================================================================
# Selection helpers (Blender equivalent of the Maya selection queries)
# ============================================================================
def _active_material(context):
    """Active material slot of the active mesh object, or None."""
    obj = context.active_object
    if obj is None or obj.type != "MESH":
        return None
    return obj.active_material


def _is_update_mode(context) -> bool:
    """True when the picked texture already drives the active material's base color."""
    props = _props(context)
    idx = props.textures_index
    if not (0 <= idx < len(props.textures)):
        return False
    path = props.textures[idx].path
    mat = _active_material(context)
    if not path or mat is None:
        return False
    image_node = _find_base_color_image(mat)
    if image_node is None or image_node.image is None:
        return False
    existing = (bpy.path.abspath(image_node.image.filepath) or "").replace("\\", "/")
    return os.path.normpath(existing).lower() == os.path.normpath(path).lower()


# ============================================================================
# Refresh operators
# ============================================================================


class GS_OT_HW3_RefreshMaterials(Operator):
    bl_idname = "gs_pipeline.hw3_refresh_materials"
    bl_label = "Refresh Materials"
    bl_description = "Reload material-instance JSON from the pipeline folder"

    def execute(self, context):
        props = _props(context)
        _fill_collection(props.json_mats, payloads.list_json_materials())
        props.json_mats_index = -1
        return {"FINISHED"}


class GS_OT_HW3_RefreshTextures(Operator):
    bl_idname = "gs_pipeline.hw3_refresh_textures"
    bl_label = "Refresh Textures"
    bl_description = "Reload standalone textures from the pipeline folder"

    def execute(self, context):
        props = _props(context)
        _fill_collection(props.textures, payloads.load_textures())
        props.textures_index = -1
        return {"FINISHED"}


# ============================================================================
# Material-JSON / texture selection side effects
# ============================================================================
class GS_OT_HW3_ResetUV(Operator):
    bl_idname = "gs_pipeline.hw3_reset_uv"
    bl_label = "Reset"
    bl_description = "Reset UV scale/offset to the selected material's defaults"

    def execute(self, context):
        props = _props(context)
        props.uv_r = props.uv_default_r
        props.uv_g = props.uv_default_g
        props.uv_b = props.uv_default_b
        props.uv_a = props.uv_default_a
        return {"FINISHED"}


# ============================================================================
# Assign
# ============================================================================
class GS_OT_HW3_Assign(Operator):
    bl_idname = "gs_pipeline.hw3_assign"
    bl_label = "Assign"
    bl_description = "Assign the selected material JSON or texture to the active material"

    def execute(self, context):
        props = _props(context)
        mat = _active_material(context)
        if mat is None:
            self.report({"WARNING"}, "GS Pipeline: select a mesh with an active material.")
            return {"CANCELLED"}

        r, g, b, a = props.uv_r, props.uv_g, props.uv_b, props.uv_a
        mat_idx = props.json_mats_index
        tex_idx = props.textures_index

        # Material JSON takes priority (mirrors the Maya branch order).
        if 0 <= mat_idx < len(props.json_mats):
            data = payloads.load_json_material(props.json_mats[mat_idx].path)
            if data is None:
                self.report({"WARNING"}, "GS Pipeline: material JSON not found. Refresh the list.")
                return {"CANCELLED"}
            bc_path, n_path = payloads.find_mat_textures(data)
            if not bc_path and not n_path:
                self.report({"WARNING"}, "GS Pipeline: no textures found in material JSON.")
                return {"CANCELLED"}
            _assign_material_network(mat, bc_path, n_path, r, g, b, a)
            self.report({"INFO"}, f"Material assigned to {mat.name}")
            return {"FINISHED"}

        if 0 <= tex_idx < len(props.textures):
            path = props.textures[tex_idx].path
            if not path or not os.path.isfile(path):
                self.report({"WARNING"}, "GS Pipeline: texture file not found.")
                return {"CANCELLED"}
            _assign_material_network(mat, path, None, r, g, b, a)
            verb = "updated" if _is_update_mode(context) else "assigned"
            self.report({"INFO"}, f"Texture {verb} on {mat.name}")
            return {"FINISHED"}

        self.report({"WARNING"}, "GS Pipeline: select a Material or Texture first.")
        return {"CANCELLED"}


# ============================================================================
# Clear folder operators
# ============================================================================
def _clear_folder(root: str) -> None:
    for entry in os.listdir(root):
        full = os.path.join(root, entry)
        try:
            if os.path.isfile(full) or os.path.islink(full):
                os.remove(full)
            elif os.path.isdir(full):
                shutil.rmtree(full)
        except OSError:
            pass


class GS_OT_HW3_ClearMaterials(Operator):
    bl_idname = "gs_pipeline.hw3_clear_materials"
    bl_label = "Clear Materials"
    bl_description = "Delete all files in the material-instance folder"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        if os.path.isdir(payloads.MAT_ROOT):
            _clear_folder(payloads.MAT_ROOT)
        bpy.ops.gs_pipeline.hw3_refresh_materials()
        return {"FINISHED"}


class GS_OT_HW3_ClearTextures(Operator):
    bl_idname = "gs_pipeline.hw3_clear_textures"
    bl_label = "Clear Textures"
    bl_description = "Delete all files in the textures folder"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        if os.path.isdir(payloads.TEX_ROOT):
            _clear_folder(payloads.TEX_ROOT)
        bpy.ops.gs_pipeline.hw3_refresh_textures()
        return {"FINISHED"}


# ============================================================================
# Draw (the panel calls it under Projects > HW3 > Materials)
# ============================================================================
def draw_materials(layout, context):
    props = _props(context)

    # --- Material instances ---
    header = layout.row(align=True)
    header.label(text="Material:", icon="MATERIAL")
    header.operator("gs_pipeline.hw3_refresh_materials", text="Refresh")
    op = header.operator("gs_pipeline.hw3_clear_materials", text="Clear")
    layout.template_list(
        "GS_UL_HW3_Simple", "json_mats", props, "json_mats", props, "json_mats_index", rows=4
    )

    # --- UV scale/offset ---
    uv_header = layout.row(align=True)
    uv_header.label(text="UV - Scale/Offset")
    uv_header.operator("gs_pipeline.hw3_reset_uv", text="Reset")
    col = layout.column(align=True)
    col.prop(props, "uv_r")
    col.prop(props, "uv_g")
    col.prop(props, "uv_b")
    col.prop(props, "uv_a")

    layout.separator()

    # --- Textures ---
    tex_header = layout.row(align=True)
    tex_header.label(text="Textures:", icon="TEXTURE")
    tex_header.operator("gs_pipeline.hw3_refresh_textures", text="Refresh")
    tex_header.operator("gs_pipeline.hw3_clear_textures", text="Clear")
    layout.template_list(
        "GS_UL_HW3_Simple", "textures", props, "textures", props, "textures_index", rows=4
    )

    # --- Active material readout + Assign ---
    mat = _active_material(context)
    info = layout.row()
    info.label(text=f"Active Material: {mat.name if mat else '(none)'}")

    assign = layout.row()
    assign.scale_y = 1.5
    label = "Update" if _is_update_mode(context) else "Assign"
    assign.operator("gs_pipeline.hw3_assign", text=label, icon="CHECKMARK")


TAB = Tab("Materials", draw_materials)

CLASSES = (
    GS_OT_HW3_RefreshMaterials,
    GS_OT_HW3_RefreshTextures,
    GS_OT_HW3_ResetUV,
    GS_OT_HW3_Assign,
    GS_OT_HW3_ClearMaterials,
    GS_OT_HW3_ClearTextures,
)


def register():
    common.register_classes(CLASSES)


def unregister():
    common.unregister_classes(CLASSES)
