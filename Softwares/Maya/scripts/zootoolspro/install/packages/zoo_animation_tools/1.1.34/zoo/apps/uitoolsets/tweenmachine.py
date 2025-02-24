""" Tween Machine Toolset UI

Zoo UI Author: Andrew Silke
Tween Machine Logic: Justin S Barrett, mods by Wade Schneider and Andrew Silke

Free Version: https://github.com/The-Maize/tweenMachine
Logic License: MIT, see zoo.libs.tweenmachine.LICENSE
"""
from functools import partial

from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs.utils import output
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

try:
    from zoo.libs.tweenmachine import tweenmachine
except:
    tweenmachine = None
    output.displayWarning("Tween Machine Logic was not found in Community Scripts, so this UI cannot be used.")

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class TweenMachine(toolsetwidget.ToolsetWidget):
    id = "tweenMachine"
    info = "Animation tweener by Justin S Barrett, mods by Wade Schneider and Andrew Silke"
    uiData = {"label": "Tween Machine",
              "icon": "blender",
              "tooltip": "Animation tweener by Justin S Barrett, mods by Wade Schneider and Andrew Silke.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-tween-machine/"}

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
        try:
            self.tweenInstance = tweenmachine.TweenMachine()
        except:  # not installed
            self.tweenInstance = None

        self.countr = 0  # hack count for textModified triggering twice
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
        return super(TweenMachine, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(TweenMachine, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def enterEvent(self, event):
        """Update selection on enter event
        """
        if not self.tweenInstance:
            self.notInstalled()
            return
        self.tweenInstance.tweenSel(self.properties.tweenFloatSlider.value,
                                    start=False,
                                    message=False)  # cache & do nothing

    def leaveEvent(self, event):
        if not self.tweenInstance:
            self.notInstalled()
            return
        self.tweenInstance.clearCache()  # resets for next session

    def notInstalled(self):
        output.displayWarning("Tween Machine Logic was not found in Community Scripts, so this UI cannot be used.")

    # -------------
    # COMMANDS
    # -------------

    def updateSlider(self, bias):
        self.properties.tweenFloatSlider.value = bias
        self.updateFromProperties()

    def tweenSliderPressed(self):
        """Start the tween"""
        self.openUndoChunk(name="zooTweenMachine")
        self.tweenInstance.pressed = True

    def tweenSliderMoved(self):
        """When the slider is moved.
        """
        self.tweenInstance.tween(self.properties.tweenFloatSlider.value)  # main tween on the existing cache

    def tweenSliderReleased(self):
        """After the slider is released finish the instance"""
        self.tweenInstance.successMessage()
        self.tweenInstance.keyStaticCurves()  # keys other curves that did not need value calculations.
        self.tweenInstance.pressed = False
        self.closeUndoChunk(name="zooTweenMachine")

    def tweenTextChanged(self):
        self.countr += self.countr
        if self.countr == 0:
            self.countr = 1  # Hack as is triggering twice, will trigger on second go.
            return
        self.tweenInstance.tweenCachedDataOnce(self.properties.tweenFloatSlider.value)

    def tweenSetBias(self, bias):
        self.updateSlider(bias)
        self.tweenInstance.tweenCachedDataOnce(bias)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        if not self.tweenInstance:
            self.notInstalled()
            return
        for widget in self.widgets():
            widget.tweenFloatSlider.sliderPressed.connect(self.tweenSliderPressed)
            widget.tweenFloatSlider.sliderReleased.connect(self.tweenSliderReleased)
            widget.tweenFloatSlider.numSliderChanged.connect(self.tweenSliderMoved)
            widget.tweenFloatSlider.textModified.connect(self.tweenTextChanged)
            bias = -0.25
            for btn in widget.tweenTickBtns:
                btn.clicked.connect(partial(self.tweenSetBias, bias=bias))
                bias += 0.125


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
        # Tween Slider ---------------------------------------
        tooltip = "Blends the selected animated object between the next & previous keyframes. \n" \
                  "Select objects with keys and run.  Keys the current frame. \n" \
                  "Select Objects (all curves) or Channel Box (filter curves) or Graph Editor Curves/Keys.\n\n" \
                  "Tween Machine is by Justin Barrett, updated by Wade Schneider & Andrew Silke"
        self.tweenFloatSlider = elements.FloatSlider(label="Tween",
                                                     defaultValue=0.5,
                                                     toolTip=tooltip,
                                                     sliderMin=-0.25,
                                                     sliderMax=1.25,
                                                     sliderRatio=3,
                                                     labelBtnRatio=1,
                                                     labelRatio=1,
                                                     editBoxRatio=2,
                                                     dynamicMin=True,
                                                     dynamicMax=True)
        # Tick Buttons Below Slider ---------------------------------------
        startValue = -0.25
        self.tweenTickBtns = list()
        for x in range(0, 13):
            toolTip = "{}".format(str(startValue))
            icon = "verticalBarThin" if (x % 2) else "verticalBar"  # thin if odd
            if startValue in [0.0, 0.5, 1.0]:
                height = 10
            else:
                height = 6 if (x % 2) else 6  # thin if odd
            self.tweenTickBtns.append(elements.styledButton("", icon,
                                                            toolTip=toolTip,
                                                            style=uic.BTN_TRANSPARENT_BG,
                                                            iconSize=8,
                                                            maxWidth=20,
                                                            btnHeight=height))
            startValue += 0.125


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
        # Spacer layout ---------------------
        blankLayout = elements.hBoxLayout(spacing=0)
        blankLayout.addItem(elements.Spacer(1, 1))  # nothing
        # Ticks inside layout ---------------------
        tickLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=0)

        for btn in self.tweenTickBtns:
            tickLayout.addWidget(btn, 1)
            tickLayout.setAlignment(btn, QtCore.Qt.AlignTop)
        # Ticks row layout ---------------------
        tickRowLayout = elements.hBoxLayout(spacing=0)
        tickRowLayout.addLayout(blankLayout, 34)
        tickRowLayout.addLayout(tickLayout, 100)
        # Vertical layout with no spacing between slider and ticks ---------------------
        sliderLayout = elements.vBoxLayout(spacing=0)
        sliderLayout.addWidget(self.tweenFloatSlider)
        sliderLayout.addLayout(tickRowLayout)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(sliderLayout)


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
        mainLayout.addWidget(self.tweenFloatSlider)
