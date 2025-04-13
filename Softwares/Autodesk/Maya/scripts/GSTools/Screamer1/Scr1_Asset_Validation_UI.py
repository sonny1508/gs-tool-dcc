def printResult(*args):
    """Print results to file"""
    pm.select(cl=True)
    # Use Maya's standard file dialog but with txt default
    resultFilePath = pm.fileDialog(m=1, dm="*.txt", t="Choose where to save the result file")
    
    if resultFilePath:
        # Ensure the file has .txt extension
        if not resultFilePath.lower().endswith('.txt'):
            resultFilePath += '.txt'
            
        try:
            if os.path.isfile(resultFilePath):      
                os.chmod(resultFilePath, S_IWUSR|S_IREAD)                       
            with open(resultFilePath, "w") as resultFile:
                resultList = pm.textScrollList("resultField", q=True, ai=True)
                if resultList:
                    for line in resultList:
                        resultFile.write(f"{line}\r\n")
            pm.textScrollList("resultField", e=True, a=f"Results saved to: {resultFilePath}")
        except Exception as e:
            pm.textScrollList("resultField", e=True, a=f"Error saving results: {str(e)}")
import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as api
import maya.mel as mel
import os
import sys
from stat import S_IWUSR, S_IREAD


class PieceInfo:  # Use Python 3 class syntax
    def __init__(self, name, materialList):
        self.name = name
        self.materialList = materialList


def check(*args):
    """Check selected objects for proper naming and setup"""
    pm.textScrollList("resultField", e=True, ra=True)
    
    # Get selected objects using longnames to prevent name inheritance issues
    selected_paths = cmds.ls(selection=True, long=True)
    if not selected_paths:
        pm.textScrollList("resultField", e=True, a="No objects selected. Please select objects to check.")
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
    
    pm.textScrollList("resultField", e=True, a=f"Checking {len(mesh_objects)} mesh objects...")
    
    # 1) CHECK: All mesh must start with SM_
    pm.textScrollList("resultField", e=True, a="--- 1. CHECKING MESH NAMING (SM_) ---")
    has_naming_issues = False
    
    for obj_path in mesh_objects:
        # Get just the object name without the full path
        obj_name = obj_path.split('|')[-1]
        
        if not obj_name.startswith("SM_"):
            pm.textScrollList("resultField", e=True, a=f"{obj_name} does not start with SM_")
            has_naming_issues = True
    
    if not mesh_objects:
        pm.textScrollList("resultField", e=True, a="No mesh objects found in selection.")
    elif not has_naming_issues:
        pm.textScrollList("resultField", e=True, a="All mesh objects follow the naming convention.")
    
    # Add separator between checks
    pm.textScrollList("resultField", e=True, a="")
    pm.textScrollList("resultField", e=True, a="=================================================")
    pm.textScrollList("resultField", e=True, a="")
    
    # 2) CHECK: All materials must start with MI_
    pm.textScrollList("resultField", e=True, a="--- 2. CHECKING MATERIAL NAMING (MI_) ---")
    has_material_issues = False
    
    for obj_path in mesh_objects:
        # Get just the object name without the full path
        obj_name = obj_path.split('|')[-1]
        
        # Get the shapes
        shapes = cmds.listRelatives(obj_path, shapes=True, fullPath=True, type="mesh") or []
        
        for shape in shapes:
            # Get shading engines (material assignments)
            shading_engines = cmds.listConnections(shape, type="shadingEngine") or []
            
            for se in shading_engines:
                try:
                    # Get the material connected to this shading engine
                    materials = cmds.listConnections(se + ".surfaceShader") or []
                    
                    if not materials:
                        continue
                    
                    material = materials[0]
                    material_name = material
                    
                    # Special handling for lambert and standardsurface materials
                    if material_name.lower().startswith("lambert") or material_name.lower().startswith("standardsurface"):
                        pm.textScrollList("resultField", e=True, a=f"{obj_name} has wrongly assigned material: {material_name}")
                        has_material_issues = True
                    # Check if material starts with MI_
                    elif not material_name.startswith("MI_"):
                        pm.textScrollList("resultField", e=True, a=f"{material_name} does not start with MI_ ({obj_name})")
                        has_material_issues = True
                except Exception as e:
                    pm.textScrollList("resultField", e=True, a=f"Error checking material on {obj_name}: {str(e)}")
                    has_material_issues = True
    
    if not has_material_issues and mesh_objects:
        pm.textScrollList("resultField", e=True, a="All materials follow the naming convention.")
    
    # Add separator between checks
    pm.textScrollList("resultField", e=True, a="")
    pm.textScrollList("resultField", e=True, a="=================================================")
    pm.textScrollList("resultField", e=True, a="")
    
    # 3) CHECK: UV channel names must be UV0 or UV1 and must have UV shells
    pm.textScrollList("resultField", e=True, a="--- 3. CHECKING UV CHANNEL NAMES AND UV SHELLS ---")
    has_uv_issues = False
    
    for obj_path in mesh_objects:
        # Get just the object name without the full path
        obj_name = obj_path.split('|')[-1]
        
        # Get the shapes
        shapes = cmds.listRelatives(obj_path, shapes=True, fullPath=True, type="mesh") or []
        
        for shape in shapes:
            # Check UV channel names
            try:
                uv_sets = cmds.polyUVSet(shape, query=True, allUVSets=True) or []
                
                if not uv_sets:
                    pm.textScrollList("resultField", e=True, a=f"{obj_name} has no UV sets")
                    has_uv_issues = True
                    continue
                
                for uv_set in uv_sets:
                    if uv_set != "UV0" and uv_set != "UV1":
                        pm.textScrollList("resultField", e=True, a=f"{obj_name} has wrong UV channel name: {uv_set}")
                        has_uv_issues = True
                    
                    # Check if UV shells exist
                    try:
                        # Get the current UV set
                        cmds.polyUVSet(shape, currentUVSet=True, uvSet=uv_set)
                        
                        # Get the UV shell count
                        shell_count = cmds.polyEvaluate(shape, uvShell=True)
                        
                        if shell_count == 0:
                            pm.textScrollList("resultField", e=True, a=f"{obj_name} has no UV shells in channel: {uv_set}")
                            has_uv_issues = True
                    except Exception as e:
                        pm.textScrollList("resultField", e=True, a=f"Error checking UV shells for {obj_name}: {str(e)}")
                        has_uv_issues = True
            except Exception as e:
                pm.textScrollList("resultField", e=True, a=f"Error checking UVs on {obj_name}: {str(e)}")
                has_uv_issues = True
    
    if not has_uv_issues and mesh_objects:
        pm.textScrollList("resultField", e=True, a="All UV channels follow the naming convention and have proper UV shells.")
    
    # Add separator for completion
    pm.textScrollList("resultField", e=True, a="")
    pm.textScrollList("resultField", e=True, a="=================================================")
    pm.textScrollList("resultField", e=True, a="")
    
    # 4) CHECK COMPLETE
    pm.textScrollList("resultField", e=True, a="--- 4. CHECK COMPLETE ---")
    
    # Summary
    pm.textScrollList("resultField", e=True, a="")
    pm.textScrollList("resultField", e=True, a=f"Checked {len(mesh_objects)} mesh objects.")
    if not has_naming_issues and not has_material_issues and not has_uv_issues and mesh_objects:
        pm.textScrollList("resultField", e=True, a="No issues found! All assets follow the required conventions.")


def exportSelectionAsFBX(*args):
    """Export selected objects as FBX files"""
    # First, make sure user has saved their file
    pm.textScrollList("resultField", e=True, ra=True)
    pm.textScrollList("resultField", e=True, a="Please save your Maya file before exporting...")
    
    # Use centered dialog (appears on main screen)
    try:
        # Try to position the dialog in the center of Maya's main window
        result = cmds.confirmDialog(
            title='Save File',
            message='Please save your Maya file before exporting.\nClick OK when ready to continue.',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel',
            icon='warning'
        )
    except:
        # Fallback if positioning fails
        result = cmds.confirmDialog(
            title='Save File',
            message='Please save your Maya file before exporting.\nClick OK when ready to continue.',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel'
        )
    
    if result != 'OK':
        pm.textScrollList("resultField", e=True, a="Export canceled.")
        return
    
    # Get export folder - use directory browser that only shows folders
    try:
        # Use fileMode=3 to ensure only directories are visible/selectable
        # Use dialogStyle=2 for directory browser (no files shown)
        # Set fileFilter to only show folders by using "Folders (*)" as a filter
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
    
    if not export_folder:
        pm.textScrollList("resultField", e=True, a="Export canceled - no folder selected.")
        return
    
    export_folder = export_folder[0]  # Get the first path
    
    # Get selected objects using longnames (using same approach as the check function)
    selected_paths = cmds.ls(selection=True, long=True)
    if not selected_paths:
        pm.textScrollList("resultField", e=True, a="No objects selected for export.")
        return
    
    # Process groups to get all mesh objects (using same approach as the check function)
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
        pm.textScrollList("resultField", e=True, a="The following groups will be processed for their children:")
        for obj in group_objects:
            pm.textScrollList("resultField", e=True, a=f"  - {obj}")
    
    # Check if we have valid objects to export
    if not mesh_objects:
        pm.textScrollList("resultField", e=True, a="No valid geometry objects to export. Only mesh objects can be exported.")
        return
    
    pm.textScrollList("resultField", e=True, a=f"Exporting {len(mesh_objects)} individual mesh objects to: {export_folder}")
    
    # Process each mesh object individually
    for obj_path in mesh_objects:
        # Get just the object name without the full path
        obj_name = obj_path.split('|')[-1]
        file_path = os.path.join(export_folder, f"{obj_name}.fbx")
        
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
            fbx_command = f'FBXExport -f "{file_path_mel}" -s'
            mel.eval(fbx_command)
            pm.textScrollList("resultField", e=True, a=f"Exported: {obj_name}.fbx")
                
        except Exception as e:
            pm.textScrollList("resultField", e=True, a=f"Error exporting {obj_name}: {str(e)}")
    
    # Restore original selection
    cmds.select(selected_paths)
    pm.textScrollList("resultField", e=True, a="Export complete.")
    
    # Final verification message
    pm.textScrollList("resultField", e=True, a="")
    pm.textScrollList("resultField", e=True, a="Export Settings Used:")
    pm.textScrollList("resultField", e=True, a="- FBX Version: 2020")
    pm.textScrollList("resultField", e=True, a="- Up Axis: Z")
    pm.textScrollList("resultField", e=True, a="- Units: Centimeters")
    pm.textScrollList("resultField", e=True, a="- Included: Smoothing Groups, Smooth Mesh, Triangulate")
    pm.textScrollList("resultField", e=True, a="- Excluded: Animation, Cameras, Lights, Audio, Embedded Media")

def exportSelectionAsUV2FBX(*args):
    """Export all selected objects as a single FBX file with only UV channel 2 preserved"""
    # First, make sure user has saved their file
    pm.textScrollList("resultField", e=True, ra=True)
    pm.textScrollList("resultField", e=True, a="Please save your Maya file before exporting...")
    
    # Use centered dialog (appears on main screen)
    try:
        # Try to position the dialog in the center of Maya's main window
        result = cmds.confirmDialog(
            title='Save File',
            message='Please save your Maya file before exporting.\nClick OK when ready to continue.',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel',
            icon='warning'
        )
    except:
        # Fallback if positioning fails
        result = cmds.confirmDialog(
            title='Save File',
            message='Please save your Maya file before exporting.\nClick OK when ready to continue.',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel'
        )
    
    if result != 'OK':
        pm.textScrollList("resultField", e=True, a="Export canceled.")
        return
    
    # Get selected objects using longnames
    selected_paths = cmds.ls(selection=True, long=True)
    if not selected_paths:
        pm.textScrollList("resultField", e=True, a="No objects selected for export.")
        return
    
    # Process groups to get all mesh objects
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
    
    # Check if we have valid objects to export
    if not mesh_objects:
        pm.textScrollList("resultField", e=True, a="No valid geometry objects to export. Only mesh objects can be exported.")
        return
    
    # Ask user for the export filename
    try:
        # Use Maya's standard file dialog with FBX default
        result_file = pm.fileDialog(m=1, dm="*.fbx", t="Enter name for exported FBX")
        
        if not result_file:
            pm.textScrollList("resultField", e=True, a="Export canceled - no filename provided.")
            return
            
        # Ensure the file has .fbx extension
        if not result_file.lower().endswith('.fbx'):
            result_file += '.fbx'
    except:
        pm.textScrollList("resultField", e=True, a="Error getting export filename.")
        return
    
    # Store original selection to restore later
    original_selection = cmds.ls(selection=True, long=True)
    
    # List to keep track of objects to clean up
    temp_objects = []
    
    # Process each mesh object individually to prepare UV sets
    pm.textScrollList("resultField", e=True, a=f"Processing {len(mesh_objects)} mesh objects for export...")
    
    for obj_path in mesh_objects:
        # Get just the object name without the full path
        obj_name = obj_path.split('|')[-1]
        
        # Check if the object has UV sets
        shapes = cmds.listRelatives(obj_path, shapes=True, fullPath=True, type="mesh") or []
        if not shapes:
            pm.textScrollList("resultField", e=True, a=f"No mesh shape found for {obj_name}, skipping...")
            continue
            
        shape = shapes[0]
        original_uv_sets = cmds.polyUVSet(shape, query=True, allUVSets=True) or []
        
        # Check if the mesh has any UV sets
        if not original_uv_sets:
            pm.textScrollList("resultField", e=True, a=f"{obj_name} has no UV sets, skipping...")
            continue
            
        # Duplicate the object
        cmds.select(obj_path, replace=True)
        duplicate_result = cmds.duplicate()[0]  # Get the first result (the duplicated object)
        
        # Add to temp objects for cleanup later
        temp_objects.append(duplicate_result)
        
        # Get the duplicated shape node
        dup_shapes = cmds.listRelatives(duplicate_result, shapes=True, fullPath=True, type="mesh") or []
        if not dup_shapes:
            pm.textScrollList("resultField", e=True, a=f"No mesh shape found in duplicated {obj_name}, skipping...")
            continue
            
        dup_shape = dup_shapes[0]
        
        try:
            # Get UV sets in the duplicate
            dup_uv_sets = cmds.polyUVSet(dup_shape, query=True, allUVSets=True) or []
            
            # Handle based on number of UV sets
            if len(dup_uv_sets) >= 2:
                # Case: Multiple UV sets - preserve only UV channel 2
                
                # Get the name of the second UV set (index 1)
                uv_channel_2 = dup_uv_sets[1]
                
                # Create a temporary UV set as a buffer
                temp_uv_set = "TEMP_UV_SET"
                cmds.polyUVSet(dup_shape, create=True, uvSet=temp_uv_set)
                
                # Copy UV channel 2 to temporary set
                cmds.polyUVSet(dup_shape, copy=True, uvSet=uv_channel_2, newUVSet=temp_uv_set)
                
                # Delete all original UV sets except the first one (which we'll overwrite)
                for uv_set in dup_uv_sets:
                    if uv_set != dup_uv_sets[0]:  # Don't delete the first UV set
                        cmds.polyUVSet(dup_shape, delete=True, uvSet=uv_set)
                
                # Copy temp UV set to the first UV set
                cmds.polyUVSet(dup_shape, copy=True, uvSet=temp_uv_set, newUVSet=dup_uv_sets[0])
                
                # Delete the temporary UV set
                cmds.polyUVSet(dup_shape, delete=True, uvSet=temp_uv_set)
                
                pm.textScrollList("resultField", e=True, a=f"For {obj_name}: Moved UV channel 2 to slot 1")
            else:
                # Case: Only one UV set - just rename it
                pm.textScrollList("resultField", e=True, a=f"For {obj_name}: Only one UV set found, keeping it")
            
            # Rename the UV set to UVChannel2 (regardless of which case)
            current_uv_sets = cmds.polyUVSet(dup_shape, query=True, allUVSets=True) or []
            if current_uv_sets:
                cmds.polyUVSet(dup_shape, rename=True, uvSet=current_uv_sets[0], newUVSet="UVChannel2")
            
        except Exception as e:
            pm.textScrollList("resultField", e=True, a=f"Error processing UV sets for {obj_name}: {str(e)}")
    
    # Select all duplicated objects for combined export
    if temp_objects:
        cmds.select(temp_objects, replace=True)
        
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
        
        # Export the combined FBX - using forward slashes and quotes
        try:
            # Convert path to use forward slashes for Maya's MEL
            file_path_mel = result_file.replace("\\", "/")
            
            # Export
            fbx_command = f'FBXExport -f "{file_path_mel}" -s'
            mel.eval(fbx_command)
            pm.textScrollList("resultField", e=True, a=f"Exported combined FBX to: {result_file}")
                
        except Exception as e:
            pm.textScrollList("resultField", e=True, a=f"Error exporting: {str(e)}")
    else:
        pm.textScrollList("resultField", e=True, a="No valid objects to export after UV processing.")
    
    # Clean up - delete all temporary objects
    if temp_objects:
        cmds.select(temp_objects, replace=True)
        cmds.delete()
        # pm.textScrollList("resultField", e=True, a="Cleaned up temporary objects.")
    
    # Restore original selection
    cmds.select(original_selection)
    pm.textScrollList("resultField", e=True, a="Export with UVchannel2 complete.")
    
    # Final verification message
    pm.textScrollList("resultField", e=True, a="")
    pm.textScrollList("resultField", e=True, a="Export Settings Used:")
    pm.textScrollList("resultField", e=True, a="- FBX Version: 2020")
    pm.textScrollList("resultField", e=True, a="- Up Axis: Z")
    pm.textScrollList("resultField", e=True, a="- Units: Centimeters")
    pm.textScrollList("resultField", e=True, a="- Included: Smoothing Groups, Smooth Mesh, Triangulate")
    pm.textScrollList("resultField", e=True, a="- Excluded: Animation, Cameras, Lights, Audio, Embedded Media")
    pm.textScrollList("resultField", e=True, a="- UV Modification: Keep only UV Set 2 and renamed to UVChannel2")
    pm.textScrollList("resultField", e=True, a="- Export Type: Combined single FBX file")

def UI():
    if cmds.window("win", exists=True):
        cmds.deleteUI("win", window=True)
    
    cmds.window("win", title="Scr1 GSTools (Python 3.7)")   
    
    height = 20
        
    mainLayout = pm.columnLayout(adjustableColumn=True)
    
    # Main check section
    pm.separator(style="out", height=5)
    pm.text(label="Asset Validation", font="boldLabelFont", align="center")
    pm.separator(style="in", height=10)
    
    pm.button(label="Check Selection", height=height+10, command=check)
    pm.separator(style="none", height=5)
    
    pm.text(label="Results:", align="left")
    pm.textScrollList("resultField", height=300)
    # pm.button(label="Print Results", height=height+10, command=printResult)
    
    pm.separator(style="in", height=30)

    # Export section
    pm.text(label="Export Tools", font="boldLabelFont", align="center")
    pm.separator(style="in", height=10)
    
    pm.button(label="Export Selection as FBX", height=height+10, command=exportSelectionAsFBX)
    pm.button(label="Export FBX with UVChannel 2", height=height+10, command=exportSelectionAsUV2FBX)
    
    pm.separator(style="in", height=10)

    cmds.showWindow("win")

if __name__ == "__main__":
    UI()