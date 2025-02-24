""" ---------- Keyframe Randomizer -------------
Randomize animation keyframe UI.

Author: Andrew Silke
"""

from zoovendor.Qt import QtWidgets, QtCore

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output
from zoo.libs.maya.cmds.animation import randomizeanim, disableviewport, timerange

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

TIME_RANGE_COMBO_LIST = ["Playback Range", "Full Animation Range", "Custom Frame Range"]
DEFAULT_BAKE_STATE = True


class KeyRandomizer(toolsetwidget.ToolsetWidget):
    id = "keyRandomizer"
    info = "Randomizes Keyframe Animation"
    uiData = {"label": "Randomize Keyframes",
              "icon": "noise",
              "tooltip": "Randomizes Keyframe Animation.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-randomize-keyframes/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

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
        self.bakeKeysClicked()  # set the disable enable of the frequency float widget
        self.rangeComboChanged()  # set disable/enable of the start end
        self.randKeysObj = randomizeanim.RandomizeKeyframes()  # starts the logic instance
        self.showHideCacheButtons()
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
        return super(KeyRandomizer, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(KeyRandomizer, self).widgets()

    # ------------------
    # UI UPDATES
    # ------------------

    def enterEvent(self, event):
        """Update selection on enter event
        """
        index = self.properties.rangeOptionsCombo.value
        if index == 0:  # playback range auto
            self.properties.startEndFrameFloat.value = timerange.getRangePlayback()
        elif index == 1:  # full animation range so auto
            self.properties.startEndFrameFloat.value = timerange.getRangeAnimation()
        else:
            return
        self.updateFromProperties()

    def showHideCacheButtons(self):
        """Automatically shows/hides the Cache and Main buttons depending if self.graphCurveDict is empty or not.
        """
        cacheVis = False
        if self.randKeysObj.cacheExists():  # show the cache buttons and hide the main buttons
            cacheVis = True
        # Cache Buttons and Scale Slider
        self.compactWidget.clearCacheBtn.setVisible(cacheVis)
        self.compactWidget.reseedBtn.setVisible(cacheVis)
        self.compactWidget.resetBtn.setVisible(cacheVis)
        # Main Randomize Buttons
        self.compactWidget.randomizeKeyframesBtn.setVisible(not cacheVis)
        self.updateTree(delayed=True)  # Refresh GUI size

    def bakeKeysClicked(self):
        """Enables and disables the frequency in edit
        """
        if self.properties.bakeCheckbox.value:
            # enable frequency
            self.compactWidget.bakeFrequencyInt.setDisabled(False)
        else:
            # disable frequency
            self.compactWidget.bakeFrequencyInt.setDisabled(True)

    def rangeComboChanged(self):
        """Enables and disables the start End Frame Float widget
        """
        index = self.properties.rangeOptionsCombo.value
        if index == 0:  # playback range auto
            self.compactWidget.startEndFrameFloat.setDisabled(True)
            self.properties.startEndFrameFloat.value = timerange.getRangePlayback()
        elif index == 1:  # full animation range so auto
            self.compactWidget.startEndFrameFloat.setDisabled(True)
            self.properties.startEndFrameFloat.value = timerange.getRangeAnimation()
        elif index == 2:  # custom user range
            self.compactWidget.startEndFrameFloat.setDisabled(False)
            self.properties.startEndFrameFloat.value = timerange.getRangePlayback()
        self.updateFromProperties()  # updates all widgets

    def clearCache(self):
        """Clears the keyframe cache"""
        self.randKeysObj.clearCache()
        self.showHideCacheButtons()  # auto displays the correct buttons depending on self.graphCurveDict
        self.properties.randomRangeSlider.value = 1.0
        self.updateFromProperties()
        output.displayInfo("Animation has been applied, the `Randomize Cache` has been deleted")

    # ------------------------------------
    # OFFSET BTN VALUES - ALT CTRL SHIFT
    # ------------------------------------

    def cntrlShiftMultiplier(self, pos=True):
        """For offset functions multiply shift and minimise if ctrl is held down
        If alt then call the reset option

        :param pos: Is the button positive True or negative False?
        :type pos: bool

        :return multiplier: multiply value, .2 if ctrl 5 if shift 1 if None
        :rtype multiplier: float
        :return reset: reset becomes true for resetting
        :rtype reset: bool
        """
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if pos:
            if modifiers == QtCore.Qt.ShiftModifier:
                return 1.5, False
            elif modifiers == QtCore.Qt.ControlModifier:
                return 1.05, False
            elif modifiers == QtCore.Qt.AltModifier:
                return 1.0, True
            return 1.2, False
        # else neg
        if modifiers == QtCore.Qt.ShiftModifier:
            return 0.7, False
        elif modifiers == QtCore.Qt.ControlModifier:
            return 0.96, False
        elif modifiers == QtCore.Qt.AltModifier:
            return 1.0, True
        return 0.85, False

    # ------------------
    # LOGIC
    # ------------------

    def checkSelection(self):
        """Checks the selection and if no cache tries to build it

        :return cacheFound: True if there is a cache, False if not
        :rtype cacheFound: bool
        :return cacheStarted: True if the cache had to be started, False if it was already started
        :rtype cacheStarted: bool
        """
        if self.randKeysObj.cacheExists():  # cache exists so go
            return True, False
        self.randKeysObj.buildCacheCurvesSel()
        self.showHideCacheButtons()
        if not self.randKeysObj.cacheExists():  # still doesn't exist fail
            return False, True
        return True, True  # Exists now so go

    def plusPressed(self):
        """Plus button is pressed"""
        cacheFound, cacheStarted = self.checkSelection()
        if not cacheFound:
            return
        scaleValue, reset = self.cntrlShiftMultiplier(pos=True)
        if reset:
            self.resetGraphCurves()
            return
        self.properties.randomRangeSlider.value = scaleValue * self.properties.randomRangeSlider.value
        if cacheStarted:
            self.randKeysObj.clearCache()
            self.randomizeKeyframes()  # build from scratch
        else:
            self.randomizeFromCache()  # randomize existing
        self.updateFromProperties()

    def minusPressed(self):
        """Minus button is pressed"""
        cacheFound, cacheStarted = self.checkSelection()
        if not cacheFound:
            return
        scaleValue, reset = self.cntrlShiftMultiplier(pos=False)
        if reset:
            self.resetGraphCurves()
            return
        self.properties.randomRangeSlider.value = scaleValue * self.properties.randomRangeSlider.value
        if cacheStarted:
            self.randKeysObj.clearCache()
            self.randomizeKeyframes(setScale=False)  # build from scratch
        else:
            self.randomizeFromCache()  # randomize existing
        self.updateFromProperties()

    @disableviewport.disableViewportRefreshDec
    @toolsetwidget.ToolsetWidget.undoDecorator
    def randomizeKeyframes(self):
        """Does the randomize
        """
        self.randKeysObj.setRandomizeScale(self.properties.randomRangeSlider.value)
        self.randKeysObj.setTimeRange(self.properties.startEndFrameFloat.value)
        self.randKeysObj.setBakeState(self.properties.bakeCheckbox.value)
        self.randKeysObj.setBakeFrequency(float(self.properties.bakeFrequencyInt.value))
        self.randKeysObj.setTimeSliderMode(self.properties.rangeOptionsCombo.value)
        # Do the randomize
        self.randKeysObj.randomizeKeysSelection()
        # UI Update
        self.showHideCacheButtons()  # auto displays the correct buttons depending on self.randKeysObj.cacheExists()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def reseedCurves(self):
        """Reseed the curves, give them another random pass at the current scale values"""
        if not self.randKeysObj.cacheExists():
            return
        self.randKeysObj.setRandomizeScale(self.properties.randomRangeSlider.value)
        self.randKeysObj.reSeedKeys()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def resetGraphCurves(self):
        """Resets the curves to their value before the cache was set"""
        if not self.randKeysObj.cacheExists():
            return
        self.randKeysObj.resetKeys()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def randomizeFromCache(self, text=""):
        """Randomize from the cache, used with a text change on the slider for the undo"""
        if not self.randKeysObj.cacheExists():
            return
        self.randKeysObj.setRandomizeScale(self.properties.randomRangeSlider.value)
        self.randKeysObj.randomizeKeysFromCache()

    def sliderPressed(self):
        """Activates when the slider is pressed, starts the cache etc. On release uses self.closeUndoChunk()
        On the update uses self.interactiveScaleCenter()
        """
        self.openUndoChunk()
        disableviewport.suspendViewportUpdate(True)
        self.checkSelection()  # attempts to update the cache if there is none

    def interactiveScaleCenter(self):
        """Run when the scaleKeysByCenterDict is active and slider has been moved"""
        if not self.randKeysObj.cacheExists():
            return
        self.randKeysObj.setRandomizeScale(self.properties.randomRangeSlider.value)
        self.randKeysObj.randomizeKeysFromCache()

    def sliderReleased(self):
        """Run when the slider is released just updates the undo and viewport"""
        disableviewport.suspendViewportUpdate(False)
        self.closeUndoChunk()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.bakeCheckbox.stateChanged.connect(self.bakeKeysClicked)
            widget.rangeOptionsCombo.itemChanged.connect(self.rangeComboChanged)
            # buttons
            widget.randomizeKeyframesBtn.clicked.connect(self.randomizeKeyframes)
            widget.clearCacheBtn.clicked.connect(self.clearCache)
            widget.resetBtn.clicked.connect(self.resetGraphCurves)
            widget.reseedBtn.clicked.connect(self.reseedCurves)
            widget.plusBtn.clicked.connect(self.plusPressed)
            widget.minusBtn.clicked.connect(self.minusPressed)
            # Slider connections
            widget.randomRangeSlider.textModified.connect(self.randomizeFromCache)
            widget.randomRangeSlider.sliderChanged.connect(self.interactiveScaleCenter)
            widget.randomRangeSlider.sliderPressed.connect(self.sliderPressed)
            widget.randomRangeSlider.sliderReleased.connect(self.sliderReleased)


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
        # Bake Checkbox ---------------------------------------
        tooltip = "Bakes the frame range for the selected animation curves or Channel Box attributes."
        self.bakeCheckbox = elements.CheckBox(label="Bake Keys", checked=True, toolTip=tooltip, right=True,
                                              labelRatio=1, boxRatio=2)
        # Bake Frequency ---------------------------------------
        tooltip = "While baking set new keys every `frequency` of frames."
        self.bakeFrequencyInt = elements.IntEdit(label="Frequency",
                                                 editText=1,
                                                 toolTip=tooltip,
                                                 editRatio=2,
                                                 labelRatio=1)
        # Range Slider ---------------------------------------
        tooltip = "Sets the vertical value range of the random noise. \n" \
                  "Type larger or negative values for more range."
        self.randomRangeSlider = elements.FloatSlider(label="Random Amount", toolTip=tooltip, sliderMax=10.0,
                                                      sliderMin=0.0, decimalPlaces=4, defaultValue=1.0,
                                                      dynamicMax=True)
        # Time Range -------------------------------------------
        tooltip = "Set the time range to affect. Enable by setting to `Custom Frame Range` \n" \
                  "Use the Channel Box selection only with this setting."
        self.startEndFrameFloat = elements.VectorLineEdit(label="Start/End",
                                                          value=(1.0, 100.0),
                                                          axis=("start", "end"),
                                                          toolTip=tooltip,
                                                          editRatio=2,
                                                          labelRatio=1)
        # Use Time Slider Range Combo ----------------------------------
        tooltip = "Choose the time range to affect. Channel Box selection only. \n" \
                  " - Playback Range: Frames in the timeline while playing. \n" \
                  " - Full Animation Range: All frames in the min/max time slider setting. \n" \
                  " - Custom Range: User start and end frame."
        self.rangeOptionsCombo = elements.ComboBoxRegular(items=TIME_RANGE_COMBO_LIST,
                                                          setIndex=0,
                                                          toolTip=tooltip)
        # Randomize Keyframes Button ---------------------------------------
        tooltip = "Select `Graph Keys` or use the `Channel Box` selection and run. \n" \
                  "  - Graph Selection: Priority. Uses the selected keyframe's frame range. \n" \
                  "  - Channel Box Selection: Uses the timeline settings.\n" \
                  "Tweak the random scale after running. \n" \
                  "Click `Done` to finalize or to use another selection."
        self.randomizeKeyframesBtn = elements.styledButton("Randomize Keyframes",
                                                           icon="noise",
                                                           toolTip=tooltip,
                                                           style=uic.BTN_DEFAULT)
        # Reseed Button ---------------------------------------
        tooltip = "Randomize again using the same values."
        self.reseedBtn = elements.styledButton("Reseed",
                                               icon="noise",
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT)
        # Reset Button ---------------------------------------
        tooltip = "Reset the randomize to the original settings. "
        self.resetBtn = elements.styledButton("Reset",
                                              icon="reload",
                                              toolTip=tooltip,
                                              style=uic.BTN_DEFAULT)
        # Clear Cache Button ---------------------------------------
        tooltip = "Applies the current values, and clears the remembered cache for the scale slider tweaks"
        self.clearCacheBtn = elements.styledButton("Done (Restart)",
                                                   icon="checkOnly",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_DEFAULT)
        # Plus Button ---------------------------------------
        toolTip = "Increases the amount of random scale. \n" \
                  "Select curves and run. \n" \
                  "After starting the scale will affect the stored keys. \n" \
                  "Finalize the Randomize by clicking `Done`\n" \
                  "  Hold shift: faster \n" \
                  "  Hold ctrl: slower\n" \
                  "  Hold alt: Reset"
        self.plusBtn = elements.styledButton("",
                                             "plus",
                                             toolTip=toolTip,
                                             parent=parent,
                                             minWidth=uic.BTN_W_ICN_MED)
        # Neg Button ---------------------------------------
        toolTip = "Decreases the amount of random scale. \n" \
                  "Select curves and run. \n" \
                  "After starting the scale will affect the stored keys. \n" \
                  "Finalize the Randomize by clicking `Done`\n" \
                  "  Hold shift: faster \n" \
                  "  Hold ctrl: slower\n" \
                  "  Hold alt: Reset"
        self.minusBtn = elements.styledButton("",
                                              "minusSolid",
                                              toolTip=toolTip,
                                              parent=parent,
                                              minWidth=uic.BTN_W_ICN_MED)


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
        # Bake Layout -----------------------------
        bakeLayout = elements.hBoxLayout()
        bakeLayout.addWidget(self.bakeCheckbox, 1)
        bakeLayout.addWidget(self.bakeFrequencyInt, 1)
        # Time Range Layout -----------------------------
        timeRangeLayout = elements.hBoxLayout()
        timeRangeLayout.addWidget(self.rangeOptionsCombo, 1)
        timeRangeLayout.addWidget(self.startEndFrameFloat, 1)
        # Cache Btn Layout -----------------------------
        cacheButtonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        cacheButtonLayout.addWidget(self.randomizeKeyframesBtn, 8)
        cacheButtonLayout.addWidget(self.reseedBtn, 2)
        cacheButtonLayout.addWidget(self.resetBtn, 2)
        cacheButtonLayout.addWidget(self.clearCacheBtn, 4)
        cacheButtonLayout.addWidget(self.minusBtn, 1)
        cacheButtonLayout.addWidget(self.plusBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(bakeLayout)
        mainLayout.addLayout(timeRangeLayout)
        mainLayout.addWidget(self.randomRangeSlider)
        mainLayout.addLayout(cacheButtonLayout)


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
        # Bake Layout -----------------------------
        bakeLayout = elements.hBoxLayout()
        bakeLayout.addWidget(self.bakeCheckbox, 1)
        bakeLayout.addWidget(self.bakeFrequencyInt, 1)
        # Time Range Layout -----------------------------
        timeRangeLayout = elements.hBoxLayout()
        timeRangeLayout.addWidget(self.rangeOptionsCombo, 1)
        timeRangeLayout.addWidget(self.startEndFrameFloat, 1)
        # Button Layout -----------------------------
        buttonLayout = elements.hBoxLayout(margins=(0, uic.SREG, 0, 0))
        buttonLayout.addWidget(self.randomizeKeyframesBtn, 1)
        # Cache Btn Layout -----------------------------
        cacheButtonLayout = elements.hBoxLayout()
        cacheButtonLayout.addWidget(self.reseedBtn, 1)
        cacheButtonLayout.addWidget(self.resetBtn, 1)
        cacheButtonLayout.addWidget(self.clearCacheBtn, 2)

        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(elements.LabelDivider("Channel Box Options",
                                                   margins=(0, 0, 0, uic.SSML)))
        mainLayout.addLayout(bakeLayout)
        mainLayout.addLayout(timeRangeLayout)
        mainLayout.addWidget(elements.LabelDivider("All Options",
                                                   margins=(0, uic.LRGPAD, 0, uic.SSML)))
        mainLayout.addWidget(self.randomRangeSlider)
        mainLayout.addLayout(buttonLayout)
        mainLayout.addLayout(cacheButtonLayout)
