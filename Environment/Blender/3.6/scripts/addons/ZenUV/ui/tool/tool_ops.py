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
from mathutils import Vector, Matrix

from ZenUV.utils.constants import UV_AREA_BBOX
from ZenUV.utils.blender_zen_utils import update_areas_in_all_screens, rsetattr
from ZenUV.utils.vlog import Log
from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils

from timeit import default_timer as timer


class ZUV_OT_ToolTrimHandle(bpy.types.Operator):
    bl_idname = 'zenuv.tool_trim_handle'
    bl_label = 'Align|Fit|Flip Trims'
    bl_options = {'INTERNAL'}

    direction: bpy.props.StringProperty(
        name='Handle Direction',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    mode: bpy.props.EnumProperty(
        name='Mode',
        items=[
            ('ALIGN', 'Align', ''),
            ('FIT', 'Fit', ''),
            ('FLIP', 'Flip', ''),
            ('ROTATE', 'Rotate', ''),
            ('ORIENT', 'Orient', ''),

            ('PIVOT', 'Island Pivot', ''),
            ('UNWRAP', 'Unwrap', ''),
            ('WORLD_ORIENT', 'World Orient', ''),
            ('SELECT_BY_FACE', 'Trim By Face', 'Trim select by active face'),
        ],
        default='ALIGN',
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    pivot_prop: bpy.props.StringProperty(
        name='Pivot Property',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def __init__(self) -> None:
        self._timer = None
        self._last_click = 0

    def cancel(self, context: bpy.types.Context):
        if self._timer is not None:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
            self._timer = None
        self._last_click = 0

    @classmethod
    def description(cls, context: bpy.types.Context, properties: bpy.types.OperatorProperties):
        from ZenUV.ops.transform_sys.trim_depend_transform import (
            ZUV_OT_TrAlignToTrim,
            ZUV_OT_TrFlipInTrim,
            ZUV_OT_TrFitToTrim
        )

        from ZenUV.ops.transform_sys.tr_rotate import (
            ZUV_OT_TrRotate3DV
        )

        s_out = [
            ZUV_OT_TrAlignToTrim.bl_description,
            ' * Ctrl - ' + ZUV_OT_TrRotate3DV.bl_description,
            ' * Shift - ' + ZUV_OT_TrFitToTrim.bl_description,
            ' * Ctrl+Shift - ' + ZUV_OT_TrFlipInTrim.bl_description
        ]

        s_double = ['-----------------------']
        if properties.pivot_prop:
            s_double.append(
                ' * Double Click - Set Transform Pivot'
            )
        if properties.direction == 'cen':
            s_double.append(
                ' * Double Click+Shift - Unwrap'
            )
            s_double.append(
                ' * Double Click+Ctrl - World Orient'
            )
            s_double.append(
                ' * Double Click+Ctrl+Shift - Trim by Face'
            )

        if len(s_double) > 1:
            s_out += s_double

        return '\n'.join(s_out)

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if self._timer is None:
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.cancel(context)

            if self.mode == 'FIT':
                self.mode = 'UNWRAP'
                return self.execute(context)
            elif self.mode in {'ROTATE', 'ORIENT'}:
                self.mode = 'WORLD_ORIENT'
                return self.execute(context)
            elif self.mode == 'FLIP':
                self.mode = 'SELECT_BY_FACE'
                return self.execute(context)
            elif self.pivot_prop:
                self.mode = 'PIVOT'
                return self.execute(context)

            return {'CANCELLED'}

        if timer() - self._last_click > 0.3:
            self.cancel(context)
            return self.execute(context)

        return {'RUNNING_MODAL'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if self._timer is not None:
            return {'CANCELLED'}

        self.mode = 'ALIGN'
        if event.ctrl and event.shift:
            self.mode = 'FLIP'
        elif event.ctrl:
            self.mode = (
                'ROTATE' if self.direction in UV_AREA_BBOX.bbox_corner_handles else
                'ORIENT')
        elif event.shift:
            self.mode = 'FIT'

        if self.pivot_prop or ((event.ctrl or event.shift) and self.direction == 'cen'):
            wm = context.window_manager
            wm.modal_handler_add(self)

            self._timer = wm.event_timer_add(0.1, window=context.window)
            self._last_click = timer()

            return {'RUNNING_MODAL'}
        else:
            return self.execute(context)

    def execute(self, context: bpy.types.Context):
        try:
            if self.mode == 'ALIGN':
                return bpy.ops.uv.zenuv_align_to_trim(
                    'INVOKE_DEFAULT', True,
                    align_direction=self.direction,
                    island_pivot=self.direction,
                    i_pivot_as_direction=True,
                    )
            elif self.mode == 'ROTATE':
                if self.direction in UV_AREA_BBOX.bbox_not_bottom_left:
                    angle = 90
                if self.direction == UV_AREA_BBOX.bbox_bottom_left:
                    angle = -90
                return bpy.ops.view3d.zenuv_rotate(
                    'INVOKE_DEFAULT', True,
                    rotation_mode='ANGLE',
                    tr_rot_inc_full_range=angle)
            elif self.mode == 'ORIENT':
                if self.direction in UV_AREA_BBOX.bbox_horizontal_handles:
                    orient_dir = 'HORIZONTAL'
                elif self.direction in UV_AREA_BBOX.bbox_vertical_handles:
                    orient_dir = "VERTICAL"
                elif self.direction == 'cen':
                    orient_dir = "AUTO"
                return bpy.ops.uv.zenuv_orient_island(
                    'INVOKE_DEFAULT',
                    mode='BBOX',
                    orient_direction=orient_dir,
                    rotate_direction='CW')
            elif self.mode == 'FIT':
                return bpy.ops.uv.zenuv_fit_to_trim(
                    'INVOKE_DEFAULT', True,
                    op_align_to=self.direction,
                    )
            elif self.mode == 'FLIP':
                return bpy.ops.uv.zenuv_flip_in_trim(
                    'INVOKE_DEFAULT', True,
                    direction=self.direction)
            elif self.mode == 'PIVOT':
                if self.pivot_prop:
                    p_scene = context.scene
                    rsetattr(p_scene, self.pivot_prop, self.direction)
                    context.area.tag_redraw()
            elif self.mode == 'UNWRAP':
                return bpy.ops.uv.zenuv_unwrap_for_tool(
                    'INVOKE_DEFAULT', True)
            elif self.mode == 'WORLD_ORIENT':
                return bpy.ops.uv.zenuv_world_orient(
                    'INVOKE_DEFAULT', True)
            elif self.mode == 'SELECT_BY_FACE':
                return bpy.ops.uv.zenuv_trim_select_by_face(
                    'INVOKE_DEFAULT', True)
            return {'FINISHED'}

        except Exception as e:
            self.report({'WARNING'}, str(e))

        return {'CANCELLED'}


class ZUV_OT_ToolAreaUpdate(bpy.types.Operator):
    bl_idname = 'zenuv.tool_area_update'
    bl_label = 'Update UV and 3D Areas'
    bl_description = 'Internal Zen UV tool operator to update UV and 3D areas by hotkeys'
    bl_options = {'INTERNAL'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        bpy.ops.wm.zuv_event_service('INVOKE_DEFAULT')
        update_areas_in_all_screens(context)
        return {'PASS_THROUGH'}  # NEVER CHANGE THIS !


class ZUV_OT_ToolExitCreate(bpy.types.Operator):
    bl_idname = 'zenuv.tool_exit_create'
    bl_label = 'Exit Create Mode'
    bl_description = 'Exit Zen Uv tool create trims mode'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        p_scene = context.scene
        return p_scene.zen_uv.ui.uv_tool.trim_mode == 'CREATE'

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        p_scene = context.scene
        p_scene.zen_uv.ui.uv_tool.trim_mode = 'RESIZE'
        return {'PASS_THROUGH'}  # NEVER CHANGE THIS !


class ZUV_OT_TrimScrollFit(bpy.types.Operator):
    bl_idname = 'wm.zenuv_trim_scroll_fit'
    bl_label = 'Scroll Fit Trim'
    bl_description = 'Scroll active trim forward-backward and fit island(s) to it'
    bl_options = {'INTERNAL'}

    is_up: bpy.props.BoolProperty(
        default=False
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        p_data = ZuvTrimsheetUtils.getActiveTrimData(context)
        if p_data:
            idx, p_trim, p_trimsheet = p_data
            n_count = len(p_trimsheet)
            if n_count > 1:
                if self.is_up:
                    new_idx = idx + 1
                    if new_idx >= n_count:
                        new_idx = 0
                else:
                    new_idx = idx - 1
                    if new_idx < 0:
                        new_idx = n_count - 1

                if new_idx != idx:
                    bpy.ops.wm.zuv_trim_set_index(trimsheet_index=new_idx)
                    res = bpy.ops.uv.zenuv_fit_to_trim('INVOKE_DEFAULT', True)
                    context.area.tag_redraw()
                    return res
        return {'CANCELLED'}


class ZUV_OT_ToolScreenZoom(bpy.types.Operator):
    bl_idname = 'view3d.tool_screen_zoom'
    bl_label = 'Screen Select Scale'
    bl_description = 'Scale view3d tool in screen select mode'
    bl_options = {'INTERNAL'}

    is_up: bpy.props.BoolProperty(
        default=False
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        p_scene = context.scene
        return p_scene.zen_uv.ui.view3d_tool.is_screen_selector_position_enabled()

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        p_scene = context.scene
        p_scene.zen_uv.ui.view3d_tool.screen_scale += (0.1 if self.is_up else -0.1)
        context.area.tag_redraw()
        return {'FINISHED'}


class ZUV_OT_ToolScreenPan(bpy.types.Operator):
    bl_idname = 'view3d.tool_screen_pan'
    bl_label = 'Screen Select Pan'
    bl_description = 'Pan view3d tool in screen select mode'
    bl_options = {'INTERNAL'}

    def __init__(self) -> None:
        self.init_mouse = Vector((0, 0))
        self.init_value = Vector((0, 0))

    @classmethod
    def poll(cls, context: bpy.types.Context):
        p_scene = context.scene
        return p_scene.zen_uv.ui.view3d_tool.is_screen_selector_position_enabled()

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.value == 'RELEASE' or event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}

        delta = self.init_mouse - Vector((event.mouse_x, event.mouse_y))

        p_scene = context.scene

        value = self.init_value - delta

        p_scene.zen_uv.ui.view3d_tool.screen_pan_x = value.x
        p_scene.zen_uv.ui.view3d_tool.screen_pan_y = value.y

        context.area.tag_redraw()

        return {'RUNNING_MODAL'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        self.init_mouse = Vector((event.mouse_x, event.mouse_y))

        wm = context.window_manager
        p_scene = context.scene

        self.init_value = Vector((
            p_scene.zen_uv.ui.view3d_tool.screen_pan_x,
            p_scene.zen_uv.ui.view3d_tool.screen_pan_y
        ))

        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}


class ZUV_OT_ToolScreenReset(bpy.types.Operator):
    bl_idname = 'view3d.tool_screen_reset'
    bl_label = 'Screen Select Reset'
    bl_description = 'Reset scale and pan view3d tool in screen select mode'
    bl_options = {'INTERNAL'}

    mode: bpy.props.EnumProperty(
        name='Mode',
        items=[
            ('RESET', 'Reset', ''),
            ('CENTER', 'Center in view', '')
        ],
        default='RESET'
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        p_scene = context.scene
        tool_props = p_scene.zen_uv.ui.view3d_tool
        return tool_props.is_screen_selector_position_enabled()

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        p_scene = context.scene
        p_tool_props = p_scene.zen_uv.ui.view3d_tool

        p_trim_data = ZuvTrimsheetUtils.getActiveTrimData(context)

        if self.mode == 'RESET' or p_trim_data is None:
            p_tool_props.screen_scale = 1.0
            p_tool_props.screen_pan_x = 0.0
            p_tool_props.screen_pan_y = 0.0
        else:
            v_scr_cen = Vector(p_tool_props.screen_pos)
            v_scr_pan = Vector((p_tool_props.screen_pan_x, p_tool_props.screen_pan_y))
            d_rect_length = p_tool_props.screen_size

            v_scr = v_scr_cen - v_scr_pan
            v_start = v_scr - Vector((d_rect_length / 2, d_rect_length / 2))

            _, p_trim, p_trimsheet = p_trim_data
            bounds = ZuvTrimsheetUtils.getTrimsheetBounds(p_trimsheet)

            v_cen = Vector(p_trim.get_center()).to_3d()

            d_trimsheet_size = max(max(bounds.width, bounds.height), 1.0)
            d_trimsheet_size_ratio = 1.0 / d_trimsheet_size

            d_size = max(p_trim.width, p_trim.height) * 2.0 * d_trimsheet_size_ratio
            was_scale = p_tool_props.screen_scale

            if d_size != 0 and was_scale != 0:
                p_tool_props.screen_scale = 1 / d_size
                sca_diff = p_tool_props.screen_scale / was_scale
            else:
                sca_diff = 1.0

            mtx_pos = Matrix.Translation(v_start.resized(3))
            mtx_sca = Matrix.Diagonal((d_rect_length, d_rect_length, 1.0)).to_4x4()
            mtx = mtx_pos @ mtx_sca
            v_cen = mtx @ v_cen

            p_tool_props.screen_pan_x = (v_scr.x - v_cen.x) * sca_diff
            p_tool_props.screen_pan_y = (v_scr.y - v_cen.y) * sca_diff

        context.area.tag_redraw()
        return {'FINISHED'}


class ZUV_OT_ToolScreenSelector(bpy.types.Operator):
    bl_idname = 'view3d.tool_screen_selector'
    bl_label = 'Trim Screen Selector'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context: bpy.types.Context, properties: bpy.types.OperatorProperties) -> str:
        p_scene = context.scene
        t_out = ['Show screen viewport trim selector']
        if p_scene.zen_uv.ui.view3d_tool.enable_screen_selector:
            t_out.append('* Shift+Click - Lock screen selector position')
        return '\n'.join(t_out)

    mode: bpy.props.EnumProperty(
        name='Mode',
        items=[
            ('DEFAULT', 'Default', ''),
            ('LOCK', 'Lock', '')
        ],
        default='DEFAULT',
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        self.mode = 'DEFAULT'
        p_scene = context.scene
        if p_scene.zen_uv.ui.view3d_tool.enable_screen_selector:
            if event.shift:
                self.mode = 'LOCK'
        return self.execute(context)

    def execute(self, context: bpy.types.Context):
        p_scene = context.scene
        if self.mode == 'DEFAULT':
            p_scene.zen_uv.ui.view3d_tool.enable_screen_selector = not p_scene.zen_uv.ui.view3d_tool.enable_screen_selector
        elif self.mode == 'LOCK':
            p_scene.zen_uv.ui.view3d_tool.screen_position_locked = not p_scene.zen_uv.ui.view3d_tool.screen_position_locked

        context.area.tag_redraw()

        return {'FINISHED'}


class ZUV_OT_TrimActivateTool(bpy.types.Operator):
    bl_idname = "uv.zuv_activate_tool"
    bl_label = "Zen UV Tool"
    bl_description = 'Activate Zen UV tool'  # Is used for Pie
    bl_option = {'REGISTER'}

    mode: bpy.props.EnumProperty(
        name='Mode',
        description='Trim sheets data mode',
        items=[
            ('OFF', 'Off', ''),
            ('RESIZE', 'Resize', ''),
            ('CREATE', 'Create', ''),
            ('ACTIVATE', 'Activate', '')
        ],
        default='OFF'
    )

    prev_tool: bpy.props.StringProperty(
        name='Previous Tool',
        default=''
    )

    @classmethod
    def description(cls, context: bpy.types.Context, properties: bpy.types.OperatorProperties) -> str:
        if properties.mode == 'RESIZE':
            return "Activate Tool in Resize Trims mode"
        if properties.mode == 'CREATE':
            return "Activate Tool in Create Trims mode"
        if properties.mode == 'ACTIVATE':
            return "Activate Tool"

        return "Deactivate Tool"

    def set_uv_prev_tool(self, context: bpy.types.Context):
        _id_UV = getattr(context.workspace.tools.from_space_image_mode('UV', create=False), 'idname', None)
        if isinstance(_id_UV, str):
            self.prev_tool = _id_UV

    def execute(self, context: bpy.types.Context):
        if self.mode == 'CREATE':
            self.set_uv_prev_tool(context)

            bpy.context.scene.zen_uv.ui.uv_tool.category = 'TRIMS'
            bpy.context.scene.zen_uv.ui.uv_tool.trim_mode = 'CREATE'
            bpy.ops.wm.tool_set_by_id(name="zenuv.uv_tool")

        elif self.mode == 'RESIZE':
            self.set_uv_prev_tool(context)

            bpy.context.scene.zen_uv.ui.uv_tool.category = 'TRIMS'
            bpy.context.scene.zen_uv.ui.uv_tool.trim_mode = 'RESIZE'
            bpy.ops.wm.tool_set_by_id(name="zenuv.uv_tool")
        elif self.mode == 'ACTIVATE':
            self.prev_tool = ''
            if context.area.type == 'IMAGE_EDITOR':
                bpy.ops.wm.tool_set_by_id(name="zenuv.uv_tool")
            elif context.area.type == 'VIEW_3D':
                bpy.ops.wm.tool_set_by_id(name="zenuv.view3d_tool")
        else:
            bpy.context.scene.zen_uv.ui.uv_tool.category = 'TRANSFORMS'

            if self.prev_tool:
                try:
                    bpy.ops.wm.tool_set_by_id(name=self.prev_tool)
                except Exception as e:
                    Log.error('DEACTIVATE TOOL:', str(e))

        return {'FINISHED'}
