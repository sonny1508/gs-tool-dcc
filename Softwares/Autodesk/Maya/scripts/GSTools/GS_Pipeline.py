import os
import sys
import maya.cmds as cmds
import maya.utils

# Python version compatibility functions
def is_python2():
    """Check if running Python 2"""
    return sys.version_info.major < 3

def ensure_unicode(text):
    """Ensure string is unicode for Python 2/3 compatibility"""
    if is_python2() and isinstance(text, str):
        return text.decode('utf-8')
    return text

def ensure_str(text):
    """Ensure unicode is converted to str for Python 2/3 compatibility"""
    if is_python2() and isinstance(text, unicode):  # noqa: F821
        return text.encode('utf-8')
    return text

def join_paths(path1, path2):
    """Join paths with os.path.join and ensure proper string type"""
    path = os.path.join(ensure_str(path1), ensure_str(path2))
    if is_python2():
        return path
    return path

def get_icon_name_from_script(script_name):
    """Convert a script name to an icon name based on the given pattern"""
    # Convert to lowercase and ensure underscores are used
    name = script_name.lower().replace(" ", "_")
    
    # Add the icon suffix
    return name + "_icon.png"

def find_ui_scripts_recursive(base_dir, folder_path, parent_folder=""):
    """
    Recursively find all UI scripts in a directory and its subdirectories
    
    Args:
        base_dir (str): The root directory to use for relative paths
        folder_path (str): The current directory to search
        parent_folder (str): The top-level parent folder name
        
    Returns:
        list: List of UI scripts found
    """
    ui_scripts = []
    
    # Process all items in the current folder
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        
        # If it's a directory, process it recursively
        if os.path.isdir(item_path):
            # Recursively find UI scripts in this subfolder
            subfolder_scripts = find_ui_scripts_recursive(
                base_dir, item_path, parent_folder
            )
            
            # Add scripts from this subfolder to our list
            ui_scripts.extend(subfolder_scripts)
        
        # If it's a file, check if it's a UI script
        elif os.path.isfile(item_path):
            filename, ext = os.path.splitext(item)
            
            # Look for files ending with "UI" with .py or .mel extensions
            if filename.endswith("UI") and ext.lower() in ['.py', '.mel']:
                script_name = filename
                
                # Format the display name: remove underscores and "UI" suffix
                display_name = script_name
                if display_name.endswith("_UI"):
                    display_name = display_name[:-3]  # Remove "_UI" suffix
                display_name = display_name.replace("_", " ")  # Replace underscores with spaces
                
                # Get button name from script name
                button_name = script_name
                if button_name.endswith("_UI"):
                    button_name = button_name[:-3]  # Remove "_UI" suffix
                
                script_path = os.path.join(folder_path, item).replace("\\", "/")
                
                # Create appropriate command based on file extension
                if ext.lower() == '.py':
                    # Python command
                    if sys.version_info.major >= 3:
                        # For Python 3.x
                        cmd = "exec(compile(open(r'{}', 'r').read(), r'{}', 'exec'))".format(script_path, script_path)
                    else:
                        # For Python 2.x
                        cmd = "execfile(r'{}')".format(script_path)
                else:  # .mel file
                    # Use Python's maya.mel.eval to properly execute MEL commands
                    cmd = "import maya.mel as mel; mel.eval('source \\\"{}\\\" ; {}();')".format(
                        script_path.replace("\\", "/"), 
                        filename
                    )
                
                # Add to UI scripts list
                ui_scripts.append({
                    'name': display_name,
                    'button_name': button_name,
                    'path': script_path,
                    'parent_folder': parent_folder,
                    'command': cmd
                })
    
    return ui_scripts

def createMenuAndShelf():
    try:
        # Get the directory where this script is located
        SCRIPT_DIR = os.path.dirname(os.path.abspath(ensure_str(__file__)))
        
        # Get current script name without extension and path
        SCRIPT_NAME = os.path.splitext(os.path.basename(ensure_str(__file__)))[0]
        
        # Create display name by replacing underscores with spaces
        DISPLAY_NAME = ensure_unicode(SCRIPT_NAME).replace("_", " ")
        
        # Create internal name (without spaces)
        INTERNAL_NAME = ensure_unicode(SCRIPT_NAME).replace("_", "")
        
        # ================ MENU CREATION ================
        # Menu ID - use lowercase prefix for consistency
        MENU_ID = INTERNAL_NAME.lower() + 'Menu'
        
        # Remove existing menu if it exists
        if cmds.menu(MENU_ID, exists=True):
            cmds.deleteUI(MENU_ID, menu=True)
            
        # Create main menu
        main_menu = cmds.menu(MENU_ID, 
                             label=DISPLAY_NAME,
                             parent='MayaWindow',
                             tearOff=True)
        
        # ================ SHELF CREATION ================
        # Name for our shelf - use display name with spaces
        SHELF_NAME = DISPLAY_NAME
        
        # Also check for legacy shelf names that might exist
        LEGACY_SHELF_NAMES = [
            INTERNAL_NAME,  # "GSPipeline"
            SCRIPT_NAME     # "GS_Pipeline"
        ]
        
        # Delete legacy shelves if they exist
        for legacy_name in LEGACY_SHELF_NAMES:
            if cmds.shelfLayout(legacy_name, exists=True):
                print("Removing legacy shelf: {}".format(legacy_name))
                cmds.deleteUI(legacy_name, layout=True)
        
        # Delete the current shelf if it already exists
        if cmds.shelfLayout(SHELF_NAME, exists=True):
            cmds.deleteUI(SHELF_NAME, layout=True)
        
        # Create a new shelf
        main_shelf = cmds.shelfLayout(SHELF_NAME, parent='ShelfLayout')
        
        # ================ GET FOLDERS AND SCRIPTS RECURSIVELY ================
        folder_menus = {}  # Store folder menus by name
        all_scripts = []   # Store all found UI scripts
        
        # Get all top-level folders in the script directory, excluding __pycache__ and Icons
        folder_list = []
        for item in os.listdir(SCRIPT_DIR):
            item_path = os.path.join(SCRIPT_DIR, item)
            
            excluded_folders = {"__pycache__", "Icons"}
            
            if os.path.isdir(item_path) and item not in excluded_folders:
                folder_list.append(item)
        
        # Sort folders alphabetically for consistent menu ordering
        folder_list.sort()
        
        # Create menus for each top-level folder with separators between them
        for i, folder in enumerate(folder_list):
            item_path = os.path.join(SCRIPT_DIR, folder)
            
            # Add a separator before each folder (except the first one)
            if i > 0:
                cmds.menuItem(parent=main_menu, divider=True)
            
            # Format the folder name for display
            display_folder_name = folder.replace("_", " ")
            
            # Create a submenu for this top-level folder
            folder_menu = cmds.menuItem(
                parent=main_menu,
                label=display_folder_name,
                subMenu=True,
                tearOff=True
            )
            
            # Store the menu for this folder
            folder_menus[folder] = folder_menu
            
            # Find all UI scripts recursively in this folder and its subfolders
            folder_scripts = find_ui_scripts_recursive(SCRIPT_DIR, item_path, folder)
            
            # Add menu items for all scripts under this folder
            has_ui_scripts = False
            for script in folder_scripts:
                has_ui_scripts = True
                cmds.menuItem(
                    parent=folder_menu,
                    label=script['name'],
                    command=script['command']
                )
                
                # Add to the global list of scripts
                all_scripts.append(script)
            
            # If no UI scripts were found, add a placeholder
            if not has_ui_scripts:
                cmds.menuItem(
                    parent=folder_menu,
                    label="No UI scripts found",
                    enable=False
                )
        
        # ================ CREATE SHELF BUTTONS ================
        # Group scripts by their parent folder
        scripts_by_folder = {}
        for script in all_scripts:
            parent_folder = script['parent_folder']
            if parent_folder not in scripts_by_folder:
                scripts_by_folder[parent_folder] = []
            scripts_by_folder[parent_folder].append(script)
        
        # Sort folders for consistent ordering
        sorted_folders = sorted(scripts_by_folder.keys())
        
        # Create buttons with separators between different folders
        for i, folder in enumerate(sorted_folders):
            # Add a separator before each folder's buttons (except the first one)
            if i > 0:
                # Create a separator using a blank button (more reliable than separator.png)
                cmds.separator(
                    parent=main_shelf,
                    width=34,
                    height=35,
                    enable=True,
                    visible=True,
                    manage=True,
                    preventOverride=False,
                    enableBackground=False,
                    backgroundColor=(0, 0, 0),
                    style="shelf",  # The specific shelf style from your MEL code
                    horizontal=False  # Vertical separator
                )
            
            # Create buttons for all scripts in this folder
            folder_scripts = scripts_by_folder[folder]
            for script in folder_scripts:
                # Generate the icon name from the script name
                original_button_name = script['button_name']
                icon_filename = get_icon_name_from_script(original_button_name)
                
                # Path to the potential icon (with forward slashes for Maya)
                icons_dir = os.path.join(SCRIPT_DIR, "Icons")
                icon_path = os.path.join(icons_dir, icon_filename).replace("\\", "/")
                
                # Use the icon if it exists, otherwise use default
                if os.path.exists(icon_path):
                    icon_to_use = icon_path
                else:
                    print(f"Icon not found: {icon_filename}. Using default icon.")
                    icon_to_use = 'pythonFamily.png'  # Default Maya script icon
                
                # Create a shelf button with label on top of the icon
                cmds.shelfButton(
                    parent=main_shelf,
                    label=script['button_name'],
                    image=icon_to_use,
                    # imageOverlayLabel=original_button_name,
                    annotation=script['name'],
                    command=script['command'],
                    width=100,
                    height=100
                )
        
        # Print Python version info for debugging
        print("Python Version: " + str(sys.version_info.major) + "." + str(sys.version_info.minor))
        print("{} menu and shelf created successfully".format(DISPLAY_NAME))
        print("Script directory: " + SCRIPT_DIR)
        print("Menu ID: " + MENU_ID)
        print("Shelf name: " + SHELF_NAME)
        print("Number of UI scripts found: " + str(len(all_scripts)))
        
    except Exception as e:
        cmds.warning("Failed to create menu and shelf: " + str(e))
        import traceback
        traceback.print_exc()

# Create the menu and shelf when this script is run
maya.utils.executeDeferred(createMenuAndShelf)