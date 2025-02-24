
from maya import cmds

import maya.mel as mel
from zoo.libs.utils import output

SHAPES_PLUGIN_NAME = "SHAPESTools"

def getRendererIsLoaded(pluginName):
    """checks if the plugin is loaded

    :param pluginName: the name of the plugin
    :type pluginName: str
    :return loaded: is the plugin loaded?
    :rtype loaded: bool
    """
    loaded = cmds.pluginInfo(pluginName, query=True, loaded=True)
    return loaded


def loadSHAPES():
    """Load the SHAPES Plugin

    :return loaded: did SHAPES get loaded?
    :rtype loaded: bool
    """
    if getRendererIsLoaded(SHAPES_PLUGIN_NAME):
        output.displayWarning("SHAPES Is Already Loaded")
    try:
        cmds.loadPlugin(SHAPES_PLUGIN_NAME)
        output.displayInfo("SHAPES Has Been Loaded")
        return True
    except RuntimeError:
        output.displayWarning("SHAPES not found in plugin path, it may not be installed")
        return False


def checkSymmetrySHAPESCommand():
    return mel.eval('br_polyMapVertexOrder -check;')  # checks symmetry in SHAPES

def checkAndLoadSHAPES():
    SHAPES_loaded = getRendererIsLoaded(SHAPES_PLUGIN_NAME)
    if not SHAPES_loaded:
        SHAPES_loaded = loadSHAPES()
    return SHAPES_loaded

def checkSymmetrySHAPES():
    SHAPES_loaded = checkAndLoadSHAPES()
    if not SHAPES_loaded:
        return
    checkSymmetrySHAPESCommand()



