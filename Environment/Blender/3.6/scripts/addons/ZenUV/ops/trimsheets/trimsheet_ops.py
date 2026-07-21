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

# Copyright 2022, Alex Zhornyak

import bpy

import json
from collections import defaultdict
from functools import partial

from .trimsheet_utils import ZuvTrimsheetUtils, TrimImportUtils

from ZenUV.utils.blender_zen_utils import update_areas_in_all_screens, ZenPolls, ZenStrUtils
from ZenUV.utils.vlog import Log


class ZUV_PT_UVMathVisualizer(bpy.types.Panel):
    bl_label = "Zen UV Math"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_parent_id = "IMAGE_PT_annotation"

    def draw(self, context):
        layout = self.layout

        layout.operator('uv.zuv_math_vis')


class ZUV_PT_3DVMathVisualizer(bpy.types.Panel):
    bl_label = "Zen UV Math"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "VIEW3D_PT_grease_pencil"

    def draw(self, context):
        layout = self.layout

        layout.operator('view3d.zuv_math_vis')


class ZUV_OT_View3DMathVis(bpy.types.Operator):
    bl_idname = "view3d.zuv_math_vis"
    bl_label = 'Math Vis'
    bl_options = {'REGISTER', 'UNDO'}

    co_start: bpy.props.FloatVectorProperty(
        name='Vec Start', size=3, subtype='XYZ', default=(0, 0, 0))
    co_end: bpy.props.FloatVectorProperty(
        name='Vec End', size=3, subtype='XYZ', default=(1, 1, 0))

    def execute(self, context: bpy.types.Context):
        from ZenUV.utils.math_visualizer import MathVisualizer

        debugger = MathVisualizer(context)
        debugger.add_vector('First Vector', 0, self.co_start, self.co_end, color=(1, 0, 0))

        return {'FINISHED'}


class ZUV_OT_UVMathVis(bpy.types.Operator):
    bl_idname = "uv.zuv_math_vis"
    bl_label = 'Math Vis'
    bl_options = {'REGISTER', 'UNDO'}

    co_start: bpy.props.FloatVectorProperty(
        name='Vec Start', size=2, subtype='XYZ', default=(0, 0))
    co_end: bpy.props.FloatVectorProperty(
        name='Vec End', size=2, subtype='XYZ', default=(1, 1))

    def execute(self, context: bpy.types.Context):
        from ZenUV.utils.math_visualizer import MathVisualizer

        debugger = MathVisualizer(context)
        debugger.add_vector('First Vector', 0, self.co_start, self.co_end, color=(1, 0, 0))

        return {'FINISHED'}


class ZUV_OT_TrimSetIndex(bpy.types.Operator):
    bl_idname = "wm.zuv_trim_set_index"
    bl_label = 'Set Trim Index'
    bl_description = 'Sets trimsheet active index'
    bl_options = {'REGISTER', 'UNDO'}

    trimsheet_index: bpy.props.IntProperty(
        name='Trimsheet Index',
        default=-1,
        min=-1,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    extend: bpy.props.BoolProperty(
        name='Extend Selection',
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    select: bpy.props.BoolProperty(
        name='Select Trim',
        default=True,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):

        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_data is not None:
            n_count = len(p_data.trimsheet)
            if self.trimsheet_index in range(n_count):
                if event.shift:
                    self.extend = True
                    self.select = not p_data.trimsheet[self.trimsheet_index].selected
                elif event.ctrl:
                    self.extend = True
                    self.select = False
                else:
                    self.select = True
                    self.extend = False

                return self.execute(context)
        return {'CANCELLED'}

    def execute(self, context: bpy.types.Context):
        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_data is not None:
            n_count = len(p_data.trimsheet)
            if self.trimsheet_index in range(n_count):

                if not self.extend:
                    arr_selected = [False] * n_count
                    arr_selected[self.trimsheet_index] = self.select
                    p_data.trimsheet.foreach_set("selected", arr_selected)

                    if p_data.trimsheet_index != self.trimsheet_index:
                        p_data.trimsheet_index = self.trimsheet_index
                else:
                    p_data.trimsheet[self.trimsheet_index].selected = self.select

                ZuvTrimsheetUtils.fix_undo()
                update_areas_in_all_screens(context)

                return {'FINISHED'}

        return {'CANCELLED'}


class ZuvTrimAddItemBase:
    bl_label = 'Add Trim'
    bl_description = 'Adds trim to trimsheet'
    bl_options = {'REGISTER', 'UNDO'}

    color: bpy.props.FloatVectorProperty(
        name="Color",
        description="Trim's color",
        subtype='COLOR',
        default=(0.0, 0.0, 0.0),
        size=3,
        min=0,
        max=1,
        options={'HIDDEN'}

    )

    def get_rectangle(self, context: bpy.types.Context):
        # left, top, right, bottom
        return (0.25, 0.75, 0.75, 0.25)

    def invoke(self, context, event):
        if self.color[:] == (0.0, 0.0, 0.0):
            self.color = ZuvTrimsheetUtils.getTrimsheetRandomColor()
        return self.execute(context)

    def execute(self, context: bpy.types.Context):
        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_data is not None:
            if self.color[:] == (0.0, 0.0, 0.0):
                self.color = ZuvTrimsheetUtils.getTrimsheetRandomColor()

            p_rect = self.get_rectangle(context)

            p_data.trimsheet.add()
            n_count = len(p_data.trimsheet)
            p_data.trimsheet[-1].name_ex = 'Trim'
            p_data.trimsheet[-1].color = self.color
            p_data.trimsheet[-1].set_rectangle(*p_rect)
            p_data.trimsheet_index = n_count - 1

            p_data.trimsheet_mark_geometry_update()

            ZuvTrimsheetUtils.auto_highlight_trims(context)

            ZuvTrimsheetUtils.fix_undo()
            update_areas_in_all_screens(context)

            return {'FINISHED'}
        else:
            return {'CANCELLED'}


class ZUV_OT_TrimAddItem(bpy.types.Operator, ZuvTrimAddItemBase):
    bl_idname = "uv.zuv_trim_add"


class ZUV_OT_TrimAddSizedItem(bpy.types.Operator, ZuvTrimAddItemBase):
    bl_idname = "uv.zuv_trim_add_sized"

    size: bpy.props.FloatProperty(
        name='Size',
        description='Size of the Trim',
        min=0.0,
        default=0.0
    )

    def get_rectangle(self, context: bpy.types.Context):
        if context.area.type == 'IMAGE_EDITOR':
            region = context.region
            rgn2d = region.view2d
            n_panel_width = [region.width for region in context.area.regions if region.type == "UI"][0]
            tools_width = [region.width for region in context.area.regions if region.type == "TOOLS"][0]
            free_zone = region.width - n_panel_width - tools_width

            trim_pos_x = tools_width + free_zone
            t_size = min(trim_pos_x, region.height) * 0.2

            trim_pos_x *= 0.5
            x, y, = rgn2d.region_to_view(trim_pos_x, region.height / 2)

            x_size, y_size, = rgn2d.region_to_view(trim_pos_x + t_size, y)
            if self.size == 0.0:
                t_size = (x - x_size) * 0.8
            else:
                t_size = self.size * 0.5

        else:
            x = y = 0.5
            if self.size == 0.0:
                t_size = 0.1
            else:
                t_size = self.size

        return (x - t_size, y + t_size, x + t_size, y - t_size)


class ZUV_OT_TrimRemoveItem(bpy.types.Operator):
    bl_idname = "uv.zuv_trim_remove"
    bl_label = 'Remove Trim'
    bl_description = 'Remove active Trim from Trimsheet'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context: bpy.types.Context):
        return ZuvTrimsheetUtils.getActiveTrim(context) is not None

    def execute(self, context: bpy.types.Context):
        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_data is not None:
            n_count = len(p_data.trimsheet)
            idx = p_data.trimsheet_index
            if idx in range(0, n_count):
                p_data.trimsheet.remove(idx)
                p_data.trimsheet_index = max(idx - 1, 0) if n_count > 1 else -1

                p_data.trimsheet_mark_geometry_update()
                ZuvTrimsheetUtils.fix_undo()
                ZuvTrimsheetUtils.update_imageeditor_in_all_screens()

                return {'FINISHED'}

        return {'CANCELLED'}


class ZUV_OT_TrimRemoveItemUI(bpy.types.Operator):
    bl_idname = "uv.zuv_trim_remove_ui"
    bl_label = 'Remove Trim'
    bl_description = (
        'Remove active Trim from Trimsheet\n'
        '* Shift - Remove selected Trims from Trimsheet')
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context: bpy.types.Context):
        return ZuvTrimsheetUtils.getTrimsheetSelectedAndActiveCount(context) > 0

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.shift:
            return bpy.ops.uv.zuv_trim_delete_all(use_dialog=False, mode='SELECTED')
        else:
            return bpy.ops.uv.zuv_trim_remove()


class ZUV_OT_TrimDuplicate(bpy.types.Operator):
    bl_idname = "uv.zuv_trim_duplicate"
    bl_label = 'Duplicate Trim'
    bl_description = 'Duplicate active or selected Trims in Trimsheet'
    bl_options = {'REGISTER'}

    mode: bpy.props.EnumProperty(
        name='Mode',
        items=[
            ('ACTIVE', 'Active', 'Duplicate active trim'),
            ('SELECTED', 'Selected', 'Duplicate selected trims'),
        ],
        default='ACTIVE'
    )

    ignore_color: bpy.props.BoolProperty(
        name='Ignore Color',
        description='Does not copy trim color settings',
        default=True
    )
    clear_selection: bpy.props.BoolProperty(
        name="Clear Selection",
        description="Clear trimsheet selection",
        default=True
    )

    @classmethod
    def poll(self, context: bpy.types.Context):
        return ZuvTrimsheetUtils.getTrimsheetSelectedAndActiveCount(context) > 0

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):

        ZuvTrimsheetUtils.fix_undo()

        def clone_trim(p_source, p_idx, p_trimsheet):
            p_skipped = {'name', 'uuid'}
            if self.ignore_color:
                p_skipped.add('color')
                p_skipped.add('border_color')

            def fn_skip_prop(inst, attr):
                if inst == p_source and attr in p_skipped:
                    return True
                return False

            p_dict = p_source.to_dict(fn_skip_prop=fn_skip_prop)
            s_was_name = p_source.name

            p_trimsheet.add()
            p_trimsheet[-1].color = ZuvTrimsheetUtils.getTrimsheetRandomColor()
            p_trimsheet[-1].from_dict(p_dict)
            p_trimsheet[-1].name_ex = s_was_name if 'copy' in s_was_name else (s_was_name + ' copy')
            p_trimsheet[-1].selected = True

            p_new_index = len(p_trimsheet) - 1
            if p_new_index - p_idx > 1:
                p_trimsheet.move(p_new_index, p_idx + 1)
                return p_trimsheet[p_idx + 1]
            else:
                return p_trimsheet[-1]

        p_owner = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_owner:
            p_trimsheet = p_owner.trimsheet
            idx = p_owner.trimsheet_index
            p_first_uuid = None
            if self.mode == 'ACTIVE':
                p_trim = ZuvTrimsheetUtils.getActiveTrimFromOwner(p_owner)
                if p_trim:
                    p_cloned = clone_trim(p_trim, idx, p_trimsheet)
                    p_first_uuid = p_cloned.uuid
                    if self.clear_selection:
                        p_trim.selected = False
            else:
                p_indices = ZuvTrimsheetUtils.getTrimsheetSelectedIndices(p_trimsheet)
                if self.clear_selection:
                    for it_idx in p_indices:
                        p_trimsheet[it_idx].selected = False

                for it_idx in reversed(p_indices):
                    p_cloned = clone_trim(p_trimsheet[it_idx], it_idx, p_trimsheet)
                    if p_first_uuid is None:
                        p_first_uuid = p_cloned.uuid

            if p_first_uuid is not None:
                new_idx = ZuvTrimsheetUtils.indexOfTrimByUuid(p_trimsheet, p_first_uuid)
                if p_owner.trimsheet_index != new_idx:
                    p_owner.trimsheet_index = new_idx

                p_owner.trimsheet_mark_geometry_update()

                ZuvTrimsheetUtils.auto_highlight_trims(context)

                ZuvTrimsheetUtils.fix_undo()
                update_areas_in_all_screens(context)
                bpy.ops.ed.undo_push(message='Duplicate Trim(s)')

                return {'FINISHED'}
            else:
                self.report({'INFO'}, 'Nothing selected to duplicate!')
        else:
            self.report({'INFO'}, 'No Trimsheet Data!')

        return {'CANCELLED'}


class ZUV_OT_TrimDeleteAll(bpy.types.Operator):
    bl_idname = "uv.zuv_trim_delete_all"
    bl_label = 'Delete Trims'
    bl_description = 'Delete all, selected, duplicated or empty Trims'
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        name='Mode',
        description='Deletion trims mode',
        items=[
            ('ALL', 'All', 'Delete all trims in trimsheet'),
            ('SELECTED', 'Selected', 'Delete selected trims in trimsheet'),
            ('EMPTY', 'Empty', 'Delete trims with zero width or height'),
            ('DUPLICATES', 'Duplicates', 'Delete trims with duplicated dimensions'),
        ],
        default='ALL'
    )

    use_dialog: bpy.props.BoolProperty(
        name='Use Dialog',
        description='Call dialog to select properties',
        default=True,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        col = layout.column(align=True)
        col.use_property_split = True
        col.prop(self, 'mode', expand=True)

    @classmethod
    def poll(self, context: bpy.types.Context):
        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        return p_data is not None

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if self.use_dialog:
            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def execute(self, context: bpy.types.Context):
        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_data is not None:
            p_trimsheet = p_data.trimsheet
            n_count = len(p_trimsheet)
            if n_count > 0:
                if self.mode == 'ALL':
                    p_trimsheet.clear()
                elif self.mode == 'SELECTED':
                    for idx in reversed(ZuvTrimsheetUtils.getTrimsheetSelectedIndices(p_trimsheet)):
                        p_trimsheet.remove(idx)
                elif self.mode == 'EMPTY':
                    for idx in range(n_count - 1, -1, -1):
                        p_trim = p_trimsheet[idx]
                        if p_trim.is_empty():
                            p_trimsheet.remove(idx)
                elif self.mode == 'DUPLICATES':
                    # we use this approach to delete last duplicates
                    p_duplicates = defaultdict(list)
                    for idx, p_trim in enumerate(p_trimsheet):
                        left, top, right, bottom = p_trim.rect
                        p_rounded = (round(left, 3), round(top, 3), round(right, 3), round(bottom, 3))

                        p_duplicates[p_rounded].append(idx)

                    p_del_indices = set()
                    for v in p_duplicates.values():
                        if len(v) > 1:
                            p_del_indices.update(v[1:])

                    for idx in range(n_count - 1, -1, -1):
                        if idx in p_del_indices:
                            p_trimsheet.remove(idx)

                if p_data.trimsheet_index not in range(len(p_trimsheet)):
                    p_data.trimsheet_index = min(0, len(p_trimsheet) - 1)

                p_data.trimsheet_mark_geometry_update()
                ZuvTrimsheetUtils.fix_undo()
                ZuvTrimsheetUtils.update_imageeditor_in_all_screens()

                return {'FINISHED'}

        return {'CANCELLED'}


class ZUV_OT_TrimCopyToClipboard(bpy.types.Operator):
    bl_idname = "uv.zuv_copy_trimsheet"
    bl_label = 'Copy'
    bl_description = 'Copy Trims to clipboard'
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        name='Mode',
        items=[
            ('ACTIVE', 'Active', 'Copy active trim'),
            ('SELECTED', 'Selected', 'Copy selected trims'),
            ('ALL', 'All', 'Copy all trims in the trimsheet')
        ],
        default='ACTIVE'
    )

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, 'mode', expand=True)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):

        p_out = ZuvTrimsheetUtils.export_to_json(context, self)
        if p_out:
            context.window_manager.clipboard = p_out
            return {'FINISHED'}

        return {'CANCELLED'}


class ZUV_OT_TrimPasteFromClipboard(bpy.types.Operator):
    bl_idname = "uv.zuv_paste_trimsheet"
    bl_label = 'Paste'
    bl_description = 'Paste Trims from clipboard'
    bl_options = {'REGISTER', 'UNDO'}

    mode: TrimImportUtils.paste_mode

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        col = layout.column(align=True)
        col.use_property_split = True
        col.prop(self, 'mode', expand=True)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        try:
            wm = context.window_manager
            json_data = wm.clipboard
            ZuvTrimsheetUtils.import_from_json(context, self, json_data)

            ZuvTrimsheetUtils.auto_highlight_trims(context)

            ZuvTrimsheetUtils.fix_undo()
            ZuvTrimsheetUtils.update_imageeditor_in_all_screens()

            return {'FINISHED'}
        except json.decoder.JSONDecodeError as e:
            self.report({'ERROR'}, 'Invalid clipboard JSON: ' + str(e))
        except Exception as e:
            self.report({'ERROR'}, str(e))

        return {'CANCELLED'}


class ZUV_OT_TrimMoveItem(bpy.types.Operator):
    bl_idname = "uv.zuv_trim_move"
    bl_label = 'Move Trims Up | Down'
    bl_description = 'Moves active Trim Up | Down in Trimsheet'
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        items=(
            ('UP', 'Up', ""),
            ('DOWN', 'Down', "")
        ),
        options={'HIDDEN', 'SKIP_SAVE'},
        default='UP'
    )

    mode: bpy.props.EnumProperty(
        name='Mode',
        items=(
            ('ACTIVE', 'Active', "Moves active trim up | down in the trimsheet"),
            ('SELECTED_UP_DOWN', 'Selected Up | Down', "Moves selected trims up | down in the trimsheet"),
            ('SELECTED_TOP_BOTTOM', 'Selected Top | Bottom', "Moves selected trims to the top | bottom of the trimsheet"),
            ('SELECTED_FIRST_LAST', 'Selected First | Last', "Moves selected trims to the first | last selected")
        ),
        # options={'HIDDEN', 'SKIP_SAVE'},
        default='ACTIVE'
    )

    keep_intervals: bpy.props.BoolProperty(
        name='Keep Intervals',
        description='Keep intervals in list between selected trims',
        default=True
    )

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.use_property_split = True

        row = layout.row(align=True)
        row.enabled = False
        row.prop(self, 'mode')

        if self.mode not in {'ACTIVE', 'SELECTED_FIRST_LAST'}:
            layout.prop(self, 'keep_intervals')

    @classmethod
    def description(cls, context: bpy.types.Context, properties: bpy.types.OperatorProperties) -> str:
        s_direction = bpy.types.UILayout.enum_item_name(properties, 'direction', properties.direction)
        s_top_bottom = 'top' if properties.direction == 'UP' else 'bottom'
        s_first_last = 'first' if properties.direction == 'UP' else 'last'
        return (
            f'Moves active trim {s_direction.lower()} in the trimsheet\n'
            f'* Shift - Move selected Trims {s_direction.lower()} in Trimsheet\n'
            f'* Ctrl - Move selected Trims to the {s_top_bottom} of Trimsheet\n'
            f'* Shift + Ctrl - Move selected Trims to the {s_first_last} selected Trim in Trimsheet')

    @classmethod
    def poll(cls, context):
        return len(ZuvTrimsheetUtils.getTrimsheet(context)) > 1

    def move_index(self, context):
        """ Move index of an item render queue while clamping it. """
        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_data is not None:
            index = p_data.trimsheet_index
            list_length = len(p_data.trimsheet) - 1
            # (index starts at 0)
            new_index = index + (-1 if self.direction == 'UP' else 1)
            i_new_index = max(0, min(new_index, list_length))
            if i_new_index != p_data.trimsheet_index:
                p_data.trimsheet_index = i_new_index

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.shift and event.ctrl:
            self.mode = 'SELECTED_FIRST_LAST'
        elif event.shift:
            self.mode = 'SELECTED_UP_DOWN'
        elif event.ctrl:
            self.mode = 'SELECTED_TOP_BOTTOM'
        else:
            self.mode = 'ACTIVE'

        return self.execute(context)

    def execute(self, context):
        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_data is not None:
            p_trimsheet = p_data.trimsheet
            n_trims_count = len(p_trimsheet)
            p_list = p_data.trimsheet
            index = p_data.trimsheet_index

            if self.mode == 'ACTIVE':
                neighbor = index + (-1 if self.direction == 'UP' else 1)
                p_list.move(neighbor, index)
                self.move_index(context)
            else:
                p_indices = ZuvTrimsheetUtils.getTrimsheetSelectedIndices(p_trimsheet)
                if len(p_indices) > 0:

                    b_keep_intervals = False if self.mode == 'SELECTED_FIRST_LAST' else self.keep_intervals

                    if self.direction == 'UP':
                        i_min = 0
                        if self.mode == 'SELECTED_UP_DOWN':
                            i_min = max(p_indices[0] - 1, 0)
                        elif self.mode == 'SELECTED_FIRST_LAST':
                            i_min = max(p_indices[0], 0)
                        i_count = i_min
                        for idx in p_indices:
                            i_new_idx = (
                                i_min + (idx - p_indices[0])
                                if b_keep_intervals else i_count)
                            p_list.move(idx, i_new_idx)
                            if p_data.trimsheet_index == idx:
                                p_data.trimsheet_index = i_new_idx
                            i_count += 1
                    else:
                        n_indices_count = len(p_indices)

                        i_last = n_indices_count - 1

                        i_max = n_trims_count - 1
                        if self.mode == 'SELECTED_UP_DOWN':
                            i_max = min(p_indices[i_last] + 1, n_trims_count - 1)
                        elif self.mode == 'SELECTED_FIRST_LAST':
                            i_max = min(p_indices[i_last], n_trims_count - 1)

                        i_count = i_max
                        for idx in reversed(p_indices):
                            i_new_idx = (
                                i_max - (p_indices[i_last] - idx)
                                if b_keep_intervals else i_count)
                            p_list.move(idx, i_new_idx)
                            if p_data.trimsheet_index == idx:
                                p_data.trimsheet_index = i_new_idx
                            i_count -= 1

            p_data.trimsheet_mark_geometry_update()
            ZuvTrimsheetUtils.fix_undo()
            ZuvTrimsheetUtils.update_imageeditor_in_all_screens()

            return {'FINISHED'}

        return {'CANCELLED'}


class ZUV_OT_TrimFrame(bpy.types.Operator):
    bl_idname = "uv.zuv_trim_frame"
    bl_label = 'Frame Trim'
    bl_description = 'Move view to active Trim center in UV Editor'
    bl_options = {'REGISTER', 'UNDO'}

    mode: bpy.props.EnumProperty(
        name='Mode',
        items=[
            ('ACTIVE', 'Active', 'View active trim'),
            ('SELECTED', 'Selected', 'View selected trims'),
        ],
        default='ACTIVE'
    )

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, 'mode', expand=True)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return ZuvTrimsheetUtils.isImageEditorSpace(context)

    @classmethod
    def description(cls, context: bpy.types.Context, properties: bpy.types.OperatorProperties) -> str:
        s_mode = bpy.types.UILayout.enum_item_name(properties, "mode", properties.mode)
        return f'Move view to {s_mode.lower()} Trim center in UV Editor'

    def view_zoom(self, p_override, xmin, xmax, ymin, ymax):
        rgn = p_override['region']

        p_view_coords_1 = list(rgn.view2d.view_to_region(xmin, ymin, clip=False))
        p_view_coords_2 = list(rgn.view2d.view_to_region(xmax, ymax, clip=False))

        p_view_coords_1[0] = round(p_view_coords_1[0])
        p_view_coords_1[1] = round(p_view_coords_1[1])

        p_view_coords_2[0] = round(p_view_coords_2[0])
        p_view_coords_2[1] = round(p_view_coords_2[1])


        if ZenPolls.version_greater_3_2_0:
            with bpy.context.temp_override(**p_override):
                bpy.ops.image.view_zoom_border(
                    xmin=p_view_coords_1[0], xmax=p_view_coords_2[0],
                    ymin=p_view_coords_1[1], ymax=p_view_coords_2[1],
                    wait_for_input=False, zoom_out=False)
        else:
            bpy.ops.image.view_zoom_border(
                p_override,
                xmin=p_view_coords_1[0], xmax=p_view_coords_2[0],
                ymin=p_view_coords_1[1], ymax=p_view_coords_2[1],
                wait_for_input=False, zoom_out=False)

        area = p_override['area']

        area.tag_redraw()

    def execute(self, context: bpy.types.Context):
        try:
            if not ZuvTrimsheetUtils.isImageEditorSpace(context):
                raise RuntimeError('Only ImageEditor context is supported!')

            xmin = 0
            xmax = 0
            ymin = 0
            ymax = 0

            if self.mode == 'ACTIVE':
                p_trim = ZuvTrimsheetUtils.getActiveTrim(context)
                if p_trim is None:
                    raise RuntimeError('No active trim!')

                xmin, ymax, xmax, ymin = p_trim.rect
            elif self.mode == 'SELECTED':
                p_trimsheet = ZuvTrimsheetUtils.getTrimsheet(context)
                if p_trimsheet is None:
                    raise RuntimeError('No active trimsheet!')
                p_rects = [p_trimsheet[idx].rect for idx in ZuvTrimsheetUtils.getTrimsheetSelectedIndices(p_trimsheet)]
                if len(p_rects) == 0:
                    raise RuntimeError('No selected trims!')
                xmin_arr, ymax_arr, xmax_arr, ymin_arr = zip(*p_rects)
                xmin = min(xmin_arr)
                xmax = max(xmax_arr)
                ymin = min(ymin_arr)
                ymax = max(ymax_arr)

            if xmax - xmin == 0 or ymax - ymin == 0:
                raise RuntimeError('Can not frame empty trim(s)!')

            bpy.ops.image.view_zoom_ratio('INVOKE_DEFAULT', ratio=1.0)
            bpy.ops.image.view_all('INVOKE_DEFAULT', fit_view=True)

            context.area.tag_redraw()

            # this function does not recalculate region dimensions, so we need to put in queue
            bpy.app.timers.register(partial(self.view_zoom, context.copy(), xmin, xmax, ymin, ymax), first_interval=0.016)
            return {'FINISHED'}
        except Exception as e:
            self.report({'WARNING'}, str(e))
        return {'CANCELLED'}


class ZUV_OT_TrimsSetProps(bpy.types.Operator):
    bl_idname = "wm.zenuv_set_props_to_trims"
    bl_label = "Set Props to Trims"
    bl_options = {'REGISTER', 'UNDO'}

    data_path: bpy.props.StringProperty(
        name='Data Path',
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    data_value: bpy.props.StringProperty(
        name='Data Value',
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    mode: bpy.props.EnumProperty(
        name='Mode',
        items=[
            ('SINGLE_PARAM', 'Single Param', ''),
            ('ADVANCED_PARAMS', 'Advanced Params', ''),
            ('TAGS', 'Tags', '')
        ],
        default='SINGLE_PARAM',
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    @classmethod
    def description(cls, context: bpy.types.Context, properties: bpy.types.OperatorProperties) -> str:
        if properties.mode == 'TAGS':
            return (
                'Set current trim tags to all selected trims\n'
                '* Shift - Set all advanced settings')

        if properties.mode == 'ADVANCED_PARAMS':
            return 'Set all Advanced Settings to all selected trims'

        p_trim = ZuvTrimsheetUtils.getActiveTrim(context)
        if p_trim:
            prop = p_trim.bl_rna.properties.get(properties.data_path)
            s_val = properties.data_value
            if isinstance(prop, bpy.types.FloatProperty):
                s_val = f'{getattr(p_trim, properties.data_path):.2f}'
            return (
                f"Set '{prop.name}' with value '{s_val}' to all selected trims\n"
                "* Shift - Set all advanced settings")
        return ""

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return ZuvTrimsheetUtils.getTrimsheet(context) is not None

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.shift:
            self.mode = 'ADVANCED_PARAMS'
        return self.execute(context)

    def execute(self, context: bpy.types.Context):
        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_data is not None:
            p_trim = ZuvTrimsheetUtils.getActiveTrimFromOwner(p_data)
            if p_trim:
                p_trimsheet = p_data.trimsheet
                sel_indices = ZuvTrimsheetUtils.getTrimsheetSelectedAndActiveIndices(p_trimsheet)
                if len(sel_indices) >= 2:

                    t_dict = None
                    fn_skip = None

                    b_TAGS_MODE = self.mode == 'TAGS'
                    b_ADV_PARAMS_MODE = self.mode == 'ADVANCED_PARAMS'

                    if b_TAGS_MODE:
                        def fn_skip_not_tags(it_trim, inst, attr):
                            if inst == it_trim and attr not in {'tags', 'tag_index'}:
                                return True
                            return False

                        fn_skip = fn_skip_not_tags
                        t_dict = p_trim.to_dict(fn_skip_prop=partial(fn_skip, p_trim))
                    elif b_ADV_PARAMS_MODE:
                        t_filtered_props = {
                            'selected',
                            'uuid',
                            'normal'
                        }

                        t_advanced_props = p_trim.get_common_props(skipped=t_filtered_props)
                        t_advanced_props.append('tags')
                        t_advanced_props.append('tag_index')

                        def fn_skip_not_adv(it_trim, inst, attr):
                            if inst == it_trim and attr not in t_advanced_props:
                                return True
                            return False

                        fn_skip = fn_skip_not_adv
                        t_dict = p_trim.to_dict(fn_skip_prop=partial(fn_skip, p_trim))

                    for idx in sel_indices:
                        it_trim = p_trimsheet[idx]
                        if p_trim != it_trim:
                            if b_TAGS_MODE or b_ADV_PARAMS_MODE:
                                it_trim.from_dict(t_dict, fn_skip_prop=partial(fn_skip, it_trim))
                            else:
                                setattr(it_trim, self.data_path, eval(self.data_value))

                    p_data.trimsheet_mark_geometry_update()
                    ZuvTrimsheetUtils.fix_undo()
                    update_areas_in_all_screens(context)

        return {'FINISHED'}


class ZUV_OT_TrimBatchRename(bpy.types.Operator):
    bl_idname = 'wm.zuv_trim_batch_rename'
    bl_label = 'Batch Rename'
    bl_description = "If 'what' is empty, text will be completely replaced with 'replace' value"
    bl_options = {'REGISTER', 'UNDO'}

    group_mode: bpy.props.EnumProperty(
        name='Mode',
        items=[
            ('SELECTED', 'Selected', ''),
            ('ALL', 'All', ''),
        ],
        default='ALL')
    find: bpy.props.StringProperty(name='Find')
    replace: bpy.props.StringProperty(name='Replace')
    match_case: bpy.props.BoolProperty(name='Match Case', default=True)
    use_counter: bpy.props.BoolProperty(name='Counter', default=False)
    start_from: bpy.props.IntProperty(name='Start from', default=1)
    use_regex: bpy.props.BoolProperty(
        name='Use Regex',
        description='Use Replace by Regular Expression',
        default=False
    )

    def execute(self, context):
        if self.replace == '' and self.find == '':
            self.report({'WARNING'}, 'Nothing was defined to replace!')
            return {'CANCELLED'}

        i_start = self.start_from
        is_modified = False

        try:
            p_data = ZuvTrimsheetUtils.getActiveTrimData(context)
            if p_data is None:
                self.report({'WARNING'}, 'No Active Trim!')
                return {'CANCELLED'}

            act_idx, p_trim, p_trimsheet = p_data

            for it_trim in p_trimsheet:
                if self.group_mode == 'SELECTED':
                    if not it_trim.selected and it_trim != p_trim:
                        continue

                p_old_name = it_trim.name
                new_name, err = ZenStrUtils.smart_replace(p_old_name, self)
                if err:
                    raise RuntimeError(err)

                if self.use_counter:
                    new_name = new_name + str(i_start)
                    i_start += 1

                if p_old_name != new_name:
                    it_trim.name_ex = new_name
                    is_modified = True
        except Exception as e:
            self.report({'ERROR'}, str(e))
            is_modified = True

        if is_modified:
            ZuvTrimsheetUtils.fix_undo()
            update_areas_in_all_screens(context)

            return {'FINISHED'}
        else:
            self.report({'WARNING'}, 'No replace matches found!')

        return {'CANCELLED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "group_mode", expand=True)
        layout.prop(self, "find")
        layout.prop(self, "replace")
        layout.prop(self, "match_case")
        layout.prop(self, 'use_regex')
        row = layout.row()
        row.prop(self, "use_counter")
        row.prop(self, "start_from")

        p_trim = ZuvTrimsheetUtils.getActiveTrim(context)
        if p_trim:
            box = layout.box()
            box.label(text='Preview')

            p_old_name = p_trim.name
            p_new_name, err = ZenStrUtils.smart_replace(p_old_name, self)

            if self.use_counter:
                p_new_name = p_new_name + str(self.start_from)

            col = box.column(align=True)
            col.alert = err != ''
            col.active = p_old_name != p_new_name
            row = col.row(align=True)
            row = row.split(factor=0.2)
            row.label(text='Old:')
            row.label(text=p_old_name)

            row = col.row(align=True)
            row = row.split(factor=0.2)
            row.label(text='New:')
            row.label(text=p_new_name)

            if err:
                row = box.row(align=True)
                row.alert = True
                row.label(text='ERROR: ' + err, icon='ERROR')
