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
from dataclasses import dataclass
from math import radians
from ZenUV.utils.generic import (
    resort_by_type_mesh_in_edit_mode_and_sel
)
from ZenUV.utils.base_clusters.stripes import UvStripes
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.base_clusters.zen_cluster import ZenCluster
from ZenUV.utils.vlog import Log
from ZenUV.utils.transform import UvTransformUtils
from ZenUV.ops.transform_sys.transform_utils.tr_utils import ActiveUvImage


@dataclass
class TransformSwitch:

    location: bool = False
    rotation: bool = False
    scale: bool = False

    def to_list(self):
        return [self.location, self.rotation, self.scale]

    def set_state(self, operator):
        if operator.allow_match:
            self.location = operator.match_pos
            self.rotation = operator.match_rotation
            self.scale = operator.match_scale
        else:
            self.location = False
            self.rotation = False
            self.scale = False


class ZUV_OT_Stitch(bpy.types.Operator):
    bl_idname = "uv.zenuv_match_stitch"
    bl_label = 'Match and Stitch'
    bl_description = 'Matching the position, rotation, and scale of the island. Stitch the vertices together, if possible'
    bl_options = {'REGISTER', 'UNDO'}

    base_index: bpy.props.IntProperty(name='Base Island', default=0, min=0)
    allow_match: bpy.props.BoolProperty(
        name='Match',
        description='Match Island parameters',
        default=True
    )
    match_pos: bpy.props.BoolProperty(
        name='Position',
        description='Match Island position',
        default=True
    )
    match_rotation: bpy.props.BoolProperty(
        name='Rotation',
        description='Match Island rotation',
        default=True
    )
    match_scale: bpy.props.BoolProperty(
        name='Scale',
        description='Match Island position',
        default=True
    )
    reverse_matched: bpy.props.BoolProperty(
        name='Reverse Matched',
        description='Change the direction to the opposite direction for the matched island',
        default=False
    )
    reverse_base: bpy.props.BoolProperty(
        name='Reverse Base',
        description='Change the direction to the opposite direction for the matched island',
        default=False
    )
    stripe_offset: bpy.props.IntProperty(name='Offset loop', default=0)
    allow_stitch: bpy.props.BoolProperty(
        name='Stitch',
        description='Stitch the vertices together, if possible',
        default=False
    )
    average: bpy.props.BoolProperty(
        name='Average',
        description='Average Stitching',
        default=True
    )
    ignore_pin: bpy.props.BoolProperty(
        name='Ignore Pin',
        description='Ignore Pinned vertices',
        default=True
    )
    clear_seam: bpy.props.BoolProperty(
        name='Clear Seams',
        description='Clear the seams on the stitched edges',
        default=True
    )
    clear_pin: bpy.props.BoolProperty(
        name='Clear Pin',
        description='Clear the Pins on the Primary edgeloop',
        default=True
    )
    allow_postprocess: bpy.props.BoolProperty(
        name='Postprocess',
        description='Allow Postprocess',
        default=False
    )
    adv_offset: bpy.props.FloatVectorProperty(
        name='Offset',
        description='Advanced Offset',
        size=2,
        default=(0.0, 0.0),
        subtype='COORDINATES',
        precision=3
    )
    adv_rotate: bpy.props.FloatProperty(
        name='Rotate',
        description='Advanced Rotate',
        default=0.0,
        precision=3
    )
    adv_scale: bpy.props.FloatProperty(
        name='Scale',
        description='Advanced Scale',
        default=1.0,
        precision=3
    )

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.prop(self, 'base_index')

        layout.prop(self, 'allow_match', text='Match:')
        self.draw_match(layout)

        layout.prop(self, 'allow_stitch', text='Stitch:')
        self.draw_stitch(layout)

        layout.prop(self, 'allow_postprocess', text='Postprocess:')
        self.draw_postprocess(layout)

    def draw_postprocess(self, layout):
        box = layout.box()
        box.enabled = self.allow_postprocess
        box.prop(self, 'adv_offset')
        box.prop(self, 'adv_rotate')
        box.prop(self, 'adv_scale')
        box = box.box()
        row = box.row()
        row.prop(self, 'clear_pin')
        row.prop(self, 'clear_seam')

    def draw_stitch(self, layout):
        box = layout.box()
        box.enabled = self.allow_stitch
        box.prop(self, 'ignore_pin')
        box.prop(self, 'average')
        box.prop(self, 'stripe_offset')

    def draw_match(self, layout):
        box = layout.box()
        box.enabled = self.allow_match
        row = box.row()
        row.prop(self, 'match_pos')
        row.prop(self, 'match_rotation')
        row.prop(self, 'match_scale')
        box.prop(self, 'reverse_base')
        box.prop(self, 'reverse_matched')

    def reset_props(self):
        # Match
        if not self.allow_match:
            self.match_pos = True
            self.match_rotation = True
            self.match_scale = True
            self.reverse_base = False
            self.reverse_matched = False
        # Stitch
        if not self.allow_stitch:
            self.ignore_pin = True
            self.average = True
            self.stripe_offset = 0
        # Postprocess
        if not self.allow_postprocess:
            self.adv_offset = (0.0, 0.0)
            self.adv_rotate = 0.0
            self.adv_scale = 1.0

            self.clear_pin = True
            self.clear_seam = True

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "There are no selected objects.")
            return {'CANCELLED'}

        self.reset_props()

        Matcher = TransformSwitch()
        Matcher.set_state(self)

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()
            islands = island_util.get_island(context, bm, uv_layer, _sorted=True)
            islands = sorted(islands, key=(lambda x: x[0].index))

            if len(islands) == 1:
                self.report({'WARNING'}, "Only one Island has been selected. For normal operation, two islands must be selected.")
            if len(islands) > 2:
                self.report({'WARNING'}, "More than two islands selected. The result may not be acceptable.")

            clusters = list()
            for idx, island in enumerate(islands):
                clusters.append(ZenCluster(context, obj, island, bm, idx))
                p_cl = clusters[-1]
                p_edges = p_cl.get_selected_edges()
                if not len(p_edges):
                    clusters.pop(-1)
                    continue
                z_stripes = UvStripes(p_cl.get_selected_edges(), p_cl.uv_layer).get_stripes_from_selection()
                p_cl.stripes = z_stripes.stripes[0]
                p_cl.stripes.orient_alternative()

            if not len(clusters):
                self.report({'WARNING'}, "No islands with correctly selected edge loops were found.")
                return {'CANCELLED'}

            m_clusters = [cl for cl in clusters if True in [n.pinned for n in cl.stripes.nodes]]

            # if len(m_clusters) > 1:
            #     self.report({'WARNING'}, "More than one island is pinned down. The result may not be acceptable")
            if not len(m_clusters):
                # self.report({'WARNING'}, "No Primary island were found for processing")
                # return {'FINISHED'}
                b_index = self.base_index if self.base_index <= len(islands) - 1 else -1
                m_cluster = clusters.pop(b_index)  # type: ZenCluster
            else:
                b_index = 0
                m_cluster = clusters.pop(m_clusters[b_index].index)  # type: ZenCluster

            if self.reverse_base:
                m_cluster.stripes.reverse()

            result_scale = 1.0

            for cl in clusters:
                if cl.stripes.mesh_cycled and m_cluster.stripes.mesh_cycled:
                    is_cycled = True
                else:
                    is_cycled = False

                if self.reverse_matched:
                    cl.stripes.reverse()

                if is_cycled and not cl.stripes.is_matched_direction_for_stitch(m_cluster.stripes):
                    cl.stripes.reverse()

                cl.stripes.match_by_offset(m_cluster.stripes)

                if is_cycled:
                    Matcher.rotation = True

                    if Matcher.scale is True:
                        result_scale = cl.stripes.bounding_box.get_diff_scale_vec(m_cluster.stripes.bounding_box)[0]
                        result_scale += self.adv_scale - 1.0
                        Matcher.scale = False

                    origin_pivot = m_cluster.stripes.bounding_box.center
                    cl_pivot = cl.stripes.bounding_box.center
                else:
                    result_scale = self.adv_scale
                    origin_pivot = m_cluster.stripes.head_co
                    cl_pivot = cl.stripes.head_co

                if self.stripe_offset != 0:
                    cl.stripes.offset(self.stripe_offset)

                UvTransformUtils.match_islands_by_vectors(
                    cl.island,
                    uv_layer,
                    origin_pivot,
                    m_cluster.stripes.base_vec,
                    cl_pivot,
                    cl.stripes.base_vec,
                    ActiveUvImage(context).aspect,
                    adv_offset=self.adv_offset,
                    adv_rotate=radians(-self.adv_rotate),
                    adv_scale=result_scale,
                    matching=Matcher.to_list(),
                    is_cycled=is_cycled
                )

                if self.allow_stitch:
                    for c, m in zip(cl.stripes.nodes, m_cluster.stripes.nodes):
                        if self.allow_match:
                            c.update_uv_co()
                        if not self.average:
                            if self.ignore_pin:
                                c.set_position(m.uv_co)
                            else:
                                if not c.pinned:
                                    c.set_position(m.uv_co)
                        else:
                            if self.ignore_pin:
                                pos = (c.uv_co + m.uv_co) * 0.5
                                c.set_position(pos)
                                m.set_position(pos)
                            else:
                                if m.pinned and c.pinned:
                                    continue
                                if m.pinned and not c.pinned:
                                    c.set_position(m.uv_co)
                                elif not m.pinned and c.pinned:
                                    m.set_position(c.uv_co)
                                else:
                                    pos = (c.uv_co + m.uv_co) * 0.5
                                    c.set_position(pos)
                                    m.set_position(pos)

                if self.allow_stitch and self.clear_seam:
                    for edge in m_cluster.stripes.stripe:
                        edge.mesh_edge.seam = False

            if self.clear_pin:
                for node in m_cluster.stripes.nodes:
                    node.pinned = False

            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


classes = (
    ZUV_OT_Stitch,

)


def register():
    from bpy.utils import register_class
    for cl in classes:
        register_class(cl)


def unregister():
    from bpy.utils import unregister_class
    for cl in classes:
        unregister_class(cl)
