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


from ...operator import UVPM3_OT_Engine, ModeIdAttributeMixin
from ...operator_islands import UVPM3_OT_ShowManualGroupIParamBase
from ...grouping_scheme import TargetGroupingSchemeMixin
from ...enums import GroupingMethod, UvpmIParamFlags
from ...group import UVPM3_GroupInfo
from ...grouping_scheme_access import GroupingSchemeAccess
from ...utils import redraw_ui
from .grouping_editor_operator import UVPM3_OT_EditGroupingSchemeInEditor

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, EnumProperty, CollectionProperty, PointerProperty



class UVPM3_OT_AlignGeneric(UVPM3_OT_Engine):

    def split_offset_enabled(self):
        return False


class UVPM3_OT_SelectSimilar(UVPM3_OT_AlignGeneric, ModeIdAttributeMixin):

    bl_idname = 'uvpackmaster3.select_similar'
    bl_label = 'Select Similar'
    bl_description = "From all unselected islands, selects all islands which have similar shape to at least one island which is currently selected. For more info regarding similarity detection click the help button"

    SCENARIO_ID = 'align.select_similar'

    def send_unselected_islands(self):
        return True


class UVPM3_OT_AlignSimilar(UVPM3_OT_AlignGeneric, ModeIdAttributeMixin):

    bl_idname = 'uvpackmaster3.align_similar'
    bl_label = 'Align Similar (Stack)'
    bl_description = "Align the selected islands, so islands which are similar are stacked on the top of each other. For more info regarding similarity detection click the help button"

    SCENARIO_ID = 'align.align_similar'



def _simi_group_name(group_num):
    return 'S{}'.format(group_num)


class UVPM3_OT_GroupBySimilarity(TargetGroupingSchemeMixin, UVPM3_OT_ShowManualGroupIParamBase, UVPM3_OT_AlignGeneric, ModeIdAttributeMixin):

    bl_idname = 'uvpackmaster3.group_by_similarity'
    bl_label = 'Group By Similarity'
    bl_description = 'Group all selected islands by similarity and save generated groups in a grouping scheme'

    SCENARIO_ID = 'align.split_by_similarity'


    min_group_size : IntProperty(
        name='Minimum Group Size',
        description='All similarity groups of size lower than the value of this parameter will be ignored and their islands will be reassigned to the default group ({}). If the functionality is not used (value set to 1), the default group will be empty'.format(_simi_group_name(UVPM3_GroupInfo.DEFAULT_GROUP_NUM)),
        min=1,
        max=100,
        default=1)

    def target_scheme_name_impl(self, context):
        return "Scheme 'Similarity'"
    
    def draw_impl(self, context):
        layout = self.layout

        if (not self.create_new_g_scheme()) and (len(self.get_g_schemes()) > 0):
            row = layout.row()
            row.label(text='WARNING: operation will overwrite all groups in the existing scheme.')

        row = layout.row()
        row.prop(self, 'min_group_size')

    def pre_operation(self):
        target_g_scheme = self.get_target_g_scheme()

        idx = 0
        while idx < len(target_g_scheme.groups):
            group = target_g_scheme.groups[idx]

            if not group.is_default():
                target_g_scheme.remove_group(idx)
            else:
                idx = idx + 1

        assert len(target_g_scheme.groups) == 1
        def_group = target_g_scheme.groups[0]
        def_group.name = _simi_group_name(def_group.num)
        
        super().pre_operation()

    def post_operation(self):
        self.init_access(self.context)
        UVPM3_OT_EditGroupingSchemeInEditor.execute_impl(self.context, self.get_active_g_scheme_idx())

        super().post_operation()

    def get_save_iparam_handler(self):

        def save_iparam_handler(iparam_info, g_num):
            group = self.active_g_scheme.get_group_by_num(g_num)
            if not group:
                self.active_g_scheme.add_group_with_target_box(_simi_group_name(g_num), g_num)

        return save_iparam_handler
    
    def setup_script_params(self):
        script_params = super().setup_script_params()
        script_params.add_param('target_iparam_name', self.active_g_scheme.get_iparam_info().script_name)
        script_params.add_param('min_group_size', self.min_group_size)
        return script_params


class UVPM3_OT_SplitOverlappingGeneric(UVPM3_OT_AlignGeneric):

    def split_offset_enabled(self):
        return True
    
    def split_offset_iparam_flags(self):
        return 0

    def operation_done_hint(self):
        return ''


class UVPM3_OT_SplitOverlapping(UVPM3_OT_SplitOverlappingGeneric, ModeIdAttributeMixin):

    bl_idname = 'uvpackmaster3.split_overlapping'
    bl_label = 'Split Overlapping Islands'
    bl_description = 'Methodically move overlapping islands to adjacent tiles (in the +X axis direction), so that no selected islands are overlapping each other after the operation is done'

    SCENARIO_ID = 'align.split_overlapping'

    def split_offset_iparam_flags(self):
        return UvpmIParamFlags.CONSISTENCY_CHECK_DISABLE


class UVPM3_OT_UndoIslandSplit(UVPM3_OT_SplitOverlappingGeneric, ModeIdAttributeMixin):

    bl_idname = 'uvpackmaster3.undo_island_split'
    bl_label = 'Undo Island Split'
    bl_description = 'Undo the last island split operation - move all selected islands to their original locations before split. WARNING: the operation only process currently selected islands so in order to move an island to its original location, you have to make sure the island is selected when an Undo operation is run'

    SCENARIO_ID = 'align.undo_island_split'

    def skip_topology_parsing(self):
        return True
