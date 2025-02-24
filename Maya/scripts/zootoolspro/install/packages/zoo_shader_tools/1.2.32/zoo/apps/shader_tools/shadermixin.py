from zoo.apps.toolsetsui import toolsetui
from zoo.libs.maya.cmds.shaders.shdmultconstants import RENDERER_SHADERS_DICT


class ShaderMixin(object):
    """ Send/Receive all toolsets (Renderer and shader create)

    """

    def global_shaderUpdated(self):
        """Updates all GUIs with the current renderer"""
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveShaderUpdated")
        for tool in toolsets:
            tool.global_receiveShaderUpdated()

    # ------------------------------------
    # COPY PASTE - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    def global_sendCopyShader(self):
        """Updates all GUIs with the copied shader"""
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveCopiedShader")
        for tool in toolsets:
            tool.global_receiveCopiedShader(self.copiedShaderName, self.copiedAttributes)

    def global_receiveCopiedShader(self, copiedShaderName, copiedAttributes):
        """Receives the copied shader from other GUIs"""
        self.copiedShaderName = copiedShaderName
        self.copiedAttributes = copiedAttributes

    # ------------------------------------
    # SHADER TYPE UPDATED
    # ------------------------------------

    def global_shaderTypeUpdated(self):
        """Updates all GUIs with the current shader type"""
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveShaderType")
        for tool in toolsets:
            self.shaderTypesList = RENDERER_SHADERS_DICT[self.properties.rendererIconMenu.value]
            # sends an int from the combo box, the renderer should be changed first before the shader type.
            tool.global_receiveShaderType(self.properties.shaderTypeCombo.value)

    def global_receiveShaderType(self, comboIndex):
        """Receives the shadertype from other GUIs"""
        for widget in self.widgets():
            widget.shaderTypeCombo.setCurrentIndex(comboIndex)
