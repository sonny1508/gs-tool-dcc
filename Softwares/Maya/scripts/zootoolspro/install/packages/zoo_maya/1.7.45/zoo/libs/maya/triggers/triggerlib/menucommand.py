from operator import itemgetter
from maya import cmds
from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya import zapi
from zoo.libs.maya import markingmenu
from zoo.libs.maya.triggers import triggerbase
from zoo.libs.maya.utils import general
from zoo.core.util import zlogging
from zoo.libs.maya.triggers import triggercallbackutils


logger = zlogging.getLogger(__name__)

TOP_LEVEL_MENU_NAME = "zooTriggerMenu"


def removePrimaryMenu():
    markingmenu.removeExistingMenu(TOP_LEVEL_MENU_NAME)


class TriggerMenuCommand(triggerbase.TriggerCommand):
    id = "triggerMenu"

    # The maya attribute name which contains our menu plugin id
    COMMAND_ATTR_NAME = "zooTriggerMenuName"
    _OLD_COMMAND_ATTR_NAME = "zooTriggerString"

    def attributes(self):
        return [
            {"name": TriggerMenuCommand.COMMAND_ATTR_NAME, "Type": zapi.attrtypes.kMFnDataString,
             "isArray": False, "value": "",
             "locked": True}
        ]

    def menuId(self):
        """Returns the internal id of the marking menu layout.

        :return: The marking menu layout id.
        :rtype: str
        """
        attr = self._node.attribute(TriggerMenuCommand.COMMAND_ATTR_NAME)
        if attr is None:
            attr = self._node.attribute(TriggerMenuCommand._OLD_COMMAND_ATTR_NAME)
        if attr is None:
            return ""
        return attr.value()

    def setMenu(self, menuId, mod=None):
        """Set's the current menu layout id for this command on the node.

        :param menuId: The marking menu layout id
        :type menuId: str
        :param mod: The modifier to use for undo.
        :type mod: :class:`zapi.dgModifier`
        """
        if not markingmenu.Registry().hasMenu(menuId):
            raise markingmenu.MissingMarkingMenu("No marking menu registered in system: {}".format(menuId))
        attr = self._node.attribute(TriggerMenuCommand.COMMAND_ATTR_NAME)
        try:
            attr.lock(False)
            attr.set(menuId, mod=mod)
        finally:
            attr.lock(True)

    def execute(self, arguments):
        """This method loads the marking menu layout for the command, if the layout is off dynamic then
        the class will be executed other the static layout will be loaded.

        :param arguments: The arguments to pass to the marking menu class if this command is dynamic.
        :type arguments: dict
        :return: The consolidate unsolved marking menu layout.
        :rtype: :class:`markingmenu.Layout`
        """
        menuId = self.menuId()
        if not menuId:
            return markingmenu.Layout()
        registry = markingmenu.Registry()
        menuType = registry.menuType(menuId)
        layout = markingmenu.Layout(**{"items": {}})
        if menuType == registry.STATIC_LAYOUT_TYPE:
            newLayout = markingmenu.findLayout(menuId)
        else:
            menuPlugin = registry.menuRegistry.loadPlugin(menuId)
            newLayout = menuPlugin.execute(layout, arguments=arguments)
            layout.merge(newLayout)
        if newLayout:
            layout = newLayout

        return layout


@general.undoDecorator
@triggercallbackutils.blockSelectionCallbackDecorator
def buildTriggerMenu(parentMenu, nodeName):
    """Internal method to Build and display the trigger menu for the specified node by name.

    :param parentMenu: The maya parent menu name.
    :type parentMenu: str
    :param nodeName: The initial node(under the mouse pointer), can be None we consolidate the \
    currently selected nodes.

    :type nodeName: str or None
    :return: If the menu was successfully built.
    :rtype: bool
    """
    contextInfo = gatherMenusFromNodes(nodeName)
    if not contextInfo:
        return 0
    layout = contextInfo["layout"]
    overrides = False

    if layout:
        # cancel the custom menu if nothing in the layout is even valid
        if not layout.solve():
            return overrides
        menu.MarkingMenu.buildFromLayoutData(layout, TOP_LEVEL_MENU_NAME, parentMenu, options={},
                                             arguments={"nodes": contextInfo["nodes"]})
        overrides = True
    return overrides


def gatherMenusFromNodes(nodeName=None):
    """Internal function which gets called by :func:`buildTriggerMenu` which returns the current
    selected nodes and the final composed(unSolved) trigger menu layout.

    :note: This function is the one that executes the trigger commands.
    :param nodeName: The maya path to the scene node to find the initial trigger on
    :type nodeName: str or None
    :return:
    :rtype:
    """
    nodeName = nodeName or ""
    selectedNodes = list(zapi.selected())
    # if the node name exist, insert to the front of the selected.
    # We append to the front because the trigger priority is selection order
    if cmds.objExists(nodeName):
        triggerNode = zapi.nodeByName(nodeName)
        if triggerNode not in selectedNodes:
            selectedNodes.insert(0, triggerNode)
    if not selectedNodes:
        return {}
    # reverse in place so the last(first selected) acts as the priority
    # selectedNodes.reverse()
    # gather the trigger information from the current node and the selection
    triggerNodes = triggerbase.connectedTriggerNodes(selectedNodes, filterCls=TriggerMenuCommand)
    if not triggerNodes:
        return {}
    layouts = []
    visited = set()
    for menuNode in triggerNodes:
        trigger = triggerbase.TriggerNode.fromNode(menuNode)
        cmd = trigger.command()  # type: TriggerMenuCommand
        # ignore any triggers which have the same command id as we don't need to build
        # the same menu multiple times
        menuId = cmd.menuId()
        if menuId in visited or not menuId:
            continue
        visited.add(menuId)
        layout = cmd.execute({"nodes": selectedNodes})
        layouts.append(layout)
    if not layouts:
        return {}

    layouts.sort(key=itemgetter("sortOrder"), reverse=True)
    # merge(flatten) by sort order, this will merge all layouts into the first layout
    # reduce(stdgeneral.merge, [layout["items"] for layout in layouts])

    return {
        "nodes": selectedNodes,
        "layout": layouts[-1],
    }


def buildMenuFromSelection():
    """Builds and displays the marking menu for the current selected nodes.

    :return: 1 if the selected displayed a marking menu else 0.
    :rtype: int
    """
    panel = cmds.getPanel(withFocus=True)
    if not panel:
        logger.warning("No Maya Panel is currently in focus, aborting MarkingMenu gen")
        return 0
    return buildTriggerMenu(panel, None)
