import bpy
from bpy.app.handlers import persistent

bl_info = {
    "name": "GS Pipeline Setup",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "description": "Auto-configures GS pipeline settings",
    "category": "System",
}

@persistent
def setup_script_paths_handler(dummy):
    """Run the setup after Blender has fully loaded a file"""
    print("Setting up script paths...")
    
    # Target paths to set up
    target_paths = [
        ("Technical_Script", r"\\192.168.1.10\Softwares\Technical_Script\Blender")
    ]
    
    # Get user preferences
    prefs = bpy.context.preferences
    filepaths = prefs.filepaths
    
    # First, remove all existing script directories (safer approach)
    while len(filepaths.script_directories) > 0:
        # Always remove the first one until all are gone
        filepaths.script_directories.remove(filepaths.script_directories[0])
        print("Removed a script directory")
    
    # Now add all our directories
    for name, path in target_paths:
        # Add a new directory
        bpy.ops.preferences.script_directory_add()
        # The new directory is the last one added
        new_dir = filepaths.script_directories[-1]
        new_dir.name = name
        new_dir.directory = path
        print(f"Added script directory: {name} -> {path}")
    
    # Final list of script directories
    print("\nFinal Script Directories:")
    for i, sd in enumerate(filepaths.script_directories):
        print(f"{i}: {sd.name} -> {sd.directory}")
    
    # Enable the GS File Transfer add-on
    addon_names = [
        "GS_File_Transfer",  # This should be the actual module name of the add-on
        "GS_Asset_Validation"
    ]
    
    # Enable each add-on in the list
    for addon_name in addon_names:
        try:
            # Check if it's already enabled
            if not addon_name in bpy.context.preferences.addons:
                print(f"Enabling add-on: {addon_name}")
                bpy.ops.preferences.addon_enable(module=addon_name)
                print(f"Successfully enabled add-on: {addon_name}")
            else:
                print(f"Add-on {addon_name} is already enabled")
        except Exception as e:
            print(f"Error enabling add-on {addon_name}: {str(e)}")
    
    # Save preferences
    bpy.ops.wm.save_userpref()
    print("Preferences saved successfully")

def register():
    """Required register function for Blender startup scripts"""
    print("Registering GS Pipeline Setup")
    # Register the load handler to run when Blender is fully initialized
    bpy.app.handlers.load_post.append(setup_script_paths_handler)

def unregister():
    """Required unregister function for Blender startup scripts"""
    print("Unregistering GS Pipeline Setup")
    # Remove our handler
    if setup_script_paths_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(setup_script_paths_handler)

# This runs when the script is loaded
if __name__ == "__main__":
    register()