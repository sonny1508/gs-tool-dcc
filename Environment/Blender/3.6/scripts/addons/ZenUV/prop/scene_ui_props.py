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

from ZenUV.ico import icon_get
from ZenUV.utils.blender_zen_utils import update_areas_in_uv, update_areas_in_view3d

from ZenUV.ops.transform_sys.transform_utils.tr_utils import (
    TransformSysOpsProps
)

from ZenUV.ui.labels import ZuvLabels


_mode_items = []


class ZuvToolProps:

    space_type = ''

    def update_view(self, context: bpy.types.Context):
        if self.space_type == 'UV':
            update_areas_in_uv(context)
        else:
            update_areas_in_view3d(context)

    display_trims: bpy.props.BoolProperty(
        name='Display Trims',
        description='Display Trimsheet Trims',
        default=False,
        update=update_view
    )

    display_all: bpy.props.BoolProperty(
        name='Display All Trims',
        description='Display all Trims or only active Trim',
        default=True,
        update=update_view
    )

    select_trim: bpy.props.BoolProperty(
        name='Trim Select',
        description='Activate Trim Selector',
        default=False,
        update=update_view
    )

    def get_select_trim_ex(self):
        return self.display_trims and self.select_trim

    def set_select_trim_ex(self, value):
        if value:
            self.display_trims = True
            if hasattr(self, 'trim_select_mode'):
                self.trim_select_mode = 'MESH'

        self.select_trim = value

    select_trim_ex: bpy.props.BoolProperty(
        name='Trim Select',
        description='Activate Trim Selector',
        get=get_select_trim_ex,
        set=set_select_trim_ex,
        update=update_view,
        options={'SKIP_SAVE'}
    )

    tr_handles: bpy.props.EnumProperty(
        name='Transform Handles',
        description='Enable handles for uv transform operations',
        items=[
            ('OFF', 'Off', 'Transform handles are disabled', 'CURSOR', 1),
            ('TRIM', 'Trim', 'Transform handles are placed at the trim corners', 'PIVOT_BOUNDBOX', 2),
            ('GIZMO', 'Gizmo', 'Transform handles are placed around gizmo', 'PIVOT_CURSOR', 3)
        ],
        default='TRIM',
        update=update_view
    )

    auto_options_expanded: bpy.props.BoolProperty(
        name='Automatic Settings',
        description='Tool automatic settings expanded-collapsed',
        default=False
    )

    scale_island_pivot: TransformSysOpsProps.island_pivot

    rotate_island_pivot: TransformSysOpsProps.island_pivot


class ZUV_UVToolProps(bpy.types.PropertyGroup, ZuvToolProps):

    space_type = 'UV'

    category: bpy.props.EnumProperty(
        name='Tool Category',
        description='Zen UV tool category',
        items=[
            ('TRANSFORMS', 'Transforms', 'Transform uv category: move, rotate, scale', icon_get('pn_Transform'), 1),
            ('TRIMS', 'Trims', 'Trims category: display, select, create and resize', icon_get('pn_Trimsheet'), 2)
        ],
        default=('TRANSFORMS')
    )

    transform_mode: bpy.props.EnumProperty(
        name='Transform Mode',
        description='Zen UV tool transform mode',
        items=[
            ('MOVE', 'Move', 'Moves UV islands or mesh elements', icon_get('transform-move'), 1),
            ('ROTATE', 'Rotate', 'Rotates UV islands or mesh elements', icon_get('transform-rotate'), 2),
            ('SCALE', 'Scale', 'Scales UV islands or mesh elements', icon_get('transform-scale'), 3),
        ],
        default='MOVE',
        update=ZuvToolProps.update_view
    )

    trim_mode: bpy.props.EnumProperty(
        name='Trim Mode',
        description='Zen UV tool trims mode',
        items=[
            ('RESIZE', 'Resize', 'Resize trims', 'CON_SIZELIMIT', 1),
            ('CREATE', 'Create', 'Create trims', 'GREASEPENCIL', 2),
        ],
        default='RESIZE',
        update=ZuvToolProps.update_view
    )

    def mode_items(self, context):
        p_rna = self.bl_rna.properties['transform_mode']
        p_items_1 = [
            # get icons only thgrough function !
            (item.identifier, item.name, item.description, icon_get(f'transform-{item.identifier.lower()}'), idx + 1)
            for idx, item in enumerate(p_rna.enum_items)]

        p_rna = self.bl_rna.properties['trim_mode']
        p_items_2 = [
            (item.identifier, item.name, item.description, item.icon, idx + 1 + len(p_items_1))
            for idx, item in enumerate(p_rna.enum_items)]
        p_items = p_items_1 + p_items_2

        global _mode_items
        if len(_mode_items) == 0:
            _mode_items = p_items.copy()

        return _mode_items

    def get_mode(self):
        p_rna_items = self.bl_rna.properties['transform_mode'].enum_items
        if self.category == 'TRANSFORMS':
            for idx, item in enumerate(p_rna_items):
                if item.identifier == self.transform_mode:
                    return idx + 1
        else:
            p_rna_items_2 = self.bl_rna.properties['trim_mode'].enum_items
            for idx, item in enumerate(p_rna_items_2):
                if item.identifier == self.trim_mode:
                    return len(p_rna_items) + idx + 1
        return 0

    def set_mode(self, value):
        p_rna = self.bl_rna.properties['transform_mode']
        idx = 0
        for item in p_rna.enum_items:
            idx += 1
            if value == idx:
                self.transform_mode = item.identifier
                self.category = 'TRANSFORMS'
                return

        p_rna = self.bl_rna.properties['trim_mode']
        for item in p_rna.enum_items:
            idx += 1
            if value == idx:
                self.trim_mode = item.identifier
                self.category = 'TRIMS'
                return

    mode: bpy.props.EnumProperty(
        name='Tool Mode',
        description='Zen UV tool mode',
        items=mode_items,
        get=get_mode,
        set=set_mode
    )


class ZUV_3DVToolProps(bpy.types.PropertyGroup, ZuvToolProps):
    space_type = 'VIEW_3D'

    trim_select_mode: bpy.props.EnumProperty(
        name='Trim Select Mode',
        description='Trim selector is binded to mesh or center of screen',
        items=[
            (
                'MESH', 'Mesh',
                'Trim selector center is the center of the active object active face center',
                'MESH_DATA', 1
            ),
            (
                'SCREEN', 'Screen',
                'Trim selector center is the center of 3D viewport',
                'SCREEN_BACK', 2
            )
        ],
        default='MESH',
        update=ZuvToolProps.update_view
    )

    mode: bpy.props.EnumProperty(
        name='Tool Mode',
        items=[
            ('MOVE', 'Move', 'Moves UV islands or mesh elements', icon_get('transform-move'), 1),
            ('ROTATE', 'Rotate', 'Rotates UV islands or mesh elements', icon_get('transform-rotate'), 2),
            ('SCALE', 'Scale', 'Scales UV islands or mesh elements', icon_get('transform-scale'), 3),
        ],
        default='MOVE',
        update=ZuvToolProps.update_view
    )

    texture_preview: bpy.props.BoolProperty(
        name='Texture Preview',
        default=True
    )

    screen_position_locked: bpy.props.BoolProperty(
        name='Screen Locked',
        description='Screen position scale and pan locked',
        default=False
    )

    screen_scale: bpy.props.FloatProperty(
        name='Screen Scale',
        min=0.1,
        default=1.0
    )

    screen_pan_x: bpy.props.FloatProperty(
        name='Screen Pan X',
        precision=0,
        default=0.0
    )

    screen_pan_y: bpy.props.FloatProperty(
        name='Screen Pan Y',
        precision=0,
        default=0.0
    )

    screen_pos: bpy.props.FloatVectorProperty(
        name='Screen Pos',
        precision=0,
        step=100,
        size=2,
        default=(0, 0),
    )

    screen_size: bpy.props.FloatProperty(
        name='Screen Size',
        precision=0,
        step=100,
        min=50,
        default=500,
    )

    def is_texture_visible(self):
        return (self.display_trims and self.texture_preview) or self.is_select_trim_enabled()

    def is_cage_visible(self):
        return self.display_trims or self.enable_screen_selector

    def is_screen_selector_position_enabled(self):
        return not self.screen_position_locked and self.trim_select_mode == 'SCREEN'

    def is_select_trim_enabled(self):
        return (self.display_trims and self.select_trim) or self.trim_select_mode == 'SCREEN'

    def get_select_mode(self):
        return self.trim_select_mode

    def get_display_trims_ex(self):
        return (self.trim_select_mode == 'SCREEN') or self.display_trims

    def set_display_trims_ex(self, value):
        if not value:
            if self.trim_select_mode == 'SCREEN':
                self.trim_select_mode = 'MESH'

        self.display_trims = value

    display_trims_ex: bpy.props.BoolProperty(
        name='Display Trims',
        description='Display Trimsheet Trims',
        get=get_display_trims_ex,
        set=set_display_trims_ex,
        update=ZuvToolProps.update_view,
        options={'SKIP_SAVE'}
    )

    def get_select_trim_ex(self):
        return self.trim_select_mode == 'SCREEN'

    def set_select_trim_ex(self, value):
        if value:
            self.trim_select_mode = 'SCREEN'
        else:
            self.trim_select_mode = 'MESH'

    enable_screen_selector: bpy.props.BoolProperty(
        name='Trim Viewport Selector',
        description='Show trim selector in screen viewport mode',
        get=get_select_trim_ex,
        set=set_select_trim_ex,
        update=ZuvToolProps.update_view,
        options={'SKIP_SAVE'}
    )


class ZUV_SceneUIProps(bpy.types.PropertyGroup):

    def on_update_view3d(self, context: bpy.types.Context):
        if hasattr(context, 'area') and context.area is not None:
            context.area.tag_redraw()

    def on_update_all_uvs(self, context: bpy.types.Context):
        update_areas_in_uv(context)

    def on_update_all_3ds(self, context: bpy.types.Context):
        update_areas_in_view3d(context)

    trim_preview_image: bpy.props.PointerProperty(
        name='Trim Preview Image',
        type=bpy.types.Image,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    tool_mode: bpy.props.EnumProperty(
        name='Tool Mode',
        items=[
            ('MOVE', 'Move', 'Moves UV islands or mesh elements', icon_get('transform-move'), 1),
            ('ROTATE', 'Rotate', 'Rotates UV islands or mesh elements', icon_get('transform-rotate'), 2),
            ('SCALE', 'Scale', 'Scales UV islands or mesh elements', icon_get('transform-scale'), 3),
        ],
        default='MOVE',
        update=on_update_view3d
    )

    tool_settings_expanded: bpy.props.BoolProperty(
        name='Tool Settings',
        description='Expand-collapse tool settings',
        default=False
    )

    uv_tool: bpy.props.PointerProperty(name='UV Tool', type=ZUV_UVToolProps)

    view3d_tool: bpy.props.PointerProperty(name='View3D Tool', type=ZUV_3DVToolProps)

    draw_mode_UV: bpy.props.EnumProperty(
        name='Draw Mode',
        description='Zen UV draw mode',
        items=[
            ('NONE', 'None', 'All UV draws disabled'),
            ('FINISHED', 'Finished', 'Display finished islands'),
            ('FLIPPED', 'Flipped', 'Display flipped faces'),
            ('EXCLUDED', 'Excluded', 'Display excluded islands'),

            ('SIMILAR_STATIC', 'Similar', ZuvLabels.PROP_ENUM_STACK_DISPLAY_SIMILAR_DESC),
            ('SIMILAR_SELECTED', 'Similar By Selection', ZuvLabels.PROP_ENUM_STACK_DISPLAY_SELECTED_DESC),
            ('STACKED', ZuvLabels.PROP_AST_STACKED_LABEL, ZuvLabels.PROP_AST_STACKED_DESC),
            ('STACKED_MANUAL', 'Manual Stacks', ZuvLabels.PROP_M_STACKED_DESC),

            ('TEXEL_DENSITY', 'Texel Density', 'Display texel density'),
        ],
        default='NONE',
        update=on_update_all_uvs
    )

    draw_mode_3D: bpy.props.EnumProperty(
        name='Draw Mode',
        description='Zen UV draw mode',
        items=[
            ('NONE', 'None', 'All UV draws disabled'),
            ('FINISHED', 'Finished', 'Display finished islands'),
            ('FLIPPED', 'Flipped', 'Display flipped islands'),
            ('STRETCHED', 'Stretched', 'Display stretched islands'),
            ('EXCLUDED', 'Excluded', 'Display excluded islands'),
            ('UV_NO_SYNC', 'UV No Sync', 'Display faces that are selected in UV no sync mode'),

            ('SIMILAR_STATIC', 'Similar', ZuvLabels.PROP_ENUM_STACK_DISPLAY_SIMILAR_DESC),
            ('SIMILAR_SELECTED', 'Similar By Selection', ZuvLabels.PROP_ENUM_STACK_DISPLAY_SELECTED_DESC),
            ('STACKED', ZuvLabels.PROP_AST_STACKED_LABEL, ZuvLabels.PROP_AST_STACKED_DESC),
            ('STACKED_MANUAL', 'Manual Stacks', ZuvLabels.PROP_M_STACKED_DESC),
            ('TAGGED', 'Tagged', 'Display tagged islands'),

            ('TEXEL_DENSITY', 'Texel Density', 'Display texel density'),
        ],
        default='NONE',
        update=on_update_all_3ds
    )

    def get_draw_mode_pair_by_context(self, context: bpy.types.Context):
        b_is_UV = context.space_data.type == 'IMAGE_EDITOR'
        s_space = 'UV' if b_is_UV else '3D'
        attr_name = 'draw_mode_' + s_space
        p_mode = getattr(context.scene.zen_uv.ui, attr_name)
        return (attr_name, p_mode)

    use_draw_overlay_sync: bpy.props.BoolProperty(
        name='Overlay Sync',
        description='Draw is synchronized with overlay on-off setting',
        default=False
    )

    draw_stretched_modal: bpy.props.BoolProperty(
        name='Stretched Dynamic',
        description='Display stretched in viewport modal operations: dragging etc.',
        default=False,
        options=set()
    )
