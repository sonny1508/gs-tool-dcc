"""'Review' category for GS Pipeline: checks an asset before it moves on.

    asset_validation/   checks and quick fixes, with a Log of the objects found
    lod_check.py        show one LOD at a time (LOD0-6, numbered or lettered)
"""
from __future__ import annotations

from ..panel import Category
from . import asset_validation, lod_check

CATEGORY = Category("REVIEW", "Review", (asset_validation, lod_check))
