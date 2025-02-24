""" ---------- Bake Animation -------------
Simple UI for baking keyframes.

Author: Andrew Silke
"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements


from zoo.libs.maya.cmds.animation import bakeanim, timerange, generalanimation

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

TIME_RANGE_COMBO_LIST = ["Playback/Sel Range", "Full Animation Range", "Custom Frame Range"]


class BakeAnimation(toolsetwidget.ToolsetWidget):
    id = "bakeAnimation"
    info = "Simple UI for Keyframe baking."
    uiData = {"label": "Bake Animation",
              "icon": "bake",
              "tooltip": "Simple UI for Keyframe baking.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-bake-animation/"}

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

    def postContentSetup(self):
        """Last of the initialize code"""
        self.rangeComboChanged()  # set disable/enable of the start end
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
        return super(BakeAnimation, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(BakeAnimation, self).widgets()

    # ------------------
    # UI UPDATES
    # ------------------

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

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def bakeAnimation(self):
        bakeanim.bakeSelected(timeRange=self.properties.startEndFrameFloat.value,
                              timeSlider=self.properties.rangeOptionsCombo.value,
                              bakeFrequency=self.properties.bakeFrequencyInt.value,
                              shapes=self.properties.includeShapesCheckbox.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def eulerFilter(self):
        """Runs Maya's Euler Filter for rotation keyframes"""
        generalanimation.eulerFilter()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.rangeOptionsCombo.itemChanged.connect(self.rangeComboChanged)
            widget.bakeAnimationBtn.clicked.connect(self.bakeAnimation)
            widget.eulerFilterBtn.clicked.connect(self.eulerFilter)


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
        # Bake Frequency ---------------------------------------
        tooltip = "Bake by setting keys every `frequency` of frames."
        self.bakeFrequencyInt = elements.FloatEdit(label="Frequency",
                                                   editText=1.0,
                                                   toolTip=tooltip,
                                                   editRatio=2,
                                                   labelRatio=1,
                                                   slideDist=0.25, smallSlideDist=0.1, largeSlideDist=1.0)
        # Keep Unbaked Keys ---------------------------------------
        tooltip = "Include shape nodes in the `bake all attributes`. \n" \
                  "Is only used with `Bake All Attributes` (with no graph curves or channels selected)."
        self.includeShapesCheckbox = elements.CheckBox(label="Include Shape Nodes",
                                                       checked=False,
                                                       toolTip=tooltip,
                                                       right=True,
                                                       boxRatio=1,
                                                       labelRatio=10)
        # Time Range -------------------------------------------
        tooltip = "Set the time range to bake, must be set to `Custom Frame Range` \n" \
                  "Start frame - end frame"
        self.startEndFrameFloat = elements.VectorLineEdit(label="Start/End",
                                                          value=(1.0, 100.0),
                                                          axis=("start", "end"),
                                                          toolTip=tooltip,
                                                          editRatio=2,
                                                          labelRatio=1)
        # Use Time Slider Range Combo ----------------------------------
        tooltip = "Choose the time range to affect, used only with Channel Box selection. \n" \
                  " - Playback Range: Frames in the timeline or selected (red range). \n" \
                  " - Full Animation Range: All frames in the min/max time slider setting. \n" \
                  " - Custom Range: User start and end frame. "
        self.rangeOptionsCombo = elements.ComboBoxRegular(items=TIME_RANGE_COMBO_LIST,
                                                          setIndex=0,
                                                          toolTip=tooltip)
        # Bake Button ---------------------------------------
        tooltip = "Bake Animation based on selection: \n" \
                  " 1. Graph keyframe selection.  (Time Range is ignored)\n" \
                  " 2. Channel Box selection. \n" \
                  " 3. If no channels are selected will bake all attributes."
        self.bakeAnimationBtn = elements.AlignedButton("Bake Animation",
                                                       icon="bake",
                                                       toolTip=tooltip)
        # Euler Filter Button ---------------------------------------
        tooltip = "Euler Rotations for fixing flipping rotation keys.  Fix gimbal lock flips. \n" \
                  "Select objects and run.  Objects rotation values will be affected."
        self.eulerFilterBtn = elements.AlignedButton("Euler Filter",
                                                     icon="eulerFilter",
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
        # Bake Layout -----------------------------
        bakeLayout = elements.hBoxLayout()
        bakeLayout.addWidget(self.bakeFrequencyInt, 1)
        bakeLayout.addWidget(self.includeShapesCheckbox, 1)
        # Time Range Layout -----------------------------
        timeRangeLayout = elements.hBoxLayout()
        timeRangeLayout.addWidget(self.rangeOptionsCombo, 1)
        timeRangeLayout.addWidget(self.startEndFrameFloat, 1)
        # Button Layout -----------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        buttonLayout.addWidget(self.bakeAnimationBtn, 1)
        buttonLayout.addWidget(self.eulerFilterBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(timeRangeLayout)
        mainLayout.addLayout(bakeLayout)
        mainLayout.addLayout(buttonLayout)
