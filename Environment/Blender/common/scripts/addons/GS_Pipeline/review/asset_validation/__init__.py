"""Asset Validation, in the GS Pipeline 'Review' category.

Checks and quick fixes for an asset before it moves on, merged from the old
standalone GS_Asset_Validation addon. One module per section of the tab:

    geometry, normals, symmetry, uv, cleanup

Each section module has TITLE, ICON and TOOLS, a list of _shared.Tool. This
module turns every Tool into an operator (gs_pipeline.av_<name>) and draws the
sections. To add a check, write its function in the right section and add a
Tool for it; nothing here changes.

Checks select what they find and enter Edit Mode to show it; a clean result
goes back to Object Mode. Results go to the log at the bottom of the tab.
"""
from __future__ import annotations

import traceback

import bpy
from bpy.types import Operator

from ... import common
from . import cleanup, geometry, normals, symmetry, uv
from ._shared import ValidationError

SECTIONS = (geometry, normals, symmetry, uv, cleanup)

LOG = common.ToolLog("Select the meshes to check, then pick a check.")

# Wide enough (px at 1x) for the longest button labels to sit in two columns.
_TWO_COLUMN_WIDTH = 400


def _idname(tool):
    return "gs_pipeline.av_" + tool.name


class _ToolOperator:
    """Runs one Tool, with its result in the log. Made into an operator per Tool by _make_operator."""
    bl_options = {'UNDO'}

    def execute(self, context):
        LOG.clear()
        try:
            with common.wait_cursor(context):
                level, message = self.run(context)
        except ValidationError as exc:
            LOG.add(str(exc), "error", self)
            return {'CANCELLED'}
        except Exception as exc:        # keep the panel alive, keep the traceback
            traceback.print_exc()
            LOG.add("Something went wrong: {}. Details in the System Console.".format(exc),
                    "error", self)
            return {'CANCELLED'}
        LOG.add(message, level, self)
        return {'FINISHED'}


def _make_operator(tool):
    return type(
        "GS_OT_AV_" + tool.name,
        (_ToolOperator, Operator),
        {
            "bl_idname": _idname(tool),
            "bl_label": tool.label,
            "bl_description": tool.description,
            "run": staticmethod(tool.run),
        },
    )


CLASSES = tuple(_make_operator(tool) for section in SECTIONS for tool in section.TOOLS)


# ---------------------------------------------------------------------------
# Draw (called by the GS Pipeline menu framework under Review > Asset Validation)
# ---------------------------------------------------------------------------
def draw_asset_validation(layout, context):
    columns = 2 if common.is_wide(context, _TWO_COLUMN_WIDTH) else 1
    for section in SECTIONS:
        box = layout.box()
        box.label(text=section.TITLE, icon=section.ICON)
        grid = box.grid_flow(row_major=True, columns=columns, even_columns=True, align=True)
        for tool in section.TOOLS:
            grid.operator(_idname(tool), text=tool.label)
    LOG.draw(layout, context)


# ---------------------------------------------------------------------------
# Group descriptor (consumed by review/__init__.py)
# ---------------------------------------------------------------------------
GROUP = {
    "id": "ASSET_VALIDATION",
    "label": "Asset Validation",
    "tabs": [
        {"label": "Asset Validation", "draw": draw_asset_validation},
    ],
}


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
