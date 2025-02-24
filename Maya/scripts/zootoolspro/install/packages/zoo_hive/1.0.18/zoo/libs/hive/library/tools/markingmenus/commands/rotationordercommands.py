from zoo.libs.maya.markingmenu import menu
from zoo.libs.utils import output
from zoo.core.util import zlogging
from zoo.libs.maya import zapi
from zoo.libs.maya.api import constants


logger = zlogging.getLogger(__name__)


class RotationOrderbake(menu.MarkingMenuCommand):
    id = "hiveRotationOrderBake"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        rotationOrder = arguments["rotationOrder"]
        nodes = arguments.get("nodes", [])
        bold = False
        if any(n.rotationOrder() == rotationOrder for n in nodes):
            bold = True
        rotationOrder = constants.kRotateOrderNames[rotationOrder].upper()
        uiData = {"label": "Set Rotation Order to {}".format(rotationOrder),
                  "bold": bold,
                  "italic": False,
                  "optionBox": False,
                  }
        return uiData

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        nodes = arguments.get("nodes")
        zapi.setRotationOrderOverFrames(nodes, arguments["rotationOrder"])
        output.displayInfo("Completed switching display of the skeleton")


class HiveOpenRotationOrderUI(menu.MarkingMenuCommand):
    id = "hiveOpenChangeRotationOrderToolset"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        uiData = {"label": "Change Rotate Options",
                  "bold": False,
                  "italic": False,
                  "optionBox": False,
                  }
        return uiData

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        from zoo.apps.toolsetsui import run
        run.openToolset("rotationOrder")
