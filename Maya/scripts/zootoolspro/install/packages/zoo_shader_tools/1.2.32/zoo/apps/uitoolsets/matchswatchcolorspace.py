""" ---------- Convert Shaders -------------


"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.shaders import convertshaders
from zoo.libs.maya.cmds.renderer import rendererconstants

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class MatchSwatchSpace(toolsetwidget.ToolsetWidget):
    id = "matchSwatchSpace"
    info = "Matches the swatch colors of shaders to match the current render space."
    uiData = {"label": "Match Swatch Color Space",
              "icon": "paintroller",
              "tooltip": "Matches the swatch colors of shaders to match the current render space.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-match-swatch-color-space/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

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
        return super(MatchSwatchSpace, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(MatchSwatchSpace, self).widgets()

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Needed to set self.properties.rendererIconMenu.value in the self.preContentSetup() """
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def matchSwatchColors(self):
        """Main button of the tool"""
        originalRenderSpace = rendererconstants.RENDERER_COLORSPACES[self.properties.prevRenderingSpaceCombo.value]
        if self.properties.matchShadersCombo.value:  # then selected shaders is 1
            convertshaders.swatchColorsToNewRenderSpaceSel(originalRenderSpace=originalRenderSpace)
        else:
            convertshaders.swatchColorsToNewRenderSpaceScene(originalRenderSpace=originalRenderSpace)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.matchSwatchColorsBtn.clicked.connect(self.matchSwatchColors)


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

        # Previous Rendering Space Combo ---------------------------------------
        toolTip = "Set the scene or model's previous rendering space. \n" \
                  "Usually: scene-linear Rec.709-sRGB \n\n" \
                  "If upgrading from older scenes use the default settings."
        self.prevRenderingSpaceCombo = elements.ComboBoxRegular(label="Previous Rendering Space",
                                                                items=rendererconstants.RENDERER_COLORSPACES,
                                                                parent=self,
                                                                toolTip=toolTip,
                                                                setIndex=0,
                                                                labelRatio=1,
                                                                boxRatio=1)
        # Previous Rendering Space Combo ---------------------------------------
        toolTip = "Match/convert all shaders in the scene or restrict to selected shaders only. \n" \
                  "If Selected Objects/Shaders the shaders are automatically detected from the object selection."
        self.matchShadersCombo = elements.ComboBoxRegular(label="Match Shaders",
                                                                items=["All Shaders In Scene",
                                                                       "Selected Objects/Shaders"],
                                                                parent=self,
                                                                toolTip=toolTip,
                                                                setIndex=0,
                                                                labelRatio=1,
                                                                boxRatio=1)
        # Match Swatch Colors Button ---------------------------------------
        tooltip = "Converts/matches the swatch colors of shaders from the previous rendering space \n" \
                  "to the current rendering space. "
        self.matchSwatchColorsBtn = elements.styledButton("Match Shader Swatch Colors",
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
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.prevRenderingSpaceCombo)
        mainLayout.addWidget(self.matchShadersCombo)
        mainLayout.addWidget(self.matchSwatchColorsBtn)


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
        mainLayout.addWidget(self.prevRenderingSpaceCombo)
        mainLayout.addWidget(self.matchShadersCombo)
        mainLayout.addWidget(self.matchSwatchColorsBtn)

