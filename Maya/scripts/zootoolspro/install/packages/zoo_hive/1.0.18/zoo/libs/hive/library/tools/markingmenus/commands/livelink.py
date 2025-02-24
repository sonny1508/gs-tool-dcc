from zoo.libs.maya.markingmenu import menu


class HiveLiveLink(menu.MarkingMenuCommand):
    id = "hiveLiveLink"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {"icon": "reload2",
                "bold": False,
                "italic": False,
                "optionBox": False,
                "checkBox": arguments.get("liveLink"),
                "label": "Toggle Live Link"
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """

        rigInstance = arguments.get("rig")
        liveLinkState = arguments.get("liveLink", False)
        rigInstance.setLiveLink(not liveLinkState)
