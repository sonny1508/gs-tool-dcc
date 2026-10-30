"""CM project tools (the client's Rev Match Racing cars), under Projects > CM.
One tab:

    vehicle.py      the tab: Scope, LOD and Custom Parts switching, Check Names,
                    and its Log (the add-on's object_log.ObjectLog)
    variants.py     which LOD / part version each object is; hiding the rest
    name_check.py   the Check Names rules
    names.py        the CM naming contract: LOD / part tokens, the essential names
"""
from __future__ import annotations

from ... import common
from ...panel import Group
from . import vehicle

# Tool modules in tab-bar order. Each has a TAB and register() / unregister().
TOOLS = (vehicle,)

GROUP = Group("CM", "CM", tuple(tool.TAB for tool in TOOLS))


def register():
    common.register_modules(TOOLS)


def unregister():
    common.unregister_modules(TOOLS)
