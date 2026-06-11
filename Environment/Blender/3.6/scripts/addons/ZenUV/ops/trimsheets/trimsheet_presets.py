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
from bl_operators.presets import AddPresetBase, ExecutePreset
from bpy.app.translations import (
    pgettext_tip as tip_,
)

from pathlib import Path

from .trimsheet_utils import ZuvTrimsheetUtils

from ZenUV.utils.blender_zen_utils import ZuvPresets


class ZUV_OT_TrimExecutePreset(bpy.types.Operator):
    bl_idname = "uv.zuv_execute_preset_in_imageeditor"

    bl_label = 'You are about to load trimsheet'
    bl_description = "Load trimsheet preset from file"

    filepath: bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE'},
    )

    # we need this to prevent 'getattr()' is None
    menu_idname: bpy.props.StringProperty(
        name="Menu ID Name",
        description="ID name of the menu this was called from",
        options={'SKIP_SAVE'},
        default='ZUV_MT_StoreTrimsheetPresets'
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

    def execute(self, context):
        # Use this method because if it is inherited, can not change Blender theme !
        res = ExecutePreset.execute(self, context)

        ZuvTrimsheetUtils.update_imageeditor_in_all_screens()

        return res


class ZUV_MT_StoreTrimsheetPresets(bpy.types.Menu):
    bl_label = 'Trimsheet Presets'

    default_label = 'Trimsheet Presets'

    preset_subdir = ZuvPresets.get_preset_path(ZuvTrimsheetUtils.TRIM_PRESET_SUBDIR)
    preset_operator = 'uv.zuv_execute_preset_in_imageeditor'

    draw = bpy.types.Menu.draw_preset


class ZUV_OT_TrimAddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'uv.zuv_add_trimsheet_preset'
    bl_label = 'Add|Remove Preset'
    preset_menu = 'ZUV_MT_StoreTrimsheetPresets'

    @classmethod
    def description(cls, context, properties):
        return ('Remove' if properties.remove_active else 'Add') + ' trimsheet preset'

    # Common variable used for all preset values
    preset_defines = [
        'prefs = bpy.context.scene.zen_uv if bpy.context.preferences.addons["ZenUV"].preferences.trimsheet.mode == "SCENE" else bpy.context.space_data.image.zen_uv'
    ]

    # Properties to store in the preset
    preset_values = [
        'prefs.trimsheet',
        'prefs.trimsheet_index',
    ]

    # Directory to store the presets
    preset_subdir = ZuvPresets.get_preset_path(ZuvTrimsheetUtils.TRIM_PRESET_SUBDIR)

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
