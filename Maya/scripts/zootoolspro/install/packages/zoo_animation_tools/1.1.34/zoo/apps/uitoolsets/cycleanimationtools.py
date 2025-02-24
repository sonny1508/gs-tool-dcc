""" ---------- Toolset Boiler Plate (Multiple UI Modes) -------------
The following code is a template (boiler plate) for building Zoo Toolset GUIs that multiple UI modes.

Multiple UI modes include compact and medium or advanced modes.

This UI will use Compact and Advanced Modes.

The code gets more complicated while dealing with UI Modes.

"""
from functools import partial

from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs import iconlib
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.animation import timerange, grapheditorfcurve, bakeanim, mirroranimation, animconstants, \
    generalanimation

try:
    from zoo.libs.hive.anim import mirroranim
    HIVE_ACTIVE = True
except:  # Hive Package is not loaded
    HIVE_ACTIVE = False

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

CYCLE_LIST = ["constant", "linear", "cycle", "cycleRelative", "oscillate"]
FLIP_PRESETS = ["No Mirror - Copy Only", "Mirror - World Controls", "Mirror - Joint Children Regular FK",
                "Mirror - Joint World Parent"]
FLIP_PRESET_NONE = [False, False, False, False, False, False]
FLIP_PRESET_WORLD = [True, False, False, False, True, True]
FLIP_PRESET_FKREG = [True, True, True, False, False, False]
FLIP_PRESET_FKWORLD = [True, False, False, False, False, False]
FLIP_VAL_LIST = [FLIP_PRESET_NONE, FLIP_PRESET_WORLD, FLIP_PRESET_FKREG, FLIP_PRESET_FKWORLD]


class CycleAnimationTools(toolsetwidget.ToolsetWidget):
    id = "cycleAnimationTools"
    info = "Tools related to animation cycles."
    uiData = {"label": "Cycle Animation Tools",
              "icon": "sineWave",
              "tooltip": "Tools related to animation cycles.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-cycle-animation-tools"}

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
        self.setPreset()
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
        return super(CycleAnimationTools, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(CycleAnimationTools, self).widgets()

    # ------------------
    # UI & UPDATE
    # ------------------

    def setPreset(self):
        """Sets the UI checkboxes from the combo box settings"""
        xyzSettings = FLIP_VAL_LIST[self.properties.presetFlipCombo.value]
        self.properties.translateXCheckbox.value = xyzSettings[0]
        self.properties.translateYCheckbox.value = xyzSettings[1]
        self.properties.translateZCheckbox.value = xyzSettings[2]
        self.properties.rotateXCheckbox.value = xyzSettings[3]
        self.properties.rotateYCheckbox.value = xyzSettings[4]
        self.properties.rotateZCheckbox.value = xyzSettings[5]
        self.updateFromProperties()

    def flipAttrs(self):
        """Returns all the flip checkboxes as an attribute list if they are on.

            ["translateX", "rotateY"]

        :return flipAttrList:
        :rtype flipAttrList:
        """
        flipAttrList = list()
        if self.properties.translateXCheckbox.value:
            flipAttrList.append("translateX")
        if self.properties.translateYCheckbox.value:
            flipAttrList.append("translateY")
        if self.properties.translateZCheckbox.value:
            flipAttrList.append("translateZ")
        if self.properties.rotateXCheckbox.value:
            flipAttrList.append("rotateX")
        if self.properties.rotateYCheckbox.value:
            flipAttrList.append("rotateY")
        if self.properties.rotateZCheckbox.value:
            flipAttrList.append("rotateZ")
        return flipAttrList

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def cycleAnimation(self, pre=True, post=True):
        """Cycles the animation either pre or post or both"""
        generalanimation.cycleAnimation(cycleMode=self.properties.cycleCombo.value,
                                        pre=pre,
                                        post=post,
                                        displayInfinity=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def removeCycleAnimation(self):
        generalanimation.removeCycleAnimation()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def toggleInfinity(self):
        generalanimation.toggleInfinity()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def limitKeysToTimerange(self):
        """
        """
        bakeanim.bakeLimitKeysToTimerangeSel(self.properties.startFloatEdit.value,
                                             self.properties.endFloatEdit.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def autoTangentCycle(self):
        grapheditorfcurve.autoTangentCycleSel(self.properties.startFloatEdit.value,
                                              self.properties.endFloatEdit.value,
                                              tangentType="auto",
                                              message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def mirrorAnimationSelected(self):
        """Runs the tool.
        """
        mirroranimation.mirrorPasteAnimSel(self.properties.startFloatEdit.value,
                                           self.properties.endFloatEdit.value,
                                           cyclePre=CYCLE_LIST[self.properties.preCycleCombo.value],
                                           cyclePost=CYCLE_LIST[self.properties.postCycleCombo.value],
                                           flipCurveAttrs=self.flipAttrs(),
                                           offset=self.properties.offsetFloatEdit.value,
                                           limitRange=self.properties.limitRangeCheckbox.value,
                                           proxyAttrs=True,
                                           includeStaticValues=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def hiveMirrorPasteAnimation(self):
        """Runs the tool.
        """
        if not HIVE_ACTIVE:  # The Hive package is not loaded so skip
            return
        mirroranim.mirrorPasteHiveCtrlsSel(self.properties.startFloatEdit.value,
                                           self.properties.endFloatEdit.value,
                                           offset=self.properties.offsetFloatEdit.value,
                                           mirrorControlPanel=self.properties.includeProxyAttrCheckbox.value,
                                           preCycle=CYCLE_LIST[self.properties.preCycleCombo.value],
                                           postCycle=CYCLE_LIST[self.properties.postCycleCombo.value],
                                           limitRange=self.properties.limitRangeCheckbox.value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            # Buttons --------------
            widget.cycleAnimationBtn.clicked.connect(self.cycleAnimation)
            widget.toggleInfinityBtn.clicked.connect(self.toggleInfinity)
            widget.removeCycleAnimationBtn.clicked.connect(self.removeCycleAnimation)
            widget.limitTimeCurvesBtn.clicked.connect(self.limitKeysToTimerange)
            widget.cycleEndTangentsBtn.clicked.connect(self.autoTangentCycle)
            widget.mirrorAnimationHiveBtn.clicked.connect(self.hiveMirrorPasteAnimation)
            widget.mirrorPasteAnimationBtn.clicked.connect(self.mirrorAnimationSelected)
            # Combo Box --------------
            widget.presetFlipCombo.itemChanged.connect(self.setPreset)
            # Right Click Save Menu ------------
            widget.cycleAnimationBtn.addAction("Loop Pre Infinity Only",
                                               mouseMenu=QtCore.Qt.RightButton,
                                               icon=iconlib.icon("loopAbc"),
                                               connect=partial(self.cycleAnimation, pre=True, post=False))
            widget.cycleAnimationBtn.addAction("Loop Post Infinity Only",
                                               mouseMenu=QtCore.Qt.RightButton,
                                               icon=iconlib.icon("loopAbc"),
                                               connect=partial(self.cycleAnimation, pre=False, post=True))
            widget.cycleAnimationBtn.addAction("Loop Pre/Post Infinity (default)",
                                               mouseMenu=QtCore.Qt.RightButton,
                                               icon=iconlib.icon("loopAbc"),
                                               connect=partial(self.cycleAnimation, pre=True, post=True))


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
        # Start Frame float ---------------------------------------
        timeStart, timeEnd = timerange.getRangePlayback()
        tooltip = "The start frame to copy from.  \n" \
                  "If copying a cycle the start \n" \
                  "and end frame should match."
        self.startFloatEdit = elements.FloatEdit("Start",
                                                 toolTip=tooltip,
                                                 editText=timeStart,
                                                 labelRatio=1,
                                                 editRatio=2)
        # End Frame float ---------------------------------------
        tooltip = "The end frame to copy from.  \n" \
                  "If copying a cycle the start \n" \
                  "and end frame should match."
        self.endFloatEdit = elements.FloatEdit("End",
                                               toolTip=tooltip,
                                               editText=timeEnd,
                                               labelRatio=1,
                                               editRatio=2)
        # Offset Frames Opposite Target Float ---------------------------------------
        tooltip = "Offset the opposite amount in time. \n" \
                  "The pasted animation will be offset by this amount."
        self.offsetFloatEdit = elements.FloatEdit("Offset",
                                                  toolTip=tooltip,
                                                  editText=0.0,
                                                  labelRatio=1,
                                                  editRatio=2)

        # ---------------- MIRROR OPTIONS ------------------

        # Mirror Control Panel Checkbox ---------------------------------------
        tooltip = "Include proxy attributes? These are attributes \n" \
                  "that may belong to other objects."
        self.includeProxyAttrCheckbox = elements.CheckBox("Include Proxy Attributes",
                                                          checked=True,
                                                          toolTip=tooltip)
        # Limit Range Checkbox ---------------------------------------
        tooltip = "Add keys on the start/end frames to match the source controls while maintaining offsets. \n" \
                  "No animation will exist outside of the frame range, useful for cycles."
        self.limitRangeCheckbox = elements.CheckBox("Limit Keys To Start/End",
                                                    checked=True,
                                                    toolTip=tooltip)
        # Preset Flip Combo ---------------------------------------
        tooltip = "Change the presets to use common flip values."
        self.presetFlipCombo = elements.ComboBoxRegular("Flip Presets",
                                                        items=FLIP_PRESETS,
                                                        setIndex=2,
                                                        labelRatio=8,
                                                        boxRatio=30,
                                                        margins=(uic.SMLPAD, 0, uic.SMLPAD, 0),
                                                        toolTip=tooltip)
        # Flip Channels Range Checkbox ---------------------------------------
        tooltip = "Set the flip values for rotate and translation. \n" \
                  "Animation on checked attributes will be flip inverted. \n" \
                  "Static values will be reversed or `multiply by -1`. "
        self.translateLabel = elements.Label("Translate XYZ", toolTip=tooltip)
        self.translateXCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        self.translateYCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        self.translateZCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        self.rotateLabel = elements.Label("Rotate XYZ", toolTip=tooltip)
        self.rotateXCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        self.rotateYCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        self.rotateZCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)

        # ---------------- PRE POST ------------------

        # Pre-Cycle Combo ---------------------------------------
        tooltip = "Sets the Mirror-Animation pasted Pre-Infinity animation behaviour."
        self.preCycleCombo = elements.ComboBoxRegular("Pre",
                                                      items=CYCLE_LIST,
                                                      setIndex=2,
                                                      labelRatio=1,
                                                      boxRatio=3,
                                                      toolTip=tooltip)
        # Post-Cycle Combo ---------------------------------------
        tooltip = "Sets the Mirror-Animation pasted Post-Infinity animation behaviour."
        self.postCycleCombo = elements.ComboBoxRegular("Post",
                                                       items=CYCLE_LIST,
                                                       setIndex=2,
                                                       labelRatio=1,
                                                       boxRatio=3,
                                                       toolTip=tooltip)

        # ---------------- CYCLES ------------------

        # Cycle Combo ---------------------------------------
        toolTip = "Cycles the selected objects for both pre and post. \n" \
                  "Right-Click to affect Pre or Post only. \n" \
                  "Zoo Hotkey: alt o (Regular Cycle)"
        self.cycleCombo = elements.ComboBoxRegular(label="",
                                                   items=animconstants.GRAPH_CYCLE_LONG,
                                                   toolTip=toolTip)
        self.cycleAnimationBtn = elements.AlignedButton("Apply Cycle (right-click)",
                                                        icon="loopAbc",
                                                        toolTip=toolTip)
        # Toggle Infinity ---------------------------------
        toolTip = "Toggles the infinity display in the graph editor. \n" \
                  "Zoo Hotkey: shift i"
        self.toggleInfinityBtn = elements.AlignedButton("Toggle Infinity",
                                                        icon="infinite",
                                                        toolTip=toolTip)
        # Remove Cycle ---------------------------------
        toolTip = "Removes any cycling animation on the selected objects for both pre and post. \n" \
                  "Zoo Hotkey: ctrl alt o"
        self.removeCycleAnimationBtn = elements.AlignedButton("Remove Cycle",
                                                              icon="removeLoop",
                                                              toolTip=toolTip)

        # ---------------- BUTTONS ------------------

        #  Mirror Button ---------------------------------------
        tooltip = "Corrects offset cycles to the start and end frames. \n" \
                  "Adds keys on the start/end while removing keyframes \n" \
                  "outside of the start/end range. \n\n" \
                  "Select animation curves, channel box selection or objects \n" \
                  "with animation and run. "
        self.limitTimeCurvesBtn = elements.AlignedButton("Limit Cycle Time",
                                                         icon="clampTime",
                                                         toolTip=tooltip)
        #  Cycle Tangents Button ---------------------------------------
        tooltip = "Matches start/end tangents on animation curves so they \n" \
                  "loop correctly with continuity over the cycle. \n" \
                  "Keyframes must be present on the both the start and end frames. \n\n" \
                  "Select animation curves, channel box selection or objects \n" \
                  "with animation and run. "
        self.cycleEndTangentsBtn = elements.AlignedButton("Cycle End Tangents",
                                                          icon="tangentDiagonal",
                                                          toolTip=tooltip)
        #  Mirror Sel Button ---------------------------------------
        tooltip = "Copies, mirrors animation from first half of selected objects \n" \
                  "to the second half of selected objects \n" \
                  "The offset/mirror options are useful for cycles. \n" \
                  "Start and end frames should have identical values for cycles. \n" \
                  "Example: 0-24 not 1-24"
        self.mirrorPasteAnimationBtn = elements.AlignedButton("Mirror Animation Selected",
                                                              icon="symmetryTri",
                                                              toolTip=tooltip)
        #  Mirror Hive Button ---------------------------------------
        tooltip = "Copies the currently selected Hive control's animation and \n" \
                  "pastes it onto the opposite control with \n" \
                  "mirrored behavior.  \n" \
                  "The offset is useful for cycles. \n" \
                  "Start and end frames should have identical values for cycles. \n" \
                  "Example: 0-24 not 1-24"
        self.mirrorAnimationHiveBtn = elements.AlignedButton("Mirror Animation Hive",
                                                             icon="hive",
                                                             toolTip=tooltip)
        if not HIVE_ACTIVE:
            self.mirrorAnimationHiveBtn.setVisible(False)
        # ---------------- COLLAPSABLES ------------------
        self.flipCollapsable = elements.CollapsableFrameThin("Mirror Animation - Flip Attributes",
                                                             contentMargins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG),
                                                             contentSpacing=uic.SLRG,
                                                             collapsed=True)
        self.prePostCollapsable = elements.CollapsableFrameThin("Mirror Animation - Pre/Post Infinity",
                                                                contentMargins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG),
                                                                contentSpacing=uic.SLRG,
                                                                collapsed=True)
        self.optionsCollapsable = elements.CollapsableFrameThin("Options",
                                                                contentMargins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG),
                                                                contentSpacing=uic.SLRG,
                                                                collapsed=True)


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
        # Start/End/Offset Layout ---------------------------------------
        startEndLayout = elements.hBoxLayout(margins=(uic.SMLPAD, uic.SMLPAD, uic.SMLPAD, uic.SREG),
                                             spacing=uic.SVLRG2)
        startEndLayout.addWidget(self.startFloatEdit, 1)
        startEndLayout.addWidget(self.endFloatEdit, 1)
        startEndLayout.addWidget(self.offsetFloatEdit, 1)
        # Translate Layout ---------------------------------------
        translateLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        translateLayout.addWidget(self.translateLabel, 4)
        translateLayout.addWidget(self.translateXCheckbox, 1)
        translateLayout.addWidget(self.translateYCheckbox, 1)
        translateLayout.addWidget(self.translateZCheckbox, 1)
        # Rotate Layout ---------------------------------------
        rotateLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        rotateLayout.addWidget(self.rotateLabel, 4)
        rotateLayout.addWidget(self.rotateXCheckbox, 1)
        rotateLayout.addWidget(self.rotateYCheckbox, 1)
        rotateLayout.addWidget(self.rotateZCheckbox, 1)
        # Trans Rot Layout ---------------------------------------
        transRotLayout = elements.hBoxLayout(margins=(uic.SMLPAD, 0, uic.SMLPAD, 0), spacing=uic.SVLRG2)
        transRotLayout.addLayout(translateLayout, 1)
        transRotLayout.addLayout(rotateLayout, 1)
        # Tangent Layout ---------------------------------------
        tangentLayout = elements.hBoxLayout(margins=(0, 0, 0, 0),
                                            spacing=uic.SPACING)
        tangentLayout.addWidget(self.limitTimeCurvesBtn, 1)
        tangentLayout.addWidget(self.cycleEndTangentsBtn, 1)
        # Mirror Layout ---------------------------------------
        mirrorBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0),
                                              spacing=uic.SPACING)
        mirrorBtnLayout.addWidget(self.mirrorPasteAnimationBtn)
        mirrorBtnLayout.addWidget(self.mirrorAnimationHiveBtn)
        # Button V Layout ---------------------------------------
        vButtonLayout = elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        vButtonLayout.addLayout(tangentLayout)
        vButtonLayout.addLayout(mirrorBtnLayout)
        #  Flip Collapsable ---------------------------------------
        self.flipCollapsable.addWidget(self.presetFlipCombo)
        self.flipCollapsable.addLayout(transRotLayout)
        # Collapsable Connections -------------------------------------
        self.flipCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.prePostCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(startEndLayout)
        mainLayout.addWidget(self.flipCollapsable)
        mainLayout.addLayout(vButtonLayout)


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
        # Start/End/Offset Layout ---------------------------------------
        startEndLayout = elements.hBoxLayout(margins=(uic.SMLPAD, uic.SMLPAD, uic.SMLPAD, uic.SREG),
                                             spacing=uic.SVLRG2)
        startEndLayout.addWidget(self.startFloatEdit, 1)
        startEndLayout.addWidget(self.endFloatEdit, 1)
        startEndLayout.addWidget(self.offsetFloatEdit, 1)
        # Tangent Layout ---------------------------------------
        tangentLayout = elements.hBoxLayout(margins=(0, 0, 0, 0),
                                            spacing=uic.SPACING)
        tangentLayout.addWidget(self.limitTimeCurvesBtn, 1)
        tangentLayout.addWidget(self.cycleEndTangentsBtn, 1)
        # Mirror Layout ---------------------------------------
        mirrorBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0),
                                              spacing=uic.SPACING)
        mirrorBtnLayout.addWidget(self.mirrorPasteAnimationBtn)
        mirrorBtnLayout.addWidget(self.mirrorAnimationHiveBtn)
        # Translate Layout ---------------------------------------
        translateLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        translateLayout.addWidget(self.translateLabel, 4)
        translateLayout.addWidget(self.translateXCheckbox, 1)
        translateLayout.addWidget(self.translateYCheckbox, 1)
        translateLayout.addWidget(self.translateZCheckbox, 1)
        # Rotate Layout ---------------------------------------
        rotateLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        rotateLayout.addWidget(self.rotateLabel, 4)
        rotateLayout.addWidget(self.rotateXCheckbox, 1)
        rotateLayout.addWidget(self.rotateYCheckbox, 1)
        rotateLayout.addWidget(self.rotateZCheckbox, 1)
        # Cycle Anim Combo Btn Layout ---------------------------------------
        cycleComboLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        cycleComboLayout.addWidget(self.cycleCombo, 1)
        cycleComboLayout.addWidget(self.cycleAnimationBtn, 1)
        # Infinity Layout ---------------------------------------
        infinityLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        infinityLayout.addWidget(self.toggleInfinityBtn, 1)
        infinityLayout.addWidget(self.removeCycleAnimationBtn, 1)
        # Trans Rot Layout ---------------------------------------
        transRotLayout = elements.hBoxLayout(margins=(uic.SMLPAD, 0, uic.SMLPAD, 0), spacing=uic.SVLRG2)
        transRotLayout.addLayout(translateLayout, 1)
        transRotLayout.addLayout(rotateLayout, 1)
        #  Pre Post Layout ---------------------------------------
        prePostLayout = elements.hBoxLayout(margins=(uic.SMLPAD, 0, uic.SMLPAD, 0),
                                            spacing=uic.SVLRG2)
        prePostLayout.addWidget(self.preCycleCombo, 1)
        prePostLayout.addWidget(self.postCycleCombo, 1)
        #  Checkbox Layout ---------------------------------------
        optionsLayout = elements.hBoxLayout(margins=(uic.SMLPAD, 0, uic.SMLPAD, uic.SMLPAD),
                                            spacing=uic.SLRG)
        optionsLayout.addWidget(self.includeProxyAttrCheckbox, 1)
        optionsLayout.addWidget(self.limitRangeCheckbox, 1)
        # Button V Layout ---------------------------------------
        vButtonLayout = elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        vButtonLayout.addLayout(cycleComboLayout)
        vButtonLayout.addLayout(infinityLayout)
        vButtonLayout.addLayout(tangentLayout)
        vButtonLayout.addLayout(mirrorBtnLayout)
        #  Flip Collapsable ---------------------------------------
        self.flipCollapsable.addWidget(self.presetFlipCombo)
        self.flipCollapsable.addLayout(transRotLayout)
        #  Pre post Collapsable ---------------------------------------
        self.prePostCollapsable.hiderLayout.addLayout(prePostLayout)
        #  Options Collapsable ---------------------------------------
        self.optionsCollapsable.hiderLayout.addLayout(optionsLayout)
        # Collapsable Connections -------------------------------------
        self.flipCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.prePostCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.optionsCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(startEndLayout)
        mainLayout.addWidget(self.flipCollapsable)
        mainLayout.addWidget(self.prePostCollapsable)
        mainLayout.addWidget(self.optionsCollapsable)
        mainLayout.addLayout(vButtonLayout)
