import os
import sys
import maya.cmds as cmds

import maya.utils

def createMenu():
    try:
        # Get the directory where this script is located
        tools_path = r"S:/Fr_Sonny/GSTools/Internal/Maya/scripts"
        ride6_path = os.path.join(tools_path, "Ride6")
        
        # Check if Ride6 path exists
        if not os.path.exists(ride6_path):
            cmds.warning("Ride6 folder not found at: " + ride6_path)
            return
            
        # Remove existing menu if it exists
        if cmds.menu('gsDevMenu', exists=True):
            cmds.deleteUI('gsDevMenu', menu=True)
            
        # Create menu
        main_menu = cmds.menu('gsDevMenu', 
                             label='GS Development',
                             parent='MayaWindow',
                             tearOff=True)
        
        # Add scripts to menu
        for file in os.listdir(ride6_path):
            if file.endswith(".py"):
                script_name = os.path.splitext(file)[0]
                script_path = os.path.join(ride6_path, file).replace("\\", "/")
                
                cmds.menuItem(
                    parent=main_menu,
                    label=script_name,
                    command="execfile(r'{}')".format(script_path)
                )
                
        print("Menu created successfully")
        print("Ride6 path: " + ride6_path)
        
    except Exception as e:
        cmds.warning("Failed to create menu: " + str(e))
        raise  # Re-raise the exception to see the full error trace

# Create the menu when this script is run
maya.utils.executeDeferred(createMenu)