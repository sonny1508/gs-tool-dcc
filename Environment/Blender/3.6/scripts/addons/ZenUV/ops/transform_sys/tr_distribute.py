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
import random
from mathutils import Vector
from math import radians
from ZenUV.stacks.utils import Cluster
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import (
    resort_objects,
    get_mesh_data,
)
from ZenUV.utils.transform import (
    rotate_island,
    move_island,
    zen_convex_hull_2d,
    bound_box,
    UvTransformUtils
)
from ZenUV.ops.transform_sys.tr_labels import TrLabels
from .transform_utils.tr_utils import Cursor2D, TransformOrderSolver


class ZUV_OT_TrArrange(bpy.types.Operator):
    bl_idname = "uv.zenuv_arrange_transform"
    bl_label = TrLabels.OT_ARRANGE_LABEL
    bl_description = TrLabels.OT_ARRANGE_DESC
    bl_options = {'REGISTER', 'UNDO'}

    # def update_uniform(self, context):
    #     if self.uniform_quant:
    #         self.count_v = 0
    #         self.quant_v = 0

    def upd_count_u(self, context):
        if self.count_u != 0:
            self.quant.x = 1 / self.count_u
        else:
            self.quant.x = 0

    def upd_count_v(self, context):
        if self.count_v != 0:
            self.quant.y = 1 / self.count_v
        else:
            self.quant.y = 0

    def upd_quant_u(self, context):
        self.quant.x = self.quant_u

    def upd_quant_v(self, context):
        self.quant.y = self.quant_v

    def update_input_mode(self, context):
        if self.input_mode == "SIMPLIFIED":
            if self.quant.x != 0:
                self.count_u = 1 / self.quant.x
            else:
                self.count_u = 0
            if self.quant.y != 0:
                self.count_v = 1 / self.quant.y
            else:
                self.count_v = 0

        elif self.input_mode == "ADVANCED":
            self.quant_u = self.quant.x
            self.quant_v = self.quant.y

    quant: bpy.props.FloatVectorProperty(
        name="",
        size=2,
        default=(0.0, 0.0),
        subtype='XYZ',
        options={"HIDDEN"}
    )
    quant_u: bpy.props.FloatProperty(
        name=TrLabels.PROP_ARRANGE_QUANT_U_LABEL,
        description=TrLabels.PROP_ARRANGE_QUANT_U_DESC,
        precision=3,
        default=0.0,
        step=1,
        min=0.0,
        update=upd_quant_u
    )
    quant_v: bpy.props.FloatProperty(
        name=TrLabels.PROP_ARRANGE_QUANT_V_LABEL,
        description=TrLabels.PROP_ARRANGE_QUANT_V_DESC,
        precision=3,
        default=0.0,
        step=1,
        min=0.0,
        update=upd_quant_v
    )
    count_u: bpy.props.IntProperty(
        name=TrLabels.PROP_ARRANGE_COUNT_U_LABEL,
        description=TrLabels.PROP_ARRANGE_COUNT_U_DESC,
        default=0,
        min=0,
        update=upd_count_u
    )
    count_v: bpy.props.IntProperty(
        name=TrLabels.PROP_ARRANGE_COUNT_V_LABEL,
        description=TrLabels.PROP_ARRANGE_COUNT_V_DESC,
        default=0,
        min=0,
        update=upd_count_v
    )
    reposition: bpy.props.FloatVectorProperty(
        name=TrLabels.PROP_ARRANGE_POSITION_LABEL,
        description=TrLabels.PROP_ARRANGE_POSITION_DESC,
        size=2,
        precision=4,
        step=1,
        default=(0.0, 0.0),
        subtype='XYZ'
    )
    limit: bpy.props.FloatVectorProperty(
        name=TrLabels.PROP_ARRANGE_LIMIT_LABEL,
        description=TrLabels.PROP_ARRANGE_LIMIT_DESC,
        size=2,
        precision=3,
        min=0.0,
        default=(1.0, 1.0),
        subtype='XYZ'
    )
    input_mode: bpy.props.EnumProperty(
        name=TrLabels.PROP_ARRANGE_INP_MODE_LABEL,
        description=TrLabels.PROP_ARRANGE_INP_MODE_DESC,
        items=[
            ("SIMPLIFIED", TrLabels.PROP_ARRANGE_INP_MODE_SIMPL_LABEL, ""),
            ("ADVANCED", TrLabels.PROP_ARRANGE_INP_MODE_ADV_LABEL, ""),
        ],
        default="SIMPLIFIED",
        update=update_input_mode
    )
    start_from: bpy.props.EnumProperty(
        name=TrLabels.PROP_ARRANGE_START_FROM_LABEL,
        description=TrLabels.PROP_ARRANGE_START_FROM_DESC,
        items=[
            ("INPLACE", "In Place", ""),
            ("BOTTOM", "Bottom", ""),
            ("CENTER", "Center", ""),
            ("TOP", "Top", ""),
            ("CURSOR", "Cursor", "")
        ],
        default="INPLACE"
    )
    randomize: bpy.props.BoolProperty(
        name=TrLabels.PROP_ARRANGE_RANDOMIZE_LABEL,
        description=TrLabels.PROP_ARRANGE_RANDOMIZE_DESC,
        default=False
    )
    seed: bpy.props.IntProperty(
        name=TrLabels.PROP_ARRANGE_SEED_LABEL,
        description=TrLabels.PROP_ARRANGE_SEED_DESC,
        default=132,
    )
    scale: bpy.props.FloatProperty(
        name=TrLabels.PROP_ARRANGE_SCALE_LABEL,
        description=TrLabels.PROP_ARRANGE_SCALE_DESC,
        precision=3,
        default=1.0,
        step=1,
        min=0.01
    )

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def draw_quant(self, context):
        self.layout.separator_spacer()
        col = self.layout.column(align=True)
        row = col.row(align=True)
        if self.input_mode == "SIMPLIFIED":
            mode = "count"
        elif self.input_mode == "ADVANCED":
            mode = "quant"
        row.prop(self, mode + "_u")
        col = row.column(align=True)
        col.prop(self, mode + "_v")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "input_mode")
        row = layout.row(align=True)
        row.prop(self, "start_from")

        self.draw_quant(context)
        if not self.input_mode == "SIMPLIFIED":
            layout.prop(self, "limit")
        layout.label(text="Correction:")
        box = layout.box()
        box.prop(self, "reposition")
        row = box.row(align=True)
        row.prop(self, "randomize")
        if self.randomize:
            row.prop(self, "seed")
        box.prop(self, "scale")

    def invoke(self, context, event):
        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            return {"CANCELLED"}
        self.criterion_data = dict()
        counter = 0
        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()
            bm.faces.ensure_lookup_table()
            islands = island_util.get_island(context, bm, uv_layer)
            for island in islands:
                cluster = Cluster(context, obj, island)
                criterion = counter
                self.criterion_data.update(
                    {
                        counter:
                            {
                                "cluster": cluster.geometry["faces_ids"],
                                "bbox": cluster.bbox,
                                "center": cluster.bbox["cen"],
                                "criterion": criterion,
                                "object": obj.name
                            }
                    }
                )
                counter += 1
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        if self.input_mode == "SIMPLIFIED":
            self.limit = Vector((1.0, 1.0))
        reposition = self.reposition
        base_position = Vector((0.0, 0.0))
        criterion_chart = sorted(self.criterion_data.keys())
        position_chart = sorted(criterion_chart, key=lambda x: self.criterion_data[x]["center"].x, reverse=False)

        for _id in position_chart:
            if self.criterion_data[_id]["center"].x > 0:
                break

        if self.start_from == "TOP":
            base_position = Vector((0, 1 - self.criterion_data[_id]["bbox"]["len_y"]))
        elif self.start_from == "BOTTOM":
            base_position = Vector((0.0, 0.0))
        elif self.start_from == "CENTER":
            base_position = Vector((0, 0.5 - self.criterion_data[_id]["bbox"]["len_y"] / 2))
        elif self.start_from == "INPLACE":
            base_position = self.criterion_data[_id]["bbox"]["bl"]
        elif self.start_from == "CURSOR":
            base_position = Cursor2D(context).uv_cursor_pos

        if self.randomize:
            random.shuffle(criterion_chart)

        real_limit = base_position + reposition + self.limit
        current = Vector((0.0, 0.0))
        for _id in criterion_chart:
            cluster = self.criterion_data[_id]
            cl_size = Vector((cluster["bbox"]["len_x"], cluster["bbox"]["len_y"])) * 0.5
            cl_position = base_position + cl_size + reposition

            if self.limit.x != 0:
                if cl_position.x + current.x > real_limit.x:
                    current.x = 0
                    current.y += self.quant.y

            if self.limit.y != 0:
                if cl_position.y + current.y > real_limit.y:
                    current.y = 0

            self.criterion_data[_id].update({"position": cl_position + current})
            current = current + Vector((self.quant.x, 0))

        # Set Cluster to position
        for cluster in self.criterion_data.values():
            cl = Cluster(context, cluster['object'], cluster["cluster"])
            cl.move_to(cluster["position"])
            cl.scale([self.scale, self.scale], cl.bbox["bl"])
            cl.update_mesh()

        return {'FINISHED'}


class ZUV_OT_RandomizeTransform(bpy.types.Operator):
    bl_idname = "uv.zenuv_randomize_transform"
    bl_label = TrLabels.OT_RANDOMIZE_TRANSFORM_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = TrLabels.OT_RANDOMIZE_TRANSFORM_DESC

    def update_scale(self, context):
        if self.uniform_scale:
            self.scale_v = self.scale_u

    def update_move(self, context):
        if self.uniform_move:
            self.move_v = self.move_u

    transform_islands: bpy.props.EnumProperty(
        name=TrLabels.PROP_TRANSFORM_TYPE_LABEL,
        description=TrLabels.PROP_TRANSFORM_TYPE_DESC,
        items=[
            ("ISLAND", "Island", ""),
            ("SELECTION", "Selection", "")
        ],
        default="ISLAND"
    )
    move_u: bpy.props.FloatProperty(
        name="U",
        description=TrLabels.PROP_RAND_POS_DESC,
        default=0.0,
        update=update_move
    )
    move_v: bpy.props.FloatProperty(
        name="V",
        description=TrLabels.PROP_RAND_POS_DESC,
        default=0.0,
    )
    uniform_move: bpy.props.BoolProperty(
        name=TrLabels.PROP_RAND_LOCK_LABEL,
        description=TrLabels.PROP_RAND_LOCK_DESC,
        default=True
    )
    scale_u: bpy.props.FloatProperty(
        name="U",
        description=TrLabels.PROP_RAND_SCALE_DESC,
        default=0.0,
        update=update_scale
    )
    scale_v: bpy.props.FloatProperty(
        name="V",
        description=TrLabels.PROP_RAND_SCALE_DESC,
        default=0.0,
    )
    uniform_scale: bpy.props.BoolProperty(
        name=TrLabels.PROP_RAND_LOCK_LABEL,
        description=TrLabels.PROP_RAND_LOCK_DESC,
        default=True
    )
    rotate: bpy.props.FloatProperty(
        name=TrLabels.PROP_RAND_ROT_LABEL,
        description=TrLabels.PROP_RAND_ROT_DESC,
        default=0.0,
    )
    shaker: bpy.props.IntProperty(
        name=TrLabels.PROP_RAND_SHAKE_LABEL,
        description=TrLabels.PROP_RAND_SHAKE_DESC,
        default=132,
    )

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def draw_move(self, context):
        col = self.layout.column(align=True)
        col.label(text="Position:")
        row = col.row(align=True)
        row.prop(self, "move_u")
        if self.uniform_move:
            lock_icon = "LOCKED"
            enb = False
        else:
            lock_icon = "UNLOCKED"
            enb = True
        row.prop(self, "uniform_move", icon=lock_icon, icon_only=True)
        col = row.column(align=True)
        col.enabled = enb
        col.prop(self, "move_v", text="")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "transform_islands")
        if self.transform_islands == 'ISLAND':
            # Move
            self.draw_move(context)
            # Rotate
            layout.separator_spacer()
            layout.label(text="Rotation:")
            row = layout.row(align=True)
            row.prop(self, "rotate", text="")
            # Scale
            layout.separator_spacer()
            col = layout.column(align=True)
            col.label(text="Scale:")
            row = col.row(align=True)
            row.prop(self, "scale_u")
            if self.uniform_scale:
                lock_icon = "LOCKED"
                enb = False
            else:
                lock_icon = "UNLOCKED"
                enb = True
            row.prop(self, "uniform_scale", icon=lock_icon, icon_only=True)
            col = row.column(align=True)
            col.enabled = enb
            col.prop(self, "scale_v", text="")
        else:
            self.draw_move(context)
        layout.separator_spacer()
        layout.prop(self, "shaker")

    def execute(self, context):

        # Type of transformation Islands or Selection
        # self.transform_islands = scene.zen_uv.tr_type == 'ISLAND'

        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            return {"CANCELLED"}

        pivot_point = TransformOrderSolver.get(context)
        if pivot_point == '':
            pivot_point = 'CENTER'

        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()
            if self.transform_islands == 'ISLAND':
                bm.faces.ensure_lookup_table()
                islands_for_process = island_util.get_island(context, bm, uv_layer)
                for island in islands_for_process:
                    # Move
                    position = Vector((random.uniform(-self.move_u, self.move_u), random.uniform(-self.move_v, self.move_v)))
                    move_island(island, uv_layer, position)
                    # Rotate
                    points = [loop[uv_layer].uv for face in island for loop in face.loops]
                    bbox = bound_box(points=zen_convex_hull_2d(points), uv_layer=uv_layer)
                    anchor = bbox["cen"]
                    angle = random.uniform(self.rotate * -1, self.rotate)
                    rotate_island(island, uv_layer, -radians(angle), anchor)
                    # Scale
                    points = [loop[uv_layer].uv for face in island for loop in face.loops]
                    bbox = bound_box(points=zen_convex_hull_2d(points), uv_layer=uv_layer)
                    anchor = bbox["cen"]
                    scale_factor_u = 1 + random.uniform(self.scale_u * -1, self.scale_u)
                    scale_factor_v = 1 + random.uniform(self.scale_v * -1, self.scale_v)
                    if self.uniform_scale:
                        scale = Vector((scale_factor_u, scale_factor_u))
                    else:
                        scale = Vector((scale_factor_u, scale_factor_v))
                    UvTransformUtils.scale_island(island, uv_layer, scale, anchor)

            else:
                loops = island_util.LoopsFactory.loops_by_sel_mode(context, bm, uv_layer)
                f_loops = {loop[uv_layer].uv.copy().freeze(): [lp for lp in loop.vert.link_loops if lp[uv_layer].uv == loop[uv_layer].uv] for loop in loops}
                for loops in f_loops.values():
                    direction = Vector((random.uniform(0, self.move_u), random.uniform(0, self.move_v)))
                    for loop in loops:
                        loop[uv_layer].uv += direction

            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {'FINISHED'}


uv_tr_distribute_classes = (
    ZUV_OT_TrArrange,
    ZUV_OT_RandomizeTransform,
)


def register_tr_distribute():
    from bpy.utils import register_class
    for cl in uv_tr_distribute_classes:
        register_class(cl)


def unregister_tr_distribute():
    from bpy.utils import unregister_class
    for cl in uv_tr_distribute_classes:
        unregister_class(cl)
