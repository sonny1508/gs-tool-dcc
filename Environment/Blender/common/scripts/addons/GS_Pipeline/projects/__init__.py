"""'Projects' category for GS Pipeline.

One group per project; the panel shows a project bar once there is more than
one. Each project module exposes a ``PROJECT`` descriptor::

    {"id", "label", "tabs": [{"label", "draw"}, ...]}

To add a new project, drop a module in this package and append it to ``MODULES``.
"""
from __future__ import annotations

from . import hw3_tools
from . import mgp27_tools

# Ordered list of project modules. Order defines the project (group) order.
MODULES = (hw3_tools, mgp27_tools)

# Category descriptor consumed by the top-level GS Pipeline menu framework.
CATEGORY = {
    "id": "PROJECTS",
    "label": "Projects",
    "groups": [m.PROJECT for m in MODULES],
}


def register():
    for module in MODULES:
        module.register()


def unregister():
    for module in reversed(MODULES):
        module.unregister()
