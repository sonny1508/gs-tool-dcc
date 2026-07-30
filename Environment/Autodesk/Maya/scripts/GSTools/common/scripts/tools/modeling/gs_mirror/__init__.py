"""
gs_mirror - live mirror tool for Maya 2022+.

Mirrors a mesh across a plane defined by a user-picked pivot object, live and
welded, in a single merged mesh. Normals stay correct because the mirror itself
is done by the polyMirror node (which reverses winding internally) rather than
by a negative-determinant matrix.

    from gs_mirror import ui
    ui.show()

Inside GSTools the tool is launched through gstools.launch('gs_mirror'), which
resolves to show() below.
"""

import importlib

from . import core   # noqa: F401
from . import ui     # noqa: F401

__version__ = "0.1.0"


def show():
    """Entry point used by gstools.launch('gs_mirror').

    The GSTools launcher reloads this package (its __init__) on every launch,
    but reloading a package does not re-execute its submodules, so reload core
    and ui here to pick up edits during development. core has no dependency on
    ui, so reload it first; reloading ui then re-binds its `core` reference to
    the freshly reloaded module.
    """
    importlib.reload(core)
    importlib.reload(ui)
    return ui.show()
