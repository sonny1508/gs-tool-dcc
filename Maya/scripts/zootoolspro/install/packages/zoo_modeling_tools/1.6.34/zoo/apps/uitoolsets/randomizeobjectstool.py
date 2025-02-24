from zoovendor.Qt import QtWidgets

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.objutils import randomizeobjects
from zoo.apps.toolsetsui.widgets import toolsetwidget

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class RandomizeObjects(toolsetwidget.ToolsetWidget):
    id = "randomizeObjects"
    info = "Template file for building new GUIs."
    uiData = {"label": "Randomize Objects",
              "icon": "randomizeObjects_64",
              "tooltip": "Randomizes the translation, rotation, and scale of the selected objects",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-randomize-objects/"}

    # ------------------
    # STARTUP
    # ------------------

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

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

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(RandomizeObjects, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(RandomizeObjects, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def randomizeObjectsTransforms(self):
        """Randomize the selected object's attributes, see randomizeobjects.randomObjSelection() for documentation
        """
        randomizeobjects.randomObjSelection(randRotate=self.properties.rotateCheckbox.value,
                                            randTranslate=self.properties.translateCheckbox.value,
                                            randScale=self.properties.scaleCheckbox.value,
                                            randOther=self.properties.customCheckbox.value,
                                            translateMinMax=(self.properties.translateMinVector.value,
                                                             self.properties.translateMaxVector.value),
                                            rotateMinMax=(self.properties.rotateMinVector.value,
                                                          self.properties.rotateMaxVector.value),
                                            scaleMinMax=(self.properties.scaleMinVector.value,
                                                         self.properties.scaleMaxVector.value),
                                            otherMinMax=self.properties.customMinMaxVector.value,
                                            otherAttrName=self.properties.customAttrTxt.value,
                                            absolute=self.properties.relativeAbsoluteRadio.value,
                                            uniformScale=self.properties.scaleUniformRadio.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def randomizeObjectsChannelBox(self):
        """Randomize the selected object's attributes, see randomizeobjects.randomObjSelection() for documentation
        """
        randomizeobjects.randomAttrChannelSelection(self.properties.channelMinMaxVector.value,
                                                    absolute=self.properties.channelAbsoluteCombo.value,
                                                    uniformScale=self.properties.channelUniformCombo.value,
                                                    message=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        self.compactWidget.randomizeChannelBoxBtn.clicked.connect(self.randomizeObjectsChannelBox)
        self.advancedWidget.randomizeBtn.clicked.connect(self.randomizeObjectsTransforms)


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
        # Channel Selection Options Absolute Combo -----------------------------
        tooltip = "Relative: The objects are randomly offset relative to their current values. \n" \
                  "Absolute: The objects are randomized within the absolute given range."
        self.channelAbsoluteCombo = elements.ComboBoxRegular(items=["Relative Obj Offset", "Absolute Obj Offset"],
                                                             toolTip=tooltip)
        tooltip = "Affect`Randomly` or `Uniformly` per attribute. \n" \
                  "Example: use on `Uniform` to keep all scale ratios consistent."
        self.channelUniformCombo = elements.ComboBoxRegular(items=["Random Per Axis", "Uniform Per Axis"],
                                                            toolTip=tooltip)
        # Channel Box Selection ---------------------------------------
        tooltip = "Minimum and maximum range values for the randomize"
        self.channelMinMaxVector = elements.VectorLineEdit(label="Range Min/Max",
                                                           value=(0.0, 1.0),
                                                           axis=("min", "max"),
                                                           toolTip=tooltip)
        # Randomize Button ---------------------------------------
        tooltip = "Select objects and attributes in the channel box (see tutorial) and run."
        self.randomizeChannelBoxBtn = elements.styledButton("Randomize Selected Channel Box Attributes",
                                                            icon="randomizeObjects",
                                                            toolTip=tooltip,
                                                            style=uic.BTN_DEFAULT)

        # Transform Relative Absolute Combo -----------------------------
        tooltip = "Relative: The objects are randomly offset from their current values. \n" \
                  "Absolute: The Objects are randomized from their absolute values."
        self.relativeAbsoluteCombo = elements.ComboBoxRegular(label="Randomize Object Space",
                                                              items=["Relative Offset", "Absolute Offset"],
                                                              toolTip=tooltip)
        # Rotation ---------------------------------------
        tooltip = "If checked, randomize the rotation values"
        self.rotateCheckbox = elements.CheckBox(label="", checked=False, toolTip=tooltip)
        tooltip = "The range of the rotation values to randomize. X, Y , Z."
        self.rotateMinVector = elements.VectorLineEdit(label="Min",
                                                       value=(0.0, 0.0, 0.0),
                                                       editRatio=3,
                                                       labelRatio=1,
                                                       toolTip=tooltip)
        self.rotateMaxVector = elements.VectorLineEdit(label="Max",
                                                       value=(90.0, 90.0, 90.0),
                                                       editRatio=3,
                                                       labelRatio=1,
                                                       toolTip=tooltip)
        # Translation ---------------------------------------
        tooltip = "If checked, randomize the translate values"
        self.translateCheckbox = elements.CheckBox(label="", checked=False)
        tooltip = "The range of the translate values to randomize. X, Y , Z."
        self.translateMinVector = elements.VectorLineEdit(label="Min",
                                                          value=(0.0, 0.0, 0.0),
                                                          editRatio=3,
                                                          labelRatio=1,
                                                          toolTip=tooltip)
        self.translateMaxVector = elements.VectorLineEdit(label="Max",
                                                          value=(10.0, 10.0, 10.0),
                                                          editRatio=3,
                                                          labelRatio=1,
                                                          toolTip=tooltip)
        # Scale ---------------------------------------
        tooltip = "If checked, randomize the scale values"
        self.scaleCheckbox = elements.CheckBox(label="", checked=False, toolTip=tooltip)
        tooltip = "Either scale Randomly or Uniformly per attribute. \n" \
                  "Keep Uniform on to keep scale ratios consistent."
        self.scaleUniformRadio = elements.RadioButtonGroup(radioList=["Random Per Axis", "Uniform Per Axis"],
                                                           default=1,
                                                           toolTipList=[tooltip, tooltip],
                                                           margins=(uic.REGPAD,
                                                                    uic.SMLPAD,
                                                                    uic.REGPAD,
                                                                    uic.SMLPAD))
        tooltip = "The range of the scale values to randomize. X, Y , Z."
        self.scaleMinVector = elements.VectorLineEdit(label="Min",
                                                      value=(1.0, 1.0, 1.0),
                                                      editRatio=3,
                                                      labelRatio=1, toolTip=tooltip)
        self.scaleMaxVector = elements.VectorLineEdit(label="Max",
                                                      value=(2.0, 2.0, 2.0),
                                                      editRatio=3,
                                                      labelRatio=1,
                                                      toolTip=tooltip)
        # Custom ---------------------------------------
        tooltip = "If checked, randomize the custom values"
        self.customCheckbox = elements.CheckBox(label="", checked=False, toolTip=tooltip)
        tooltip = "The range of the custom values to randomize. Min, Max"
        self.customMinMaxVector = elements.VectorLineEdit(label="Custom Min/Max",
                                                          value=(0.0, 1.0),
                                                          axis=("min", "max"),
                                                          toolTip=tooltip)
        # Custom Attribute ---------------------------------------
        tooltip = "The name of the custom attribute to randomize"
        self.customAttrTxt = elements.StringEdit(label="Custom Attribute Name",
                                                 editPlaceholder="attributeName",
                                                 toolTip=tooltip)
        # Randomize Button ---------------------------------------
        tooltip = "Randomize the selected objects"
        self.randomizeBtn = elements.styledButton("Randomize Objects",
                                                  icon="randomizeObjects",
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
        # Custom Title Layout -----------------------------
        customTitleLayout = elements.hBoxLayout()
        customTitleLayout.addWidget(self.channelAbsoluteCombo, 1)
        customTitleLayout.addWidget(self.channelUniformCombo, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(customTitleLayout)
        mainLayout.addWidget(self.channelMinMaxVector)
        mainLayout.addWidget(self.randomizeChannelBoxBtn)


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
        # Rot Title Layout -----------------------------
        rotTitleLayout = elements.hBoxLayout()
        rotTitleLayout.addWidget(elements.LabelDivider(text="Rotation Range"), 20)
        rotTitleLayout.addWidget(self.rotateCheckbox, 1)
        # Trans Title Layout -----------------------------
        translateTitleLayout = elements.hBoxLayout()
        translateTitleLayout.addWidget(elements.LabelDivider(text="Translation Range"), 20)
        translateTitleLayout.addWidget(self.translateCheckbox, 1)
        # Scale Title Layout -----------------------------
        scaleTitleLayout = elements.hBoxLayout()
        scaleTitleLayout.addWidget(elements.LabelDivider(text="Scale Range"), 20)
        scaleTitleLayout.addWidget(self.scaleCheckbox, 1)
        # Custom Title Layout -----------------------------
        customTitleLayout = elements.hBoxLayout()
        customTitleLayout.addWidget(elements.LabelDivider(text="Custom Attribute"), 20)
        customTitleLayout.addWidget(self.customCheckbox, 1)
        # Custom Title Layout -----------------------------
        btnLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, 0))
        btnLayout.addWidget(self.randomizeBtn)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.relativeAbsoluteCombo)
        mainLayout.addLayout(translateTitleLayout)
        mainLayout.addWidget(self.translateMinVector)
        mainLayout.addWidget(self.translateMaxVector)
        mainLayout.addLayout(rotTitleLayout)
        mainLayout.addWidget(self.rotateMinVector)
        mainLayout.addWidget(self.rotateMaxVector)
        mainLayout.addLayout(scaleTitleLayout)
        mainLayout.addWidget(self.scaleUniformRadio)
        mainLayout.addWidget(self.scaleMinVector)
        mainLayout.addWidget(self.scaleMaxVector)
        mainLayout.addLayout(customTitleLayout)
        mainLayout.addWidget(self.customAttrTxt)
        mainLayout.addWidget(self.customMinMaxVector)
        mainLayout.addLayout(btnLayout)
