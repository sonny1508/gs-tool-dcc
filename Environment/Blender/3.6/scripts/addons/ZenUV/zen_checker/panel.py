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

""" Zen Checker Main Panel """

import bpy
from bpy.types import Panel

# import addon_utils
from ZenUV.zen_checker.zen_checker_labels import ZCheckerLabels as label
from ZenUV.ico import icon_get
from ZenUV.zen_checker import checker
from ZenUV.ui.labels import ZuvLabels
from ZenUV.prop.common import get_combo_panel_order


class ZUV_PT_Checker(Panel):
    bl_idname = "ZUV_PT_Checker"
    bl_label = label.PANEL_CHECKER_LABEL
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    bl_category = "Zen UV"
    bl_order = get_combo_panel_order('VIEW_3D', 'ZUV_PT_Checker')

    @classmethod
    def get_icon(cls):
        return icon_get('pn_CheckerMap')

    @classmethod
    def poll(cls, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        return addon_prefs.float_VIEW_3D_panels.enable_pt_checker_map

    def draw(self, context):
        draw_checker_panel_3D(self, context)


class ZUV_PT_Checker_UVL(Panel):
    bl_idname = "ZUV_PT_Checker_UVL"
    bl_label = label.PANEL_CHECKER_LABEL
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = 'UI'
    bl_category = "Zen UV"
    bl_order = get_combo_panel_order('UV', 'ZUV_PT_Checker_UVL')

    get_icon = ZUV_PT_Checker.get_icon

    @classmethod
    def poll(cls, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        return addon_prefs.float_UV_panels.enable_pt_checker_map

    def draw(self, context):
        draw_checker_panel_UV(self, context)


def draw_filtration_sys(addon_prefs, layout):
    col = layout.column(align=True)
    row = col.row(align=True)
    col = row.column(align=True)
    row.prop(addon_prefs, "SizesX", text="", index=0)
    col = row.column(align=True)
    if addon_prefs.lock_axes:
        lock_icon = "LOCKED"
    else:
        lock_icon = "UNLOCKED"
    col.prop(addon_prefs, "lock_axes", icon=lock_icon, icon_only=True)
    col = row.column(align=True)
    col.enabled = not addon_prefs.lock_axes
    col.prop(addon_prefs, "SizesY", text="", index=0)
    row.prop(addon_prefs, "chk_orient_filter", icon="EVENT_O", icon_only=True)


class ZenUVCheckerPopover(Panel):
    """ Zen Checker Properties Popover """
    bl_idname = "ZUV_CH_PT_Properties"
    bl_label = "Zen Checker Properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        layout = self.layout
        layout.label(text=label.CHECKER_PANEL_LABEL)

        col = layout.column(align=True)
        row = col.row()
        col = row.column(align=True)
        col.prop(addon_prefs, "assetspath", text="")
        col = row.column(align=True)
        col.operator("ops.zenuv_checker_reset_path", text="Reset Folder")

        layout.operator("view3d.zenuv_checker_append_checker_file", icon="FILEBROWSER")
        layout.operator("view3d.zenuv_checker_collect_images", icon="FILE_REFRESH")
        layout.prop(addon_prefs, "dynamic_update", )
        layout.operator("view3d.zenuv_checker_open_editor")
        layout.operator("view3d.zenuv_checker_reset")


def draw_checker_panel_UV(self, context: bpy.types.Context):
    addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
    layout = self.layout  # type: bpy.types.UILayout
    col = layout.column(align=True)
    row = col.row(align=True)
    checker.ZUVChecker_OT_CheckerToggle.draw_toggled(row, context)
    row.popover(panel="ZUV_CH_PT_Properties", text="", icon="PREFERENCES")

    # Filtration System
    if addon_prefs.chk_rez_filter:
        draw_filtration_sys(addon_prefs, layout)

    row = layout.row(align=True)
    row.prop(context.scene.zen_uv, "tex_checker_interpolation", icon_only=True, icon="NODE_TEXTURE")
    row.prop(addon_prefs, "ZenCheckerImages", index=0)

    row.prop(addon_prefs, "chk_rez_filter", icon="FILTER", icon_only=True)


def draw_checker_panel_3D(self, context: bpy.types.Context):
    addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
    layout = self.layout  # type: bpy.types.UILayout

    col = layout.column(align=True)
    row = col.row(align=True)
    checker.ZUVChecker_OT_CheckerToggle.draw_toggled(row, context)
    row.popover(panel="ZUV_CH_PT_Properties", text="", icon="PREFERENCES")
    col.operator("view3d.zenuv_checker_remove")

    # Filtration System
    if addon_prefs.chk_rez_filter:
        draw_filtration_sys(addon_prefs, layout)

    row = layout.row(align=True)

    row.prop(context.scene.zen_uv, "tex_checker_interpolation", icon_only=True, icon="NODE_TEXTURE")
    row.prop(addon_prefs, "ZenCheckerImages", index=0)
    row.prop(addon_prefs, "chk_rez_filter", icon="FILTER", icon_only=True)
    if context.area is not None and context.area.type == 'VIEW_3D' and len(context.area.spaces) and context.area.spaces[0].shading.type in {'RENDERED', 'MATERIAL'}:
        layout.prop(context.scene.zen_uv, "tex_checker_tiling")
        layout.prop(context.scene.zen_uv, "tex_checker_offset")
