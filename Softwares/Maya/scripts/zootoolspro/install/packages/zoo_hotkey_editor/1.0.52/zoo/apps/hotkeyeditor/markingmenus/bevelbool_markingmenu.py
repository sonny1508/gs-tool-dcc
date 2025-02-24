from zoovendor import six
from zoo.core.util import classtypes

import maya.mel as mel

from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.modeling import modelnodes


@six.add_metaclass(classtypes.Singleton)
class ZooBevelBoolTrackerSingleton(object):
    """Used by the bevel boolean marking menu & UI, tracks the press and release
    """

    def __init__(self):
        self.markingMenuTriggered = False


TRACKER_INSTANCE = ZooBevelBoolTrackerSingleton()


def secondaryFunction():
    """When the marking menu is released, run for a secondary feature

    Search for `MT_TRACKER_INST.markingMenuTriggered = True ` to see where the trigger is set to be True
    """
    if TRACKER_INSTANCE.markingMenuTriggered:  # Ignore if the menu was triggered
        TRACKER_INSTANCE.markingMenuTriggered = False
        return
    # Bevel and select all bevel nodes.
    modelnodes.createBevel(message=True)


class BevelBoolMarkingMenuCommand(menu.MarkingMenuCommand):
    """Command class for the joints marking menu.

    Commands are related to the file (JSON) in the same directory:

    .. code-block:: python

        bevelbool.mmlayout

    Zoo paths must point to this directory, usually on zoo startup inside the repo root package.json file.

    Example add to package.json:

    .. code-block:: python

        "ZOO_MM_COMMAND_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",
        "ZOO_MM_MENU_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",
        "ZOO_MM_LAYOUT_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",

    Or if not on startup, run in the script editor, with your path:

        os.environ["ZOO_MM_COMMAND_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"
        os.environ["ZOO_MM_MENU_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"
        os.environ["ZOO_MM_LAYOUT_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"

    Map the following code to a hotkey press. Note: Change the key modifiers if using shift alt ctrl etc:

    .. code-block:: python

        from zoo.libs.maya.cmds.hotkeys import definedhotkeys
        definedhotkeys.bevelBoolMarkingMenuPress(alt=False, shift=False, ctrl=True)

    Map to hotkey release:

    .. code-block:: python

        from zoo.libs.maya.cmds.hotkeys import definedhotkeys
        definedhotkeys.bevelBoolMarkingMenuRelease()

    """
    id = "bevelBoolMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        """This method is mostly overridden by the associated json file"""
        TRACKER_INSTANCE.markingMenuTriggered = True
        return {"icon": "",
                "label": "",
                "bold": False,
                "italic": False,
                "optionBox": False,
                "optionBoxIcon": ""
                }

    def execute(self, arguments):
        """The main execute methods for the joints marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "createBevel":
            modelnodes.createBevel(chamfer=True, segments=1)
        elif operation == "bevelNoChamfer":
            modelnodes.createBevel(chamfer=False, segments=1)
        elif operation == "bevelRoundedEdges":
            modelnodes.createBevel(chamfer=True, segments=4)
        elif operation == "selectLastBevelNode":
            modelnodes.selectModelNodesSel(nodeType="polyBevel3", returnAllNodes=False)
        elif operation == "selectAllBevelNodes":
            modelnodes.selectModelNodesSel(nodeType="polyBevel3", returnAllNodes=True)
        elif operation == "differenceAB":
            mel.eval('polyPerformBooleanAction 2 o 0')
        elif operation == "differenceBA":
            mel.eval('polyPerformBooleanAction 4 o 0')
        elif operation == "union":
            mel.eval('polyPerformBooleanAction 1 o 0')
        elif operation == "intersection":
            mel.eval('polyPerformBooleanAction 3 o 0')
        elif operation == "slice":
            mel.eval('polyPerformBooleanAction 5 o 0')
        elif operation == "holePunch":
            mel.eval('polyPerformBooleanAction 6 o 0')
        elif operation == "cutOut":
            mel.eval('polyPerformBooleanAction 7 o 0')
        elif operation == "splitEdges":
            mel.eval('polyPerformBooleanAction 8 o 0')

    def executeUI(self, arguments):
        """The option box execute methods for the joints marking menu. see execute() for main commands

        For this method to be called, in the JSON set "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "createBevel" or operation == "bevelNoChamfer" or operation == "bevelRoundedEdges":
            mel.eval('performPolyBevel 1')
        elif operation == "differenceAB":
            mel.eval('polyPerformBooleanAction 2 o 1')
        elif operation == "differenceBA":
            mel.eval('polyPerformBooleanAction 4 o 1')
        elif operation == "union":
            mel.eval('polyPerformBooleanAction 1 o 1')
        elif operation == "intersection":
            mel.eval('polyPerformBooleanAction 3 o 1')
        elif operation == "slice":
            mel.eval('polyPerformBooleanAction 5 o 1')
        elif operation == "holePunch":
            mel.eval('polyPerformBooleanAction 6 o 1')
        elif operation == "cutOut":
            mel.eval('polyPerformBooleanAction 7 o 1')
        elif operation == "splitEdges":
            mel.eval('polyPerformBooleanAction 8 o 1')
