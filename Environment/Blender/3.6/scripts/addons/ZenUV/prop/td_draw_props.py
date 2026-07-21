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

# from ZenUV.utils.blender_zen_utils import update_areas_in_all_screens


class ZUV_TexelDensityDrawProps(bpy.types.PropertyGroup):

    width: bpy.props.IntProperty(
        name='TD Gradient Width',
        min=50,
        max=2000,
        default=300
    )

    height: bpy.props.IntProperty(
        name='TD Gradient Height',
        min=10,
        max=500,
        default=50
    )

    def draw(self, layout: bpy.types.UILayout, context: bpy.types.Context):
        for key in self.__annotations__.keys():
            layout.prop(self, key)
