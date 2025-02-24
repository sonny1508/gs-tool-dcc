import webbrowser

from maya import cmds
import maya.mel as mel

from zoo.libs.utils import output
from zoo.libs.maya.utils import general


def installPlugin():
    address = "https://create3dcharacters.com/maya-third-party/#smoothweights"
    webbrowser.open(address)
    output.displayWarning("Smooth Skin Weights is a third party script and is not installed correctly, "
                          "please install from the instructions at {}.".format(address))


def loadPlugin():
    return general.loadPlugin('brSmoothWeights')


def smoothSkinBrush():
    # todo check for plugin
    mel.eval('brSmoothWeightsToolCtx')


def getTool():
    """Returns the braverabbit smooth weights skin tool

    :return tool: The smooth skins context as a maya tool
    :rtype tool: str
    """
    tool = mel.eval("brSmoothWeightsContext")
    return tool


def setTool(tool):
    cmds.setToolTo(tool)


def brushSize(tool):
    return cmds.brSmoothWeightsContext(tool, query=True, size=True)


def setBrushSize(tool, size=5.0):
    cmds.brSmoothWeightsContext(tool, edit=True, size=size)


def strength(tool):
    return cmds.brSmoothWeightsContext(tool, query=True, strength=True)


def setStrength(tool, strength=0.25):
    cmds.brSmoothWeightsContext(tool, edit=True, strength=strength)


def oversampling(tool):
    return cmds.brSmoothWeightsContext(tool, query=True, oversampling=True)


def setOversampling(tool, oversampling=1):
    cmds.brSmoothWeightsContext(tool, edit=True, oversampling=oversampling)


def flood(tool, strength=0.5):
    cmds.brSmoothWeightsContext(tool, edit=True, flood=strength)
    # mel version below
    # mel.eval("brSmoothWeightsContext -edit -flood {} {};".format(strength, tool))


def openBraverabbitToolWindow():
    mel.eval("toolPropertyWindow;")
