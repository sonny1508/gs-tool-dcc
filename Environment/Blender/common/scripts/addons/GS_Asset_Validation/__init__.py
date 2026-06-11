bl_info = {
    "name": "GS Asset Validation",
    "author": "",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > GS Asset Validation",
    "description": "Tools for validating and fixing 3D assets",
    "category": "3D View",
}

import bpy
from . import GS_Asset_Validation_List
from . import GS_Asset_Validation_Function
from . import GS_Asset_Validation_UI

# Debug print to confirm initialization
print("Initializing GS Asset Validation")

def register():
    print("Registering GS Asset Validation")
    GS_Asset_Validation_List.register()
    GS_Asset_Validation_Function.register()
    GS_Asset_Validation_UI.register()
    print("GS Asset Validation registered")

def unregister():
    print("Unregistering GS Asset Validation")
    GS_Asset_Validation_UI.unregister()
    GS_Asset_Validation_Function.unregister()
    GS_Asset_Validation_List.unregister()
    print("GS Asset Validation unregistered")

if __name__ == "__main__":
    register()