"""
GSTools - Menu configuration (single source of truth)

This is the DATA that defines the GSTools menu and shelf. The menu builder and
the shelf both read from here, and every launch goes through gstools.launch(id),
so adding / moving / renaming a tool is a data edit in this file - no UI or
dispatch code needs to change.

Each tool item is a dict:
    id          stable, unique key (used by launch() and by the shelf)
    label       text shown in the menu
    icon        icon filename (resolved by Maya via XBMLANGPATH -> GSTools/icons)
    annotation  tooltip
    type        "python" | "mel" | "mel_source" | "special"  (see launcher.py)
      python:      module, function   (function may be omitted = run module body)
      mel:         command            (proc already on the script path)
      mel_source:  source, command    (source path is relative to the scripts root)
      special:     action             ("about" | "rebuild" | "version")

A category is: {"label", "icon", "items": [ <tool|divider>, ... ]}
A divider is:  {"divider": True, "label": <optional section label>}
"""

MENU = [
    {
        "label": "Help",
        "icon": "defaultOutliner.svg",
        "items": [
            {"id": "about", "label": "About", "icon": "help.png", "type": "special",
             "action": "about", "annotation": "Opens the GSTools about window."},
            {"id": "rebuild", "label": "Re-Build Menu", "icon": "refresh.png", "type": "special",
             "action": "rebuild", "annotation": "Rebuilds the GSTools menu (picks up new tools)."},
            {"id": "version", "label": "Version", "icon": "SP_FileDialogToParent_Disabled.png",
             "type": "special", "action": "version", "enabled": False,
             "annotation": "Installed GSTools version."},
        ],
    },
    {
        "label": "Tools",
        "icon": "toolSettings.png",
        "items": [
            {"id": "nitropoly", "label": "Nitropoly", "icon": "nitropoly.png",
             "type": "python", "module": "NitroPoly", "function": "main",
             "annotation": "Nitropoly modeling toolset."},
            {"id": "instance_tool", "label": "Instance Tool", "icon": "commandButton.png",
             "type": "mel_source", "source": "tools/modeling/instance_tool.mel",
             "command": "ObjReplaceTool;", "annotation": "Replace objects with instances of a base object."},
            {"id": "crease_tool", "label": "Crease Tool", "icon": "CP_Icons/sp_crease.png",
             "type": "mel_source", "source": "vendor/crease_plus/CreasePlus.mel",
             "annotation": "CreasePlus crease toolset."},
            {"id": "welder", "label": "Welder", "icon": "Welder_icons/Welder_Icon.png",
             "type": "python", "module": "welder", "function": "show",
             "annotation": "Welder create tool."},
            {"id": "remove_namespace", "label": "Remove NameSpace", "icon": "pythonFamily.png",
             "type": "python", "module": "remove_namespace", "function": "run",
             "annotation": "Remove all non-reference namespaces."},
            {"id": "material_manager", "label": "Material Manager", "icon": "ddoMM/icon_DP.png",
             "type": "mel_source", "source": "tools/material_manager/dp_MaterialManager.mel",
             "command": "materialManager;", "annotation": "Material Manager."},
            {"id": "cable_tool", "label": "Cable Tool", "icon": "Cable_script/Icons/Cable_2.0_icon.png",
             "type": "python", "module": "Cable_Create", "function": "main",
             "annotation": "Cable create tool."},
            {"id": "vertex_color_manager", "label": "Vertexcolor Manager", "icon": "ari/AriVertexColorEditor.png",
             "type": "mel_source", "source": "vendor/ari/AriVertexColorEditor.mel",
             "command": "AriVertexColorEditor;", "annotation": "Vertex color manager."},
            {"id": "uvset_manager", "label": "UVSet Manager", "icon": "ari/AriUVSetList.png",
             "type": "mel_source", "source": "vendor/ari/AriUVSetList.mel",
             "command": "AriUVSetList;", "annotation": "UV set manager."},
            {"id": "renamer", "label": "GS Renamer", "icon": "renamePreset.png",
             "type": "python", "module": "GS_renamer", "function": "build_gui_renamer",
             "annotation": "Rename multiple objects."},
            {"id": "outliner_sorter", "label": "Outliner Sorter", "icon": "outliner.png",
             "type": "python", "module": "GS_outliner_sorter", "function": "build_gui_outliner_sorter",
             "annotation": "Manage the order of elements in the outliner."},
            {"divider": True, "label": "Vertex Normal"},
            {"id": "smooth_normal", "label": "Smooth Normal", "icon": "ari/AriNormalSmooth.png",
             "type": "mel_source", "source": "vendor/ari/AriNormalSmooth.mel",
             "command": "AriNormalSmooth;", "annotation": "Vertex normal smooth."},
            {"id": "normal_tweakage", "label": "Normal Tweakage Tool", "icon": "commandButton.png",
             "type": "mel_source", "source": "tools/normals/GS_NormalTweakageTools_UI.mel",
             "command": "GS_NormalTweakageTools_UI;", "annotation": "Normal tweakage tool."},
            {"id": "normal_tool", "label": "Normal Tool", "icon": "add_chris.png",
             "type": "mel_source", "source": "tools/normal_tools/GS_NormalTools_UI.mel",
             "command": "GS_NormalTools_UI;", "annotation": "Simple normal tool."},
            {"id": "unlock_normal", "label": "Unlock Normal Tool", "icon": "add.png",
             "type": "python", "module": "unlock_normal", "function": "run",
             "annotation": "Unlock normals and keep smoothing groups."},
            {"divider": True},
            {"id": "path_manager", "label": "Path Manager", "icon": "annotation.png",
             "type": "python", "module": "GS_path_manager", "function": "launch",
             "annotation": "Manage and repair node file paths."},
            {"id": "transfer_transforms", "label": "Transfer Transforms", "icon": "transform.svg",
             "type": "python", "module": "GS_transfer_transforms", "function": "build_gui_transfer_transforms",
             "annotation": "Transfer translate/rotate/scale between objects."},
        ],
    },
    {
        "label": "Modeling",
        "icon": "mesh.svg",
        "items": [
            {"id": "flatten_combine", "label": "Flatten Combine", "icon": "commandButton.png",
             "type": "mel_source", "source": "tools/modeling/flattenCombine.mel",
             "command": "flattenCombine;", "annotation": "Combine objects without history."},
            {"id": "force_cleanup", "label": "Force CleanUp By Combine", "icon": "commandButton.png",
             "type": "mel_source", "source": "tools/modeling/forceCleanUpByCombine.mel",
             "command": "forceCleanUpByCombine;", "annotation": "Force cleanup via combine."},
            {"id": "extract_tool", "label": "Extract Tool", "icon": "commandButton.png",
             "type": "mel_source", "source": "tools/modeling/extract_tool.mel",
             "command": "Extract;", "annotation": "Extract / duplicate / clone faces."},
            {"divider": True},
            {"id": "select_every_n_edge", "label": "Select Every N-Edge in Loop/Ring",
             "icon": "NS_shortestPathTool.png", "type": "mel_source",
             "source": "tools/modeling/select_every_n_edge.mel",
             "annotation": "Select every N edges in a loop/ring."},
            {"id": "set_edge_length", "label": "Set Edge Length", "icon": "NinjaIcon_NinjaUV_EdgeMap.png",
             "type": "python", "module": "set_length_edge", "function": "Gui",
             "annotation": "Set edge length tool."},
            {"id": "snap_vertex", "label": "Snap Vertex", "icon": "snap_vertex.png",
             "type": "python", "module": "snap_vertex", "function": "run",
             "annotation": "Snap vertices to nearest / center."},
            {"id": "advance_snap_vertex", "label": "Advance Snap Vertex Tools", "icon": "NS_snapAtoB_old.png",
             "type": "mel_source", "source": "tools/modeling/gsSnapVertexTools.mel",
             "command": "gsSnapVertexTools;", "annotation": "Advanced snap vertex tools."},
            {"divider": True},
            {"id": "create_bbox", "label": "Create BBox", "icon": "ari/AriBoundingSizePrimitive.png",
             "type": "mel_source", "source": "vendor/ari/AriBoundingSizePrimitive.mel",
             "command": "AriBoundingSizePrimitive;", "annotation": "Create bounding-box-sized primitive."},
            {"id": "refreeze_transform", "label": "ReFreeze Transform Tool", "icon": "ari/AriReFreezeRotate.png",
             "type": "mel_source", "source": "vendor/ari/AriReFreezeRotate.mel",
             "command": "AriReFreezeRotate;", "annotation": "ReFreeze rotate tool."},
            {"id": "circle_tool", "label": "Circle Tool", "icon": "ari/AriCircleVertex.png",
             "type": "mel_source", "source": "vendor/ari/AriCircleVertex.mel",
             "command": "AriCircleVertex;", "annotation": "Make circle from vertices."},
            {"divider": True},
            {"id": "sphere_types", "label": "Sphere Types", "icon": "blinn.svg",
             "type": "python", "module": "GS_create_sphere_types", "function": "build_gui_sphere_type",
             "annotation": "Create other sphere types."},
        ],
    },
    {
        "label": "UVTools",
        "icon": "UVs_btn.png",
        "items": [
            {"id": "straighten_uv", "label": "Straighten UV", "icon": "straighten_uv.png",
             "type": "mel_source", "source": "vendor/ari/AriUVGridding.mel",
             "command": "AriUVGridding;", "annotation": "Straighten UVs."},
            {"id": "rizomuv_tool", "label": "RizomUV Tool", "icon": "unfold/rizomVS.png",
             "type": "python", "module": "RizomUV_tool", "function": "UI",
             "annotation": "Send mesh to RizomUV."},
            {"id": "transfer_uv", "label": "Transfer UV", "icon": "NS_copyUV.png",
             "type": "mel_source", "source": "tools/uv/Transfer_UV.mel",
             "command": "TransUVTool;", "annotation": "Transfer UV tool."},
        ],
    },
    {
        "label": "Baking Tools",
        "icon": "zoo_packageBrowser_32.png",
        "items": [
            {"id": "bake_match_name", "label": "Bake Match Name", "icon": "pythonFamily.png",
             "type": "python", "module": "cbNameMatch", "function": "cbMatchNames",
             "annotation": "Baking name match."},
            {"id": "auto_match_name", "label": "Auto Match Name", "icon": "pythonFamily.png",
             "type": "python", "module": "rename", "function": "show",
             "annotation": "Auto baking rename tool."},
            {"id": "baking_exporter", "label": "Baking Exporter", "icon": "zoo_importExport_32.png",
             "type": "mel_source", "source": "tools/baking/baking_exporter.mel",
             "command": "m341_tbExporter_launchWindow;", "annotation": "High/low FBX baking exporter."},
        ],
    },
    {
        "label": "Rigging",
        "icon": "kinReroot.png",
        "items": [
            {"id": "weight_tools", "label": "Weight Tools", "icon": "pythonFamily.png",
             "type": "python", "module": "kmjDuplicateCopyWeight", "function": "main",
             "annotation": "Weight tools."},
            {"id": "skin_save", "label": "Skin Save Tool", "icon": "pythonFamily.png",
             "type": "python", "module": "SkinSaverDeluxe", "function": "UI",
             "annotation": "Skin save tool."},
        ],
    },
    {
        "label": "Utilities",
        "icon": "bsd-head.png",
        "items": [
            {"id": "reload_file", "label": "Reload File", "icon": "openScript.png",
             "type": "python", "module": "gs_maya_utilities", "function": "force_reload_file",
             "annotation": "Force re-open the current file (changes ignored)."},
            {"divider": True},
            {"id": "switch_viewport_color", "label": "Switch Viewport Color", "icon": "magenta.png",
             "type": "python", "module": "switch_viewport_color", "function": "run",
             "annotation": "Toggle viewport background color."},
            {"id": "remove_mentalray", "label": "Remove MentalRay Plugin", "icon": "commandButton.png",
             "type": "mel_source", "source": "tools/utilities/remove_mentalray.mel",
             "annotation": "Remove mental ray nodes/plugin from the scene."},
            {"id": "auto_smoothing_groups", "label": "Auto Smoothing Groups", "icon": "commandButton.png",
             "type": "mel_source", "source": "tools/utilities/dp_autoSmoothingGroups.mel",
             "command": "dp_autoSG;", "annotation": "Automatic smoothing groups."},
        ],
    },
    {
        "label": "Pipeline",
        "icon": "zoo_importExport_32.png",
        "items": [
            {"id": "gn_import", "label": "GN Import", "icon": "pythonFamily.png",
             "type": "mel", "command": "GN_Import;", "annotation": "GN import."},
            {"id": "gn_export", "label": "GN Export", "icon": "pythonFamily.png",
             "type": "mel", "command": "GN_Export;", "annotation": "GN export."},
            {"id": "export_to_max", "label": "Export to 3dsMax", "icon": "pythonFamily.png",
             "type": "python", "module": "export_to_max", "function": "run",
             "annotation": "Export selected mesh to 3ds Max."},
            {"id": "bmc_send_mesh", "label": "Send Mesh (bmc)", "icon": "pythonFamily.png",
             "type": "python", "module": "bmc_menu", "function": "show",
             "annotation": "bmc send-mesh tool."},
            {"id": "fix_green_mesh", "label": "Fix Green/Lost Mesh", "icon": "pythonFamily.png",
             "type": "python", "module": "fix_green_mesh", "function": "run",
             "annotation": "Fix green/lost mesh for MA files."},
        ],
    },
    {
        "label": "Miscellaneous",
        "icon": "bin.png",
        "items": [
            {"id": "startup_faster", "label": "Startup Faster", "icon": "out_time.png",
             "type": "python", "module": "GS_faster_startup", "function": "build_gui_startup_booster",
             "annotation": "Manage which plugins load at startup."},
            {"id": "close_maya_fast", "label": "Close Maya Faster", "icon": "none.png",
             "type": "mel_source", "source": "tools/utilities/close_maya_fast.mel",
             "annotation": "Faster Maya shutdown."},
            {"id": "recreate_hotkey", "label": "Re-Create Hotkey Setting", "icon": "zoo_hotkeys_32.png",
             "type": "mel_source", "source": "tools/utilities/recreate_hotkey.mel",
             "annotation": "Re-create and assign the GSTools hotkey set."},
        ],
    },
]

# Ordered tool ids shown on the GSTools shelf. Shares ids (and therefore the
# launch + telemetry path) with the menu above. None entries are separators.
SHELF = [
    "flatten_combine", "instance_tool", "force_cleanup", "extract_tool", "remove_namespace",
    None,
    "straighten_uv", "transfer_uv", "rizomuv_tool",
    None,
    "bake_match_name", "auto_match_name", "baking_exporter",
    None,
    "crease_tool", "welder", "material_manager", "cable_tool", "sphere_types",
    None,
    "select_every_n_edge", "set_edge_length", "snap_vertex", "advance_snap_vertex",
    None,
    "create_bbox", "refreeze_transform", "circle_tool", "vertex_color_manager", "uvset_manager",
    "renamer", "smooth_normal", "normal_tweakage", "normal_tool", "unlock_normal",
    None,
    "switch_viewport_color", "remove_mentalray", "auto_smoothing_groups",
    "outliner_sorter", "path_manager", "transfer_transforms",
    None,
    "gn_import", "gn_export", "export_to_max", "bmc_send_mesh", "fix_green_mesh",
    None,
    "startup_faster", "recreate_hotkey", "close_maya_fast",
]


# --- lookup -----------------------------------------------------------------
_INDEX = None


def _build_index():
    index = {}
    for category in MENU:
        for item in category.get("items", []):
            if item.get("divider"):
                continue
            tid = item.get("id")
            if tid in index:
                raise ValueError("GSTools menu_config: duplicate tool id '%s'" % tid)
            index[tid] = item
    return index


def get_tool(tool_id):
    """Return the tool dict for `tool_id`, or None."""
    global _INDEX
    if _INDEX is None:
        _INDEX = _build_index()
    return _INDEX.get(tool_id)


def all_tool_ids():
    """Return the set of every tool id defined in the menu."""
    global _INDEX
    if _INDEX is None:
        _INDEX = _build_index()
    return set(_INDEX.keys())
