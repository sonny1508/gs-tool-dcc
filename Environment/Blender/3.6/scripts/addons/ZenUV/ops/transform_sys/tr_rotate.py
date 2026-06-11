# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright 2023, Valeriy Yatsenko

import bpy

from ZenUV.utils.generic import resort_by_type_mesh_in_edit_mode_and_sel
from .transform_utils.tr_utils import TransformSysOpsProps
from .transform_utils.tr_rotate_utils import TrRotateProps, RotateFactory, TrOrientProcessor
from ZenUV.ops.transform_sys.tr_labels import TrLabels


class ZuvTrRotateBase:
    bl_label = "Rotate"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Rotate selected Islands or Selection"

    influence_mode: TransformSysOpsProps.influence_mode
    op_order: TransformSysOpsProps.get_order_prop()
    rotation_mode: bpy.props.EnumProperty(
        name='Direction',
        description="Direction of rotation",
        items=[
            ("ANGLE", "By Angle", ""),
            ("DIRECTION", "By Direction", ""),
        ],
        default="DIRECTION"
    )

    # Operator Settings
    tr_rot_inc: bpy.props.IntProperty(
        name=TrLabels.PROP_ROTATE_INCREMENT_LABEL,
        description=TrLabels.PROP_ROTATE_INCREMENT_DESC,
        min=0,
        max=360,
        default=90
    )
    direction: bpy.props.EnumProperty(
        name='Direction',
        description="Direction of rotation",
        items=[
            ("CW", "Clockwise", ""),
            ("CCW", "Counter-clockwise", ""),
        ],
        default="CW"
    )
    tr_rot_inc_full_range: bpy.props.FloatProperty(
        name=TrLabels.PROP_ROTATE_ANGLE_LABEL,
        description=TrLabels.PROP_ROTATE_ANGLE_DESC,
        min=-360,
        max=360,
        default=90
    )
    op_island_pivot: TransformSysOpsProps.island_pivot

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "influence_mode")
        layout.prop(self, 'op_order')
        layout.prop(self, 'rotation_mode')
        layout.separator()
        box = layout.box()
        box.label(text='Settings:')
        if self.rotation_mode == 'DIRECTION':
            box.prop(self, 'direction')
            box.prop(self, 'tr_rot_inc')
        else:
            box.prop(self, 'tr_rot_inc_full_range')

        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "op_island_pivot")

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "There are no selected objects.")
            return {'CANCELLED'}

        RP = TrRotateProps(context, is_global=False)
        RP.op_tr_rotate_inc = self.tr_rot_inc
        RP.op_direction = self.direction
        RP.op_tr_rotate_angle = self.tr_rot_inc_full_range

        RF = RotateFactory(
            context,
            RP,
            self.influence_mode == 'ISLAND',
            objs,
            self.op_order,
            self.op_island_pivot,
            self.rotation_mode
        )
        RF.rotate()

        return {'FINISHED'}


class ZUV_OT_TrRotate(bpy.types.Operator, ZuvTrRotateBase):
    bl_idname = "uv.zenuv_rotate"


class ZUV_OT_TrRotate3DV(bpy.types.Operator, ZuvTrRotateBase):
    bl_idname = "view3d.zenuv_rotate"

    influence_mode: TransformSysOpsProps.influence_scene_mode


class ZUV_OT_TrOrient(bpy.types.Operator):

    bl_idname = "uv.zenuv_orient_island"
    bl_label = "Orient"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Orient Island"

    mode: bpy.props.EnumProperty(
        name='Orient by',
        description='Orient Mode',
        items=[
            ('BBOX', 'Bounding Box', 'Orient Island by bounding box'),
            ('BY_SELECTION', 'By Selection', 'Orient Island by selection')
        ],
        default='BBOX'
    )
    orient_direction: bpy.props.EnumProperty(
        name="Direction",
        description="",
        items=[
            ("HORIZONTAL", "Horizontal", "Horizontal orientation"),
            ("VERTICAL", "Vertical", "Vertical orientation"),
            ("AUTO", "Auto", "Auto detect orientation"),
        ],
        default="AUTO"
    )
    rotate_direction: bpy.props.EnumProperty(
        name='Rotation',
        description="Direction of rotation",
        items=[
            ("CW", "Clockwise", ""),
            ("CCW", "Counter-clockwise", ""),
        ],
        default="CW"
    )
    desc: bpy.props.StringProperty(name="Description", default="", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'mode')
        layout.prop(self, 'orient_direction')
        row = layout.row()
        row.enabled = self.orient_direction != 'AUTO'
        row.prop(self, 'rotate_direction')

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "There are no selected objects.")
            return {'CANCELLED'}

        TrOrientProcessor.orient(
            context,
            objs,
            self.mode,
            self.orient_direction,
            self.rotate_direction
            )

        return {'FINISHED'}


uv_tr_rotate_classes = (
    ZUV_OT_TrRotate,
    ZUV_OT_TrOrient,

    ZUV_OT_TrRotate3DV,
)


def register_tr_rotate():
    from bpy.utils import register_class
    for cl in uv_tr_rotate_classes:
        register_class(cl)


def unregister_tr_rotate():
    from bpy.utils import unregister_class
    for cl in uv_tr_rotate_classes:
        unregister_class(cl)
