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

""" Init Zen UV """
import bpy

import sys
import importlib
import os
import json

from ZenUV.utils.blender_zen_utils import ZenPolls
from ZenUV.utils.vlog import Log
from ZenUV.utils.translations import translations_dict


bl_info = {
    "name": "Zen UV",
    "author": "Valeriy Yatsenko, Alex Zhornyak, Sergey Tyapkin, Viktor [VAN] Teplov",
    "version": (4, 1, 0, 4),
    "description": "Optimize UV mapping workflow",
    "blender": (2, 93, 0),
    "location": "View3D > Sidebar > Zen UV",
    "category": "UV",
    "tracker_url": "https://discordapp.com/invite/wGpFeME",
    "doc_url": "https://zenmastersteam.github.io/Zen-UV/4.0/"
}


module_names = [
    ('.ico', 'ZenUV'),
    ('.ops', 'ZenUV'),
    ('.ui', 'ZenUV'),
    ('.prop', 'ZenUV'),
    ('.zen_checker', 'ZenUV'),
    ('.stacks', 'ZenUV'),
    ('.sticky_uv_editor', 'ZenUV'),
    ('.addon_test', 'ZenUV.utils.tests'),
    ('.clib', 'ZenUV.utils'),
    ('.system_operators', 'ZenUV.utils.tests'),
    ('.keymap_manager', 'ZenUV.ui')
]


user_module = None


def register():
    """ Register classes """

    if bpy.app.background:
        return

    if bpy.app.version >= (3, 2, 0):
        ZenPolls.version_greater_3_2_0 = True

    if bpy.app.version < (3, 4, 0):
        ZenPolls.version_lower_3_4_0 = True

    if bpy.app.version < (3, 5, 0):
        ZenPolls.version_lower_3_5_0 = True

    ZenPolls.doc_url = bl_info['doc_url']

    try:
        if Log.ENABLE_DEBUG:
            base_dir = os.path.dirname(__file__)
            with open(os.path.join(base_dir, 'log.json'), 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                Log.CATEGORY = data['Category']
    except Exception:
        pass

    for name, package in module_names:
        mod = importlib.import_module(name, package)
        mod.register()

    bpy.app.translations.register(__name__, translations_dict)

    try:
        from ZenUV.prop.zuv_preferences import get_prefs

        addon_prefs = get_prefs()

        if addon_prefs.user_script.file_path:
            if os.path.exists(addon_prefs.user_script.file_path):
                spec = importlib.util.spec_from_file_location(
                    "ZenUV.user_script", addon_prefs.user_script.file_path)
                global user_module
                user_module = importlib.util.module_from_spec(spec)
                sys.modules["ZenUV.user_script"] = user_module
                spec.loader.exec_module(user_module)
                user_module.register()
    except Exception as e:
        Log.error('LOAD USER SCRIPT:', str(e))


def unregister():
    """ Unregister classes """

    if bpy.app.background:
        return

    if user_module:
        try:
            user_module.unregister()
        except Exception as e:
            Log.error('UNLOAD USER SCRIPT:', str(e))

    bpy.app.translations.unregister(__name__)

    for name, package in reversed(module_names):
        mod_name = package + name
        mod = sys.modules.get(mod_name)
        if mod:
            mod.unregister()
