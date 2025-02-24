""" ---------- Convert Shaders -------------


"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.apps.shader_tools.shadermixin import ShaderMixin

from zoo.apps.toolsetsui.ext.renderers import RendererMixin
from zoo.libs.maya.cmds.shaders.shdmultconstants import RENDERER_SHADERS_DICT
from zoo.libs.maya.cmds.shaders import convertshaders
from zoo.libs.maya.cmds.renderer import rendererload

from zoo.libs.maya.cmds.renderer import rendererconstants

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ConvertShadersUI(toolsetwidget.ToolsetWidget, RendererMixin, ShaderMixin):
    id = "convertShaders"
    info = "Converts shaders to different types based on selection."
    uiData = {"label": "Convert Shaders (Multi-Renderer)",
              "icon": "shaderSwap",
              "tooltip": "Converts shaders to different types based on selection.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-convert-shaders/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.initRendererMixin()  # sets self.properties.rendererIconMenu.value

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]  # self.initAdvancedWidget()

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        self.advancedWidget = GuiAdvanced(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()
        self.updateShaderTypeList()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(ConvertShadersUI, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ConvertShadersUI, self).widgets()

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Needed to set self.properties.rendererIconMenu.value in the self.preContentSetup() """
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    # ------------------------------------
    # CHANGE RENDERER SHADER TYPE
    # ------------------------------------

    def updateShaderTypeList(self):
        """Updates the shaderTypeCombo on startup or when the renderer is changed

        Sets the list self.shaderTypesList
        """
        self.shaderTypesList = RENDERER_SHADERS_DICT[self.properties.rendererIconMenu.value]
        for widget in self.widgets():
            widget.shaderTypeCombo.clear()
            widget.shaderTypeCombo.addItems(self.shaderTypesList)

    def changeRenderer(self):
        """Run when the renderer is changed"""
        self.updateShaderTypeList()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def convertShaders(self):
        shaderType = self.shaderTypesList[self.properties.shaderTypeCombo.value]
        renderer = self.properties.rendererIconMenu.value
        if not rendererload.getRendererIsLoaded(renderer):  # the renderer is not loaded open window
            if not elements.checkRenderLoaded(renderer):
                return
        shadInsts = convertshaders.convertShaderSelection(convertToShaderType=shaderType,
                                                          removeShaders=self.properties.removeShadersCheckbox.value,
                                                          maintainConnections=True,
                                                          message=True)
        if shadInsts:  # convert was successful so change renderer to destination
            self.changeRenderer()
            self.global_shaderUpdated()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.convertShadersBtn.clicked.connect(self.convertShaders)
            widget.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)  # updates other UIs
            widget.rendererIconMenu.actionTriggered.connect(self.changeRenderer)
            widget.shaderTypeCombo.itemChanged.connect(self.global_shaderTypeUpdated)  # updates other UIs


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties

        # Remove Previous Shaders Checkbox ---------------------------------------
        self.removeShadersCheckbox = elements.CheckBox("Remove Previous Shaders", checked=True)
        # Shader Type Combo ---------------------------------------
        toolTip = "Select a shader type to convert to.  Change renderer with the renderer icon button. "
        self.shaderTypeCombo = elements.ComboBoxRegular(label="",
                                                        items=[],
                                                        parent=self,
                                                        toolTip=toolTip,
                                                        setIndex=0,
                                                        labelRatio=20,
                                                        boxRatio=55)  # is populated by the renderer
        # Renderer Button --------------------------------------
        toolTip = "While creating new shaders use either Arnold, Redshift or Renderman \n" \
                  "The button `Set Shaders` will ignore this setting and use existing shaders. "
        self.rendererIconMenu = elements.iconMenuButtonCombo(rendererconstants.RENDERER_ICONS_LIST,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)
        # Convert Shaders Button ---------------------------------------
        tooltip = "Select objects or shaders and run convert to a new shader type. \n" \
                  "Textures are not currently supported"
        self.convertShadersBtn = elements.styledButton("Convert Selected To Shader Type",
                                                       icon="shaderSwap",
                                                       toolTip=tooltip,
                                                       style=uic.BTN_DEFAULT)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # ShaderType Layout  ---------------------------------------
        typeLay = elements.hBoxLayout()
        typeLay.addWidget(self.shaderTypeCombo, 10)
        typeLay.addWidget(self.rendererIconMenu, 1)
        # Options Layout  ---------------------------------------
        optionsLay = elements.hBoxLayout()
        optionsLay.addWidget(self.removeShadersCheckbox, 10)
        optionsLay.addLayout(typeLay, 10)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(optionsLay)
        mainLayout.addWidget(self.convertShadersBtn)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.shaderTypeCombo)
        mainLayout.addWidget(self.convertShadersBtn)
