import os
import sys
import bpy

def register():
    # Define custom script path - use the one that works in your environment
    custom_script_path = r"\\192.168.1.10\Softwares\Pipeline\GSTools\Softwares\Blender\3.6\scripts"
    
    # Alternative formats:
    # custom_script_path = r"Z:\Pipeline\GSTools\Softwares\Blender\3.6\scripts"  # Mapped drive
    # custom_script_path = os.path.join(os.path.expanduser("~"), "local_scripts_folder")  # Local folder
    
    # Set the environment variable
    os.environ["BLENDER_USER_SCRIPTS"] = custom_script_path
    
    # Add to sys.path if not already there
    if custom_script_path not in sys.path:
        sys.path.append(custom_script_path)
    
    # Report success to user
    print(f"Custom Scripts Path addon: Added {custom_script_path}")

def unregister():
    # This function is required but we don't need to undo anything
    pass

# This allows you to run the script directly from Blender's Text editor
if __name__ == "__main__":
    register()