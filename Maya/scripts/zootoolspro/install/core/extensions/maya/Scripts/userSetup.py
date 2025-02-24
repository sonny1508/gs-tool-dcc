import os
import json
from maya import cmds
from maya.api import OpenMaya as om2


def zooSetup():
    """Loads the zootools main maya plugins.
    """
    rootPath = os.getenv("ZOOTOOLS_PRO_ROOT", "")
    startupPrefsPath = os.path.join(rootPath, u"extensions", u"maya", u"zootools_maya_startup.json")
    if not os.path.exists(startupPrefsPath):
        return
    try:
        with open(startupPrefsPath, "r") as f:
            prefs = json.load(f)
    except ValueError as er:
        om2.MGlobal.displayError("Failed to load zootools startup path :\n{}".format(er))
        return

    if prefs.get("autoload", False):
        cmds.loadPlugin("zootools.py")
    # temporary solution til will either put this in the prefs or go a different route
    autoLoadDagMenu = prefs.get("loadDagMenuTriggers", True)
    os.environ["ZOO_DAGMENU_AUTOLOAD"] = "1" if autoLoadDagMenu else "0"


if __name__ == "__main__":
    cmds.evalDeferred(zooSetup)
