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

# Copyright 2023, Alex Zhornyak, Valeriy Yatsenko

import bpy
import bmesh
import gpu
import blf
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Color, Vector
from timeit import default_timer as timer
from dataclasses import dataclass
from collections import defaultdict
from itertools import chain
from ZenUV.utils.simple_geometry import TextRect
from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils

import numpy as np
import uuid


from ZenUV.utils.inject import is_modal_procedure
from ZenUV.utils.generic import resort_by_type_mesh_in_edit_mode_and_sel
from ZenUV.utils.blender_zen_utils import update_areas_in_uv, update_areas_in_view3d, ZenPolls
from ZenUV.utils.vlog import Log
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.stacks.utils import (
    M_STACK_LAYER_NAME,
    STACK_LAYER_NAME,
    StacksSystem,
    write_sim_data_to_layer,
    color_by_layer_sim_index,
    color_by_sim_index,
    enshure_stack_layer)


LITERAL_ZENUV_UPDATE = 'zenuv_update'
LITERAL_ZENUV_GENERAL_UPDATE = 'zenuv_general_update'
LITERAL_ZENUV_DELAYED_UV_GIZMOS = 'zenuv_delayed_uv_gizmos'
LITERAL_ZENUV_DELAYED_3D_GIZMOS = 'zenuv_delayed_3d_gizmos'

COLOR_FLIPPED = (0, 1, 0, 0.1)

t_3D_GIZMOS = {}


def get_z_offset(p_obj: bpy.types.Object):
    try:
        # object_volume = sum(p_obj.dimensions[:]) / 3
        # z_offset = object_volume / 5000 if object_volume < 5 else 0.0001

        # TODO: Check, could we leave just fixed ?

        return 0.00001
    except Exception:
        return 0.00001


if ZenPolls.version_lower_3_5_0:
    shader_tris = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    shader_smooth_tris = gpu.shader.from_builtin('3D_SMOOTH_COLOR')
else:

    def get_tris_shader():
        vert_out = gpu.types.GPUStageInterfaceInfo("gizmo_tris")
        vert_out.smooth('VEC4', 'finalColor')

        shader_info = gpu.types.GPUShaderCreateInfo()
        shader_info.push_constant('MAT4', "ModelViewProjectionMatrix")
        shader_info.push_constant('FLOAT', "z_offset")
        shader_info.push_constant('VEC4', "color")

        shader_info.vertex_in(0, 'VEC3', "pos")
        shader_info.vertex_out(vert_out)
        shader_info.fragment_out(0, 'VEC4', "fragColor")

        shader_info.vertex_source(
            """
            void main()
            {
                gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0f);
                gl_Position.z -= z_offset;
                finalColor = color;
            }
            """
        )

        shader_info.fragment_source(
            """
            void main()
            {
            fragColor = finalColor;
            }
            """
        )

        try:
            shader = gpu.shader.create_from_info(shader_info)
        except Exception as e:
            Log.error('GIZMO_SHADER:', str(e))
            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

        del vert_out
        del shader_info

        return shader

    def get_tris_smooth_shader():
        vert_out = gpu.types.GPUStageInterfaceInfo("gizmo_smooth_tris")
        vert_out.smooth('VEC4', 'finalColor')

        shader_info = gpu.types.GPUShaderCreateInfo()
        shader_info.push_constant('MAT4', "ModelViewProjectionMatrix")
        shader_info.push_constant('FLOAT', "z_offset")

        shader_info.vertex_in(0, 'VEC3', "pos")
        shader_info.vertex_in(1, 'VEC4', "color")

        shader_info.vertex_out(vert_out)
        shader_info.fragment_out(0, 'VEC4', "fragColor")

        shader_info.vertex_source(
            """
            void main()
            {
                gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0f);
                gl_Position.z -= z_offset;
                finalColor = color;
            }
            """
        )

        shader_info.fragment_source(
            """
            void main()
            {
            fragColor = finalColor;
            }
            """
        )

        shader = gpu.shader.create_from_info(shader_info)
        del vert_out
        del shader_info

        return shader

    shader_tris = get_tris_shader()
    shader_smooth_tris = get_tris_smooth_shader()


@bpy.app.handlers.persistent
def zenuv_depsgraph_ui_update(_):
    ctx = bpy.context


    depsgraph = ctx.evaluated_depsgraph_get()

    t_updates = None

    b_update_general = False

    for update in depsgraph.updates:
        if not isinstance(update.id, bpy.types.Mesh):
            continue

        b_geom = update.is_updated_geometry
        b_shade = update.is_updated_shading

        if b_geom or b_shade:
            if t_updates is None:
                t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

            s_uuid = str(uuid.uuid4())

            if not b_update_general:
                bpy.app.driver_namespace[LITERAL_ZENUV_GENERAL_UPDATE] = s_uuid
                b_update_general = True

            p_data = t_updates.get(update.id.original, ['', ''])

            if b_geom:
                p_data[0] = s_uuid
            if b_shade:
                p_data[1] = s_uuid

            t_updates[update.id.original] = p_data

    if t_updates is not None:
        bpy.app.driver_namespace[LITERAL_ZENUV_UPDATE] = t_updates


@dataclass
class DrawCustomShape:
    batch: object = None
    shader: object = None
    obj: bpy.types.Object = None
    color: callable = None
    z_offset: float = 0.0001

    def get_shape(self):
        return (self.batch, self.shader)


class ZUV_GGT_DetectionUV(bpy.types.GizmoGroup):
    bl_idname = "ZUV_GGT_DetectionUV"
    bl_label = "UV Detection Utils"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SHOW_MODAL_ALL'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        p_scene = context.scene
        return (
            (context.space_data.overlay.show_overlays or not p_scene.zen_uv.ui.use_draw_overlay_sync) and
            p_scene.zen_uv.ui.draw_mode_3D == 'UV_NO_SYNC' and context.mode == 'EDIT_MESH'
        )

    def setup(self, context: bpy.types.Context):
        pass

    def refresh(self, context: bpy.types.Context):
        if not is_modal_procedure(context):

            b_need_to_update = False

            p_keys = set(t_3D_GIZMOS.keys())
            for key in p_keys:
                try:
                    t_3D_GIZMOS[key].mesh_data = {}
                    b_need_to_update = True
                except Exception as e:
                    del t_3D_GIZMOS[key]

            if b_need_to_update:
                update_areas_in_view3d(context)


class ZUV_GGT_DrawUV(bpy.types.GizmoGroup):
    bl_idname = "ZUV_GGT_DrawUV"
    bl_label = "Draw UV"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'WINDOW'
    bl_options = {
        'PERSISTENT'
    } if bpy.app.version < (3, 0, 0) else {
        'PERSISTENT', 'EXCLUDE_MODAL'
    }
    tool_mode = {'DISPLAY'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        p_scene = context.scene
        return (
            (context.space_data.overlay.show_overlays or not p_scene.zen_uv.ui.use_draw_overlay_sync) and
            p_scene.zen_uv.ui.draw_mode_UV != 'NONE' and context.mode == 'EDIT_MESH')

    def setup(self, context: bpy.types.Context):
        self.mpr_draw = self.gizmos.new("UV_GT_zenuv_overlay_draw")
        self.mpr_draw.color = 0.0, 1.0, 0.0
        self.mpr_draw.alpha = 0.1
        self.mpr_draw.color_highlight = 0, 1.0, 1.0
        self.mpr_draw.alpha_highlight = 1
        self.mpr_draw.line_width = 1
        self.mpr_draw.use_draw_value = False
        self.mpr_draw.use_draw_scale = False
        self.mpr_draw.use_draw_modal = False
        self.mpr_draw.use_select_background = False
        self.mpr_draw.use_event_handle_all = False
        self.mpr_draw.use_grab_cursor = False
        self.mpr_draw.hide_select = True

    def refresh(self, context: bpy.types.Context):
        pass


def zenuv_delayed_overlay_build_uv():
    try:
        ctx = bpy.context
        t_delayed_gizmos = bpy.app.driver_namespace.get(LITERAL_ZENUV_DELAYED_UV_GIZMOS, set())
        while t_delayed_gizmos:
            p_gizmo = t_delayed_gizmos.pop()  # type: UV_GT_zenuv_overlay_draw
            p_gizmo.mark_build = True
        bpy.app.driver_namespace[LITERAL_ZENUV_DELAYED_UV_GIZMOS] = set()
        update_areas_in_uv(ctx)
    except Exception as e:
        Log.error('DELAYED GIZMO BUILD UV:', str(e))


def zenuv_delayed_overlay_build_3D():
    try:
        ctx = bpy.context
        t_delayed_gizmos = bpy.app.driver_namespace.get(LITERAL_ZENUV_DELAYED_3D_GIZMOS, set())
        while t_delayed_gizmos:
            p_gizmo = t_delayed_gizmos.pop()  # type: UV_GT_zenuv_overlay_draw
            p_gizmo.mark_build = True
        bpy.app.driver_namespace[LITERAL_ZENUV_DELAYED_3D_GIZMOS] = set()
        update_areas_in_view3d(ctx)
    except Exception as e:
        Log.error('DELAYED GIZMO BUILD 3D:', str(e))


class UV_GT_zenuv_overlay_draw(bpy.types.Gizmo):
    bl_idname = "UV_GT_zenuv_overlay_draw"
    bl_target_properties = ()

    __slots__ = (
        "custom_shapes",
        "mesh_data",
        "uv_sync",
        "last_mode",
        "mark_build"
    )

    def draw_gradient(self, context: bpy.types.Context):
        vertices = (
            (100, 100), (300, 100),
            (100, 200), (300, 200))

        indices = (
            (0, 1, 2),
            (2, 1, 3))

        r = (1, 0, 0)
        g = (0, 1, 0)
        b = (0, 0, 1)
        w = (1, 1, 1)

        td_values = [0.0, 81.39, 93.26, 93.26, 93.26, 93.26, 172.18, 238.49, 238.49, 238.49]
        td_colors = [
            [0, 0, 1],
            [0.43010099, 0.92444303, 0.05885693],
            [0.43010099, 0.92444303, 0.05885693],
            [0.43010099, 0.92444303, 0.05885693],
            [0.43010099, 0.92444303, 0.05885693],
            [0.73979203, 0.42208784, 0.02687326],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],]

        td_values = [
            0, 50, 100, 150, 200, 250
        ]
        td_colors = [
            r, g, b, w, r, g
        ]

        if len(td_values) == 0:
            return

        indices = []
        vertices = []
        vertex_colors = []

        p_area = context.area

        p_offsets = ZuvTrimsheetUtils.get_area_offsets(p_area)

        # n_top_offset = p_offsets.get('top')
        n_right_offset = p_offsets.get('right')
        # n_left_offset = p_offsets.get('left')
        # n_bottom_offset = p_offsets.get('bottom')

        addon_prefs = get_prefs()
        ui_scale = context.preferences.view.ui_scale
        i_font_size = addon_prefs.draw_label_font_size
        try:
            blf.size(0, i_font_size, bpy.context.preferences.system.dpi)
        except TypeError:
            blf.size(0, round(i_font_size), bpy.context.preferences.system.dpi)

        i_height = addon_prefs.td_draw.height
        d_font_offset_top = i_font_size
        d_font_offset_bottom = i_font_size * 2

        start_x = p_area.width - addon_prefs.td_draw.width - n_right_offset - 20 * ui_scale
        start_y = 10 * ui_scale + d_font_offset_bottom

        scale_x = addon_prefs.td_draw.width / td_values[-1]

        for idx, val in enumerate(td_values):

            val *= scale_x

            vertices.append(
                (start_x + val, start_y)
            )
            vertices.append(
                (start_x + val, start_y + i_height)
            )
            vertex_colors.append((*td_colors[idx], 1))
            vertex_colors.append((*td_colors[idx], 1))

            b_is_odd = idx % 2 == 1

            label = TextRect(
                left=start_x + val,
                bottom=start_y + i_height + d_font_offset_top if b_is_odd else start_y - d_font_offset_bottom,
                name=str(td_values[idx]),
                auto_normalize=False,
                color=(1, 1, 1, 1)
            )
            label.draw_text()

            if idx != 0:

                n_v_idx = len(vertices) - 4

                indices.extend(
                    [
                        (n_v_idx, n_v_idx + 1, n_v_idx + 2),
                        (n_v_idx + 2, n_v_idx + 1, n_v_idx + 3)])

        gpu.state.blend_set('ALPHA')
        shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        batch = batch_for_shader(
            shader, 'TRIS',
            {"pos": vertices, "color": vertex_colors}, indices=indices
        )
        shader.bind()
        batch.draw(shader)
        gpu.state.blend_set('NONE')

    def draw_label(self, context: bpy.types.Context):
        p_scene = context.scene
        ui_scale = context.preferences.view.ui_scale
        addon_prefs = get_prefs()
        i_font_size = addon_prefs.draw_label_font_size
        try:
            blf.size(0, i_font_size, bpy.context.preferences.system.dpi)
        except TypeError:
            blf.size(0, round(i_font_size), bpy.context.preferences.system.dpi)

        p_offsets = ZuvTrimsheetUtils.get_area_offsets(context.area)
        n_top_offset = p_offsets.get('top')
        n_right_offset = p_offsets.get('right')
        n_left_offset = p_offsets.get('left')
        n_bottom_offset = p_offsets.get('bottom')

        attr_name, p_mode = p_scene.zen_uv.ui.get_draw_mode_pair_by_context(context)

        s_label = bpy.types.UILayout.enum_item_name(
            p_scene.zen_uv.ui, attr_name, p_mode)
        s_label = f'ZenUV: Display {s_label}'

        v_sca = Vector((context.area.width - n_left_offset - n_right_offset, context.area.height - n_top_offset - n_bottom_offset, 1.0))
        t_width, t_height = blf.dimensions(0, s_label)

        i_left = round(n_left_offset + v_sca.x / 2 - t_width / 2)
        i_bottom = round(n_bottom_offset + v_sca.y - t_height - 10 * ui_scale)

        label = TextRect(
            left=i_left,
            bottom=i_bottom,
            name=s_label,
            color=addon_prefs.draw_label_font_color[:],
            auto_normalize=False
        )

        label.draw_text()

    def _do_draw(self, context: bpy.types.Context, select_id=None):

        self.draw_label(context)

        # special case
        if context.scene.zen_uv.ui.draw_mode_UV == 'TEXEL_DENSITY':
            self.draw_gradient(context)
            return

        # when we assigned nothing
        if self.mesh_data is None:
            return

        if self.mark_build:
            if not is_modal_procedure(context):
                self.build(context)
        elif not self.check_valid_data(context):
            if not is_modal_procedure(context):
                if bpy.app.timers.is_registered(zenuv_delayed_overlay_build_uv):
                    bpy.app.timers.unregister(zenuv_delayed_overlay_build_uv)
                t_delayed_gizmos = bpy.app.driver_namespace.get(LITERAL_ZENUV_DELAYED_UV_GIZMOS, set())
                t_delayed_gizmos.add(self)
                bpy.app.driver_namespace[LITERAL_ZENUV_DELAYED_UV_GIZMOS] = t_delayed_gizmos
                bpy.app.timers.register(zenuv_delayed_overlay_build_uv, first_interval=0.05)
            return

        if not self.custom_shapes:
            return

        viewport_info = gpu.state.viewport_get()

        width = viewport_info[2]
        height = viewport_info[3]

        region = context.region

        uv_to_view = region.view2d.view_to_region

        origin_x, origin_y = uv_to_view(0, 0, clip=False)
        top_x, top_y = uv_to_view(1.0, 1.0, clip=False)
        axis_x = top_x - origin_x
        axis_y = top_y - origin_y

        matrix = Matrix((
            [axis_x / width * 2, 0, 0, 2.0 * -
                ((width - origin_x - 0.5 * width)) / width],
            [0, axis_y / height * 2, 0, 2.0 * -
                ((height - origin_y - 0.5 * height)) / height],
            [0, 0, 1.0, 0],
            [0, 0, 0, 1.0]))

        identiy = Matrix.Identity(4)

        gpu.state.blend_set('ALPHA')

        with gpu.matrix.push_pop():
            gpu.matrix.load_matrix(matrix)

            with gpu.matrix.push_pop_projection():
                gpu.matrix.load_projection_matrix(identiy)

                draw_shape: DrawCustomShape
                for draw_shape in self.custom_shapes:
                    batch, shader = draw_shape.get_shape()

                    shader.bind()
                    if draw_shape.color is not None:
                        shader.uniform_float("color", draw_shape.color())
                    batch.draw()

        gpu.state.blend_set('NONE')

    def draw(self, context: bpy.types.Context):
        self._do_draw(context)

    def test_select(self, context: bpy.types.Context, location):
        return -1

    def draw_select(self, context: bpy.types.Context, select_id):
        self._do_draw(context, select_id=select_id)

    def setup(self):
        if not hasattr(self, "mesh_data"):
            self.custom_shapes = []
            self.mesh_data = {}
            self.uv_sync = False
            self.last_mode = ''
            self.mark_build = False

    def exit(self, context, cancel):
        context.area.header_text_set(None)

    @classmethod
    def is_face_flipped(cls, uv_layer, p_face):
        from ZenUV.utils.generic import is_face_flipped
        return is_face_flipped(p_face, uv_layer)

    def check_valid_data(self, context: bpy.types.Context):
        b_is_uv_sync = context.scene.tool_settings.use_uv_select_sync
        if self.uv_sync != b_is_uv_sync:
            return False

        p_scene = context.scene
        if self.last_mode != p_scene.zen_uv.ui.draw_mode_UV:
            return False

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        check_data = {}

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            check_data[me] = t_updates.get(me)

        # 1) check shading, geometry
        if not b_is_uv_sync or p_scene.zen_uv.ui.draw_mode_UV == 'SIMILAR_SELECTED':
            return self.mesh_data == check_data

        # 2) check geometry only
        if self.mesh_data.keys() != check_data.keys():
            return False

        for key in self.mesh_data.keys():
            if self.mesh_data[key][0] != check_data[key][0]:
                return False

        return True

    def build(self, context: bpy.types.Context):
        p_scene = context.scene

        self.mark_build = False

        method_name = 'build_' + p_scene.zen_uv.ui.draw_mode_UV.lower()
        if hasattr(self, method_name):
            p_method = getattr(self, method_name)

            b_is_uv_sync = context.scene.tool_settings.use_uv_select_sync

            self.custom_shapes.clear()
            self.mesh_data = {}
            self.last_mode = p_scene.zen_uv.ui.draw_mode_UV
            self.uv_sync = b_is_uv_sync

            p_method(context)

    def build_finished(self, context: bpy.types.Context):
        addon_prefs = get_prefs()

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            bm = bmesh.from_edit_mesh(me)
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.active
            if uv_layer:
                loops = bm.calc_loop_triangles()

                fmap = bm.faces.layers.int.get("ZenUV_Finished")

                uvs = defaultdict(list)
                for looptris in loops:
                    if not looptris[0].face.hide and (self.uv_sync or looptris[0].face.select):
                        idx = looptris[0].face[fmap] if fmap is not None else 0
                        for loop in looptris:
                            uvs[idx].append(loop[uv_layer].uv.to_tuple(5))

                t_colors = {
                    0: lambda: (*addon_prefs.UnFinishedColor[:3], addon_prefs.UnFinishedColor[3]),
                    1: lambda: (*addon_prefs.FinishedColor[:3], addon_prefs.FinishedColor[3]),
                }

                for k, v in uvs.items():
                    if len(v) > 0:
                        uv_verts, uv_indices = np.unique(v, return_inverse=True, axis=0)
                        uv_coords = uv_verts.tolist()
                        uv_indices = uv_indices.astype(np.int32)

                        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                        batch = batch_for_shader(shader, 'TRIS', {"pos": uv_coords}, indices=uv_indices)
                        batch.program_set(shader)

                        self.custom_shapes.append(
                            DrawCustomShape(batch, shader, p_obj, t_colors[k]))

    def build_flipped(self, context: bpy.types.Context):
        addon_prefs = get_prefs()

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            bm = bmesh.from_edit_mesh(me)
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.active
            if uv_layer:
                loops = bm.calc_loop_triangles()
                uvs = [
                    loop[uv_layer].uv.to_tuple(5)
                    for looptris in loops for loop in looptris
                    if not looptris[0].face.hide and
                    (self.uv_sync or looptris[0].face.select) and
                    self.is_face_flipped(uv_layer, looptris[0].face)
                ]

                if len(uvs):
                    uv_verts, uv_indices = np.unique(uvs, return_inverse=True, axis=0)
                    uv_coords = uv_verts.tolist()
                    uv_indices = uv_indices.astype(np.int32)

                    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                    batch = batch_for_shader(shader, 'TRIS', {"pos": uv_coords}, indices=uv_indices)
                    batch.program_set(shader)

                    self.custom_shapes.append(
                        DrawCustomShape(
                            batch, shader, p_obj,
                            lambda: (*addon_prefs.FlippedColor[:3], addon_prefs.FlippedColor[3])))

    def build_excluded(self, context: bpy.types.Context):
        from ZenUV.ops.pack_exclusion import PACK_EXCLUDED_FACEMAP_NAME

        addon_prefs = get_prefs()

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            bm = bmesh.from_edit_mesh(me)
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.active
            mesh_layer = bm.faces.layers.int.get(PACK_EXCLUDED_FACEMAP_NAME)
            if uv_layer and mesh_layer:
                loops = bm.calc_loop_triangles()
                uvs = [
                    loop[uv_layer].uv.to_tuple(5)
                    for looptris in loops for loop in looptris
                    if not looptris[0].face.hide and
                    (self.uv_sync or looptris[0].face.select) and
                    looptris[0].face[mesh_layer] == 1
                ]

                if len(uvs):
                    uv_verts, uv_indices = np.unique(uvs, return_inverse=True, axis=0)
                    uv_coords = uv_verts.tolist()
                    uv_indices = uv_indices.astype(np.int32)

                    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                    batch = batch_for_shader(shader, 'TRIS', {"pos": uv_coords}, indices=uv_indices)
                    batch.program_set(shader)

                    self.custom_shapes.append(
                        DrawCustomShape(
                            batch, shader, p_obj,
                            lambda: (*addon_prefs.ExcludedColor[:3], addon_prefs.ExcludedColor[3])))

    def build_similar_static(self, context: bpy.types.Context):
        self.do_build_similar(context, False)

    def build_stacked_manual(self, context: bpy.types.Context):
        self.do_build_similar(context, True)

    def do_build_similar(self, context: bpy.types.Context, b_is_manual: bool):
        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        stacks = StacksSystem(context)
        sim_data = stacks.forecast_stacks()
        write_sim_data_to_layer(context, sim_data)

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            bm = bmesh.from_edit_mesh(me)
            bm = bm.copy()

            bm.verts.index_update()
            bm.edges.index_update()
            bm.edges.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()
            bound_edges = [bm.edges[index] for index in island_util.uv_bound_edges_indexes(bm.faces, uv_layer)]
            bmesh.ops.split_edges(bm, edges=bound_edges)
            bm.verts.ensure_lookup_table()
            no_actual_verts = [v for v in bm.verts if not v.link_faces]
            bmesh.ops.delete(bm, geom=no_actual_verts, context='VERTS')
            bm.verts.ensure_lookup_table()
            stacks_layer = enshure_stack_layer(
                bm,
                stack_layer_name=M_STACK_LAYER_NAME if b_is_manual else STACK_LAYER_NAME)
            colors = [color_by_layer_sim_index(bm, v_idx, stacks_layer) for v_idx in range(len(bm.verts))]
            loops = bm.calc_loop_triangles()

            colors = []
            uvs = []
            for looptris in loops:
                for loop in looptris:
                    if not looptris[0].face.hide and (self.uv_sync or looptris[0].face.select):
                        colors.append(
                            color_by_layer_sim_index(
                                bm, loop.vert.index, stacks_layer))
                        uvs.append(loop[uv_layer].uv.to_tuple(5))

            if len(uvs):
                uv_verts, tri_indices, uv_indices = np.unique(uvs, return_index=True, return_inverse=True, axis=0)
                uv_coords = uv_verts.tolist()
                uv_indices = uv_indices.astype(np.int32)
                uv_colors = [colors[idx] for idx in tri_indices]

                shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
                batch = batch_for_shader(shader, 'TRIS', {"pos": uv_coords, "color": uv_colors}, indices=uv_indices)
                batch.program_set(shader)

                self.custom_shapes.append(
                    DrawCustomShape(
                        batch=batch,
                        shader=shader,
                        color=None,
                        obj=p_obj))

            bm.free()

    def build_stacked(self, context: bpy.types.Context):
        addon_prefs = get_prefs()

        def get_color():
            return (*addon_prefs.StackedColor[:3], addon_prefs.StackedColor[3])

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        stacks = StacksSystem(context)
        stacks.get_stacked()
        ids_dict = stacks.get_stacked_faces_ids(stacks.ASD)

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            faces_ids = ids_dict.get(p_obj.name, [])
            if faces_ids:
                bm = bmesh.from_edit_mesh(me)
                bm.verts.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

                uv_layer = bm.loops.layers.uv.active
                if uv_layer is None:
                    continue

                loops = bm.calc_loop_triangles()

                uvs = [
                    loop[uv_layer].uv.to_tuple(5)
                    for looptris in loops for loop in looptris
                    if not looptris[0].face.hide and
                    (self.uv_sync or looptris[0].face.select) and
                    looptris[0].face.index in faces_ids
                ]

                if len(uvs):
                    uv_verts, uv_indices = np.unique(uvs, return_inverse=True, axis=0)
                    uv_coords = uv_verts.tolist()
                    uv_indices = uv_indices.astype(np.int32)

                    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                    batch = batch_for_shader(shader, 'TRIS', {"pos": uv_coords}, indices=uv_indices)
                    batch.program_set(shader)

                    self.custom_shapes.append(
                        DrawCustomShape(batch, shader, p_obj, get_color))

    def build_similar_selected(self, context: bpy.types.Context):
        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        stacks = StacksSystem(context)
        sim_data = stacks.forecast_selected()

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

        for sim_index, data in sim_data.items():
            s_index = sim_index
            for obj_name, islands in data["objs"].items():
                obj = context.scene.objects[obj_name]

                bms = bmesh.from_edit_mesh(obj.data).copy()
                bms.faces.ensure_lookup_table()
                bms.verts.ensure_lookup_table()

                s_faces = set(chain.from_iterable(islands.values()))

                faces_to_del = [f for f in bms.faces if f.index not in s_faces]

                bmesh.ops.delete(bms, geom=faces_to_del, context='FACES')
                bms.verts.ensure_lookup_table()
                bms.faces.ensure_lookup_table()

                uv_layer = bms.loops.layers.uv.active
                if uv_layer is None:
                    continue

                loops = bms.calc_loop_triangles()

                color = color_by_sim_index(s_index)

                def get_color():
                    return color

                uvs = [
                    loop[uv_layer].uv.to_tuple(5)
                    for looptris in loops for loop in looptris
                    if not looptris[0].face.hide
                ]

                if len(uvs):
                    uv_verts, uv_indices = np.unique(uvs, return_inverse=True, axis=0)
                    uv_coords = uv_verts.tolist()
                    uv_indices = uv_indices.astype(np.int32)

                    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
                    batch = batch_for_shader(shader, 'TRIS', {"pos": uv_coords}, indices=uv_indices)
                    batch.program_set(shader)

                    self.custom_shapes.append(
                        DrawCustomShape(batch, shader, obj, get_color))

                bms.free()


class ZUV_GGT_Draw3D(bpy.types.GizmoGroup):
    bl_idname = "ZUV_GGT_Draw3D"
    bl_label = "Draw 3D"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {
        '3D', 'PERSISTENT', 'SHOW_MODAL_ALL'
    }

    tool_mode = {'DISPLAY'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        p_scene = context.scene
        return (
            (context.space_data.overlay.show_overlays or not p_scene.zen_uv.ui.use_draw_overlay_sync) and
            p_scene.zen_uv.ui.draw_mode_3D != 'NONE' and context.mode == 'EDIT_MESH')

    def setup(self, context: bpy.types.Context):
        self.mpr_draw = self.gizmos.new("VIEW3D_GT_zenuv_overlay_draw")
        self.mpr_draw.color = 0.0, 1.0, 0.0
        self.mpr_draw.alpha = 0.1
        self.mpr_draw.color_highlight = 0, 1.0, 1.0
        self.mpr_draw.alpha_highlight = 1
        self.mpr_draw.line_width = 1
        self.mpr_draw.use_draw_value = False
        self.mpr_draw.use_draw_scale = False
        self.mpr_draw.use_draw_modal = False
        self.mpr_draw.use_select_background = False
        self.mpr_draw.use_event_handle_all = False
        self.mpr_draw.use_grab_cursor = False
        self.mpr_draw.hide_select = True

        t_3D_GIZMOS[context.area.as_pointer()] = self.mpr_draw

    def refresh(self, context: bpy.types.Context):
        pass


class VIEW3D_GT_zenuv_overlay_draw(bpy.types.Gizmo):
    bl_idname = "VIEW3D_GT_zenuv_overlay_draw"
    bl_target_properties = ()

    __slots__ = (
        "custom_shapes",
        "mesh_data",
        "last_mode",
        "mark_build"
    )

    def _do_draw(self, context: bpy.types.Context, select_id=None):
        # when we assigned nothing
        if self.mesh_data is None:
            return

        if self.mark_build:
            if not is_modal_procedure(context):
                self.build(context)
        elif not self.check_valid_data(context):
            p_scene = context.scene

            s_modal_attr = f'draw_{p_scene.zen_uv.ui.draw_mode_3D.lower()}_modal'
            b_use_modal = getattr(p_scene.zen_uv.ui, s_modal_attr, False)
            if b_use_modal:
                self.build(context)
            else:
                if not is_modal_procedure(context):
                    if bpy.app.timers.is_registered(zenuv_delayed_overlay_build_3D):
                        bpy.app.timers.unregister(zenuv_delayed_overlay_build_3D)
                    t_delayed_gizmos = bpy.app.driver_namespace.get(LITERAL_ZENUV_DELAYED_3D_GIZMOS, set())
                    t_delayed_gizmos.add(self)
                    bpy.app.driver_namespace[LITERAL_ZENUV_DELAYED_3D_GIZMOS] = t_delayed_gizmos
                    bpy.app.timers.register(zenuv_delayed_overlay_build_3D, first_interval=0.05)
                return

        if not self.custom_shapes:
            return

        if ZenPolls.version_lower_3_5_0:
            import bgl
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glEnable(bgl.GL_LINE_SMOOTH)
            bgl.glEnable(bgl.GL_DEPTH_TEST)
            bgl.glEnable(bgl.GL_POLYGON_OFFSET_FILL)
            bgl.glPolygonOffset(-1, -1)
        else:
            gpu.state.blend_set('ALPHA')
            gpu.state.depth_test_set('LESS_EQUAL')
            gpu.state.depth_mask_set(True)

        draw_shape: DrawCustomShape
        for draw_shape in self.custom_shapes:
            self.matrix_space = draw_shape.obj.matrix_world.copy()

            batch, shader = draw_shape.get_shape()

            shader.bind()

            if draw_shape.color is not None:
                shader.uniform_float('color', draw_shape.color())

            if not ZenPolls.version_lower_3_5_0:
                shader.uniform_float('z_offset', draw_shape.z_offset)

            with gpu.matrix.push_pop():
                gpu.matrix.multiply_matrix(self.matrix_world)

                batch.draw(shader)

        if ZenPolls.version_lower_3_5_0:
            import bgl
            bgl.glDisable(bgl.GL_BLEND)
            bgl.glDisable(bgl.GL_LINE_SMOOTH)
            bgl.glDisable(bgl.GL_POLYGON_OFFSET_FILL)
            bgl.glPolygonOffset(0, 0)
        else:
            gpu.state.blend_set('NONE')
            gpu.state.depth_mask_set(False)

    def draw(self, context: bpy.types.Context):
        self._do_draw(context)

    def test_select(self, context: bpy.types.Context, location):
        return -1

    def draw_select(self, context: bpy.types.Context, select_id):
        self._do_draw(context, select_id=select_id)

    def setup(self):
        if not hasattr(self, "mesh_data"):
            self.custom_shapes = []
            self.mesh_data = {}
            self.last_mode = ''
            self.mark_build = False

    def exit(self, context, cancel):
        context.area.header_text_set(None)

    def check_valid_data(self, context: bpy.types.Context):
        p_scene = context.scene
        if self.last_mode != p_scene.zen_uv.ui.draw_mode_3D:
            return False

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        check_data = {}

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            check_data[me] = t_updates.get(me)

        # 1) check shading, geometry
        b_is_uv_sync = context.scene.tool_settings.use_uv_select_sync
        if ((not b_is_uv_sync and p_scene.zen_uv.ui.draw_mode_3D == 'UV_NO_SYNC') or
                p_scene.zen_uv.ui.draw_mode_3D == 'SIMILAR_SELECTED'):
            return self.mesh_data == check_data

        # 2) check only geometry
        if self.mesh_data.keys() != check_data.keys():
            return False

        for key in self.mesh_data.keys():
            if self.mesh_data[key][0] != check_data[key][0]:
                return False

        return True

    def build(self, context: bpy.types.Context):
        p_scene = context.scene

        self.mark_build = False

        method_name = 'build_' + p_scene.zen_uv.ui.draw_mode_3D.lower()
        if hasattr(self, method_name):
            p_method = getattr(self, method_name)

            self.custom_shapes.clear()
            self.mesh_data = {}
            self.last_mode = p_scene.zen_uv.ui.draw_mode_3D

            p_method(context)

    def build_finished(self, context: bpy.types.Context):
        addon_prefs = get_prefs()

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            bm = bmesh.from_edit_mesh(me)
            bm.faces.ensure_lookup_table()

            verts = [v.co.to_tuple() for v in bm.verts]

            fmap = bm.faces.layers.int.get("ZenUV_Finished")

            p_loops = bm.calc_loop_triangles()
            face_tri_indices = defaultdict(list)
            for looptris in p_loops:
                if not looptris[0].face.hide:
                    idx = looptris[0].face[fmap] if fmap is not None else 0
                    face_tri_indices[idx].append([loop.vert.index for loop in looptris])

            shader = shader_tris

            z_offset = get_z_offset(p_obj)

            t_colors = {
                0: lambda: (*addon_prefs.UnFinishedColor[:3], addon_prefs.UnFinishedColor[3]),
                1: lambda: (*addon_prefs.FinishedColor[:3], addon_prefs.FinishedColor[3]),
            }

            for k, v in face_tri_indices.items():
                if len(v) > 0:
                    batch = batch_for_shader(
                        shader, 'TRIS',
                        {"pos": verts},
                        indices=v)
                    batch.program_set(shader)
                    self.custom_shapes.append(
                        DrawCustomShape(batch, shader, p_obj, t_colors[k], z_offset))

    def build_excluded(self, context: bpy.types.Context):
        from ZenUV.ops.pack_exclusion import PACK_EXCLUDED_FACEMAP_NAME

        addon_prefs = get_prefs()

        def get_layer(bm: bmesh.types.BMesh):
            return bm.faces.layers.int.get(PACK_EXCLUDED_FACEMAP_NAME)

        def is_face_enabled(layer: bmesh.types.BMLayerItem, face: bmesh.types.BMFace):
            return face[layer] == 1

        def get_color():
            return (*addon_prefs.ExcludedColor[:3], addon_prefs.ExcludedColor[3])

        self.build_uniform_layer(context, get_layer, is_face_enabled, get_color)

    def build_flipped(self, context: bpy.types.Context):
        addon_prefs = get_prefs()

        def get_layer(bm: bmesh.types.BMesh):
            return bm.loops.layers.uv.active

        def is_face_enabled(layer: bmesh.types.BMLayerItem, face: bmesh.types.BMFace):
            return UV_GT_zenuv_overlay_draw.is_face_flipped(layer, face)

        def get_color():
            return (*addon_prefs.FlippedColor[:3], addon_prefs.FlippedColor[3])

        self.build_uniform_layer(context, get_layer, is_face_enabled, get_color)

    def build_tagged(self, context: bpy.types.Context):
        def get_face_color():
            return (0.505, 0.8, 0.175, 0.2)

        def get_edge_color():
            return (0.0, 1.0, 0.25, 1)

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            bm = bmesh.from_edit_mesh(me)
            bm.faces.ensure_lookup_table()

            p_loops = bm.calc_loop_triangles()
            p_indices = [
                [loop.vert.index for loop in looptris]
                for looptris in p_loops
                if not looptris[0].face.hide and
                looptris[0].face.tag
            ]

            verts = [v.co.to_tuple() for v in bm.verts]

            if p_indices:
                shader = shader_tris

                z_offset = get_z_offset(p_obj)

                batch = batch_for_shader(
                    shader, 'TRIS',
                    {"pos": verts},
                    indices=p_indices)
                batch.program_set(shader)
                self.custom_shapes.append(
                    DrawCustomShape(batch, shader, p_obj, get_face_color, z_offset))

            edge_indices = [(v.index for v in e.verts) for e in bm.edges if e.tag]
            if edge_indices:
                shader = shader_tris

                z_offset = get_z_offset(p_obj)

                batch = batch_for_shader(
                    shader, 'LINES',
                    {"pos": verts},
                    indices=p_indices)
                batch.program_set(shader)
                self.custom_shapes.append(
                    DrawCustomShape(batch, shader, p_obj, get_edge_color, z_offset))

    def build_uniform_layer(self, context: bpy.types.Context, get_layer: callable, is_face_enabled: callable, fn_color: callable):

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            bm = bmesh.from_edit_mesh(me)
            bm.faces.ensure_lookup_table()
            uv_layer = get_layer(bm)
            if uv_layer:
                p_loops = bm.calc_loop_triangles()
                p_indices = [
                    [loop.vert.index for loop in looptris]
                    for looptris in p_loops
                    if not looptris[0].face.hide and
                    is_face_enabled(uv_layer, looptris[0].face)
                ]
                if p_indices:
                    shader = shader_tris

                    verts = [v.co.to_tuple() for v in bm.verts]

                    z_offset = get_z_offset(p_obj)

                    batch = batch_for_shader(
                        shader, 'TRIS',
                        {"pos": verts},
                        indices=p_indices)
                    batch.program_set(shader)
                    self.custom_shapes.append(
                        DrawCustomShape(batch, shader, p_obj, fn_color, z_offset))

    def build_uv_no_sync(self, context: bpy.types.Context):
        addon_prefs = get_prefs()

        b_is_uv_sync = context.scene.tool_settings.use_uv_select_sync

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            if b_is_uv_sync:
                continue

            bm = bmesh.from_edit_mesh(me).copy()
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.active
            if uv_layer:
                p_loops = bm.calc_loop_triangles()
                p_indices = [
                    [loop.vert.index for loop in looptris]
                    for looptris in p_loops
                    if not looptris[0].face.hide and looptris[0].face.select and
                    all(loop[uv_layer].select for loop in looptris[0].face.loops)
                ]

                if p_indices:
                    shader = shader_tris

                    verts = [v.co.to_tuple() for v in bm.verts]

                    z_offset = get_z_offset(p_obj)

                    batch = batch_for_shader(
                        shader, 'TRIS',
                        {"pos": verts},
                        indices=p_indices)
                    batch.program_set(shader)
                    self.custom_shapes.append(
                        DrawCustomShape(
                            batch, shader, p_obj,
                            lambda: (*addon_prefs.UvNoSyncColor[:3], addon_prefs.UvNoSyncColor[3]),
                            z_offset))

            bm.free()

    def build_stretched(self, context: bpy.types.Context):
        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        def get_dir_vector(pos_0, pos_1):
            """ Return direction Vector from 2 Vectors """
            return Vector(pos_1 - pos_0)

        def get_distortion_color(uv_layer, vertex: bmesh.types.BMVert):
            """ Returns the distortion factor for a given vertex"""
            distortion = 0

            loops = vertex.link_loops
            for loop in loops:
                mesh_angle = loop.calc_angle()
                vec_0 = get_dir_vector(loop[uv_layer].uv, loop.link_loop_next[uv_layer].uv)
                vec_1 = get_dir_vector(loop[uv_layer].uv, loop.link_loop_prev[uv_layer].uv)
                uv_angle = vec_0.angle(vec_1, 0)
                distortion += abs(mesh_angle - uv_angle)

            return (0.2, baseColor.g + distortion, baseColor.b - distortion, alpha)

        p_scene = context.scene
        b_modal = p_scene.zen_uv.ui.draw_stretched_modal

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            colors = []
            baseColor = Color((0.0, 0.0, 1.0))
            alpha = 0.6

            bm = bmesh.from_edit_mesh(me)

            if b_modal:
                bm = bm.copy()

            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

            uv_layer = bm.loops.layers.uv.verify()
            if uv_layer:
                p_loops = bm.calc_loop_triangles()

                face_tri_indices = [
                    [loop.vert.index for loop in looptris]
                    for looptris in p_loops
                    if not looptris[0].face.hide]

                if face_tri_indices:
                    verts = [v.co.to_tuple() for v in bm.verts]

                    colors = [get_distortion_color(uv_layer, vertex) for vertex in bm.verts]

                    shader = shader_smooth_tris

                    z_offset = get_z_offset(p_obj)

                    batch = batch_for_shader(
                        shader, 'TRIS',
                        {"pos": verts, "color": colors},
                        indices=face_tri_indices)
                    batch.program_set(shader)
                    self.custom_shapes.append(
                        DrawCustomShape(
                            batch=batch,
                            shader=shader,
                            color=None,
                            obj=p_obj,
                            z_offset=z_offset))

            if b_modal:
                bm.free()

    def build_similar_static(self, context: bpy.types.Context):
        self.do_build_similar(context, False)

    def build_stacked_manual(self, context: bpy.types.Context):
        self.do_build_similar(context, True)

    def do_build_similar(self, context: bpy.types.Context, b_is_manual: bool):
        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        stacks = StacksSystem(context)
        sim_data = stacks.forecast_stacks()
        write_sim_data_to_layer(context, sim_data)

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            bm = bmesh.from_edit_mesh(me)
            bm = bm.copy()

            bm.verts.index_update()
            bm.edges.index_update()
            bm.edges.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()
            bound_edges = [bm.edges[index] for index in island_util.uv_bound_edges_indexes(bm.faces, uv_layer)]
            bmesh.ops.split_edges(bm, edges=bound_edges)
            bm.verts.ensure_lookup_table()
            no_actual_verts = [v for v in bm.verts if not v.link_faces]
            bmesh.ops.delete(bm, geom=no_actual_verts, context='VERTS')
            bm.verts.ensure_lookup_table()
            stacks_layer = enshure_stack_layer(
                bm,
                stack_layer_name=M_STACK_LAYER_NAME if b_is_manual else STACK_LAYER_NAME)
            colors = [color_by_layer_sim_index(bm, v_idx, stacks_layer) for v_idx in range(len(bm.verts))]
            loops = bm.calc_loop_triangles()
            verts = [v.co for v in bm.verts]

            face_tri_indices = [
                [loop.vert.index for loop in looptris]
                for looptris in loops
                if not looptris[0].face.hide]

            shader = shader_smooth_tris

            z_offset = get_z_offset(p_obj)

            batch = batch_for_shader(
                shader, 'TRIS',
                {"pos": verts, "color": colors},
                indices=face_tri_indices)
            batch.program_set(shader)
            self.custom_shapes.append(
                DrawCustomShape(
                    batch=batch,
                    shader=shader,
                    color=None,
                    obj=p_obj,
                    z_offset=z_offset))

            bm.free()

    def build_similar_selected(self, context: bpy.types.Context):
        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        stacks = StacksSystem(context)
        sim_data = stacks.forecast_selected()

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

        for sim_index, data in sim_data.items():
            s_index = sim_index
            for obj_name, islands in data["objs"].items():
                obj = context.scene.objects[obj_name]

                bms = bmesh.from_edit_mesh(obj.data).copy()
                bms.faces.ensure_lookup_table()
                bms.verts.ensure_lookup_table()

                s_faces = set(chain.from_iterable(islands.values()))

                faces_to_del = [f for f in bms.faces if f.index not in s_faces]

                bmesh.ops.delete(bms, geom=faces_to_del, context='FACES')
                bms.verts.ensure_lookup_table()
                bms.faces.ensure_lookup_table()

                loops = bms.calc_loop_triangles()

                verts = [v.co for v in bms.verts]

                face_tri_indices = [[
                    loop.vert.index for loop in looptris]
                    for looptris in loops
                    if not looptris[0].face.hide]

                color = color_by_sim_index(s_index)

                def get_color():
                    return color

                shader = shader_tris

                z_offset = get_z_offset(obj)

                batch = batch_for_shader(
                    shader, 'TRIS',
                    {"pos": verts},
                    indices=face_tri_indices)
                batch.program_set(shader)
                self.custom_shapes.append(
                    DrawCustomShape(
                        batch=batch,
                        shader=shader,
                        color=get_color,
                        obj=obj,
                        z_offset=z_offset))

                bms.free()

    def build_stacked(self, context: bpy.types.Context):
        addon_prefs = get_prefs()

        def get_color():
            return (*addon_prefs.StackedColor[:3], addon_prefs.StackedColor[3])

        t_updates = bpy.app.driver_namespace.get(LITERAL_ZENUV_UPDATE, {})

        stacks = StacksSystem(context)
        stacks.get_stacked()
        ids_dict = stacks.get_stacked_faces_ids(stacks.ASD)

        for p_obj in resort_by_type_mesh_in_edit_mode_and_sel(context):
            me = p_obj.data

            update_data = t_updates.get(me)
            self.mesh_data[me] = update_data.copy()

            faces_ids = ids_dict.get(p_obj.name, [])
            if faces_ids:
                bm = bmesh.from_edit_mesh(me)
                bm.verts.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

                loops = bm.calc_loop_triangles()
                verts = [v.co for v in bm.verts]

                face_tri_indices = [
                    [loop.vert.index for loop in looptris]
                    for looptris in loops
                    if not looptris[0].face.hide and
                    looptris[0].face.index in faces_ids]

                shader = shader_tris

                z_offset = get_z_offset(p_obj)

                batch = batch_for_shader(
                    shader, 'TRIS',
                    {"pos": verts},
                    indices=face_tri_indices)
                batch.program_set(shader)
                self.custom_shapes.append(
                    DrawCustomShape(
                        batch=batch,
                        shader=shader,
                        color=get_color,
                        obj=p_obj,
                        z_offset=z_offset))


class ZUV_GGT_DrawView2D(bpy.types.GizmoGroup):
    bl_idname = "ZUV_GGT_DrawView2D"
    bl_label = "Draw 2D"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {
        'PERSISTENT', 'SHOW_MODAL_ALL'
    }

    @classmethod
    def poll(cls, context: bpy.types.Context):
        p_scene = context.scene
        return (
            (context.space_data.overlay.show_overlays or not p_scene.zen_uv.ui.use_draw_overlay_sync) and
            p_scene.zen_uv.ui.draw_mode_3D != 'NONE' and context.mode == 'EDIT_MESH')

    def setup(self, context: bpy.types.Context):
        self.mpr_draw = self.gizmos.new("VIEW2D_GT_zenuv_overlay_draw")
        self.mpr_draw.color = 0.0, 1.0, 0.0
        self.mpr_draw.alpha = 0.1
        self.mpr_draw.color_highlight = 0, 1.0, 1.0
        self.mpr_draw.alpha_highlight = 1
        self.mpr_draw.line_width = 1
        self.mpr_draw.use_draw_value = False
        self.mpr_draw.use_draw_scale = False
        self.mpr_draw.use_draw_modal = False
        self.mpr_draw.use_select_background = False
        self.mpr_draw.use_event_handle_all = False
        self.mpr_draw.use_grab_cursor = False
        self.mpr_draw.hide_select = True

    def refresh(self, context: bpy.types.Context):
        pass


class VIEW2D_GT_zenuv_overlay_draw(bpy.types.Gizmo):
    bl_idname = "VIEW2D_GT_zenuv_overlay_draw"
    bl_target_properties = ()

    __slots__ = ()

    draw_label = UV_GT_zenuv_overlay_draw.draw_label

    draw_gradient = UV_GT_zenuv_overlay_draw.draw_gradient

    def _do_draw(self, context: bpy.types.Context, select_id=None):
        self.draw_label(context)

        # special case
        if context.scene.zen_uv.ui.draw_mode_3D == 'TEXEL_DENSITY':
            self.draw_gradient(context)
            return

    def draw(self, context: bpy.types.Context):
        self._do_draw(context)

    def test_select(self, context: bpy.types.Context, location):
        return -1

    def draw_select(self, context: bpy.types.Context, select_id):
        self._do_draw(context, select_id=select_id)

    def setup(self):
        pass

    def exit(self, context, cancel):
        context.area.header_text_set(None)


class ZUV_PT_GizmoDrawProperties(bpy.types.Panel):
    bl_idname = "ZUV_PT_GizmoDrawProperties"
    bl_label = "Display Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 16

    def draw(self, context: bpy.types.Context):
        addon_prefs = get_prefs()
        layout = self.layout
        layout.use_property_split = True

        col = layout.column(align=True)

        p_scene = context.scene
        col.prop(p_scene.zen_uv.ui, 'use_draw_overlay_sync')

        col.prop(addon_prefs, 'FinishedColor')
        col.prop(addon_prefs, 'UnFinishedColor')

        layout.prop(addon_prefs, 'FlippedColor')
        layout.prop(addon_prefs, 'ExcludedColor')
        layout.prop(addon_prefs, 'UvNoSyncColor')

        col = layout.column(align=True)
        col.prop(addon_prefs, 'draw_label_font_size')
        col.prop(addon_prefs, 'draw_label_font_color')

        b_is_UV = context.space_data.type == 'IMAGE_EDITOR'
        if not b_is_UV:
            layout.prop(p_scene.zen_uv.ui, 'draw_stretched_modal')

        # col = layout.column(align=True)
        # addon_prefs.td_draw.draw(col, context)
