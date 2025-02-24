from zoo.libs.maya.qt.changerendererui import globalChangeRenderer
from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output

from zoo.preferences.interfaces import coreinterfaces

from zoo.libs.maya.cmds.renderer import rendererload, exportabcshaderlights
from zoo.libs.maya.cmds.renderer import rendererconstants


from zoo.apps.toolsetsui import toolsetui

RENDERER_NICE_NAMES = rendererconstants.RENDERER_NICE_NAMES

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ConvertRenderer(toolsetwidget.ToolsetWidget):
    id = "convertRenderer"
    info = "Template file for building new GUIs."
    uiData = {"label": "Convert Renderer (Multi-Renderer)",
              "icon": "convertRenderer",
              "tooltip": "Template file for building new GUIs.",
              "helpUrl": "https://create3dcharacters.com/maya-tool-convert-renderer/",
              "defaultActionDoubleClick": False}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.toolsetWidget = self  # needed for callback decorators and resizer
        self.generalPrefs = coreinterfaces.generalInterface()
        self.renderer = self.generalPrefs.primaryRenderer()
        if self.renderer == rendererconstants.VRAY:
            self.renderer = rendererconstants.ARNOLD
        if self.renderer == rendererconstants.MAYA:
            self.renderer = rendererconstants.ARNOLD

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.updateComboUI()  # updates the combos to be the current renderer and next in the list
        self.uiConnections()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype: GuiWidgets
        """
        return super(ConvertRenderer, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        super(ConvertRenderer, self).widgets()

    # ------------------------------------
    # SEND/RECEIVE ALL TOOLSETS (RENDERER AND SHADER CREATE)
    # ------------------------------------

    def global_changeRenderer(self):
        """Updates all GUIs with the current renderer"""
        self.generalPrefs.refreshSettings()
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveRendererChange")
        globalChangeRenderer(self.renderer, toolsets)

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed"""
        self.renderer = renderer
        if self.renderer == rendererconstants.VRAY:
            self.renderer = rendererconstants.ARNOLD
        if self.renderer == rendererconstants.MAYA:
            self.renderer = rendererconstants.ARNOLD
        self.updateComboUI()  # updates the combos to be the current renderer and next in the list and UI

    # ------------------
    # UPDATE UI
    # ------------------

    def updateComboUI(self):
        """Sets the renderer combos to be the default renderer and the next renderer in the list"""
        currRendererIndex = RENDERER_NICE_NAMES.index(self.renderer)
        otherRendererIndex = currRendererIndex + 1
        if otherRendererIndex >= len(RENDERER_NICE_NAMES):
            otherRendererIndex = 0
        self.properties.fromRendererCombo.value = currRendererIndex
        self.properties.toRendererCombo.value = otherRendererIndex
        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    def convertRendererPressed(self):
        """Does the conversion of the renderers"""
        currentRenderer = RENDERER_NICE_NAMES[self.properties.fromRendererCombo.value]
        toRenderer = RENDERER_NICE_NAMES[self.properties.toRendererCombo.value]
        # Check both To and From are not the same
        if currentRenderer == toRenderer:
            output.displayWarning("The `Current` and `To` renderers match. Already converted.")
            return
        # Check and load renderers
        currentRendererLoaded = rendererload.getRendererIsLoaded(currentRenderer)
        if not currentRendererLoaded:
            if not elements.checkRenderLoaded(currentRenderer):
                output.displayWarning("`{}` renderer must be loaded".format(currentRenderer))
                return
        toRendererLoaded = rendererload.getRendererIsLoaded(toRenderer)
        if not toRendererLoaded:
            if not elements.checkRenderLoaded(toRenderer):
                output.displayWarning("`{}` renderer must be loaded".format(toRenderer))
                return
        # Convert the renderers
        exportabcshaderlights.transferRenderer(currentRenderer,
                                               toRenderer,
                                               transferShader=True,
                                               transferLights=True,
                                               transferSelected=False,
                                               addSuffix=True,
                                               replaceShaders=True,
                                               deleteOld=self.properties.deleteCheckBox.value)
        # Globally update renderer to the toRenderer
        self.renderer = toRenderer
        self.global_changeRenderer()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        self.compactWidget.convertRendererBtn.clicked.connect(self.convertRendererPressed)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Combo Options ---------------------------------------
        toolTip = "Will convert the scene `from` this renderer"
        self.fromRendererCombo = elements.ComboBoxRegular("Current",
                                                          items=RENDERER_NICE_NAMES,
                                                          toolTip=toolTip,
                                                          labelRatio=2,
                                                          boxRatio=5)
        toolTip = "Will convert the scene `to` this renderer"
        self.toRendererCombo = elements.ComboBoxRegular("To",
                                                        items=RENDERER_NICE_NAMES,
                                                        toolTip=toolTip,
                                                        labelRatio=2,
                                                        boxRatio=5)
        # Delete Checkbox ---------------------------------------
        toolTip = "Will delete the shaders/lights from the `current` renderer while converting."
        self.deleteCheckBox = elements.CheckBox(label="Delete Shaders/Lights", checked=True, toolTip=toolTip)
        # Convert Renderer Button ---------------------------------------
        toolTip = "Convert the scene to the given renderer \n" \
                  "Shader attributes supported \n" \
                  "  - Diffuse Attributes \n" \
                  "  - Specular Attributes \n" \
                  "  - Clear Coat Attributes \n" \
                  "Lights will be converted\n" \
                  "  - Area \n" \
                  "  - Directional \n" \
                  "  - Skydome HDRI"
        self.convertRendererBtn = elements.styledButton("Convert Renderer",
                                                        icon="convertRenderer",
                                                        toolTip=toolTip,
                                                        style=uic.BTN_DEFAULT)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SLRG)
        # Combo Layout ---------------------------------------
        comboBoxLayout = elements.hBoxLayout(spacing=uic.SVLRG2)
        comboBoxLayout.addWidget(self.fromRendererCombo, 1)
        comboBoxLayout.addWidget(self.deleteCheckBox, 1)
        # Button Checkbox Layout ---------------------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SVLRG2)
        buttonLayout.addWidget(self.toRendererCombo, 1)
        buttonLayout.addWidget(self.convertRendererBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(comboBoxLayout)
        mainLayout.addLayout(buttonLayout)
