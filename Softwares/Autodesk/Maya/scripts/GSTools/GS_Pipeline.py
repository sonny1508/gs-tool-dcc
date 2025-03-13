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
        
        # ================ GET FOLDERS ================
        # Get all folders in the script directory, excluding __pycache__
        folder_list = []
        for item in os.listdir(SCRIPT_DIR):
            item_path = os.path.join(SCRIPT_DIR, item)
            if os.path.isdir(item_path) and item != "__pycache__":
                folder_list.append(item)
        
        # ================ CREATE MENUS AND SHELF BUTTONS ================
        for folder in folder_list:
            folder_path = os.path.join(SCRIPT_DIR, folder)
            
            # Format the folder name for display: replace underscores with spaces
            display_folder_name = folder.replace("_", " ")
            
            # == MENU: Create submenu for this folder ==
            folder_menu = cmds.menuItem(
                parent=main_menu,
                label=display_folder_name,
                subMenu=True,
                tearOff=True
            )
            
            # Find UI scripts in this folder
            ui_scripts = []
            has_ui_scripts = False
            
            for file in os.listdir(folder_path):
                # Only add scripts that end with UI.py
                if file.endswith("UI.py"):
                    has_ui_scripts = True
                    script_name = os.path.splitext(file)[0]
                    
                    # Format the display name: remove underscores and "UI" suffix
                    display_name = script_name
                    if display_name.endswith("_UI"):
                        display_name = display_name[:-3]  # Remove "_UI" suffix
                    display_name = display_name.replace("_", " ")  # Replace underscores with spaces
                    
                    script_path = os.path.join(folder_path, file).replace("\\", "/")
                    
                    # Create a simpler command that works for both Python 2 and 3
                    if sys.version_info.major >= 3:
                        # For Python 3.x
                        cmd = "exec(compile(open(r'{}', 'r').read(), r'{}', 'exec'))".format(script_path, script_path)
                    else:
                        # For Python 2.x
                        cmd = "execfile(r'{}')".format(script_path)
                    
                    # Add to UI scripts list for shelf creation
                    ui_scripts.append({
                        'name': display_name,
                        'path': script_path,
                        'command': cmd
                    })
                    
                    # == MENU: Add menu item ==
                    cmds.menuItem(
                        parent=folder_menu,
                        label=display_name,
                        command=cmd
                    )
            
            # == MENU: If no UI scripts were found, add a placeholder item ==
            if not has_ui_scripts:
                cmds.menuItem(
                    parent=folder_menu,
                    label="No UI scripts found",
                    enable=False
                )
            
            # == SHELF: If there are UI scripts in this folder, create a shelf button ==
            if ui_scripts:
                # Create a shelf button for the folder
                folder_button = cmds.shelfButton(
                    parent=main_shelf,
                    label=display_folder_name,
                    image='menuIconFolders.png',  # Default Maya folder icon
                    imageOverlayLabel=folder[:2].upper(),  # First two letters of folder name
                    annotation=display_folder_name,
                    width=37,
                    height=37
                )
                
                # Create popup menu for the folder button
                popup_menu = cmds.popupMenu(parent=folder_button)
                
                # Add menu items for each UI script
                for script in ui_scripts:
                    cmds.menuItem(
                        parent=popup_menu,
                        label=script['name'],
                        command=script['command']
                    )
                
                # If only one script in the folder, make the button execute it directly
                if len(ui_scripts) == 1:
                    cmds.shelfButton(
                        folder_button,
                        edit=True,
                        command=ui_scripts[0]['command']
                    )
        
        # Print Python version info for debugging
        print("Python Version: " + str(sys.version_info.major) + "." + str(sys.version_info.minor))
        print("{} menu and shelf created successfully".format(DISPLAY_NAME))
        print("Script directory: " + SCRIPT_DIR)
        print("Menu ID: " + MENU_ID)
        print("Shelf name: " + SHELF_NAME)
        print("Added folders: " + ", ".join(folder_list) if folder_list else "No folders found")
        
    except Exception as e:
        cmds.warning("Failed to create menu and shelf: " + str(e))
        import traceback
        traceback.print_exc()

# Create the menu and shelf when this script is run
maya.utils.executeDeferred(createMenuAndShelf)