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
from mathutils import Color, Matrix, Quaternion
import gpu
from gpu_extras.batch import batch_for_shader

from .custom_gizmo_shapes import CustomShapes
from .view3d_base import ZuvGizmoBase

from ZenUV.ops.event_service import get_blender_event
from ZenUV.utils.constants import UV_AREA_BBOX
from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils
from ZenUV.ops.transform_sys.transform_utils.tr_utils import TrSpaceMode


shader_line = gpu.shader.from_builtin('3D_POLYLINE_UNIFORM_COLOR')


class ZuvTrimCageGizmo(bpy.types.Gizmo):
    bl_idname = "VIEW3D_GT_zenuv_trim_cage"
    bl_target_properties = ()

    __slots__ = (
        "dimensions",
        "custom_shape_border",
        "custom_dimensions",
    )

    def _do_draw(self, context: bpy.types.Context, select_id=None):
        self._check_main_shape()

        was_color = self.color.copy()

        was_alpha = self.alpha

        self.alpha = 1.0
        p_color = Color(self.color)
        p_color.v = min(1.0, p_color.v * 1.5)
        self.color = p_color[:]

        _, shader = self.custom_shape_border

        region = context.region
        imm_viewport = (region.width, region.height)

        shader.bind()
        shader.uniform_float('viewportSize', imm_viewport)

        gpu.state.blend_set('ALPHA')

        self.color = (0, 0, 0)
        self.alpha = 1.0
        shader.bind()
        shader.uniform_float('lineWidth', 6)
        self.draw_custom_shape(self.custom_shape_border, select_id=select_id)

        self.color = p_color[:] if select_id is None else (0, 0, 1)
        self.alpha = 1
        shader.bind()
        shader.uniform_float('lineWidth', 1)
        self.draw_custom_shape(self.custom_shape_border, select_id=select_id)

        self.alpha = was_alpha
        self.color = was_color

        gpu.state.blend_set('NONE')

    def draw(self, context: bpy.types.Context):
        self._do_draw(context)

    def draw_select(self, context: bpy.types.Context, select_id):
        self._do_draw(context, select_id=select_id)

    def _build_shape(self):
        custom_shape_verts = (
            (-0.5, -0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5),
            (0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5)
        )

        if self.dimensions != (0, 0, 0):
            custom_shape_verts = [(co[0] * self.dimensions[0], co[1] * self.dimensions[1], 0) for co in custom_shape_verts]

        self.custom_shape_border = [None, shader_line]

        self.custom_shape_border[0] = batch_for_shader(
            shader_line, 'LINE_LOOP',
            {"pos": custom_shape_verts})
        self.custom_shape_border[0].program_set(shader_line)

    def _check_main_shape(self):
        if self.custom_dimensions != self.dimensions:
            self.custom_dimensions = self.dimensions

            self._build_shape()

    def setup(self):
        self.line_width = 3
        if not hasattr(self, "custom_shape"):
            self.custom_dimensions = (0, 0, 0)
            self.dimensions = (0, 0, 0)

            self._build_shape()

    def exit(self, context, cancel):
        context.area.header_text_set(None)


class ZuvTrimSelectGizmo(bpy.types.Gizmo):
    bl_idname = "VIEW3D_GT_zenuv_trim_select"
    bl_target_properties = ()

    __slots__ = (
        "dimensions",
        "custom_shape",
        "custom_shape_border",
        "custom_dimensions",

        "fill_color",
        "fill_alpha",
        "border_color",
        "border_alpha",
        "text_color",
    )

    def _do_draw(self, context: bpy.types.Context, select_id=None):
        self._check_main_shape()

        self.color = self.fill_color
        self.color_highlight = self.fill_color
        self.alpha = 0 if self.hide_select else self.fill_alpha
        self.alpha_highlight = 0 if self.hide_select else 0.6

        self.draw_custom_shape(self.custom_shape, select_id=select_id)

        # if self.is_highlight:
        #     return

        _, shader = self.custom_shape_border

        region = context.region
        imm_viewport = (region.width, region.height)

        shader.bind()
        shader.uniform_float('viewportSize', imm_viewport)

        gpu.state.blend_set('ALPHA')

        if not self.is_highlight:
            self.color = (0, 0, 0)
            self.alpha = 1.0
            shader.bind()
            shader.uniform_float('lineWidth', 6)
            self.draw_custom_shape(self.custom_shape_border, select_id=select_id)

        self.color = self.border_color
        self.color_highlight = self.border_color
        self.alpha = self.border_alpha
        self.alpha_highlight = 1.0
        shader.bind()
        shader.uniform_float('lineWidth', 3 if self.is_highlight else 1)
        self.draw_custom_shape(self.custom_shape_border, select_id=select_id)

        gpu.state.blend_set('NONE')

    def draw(self, context: bpy.types.Context):
        self._do_draw(context)

    def draw_select(self, context: bpy.types.Context, select_id):
        self._do_draw(context, select_id=select_id)

    def _build_shape(self):
        custom_shape_verts = (
            (-0.5, -0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5),
            (0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, -0.5, -0.5)
        )

        if self.dimensions != (0, 0, 0):
            custom_shape_verts = [(co[0] * self.dimensions[0], co[1] * self.dimensions[1], 0) for co in custom_shape_verts]

        self.custom_shape = self.new_custom_shape('TRIS', custom_shape_verts)

        self.custom_shape_border = [None, shader_line]

        self.custom_shape_border[0] = batch_for_shader(
            shader_line, 'LINE_LOOP',
            {"pos": custom_shape_verts})
        self.custom_shape_border[0].program_set(shader_line)

    def _check_main_shape(self):
        if self.custom_dimensions != self.dimensions:
            self.custom_dimensions = self.dimensions

            self._build_shape()

    def setup(self):
        self.line_width = 3
        if not hasattr(self, "custom_shape"):
            self.custom_dimensions = (0, 0, 0)
            self.dimensions = (0, 0, 0)

            self.fill_color = (1, 1, 1)
            self.fill_alpha = 0.0
            self.border_color = (1, 1, 1)
            self.border_alpha = 1.0
            self.text_color = (1, 1, 1)

            self._build_shape()

    def exit(self, context, cancel):
        context.area.header_text_set(None)


class ZuvTrimAlignGizmo(bpy.types.Gizmo):
    bl_idname = "VIEW3D_GT_zenuv_trim_align"
    bl_target_properties = ()

    __slots__ = (
        "custom_shape",
        "custom_shape_border",
        "direction",
        "is_pivot"
    )

    def draw(self, context):
        was_color = self.color.copy()
        was_alpha = self.alpha

        self.alpha = 1

        self.color = (0, 0, 0)

        _, shader = self.custom_shape_border

        region = context.region
        imm_viewport = (region.width, region.height)

        shader.bind()
        shader.uniform_float('viewportSize', imm_viewport)

        gpu.state.blend_set('ALPHA')

        self.color = (0, 0, 0)

        shader.bind()
        shader.uniform_float('lineWidth', 2)
        self.draw_custom_shape(self.custom_shape_border, matrix=self.matrix_world @ Matrix.Diagonal((0.5, 0.5, 0.0)).to_4x4())

        self.color = (0, 1, 0) if self.direction == 'bl' else was_color

        self.draw_preset_box(self.matrix_world @ Matrix.Diagonal((0.2, 0.2, 0.0)).to_4x4())

        if self.is_pivot:
            self.color = (0, 0, 0)
            self.draw_preset_box(self.matrix_world @ Matrix.Diagonal((0.15, 0.15, 0.0)).to_4x4())

        self.color = was_color
        self.alpha = was_alpha

        self.draw_custom_shape(self.custom_shape)

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.custom_shape, select_id=select_id)

    def setup(self):
        if not hasattr(self, "custom_shape"):
            custom_shape_verts = (
                (-0.5, -0.5, 0), (-0.5, 0.5, 0), (0.5, 0.5, 0),
                (0.5, 0.5, 0), (0.5, -0.5, 0), (-0.5, -0.5, 0)
            )
            self.custom_shape = self.new_custom_shape('TRIS', custom_shape_verts)

            self.custom_shape_border = [None, shader_line]

            self.custom_shape_border[0] = batch_for_shader(
                shader_line, 'LINE_LOOP',
                {"pos": custom_shape_verts})
            self.custom_shape_border[0].program_set(shader_line)

            self.direction = 'cen'
            self.is_pivot = False

    def exit(self, context, cancel):
        context.area.header_text_set(None)


class ZuvTrimFitFlipGizmo(bpy.types.Gizmo):
    bl_idname = "VIEW3D_GT_zenuv_trim_fitflip"
    bl_target_properties = ()

    __slots__ = (
        "custom_shape_fit_op",
        "custom_shape_fit_2_op",

        "custom_shape_flip_op",
        "custom_shape_flip_2_op",

        "custom_shape_rot_op",
        "custom_shape_rot_2_op",

        "custom_shape_orient_op",

        "direction"
    )

    def draw_outline(self, context, p_shape, p_mtx):
        region = context.region
        imm_viewport = (region.width, region.height)

        was_color = self.color.copy()

        self.color = (0, 0, 0)
        self.alpha = 0.99  # Do not change

        shader_line.bind()

        shader_line.uniform_float('viewportSize', imm_viewport)
        shader_line.uniform_float('lineWidth', 4)

        self.draw_custom_shape(p_shape, matrix=p_mtx)

        if self.direction == 'bl':
            self.color = (0, 1.0, 0)
            self.alpha = 1

        if p_shape == self.custom_shape_flip_op:
            self.draw_custom_shape(
                    self.custom_shape_flip_2_op,
                    matrix=p_mtx)

        if p_shape == self.custom_shape_rot_op:
            self.draw_custom_shape(
                    self.custom_shape_rot_2_op,
                    matrix=p_mtx)

        if p_shape == self.custom_shape_fit_op:
            self.draw_custom_shape(
                self.custom_shape_fit_2_op,
                matrix=p_mtx)

        self.alpha = 0.99  # Do not change
        self.color = was_color

        shader_line.bind()
        shader_line.uniform_float('lineWidth', 1)
        self.draw_custom_shape(p_shape, matrix=p_mtx)

    def draw(self, context):
        p_event_dict = get_blender_event()

        b_shift = p_event_dict.get('shift', False)
        b_ctrl = p_event_dict.get('ctrl', False)

        if b_shift and b_ctrl:
            if not self.direction == 'cen':
                self.draw_outline(
                    context, self.custom_shape_flip_op,
                    self.matrix_world @ Matrix.Diagonal((0.8, 0.8, 0)).to_4x4())
        elif b_shift:
            if not self.direction == 'cen':
                self.draw_outline(
                    context, self.custom_shape_fit_op,
                    self.matrix_world)
        elif b_ctrl:
            b_is_left_bottom = self.direction == 'bl'
            mtx_was = self.matrix_basis.copy()

            f_dir = TrSpaceMode(context).editor_direction
            if not b_is_left_bottom:
                f_dir *= -1

            self.matrix_basis @= Matrix.Diagonal((1.0, f_dir, 1.0)).to_4x4()

            if not self.direction == 'cen' and self.direction not in UV_AREA_BBOX.bbox_middle_handles:
                self.draw_outline(
                    context, self.custom_shape_rot_op,
                    self.matrix_world)
            if self.direction in UV_AREA_BBOX.bbox_middle_handles:

                # Black Box under Orient Markers
                was_color = self.color.copy()
                was_alpha = self.alpha
                self.color = (0, 0, 0)
                self.alpha = 1.0
                self.draw_preset_box(
                    self.matrix_world @ Matrix.Diagonal(
                        (0.5, 0.05, 0)).to_4x4())
                self.alpha = was_alpha
                self.color = was_color

                # Orient markers
                self.draw_outline(
                    context, self.custom_shape_orient_op,
                    self.matrix_world)

            self.matrix_basis = mtx_was

    @classmethod
    def get_direction_rotation_matrix(cls, p_direction) -> Matrix:
        dir_vec = (UV_AREA_BBOX().cen - getattr(UV_AREA_BBOX, p_direction))
        q = dir_vec.to_3d().to_track_quat('X', 'Z')  # type: Quaternion
        return q.to_matrix().to_4x4()

    def draw_select(self, context, select_id):
        pass

    def setup(self):
        if hasattr(self, "direction"):
            # 2-TWO WAY Flip Gizmo
            self.custom_shape_flip_op = [None, shader_line]
            self.custom_shape_flip_op[0] = batch_for_shader(
                shader_line, 'LINES',
                {"pos": CustomShapes.mirror_gizmo_lines})
            self.custom_shape_flip_op[0].program_set(shader_line)

            self.custom_shape_flip_2_op = self.new_custom_shape('TRIS', CustomShapes.mirror_gizmo_faces)

            # 1-ONE WAY Fit Gizmo
            self.custom_shape_fit_op = [None, shader_line]
            self.custom_shape_fit_op[0] = batch_for_shader(
                shader_line, 'LINES',
                {"pos": CustomShapes.one_way_arrow_lines})
            self.custom_shape_fit_op[0].program_set(shader_line)
            self.custom_shape_fit_2_op = self.new_custom_shape('TRIS', CustomShapes.one_way_arrow_faces)

            #  RADIAL Rotation Gizmo
            self.custom_shape_rot_op = [None, shader_line]
            self.custom_shape_rot_op[0] = batch_for_shader(
                shader_line, 'LINES',
                {"pos": CustomShapes.rotate_gizmo_lines})
            self.custom_shape_rot_op[0].program_set(shader_line)
            self.custom_shape_rot_2_op = self.new_custom_shape('TRIS', CustomShapes.rotate_gizmo_faces)

            # Rotation ORIENT
            self.custom_shape_orient_op = [None, shader_line]
            self.custom_shape_orient_op[0] = batch_for_shader(
                shader_line, 'LINES',
                {"pos": CustomShapes.orient_gizmo_lines})
            self.custom_shape_orient_op[0].program_set(shader_line)

    def exit(self, context, cancel):
        context.area.header_text_set(None)


class VIEW2D_GT_zenuv_trim_viewport_select(bpy.types.GizmoGroup):
    bl_idname = "VIEW2D_GT_zenuv_trim_viewport_select"
    bl_label = "Trim Viewport Selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SCALE'}

    def draw_prepare(self, context: bpy.types.Context):
        p_view = context.preferences.view
        ui_scale = p_view.ui_scale
        widget_size = 22 * ui_scale

        widget_height = 26 * ui_scale

        p_scene = context.scene
        p_tool_props = p_scene.zen_uv.ui.view3d_tool
        b_is_enabled = p_tool_props.enable_screen_selector
        if b_is_enabled:
            p_color = (
                Color((0.02, 0.68, 0.53))
                if p_tool_props.screen_position_locked else
                Color((120 / 255, 157 / 255, 231 / 255))
            )
            p_color_highlight = p_color.copy()
            p_color_highlight.v = 1
            self.foo_gizmo.color = p_color[:]
            self.foo_gizmo.color_highlight = p_color_highlight[:]
            self.foo_gizmo.alpha = 0.2
            self.foo_gizmo.alpha_highlight = 0.4
        else:
            self.foo_gizmo.color = 0.0, 0.0, 0.0
            self.foo_gizmo.color_highlight = 0.8, 0.8, 0.8

        i_add_y = 0
        if p_view.mini_axis_type == 'MINIMAL':
            i_add_y += p_view.mini_axis_size * 2 * ui_scale
        elif p_view.mini_axis_type == 'GIZMO':
            i_add_y += p_view.gizmo_size_navigate_v3d * ui_scale

        p_offsets = ZuvTrimsheetUtils.get_area_offsets(context.area)

        n_panel_width = p_offsets.get('right')
        base_position = context.region.width - n_panel_width - widget_size
        self.foo_gizmo.matrix_basis[0][3] = base_position

        self.foo_gizmo.matrix_basis[1][3] = (
            context.region.height - p_offsets.get('top') - widget_height * 7 - i_add_y)

    def setup(self, context):
        mpr = self.gizmos.new("GIZMO_GT_button_2d")
        mpr.show_drag = False
        mpr.icon = 'PRESET'
        mpr.draw_options = {'BACKDROP', 'OUTLINE'}

        mpr.color = 0.0, 0.0, 0.0
        mpr.alpha = 0.4
        mpr.color_highlight = 0.8, 0.8, 0.8
        mpr.alpha_highlight = 0.2

        mpr.scale_basis = (80 * 0.35) / 2  # Same as buttons defined in C
        _ = mpr.target_set_operator("view3d.tool_screen_selector")
        self.foo_gizmo = mpr

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return ZuvGizmoBase.poll_by_edit_mesh(context)
