import maya.mel as mel
from maya import cmds

from zoovendor import six
from zoo.core.util import classtypes

from zoo.libs.maya.markingmenu import menu
from zoo.libs.utils import output
from zoo.libs.maya.cmds.animation import motiontrail

@six.add_metaclass(classtypes.Singleton)
class ZooDeleteHistoryTrackerSingleton(object):
    """Used by the delete history marking menu & UI, tracks the press and release
    """

    def __init__(self):
        self.markingMenuTriggered = False


TRACKER_INSTANCE = ZooDeleteHistoryTrackerSingleton()


def secondaryFunction():
    """When the marking menu is released, run for a secondary feature

    Search for `MT_TRACKER_INST.markingMenuTriggered = True ` to see where the trigger is set to be True
    """
    if TRACKER_INSTANCE.markingMenuTriggered:  # Ignore if the menu was triggered
        TRACKER_INSTANCE.markingMenuTriggered = False
        return
    # Maya regular delete history
    mel.eval("delete -ch")


def deleteHistoryMel():
    if not cmds.ls(selection=True):
        output.displayWarning("Please select an object/s to delete history.")
        return
    mel.eval('delete -ch')


def deleteNonDeformerHistoryMel():
    if not cmds.ls(selection=True):
        output.displayWarning("Please select an object/s to delete non deformer history.")
        return
    mel.eval('performBakeNonDefHistory false')

class DeleteHistoryMarkingMenuCommand(menu.MarkingMenuCommand):
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
        definedhotkeys.deleteHistoryMarkingMenuPress(alt=True, shift=True, ctrl=False)

    Map to hotkey release:

    .. code-block:: python

        from zoo.libs.maya.cmds.hotkeys import definedhotkeys
        definedhotkeys.deleteHistoryMarkingMenuRelease()

    """
    id = "deleteHistoryMarkingMenu"  # a unique identifier for a class, should never be changed
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
        if operation == "deleteHistory":
            deleteHistoryMel()
        elif operation == "deleteNonDeformerHistory":
            deleteNonDeformerHistoryMel()
        elif operation == "deleteRelatedConstraints":
            mel.eval("DeleteConstraints;")
        elif operation == "deleteMotionPaths":
            motiontrail.deleteMotionTrails(scene=True, selected=False)
        elif operation == "deleteEdge":
            mel.eval("DeletePolyElements;")
        elif operation == "deleteKeyCurrentFrame":
            mel.eval("timeSliderClearKey;")
        elif operation == "deleteStaticChannels":
            mel.eval("delete -staticChannels -unitlessAnimationCurves false -hierarchy 0 -controlPoints 0 -shape 0;")
        elif operation == "deleteAnimationAll":
            mel.eval("delete -channels -unitlessAnimationCurves false  -hierarchy none -controlPoints 0 -shape 1;")

    def executeUI(self, arguments):
        """The option box execute methods for the joints marking menu. see execute() for main commands

        For this method to be called, in the JSON set "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "deleteStaticChannels":
            mel.eval("performDeleteStaticChannels true;")
        elif operation == "deleteAnimationAll":
            mel.eval("performDeleteChannels true;")
        elif operation == "deleteNonDeformerHistory":
            mel.eval("performBakeNonDefHistory true;")