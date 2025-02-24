""" ---------- Scale Keys From Center -------------
Uses the current graph curve selection to scale keys with a different center pivot for each curve.
Automatically detects the center of each curve selection and value scales from that pivot per curve.
Useful for animation noise random jitter.

Author: Andrew Silke based off the original mel tool by David Peers
"""

from zoovendor.Qt import QtWidgets, QtCore

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output
from zoo.libs.maya.cmds.animation import scaleretime, disableviewport

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ScaleKeysFromCenter(toolsetwidget.ToolsetWidget):
    id = "scaleKeysFromCenter"
    info = "Automatically detects the center of each curve selection and value scales from that pivot per curve."
    uiData = {"label": "Scale Keys From Center Values",
              "icon": "scaleKeyCenter",
              "tooltip": "Automatically detects the center of each curve selection and value scales from that pivot "
                         "per curve.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-scale-keys-center-values/"}

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
        self.scaleLogic = scaleretime.ScaleKeysCenter()  # Logic class object, empty ready to go.
        self.scaleLogic.setMode(scaleretime.AVERAGE_MODES[self.properties.scaleOptionsRadio.value])  # setMode from UI
        self.scaleLogic.clearCache()
        self.showHideCacheButtons()  # Hides buttons ready for tool
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
        return super(ScaleKeysFromCenter, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ScaleKeysFromCenter, self).widgets()

    # ------------------
    # UI UPDATES
    # ------------------

    def showHideCacheButtons(self):
        """Automatically shows/hides the Cache and Main buttons depending if self.graphCurveDict is empty or not.
        """
        cacheVis = False
        if self.scaleLogic.scaleCacheDict:  # Show the cache buttons and hide the main buttons
            cacheVis = True
        for widget in self.widgets():
            # Cache Buttons and Scale Slider
            widget.resetBtn.setVisible(cacheVis)
            widget.recalculateCacheBtn.setVisible(cacheVis)
            # Cache buttons
            widget.scaleCenterCacheBtn.setVisible(not cacheVis)
        self.updateTree(delayed=True)  # Refresh GUI size

    def optionsRadioChanged(self):
        """Display a warning if there's already a cache"""
        if self.scaleLogic.scaleCacheDict:
            self.scaleLogic.setMode(scaleretime.AVERAGE_MODES[self.properties.scaleOptionsRadio.value])

    # ------------------------------------
    # OFFSET BTN VALUES - CTRL SHIFT ALT
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
                return 2.0, False
            elif modifiers == QtCore.Qt.ControlModifier:
                return 1.1, False
            elif modifiers == QtCore.Qt.AltModifier:
                return 1.0, True
            return 1.25, False
        # else neg
        if modifiers == QtCore.Qt.ShiftModifier:
            return 0.25, False
        elif modifiers == QtCore.Qt.ControlModifier:
            return 0.9, False
        elif modifiers == QtCore.Qt.AltModifier:
            return 1.0, True
        return 0.75, False

    # ------------------
    # LOGIC
    # ------------------

    def checkSelection(self):
        if self.scaleLogic.scaleCacheDict:  # cache exists so go
            return True
        self.scaleFromCenterCache()  # Doesn't exist so attempt update
        if not self.scaleLogic.scaleCacheDict:  # still doesn exist fail
            return False
        return True  # Exists now so go

    @toolsetwidget.ToolsetWidget.undoDecorator
    def resetScale(self):
        """Reset from the cache"""
        if not self.scaleLogic.scaleCacheDict:
            return
        self.scaleLogic.resetScale()
        self.scaleLogic.setScaleAmount(1.0)
        # UI
        self.properties.updateScaleSlider.value = 1.0
        self.showHideCacheButtons()
        self.updateFromProperties()

    def invertScale(self):
        """Inverts the scale from the current value"""
        if not self.checkSelection():
            return
        if self.scaleLogic.scaleCacheDict:
            self.properties.updateScaleSlider.value = -self.properties.updateScaleSlider.value
            self.scaleFromCenter()
        else:
            self.displayWarning()

    def recalculateCache(self):
        """Reset from the cache"""
        self.scaleLogic.clearCache()

        self.scaleFromCenterCache()

    def plusPressed(self):
        """Plus button is pressed"""
        if not self.checkSelection():
            return
        scaleValue, reset = self.cntrlShiftMultiplier(pos=True)
        if reset:
            self.resetScale()
            return
        self.properties.updateScaleSlider.value = (scaleValue - 1.0) + self.properties.updateScaleSlider.value
        self.scaleFromCenter()

    def minusPressed(self):
        """Minus button is pressed"""
        if not self.checkSelection():
            return
        scaleValue, reset = self.cntrlShiftMultiplier(pos=False)
        if reset:
            self.resetScale()
            return
        self.properties.updateScaleSlider.value = (scaleValue - 1.0) + self.properties.updateScaleSlider.value
        self.scaleFromCenter()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def scaleFromCenterCache(self):
        """Starts the cache and doesn't scale"""
        self.scaleLogic.setMode(scaleretime.AVERAGE_MODES[self.properties.scaleOptionsRadio.value])
        self.scaleLogic.cacheDictFromSelected()
        if self.scaleLogic.scaleCacheDict:  # If the cache exists
            self.properties.updateScaleSlider.value = 1.0
            self.updateFromProperties()
            output.displayInfo("Cache has been started based off the current selection.")
        self.showHideCacheButtons()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def scaleFromCenter(self):
        """Main function that scales off the the cache, if none will attempt to create one

        The cache is self.scaleLogic.scaleCacheDict:

            Curve (key), IndexList, ValueList, MidPoint (float)
            {'pCube1_translateX': [[(22, 22), (33, 33)], [10.0, 0.0], 5.0]}

        """
        if not self.scaleLogic.scaleCacheDict:
            self.scaleLogic.cacheDictFromSelected()
            self.showHideCacheButtons()
            self.updateFromProperties()
            if not self.scaleLogic.scaleCacheDict:
                return  # message already sent
        self.scaleLogic.setScaleAmount(self.properties.updateScaleSlider.value)  # Update scale value
        self.scaleLogic.scaleKeysCenter()  # Do the scale
        self.updateFromProperties()

    def sliderPressed(self):
        """Activates when the slider is pressed, starts the cache etc. On release uses self.closeUndoChunk()
        On the update uses self.interactiveScaleCenter()
        """
        self.openUndoChunk()
        disableviewport.suspendViewportUpdate(True)
        if not self.scaleLogic.scaleCacheDict:
            self.scaleLogic.cacheDictFromSelected()  # starts the cache
            self.showHideCacheButtons()
            if not self.scaleLogic.scaleCacheDict:
                self.scaleLogic.setScaleAmount(1.0)
                self.properties.updateScaleSlider.value = 1.0
                self.updateFromProperties()
                return  # message sent

    def sliderReleased(self):
        """Run when the slider is released just updates the undo and viewport"""
        disableviewport.suspendViewportUpdate(False)
        self.closeUndoChunk()

    def interactiveScaleCenter(self):
        """Run when the scaleKeysByCenterDict is active and slider has been moved"""
        if not self.scaleLogic.scaleCacheDict:
            return
        self.scaleLogic.setScaleAmount(self.properties.updateScaleSlider.value)  # Set scale value
        self.scaleLogic.scaleKeysCenter()  # Do the scale

    @toolsetwidget.ToolsetWidget.undoDecorator
    def scaleTextChanged(self, text):
        """Run when the slider text is changed for undo"""
        if not self.scaleLogic.scaleCacheDict:
            self.scaleLogic.cacheDictFromSelected()
            self.showHideCacheButtons()
            if not self.scaleLogic.scaleCacheDict:
                return  # message already sent
        self.scaleLogic.setScaleAmount(self.properties.updateScaleSlider.value)  # Set scale value
        self.scaleLogic.scaleKeysCenter()  # Do the scale

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.scaleOptionsRadio.toggled.connect(self.optionsRadioChanged)  # On change
            widget.resetBtn.clicked.connect(self.resetScale)
            widget.invertBtn.clicked.connect(self.invertScale)
            widget.plusBtn.clicked.connect(self.plusPressed)
            widget.minusBtn.clicked.connect(self.minusPressed)
            widget.recalculateCacheBtn.clicked.connect(self.recalculateCache)
            widget.scaleCenterCacheBtn.clicked.connect(self.scaleFromCenterCache)
            # Slider connections
            widget.updateScaleSlider.textModified.connect(self.scaleTextChanged)
            widget.updateScaleSlider.sliderChanged.connect(self.interactiveScaleCenter)
            widget.updateScaleSlider.sliderPressed.connect(self.sliderPressed)
            widget.updateScaleSlider.sliderReleased.connect(self.sliderReleased)


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
        # Options Combo ---------------------------------------
        tooltip1 = "Average: Scales from the average of all selected value keys."
        tooltip2 = "Max Min Center: Scales from the mid point of the max and min keys. "
        self.scaleOptionsRadio = elements.RadioButtonGroup(radioList=["Use Average Center", "Use Max/Min Center"],
                                                           default=1,
                                                           toolTipList=[tooltip1, tooltip2],
                                                           margins=[uic.REGPAD, uic.SMLPAD, uic.REGPAD, uic.SMLPAD])
        # Scale Cached ---------------------------------------
        tooltip = "Scales from the value center of each curve. \n" \
                  "Select curves and use the slider, after starting the scale will affect the remembered keys. \n" \
                  "Add a new selection by clicking `Update Selection`."
        self.updateScaleSlider = elements.FloatSlider(label="", toolTip=tooltip, sliderMax=4.0,
                                                      sliderMin=0.0, decimalPlaces=4, defaultValue=1.0,
                                                      dynamicMax=True, dynamicMin=True, editBoxRatio=1, sliderRatio=5)
        # Invert Button ---------------------------------------
        tooltip = "Invert the curve values from the center value of each curve. \n" \
                  "Select curves and run, after starting the scale will affect the remembered keys. \n" \
                  "Reset the selection by clicking `Update Selection`."
        self.invertBtn = elements.styledButton("Invert",
                                               icon="invert",
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT)
        # Reset Button ---------------------------------------
        tooltip = "Reset to the remembered keyframe values before the scale was performed."
        self.resetBtn = elements.styledButton("Reset",
                                              icon="reload",
                                              toolTip=tooltip,
                                              style=uic.BTN_DEFAULT)
        # Plus Button ---------------------------------------
        toolTip = "Increase the scale from the value center of each curve. \n" \
                  "Select curves and run, after starting the scale will affect the remembered keys." \
                  "Reset the selection by clicking `Update Selection`\n" \
                  "  Hold shift: faster \n" \
                  "  Hold ctrl: slower\n" \
                  "  Hold alt: Reset"
        self.plusBtn = elements.styledButton("",
                                             "plus",
                                             toolTip=toolTip,
                                             parent=parent,
                                             minWidth=uic.BTN_W_ICN_MED)
        # Neg Button ---------------------------------------
        toolTip = "Decrease the scale from the value center of each curve. \n" \
                  "Select curves and run, after starting the scale will affect the remembered keys." \
                  "Reset the selection by clicking `Update Selection`\n" \
                  "  Hold shift: faster \n" \
                  "  Hold ctrl: slower \n" \
                  "  Hold alt: Reset"
        self.minusBtn = elements.styledButton("",
                                              "minusSolid",
                                              toolTip=toolTip,
                                              parent=parent,
                                              minWidth=uic.BTN_W_ICN_MED)
        # Clear Cache Button ---------------------------------------
        tooltip = "Select new keyframes and run to use a new selection of keyframes. "
        self.recalculateCacheBtn = elements.styledButton("Update Selection",
                                                         icon="checkOnly",
                                                         toolTip=tooltip,
                                                         style=uic.BTN_DEFAULT)
        # Scale Center Curve - Start Cache ---------------------------------------
        tooltip = "Start the scale by selecting keyframes in the Graph Editor \n" \
                  "The scale is perfromed by the center value scale of each graph curve."
        self.scaleCenterCacheBtn = elements.styledButton("Start Center Scale",
                                                         icon="scaleKeyCenter",
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
        # Cache Btn Layout -----------------------------
        cacheButtonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        cacheButtonLayout.addWidget(self.resetBtn, 2)
        cacheButtonLayout.addWidget(self.recalculateCacheBtn, 4)
        cacheButtonLayout.addWidget(self.scaleCenterCacheBtn, 6)
        cacheButtonLayout.addWidget(self.invertBtn, 2)
        cacheButtonLayout.addWidget(self.minusBtn, 1)
        cacheButtonLayout.addWidget(self.plusBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.updateScaleSlider)
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
        # Cache Btn Layout -----------------------------
        cacheButtonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        cacheButtonLayout.addWidget(self.resetBtn, 2)
        cacheButtonLayout.addWidget(self.recalculateCacheBtn, 4)
        cacheButtonLayout.addWidget(self.scaleCenterCacheBtn, 6)
        cacheButtonLayout.addWidget(self.invertBtn, 2)
        cacheButtonLayout.addWidget(self.minusBtn, 1)
        cacheButtonLayout.addWidget(self.plusBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.scaleOptionsRadio)
        mainLayout.addWidget(self.updateScaleSlider)
        mainLayout.addLayout(cacheButtonLayout)
