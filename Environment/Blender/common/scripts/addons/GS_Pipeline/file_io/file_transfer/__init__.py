"""GS File Transfer, under File I/O > GS File Transfer.

Moves FBX files between Blender, Maya and 3ds Max, either through this machine's
temp folder (Local) or through the studio share (Server). The tab is the import /
export settings side by side, then a Local section (the shared file and when it
was written, Import and Export) and a Server section (a user picker, the files
in both directions with when they were written, Import and Export). No section
asks for the other application: transfer files are plain FBX.

    config.py            file-name contract, folders, FBX settings
    transfer.py          FBX import / export, and the runners both sections share
    smoothing_groups.py  closing open sharp edges for 3ds Max smoothing groups
    server.py            whether the share is reachable, and the user list
    file_status.py       the file rows: what is waiting where, and since when
    ui.py                the tab: properties, operators, drawing
"""
from __future__ import annotations

from ...panel import Group, Tab
from . import file_status, server, ui

GROUP = Group("GS_FILE_TRANSFER", "GS File Transfer",
              (Tab("GS File Transfer", ui.draw_file_transfer),))


def register():
    ui.register()
    server.register()       # fills the user list ui registered


def unregister():
    file_status.unregister()
    server.unregister()
    ui.unregister()
