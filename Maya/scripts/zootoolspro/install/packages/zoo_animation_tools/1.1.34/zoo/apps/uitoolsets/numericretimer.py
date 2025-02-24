""" ---------- Retimer UI -------------
Numerical retime tool, scale and ripple keys with various scale time modes.

Handy for transferring edit changes back into Maya scenes, for previs.

Author: Andrew Silke
"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.animation import scaleretime

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

SCALE_TYPE_COMBO = ["Units Maya Style", "Percentage", "Frames Per Second"]


class NumericRetimer(toolsetwidget.ToolsetWidget):
    id = "numericRetimer"
    info = "Numerical retime tool, scale and ripple keys with various scale time modes."
    uiData = {"label": "Numeric Retimer",
              "icon": "retimer",
              "tooltip": "Numerical retime tool, scale and ripple keys with various scale time modes.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-numeric-retimer/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

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
        self.oldScaleType = 0
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
        return super(NumericRetimer, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(NumericRetimer, self).widgets()

    def convertTimeScale(self):
        """On the combo type/options change the Time Scale to match"""
        newScaleType = self.properties.optionsCombo.value
        newValue = scaleretime.convertTimeScale(self.properties.scaleFloat.value,
                                                self.oldScaleType,
                                                newScaleType)
        self.oldScaleType = newScaleType
        self.properties.scaleFloat.value = newValue
        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def retime(self):
        """Main function that does the scale and ripple keys
        """
        scaleretime.animRetimer(startRange=self.properties.startFloat.value,
                                endRange=self.properties.endFloat.value,
                                timeScale=self.properties.scaleFloat.value,
                                snapKeys=self.properties.snapKeysCheckbox.value,
                                selectType=self.properties.selectOptionsRadio.value,
                                timeScaleOptions=self.properties.optionsCombo.value,
                                allAnimLayers=self.properties.animLayersCheckbox.value,
                                message=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.optionsCombo.itemChanged.connect(self.convertTimeScale)
            widget.retimeBtn.clicked.connect(self.retime)


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
        # Label and Textbox ---------------------------------------
        tooltip1 = "Affects the selected keyframes or objects. \n" \
                   "Prioritizes graph keyframes or if none are selected \n" \
                   "will affect all keys of the selected objects."
        tooltip2 = "Affect keys on the selected objects and their children."
        tooltip3 = "Affects all animated objects in the scene."
        self.selectOptionsRadio = elements.RadioButtonGroup(radioList=["Selected", "Hierarchy", "Scene"],
                                                            default=0,
                                                            toolTipList=[tooltip1, tooltip2, tooltip3],
                                                            margins=(uic.REGPAD, 0, uic.REGPAD, uic.SMLPAD))
        # Start/End ---------------------------------------
        tooltip = "Set the start frame for the time-scale. \n" \
                  "Scales keys in-between the start and end frames."
        self.startFloat = elements.FloatEdit(label="Start Frame",
                                             editText=40.0,
                                             toolTip=tooltip)
        tooltip = "Set the end frame for the time-scale. \n" \
                  "Scales keys in-between the start and end frames."
        self.endFloat = elements.FloatEdit(label="End Frame",
                                           editText=90.0,
                                           toolTip=tooltip)
        # Scale Type ---------------------------------------
        tooltip = "Set the scale: \n" \
                  "  - Units: 0.5 is two time faster. \n" \
                  "  - Percentage: 200% is two times faster. \n" \
                  "  - Frames Per Second: 48fps (in a 24fps scene) is two times faster."
        self.optionsCombo = elements.ComboBoxRegular(label="Type",
                                                     items=SCALE_TYPE_COMBO,
                                                     toolTip=tooltip)
        # Scale Amount ---------------------------------------
        self.scaleFloat = elements.FloatEdit(label="Time Scale",
                                             editText=0.5,
                                             toolTip=tooltip)
        # Ripple Keys Checkbox ---------------------------------------
        tooltip = "Moves keys after the end frame to account for the scale change."
        self.rippleCheckbox = elements.CheckBox(label="Ripple Push Keys",
                                                checked=True,
                                                toolTip=tooltip)
        # Push Reverse ---------------------------------------
        tooltip = "Reverses the push, instead will move keys before the scale-range while pushing."
        self.pushReverseCheckbox = elements.CheckBox(label="Reverse Ripple Push",
                                                     checked=False,
                                                     toolTip=tooltip)
        # Push Ripple Keys ---------------------------------------
        tooltip = "After scaling will snap keys to whole frame numbers."
        self.snapKeysCheckbox = elements.CheckBox(label="Snap Keys Whole Frames",
                                                  checked=False,
                                                  toolTip=tooltip)
        # Include All Anim Layers ---------------------------------------
        tooltip = "Include all animation layers.  \n" \
                  "If off will only affect the selected or base animation layer."
        self.animLayersCheckbox = elements.CheckBox(label="All Animation Layers ",
                                                    checked=True,
                                                    toolTip=tooltip)
        # A Button ---------------------------------------
        tooltip = "Time-scales from the start-frame to the end-frame and ripples keys."
        self.retimeBtn = elements.styledButton("Numeric Retime Animation",
                                               icon="retimer",
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
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Start End Layout -----------------------------
        startEndLayout = elements.hBoxLayout()
        startEndLayout.addWidget(self.startFloat, 1)
        startEndLayout.addWidget(self.endFloat, 1)
        # Scale Layout -----------------------------
        scaleLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.VSMLPAD))
        scaleLayout.addWidget(self.optionsCombo, 1)
        scaleLayout.addWidget(self.scaleFloat, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.selectOptionsRadio)
        mainLayout.addLayout(startEndLayout)
        mainLayout.addLayout(scaleLayout)
        mainLayout.addWidget(self.retimeBtn)


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
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Start End Layout -----------------------------
        startEndLayout = elements.hBoxLayout()
        startEndLayout.addWidget(self.startFloat, 1)
        startEndLayout.addWidget(self.endFloat, 1)
        # Scale Layout -----------------------------
        scaleLayout = elements.hBoxLayout()
        scaleLayout.addWidget(self.optionsCombo, 1)
        scaleLayout.addWidget(self.scaleFloat, 1)
        # Checkbox Layout -----------------------------
        checkboxLayout = elements.hBoxLayout(margins=(uic.REGPAD, uic.SMLPAD, uic.REGPAD, uic.SMLPAD))
        checkboxLayout.addWidget(self.rippleCheckbox, 1)
        checkboxLayout.addWidget(self.pushReverseCheckbox, 1)
        # Checkbox Layout 2 -----------------------------
        checkboxLayout2 = elements.hBoxLayout(margins=(uic.REGPAD, 0, uic.REGPAD, uic.SMLPAD))
        checkboxLayout2.addWidget(self.snapKeysCheckbox, 1)
        checkboxLayout2.addWidget(self.animLayersCheckbox, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.selectOptionsRadio)
        mainLayout.addLayout(startEndLayout)
        mainLayout.addLayout(scaleLayout)
        mainLayout.addWidget(elements.LabelDivider(text="Options",
                                                   margins=(0, uic.SLRG, 0, uic.SSML)))
        mainLayout.addLayout(checkboxLayout)
        mainLayout.addLayout(checkboxLayout2)
        mainLayout.addWidget(self.retimeBtn)
