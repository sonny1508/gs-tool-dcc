import maya.utils
import sys
import os
import maya.cmds as cmds

sys.path.append("//192.168.1.10/Softwares/Technical_Script/Maya_2018/MayaTools/scripts")

# Python version compatibility functions
def is_python2():
    """Check if running Python 2"""
    return sys.version_info.major < 3

def ensure_str(text):
    """Ensure unicode is converted to str for Python 2/3 compatibility"""
    if is_python2() and isinstance(text, unicode):  # noqa: F821
        return text.encode('utf-8')
    return text

def ensure_unicode(text):
    """Ensure string is unicode for Python 2/3 compatibility"""
    if is_python2() and isinstance(text, str):
        return text.decode('utf-8')
    return text

def try_add_path(path):
    """Try to add a path if it exists and return success status"""
    if os.path.exists(path):
        if path not in sys.path:
            sys.path.append(path)
            print("Added path: {}".format(path))
        return True
    else:
        print("Path does not exist (skipping): {}".format(path))
        return False

def addPaths():
    try:
        # Get the current Maya version
        maya_version = cmds.about(version=True)
        print("Current Maya version: " + maya_version)
        print("Python version: " + str(sys.version_info.major) + "." + str(sys.version_info.minor))
        
        # Network path to shared scripts folder
        network_path = "//192.168.1.10/Softwares/Technical_Script"
        
        # Primary GSTools path
        primary_gst_path = "C://Users/%USERNAME%/Documents/maya/scripts/GSTools"
        # Backup GSTools path for when network is down
        # Use %USERPROFILE% equivalent in Python to get current user's directory
        user_home = os.path.expanduser("~")
        backup_gst_path = os.path.join(user_home, "maya", "scripts", "GSTools")
        
        # Add main network path
        try_add_path(network_path)
        
        # Try primary GSTools path first, if it fails use backup
        if not try_add_path(primary_gst_path):
            print("Primary GSTools path unavailable, trying backup path...")
            if try_add_path(backup_gst_path):
                print("Successfully added backup GSTools path")
            else:
                print("WARNING: Both primary and backup GSTools paths are unavailable!")
        
        # Add version-specific path if needed
        version_specific_path = os.path.join(ensure_str(network_path), "Maya_{}".format(maya_version), "MayaTools", "scripts")
        try_add_path(version_specific_path)
        
        # Import the GS_Pipeline module (this will work regardless of which path it's found in)
        try:
            import GS_Pipeline
            print("Successfully imported GS_Pipeline module")
        except ImportError as e:
            print("Error importing GS_Pipeline module: {}".format(e))
            print("Available paths:")
            for p in sys.path:
                print("  - {}".format(p))
    
    except Exception as e:
        print("Error in userSetup.py: {}".format(e))
        import traceback
        traceback.print_exc()

# Execute our setup function after Maya initializes
maya.utils.executeDeferred(addPaths)