from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya import zapi
from zoo.core.util import zlogging
from maya import cmds

logger = zlogging.getLogger(__name__)


class HiveSelectRigRootControl(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveSelectRigRootControl"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {"icon": "cursorSelect",
                "bold": False,
                "italic": False,
                "optionBox": False
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        controls = []
        for component in arguments["rig"].components():
            if component.parent():
                continue
            for control in component.rigLayer().iterControls():
                controls.append(control)
                break
        cmds.select([i.fullPathName() for i in controls])


class HiveSelectChildControls(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveSelectChildControls"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {"icon": "cursorSelect",
                "bold": False,
                "italic": False,
                "optionBox": False
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        nodes = arguments["nodes"]
        controls = []
        for n in nodes:
            for destinationNode in n.message.destinationNodes():
                if destinationNode.object().hasFn(zapi.kNodeTypes.kControllerTag):
                    controls.extend(self._childControls(destinationNode))
        cmds.select(controls)

    def _childControls(self, tag):
        controls = []
        node = tag.controllerObject.sourceNode()
        if node is not None:
            controls.append(node)
        for child in tag.children:
            subChild = child.sourceNode()
            if not subChild:
                continue
            controls.extend(self._childControls(subChild))
        return controls


class HiveSelectAllControls(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveSelectAllControls"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {"icon": "cursorSelect",
                "bold": False,
                "italic": False,
                "optionBox": False
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        controls = []

        for component in arguments["rig"].iterComponents():
            controls.extend(list(component.rigLayer().iterControls()))
        cmds.select([i.fullPathName() for i in controls])
