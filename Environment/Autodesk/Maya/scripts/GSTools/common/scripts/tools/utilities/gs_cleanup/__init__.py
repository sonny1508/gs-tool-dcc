"""
gs_cleanup - scene clean-up panel for Maya 2022+.

One window, one section per kind of mess. Sections available so far:
    Materials - find materials that are copies of each other by name
                (materialA, materialA_001, materialA1 ...), pick the one to
                keep, and merge the rest into it: their objects are reassigned
                and the duplicates, their shading groups and their orphaned
                texture nodes are deleted.

Adding a section means one CleanupSection subclass in ui.py plus its worker in
core.py; the status line and error guard are already shared.

    from gs_cleanup import ui
    ui.show()

Inside GSTools the tool is launched through gstools.launch('gs_cleanup'), which
resolves to show() below.
"""

import importlib

from . import core   # noqa: F401
from . import ui     # noqa: F401

__version__ = "0.1.0"


def show():
    """Entry point used by gstools.launch('gs_cleanup').

    The GSTools launcher reloads this package (its __init__) on every launch,
    but reloading a package does not re-execute its submodules, so reload core
    and ui here to pick up edits during development. core has no dependency on
    ui, so reload it first; reloading ui then re-binds its `core` reference to
    the freshly reloaded module.
    """
    importlib.reload(core)
    importlib.reload(ui)
    return ui.show()
