import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as api
import maya.mel as mel
import os
import sys

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
    export_all = pm.radioButton("allRadio", q=True, select=True)
    
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
    
    pm.textScrollList("operationField", e=True, a="Exporting {} individual mesh objects to: {}".format(len(mesh_objects), export_folder))
    
    # Process each mesh object individually
    for obj_path in mesh_objects:
        # Get just the object name without the full path
        obj_name = obj_path.split('|')[-1]
        file_path = os.path.join(export_folder, "{}.fbx".format(obj_name))
        
        # Select only this object (not its hierarchy)
        cmds.select(obj_path, replace=True)
        
        # Reset export settings to default
        mel.eval('FBXResetExport')
        
        # Set FBX version to 2020
        mel.eval('FBXExportFileVersion "FBX202000"')
        
        # Set up axis to Z
        mel.eval('FBXExportUpAxis z')
        
        # Set units to Centimeters (not automatic)
        mel.eval('FBXExportScaleFactor 1.0')  # 1.0 for centimeters
        mel.eval('FBXExportConvertUnitString "cm"')
        
        # Include geometry settings
        mel.eval('FBXExportSmoothingGroups -v true')      # Smoothing Groups
        mel.eval('FBXExportSmoothMesh -v true')           # Smooth Mesh
        mel.eval('FBXExportTriangulate -v true')         # Triangulate
        
        # Disable other geometry settings
        mel.eval('FBXExportTangents -v false')            # Tangents and Binormals
        mel.eval('FBXExportInstances -v false')           # Preserve Instances
        mel.eval('FBXExportHardEdges -v false')           # Hard Edges
        mel.eval('FBXExportReferencedAssetsContent -v false')  # Referenced Assets Content
        
        # Disable animation, cameras, lights, etc.
        mel.eval('FBXExportBakeComplexAnimation -v false')  # Animation
        mel.eval('FBXExportCameras -v false')               # Cameras
        mel.eval('FBXExportLights -v false')                # Lights
        mel.eval('FBXExportAudio -v false')                 # Audio
        mel.eval('FBXExportEmbeddedTextures -v false')      # Embed Media
        
        # Additional settings to ensure clean export
        mel.eval('FBXExportConstraints -v false')
        mel.eval('FBXExportInputConnections -v false')
        
        # Export the FBX - using forward slashes and quotes
        try:
            # Convert path to use forward slashes for Maya's MEL
            file_path_mel = file_path.replace("\\", "/")
            
            # Export
            fbx_command = 'FBXExport -f "{}" -s'.format(file_path_mel)
            mel.eval(fbx_command)
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
    pm.textScrollList("operationField", e=True, a="- Included: Smoothing Groups, Smooth Mesh, Triangulate")
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
    pm.radioButton("allRadio", label="All Meshes")
    pm.setParent('..')  # Go back to main layout
    
    pm.separator(style="none", height=10)
    
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