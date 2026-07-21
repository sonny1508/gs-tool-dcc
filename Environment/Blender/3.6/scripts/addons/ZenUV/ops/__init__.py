# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright 2023, Valeriy Yatsenko

import bpy

from bpy.utils import register_class, unregister_class
from bpy.props import IntProperty
from ZenUV.utils.blender_zen_utils import ZenPolls

from .operators import operators_classes
from .finishing import finishing_classes
from .mark import makr_sys_classes
from .world_orient import w_orient_classes
from .texel import td_classes
from .quadrify import ZUV_OT_Quadrify
from .distribute import uv_distribute_classes
from .pt_uv_texture_advanced import adv_uv_texture_classes
from .seam_groups import seam_groups_classes, ZSGListGroup
from .texel_presets import TDPR_classes, TDPRListGroup
from .pack import pack_classes
from .relax import relax_classes
from .select import select_classes
from .select import poll_3_2_select_classes
from .reshape.ops import uv_reshape_classes
from .context_utils import context_utils_classes
from .pack_exclusion import register_pack_exclusion, unregister_pack_exclusion
from .transform_sys.tr_register import register_transform_sys, unregister_transform_sys

# Zen Unwrap Compound
from .zen_unwrap.ops import ZenUnwrapClasses
from .zen_unwrap.ui import ZenUV_MT_ZenUnwrap_Popup, ZenUV_MT_ZenUnwrap_ConfirmPopup
from .unwrap_constraint import register_uwrp_constraint, unregister_uwrp_constraint

from .trimsheets.trimsheet import register as register_trimsheets
from .trimsheets.trimsheet import unregister as unregister_trimsheets

from .trimsheets.trimsheet_transform import register as register_trim_transform
from .trimsheets.trimsheet_transform import unregister as unregister_trim_transform
from .transform_sys.trim_batch_operators.system import register_trim_batch_ops, unregister_trim_batch_ops

from .stitch import register as register_stitch
from .stitch import unregister as unregister_stitch

from .zen_unwrap.unwrap_for_tool import register as register_unwrap_for_tool
from .zen_unwrap.unwrap_for_tool import unregister as unregister_unwrap_for_tool

from .zen_unwrap.unwrap_processor import register as register_uwrp_processor
from .zen_unwrap.unwrap_processor import unregister as unregister_uwrp_processor

from ZenUV.ops.event_service import ZUV_OT_EventService, ZUV_OT_EventGet


unwrap_ui_classes = (
    ZenUV_MT_ZenUnwrap_Popup, ZenUV_MT_ZenUnwrap_ConfirmPopup
)


def register():
    """Registering Operators"""
    for cl in operators_classes:
        register_class(cl)

    register_trimsheets()

    # Quadrify
    register_class(ZUV_OT_Quadrify)

    # Zen Unwrap Registration
    for cl in ZenUnwrapClasses:
        register_class(cl)

    for cl in unwrap_ui_classes:
        register_class(cl)

    # Zen Transform Registration
    register_transform_sys()

    # Zen Distribute Registration
    for cl in uv_distribute_classes:
        register_class(cl)

    # Reshape Island Registration
    for cl in uv_reshape_classes:
        register_class(cl)

    # Advanced UV Texture Registration
    for cl in adv_uv_texture_classes:
        register_class(cl)

    # Zen Seam Groups Registration
    for cl in seam_groups_classes:
        register_class(cl)

    # Texel Density Registration
    for cl in td_classes:
        register_class(cl)

    # Texel Density Presets Registration
    for cl in TDPR_classes:
        register_class(cl)
    register_class(TDPRListGroup)

    # Pack Registration
    for cl in pack_classes:
        register_class(cl)

    # World Orient Registration
    for cl in w_orient_classes:
        register_class(cl)

    # Relax Registration
    for cl in relax_classes:
        register_class(cl)

    # Finishing Sys
    for cl in finishing_classes:
        register_class(cl)

    # Mark Sys
    for cl in makr_sys_classes:
        register_class(cl)

    for cl in context_utils_classes:
        register_class(cl)

    # Select Registration ----------------
    if ZenPolls.version_greater_3_2_0:
        for cl in poll_3_2_select_classes:
            register_class(cl)

    for cl in select_classes:
        register_class(cl)
    # Select Registration END ------------

    register_pack_exclusion()
    register_uwrp_constraint()

    # Smooth Groups
    bpy.types.Object.zen_sg_list = bpy.props.CollectionProperty(type=ZSGListGroup)
    bpy.types.Object.zsg_list_index = IntProperty(name="Index for zen_sg_list", default=0)

    # Texel Density Presets
    bpy.types.Scene.zen_tdpr_list = bpy.props.CollectionProperty(type=TDPRListGroup)
    bpy.types.Scene.zen_tdpr_list_index = IntProperty(name="Index for zen_tdpr_list", default=0)

    register_trim_transform()

    register_stitch()
    register_trim_batch_ops()

    register_unwrap_for_tool()

    register_uwrp_processor()

    # Special class for detecting event procedures
    bpy.utils.register_class(ZUV_OT_EventService)
    bpy.utils.register_class(ZUV_OT_EventGet)


def unregister():
    """Unregistering Operators"""

    bpy.utils.unregister_class(ZUV_OT_EventService)
    bpy.utils.unregister_class(ZUV_OT_EventGet)

    for cl in operators_classes:
        unregister_class(cl)

    # Quadrify
    unregister_class(ZUV_OT_Quadrify)

    # Zen Unwrap Registration
    for cl in ZenUnwrapClasses:
        unregister_class(cl)

    for cl in unwrap_ui_classes:
        unregister_class(cl)

    # Zen Transform
    unregister_transform_sys()

    # Zen Distribute
    for cl in uv_distribute_classes:
        unregister_class(cl)

    # Reshape Island
    for cl in uv_reshape_classes:
        unregister_class(cl)

    # Advanced UV Texture
    for cl in adv_uv_texture_classes:
        unregister_class(cl)

    # Zen Seam Groups
    for cl in seam_groups_classes:
        unregister_class(cl)

    # Texel Density
    for cl in td_classes:
        unregister_class(cl)

    # Texel Density Presets
    for cl in TDPR_classes:
        unregister_class(cl)
    unregister_class(TDPRListGroup)

    # Pack Unregister
    for cl in pack_classes:
        unregister_class(cl)

    # World Orient Unregister
    for cl in w_orient_classes:
        unregister_class(cl)

    # Relax Unregister
    for cl in relax_classes:
        unregister_class(cl)

    # Finishing Sys
    for cl in finishing_classes:
        unregister_class(cl)

    # Mark Sys
    for cl in makr_sys_classes:
        unregister_class(cl)

    for cl in reversed(context_utils_classes):
        unregister_class(cl)

    # Select Unregister ------------------
    if ZenPolls.version_greater_3_2_0:
        for cl in poll_3_2_select_classes:
            unregister_class(cl)

    for cl in select_classes:
        unregister_class(cl)
    # Select Unregister END --------------

    unregister_trimsheets()

    unregister_pack_exclusion()
    unregister_uwrp_constraint()

    unregister_trim_transform()

    unregister_stitch()
    unregister_trim_batch_ops()

    unregister_unwrap_for_tool()

    unregister_uwrp_processor()


if __name__ == "__main__":
    pass
