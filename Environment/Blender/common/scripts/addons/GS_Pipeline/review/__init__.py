"""'Review' category for GS Pipeline: checks an asset before it moves on."""
from __future__ import annotations

from ..panel import Category
from . import asset_validation

CATEGORY = Category("REVIEW", "Review", (asset_validation,))
