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

""" Zen Unwrap Utilites """

import bpy
import bmesh
import numpy as np
from dataclasses import dataclass, field
from mathutils import Vector
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.base_clusters.base_cluster import BaseCluster, ProjectCluster
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.finishing_util import (
    FINISHED_FACEMAP_NAME,
    finished_sort_islands,
    set_face_int_tag
)
from ZenUV.utils.constants import PACK_EXCLUDED_FACEMAP_NAME
from ZenUV.utils.generic import Diff
from ZenUV.utils.bounding_box import BoundingBox2d
from ZenUV.utils.texel_density import get_object_averaged_td, set_texel_density_to_faces
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.utils.vlog import Log


CAT = "ZenUnwrap"


class ProjectObj(BaseCluster, ProjectCluster):

    def __init__(self, context, obj, island, bm=None) -> None:
        super().__init__(context, obj, island, bm)


class UIslandsManager:

    def __init__(self, uobj, bm, uv_layer, STATE) -> None:
        self.bm = bm
        self.uv_layer = uv_layer
        self.loops = set((loop[uv_layer] for face in bm.faces for loop in face.loops if not face.hide))
        self.init_pins = set((loop for loop in self.loops if loop.pin_uv))
        self.islands = []
        self.positions = []
        self.finished_facemap = bm.faces.layers.int.get(FINISHED_FACEMAP_NAME, None)
        self.STATE = STATE
        self.PROPS = STATE.PROPS
        self.uobj = uobj
        # self.islands_loops = None

    def create_islands(self, context):
        # Islands creating before Unwrap.
        if self.PROPS.ProcessingMode == "SEAM_SWITCH":

            self.islands = [self.bm.faces, ]
            self.positions = self.calculate_centers()
            self.set_islands_seam_switch_mode()

        else:
            if self.STATE.OPM == 'SELECTION':


                if self.PROPS.ProcessingMode == 'SEL_ONLY':


                    if self.STATE.bl_selection_mode == "FACE":

                        self.ci_sel_sel_only_face(context)

                    elif self.STATE.bl_selection_mode == "EDGE":

                        self.ci_sel_sel_only_edge(context)

                    elif self.STATE.bl_selection_mode == "VERTEX":

                        self.ci_sel_sel_only_vertex(context)

                    else:
                        return {'CANCELLED'}


                    self.positions = self.calculate_centers()

                elif self.PROPS.ProcessingMode == 'WHOLE_MESH':

                    if self.STATE.bl_selection_mode == 'FACE':

                        self.ci_sel_whole_face(context)

                    elif self.STATE.bl_selection_mode == 'EDGE':

                        self.ci_sel_whole_edge(context)

                    else:

                        self.ci_sel_whole_vertex(context)

            elif self.STATE.OPM == 'ALL':  # Whole Mesh mode

                if self.PROPS.ProcessingMode == 'SEL_ONLY':


                    # Here is a point to show object personal warning.
                    # At the moment, there are no conditions for activating this mode.
                    bpy.ops.wm.call_menu(name="ZUV_MT_ZenUnwrap_ConfirmPopup")

                    return {"CANCELLED"}

                elif self.PROPS.ProcessingMode == 'WHOLE_MESH':
                    # Here is a point to check Seams
                    if self.uobj.seam_exist:

                        self.ci_all_whole_seam_exist(context)

                    else:

                        self.ci_all_whole_seam_not_exist(context)

            else:  # If STATE.OPM is not in {'ALL', 'SELECTION'}
                return {"CANCELLED"}


            self.set_islands()

    def ci_all_whole_seam_not_exist(self, context):
        if self.STATE.skip_warning is False:
            bpy.ops.wm.call_menu(name="ZUV_MT_ZenUnwrap_Popup")
            return {'CANCELLED'}
        else:
            self.set_seams_to_object(context, self.uobj, self.bm)

        self.islands = island_util.get_islands(context, self.bm)

        self.positions = self.calculate_centers()

    def ci_all_whole_seam_exist(self, context):
        bpy.ops.mesh.select_all(action='SELECT')
        # self.select_all(self.bm, action=True)
        self.islands = island_util.get_islands_by_seams(self.bm)
        self.positions = self.calculate_centers()
        self.STATE.fit_view = 'all'

    def ci_sel_whole_vertex(self, context):
        if not self.uobj.seam_exist:
            self.set_seams_to_object(context, self.uobj, self.bm)
        self.islands = island_util.get_islands(context, self.bm)
        self.positions = self.calculate_centers()

    def ci_sel_whole_edge(self, context):
        if not self.uobj.seam_exist:
            self.set_seams_to_object(context, self.uobj, self.bm)
        self.islands = island_util.get_islands(context, self.bm)
        self.positions = self.calculate_centers()

    def ci_sel_whole_face(self, context):

        all_faces_idxs = {f.index for f in self.bm.faces if not f.hide}
        selected_idxs = set(self.uobj.s_faces)
        rest_faces = [self.bm.faces[i] for i in all_faces_idxs.difference(selected_idxs)]
        selected_faces = [self.bm.faces[i] for i in self.uobj.s_faces]

        sel_position = self.calculate_centers([selected_faces, ])[0]
        rest_position = self.calculate_centers([rest_faces, ])[0] if len(rest_faces) else None


        if not rest_faces:
            pass
        if self.uobj.closed_mesh:
            pass
        if selected_faces:
            self.perform_iso_projection(context, self.uobj, self.bm, selected_faces)
        if len(rest_faces) == len(self.bm.faces):
            self.set_seams_to_object(context, self.uobj, self.bm)
            # self.perform_iso_projection(context, self.uobj, self.bm, self.bm.faces)
        self.islands = [rest_faces, selected_faces] if len(rest_faces) else [selected_faces]

        self.positions = [rest_position, sel_position] if rest_position is not None else [sel_position]
        self.STATE.one_by_one = True

    def ci_sel_sel_only_vertex(self, context):
        self.islands = island_util.get_island(context, self.bm, self.uv_layer)

    def ci_sel_sel_only_edge(self, context):
        self.islands = island_util.get_island(context, self.bm, self.uv_layer)

    def ci_sel_sel_only_face(self, context):
        if self.uobj.closed_mesh:
            self.perform_iso_projection(context, self.uobj, self.bm, self.bm.faces)
        self.islands = island_util.get_islands_selected_only(self.bm, [self.bm.faces[i] for i in self.uobj.s_faces])

    def set_seams_to_object(self, context, uobj, bm):
        if self.STATE.PROPS.Mark and self.STATE.operator_mode == "CONTINUE":
            bpy.ops.uv.zenuv_unified_mark(convert='SEAM_BY_UV_BORDER')
            if not uobj.update_seam_exist():
                bpy.ops.uv.zenuv_unified_mark(convert='SEAM_BY_OPEN_EDGES')
            if not uobj.update_seam_exist():
                PC = ProjectObj(context, uobj.obj, bm.faces, bm=bm)
                PC.project()

    def set_seams_in_vertex_processing_mode(self, context, uobj, bm):
        bpy.ops.uv.zenuv_unified_mark(convert='SEAM_BY_UV_BORDER')
        if not uobj.update_seam_exist():
            bpy.ops.uv.zenuv_unified_mark(convert='SEAM_BY_OPEN_EDGES')
        if not uobj.update_seam_exist():
            free_edges = [e for e in bm.edges if True not in [v.select for v in e.verts]]
            if free_edges:
                free_edges[0].seam = True
            else:
                return False
        return True

    def z_unuwrap(self, context, bm):
        if self.STATE.one_by_one:
            for island in self.islands:
                bpy.ops.mesh.select_all(action='DESELECT')
                for f in island:
                    f.select = True
                # deselect_finished(bm, self.finished_facemap)
                self._unwrap(context, bm)
        else:
            bpy.ops.mesh.select_all(action='DESELECT')
            self.select_for_unwrap(self.STATE.sync_mode)
            # deselect_finished(bm, self.finished_facemap)
            self._unwrap(context, bm)

    def _unwrap(self, context, bm):
        addon_prefs = get_prefs()
        if self.PROPS.ProcessingMode == "SEAM_SWITCH" and not self.uobj.update_seam_exist(bm):
            self.perform_iso_projection(context, self.uobj, self.bm, self.bm.faces)

        if bpy.ops.uv.unwrap.poll():
            bpy.ops.uv.unwrap(
                    method=self.STATE.PROPS.UnwrapMethod,
                    fill_holes=self.STATE.PROPS.fill_holes,
                    # correct_aspect=self.STATE.PROPS.correct_aspect,
                    # ue_subsurf_data=self.use_subsurf_data,
                    margin=addon_prefs.margin
                )

    def pin_all_but_not_sel(self):
        for loop in (loop for face in self.bm.faces for loop in face.loops if not face.hide):
            loop[self.uv_layer].pin_uv = not loop.vert.select

    def restore_pins(self):
        for loop in self.loops.difference(self.init_pins):
            loop.pin_uv = False

        for loop in self.init_pins:
            loop.pin_uv = True

    def _remove_finished_clusters(self, clusters):
        return [cl for cl in clusters if cl.finished]

    def set_islands(self):
        init_clusters = [
            uCluster(
                cluster=island,
                position=position,
                finished=True not in [f[self.finished_facemap] for f in island] if self.finished_facemap is not None else True
            ) for island, position in zip(self.islands, self.positions) if island]
        clusters = self._remove_finished_clusters(init_clusters)
        if len(init_clusters) != len(clusters):
            self.STATE.finished_came_across = True
        self.islands = [cl.cluster for cl in clusters]
        self.positions = [cl.position for cl in clusters]
        for island in self.islands:
            p_loops = [loop[self.uv_layer] for f in island for loop in f.loops]
            for i in range(len(p_loops) - 1):
                p_loops[i].pin_uv = False

    def set_islands_seam_switch_mode(self):
        if self.finished_facemap is not None:
            self.islands = [[f for island in self.islands for f in island if not f[self.finished_facemap]], ]

    def select_for_unwrap(self, sync):
        if not sync:
            for loop in [loop[self.uv_layer] for island in self.islands for f in island for loop in f.loops]:
                loop.select = True
        else:
            for face in [f for i in self.islands for f in i]:
                face.select = True

    def calculate_centers(self, islands=None):
        if not islands:
            islands = self.islands
        return [BoundingBox2d(islands=[island, ], uv_layer=self.uv_layer, safe_mode=False).center for island in islands]

    def set_averaged_td(self, context, uobj, bm):
        if not self.PROPS.ProcessingMode == "SEAM_SWITCH" and self.STATE.is_avg_td_allowed(uobj.td_inputs):
            sel_only = self.STATE.PROPS.ProcessingMode == 'SEL_ONLY'

            islands = self._get_islands_for_avg_td(context, bm, uobj, sel_only)

            uobj.td_inputs.by_island = False if sel_only else True
            for island in islands:
                set_texel_density_to_faces(context, uobj.obj, island, uobj.td_inputs)
        else:
            pass

    def _get_islands_for_avg_td(self, context, bm, uobj, sel_only):

        if self.STATE.bl_selection_mode == "EDGE":
            islands = island_util.get_islands_by_edge_list_indexes(bm, uobj.s_edges)
        elif self.STATE.bl_selection_mode == "FACE":
            islands = [uobj.s_faces, ] if sel_only else [uobj.all_faces, ]
        else:
            islands = island_util.get_islands_by_vert_list_indexes(bm, uobj.s_verts, _sorted=True)
        if not islands:
            islands = island_util.get_islands(context, bm)
        return islands

    def set_islands_positions(self, offset=False):

        if not self.PROPS.ProcessingMode == "SEAM_SWITCH" and self.STATE.is_pack_allowed() is False and self.positions:
            if offset:
                pos_set = (np.array(self.positions) + [0.00001, 0.00001]).tolist()
            else:
                pos_set = (np.array(self.positions)).tolist()

            for island, co in zip(self.islands, pos_set):
                i_cen = BoundingBox2d(islands=[island, ], uv_layer=self.uv_layer).center
                for loop in [loop for face in island for loop in face.loops]:
                    loop[self.uv_layer].uv += Vector(co) - i_cen
        else:
            pass

    def split_selected_faces(self, context, uobj, bm, uv_layer):
        # Split selected faces and create single island
        islands = island_util.get_islands_selected_only(bm, [bm.faces[i] for i in uobj.s_faces])
        faces = [bm.faces[i] for i in uobj.s_faces]
        PC = ProjectObj(context, uobj.obj, faces, bm=bm)
        PC.project()
        islands = island_util.get_islands(context, bm)
        return islands

    def perform_iso_projection(self, context, uobj, bm, selection):
        ProjectObj(context, uobj.obj, selection, bm=bm).project()


@dataclass
class uCluster:

    cluster: list = field(default_factory=list)
    position: Vector = Vector((0.0, 0.0))
    finished: bool = False


class uObject:

    def __init__(self, context, obj) -> None:
        self.obj = obj
        bm = bmesh.from_edit_mesh(obj.data).copy()

        self.s_faces = [f.index for f in bm.faces if f.select and not f.hide]
        self.all_faces = [f.index for f in bm.faces if not f.hide]
        self.closed_mesh = False

        self.finished_faces = self.get_finished_faces(bm)

        self.s_edges = [e.index for e in bm.edges if e.select]
        self.s_verts = [v.index for v in bm.verts if v.select]
        self.sel_exist = (len(self.s_verts) != 0)  # or self.s_edges or self.s_verts
        self.seam_exist = self._get_seam_exist(bm)
        # self.init_seams = [e.index for e in bm.edges if e.seam]
        exclude = self.s_faces if context.scene.zen_uv.op_zen_unwrap_sc_props.ProcessingMode == 'SELECTED' else []
        self.td_inputs = get_object_averaged_td(context, obj, bm, exclude=exclude, precision=20)
        self.ready_to_unwrap = self.seam_exist or self.sel_exist
        self.seam_state = []
        self.is_pack_excluded = self.solve_is_pack_excluded(bm)
        self.pack_excluded = []
        if self.is_pack_excluded:
            self.store_pack_excluded(context, bm)
        bm.free()

    def solve_is_pack_excluded(self, bm):
        excl_fmap = bm.faces.layers.int.get(PACK_EXCLUDED_FACEMAP_NAME, None)
        if excl_fmap is not None:
            return True
        return False

    def get_finished_faces(self, bm: bmesh.types.BMesh):
        fin_fmap = bm.faces.layers.int.get(FINISHED_FACEMAP_NAME, None)
        if fin_fmap is not None:
            return [f.index for f in bm.faces if f[fin_fmap]]
        else:
            []

    def store_pack_excluded(self, context, bm):
        _facemap = bm.faces.layers.int.get(PACK_EXCLUDED_FACEMAP_NAME, None)
        islands = [island for island in island_util.get_islands(context, bm) if True in [f[_facemap] for f in island]]
        self.pack_excluded = [f.index for island in islands for f in island]

    def hide_pack_excluded(self, bm):
        bm.faces.ensure_lookup_table()
        faces = [f for f in [bm.faces[i] for i in self.pack_excluded] if not f.select]
        for f in faces:
            f.hide_set(True)
        bmesh.update_edit_mesh(self.obj.data)

    def unhide_pack_excluded(self, bm):
        bm.faces.ensure_lookup_table()
        for i in self.pack_excluded:
            bm.faces[i].hide_set(False)

    def clear_temp_seams(self):
        bm = bmesh.from_edit_mesh(self.obj.data)
        bm.edges.ensure_lookup_table()
        for i in self.s_edges:
            bm.edges[i].seam = False
        bmesh.update_edit_mesh(self.obj.data)

    def _get_seam_exist(self, bm):
        return True in [e.seam for e in bm.edges]

    def update_seam_exist(self, bm=None):
        if not bm:
            bm = bmesh.from_edit_mesh(self.obj.data).copy()
            self.seam_exist = self._get_seam_exist(bm)
            bm.free()
        else:
            self.seam_exist = self._get_seam_exist(bm)
        return self.seam_exist

    def clear_finished_and_vcolor(self, bm):
        if not bm.loops.layers.uv.items():

            finished_facemap = bm.faces.layers.int.get(FINISHED_FACEMAP_NAME, None)
            if finished_facemap is not None:
                set_face_int_tag([bm.faces], finished_facemap, int_tag=0)

    def sorting_finished(self, context):
        """ This must be redone. """
        me = self.obj.data
        bm = bmesh.from_edit_mesh(me)
        uv_layer = bm.loops.layers.uv.verify()

        finished_facemap = bm.faces.layers.int.get(FINISHED_FACEMAP_NAME, None)
        if finished_facemap is None:
            return
        if self.is_pack_excluded:
            self.hide_pack_excluded(bm)
        all_islands = island_util.get_islands(context, bm)
        if self.sel_exist:
            current_islands = island_util.get_island(context, bm, uv_layer)
            finished_sort_islands(bm, Diff(all_islands, current_islands), finished_facemap)
        else:
            finished_sort_islands(bm, all_islands, finished_facemap)

        if self.is_pack_excluded:
            self.unhide_pack_excluded(bm)

        bmesh.update_edit_mesh(me, loop_triangles=False)

    def select_set(self, state=True):
        self.obj.select_set(state=state)

    def restore_selection(self, sm, bm=None):
        # if not bm:
        me = self.obj.data
        bm = bmesh.from_edit_mesh(me)
        self._restore_selection(bm, sm)
        bm.select_flush_mode()
        bmesh.update_edit_mesh(me)

    def _restore_selection(self, bm, mode):
        """ Restore selected elements depending of Blender selection Mode """
        if mode == 'VERTEX':
            bm.verts.ensure_lookup_table()
            for index in self.s_verts:
                bm.verts[index].select = True
        if mode == 'FACE':
            bm.faces.ensure_lookup_table()
            for index in self.s_faces:
                bm.faces[index].select = True
        if mode == 'EDGE':
            bm.edges.ensure_lookup_table()
            for index in self.s_edges:
                bm.edges[index].select = True

    def restore_seams(self, bm=None):
        # if not bm:
        me = self.obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.edges.ensure_lookup_table()
        self._restore_seams(bm)
        bm.select_flush_mode()
        bmesh.update_edit_mesh(me)

    def _restore_seams(self, bm):
        for e, state in zip(bm.edges, self.seam_state):
            e.seam = state


if __name__ == '__main__':
    pass
