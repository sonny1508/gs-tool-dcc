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

# Copyright 2021, Alex Zhornyak

""" Zen Blender Utils """

import bpy

import platform
import functools
import os
import re
import math

from .vlog import Log


class ZenPolls:
    version_greater_3_2_0 = False
    version_lower_3_4_0 = False
    version_lower_3_5_0 = False
    doc_url = 'https://zenmastersteam.github.io/Zen-UV/latest/'


class CallerCmdProps:
    bl_op_cls = None
    bl_label = None
    bl_desc = None
    cmd = None


class ZsDrawConstans:
    DEFAULT_VERT_ACTIVE_ALPHA = 80
    DEFAULT_VERT_INACTIVE_ALPHA = 60
    DEFAULT_VERT_ACTIVE_POINT_SIZE = 10
    DEFAULT_VERT_INACTIVE_POINT_SIZE = 6
    DEFAULT_VERT_USE_ZOOM_FACTOR = False

    DEFAULT_EDGE_ACTIVE_ALPHA = 60
    DEFAULT_EDGE_INACTIVE_ALPHA = 40
    DEFAULT_EDGE_ACTIVE_LINE_WIDTH = 3
    DEFAULT_EDGE_INACTIVE_LINE_WIDTH = 2

    DEFAULT_FACE_ACTIVE_ALPHA = 60
    DEFAULT_FACE_INACTIVE_ALPHA = 40

    DEFAULT_OBJECT_ACTIVE_ALPHA = 40
    DEFAULT_OBJECT_INACTIVE_ALPHA = 20
    DEFAULT_OBJECT_COLLECTION_BOUNDBOX_WIDTH = 2
    DEFAULT_OBJECT_COLLECTION_LABEL_SIZE = 12

    BGL_ACTIVE_FONT_COLOR = (0.855, 0.141, 0.07)  # Zen Red Color
    BGL_INACTIVE_FONT_COLOR = (0.8, 0.8, 0.8)


def get_zen_platform():
    s_system = platform.system()
    if s_system == 'Darwin':
        try:
            import sysconfig
            if 'arch64-apple-darwin' in sysconfig.get_config_vars()['HOST_GNU_TYPE']:
                s_system = 'DarwinSilicon'

        except Exception as e:
            Log.error(e)
    return s_system


def get_command_props(cmd, context=bpy.context) -> CallerCmdProps:

    op_props = CallerCmdProps()

    if cmd:
        op_cmd = cmd
        op_args = '()'

        cmd_split = cmd.split("(", 1)
        if len(cmd_split) == 2:
            op_cmd = cmd_split[0]
            op_args = '(' + cmd_split[1]

        op_cmd_short = op_cmd.replace("bpy.ops.", "", 1)
        op_cmd = f"bpy.ops.{op_cmd_short}"

        try:
            if op_args == '()':
                wm = context.window_manager
                op_last = wm.operator_properties_last(op_cmd_short)
                if op_last:
                    props = op_last.bl_rna.properties
                    keys = set(props.keys()) - {'rna_type'}
                    args = [
                        k + '=' + repr(getattr(op_last, k))
                        for k in dir(op_last)
                        if k in keys and not props[k].is_readonly and not props[k].is_skip_save]

                    if len(args):
                        op_args = f'({",".join(args)})'

            op_props.bl_op_cls = eval(op_cmd)
            op_props.cmd = op_cmd + op_args

            try:
                rna = op_props.bl_op_cls.get_rna().rna_type \
                    if hasattr(op_props.bl_op_cls, "get_rna") \
                    else op_props.bl_op_cls.get_rna_type()

                op_props.bl_label = rna.name
                op_props.bl_desc = rna.description
            except Exception as ex:
                Log.warn('Description error:', ex)

        except Exception as ex:
            op_props = CallerCmdProps()
            Log.error('Eval error:', ex, 'cmd:', cmd)

    return op_props


# using wonder's beautiful simplification: https://stackoverflow.com/questions/31174295/getattr-and-setattr-on-nested-objects/31174427?noredirect=1#comment86638618_31174427
def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))


def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


class ZuvPresets:

    @classmethod
    def get_preset_path(cls, s_preset_subdir):
        return os.path.join('zen_uv', s_preset_subdir)

    @classmethod
    def force_full_preset_path(cls, s_preset_dir):
        target_path = os.path.join("presets", cls.get_preset_path(s_preset_dir))
        target_path = bpy.utils.user_resource('SCRIPTS', path=target_path, create=True)

        if not target_path:
            raise RuntimeError(f"Can not find or create: {s_preset_dir}")

        return target_path


class ZsOperatorAttrs:
    @classmethod
    def get_operator_attr(cls, op_name, attr_name, default=None):
        wm = bpy.context.window_manager
        op_last = wm.operator_properties_last(op_name)
        if op_last:
            return getattr(op_last, attr_name, default)
        return default

    @classmethod
    def set_operator_attr(cls, op_name, attr_name, value):
        wm = bpy.context.window_manager
        op_last = wm.operator_properties_last(op_name)
        if op_last:
            setattr(op_last, attr_name, value)

    @classmethod
    def get_operator_attr_int_enum(cls, op_name, attr_name, default, p_items):
        p_val = cls.get_operator_attr(op_name, attr_name, default)
        for i, item in enumerate(p_items):
            if item[0] == p_val:
                return i
        return 0

    @classmethod
    def set_operator_attr_int_enum(cls, op_name, attr_name, value, p_items):
        for i, item in enumerate(p_items):
            if i == value:
                cls.set_operator_attr(op_name, attr_name, item[0])


def update_areas_in_all_screens(context: bpy.types.Context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in {'VIEW_3D', 'IMAGE_EDITOR'}:
                area.tag_redraw()


def update_areas_in_uv(context: bpy.types.Context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.tag_redraw()


def update_areas_in_view3d(context: bpy.types.Context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def setnameex(self, value):

    def collection_from_element(self):
        # this gets the collection that the element is in
        path = self.path_from_id()
        match = re.match(r'(.*)\[\d*\]', path)
        parent = self.id_data
        try:
            coll_path = match.group(1)
        except AttributeError:
            raise TypeError("Propery not element in a collection.")
        else:
            return parent.path_resolve(coll_path)

    def new_val(stem, nbr):
        # simply for formatting
        return '{st}.{nbr:03d}'.format(st=stem, nbr=nbr)

    # =====================================================
    if value == self.get('name', ''):
        # check for assignement of current value
        return

    coll = collection_from_element(self)
    if value not in coll:
        # if value is not in the collection, just assign
        self['name'] = value
        return

    # see if value is already in a format like 'name.012'
    match = re.match(r'^(.*)\.(\d{3,})$', value)
    if match is None:
        stem, nbr = value, 1
    else:
        stem, nbr = match.groups()
        try:
            nbr = int(nbr)
        except Exception:
            nbr = 1

    # check for each value if in collection
    new_value = new_val(stem, nbr)
    while new_value in coll:
        nbr += 1
        new_value = new_val(stem, nbr)
    self['name'] = new_value


def calc_pixel_size(context, co):
    # returns size in blender units of a pixel at 3d coord co
    # see C code in ED_view3d_pixel_size and ED_view3d_update_viewmat
    m = context.region_data.perspective_matrix
    v1 = m[0].to_3d()
    v2 = m[1].to_3d()
    ll = min(v1.length_squared, v2.length_squared)
    len_pz = 2.0 / math.sqrt(ll)
    len_sz = max(context.region.width, context.region.height)
    rv3dpixsize = len_pz / len_sz
    proj = m[3][0] * co[0] + m[3][1] * co[1] + m[3][2] * co[2] + m[3][3]
    ups = context.preferences.system.pixel_size
    return proj * rv3dpixsize * ups


def draw_ex_last_operator_properties(context: bpy.types.Context, op_id, layout: bpy.types.UILayout):
    wm = context.window_manager
    op_last = wm.operator_properties_last(op_id)
    if op_last:
        op = bpy.types.Operator.bl_rna_get_subclass_py(op_last.__class__.__name__)
        if op:
            op.draw_ex(op_last, layout, context)


class ZenStrUtils:
    @classmethod
    def ireplace(cls, text, find, repl):
        return re.sub('(?i)' + re.escape(find), lambda m: repl, text)

    @classmethod
    def smart_replace(cls, text, props):
        err = ''
        new_name = ''
        try:
            if props.find != '':
                if props.use_regex:
                    new_name = re.sub(props.find, props.replace, text)
                else:
                    if props.match_case:
                        new_name = text.replace(props.find, props.replace)
                    else:
                        new_name = cls.ireplace(text, props.find, props.replace)
            else:
                new_name = props.replace
        except Exception as e:
            err = str(e)

        if new_name == '':
            new_name = text

        return (new_name, err)
