import bpy

import math
from mathutils import Vector, Color, Matrix


class MathVisualizer:
    def __init__(self, context: bpy.types.Context, pencil_name: str = '') -> None:

        self.display_mode = '3DSPACE' if context.space_data.type == 'VIEW_3D' else '2DSPACE'

        self.pencil = None
        if pencil_name:
            self.pencil = bpy.data.grease_pencils.get(pencil_name, None)
        else:
            self.pencil = bpy.context.annotation_data
        if not self.pencil:
            bpy.ops.gpencil.annotation_add()
            self.pencil = bpy.data.grease_pencils[-1]
            if pencil_name:
                self.pencil.name = pencil_name

    def add_vector(self, group: str, frame_idx: int, co_start: Vector, co_end: Vector, color: Color = None):
        vec_start = co_start.copy()
        vec_start.resize_3d()
        vec_end = co_end.copy()
        vec_end.resize_3d()

        lines = self.pencil.layers.get(group, None)
        if lines is None:
            lines = self.pencil.layers.new(group)

        self.pencil.layers.active = lines

        p_vectors = None

        if color is not None:
            lines.color = color[:]

        for it_frame in lines.frames:
            if it_frame.frame_number == frame_idx:
                p_vectors = it_frame

        if p_vectors is None:
            p_vectors = lines.frames.new(frame_idx, active=True)

        p_vectors.clear()

        gp_stroke = p_vectors.strokes.new()
        gp_stroke.start_cap_mode = 'ROUND'
        gp_stroke.end_cap_mode = 'ROUND'
        gp_stroke.use_cyclic = False

        gp_stroke.display_mode = self.display_mode

        gp_stroke.points.add(2)

        gp_stroke.points[0].co = vec_start
        gp_stroke.points[-1].co = vec_end

        axis_raw = vec_end - vec_start  # type: Vector
        distance = axis_raw.length
        if distance == 0:
            return

        distance /= 10

        axis = axis_raw.normalized()  # type: Vector

        vec_arrow = Vector((0, distance, 0))

        vec_right = vec_arrow.copy()
        vec_right.rotate(Matrix.Rotation(math.radians(-135), 4, "Z"))

        vec_left = vec_arrow.copy()
        vec_left.rotate(Matrix.Rotation(math.radians(-225), 4, "Z"))

        mtxRotDir = axis.to_track_quat('Y', 'Z').to_matrix().to_4x4()

        vec_right = Matrix.Translation(vec_end) @ mtxRotDir @ vec_right
        vec_left = Matrix.Translation(vec_end) @ mtxRotDir @ vec_left

        gp_stroke_left = p_vectors.strokes.new()
        gp_stroke_left.start_cap_mode = 'ROUND'
        gp_stroke_left.end_cap_mode = 'ROUND'
        gp_stroke_left.use_cyclic = False

        gp_stroke_left.display_mode = self.display_mode

        gp_stroke_left.points.add(2)

        gp_stroke_left.points[0].co = vec_end
        gp_stroke_left.points[-1].co = vec_right

        gp_stroke_right = p_vectors.strokes.new()
        gp_stroke_right.start_cap_mode = 'ROUND'
        gp_stroke_right.end_cap_mode = 'ROUND'
        gp_stroke_right.use_cyclic = False

        gp_stroke_right.display_mode = self.display_mode

        gp_stroke_right.points.add(2)

        gp_stroke_right.points[0].co = vec_end
        gp_stroke_right.points[-1].co = vec_left
