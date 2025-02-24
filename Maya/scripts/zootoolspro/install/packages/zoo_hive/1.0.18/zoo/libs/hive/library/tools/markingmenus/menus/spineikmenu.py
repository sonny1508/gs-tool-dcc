from zoo.libs.hive.library.tools.markingmenus.menus import defaultanimmenu
from zoo.libs.maya.meta import base as metabase
from zoo.libs.hive import api


class SpineIkAnimMenu(defaultanimmenu.BaseHiveAnimMM):
    """The Marking menu for spineIk component
    """
    id = "hiveSpineIkAnimMenu"

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
        spaces = {}
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
            spaceName = switch.controllerAttrName()

            if spaceName.endswith("rotSpace"):
                spaceName = "Rotate Space"
            elif spaceName.endswith("transSpace"):
                spaceName = "Translate Space"
            # temporary naming until we have a way to store marking menu with the space
            elif spaceName == "ctrl02_space":
                spaceName = "Parent Space"
            spaces[spaceName] = {"label": spaceName,
                                 "controllerAttribute": attr,
                                 "spaceNodes": spaceNode,
                                 "componentName": component.name(),
                                 "spaceIndex": spaceIndex,
                                 "switch": switch,
                                 "displayMenu": True}

        for spaceInfo in spaces.values():
            yield spaceInfo
