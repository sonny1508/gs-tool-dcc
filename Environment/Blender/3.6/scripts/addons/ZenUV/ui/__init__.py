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

""" Zen UV Init UI module """

import bpy
from bpy.utils import register_class, unregister_class

from ZenUV.ops.pt_uv_texture_advanced import DATA_PT_uv_texture_advanced, DATA_PT_UVL_uv_texture_advanced
from ZenUV.ui import main_popup, main_panel, ots_local_props
from ZenUV.zen_checker.panel import ZUV_PT_Checker, ZUV_PT_Checker_UVL
from ZenUV.ui import ui_call
from ZenUV.ui import zen_pack_popup
from ZenUV.ui import zen_mark_popup
from ZenUV.ui import zen_checker_popup
from ZenUV.ui import keymap_operator
from ZenUV.ui import uv_panel
from ZenUV.ops import seam_groups
# from ZenUV.ui.user_alt_commands import ZUV_OT_search_operator
from ZenUV.ui import third_party_popups
from ZenUV.ui import manual_map
from ZenUV.ui.pie import ZsPieFactory

# Importing Parented panels classes
from ZenUV.ops.pack_exclusion import pack_exclusion_parented_panels
from ZenUV.ops.texel_presets import TDPR_parented_panels
from ZenUV.stacks import m_stacks_parented_panels
from ZenUV.ui.main_panel import main_panel_parented_panels
from ZenUV.ui.uv_panel import main_panel_uv_parented_panels
from ZenUV.ops.trimsheets.trimsheet_panel import (
    ZUV_PT_UVL_Trimsheet, ZUV_PT_3DV_Trimsheet, ZUV_PT_PopupTrimsheetMaterial, trimsheet_parented_panels)
from ZenUV.zen_checker.check_utils import checker_parented_panels

from .combo_panel import (
    ZUV_PT_UVL_ComboPanel, ZUV_PT_3DV_ComboPanel,
    ZUV_OT_SetComboPanel, ZUV_OT_ExpandComboPanel, ZUV_OT_PinComboPanel)

from ZenUV.ui import tool

from .gizmo_draw import (
    ZUV_GGT_DetectionUV,
    ZUV_GGT_DrawUV, UV_GT_zenuv_overlay_draw,
    ZUV_GGT_Draw3D, VIEW3D_GT_zenuv_overlay_draw,
    ZUV_GGT_DrawView2D, VIEW2D_GT_zenuv_overlay_draw,
    ZUV_PT_GizmoDrawProperties,
    zenuv_depsgraph_ui_update)

from ZenUV.ops.transform_sys.tr_ui import transform_parented_panels

# Transform Extended panel
# from ZenUV.ops.transform_sys.tr_ui import (
#     # ZUV_PT_3DV_ExtendedTransform,
#     # ZUV_PT_UVL_ExtendedTransform
# )

main_panel_classes = (
    # main_panel.ZUV_PT_Global,
    DATA_PT_uv_texture_advanced,
    seam_groups.ZUV_PT_ZenSeamsGroups,
    main_panel.ZUV_PT_Unwrap,
    # main_panel.SYSTEM_PT_Finished,
    main_panel.ZUV_PT_Select,
    main_panel.ZUV_PT_Pack,
    # main_panel.PROPS_PT_Packer,
    ZUV_PT_Checker,
    main_panel.ZUV_PT_Texel_Density,
    main_panel.ZUV_PT_3DV_Transform,
    ZUV_PT_3DV_Trimsheet,
    # ZUV_PT_3DV_ExtendedTransform,
    main_panel.ZUV_PT_Stack,
    main_panel.ZUV_PT_Preferences,
    main_panel.ZUV_OT_resetPreferences,
    # main_panel.DATA_PT_Setup,
    # main_panel.DATA_PT_ZDisplay,
    # main_panel.DATA_PT_Panels_Switch,
    main_panel.ZUV_PT_Help,
    main_panel.ZUV_PT_ZenCore,

    ZUV_PT_3DV_ComboPanel,
)

uv_panel_classes = (
    DATA_PT_UVL_uv_texture_advanced,
    uv_panel.ZUV_PT_UVL_Unwrap,
    uv_panel.ZUV_PT_UVL_Select,
    uv_panel.ZUV_PT_UVL_Transform,
    ZUV_PT_UVL_Trimsheet,
    # ZUV_PT_UVL_ExtendedTransform,
    uv_panel.ZUV_PT_UVL_Texel_Density,
    uv_panel.ZUV_PT_UVL_Pack,
    ZUV_PT_Checker_UVL,
    # uv_panel.PROPS_PT_UVL_Packer,
    uv_panel.ZUV_PT_UVL_Stack,
    uv_panel.ZUV_PT_UVL_Preferences,
    # uv_panel.DATA_PT_UVL_Panels_Switch,
    # uv_panel.SYSTEM_PT_Finished_UV,
    # uv_panel.SYSTEM_PT_FitRegion_UV
    main_panel.ZUV_PT_UVL_Help,

    ZUV_PT_UVL_ComboPanel,
)

props_classes = (
    # manual_stacks.ZUV_PT_ZenManualStack,
    # manual_stacks.ZUV_PT_UVL_ZenManualStack,
    # ots_local_props.ZENUNWRAP_PT_Properties,
    ots_local_props.MARK_PT_Properties,
    ots_local_props.FINISHED_PT_Properties,
    ots_local_props.QUADRIFY_PT_Properties,
    ots_local_props.RELAX_PT_Properties,
    # ots_local_props.PACK_PT_Properties,
    ots_local_props.TD_PT_Properties,
    ots_local_props.TD_PT_Checker_Properties,
    # ots_local_props.TR_PT_Properties,
    ots_local_props.STACK_PT_Properties,
    ots_local_props.STACK_PT_DrawProperties,
    # main_pie.ZUV_OT_StretchMapSwitch,
    # main_pie.ZUV_MT_Main_Pie,
    # main_pie.ZUV_OT_Pie_Caller,
    main_popup.ZenUV_MT_Main_Popup,
    # ui_call.ZUV_OT_Main_Pie_call,
    ui_call.ZUV_OT_Main_Popup_call,
    third_party_popups.ZUV_MT_HOPS_Popup,
    # callers.ZUV_OT_Caller_Sector_9,
    # callers.ZUV_OT_Caller_Sector_4,
    # callers.ZUV_OT_Caller_Sector_7,
    # callers.ZUV_OT_Caller_Sector_3,
    # callers.ZUV_OT_Caller_Sector_6,
    # callers.ZUV_OT_Caller_Sector_8,
    # callers.ZUV_OT_Caller_Sector_2,
    # callers.ZUV_OT_Caller_Sector_1,
    # zen_unwrap_popup.ZenUV_MT_ZenUnwrap_Popup,
    zen_pack_popup.ZUV_MT_ZenPack_Uvp_Popup,
    zen_pack_popup.ZUV_MT_ZenPack_Uvpacker_Popup,
    zen_mark_popup.ZenUV_MT_ZenMark_Popup,
    zen_checker_popup.ZenUV_MT_ZenChecker_Popup,
    keymap_operator.ZUV_OT_Keymaps,

    ZUV_OT_SetComboPanel,
    ZUV_OT_ExpandComboPanel,
    ZUV_OT_PinComboPanel,

    ZUV_GGT_DetectionUV,
    UV_GT_zenuv_overlay_draw,
    ZUV_GGT_DrawUV,
    VIEW3D_GT_zenuv_overlay_draw,
    ZUV_GGT_Draw3D,
    VIEW2D_GT_zenuv_overlay_draw,
    ZUV_GGT_DrawView2D,
    ZUV_PT_GizmoDrawProperties,

    ZUV_PT_PopupTrimsheetMaterial
)

parent_panels = (
    # SYSTEM_PT_PackExcluded_UV,
    # SYSTEM_PT_PackExcluded,
    # ZUV_PT_ZenTDPresets,
    # ZUV_PT_UVL_ZenTDPresets,
    # ZUV_PT_UVL_ZenManualStack,
    # ZUV_PT_ZenManualStack,
    # DATA_PT_Setup, ==================
    # SYSTEM_PT_Finished,
    # SYSTEM_PT_Finished_UV,
    # DATA_PT_Panels_Switch,
    # DATA_PT_ZDisplay,
    # PROPS_PT_Packer,
    # DATA_PT_UVL_Panels_Switch,
    # SYSTEM_PT_FitRegion_UV, =================
    # PROPS_PT_UVL_Packer
)

# Order is important!!!
parented_groups = [
    m_stacks_parented_panels,
    TDPR_parented_panels,
    main_panel_parented_panels,
    main_panel_uv_parented_panels,
    pack_exclusion_parented_panels,
    trimsheet_parented_panels,
    checker_parented_panels,
    transform_parented_panels
]


def register_parented_panels():
    for group in parented_groups:
        for panel in group:
            register_class(panel)


def unregister_parented_panels():
    for group in parented_groups:
        for panel in group:
            unregister_class(panel)


def register():
    # Main Panel registration
    for cls in main_panel_classes:
        register_class(cls)

    # UV Panel registration
    for cls in uv_panel_classes:
        register_class(cls)

    register_parented_panels()

    # Pie menu
    for cl in ZsPieFactory.classes:
        register_class(cl)

    # Properties Popups
    for cls in props_classes:
        register_class(cls)

    manual_map.register()

    tool.register()

    # register_class(ZUV_OT_search_operator)

    if zenuv_depsgraph_ui_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(zenuv_depsgraph_ui_update)


def unregister():

    if zenuv_depsgraph_ui_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(zenuv_depsgraph_ui_update)

    tool.unregister()

    unregister_parented_panels()

    for cls in main_panel_classes:
        unregister_class(cls)

    # Unregister UV Panel
    for cls in uv_panel_classes:
        unregister_class(cls)

    # Pie menu
    for cl in ZsPieFactory.classes:
        unregister_class(cl)

    for cls in reversed(props_classes):
        unregister_class(cls)

    if hasattr(bpy.types, "ZUV_PT_System"):
        unregister_class(bpy.types.ZUV_PT_System)
    if hasattr(bpy.types, "ZUV_PT_System_UVL"):
        unregister_class(bpy.types.ZUV_PT_System_UVL)
    # unregister_class(ZUV_OT_search_operator)

    manual_map.unregister()


if __name__ == "__main__":
    pass
