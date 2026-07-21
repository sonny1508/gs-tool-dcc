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

""" Zen Texel Density Presets System """

import bpy
import bmesh
from mathutils import Color
from ZenUV.utils import vc_processor as vc
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.generic import (
    ZUV_PANEL_CATEGORY,
    ZUV_REGION_TYPE,
    ZUV_CONTEXT,
    ZUV_SPACE_TYPE,
    resort_objects,
    get_mesh_data,
    resort_by_type_mesh_in_edit_mode_and_sel,
    switch_shading_style,
    lerp_two_colors,
    remap_ranges
)

from ZenUV.utils.texel_density import (
    TdContext,
    set_texel_density,
    get_texel_density,
    get_td_data,
    get_td_color_map_from,
)
from pathlib import Path
from ZenUV.ui.ui_call import popup_areas

from ZenUV.utils.blender_zen_utils import ZuvPresets
from bl_operators.presets import AddPresetBase, ExecutePreset
from bpy.app.translations import (
    pgettext_tip as tip_,
)
from ZenUV.utils.tests.system_operators import ZUV_OT_OpenPresetsFolder


# PRESETS_TEMPLATE = {
#     "low": {"value": 5.12, "color": [0.0, 0.0, 1.0]},
#     "mid": {"value": 10.24, "color": [0.0, 1.0, 1.0]},
#     "high": {"value": 20.48, "color": [0.0, 1.0, 0.0]},
#     "ultra": {"value": 40.96, "color": [1.0, 0.0, 0.0]},
#     }
PRESET_NEW = {"name": "new", "value": 10.24, "color": [1.0, 0.0, 1.0]}
TD_PRESET_SUBDIR = 'texel_density_presets'


class ZUV_OT_TdExecutePreset(bpy.types.Operator):
    bl_idname = "uv.zuv_execute_td_preset"

    bl_label = 'You are about to load Texel Density preset'
    bl_description = "Load Texel Density preset from file"

    filepath: bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE'},
    )

    # we need this to prevent 'getattr()' is None
    menu_idname: bpy.props.StringProperty(
        name="Menu ID Name",
        description="ID name of the menu this was called from",
        options={'SKIP_SAVE'},
        default='ZUV_MT_StoreTdPresets'
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

    def execute(self, context):
        # Use this method because if it is inherited, can not change Blender theme !
        res = ExecutePreset.execute(self, context)

        # ZuvTrimsheetUtils.update_imageeditor_in_all_screens()

        return res


class ZUV_MT_StoreTdPresets(bpy.types.Menu):
    bl_label = 'TD Presets'

    default_label = 'Texel Density Presets'

    preset_subdir = ZuvPresets.get_preset_path(TD_PRESET_SUBDIR)
    preset_operator = 'uv.zuv_execute_td_preset'

    draw = bpy.types.Menu.draw_preset


class ZUV_OT_TdAddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'uv.zuv_add_td_preset'
    bl_label = 'Add|Remove Preset'
    preset_menu = 'ZUV_MT_StoreTrimsheetPresets'

    @classmethod
    def description(cls, context, properties):
        return ('Remove' if properties.remove_active else 'Add') + ' trimsheet preset'

    # Common variable used for all preset values
    preset_defines = [
        'prefs = bpy.context.scene'
    ]

    # Properties to store in the preset
    preset_values = [
        'prefs.zen_tdpr_list',
        'prefs.zen_tdpr_list_index',
    ]

    # Directory to store the presets
    preset_subdir = ZuvPresets.get_preset_path(TD_PRESET_SUBDIR)

    def execute(self, context):
        import os
        from bpy.utils import is_path_builtin

        if hasattr(self, "pre_cb"):
            self.pre_cb(context)

        preset_menu_class = getattr(bpy.types, self.preset_menu)

        is_xml = getattr(preset_menu_class, "preset_type", None) == 'XML'
        is_preset_add = not (self.remove_name or self.remove_active)

        if is_xml:
            ext = ".xml"
        else:
            ext = ".py"

        name = self.name.strip() if is_preset_add else self.name

        if is_preset_add:
            if not name:
                return {'FINISHED'}

            # Reset preset name
            wm = bpy.data.window_managers[0]
            if name == wm.preset_name:
                wm.preset_name = 'New Preset'

            filename = self.as_filename(name)

            target_path = os.path.join("presets", self.preset_subdir)
            target_path = bpy.utils.user_resource('SCRIPTS', path=target_path, create=True)

            if not target_path:
                self.report({'WARNING'}, "Failed to create presets path")
                return {'CANCELLED'}

            filepath = os.path.join(target_path, filename) + ext

            if hasattr(self, "add"):
                self.add(context, filepath)
            else:
                print("Writing Preset: %r" % filepath)

                if is_xml:
                    import rna_xml
                    rna_xml.xml_file_write(context,
                                           filepath,
                                           preset_menu_class.preset_xml_map)
                else:

                    def rna_recursive_attr_expand(value, rna_path_step, level):
                        if isinstance(value, bpy.types.PropertyGroup):
                            for sub_value_attr, sub_value_prop in value.bl_rna.properties.items():
                                if sub_value_attr == "rna_type":
                                    continue
                                if sub_value_prop.is_skip_save:
                                    continue
                                sub_value = getattr(value, sub_value_attr)
                                rna_recursive_attr_expand(sub_value, "%s.%s" % (rna_path_step, sub_value_attr), level)
                        elif type(value).__name__ == "bpy_prop_collection_idprop":  # could use nicer method
                            file_preset.write("%s.clear()\n" % rna_path_step)
                            for sub_value in value:
                                file_preset.write("item_sub_%d = %s.add()\n" % (level, rna_path_step))
                                rna_recursive_attr_expand(sub_value, "item_sub_%d" % level, level + 1)
                        else:
                            # convert thin wrapped sequences
                            # to simple lists to repr()
                            try:
                                value = value[:]
                            except Exception:
                                pass

                            file_preset.write("%s = %r\n" % (rna_path_step, value))

                    file_preset = open(filepath, 'w', encoding="utf-8")
                    file_preset.write("import bpy\n")

                    if hasattr(self, "preset_defines"):
                        for rna_path in self.preset_defines:
                            exec(rna_path)
                            file_preset.write("%s\n" % rna_path)
                        file_preset.write("\n")

                    for rna_path in self.preset_values:
                        value = eval(rna_path)
                        rna_recursive_attr_expand(value, rna_path, 1)

                    file_preset.close()

            preset_menu_class.bl_label = Path(filename).stem

        else:
            if self.remove_active:
                name = preset_menu_class.bl_label

            # fairly sloppy but convenient.
            filepath = bpy.utils.preset_find(name,
                                             self.preset_subdir,
                                             ext=ext)

            if not filepath:
                filepath = bpy.utils.preset_find(name,
                                                 self.preset_subdir,
                                                 display_name=True,
                                                 ext=ext)

            if not filepath:
                return {'CANCELLED'}

            # Do not remove bundled presets
            if is_path_builtin(filepath):
                self.report({'WARNING'}, "Unable to remove default presets")
                return {'CANCELLED'}

            try:
                if hasattr(self, "remove"):
                    self.remove(context, filepath)
                else:
                    os.remove(filepath)
            except Exception as e:
                self.report({'ERROR'}, tip_("Unable to remove preset: %r") % e)
                import traceback
                traceback.print_exc()
                return {'CANCELLED'}

            preset_menu_class.bl_label = preset_menu_class.default_label

        if hasattr(self, "post_cb"):
            self.post_cb(context)

        context.area.tag_redraw()

        return {'FINISHED'}


def do_draw_preset(layout: bpy.types.UILayout):
    row = layout.row(align=True)
    preset_menu_class = getattr(bpy.types, 'ZUV_MT_StoreTdPresets')
    row.menu("ZUV_MT_StoreTdPresets", text=preset_menu_class.bl_label)

    s_preset_name = preset_menu_class.bl_label

    op = row.operator("uv.zuv_add_td_preset", text="", icon="ADD")
    if s_preset_name and s_preset_name != preset_menu_class.default_label:
        op.name = s_preset_name
    op = row.operator("uv.zuv_add_td_preset", text="", icon="REMOVE")
    op.remove_active = True
    row.operator(
        ZUV_OT_OpenPresetsFolder.bl_idname,
        icon=ZUV_OT_OpenPresetsFolder.get_icon_name(),
        text='').preset_folder = TD_PRESET_SUBDIR


def draw_presets(self, context):
    layout = self.layout
    # ob = context.object
    scene = context.scene
    do_draw_preset(layout)
    row = layout.row(align=True)
    # row.operator(TDPR_OT_Generate.bl_idname, icon='GROUP')
    row.operator(TDPR_OT_Get.bl_idname, icon='IMPORT')
    row.operator(TDPR_OT_Clear.bl_idname, icon='TRASH', text="")

    row = layout.row()
    col = row.column()
    col.template_list(
        "TDPR_UL_List",
        "name",
        scene,
        "zen_tdpr_list",
        scene,
        "zen_tdpr_list_index",
        rows=2
    )

    col = row.column(align=True)
    col.operator(TDPR_OT_NewItem.bl_idname, text="", icon='ADD')
    col.operator(TDPR_OT_DeleteItem.bl_idname, text="", icon='REMOVE')

    col.operator(TDPR_OT_MoveItem.bl_idname, text="", icon='TRIA_UP').direction = 'UP'
    col.operator(TDPR_OT_MoveItem.bl_idname, text="", icon='TRIA_DOWN').direction = 'DOWN'
    col.separator()

    col = layout.column(align=True)
    col.operator(TDPR_OT_Set.bl_idname)
    row = col.row(align=True)
    row.prop(scene.zen_uv, "td_select_type", text="")
    sel_by_td = row.operator("zen_tdpr.select_by_texel_density", text="", icon="RESTRICT_SELECT_OFF")

    if scene.zen_uv.td_select_type == "VALUE":
        sel_by_td.by_value = True
        list_index = scene.zen_tdpr_list_index
        if list_index in range(len(scene.zen_tdpr_list)):
            sel_by_td.texel_density = context.scene.zen_tdpr_list[list_index].value
        else:
            sel_by_td.texel_density = 0.0

        sel_by_td.sel_underrated = False
        sel_by_td.sel_overrated = False
    if scene.zen_uv.td_select_type == "UNDERRATED":
        sel_by_td.sel_underrated = True
        sel_by_td.sel_overrated = False
        sel_by_td.by_value = False
    if scene.zen_uv.td_select_type == "OVERRATED":
        sel_by_td.sel_underrated = False
        sel_by_td.sel_overrated = True
        sel_by_td.by_value = False
    if context.area.type == 'VIEW_3D':
        row = layout.row(align=True)
        row.operator(ZUV_OT_Display_TD_Presets.bl_idname, icon='HIDE_OFF')
        row.operator("uv.zenuv_hide_texel_density", text="Hide").map_type = "ALL"


def remap_ranges_to_color(value, base_range, begin_color, finish_color):
    # print(begin_color)
    # print(finish_color)
    output = []
    for i in range(3):
        output.append(remap_ranges(value, base_range, (begin_color[i], finish_color[i])))
    return Color(output)


def new_list_item(context):
    scene = context.scene
    scene.zen_tdpr_list.add()
    name = PRESET_NEW["name"]
    value = PRESET_NEW["value"]
    color = PRESET_NEW["color"]
    i = 1

    while name in scene.zen_tdpr_list:
        name = f"{PRESET_NEW['name']}_{str(i)}"
        i = i + 1

    scene.zen_tdpr_list[-1].name = name
    scene.zen_tdpr_list[-1].value = value
    scene.zen_tdpr_list[-1].display_color = color
    scene.zen_tdpr_list_index = len(scene.zen_tdpr_list) - 1


def select_by_td(context, td_set, texel_density, treshold):
    for c_td, data in td_set.items():
        # print(f"TD: {c_td}, Islands: {len(data['objs'])}, --, {data['color']}")
        if texel_density - treshold < c_td < texel_density + treshold:
            for obj_name in data["objs"]:
                obj = context.scene.objects[obj_name]
                me, bm = get_mesh_data(obj)
                bm.faces.ensure_lookup_table()
                for island in data["objs"][obj_name]:
                    for f in island:
                        bm.faces[f].select = True
                bmesh.update_edit_mesh(me)


class TDPRListGroup(bpy.types.PropertyGroup):
    """
    Group of properties representing
    an item in the zen TD Presets groups.
    """

    name: bpy.props.StringProperty(
        name="Name",
        description="A name for this item",
        default="new"
    )
    value: bpy.props.FloatProperty(
        name="Value",
        description="Texel Density Value",
        default=10.24
    )
    display_color: bpy.props.FloatVectorProperty(
        name="Color",
        description="Color to display the density of texels",
        subtype='COLOR',
        default=[0.316, 0.521, 0.8],
        size=3,
        min=0,
        max=1
    )


class TDPR_UL_List(bpy.types.UIList):
    """ Zen TD Presets UIList """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        custom_icon = 'OBJECT_DATAMODE'

        act_idx = getattr(active_data, active_propname)
        b_active = index == act_idx

        b_emboss = (context.area.as_pointer() in popup_areas) and b_active

        # Make sure code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # -- Test Version
            layout.alignment = 'LEFT'  # required for 'ui_units_x'

            # minimum possible alignment
            layout.separator(factor=0.1)

            r = layout.row()
            r.ui_units_x = 0.7

            col = r.column()
            col.separator(factor=0.8)

            col.scale_y = 0.6
            col.prop(item, 'display_color', text='')

            r = layout.split(factor=0.5, align=False)
            r.prop(item, 'name', text='', emboss=b_emboss, icon='NONE')
            r.prop(item, "value", text="", emboss=False)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(item, 'name', text="", emboss=False, icon=custom_icon)


class ZUV_PT_ZenTDPresets(bpy.types.Panel):
    """  Zen TD Presets Panel """
    bl_label = "Presets"
    bl_context = ZUV_CONTEXT
    bl_space_type = ZUV_SPACE_TYPE
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_Texel_Density"
    bl_idname = "ZUV_PT_ZenTDPresets"

    def draw(self, context):
        draw_presets(self, context)


class ZUV_PT_UVL_ZenTDPresets(bpy.types.Panel):
    bl_parent_id = "ZUV_PT_UVL_Texel_Density"
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_ZenTDPresetsUV"
    bl_label = ZuvLabels.PANEL_TDPR_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY

    def draw(self, context):
        draw_presets(self, context)


class TDPR_OT_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_description = ZuvLabels.OT_SGL_NEW_ITEM_DESC
    bl_idname = "zen_tdpr.new_item"
    bl_label = ZuvLabels.OT_SGL_NEW_ITEM_LABEL
    bl_options = {'INTERNAL'}

    def execute(self, context):
        new_list_item(context)
        return {'FINISHED'}


class TDPR_OT_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_description = ZuvLabels.OT_SGL_DEL_ITEM_DESC
    bl_idname = "zen_tdpr.delete_item"
    bl_label = ZuvLabels.OT_SGL_DEL_ITEM_LABEL
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.zen_tdpr_list

    def execute(self, context):
        scene = context.scene
        list_index = scene.zen_tdpr_list_index
        if list_index in range(len(scene.zen_tdpr_list)):
            zen_tdpr_list = scene.zen_tdpr_list
            index = scene.zen_tdpr_list_index
            if index in range(len(scene.zen_tdpr_list)):
                zen_tdpr_list.remove(index)
                scene.zen_tdpr_list_index = min(max(0, index - 1), len(zen_tdpr_list) - 1)

        return {'FINISHED'}


class TDPR_OT_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "zen_tdpr.move_item"
    bl_label = ZuvLabels.OT_SGL_MOVE_ITEM_LABEL
    bl_description = ZuvLabels.OT_SGL_MOVE_ITEM_DESC
    bl_options = {'INTERNAL'}

    direction: bpy.props.EnumProperty(
        items=(
            ('UP', 'Up', ""),
            ('DOWN', 'Down', ""),
        )
    )

    @classmethod
    def poll(cls, context):
        return context.scene.zen_tdpr_list

    def move_index(self, context):
        """ Move index of an item render queue while clamping it. """
        index = context.scene.zen_tdpr_list_index
        list_length = len(context.scene.zen_tdpr_list) - 1
        # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)
        context.scene.zen_tdpr_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        zen_tdpr_list = context.scene.zen_tdpr_list
        index = context.scene.zen_tdpr_list_index
        neighbor = index + (-1 if self.direction == 'UP' else 1)
        zen_tdpr_list.move(neighbor, index)
        self.move_index(context)
        return {'FINISHED'}


class TDPR_OT_Set(bpy.types.Operator):
    """ Set TD from active preset to selected Islands """
    bl_idname = "zen_tdpr.set_td_from_preset"
    bl_label = ZuvLabels.OT_TDPR_SET_LABEL
    bl_idname = "zen_tdpr.set_td_from_preset"
    bl_description = ZuvLabels.OT_TDPR_SET_DESC

    def execute(self, context):
        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            return {'CANCELLED'}
        scene = context.scene
        list_index = scene.zen_tdpr_list_index
        if list_index in range(len(scene.zen_tdpr_list)):
            td_inputs = TdContext(context)
            td_inputs.td = scene.zen_tdpr_list[list_index].value
            set_texel_density(context, objs, td_inputs)
        return {'FINISHED'}


class TDPR_OT_Get(bpy.types.Operator):
    """ Get TD from selected Islands to active preset """
    bl_idname = "zen_tdpr.get_td_from_preset"
    bl_label = ZuvLabels.OT_TDPR_GET_LABEL
    bl_description = ZuvLabels.OT_TDPR_GET_DESC

    def execute(self, context):
        objs = resort_objects(context, context.objects_in_mode)
        if not objs:
            return {'CANCELLED'}
        scene = context.scene
        list_index = scene.zen_tdpr_list_index
        if list_index not in range(len(scene.zen_tdpr_list)):
            new_list_item(context)
        td_inputs = TdContext(context)
        scene.zen_tdpr_list[list_index].value, tmp = get_texel_density(context, objs, td_inputs)

        return {'FINISHED'}


# class TDPR_OT_Generate(bpy.types.Operator):
#     """ Set TD from active preset to selected Islands """
#     bl_idname = "zen_tdpr.generate_presets"
#     bl_label = ZuvLabels.OT_TDPR_GENERATE_LABEL
#     bl_description = ZuvLabels.OT_TDPR_GENERATE_DESC

#     def execute(self, context):
#         scene = context.scene
#         for name, data in PRESETS_TEMPLATE.items():
#             scene.zen_tdpr_list.add()
#             scene.zen_tdpr_list[-1].name = name
#             scene.zen_tdpr_list[-1].value = data["value"]
#             scene.zen_tdpr_list[-1].display_color = data["color"]
#             scene.zen_tdpr_list_index = len(scene.zen_tdpr_list) - 1
#         return {'FINISHED'}


class TDPR_OT_Clear(bpy.types.Operator):
    """ Clear Presets List """
    bl_idname = "zen_tdpr.clear_presets"
    # bl_label = ZuvLabels.OT_TDPR_CLEAR_DESC
    bl_description = ZuvLabels.OT_TDPR_CLEAR_LABEL

    bl_label = 'You are about to Clear preset list'

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

    def execute(self, context):
        scene = context.scene
        scene.zen_tdpr_list.clear()
        scene.zen_tdpr_list_index = -1
        return {'FINISHED'}


class TDPR_OT_SelectByTd(bpy.types.Operator):
    """ Select Islands By Texel Density """
    bl_idname = "zen_tdpr.select_by_texel_density"
    bl_label = ZuvLabels.OT_TDPR_SEL_BY_TD_LABEL
    bl_description = ZuvLabels.OT_TDPR_SEL_BY_TD_DESC
    bl_options = {'REGISTER', 'UNDO'}

    texel_density: bpy.props.FloatProperty(
        name="Texel Density",
        description="",
        precision=2,
        default=0.0,
        step=1,
        min=0.0
    )
    treshold: bpy.props.FloatProperty(
        name="Treshold",
        description="",
        precision=2,
        default=0.01,
        step=1,
        min=0.0
    )
    clear_selection: bpy.props.BoolProperty(name=ZuvLabels.OT_TDPR_SEL_BY_TD_CLEAR_SEL_LABEL, default=True)
    sel_underrated: bpy.props.BoolProperty(name=ZuvLabels.OT_TDPR_SEL_BY_TD_SEL_UNDER_LABEL, default=False)
    sel_overrated: bpy.props.BoolProperty(name=ZuvLabels.OT_TDPR_SEL_BY_TD_SEL_OVER_LABEL, default=False)
    by_value: bpy.props.BoolProperty(name=ZuvLabels.OT_TDPR_SEL_BY_TD_SEL_VALUE_LABEL, default=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "clear_selection")
        layout.separator_spacer()
        layout.prop(self, "by_value")
        col = layout.column(align=True)
        col.enabled = self.by_value
        col.prop(self, "texel_density")
        col.prop(self, "treshold")
        layout.separator_spacer()
        layout.prop(self, "sel_underrated")
        layout.prop(self, "sel_overrated")

    def prepare_context(self, context):
        td_inputs = TdContext(context)
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            return False
        self.td_set = get_td_data(context, objs, td_inputs)
        return True

    def execute(self, context):
        result = self.prepare_context(context)
        if not result:
            return {'CANCELLED'}
        if self.clear_selection:
            bpy.ops.mesh.select_all(action='DESELECT')

        # Select by Value
        if self.by_value:
            select_by_td(context, self.td_set, self.texel_density, self.treshold)

        if self.sel_overrated or self.sel_underrated:
            # Detect / Select Overrated / Underrated

            presets = []
            for i in context.scene.zen_tdpr_list:
                td = round(i.value, 2)
                presets.append(td)
                if td not in self.td_set.keys():
                    self.td_set[td] = {"objs": {}, "color": Color(i.display_color)}
                else:
                    self.td_set[td]["color"] = Color(i.display_color)

            ranges = sorted(self.td_set)
            if not presets:
                self.report({'WARNING'}, "Presets List is empty")
                return {'CANCELLED'}

            min_preset = min(presets)
            max_preset = max(presets)
            underrated = ranges[0: ranges.index(min_preset)]
            overrated = ranges[ranges.index(max_preset)+1:]

            if self.sel_underrated:
                for i in underrated:
                    select_by_td(context, self.td_set, i, 0.01)
            if self.sel_overrated:
                for i in overrated:
                    select_by_td(context, self.td_set, i, 0.01)

        return {'FINISHED'}


class ZUV_OT_Display_TD_Presets(bpy.types.Operator):
    """ Display Texel Density Presets """
    bl_idname = "uv.zenuv_display_td_preset"
    bl_label = ZuvLabels.OT_TDPR_DISPLAY_TD_PRESETS_LABEL
    bl_description = ZuvLabels.OT_TDPR_DISPLAY_TD_PRESETS_DESC
    bl_options = {'REGISTER', 'UNDO'}

    face_mode: bpy.props.BoolProperty(name="Per Face", default=False, options={'HIDDEN'})
    presets_only: bpy.props.BoolProperty(name=ZuvLabels.OT_TDPR_DISPLAY_TD_PRESETS_ONLY_LABEL, default=False)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "presets_only")

    def prepare_context(self, context):
        td_inputs = TdContext(context)
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            return False
        self.td_set = get_td_data(context, objs, td_inputs, self.face_mode)
        return True

    def execute(self, context):
        result = self.prepare_context(context)
        if not result:
            return {'CANCELLED'}
        bpy.ops.uv.zenuv_hide_texel_density(map_type='ALL')
        presets = []
        for i in context.scene.zen_tdpr_list:
            td = round(i.value, 2)
            presets.append(td)
            if td not in self.td_set.keys():
                self.td_set[td] = {"objs": {}, "color": Color(i.display_color)}
            else:
                self.td_set[td]["color"] = Color(i.display_color)

        if not presets:
            self.report({'WARNING'}, "Presets List is empty")
            return {'CANCELLED'}

        color_under = Color((0.0, 0.0, 0.0))
        color_over = Color((1.0, 1.0, 1.0))

        ranges = sorted(self.td_set)
        max_ranges = max(ranges)

        ranges_filled = dict()
        for r in ranges:
            ranges_filled[r] = {"color": self.td_set[r]["color"], "preset": r in presets}

        if not self.presets_only:
            # Put Overrated / Underrated colors in self.td_set
            max_td = max(self.td_set.keys())
            min_td = min(self.td_set.keys())

            if max_td not in presets:
                self.td_set[max_td]["color"] = color_over
                presets.append(max_td)
                ranges_filled[max_td] = {"color": color_over, "preset": True}
            if min_td not in presets:
                self.td_set[min_td]["color"] = color_under
                presets.append(min_td)
                ranges_filled[min_td] = {"color": color_under, "preset": True}
            presets = sorted(presets)

            sub_range = []
            for i in sorted(ranges_filled):
                sub_range.append(i)
                if ranges_filled[i]["preset"] or i == max_ranges:

                    first_preset = sub_range[0]
                    last_preset = sub_range[-1]
                    first_point = ranges_filled[first_preset]
                    last_point = ranges_filled[last_preset]

                    top_color = last_point["color"]
                    bottom_color = first_point["color"]

                    preset_range = [first_preset, last_preset]

                    no_steps = 101
                    ligc = []
                    for j in range(no_steps):
                        color = lerp_two_colors(bottom_color, top_color, j / no_steps)
                        ligc.append(color)
                    for k in range(len(sub_range)):
                        value = sub_range[k]
                        position = remap_ranges(value, preset_range, (0, 100))
                        # if value not in presets:
                        self.td_set[value]["color"] = Color(ligc[round(position)])

                    sub_range = [sub_range[-1], ]
        else:
            for td in self.td_set.keys():
                if td not in presets:
                    self.td_set[td]["color"] = color_under

        # Set Vertex Color to Object
        for c_td, data in self.td_set.items():
            for obj_name in data["objs"]:
                obj = context.scene.objects[obj_name]
                me, bm = get_mesh_data(obj)
                bm.faces.ensure_lookup_table()
                for island in data["objs"][obj_name]:
                    island_faces = [bm.faces[i] for i in island]
                    vc.set_v_color(
                        island_faces,
                        vc.set_color_layer(bm, vc.Z_TD_PRESETS_V_MAP_NAME),
                        data["color"],
                        randomize=False
                    )
                    bmesh.update_edit_mesh(me, loop_triangles=False)
                vc_td_layer = get_td_color_map_from(obj, vc.Z_TD_PRESETS_V_MAP_NAME)
                if vc_td_layer:
                    vc_td_layer.active = True
                obj.update_from_editmode()
        switch_shading_style(context, "VERTEX", switch=False)
        return {'FINISHED'}


TDPR_classes = (
    ZUV_MT_StoreTdPresets,
    ZUV_OT_TdAddPreset,
    ZUV_OT_TdExecutePreset,
    # TDPRListGroup,
    TDPR_UL_List,
    TDPR_OT_NewItem,
    TDPR_OT_DeleteItem,
    TDPR_OT_Set,
    TDPR_OT_Get,
    TDPR_OT_MoveItem,
    # TDPR_OT_Generate,
    TDPR_OT_Clear,
    TDPR_OT_SelectByTd,
    ZUV_OT_Display_TD_Presets,

)

TDPR_parented_panels = [
    ZUV_PT_ZenTDPresets,
    ZUV_PT_UVL_ZenTDPresets,
]

if __name__ == "__main__":
    pass
