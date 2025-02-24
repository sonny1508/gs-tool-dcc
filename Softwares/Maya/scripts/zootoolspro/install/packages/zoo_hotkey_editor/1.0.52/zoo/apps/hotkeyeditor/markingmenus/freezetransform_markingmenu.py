import maya.mel as mel
from maya import cmds

from zoovendor import six
from zoo.core.util import classtypes

from zoo.libs.utils import output
from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.objutils import objhandling, matrix


@six.add_metaclass(classtypes.Singleton)
class ZooFreezeTransformTrackerSingleton(object):
    """Used by the freeze transform marking menu & UI, tracks the press and release
    """

    def __init__(self):
        self.markingMenuTriggered = False


TRACKER_INSTANCE = ZooFreezeTransformTrackerSingleton()


def secondaryFunction():
    """When the marking menu is released, run for a secondary feature

    Search for `MT_TRACKER_INST.markingMenuTriggered = True ` to see where the trigger is set to be True
    """
    if TRACKER_INSTANCE.markingMenuTriggered:  # Ignore if the menu was triggered
        TRACKER_INSTANCE.markingMenuTriggered = False
        return
    # Maya regular freeze transforms
    mel.eval("performFreezeTransformations(0)")


class FreezeTransformMarkingMenuCommand(menu.MarkingMenuCommand):
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
        definedhotkeys.freezeTransformMarkingMenuPress(alt=True, shift=False, ctrl=False)

    Map to hotkey release:

    .. code-block:: python

        from zoo.libs.maya.cmds.hotkeys import definedhotkeys
        definedhotkeys.freezeTransformMarkingMenuRelease()

    """
    id = "freezeTransformMarkingMenu"  # a unique identifier for a class, should never be changed
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
        freezeMessage = "Please select an object/s to freeze."
        operation = arguments.get("operation", "")
        if operation == "freezeTransformations":
            if not cmds.ls(selection=True):
                output.displayWarning(freezeMessage)
                return
            mel.eval('performFreezeTransformations(0)')
        elif operation == "freezeScale":
            if not cmds.ls(selection=True):
                output.displayWarning(freezeMessage)
                return
            cmds.makeIdentity(apply=True, translate=False, rotate=False, scale=True, jointOrient=False, n=False,
                              pn=True)
        elif operation == "unfreeze":
            if not cmds.ls(selection=True):
                output.displayWarning("Please select an object/s to unfreeze.")
                return
            objhandling.removeFreezeTransformSelected()
        elif operation == "freezeRotate":
            if not cmds.ls(selection=True):
                output.displayWarning(freezeMessage)
                return
            cmds.makeIdentity(apply=True, translate=False, rotate=True, scale=False, jointOrient=False, n=False,
                              pn=True)
        elif operation == "freezeMatrixModeller":
            matrix.zeroSrtModelMatrixSel()
        elif operation == "freezeMatrixAll":
            matrix.srtToMatrixOffsetSel()
        elif operation == "unfreezeMatrix":
            matrix.zeroMatrixOffsetSel()
        elif operation == "freezeTranslate":
            if not cmds.ls(selection=True):
                output.displayWarning(freezeMessage)
                return
            cmds.makeIdentity(apply=True, translate=True, rotate=False, scale=False, jointOrient=False, n=False,
                              pn=True)
        elif operation == "freezeJointOrient":
            if not cmds.ls(selection=True):
                output.displayWarning(freezeMessage)
                return
            cmds.makeIdentity(apply=True, translate=False, rotate=False, scale=False, jointOrient=True, n=False,
                              pn=True)

    def executeUI(self, arguments):
        """The option box execute methods for the joints marking menu. see execute() for main commands

        For this method to be called, in the JSON set "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "freezeTransformations":
            mel.eval('performFreezeTransformations 1')
