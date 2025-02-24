from zoo.libs.maya import zapi
from zoo.libs.maya.markingmenu import menu
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class DynamicMMBySelectionExample(menu.MarkingMenuDynamic):
    """Example Class for dynamically creating marking menus.
    """
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "dynamicMMBySelectionExample"

    def execute(self, layout, arguments):
        """Example override creating a linear menu with passing arguments down to the MMCommands.

        :param layout: The layout instance to update.
        :type layout: :class:`menu.Layout`
        """
        # grab the nodes value which comes from the marking menu executor
        selNodes = arguments.get("nodes", list(zapi.selected()))
        if not selNodes:
            return layout
        arguments["nodes"] = selNodes
        logArgs = dict(arguments)
        logArgs["operation"] = "log"
        # build a dict which contains our commands
        # each command must be specified in the format of {"type": "command", "id": "mycommandid"}
        items = {"N": {
            "type": "command",
            "id": "printNodePath",
            "arguments": logArgs
        },
            "generic": [
                {
                    "type": "command",
                    "id": "printNodePath",
                    "arguments": arguments
                }
            ]}

        # finally update the layout object
        layout["items"] = items
        # ensure the layout has been solved to contain our commands
        return layout


class PrintNodePath(menu.MarkingMenuCommand):
    """Example Command class which demonstrates how to dynamically change the UI Label and to have
    a UI.
    Specifying a Docstring for the class will act as the tooltip.
    """
    # a unique identifier for a class, once released to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "printNodePath"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        op = arguments.get("operation")
        return {"icon": "eye",
                "label": "log" if op else "print",
                "bold": False,
                "italic": True,
                "optionBox": True,
                "optionBoxIcon": "eye"
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        currentNodes = arguments.get("nodes")
        if operation == "print":
            for n in currentNodes:
                print(n.fullPathName())

        elif operation == "log":
            for n in currentNodes:
                logger.info(n.fullPathName())
        else:
            for n in currentNodes:
                print(n)

    def executeUI(self, arguments):
        """The executeUI method is called when the user triggering the box icon on the right handle side
        of the action item.

        For this method to be called you must specify in the UIData method "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "print":
            currentNodes = arguments.get("nodes")
            for n in currentNodes:
                print(n.fullPathName())
