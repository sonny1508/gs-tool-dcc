"""HW3 project tools, under Projects > HW3 (Blender port of Maya's HW3_Tools.py).

    materials.py   Materials tab: material-instance / texture data onto materials
    modeling.py    Modeling tab: source-module FBX I/O, building-scene sync
    props.py       the lists and fields both tabs share, on the scene
    payloads.py    the pipeline folders and reading what's in them
"""
from __future__ import annotations

from ... import common
from ...panel import Group
from . import materials, modeling, props

# Tool modules in tab-bar order. Each has a TAB and register() / unregister().
TOOLS = (materials, modeling)

GROUP = Group("HW3", "HW3", tuple(tool.TAB for tool in TOOLS))


def register():
    props.register()
    common.register_modules(TOOLS)


def unregister():
    common.unregister_modules(TOOLS)
    props.unregister()
