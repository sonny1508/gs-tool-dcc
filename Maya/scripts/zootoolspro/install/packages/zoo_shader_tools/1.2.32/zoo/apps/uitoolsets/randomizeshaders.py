""" ---------- Randomize Shaders -------------
A tool that creates and assigns randomized shaders.

Author: Andrew Silke
"""
from zoo.apps.toolsetsui.ext.renderers import RendererMixin
from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.core.util import env

if env.isMaya():
    from zoo.libs.maya.cmds.shaders import randomshaders, shdmultconstants
    from zoo.libs.maya.cmds.renderer import rendererload, rendererconstants
    from zoo.apps.shader_tools.shadermixin import ShaderMixin

from zoo.libs.utils import color

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class RandomizeShaders(toolsetwidget.ToolsetWidget, RendererMixin, ShaderMixin):
    id = "randomizeShaders"
    info = "A tool that creates and assigns randomized shaders."
    uiData = {"label": "Randomize Shaders",
              "icon": "randomSelect",
              "tooltip": "A tool that creates and assigns randomized shaders.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-randomize-shaders/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.initRendererMixin()

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
        self.randomShad = randomshaders.RandomShader()
        self.shadersColorable = True
        self.showHideUiElements()
        self.updateShaderTypeList()
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
        return super(RandomizeShaders, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(RandomizeShaders, self).widgets()

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    # ------------------
    # UI UPDATES
    # ------------------

    def showSliders(self, visible):
        self.compactWidget.colorSlider.setVisible(visible)
        self.compactWidget.hueRangeFloatSlider.setVisible(visible)
        self.compactWidget.saturationRangeFloatSlider.setVisible(visible)
        self.compactWidget.valueRangeFloatSlider.setVisible(visible)

    def showHideUiElements(self):
        """Automatically shows/hides the Cache and Main buttons depending if self.graphCurveDict is empty or not:

            startMode: True means nothing is loaded so show default UI
            loadObjMode: Shaders are loaded but not objects
            objsLoaded: Objects are loaded ready to randomize

        Sliders will be hidden if an unsupported shader is loaded if self.randomShad.shadersColorable() is False

        """
        startMode = True
        loadObjMode = False
        objsLoaded = False
        reseedColorBtnVis = False
        amountDisabled = False
        # Set UI states -------------------------------
        if self.randomShad.exists():  # show the cache buttons and hide the main buttons
            startMode = False
            if self.randomShad.nodeList:  # are there objects loaded
                objsLoaded = True
            else:
                loadObjMode = True
        if objsLoaded and self.randomShad.shadersColorable():
            reseedColorBtnVis = True
        if not reseedColorBtnVis and objsLoaded:
            amountDisabled = True

        # Cache Buttons -------------------------------
        self.compactWidget.reseedColorsBtn.setVisible(reseedColorBtnVis)
        self.compactWidget.reseedAssignmentsBtn.setVisible(objsLoaded)
        self.compactWidget.doneReselectBtn.setVisible(objsLoaded)
        # Main Randomize Buttons -------------------------
        self.compactWidget.createRandomizeShadersBtn.setVisible(startMode)
        self.showSliders(self.randomShad.shadersColorable())  # Hide or show all the color sliders
        self.compactWidget.useShadersBtn.setVisible(startMode)
        self.compactWidget.selectObjectsBtn.setVisible(loadObjMode)
        self.compactWidget.cancelBtn.setVisible(loadObjMode)
        # Create ShaderType and Renderer ----------------
        self.compactWidget.shaderTypeCombo.setVisible(startMode)
        self.compactWidget.rendererIconMenu.setVisible(startMode)
        # Disable Amount textbox ---------------------------
        self.compactWidget.shaderAmountInt.setDisabled(amountDisabled)
        # Update UI size ----------------------------
        self.updateTree(delayed=True)  # Refresh GUI size

    # ------------------------------------
    # CHANGE RENDERER SHADER TYPE
    # ------------------------------------

    def updateShaderTypeList(self):
        """Updates the shaderTypeCombo on startup or when the renderer is changed

        Sets the list self.shaderTypesList
        """
        self.shaderTypesList = shdmultconstants.RENDERER_SHADERS_DICT[self.properties.rendererIconMenu.value]
        for widget in self.widgets():
            widget.shaderTypeCombo.clear()
            widget.shaderTypeCombo.addItems(self.shaderTypesList)
        self.randomShad.setRenderer(self.properties.rendererIconMenu.value)
        self.randomShad.setShaderType(self.shaderTypesList[self.properties.shaderTypeCombo.value])

    def changeRenderer(self):
        """Run when the renderer is changed"""
        self.updateShaderTypeList()

    def changeShaderType(self):
        """Sets the shader type to the self.randomShad instance when the combo is changed"""
        self.randomShad.setShaderType(self.shaderTypesList[self.properties.shaderTypeCombo.value])

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setShaderAmount(self, shaderAmount):
        """Set the amount of shaders to affect"""
        self.randomShad.updateShaderAmount(self.properties.shaderAmountInt.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setShaderBaseName(self, shaderName):
        """Rename/set the shader base name"""
        self.randomShad.updateShaderNames(self.properties.baseShaderNameTxt.value)

    # -----------------------
    # LOGIC - HSV SLIDERS - UNDO HANDLED
    # -----------------------

    def colorLinear(self):
        """Returns the linear color of the color slider"""
        return self.compactWidget.colorSlider.colorLinearFloat()

    def setColor(self):
        """Updates color changes"""
        self.randomShad.updateColor(self.colorLinear())

    def setHueRangeColor(self):
        """Slider changes for hue"""
        self.randomShad.updateHue(self.properties.hueRangeFloatSlider.value)

    def setSaturationRangeColor(self):
        """Slider changes for saturation"""
        self.randomShad.updateSaturation(self.properties.saturationRangeFloatSlider.value)

    def setValueRangeColor(self):
        """Slider changes for value"""
        self.randomShad.updateValue(self.properties.valueRangeFloatSlider.value)

    def hsvSliderPressed(self):
        """Lock colors for the interactive sliders when the a hsv slider is pressed"""
        self.randomShad.lockColor(self.colorLinear())

    def setHsvValues(self):
        """When a hsv slider is released save the current values in the self.randomShad class"""
        self.randomShad.setHueRangeColor(self.colorLinear(),
                                         self.properties.hueRangeFloatSlider.value)
        self.randomShad.setSaturationRangeColor(self.colorLinear(),
                                                self.properties.saturationRangeFloatSlider.value)
        self.randomShad.setValueRangeColor(self.colorLinear(),
                                           self.properties.valueRangeFloatSlider.value)

    # ------------------
    # LOGIC - OTHER
    # ------------------

    def setAffectShells(self):
        """Affect shells of each object *not implemented"""
        # TODO not implimented
        self.randomShad.setAffectShells(False)

    def setRenderer(self, updateAllUIs=True):
        """Set the renderer"""
        self.randomShad.setRenderer(self.properties.rendererIconMenu.value)
        super(RandomizeShaders, self).setRenderer(updateAllUIs=updateAllUIs)

    def setSuffix(self):
        """Set the suffix name on the shader, not implemented"""
        self.randomShad.setSuffix(True)

    def _updateDataUI(self):
        """Updates the UI data into the logic instance"""
        self.setHsvValues()
        self.randomShad.setShaderAmount(self.properties.shaderAmountInt.value)
        self.randomShad.setShaderBaseName(self.properties.baseShaderNameTxt.value)
        self.randomShad.setRenderer(self.properties.rendererIconMenu.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def reseedColors(self):
        """Reseeds/randomizes the colors"""
        if not rendererload.getRendererIsLoaded(self.properties.rendererIconMenu.value):  # the renderer is not loaded
            if not elements.checkRenderLoaded(self.properties.rendererIconMenu.value):
                return
        self._updateDataUI()
        self.randomShad.reseedColors()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def reseedAssignments(self):
        """Reseeds/randomizes the shader assignments"""
        if not rendererload.getRendererIsLoaded(self.properties.rendererIconMenu.value):  # the renderer is not loaded
            if not elements.checkRenderLoaded(self.properties.rendererIconMenu.value):
                return
        self._updateDataUI()
        self.randomShad.reseedAssignments()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def randomizeShaders(self):
        """Starts the randomize by assigning and changing the UI buttons for tweak mode"""
        if not rendererload.getRendererIsLoaded(self.properties.rendererIconMenu.value):  # the renderer is not loaded
            if not elements.checkRenderLoaded(self.properties.rendererIconMenu.value):
                return
        if not self.randomShad.objList:
            # is there now a selection?
            self.randomShad.setSelectedObjs()
            if not self.randomShad.objList:
                return
        self._updateDataUI()
        self.randomShad.randomizeShaders()
        self.showHideUiElements()

    def selectObjectsRandomize(self):
        """Run when the shaders are already loaded and the objects need to be selected, starts the randomize"""
        selObjs = self.randomShad.setSelectedObjs()
        if not selObjs:  # no objects are selected so return
            return
        self._updateDataUI()
        self.showHideUiElements()
        self.randomShad.randomizeShaders()

    def clearCache(self):
        """Done Reselect - clears the instance logic"""
        self.randomShad.clearCache()
        self.showHideUiElements()

    def useShaders(self):
        """Use the selected shaders"""
        shaderAmount, averageColor = self.randomShad.useShaders()
        if not shaderAmount:
            return
        if averageColor:
            self.properties.colorSlider.value = color.convertColorLinearToSrgb(averageColor)
        self.properties.shaderAmountInt.value = shaderAmount
        self.shadersColorable = self.randomShad.shadersColorable()
        # update the UI
        self.showHideUiElements()
        self.updateFromProperties()  # updates UI with new values

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            # Buttons
            widget.createRandomizeShadersBtn.clicked.connect(self.randomizeShaders)
            widget.reseedAssignmentsBtn.clicked.connect(self.reseedAssignments)
            widget.reseedColorsBtn.clicked.connect(self.reseedColors)
            widget.doneReselectBtn.clicked.connect(self.clearCache)
            widget.useShadersBtn.clicked.connect(self.useShaders)
            widget.selectObjectsBtn.clicked.connect(self.selectObjectsRandomize)
            widget.cancelBtn.clicked.connect(self.clearCache)
            widget.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)
            widget.rendererIconMenu.actionTriggered.connect(self.changeRenderer)
            widget.shaderTypeCombo.itemChanged.connect(self.global_shaderTypeUpdated)  # updates other UIs
            widget.shaderTypeCombo.itemChanged.connect(self.changeShaderType)
            # Text Boxes
            widget.baseShaderNameTxt.textModified.connect(self.setShaderBaseName)
            widget.shaderAmountInt.textModified.connect(self.setShaderAmount)
            # Sliders
            widget.colorSlider.colorSliderChanged.connect(self.setColor)
            floatSliderList = list()  # reset in case of advanced UI
            floatSliderList.append(widget.hueRangeFloatSlider)
            floatSliderList.append(widget.saturationRangeFloatSlider)
            floatSliderList.append(widget.valueRangeFloatSlider)
            # Connect the float and color sliders correctly
            for floatSlider in floatSliderList:
                floatSlider.sliderPressed.connect(self.openUndoChunk)
                floatSlider.sliderPressed.connect(self.hsvSliderPressed)
                floatSlider.sliderReleased.connect(self.closeUndoChunk)
                floatSlider.sliderPressed.connect(self.setHsvValues)
            widget.hueRangeFloatSlider.numSliderChanged.connect(self.setHueRangeColor)
            widget.saturationRangeFloatSlider.numSliderChanged.connect(self.setSaturationRangeColor)
            widget.valueRangeFloatSlider.numSliderChanged.connect(self.setValueRangeColor)


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
        # Base Shader Name String ---------------------------------------
        tooltip = "The base name of the created shaders.  \n" \
                  "All shaders will be renamed automatically if the name is changed. \n" \
                  "Shaders will be named `randomShader_01`, `randomShader_02` etc \n" \
                  "Don't change this value if using existing shaders. "
        self.baseShaderNameTxt = elements.StringEdit(label="Name Base",
                                                     editText="randomShader",
                                                     toolTip=tooltip,
                                                     labelRatio=97,
                                                     editRatio=160)
        # Color Slider Tuple ---------------------------------------
        tooltip = "The base color. The random colors are offset from this color."
        self.colorSlider = elements.ColorSlider(label="Base Color",
                                                color=(0.3, 0.88, 0.66),
                                                toolTip=tooltip)
        # Hue Range Float Tuple ---------------------------------------
        tooltip = "The hue/spectrum range of the randomized colors. Offset from the base color. \n" \
                  "Example: 360.0 uses the full spectrum of colors, or 180.0 in each direction."
        self.hueRangeFloatSlider = elements.FloatSlider(label="Hue Range",
                                                        defaultValue=200.0,
                                                        toolTip=tooltip,
                                                        sliderMin=0.0,
                                                        sliderMax=360.0)
        # Value Range Float Tuple ---------------------------------------
        tooltip = "The brightness (value) range of the randomized colors.  Offset from the base color.  \n" \
                  "Example: 1.0 will randomize the brightness 0.5 from each side of the current color. \n" \
                  "Values can be randomized to a max range of 2.0, or 1.0 either side.  \n" \
                  "Type 2.0 to lengthen the value range."
        self.valueRangeFloatSlider = elements.FloatSlider(label="Brightness Range",
                                                          defaultValue=0.2,
                                                          toolTip=tooltip,
                                                          sliderMin=0.0,
                                                          sliderMax=1.0,
                                                          dynamicMax=True)
        # Saturation Range Float Tuple ---------------------------------------
        tooltip = "The saturation range of the randomized colors.  Offset from the base color.  \n" \
                  "Example: 1.0 will randomize the saturation 0.5 from each side of the current color. \n" \
                  "Saturation can be randomized to a max range of 2.0, or 1.0 either side.  \n" \
                  "Type 2.0 to lengthen the saturation range."
        self.saturationRangeFloatSlider = elements.FloatSlider(label="Saturation range",
                                                               defaultValue=0.2,
                                                               toolTip=tooltip,
                                                               sliderMin=0.0,
                                                               sliderMax=1.0,
                                                               dynamicMax=True)
        # Shader Amount Int ---------------------------------------
        tooltip = "The amount of shaders that will be created for the randomize. \n" \
                  "Note: The `Set Shaders` button will automatically set this number."
        self.shaderAmountInt = elements.IntEdit(label="Amount",
                                                editText=4,
                                                toolTip=tooltip)
        # Shader Type Combo ---------------------------------------
        toolTip = "Select a shader Type used while creating new shaders only. "
        self.shaderTypeCombo = elements.ComboBoxRegular(label="Create Shader",
                                                        items=[],
                                                        parent=self,
                                                        toolTip=toolTip,
                                                        setIndex=0,
                                                        labelRatio=20,
                                                        boxRatio=55)  # is populated by the renderer
        # Renderer Button --------------------------------------
        toolTip = "While creating new shaders set the renderer and shader type. \n" \
                  "The button `Set Shaders/Objects` will ignore this setting and use existing shaders. "
        self.rendererIconMenu = elements.iconMenuButtonCombo(rendererconstants.RENDERER_ICONS_LIST,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)
        # Reseed Colors Btn ---------------------------------------
        tooltip = "Reseed the color of all shaders."
        self.reseedColorsBtn = elements.styledButton("Colors",
                                                     icon="randomSelect",
                                                     toolTip=tooltip)
        # Reseed Assignments Btn ---------------------------------------
        tooltip = "Reseed the shader assignments of all objects."
        self.reseedAssignmentsBtn = elements.styledButton("Assignments",
                                                          icon="randomSelect",
                                                          toolTip=tooltip)
        # Clear Cache Btn ---------------------------------------
        tooltip = "Finish a shader-randomize and start on a new selection."
        self.doneReselectBtn = elements.styledButton("Done/Reselect",
                                                     icon="checkOnly",
                                                     toolTip=tooltip)
        # Randomize Btn ---------------------------------------
        tooltip = "Creates new, random colored shaders on the selected objects. \n" \
                  "Shaders are assigned with varying colors and can be tweaked after assignment.  \n" \
                  "Select the objects to randomize and run."
        self.createRandomizeShadersBtn = elements.styledButton("Create Shaders And Randomize",
                                                               icon="randomSelect",
                                                               toolTip=tooltip)
        # Select Objects Btn ---------------------------------------
        tooltip = "The shaders have been set, so now select the objects you wish to affect."
        self.selectObjectsBtn = elements.styledButton("Select Objects",
                                                      icon="cursorSelect",
                                                      toolTip=tooltip)
        # Cancel Btn ---------------------------------------
        tooltip = "Cancel the randomization and start again."
        self.cancelBtn = elements.styledButton("Cancel",
                                               icon="crossXFat",
                                               toolTip=tooltip)
        # Randomize Btn ---------------------------------------
        tooltip = "Use existing shaders for the randomize. \n" \
                  "The shaders can be selected shaders/shading groups or objects. \n" \
                  "In the case of objects their related shaders will be used in the randomize. "
        self.useShadersBtn = elements.styledButton("Use Shaders",
                                                   icon="cursorSelect",
                                                   toolTip=tooltip)


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
        # Text Layout --------------------------------------
        textLayout = elements.hBoxLayout()
        textLayout.addWidget(self.baseShaderNameTxt, 2)
        textLayout.addWidget(self.shaderAmountInt, 1)

        # Button1 Layout --------------------------------------
        btnLayout1 = elements.hBoxLayout(spacing=uic.SPACING)
        btnLayout1.addWidget(self.shaderTypeCombo, 1)
        btnLayout1.addWidget(self.rendererIconMenu, 1)
        # Button2 Layout --------------------------------------
        btnLayout2 = elements.hBoxLayout(spacing=uic.SPACING)
        btnLayout2.addWidget(self.reseedColorsBtn, 1)
        btnLayout2.addWidget(self.reseedAssignmentsBtn, 1)
        btnLayout2.addWidget(self.doneReselectBtn, 1)
        btnLayout2.addWidget(self.createRandomizeShadersBtn, 20)
        btnLayout2.addWidget(self.selectObjectsBtn, 20)
        btnLayout2.addWidget(self.cancelBtn, 10)
        btnLayout2.addWidget(self.useShadersBtn, 10)
        # Buttons Vertical Layout --------------------------------------
        btnVertLayout = elements.vBoxLayout(spacing=uic.SPACING)
        btnVertLayout.addLayout(btnLayout1)
        btnVertLayout.addLayout(btnLayout2)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(textLayout)
        mainLayout.addWidget(self.colorSlider)
        mainLayout.addWidget(self.hueRangeFloatSlider)
        mainLayout.addWidget(self.saturationRangeFloatSlider)
        mainLayout.addWidget(self.valueRangeFloatSlider)
        mainLayout.addLayout(btnVertLayout)


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
        mainLayout.addWidget(self.baseShaderNameTxt)
        mainLayout.addWidget(self.createRandomizeShadersBtn)
