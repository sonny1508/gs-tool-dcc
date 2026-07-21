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
import bmesh
from mathutils import Vector
from . transform_utils.tr_move_utils import TrMoveProps, MoveFactory
from ZenUV.utils.generic import resort_by_type_mesh_in_edit_mode_and_sel
from .transform_utils.tr_utils import TransformSysOpsProps
from ZenUV.ops.transform_sys.tr_labels import TrLabels
from ZenUV.utils.generic import get_mesh_data
from ZenUV.ops.transform_sys.transform_utils.transform_loops import TransformLoops
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.bounding_box import BoundingBox2d


class ZUV_OT_TrMove(bpy.types.Operator):
    bl_idname = "uv.zenuv_move"
    bl_label = "Move"
    bl_description = "Move selected Islands or Selection"
    bl_options = {'REGISTER', 'UNDO'}

    influence_mode: TransformSysOpsProps.influence_mode
    op_order: TransformSysOpsProps.get_order_prop()
    move_mode: bpy.props.EnumProperty(
        name='Move',
        description="Transform Mode",
        items=[
                ("INCREMENT", "By Increment", ""),
                ("TO_POSITION", "To Position", ""),
                ("TO_CURSOR", "To 2D Cursor", ""),
                ("TO_ACTIVE_TRIM", "To Active Trim Center", ""),
                ("TO_M_CURSOR", "To Mouse Cursor", "")
            ],
        default="INCREMENT"
    )

    # Operator Settings
    direction: TransformSysOpsProps.direction
    increment: bpy.props.FloatProperty(
        name=TrLabels.PROP_MOVE_INCREMENT_LABEL,
        default=1.0,
        min=0,
        step=0.1,
    )
    destination_pos: bpy.props.FloatVectorProperty(
        name="Position",
        size=2,
        default=(0.0, 0.0),
        subtype='COORDINATES',
    )
    mouse_pos: bpy.props.FloatVectorProperty(
        name="Mouse Position",
        size=2,
        default=(0.5, 0.5),
        subtype='XYZ',
        options={'HIDDEN'}
    )

    island_pivot: TransformSysOpsProps.island_pivot

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        self.mouse_pos = context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "influence_mode")
        layout.prop(self, "op_order")
        layout.prop(self, "move_mode")

        if self.move_mode not in {'TO_CURSOR', 'TO_M_CURSOR', "TO_ACTIVE_TRIM"}:
            layout.separator()
            box = layout.box()
            box.label(text='Settings:')

        if self.move_mode == 'TO_POSITION':
            box.prop(self, "destination_pos")
        elif self.move_mode == 'TO_CURSOR':
            pass
        elif self.move_mode == "INCREMENT":
            box.prop(self, 'direction')
            box.prop(self, "increment")

        if self.move_mode in {'TO_CURSOR', 'TO_POSITION', "TO_M_CURSOR", "TO_ACTIVE_TRIM"}:
            box = layout.box()
            box.label(text='Advanced:')
            box.prop(self, "island_pivot")

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "There are no selected objects.")
            return {'CANCELLED'}

        move_mode = self.move_mode

        if self.move_mode == 'TO_M_CURSOR':
            if context.area.type == 'IMAGE_EDITOR':
                destination_pos = self.mouse_pos
                move_mode = 'TO_POSITION'
            else:
                move_mode = 'HOLD'
                destination_pos = self.destination_pos
                self.report({'WARNING'}, "Move To Mouse Cursor allowed only in the UV Editor")
        else:
            destination_pos = self.destination_pos

        MP = TrMoveProps(context, is_global=False)
        MP.move_mode = move_mode
        MP.direction_str = self.direction
        MP.increment = self.increment
        MP.destination_pos = destination_pos

        MF = MoveFactory(
            context,
            MP,
            self.influence_mode,
            objs,
            self.op_order,
            self.island_pivot
        )
        if not MF.move():
            self.report(MF.message[0], MF.message[1])
            return {'CANCELLED'}

        return {'FINISHED'}


class ZUV_OT_MoveToUvArea(bpy.types.Operator):
    bl_idname = "uv.zenuv_move_to_uv_area"
    bl_label = "Move To UV Area"
    bl_description = "Move center of the selected Islands to the UV Area"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "There are no selected objects.")
            return {'CANCELLED'}

        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()

            loops = island_util.LoopsFactory.loops_by_islands(context, bm, uv_layer)

            for cluster in loops:
                cp = BoundingBox2d(points=[loop[uv_layer].uv for loop in cluster]).center

                offset = Vector((cp.x % 1, cp.y % 1)) - cp
                TransformLoops.move_loops(cluster, uv_layer, offset)

            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {'FINISHED'}


uv_tr_move_classes = (
    ZUV_OT_TrMove,
    ZUV_OT_MoveToUvArea
)


def register_tr_move():
    from bpy.utils import register_class
    for cl in uv_tr_move_classes:
        register_class(cl)


def unregister_tr_move():
    from bpy.utils import unregister_class
    for cl in uv_tr_move_classes:
        unregister_class(cl)
