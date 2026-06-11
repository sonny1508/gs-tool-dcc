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

import os
import numpy as np
import math
from timeit import default_timer as timer

from .trimsheet_utils import ZuvTrimsheetUtils
from ZenUV.utils.vlog import Log
from ZenUV.utils.blender_zen_utils import ZuvPresets


preview_collections = {}


class ZuvTrimPreviewer:
    def __init__(self) -> None:
        self.preview_id = bpy.utils.previews.new()
        self.enum_previews = None

    def __del__(self) -> None:
        bpy.utils.previews.remove(self.preview_id)

    @classmethod
    def get_image_preview_dir(cls, p_image: bpy.types.Image):
        trim_dir = ZuvPresets.force_full_preset_path(ZuvTrimsheetUtils.TRIM_PREVIEW_SUBDIR)
        trim_dir = os.path.join(trim_dir, p_image.name)
        return trim_dir

    def collect_previews(self, p_image: bpy.types.Image):
        trim_dir = self.get_image_preview_dir(p_image)

        p_out_previews = []

        if os.path.exists(trim_dir):
            p_original_data = {p_trim.get_preview_name(): p_trim for p_trim in p_image.zen_uv.trimsheet}

            p_trim_data = p_original_data.copy()

            # we need to do through copy procedure, because keys will be removed !
            for key in list(self.preview_id.keys()):
                if key in p_trim_data:
                    del p_trim_data[key]
                else:
                    del self.preview_id[key]

            for p_preview_name, p_trim in p_trim_data.items():
                img_file = os.path.join(trim_dir, p_preview_name)
                if os.path.exists(img_file):
                    print('PREVIEW: 3) load', p_trim.name, p_preview_name)
                    self.preview_id.load(p_preview_name, img_file, 'IMAGE')
                else:
                    Log.error("Can not find preview for:", img_file)

            idx = 0
            for p_preview_name, p_trim in p_original_data.items():
                p_preview_item = self.preview_id.get(p_preview_name, None)
                p_icon_id = 0 if p_preview_item is None else p_preview_item.icon_id
                p_out_previews.append((p_preview_name, p_trim.name, f"{p_trim.name} - {p_image.name}", p_icon_id, idx))
                idx += 1

        if self.enum_previews != p_out_previews:
            print('PREVIEW: 4) Update preview enum!')
            self.enum_previews = p_out_previews

    def mark_modified(self):
        self.enum_previews = None


def get_enum_previews(self):
    p_image = self.id_data
    if p_image is not None:
        if p_image.zen_uv == self:
            p_preview = preview_collections.get(p_image.name, None)
            if p_preview and p_preview.enum_previews:
                return p_preview.enum_previews
    return []


def enum_previews_from_directory_items(self, context: bpy.types.Context):
    """EnumProperty callback"""
    enum_items = []

    p_image = self.id_data
    if p_image is not None:
        if p_image.zen_uv == self:

            if p_image.name not in preview_collections:
                preview_collections[p_image.name] = ZuvTrimPreviewer()

            p_preview = preview_collections[p_image.name]
            if p_preview.enum_previews is None:
                p_preview.collect_previews(p_image)

            return p_preview.enum_previews

    return enum_items


class ZUV_OT_TrimPreview(bpy.types.Operator):
    bl_idname = "wm.zuv_trim_preview"
    bl_label = 'Preview'
    bl_description = 'Open Trim Preview window to select active Trim'
    bl_options = {'REGISTER', 'UNDO'}

    def update_preview(self, p_image):
        width, height = p_image.size
        if width == 0 or height == 0:
            Log.warn("Image is empty!")
            return

        trim_dir = ZuvTrimPreviewer.get_image_preview_dir(p_image)

        p_trimsheet = p_image.zen_uv.trimsheet
        if len(p_trimsheet) == 0:
            return

        interval = timer()

        os.makedirs(trim_dir, exist_ok=True)

        p_trims = {p_trim.get_preview_name(): p_trim for p_trim in p_image.zen_uv.trimsheet}

        p_preview = preview_collections.get(p_image.name, None)
        if p_preview and p_preview.enum_previews:
            ids, names, descs, icon_ids, bl_ids = zip(*p_preview.enum_previews)
            if set(ids) == set(p_trims.keys()) and 0 not in icon_ids:
                print('PREVIEW: 1) Actual, no need to generate!')
                return
            # maybe we need optimize here more !
            p_preview.mark_modified()

        p_trims = [
            p_trim for p_preview_name, p_trim in p_trims.items()
            if not os.path.exists(os.path.join(trim_dir, p_preview_name))]

        if len(p_trims) == 0:
            print('PREVIEW: 2) All images were generated!')
            if p_preview:
                p_preview.mark_modified()
            return

        interval = timer()

        pixels = np.empty(width * height * p_image.channels, dtype=np.float32)
        p_image.pixels.foreach_get(pixels)
        arr = pixels.reshape((height, width, p_image.channels)).T

        Log.debug('1) get array:', timer() - interval)

        img_x1 = None
        img_x2 = None
        img_y1 = None
        img_y2 = None

        for p_trim in p_trims:
            left, bottom = p_trim.left_bottom
            right, top = p_trim.top_right

            min_x = left * width
            min_y = bottom * height

            max_x = right * width
            max_y = top * height

            if img_x1 is None or min_x < img_x1:
                img_x1 = min_x

            if img_x2 is None or max_x > img_x2:
                img_x2 = max_x

            if img_y1 is None or min_y < img_y1:
                img_y1 = min_y

            if img_y2 is None or max_y > img_y2:
                img_y2 = max_y

        tile_x1 = (math.ceil if img_x1 >= 0 else math.floor)((img_x1 / width))
        tile_x2 = (math.ceil if img_x2 >= 0 else math.floor)((img_x2 / width))

        tile_x = tile_x2 - tile_x1
        if 0 not in range(tile_x1, tile_x2):
            tile_x += 1

        # print('tile_x:', tile_x, 'tile_x1:', tile_x1, 'tile_x2:', tile_x2)

        tile_y1 = (math.ceil if img_y1 >= 0 else math.floor)((img_y1 / width))
        tile_y2 = (math.ceil if img_y2 >= 0 else math.floor)((img_y2 / width))

        tile_y = tile_y2 - tile_y1
        if 0 not in range(tile_y1, tile_y2):
            tile_y += 1

        # print('tile_y:', tile_y, 'tile_y1:', tile_y1, 'tile_y2:', tile_y2)

        tile_x = max(1, tile_x)
        tile_y = max(1, tile_y)

        if tile_x > 1 or tile_y > 1:
            arr = np.tile(arr, (tile_x, tile_y))

        arr = arr.T

        for p_trim in p_trims:
            left, bottom = p_trim.left_bottom
            right, top = p_trim.top_right

            min_x = left * width
            min_y = bottom * height

            max_x = right * width
            max_y = top * height

            if tile_x1 < 0:
                x_offset = abs(tile_x1) * width
                min_x += x_offset
                max_x += x_offset

            if tile_y1 < 0:
                y_offset = abs(tile_y1) * height
                min_y += y_offset
                max_y += y_offset

            min_x = round(min_x)
            max_x = round(max_x)
            min_y = round(min_y)
            max_y = round(max_y)

            trim_width_px = max_x - min_x
            trim_height_px = max_y - min_y

            p_trim_img_name = p_trim.name + '_' + p_image.name
            img = bpy.data.images.get(p_trim_img_name)
            if img is not None:
                bpy.data.images.remove(img)
            img = bpy.data.images.new(p_trim_img_name, trim_width_px, trim_height_px)
            img.file_format = p_image.file_format

            img.pixels.foreach_set(arr[min_y:max_y, min_x:max_x].ravel())

            trim_img_file = os.path.join(trim_dir, p_trim.get_preview_name())

            if bpy.app.version < (3, 4, 1):
                img.filepath_raw = trim_img_file
                img.save()
            else:
                img.save(filepath=trim_img_file)

            bpy.data.images.remove(img)

        Log.debug("2) Trims preview elapsed:", timer() - interval)

    def draw_popup_menu(self, context: bpy.types.Context):
        layout = self.layout
        p_image = context.scene.zen_uv.ui.trim_preview_image
        if p_image is not None:
            layout.template_icon_view(p_image.zen_uv, "trimsheet_previews", show_labels=True)
        else:
            layout.label(text='No Active Image!', icon='ERROR')

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.template_ID(context.scene.zen_uv.ui, 'trim_preview_image')

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        wm = context.window_manager

        p_image = ZuvTrimsheetUtils.getActiveImage(context)
        p_scene = context.scene
        p_scene.zen_uv.ui.trim_preview_image = p_image
        if p_image is None:
            return wm.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def execute(self, context: bpy.types.Context):
        try:
            p_scene = context.scene
            p_image = p_scene.zen_uv.ui.trim_preview_image
            if p_image is not None:
                self.update_preview(p_image)

            context.window_manager.popup_menu(ZUV_OT_TrimPreview.draw_popup_menu, title='Select Active Trim', icon='INFO')
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))

        return {'CANCELLED'}


class ZUV_PT_ImageIcons(bpy.types.Panel):
    bl_label = "Image Icons"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'HEADER'

    def draw(self, context: bpy.types.Image):
        layout = self.layout

        if hasattr(context.space_data, "image"):
            p_image = context.space_data.image

            if p_image:
                layout.template_icon_view(p_image.zen_uv, "trimsheet_previews", show_labels=True)
