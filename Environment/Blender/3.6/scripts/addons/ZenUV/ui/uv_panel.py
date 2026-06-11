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

""" Zen UV Panel In UV Layout """
import bpy
from ZenUV.utils.generic import ZUV_PANEL_CATEGORY, ZUV_REGION_TYPE
from ZenUV.ui.labels import ZuvLabels
from ZenUV.ico import icon_get
from ZenUV.prop.zuv_preferences import (
    get_prefs, draw_panels_enabler)
from ZenUV.prop.common import get_combo_panel_order, uv_enblr
from ZenUV.ui.panel_draws import (
    draw_select,
    draw_texel_density,
    draw_pack,
    draw_copy_paste,
    # draw_simple_stack,
    draw_stack,
    uv_draw_unwrap,
    draw_finished_section,
    draw_packer_props,
)
from ZenUV.ops.transform_sys.tr_ui import draw_transform_panel


class ZUV_PT_UVL_Preferences(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Preferences"
    bl_label = ZuvLabels.PANEL_PREFERENCES_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = get_combo_panel_order('UV', 'ZUV_PT_UVL_Preferences')

    # An empty panel that serves as a parent for other child panels.

    @classmethod
    def get_icon(cls):
        return icon_get('pn_Preferences')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        b_poll = addon_prefs.float_UV_panels.enable_pt_preferences
        if not b_poll:
            b_is_any_float = any([
                (val.get('UV') is not None and getattr(addon_prefs.float_UV_panels, key, False))
                for key, val in uv_enblr.items()])
            if not b_is_any_float:
                b_is_any_dock = addon_prefs.dock_UV_panels_enabled
                if not b_is_any_dock:
                    return True

        return b_poll

    @classmethod
    def do_draw(cls, layout: bpy.types.UILayout, context: bpy.types.Context, is_combo=False):
        layout.operator(
            'ops.zenuv_show_prefs',
            icon_value=icon_get(ZuvLabels.ADDON_ICO),
            text="Zen UV Keymaps").tabs = "KEYMAP"

    def draw(self, context):
        self.do_draw(self.layout, context, is_combo=False)

    @classmethod
    def combo_draw(cls, layout: bpy.types.UILayout, context: bpy.types.Context):
        cls.do_draw(layout, context, is_combo=True)


class DATA_PT_UVL_Panels_Switch(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_label = "Panels"
    bl_parent_id = "ZUV_PT_UVL_Preferences"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "DATA_PT_UVL_Panels_Switch"
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        draw_panels_enabler(context, layout, "UV")

    @classmethod
    def combo_draw(cls, layout: bpy.types.UILayout, context: bpy.types.Context):
        draw_panels_enabler(context, layout, "UV", is_combo=True)


class ZUV_PT_UVL_Transform(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Transform"
    bl_label = ZuvLabels.PANEL_TRANSFORM_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('UV', 'ZUV_PT_UVL_Transform')

    @classmethod
    def get_icon(cls):
        return icon_get('pn_Transform')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_UV_panels.enable_pt_transform and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_transform_panel(self, context)


class ZUV_PT_UVL_Texel_Density(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Texel_Density"
    bl_label = ZuvLabels.PANEL_TEXEL_DENSITY_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('UV', 'ZUV_PT_UVL_Texel_Density')

    @classmethod
    def get_icon(cls):
        return icon_get('pn_TD')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_UV_panels.enable_pt_texel_density and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_texel_density(self, context)


class ZUV_PT_UVL_Pack(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Pack"
    bl_label = ZuvLabels.PANEL_PACK_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('UV', 'ZUV_PT_UVL_Pack')

    @classmethod
    def get_icon(cls):
        return icon_get('pn_Pack')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_UV_panels.enable_pt_pack and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_pack(self, context)


class ZUV_PT_UVL_Stack(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Stack"
    bl_label = ZuvLabels.PANEL_STACK_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('UV', 'ZUV_PT_UVL_Stack')

    @classmethod
    def get_icon(cls):
        return icon_get('pn_Stack')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_UV_panels.enable_pt_stack and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_stack(self, context)
        draw_copy_paste(self, context)
        # draw_simple_stack(self, context)


class ZUV_PT_UVL_Unwrap(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Unwrap"
    bl_label = ZuvLabels.PANEL_UNWRAP_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('UV', 'ZUV_PT_UVL_Unwrap')

    @classmethod
    def get_icon(cls):
        return icon_get("pn_Unwrap")

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_UV_panels.enable_pt_unwrap and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        uv_draw_unwrap(self, context)


class ZUV_PT_UVL_Select(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Select"
    bl_label = ZuvLabels.PANEL_SELECT_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('UV', 'ZUV_PT_UVL_Select')

    @classmethod
    def get_icon(cls):
        return icon_get('pn_Select')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_UV_panels.enable_pt_select and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_select(self, context)


class SYSTEM_PT_Finished_UV(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_label = "Finished"
    bl_parent_id = "ZUV_PT_UVL_Unwrap"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "SYSTEM_PT_Finished_UV"
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_finished_section(self, context)


class PROPS_PT_UVL_Packer(bpy.types.Panel):
    bl_idname = "PROPS_PT_UVL_Packer"
    bl_space_type = "IMAGE_EDITOR"
    bl_label = "Pack Engine"
    bl_parent_id = "ZUV_PT_UVL_Pack"
    bl_region_type = ZUV_REGION_TYPE
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        draw_packer_props(self, context)


main_panel_uv_parented_panels = [
    SYSTEM_PT_Finished_UV,
    DATA_PT_UVL_Panels_Switch,
    PROPS_PT_UVL_Packer,
    # SYSTEM_PT_FitRegion_UV
]


if __name__ == '__main__':
    pass
