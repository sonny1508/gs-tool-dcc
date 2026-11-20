"""GS File Transfer: whether this Blender can export 3ds Max smoothing groups.

The FBX exporter's 'SMOOTH_GROUP' mode builds the groups from sharp edges and
flat faces itself. A sharp edge only becomes a hard edge in Max where it closes
off a region; one that stops partway across a surface comes out soft, as it
does from a manual File > Export. The export is left exactly like the manual one:
an earlier version extended those open ends before exporting, and the lines it
guessed cut extra hard edges into the mesh.
"""
from __future__ import annotations

import bpy


# What fbx_supports_smoothing_groups() found; None until the exporter could be asked.
_supports_smoothing_groups = None


def fbx_supports_smoothing_groups():
    """True when this Blender's FBX exporter can write 3ds Max smoothing groups.

    The 'SMOOTH_GROUP' smoothing mode exists in 4.5 and 5.2 but not in 3.6, whose
    exporter only offers normals / face / edge smoothing. The tab asks on every
    redraw, so the answer is kept once the exporter has given one; while the FBX
    add-on isn't loaded it's False and asked again next time.
    """
    global _supports_smoothing_groups
    if _supports_smoothing_groups is None:
        try:
            prop = bpy.ops.export_scene.fbx.get_rna_type().properties["mesh_smooth_type"]
        except (AttributeError, KeyError, RuntimeError):
            return False
        _supports_smoothing_groups = "SMOOTH_GROUP" in prop.enum_items.keys()
    return _supports_smoothing_groups
