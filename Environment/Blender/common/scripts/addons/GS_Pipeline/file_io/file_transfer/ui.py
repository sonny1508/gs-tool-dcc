"""GS File Transfer: the tab's properties, its buttons' operators, and drawing it."""
from __future__ import annotations

import math
import os

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import Operator

from ... import common
from .config import INDIVIDUAL_MODE, SERVER_DIR, server_stem, username
from .file_status import ServerFiles, local_row
from .server import ServerStatus
from .smoothing_groups import fbx_supports_smoothing_groups
from .transfer import individual_mode, local_location, run_export, run_import


# ---------------------------------------------------------------------------
# Person list (on the window manager, the search source for the User field)
# ---------------------------------------------------------------------------
class GS_PersonItem(bpy.types.PropertyGroup):
    name: StringProperty()


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------
# Local: one shared file on this machine, whichever application wrote it or reads
# it. The ids predate that (they used to take an application) and may be in keymaps.
class IMPORT_OT_from_application(Operator):
    bl_idname = "gs.import_from_application"
    bl_label = "Import"
    bl_description = "Import the last transfer exported on this machine, from any application"
    bl_options = {'UNDO'}

    def execute(self, context):
        directory, stem = local_location(context)
        return run_import(self, context, directory, stem)


class EXPORT_OT_to_application(Operator):
    bl_idname = "gs.export_to_application"
    bl_label = "Export"
    bl_description = "Export the selection for any application on this machine to import"
    bl_options = {'UNDO'}

    def execute(self, context):
        directory, stem = local_location(context)
        return run_export(self, context, directory, stem)


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
        other = context.scene.gs_file_transfer_props.server_user or "the selected user"
        return f"Import what {other} sent you"

    def execute(self, context):
        gs_props = context.scene.gs_file_transfer_props
        other = _server_user_or_report(self, gs_props)
        if not other:
            return {'CANCELLED'}
        # <sender>_to_<me>.fbx, sitting in the sender's folder
        result = run_import(self, context, os.path.join(SERVER_DIR, other), server_stem(other, username))
        ServerFiles.clear()
        return result


class EXPORT_OT_to_server(_NeedsServer, Operator):
    bl_idname = "gs.export_to_server"
    bl_label = "Export to Server"
    bl_description = "Send the selection to the selected user"
    bl_options = {'UNDO'}

    @classmethod
    def description(cls, context, properties):
        other = context.scene.gs_file_transfer_props.server_user or "the selected user"
        return f"Send the selection to {other}"

    def execute(self, context):
        gs_props = context.scene.gs_file_transfer_props
        other = _server_user_or_report(self, gs_props)
        if not other:
            return {'CANCELLED'}
        # <me>_to_<receiver>.fbx, sitting in my own folder
        result = run_export(self, context, os.path.join(SERVER_DIR, username), server_stem(username, other))
        ServerFiles.clear()
        return result


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
        description="For 3ds Max: turn your sharp edges into smoothing groups. In Max, tick "
                    "'Import Smoothing Groups'. Turn off when sending to Maya or Blender. "
                    "Needs Blender 4.5 or newer",
        default=True,
    )

    # --- Server ---
    # No application picker: transfer files are plain FBX, whatever DCC either side runs.
    server_user: StringProperty(
        name="User",
        description="The artist you are sending to or receiving from. Click and type to search",
        default="",
    )


class GS_OT_check_server(Operator):
    bl_idname = "gs.check_server"
    bl_label = "Check Server"
    bl_description = "Check the server connection and the files again, and reload the user list"

    def execute(self, context):
        ServerStatus.check()
        ServerFiles.clear()
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Draw (the panel calls it under File I/O > GS File Transfer)
# ---------------------------------------------------------------------------
def _draw_settings(layout, gs_props):
    box = layout.box()
    if INDIVIDUAL_MODE:     # shelved: see config.INDIVIDUAL_MODE
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
    row.operator(import_op, text="Import", icon='IMPORT')
    row.operator(export_op, text="Export", icon='EXPORT')


def _draw_file_row(layout, icon, name, when):
    """One file line: its name, and when it was written on the right."""
    row = layout.row()
    row.label(text=name, icon=icon)
    right = row.row()
    right.alignment = 'RIGHT'
    right.label(text=when)


def _draw_server_files(layout, context, gs_props, people):
    other = gs_props.server_user.strip()
    if not other or other not in people:
        layout.label(text="Pick a user to see the files", icon='INFO')
        return
    rows = ServerFiles.rows_for(other, individual_mode(context))
    if rows is None:
        layout.label(text="Checking the files...", icon='TIME')
        return
    received, sent = rows
    _draw_file_row(layout, 'IMPORT', *received)     # what they sent me
    _draw_file_row(layout, 'EXPORT', *sent)         # what I last sent them


def draw_file_transfer(layout, context):
    scene = context.scene
    gs_props = scene.gs_file_transfer_props

    _draw_settings(layout, gs_props)

    local = layout.box()
    local.label(text="Local", icon='HOME')
    _draw_file_row(local, 'FILE', *local_row(context))
    _draw_transfer_buttons(local, "gs.import_from_application", "gs.export_to_application")

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
    if online:
        _draw_server_files(body, context, gs_props, people)
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
