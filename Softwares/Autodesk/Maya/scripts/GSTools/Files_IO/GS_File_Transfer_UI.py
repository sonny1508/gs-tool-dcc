import maya.cmds as cmds
import maya.mel as mel
import os
import socket
import getpass
import sys

# Python version detection
PY3 = sys.version_info[0] >= 3

def safe_mel_path(path):
    """
    Make a path safe for MEL commands in both Python 2 and 3.
    MEL requires paths to use forward slashes and proper quoting.
    """
    # Normalize the path to use forward slashes (which MEL can handle)
    normalized = path.replace('\\', '/')
    return normalized

def GS_File_Transfer_UI():
    # Get current Windows username
    username = getpass.getuser()
    computer_name = socket.gethostname()
    
    # Construct temp directory path directly using username (similar to 3ds Max script)
    # Handle path joining differently depending on Python version
    if PY3:
        temp_dir = os.path.join("C:\\Users", username, "AppData\\Local\\Temp\\")
        local_export_path = os.path.join(temp_dir, "fileTransferFbx\\")
    else:
        # In Python 2, manually construct paths to avoid issues
        temp_dir = "C:\\Users\\" + username + "\\AppData\\Local\\Temp\\"
        local_export_path = temp_dir + "fileTransferFbx\\"
    
    # Create the directory if it doesn't exist
    if not os.path.exists(local_export_path):
        try:
            os.makedirs(local_export_path)
            print("Created directory: " + local_export_path)
        except:
            cmds.warning("Failed to create directory: " + local_export_path)
    
    # Generate gs folder list (like in 3ds Max script)
    gs_folder_list = []
    for i in range(1, 100):
        # Format string differently depending on Python version
        if PY3:
            gs_num = "{:02d}".format(i)
        else:
            gs_num = "{0:02d}".format(i)
        gs_folder_list.append("gs" + gs_num)

    # Import functions
    def Import_From_Blender(*args):
        import_file = os.path.join(local_export_path, "blender_to_maya.fbx")
        print("Attempting to import: " + import_file)
        
        if os.path.exists(import_file):
            mel.eval('FBXImportUnlockNormals -v true;')
            mel.eval('FBXImportScaleFactor 1;')
            
            # Convert path to MEL-safe format
            safe_path = safe_mel_path(import_file)
            mel.eval('FBXImport -f "' + safe_path + '";')
        else:
            cmds.confirmDialog(title="Import Error", message="File does not exist: " + import_file, button="OK")

    def Export_To_Blender(*args):
        if cmds.ls(sl=True):
            export_file = os.path.join(local_export_path, "maya_to_blender.fbx")
            print("Attempting to export to: " + export_file)
            
            # Create export directory if it doesn't exist
            if not os.path.exists(os.path.dirname(export_file)):
                try:
                    os.makedirs(os.path.dirname(export_file))
                except:
                    cmds.confirmDialog(title="Export Error", message="Failed to create directory: " + os.path.dirname(export_file), button="OK")
                    return
            
            mel.eval('FBXExportScaleFactor 1.0;')
            
            # Convert path to MEL-safe format
            safe_path = safe_mel_path(export_file)
            mel.eval('FBXExport -f "' + safe_path + '" -s;')
            
            print("Successfully exported to: " + export_file)
        else:
            cmds.confirmDialog(title="Warning", message="Please select objects to export!", button="OK")

    def Import_From_Max(*args):
        import_file = os.path.join(local_export_path, "max_to_maya.fbx")
        print("Attempting to import: " + import_file)
        
        if os.path.exists(import_file):
            mel.eval('FBXImportUnlockNormals -v true;')
            
            # Convert path to MEL-safe format
            safe_path = safe_mel_path(import_file)
            mel.eval('FBXImport -f "' + safe_path + '";')
        else:
            cmds.confirmDialog(title="Import Error", message="File does not exist: " + import_file, button="OK")

    def Export_To_Max(*args):
        if cmds.ls(sl=True):
            export_file = os.path.join(local_export_path, "maya_to_max.fbx")
            print("Attempting to export to: " + export_file)
            
            # Create export directory if it doesn't exist
            if not os.path.exists(os.path.dirname(export_file)):
                try:
                    os.makedirs(os.path.dirname(export_file))
                except:
                    cmds.confirmDialog(title="Export Error", message="Failed to create directory: " + os.path.dirname(export_file), button="OK")
                    return
                    
            mel.eval('FBXExportScaleFactor 1.0;')
            
            # Convert path to MEL-safe format
            safe_path = safe_mel_path(export_file)
            mel.eval('FBXExport -f "' + safe_path + '" -s;')
            
            print("Successfully exported to: " + export_file)
        else:
            cmds.confirmDialog(title="Warning", message="Please select objects to export!", button="OK")

    def Import_From_Server(*args):
        app1 = cmds.optionMenu("APP_IMPORT", query=True, value=True).lower()
        app2 = "maya"
        gs_folder = cmds.optionMenu("PERSON_IMPORT", query=True, value=True)
        
        # Build the path with new folder structure (matching 3ds Max script)
        server_path = "\\\\192.168.1.10\\Temp\\File_Transfer\\"
        file_path = server_path + gs_folder + "\\" + gs_folder + "_" + app1 + "_to_" + app2 + "_" + username + ".fbx"
        
        print("Attempting to import from server: " + file_path)
        if os.path.exists(file_path):
            mel.eval('FBXImportUnlockNormals -v true;')
            
            # Convert path to MEL-safe format
            safe_path = safe_mel_path(file_path)
            mel.eval('FBXImport -f "' + safe_path + '";')
        else:
            cmds.confirmDialog(title="Import Error", message="File does not exist: " + file_path, button="OK")

    def Export_To_Server(*args):
        if cmds.ls(sl=True):
            app1 = "maya"
            app2 = cmds.optionMenu("APP_EXPORT", query=True, value=True).lower()
            gs_folder = cmds.optionMenu("PERSON_EXPORT", query=True, value=True)
            
            # Build the path with new folder structure (matching 3ds Max script)
            server_path = "\\\\192.168.1.10\\Temp\\File_Transfer\\"
            file_path = server_path + username + "\\" + username + "_" + app1 + "_to_" + app2 + "_" + gs_folder + ".fbx"
            
            print("Attempting to export to server: " + file_path)
            
            # Create export directory if it doesn't exist
            dir_path = os.path.dirname(file_path)
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                except:
                    cmds.confirmDialog(title="Export Error", message="Failed to create directory: " + dir_path, button="OK")
                    return
                    
            mel.eval('FBXExportScaleFactor 1.0;')
            
            # Convert path to MEL-safe format
            safe_path = safe_mel_path(file_path)
            mel.eval('FBXExport -f "' + safe_path + '" -s;')
            
            print("Successfully exported to: " + file_path)
        else:
            cmds.confirmDialog(title="Warning", message="Please select objects to export!", button="OK")

    # Check if window exists and delete it
    if cmds.window("GS_File_Transfer_Window", exists=True):
        cmds.deleteUI("GS_File_Transfer_Window")

    # Create window with responsive layout
    window = cmds.window("GS_File_Transfer_Window", title='GS_File_Transfer', width=140, minimizeButton=False, maximizeButton=False)
    
    # Main column layout
    main_layout = cmds.columnLayout(adjustableColumn=True, width=140)
    
    # Local section
    cmds.frameLayout('localFrame', parent=main_layout, collapsable=True, label='Local', marginWidth=5, marginHeight=5)
    local_form = cmds.formLayout(parent='localFrame', numberOfDivisions=100)
    
    # Blender group
    blender_frame = cmds.frameLayout(parent=local_form, collapsable=False, label='Blender', width=60)
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(height=10, style='none')
    cmds.button(height=25, label='Import', c=Import_From_Blender)
    cmds.separator(height=5, style='none')
    cmds.button(height=25, label='Export', c=Export_To_Blender)
    
    # Max group
    max_frame = cmds.frameLayout(parent=local_form, collapsable=False, label='Max', width=60)
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(height=10, style='none')
    cmds.button(height=25, label='Import', c=Import_From_Max)
    cmds.separator(height=5, style='none')
    cmds.button(height=25, label='Export', c=Export_To_Max)
    
    # Layout the frames side by side with responsive positioning
    cmds.formLayout(
        local_form, edit=True,
        attachForm=[(blender_frame, 'left', 5), (blender_frame, 'top', 5), 
                   (max_frame, 'right', 5), (max_frame, 'top', 5)],
        attachPosition=[(blender_frame, 'right', 5, 50), (max_frame, 'left', 5, 50)]
    )
    
    cmds.setParent(main_layout)
    cmds.separator(height=5)
    
    # Server section
    cmds.frameLayout('serverFrame', parent=main_layout, collapsable=True, label='Server', marginWidth=5, marginHeight=5)
    server_column = cmds.columnLayout(adjustableColumn=True)
    
    # Import section - using formLayout for responsive behavior
    import_form = cmds.formLayout(numberOfDivisions=100)
    
    # Create application and person dropdowns
    app_import = cmds.optionMenu("APP_IMPORT")
    for app in ["Blender", "Maya", "Max"]:
        cmds.menuItem(label=app)
    
    person_import = cmds.optionMenu("PERSON_IMPORT")
    for gs_folder in gs_folder_list:
        cmds.menuItem(label=gs_folder)
    
    # Position the dropdowns side by side
    cmds.formLayout(
        import_form, edit=True,
        attachForm=[
            (app_import, 'left', 5),
            (app_import, 'top', 5),
            (person_import, 'right', 5),
            (person_import, 'top', 5)
        ],
        attachPosition=[
            (app_import, 'right', 5, 50),
            (person_import, 'left', 5, 50)
        ]
    )
    
    # Import button - full width
    cmds.setParent(server_column)
    cmds.separator(height=5, style='none')
    cmds.button(height=25, label='Import', c=Import_From_Server)
    
    # Separator between import and export sections
    cmds.separator(height=10)
    
    # Export section - using formLayout for responsive behavior
    export_form = cmds.formLayout(numberOfDivisions=100)
    
    # Create application and person dropdowns
    app_export = cmds.optionMenu("APP_EXPORT")
    for app in ["Blender", "Maya", "Max"]:
        cmds.menuItem(label=app)
    
    person_export = cmds.optionMenu("PERSON_EXPORT")
    for gs_folder in gs_folder_list:
        cmds.menuItem(label=gs_folder)
    
    # Position the dropdowns side by side
    cmds.formLayout(
        export_form, edit=True,
        attachForm=[
            (app_export, 'left', 5),
            (app_export, 'top', 5),
            (person_export, 'right', 5),
            (person_export, 'top', 5)
        ],
        attachPosition=[
            (app_export, 'right', 5, 50),
            (person_export, 'left', 5, 50)
        ]
    )
    
    # Export button - full width
    cmds.setParent(server_column)
    cmds.separator(height=5, style='none')
    cmds.button(height=25, label='Export', c=Export_To_Server)
    
    # User information at the bottom
    cmds.setParent(main_layout)
    cmds.separator(height=5)
    
    # Create a form layout for better alignment
    user_form = cmds.formLayout(parent=main_layout, width=140)
    user_label = cmds.text(label="Current User: ", align="left", width=80)
    user_name = cmds.text(label=username, align="left")
    
    # Position the text fields to be fully aligned with main layout
    cmds.formLayout(
        user_form, edit=True,
        attachForm=[
            (user_label, 'left', 10),
            (user_label, 'top', 0),
            (user_name, 'top', 0),
            (user_name, 'right', 5)
        ],
        attachControl=[
            (user_name, 'left', 0, user_label)
        ]
    )
    
    # Show window and adjust size to content
    cmds.showWindow(window)
    cmds.window(window, edit=True, width=200, height=320, resizeToFitChildren=False)

# Run the UI
GS_File_Transfer_UI()