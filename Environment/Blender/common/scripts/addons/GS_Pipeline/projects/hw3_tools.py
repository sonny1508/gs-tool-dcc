"""HW3 Tools project for the GS Pipeline addon (Blender port of HW3_Tools.py).

Two work areas, matching the Maya tabs:
  * Materials  - assign UE material-instance / texture data onto scene materials.
  * Modelling  - source-module FBX I/O and building-scene sync.
"""
from __future__ import annotations

import os
import shutil

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import Operator, Panel, PropertyGroup, UIList

from .. import common

# Property group lives on the scene under this attribute.
PROP = "gs_hw3"


# ============================================================================
# Data model (UI lists need real CollectionProperty items)
# ============================================================================
class GS_HW3_ListItem(PropertyGroup):
    name: StringProperty()
    path: StringProperty()


# Guards against the two index ``update`` callbacks ping-ponging into each other
# when one clears the other (single-selection between the two lists).
_SELECTING = [False]


def _on_mat_json_index(self, context):
    """Pull UV scale/offset defaults from the newly selected material JSON."""
    if _SELECTING[0]:
        return
    _SELECTING[0] = True
    try:
        if self.json_mats_index >= 0:
            self.textures_index = -1
        idx = self.json_mats_index
        if not (0 <= idx < len(self.json_mats)):
            return
        mats = common.load_json_materials()
        if not (0 <= idx < len(mats)):
            return
        uv = mats[idx].get("vectors", {}).get("UV - ScaleOffset") or {}
        self.uv_r = self.uv_default_r = uv.get("r", 1.0)
        self.uv_g = self.uv_default_g = uv.get("g", 1.0)
        self.uv_b = self.uv_default_b = uv.get("b", 0.0)
        self.uv_a = self.uv_default_a = uv.get("a", 0.0)
    finally:
        _SELECTING[0] = False


def _on_texture_index(self, context):
    if _SELECTING[0]:
        return
    _SELECTING[0] = True
    try:
        if self.textures_index >= 0:
            self.json_mats_index = -1
    finally:
        _SELECTING[0] = False


class GS_HW3_Props(PropertyGroup):
    # JSON material instances
    json_mats: CollectionProperty(type=GS_HW3_ListItem)
    json_mats_index: IntProperty(default=-1, update=_on_mat_json_index)
    # standalone textures
    textures: CollectionProperty(type=GS_HW3_ListItem)
    textures_index: IntProperty(default=-1, update=_on_texture_index)
    # source-module FBX files
    fbx_files: CollectionProperty(type=GS_HW3_ListItem)
    fbx_files_index: IntProperty(default=-1)

    # UV scale/offset fields (R,G,B,A) - same semantics as the Maya floatFields.
    uv_r: FloatProperty(name="R", default=1.0, precision=4, step=10)
    uv_g: FloatProperty(name="G", default=1.0, precision=4, step=10)
    uv_b: FloatProperty(name="B", default=0.0, precision=4, step=10)
    uv_a: FloatProperty(name="A", default=0.0, precision=4, step=10)

    # remembered defaults from the last selected material JSON (for Reset)
    uv_default_r: FloatProperty(default=1.0)
    uv_default_g: FloatProperty(default=1.0)
    uv_default_b: FloatProperty(default=0.0)
    uv_default_a: FloatProperty(default=0.0)


def _props(context) -> GS_HW3_Props:
    return getattr(context.scene, PROP)


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
    image_node.image = common.load_image(texture_path, is_data=False)
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
    image_node.image = common.load_image(texture_path, is_data=True)
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
def _fill_collection(coll, rows: list[dict]) -> None:
    coll.clear()
    for row in rows:
        item = coll.add()
        item.name = row.get("name", "???")
        item.path = row.get("path", "")


class GS_OT_HW3_RefreshMaterials(Operator):
    bl_idname = "gs_pipeline.hw3_refresh_materials"
    bl_label = "Refresh Materials"
    bl_description = "Reload material-instance JSON from the pipeline folder"

    def execute(self, context):
        props = _props(context)
        _fill_collection(props.json_mats, common.load_json_materials())
        props.json_mats_index = -1
        return {"FINISHED"}


class GS_OT_HW3_RefreshTextures(Operator):
    bl_idname = "gs_pipeline.hw3_refresh_textures"
    bl_label = "Refresh Textures"
    bl_description = "Reload standalone textures from the pipeline folder"

    def execute(self, context):
        props = _props(context)
        _fill_collection(props.textures, common.load_textures())
        props.textures_index = -1
        return {"FINISHED"}


class GS_OT_HW3_RefreshFBX(Operator):
    bl_idname = "gs_pipeline.hw3_refresh_fbx"
    bl_label = "Refresh FBX"
    bl_description = "Reload the source-module FBX list"

    def execute(self, context):
        props = _props(context)
        rows = [{"name": n, "path": p} for n, p in common.load_fbx_list().items()]
        _fill_collection(props.fbx_files, rows)
        props.fbx_files_index = -1
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
            mats = common.load_json_materials()
            if not (0 <= mat_idx < len(mats)):
                return {"CANCELLED"}
            bc_path, n_path = common.find_mat_textures(mats[mat_idx])
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
        if os.path.isdir(common.MAT_ROOT):
            _clear_folder(common.MAT_ROOT)
        bpy.ops.gs_pipeline.hw3_refresh_materials()
        return {"FINISHED"}


class GS_OT_HW3_ClearTextures(Operator):
    bl_idname = "gs_pipeline.hw3_clear_textures"
    bl_label = "Clear Textures"
    bl_description = "Delete all files in the textures folder"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        if os.path.isdir(common.TEX_ROOT):
            _clear_folder(common.TEX_ROOT)
        bpy.ops.gs_pipeline.hw3_refresh_textures()
        return {"FINISHED"}


class GS_OT_HW3_ClearFBX(Operator):
    bl_idname = "gs_pipeline.hw3_clear_fbx"
    bl_label = "Clear FBX"
    bl_description = "Delete the selected FBX, or all FBX files if none selected"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        props = _props(context)
        idx = props.fbx_files_index
        if 0 <= idx < len(props.fbx_files):
            path = props.fbx_files[idx].path
            try:
                if path and os.path.isfile(path):
                    os.remove(path)
            except OSError:
                pass
        elif os.path.isdir(common.MESH_ROOT):
            for entry in os.listdir(common.MESH_ROOT):
                full = os.path.join(common.MESH_ROOT, entry)
                if os.path.isfile(full):
                    try:
                        os.remove(full)
                    except OSError:
                        pass
        bpy.ops.gs_pipeline.hw3_refresh_fbx()
        return {"FINISHED"}


# ============================================================================
# Source-module I/O
# ============================================================================
class GS_OT_HW3_ExportSourceModules(Operator):
    bl_idname = "gs_pipeline.hw3_export_source_modules"
    bl_label = "Export Source Modules"
    bl_description = "Export each selected object to its own FBX in the mesh folder"

    def execute(self, context):
        selected = [o for o in context.selected_objects if o.type in {"MESH", "EMPTY"}]
        if not selected:
            self.report({"WARNING"}, "GS Pipeline: select at least one object to export.")
            return {"CANCELLED"}
        os.makedirs(common.MESH_ROOT, exist_ok=True)
        exported = 0
        active = context.view_layer.objects.active
        for obj in selected:
            fbx_path = os.path.join(common.MESH_ROOT, obj.name + ".fbx")
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
            try:
                common.export_selected_fbx(fbx_path)
                exported += 1
            except Exception as exc:
                self.report({"WARNING"}, f"GS Pipeline: failed to export {obj.name}: {exc}")
        # Restore selection.
        bpy.ops.object.select_all(action="DESELECT")
        for obj in selected:
            obj.select_set(True)
        if active:
            context.view_layer.objects.active = active
        bpy.ops.gs_pipeline.hw3_refresh_fbx()
        if exported:
            self.report({"INFO"}, f"Exported {exported} object(s)")
        return {"FINISHED"}


class GS_OT_HW3_ImportSourceModules(Operator):
    bl_idname = "gs_pipeline.hw3_import_source_modules"
    bl_label = "Import Source Modules"
    bl_description = "Import the selected source-module FBX file"

    def execute(self, context):
        props = _props(context)
        idx = props.fbx_files_index
        if not (0 <= idx < len(props.fbx_files)):
            self.report({"WARNING"}, "GS Pipeline: select an FBX file to import.")
            return {"CANCELLED"}
        path = props.fbx_files[idx].path
        if not path or not os.path.isfile(path):
            self.report({"WARNING"}, "GS Pipeline: FBX file not found.")
            return {"CANCELLED"}
        if common.import_fbx_with_material_reuse(path) is None:
            self.report({"WARNING"}, "GS Pipeline: import failed.")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Imported {props.fbx_files[idx].name}")
        return {"FINISHED"}


# ============================================================================
# File I/O (building scene sync, temp import/export)
# ============================================================================
class GS_OT_HW3_SyncBuildingScene(Operator):
    bl_idname = "gs_pipeline.hw3_sync_building_scene"
    bl_label = "Sync Building Scene"
    bl_description = "Import temp_building_scene.fbx, reuse materials, and group by collection"

    def execute(self, context):
        fbx_path = os.path.join(common.IO_ROOT, "temp_building_scene.fbx")
        new_objects = common.import_fbx_with_material_reuse(fbx_path)
        if new_objects is None:
            self.report({"WARNING"}, "GS Pipeline: building scene not found.")
            return {"CANCELLED"}
        common.group_imported_by_collection(new_objects)
        self.report({"INFO"}, "Building scene synced")
        return {"FINISHED"}


class GS_OT_HW3_ImportTemp(Operator):
    bl_idname = "gs_pipeline.hw3_import_temp"
    bl_label = "Import"
    bl_description = "Import temp.fbx from the I/O folder with material reuse"

    def execute(self, context):
        fbx_path = os.path.join(common.IO_ROOT, "temp.fbx")
        if common.import_fbx_with_material_reuse(fbx_path) is None:
            self.report({"WARNING"}, "GS Pipeline: temp.fbx not found.")
            return {"CANCELLED"}
        self.report({"INFO"}, "Imported")
        return {"FINISHED"}


class GS_OT_HW3_ExportSelected(Operator):
    bl_idname = "gs_pipeline.hw3_export_selected"
    bl_label = "Export Selected"
    bl_description = "Export the current selection to temp.fbx in the I/O folder"

    def execute(self, context):
        selected = [o for o in context.selected_objects if o.type in {"MESH", "EMPTY"}]
        if not selected:
            self.report({"WARNING"}, "GS Pipeline: select at least one object to export.")
            return {"CANCELLED"}
        export_path = os.path.join(common.IO_ROOT, "temp.fbx")
        try:
            common.export_selected_fbx(export_path)
            self.report({"INFO"}, "Exported selected")
        except Exception as exc:
            self.report({"WARNING"}, f"GS Pipeline: export failed: {exc}")
            return {"CANCELLED"}
        return {"FINISHED"}


# ============================================================================
# UI Lists
# ============================================================================
class GS_UL_HW3_Simple(UIList):
    """Generic single-column name list."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_prop, index):
        layout.label(text=item.name)


# ============================================================================
# Panels (drawn under the active project tab by projects/__init__.py)
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


def draw_modelling(layout, context):
    props = _props(context)

    box = layout.box()
    box.label(text="Source Modules I/O", icon="MESH_CUBE")
    header = box.row(align=True)
    header.label(text="FBX Mesh:")
    header.operator("gs_pipeline.hw3_refresh_fbx", text="Refresh")
    header.operator("gs_pipeline.hw3_clear_fbx", text="Clear")
    box.template_list(
        "GS_UL_HW3_Simple", "fbx_files", props, "fbx_files", props, "fbx_files_index", rows=5
    )
    row = box.row(align=True)
    row.operator("gs_pipeline.hw3_export_source_modules", text="Export Source Modules")
    row.operator("gs_pipeline.hw3_import_source_modules", text="Import Source Modules")

    layout.separator()

    box = layout.box()
    box.label(text="File I/O", icon="FILE")
    sync = box.row()
    sync.scale_y = 1.4
    sync.operator("gs_pipeline.hw3_sync_building_scene", text="Sync Building Scene", icon="SCENE_DATA")
    row = box.row(align=True)
    row.operator("gs_pipeline.hw3_import_temp", text="Import")
    row.operator("gs_pipeline.hw3_export_selected", text="Export Selected")


# ============================================================================
# Project descriptor (consumed by projects/__init__.py)
# ============================================================================
PROJECT = {
    "id": "HW3",
    "label": "HW3",
    "tabs": [
        {"label": "Materials", "draw": draw_materials},
        {"label": "Modelling", "draw": draw_modelling},
    ],
}

CLASSES = (
    GS_HW3_ListItem,
    GS_HW3_Props,
    GS_UL_HW3_Simple,
    GS_OT_HW3_RefreshMaterials,
    GS_OT_HW3_RefreshTextures,
    GS_OT_HW3_RefreshFBX,
    GS_OT_HW3_ResetUV,
    GS_OT_HW3_Assign,
    GS_OT_HW3_ClearMaterials,
    GS_OT_HW3_ClearTextures,
    GS_OT_HW3_ClearFBX,
    GS_OT_HW3_ExportSourceModules,
    GS_OT_HW3_ImportSourceModules,
    GS_OT_HW3_SyncBuildingScene,
    GS_OT_HW3_ImportTemp,
    GS_OT_HW3_ExportSelected,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    setattr(bpy.types.Scene, PROP, bpy.props.PointerProperty(type=GS_HW3_Props))


def unregister():
    if hasattr(bpy.types.Scene, PROP):
        delattr(bpy.types.Scene, PROP)
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
