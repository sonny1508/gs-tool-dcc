bl_info = {
    "name": "GS Pipeline",
    "author": "Glenda Studio",
    "version": (1, 4),
    "blender": (3, 6, 10),
    "location": "View3D > Sidebar > GS Pipeline",
    "description": "Glenda Studio production pipeline tools, organized by category > group > tab.",
    "category": "3D View",
}

# Layout (see panel.py for how the sidebar is put together):
#
#   panel.py        the sidebar panel; Category / Group / Tab descriptors
#   common.py       helpers every tool shares (scene, log, preferences, registration)
#   object_log.py   the Log with a list of objects that check-style tools share
#   file_io/        File I/O category: file_transfer/
#   review/         Review category: asset_validation/
#   projects/       Projects category: one package per project (cm/, hw3/, mgp27/)

from . import common, object_log, panel
from . import file_io, projects, review

# Category bar order.
CATEGORIES = (projects.CATEGORY, review.CATEGORY, file_io.CATEGORY)

# Category shown when the panel first appears. Only which one is active on
# startup; the bar keeps the order above.
DEFAULT_CATEGORY = "FILE_IO"


def register():
    object_log.register()
    for category in CATEGORIES:
        common.register_modules(category.modules)
    panel.register(CATEGORIES, DEFAULT_CATEGORY)
    print("GS Pipeline registered")


def unregister():
    panel.unregister()
    for category in reversed(CATEGORIES):
        common.unregister_modules(category.modules)
    object_log.unregister()
