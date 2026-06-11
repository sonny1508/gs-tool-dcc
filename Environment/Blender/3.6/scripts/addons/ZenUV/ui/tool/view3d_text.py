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

# Copyright 2023, Alex Zhornyak

import bpy
import blf
from bpy_extras import view3d_utils

from mathutils import Vector

from .view3d_base import gizmo_trims, ZuvGizmoBase

from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils
from ZenUV.utils.vlog import Log
from ZenUV.utils.simple_geometry import TextRect
from ZenUV.utils.inject import is_modal_procedure


class ZUV_GGT_2DVToolText(bpy.types.GizmoGroup):
    bl_idname = "ZUV_GGT_2DVToolText"
    bl_label = "Tool Text"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT', 'SHOW_MODAL_ALL'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return ZuvGizmoBase.poll_by_edit_mesh(context)

    def setup(self, context: bpy.types.Context):
        self.mpr_text = self.gizmos.new("VIEW2D_GT_zenuv_tool_text")
        self.mpr_text.color = 0.0, 1.0, 0.0
        self.mpr_text.alpha = 1.0
        self.mpr_text.color_highlight = 0, 1.0, 1.0
        self.mpr_text.alpha_highlight = 1
        self.mpr_text.use_draw_value = True
        self.mpr_text.use_draw_scale = False
        self.mpr_text.use_select_background = False
        self.mpr_text.use_event_handle_all = False
        self.mpr_text.use_grab_cursor = False
        self.mpr_text.hide_select = True
        self.mpr_text.hide = False


class VIEW2D_GT_zenuv_tool_text(bpy.types.Gizmo):
    bl_idname = "VIEW2D_GT_zenuv_tool_text"
    bl_target_properties = ()

    __slots__ = (
        "handled_rects"
    )

    def _do_draw(self, context: bpy.types.Context, select_id=None):
        addon_prefs = get_prefs()
        p_scene = context.scene
        p_tool_props = p_scene.zen_uv.ui.view3d_tool

        b_is_image_editor = context.space_data.type == 'IMAGE_EDITOR'
        b_is_screen = p_tool_props.enable_screen_selector

        b_is_text_displayed = (
            addon_prefs.trimsheet.display_name if b_is_image_editor else
            addon_prefs.trimsheet.display_name or b_is_screen
        )

        if b_is_text_displayed:
            ui_scale = context.preferences.view.ui_scale

            i_font_size = addon_prefs.trimsheet.font_size * ui_scale
            i_default_size = addon_prefs.trimsheet.font_size * ui_scale
            if addon_prefs.trimsheet.scale_font:
                if b_is_image_editor:
                    i_font_size *= context.space_data.zoom[0]
                else:
                    if not b_is_screen:
                        d_ratio = 75 / context.region_data.perspective_matrix.inverted_safe().median_scale
                        i_font_size *= d_ratio
                        i_font_size = min(max(i_font_size, 2), i_default_size * 2)

            p_trim_items = gizmo_trims.get(context.area.as_pointer(), {})

            rgn = context.region
            rgn3d = context.space_data.region_3d

            p_trimsheet = ZuvTrimsheetUtils.getTrimsheet(context)
            if p_trimsheet:

                try:
                    if len(p_trimsheet) == len(p_trim_items):
                        try:
                            blf.size(0, i_font_size, bpy.context.preferences.system.dpi)
                        except TypeError:
                            blf.size(0, round(i_font_size), bpy.context.preferences.system.dpi)

                        p_handled_rects = set()

                        p_trim_names = []

                        b_is_modal = is_modal_procedure(context)
                        if b_is_modal:
                            p_trim_names = [it_r.name for it_r in self.handled_rects]

                        for k, v in p_trim_items.items():
                            p_gizmo: bpy.types.Gizmo = v
                            if p_gizmo.hide:
                                continue

                            p_trim = p_trimsheet[k]

                            v_pos = p_gizmo.matrix_world @ Vector.Fill(3, 0.0)
                            v_pos2d = view3d_utils.location_3d_to_region_2d(rgn, rgn3d, v_pos, default=Vector())

                            text = p_trim.name

                            t_width, t_height = blf.dimensions(0, text)

                            b_trim_active = p_trim.is_active()
                            pos_x = v_pos2d.x + 10 if b_trim_active else v_pos2d.x - t_width / 2
                            pos_y = v_pos2d.y - t_height / 2

                            d_intersect_ratio = 0.7
                            r_text = TextRect(
                                left=round(pos_x),
                                top=round(pos_y + t_height * d_intersect_ratio),
                                right=round(pos_x + t_width * d_intersect_ratio),
                                bottom=round(pos_y),
                                name=text,
                                color=(*p_trim.color, 1))

                            if b_is_modal:
                                if text in p_trim_names:
                                    p_handled_rects.add(r_text)
                            else:
                                if p_gizmo.is_highlight or p_trim.is_active() or not any(r_text.intersects(it_r) for it_r in p_handled_rects):
                                    p_handled_rects.add(r_text)

                        for it_r in p_handled_rects:
                            it_r.draw_text()

                        self.handled_rects = p_handled_rects
                except Exception as e:
                    pass  # Do not remove!

    def draw(self, context: bpy.types.Context):
        self._do_draw(context)

    def test_select(self, context: bpy.types.Context, location):
        return -1

    def draw_select(self, context: bpy.types.Context, select_id):
        self._do_draw(context, select_id=select_id)

    def setup(self):
        if not hasattr(self, "handled_rects"):
            self.handled_rects = set()

    def exit(self, context, cancel):
        context.area.header_text_set(None)
