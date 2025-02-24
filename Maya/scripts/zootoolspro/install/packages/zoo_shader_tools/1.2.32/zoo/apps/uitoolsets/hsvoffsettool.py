""" ---------- HSV Offset -------------
Offsets diffuse color by Hue Saturation and Value for all selected objects and shaders.

"""

from zoovendor.Qt import QtWidgets

from maya import cmds

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.apps.toolsetsui import toolsetui
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic

from zoo.libs.maya.cmds.shaders import shaderhsv, shadermulti, shdmultconstants as sc

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class HsvOffset(toolsetwidget.ToolsetWidget):
    id = "hsvOffset"
    info = "Offsets hue saturation and value shader colors."
    uiData = {"label": "HSV Offset Shaders (beta)",
              "icon": "hsvPicker",
              "tooltip": "Offsets hue saturation and value shader colors.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-hsv-offset-shaders/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.shaderAttrs = list()
        self.shadersSet = False  # state tracker for the hsv instance

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
        self.properties.diffuseColorSldr.value = self.firstShaderColor()  # sets color as rendering space color.
        self.uiConnections()
        self.startSelectionCallback()  # start selection callback

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
        return super(HsvOffset, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(HsvOffset, self).widgets()

    # ------------------
    # UI
    # ------------------

    def enterEvent(self, event):
        """Cursor entered UI"""
        self.properties.diffuseColorSldr.value = self.firstShaderColor()
        self.resetSliders()

    def firstShaderColor(self):
        """Returns the first color from the selection, or mid grey in rendering space"""
        shdrInsts = shadermulti.shaderInstancesFromSelected(message=False)
        if not shdrInsts:
            return [0.5, 0.5, 0.5]
        for shdrInst in shdrInsts:
            shaderDict = shdrInst.connectedAttrs()
            if shaderDict:
                if sc.DIFFUSE in shaderDict:
                    continue
            return shdrInst.diffuseDisplay()  # returns the first legit diffuse col found
        return [0.5, 0.5, 0.5]  # no legit colors found

    def resetSliders(self):
        """Resets all float sliders to be zero, triggered after using"""
        self.properties.hueFloatSlider.value = 0.0
        self.properties.saturationFloatSlider.value = 0.0
        self.properties.valueFloatSlider.value = 0.0
        self.updateFromProperties()

    def selectionChanged(self, selection):
        """Triggered when the selection changes, update the color slider"""
        if not selection:  # then still may be a component face selection
            selection = cmds.ls(selection=True)
            if not selection:  # then nothing is selected
                return
        self.properties.diffuseColorSldr.value = self.firstShaderColor()
        self.resetSliders()

    def global_sendDiffuseColor(self):
        """Updates all GUIs with diffuse shader color"""
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveDiffuseColor")
        for tool in toolsets:
            tool.global_receiveDiffuseColor(self.properties.diffuseColorSldr.value)

    def global_receiveDiffuseColor(self, diffuseColorDisplay):
        """Receives the diffuse shader color from other GUIs"""
        self.properties.diffuseColorSldr.value = diffuseColorDisplay
        self.updateFromProperties()

    # -------------
    # LOGIC
    # -------------

    def setDiffuseColor(self):
        """Sets the diffuse color for all selected objects/shaders"""
        shdrInsts = shadermulti.shaderInstancesFromSelected(message=False)
        if not shdrInsts:
            return list()
        for shdrInst in shdrInsts:
            shdrInst.setDiffuseDisplay(self.properties.diffuseColorSldr.value)

    def startupHsvInstance(self):
        """Starts th HSV instance, selects shaders"""
        self.openUndoChunk()
        self.hsvInstance = shaderhsv.ShaderHSV()  # sets the shader instances and start colors.
        if self.hsvInstance.shdrInsts:
            self.shadersSet = True

    def shutdownHsvInstance(self):
        """After the slider is released finish the instance"""
        self.closeUndoChunk()
        self.global_sendDiffuseColor()
        self.resetSliders()
        if not self.shadersSet:
            return
        self.hsvInstance.shdrInsts = list()
        self.shadersSet = False

    def setHueOffset(self):
        """Offset the hue"""
        if not self.shadersSet:
            return
        col = self.hsvInstance.setHueOffsetDisplay(self.properties.hueFloatSlider.value)
        self.properties.diffuseColorSldr.value = col
        self.updateFromProperties()

    def setSaturationOffset(self):
        """Offset the saturation"""
        if not self.shadersSet:
            return
        col = self.hsvInstance.setSaturationOffsetDisplay(self.properties.saturationFloatSlider.value)
        self.properties.diffuseColorSldr.value = col
        self.updateFromProperties()

    def setValueOffset(self):
        """Offset the value"""
        if not self.shadersSet:
            return
        col = self.hsvInstance.setValueOffsetDisplay(self.properties.valueFloatSlider.value)
        self.properties.diffuseColorSldr.value = col
        self.updateFromProperties()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.diffuseColorSldr.colorSliderChanged.connect(self.setDiffuseColor)
            widget.diffuseColorSldr.sliderPressed.connect(self.startupHsvInstance)
            widget.diffuseColorSldr.sliderReleased.connect(self.shutdownHsvInstance)
            # Connect the float and color sliders correctly
            for floatSlider in widget.floatSliderList:
                floatSlider.sliderPressed.connect(self.startupHsvInstance)
                floatSlider.sliderReleased.connect(self.shutdownHsvInstance)

            widget.hueFloatSlider.numSliderChanged.connect(self.setHueOffset)
            widget.saturationFloatSlider.numSliderChanged.connect(self.setSaturationOffset)
            widget.valueFloatSlider.numSliderChanged.connect(self.setValueOffset)

        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


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
        # Diffuse Color Slider ---------------------------------------
        toolTip = "Change to set diffuse color of all the selected objects/shaders"
        self.diffuseColorSldr = elements.ColorSlider(label="Col",
                                                     color=(0.5, 0.5, 0.5),
                                                     toolTip=toolTip,
                                                     labelBtnRatio=1,
                                                     sliderRatio=3,
                                                     labelRatio=1,
                                                     colorBtnRatio=2)
        # Hue Range Float Tuple ---------------------------------------
        tooltip = "Offset hue for all selected shaders diffuse value. \n" \
                  "Select shader nodes or geo with shaders. "
        self.hueFloatSlider = elements.FloatSlider(label="Hue",
                                                   defaultValue=0.0,
                                                   toolTip=tooltip,
                                                   sliderMin=-90.0,
                                                   sliderMax=90.0,
                                                   sliderRatio=3,
                                                   labelBtnRatio=1,
                                                   labelRatio=1,
                                                   editBoxRatio=2)
        # Value Range Float Tuple ---------------------------------------
        tooltip = "Offset value (brightness) for all selected shaders diffuse value. \n" \
                  "Select shader nodes or geo with shaders. "
        self.valueFloatSlider = elements.FloatSlider(label="Val",
                                                     defaultValue=0.0,
                                                     toolTip=tooltip,
                                                     sliderMin=-.5,
                                                     sliderMax=0.5,
                                                     dynamicMax=True,
                                                     sliderRatio=3,
                                                     labelBtnRatio=1,
                                                     labelRatio=1,
                                                     editBoxRatio=2)
        # Saturation Range Float Tuple ---------------------------------------
        tooltip = "Offset saturation (brightness) for all selected shaders diffuse value. \n" \
                  "Select shader nodes or geo with shaders. "
        self.saturationFloatSlider = elements.FloatSlider(label="Sat",
                                                          defaultValue=0.0,
                                                          toolTip=tooltip,
                                                          sliderMin=-0.5,
                                                          sliderMax=0.5,
                                                          dynamicMax=True,
                                                          sliderRatio=3,
                                                          labelBtnRatio=1,
                                                          labelRatio=1,
                                                          editBoxRatio=2)
        self.floatSliderList = list()  # reset in case of advanced UI
        self.floatSliderList.append(self.hueFloatSlider)
        self.floatSliderList.append(self.saturationFloatSlider)
        self.floatSliderList.append(self.valueFloatSlider)


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
        mainLayout.addWidget(self.diffuseColorSldr)
        mainLayout.addWidget(self.hueFloatSlider)
        mainLayout.addWidget(self.saturationFloatSlider)
        mainLayout.addWidget(self.valueFloatSlider)


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
        mainLayout.addWidget(self.aLabelAndTextbox)
        mainLayout.addWidget(self.aBtn)
