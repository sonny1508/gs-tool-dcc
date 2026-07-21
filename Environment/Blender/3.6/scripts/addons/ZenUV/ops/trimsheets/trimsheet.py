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
import mathutils

import uuid

from typing import Tuple, Dict, Callable
from dataclasses import dataclass

from .trimsheet_props import ZuvTrimsheetProps, ZuvTrimsheetOwnerProps
from .trimsheet_utils import ZuvTrimsheetUtils
from .trimsheet_modal import ZUV_OT_TrimCreate, ZUV_OT_TrimBoxSelect
from .trimsheet_preview import (
    ZUV_PT_ImageIcons, ZUV_OT_TrimPreview,
    get_enum_previews,
    enum_previews_from_directory_items)
from .trimsheet_presets import (
    ZUV_MT_StoreTrimsheetPresets,
    ZUV_OT_TrimAddPreset,
    ZUV_OT_TrimExecutePreset)
from .trimsheet_svg import ZUV_OT_TrimImportSVG, ZUV_OT_TrimExportSVG
from .trimsheet_from_mesh import register_trim_create, unregister_trim_create
from .trimsheet_ops import (
    ZUV_OT_TrimAddItem,
    ZUV_OT_TrimAddSizedItem,
    ZUV_OT_TrimRemoveItem,
    ZUV_OT_TrimMoveItem,
    ZUV_OT_TrimCopyToClipboard,
    ZUV_OT_TrimPasteFromClipboard,
    ZUV_OT_TrimDeleteAll,
    ZUV_OT_TrimFrame,
    ZUV_OT_TrimSetIndex,
    ZUV_OT_TrimRemoveItemUI,
    ZUV_OT_TrimDuplicate,
    ZUV_OT_TrimBatchRename,

    ZUV_OT_View3DMathVis,
    ZUV_OT_UVMathVis,

    ZUV_PT_3DVMathVisualizer,
    ZUV_PT_UVMathVisualizer,

    ZUV_OT_TrimsSetProps
)
from .trimsheet_tags import (
    ZuvTrimTag, ZUV_UL_TrimTagsList,
    ZUV_OT_TrimTagAddItem,
    ZUV_OT_TrimTagRemoveItem,
    ZUV_OT_TrimTagDeleteAll,
    ZUV_OT_TrimTagMoveItem,
    ZUV_MT_TrimTagMenu
)
from .darken_image import ZUV_OT_DarkenImage, ZUV_PT_ImageUIOverlay
from .trimsheet_export_image import (
    ZUV_OT_TrimExportPNG,
    ZUV_OT_TrimExportTGA,
    ZUV_OT_TrimExportBMP,
    ZUV_MT_TrimExport)
from .trimsheet_import import (
    ZUV_OT_TrimImportDecal,
    ZUV_MT_TrimImport
)

from ZenUV.utils.blender_zen_utils import update_areas_in_all_screens, setnameex
from ZenUV.utils.group_dict_utils import group_from_dict, group_to_dict


@dataclass
class TrimColorSettings:
    color: mathutils.Color = mathutils.Color()
    border: mathutils.Color = mathutils.Color()
    text_color: mathutils.Color = mathutils.Color()

    color_alpha: float = 1.0
    border_alpha: float = 1.0

    border_width: float = 1.0

    def get_color4(self) -> Tuple[float, float, float, float]:
        return (self.color[:] + (self.color_alpha,))

    def get_border4(self) -> Tuple[float, float, float, float]:
        return (self.border[:] + (self.border_alpha,))

    def get_text4(self) -> Tuple[float, float, float, float]:
        return (self.text_color[:] + (1.0,))


class ZuvTrimsheetGroup(bpy.types.PropertyGroup):

    def geometry_uuid_update(self, context: bpy.types.Context):
        p_id_data = self.id_data
        if p_id_data:
            p_id_data.zen_uv.trimsheet_mark_geometry_update()
            update_areas_in_all_screens(context)

    def set_left_bottom(self, value):
        p_opposite = self.get('top_right', (0.0, 0.0))
        self['left_bottom'] = (
            min(value[0], p_opposite[0]),
            min(value[1], p_opposite[1])
        )

    def set_top_right(self, value):
        p_opposite = self.get('left_bottom', (0.0, 0.0))
        self['top_right'] = (
            max(value[0], p_opposite[0]),
            max(value[1], p_opposite[1])
        )

    def get_rect(self):
        p_left, p_bottom = self.get('left_bottom', (0.0, 0.0))
        p_right, p_top = self.get('top_right', (0.0, 0.0))
        return (p_left, p_top, p_right, p_bottom)

    def set_rect(self, value):
        self.set_rectangle(value[0], value[1], value[2], value[3])

    def set_rectangle(self, left, top, right, bottom):
        self['left_bottom'] = (min(left, right), min(top, bottom))
        self['top_right'] = (max(left, right), max(top, bottom))

    def get_width(self):
        p_left, _ = self.get('left_bottom', (0.0, 0.0))
        p_right, _ = self.get('top_right', (0.0, 0.0))
        return p_right - p_left

    def get_height(self):
        _, p_bottom = self.get('left_bottom', (0.0, 0.0))
        _, p_top = self.get('top_right', (0.0, 0.0))
        return p_top - p_bottom

    def get_left(self):
        p_left, _ = self.get('left_bottom', (0.0, 0.0))
        return p_left

    def get_bottom(self):
        _, p_bottom = self.get('left_bottom', (0.0, 0.0))
        return p_bottom

    def set_width(self, value):
        p_left, _ = self.get('left_bottom', (0.0, 0.0))
        _, p_top = self.get('top_right', (0.0, 0.0))
        self['top_right'] = (p_left + value, p_top)

    def set_height(self, value):
        _, p_bottom = self.get('left_bottom', (0.0, 0.0))
        p_right, _ = self.get('top_right', (0.0, 0.0))
        self['top_right'] = (p_right, p_bottom + value)

    def set_left(self, value):
        _, p_bottom = self.get('left_bottom', (0.0, 0.0))
        _, p_top = self.get('top_right', (0.0, 0.0))
        p_width = self.get_width()
        self.set_rectangle(value, p_top, value + p_width, p_bottom)

    def set_bottom(self, value):
        p_left, _ = self.get('left_bottom', (0.0, 0.0))
        p_right, _ = self.get('top_right', (0.0, 0.0))
        p_height = self.get_height()
        self.set_rectangle(p_left, value + p_height, p_right, value)

    def get_rect_px(self):
        ctx = bpy.context
        p_image = ZuvTrimsheetUtils.getActiveImage(ctx)
        if p_image:
            width, height = p_image.size
            left_px = round(self.left * width)
            bottom_px = round(self.bottom * height)
            width_px = round(self.width * width)
            height_px = round(self.height * height)

            return (left_px, bottom_px, width_px, height_px)

        return (0, 0, 0, 0)

    def set_rect_px(self, value, mode):
        ctx = bpy.context
        p_image = ZuvTrimsheetUtils.getActiveImage(ctx)
        if p_image:
            width_px, height_px = p_image.size

            if width_px > 0 and height_px > 0:
                if mode == 0:
                    self.left = value / width_px
                elif mode == 1:
                    self.bottom = value / width_px
                elif mode == 2:
                    self.width = value / width_px
                elif mode == 3:
                    self.height = value / height_px

    def get_left_px(self):
        return self.get_rect_px()[0]

    def get_bottom_px(self):
        return self.get_rect_px()[1]

    def get_width_px(self):
        return self.get_rect_px()[2]

    def get_height_px(self):
        return self.get_rect_px()[3]

    def set_left_px(self, value):
        self.set_rect_px(value, 0)

    def set_bottom_px(self, value):
        self.set_rect_px(value, 1)

    def set_width_px(self, value):
        self.set_rect_px(value, 2)

    def set_height_px(self, value):
        self.set_rect_px(value, 3)

    def get_rgn2d_rect(self, rgn2d: bpy.types.View2D) -> Tuple[float, float, float, float]:
        left, top, right, bottom = self.rect

        left_2d, top_2d = rgn2d.view_to_region(left, top, clip=False)
        right_2d, bottom_2d = rgn2d.view_to_region(right, bottom, clip=False)

        return left_2d, top_2d, right_2d, bottom_2d

    def get_rgn2d_origin_dimensions(self, rgn2d: bpy.types.View2D) -> Tuple[float, float, float, float]:
        left_2d, top_2d, right_2d, bottom_2d = self.get_rgn2d_rect(rgn2d)

        width = right_2d - left_2d
        height = top_2d - bottom_2d

        x_cen = left_2d + width/2
        y_cen = bottom_2d + height/2

        return x_cen, y_cen, width, height

    def get_center(self):
        left, top, right, bottom = self.get_rect()
        return (left + (right - left) / 2, bottom + (top - bottom) / 2)

    left_px: bpy.props.IntProperty(
        name='Left',
        description='Trim left point',
        get=get_left_px,
        set=set_left_px,
        subtype='PIXEL',
        options={'SKIP_SAVE'},
        update=geometry_uuid_update
    )

    bottom_px: bpy.props.IntProperty(
        name='Bottom',
        description='Trim bottom point',
        get=get_bottom_px,
        set=set_bottom_px,
        subtype='PIXEL',
        options={'SKIP_SAVE'},
        update=geometry_uuid_update
    )

    width_px: bpy.props.IntProperty(
        name='Width',
        description='Trim width in pixels',
        min=0,
        get=get_width_px,
        set=set_width_px,
        subtype='PIXEL',
        options={'SKIP_SAVE'},
        update=geometry_uuid_update
    )

    height_px: bpy.props.IntProperty(
        name='Height',
        description='Trim height in pixels',
        min=0,
        get=get_height_px,
        set=set_height_px,
        subtype='PIXEL',
        options={'SKIP_SAVE'},
        update=geometry_uuid_update
    )

    left_bottom: bpy.props.FloatVectorProperty(
        name='Left Bottom',
        description='Left bottom trim point',
        get=lambda self: self.get('left_bottom', (0.0, 0.0)),
        set=set_left_bottom,
        subtype='COORDINATES',
        size=2,
        options={'SKIP_SAVE'},
        update=geometry_uuid_update
    )

    top_right: bpy.props.FloatVectorProperty(
        name='Top Right',
        description='Right top trim point',
        get=lambda self: self.get('top_right', (0.0, 0.0)),
        set=set_top_right,
        subtype='COORDINATES',
        size=2,
        options={'SKIP_SAVE'},
        update=geometry_uuid_update
    )

    left: bpy.props.FloatProperty(
        name='Left',
        description='Trim left point',
        get=get_left,
        set=set_left,
        options={'SKIP_SAVE'},
        update=geometry_uuid_update
    )

    bottom: bpy.props.FloatProperty(
        name='Bottom',
        description='Trim bottom point',
        get=get_bottom,
        set=set_bottom,
        options={'SKIP_SAVE'},
        update=geometry_uuid_update
    )

    width: bpy.props.FloatProperty(
        name='Width',
        description='Trim width',
        min=0,
        get=get_width,
        set=set_width,
        options={'SKIP_SAVE'},
        update=geometry_uuid_update
    )

    height: bpy.props.FloatProperty(
        name='Height',
        description='Trim height',
        min=0,
        get=get_height,
        set=set_height,
        options={'SKIP_SAVE'},
        update=geometry_uuid_update
    )

    rect: bpy.props.FloatVectorProperty(
        name='Bound Rect',
        description='Trim bounds rectangle: left, top, right, bottom',
        get=get_rect,
        set=set_rect,
        subtype='NONE',
        size=4,
        default=(0, 0, 0, 0)
    )

    color: bpy.props.FloatVectorProperty(
        name='Fill Color',
        description='Fill Color for area inside Trim rectangle',
        subtype='COLOR_GAMMA',
        size=3,
        default=(0.0, 0.5, 0.0),
        min=0, max=1
    )

    border_color: bpy.props.FloatVectorProperty(
        name='Border Color',
        description='Pen color to draw outline',
        subtype='COLOR_GAMMA',
        size=3,
        default=(1.0, 0.0, 0.0),
        min=0, max=1
    )

    selected: bpy.props.BoolProperty(
        name='Selected',
        description='Selected trim sheet state',
        default=False,
        options=set()
    )

    inset: bpy.props.FloatProperty(
        name="Inset",
        description="Trim Inset",
        default=0.0,
        options=set()
    )

    keep_proportion: bpy.props.BoolProperty(
        name="Keep proportion",
        description="",
        default=True,
        options=set()
    )

    align_to: bpy.props.EnumProperty(
        name="Align to",
        items=[
            ("br", 'Bottom-Right', ''),
            ("bl", 'Bottom-Left', ''),
            ("tr", 'Top-Right', ''),
            ("tl", 'Top-Left', ''),
            ("cen", 'Center', ''),
            ("rc", 'Right', ''),
            ("lc", 'Left', ''),
            ("bc", 'Bottom', ''),
            ("tc", 'Top', ''),
        ],
        default='cen',
        options=set()
    )

    fit_axis: bpy.props.EnumProperty(
        name='Fit Axis',
        description='Fit Axis',
        items=[
            ('U', 'U', 'U axis'),
            ('V', 'V', 'V axis'),
            ('MIN', 'Min', 'The minimum length axis is automatically determined'),
            ('MAX', 'Max', 'The maximum length axis is automatically determined'),
            ('AUTO', 'Automatic', 'Automatically detected axis for full dimensional compliance'),
        ],
        default='AUTO',
        options=set()
    )
    normal: bpy.props.FloatVectorProperty(
        name='Normal',
        description="An imaginary normal representing Trim's orientation if it were in 3D space",
        default=(0.0, 0.0, 0.0),
        subtype='COORDINATES',
        options=set()
    )

    def get_uuid(self):
        p_uuid = self.get('uuid', None)
        if p_uuid is None:
            self['uuid'] = str(uuid.uuid4())
            return self['uuid']
        return p_uuid

    def set_uuid(self, value):
        parent = self.id_data
        # do not allow same uuid's
        for p_trim in parent.zen_uv.trimsheet:
            if p_trim != self and p_trim.uuid == value:
                self['uuid'] = str(uuid.uuid4())
                return

        self['uuid'] = value

    uuid: bpy.props.StringProperty(
        name='UUID',
        description='Unique indentifier',
        get=get_uuid,
        set=set_uuid,
        options=set()
    )

    match_rotation: bpy.props.BoolProperty(
        name="Match Rotation",
        description="",
        default=False,
        options=set()
    )

    def get_index(self) -> int:
        p_id_data = self.id_data
        if p_id_data:
            try:
                s_prop_name = self.path_from_id()
                list_idx = s_prop_name.split('[')[1][0:-1]
                return int(list_idx)
            except Exception:
                pass
        return -1

    def is_active(self) -> bool:
        p_id_data = self.id_data
        if p_id_data:
            try:
                s_prop_name = self.path_from_id()
                list_idx = s_prop_name.split('[')[1][0:-1]
                return p_id_data.zen_uv.trimsheet_index == int(list_idx)
            except Exception:
                pass
        return False

    def is_empty(self) -> bool:
        return self.width == 0 or self.height == 0

    # we use extern 'actve' and 'selected' for different color values, like SVG or DRAW
    def get_draw_color_settings(self, p_trim_prefs, b_is_active, b_is_selected) -> TrimColorSettings:
        t_colors = TrimColorSettings()
        t_colors.color = self.color[:3]
        t_colors.border_width = p_trim_prefs.border_width
        d_fill_alpha = p_trim_prefs.fill_transparency / 100
        d_fill_border = p_trim_prefs.border_transparency / 100

        # p_color = mathutils.Color(t_colors['color'])
        # p_color.v = 1.0

        p_color = t_colors.color

        if p_trim_prefs.border_style == 'FIXED':
            if b_is_active:
                t_colors.border = p_trim_prefs.active_border_color[:3]
            elif b_is_selected:
                t_colors.border = p_trim_prefs.selected_border_color[:3]
            else:
                t_colors.border = p_trim_prefs.border_color[:3]
        elif p_trim_prefs.border_style == 'USER':
            if b_is_selected:
                t_colors.border = p_trim_prefs.selected_border_color[:3]
            else:
                t_colors.border = self.border_color[:3]
        else:
            if b_is_selected:
                t_colors.border = p_trim_prefs.selected_border_color[:3]
            else:
                t_colors.border = p_color[:]

        if b_is_active:
            d_fill_border = 1.0
            t_colors.border_width *= 2
            d_fill_alpha *= 2

        t_colors.text_color = p_color[:]

        t_colors.border_alpha = d_fill_border
        t_colors.color_alpha = d_fill_alpha

        return t_colors

    def get_preview_name(self):
        p_left, p_top, p_right, p_bottom = self.get_rect()
        return f'{self.uuid}@{p_left:.2f}@{p_top:.2f}@{p_right:.2f}@{p_bottom:.2f}'.replace('.', '_')

    def get_int32_id(self):
        return ZuvTrimsheetUtils.hash32(self.uuid)

    # properties, that does not require special operations
    @classmethod
    def get_common_props(cls, skipped=set()):
        t_props = (
            'fit_axis',
            'inset',
            'keep_proportion',
            'match_rotation',
            'align_to',
            'normal',
            'selected',
            'uuid',
        )
        return [prop for prop in t_props if prop not in skipped]

    def to_dict(self, fn_skip_prop: Callable = None):
        return group_to_dict(self, fn_skip_prop=fn_skip_prop)

    def from_dict(self, t_dict: Dict, fn_skip_prop: Callable = None):
        group_from_dict(self, t_dict, fn_skip_prop=fn_skip_prop)

    def update_name_ex(self, context):
        from .trimsheet_props import TimeData
        bpy.app.driver_namespace[TimeData.literal_id] = TimeData()

    name_ex: bpy.props.StringProperty(
        name='Name',
        description='Trim name',
        get=lambda self: getattr(self, 'name', ''),
        set=setnameex,
        update=update_name_ex,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def get_tag(self, tag_name='', tag_category='', default=None):
        p_tag = None  # type: ZuvTrimTag

        for it_tag in self.tags:
            if tag_name:
                if it_tag.name == tag_name:
                    p_tag = it_tag
                    if not tag_category or tag_category == it_tag.category:
                        break

            if tag_category:
                if it_tag.category == tag_category:
                    p_tag = it_tag
                    break

        if p_tag:
            return p_tag
        else:
            return default

    def set_tag_value(self, tag_name='', tag_category='', tag_value=''):
        if not tag_name and not tag_category:
            raise RuntimeError('Trim Tag Name or Category not defined!')

        p_tag = self.get_tag(tag_name=tag_name, tag_category=tag_category, default=None)

        if p_tag is None:
            self.tags.add()

            p_tag = self.tags[-1]
            p_tag.name = tag_name
            p_tag.category = tag_category

        p_tag.value = tag_value

    def get_tag_value(self, tag_name='', tag_category='', default=None):
        if not tag_name and not tag_category:
            raise RuntimeError('Trim Tag Name or Category not defined!')

        p_tag = self.get_tag(tag_name=tag_name, tag_category=tag_category, default=None)
        if p_tag:
            return p_tag.value
        else:
            return default

    def get_active_tag(self) -> ZuvTrimTag:
        if self.tag_index in range(0, len(self.tags)):
            return self.tags[self.tag_index]
        return None

    tags: bpy.props.CollectionProperty(
        name='Trim Tags',
        description='Trim service tags',
        type=ZuvTrimTag
    )

    tag_index: bpy.props.IntProperty(
        name='Trim Active Tag Index',
        description='Active tag index of the current trim',
        default=-1,
        min=-1
    )

    hide: bpy.props.BoolProperty(
        name='Hide in Viewport',
        description='Hide trimsheet in viewport',
        default=False
    )


def on_zenuv_trimsheet_index_update(self, context):
    p_trimsheet_names = [p_trim.get_preview_name() for p_trim in self.trimsheet]
    p_previews = enum_previews_from_directory_items(self, context)

    p_preview_names = [item[0] for item in p_previews]

    if p_preview_names == p_trimsheet_names:
        if self.trimsheet_index in range(len(p_preview_names)):
            if self.trimsheet_previews != p_preview_names[self.trimsheet_index]:
                self.trimsheet_previews = p_preview_names[self.trimsheet_index]


def on_zenuv_trimsheet_previews_update(self, context):
    p_trimsheet_names = [p_trim.get_preview_name() for p_trim in self.trimsheet]
    p_previews = enum_previews_from_directory_items(self, context)

    p_preview_names = [item[0] for item in p_previews]

    if p_preview_names == p_trimsheet_names:
        if self.trimsheet_previews in p_trimsheet_names:
            p_index = p_trimsheet_names.index(self.trimsheet_previews)
            if self.trimsheet_index != p_index:
                self.trimsheet_index = p_index


def get_trimsheet_previews(self):
    p_trimsheet_names = [p_trim.get_preview_name() for p_trim in self.trimsheet]
    p_previews = get_enum_previews(self)

    p_preview_names = [item[0] for item in p_previews]

    if p_preview_names == p_trimsheet_names:
        return self.trimsheet_index
    else:
        return -1


def set_trimsheet_previews(self, value):
    p_trimsheet_names = [p_trim.get_preview_name() for p_trim in self.trimsheet]
    p_previews = get_enum_previews(self)

    p_preview_names = [item[0] for item in p_previews]

    if p_preview_names == p_trimsheet_names:
        self.trimsheet_index = value
        update_areas_in_all_screens(bpy.context)


class ZuvImageProperties(bpy.types.PropertyGroup):
    trimsheet: bpy.props.CollectionProperty(name='Trimsheet', type=ZuvTrimsheetGroup)
    trimsheet_index: ZuvTrimsheetOwnerProps.trimsheet_index
    trimsheet_index_ui: ZuvTrimsheetOwnerProps.trimsheet_index_ui
    trimsheet_geometry_uuid: ZuvTrimsheetOwnerProps.trimsheet_geometry_uuid

    # image properties only
    trimsheet_previews: bpy.props.EnumProperty(
        name='Trimsheet Previews', items=enum_previews_from_directory_items,
        get=get_trimsheet_previews,
        set=set_trimsheet_previews,
        update=on_zenuv_trimsheet_previews_update)

    def trimsheet_mark_geometry_update(self):
        self.trimsheet_geometry_uuid = str(uuid.uuid4())


class ZUV_UL_TrimsheetList(bpy.types.UIList):
    """ Zen Trimsheet Groups UIList """
    def draw_item(self, context: bpy.types.Context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname, index):

        custom_icon = 'OBJECT_DATAMODE'

        from ZenUV.prop.zuv_preferences import get_prefs
        addon_prefs = get_prefs()

        # Make sure code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            layout.alert = item.width == 0 or item.height == 0

            layout.prop(item, 'selected', text='')

            row = layout.row(align=True)
            row.scale_x = 0.35
            row.prop(item, "color", text="")

            # DEBUG:
            # act_idx = getattr(active_data, active_propname)

            from .trimsheet_props import TimeData
            p_last_time_data = bpy.app.driver_namespace.get(TimeData.literal_id, TimeData())  # type: TimeData

            b_alert_icon = 'ERROR' if layout.alert else 'NONE'
            if p_last_time_data.trim == item:
                layout.prop(item, "name_ex", text="", emboss=True, icon=b_alert_icon)
            else:
                layout.label(text=item.name, icon=b_alert_icon)

            if addon_prefs.trimsheet.border_style == 'USER':
                layout.prop(item, "border_color", text="")

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(text="", emboss=False, icon=custom_icon)


class ZUV_PT_TrimOverlayFilter(bpy.types.Panel):
    bl_label = "ZenUV Trimsheet Overlay Filter"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "mesh_edit"  # Do not remove !!!
    bl_ui_units_x = 12

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        from ZenUV.prop.zuv_preferences import get_prefs

        col = layout.column(align=False)
        col.use_property_split = True

        p_scene = context.scene

        tool_props = None

        addon_prefs = get_prefs()

        if context.area.type == 'IMAGE_EDITOR':
            tool_props = p_scene.zen_uv.ui.uv_tool
            col.prop(tool_props, 'display_all')
            col.prop(addon_prefs.trimsheet, 'display_name')

            row = layout.row(align=True)
            row.alignment = 'LEFT'
            row.prop(
                tool_props, 'auto_options_expanded',
                emboss=False,
                icon='DISCLOSURE_TRI_DOWN' if tool_props.auto_options_expanded else 'DISCLOSURE_TRI_RIGHT')

            if tool_props.auto_options_expanded:
                col = layout.column(align=False)
                col.use_property_split = True
                col.prop(addon_prefs.trimsheet, 'auto_highlight', expand=True)

        else:
            tool_props = p_scene.zen_uv.ui.view3d_tool

            if tool_props.enable_screen_selector:
                col = layout.column(align=False)
                col.use_property_split = True
                col.prop(tool_props, 'screen_position_locked')

                if not tool_props.screen_position_locked:
                    col.prop(tool_props, 'screen_scale')
                    col.prop(tool_props, 'screen_pan_x')
                    col.prop(tool_props, 'screen_pan_y')
                else:
                    col.prop(tool_props, 'screen_pos', text='Left', index=0)
                    col.prop(tool_props, 'screen_pos', text='Bottom', index=1)
                    col.prop(tool_props, 'screen_size', text='Size')
            else:
                col.prop(tool_props, 'display_all')
                col.prop(tool_props, 'texture_preview')
                col.prop(addon_prefs.trimsheet, 'display_name')

            row = layout.row(align=True)
            row.alignment = 'LEFT'
            row.prop(
                tool_props, 'auto_options_expanded',
                emboss=False,
                icon='DISCLOSURE_TRI_DOWN' if tool_props.auto_options_expanded else 'DISCLOSURE_TRI_RIGHT')

            if tool_props.auto_options_expanded:
                col = layout.column(align=False)
                col.use_property_split = True
                col.prop(addon_prefs.trimsheet, 'auto_highlight', expand=True)

                col.separator()
                row = col.row(align=True)
                s_row = row.split(factor=1/2.5)
                s_row.alignment = 'LEFT'
                s_row.label(text='')
                s_row.label(text='Auto Disable Overlay')

                col.prop(addon_prefs.trimsheet, 'auto_disable_blender_overlay', text='Blender')
                col.prop(addon_prefs.trimsheet, 'auto_disable_trims_overlay', text='Trims')

        addon_prefs.trimsheet.draw_style(layout, context)


class ZUV_MT_TrimsheetMenu(bpy.types.Menu):
    bl_label = "ZenUV Trimsheet Menu"

    def draw(self, context):
        from .trimsheet_panel import ZUV_PT_UVL_SubTrimsheetImport
        ZUV_PT_UVL_SubTrimsheetImport.draw(self, context)
        layout = self.layout
        layout.separator()
        op = layout.operator('uv.zuv_trim_frame', text='Frame Active Trim')
        op.mode = 'ACTIVE'
        op = layout.operator('uv.zuv_trim_frame', text='Frame Selected Trims')
        op.mode = 'SELECTED'


# Initialization order is important
classes = (
    ZuvTrimTag,
    ZuvTrimsheetGroup,

    ZuvTrimsheetProps,
    ZuvImageProperties,

    ZUV_UL_TrimsheetList,
    ZUV_UL_TrimTagsList,

    ZUV_PT_ImageIcons,

    ZUV_OT_TrimAddItem,
    ZUV_OT_TrimAddSizedItem,
    ZUV_OT_TrimRemoveItem,
    ZUV_OT_TrimCreate,
    ZUV_OT_TrimMoveItem,
    ZUV_OT_TrimCopyToClipboard,
    ZUV_OT_TrimPasteFromClipboard,
    ZUV_OT_TrimPreview,
    ZUV_OT_TrimAddPreset,
    ZUV_OT_TrimExecutePreset,
    ZUV_OT_TrimDeleteAll,
    ZUV_OT_TrimFrame,
    ZUV_OT_TrimSetIndex,
    ZUV_OT_TrimDuplicate,
    ZUV_OT_TrimBatchRename,

    ZUV_OT_TrimTagAddItem,
    ZUV_OT_TrimTagRemoveItem,
    ZUV_OT_TrimTagDeleteAll,
    ZUV_OT_TrimTagMoveItem,

    ZUV_OT_TrimImportSVG,
    ZUV_OT_TrimExportSVG,

    ZUV_OT_TrimExportPNG,
    ZUV_OT_TrimExportTGA,
    ZUV_OT_TrimExportBMP,
    ZUV_MT_TrimExport,

    ZUV_OT_TrimImportDecal,
    ZUV_MT_TrimImport,

    ZUV_OT_DarkenImage,

    ZUV_PT_ImageUIOverlay,

    ZUV_PT_TrimOverlayFilter,
    ZUV_MT_StoreTrimsheetPresets,
    ZUV_MT_TrimsheetMenu,
    ZUV_MT_TrimTagMenu,

    ZUV_OT_View3DMathVis,
    ZUV_OT_UVMathVis,
    ZUV_PT_UVMathVisualizer,
    ZUV_PT_3DVMathVisualizer,

    ZUV_OT_TrimsSetProps,

    ZUV_OT_TrimBoxSelect,

    ZUV_OT_TrimRemoveItemUI
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Image.zen_uv = bpy.props.PointerProperty(
        name='Zen UV Image Properties',
        type=ZuvImageProperties)

    register_trim_create()


def unregister():
    try:
        del bpy.types.Image.zen_uv
    except Exception:
        pass

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    unregister_trim_create()
