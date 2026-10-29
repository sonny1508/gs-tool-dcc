"""GS File Transfer: the tab's properties, its buttons' operators, and drawing it."""
from __future__ import annotations

import math
import os

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import Operator

from ... import common
from .config import APP_ITEMS, APP_LABELS, SERVER_DIR, THIS_APP, transfer_stem, username
from .server import ServerStatus
from .smoothing_groups import fbx_supports_smoothing_groups
from .transfer import local_dir, run_export, run_import


# ---------------------------------------------------------------------------
# Person list (on the window manager, the search source for the User field)
# ---------------------------------------------------------------------------
class GS_PersonItem(bpy.types.PropertyGroup):
    name: StringProperty()


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------
class IMPORT_OT_from_application(Operator):
    bl_idname = "gs.import_from_application"
    bl_label = "Import"
    bl_description = "Import what another application exported on this machine"
    bl_options = {'UNDO'}

    source_app: StringProperty(default="")

    @classmethod
    def description(cls, context, properties):
        label = APP_LABELS.get(properties.source_app, "another application")
        stem = transfer_stem(properties.source_app, THIS_APP)
        return f"Import what {label} last exported on this machine ({stem}.fbx)"

    def execute(self, context):
        if self.source_app not in APP_LABELS:
            self.report({'ERROR'}, "Invalid source application")
            return {'CANCELLED'}
        return run_import(self, context, local_dir(context), transfer_stem(self.source_app, THIS_APP))


class EXPORT_OT_to_application(Operator):
    bl_idname = "gs.export_to_application"
    bl_label = "Export"
    bl_description = "Export the selection for another application on this machine"
    bl_options = {'UNDO'}

    target_app: StringProperty(default="")

    @classmethod
    def description(cls, context, properties):
        label = APP_LABELS.get(properties.target_app, "another application")
        stem = transfer_stem(THIS_APP, properties.target_app)
        return f"Export the selection for {label} to import on this machine ({stem}.fbx)"

    def execute(self, context):
        if self.target_app not in APP_LABELS:
            self.report({'ERROR'}, "Invalid target application")
            return {'CANCELLED'}
        return run_export(self, context, local_dir(context),
                          transfer_stem(THIS_APP, self.target_app), self.target_app)


def _server_user_or_report(op, gs_props):
    other = gs_props.server_user.strip()
    if not other:
        op.report({'ERROR'}, "Pick a user first")
    return other


class _NeedsServer:
    """Mixin: the operator is unavailable until the share has been found reachable."""

    @classmethod
    def poll(cls, context):
        if ServerStatus.online:
            return True
        cls.poll_message_set("Still checking the server" if ServerStatus.online is None
                             else "Can't reach the server")
        return False


class IMPORT_OT_from_server(_NeedsServer, Operator):
    bl_idname = "gs.import_from_server"
    bl_label = "Import from Server"
    bl_description = "Import what the selected user sent you"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        gs_props = context.scene.gs_file_transfer_props
        other = gs_props.server_user or "the selected user"
        return f"Import what {other} sent you from {APP_LABELS[gs_props.server_app]}"

    def execute(self, context):
        gs_props = context.scene.gs_file_transfer_props
        other = _server_user_or_report(self, gs_props)
        if not other:
            return {'CANCELLED'}
        # <sender>_<app>_to_blender_<me>.fbx, sitting in the sender's folder
        stem = f"{other}_{transfer_stem(gs_props.server_app, THIS_APP)}_{username}"
        return run_import(self, context, os.path.join(SERVER_DIR, other), stem)


class EXPORT_OT_to_server(_NeedsServer, Operator):
    bl_idname = "gs.export_to_server"
    bl_label = "Export to Server"
    bl_description = "Send the selection to the selected user"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        gs_props = context.scene.gs_file_transfer_props
        other = gs_props.server_user or "the selected user"
        return f"Send the selection to {other}, to import in {APP_LABELS[gs_props.server_app]}"

    def execute(self, context):
        gs_props = context.scene.gs_file_transfer_props
        other = _server_user_or_report(self, gs_props)
        if not other:
            return {'CANCELLED'}
        target_app = gs_props.server_app
        # <me>_blender_to_<app>_<receiver>.fbx, sitting in my own folder
        stem = f"{username}_{transfer_stem(THIS_APP, target_app)}_{other}"
        return run_export(self, context, os.path.join(SERVER_DIR, username), stem, target_app)


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------
class GSFileTransferProperties(bpy.types.PropertyGroup):
    export_mode: EnumProperty(
        name="Mode",
        items=[
            ("MERGE", "Merge", "Transfer all selected objects as one FBX file"),
            ("INDIVIDUAL", "Individual", "Transfer each selected object as its own FBX file"),
        ],
        default="MERGE",
    )

    # --- Import ---
    clear_normals: BoolProperty(
        name="Clear Normal Data",
        description="Strip custom normals and sharp edges from imported meshes, "
                    "leaving plain smooth shading",
        default=False,
    )
    merge_materials: BoolProperty(
        name="Merge Materials",
        description="When the import duplicates a material because its name is taken "
                    "(Material.001, Material.002...), use the existing Material instead",
        default=True,
    )
    set_auto_smooth: BoolProperty(
        name="Set Auto Smooth",
        description="Run Blender's Shade Auto Smooth on imported meshes. "
                    "Off keeps the shading the FBX came with",
        default=False,
    )
    smooth_angle: FloatProperty(
        name="Angle",
        description="Maximum angle between face normals that will be considered as smooth",
        subtype='ANGLE',
        default=math.radians(30.0),
        min=0.0,
        max=math.pi,
    )

    # --- Export ---
    export_mesh_only: BoolProperty(
        name="Mesh Only",
        description="Export only the selected meshes, leaving out the empties (nulls) that "
                    "hold the hierarchy. Meshes keep their position in the world",
        default=False,
    )
    export_smooth_groups: BoolProperty(
        name="Export Smoothing Groups",
        description="When exporting to 3ds Max, turn your sharp edges into smoothing groups. "
                    "In Max, tick 'Import Smoothing Groups'. Needs Blender 4.5 or newer",
        default=True,
    )

    # --- Local / Server ---
    local_app: EnumProperty(
        name="Software",
        description="The application on this machine you are transferring with",
        items=APP_ITEMS,
        default="maya",
    )
    server_app: EnumProperty(
        name="Software",
        description="The application the other artist is using",
        items=APP_ITEMS,
        default="maya",
    )
    server_user: StringProperty(
        name="User",
        description="The artist you are sending to or receiving from. Click and type to search",
        default="",
    )


class GS_OT_check_server(Operator):
    bl_idname = "gs.check_server"
    bl_label = "Check Server"
    bl_description = "Check the server connection again and reload the user list"

    def execute(self, context):
        ServerStatus.check()
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Draw (the panel calls it under File I/O > GS File Transfer)
# ---------------------------------------------------------------------------
def _draw_settings(layout, gs_props):
    box = layout.box()
    mode_row = box.split(factor=0.3)
    mode_row.label(text="Mode")
    mode_row.row(align=True).prop(gs_props, "export_mode", expand=True)

    columns = box.split(factor=0.5)
    import_col = columns.column()
    import_col.label(text="Import", icon='IMPORT')
    import_col.prop(gs_props, "clear_normals")
    import_col.prop(gs_props, "merge_materials")
    import_col.prop(gs_props, "set_auto_smooth")
    angle_row = import_col.row()
    angle_row.enabled = gs_props.set_auto_smooth
    angle_row.prop(gs_props, "smooth_angle")

    export_col = columns.column()
    export_col.label(text="Export", icon='EXPORT')
    export_col.prop(gs_props, "export_mesh_only")
    smoothing = export_col.row()
    smoothing.enabled = fbx_supports_smoothing_groups()  # greyed out in Blender 3.6
    smoothing.prop(gs_props, "export_smooth_groups")


def _draw_transfer_buttons(layout, import_op, export_op):
    row = layout.row()
    row.scale_y = 1.3
    imp = row.operator(import_op, text="Import", icon='IMPORT')
    exp = row.operator(export_op, text="Export", icon='EXPORT')
    return imp, exp


def draw_file_transfer(layout, context):
    scene = context.scene
    gs_props = scene.gs_file_transfer_props

    _draw_settings(layout, gs_props)

    local = layout.box()
    local.label(text="Local", icon='HOME')
    local.prop(gs_props, "local_app")
    imp, exp = _draw_transfer_buttons(local, "gs.import_from_application", "gs.export_to_application")
    imp.source_app = gs_props.local_app
    exp.target_app = gs_props.local_app

    server = layout.box()
    header = server.row()
    header.label(text="Server", icon='WORLD')
    header.operator("gs.check_server", text="", icon='FILE_REFRESH', emboss=False)
    online = ServerStatus.online
    if online is None:
        server.label(text="Checking the server...", icon='TIME')
    elif not online:
        server.label(text="Can't reach the server", icon='ERROR')

    body = server.column()
    body.enabled = bool(online)
    people = context.window_manager.gs_person_list
    body.prop_search(gs_props, "server_user", context.window_manager, "gs_person_list", icon='USER')
    if online and len(people) == 0:
        body.label(text="User list unavailable", icon='ERROR')
    body.prop(gs_props, "server_app")
    _draw_transfer_buttons(body, "gs.import_from_server", "gs.export_to_server")

    layout.label(text="Current User: " + username)


# ---------------------------------------------------------------------------
# Registration (by file_transfer/__init__.py)
# ---------------------------------------------------------------------------
CLASSES = (
    GS_PersonItem,
    IMPORT_OT_from_application,
    EXPORT_OT_to_application,
    IMPORT_OT_from_server,
    EXPORT_OT_to_server,
    GS_OT_check_server,
    GSFileTransferProperties,
)


def register():
    common.register_classes(CLASSES)
    bpy.types.Scene.gs_file_transfer_props = PointerProperty(type=GSFileTransferProperties)
    # Runtime-only (window manager data isn't saved), shared by every scene.
    bpy.types.WindowManager.gs_person_list = CollectionProperty(type=GS_PersonItem)


def unregister():
    if hasattr(bpy.types.WindowManager, "gs_person_list"):
        del bpy.types.WindowManager.gs_person_list
    if hasattr(bpy.types.Scene, "gs_file_transfer_props"):
        del bpy.types.Scene.gs_file_transfer_props
    common.unregister_classes(CLASSES)
