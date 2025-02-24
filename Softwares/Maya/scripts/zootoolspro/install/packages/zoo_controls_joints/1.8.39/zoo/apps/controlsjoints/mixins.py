from zoo.apps.toolsetsui import toolsetui


class ControlsJointsMixin(object):
    def global_sendCntrlSelection(self):
        """Updates all GUIs with the current selection memory self.selObjs"""
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveCntrlSelection")  # type: list[ControlsJointsMixin]
        for tool in toolsets:
            tool.global_receiveCntrlSelection(self.selObjs)

    def global_receiveCntrlSelection(self, selObjs):
        """Receives from all GUIs, changes the current selection stored in self.selObjs"""
        self.selObjs = selObjs

    def global_receiveCntrlColor(self, color):
        """Receives from all GUIs, changes the color"""
        self.properties.color.value = color
        self.updateFromProperties()

    def global_sendCntrlColor(self):
        """Updates all GUIs with the current color"""
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveCntrlColor")
        for tool in toolsets:
            tool.global_receiveCntrlColor(self.properties.color.value)