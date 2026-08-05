"""
gs_property_transfer - source -> target property transfer for Maya 2022+.

Pick one source object, select any number of targets, and push a property from
the source onto them. The picked source is stored per scene by a message
connection, so it survives renaming and reparenting.

Sections available so far:
    Pivot - move the selected objects' pivots onto the source object, matching
            translate / rotate / scale as ticked, optionally freezing the
            targets' transforms first.

Adding a section means one TransferSection subclass in ui.py plus its worker in
core.py; the picked source, status line and error guard are already shared.

    from gs_property_transfer import ui
    ui.show()

Inside GSTools the tool is launched through gstools.launch('gs_property_transfer'),
which resolves to show() below.
"""

import importlib

from . import core   # noqa: F401
from . import ui     # noqa: F401

__version__ = "0.1.0"


def show():
    """Entry point used by gstools.launch('gs_property_transfer').

    The GSTools launcher reloads this package (its __init__) on every launch,
    but reloading a package does not re-execute its submodules, so reload core
    and ui here to pick up edits during development. core has no dependency on
    ui, so reload it first; reloading ui then re-binds its `core` reference to
    the freshly reloaded module.
    """
    importlib.reload(core)
    importlib.reload(ui)
    return ui.show()
