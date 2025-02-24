""" ---------- Toolset Boiler Plate (Multiple UI Modes) -------------
The following code is a template (boiler plate) for building Zoo Toolset GUIs that multiple UI modes.

Multiple UI modes include compact and medium or advanced modes.

This UI will use Compact and Advanced Modes.

The code gets more complicated while dealing with UI Modes.

"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.braverabbitsmoothskin import brsmoothskin

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class SmoothSkin(toolsetwidget.ToolsetWidget):
    id = "smoothSkin"
    info = "braverabbit Smooth Skin for smoothing skinned meshes."
    uiData = {"label": "Smooth Skin - brave rabbit",
              "icon": "brSmoothSkinWeights",
              "tooltip": "braverabbit Smooth Skin for smoothing skinned meshes.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-third-party/#smoothweights"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.tool = None
        if brsmoothskin.loadPlugin():
            self.tool = brsmoothskin.getTool()

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
        return super(SmoothSkin, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(SmoothSkin, self).widgets()

    # ------------------
    # UPDATE UI
    # ------------------

    def setTool(self):
        """When the UI loads it should start up the tool, this function sets it so the tool is on.
        Also tries to get the tool if it doesn't exist which is unlikely unless the plugin is not installed. """
        if not self.tool:
            if not brsmoothskin.loadPlugin():
                brsmoothskin.installPlugin()
                return False
            else:
                self.tool = brsmoothskin.getTool()
        brsmoothskin.setTool(self.tool)
        return True

    def updateUI(self):
        """Updates the UI by pulling in the strength and size values to the sliders"""
        if not self.tool:
            return
        self.properties.strengthFSlider.value = brsmoothskin.strength(self.tool)
        self.properties.sizeFSlider.value = brsmoothskin.brushSize(self.tool)
        self.properties.oversampleIntSlider.value = brsmoothskin.oversampling(self.tool)
        self.updateFromProperties()

    def enterEvent(self, event):
        """Updates the UI by pulling in the strength and size values to the sliders"""
        self.updateUI()

    # ------------------
    # LOGIC
    # ------------------

    def smoothSkinBrush(self):
        """Enters the tool (brush mode on)
        """
        self.setTool()  # enters the brush mode

    @toolsetwidget.ToolsetWidget.undoDecorator
    def flood(self):
        """Enters the tool and floods the selection.
        """
        if not self.setTool():
            return
        brsmoothskin.flood(self.tool, strength=self.properties.strengthFSlider.value)

    def setStrength(self):
        """Sets the brush and flood strength
        """
        if not self.setTool():
            return
        brsmoothskin.setStrength(self.tool, strength=self.properties.strengthFSlider.value)

    def setSize(self):
        """Sets the size of the brush
        """
        if not self.setTool():
            return
        brsmoothskin.setBrushSize(self.tool, size=self.properties.sizeFSlider.value)

    def setOversample(self):
        if not self.setTool():
            return
        brsmoothskin.setOversampling(self.tool, oversampling=self.properties.oversampleIntSlider.value)

    def openToolWindow(self):
        if not self.setTool():
            return
        brsmoothskin.openBraverabbitToolWindow()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            # Buttons ---------
            widget.floodBtn.clicked.connect(self.flood)
            widget.brushBtn.clicked.connect(self.smoothSkinBrush)
            widget.toolWindowBtn.clicked.connect(self.openToolWindow)
            # Sliders ---------
            widget.sizeFSlider.sliderChanged.connect(self.setSize)
            widget.strengthFSlider.sliderChanged.connect(self.setStrength)
            widget.oversampleIntSlider.sliderChanged.connect(self.setOversample)


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
        # Slider ---------------------------------------
        tooltip = "Sets the size of the smooth skin weights brush \n\n" \
                  "Hotkey: Middle-Mouse Drag Left-Right"
        self.sizeFSlider = elements.FloatSlider(label="Size",
                                                defaultValue=5.0,
                                                toolTip=tooltip,
                                                sliderMax=10.0,
                                                dynamicMax=True)
        # Slider ---------------------------------------
        tooltip = "Sets the strength of the smooth skin weights brush and flood command. \n\n" \
                  "Hotkey: Middle-Mouse Drag Up-Down"
        self.strengthFSlider = elements.FloatSlider(label="Strength",
                                                    defaultValue=0.25,
                                                    toolTip=tooltip)
        # Slider ---------------------------------------
        tooltip = ("Sets the number of iterations for the smoothing. \n"
                   "Higher numbers will smooth faster.")
        self.oversampleIntSlider = elements.IntSlider(label="Oversample",
                                                      defaultValue=1,
                                                      toolTip=tooltip,
                                                      sliderMin=1,
                                                      sliderMax=10)
        # Smooth Skin Brush ---------------------------------------
        tooltip = "Enter the Smooth Skin Weights brush. \n\n" \
                  "Paint Smooth: Left Mouse Button \n\n" \
                  "Strength: Middle-Mouse Drag Up-Down \n" \
                  "Size: Middle-Mouse Drag Left-Right \n\n" \
                  "Add Vertices: Shift + Left Mouse Button \n" \
                  "Remove Vertices: Ctrl + Left Mouse Button\n" \
                  "Clear Vertices: Ctrl + Shift + LMB\n\n" \
                  "Tool by: brave rabbit (braverabbit.com)"
        self.brushBtn = elements.styledButton("Smooth Skin Brush",
                                              icon="menu_paintLine",
                                              toolTip=tooltip,
                                              style=uic.BTN_DEFAULT)
        # Flood ---------------------------------------
        tooltip = "Select vertices and flood to smooth skin weights. \n\n" \
                  "Note: Can select vertices in the brush mode.\n" \
                  "Hold shift to add, ctrl to remove and ctrl shift to clear \n" \
                  "Tool by: brave rabbit (braverabbit.com)"

        self.floodBtn = elements.styledButton("Flood",
                                              icon="downloadCircle",
                                              toolTip=tooltip,
                                              style=uic.BTN_DEFAULT)
        # Open Tool button ---------------------------------------
        tooltip = "Open the braverabbit Maya Tool UI \n" \
                  "for extra options. "
        self.toolWindowBtn = elements.styledButton("",
                                                   icon="window",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_DEFAULT,
                                                   minWidth=uic.BTN_W_ICN_MED,
                                                   maxWidth=uic.BTN_W_ICN_MED)


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
        floodOpenToolLay = elements.hBoxLayout(spacing=uic.SPACING)
        floodOpenToolLay.addWidget(self.floodBtn, 10)
        floodOpenToolLay.addWidget(self.toolWindowBtn, 1)
        # Grid Layout ---------------------------------------
        buttonLay = elements.GridLayout(spacing=uic.SPACING)  # 2 spacing
        row = 0
        buttonLay.addWidget(self.brushBtn, row, 0)
        buttonLay.addLayout(floodOpenToolLay, row, 1)
        # Keep grid columns 50/50 sized
        buttonLay.setColumnStretch(0, 1)
        buttonLay.setColumnStretch(1, 1)

        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.sizeFSlider)
        mainLayout.addWidget(self.strengthFSlider)
        mainLayout.addWidget(self.oversampleIntSlider)
        mainLayout.addLayout(buttonLay)


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
        floodOpenToolLay = elements.hBoxLayout(spacing=uic.SPACING)
        floodOpenToolLay.addWidget(self.floodBtn, 10)
        floodOpenToolLay.addWidget(self.toolWindowBtn, 1)
        # Grid Layout ---------------------------------------
        buttonLay = elements.GridLayout(spacing=uic.SPACING)  # 2 spacing
        row = 0
        buttonLay.addWidget(self.brushBtn, row, 0)
        buttonLay.addLayout(floodOpenToolLay, row, 1)
        # Keep grid columns 50/50 sized
        buttonLay.setColumnStretch(0, 1)
        buttonLay.setColumnStretch(1, 1)

        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.sizeFSlider)
        mainLayout.addWidget(self.strengthFSlider)
        mainLayout.addWidget(self.oversampleFSlider)
        mainLayout.addLayout(buttonLay)
