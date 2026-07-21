"""'File I/O' category for GS Pipeline.

Holds shared file-transfer tooling. Each group module exposes a ``GROUP``
descriptor::

    {"id", "label", "tabs": [{"label", "draw"}, ...]}
"""
from __future__ import annotations

from . import gs_file_transfer

# Ordered list of group modules within the File I/O category.
MODULES = (gs_file_transfer,)

CATEGORY = {
    "id": "FILE_IO",
    "label": "File I/O",
    "groups": [m.GROUP for m in MODULES],
}


def register():
    for module in MODULES:
        module.register()


def unregister():
    for module in reversed(MODULES):
        module.unregister()
