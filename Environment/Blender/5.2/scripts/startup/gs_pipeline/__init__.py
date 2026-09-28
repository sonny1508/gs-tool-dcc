"""Per-version shim for the GS pipeline startup.

Blender only auto-runs startup scripts from ``<version>/scripts/startup``, so
this thin file is the entry point. The real logic lives once under
``common/scripts/gs_pipeline_core`` — we just add that folder to ``sys.path``
and delegate. Do not put logic here; edit ``gs_pipeline_core`` instead.
"""

import os
import sys

# <...>/Blender/<version>/scripts/startup/gs_pipeline -> up 4 -> <...>/Blender,
# then into the shared common/scripts folder.
_COMMON = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "common", "scripts")
)
if _COMMON not in sys.path:
    sys.path.insert(0, _COMMON)

import gs_pipeline_core


def register():
    gs_pipeline_core.register()


def unregister():
    gs_pipeline_core.unregister()
