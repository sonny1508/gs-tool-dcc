bl_info = {
    "name": "GS Pipeline",
    "author": "Glenda Studio",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > GS Pipeline",
    "description": "Glenda Studio production pipeline tools, organized by category > group > tab.",
    "category": "3D View",
}

import bpy

from . import common  # noqa: F401  (shared helpers, imported by tool modules)
from . import projects
from . import file_io

print("Initializing GS Pipeline")

# Ordered top-level categories. Each exposes a CATEGORY descriptor:
#   {"id", "label", "groups": [{"id", "label", "tabs": [{"label","draw"}, ...]}, ...]}
CATEGORY_MODULES = (projects, file_io)
CATEGORIES = [m.CATEGORY for m in CATEGORY_MODULES]


# ----------------------------------------------------------------------------
# Descriptor lookup helpers
# ----------------------------------------------------------------------------
def _get_category(cat_id):
    return next((c for c in CATEGORIES if c["id"] == cat_id), CATEGORIES[0] if CATEGORIES else None)


def _get_group(category, group_id):
    groups = category["groups"]
    return next((g for g in groups if g["id"] == group_id), groups[0] if groups else None)


def _get_tab(group, tab_value):
    tabs = group["tabs"]
    return next(
        (t for t in tabs if t["label"].upper() == tab_value),
        tabs[0] if tabs else None,
    )


# ----------------------------------------------------------------------------
# Dynamic EnumProperty item callbacks (category > group > sub-tab)
# ----------------------------------------------------------------------------
def _category_items(self, context):
    return [(c["id"], c["label"], f"{c['label']} tools") for c in CATEGORIES]


def _group_items(self, context):
    category = _get_category(getattr(context.window_manager, "gs_category", ""))
    if not category or not category["groups"]:
        return [("NONE", "None", "")]
    return [(g["id"], g["label"], g["label"]) for g in category["groups"]]


def _subtab_items(self, context):
    wm = context.window_manager
    category = _get_category(getattr(wm, "gs_category", ""))
    if not category:
        return [("NONE", "None", "")]
    group = _get_group(category, getattr(wm, "gs_group", ""))
    if not group or not group["tabs"]:
        return [("NONE", "None", "")]
    return [(t["label"].upper(), t["label"], t["label"]) for t in group["tabs"]]


def _register_wm_props():
    bpy.types.WindowManager.gs_category = bpy.props.EnumProperty(
        name="Category",
        description="Active GS Pipeline category",
        items=_category_items,
    )
    bpy.types.WindowManager.gs_group = bpy.props.EnumProperty(
        name="Group",
        description="Active group within the category",
        items=_group_items,
    )
    bpy.types.WindowManager.gs_subtab = bpy.props.EnumProperty(
        name="Tab",
        description="Active tool tab within the group",
        items=_subtab_items,
    )


def _unregister_wm_props():
    for attr in ("gs_category", "gs_group", "gs_subtab"):
        if hasattr(bpy.types.WindowManager, attr):
            delattr(bpy.types.WindowManager, attr)


# ----------------------------------------------------------------------------
# Main panel: category bar > group bar > sub-tab bar > active tool UI
# ----------------------------------------------------------------------------
class GS_PT_Pipeline(bpy.types.Panel):
    bl_label = "GS Pipeline"
    bl_idname = "GS_PT_Pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GS Pipeline"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        # --- Level 1: category bar ---
        if len(CATEGORIES) > 1:
            layout.prop(wm, "gs_category", expand=True)
        category = _get_category(wm.gs_category)
        if category is None:
            return

        # --- Level 2: group bar (only when the category has >1 group) ---
        if len(category["groups"]) > 1:
            layout.prop(wm, "gs_group", expand=True)
        group = _get_group(category, wm.gs_group)
        if group is None:
            return

        # --- Level 3: sub-tab bar (only when the group has >1 tab) ---
        if len(group["tabs"]) > 1:
            layout.prop(wm, "gs_subtab", expand=True)
        tab = _get_tab(group, getattr(wm, "gs_subtab", ""))
        if tab is None:
            return

        # --- Content ---
        box = layout.box()
        tab["draw"](box, context)


def register():
    print("Registering GS Pipeline")
    for module in CATEGORY_MODULES:
        module.register()
    _register_wm_props()
    bpy.utils.register_class(GS_PT_Pipeline)
    print("GS Pipeline registered")


def unregister():
    print("Unregistering GS Pipeline")
    bpy.utils.unregister_class(GS_PT_Pipeline)
    _unregister_wm_props()
    for module in reversed(CATEGORY_MODULES):
        module.unregister()
    print("GS Pipeline unregistered")


if __name__ == "__main__":
    register()
