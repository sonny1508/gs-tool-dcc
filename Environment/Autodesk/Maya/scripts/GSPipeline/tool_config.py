# -*- coding: utf-8 -*-
"""
GSPipeline tool configuration.

Defines exactly which tools appear in the GSPipeline menu/shelf, their order,
their display names, and their icons. Nothing is inferred from filenames - if a
script is not listed here, it is not loaded.

Structure
---------
TOOLS is a list of entries. Each entry is one of:

  * A GROUP - a (label, children) tuple. It becomes a submenu. Children is
    itself a list of entries, so groups can nest to any depth:

        GSPipeline > 05 Projects > HW3 > HW3 Tools

  * A TOOL - a dict:

        {
            "name":   "HW3 Tools",                              # menu/shelf label
            "script": "05_Projects/HW3/HW3_Tools.py",    # relative to this folder
            "icon":   "HW3_Tools_Icon.png",                     # optional; in Icons/, omit for default
        }

Both name and icon are explicit. Icons live in the Icons/ folder next to this
file; a tool with no "icon" (or a missing icon file) uses Maya's default.
"""

TOOLS = [
    ("01 Modeling", [
        {"name": "Edge Sensei",     "script": "Modeling/Edge_Sensei_UI.py",                  "icon": "Edge_Sensei_Icon.png"},
        {"name": "Vertex Painter",  "script": "Modeling/Vertex_Painter_UI.py"},
        {"name": "Speed Workflow",  "script": "Modeling/Speed_Workflow/Speed_Workflow_UI.py"},
    ]),

    ("02 Normals", [
        {"name": "GS Normal Tools", "script": "Normals/GS_Normal_Tools_UI.py", "icon": "GS_Normal_Tools_Icon.png"},
    ]),

    ("03 UV", [
        {"name": "Texel Density Visualizer",   "script": "UV/texel-density-visualizer/texel-density-visualizer.py",   "icon": "texel-density-visualzier-icon.png"},
        {"name": "UV Shell Scaler",            "script": "UV/uv-shell-scaler/uv-shell-scaler.py"},
    ]),

    ("04 Files I/O", [
        {"name": "GS File Export",   "script": "Files_IO/gs_file_export.py",   "icon": "GS_File_Export_Icon.png"},
        {"name": "GS File Transfer", "script": "Files_IO/gs_file_transfer.py", "icon": "GS_File_Transfer_Icon.png"},
    ]),

    ("05 Review", [
        {"name": "LOD Checker",   "script": "Review/LOD_Checker/LOD_Checker_UI.py",     "icon": "LOD_Checker_Icon.png"},
        {"name": "Model Checker", "script": "Review/Model_Checker/Model_Checker_UI.py", "icon": "Model_Checker_Icon.png"},
    ]),

    ("06 Projects", [
        ("HW3", [
            {"name": "HW3 Tools",            "script": "Projects/HW3/HW3_Tools.py", "icon": "HW3.png"},
            {"name": "HW3 Asset Validation", "script": "Projects/HW3/HW3_Asset_Validation_UI.py", "icon": "HW3.png"},
        ]),
        ("MGP25", [
            {"name": "MGP25 Asset Checker",         "script": "Projects/MGP25/Mgp25_Asset_Checker_UI.py",          "icon": "Mgp25_Asset_Checker_Icon.png"},
            {"name": "MGP25 Custom Parts Rigger",   "script": "Projects/MGP25/Mgp25_Custom_Parts_Rigger_UI.py",    "icon": "Mgp25_Custom_Parts_Rigger_Icon.png"},
            {"name": "MGP25 Ultimate Bike Riggator","script": "Projects/MGP25/Mgp25_Ultimate_Bike_Riggator_UI.py", "icon": "Mgp25_Ultimate_Bike_Riggator_Icon.png"},
        ]),
        ("MGP26", [
            {"name": "MGP26 Asset Checker",          "script": "Projects/MGP26/Mgp26_Asset_Checker_UI.py"},
            {"name": "MGP26 Ultimate Bike Riggator", "script": "Projects/MGP26/Mgp26_Ultimate_Bike_Riggator_UI.py"},
        ]),
        ("R6", [
            {"name": "R6 Asset Validation", "script": "Projects/R6/R6_Asset_Validation_UI.py", "icon": "R6_Asset_Validation_Icon.png"},
        ]),
        ("SCR1", [
            {"name": "SCR1 Asset Validation", "script": "Projects/SCR1/Scr1_Asset_Validation_UI.py", "icon": "Scr1_Asset_Validation_Icon.png"},
        ]),
        ("GSW", [
            {"name": "GSW Vehicle Tools",        "script": "Projects/GSW/gsw_vehicle_tools/launch.py"},
            {"name": "Rename Building Textures", "script": "Projects/GSW/rename_building_textures.py"},
        ]),
    ]),
]
