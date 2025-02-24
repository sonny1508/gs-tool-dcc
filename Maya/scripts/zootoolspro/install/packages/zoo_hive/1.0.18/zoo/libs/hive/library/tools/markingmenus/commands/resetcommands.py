from zoo.libs.maya.markingmenu import menu
from zoo.core.util import zlogging
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.animation import resetattrs

logger = zlogging.getLogger(__name__)


def childControlsFromNodes(nodes):
    controls = []
    for n in nodes:
        for destinationNode in n.message.destinationNodes():
            if destinationNode.object().hasFn(zapi.kNodeTypes.kControllerTag):
                controls.extend(_childControls(destinationNode))
    return controls


def _childControls(tag):
    controls = []
    for child in tag.children:
        subChild = child.sourceNode()
        if not subChild:
            continue
        node = subChild.controllerObject.sourceNode()
        if node:
            controls.append(node.fullPathName())
        controls.extend(_childControls(subChild))
    return controls


class HiveResetTransformBelow(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveResetTransformBelow"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {"icon": "reload2",
                "bold": False,
                "italic": False,
                "optionBox": False,
                "label": "Reset All Below"
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        controls = childControlsFromNodes(arguments["nodes"])
        for component in arguments["components"]:
            for child in component.children():
                rigLayer = child.rigLayer()
                for ctrl in rigLayer.iterControls():
                    if ctrl not in controls:
                        controls.append(ctrl.fullPathName())
                controls.append(rigLayer.controlPanel().fullPathName())
        resetattrs.resetNodes(controls, skipVisibility=True, message=False)


class HiveResetTransform(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveResetTransform"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {"icon": "reload2",
                "bold": False,
                "italic": False,
                "optionBox": False,
                "label": "Reset"
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        controls = [i.fullPathName() for i in arguments["nodes"]]
        for component in arguments["components"]:
            rigLayer = component.rigLayer()
            controls.append(rigLayer.controlPanel().fullPathName())
        resetattrs.resetNodes(controls, skipVisibility=True, message=False)
