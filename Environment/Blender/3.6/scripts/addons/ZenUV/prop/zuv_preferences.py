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

""" Zen UV Addon Properties module """
import os
import sys
from json import loads, dumps
from timeit import default_timer as timer

import bpy
import addon_utils
from bpy.types import AddonPreferences
from bpy.props import (
    BoolProperty,
    FloatProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
    FloatVectorProperty,
    PointerProperty
)
from ZenUV.zen_checker.files import update_files_info, load_checker_image, get_checker_previews
from ZenUV.utils.messages import zen_message
from ZenUV.zen_checker.checker import (
    zen_checker_image_update,
    get_materials_with_overrider)
from ZenUV.ico import icon_get
from ZenUV.ui.labels import ZuvLabels
from ZenUV.zen_checker.zen_checker_labels import ZCheckerLabels as label
from ZenUV.utils.generic import get_padding_in_pct, get_padding_in_px

from ZenUV.ui.keymap_manager import draw_keymaps
from ZenUV.utils.clib.lib_init import StackSolver, get_zenlib_name, get_zenlib_version, is_zenlib_present

from ZenUV.sticky_uv_editor.stk_uv_props import UVEditorSettings, draw_sticky_editor_settings

from ZenUV.ops.zen_unwrap.props import ZUV_ZenUnwrapOpAddonProps
from ZenUV.ops.trimsheets.trimsheet_props import ZuvTrimsheetProps

from ZenUV.ops.trimsheets.trimsheet_labels import TrimSheetLabels as TrsLabels

from ZenUV.utils.blender_zen_utils import update_areas_in_all_screens, ZenPolls

from ZenUV.prop.demo_examples import ZUV_DemoExampleProps
from ZenUV.prop.user_script_props import ZUV_UserScriptProps
from ZenUV.prop.td_draw_props import ZUV_TexelDensityDrawProps


resolutions_x = []
resolutions_y = []
values_x = []
values_y = []


_CACHE_ADDON_VERSION = None


def get_addon_version():
    global _CACHE_ADDON_VERSION
    if _CACHE_ADDON_VERSION is None:
        for addon in addon_utils.modules():
            if addon.bl_info['name'] == 'Zen UV':
                ver = addon.bl_info['version']
                _CACHE_ADDON_VERSION = '%i.%i.%i' % (ver[0], ver[1], ver[2])
                break

    return _CACHE_ADDON_VERSION if _CACHE_ADDON_VERSION else '0.0.0'


def get_name():
    """Get Name"""
    return os.path.basename(get_path())


def get_path():
    """Get the path of Addon"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def draw_panels_enabler(context: bpy.types.Context, layout: bpy.types.UILayout, viewport, is_combo=False):
    from .common import uv_enblr

    addon_prefs = get_prefs()

    if is_combo:
        op = layout.operator(
            'ops.zenuv_show_prefs',
            text=addon_prefs.bl_rna.properties[f'dock_{viewport}_panels_enabled'].name.replace('Enable', 'Disable'),
            icon='NONE', emboss=True)
        op.tabs = 'PANELS'
        box = layout.box()
        box.prop(addon_prefs.combo_panel, 'use_shift_select')
        box.prop(addon_prefs.combo_panel, 'combo_popup_width')

        # Temporary
        col = box.column(align=True)
        col.prop(addon_prefs.combo_panel, 'selector_style', expand=True)
    else:
        b1 = layout.box()
        b1.prop(addon_prefs, f'dock_{viewport}_panels_enabled')

    box = layout.box()

    for pref, switch in uv_enblr.items():
        p_type = switch.get(viewport, None)
        b_enabled = p_type is not None
        p_row = box.split(factor=0.5, align=True)
        p_row.enabled = b_enabled

        r1 = p_row.row(align=True)
        r1.alignment = 'LEFT'
        r1.active = getattr(addon_prefs, f'dock_{viewport}_panels_enabled')

        p_float_prop = getattr(addon_prefs, f'float_{viewport}_panels')
        p_prop_name = p_float_prop.bl_rna.properties[pref].name

        if b_enabled:
            p_panel_type = getattr(bpy.types, p_type)
            p_dock_prop = getattr(addon_prefs, f'dock_{viewport}_panels')
            if pref == 'enable_pt_preferences':
                r1.label(text=p_prop_name, icon='LOCKED')
            else:
                r1.prop(p_dock_prop, pref)

            enb = p_row.row(align=True)
            enb.alignment = 'RIGHT'

            if p_panel_type:
                if hasattr(p_panel_type, 'combo_poll'):
                    b_active = p_panel_type.combo_poll(context)
                    p_row.active = b_active

            enb.prop(p_float_prop, pref, text='Floating')
        else:
            r1.label(text=p_prop_name, icon='CHECKBOX_DEHLT')


def draw_alt_commands(self):
    box = self.layout.box()
    addon_prefs = self
    box.label(text="Pie Menu commands that will be executed in combination with the SHIFT key.")
    row = box.row(align=True)
    row.prop(addon_prefs, 's8', icon="TRIA_UP")
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's8'
    row = box.row(align=True)
    row.prop(addon_prefs, 's9')
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's9'
    row.enabled = False
    row = box.row(align=True)
    row.prop(addon_prefs, 's6', icon="TRIA_RIGHT")
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's6'
    row = box.row(align=True)
    row.prop(addon_prefs, 's3')
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's3'
    row = box.row(align=True)
    row.prop(addon_prefs, 's2', icon="TRIA_DOWN")
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's2'
    row = box.row(align=True)
    row.prop(addon_prefs, 's1')
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's1'
    row = box.row(align=True)
    row.prop(addon_prefs, 's4', icon="TRIA_LEFT")
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's4'
    row = box.row(align=True)
    row.prop(addon_prefs, 's7')
    row.operator("zenuv.search_operator", icon="COLLAPSEMENU", text="").sector = 's7'


class ZuvPanelEnableGroup(bpy.types.PropertyGroup):

    def get_context(self):
        p_context = self.get('_context', None)
        if p_context is None:

            p_context = {}

            addon_prefs = get_prefs()

            if addon_prefs.dock_UV_panels == self:
                p_context['is_floating'] = False
                p_context['mode'] = 'UV'
            elif addon_prefs.dock_VIEW_3D_panels == self:
                p_context['is_floating'] = False
                p_context['mode'] = 'VIEW_3D'
            elif addon_prefs.float_UV_panels == self:
                p_context['is_floating'] = True
                p_context['mode'] = 'UV'
            elif addon_prefs.float_VIEW_3D_panels == self:
                p_context['is_floating'] = True
                p_context['mode'] = 'VIEW_3D'

            self['_context'] = p_context
        return p_context

    def get_val(self, prop_name):
        from .common import uv_enblr

        p_context = self.get_context()
        b_is_floating = p_context['is_floating']
        s_context_mode = p_context['mode']

        p_default = False if b_is_floating else uv_enblr[prop_name][s_context_mode] is not None
        if p_default and not b_is_floating:
            if prop_name == 'enable_pt_preferences':
                return True

        return self.get(prop_name, p_default)

    def set_val(self, prop_name, value):
        p_old_val = self.get_val(prop_name)
        if p_old_val != value:
            self[prop_name] = value
            update_areas_in_all_screens(bpy.context)

    enable_pt_adv_uv_map: BoolProperty(
        name=ZuvLabels.PT_ADV_UV_MAPS_LABEL,
        get=lambda self: self.get_val('enable_pt_adv_uv_map'),
        set=lambda self, value: self.set_val('enable_pt_adv_uv_map', value))
    enable_pt_seam_group: BoolProperty(
        name=ZuvLabels.PT_SEAMS_GROUP_LABEL,
        get=lambda self: self.get_val('enable_pt_seam_group'),
        set=lambda self, value: self.set_val('enable_pt_seam_group', value))
    enable_pt_unwrap: BoolProperty(
        name=ZuvLabels.PANEL_UNWRAP_LABEL,
        get=lambda self: self.get_val('enable_pt_unwrap'),
        set=lambda self, value: self.set_val('enable_pt_unwrap', value))
    enable_pt_select: BoolProperty(
        name=ZuvLabels.PANEL_SELECT_LABEL,
        get=lambda self: self.get_val('enable_pt_select'),
        set=lambda self, value: self.set_val('enable_pt_select', value))
    enable_pt_pack: BoolProperty(
        name=ZuvLabels.PANEL_PACK_LABEL,
        get=lambda self: self.get_val('enable_pt_pack'),
        set=lambda self, value: self.set_val('enable_pt_pack', value))
    enable_pt_checker_map: BoolProperty(
        name=ZuvLabels.PANEL_CHECKER_LABEL,
        get=lambda self: self.get_val('enable_pt_checker_map'),
        set=lambda self, value: self.set_val('enable_pt_checker_map', value))
    enable_pt_texel_density: BoolProperty(
        name=ZuvLabels.TEXEL_DENSITY_LABEL,
        get=lambda self: self.get_val('enable_pt_texel_density'),
        set=lambda self, value: self.set_val('enable_pt_texel_density', value))
    enable_pt_transform: BoolProperty(
        name=ZuvLabels.PANEL_TRANSFORM_LABEL,
        get=lambda self: self.get_val('enable_pt_transform'),
        set=lambda self, value: self.set_val('enable_pt_transform', value))
    enable_pt_help: BoolProperty(
        name=ZuvLabels.PANEL_HELP_LABEL,
        get=lambda self: self.get_val('enable_pt_help'),
        set=lambda self, value: self.set_val('enable_pt_help', value))
    enable_pt_stack: BoolProperty(
        name=ZuvLabels.PANEL_STACK_LABEL,
        get=lambda self: self.get_val('enable_pt_stack'),
        set=lambda self, value: self.set_val('enable_pt_stack', value))
    enable_pt_preferences: BoolProperty(
        name=ZuvLabels.PANEL_PREFERENCES_LABEL,
        get=lambda self: self.get_val('enable_pt_preferences'),
        set=lambda self, value: self.set_val('enable_pt_preferences', value))
    enable_pt_trimsheet: BoolProperty(
        name=TrsLabels.PANEL_TRSH_LABEL,
        get=lambda self: self.get_val('enable_pt_trimsheet'),
        set=lambda self, value: self.set_val('enable_pt_trimsheet', value))


class ZuvComboSettings(bpy.types.PropertyGroup):
    expanded: bpy.props.StringProperty(
        name='Expanded Combo Panels',
        default=''
    )

    pinned: bpy.props.StringProperty(
        name='Pinned Combo Panels',
        default=''
    )

    use_shift_select: bpy.props.BoolProperty(
        name='Multiselect With Shift',
        description='If set multiple docked panels are selected with shift',
        default=True
    )

    combo_popup_width: bpy.props.IntProperty(
        name='Popup Panel Width',
        description='If set multiple docked panels are selected with shift',
        min=100,
        max=1200,
        subtype='PIXEL',
        default=300
    )

    combo_VIEW_3D_edit_mode: bpy.props.EnumProperty(
        name='Combo Edit Mode',
        description='Selected panel in view 3d edit mesh combo mode',
        items=[
            ('DATA_PT_uv_texture_advanced', 'Adv UV Maps', ''),
            ('ZUV_PT_ZenSeamsGroups', 'Seam Groups', ''),
            ('ZUV_PT_Unwrap', 'Unwrap', ''),
            ('ZUV_PT_Select', 'Select', ''),
            ('ZUV_PT_3DV_Transform', 'Transform', ''),
            ('ZUV_PT_3DV_Trimsheet', 'Trimsheet', ''),
            ('ZUV_PT_Stack', 'Stack', ''),
            ('ZUV_PT_Texel_Density', 'Texel Density', ''),
            ('ZUV_PT_Checker', 'UV Checker', ''),
            ('ZUV_PT_Pack', 'Pack', ''),
            ('ZUV_PT_Preferences', 'Preferences', ''),
            ('ZUV_PT_Help', 'Help', '')
        ],
        options={'ENUM_FLAG'},
        default={'DATA_PT_uv_texture_advanced'}
    )

    combo_UV_edit_mode: bpy.props.EnumProperty(
        name='Combo Edit Mode',
        description='Selected panel in view 3d edit mesh combo mode',
        items=[
            ('DATA_PT_UVL_uv_texture_advanced', 'Adv UV Maps', ''),
            ('ZUV_PT_UVL_Unwrap', 'Unwrap', ''),
            ('ZUV_PT_UVL_Select', 'Select', ''),
            ('ZUV_PT_UVL_Transform', 'Transform', ''),
            ('ZUV_PT_UVL_Trimsheet', 'Trimsheet', ''),
            ('ZUV_PT_UVL_Stack', 'Stack', ''),
            ('ZUV_PT_UVL_Texel_Density', 'Texel Density', ''),
            ('ZUV_PT_Checker_UVL', 'UV Checker', ''),
            ('ZUV_PT_UVL_Pack', 'Pack', ''),
            ('ZUV_PT_UVL_Preferences', 'Preferences', ''),
            ('ZUV_PT_UVL_Help', 'Help', '')
        ],
        options={'ENUM_FLAG'},
        default={'DATA_PT_UVL_uv_texture_advanced'}
    )

    selector_style: bpy.props.EnumProperty(
        name='Selector Style',
        description='Dock panel selector style',
        items=[
            ('NO_BACK', 'No background 1', ''),
            ('NO_BACK_2', 'No background 2', ''),
            ('BL_1', 'Blender Style 1', ''),
            ('BL_2', 'Blender Style 2', ''),
            ('BL_INV_1', 'Blender Invert Style 1', ''),
            ('BL_INV_2', 'Blender Invert Style 2', ''),
        ],
        default='NO_BACK'
    )


class ZUV_AddonPreferences(AddonPreferences):

    bl_idname = ZuvLabels.ADDON_NAME  # "ZenUV"

    t_CONTEXT_PANEL_MAP = {
        "IMAGE_EDITOR": 'UV',
        "VIEW_3D": "VIEW_3D"
    }

    def draw(self, context):
        layout = self.layout
        self.draw_update_note(layout)

        row = layout.row()
        row.prop(self, "tabs", expand=True)

        if self.tabs == 'KEYMAP':
            layout.prop(self, "zen_key_modifier")

            draw_keymaps(context, layout)

        # if self.tabs == 'PIE_MENU':
        #     draw_alt_commands(self)
        if self.tabs == 'PANELS':
            layout = self.layout
            pie_box = layout.box()
            pie_box.label(text="Pie Menu: ")
            pie_box.prop(self, "pie_assist")
            pie_box.prop(self, "pie_assist_font_size")
            row = layout.row()
            col = row.column()
            # col.alignment = 'RIGHT'
            # draw_uv_panels_enabler(self, context, row)
            title_box = col.box()
            title_box.label(text="UV Editor", icon="UV")
            draw_panels_enabler(context, col, "UV")
            col = row.column()
            title_box = col.box()
            title_box.label(text="3D Viewport", icon="VIEW3D")
            draw_panels_enabler(context, col, "VIEW_3D")

        if self.tabs == 'HELP':
            box = layout.box()
            box.operator(
                "wm.url_open",
                text=ZuvLabels.PANEL_HELP_DOC_LABEL,
                icon="HELP"
            ).url = ZenPolls.doc_url
            box.operator(
                "wm.url_open",
                text=ZuvLabels.PANEL_HELP_DISCORD_LABEL,
                icon_value=icon_get(ZuvLabels.PANEL_HELP_DISCORD_ICO)
            ).url = ZuvLabels.PANEL_HELP_DISCORD_LINK

            box = layout.box()
            self.demo.draw(box, context)

        if self.tabs == 'MODULES':
            self.draw_modules_tab(layout)
            self.user_script.draw(layout, context)
        if self.tabs == 'STK_UV_EDITOR':
            draw_sticky_editor_settings(self, context)

        box_products = layout.box()
        box_products.label(text='Zen Add-ons')
        box_products.operator(
            "wm.url_open",
            text=ZuvLabels.PREF_ZEN_SETS_URL_DESC,
            icon_value=icon_get(ZuvLabels.AddonZenSets)
        ).url = ZuvLabels.PREF_ZEN_SETS_URL_LINK
        box_products.operator(
            "wm.url_open",
            text=ZuvLabels.PREF_ZEN_UV_BBQ_URL_DESC,
            icon_value=icon_get(ZuvLabels.AddonZenBBQ)
        ).url = ZuvLabels.PREF_ZEN_UV_BBQ_URL_LINK
        box_products.operator(
            "wm.url_open",
            text=ZuvLabels.PREF_ZEN_UV_CHECKER_URL_DESC,
            icon_value=icon_get(ZuvLabels.AddonZenChecker)
        ).url = ZuvLabels.PREF_ZEN_UV_CHECKER_URL_LINK
        box_products.operator(
            "wm.url_open",
            text=ZuvLabels.PREF_ZEN_UV_TOPMOST_URL_DESC,
            icon='WINDOW',
        ).url = ZuvLabels.PREF_ZEN_UV_TOPMOST_URL_LINK

    def draw_modules_tab(self, layout):
        box = layout.box()
        if not StackSolver():
            b_is_zenlib_present = is_zenlib_present()
            row = box.row()
            row.alert = True
            row.label(text=ZuvLabels.CLIB_NAME + (": not installed" if not b_is_zenlib_present else ": not registered"))
            box.operator(
                    "wm.url_open",
                    text=ZuvLabels.PREF_ZEN_CORE_URL_DESC,

                ).url = ZuvLabels.PREF_ZEN_CORE_URL_LINK

            s_label = ("Register " if b_is_zenlib_present else "Install ") + ZuvLabels.CLIB_NAME
            box.operator("view3d.zenuv_install_library", text=s_label)
        else:
            result = get_zenlib_version()

            box.label(text=ZuvLabels.CLIB_NAME + f": {result[0]}.{result[1]}.{result[2]} ({get_zenlib_name()})" + ' is installed.')
            box.operator("uv.zenuv_unregister_library")
            box.label(text=ZuvLabels.UPDATE_WARNING_UNREGISTER)

    def draw_update_note(self, layout):
        upd_box = layout.box()
        # col.label(text=ZuvLabels.UPDATE_MESSAGE_SHORT)
        if StackSolver():
            # col = upd_box.column()
            # col.alert = True
            upd_box.label(text='NOTE', icon='ERROR')
            mes_box = upd_box.box()
            mes_box.label(text=ZuvLabels.UPDATE_WARNING_MAIN_01)
            mes_box.label(text=ZuvLabels.UPDATE_WARNING_MAIN_02)
        row = upd_box.row()
        row.operator("uv.zenuv_update_addon")

    def pack_eng_callback(self, context):
        return (
            ("BLDR", ZuvLabels.PREF_PACK_ENGINE_BLDR_LABEL, ZuvLabels.PREF_PACK_ENGINE_BLDR_DESC),
            ("UVP", ZuvLabels.PREF_PACK_ENGINE_UVP_LABEL, ZuvLabels.PREF_PACK_ENGINE_UVP_DESC),
            ("UVPACKER", ZuvLabels.PREF_PACK_ENGINE_UVPACKER_LABEL, ZuvLabels.PREF_PACK_ENGINE_UVPACKER_DESC)
            # ("CUSTOM", ZuvLabels.PREF_PACK_CUSTOM_LABEL, ZuvLabels.PREF_PACK_CUSTOM_DESC)
        )

    def mark_update_function(self, context):
        if not self.markSharpEdges and not self.markSeamEdges:
            zen_message(
                context,
                message=ZuvLabels.PREF_MARK_WARN_MES,
                title=ZuvLabels.PREF_MARK_WARN_TITLE)

    def update_margin_px(self, context):
        self.margin = get_padding_in_pct(context, self.margin_px)

    def update_margin_show_in_px(self, context):
        if self.margin_show_in_px:
            self.margin_px = get_padding_in_px(context, self.margin)
        else:
            self.margin = get_padding_in_pct(context, self.margin_px)

    def image_size_update_function(self, context):
        if self.td_im_size_presets.isdigit():
            self.TD_TextureSizeX = self.TD_TextureSizeY = int(self.td_im_size_presets)
        self.margin = get_padding_in_pct(context, self.margin_px)

    op_zen_unwrap_props: bpy.props.PointerProperty(type=ZUV_ZenUnwrapOpAddonProps)

    pie_assist: bpy.props.BoolProperty(
        name=ZuvLabels.PROP_DISPLAY_PIE_ASSIST_LABEL,
        description=ZuvLabels.PROP_DISPLAY_PIE_ASSIST_DESC,
        default=True
    )

    pie_assist_font_size: IntProperty(
        name=ZuvLabels.PROP_PIE_ASSIST_FONT_SIZE_LABEL,
        description=ZuvLabels.PROP_PIE_ASSIST_FONT_SIZE_DESC,
        min=8,
        max=16,
        default=11,
    )

    # Stack Preferences
    StackedColor: bpy.props.FloatVectorProperty(
        name=ZuvLabels.PREF_ST_STACKED_COLOR_LABEL,
        description=ZuvLabels.PREF_ST_STACKED_COLOR_DESC,
        subtype='COLOR',
        default=[0.325, 0.65, 0.0, 0.35],
        size=4,
        min=0,
        max=1
    )

    st_stack_mode: EnumProperty(
        name=ZuvLabels.PREF_ST_STACK_MODE_LABEL,
        description=ZuvLabels.PREF_ST_STACK_MODE_DESC,
        items=[
            (
                'ALL',
                ZuvLabels.PREF_ST_STACK_MODE_ALL_LABEL,
                ZuvLabels.PREF_ST_STACK_MODE_ALL_DESC
            ),
            (
                'SELECTED',
                ZuvLabels.PREF_ST_STACK_MODE_SEL_LABEL,
                ZuvLabels.PREF_ST_STACK_MODE_SEL_DESC
            ),
            (
                'SIMPLE',
                ZuvLabels.PREF_ST_STACK_MODE_SIMPLE_LABEL,
                ZuvLabels.PREF_ST_STACK_MODE_SIMPLE_DESC
            ),
        ],
        default="ALL"
    )

    unstack_direction: FloatVectorProperty(
        name="Direction",
        size=2,
        default=(1.0, 0.0),
        subtype='XYZ'
    )

    stack_offset: FloatVectorProperty(
        name="Direction",
        size=2,
        default=(0.0, 0.0),
        subtype='XYZ'
    )

    stackMoveOnly: BoolProperty(
        name=ZuvLabels.PREF_STACK_MOVE_ONLY_LABEL,
        default=False,
        description=ZuvLabels.PREF_STACK_MOVE_ONLY_DESC,
        )

    dock_VIEW_3D_panels: bpy.props.PointerProperty(
        name='Docked View3D Panels', type=ZuvPanelEnableGroup)

    dock_UV_panels: bpy.props.PointerProperty(
        name='Docked UV Panels', type=ZuvPanelEnableGroup)

    dock_VIEW_3D_panels_enabled: bpy.props.BoolProperty(
        name="Enable Docked View3D Panel",
        default=True
    )

    dock_UV_panels_enabled: bpy.props.BoolProperty(
        name="Enable Docked UV Panel",
        default=True
    )

    float_VIEW_3D_panels: bpy.props.PointerProperty(
        name='Floating View3D Panels', type=ZuvPanelEnableGroup)

    float_UV_panels: bpy.props.PointerProperty(
        name='Floating UV Panels', type=ZuvPanelEnableGroup)

    combo_panel: bpy.props.PointerProperty(name='Combo Panel Settings', type=ZuvComboSettings)

    # Alt Commands Preferences
    s8: StringProperty(name="Sector 8", default='')
    s9: StringProperty(name="Sector 9", default='')
    s6: StringProperty(name="Sector 6", default='')
    s3: StringProperty(name="Sector 3", default='')
    s2: StringProperty(name="Sector 2", default='')
    s1: StringProperty(name="Sector 1", default='')
    s4: StringProperty(name="Sector 4", default='')
    s7: StringProperty(name="Sector 7", default='bpy.ops.uv.zenuv_select_similar()')

    operator: StringProperty(
        name="Operator",
        default=''
    )

    # Zen UV Preferences
    hops_uv_activate: BoolProperty(
        name=ZuvLabels.HOPS_UV_ACTIVATE_LABEL,
        description=ZuvLabels.HOPS_UV_ACTIVATE_DESC,
        default=False,
    )
    hops_uv_context: BoolProperty(
        name=ZuvLabels.HOPS_UV_CONTEXT_LABEL,
        description=ZuvLabels.HOPS_UV_CONTEXT_DESC,
        default=True,
    )

    def on_tabs_update(self, context: bpy.types.Context):
        if self.tabs == 'HELP':

            from .demo_examples import ZUV_OT_DemoExamplesUpdate

            d_last_update = bpy.app.driver_namespace.get(ZUV_OT_DemoExamplesUpdate.LITERAL_LAST_UPDATE, 0)
            if d_last_update == 0 or timer() - d_last_update > 60000:
                bpy.ops.wm.zuv_demo_examples_update('INVOKE_DEFAULT', True)

    tabs: EnumProperty(
        items=[
            ("KEYMAP", "Keymap", ""),
            ("PANELS", "Panels", ""),
            # ("PIE_MENU", "Pie Menu", ""),
            ("MODULES", "Modules", ""),
            ("STK_UV_EDITOR", "Sticky UV Editor", ""),
            ("HELP", "Help", ""),
        ],
        default="MODULES",
        update=on_tabs_update
    )
    # Zen UV UI Key modifier
    zen_key_modifier: EnumProperty(
        items=[
            ("ALT", "Alt", "Alt"),
            ("CTRL", "Ctrl", "Ctrl"),
            ("SHIFT", "Shift", "Shift")
        ],
        default="ALT",
        description=ZuvLabels.ZEN_MODIFIER_KEY_DESC,
        name=ZuvLabels.ZEN_MODIFIER_KEY_LABEL,

    )
    # Tabs for Sticky UV Editor Setup
    stk_tabs: EnumProperty(
        items=[
            ("GENERAL", "General", ""),
            ("OVERLAY", "Overlay", ""),
            ("VIEW", "View", ""),
            ("ABOUT", "About", "")
        ],
        default="GENERAL"
    )

    useGlobalMarkSettings: BoolProperty(
        name=ZuvLabels.PREF_USE_GLOBAL_MARK_LABEL,
        description=ZuvLabels.PREF_USE_GLOBAL_MARK_DESC,
        default=True
    )

    markSharpEdges: BoolProperty(
        name=ZuvLabels.PREF_MARK_SHARP_EDGES_LABEL,
        description=ZuvLabels.PREF_MARK_SHARP_EDGES_DESC,
        default=False,
        update=mark_update_function)

    markSeamEdges: BoolProperty(
        name=ZuvLabels.PREF_MARK_SEAM_EDGES_LABEL,
        description=ZuvLabels.PREF_MARK_SEAM_EDGES_DESC,
        default=True,
        update=mark_update_function)

    # MarkUnwrapped: BoolProperty(
    #     name=ZuvLabels.PREF_AUTO_SEAMS_WITH_UNWRAP_LABEL,
    #     description=ZuvLabels.PREF_AUTO_SEAMS_WITH_UNWRAP_DESC,
    #     default=True)

    # packAfUnwrap: BoolProperty(
    #     name=ZuvLabels.PREF_PACK_AF_UNWRAP_LABEL,
    #     description=ZuvLabels.PREF_PACK_AF_UNWRAP_DESC,
    #     default=True)

    # Quadrify Props ------------------------------------------------

    # autoPinQuadrified: BoolProperty(
    #     name=ZuvLabels.PREF_AUTO_PIN_QUADRIFIED_LABEL,
    #     description=ZuvLabels.PREF_AUTO_PIN_QUADRIFIED_DESC,
    #     default=False)

    # quadrifyOrientToWorld: BoolProperty(
    #     name=ZuvLabels.PREF_ORIENT_TO_WORLD_QUADRIFY_LABEL,
    #     description=ZuvLabels.PREF_ORIENT_TO_WORLD_QUADRIFY_DESC,
    #     default=False)

    # mark_borders: BoolProperty(
    #     name=ZuvLabels.PREF_UPD_SEAMS_AF_QUADRIFY_LABEL,
    #     description=ZuvLabels.PREF_UPD_SEAMS_AF_QUADRIFY_DESC,
    #     default=True)

    # QuadrifyBySelected: BoolProperty(
    #     name=ZuvLabels.PREF_QUADRIFY_BY_SELECTED_EDGES_LABEL,
    #     description=ZuvLabels.PREF_QUADRIFY_BY_SELECTED_EDGES_DESC,
    #     default=True)

    # packAfQuadrify: BoolProperty(
    #     name=ZuvLabels.PREF_PACK_AF_QUADRIFY_LABEL,
    #     description=ZuvLabels.PREF_PACK_AF_QUADRIFY_DESC,
    #     default=False)

    # Quadrify Props END --------------------------------------------

    packEngine: EnumProperty(
        items=pack_eng_callback,
        name=ZuvLabels.PREF_PACK_ENGINE_LABEL,
        description=ZuvLabels.PREF_PACK_ENGINE_DESC,
        default=None
        )

    # customEngine: StringProperty(
    #     default="bpy.ops.uvpackeroperator.packbtn()",
    #     description="Custom Pack Command"
    # )

    averageBeforePack: BoolProperty(
        name=ZuvLabels.PREF_AVERAGE_BEFORE_PACK_LABEL,
        description=ZuvLabels.PREF_AVERAGE_BEFORE_PACK_DESC,
        default=True)

    rotateOnPack: BoolProperty(
        name=ZuvLabels.PREF_ROTATE_ON_PACK_LABEL,
        description=ZuvLabels.PREF_ROTATE_ON_PACK_DESC,
        default=True)

    packInTrim: BoolProperty(
        name='Pack in Trim',
        description='Use Active Trim instead of UV Area',
        default=False)

    packSelectedIslOnly: BoolProperty(
        name='Pack Selected Islands',
        description='Pack only selected Islands',
        default=False)

    # keepStacked: BoolProperty(
    #     name=ZuvLabels.PREF_KEEP_STACKED_LABEL,
    #     description=ZuvLabels.PREF_KEEP_STACKED_DESC,
    #     default=True)

    def update_lock_ovelap_enbl(self, context):
        if self.lock_overlapping_mode == '0':
            self.lock_overlapping_enable = False
        else:
            self.lock_overlapping_enable = True

    lock_overlapping_mode: EnumProperty(
        items=[
            ('0', 'Disabled', ZuvLabels.LOCK_OVERLAPPING_MODE_DISABLED_DESC),
            ('1', 'Any Part', ZuvLabels.LOCK_OVERLAPPING_MODE_ANY_PART_DESC),
            ('2', 'Exact', ZuvLabels.LOCK_OVERLAPPING_MODE_EXACT_DESC)
        ],
        name=ZuvLabels.LOCK_OVERLAPPING_MODE_NAME,
        description=ZuvLabels.LOCK_OVERLAPPING_MODE_DESC,
        update=update_lock_ovelap_enbl
    )

    lock_overlapping_enable: BoolProperty(
        name=ZuvLabels.LOCK_OVERLAPPING_ENABLE_NAME,
        description=ZuvLabels.LOCK_OVERLAPPING_ENABLE_DESC,
    )

    packFixedScale: BoolProperty(
        name=ZuvLabels.PREF_FIXED_SCALE_LABEL,
        description=ZuvLabels.PREF_FIXED_SCALE_DESC,
        default=False)

    autoFitUV: BoolProperty(
        name=ZuvLabels.PREF_AUTO_FIT_UV_LABEL,
        description=ZuvLabels.PREF_AUTO_FIT_UV_DESC,
        default=False)

    # unwrapAutoSorting: BoolProperty(
    #     name=ZuvLabels.PREF_ZEN_UNWRAP_SORT_ISLANDS_LABEL,
    #     description=ZuvLabels.PREF_ZEN_UNWRAP_SORT_ISLANDS_DESC,
    #     default=False)

    sortAutoSorting: BoolProperty(
        name=ZuvLabels.PREF_ZEN_SORT_ISLANDS_LABEL,
        description=ZuvLabels.PREF_ZEN_SORT_ISLANDS_DESC,
        default=True)

    autoPinnedAsFinished: BoolProperty(
        name=ZuvLabels.PREF_AUTO_PINNED_AS_FINISHED_LABEL,
        description=ZuvLabels.PREF_AUTO_PINNED_AS_FINISHED_DESC,
        default=True)

    autoFinishedToPinned: BoolProperty(
        name=ZuvLabels.PREF_AUTO_FINISHED_TO_PINNED_LABEL,
        description=ZuvLabels.PREF_AUTO_FINISHED_TO_PINNED_DESC,
        default=False)

    # autoTagFinished: BoolProperty(
    #     name=ZuvLabels.PREF_AUTO_TAG_FINISHED_LABEL,
    #     description=ZuvLabels.PREF_AUTO_TAG_FINISHED_DESC,
    #     default=False)

    margin: FloatProperty(
        name=ZuvLabels.PREF_MARGIN_LABEL,
        description=ZuvLabels.PREF_MARGIN_DESC,
        min=0.0,
        default=0.005,
        precision=3
    )

    margin_px: IntProperty(
        name=ZuvLabels.PREF_MARGIN_PX_LABEL,
        description=ZuvLabels.PREF_MARGIN_PX_DESC,
        min=0,
        default=5,
        update=update_margin_px
    )

    margin_show_in_px: BoolProperty(
        name=ZuvLabels.PREF_MARGIN_SHOW_PX_LABEL,
        description=ZuvLabels.PREF_MARGIN_SHOW_PX_DESC,
        default=True,
        update=update_margin_show_in_px
    )

    # ProcessingMode: BoolProperty(
    #     name=ZuvLabels.PREF_WORK_ON_SELECTED_LABEL,
    #     description=ZuvLabels.PREF_WORK_ON_SELECTED_DESC,
    #     default=False)

    UnwrapMethod: EnumProperty(
        items=[
            ("ANGLE_BASED",
                ZuvLabels.PREF_UNWRAP_METHOD_ANGLE_LABEL,
                ZuvLabels.PREF_UNWRAP_METHOD_ANGLE_DESC),
            ("CONFORMAL",
                ZuvLabels.PREF_UNWRAP_METHOD_CONFORMAL_LABEL,
                ZuvLabels.PREF_UNWRAP_METHOD_CONFORMAL_DESC)],
        default="CONFORMAL")

    PinColor: bpy.props.FloatVectorProperty(
        name=ZuvLabels.PIN_UV_ISLAND_ISLAND_COLOR_NAME,
        description=ZuvLabels.PIN_UV_ISLAND_ISLAND_COLOR_DESC,
        subtype='COLOR',
        default=[0.25, 0.4, 0.4, 1],
        size=4,
        min=0,
        max=1)

    FlippedColor: bpy.props.FloatVectorProperty(
        name='Flipped Color',
        description='Flipped islands viewport display color',
        subtype='COLOR',
        default=[0, 1, 0, 0.1],
        size=4,
        min=0,
        max=1)

    UvNoSyncColor: bpy.props.FloatVectorProperty(
        name='UV No Sync Color',
        description='Color of mesh elements that are selected in UV no sync mode',
        subtype='COLOR',
        default=[1, 1, 0, 0.5],
        size=4,
        min=0,
        max=1)

    FinishedColor: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TAG_FINISHED_COLOR_NAME,
        description=ZuvLabels.TAG_FINISHED_COLOR_DESC,
        subtype='COLOR',
        default=[0, 0.5, 0, 0.4],
        size=4,
        min=0,
        max=1)

    ExcludedColor: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TAG_EXCLUDED_COLOR_NAME,
        description=ZuvLabels.TAG_EXCLUDED_COLOR_DESC,
        subtype='COLOR',
        default=[0.97, 0.026, 0.5, 0.4],
        size=4,
        min=0,
        max=1)

    UnFinishedColor: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TAG_UNFINISHED_COLOR_NAME,
        description=ZuvLabels.TAG_UNFINISHED_COLOR_DESC,
        subtype='COLOR',
        default=[0.937, 0.448, 0.735, 0.2],
        size=4,
        min=0,
        max=1)

    RandomizePinColor: bpy.props.BoolProperty(
        name=ZuvLabels.PIN_UV_ISLAND_RAND_COLOR_NAME,
        description=ZuvLabels.PIN_UV_ISLAND_RAND_COLOR_DESC,
        default=True)

    TexelDensity: FloatProperty(
        name=ZuvLabels.PREF_TEXEL_DENSITY_LABEL,
        description=ZuvLabels.PREF_TEXEL_DENSITY_DESC,
        min=0.001,
        default=1024.0,
        precision=2
    )

    td_checker: FloatProperty(
        name=ZuvLabels.PREF_TD_CHECKER_LABEL,
        description=ZuvLabels.PREF_TD_CHECKER_DESC,
        min=0.001,
        default=47.59,
        precision=2
    )

    td_set_mode: EnumProperty(
        name=ZuvLabels.PREF_TD_SET_MODE_LABEL,
        description=ZuvLabels.PREF_TD_SET_MODE_DESC,
        items=[
            (
                'island',
                ZuvLabels.PREF_SET_PER_ISLAND_LABEL,
                ZuvLabels.PREF_SET_PER_ISLAND_DESC
            ),
            (
                'overall',
                ZuvLabels.PREF_SET_OVERALL_LABEL,
                ZuvLabels.PREF_SET_OVERALL_DESC
            ),
        ],
        default="overall"
    )

    UVCoverage: FloatProperty(
        name=ZuvLabels.PREF_UV_COVERAGE_LABEL,
        description=ZuvLabels.PREF_UV_DENSITY_DESC,
        min=0.001,
        default=1.0,
        precision=3
    )

    # td_unit: EnumProperty(
    #     name=ZuvLabels.PREF_UNITS_LABEL,
    #     description=ZuvLabels.PREF_UNITS_DESC,
    #     items=[
    #         ('100000', 'km', 'KILOMETERS'),
    #         ('100', 'm', 'METERS'),
    #         ('1', 'cm', 'CENTIMETERS'),
    #         ('0.1', 'mm', 'MILLIMETERS'),
    #         ('0.0001', 'um', 'MICROMETERS'),
    #         ('160934', 'mil', 'MILES'),
    #         ('30.48', 'ft', 'FEET'),
    #         ('2.54', 'in', 'INCHES'),
    #         ('0.00254', 'th', 'THOU')
    #     ],
    #     default="100"
    # )

    td_unit: EnumProperty(
        name=ZuvLabels.PREF_UNITS_LABEL,
        description=ZuvLabels.PREF_UNITS_DESC,
        items=[
            ('km', 'km', 'KILOMETERS'),
            ('m', 'm', 'METERS'),
            ('cm', 'cm', 'CENTIMETERS'),
            ('mm', 'mm', 'MILLIMETERS'),
            ('um', 'um', 'MICROMETERS'),
            ('mil', 'mil', 'MILES'),
            ('ft', 'ft', 'FEET'),
            ('in', 'in', 'INCHES'),
            ('th', 'th', 'THOU')
        ],
        default="m"
    )

    TD_TextureSizeX: IntProperty(
        name=ZuvLabels.PREF_TD_TEXTURE_SIZE_LABEL,
        description=ZuvLabels.PREF_TD_TEXTURE_SIZE_DESC,
        min=1,
        default=1024)

    TD_TextureSizeY: IntProperty(
        name=ZuvLabels.PREF_TD_TEXTURE_SIZE_LABEL,
        description=ZuvLabels.PREF_TD_TEXTURE_SIZE_DESC,
        min=1,
        default=1024)

    td_im_size_presets: EnumProperty(
        name=ZuvLabels.PREF_IMAGE_SIZE_PRESETS_LABEL,
        description=ZuvLabels.PREF_IMAGE_SIZE_PRESETS_DESC,
        items=[
            ('16', '16', ''),
            ('32', '32', ''),
            ('64', '64', ''),
            ('128', '128', ''),
            ('256', '256', ''),
            ('512', '512', ''),
            ('1024', '1024', ''),
            ('2048', '2048', ''),
            ('4096', '4096', ''),
            ('8192', '8192', ''),
            ('Custom', 'Custom', '')
        ],
        default='1024',
        update=image_size_update_function)

    td_color_equal: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TD_COLOR_EQUAL_LABEL,
        description=ZuvLabels.TD_COLOR_EQUAL_DESC,
        subtype='COLOR',
        default=[0.0, 1.0, 0.0],
        size=3,
        min=0,
        max=1
    )

    td_color_less: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TD_COLOR_LESS_LABEL,
        description=ZuvLabels.TD_COLOR_LESS_DESC,
        subtype='COLOR',
        default=[0.0, 0.0, 1.0],
        size=3,
        min=0,
        max=1
    )

    td_color_over: bpy.props.FloatVectorProperty(
        name=ZuvLabels.TD_COLOR_OVER_LABEL,
        description=ZuvLabels.TD_COLOR_OVER_DESC,
        subtype='COLOR',
        default=[1.0, 0.0, 0.0],
        size=3,
        min=0,
        max=1
    )

    trimsheet: bpy.props.PointerProperty(type=ZuvTrimsheetProps)

    use_progress_bar: bpy.props.BoolProperty(
        name='Display Progress Bar',
        description='Display progress bar window',
        default=True)

    # autoActivateUVSync: bpy.props.BoolProperty(
    #     name=ZuvLabels.PREF_AUTO_ACTIVATE_UV_SYNC_LABEL,
    #     description=ZuvLabels.PREF_AUTO_ACTIVATE_UV_SYNC_DESC,
    #     default=True)

# Zen UV Checker Preferences
    def get_files_dict(self, context):
        try:
            if self.files_dict == "":
                self.files_dict = dumps(update_files_info(self.assetspath))
            files_dict = loads(self.files_dict)
            return files_dict
        except Exception:
            print("Warning!", sys.exc_info()[0], "occurred.")
            self.files_dict = dumps(update_files_info(self.assetspath))
            return None

    def get_x_res_list(self, context):
        """ Get resolutions list for files from files_dict """
        files_dict = self.get_files_dict(context)
        if files_dict:
            # Update info in resolutions_x list
            values_x.clear()
            for image in files_dict:
                value = files_dict[image]["res_x"]
                if value not in values_x:
                    values_x.append(value)
            values_x.sort()
            identifier = 0
            resolutions_x.clear()
            for value in values_x:
                resolutions_x.append((str(value), str(value), "", identifier))
                identifier += 1
            return resolutions_x
        return [('None', 'None', '', 0), ]

    def get_y_res_list(self, context):
        """ Fills resolutions_y depend on current value of SizeX """
        files_dict = self.get_files_dict(context)
        if files_dict:
            res_x = self.SizesX
            if res_x and res_x.isdigit():
                res_x = int(res_x)
                # If axes locked - return same value as Resolution X
                if self.lock_axes:
                    return [(str(res_x), str(res_x), "", 0)]
                identifier = 0
                values_y.clear()
                resolutions_y.clear()
                for image in files_dict:
                    value = files_dict[image]["res_y"]
                    if files_dict[image]["res_x"] == res_x and value not in values_y:
                        values_y.append(value)
                        resolutions_y.append((str(value), str(value), "", identifier))
                        identifier += 1
            if resolutions_y:
                return resolutions_y
        return [('None', 'None', '', 0), ]

    def zchecker_image_items(self, context):
        files_dict = self.get_files_dict(context)
        if files_dict:
            files = []
            identifier = 0
            # If filter disabled - return all images from dict
            if not self.chk_rez_filter:
                for image in files_dict:
                    icon_id = 'BLANK1'
                    try:
                        icon_id = get_checker_previews()[image].icon_id
                    except Exception as e:
                        print(str(e))
                    files.append((image, image, "", icon_id, identifier))
                    identifier += 1
                return files

            res_x = self.SizesX
            res_y = self.SizesY
            if res_x and res_y and res_x.isdigit() and res_y.isdigit():
                res_x = int(res_x)
                res_y = int(res_y)
                values = []
                for image in files_dict:
                    if files_dict[image]["res_x"] == res_x \
                            and files_dict[image]["res_y"] == res_y \
                            and image not in values:
                        values.append(image)

                        icon_id = 'BLANK1'
                        try:
                            icon_id = get_checker_previews()[image].icon_id
                        except Exception as e:
                            print(str(e))

                        if self.chk_orient_filter:
                            if "orient" in image:
                                files.append((image, image, "", icon_id, identifier))
                                identifier += 1
                        else:
                            files.append((image, image, "", icon_id, identifier))
                            identifier += 1
            if files:
                return files
        return [('None', 'None', '', 0), ]

    def dynamic_update_function(self, context):
        if self.dynamic_update and get_materials_with_overrider(bpy.data.materials):
            self.checker_presets_update_function(context)

    def update_x_res(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        addon_prefs["SizesY"] = 0
        addon_prefs["ZenCheckerImages"] = 0
        self.dynamic_update_function(context)

    def update_orient_switch(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        if self.chk_orient_filter:
            addon_prefs["SizesX"] = 1
            addon_prefs["SizesY"] = 0
        addon_prefs["ZenCheckerImages"] = 0
        self.dynamic_update_function(context)

    def update_y_res(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        addon_prefs["ZenCheckerImages"] = 0
        self.dynamic_update_function(context)

    def dynamic_update_function_overall(self, context):
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        addon_prefs["SizesY"] = 0
        addon_prefs["ZenCheckerImages"] = 0
        if self.dynamic_update:
            materials_with_overrider = get_materials_with_overrider(bpy.data.materials)
            # print("Mats with overrider in bpy.data: ", materials_with_overrider)
            if materials_with_overrider:
                self.checker_presets_update_function(context)

    # def show_checker_in_uv_layout(self, context):
    #     materials_with_overrider = get_materials_with_overrider(get_materials_from_objects(context, context.selected_objects))
    #     if materials_with_overrider:
    #         image = bpy.data.images.get(self.ZenCheckerPresets)
    #         # update_image_in_uv_layout(context, image)

    def checker_presets_update_function(self, context):
        image = bpy.data.images.get(self.ZenCheckerImages)
        if image:
            zen_checker_image_update(context, image)
        else:
            # print("Image not Loaded. Load image ", self.ZenCheckerPresets)
            image = load_checker_image(context, self.ZenCheckerImages)
            if image:
                zen_checker_image_update(context, image)
        # self.show_checker_in_uv_layout(context)

    def update_assetspath(self, context):
        self.files_dict = dumps(update_files_info(self.assetspath))

    assetspath: StringProperty(
        name=label.PROP_ASSET_PATH,
        subtype='DIR_PATH',
        default=os.path.join(get_path(), "images"),
        update=update_assetspath
    )

    files_dict: StringProperty(
        name="Zen Checker Files Dict",
        default=""
    )

    dynamic_update: BoolProperty(
        name=label.PROP_DYNAMIC_UPDATE_LABEL,
        description=label.PROP_DYNAMIC_UPDATE_DESC,
        default=True
    )

    ZenCheckerPresets: EnumProperty(
        name=label.CHECKER_PRESETS_LABEL,
        description=label.CHECKER_PRESETS_DESC,
        items=[
            ('Zen-UV-512-colour.png', 'Zen Color 512x512', '', 1),
            ('Zen-UV-1K-colour.png', 'Zen Color 1024x1024', '', 2),
            ('Zen-UV-2K-colour.png', 'Zen Color 2048x2048', '', 3),
            ('Zen-UV-4K-colour.png', 'Zen Color 4096x4096', '', 4),
            ('Zen-UV-512-mono.png', 'Zen Mono 512x512', '', 5),
            ('Zen-UV-1K-mono.png', 'Zen Mono 1024x1024', '', 6),
            ('Zen-UV-2K-mono.png', 'Zen Mono 2048x2048', '', 7),
            ('Zen-UV-4K-mono.png', 'Zen Mono 4096x4096', '', 8)],
        default="Zen-UV-1K-colour.png",
        update=checker_presets_update_function
    )

    # ShowCheckerInUVLayout: bpy.props.BoolProperty(
    #     name=label.CHECKER_SHOW_IN_UV_LABEL,
    #     description=label.CHECKER_SHOW_IN_UV_DESC,
    #     default=True,
    #     update=show_checker_in_uv_layout
    # )

    lock_axes: BoolProperty(
        name=label.PROP_LOCK_AXES_LABEL,
        description=label.PROP_LOCK_AXES_DESC,
        default=True,
        update=update_x_res
    )

    chk_rez_filter: BoolProperty(
        name=label.PROP_RES_FILTER_LABEL,
        description=label.PROP_RES_FILTER_DESC,
        default=False,
        update=update_x_res
    )

    chk_orient_filter: BoolProperty(
        name=label.PROP_ORIENT_FILTER_LABEL,
        description=label.PROP_ORIENT_FILTER_DESC,
        default=False,
        update=update_orient_switch
    )

    SizesX: EnumProperty(
        name=label.PROP_TEXTURE_X_LABEL,
        description=label.PROP_TEXTURE_X_DESC,
        items=get_x_res_list,
        update=update_x_res
    )

    SizesY: EnumProperty(
        name=label.PROP_TEXTURE_Y_LABEL,
        description=label.PROP_TEXTURE_Y_DESC,
        items=get_y_res_list,
        update=update_y_res
    )

    ZenCheckerImages: EnumProperty(
        name=label.PROP_CHK_IMAGES_LABEL,
        items=zchecker_image_items,
        update=checker_presets_update_function
    )

    use_zensets: BoolProperty(
        name="Use Zen Sets to Highlight Errors",
        description="Use Zen Sets to create Zen Sets Groups with Mesh Errors",
        default=False)

    # Sticky UV Editor Properties
    uv_editor_side: EnumProperty(
        name="UV Editor Side",
        description="3D Viewport area side where to open UV Editor",
        items={('LEFT', "Left",
                "Open UV Editor on the left side of 3D Viewport area", 0),
               ('RIGHT', "Right",
                "Open UV Editor on the right side of 3D Viewport area", 1)},
        default='LEFT')
    show_ui_button: BoolProperty(
        name="Show Overlay Button",
        description="Show overlay button on corresponding side of 3D Viewport",
        default=True)
    remember_uv_editor_settings: BoolProperty(
        name="Remember UV Editor Settings",
        description="Remember changes made in UV Editor area",
        default=True)

    StkUvEdProps: PointerProperty(type=UVEditorSettings)

    view_mode: EnumProperty(
        name="View Mode",
        description="Adjust UV Editor view when open",
        items={('DISABLE', "Disable",
                "Do not modify the view", 0),
               ('FRAME_ALL', "Frame All UVs",
                "View all UVs", 1),
               ('FRAME_SELECTED', "Frame Selected",
                "View all selected UVs", 2),
               ('FRAME_ALL_FIT', "Frame All UDIMs",
                "View all UDIMs", 3)},
        default='DISABLE')
    use_uv_select_sync: BoolProperty(
        name="UV Sync Selection",
        description="Keep UV an edit mode mesh selection in sync",
        default=False)

    stk_ed_button_v_position: FloatProperty(
        name="Button Vertical Position %",
        description="The vertical position of the button in percentages.",
        min=2.0,
        max=90.0,
        default=50,
        precision=1
    )

    stk_ed_button_h_position: FloatProperty(
        name="Button Horizontal Position %",
        description="The horizontal position of the button in percentages.",
        min=0.0,
        max=40.0,
        default=0.0,
        precision=1
    )

    # MUST BE Integer to support previous BLF versions
    draw_label_font_size: bpy.props.IntProperty(
        name='Font Size',
        description='Font size of drawing mode label',
        subtype='PIXEL',
        min=4,
        max=40,
        default=10
    )

    draw_label_font_color: bpy.props.FloatVectorProperty(
        name='Font Color',
        description='Font color of drawing mode label',
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0,
        max=1)

    demo: bpy.props.PointerProperty(
        name='Demo',
        type=ZUV_DemoExampleProps
    )

    user_script: bpy.props.PointerProperty(
        name='User Script',
        type=ZUV_UserScriptProps
    )

    td_draw: bpy.props.PointerProperty(
        name='Texel Density Draw',
        type=ZUV_TexelDensityDrawProps
    )


def get_prefs() -> ZUV_AddonPreferences:
    """ Return Zen UV Properties obj """
    return bpy.context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
