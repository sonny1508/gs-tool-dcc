"""Graph editor marking menu.

Hotkey found at zoo.libs.maya.cmds.hotkeys.definedhotkeys.py

Map to press:

.. code-block:: python

    from zoo.libs.maya.cmds.hotkeys import definedhotkeys
    definedhotkeys.graphEditorMarkingMenuPress()

Map to release:

.. code-block:: python

    from zoo.libs.maya.cmds.hotkeys import definedhotkeys
    definedhotkeys.graphEditorMarkingMenuRelease()


Authors: Cosmo Park & Andrew Silke
"""

from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.animation import generalanimation
from zoo.libs.maya.cmds.hotkeys import definedhotkeys
from maya import cmds, mel
from zoo.apps.toolsetsui.run import openToolset
from zoo.libs.utils import output

GRAPH_TRACKER_INST = generalanimation.ZooGraphEditorTrackerSingleton()


def secondaryFunction():
    """When the marking menu is released, run for a secondary feature

    Search for `GRAPH_TRACKER_INST.markingMenuTriggered = True ` to see where the trigger is set to be True
    """
    GRAPH_TRACKER_INST.markingMenuMoShapes = None
    if GRAPH_TRACKER_INST.markingMenuTriggered:  # Ignore if the menu was triggered
        GRAPH_TRACKER_INST.markingMenuTriggered = False
        return
    else:
        definedhotkeys.animMakeHold()


class GraphEditorMarkingMenuCommand(menu.MarkingMenuCommand):
    """Command class for the Graph Editor Marking Menu

    Commands are related to the file (JSON) in the same directory:

    .. code-block:: python

        grapheditor.mmlayout

    Zoo paths must point to this directory, usually on zoo startup inside the repo root package.json file.

    Example add to package.json:

    .. code-block:: python

        "ZOO_MM_COMMAND_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",
        "ZOO_MM_MENU_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",
        "ZOO_MM_LAYOUT_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",

    Or if not on startup, run in the script editor, with your path:

    .. code-block:: python

        os.environ["ZOO_MM_COMMAND_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"
        os.environ["ZOO_MM_MENU_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"
        os.environ["ZOO_MM_LAYOUT_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"

    Map the following code to a hotkey press. Note: Change the key modifiers if using shift alt ctrl etc:

    .. code-block:: python

        import maya.mel as mel
        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.buildFromLayout("markingMenu.graphEditor",
                                            graphEditorMarkingMenu",
                                            parent=mel.eval("findPanelPopupParent"),
                                            options={"altModifier": False,
                                                     "shiftModifier": False})

    Map to hotkey release:

    .. code-block:: python

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.removeExistingMenu("graphEditorMarkingMenu")

    """
    id = "graphEditorMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "ZooTools"

    def toggleCycleAndInfinity(self):
        if not GRAPH_TRACKER_INST.cycleToggle:
            try:
                mel.eval("animCurveEditor -edit -displayInfinities {} graphEditor1GraphEd;".format(1))
                generalanimation.cycleAnimation()
                GRAPH_TRACKER_INST.cycleToggle = True
            except RuntimeError:
                output.displayWarning("Nothing Selected. Please select one.")
        else:
            try:
                mel.eval("animCurveEditor -edit -displayInfinities {} graphEditor1GraphEd;".format(0))
                generalanimation.removeCycleAnimation()
                GRAPH_TRACKER_INST.cycleToggle = False
            except RuntimeError:
                output.displayWarning("Nothing Selected. Please select one.")

    def toggleIsolateMatchingCurveAttrs(self):
        selection = cmds.ls(selection=True)
        selectedCurve = cmds.keyframe(q=True, name=True, sl=True)
        if not selectedCurve:
            output.displayInfo("Nothing Selected, please select an animation curve")
            return
        selectedAttrList = list()
        for selected in selectedCurve:
            selectedAttr = selected.split("_")[-1]
            selectedAttrList.append(selectedAttr)
        selectedAttrList = list(set(selectedAttrList))
        selectedList = list()
        i = 0
        for selected in selection:
            while i < len(selectedAttrList):
                selectedCtrlAttr = ".".join([selected, selectedAttrList[i]])
                selectedList.append(selectedCtrlAttr)
                i += 1
            i = 0
        cmds.selectKey(selectedList, addTo=True, replace=True)

        if not GRAPH_TRACKER_INST.isolateCurveToggle:
            isolateCurveOn = mel.eval("isolateAnimCurve true graphEditor1FromOutliner graphEditor1GraphEd;")
            GRAPH_TRACKER_INST.isolateCurveToggle = True
        else:
            isolateCurveOff = mel.eval("isolateAnimCurve false graphEditor1FromOutliner graphEditor1GraphEd;")
            GRAPH_TRACKER_INST.isolateCurveToggle = False

    @staticmethod
    def uiData(arguments):
        """This method is mostly over-ridden by the associated json file"""
        ret = {"icon": "",
               "label": "",
               "bold": False,
               "italic": False,
               "optionBox": False,
               "optionBoxIcon": ""
               }

        if arguments['operation'] == 'toggleCycleAndInfinity':
            GRAPH_TRACKER_INST.markingMenuTriggered = True
            queryInfinity = mel.eval("animCurveEditor -query -displayInfinities {} graphEditor1GraphEd;")
            if queryInfinity:
                GRAPH_TRACKER_INST.cycleToggle = True
            else:
                GRAPH_TRACKER_INST.cycleToggle = False
            if GRAPH_TRACKER_INST.cycleToggle:
                ret['checkBox'] = True
            else:
                ret['checkBox'] = False

        if arguments['operation'] == 'matchAndIsolateSelCurveAttrs':
            if GRAPH_TRACKER_INST.isolateCurveToggle:
                ret['checkBox'] = True
            else:
                ret['checkBox'] = False

        return ret

    def execute(self, arguments):
        """The main execute methods for the motion trail marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "toggleCycleAndInfinity":
            self.toggleCycleAndInfinity()
        elif operation == "matchAndIsolateSelCurveAttrs":
            self.toggleIsolateMatchingCurveAttrs()
        elif operation == "bakeAnimation":
            generalanimation.bakeKeys()
        elif operation == "selObjFromFCurve":
            generalanimation.selObjGraph()
        elif operation == "eulerFilter":
            generalanimation.eulerFilter()
        elif operation == "snapWholeFrames":
            generalanimation.snapKeysWholeFrames()
        elif operation == "insertKeyTool":
            mel.eval("insertKey")
        elif operation == "timeToSelectedKeys":
            generalanimation.timeToKey()
        elif operation == "snapKeysToCurrent":
            generalanimation.snapKeysCurrent()
        elif operation == "changeRotationOrder":
            openToolset("rotationOrder", advancedMode=False)
        elif operation == "openGraphEditorToolbox":
            definedhotkeys.open_graphEditorTools(advancedMode=False)
        elif operation == "mayaRetimerTool":
            mel.eval("RetimeKeysTool")
        return

    def executeUI(self, arguments):
        """The option box execute methods for the motion paths marking menu. see execute() for main commands

        For this method to be called "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "bakeAnimation":
            openToolset("bakeAnimation", advancedMode=False)
        return
