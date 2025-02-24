from zoo.libs.maya.markingmenu import menu
from zoo.core.util import zlogging
from zoo.libs.commands import hive
from zoo.libs.maya.cmds.animation import timerange
from zoo.libs.maya.utils import general

logger = zlogging.getLogger(__name__)


class HiveIKFKSwitch(menu.MarkingMenuCommand):
    id = "hiveIKFKSwitch"
    creator = "Zootools"
    _ikfkStates = {
        0: "IK",
        1: "FK"
    }

    @staticmethod
    def uiData(arguments):
        info = {"icon": "axis",
                "bold": False,
                "italic": False,
                "optionBox": False,
                }
        label = ""
        for component in arguments["components"]:
            if not hasattr(component, "hasIkFk"):
                continue
            panel = component.controlPanel()
            ikfkState = panel.attribute("ikfk").value()
            label = "{} Current Frame".format(HiveIKFKSwitch._ikfkStates[int(not ikfkState)])
            arguments["switchIndex"] = int(not ikfkState)
            break
        if not label:
            info["show"] = False
        info["label"] = label
        return info

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        hive.matchIKFK(arguments["components"], arguments["switchIndex"])


class HiveIKFKSwitchBakeRange(menu.MarkingMenuCommand):
    id = "hiveIKFKSwitchBakeRange"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        info = {"icon": "bake",
                "bold": False,
                "italic": False,
                "optionBox": False,
                }
        label = ""
        for component in arguments["components"]:
            if not hasattr(component, "hasIkFk"):
                continue
            panel = component.controlPanel()
            ikfkState = panel.attribute("ikfk").value()
            label = "{} Bake Timeline".format(HiveIKFKSwitch._ikfkStates[int(not ikfkState)])
            arguments["switchIndex"] = int(not ikfkState)
            break
        if not label:
            info["show"] = False
        info["label"] = label
        return info

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """

        frameRange = list(map(int, timerange.getSelectedOrCurrentFrameRange()))
        hive.matchIKFK(arguments["components"], arguments["switchIndex"], frameRange=frameRange)


class HiveIKFKSwitchKeys(menu.MarkingMenuCommand):
    id = "hiveIKFKSwitchKeys"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        info = {"icon": "key",
                "bold": False,
                "italic": False,
                "optionBox": False,
                }
        label = ""
        for component in arguments["components"]:
            if not hasattr(component, "hasIkFk"):
                continue
            panel = component.controlPanel()
            ikfkState = panel.attribute("ikfk").value()
            label = "{} Keys Timeline".format(HiveIKFKSwitch._ikfkStates[int(not ikfkState)])
            arguments["switchIndex"] = int(not ikfkState)
            break
        if not label:
            info["show"] = False
        info["label"] = label
        return info

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """

        frameRange = list(map(int, timerange.getSelectedOrCurrentFrameRange()))
        hive.matchIKFK(arguments["components"], arguments["switchIndex"], frameRange=frameRange, bakeEveryFrame=False)


class HiveFixFkRotation(menu.MarkingMenuCommand):
    id = "hiveFixFkRotation"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        info = {"icon": "componentVChain",
                "bold": False,
                "italic": False,
                "optionBox": False,
                }
        label = ""
        for component in arguments["components"]:
            if not hasattr(component, "hasIkFk"):
                continue
            if component.controlPanel().attribute("ikfk").value() != 1:
                continue
            rigLayer = component.rigLayer()
            rot = rigLayer.control("midfk").rotation(asQuaternion=False)
            valuesNotZero = 0
            for value in rot:
                if abs(value) != 0.0:
                    valuesNotZero += 1
            if valuesNotZero > 1:
                label = component.fixMidJointMMLabel
                break

        if not label:
            info["show"] = False
        info["label"] = label

        return info

    def execute(self, arguments):
        with general.maintainSelectionContext():
            hive.matchIKFK(arguments["components"], state=False)
            hive.matchIKFK(arguments["components"], state=True)


class HiveRecalculatePoleVector(menu.MarkingMenuCommand):
    id = "hiveRecalculatePoleVector"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        info = {"icon": "axis",
                "bold": False,
                "italic": False,
                "optionBox": False,
                }
        label = ""
        for component in arguments["components"]:
            if not hasattr(component, "hasIkFk"):
                continue
            label = "Current Frame"
            break
        if not label:
            info["show"] = False
        info["label"] = label
        return info

    def execute(self, arguments):
        hive.recalculatePoleVector(arguments["components"])


class HiveRecalculatePoleVectorBakeRange(menu.MarkingMenuCommand):
    id = "hiveRecalculatePoleVectorBakeRange"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        info = {"icon": "bake",
                "bold": False,
                "italic": False,
                "optionBox": False,
                }
        label = ""
        for component in arguments["components"]:
            if not hasattr(component, "hasIkFk"):
                continue
            label = "Bake Timeline"
            break
        if not label:
            info["show"] = False
        info["label"] = label
        return info

    def execute(self, arguments):
        frameRange = list(map(int, timerange.getSelectedOrCurrentFrameRange()))
        hive.recalculatePoleVector(arguments["components"], frameRange=frameRange, bakeEveryFrame=True)


class HiveRecalculatePoleVectorKeys(menu.MarkingMenuCommand):
    id = "hiveRecalculatePoleVectorKeys"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        info = {"icon": "key",
                "bold": False,
                "italic": False,
                "optionBox": False,
                }
        label = ""
        for component in arguments["components"]:
            if not hasattr(component, "hasIkFk"):
                continue
            label = "Keys Timeline"
            break
        if not label:
            info["show"] = False
        info["label"] = label
        return info

    def execute(self, arguments):
        frameRange = list(map(int, timerange.getSelectedOrCurrentFrameRange()))
        hive.recalculatePoleVector(arguments["components"], frameRange=frameRange, bakeEveryFrame=False)
