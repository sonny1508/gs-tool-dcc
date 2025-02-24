import maya.mel as mel

from zoo.apps.toolsetsui.run import openToolset
from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.modeling import subdivisions

SD_TRACKER_INST = subdivisions.ZooSubDTrackerSingleton()


def secondaryFunction():
    """When the marking menu is released, run for a secondary feature

    Search for `MT_TRACKER_INST.markingMenuTriggered = True ` to see where the trigger is set to be True
    """
    if SD_TRACKER_INST.markingMenuTriggered:  # Ignore if the menu was triggered
        SD_TRACKER_INST.markingMenuTriggered = False
        return
    subdivisions.toggleSubDsSel()


class SubDMarkingMenuCommand(menu.MarkingMenuCommand):
    """

    """
    id = "subDMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        """This method is mostly over ridden by the associated json file"""
        SD_TRACKER_INST.markingMenuTriggered = True
        return {"icon": "",
                "label": "",
                "bold": False,
                "italic": False,
                "optionBox": False,
                "optionBoxIcon": ""
                }

    def execute(self, arguments):
        """The main execute methods for the skinning marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        operation = arguments.get("operation", "")

        if operation == "subDOff":
            subdivisions.setSubDMode(value=0)
        elif operation == "subDHull":
            subdivisions.setSubDMode(value=1)
        elif operation == "subDOn":
            subdivisions.setSubDMode(value=2)
        elif operation == "openSubDSmoothControl":
            openToolset("subDSmoothControl")
        elif operation == "polySmooth":
            mel.eval("performPolySmooth 0; toggleSelMode; toggleSelMode; select - addFirst polySmoothFace1;")
