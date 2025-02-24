"""
This script file is responsible for patching maya modules with MockExt.

You can modify the sphinx documentation conf.py in here as well.
All variables in sphinx configuration is accessible as globals ie. autodoc_mock_imports = []

If you need to mock an object you can use our custom mock object called MockExt
"""

sys.modules.update((mod_name, MockExt()) for mod_name in [
    "maya",
    "maya.api",
    "maya.api.OpenMaya",
    "maya.api.OpenMayaAnim",
    "maya.OpenMaya",
    "maya.OpenMayaUI",
    "maya.OpenMayaAnim",
    "maya.cmds",
    "maya.mel",
    "maya.app",
    "maya.app.general",
    "maya.app.general.mayaMixin",

])

