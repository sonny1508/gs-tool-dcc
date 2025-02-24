from zoo.libs.hive.library.tools.markingmenus.menus import defaultguidemenu
from zoo.libs.hive.library.tools.markingmenus.menus import defaultanimmenu
from zoo.libs.maya.meta import base as metabase
from zoo.libs.hive import api


class FKChainGuideMenu(defaultguidemenu.BaseHiveGuideMM):
    id = "hiveFkChainGuideMenu"

    def execute(self, layout, arguments):
        layout = super(FKChainGuideMenu, self).execute(layout, arguments)
        if layout is None:
            return layout
        layout["sortOrder"] = 10
        # grab from the component registry as we have no idea where the component
        # would be.
        registry = api.Configuration().componentRegistry()
        fkCompObj = registry.findComponentByType("fkchain")
        for comp, nodes in arguments.get("componentToNodes", {}).items():
            if not isinstance(comp, fkCompObj):
                continue

            layout["items"]["generic"].insert(0, {
                "type": "command",
                "id": "hiveFkAddGuide",
                "arguments": arguments
            })
            layout["items"]["generic"].insert(1, {
                "type": "command",
                "id": "hiveFkSetParentGuide",
                "arguments": arguments
            })
            layout["items"]["generic"].insert(2, {
                "type": "separator",
            })
            break
        return layout


class FkChainAnimMenu(defaultanimmenu.BaseHiveAnimMM):
    """The Marking menu for all ikfk components ie. vchain/leg
    """
    id = "hiveFkChainAnimMenu"

    def spaceSwitchesForComponent(self, component, selectedNodes):
        """Generator function which return each space switch needed for the provided component.

        :param component: The component to get the space switch info from
        :type component: :class:`api.Component`
        :param selectedNodes: The current selected nodes determined by the marking menu internals
        :type selectedNodes: list[:class:`zapi.DagNode`]
        :return:
        :rtype: generate[dict]
        """
        rigLayer = component.rigLayer()
        switches = list(rigLayer.spaceSwitches())
        spaces = []
        for index, switch in enumerate(switches):
            controller = switch.controller()
            attr = controller["attr"]
            if not attr:
                continue
            spaceNode = switch.driven()
            metaNodes = metabase.getConnectedMetaNodes(spaceNode)  # type: list[metabase.MetaBase]
            if not metaNodes:
                return
            hiveLayer = metaNodes[0]  # type: api.HiveRigLayer
            # rigLayer class has the required api to get the control from a given srt node
            if not hiveLayer.isClassType(api.HiveRigLayer):
                continue
            controlNode = hiveLayer.controlForSrt(spaceNode)

            if controlNode not in selectedNodes:
                continue
            spaceIndex = attr.value()
            spaces.append({"label": "FK Space",
                           "controllerAttribute": attr,
                           "spaceNodes": spaceNode,
                           "componentName": component.name(),
                           "spaceIndex": spaceIndex,
                           "switch": switch,
                           "displayMenu": True})
        totalSpaces = len(spaces) - 1
        for index, spaceInfo in enumerate(spaces):
            spaceInfo["displayMenu"] = index == totalSpaces
            yield spaceInfo
