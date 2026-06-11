import maya.cmds as cmds
import os, shutil

from ..GN_source import GN_Print

def GN_ImportExportCleanup():
    confirm = cmds.confirmDialog(t="Cleanup confirmation", b=["OK", "Cancel"], m="Press OK to clean cache.", db="OK", cb="Cancel", ds="Closed by user")
    if confirm == "OK":
        directory = "C:/temp/"
        exported = "exported"
        if os.path.isdir(directory):
            files = os.listdir(directory)
            for file in files:
                name = file.split(".")[0]
                path = os.path.join(directory, file)
                if name == exported:
                    # Remove exported files
                    if os.path.isfile(path):
                        os.remove(path)
                    # Remove exported folder
                    elif os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
            # Remove temp folder if empty
            if not os.listdir(directory):
                os.rmdir(directory)
        
        # Print
        GN_Print.GN_Print("# Result: Deleted all files exported in C:/temp")