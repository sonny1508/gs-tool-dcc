"""Scripts related to selection order in the prefernces

Main script has issues and currently requires Maya's Preferences Window > Selection to be
open while saving

from zoo.libs.maya.cmds.preferences import prefsselection
prefsselection.setZooSelectionOrder()

"""


from maya import cmds
import maya.mel as mel

from zoo.libs.maya.cmds.preferences.prefsconstants import ZOO_SEL_ORDER
from zoo.libs.utils import output


def setZooSelectionOrder(save=True):
    """

    :param save:
    :type save:
    :return:
    :rtype:
    """
    setSelectionOrderDict(ZOO_SEL_ORDER, save=False)
    if not save:
        output.displayInfo("Selection Preferences have been set to Zoo Tools Defaults.")
        return
    try:
        mel.eval("prefSelectPriorListChanged; prefSelectPriorValChanged; savePrefs -general;")
        output.displayInfo("Selection Preferences have been set and saved to Zoo Tools Defaults.")
    except RuntimeError:
        output.displayWarning("Selection Preferences have been set but not saved.  "
                              "To save please open Maya's Preferences Window and select `Selection` then run. ")


def setSelectionOrderDict(selorderDict, save=True):
    cmds.selectPriority(light=selorderDict["light"],
                        locator=selorderDict["locator"],
                        nurbsCurve=selorderDict["nurbsCurve"],
                        nurbsSurface=selorderDict["nurbsSurface"],
                        polymesh=selorderDict["polymesh"],
                        polymeshEdge=selorderDict["polymeshEdge"],
                        polymeshFace=selorderDict["polymeshFace"],
                        polymeshUV=selorderDict["polymeshUV"],
                        polymeshVertex=selorderDict["polymeshVertex"],
                        camera=selorderDict["camera"],
                        isoparm=selorderDict["isoparm"],
                        controlVertex=selorderDict["controlVertex"],
                        surfaceEdge=selorderDict["surfaceEdge"],
                        surfaceFace=selorderDict["surfaceFace"],
                        lattice=selorderDict["lattice"],
                        latticePoint=selorderDict["latticePoint"],
                        follicle=selorderDict["follicle"],
                        cluster=selorderDict["cluster"])
    if not save:
        return
    try:
        mel.eval("prefSelectPriorListChanged; prefSelectPriorValChanged; savePrefs -general;")
        output.displayInfo("Selection Preferences have been set and saved.")
    except RuntimeError:
        output.displayInfo("Selection Preferences have not been saved.  "
                           "To save please open Maya's Preferences Window > Selection and run again. ")
