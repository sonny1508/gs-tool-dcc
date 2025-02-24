from zoo.libs.hive import api
from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.api import constants
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.animation import generalanimation
from zoo.core.util import zlogging
from zoo.core.util import strutils
from zoo.libs.hive.library.tools.toolui import markingmenutils

logger = zlogging.getLogger(__name__)


class BaseHiveAnimMM(menu.MarkingMenuDynamic):
    id = "hiveDefaultAnimMenu"

    def _applyHiveContextToArguments(self, arguments):
        """Get component from marking menu arguments

        :type arguments: generator[:class:`api.Component`]
        """
        arguments["nodes"] = [
            i for i in arguments["nodes"] if i.hasFn(zapi.kNodeTypes.kDagNode)
        ]
        try:
            components = api.componentsFromNodes(arguments["nodes"])
        except Exception:
            markingmenutils.logUnableToLoadComponentsMM()
            return None, None
        componentInstances = list(components.keys())
        rig = None
        if componentInstances:
            rig = componentInstances[0].rig
        arguments["rig"] = rig
        arguments["components"] = componentInstances
        arguments["componentToNodes"] = components
        return componentInstances, rig

    def spaceSwitchesForComponent(self, component, selectedNodes):
        rigLayer = component.rigLayer()
        switches = rigLayer.spaceSwitches()
        for switch in switches:
            controller = switch.controller()
            attr = controller["attr"]
            if not attr:
                continue
            spaceIndex = attr.value()
            attrName = attr.partialName()
            yield {
                "label": attrName,
                "controllerAttribute": attr,
                "spaceNodes": switch.driven(),
                "componentName": component.name(),
                "spaceIndex": spaceIndex,
                "switch": switch,
                "displayMenu": True,
            }

    def _findSpaceSwitches(self, components, selectedNodes):
        """
        :param components:
        :type components: list[:class:`api.Component`]
        :return:
        :rtype: list[dict]
        """
        spacesMenu = []
        # common set of space switches by combining the same space. We use the first component as the primary
        # state value
        # {"upVec": {
        #     "spaceNodes": [],
        #     "controllerAttrs": [],
        #     "currentSpaceIndex": 0,
        #     "menuItems": {"fieldName": {"radioButtonState": 0,
        #                    "index": 0
        #                    }}
        # }}
        combinedSpaces = {}  # space: {}
        lastComponentIndex = len(components) - 1

        # loop through the components sorting out unique shared spaces and collect space state
        for componentIndex, component in enumerate(components):
            for spaceInfo in self.spaceSwitchesForComponent(component, selectedNodes):
                label = spaceInfo["label"]
                switch = spaceInfo["switch"]
                spaceIndex = spaceInfo["spaceIndex"]
                currentEntry = combinedSpaces.setdefault(label, {})
                currentEntry.setdefault("controllerAttributes", []).append(
                    spaceInfo["controllerAttribute"]
                )
                currentEntry.setdefault("spaceNodes", []).append(switch.driven())
                if not currentEntry:
                    currentEntry["currentSpaceIndex"] = spaceInfo["currentSpaceIndex"]

                if componentIndex == lastComponentIndex and spaceInfo["displayMenu"]:
                    for index, driver in enumerate(switch.drivers()):
                        driverLabel, driverNode = driver
                        if driverLabel not in currentEntry.get("menuItems", {}):
                            currentEntry.setdefault("menuItems", {})[driverLabel] = {
                                "radioButtonState": index == spaceIndex,
                                "index": index,
                            }

        # now generate the menu items
        for spaceAttrName, info in combinedSpaces.items():
            children = []
            attrs = info["controllerAttributes"]
            menuLabel = strutils.titleCase(spaceAttrName)

            nodes = info["spaceNodes"]
            for field, fieldInfo in info.get("menuItems", {}).items():
                fieldInfo["type"] = "menu"
                fieldInfo["label"] = strutils.titleCase(field)
                fieldInfo["children"] = [
                    {
                        "type": "command",
                        "id": "hiveSpaceSwitch",
                        "label": "Current Frame",
                        "arguments": {
                            "controllerAttributes": attrs,
                            "spaceNodes": nodes,
                            "index": fieldInfo["index"],
                        },
                    },
                    {
                        "type": "command",
                        "id": "hiveSpaceSwitchBake",
                        "label": "Keys Timeline",
                        "arguments": {
                            "controllerAttributes": attrs,
                            "spaceNodes": nodes,
                            "index": fieldInfo["index"],
                            "bakeEveryFrame": False,
                        },
                    },
                    {
                        "type": "command",
                        "id": "hiveSpaceSwitchBake",
                        "label": "Bake Timeline",
                        "arguments": {
                            "controllerAttributes": attrs,
                            "spaceNodes": nodes,
                            "index": fieldInfo["index"],
                            "bakeEveryFrame": True,
                        },
                    },
                ]

                children.append(fieldInfo)

            if children:
                spacesMenu.append(
                    {
                        "type": "menu",
                        "label": menuLabel,
                        "children": children,
                    }
                )
        return spacesMenu

    def _createRotationOrderMenus(self, arguments):
        menus = {"type": "menu", "label": "Change Rotation Order"}
        children = [
            {
                "type": "command",
                "id": "hiveOpenChangeRotationOrderToolset",
                "icon": "rotateManipulator",
            },
            {"type": "separator"},
        ]
        nodes = arguments["nodes"]

        values = generalanimation.allGimbalTolerancesForKeys(
            nodes[-1], currentFrameRange=True, message=False
        )

        labels = generalanimation.gimbalTolerancesToLabels(values)

        for index, order in enumerate(constants.kRotateOrders):
            children.append(
                {
                    "type": "command",
                    "id": "hiveRotationOrderBake",
                    "label": labels[index],
                    "arguments": {"nodes": arguments["nodes"], "rotationOrder": order},
                }
            )
        menus["children"] = children
        result = [{"type": "separator"}, menus, {"type": "separator"}]
        return result

    def execute(self, layout, arguments):
        components, rig = self._applyHiveContextToArguments(arguments)
        if components is None or rig is None:
            return layout
        generic = self._findSpaceSwitches(components, arguments.get("nodes"))
        generic.extend(self._createMirrorMenu(arguments))

        generic.extend(self._createSelectionActions(arguments))
        generic.extend(self._createRotationOrderMenus(arguments))
        generic.extend(
            [
                {"type": "separator"},
                {"type": "command", "id": "hiveResetTransform", "arguments": arguments},
                {
                    "type": "command",
                    "id": "hiveResetTransformBelow",
                    "arguments": arguments,
                },
            ]
        )

        if rig.configuration.useContainers:
            generic.append(
                {
                    "type": "menu",
                    "label": "Display",
                    "children": [
                        {
                            "type": "command",
                            "id": "hiveToggleBlackBox",
                            "arguments": arguments,
                        },
                        {
                            "type": "command",
                            "id": "hiveToggleDeformVisibility",
                            "arguments": arguments,
                        },
                    ],
                }
            )
        else:
            generic.append(
                {
                    "type": "menu",
                    "label": "Display",
                    "children": [
                        {
                            "type": "command",
                            "id": "hiveToggleDeformVisibility",
                            "arguments": arguments,
                        }
                    ],
                }
            )
        layout["items"] = {"generic": generic}
        return layout

    def _createSelectionActions(self, arguments):
        return [
            {
                "type": "separator",
            },
            {
                "type": "command",
                "id": "hiveSelectRigRootControl",
                "label": "Select Rig Root Control",
                "arguments": arguments,
            },
            {
                "type": "command",
                "id": "hiveSelectChildControls",
                "label": "Select Child Controls",
                "arguments": arguments,
            },
            {
                "type": "command",
                "id": "hiveSelectAllControls",
                "label": "Select All Controls",
                "arguments": arguments,
            },
            {
                "type": "separator",
            },
        ]

    def _createMirrorMenu(self, arguments):
        children = [
            {
                "type": "command",
                "id": "hiveAnimMirror",
                "label": "Mirror Pose",
                "arguments": {"animation": 0},
                "icon": "mirrorGeo",
            },
            {
                "type": "command",
                "id": "hiveAnimMirror",
                "label": "Mirror Animation",
                "arguments": {"animation": 1},
                "icon": "mirrorGeo",
            },
            {
                "type": "command",
                "id": "hiveAnimFlipMirror",
                "label": "Flip Mirror Pose",
                "arguments": {"animation": 0},
                "icon": "symmetryTri",
            },
            {
                "type": "command",
                "id": "hiveAnimFlipMirror",
                "label": "Flip Mirror Animation",
                "arguments": {"animation": 1},
                "icon": "symmetryTri",
            },
            {
                "type": "command",
                "id": "hiveOpenMirrorWindow",
                "label": "Open Mirror Flip UI",
                "icon": "window",
            },
        ]
        return [
            {
                "type": "separator",
            },
            {"type": "menu", "label": "Mirror", "children": children},
            {
                "type": "separator",
            },
        ]
