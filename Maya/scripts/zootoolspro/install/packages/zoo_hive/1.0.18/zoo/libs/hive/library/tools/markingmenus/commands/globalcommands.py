from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.qt import mayaui
from zoo.libs.utils import output
from zoo.libs.commands import hive


class ToggleBlackBox(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveToggleBlackBox"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        uiData = {"icon": "blackBox",
                  "label": "BlackBox",
                  "bold": False,
                  "italic": False,
                  "optionBox": False,
                  "checkBox": False
                  }
        components = arguments.get("components")
        for comp in components:
            if comp.blackBox:
                uiData["checkBox"] = True
                break
        return uiData

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        rig = arguments.get("rig")
        comps = rig.components()
        if not comps:
            return
        hive.toggleBlackBox(comps, save=True)
        # required for the outliner to reflect the state change as it's not automatic
        mayaui.refreshOutliners()
        output.displayInfo("Toggled blackbox")


class DeleteSelectedComponent(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveDeleteComponent"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {"icon": "trash",
                "label": "Delete",
                "bold": False,
                "italic": False,
                "optionBox": False
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        comps = arguments.get("components")
        rig = arguments.get("rig")
        compMessageName = ",".join("_".join([comp.name(), comp.side()]) for comp in comps)
        hive.deleteComponents(rig, comps, children=True)
        output.displayInfo("Completed deleting components: {}".format(compMessageName))


class PolishRigComponent(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hivePolishRig"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {"icon": "publishRig",
                "label": "Polish Rig",
                "bold": False,
                "italic": False,
                "optionBox": False
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """

        rig = arguments.get("rig")
        hive.polishRig(rig)
        output.displayInfo("Completed deleting components: {}".format(rig.name()))
