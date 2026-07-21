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

import bmesh
import numpy as np
from math import radians
from mathutils import Vector, Matrix
from .tr_utils import TrConstants
from ZenUV.utils.bounding_box import BoundingBox2d
from ZenUV.utils.transform import UvTransformUtils


class TransformLoops:

    @classmethod
    def mute_axis(self, _offset: Vector, direction: str, opposite: bool = False) -> Vector:
        ''' In this case, opposite_direction is used to introduce a correction
            in cases where we have an alignment by cen_v or cen_h.
            Mathematically, with cen_v alignment, we get horizontally aligned islands.
            This is not what the user expects.
        '''
        if opposite:
            direction = TrConstants.opposite_direction[direction]
        return _offset * TrConstants.mute_axis[direction]

    @classmethod
    def _collect_uvs(
        cls,
        loops: list,
        uv_layer: bmesh.types.BMLayerItem,
    ):
        return [lp[uv_layer].uv for lp in loops]

    @classmethod
    def _set_uvs(
        cls,
        uv_layer: bmesh.types.BMLayerItem,
        loops: list,
        uvs: list
    ):
        for lp, uv in zip(loops, uvs):
            lp[uv_layer].uv = uv

    @classmethod
    def move_loops(
        cls,
        loops: list,
        uv_layer: bmesh.types.BMLayerItem,
        delta: Vector = Vector((0.0, 0.0))
    ) -> None:

        if delta.magnitude == 0:
            return
        uvs = np.array(cls._collect_uvs(loops, uv_layer)).reshape((-1, 2)) + delta
        cls._set_uvs(uv_layer, loops, uvs)

    @classmethod
    def scale_loops(
        cls,
        loops: list,
        uv_layer,
        scale: Vector = Vector((0.0, 0.0)),
        pivot: Vector = Vector((0.0, 0.0))
    ) -> None:

        if scale.x == 1.0 and scale.y == 1.0:
            return

        S = Matrix.Diagonal(scale)
        uvs = np.dot(np.array(cls._collect_uvs(loops, uv_layer)).reshape((-1, 2)) - pivot, S) + pivot
        cls._set_uvs(uv_layer, loops, uvs)

    @classmethod
    def rotate_loops(
        cls,
        loops: list,
        uv_layer,
        angle: float,
        pivot: Vector = Vector((0.0, 0.0)),
        image_aspect: float = 1.0,
        angle_in_radians: bool = False
    ) -> None:
        # image_aspect - aspect ratio
        # image_aspect = image.y / image.x

        if angle == 0:
            return

        if not angle_in_radians:
            angle = np.radians(angle)

        R = cls._get_rotation_matrix(angle, image_aspect)
        uvs = np.dot(np.array(cls._collect_uvs(loops, uv_layer)).reshape((-1, 2)) - pivot, R) + pivot

        cls._set_uvs(uv_layer, loops, uvs)

    @classmethod
    def _get_rotation_matrix(cls, angle, aspect=1):

        return Matrix(
            (
                (np.cos(angle), np.sin(angle) / aspect),
                (-aspect * np.sin(angle), np.cos(angle)),
            )
        )

    @classmethod
    def get_current_axis(cls, axis_name: str, i_bbox: BoundingBox2d, fit_bbox: BoundingBox2d):
        return {
            'V': 'V',
            'U': 'U',
            'MIN': i_bbox.get_shortest_axis_name(),
            'MAX': i_bbox.get_longest_axis_name(),
            'AUTO': cls.get_optimal_axis_name(i_bbox, fit_bbox),
            'MAX_FIT': fit_bbox.get_longest_axis_name(),
            'MIN_FIT': fit_bbox.get_shortest_axis_name()
        }[axis_name]

    @classmethod
    def get_optimal_axis_name(cls, i_bbox, fit_bbox) -> str:  # 'U', 'V'

        i_factor = i_bbox.aspect
        fit_factor = fit_bbox.aspect

        if i_factor < 1:
            if fit_factor >= i_factor:
                return i_bbox.get_longest_axis_name()
            else:
                return i_bbox.get_shortest_axis_name()
        elif i_factor == 1:
            return fit_bbox.get_shortest_axis_name()
        else:
            if fit_factor >= i_factor:
                return i_bbox.get_shortest_axis_name()
            else:
                return i_bbox.get_longest_axis_name()

    @classmethod
    def fit_loops(
        cls,
        loops: list,
        uv_layer: bmesh.types.BMLayerItem,
        fit_bbox: BoundingBox2d,
        fit_axis_name: str = 'AUTO',
        single_axis: bool = False,
        keep_proportion: bool = True,
        align_to: str = 'cen',
        padding: float = 0.0,
        angle: radians = 0.0,
        image_aspect: float = 1.0,
        move: bool = True,
        rotate: bool = True,
        scale: bool = True,
        flip: bool = False
    ) -> Vector:
        """
        :param loops: [bmesh.types.BMLoop, ...]
        :param uv_layer: bmesh.types.BMLayerItem
        :param fit_bbox: BoundingBox2d. Fit region Bounding box
        :param fit_axis_name: {'U', 'V', 'MIN', 'MAX', 'AUTO'}
        :param single_axis: bool
        :param keep_proportion: Bool
        :param align_to: {"tl","tc","tr","lc","cen","rc","bl","bc","br"}
        :param padding: float. Padding value from Fit region bbox
        :param angle: radians Island rotation
        :param image_aspect: float Current image aspect for rotate correction.
        :param move: is moving allowed?
        :param rotate: is rotation allowed?
        :param scale: is scaling allowed?
        :param flip: is flipping allowed?

        :return: flip pivot
        :rtype: Vector
        """

        if not len(loops):
            return Vector()

        uvs = cls._collect_uvs(loops, uv_layer)

        R = cls._get_rotation_matrix(angle, image_aspect)

        i_bbox = BoundingBox2d(points=uvs, uv_layer=uv_layer)
        fit_bbox_pivot = fit_bbox.get_as_dict()[align_to]
        i_bbox.rotate_by_matrix(R, fit_bbox_pivot)

        fit_axis_name = cls.get_current_axis(fit_axis_name, i_bbox, fit_bbox)

        scale_vec = UvTransformUtils._get_scale_vec(
            fit_axis_name,
            single_axis,
            keep_proportion,
            i_bbox,
            fit_bbox,
            padding=padding + BoundingBox2d.transform_safe_zone
        ) if scale else Vector((1.0, 1.0))
        scale_vec = scale_vec * TrConstants.flip_vector[align_to] if flip else scale_vec
        S = Matrix.Diagonal(scale_vec)

        RS = R @ S if rotate else S

        if flip is True:
            scale_vec *= TrConstants.flip_vector[align_to]
            align_to = TrConstants.opposite_direction[align_to]

        i_pivot = (i_bbox.get_as_dict()[align_to] - fit_bbox_pivot) @ S + fit_bbox_pivot

        if not move:
            fit_bbox_pivot = i_pivot

        uvs = (np.dot(np.array(uvs).reshape((-1, 2)) - fit_bbox_pivot, RS) + fit_bbox_pivot) + fit_bbox_pivot - i_pivot

        cls._set_uvs(uv_layer, loops, uvs)

        return fit_bbox_pivot

    @classmethod
    def transform_loops(
        cls,
        loops: list,
        uv_layer: bmesh.types.BMLayerItem,
        fit_bbox: BoundingBox2d,
        fit_axis_name: str = 'AUTO',
        single_axis: bool = False,
        keep_proportion: bool = True,
        align_to: str = 'cen',
        padding: float = 0.0,
        angle: radians = 0.0,
        image_aspect: float = 1.0,
        move: bool = True,
        rotate: bool = True,
        scale: bool = True,
        flip: bool = False
    ) -> None:
        """
        :param loops: [bmesh.types.BMLoop, ...]
        :param uv_layer: bmesh.types.BMLayerItem
        :param fit_bbox: BoundingBox2d. Fit region Bounding box
        :param fit_axis_name: {'U', 'V', 'MIN', 'MAX', 'AUTO'}
        :param single_axis: bool
        :param keep_proportion: Bool
        :param align_to: {"tl","tc","tr","lc","cen","rc","bl","bc","br"}
        :param padding: float. Padding value from Fit region bbox
        :param angle: radians Island rotation
        :param image_aspect: float Current image aspect for rotate correction.
        :param move: is moving allowed?
        :param rotate: is rotation allowed?
        :param scale: is scaling allowed?
        :param flip: is flipping allowed?
        """

        if not len(loops):
            return

        uvs = cls._collect_uvs(loops, uv_layer)

        R = cls._get_rotation_matrix(angle, image_aspect)

        i_bbox = BoundingBox2d(points=uvs, uv_layer=uv_layer)
        fit_bbox_pivot = fit_bbox.get_as_dict()[align_to] if move else i_bbox.get_as_dict()[align_to]
        if rotate or angle != 0:
            i_bbox.rotate_by_matrix(R, fit_bbox_pivot)

        fit_axis_name = cls.get_current_axis(fit_axis_name, i_bbox, fit_bbox)

        scale_vec = UvTransformUtils._get_scale_vec(
            fit_axis_name,
            single_axis,
            keep_proportion,
            i_bbox,
            fit_bbox,
            padding=padding
        ) if scale else Vector((1.0, 1.0))

        scale_vec = scale_vec * TrConstants.flip_vector[align_to] if flip else scale_vec
        S = Matrix.Diagonal(scale_vec)

        RS = R @ S if rotate else S

        if flip is True:
            scale_vec *= TrConstants.flip_vector[align_to]
            align_to = TrConstants.opposite_direction[align_to]

        i_pivot = (i_bbox.get_as_dict()[align_to] - fit_bbox_pivot) @ S + fit_bbox_pivot

        if not move:
            fit_bbox_pivot = i_pivot

        uvs = (np.dot(np.array(uvs).reshape((-1, 2)) - fit_bbox_pivot, RS) + fit_bbox_pivot) + fit_bbox_pivot - i_pivot

        cls._set_uvs(uv_layer, loops, uvs)
