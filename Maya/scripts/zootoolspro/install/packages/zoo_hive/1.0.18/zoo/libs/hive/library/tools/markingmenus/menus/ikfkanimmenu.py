from zoo.libs.hive.library.tools.markingmenus.menus import defaultanimmenu


class IKFKAnimMenu(defaultanimmenu.BaseHiveAnimMM):
    """The Marking menu for all ikfk components ie. vchain/leg
    """
    id = "hiveIKFKAnimMenu"

    def spaceSwitchesForComponent(self, component, selectedNodes):
        rigLayer = component.rigLayer()
        switches = rigLayer.spaceSwitches()
        panel = component.controlPanel()
        ikfk = panel.attribute("ikfk")
        if ikfk is None:
            return
        ikfkState = ikfk.value()
        allowedSpaces = ("ikSpace", "poleVectorSpace") if ikfkState == 0 else ("fkSpace", )
        for switch in switches:
            controller = switch.controller()
            attr = controller["attr"]
            if not attr:
                continue
            spaceIndex = attr.value()
            attrName = attr.partialName()
            if attrName not in allowedSpaces:
                continue
            yield {"label": attrName,
                   "controllerAttribute": attr,
                   "spaceNodes": switch.driven(),
                   "componentName": component.name(),
                   "spaceIndex": spaceIndex,
                   "switch": switch,
                   "displayMenu": True}

    def execute(self, layout, arguments):
        layout = super(IKFKAnimMenu, self).execute(layout, arguments)
        if not layout["items"]:
            return layout
        menus = {
            "type": "menu",
            "label": "IK FK Match",
            "children": [
                {
                    "type": "command",
                    "id": "hiveIKFKSwitch",
                    "arguments": arguments
                },
                {
                    "type": "command",
                    "id": "hiveIKFKSwitchKeys",
                    "arguments": arguments
                },
                {
                    "type": "command",
                    "id": "hiveIKFKSwitchBakeRange",
                    "arguments": arguments
                }

            ]
        }
        layout["items"]["generic"].insert(0, menus)
        layout["items"]["generic"].insert(1, {"type": "command", "id": "hiveFixFkRotation", "arguments": arguments})
        layout["items"]["generic"].insert(2, {
            "type": "separator"
        })
        poleVectorMenu = {
            "type": "menu",
            "label": "Place Pole Vector Sensibly",
            "children": [
                {
                    "type": "command",
                    "id": "hiveRecalculatePoleVector",
                    "arguments": arguments
                },
                {
                    "type": "command",
                    "id": "hiveRecalculatePoleVectorKeys",
                    "arguments": arguments
                },
                {
                    "type": "command",
                    "id": "hiveRecalculatePoleVectorBakeRange",
                    "arguments": arguments
                }
            ]
        }

        layout["items"]["generic"].insert(3, poleVectorMenu)
        layout["items"]["generic"].insert(4, {
            "type": "separator"
        })
        return layout
