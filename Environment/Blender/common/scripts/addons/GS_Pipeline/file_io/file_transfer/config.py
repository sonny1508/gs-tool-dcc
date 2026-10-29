"""GS File Transfer settings: the file-name contract, the folders, the
applications and the FBX import / export settings.

File names are a contract with the Maya and 3ds Max sides of GS File Transfer
(``<source>_to_<target>.fbx`` and the per-object / per-user variants built in
transfer.py and ui.py). Change them in all three tools or not at all.
"""
from __future__ import annotations

import getpass
import os
import tempfile


# ===== GLOBAL FBX SETTINGS CONFIGURATION =====
username = getpass.getuser()
temp_dir = tempfile.gettempdir()

LOCAL_DIR = os.path.join(temp_dir, "fileTransferFbx")
LOCAL_DIR_INDIVIDUAL = os.path.join(temp_dir, "fileTransferFbxIndividual")
SERVER_DIR = r"\\192.168.1.210\Temp\File_Transfer"
# Combined into one user list. Same format: a header row with a 'User' column.
USER_CSVS = (
    r"\\192.168.1.210\Pipeline\Library\Data\Data_Computer_Update.csv",
    r"\\192.168.1.210\Pipeline\Library\Data\Data_Computer_Manual.csv",
)

# (token used in transfer file names, label shown in the panel). The tokens are
# shared with the Maya and 3ds Max tools -- don't rename them.
APPS = (
    ("maya", "Maya"),
    ("max", "3ds Max"),
    ("blender", "Blender"),
)
APP_LABELS = dict(APPS)
APP_ITEMS = [(token, label, "") for token, label in APPS]
THIS_APP = "blender"


class FBXSettings:
    """Centralized FBX import/export settings configuration.

    IMPORT and EXPORT keys are passed straight through to the FBX operators, so
    every key must be a real parameter of bpy.ops.import_scene.fbx /
    bpy.ops.export_scene.fbx.
    """

    IMPORT = {
        'use_custom_normals': True,
        'use_image_search': True,
        'use_alpha_decals': False,
        'decal_offset': 0.0,
        'use_anim': True,
        'anim_offset': 1.0,
        'use_subsurf': False,
        'use_custom_props': True,
        'use_custom_props_enum_as_string': True,
        'ignore_leaf_bones': False,
        'force_connect_children': False,
        'automatic_bone_orientation': False,
        'primary_bone_axis': 'Y',
        'secondary_bone_axis': 'X',
    }

    EXPORT = {
        'use_selection': True,
        'use_active_collection': False,
        'apply_unit_scale': True,
        'apply_scale_options': 'FBX_SCALE_ALL',
        'use_space_transform': True,
        'bake_space_transform': False,
        'object_types': {'MESH', 'EMPTY'},  # empties carry the hierarchy; narrowed to meshes by Mesh Only
        'use_mesh_modifiers': True,
        'use_mesh_modifiers_render': True,
        'mesh_smooth_type': 'OFF',  # switched to 'SMOOTH_GROUP' for 3ds Max when enabled
        'use_subsurf': False,
        'use_mesh_edges': False,
        'use_tspace': False,
        'use_custom_props': False,
        'add_leaf_bones': True,
        'primary_bone_axis': 'Y',
        'secondary_bone_axis': 'X',
        'use_armature_deform_only': False,
        'armature_nodetype': 'NULL',
        'bake_anim': False,
        'bake_anim_use_all_bones': True,
        'bake_anim_use_nla_strips': True,
        'bake_anim_use_all_actions': True,
        'bake_anim_force_startend_keying': True,
        'bake_anim_step': 1.0,
        'bake_anim_simplify_factor': 1.0,
        'path_mode': 'AUTO',
        'embed_textures': False,
        'batch_mode': 'OFF',
        'use_batch_own_dir': True,
        'use_metadata': True,
    }

    SCALE = {
        'use_auto_scale': True,
        'manual_import_scale': 1.0,
        'manual_export_scale': 1.0,
    }

    TRANSFORM = {
        'apply_transform_on_import': True,
        'apply_transform_on_export': True,
    }


# ---------------------------------------------------------------------------
# File names
# ---------------------------------------------------------------------------
def transfer_stem(source_app, target_app):
    """'<source>_to_<target>', the core of every transfer file name."""
    return f"{source_app}_to_{target_app}"


def safe_file_name(name):
    cleaned = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return cleaned or "object"
