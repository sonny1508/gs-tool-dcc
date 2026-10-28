"""'Review' category for GS Pipeline.

Checks an asset before it moves on. Each group module exposes a ``GROUP``
descriptor::

    {"id", "label", "tabs": [{"label", "draw"}, ...]}
"""
from __future__ import annotations

from . import asset_validation

# Ordered list of group modules within the Review category.
MODULES = (asset_validation,)

CATEGORY = {
    "id": "REVIEW",
    "label": "Review",
    "groups": [m.GROUP for m in MODULES],
}


def register():
    for module in MODULES:
        module.register()


def unregister():
    for module in reversed(MODULES):
        module.unregister()
