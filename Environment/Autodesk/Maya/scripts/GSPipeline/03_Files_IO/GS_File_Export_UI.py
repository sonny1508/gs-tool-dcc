import pymel.core as pm
import maya.cmds as cmds
import os
import sys

# GSPipeline launches tools by exec'ing scripts, so _core is not on sys.path.
# Put it there once, the same way 02_Normals reaches gs_normal_core.
_CORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_core')
if _CORE not in sys.path:
    sys.path.append(_CORE)

import gs_fbx  # noqa: E402  (must follow the sys.path setup)

# The FBX preset this tool exports with. gs_fbx resets the plug-in before
# applying it, so settings left behind by another tool can no longer leak in.
FBX_PRESET = 'asset'


def batchExportFBX(*args):
    """Export objects as FBX files based on selection mode"""
    # Clear the operation field
    pm.textScrollList("operationField", e=True, ra=True)
    
    # Get the export folder from the text field
    export_folder = pm.textField("exportDirField", q=True, text=True)
    
    # Check if the export folder exists
    if not export_folder or not os.path.isdir(export_folder):
        pm.textScrollList("operationField", e=True, a="Invalid export directory. Please select a valid folder.")
        return
    
    # Determine if we're exporting all or selection based on the radio button
    export_all = pm.radioButton("everythingRadio", q=True, select=True)
    
    # Get objects to export
    if export_all:
        # Get all mesh objects in the scene
        pm.textScrollList("operationField", e=True, a="Exporting all mesh objects in the scene...")
        selected_paths = cmds.ls(type="transform", long=True)
    else:
        # Get selected objects
        pm.textScrollList("operationField", e=True, a="Exporting selected mesh objects...")
        selected_paths = cmds.ls(selection=True, long=True)
        
    if not selected_paths:
        pm.textScrollList("operationField", e=True, a="No objects found to export.")
        return
    
    # Process groups to get all mesh objects (without inheriting names)
    mesh_objects = []
    for obj_path in selected_paths:
        # Check if the selected object is itself a mesh
        if cmds.objectType(obj_path, isType="transform"):
            shapes = cmds.listRelatives(obj_path, shapes=True, fullPath=True, type="mesh")
            if shapes:
                mesh_objects.append(obj_path)
        
        # Find all mesh children but keep their full paths
        children = cmds.listRelatives(obj_path, allDescendents=True, fullPath=True, type="transform") or []
        for child_path in children:
            shapes = cmds.listRelatives(child_path, shapes=True, fullPath=True, type="mesh")
            if shapes and child_path not in mesh_objects:
                mesh_objects.append(child_path)
    
    # Track groups for reporting
    group_objects = []
    for obj_path in selected_paths:
        if obj_path not in mesh_objects:
            children = cmds.listRelatives(obj_path, allDescendents=True, fullPath=True, type="transform") or []
            has_mesh_children = False
            for child_path in children:
                if child_path in mesh_objects:
                    has_mesh_children = True
                    break
            
            if has_mesh_children:
                # Get just the object name without the full path for reporting
                obj_name = obj_path.split('|')[-1]
                group_objects.append(obj_name)
    
    # Report processing information
    if group_objects:
        pm.textScrollList("operationField", e=True, a="The following groups will be processed for their children:")
        for obj in group_objects:
            pm.textScrollList("operationField", e=True, a="  - {}".format(obj))
    
    # Check if we have valid objects to export
    if not mesh_objects:
        pm.textScrollList("operationField", e=True, a="No valid geometry objects to export. Only mesh objects can be exported.")
        return
    
    # Check if "As Parent" mode is enabled
    as_parent = pm.checkBox("asParentCheck", q=True, value=True)
    
    if as_parent:
        if export_all:
            # All mode + As Parent: find top-level parents (roots) and export each with all descendants
            # Get all transforms that have mesh descendants but no parent with mesh descendants
            top_parents = []
            for obj_path in mesh_objects:
                # Walk up to find the top-most ancestor that contains meshes
                current = obj_path
                while True:
                    parent = cmds.listRelatives(current, parent=True, fullPath=True)
                    if not parent:
                        break
                    current = parent[0]
                if current not in top_parents:
                    top_parents.append(current)
            
            pm.textScrollList("operationField", e=True, a="Exporting {} top-level parents to: {}".format(len(top_parents), export_folder))
            
            for parent_path in top_parents:
                parent_name = parent_path.split('|')[-1]
                file_path = os.path.join(export_folder, "{}.fbx".format(parent_name))
                
                # Select the parent and all its descendants
                cmds.select(parent_path, hierarchy=True, replace=True)
                
                try:
                    gs_fbx.export_selection(file_path, preset=FBX_PRESET)
                    pm.textScrollList("operationField", e=True, a="Exported: {}.fbx".format(parent_name))
                except Exception as e:
                    pm.textScrollList("operationField", e=True, a="Error exporting {}: {}".format(parent_name, str(e)))
        else:
            # Selection mode + As Parent: selected objects ARE the parents, export each with children
            pm.textScrollList("operationField", e=True, a="Exporting {} selected parents to: {}".format(len(selected_paths), export_folder))
            
            for obj_path in selected_paths:
                obj_name = obj_path.split('|')[-1]
                file_path = os.path.join(export_folder, "{}.fbx".format(obj_name))
                
                # Select this object and all its descendants
                cmds.select(obj_path, hierarchy=True, replace=True)
                
                try:
                    gs_fbx.export_selection(file_path, preset=FBX_PRESET)
                    pm.textScrollList("operationField", e=True, a="Exported: {}.fbx".format(obj_name))
                except Exception as e:
                    pm.textScrollList("operationField", e=True, a="Error exporting {}: {}".format(obj_name, str(e)))
    else:
        pm.textScrollList("operationField", e=True, a="Exporting {} individual mesh objects to: {}".format(len(mesh_objects), export_folder))
        
        # Process each mesh object individually
        for obj_path in mesh_objects:
            obj_name = obj_path.split('|')[-1]
            file_path = os.path.join(export_folder, "{}.fbx".format(obj_name))
            
            cmds.select(obj_path, replace=True)
            
            try:
                gs_fbx.export_selection(file_path, preset=FBX_PRESET)
                pm.textScrollList("operationField", e=True, a="Exported: {}.fbx".format(obj_name))
            except Exception as e:
                pm.textScrollList("operationField", e=True, a="Error exporting {}: {}".format(obj_name, str(e)))
    
    # Restore original selection
    cmds.select(selected_paths)
    pm.textScrollList("operationField", e=True, a="Export complete.")
    
    # Final verification message
    pm.textScrollList("operationField", e=True, a="")
    pm.textScrollList("operationField", e=True, a="Export Settings Used:")
    pm.textScrollList("operationField", e=True, a="- FBX Version: 2020")
    pm.textScrollList("operationField", e=True, a="- Up Axis: Z")
    pm.textScrollList("operationField", e=True, a="- Units: Centimeters")
    pm.textScrollList("operationField", e=True, a="- Included: Smoothing Groups")
    pm.textScrollList("operationField", e=True, a="- Excluded: Animation, Cameras, Lights, Audio, Embedded Media")

def browseForExportDir(*args):
    """Open a file browser to select an export directory"""
    try:
        # Use fileMode=3 to ensure only directories are visible/selectable
        # Use dialogStyle=2 for directory browser (no files shown)
        export_folder = cmds.fileDialog2(
            fileMode=3,          # 3 = Directory selection only
            dialogStyle=2,       # 2 = Directory browser (hides files)
            caption="Select Export Folder",
            okCaption="Select",
            fileFilter="Folders (*)|" # This ensures only folders are shown in the browser
        )
    except:
        # Fallback if advanced options cause issues
        export_folder = cmds.fileDialog2(
            fileMode=3,          # Directory selection only
            fileFilter="Folders (*)|" # Filter to show only folders
        )
    
    if export_folder:
        pm.textField("exportDirField", e=True, text=export_folder[0])

def UI():
    """Create the GS File Exporter UI"""
    # Close existing window if it exists
    if cmds.window("gs_exporter_win", exists=True):
        cmds.deleteUI("gs_exporter_win", window=True)
    
    # Create main window with initial size, but resizable
    cmds.window("gs_exporter_win", title="GS File Exporter", width=720, height=480, sizeable=True)
    
    height = 20
        
    # Main layout
    mainLayout = pm.columnLayout(adjustableColumn=True)
    
    # Title section
    pm.separator(style="out", height=5)
    pm.text(label="GS File Exporter", font="boldLabelFont", align="center")
    pm.separator(style="in", height=10)
    
    # Export directory section
    pm.rowLayout(numberOfColumns=3, columnWidth3=(100, 400, 80), columnAlign=(1, 'right'),
                 columnAttach=[(1, 'both', 5), (2, 'both', 5), (3, 'both', 5)])
    pm.text(label="Export Directory:")
    pm.textField("exportDirField", placeholderText="Select or enter export directory", width=440)
    pm.button(label="Browse...", command=browseForExportDir, width=80)
    pm.setParent('..')  # Go back to main layout
    
    pm.separator(style="none", height=10)
    
    # Selection mode section
    pm.rowLayout(numberOfColumns=3, columnWidth3=(100, 180, 180), columnAlign=(1, 'right'),
                 columnAttach=[(1, 'both', 5), (2, 'both', 5), (3, 'both', 5)])
    pm.text(label="Export Mode:")
    pm.radioCollection()
    pm.radioButton("selectionRadio", label="Selection", select=True)
    pm.radioButton("everythingRadio", label="Everything")
    pm.setParent('..')  # Go back to main layout
    
    pm.separator(style="none", height=10)
    
    # As Parent option
    pm.rowLayout(numberOfColumns=2, columnWidth2=(100, 280), columnAlign=(1, 'right'),
                 columnAttach=[(1, 'both', 5), (2, 'both', 5)])
    pm.text(label="")
    pm.checkBox("asParentCheck", label="As Parent", value=False)
    pm.setParent('..')  # Go back to main layout
    
    # Export button
    pm.separator(style="none", height=10)
    pm.button(label="Batch FBX Export", height=height+10, command=batchExportFBX, backgroundColor=[0.3, 0.3, 0.3])
    
    pm.separator(style="in", height=10)
    
    # Operations output section
    pm.text(label="Operations:", align="left")
    pm.frameLayout(label="", borderVisible=False, labelVisible=False, backgroundColor=[0.3, 0.3, 0.3], marginWidth=0, marginHeight=0)
    pm.textScrollList("operationField", height=280)
    pm.setParent('..')
    
    # Show the window
    cmds.showWindow("gs_exporter_win")

if __name__ == "__main__":
    UI()