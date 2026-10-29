"""The GS Pipeline sidebar panel, and the descriptors tools use to appear in it.

    Category   File I/O, Review, Projects        a package under GS_Pipeline
      Group    GS File Transfer, HW3, MGP27...   a tool or project (a module or package)
        Tab    Materials, Modeling...            one screen of it: a draw function

The panel is a category bar, a group bar and a tab bar over the active tab; a
bar shows only when it has more than one entry. Only the active tab's draw
function runs on a redraw, so a tool costs nothing while it isn't on screen.

To add a tool: give its module (or package) a GROUP and register() /
unregister(), then add it to its category's Category(...) in that package's
__init__.py.
"""
from __future__ import annotations

from collections import namedtuple

import bpy

# One screen of a tool: its label in the tab bar, and draw(layout, context).
Tab = namedtuple("Tab", "label draw")

# A tool or project, with its tabs in bar order.
Group = namedtuple("Group", "id label tabs")


class Category:
    """A top-level category. ``modules`` are its tools / projects in bar order,
    each with a GROUP and register() / unregister()."""

    def __init__(self, ident, label, modules):
        self.id = ident
        self.label = label
        self.modules = tuple(modules)
        self.groups = tuple(module.GROUP for module in self.modules)


# ----------------------------------------------------------------------------
# Bars: one enum per level on the window manager (runtime, never saved)
# ----------------------------------------------------------------------------
# Built once in register() and kept here: Blender doesn't copy the strings an
# enum items callback returns, so a list made fresh on every call can be freed
# while the UI still shows it.
_categories = {}        # id -> Category, in bar order
_category_items = []
_group_items = {}       # category id -> items
_tab_items = {}         # (category id, group id) -> items
_NO_ITEMS = [("NONE", "None", "")]


def _tab_id(tab):
    return tab.label.upper()


def _active_group(wm):
    """(category, group) the bars point at, falling back to the first of each.

    Reads gs_category and gs_group, never gs_subtab: reading a dynamic enum runs
    its items callback, so _tab_enum_items (which calls this) reading gs_subtab
    would call itself without end.
    """
    category = _categories.get(wm.gs_category) or next(iter(_categories.values()))
    groups = category.groups
    group = next((g for g in groups if g.id == wm.gs_group), groups[0] if groups else None)
    return category, group


def _active(wm):
    """(category, group, tab) the bars point at. Never call it from an items callback."""
    category, group = _active_group(wm)
    if group is None:
        return category, None, None
    tab = next((t for t in group.tabs if _tab_id(t) == wm.gs_subtab),
               group.tabs[0] if group.tabs else None)
    return category, group, tab


def _group_enum_items(wm, context):
    return _group_items.get(wm.gs_category, _NO_ITEMS)


def _tab_enum_items(wm, context):
    category, group = _active_group(wm)
    if group is None:
        return _NO_ITEMS
    return _tab_items[(category.id, group.id)]


# ----------------------------------------------------------------------------
# Panel
# ----------------------------------------------------------------------------
# Blender has no API for a minimum sidebar width (Region.width is read-only in
# 3.6 - 5.2), so tabs lay themselves out for the width they get instead; see
# common.is_wide().
class GS_PT_Pipeline(bpy.types.Panel):
    bl_label = "GS Pipeline"
    bl_idname = "GS_PT_Pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GS Pipeline"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        category, group, tab = _active(wm)
        if len(_categories) > 1:
            layout.prop(wm, "gs_category", expand=True)
        if len(category.groups) > 1:
            layout.prop(wm, "gs_group", expand=True)
        if group is None:
            return
        if len(group.tabs) > 1:
            layout.prop(wm, "gs_subtab", expand=True)
        if tab is not None:
            tab.draw(layout.box(), context)


# ----------------------------------------------------------------------------
# Registration (by the addon's __init__.py, after the tools)
# ----------------------------------------------------------------------------
def register(categories, default_category):
    _categories.clear()
    _categories.update((category.id, category) for category in categories)
    _category_items[:] = [(c.id, c.label, c.label + " tools") for c in categories]
    _group_items.clear()
    _tab_items.clear()
    for category in categories:
        _group_items[category.id] = [(g.id, g.label, g.label) for g in category.groups] or _NO_ITEMS
        for group in category.groups:
            _tab_items[(category.id, group.id)] = (
                [(_tab_id(t), t.label, t.label) for t in group.tabs] or _NO_ITEMS)

    wm = bpy.types.WindowManager
    wm.gs_category = bpy.props.EnumProperty(
        name="Category",
        description="Active GS Pipeline category",
        items=_category_items,
        default=default_category if default_category in _categories else _category_items[0][0],
    )
    wm.gs_group = bpy.props.EnumProperty(
        name="Group", description="Active group within the category", items=_group_enum_items)
    wm.gs_subtab = bpy.props.EnumProperty(
        name="Tab", description="Active tool tab within the group", items=_tab_enum_items)
    bpy.utils.register_class(GS_PT_Pipeline)


def unregister():
    bpy.utils.unregister_class(GS_PT_Pipeline)
    for attr in ("gs_category", "gs_group", "gs_subtab"):
        if hasattr(bpy.types.WindowManager, attr):
            delattr(bpy.types.WindowManager, attr)
