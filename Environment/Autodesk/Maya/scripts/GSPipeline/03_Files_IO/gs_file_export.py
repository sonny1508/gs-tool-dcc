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

WINDOW = "gs_exporter_win"

# Full paths of the controls, filled in by UI(). cmds resolves a short UI name
# only while it stays unique across every open window, so keep the paths the
# create calls hand back rather than looking the controls up by name again.
_CTRL = {}


def _log(message):
    """Append a line to the operations list."""
    field = _CTRL.get("log")
    if field and cmds.textScrollList(field, exists=True):
        cmds.textScrollList(field, e=True, a=message)


def batchExportFBX(*args):
    """Export objects as FBX files based on selection mode"""
    # Clear the operation field
    cmds.textScrollList(_CTRL["log"], e=True, ra=True)

    # Get the export folder from the text field
    export_folder = cmds.textField(_CTRL["exportDir"], q=True, text=True)

    # Check if the export folder exists
    if not export_folder or not os.path.isdir(export_folder):
        _log("Invalid export directory. Please select a valid folder.")
        return

    # Determine if we're exporting all or selection based on the radio button
    export_all = cmds.radioButton(_CTRL["everythingRadio"], q=True, select=True)

    # Get objects to export
    if export_all:
        # Get all mesh objects in the scene
        _log("Exporting all mesh objects in the scene...")
        selected_paths = cmds.ls(type="transform", long=True)
    else:
        # Get selected objects
        _log("Exporting selected mesh objects...")
        selected_paths = cmds.ls(selection=True, long=True)

    if not selected_paths:
        _log("No objects found to export.")
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
        _log("The following groups will be processed for their children:")
        for obj in group_objects:
            _log("  - {}".format(obj))

    # Check if we have valid objects to export
    if not mesh_objects:
        _log("No valid geometry objects to export. Only mesh objects can be exported.")
        return

    # Check if "As Parent" mode is enabled
    as_parent = cmds.checkBox(_CTRL["asParent"], q=True, value=True)

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

            _log("Exporting {} top-level parents to: {}".format(len(top_parents), export_folder))

            for parent_path in top_parents:
                parent_name = parent_path.split('|')[-1]
                file_path = os.path.join(export_folder, "{}.fbx".format(parent_name))

                # Select the parent and all its descendants
                cmds.select(parent_path, hierarchy=True, replace=True)

                try:
                    gs_fbx.export_selection(file_path, preset=FBX_PRESET)
                    _log("Exported: {}.fbx".format(parent_name))
                except Exception as e:
                    _log("Error exporting {}: {}".format(parent_name, str(e)))
        else:
            # Selection mode + As Parent: selected objects ARE the parents, export each with children
            _log("Exporting {} selected parents to: {}".format(len(selected_paths), export_folder))

            for obj_path in selected_paths:
                obj_name = obj_path.split('|')[-1]
                file_path = os.path.join(export_folder, "{}.fbx".format(obj_name))

                # Select this object and all its descendants
                cmds.select(obj_path, hierarchy=True, replace=True)

                try:
                    gs_fbx.export_selection(file_path, preset=FBX_PRESET)
                    _log("Exported: {}.fbx".format(obj_name))
                except Exception as e:
                    _log("Error exporting {}: {}".format(obj_name, str(e)))
    else:
        _log("Exporting {} individual mesh objects to: {}".format(len(mesh_objects), export_folder))

        # Process each mesh object individually
        for obj_path in mesh_objects:
            obj_name = obj_path.split('|')[-1]
            file_path = os.path.join(export_folder, "{}.fbx".format(obj_name))

            cmds.select(obj_path, replace=True)

            try:
                gs_fbx.export_selection(file_path, preset=FBX_PRESET)
                _log("Exported: {}.fbx".format(obj_name))
            except Exception as e:
                _log("Error exporting {}: {}".format(obj_name, str(e)))

    # Restore original selection
    cmds.select(selected_paths)
    _log("Export complete.")

    # Final verification message
    _log("")
    _log("Export Settings Used:")
    _log("- FBX Version: 2020")
    _log("- Up Axis: Z")
    _log("- Units: Centimeters")
    _log("- Included: Smoothing Groups")
    _log("- Excluded: Animation, Cameras, Lights, Audio, Embedded Media")


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
            fileFilter="Folders (*)|"  # This ensures only folders are shown in the browser
        )
    except:
        # Fallback if advanced options cause issues
        export_folder = cmds.fileDialog2(
            fileMode=3,          # Directory selection only
            fileFilter="Folders (*)|"  # Filter to show only folders
        )

    if export_folder:
        cmds.textField(_CTRL["exportDir"], e=True, text=export_folder[0])


def UI():
    """Create the GS File Exporter UI"""
    # Close existing window if it exists
    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW, window=True)

    _CTRL.clear()

    # Create main window with initial size, but resizable
    cmds.window(WINDOW, title="GS File Exporter", width=720, height=480, sizeable=True)

    height = 20

    # Main layout
    cmds.columnLayout(adjustableColumn=True)

    # Title section
    cmds.separator(style="out", height=5)
    cmds.text(label="GS File Exporter", font="boldLabelFont", align="center")
    cmds.separator(style="in", height=10)

    # Export directory section
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(100, 400, 80), columnAlign=(1, 'right'),
                   columnAttach=[(1, 'both', 5), (2, 'both', 5), (3, 'both', 5)])
    cmds.text(label="Export Directory:")
    _CTRL["exportDir"] = cmds.textField(placeholderText="Select or enter export directory", width=440)
    cmds.button(label="Browse...", command=browseForExportDir, width=80)
    cmds.setParent('..')  # Go back to main layout

    cmds.separator(style="none", height=10)

    # Selection mode section
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(100, 180, 180), columnAlign=(1, 'right'),
                   columnAttach=[(1, 'both', 5), (2, 'both', 5), (3, 'both', 5)])
    cmds.text(label="Export Mode:")
    cmds.radioCollection()
    _CTRL["selectionRadio"] = cmds.radioButton(label="Selection", select=True)
    _CTRL["everythingRadio"] = cmds.radioButton(label="Everything")
    cmds.setParent('..')  # Go back to main layout

    cmds.separator(style="none", height=10)

    # As Parent option
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(100, 280), columnAlign=(1, 'right'),
                   columnAttach=[(1, 'both', 5), (2, 'both', 5)])
    cmds.text(label="")
    _CTRL["asParent"] = cmds.checkBox(label="As Parent", value=False)
    cmds.setParent('..')  # Go back to main layout

    # Export button
    cmds.separator(style="none", height=10)
    cmds.button(label="Batch FBX Export", height=height + 10, command=batchExportFBX, backgroundColor=[0.3, 0.3, 0.3])

    cmds.separator(style="in", height=10)

    # Operations output section
    cmds.text(label="Operations:", align="left")
    cmds.frameLayout(label="", borderVisible=False, labelVisible=False, backgroundColor=[0.3, 0.3, 0.3], marginWidth=0, marginHeight=0)
    _CTRL["log"] = cmds.textScrollList(height=280)
    cmds.setParent('..')

    # Show the window
    cmds.showWindow(WINDOW)


if __name__ == "__main__":
    UI()
