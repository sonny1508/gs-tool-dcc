""" ---------- Hive Mirror Copy Paste Animation -------------


"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.hive.anim import mirroranim
from zoo.libs.maya.cmds.animation import timerange

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

CYCLE_LIST = ["constant", "linear", "cycle", "cycleRelative", "oscillate"]


class HiveMirrorPasteAnim(toolsetwidget.ToolsetWidget):
    id = "hiveMirrorPasteAnim"
    info = "Hive mirror copy and paste animation."
    uiData = {"label": "Hive Mirror Flip Animation",
              "icon": "symmetryTri",
              "tooltip": "Hive mirror copy and paste animation.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-hive-mirror-paste-animation"
              }

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
        return super(HiveMirrorPasteAnim, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(HiveMirrorPasteAnim, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def mirrorPasteAnimation(self):
        """Runs the tool.
        """
        mirroranim.mirrorPasteHiveCtrlsSel(self.properties.startFloatEdit.value,
                                           self.properties.endFloatEdit.value,
                                           offset=self.properties.offsetFloatEdit.value,
                                           mirrorControlPanel=self.properties.includeProxyAttrCheckbox.value,
                                           preCycle=CYCLE_LIST[self.properties.preCycleCombo.value],
                                           postCycle=CYCLE_LIST[self.properties.postCycleCombo.value],
                                           limitRange=self.properties.limitRangeCheckbox.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def flipPoseSel(self):
        mirroranim.flipPoseCtrlsSelected(flip=True, animation=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def flipAnimationSel(self):
        mirroranim.flipPoseCtrlsSelected(flip=True, animation=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def mirrorPoseSel(self):
        mirroranim.flipPoseCtrlsSelected(flip=False, animation=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def mirrorAnimationSel(self):
        mirroranim.flipPoseCtrlsSelected(flip=False, animation=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.mirrorPasteAnimationBtn.clicked.connect(self.mirrorPasteAnimation)
            widget.flipPoseSelBtn.clicked.connect(self.flipPoseSel)
            widget.flipAnimationSelBtn.clicked.connect(self.flipAnimationSel)
            widget.mirrorPoseSelBtn.clicked.connect(self.mirrorPoseSel)
            widget.mirrorAnimationSelBtn.clicked.connect(self.mirrorAnimationSel)


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
        # Flip Pose Buttons ---------------------------------------
        tooltip = "Flips the pose of the selected controls. \n" \
                  "Select a Hive control/s and run.  \n" \
                  "Center controls will flip and side controls will flip mirror."
        self.flipPoseSelBtn = elements.AlignedButton("Flip Pose - Selected",
                                                     icon="symmetryTri",
                                                     toolTip=tooltip)
        # Mirror Pose Button ---------------------------------------
        tooltip = "Mirrors the pose of the selected controls. \n" \
                  "Select a Hive control/s and run, pose will mirror to the other side.  \n" \
                  "Side controls mirror settings to the opposite side. \n" \
                  "Center controls will be ignored."
        self.mirrorPoseSelBtn = elements.AlignedButton("Mirror Pose - Selected",
                                                       icon="mirrorGeo",
                                                       toolTip=tooltip)
        # Flip Animation Buttons ---------------------------------------
        tooltip = "Flips all animation of the selected controls. \n" \
                  "Select a Hive control/s and run.  \n" \
                  "Center controls will flip and side controls will flip mirror."
        self.flipAnimationSelBtn = elements.AlignedButton("Flip Animation - Selected",
                                                          icon="symmetryTri",
                                                          toolTip=tooltip)
        # Mirror Pose Button ---------------------------------------
        tooltip = "Mirrors all animation on the selected controls. \n" \
                  "Select a Hive control/s and run, animation will mirror to the other side.  \n" \
                  "Side controls mirror settings to the opposite side. \n" \
                  "Center controls will be ignored."
        self.mirrorAnimationSelBtn = elements.AlignedButton("Mirror Animation - Selected",
                                                            icon="mirrorGeo",
                                                            toolTip=tooltip)
        # Start Frame float ---------------------------------------
        timeStart, timeEnd = timerange.getRangePlayback()
        halfTime = float(int(timeEnd - timeStart) / 2)
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
        tooltip = "Opposite control offset amount in time. \n" \
                  "The pasted animation will be offset by this amount."
        self.offsetFloatEdit = elements.FloatEdit("Offset",
                                                  toolTip=tooltip,
                                                  editText=halfTime,
                                                  labelRatio=1,
                                                  editRatio=2)
        # Mirror Control Panel Checkbox ---------------------------------------
        tooltip = "Includes all the space-switch, vis and `Hive control panel` options for each control. "
        self.includeProxyAttrCheckbox = elements.CheckBox("Include Extra Attributes",
                                                          checked=True,
                                                          toolTip=tooltip)
        # Limit Range Checkbox ---------------------------------------
        tooltip = "Add keys on the start/end frames to match the source controls while maintaining offsets. \n" \
                  "No animation will exist outside of the frame range, useful for cycles."
        self.limitRangeCheckbox = elements.CheckBox("Limit Keys To Start/End",
                                                    checked=True,
                                                    toolTip=tooltip)
        # Pre-Cycle Combo ---------------------------------------
        tooltip = "Sets the default Pre-Infinity animation behaviour."
        self.preCycleCombo = elements.ComboBoxRegular("Pre",
                                                      items=CYCLE_LIST,
                                                      setIndex=2,
                                                      labelRatio=1,
                                                      boxRatio=3,
                                                      toolTip=tooltip)
        # Post-Cycle Combo ---------------------------------------
        tooltip = "Sets the default Post-Infinity animation behaviour."
        self.postCycleCombo = elements.ComboBoxRegular("Post",
                                                       items=CYCLE_LIST,
                                                       setIndex=2,
                                                       labelRatio=1,
                                                       boxRatio=3,
                                                       toolTip=tooltip)

        # Mirror Animation To Opposite Control Button ---------------------------------------
        tooltip = "Copies the currently selected control's animation and \n" \
                  "pastes it onto the opposite control with \n" \
                  "mirrored behavior.  \n" \
                  "The offset is useful for cycles. \n" \
                  "Start and end frames should have identical poses for cycles. \n" \
                  "Example: 0-24 not 1-24"
        self.mirrorPasteAnimationBtn = elements.styledButton("Mirror Selected Animation Control To Its Opposite",
                                                             icon="symmetryTri",
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
                                         spacing=uic.SLRG)
        #  Start/End/Offset Layout ---------------------------------------
        startEndLayout = elements.hBoxLayout(margins=(0, uic.SMLPAD, 0, 0),
                                             spacing=uic.SVLRG2)
        startEndLayout.addWidget(self.startFloatEdit, 1)
        startEndLayout.addWidget(self.endFloatEdit, 1)
        startEndLayout.addWidget(self.offsetFloatEdit, 1)
        #  Pre Post Layout ---------------------------------------
        prePostLayout = elements.hBoxLayout(margins=(0, 0, 0, 0),
                                            spacing=uic.SVLRG2)
        prePostLayout.addWidget(self.preCycleCombo, 1)
        prePostLayout.addWidget(self.postCycleCombo, 1)
        # Flip Pose Button Layout ---------------------------------------
        topPoseBtnLayout = (elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING))
        topPoseBtnLayout.addWidget(self.flipPoseSelBtn, 1)
        topPoseBtnLayout.addWidget(self.mirrorPoseSelBtn, 1)
        # Flip Anim Button Layout ---------------------------------------
        animFlipButtonLayout = (elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING))
        animFlipButtonLayout.addWidget(self.flipAnimationSelBtn, 1)
        animFlipButtonLayout.addWidget(self.mirrorAnimationSelBtn, 1)
        # Flip All Button Layout ---------------------------------------
        flipBtnLayout = (elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING))
        flipBtnLayout.addLayout(topPoseBtnLayout, 1)
        flipBtnLayout.addLayout(animFlipButtonLayout, 1)

        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(elements.LabelDivider("Flip/Mirror Pose & Animation"))
        mainLayout.addLayout(flipBtnLayout)
        mainLayout.addWidget(elements.LabelDivider("Offset Mirror Cycle - Left/Right"))
        mainLayout.addLayout(startEndLayout)
        mainLayout.addWidget(elements.LabelDivider("Pre/Post Infinity"))
        mainLayout.addLayout(prePostLayout)
        mainLayout.addWidget(self.mirrorPasteAnimationBtn)


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
                                         spacing=uic.SLRG)
        #  Start/End/Offset Layout ---------------------------------------
        startEndLayout = elements.hBoxLayout(margins=(0, uic.SMLPAD, 0, 0),
                                             spacing=uic.SVLRG2)
        startEndLayout.addWidget(self.startFloatEdit, 1)
        startEndLayout.addWidget(self.endFloatEdit, 1)
        startEndLayout.addWidget(self.offsetFloatEdit, 1)
        #  Pre Post Layout ---------------------------------------
        prePostLayout = elements.hBoxLayout(margins=(0, 0, 0, 0),
                                            spacing=uic.SVLRG2)
        prePostLayout.addWidget(self.preCycleCombo, 1)
        prePostLayout.addWidget(self.postCycleCombo, 1)
        #  Checkbox Layout ---------------------------------------
        checkboxLayout = elements.hBoxLayout(margins=(uic.LRGPAD, 0, uic.LRGPAD, uic.SMLPAD),
                                             spacing=uic.SLRG)
        checkboxLayout.addWidget(self.includeProxyAttrCheckbox, 1)
        checkboxLayout.addWidget(self.limitRangeCheckbox, 1)
        # Flip Pose Button Layout ---------------------------------------
        topPoseBtnLayout = (elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING))
        topPoseBtnLayout.addWidget(self.flipPoseSelBtn, 1)
        topPoseBtnLayout.addWidget(self.mirrorPoseSelBtn, 1)
        # Flip Anim Button Layout ---------------------------------------
        animFlipButtonLayout = (elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING))
        animFlipButtonLayout.addWidget(self.flipAnimationSelBtn, 1)
        animFlipButtonLayout.addWidget(self.mirrorAnimationSelBtn, 1)
        # Flip All Button Layout ---------------------------------------
        flipBtnLayout = (elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING))
        flipBtnLayout.addLayout(topPoseBtnLayout, 1)
        flipBtnLayout.addLayout(animFlipButtonLayout, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(elements.LabelDivider("Flip/Mirror Pose & Animation"))
        mainLayout.addLayout(flipBtnLayout)
        mainLayout.addWidget(elements.LabelDivider("Offset Mirror Cycle - Left/Right"))
        mainLayout.addLayout(startEndLayout)
        mainLayout.addWidget(elements.LabelDivider("Pre/Post Infinity"))
        mainLayout.addLayout(prePostLayout)
        mainLayout.addWidget(elements.LabelDivider("Options"))
        mainLayout.addLayout(checkboxLayout)
        mainLayout.addWidget(self.mirrorPasteAnimationBtn)
