"""MGP27 project tools, under Projects > MGP27. One module per tab:

    kerb_checker.py   Kerb Height Checker tab (measuring in kerb_measure.py)
"""
from __future__ import annotations

from ... import common
from ...panel import Group
from . import kerb_checker

# Tool modules in tab-bar order. Each has a TAB and register() / unregister().
TOOLS = (kerb_checker,)

GROUP = Group("MGP27", "MGP27", tuple(tool.TAB for tool in TOOLS))


def register():
    common.register_modules(TOOLS)


def unregister():
    common.unregister_modules(TOOLS)
