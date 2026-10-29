"""HW3 Modeling tab: source-module FBX in and out, and the building-scene sync."""
from __future__ import annotations

import os

import bpy
from bpy.types import Operator

from ... import common
from ...panel import Tab
from . import payloads
from .props import _fill_collection, _props


class GS_OT_HW3_RefreshFBX(Operator):
    bl_idname = "gs_pipeline.hw3_refresh_fbx"
    bl_label = "Refresh FBX"
    bl_description = "Reload the source-module FBX list"

    def execute(self, context):
        props = _props(context)
        rows = [{"name": n, "path": p} for n, p in payloads.load_fbx_list().items()]
        _fill_collection(props.fbx_files, rows)
        props.fbx_files_index = -1
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
        elif os.path.isdir(payloads.MESH_ROOT):
            for entry in os.listdir(payloads.MESH_ROOT):
                full = os.path.join(payloads.MESH_ROOT, entry)
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
        os.makedirs(payloads.MESH_ROOT, exist_ok=True)
        exported = 0
        active = context.view_layer.objects.active
        for obj in selected:
            fbx_path = os.path.join(payloads.MESH_ROOT, obj.name + ".fbx")
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
            try:
                payloads.export_selected_fbx(fbx_path)
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
        if payloads.import_fbx_with_material_reuse(path) is None:
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
        fbx_path = os.path.join(payloads.IO_ROOT, "temp_building_scene.fbx")
        new_objects = payloads.import_fbx_with_material_reuse(fbx_path)
        if new_objects is None:
            self.report({"WARNING"}, "GS Pipeline: building scene not found.")
            return {"CANCELLED"}
        payloads.group_imported_by_collection(new_objects)
        self.report({"INFO"}, "Building scene synced")
        return {"FINISHED"}


class GS_OT_HW3_ImportTemp(Operator):
    bl_idname = "gs_pipeline.hw3_import_temp"
    bl_label = "Import"
    bl_description = "Import temp.fbx from the I/O folder with material reuse"

    def execute(self, context):
        fbx_path = os.path.join(payloads.IO_ROOT, "temp.fbx")
        if payloads.import_fbx_with_material_reuse(fbx_path) is None:
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
        export_path = os.path.join(payloads.IO_ROOT, "temp.fbx")
        try:
            payloads.export_selected_fbx(export_path)
            self.report({"INFO"}, "Exported selected")
        except Exception as exc:
            self.report({"WARNING"}, f"GS Pipeline: export failed: {exc}")
            return {"CANCELLED"}
        return {"FINISHED"}


# ============================================================================
# Draw (the panel calls it under Projects > HW3 > Modeling)
# ============================================================================
def draw_modeling(layout, context):
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


TAB = Tab("Modeling", draw_modeling)

CLASSES = (
    GS_OT_HW3_RefreshFBX,
    GS_OT_HW3_ClearFBX,
    GS_OT_HW3_ExportSourceModules,
    GS_OT_HW3_ImportSourceModules,
    GS_OT_HW3_SyncBuildingScene,
    GS_OT_HW3_ImportTemp,
    GS_OT_HW3_ExportSelected,
)


def register():
    common.register_classes(CLASSES)


def unregister():
    common.unregister_classes(CLASSES)
