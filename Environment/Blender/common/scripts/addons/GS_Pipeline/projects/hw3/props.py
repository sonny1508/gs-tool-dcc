"""HW3 data both tabs share: the Material, Texture and FBX lists and the UV
fields. It lives on the scene, so it is saved with the .blend file."""
from __future__ import annotations

import bpy
from bpy.props import CollectionProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup, UIList

from ... import common
from . import payloads


# Property group lives on the scene under this attribute.
PROP = "gs_hw3"


# ============================================================================
# Data model (UI lists need real CollectionProperty items)
# ============================================================================
class GS_HW3_ListItem(PropertyGroup):
    name: StringProperty()
    path: StringProperty()


# Guards against the two index ``update`` callbacks ping-ponging into each other
# when one clears the other (single-selection between the two lists).
_SELECTING = [False]


def _on_mat_json_index(self, context):
    """Pull UV scale/offset defaults from the newly selected material JSON."""
    if _SELECTING[0]:
        return
    _SELECTING[0] = True
    try:
        if self.json_mats_index >= 0:
            self.textures_index = -1
        idx = self.json_mats_index
        if not (0 <= idx < len(self.json_mats)):
            return
        data = payloads.load_json_material(self.json_mats[idx].path)
        if data is None:
            return
        uv = data.get("vectors", {}).get("UV - ScaleOffset") or {}
        self.uv_r = self.uv_default_r = uv.get("r", 1.0)
        self.uv_g = self.uv_default_g = uv.get("g", 1.0)
        self.uv_b = self.uv_default_b = uv.get("b", 0.0)
        self.uv_a = self.uv_default_a = uv.get("a", 0.0)
    finally:
        _SELECTING[0] = False


def _on_texture_index(self, context):
    if _SELECTING[0]:
        return
    _SELECTING[0] = True
    try:
        if self.textures_index >= 0:
            self.json_mats_index = -1
    finally:
        _SELECTING[0] = False


class GS_HW3_Props(PropertyGroup):
    # JSON material instances
    json_mats: CollectionProperty(type=GS_HW3_ListItem)
    json_mats_index: IntProperty(default=-1, update=_on_mat_json_index)
    # standalone textures
    textures: CollectionProperty(type=GS_HW3_ListItem)
    textures_index: IntProperty(default=-1, update=_on_texture_index)
    # source-module FBX files
    fbx_files: CollectionProperty(type=GS_HW3_ListItem)
    fbx_files_index: IntProperty(default=-1)

    # UV scale/offset fields (R,G,B,A) - same semantics as the Maya floatFields.
    uv_r: FloatProperty(name="R", default=1.0, precision=4, step=10)
    uv_g: FloatProperty(name="G", default=1.0, precision=4, step=10)
    uv_b: FloatProperty(name="B", default=0.0, precision=4, step=10)
    uv_a: FloatProperty(name="A", default=0.0, precision=4, step=10)

    # remembered defaults from the last selected material JSON (for Reset)
    uv_default_r: FloatProperty(default=1.0)
    uv_default_g: FloatProperty(default=1.0)
    uv_default_b: FloatProperty(default=0.0)
    uv_default_a: FloatProperty(default=0.0)


def _props(context) -> GS_HW3_Props:
    return getattr(context.scene, PROP)


def _fill_collection(coll, rows: list[dict]) -> None:
    coll.clear()
    for row in rows:
        item = coll.add()
        item.name = row.get("name", "???")
        item.path = row.get("path", "")


# ============================================================================
# UI Lists
# ============================================================================
class GS_UL_HW3_Simple(UIList):
    """Generic single-column name list."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_prop, index):
        layout.label(text=item.name)


CLASSES = (
    GS_HW3_ListItem,
    GS_HW3_Props,
    GS_UL_HW3_Simple,
)


def register():
    common.register_classes(CLASSES)
    setattr(bpy.types.Scene, PROP, PointerProperty(type=GS_HW3_Props))


def unregister():
    if hasattr(bpy.types.Scene, PROP):
        delattr(bpy.types.Scene, PROP)
    common.unregister_classes(CLASSES)
