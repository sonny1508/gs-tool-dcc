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

""" Zen UV Islands Processor """

import bpy
import bmesh
# from ZenUV.utils.generic import Timer
from ZenUV.utils.blender_zen_utils import ZenPolls

from ZenUV.utils.vlog import Log


def get_active_component(context: bpy.types.Context, bm: bmesh.types.BMesh, component_type: str = 'ISLAND'):
    if context.tool_settings.mesh_select_mode[:] == (False, False, True):
        a_face = bm.faces.active
        if a_face is not None:
            return [get_islands_by_face_list_indexes(bm, [a_face.index, ]), 'ISLAND'] if component_type == 'ISLAND' else [a_face, 'FACE']

    if len(bm.select_history) > 0:
        active_element = bm.select_history[-1]
        if isinstance(active_element, bmesh.types.BMVert):
            return [get_islands_by_vert_list_indexes(bm, [active_element.index, ]), 'ISLAND'] if component_type == 'ISLAND' else [active_element, 'VERTEX']
        elif isinstance(active_element, bmesh.types.BMEdge):
            return [get_islands_by_edge_list_indexes(bm, [active_element.index, ]), 'ISLAND'] if component_type == 'ISLAND' else [active_element, 'EDGE']
        elif isinstance(active_element, bmesh.types.BMFace):
            return [get_islands_by_face_list_indexes(bm, [active_element.index, ]), 'ISLAND'] if component_type == 'ISLAND' else [active_element, 'FACE']
        else:
            return None, 'NONE'
    else:
        return None, 'NONE'


def sort_island_faces(f):
    return f.index


def get_islands_by_face_list(context, bm, faces, uv_layer):
    ''' Return islands by indexes '''
    # faces = [bm.faces[index] for index in indexes]
    selection = [f for f in faces if not f.hide]

    return zen_get_islands(bm, selection, has_selected_faces=True)


def get_islands_by_edge_list_indexes(bm, edge_list):
    ''' Return islands by indexes '''
    # faces = [bm.faces[index] for index in indexes]
    bm.edges.ensure_lookup_table()
    selection = {face for edge in [bm.edges[index] for index in edge_list] for face in edge.link_faces if not face.hide}
    return zen_get_islands(bm, selection, has_selected_faces=True)


def get_islands_by_vert_list_indexes(bm, verts, _sorted=False):
    ''' Return islands by indexes '''
    bm.verts.ensure_lookup_table()
    selection = [face for vert in [bm.verts[index] for index in verts] for face in vert.link_faces if not face.hide]
    return zen_get_islands(bm, selection, has_selected_faces=True, _sorted=_sorted)


def get_islands_by_seams(bm):
    ''' Return islands by seams '''
    return zen_get_islands_by_seams(bm, bm.faces, _sorted=True, by_seams=True)


def get_islands_by_face_list_indexes(bm, face_list):
    ''' Return islands by indexes '''
    # faces = [bm.faces[index] for index in indexes]
    bm.faces.ensure_lookup_table()
    selection = [bm.faces[index] for index in face_list if not bm.faces[index].hide]
    return zen_get_islands(bm, selection, has_selected_faces=True)


def get_island(context, bm, uv_layer, _sorted: bool = False):
    ''' Return island (s) by selected faces, edges or vertices '''
    bm.faces.ensure_lookup_table()
    selection = [bm.faces[index] for index in FacesFactory.face_indexes_by_sel_mode(context, bm)]
    return zen_get_islands(bm, selection, has_selected_faces=True, _sorted=_sorted)


def get_selected_faces(context, bm):
    selection = [bm.faces[index] for index in FacesFactory.face_indexes_by_sel_mode(context, bm)]
    if selection:
        return [selection, ]
    return []


def get_islands_legacy(bm):
    ''' Return all islands from mesh '''
    return zen_get_islands(bm, None, has_selected_faces=False)


def get_islands(context: bpy.types.Context, bm: bmesh.types.BMesh, is_include_hidden: bool = False):
    ''' Return all islands from mesh '''
    sync_uv = context.scene.tool_settings.use_uv_select_sync
    if is_include_hidden:
        return zen_get_islands(bm, bm.faces, is_include_hidden=True)

    if context.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
        faces = {f for f in bm.faces if f.select}
    else:
        faces = {f for f in bm.faces if not f.hide}
    return zen_get_islands(bm, faces, has_selected_faces=True)


def get_island_by_loops(bm: bmesh.types.BMesh, loops: list):
    ''' Return all islands from given loops '''
    faces = list({loop.face for loop in loops})
    return list(zen_get_islands(bm, faces, has_selected_faces=True))


def get_islands_in_indices(bm):
    ''' Return all islands as indices from mesh '''
    islands_ind = []
    islands = zen_get_islands(bm, None, has_selected_faces=False)
    for island in islands:
        islands_ind.append([f.index for f in island])
    return islands_ind


def get_islands_selected_only(bm, selection):
    """ Return islands consist from selected faces only """
    return [sorted(island, key=sort_island_faces) for island in zen_get_islands(bm, selection, True, True)]
    # return zen_get_islands(bm, selection, True, True)


def uv_bound_edges_indexes(faces, uv_layer):
    """ Return indexes of border edges of given island (faces) from current UV Layer """
    if faces:
        edges = {edge for face in faces for edge in face.edges if edge.link_loops}
        return [edge.index for edge in edges
                if edge.link_loops[0][uv_layer].uv
                != edge.link_loops[0].link_loop_radial_next.link_loop_next[uv_layer].uv
                or edge.link_loops[-1][uv_layer].uv
                != edge.link_loops[-1].link_loop_radial_next.link_loop_next[uv_layer].uv]
    return []


def get_bound_edges(edges_from_polygons):
    boundary_edges = []
    for edge in edges_from_polygons:
        if False in [f.select for f in edge.link_faces] or edge.is_boundary:
            boundary_edges.append(edge.index)
    return boundary_edges


def get_bound_edges_idxs_from_selected_faces(faces):
    if len(faces) == 1:
        return set()
    return {e.index for e in [e for f in faces for e in f.edges] if False in [f.select for f in e.link_faces] or e.is_boundary}


def zen_get_islands(
    bm: bmesh.types.BMesh,
    _selection: list,
    has_selected_faces: bool = False,
    selected_only: bool = False,
    _sorted: bool = False,
    is_include_hidden: bool = False
) -> list:
    # print("SELECTION: ", _selection)
    uv_layer = bm.loops.layers.uv.verify()
    if not selected_only:
        _bounds = uv_bound_edges_indexes(bm.faces, uv_layer)
    else:
        _bounds = get_bound_edges([e for f in _selection for e in f.edges])
    bm.edges.ensure_lookup_table()
    for edge in bm.edges:
        edge.tag = False
    # Tag all edges in uv borders
    for index in _bounds:
        bm.edges[index].tag = True
        # print(bm.edges[index], bm.edges[index].tag)

    _islands = []
    if has_selected_faces:
        faces = set(_selection)
    # if has_selected_faces:
    #     faces = {f for f in bm.faces if f.select}
        # faces = {f for f in bm.faces for l in f.loops if l[uv_layer].select}
    else:
        faces = set(bm.faces)
    while len(faces) != 0:
        init_face = faces.pop()
        island = {init_face}
        stack = [init_face]
        while len(stack) != 0:
            face = stack.pop()
            for e in face.edges:
                if not e.tag:
                    for f in e.link_faces:
                        if f not in island:
                            stack.append(f)
                            island.add(f)
        for f in island:
            faces.discard(f)
        if not is_include_hidden and True in [f.hide for f in island]:
            continue
        _islands.append(island)
    for index in _bounds:
        bm.edges[index].tag = False

    if _sorted:
        return [sorted(island, key=sort_island_faces) for island in _islands]

    return _islands


def zen_get_islands_by_seams(bm, _selection, has_selected_faces=False, selected_only=False, _sorted=False, by_seams=False):
    # print("SELECTION: ", _selection)
    uv_layer = bm.loops.layers.uv.verify()
    if not selected_only:
        _bounds = uv_bound_edges_indexes(bm.faces, uv_layer)
    elif selected_only:
        _bounds = get_bound_edges([e for f in _selection for e in f.edges])
    if by_seams:
        _bounds = [e.index for e in bm.edges if e.seam]

    bm.edges.ensure_lookup_table()
    for edge in bm.edges:
        edge.tag = False
    # Tag all edges in uv borders
    for index in _bounds:
        bm.edges[index].tag = True
        # print(bm.edges[index], bm.edges[index].tag)

    _islands = []
    if has_selected_faces:
        faces = set(_selection)
    # if has_selected_faces:
    #     faces = {f for f in bm.faces if f.select}
        # faces = {f for f in bm.faces for l in f.loops if l[uv_layer].select}
    else:
        faces = set(bm.faces)
    while len(faces) != 0:
        init_face = faces.pop()
        island = {init_face}
        stack = [init_face]
        while len(stack) != 0:
            face = stack.pop()
            for e in face.edges:
                if not e.tag:
                    for f in e.link_faces:
                        if f not in island:
                            stack.append(f)
                            island.add(f)
        for f in island:
            faces.discard(f)
        if True in [f.hide for f in island]:
            continue
        _islands.append(island)
    for index in _bounds:
        bm.edges[index].tag = False

    if _sorted:
        return [sorted(island, key=sort_island_faces) for island in _islands]

    return _islands


class FacesFactory:

    @classmethod
    def face_indexes_by_sel_mode(cls, context, bm):
        """ Return face indexes converted from selected elements """
        uv_layer = bm.loops.layers.uv.verify()
        sync_uv = context.scene.tool_settings.use_uv_select_sync
        if context.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
            mode = context.scene.tool_settings.uv_select_mode
            # sel_faces = set()
            # sel_faces.update([f.index for f in bm.faces for loop in f.loops if loop[uv_layer].select])
            # sel_faces.update({f.index for f in bm.faces for loop in f.loops if not f.hide and f.select and loop[uv_layer].select})
            if ZenPolls.version_greater_3_2_0:
                if mode == 'VERTEX':
                    return list({f.index for f in bm.faces if not f.hide and f.select and True in [loop[uv_layer].select for loop in f.loops]})
                else:
                    return list({f.index for f in bm.faces for loop in f.loops if not f.hide and f.select and loop[uv_layer].select and loop[uv_layer].select_edge})
            else:
                if mode == 'VERTEX':
                    return list({f.index for f in bm.faces if not f.hide and f.select and True in [loop[uv_layer].select for loop in f.loops]})
                else:
                    return list({f.index for f in bm.faces for loop in f.loops if not f.hide and f.select and loop[uv_layer].select})
            # if sel_faces:
            #     selection.extend(list(sel_faces))
        else:
            mode = context.tool_settings.mesh_select_mode
            if mode[1]:
                return [face.index for edge in [e for e in bm.edges if e.select] for face in edge.link_faces if not face.hide]
            elif mode[2]:
                return [face.index for face in bm.faces if face.select and not face.hide]
            elif mode[0]:
                return [face.index for vert in [v for v in bm.verts if v.select] for face in vert.link_faces if not face.hide]


class LoopsFactory:

    @classmethod
    def loops_by_islands(
        cls,
        context: bpy.types.Context,
        bm: bmesh.types.BMesh,
        uv_layer: bmesh.types.BMLayerItem,
    ) -> list:

        return [[lp for f in island for lp in f.loops] for island in get_island(context, bm, uv_layer)]

    @classmethod
    def loops_by_sel_mode(
        cls,
        context: bpy.types.Context,
        bm: bmesh.types.BMesh,
        uv_layer: bmesh.types.BMLayerItem,
        only_uv_edges: bool = False,
        groupped: bool = False,
        per_face: bool = False
    ) -> list:

        """ Return loops based on selected elements """

        loops = cls._loops_by_sel_mode(context, bm.faces, uv_layer, only_uv_edges, per_face)

        if groupped:
            if per_face:
                loops = [lp for cl in loops for lp in cl]
            return cls.compound_groups_from_loops(loops, uv_layer)

        return loops

    @classmethod
    def _loops_by_sel_mode_from_whole_mesh(cls, context, bm, uv_layer, only_uv_edges, per_face):
        return cls._loops_by_sel_mode(context, bm.faces, uv_layer, only_uv_edges, per_face)

    @classmethod
    def sel_loops_by_island(
        cls,
        context: bpy.types.Context,
        island: list,
        uv_layer: bmesh.types.BMLayerItem,
        only_uv_edges: bool = False,
        per_face: bool = False
    ) -> list:
        return cls._loops_by_sel_mode(context, island, uv_layer, only_uv_edges, per_face)

    @classmethod
    def _loops_by_sel_mode(cls, context, inp_faces, uv_layer, only_uv_edges, per_face):
        """ Return loops converted from selected elements """

        sync_uv = context.scene.tool_settings.use_uv_select_sync
        if context.space_data.type == 'IMAGE_EDITOR' and not sync_uv:
            mode = 'FACE' if per_face else context.scene.tool_settings.uv_select_mode
            if ZenPolls.version_greater_3_2_0:
                if only_uv_edges:
                    return list({loop for face in inp_faces for loop in face.loops if not face.hide and loop[uv_layer].select_edge})
                else:
                    if mode == 'VERTEX':
                        return list({loop for face in inp_faces for loop in face.loops if not face.hide and face.select and loop[uv_layer].select})
                    elif mode == 'EDGE':
                        loops = list({loop for face in inp_faces for loop in face.loops if not face.hide and face.select and loop[uv_layer].select and loop[uv_layer].select_edge})
                        loops.extend([lp.link_loop_next for lp in loops])
                        return loops
                    else:
                        if per_face:
                            return [face.loops for face in inp_faces if not face.hide and face.select and False not in [loop[uv_layer].select for loop in face.loops] and False not in [loop[uv_layer].select_edge for loop in face.loops]]
                        else:
                            return list({loop for face in inp_faces for loop in face.loops if not face.hide and face.select and loop[uv_layer].select and loop[uv_layer].select_edge})
            else:  # Blender Ver less than 3.2.0
                return list({loop for face in inp_faces for loop in face.loops if not face.hide and face.select and loop[uv_layer].select})

        else:
            mesh_select_mode = context.tool_settings.mesh_select_mode

            if mesh_select_mode[1] or mesh_select_mode[0]:
                # verts = list({v for f in inp_faces for v in f.verts})
                return [loop for vertex in [v for v in {v for f in inp_faces for v in f.verts} if v.select] for loop in vertex.link_loops]

            elif mesh_select_mode[2]:
                if per_face:
                    return [[loop for loop in face.loops] for face in [face for face in inp_faces if face.select and not face.hide]]
                else:
                    return [loop for face in [face for face in inp_faces if face.select and not face.hide] for loop in face.loops]

    @classmethod
    def compound_groups_from_loops(
        cls,
        loops: list,
        uv_layer: bmesh.types.BMLayerItem,
        _sorted: bool = True
    ) -> list:

        def sort_by_index(f):
            return f.index

        def update_storages(upd):
            cluster.update(upd)
            stack.update(upd)

        _groups = []
        loops = set(loops)

        while len(loops) != 0:
            init_loop = loops.pop()
            cluster = {init_loop}
            stack = {init_loop}
            while len(stack) != 0:
                loop = stack.pop()

                linked = [lp for lp in loop.vert.link_loops if lp in loops and lp not in cluster and lp[uv_layer].uv == loop[uv_layer].uv]
                update_storages(linked)
                linked.append(loop)

                adj = [lp.link_loop_next for lp in linked if lp.link_loop_next in loops and lp.link_loop_next not in cluster]
                adj.extend([lp.link_loop_prev for lp in linked if lp.link_loop_prev in loops and lp.link_loop_prev not in cluster])
                update_storages(adj)

            for lp in cluster:
                loops.discard(lp)
            _groups.append(list(cluster))

        if _sorted:
            return [sorted(cluster, key=sort_by_index) for cluster in _groups]

        return _groups


if __name__ == "__main__":
    pass
