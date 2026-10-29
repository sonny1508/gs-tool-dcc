"""GS File Transfer, under File I/O > GS File Transfer.

Moves FBX files between Blender, Maya and 3ds Max, either through this machine's
temp folder (Local) or through the studio share (Server). The tab is the import /
export settings side by side, then a Local and a Server section, each with one
software picker and an Import and Export button.

    config.py            file-name contract, folders, applications, FBX settings
    transfer.py          FBX import / export, and the runners both sections share
    smoothing_groups.py  closing open sharp edges for 3ds Max smoothing groups
    server.py            whether the share is reachable, and the user list
    ui.py                the tab: properties, operators, drawing
"""
from __future__ import annotations

from ...panel import Group, Tab
from . import server, ui

GROUP = Group("GS_FILE_TRANSFER", "GS File Transfer",
              (Tab("GS File Transfer", ui.draw_file_transfer),))


def register():
    ui.register()
    server.register()       # fills the user list ui registered


def unregister():
    server.unregister()
    ui.unregister()
