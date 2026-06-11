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

# Copyright 2023, Valeriy Yatsenko


import bpy
import bmesh

from dataclasses import dataclass

from ZenUV.utils.generic import ZUV_PANEL_CATEGORY, ZUV_REGION_TYPE, ZUV_SPACE_TYPE
from ZenUV.utils.generic import resort_by_type_mesh_in_edit_mode_and_sel, get_mesh_data


class ZUV_OT_ClearMeshAttributes(bpy.types.Operator):

    bl_idname = "uv.zenuv_clear_mesh_attrs"
    bl_label = 'Clear Attributes'
    bl_description = 'Clear mesh attributes used in the Zen UV. Finished and Excluded'
    bl_options = {'REGISTER'}

    clear_finished: bpy.props.BoolProperty(name='Finished', description='Clear Finished tag', default=True)
    clear_excluded: bpy.props.BoolProperty(name='Pack Excluded', description='Clear Pack Excluded tag', default=True)

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        from ZenUV.ops.pack_exclusion import PackExcludedFactory as PF
        from ZenUV.utils.constants import PACK_EXCLUDED_FACEMAP_NAME
        from ZenUV.utils.finishing_util import FINISHED_FACEMAP_NAME

        p_layer_names = []
        if self.clear_finished:
            p_layer_names.append(FINISHED_FACEMAP_NAME)
        if self.clear_excluded:
            p_layer_names.append(PACK_EXCLUDED_FACEMAP_NAME)

        for obj in objs:
            me, bm, _ = PF._get_obj_bm_data(obj)

            for p_name in p_layer_names:
                p_fmap = bm.faces.layers.int.get(p_name, None)
                if p_fmap is None:
                    continue
                bm.faces.layers.int.remove(p_fmap)
                bmesh.update_edit_mesh(me)

        bpy.ops.ed.undo_push(message='Clear Attributes')

        self.report({'INFO'}, 'Zen UV: Finished.')

        return {'FINISHED'}


@dataclass
class iCounterUnit:

    obj_name: str = ''
    total: int = 0
    hidden: int = 0


class ZUV_OT_IslandCounter(bpy.types.Operator):
    bl_idname = "uv.zenuv_island_counter"
    bl_label = 'UV Island Counter'
    bl_options = {'REGISTER'}
    bl_description = 'Count UV islands in selected objects and display the result'

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        from ZenUV.utils import get_uv_islands as island_util
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {"CANCELLED"}
        print('\nZen UV Island Counter:')
        storage = list()
        for obj in objs:
            _, bm = get_mesh_data(obj)
            i_count_total = len(island_util.get_islands(context, bm, is_include_hidden=True))
            storage.append(iCounterUnit(
                obj_name=obj.name,
                total=len(island_util.get_islands(context, bm, is_include_hidden=True)),
                hidden=i_count_total - len(island_util.get_islands(context, bm, is_include_hidden=False))
                ))

        self.report({'INFO'}, f'Total {sum([o.total for o in storage])}, Hidden {sum([o.hidden for o in storage])} Islands in {len(storage)} objects. Extended info in the system console.')

        print(''.join([f'\n{o.obj_name}\t\ttotal {o.total}\thidden {o.hidden}' for o in storage]) + '\n')

        return {'FINISHED'}


class ZUV_OT_SelectEmptyObjects(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_empty_objects"
    bl_label = 'Select Empty Objects'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = 'Selects objects that do not contain faces'

    def execute(self, context):
        objs = self.filter_instances(
            [obj for obj in context.scene.objects if obj.type == 'MESH' and len(obj.data.polygons) == 0])
        if not objs:
            self.report({'INFO'}, "Zen UV: No objects with missing faces were found.")
            return {"FINISHED"}
        print('\nZen UV Empty Islands report:\n')
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        for obj in context.scene.objects:
            obj.select_set(False)

        for obj in objs:
            print(obj.name)
            obj.select_set(True)

        context.view_layer.objects.active = objs[0]

        self.report({'INFO'}, f'Zen UV: Total {len(objs)} empty objects were found.')

        return {'FINISHED'}

    def filter_instances(self, objs):
        if len(objs) == 1:
            return objs
        res = []
        for p_obj in objs:
            if True not in [p_obj.data == t_obj.data for t_obj in res]:
                res.append(p_obj)
        return res


class ZUV_OT_SelectEdgesByIndex(bpy.types.Operator):
    """Select elements by their indices"""
    bl_idname = "object.zenuv_select_elements_by_index"
    bl_label = "Select Elements By Index"
    bl_options = {'REGISTER', 'UNDO'}

    # Test List [96969, 97796, 88516, 97816, 88381, 88362, 88447]

    selection_type: bpy.props.EnumProperty(
        name='Selection Type',
        items=[
            ("VERTEX", "Vertex", "Select vertices"),
            ("EDGE", "Edge", "Select edges"),
            ("FACE", "Face", "Select faces")
        ],
        default="VERTEX"
    )
    indices: bpy.props.StringProperty(name="Indices", description="Comma-separated list of indices to select")

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        indices = [int(idx) for idx in ''.join(self.indices.split()).split(',') if idx.isdigit()]

        if not indices:
            self.report({'ERROR'}, "Invalid edge indices")
            return {'CANCELLED'}

        obj = context.object
        if obj.type != 'MESH':
            self.report({'WARNING'}, 'Active object type is not a Mesh')
            return {'CANCELLED'}
        bpy.ops.mesh.select_all(action='DESELECT')

        bm = bmesh.from_edit_mesh(obj.data)
        if self.selection_type == "VERTEX":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            for i in {k.index for k in bm.verts}.intersection(set(indices)):
                bm.verts[i].select = True
        elif self.selection_type == "EDGE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            for i in {k.index for k in bm.edges}.intersection(set(indices)):
                bm.edges[i].select = True
        elif self.selection_type == "FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            for i in {k.index for k in bm.faces}.intersection(set(indices)):
                bm.faces[i].select = True

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ZUV_OT_SelectEdgesWithoutFaces(bpy.types.Operator):
    """ Select edges without faces """
    bl_idname = "object.zenuv_select_edges_without_faces"
    bl_label = "Select Edges Without Faces"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "There are no selected objects.")
            return {'CANCELLED'}
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            edges = [e for e in bm.edges if not e.link_faces]
            for e in edges:
                e.select = True
            bmesh.update_edit_mesh(obj.data)
        e_count = len(edges)
        if e_count:
            self.report({'WARNING'}, f'There are {e_count} edges without faces.')
        else:
            self.report({'INFO'}, 'There are no edges without faces.')
        return {'FINISHED'}


class ZUV_OT_SelectEdgesWithMultipleLoops(bpy.types.Operator):
    """ Select edges with Multiple Loops """
    bl_idname = "object.zenuv_select_edges_with_multiple_loops"
    bl_label = "Select Edges with multiple loops"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "There are no selected objects.")
            return {'CANCELLED'}
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

        for obj in objs:
            bm = bmesh.from_edit_mesh(obj.data)
            edge_idxs = [edge.index for edge in bm.edges if len(edge.link_loops) > 2]
            for i in edge_idxs:
                bm.edges[i].select = True
            bmesh.update_edit_mesh(obj.data)
        e_count = len(edge_idxs)
        if e_count:
            self.report({'WARNING'}, f'There are {e_count} edges with Multiple Loops.')
        else:
            self.report({'INFO'}, 'There are no edges with Multiple Loops.')
        return {'FINISHED'}


def draw_check_operators(self, layout):
    col = layout.column(align=True)
    col.label(text="Select:")
    col.operator(ZUV_OT_SelectEdgesByIndex.bl_idname, text=ZUV_OT_SelectEdgesByIndex.bl_label.replace('Select', ''))
    # Zero Area
    ot = col.operator('uv.zenuv_select_by_uv_area', text='Zero Area Faces')
    ot.mode = 'FACE'
    ot.clear_selection = True
    ot.condition = 'ZERO'
    ot.treshold = 0.5
    # --
    col.operator(ZUV_OT_SelectEdgesWithoutFaces.bl_idname, text=ZUV_OT_SelectEdgesWithoutFaces.bl_label.replace('Select', ''))
    col.operator(ZUV_OT_SelectEdgesWithMultipleLoops.bl_idname, text=ZUV_OT_SelectEdgesWithMultipleLoops.bl_label.replace('Select', ''))
    col.operator(ZUV_OT_SelectEmptyObjects.bl_idname, text=ZUV_OT_SelectEmptyObjects.bl_label.replace('Select', ''))

    col.label(text="Info:")
    col.operator(ZUV_OT_IslandCounter.bl_idname)

    col.label(text='Misc:')
    col.operator(ZUV_OT_ClearMeshAttributes.bl_idname)


class ZUV_PT_3DV_CheckPanel(bpy.types.Panel):
    """  Zen Trimsheet Transform Subpanel 3DV """
    bl_label = "Tools"
    bl_space_type = ZUV_SPACE_TYPE
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_Checker"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.scene.tool_settings.use_uv_select_sync

    def draw(self, context):
        draw_check_operators(context, self.layout)


class ZUV_PT_UVL_CheckPanel(bpy.types.Panel):
    """  Zen Trimsheet Transform Subpanel UV """
    bl_label = ZUV_PT_3DV_CheckPanel.bl_label
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_Checker_UVL"

    poll = ZUV_PT_3DV_CheckPanel.poll

    draw = ZUV_PT_3DV_CheckPanel.draw


@dataclass
class DisplayItem:
    modes: set = set(),
    spaces: set = set(),
    select_op_id: str = '',
    display_text: str = ''


t_draw_modes = {
    'FINISHED': DisplayItem({'EDIT_MESH'}, {'UV', '3D'}, 'uv.zenuv_select_finished'),
    'FLIPPED': DisplayItem({'OBJECT', 'EDIT_MESH'}, {'UV', '3D'}, 'uv.zenuv_select_flipped'),
    'STRETCHED': DisplayItem({'EDIT_MESH'}, {'3D'}, 'uv.zenuv_select_stretched_islands'),
    'EXCLUDED': DisplayItem({'EDIT_MESH'}, {'UV', '3D'}, 'uv.zenuv_select_pack_excluded'),
    'UV_NO_SYNC': DisplayItem({'EDIT_MESH'}, {'3D'}, ''),
    # 'TEXEL_DENSITY': DisplayItem({'EDIT_MESH'}, {'UV', '3D'}, ''),
}

t_draw_system_modes = {
    'TAGGED': DisplayItem({'EDIT_MESH'}, {'3D'}, ''),
}

t_draw_stack_modes = {
    'SIMILAR_STATIC': DisplayItem({'EDIT_MESH'}, {'UV', '3D'}, ''),
    'SIMILAR_SELECTED': DisplayItem({'EDIT_MESH'}, {'UV', '3D'}, 'uv.zenuv_select_similar'),
    'STACKED': DisplayItem({'EDIT_MESH'}, {'UV', '3D'}, 'uv.zenuv_select_stacked'),
}

t_draw_stack_manual_modes = {
    'STACKED_MANUAL': DisplayItem({'EDIT_MESH'}, {'UV', '3D'}, ''),
}


def draw_checker_display_items(layout: bpy.types.UILayout, context: bpy.types.Context, t_modes: dict):
    p_scene = context.scene

    b_active = context.space_data.overlay.show_overlays or not p_scene.zen_uv.ui.use_draw_overlay_sync
    if bpy.app.version >= (3, 3, 0):
        b_active = b_active and context.space_data.show_gizmo

    attr_name, p_mode = p_scene.zen_uv.ui.get_draw_mode_pair_by_context(context)
    s_space = attr_name.replace('draw_mode_', '')

    s_context_mode = context.mode

    col = layout.column(align=True)
    col.active = b_active

    v: DisplayItem
    for k, v in t_modes.items():
        if s_context_mode in v.modes and s_space in v.spaces:
            row = col.row(align=True)

            b_is_enabled = p_mode == k

            s_display_text = v.display_text if v.display_text else layout.enum_item_name(p_scene.zen_uv.ui, attr_name, k)

            op = row.operator('wm.context_set_enum', text=s_display_text, depress=b_is_enabled, icon='HIDE_OFF')
            op.data_path = 'scene.zen_uv.ui.' + attr_name
            op.value = 'NONE' if b_is_enabled else k
            if v.select_op_id:
                row.operator(v.select_op_id, text='', icon="RESTRICT_SELECT_OFF")


class ZUV_PT_3DV_CheckDisplayPanel(bpy.types.Panel):
    bl_label = "Display"
    bl_space_type = ZUV_SPACE_TYPE
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    # bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_Checker"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.active_object is None:
            return False
        if context.mode != 'EDIT_MESH':
            return False

        p_scene = context.scene
        if not context.space_data.overlay.show_overlays and p_scene.zen_uv.ui.use_draw_overlay_sync:
            return False

        if bpy.app.version >= (3, 3, 0):
            if not context.space_data.show_gizmo:
                return False

        return True

    def draw_header(self, context: bpy.types.Context):
        layout = self.layout

        layout.popover(panel='ZUV_PT_GizmoDrawProperties', text='', icon='PREFERENCES')

    @classmethod
    def poll_reason(cls, context: bpy.types.Context) -> str:
        if context.active_object is None:
            return 'No Active Object!'
        if context.mode != 'EDIT_MESH':
            return 'Available in Edit Mesh'

        p_scene = context.scene
        if not context.space_data.overlay.show_overlays and p_scene.zen_uv.ui.use_draw_overlay_sync:
            return """Turn Overlay On or
Enable Overlay Sync"""

        if bpy.app.version >= (3, 3, 0):
            if not context.space_data.show_gizmo:
                return 'Turn Show Gizmo On'

        return ""

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        t_blender_draws = {
            'show_edge_crease': 'Crease',
            'show_edge_sharp': 'Sharp',
            'show_edge_bevel_weight': 'Bevel',
            'show_edge_seams': 'Seams',
        }

        row = layout.row(align=True)
        for k, v in t_blender_draws.items():
            p_value = getattr(context.space_data.overlay, k)
            op = row.operator('wm.context_set_boolean', text=v, depress=p_value)
            op.data_path = f'space_data.overlay.{k}'
            op.value = not p_value

        draw_checker_display_items(layout, context, t_draw_modes)


class ZUV_PT_UVL_CheckDisplayPanel(bpy.types.Panel):
    bl_label = ZUV_PT_3DV_CheckDisplayPanel.bl_label
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    # bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_Checker_UVL"

    poll = ZUV_PT_3DV_CheckDisplayPanel.poll

    poll_reason = ZUV_PT_3DV_CheckDisplayPanel.poll_reason

    draw_header = ZUV_PT_3DV_CheckDisplayPanel.draw_header

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils
        from ZenUV.ops.trimsheets.darken_image import ZUV_OT_DarkenImage

        p_image = ZuvTrimsheetUtils.getActiveImage(context)
        row = layout.row(align=True)
        row.enabled = p_image is not None
        row.operator('uv.zuv_darken_image', depress=ZUV_OT_DarkenImage.is_mode_on(context))

        draw_checker_display_items(layout, context, t_draw_modes)


class ZUV_PT_3DV_SubStackPanel(bpy.types.Panel):
    bl_label = "Stacks"
    bl_space_type = ZUV_SPACE_TYPE
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_3DV_CheckDisplayPanel"

    def draw_header(self, context: bpy.types.Context):
        layout = self.layout

        layout.popover(panel='STACK_PT_DrawProperties', text='', icon='PREFERENCES')

    def draw(self, context):
        draw_checker_display_items(self.layout, context, {**t_draw_stack_modes, **t_draw_stack_manual_modes})


class ZUV_PT_UVL_SubStackPanel(bpy.types.Panel):
    bl_label = "Stacks"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_UVL_CheckDisplayPanel"

    draw_header = ZUV_PT_3DV_SubStackPanel.draw_header

    draw = ZUV_PT_3DV_SubStackPanel.draw


classes = (
    ZUV_OT_SelectEdgesByIndex,
    ZUV_OT_SelectEdgesWithoutFaces,
    ZUV_OT_SelectEdgesWithMultipleLoops,
    ZUV_OT_IslandCounter,
    ZUV_OT_SelectEmptyObjects,
    ZUV_OT_ClearMeshAttributes
)

checker_parented_panels = (
    ZUV_PT_3DV_CheckDisplayPanel,
    ZUV_PT_UVL_CheckDisplayPanel,

    ZUV_PT_3DV_SubStackPanel,

    ZUV_PT_3DV_CheckPanel,
    ZUV_PT_UVL_CheckPanel
)


def register():
    from bpy.utils import register_class
    for cl in classes:
        register_class(cl)


def unregister():
    from bpy.utils import unregister_class
    for cl in classes:
        unregister_class(cl)
