""" ---------- Animation Paths -------------

- Creates a CV Curve from an animated object's path
- Creates objects from an animated object's path
- Motion Path Button
- Ghosting Editor Button

Author: Andrew Silke
Credit:  Cleaned up faster code from the original script by Delano Athias
Credit URL: https://www.delanimation.com/tutorials-1/2020/1/2/generating-curves-from-motion-trails-in-maya
"""
from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.utils import mayaenv
from zoo.libs.maya.cmds.animation import motiontrail, generalanimation

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

MT_TRACKER_INST = motiontrail.ZooMotionTrailTrackerSingleton()


class AnimationPaths(toolsetwidget.ToolsetWidget):
    id = "animationPaths"
    info = "A UI for handling motion paths and cv curves."
    uiData = {"label": "Animation Paths/Trails",
              "icon": "motionTrail",
              "tooltip": "Template file for building new GUIs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-animation-paths/"}

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
        self._setDisabledEnabled()
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
        return super(AnimationPaths, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(AnimationPaths, self).widgets()

    # ------------------
    # UPDATE UI
    # ------------------

    def enterEvent(self, event):
        """When the cursor enters the UI update it"""
        self._refreshUI()

    def _refreshUI(self):
        """Refreshes the UI usually on mouse enter the UI"""
        self.properties.keyframeDotsVisCheckbox.value = MT_TRACKER_INST.keyDots_bool
        self.properties.everyFrameVisCheckbox.value = MT_TRACKER_INST.crosses_bool
        self.properties.frameSmallLargeCheckbox.value = MT_TRACKER_INST.frameSize_bool
        self.properties.altPastFutureCheckbox.value = MT_TRACKER_INST.pastFuture_bool
        self.properties.frameNumberVisCheckbox.value = MT_TRACKER_INST.frameNumbers_bool
        self.properties.limitBeforeAfterCheckbox.value = MT_TRACKER_INST.limitBeforeAfter_bool
        self.properties.limitMTrailAmountFloat.value = MT_TRACKER_INST.limitAmount
        self.updateFromProperties()

    def _setDisabledEnabled(self):
        """Enable disable frameSmallLargeCheckbox and limitMTrailAmountFloat"""
        if self.properties.limitBeforeAfterCheckbox.value:
            self.compactWidget.limitMTrailAmountFloat.setEnabled(True)
        else:
            self.compactWidget.limitMTrailAmountFloat.setEnabled(False)

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def cvCurveFromObjAnim(self):
        """Creates CV Curves from an animated object
        """
        motiontrail.cvCurveFromObjAnimationSelected(cvEveryFrame=self.properties.cvsPerFrameFloat.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def cloneObjsFromAnim(self):
        """Creates objects from an animated object
        """
        motiontrail.cloneObjsFromAnimationSelected(objToFrame=self.properties.objectsPerFrameFloat.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def openGhostEditor(self):
        """Open the Ghost Editor Window"""
        if mayaenv.mayaVersion() >= 2022:  # Should be already hidden in 2020 and below.
            generalanimation.openGhostEditor()

    # ------------------
    # MOTION TRAIL CHECKBOX CHANGES
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setAltPastFuture(self, xxx=None):
        """Checkbox set Alternatively or Past Future"""
        moTShapes = motiontrail.moTrailShapes(scene=True, selected=True)
        MT_TRACKER_INST.pastFuture_bool = self.properties.altPastFutureCheckbox.value
        if not moTShapes:
            return
        motiontrail.setPastFutureBool(moTShapes, self.properties.altPastFutureCheckbox.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setFrameCrossesVis(self, xxx=None):
        """Checkbox set Frame Crosses visible"""
        MT_TRACKER_INST.crosses_bool = self.properties.everyFrameVisCheckbox.value
        moTShapes = motiontrail.moTrailShapes(scene=True, selected=True)
        if not moTShapes:
            return
        motiontrail.setFrameCrossesBool(moTShapes, self.properties.everyFrameVisCheckbox.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setlimitBeforeAfter(self, state=None):
        """Checkbox set limit before after on/off"""
        self._setDisabledEnabled()
        MT_TRACKER_INST.limitBeforeAfter_bool = self.properties.limitBeforeAfterCheckbox.value
        MT_TRACKER_INST.limitAmount = self.properties.limitMTrailAmountFloat.value
        moTShapes = motiontrail.moTrailShapes(scene=True, selected=True)
        if not moTShapes:
            return
        motiontrail.setLimitBeforeAfterBool(moTShapes,
                                            self.properties.limitBeforeAfterCheckbox.value,
                                            framesIn=self.properties.limitMTrailAmountFloat.value,
                                            framesOut=self.properties.limitMTrailAmountFloat.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setFrameNumberVis(self, state=None):
        """Checkbox set the visibility of frame numbers"""
        MT_TRACKER_INST.frameNumbers_bool = self.properties.frameNumberVisCheckbox.value
        moTShapes = motiontrail.moTrailShapes(scene=True, selected=True)
        if not moTShapes:
            return
        motiontrail.setFrameNumbersBool(moTShapes, self.properties.frameNumberVisCheckbox.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setFrameSmallLarge(self, state=None):
        """Checkbox set the size of the frame markers"""
        MT_TRACKER_INST.frameSize_bool = self.properties.frameSmallLargeCheckbox.value
        moTShapes = motiontrail.moTrailShapes(scene=True, selected=True)
        if not moTShapes:
            return
        motiontrail.setFrameSizeBool(moTShapes, self.properties.frameSmallLargeCheckbox.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setMTrailVisibility(self, state=None):
        """Checkbox set the visibility of all trails"""
        moTShapes = motiontrail.moTrailShapes(scene=True, selected=True)
        if not moTShapes:
            return
        motiontrail.setVisibilityBool(moTShapes, self.properties.mTrailVisCheckbox.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setKeyframeDotsVisibility(self, state=None):
        """checkbox sets the visibility of the keyframe dots"""
        MT_TRACKER_INST.keyDots_bool = self.properties.keyframeDotsVisCheckbox.value
        moTShapes = motiontrail.moTrailShapes(scene=True, selected=True)
        if not moTShapes:
            return
        motiontrail.setKeyDotsVis(moTShapes, self.properties.keyframeDotsVisCheckbox.value)

    # ------------------
    # MOTION TRAIL BUTTONS
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createMotionTrail(self):
        """Creates or rebuilds motion trails from the selected objects"""
        motiontrail.createMotionTrailSelBools(MT_TRACKER_INST.keyDots_bool,
                                              MT_TRACKER_INST.crosses_bool,
                                              MT_TRACKER_INST.frameSize_bool,
                                              MT_TRACKER_INST.pastFuture_bool,
                                              MT_TRACKER_INST.frameNumbers_bool,
                                              MT_TRACKER_INST.limitBeforeAfter_bool,
                                              limitFrames=MT_TRACKER_INST.limitAmount)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteMotionTrails(self):
        """Delete all motion trails in the scene"""
        motiontrail.deleteMotionTrails(scene=True, selected=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectMotionTrails(self):
        """Select all motion trails in the scene"""
        motiontrail.selectMotionTrails()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def resetDisplayMotionTrails(self):
        """Reset the displace of selected or all motion trails in the scene"""
        motiontrail.resetMoTrialDefaultDisplay(scene=True, selected=True)
        MT_TRACKER_INST.resetDisplayDefaults()
        self._refreshUI()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.cvCurveFromKeysBtn.clicked.connect(self.cvCurveFromObjAnim)
            widget.objectsFromKeysBtn.clicked.connect(self.cloneObjsFromAnim)
            widget.motionPathBtn.clicked.connect(self.createMotionTrail)
            widget.deleteMotionTrailsBtn.clicked.connect(self.deleteMotionTrails)
            widget.selectMotionTrailsBtn.clicked.connect(self.selectMotionTrails)
            widget.resetMotionTrailsBtn.clicked.connect(self.resetDisplayMotionTrails)
            widget.openGhostEditorBtn.clicked.connect(self.openGhostEditor)
            # Checkboxes changed
            widget.altPastFutureCheckbox.stateChanged.connect(self.setAltPastFuture)
            widget.limitBeforeAfterCheckbox.stateChanged.connect(self.setlimitBeforeAfter)
            widget.frameNumberVisCheckbox.stateChanged.connect(self.setFrameNumberVis)
            widget.frameSmallLargeCheckbox.stateChanged.connect(self.setFrameSmallLarge)
            widget.mTrailVisCheckbox.stateChanged.connect(self.setMTrailVisibility)
            widget.keyframeDotsVisCheckbox.stateChanged.connect(self.setKeyframeDotsVisibility)
            widget.everyFrameVisCheckbox.stateChanged.connect(self.setFrameCrossesVis)
            # Text changed
            widget.limitMTrailAmountFloat.textModified.connect(self.setlimitBeforeAfter)


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
        # CVs Per Frame Float Box ---------------------------------------
        tooltip = "Creates a CV NURBS Curve from the selected object/s motion paths. \n" \
                  "Uses the Playback Range in the Time Slider. \n" \
                  "CVs are placed once every `x` frames."
        self.cvsPerFrameFloat = elements.FloatEdit(label="CVs/Frame Ratio",
                                                   editText=1.0,
                                                   toolTip=tooltip)
        # CV Curve From Keys ---------------------------------------
        self.cvCurveFromKeysBtn = elements.AlignedButton("CV Curve From Anim",
                                                         icon="splineCVs",
                                                         toolTip=tooltip)
        # Object/Frame Float Box ---------------------------------------
        tooltip = "Duplicates the selected object/s along their animation paths. \n" \
                  "Uses the Playback Range in the Time Slider. \n" \
                  "Objects are placed once every `x` frames."
        self.objectsPerFrameFloat = elements.FloatEdit(label="Obj/Frame Ratio",
                                                       editText=10.0,
                                                       toolTip=tooltip)
        # Objects From Keys ---------------------------------------
        self.objectsFromKeysBtn = elements.AlignedButton("Objects From Anim",
                                                         icon="objectsOnCurve",
                                                         toolTip=tooltip)

        # CV Curve From Keys ---------------------------------------
        tooltip = "Opens Maya's Ghost Editor Window. \n" \
                  "Uses the current Playback Range in the Time Slider \n" \
                  "Zoo Hotkey: shift alt }"
        self.openGhostEditorBtn = elements.styledButton("Open Ghost Editor",
                                                        icon="ghosting",
                                                        toolTip=tooltip,
                                                        minWidth=uic.BTN_W_ICN_MED,
                                                        parent=self)

        # ------------------ MOTION PATHS ------------------
        # Motion Trail Options ----------------------------------------------------------------------------------------
        self.moTrailOptionsCollapsable = elements.CollapsableFrameThin("Motion Trail Options", collapsed=True)

        # Limit Before Checkbox ---------------------------------------
        tooltip = "Limits the trails to only display a specified number \n" \
                  "before and after the current frame. "
        self.limitBeforeAfterCheckbox = elements.CheckBox(label="Limit Before/After",
                                                          checked=MT_TRACKER_INST.limitBeforeAfter_bool,
                                                          toolTip=tooltip)
        # Every Frame Crosses ---------------------------------------
        tooltip = "Shows every frame as cross markers."
        self.everyFrameVisCheckbox = elements.CheckBox(label="Every Frame Visibility",
                                                       checked=MT_TRACKER_INST.crosses_bool,
                                                       toolTip=tooltip)
        # Frame Display Small Large Checkbox ---------------------------------------
        tooltip = "Displays the frame elements as either large or small."
        self.frameSmallLargeCheckbox = elements.CheckBox(label="Frame Display Small/Large",
                                                         checked=MT_TRACKER_INST.frameSize_bool,
                                                         toolTip=tooltip)
        # Keyframe Dots Vis Checkbox ---------------------------------------
        tooltip = "Shows each keyframe as dots."
        self.keyframeDotsVisCheckbox = elements.CheckBox(label="Keyframe Dot Visibility",
                                                         checked=MT_TRACKER_INST.keyDots_bool,
                                                         toolTip=tooltip)
        # Show Frame Numbers Checkbox ---------------------------------------
        tooltip = "Displays keyframe number visibility."
        self.frameNumberVisCheckbox = elements.CheckBox(label="Frame Number Visibility",
                                                        checked=MT_TRACKER_INST.frameNumbers_bool,
                                                        toolTip=tooltip)
        # Alternating Past Future Checkbox ---------------------------------------
        tooltip = "Affects the curve draw style: \n" \
                  " - Alternate Frame display (off) \n" \
                  " - Past Future display (on)"
        self.altPastFutureCheckbox = elements.CheckBox(label="Alternating or Past/Future",
                                                       checked=MT_TRACKER_INST.pastFuture_bool,
                                                       toolTip=tooltip)
        # Trail Visibility Checkbox ---------------------------------------
        tooltip = "Show or hide all motion trails in the scene."
        self.mTrailVisCheckbox = elements.CheckBox(label="Motion Trails Visibility",
                                                   checked=True,
                                                   toolTip=tooltip)

        # Limit Before After Amount --------------------------------------
        tooltip = "The amount of frames to show if the Limit Before/After Checkbox is on. "
        self.limitMTrailAmountFloat = elements.FloatEdit(label="Limit Frames",
                                                         editText=MT_TRACKER_INST.limitAmount,
                                                         toolTip=tooltip)

        # MotionPath Button ---------------------------------------
        tooltip = "Creates a motion trail on the selected object/s.\n" \
                  "If a motion trail already exists it will be rebuilt. \n" \
                  "If nothing is selected all trails will be rebuilt. \n" \
                  "Uses the current Playback Range in the Time Slider\n\n" \
                  "Zoo Hotkey: ' (marking menu)"
        self.motionPathBtn = elements.styledButton("Create/Rebuild Motion Trail",
                                                   icon="motionTrail",
                                                   toolTip=tooltip,
                                                   minWidth=uic.BTN_W_ICN_MED,
                                                   parent=self)
        # Delete All Motion Paths Button ---------------------------------------
        tooltip = "Deletes all motion trails in the scene."
        self.deleteMotionTrailsBtn = elements.styledButton("All Trails",
                                                           icon="trash",
                                                           toolTip=tooltip,
                                                           minWidth=uic.BTN_W_ICN_MED,
                                                           parent=self)
        # Delete All Motion Paths Button ---------------------------------------
        tooltip = "Selects all motion trails in the scene."
        self.selectMotionTrailsBtn = elements.styledButton("",
                                                           icon="cursorSelect",
                                                           toolTip=tooltip,
                                                           minWidth=uic.BTN_W_ICN_MED,
                                                           parent=self)
        # Delete All Motion Paths Button ---------------------------------------
        tooltip = "Resets the display settings of all or selected motion trails in the scene."
        self.resetMotionTrailsBtn = elements.styledButton("",
                                                          icon="refresh",
                                                          toolTip=tooltip,
                                                          minWidth=uic.BTN_W_ICN_MED,
                                                          parent=self)
        if mayaenv.mayaVersion() < 2022:
            self.openGhostEditorBtn.setVisible(False)


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
                                         spacing=uic.SPACING)
        # CV Curve Layout ---------------------------------------
        cvCurveLayout = elements.hBoxLayout(spacing=uic.SPACING)
        cvCurveLayout.addWidget(self.cvsPerFrameFloat, 1)
        cvCurveLayout.addWidget(self.cvCurveFromKeysBtn, 1)
        # Object Clone Layout ---------------------------------------
        objectLayout = elements.hBoxLayout(spacing=uic.SPACING)
        objectLayout.addWidget(self.objectsPerFrameFloat, 1)
        objectLayout.addWidget(self.objectsFromKeysBtn, 1)

        # Motion Trail Options Layout -----------------------------
        mTrailOptionsLayout = elements.GridLayout(spacing=uic.SVLRG,
                                                  margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD,))
        row = 0
        mTrailOptionsLayout.addWidget(self.mTrailVisCheckbox, row, 0)
        mTrailOptionsLayout.addWidget(self.everyFrameVisCheckbox, row, 1)
        row += 1
        mTrailOptionsLayout.addWidget(self.altPastFutureCheckbox, row, 0)
        mTrailOptionsLayout.addWidget(self.keyframeDotsVisCheckbox, row, 1)
        row += 1
        mTrailOptionsLayout.addWidget(self.frameNumberVisCheckbox, row, 0)
        mTrailOptionsLayout.addWidget(self.frameSmallLargeCheckbox, row, 1)
        row += 1
        mTrailOptionsLayout.addWidget(self.limitBeforeAfterCheckbox, row, 0)
        mTrailOptionsLayout.addWidget(self.limitMTrailAmountFloat, row, 1)
        mTrailOptionsLayout.setColumnStretch(0, 1)
        mTrailOptionsLayout.setColumnStretch(1, 1)

        # Collapsable & Connections -------------------------------------
        self.moTrailOptionsCollapsable.hiderLayout.addLayout(mTrailOptionsLayout)
        self.moTrailOptionsCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.collapseLayout = elements.vBoxLayout(margins=(0, uic.SREG, 0, 0))  # adds top margin above title
        self.collapseLayout.addWidget(self.moTrailOptionsCollapsable)

        # Motion Trail Button Layout -----------------------------
        motionTrailBtnLayout = elements.hBoxLayout(spacing=uic.SPACING)
        motionTrailBtnLayout.addWidget(self.motionPathBtn, 10)
        motionTrailBtnLayout.addWidget(self.deleteMotionTrailsBtn, 5)
        motionTrailBtnLayout.addWidget(self.selectMotionTrailsBtn, 1)
        motionTrailBtnLayout.addWidget(self.resetMotionTrailsBtn, 1)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(cvCurveLayout)
        mainLayout.addLayout(objectLayout)
        mainLayout.addWidget(self.openGhostEditorBtn)
        mainLayout.addLayout(self.collapseLayout)
        mainLayout.addLayout(motionTrailBtnLayout)


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
        mainLayout.addWidget(self.cvsPerFrameFloat)
        mainLayout.addWidget(self.cvCurveFromKeysBtn)
