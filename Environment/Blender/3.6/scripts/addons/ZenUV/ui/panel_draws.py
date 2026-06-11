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

""" Zen UV draws functions for panels """
import bpy
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.ui.labels import ZuvLabels
from ZenUV.ico import icon_get
from ZenUV.utils.blender_zen_utils import ZenPolls
# from ZenUV.ops.zen_unwrap.project import ZUV_OT_ProjectByScreenCage


def draw_packer_props(self, context):
    addon_prefs = get_prefs()
    zen_props = context.scene.zen_uv
    draw_pack_engine(self, context)
    box = self.layout.box()
    row = box.row(align=True)
    row.label(text=ZuvLabels.PREF_TD_TEXTURE_SIZE_LABEL + ": ")
    row.prop(addon_prefs, 'td_im_size_presets', text="")
    if addon_prefs.td_im_size_presets == 'Custom':
        col = box.column(align=True)
        col.prop(addon_prefs, 'TD_TextureSizeX', text="Custom Res X")
        col.prop(addon_prefs, 'TD_TextureSizeY', text="Custom Res Y")

    # General Settings
    box.prop(addon_prefs, 'averageBeforePack')
    box.prop(addon_prefs, 'rotateOnPack')
    if addon_prefs.packEngine == 'BLDR':
        box.prop(addon_prefs, 'packSelectedIslOnly')

    # UVP Settings
    if addon_prefs.packEngine == 'UVP':
        # layout.prop(addon_prefs, "keepStacked")
        box.prop(addon_prefs, 'packSelectedIslOnly')
        box.prop(addon_prefs, "packFixedScale")
        box.prop(addon_prefs, "lock_overlapping_mode")
        # UVP2 Packing Modes 'Single Tile', 'Tiles', 'Groups Together', 'Groups To Tiles'
        if hasattr(bpy.types, bpy.ops.uvpackmaster2.uv_pack.idname()):
            if hasattr(context.scene, "uvp2_props") and hasattr(context.scene.uvp2_props, "margin"):
                uvp_2_scene_props = context.scene.uvp2_props
                pm = box.column(align=True)
                pm.label(text="PackingMode:")
                pm.prop(uvp_2_scene_props, "pack_mode", text='')
                if uvp_2_scene_props.pack_mode in ["2", "3"]:
                    col = box.column(align=True)
                    col.label(text="Grouping Method:")
                    col.prop(uvp_2_scene_props, "group_method", text='')
                if uvp_2_scene_props.pack_mode == "2":
                    pm.prop(uvp_2_scene_props, "group_compactness")
                if uvp_2_scene_props.pack_mode == "3":
                    pm.prop(uvp_2_scene_props, "tiles_in_row")
                if uvp_2_scene_props.pack_mode in ["1", ]:
                    col = box.column(align=True)
                    tile_col = col.column(align=True)
                    # tile_col.enabled = tile_col_enabled
                    tile_col.prop(uvp_2_scene_props, "tile_count")
                    tile_col.prop(uvp_2_scene_props, "tiles_in_row")

        if hasattr(bpy.types, bpy.ops.uvpackmaster3.pack.idname()):
            if hasattr(context.scene, "uvpm3_props") and hasattr(context.scene.uvpm3_props, "margin"):
                uvp_3_scene_props = context.scene.uvpm3_props
                box.prop(addon_prefs, 'packInTrim')
                pm = box.column(align=True)
                pm.label(text="PackingMode:")
                pm.prop(zen_props, 'uvp3_packing_method', text='')
                packing_method = zen_props.uvp3_packing_method
                if packing_method == 'pack.single_tile':
                    pass
                elif packing_method == 'pack.tiles':
                    box = self.layout.box()
                    col = box.column(align=True)
                    tile_col = col.column(align=True)
                    tile_col.prop(uvp_3_scene_props, "tile_count_x")
                    tile_col.prop(uvp_3_scene_props, "tile_count_y")

                if packing_method in ['pack.groups_to_tiles', 'pack.groups_together']:
                    box = self.layout.box()
                    col = box.column(align=True)
                    col.label(text="Grouping Method:")
                    col.prop(uvp_3_scene_props, "group_method", text='')

                if packing_method == 'pack.groups_to_tiles':
                    if uvp_3_scene_props.group_method != '4':
                        col.label(text='Grouping options:')
                        box_in = col.box()
                        col_in = box_in.column(align=True)
                        col_in.label(text='Texel Density Policy:')
                        col_in.prop(uvp_3_scene_props.auto_group_options, "tdensity_policy", text='')
                        col.prop(uvp_3_scene_props.auto_group_options.base, "tiles_in_row")
                if packing_method == 'pack.groups_together':
                    if uvp_3_scene_props.group_method != '4':
                        col.label(text='Grouping options:')
                        col.prop(uvp_3_scene_props.auto_group_options.base, "group_compactness")


def draw_progress_bar(self, context):
    if context.scene.zenuv_progress >= 0:
        self.layout.separator()
        text = context.scene.zenuv_progress_text
        self.layout.prop(
            context.scene,
            "zenuv_progress",
            text=text,
            slider=True
            )


def draw_select(self, context):
    layout = self.layout
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator("uv.zenuv_select_island", icon_value=icon_get('select'), text='Islands')
    row.operator("uv.zenuv_select_loop", text="Int. Loop")
    row = col.row(align=True)
    row.operator("uv.zenuv_select_uv_overlap", text="Overlapped")
    row.operator("uv.zenuv_select_flipped", text="Flipped")
    if context.area.type == 'VIEW_3D':
        row = col.row(align=True)
        row.operator("mesh.zenuv_select_seams", text="Seam")
        row.operator("mesh.zenuv_select_sharp", text="Sharp")
    col.operator("uv.zenuv_select_uv_borders")
    col.operator("uv.zenuv_select_similar", text="Similar")
    if ZenPolls.version_greater_3_2_0:
        col.operator("uv.zenuv_select_by_direction")
    row = col.row(align=True)
    row.operator("uv.zenuv_select_by_uv_area")
    row.operator("uv.zenuv_grab_sel_area", icon='IMPORT', text="")
    layout.operator("uv.zenuv_isolate_island")


def draw_texel_density(self, context):
    addon_prefs = get_prefs()
    layout = self.layout
    label_units = 'px/' + context.preferences.addons[ZuvLabels.ADDON_NAME].preferences.bl_rna.properties['td_unit'].enum_items[addon_prefs.td_unit].name
    col = layout.column(align=True)
    row = col.row(align=True)
    r = row.split(factor=0.7, align=True)
    r.prop(addon_prefs, 'TexelDensity', text="")
    r.label(text=label_units)
    sel_by_td = row.operator(
        "zen_tdpr.select_by_texel_density",
        text="",
        icon="RESTRICT_SELECT_OFF"
        )
    sel_by_td.by_value = True
    sel_by_td.texel_density = addon_prefs.TexelDensity
    sel_by_td.sel_underrated = False
    sel_by_td.sel_overrated = False
    row.popover(panel="TD_PT_Properties", text="", icon="PREFERENCES")
    row = col.row(align=True)
    row.operator('uv.zenuv_get_texel_density')
    row.operator('uv.zenuv_set_texel_density')
    row = col.row(align=True)
    row.prop(addon_prefs, "td_set_mode", text="")
    # label_display_td = ZuvLabels.OT_DISPLAY_TD_LABEL

    col = layout.column(align=True)
    row = col.row(align=True)
    td_checker_value = str(round(addon_prefs.td_checker, 2))
    if context.area.type == 'VIEW_3D':
        row.label(text="TD Checker: " + td_checker_value + " " + label_units)
        row.operator("zenuv.set_current_td_to_checker_td", text="", icon='IMPORT')
        row.popover(panel="TD_PT_Checker_Properties", text="", icon="PREFERENCES")
        # if is_td_display_activated(context):
        #     label_display_td = ZuvLabels.OT_REFRESH_TD_LABEL
    if context.area.type == 'VIEW_3D':
        row = layout.row(align=True)
        row.operator("uv.zenuv_display_td_balanced", icon='HIDE_OFF')
        row.operator("uv.zenuv_hide_texel_density").map_type = "ALL"


def draw_finished_section(self, context: bpy.types.Context):
    """ Finished Section """
    layout = self.layout
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator("uv.zenuv_islands_sorting", text=ZuvLabels.SORTING_LABEL)
    row.popover(panel="FINISHED_PT_Properties", text="", icon="PREFERENCES")
    row = col.row(align=True)
    row.operator("uv.zenuv_tag_finished")
    row.operator("uv.zenuv_untag_finished")

    # col.operator("uv.zenuv_batch_finished",
    #         text=ZuvLabels.BATCH_FINISHED_HIDE_ENUM_LABEL).Action = "HIDE"
    col.operator("uv.zenuv_select_finished")

    from ZenUV.zen_checker.check_utils import draw_checker_display_items, DisplayItem
    draw_checker_display_items(col, context, {'FINISHED': DisplayItem({'EDIT_MESH'}, {'UV', '3D'}, '', 'Display Finished')})


def draw_native_unwrap(self, context):
    row = self.layout.row(align=True)
    row.operator('uv.smart_project')
    row.operator('uv.cube_project')
    row.operator('uv.cylinder_project')
    row.operator('uv.sphere_project')


def draw_unwrap(self, context):
    layout = self.layout

    # Zen Unwrap Section
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator(
        "uv.zenuv_unwrap",
        icon_value=icon_get(ZuvLabels.ZEN_UNWRAP_ICO)).action = "DEFAULT"
    row.popover(panel="ZENUNWRAP_PT_Properties", text="", icon="PREFERENCES")
    col.operator("uv.zenuv_unwrap_constraint")
    # layout.operator(ZUV_OT_ProjectByScreenCage.bl_idname)

    # draw_native_unwrap(self, context)

    # Seams Section
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator("uv.zenuv_auto_mark")
    row.popover(panel="MARK_PT_Properties", text="", icon="PREFERENCES")
    row = col.row(align=True)
    row.operator(
        "uv.zenuv_mark_seams",
        icon_value=icon_get(ZuvLabels.OT_MARK_ICO))
    row.operator(
        "uv.zenuv_unmark_seams",
        icon_value=icon_get(ZuvLabels.OT_UNMARK_ICO))
    col.operator("uv.zenuv_unmark_all")

    # Seam By Section

    # col = col.column(align=True)
    row = col.row(align=True)
    row.prop(context.scene.zen_uv, "sl_convert", text="")
    row.operator("uv.zenuv_unified_mark", icon='KEYFRAME_HLT', text="")
    # col.operator("uv.zenuv_seams_by_uv_islands")
    # col.operator("uv.zenuv_seams_by_sharp")
    # col.operator("uv.zenuv_sharp_by_seams")
    # col.operator("uv.zenuv_seams_by_open_edges")
    layout.operator("mesh.zenuv_mirror_seams")

    # col = layout.column(align=True)
    layout.operator("view3d.zenuv_set_smooth_by_sharp")

    # draw_finished_section(self, context)

    # Quadrify Section

    # col = layout.column(align=True)
    # row = col.row(align=True)
    # row.operator("uv.zenuv_quadrify", icon_value=icon_get(TrLabels.ZEN_QUADRIFY_ICO))
    # row.popover(panel="QUADRIFY_PT_Properties", text="", icon="PREFERENCES")


def uv_draw_unwrap(self, context):
    # Zen Unwrap Section
    layout = self.layout
    row = layout.row(align=True)
    row.operator(
        "uv.zenuv_unwrap",
        icon_value=icon_get(ZuvLabels.ZEN_UNWRAP_ICO)).action = "DEFAULT"
    row.popover(panel="ZENUNWRAP_PT_Properties", text="", icon="PREFERENCES")
    layout.operator("uv.zenuv_unwrap_constraint")
    layout.operator('uv.zenuv_unwrap_inplace')
    # layout.operator(ZUV_OT_ProjectByScreenCage.bl_idname)


def draw_pack_engine(self, context):
    addon_prefs = get_prefs()
    layout = self.layout
    # Select Engine
    row = layout.row(align=True)
    row.label(text=ZuvLabels.PREF_PACK_ENGINE_LABEL + ':')
    row = layout.row(align=True)
    row.prop(addon_prefs, "packEngine", text="")

    if not addon_prefs.packEngine == "UVPACKER":
        layout.prop(addon_prefs, 'margin_show_in_px')

    # Sync settings to UVP
    if addon_prefs.packEngine == 'UVP':
        row.operator("uv.zenuv_sync_to_uvp", text="", icon="FILE_REFRESH")

    # # Custom Engine Settings
    # if addon_prefs.packEngine == "CUSTOM":
    #     layout.prop(addon_prefs, "customEngine", text="")


def draw_pack(self, context):
    addon_prefs = get_prefs()
    layout = self.layout
    prop = context.scene.zen_uv

    # Pack Section
    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator("uv.zenuv_pack", icon_value=icon_get('pack')).display_uv = True
    # row.popover(panel="PACK_PT_Properties", text="", icon="PREFERENCES")
    if not addon_prefs.packEngine == "UVPACKER":
        if addon_prefs.margin_show_in_px:
            col.prop(addon_prefs, 'margin_px')
        else:
            col.prop(addon_prefs, 'margin')
    else:
        col.prop(prop, "pack_uv_packer_margin")
    row = layout.row(align=True)
    uv_coverage_label = "UV Coverage: " + str(round(addon_prefs.UVCoverage, 2)) + " %"
    row.label(text=uv_coverage_label)
    row.operator("uv.zenuv_get_uv_coverage", icon="FILE_REFRESH", text="")


def draw_stack(self, context):
    addon_prefs = get_prefs()
    layout = self.layout
    # layout.split()
    main_ops_col = layout.column(align=False)
    if addon_prefs.st_stack_mode in {'ALL', 'SELECTED'}:

        draw_full_stack(addon_prefs, main_ops_col)

        row = main_ops_col.row(align=True)
        row.prop(get_prefs(), "st_stack_mode", text="")

        # if context.area.type == 'VIEW_3D':
        #     layout.split()
        #     deferred_displaying = ('PRIMARY', 'REPLICAS', 'SINGLES')
        #     row = layout.row(align=True)
        #     eye_row = row.row(align=True)
        #     if context.scene.zen_display.stack_display_mode not in deferred_displaying:
        #         eye_row.prop(context.scene.zen_display, "stack_display_solver", text="", toggle=True, icon='HIDE_OFF')
        #     row.prop(context.scene.zen_display, "stack_display_mode", text="")
        #     if context.scene.zen_display.stack_display_mode == 'STACKED':
        #         row.popover(panel="STACK_PT_DrawProperties", text="", icon="PREFERENCES")
        #         row.operator("uv.zenuv_select_stacked", text="", icon="RESTRICT_SELECT_OFF")
        #     if context.scene.zen_display.stack_display_mode in deferred_displaying:
        #         solver = context.scene.zen_display.stack_display_mode
        #         if solver == 'PRIMARY':
        #             desc = ZuvLabels.OT_SELECT_STACK_PRIMARY_DESC
        #         elif solver == 'REPLICAS':
        #             desc = ZuvLabels.OT_SELECT_STACK_REPLICAS_DESC
        #         elif solver == 'SINGLES':
        #             desc = ZuvLabels.OT_SELECT_STACK_SINGLES_DESC
        #         row.operator("uv.zenuv_select_stack", text="", icon="RESTRICT_SELECT_OFF").desc = desc
    else:

        draw_simple_stack(main_ops_col)
        row = main_ops_col.row(align=True)
        row.prop(get_prefs(), "st_stack_mode", text="")


def draw_full_stack(addon_prefs, col):
    row = col.row(align=True)
    st = row.operator("uv.zenuv_stack_similar", text="Stack", icon_value=icon_get(ZuvLabels.ZEN_STACK_ICO))
    ust = row.operator("uv.zenuv_unstack", text="Unstack")
    if addon_prefs.st_stack_mode == 'ALL':
        st.selected = ust.selected = False
    elif addon_prefs.st_stack_mode == 'SELECTED':
        st.selected = ust.selected = True
    row.popover(panel="STACK_PT_Properties", text="", icon="PREFERENCES")


def draw_copy_paste(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.operator("uv.zenuv_copy_param", icon="COPYDOWN")
    row.operator("uv.zenuv_paste_param", icon="PASTEDOWN")


def draw_simple_stack(main_ops_col):
    row = main_ops_col.row(align=True)
    row.operator("uv.zenuv_simple_stack", text="Stack")
    row.operator("uv.zenuv_simple_unstack", text="Unstack")
