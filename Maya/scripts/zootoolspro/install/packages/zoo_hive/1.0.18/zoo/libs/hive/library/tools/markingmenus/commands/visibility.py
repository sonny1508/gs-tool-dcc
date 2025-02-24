from zoo.libs.maya.markingmenu import menu
from zoo.libs.utils import output
from zoo.core.util import zlogging
from maya import cmds

logger = zlogging.getLogger(__name__)


class ConstrainGuides(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveToggleDeformVisibility"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        uiData = {"icon": "connectionSRT",
                  "label": "Show Joints",
                  "bold": False,
                  "italic": False,
                  "optionBox": False,
                  "checkBox": False
                  }
        rig = arguments.get("rig")
        if not rig:
            output.displayWarning("Unable to detect hive rig from current selection")
            return uiData
        deform = rig.deformLayer()
        if deform:
            hidden = not deform.rootTransform().isHidden()
            uiData["checkBox"] = hidden
            arguments["hiddenState"] = not hidden
        return uiData

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        rig = arguments.get("rig")
        if not rig:
            output.displayWarning("Unable to detect hive rig from current selection")
            return
        deformLayer = rig.deformLayer()
        if deformLayer:
            cmds.setAttr(".".join((deformLayer.rootTransform().fullPathName(), "visibility")),
                         arguments.get("hiddenState", False))
        output.displayInfo("Completed switching display of the skeleton")
