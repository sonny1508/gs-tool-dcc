from zoovendor.Qt import QtWidgets

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.utils import mayaenv
from zoo.libs.maya.cmds.animation import generalanimation
from zoo.libs.maya import zapi
from zoo.apps.toolsetsui.widgets import toolsetwidget

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
ROTATE_ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
SELECT_OPTIONS = ["Under Selected Hierarchy", "Scene (All)", "Within Selected"]


class GeneralAnimationTools(toolsetwidget.ToolsetWidget):
    id = "generalAnimationTools"
    info = "Assorted Maya animation tools & hotkey trainer."
    uiData = {"label": "Animation Toolbox",
              "icon": "key",
              "tooltip": "Assorted Maya animation tools & hotkey trainer",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-general-animation-tools/"}

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
        return super(GeneralAnimationTools, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(GeneralAnimationTools, self).widgets()

    # ------------------
    # RIGHT CLICK TOOLSET ICON
    # ------------------

    def actions(self):
        """Right click menu on the main toolset tool icon"""
        return [{"type": "action",
                 "name": "rotOrderXYZ",
                 "label": "XYZ Rot Order",
                 "icon": "key",
                 "tooltip": ""},
                {"type": "action",
                 "name": "rotOrderYZX",
                 "label": "YZX Rot Order",
                 "icon": "key",
                 "tooltip": ""},
                {"type": "action",
                 "name": "rotOrderZXY",
                 "label": "ZXY Rot Order",
                 "icon": "key",
                 "tooltip": ""},
                {"type": "action",
                 "name": "rotOrderXZY",
                 "label": "XZY Rot Order",
                 "icon": "key",
                 "tooltip": ""},
                {"type": "action",
                 "name": "rotOrderYXZ",
                 "label": "YXZ Rot Order",
                 "icon": "key",
                 "tooltip": ""},
                {"type": "action",
                 "name": "rotOrderZYX",
                 "label": "ZYX Rot Order",
                 "icon": "key",
                 "tooltip": ""}]

    def executeActions(self, action):

        name = action["name"].lower()
        if name in zapi.constants.kRotateOrderNames:
            self.changeRotOrder(newRotOrder=zapi.constants.kRotateOrderNames.index(name))

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def changeRotOrder(self, newRotOrder=None):
        """Main function, uses the GUI to change rotation order of the selected objs in Maya
        The logic here is an open source script by Morgan Loomis, see generalanimation.changeRotOrder for more info.
        """
        generalanimation.changeRotOrder(newRotOrder=newRotOrder or self.properties.changeRotOrderCombo.value)

    # -------------------
    # SELECT
    # -------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectAnimNodes(self):
        generalanimation.selectAnimNodes(self.properties.selectAnimCombo.value)

    # -------------------
    # GENERAL
    # -------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setKeyChannel(self):
        generalanimation.setKeyChannel()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setKeyAll(self):
        generalanimation.setKeyAll()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def animHold(self):
        generalanimation.animHold()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteCurrentFrame(self):
        generalanimation.deleteCurrentFrame()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def keyToggleVis(self):
        generalanimation.keyToggleVis()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def resetAttrs(self):
        generalanimation.resetAttrsBtn()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def toggleControlCurveVis(self):
        generalanimation.toggleControlCurveVis()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def bakeKeys(self):
        generalanimation.bakeKeys()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createMotionTrail(self):
        generalanimation.createMotionTrail()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def openGhostEditor(self):
        if mayaenv.mayaVersion() >= 2022:  # Should be already hidden in 2020 and below.
            generalanimation.openGhostEditor()

    # -------------------
    # PLAYBACK
    # -------------------

    def playPause(self):
        generalanimation.playPause()

    def reverse(self):
        generalanimation.reverse()

    def stepNextFrame(self):
        generalanimation.stepNextFrame()

    def stepLastFrame(self):
        generalanimation.stepLastFrame()

    def stepNextKey(self):
        generalanimation.stepNextKey()

    def stepLastKey(self):
        generalanimation.stepLastKey()

    def step5framesForwards(self):
        generalanimation.step5framesForwards()

    def step5framesBackwards(self):
        generalanimation.step5framesBackwards()

    # -------------------
    # TIMELINE
    # -------------------

    def playRangeStart(self):
        generalanimation.playRangeStart()

    def playRangeEnd(self):
        generalanimation.playRangeEnd()

    def timeRangeStart(self):
        generalanimation.timeRangeStart()

    def timeRangeEnd(self):
        generalanimation.timeRangeEnd()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            # General -------------------------------
            widget.changeRotOrderBtn.clicked.connect(self.changeRotOrder)
            widget.selectAnimBtn.clicked.connect(self.selectAnimNodes)
            widget.setKeyChannelBtn.clicked.connect(self.setKeyChannel)
            widget.setKeyAllBtn.clicked.connect(self.setKeyAll)
            widget.animHoldBtn.clicked.connect(self.animHold)
            widget.deleteCurrentFrameBtn.clicked.connect(self.deleteCurrentFrame)
            widget.keyToggleVisBtn.clicked.connect(self.keyToggleVis)
            widget.resetAttrsBtn.clicked.connect(self.resetAttrs)
            widget.toggleControlCurveVisBtn.clicked.connect(self.toggleControlCurveVis)
            widget.bakeKeysBtn.clicked.connect(self.bakeKeys)
            widget.motionTrailBtn.clicked.connect(self.createMotionTrail)
            widget.ghostEditorBtn.clicked.connect(self.openGhostEditor)
            # Playback -------------------------------
            widget.playPauseBtn.clicked.connect(self.playPause)
            widget.reverseBtn.clicked.connect(self.reverse)
            widget.stepNextFrameBtn.clicked.connect(self.stepNextFrame)
            widget.stepLastFrameBtn.clicked.connect(self.stepLastFrame)
            widget.stepNextKeyBtn.clicked.connect(self.stepNextKey)
            widget.stepLastKeyBtn.clicked.connect(self.stepLastKey)
            widget.step5framesForwardsBtn.clicked.connect(self.step5framesForwards)
            widget.step5framesBackwardsBtn.clicked.connect(self.step5framesBackwards)
            # Timeline -------------------------------
            widget.playRangeStartBtn.clicked.connect(self.playRangeStart)
            widget.playRangeEndBtn.clicked.connect(self.playRangeEnd)
            widget.timeRangeStartBtn.clicked.connect(self.timeRangeStart)
            widget.timeRangeEndBtn.clicked.connect(self.timeRangeEnd)


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
        # Change Rotation Order Combo ---------------------------------------
        toolTip = "Change Rotation Order - Will change the xyz rotation order on selected transforms\n" \
                  "If objects have keyframes will change each key to compensate for the correct rotation."
        self.changeRotOrderCombo = elements.ComboBoxRegular(label="Change Rotation Order",
                                                            labelRatio=16,
                                                            boxRatio=23,
                                                            items=ROTATE_ORDERS,
                                                            toolTip=toolTip)
        # Change Rot Order Button --------------------------
        self.changeRotOrderBtn = elements.styledButton("",
                                                       icon="key",
                                                       toolTip=toolTip,
                                                       minWidth=uic.BTN_W_ICN_MED)
        # Select Animated Nodes Combo ---------------------------------------
        toolTip = "Select all animated nodes filtered by the dropdown menu."
        self.selectAnimCombo = elements.ComboBoxRegular(label="Select Animated Nodes",
                                                        labelRatio=16,
                                                        boxRatio=23,
                                                        items=SELECT_OPTIONS,
                                                        toolTip=toolTip)
        # Select Animated Nodes Button --------------------------
        self.selectAnimBtn = elements.styledButton("",
                                                   icon="selectKey",
                                                   toolTip=toolTip,
                                                   minWidth=uic.BTN_W_ICN_MED,
                                                   parent=self)
        # Set Key All ----------------------------------
        toolTip = "Set Key on all attributes, but if any Channel Box attributes are \n" \
                  "selected then key only those channels. \n" \
                  "Zoo Hotkey: s"
        self.setKeyChannelBtn = elements.AlignedButton("Set Key Channel Box",
                                                       icon="key",
                                                       toolTip=toolTip)
        # Set Key ----------------------------------
        toolTip = "Sets a key on all attributes ignoring any Channel Box selection. \n" \
                  "Zoo Hotkey: shift s"
        self.setKeyAllBtn = elements.AlignedButton("Set Key All Channels",
                                                   icon="key",
                                                   toolTip=toolTip)
        # Make Animation Hold ---------------------------------
        toolTip = "Make an animation hold. \n" \
                  "Place the timeline between two keys and run. \n" \
                  "The first key will be copied to the second with flat tangents. \n" \
                  "Zoo Hotkey: alt a"

        self.animHoldBtn = elements.AlignedButton(text="Make Anim Hold",
                                                  parent=self, icon="animHold", toolTip=toolTip)

        # Delete Current Frame ---------------------------------
        toolTip = "Deletes keys at the current time, or the selected timeline range. \n" \
                  "Zoo Hotkey: ctrl shift v"
        self.deleteCurrentFrameBtn = elements.AlignedButton(text="Del Key Current Time",
                                                            icon="delKey",
                                                            parent=self,
                                                            toolTip=toolTip)
        # Toggle Vis ---------------------------------
        toolTip = "Keys and inverts the visibility of the selected objects. \n" \
                  "Visibility of True will become False \n" \
                  "Zoo Hotkey: ctrl shift alt v"
        self.keyToggleVisBtn = elements.AlignedButton("Key Visibility Toggle",
                                                      icon="eye",
                                                      toolTip=toolTip,
                                                      parent=self)
        # Reset Attrs ---------------------------------
        toolTip = "Resets the selected object/s attributes to default values. \n" \
                  "Zoo Hotkey: ctrl shift alt s"
        self.resetAttrsBtn = elements.AlignedButton("Reset Attributes",
                                                    icon="arrowBack",
                                                    toolTip=toolTip,
                                                    parent=self)
        # Toggle Curve Visibility ---------------------------------
        toolTip = "Toggles the visibility of Controls and Curves. \n" \
                  "Zoo Hotkey: d (tap)"
        self.toggleControlCurveVisBtn = elements.AlignedButton("Control Curve Toggle",
                                                               icon="starControl",
                                                               toolTip=toolTip,
                                                               parent=self)
        # Bake ----------------------------------
        toolTip = "Bake animation on the selected objects. \n" \
                  "Affects the selected range or playback range if no range is selected.\n" \
                  "Zoo Hotkey: shift alt b"
        self.bakeKeysBtn = elements.AlignedButton("Bake Animation",
                                                  icon="bake",
                                                  toolTip=toolTip,
                                                  parent=self)
        # Motion Trail ----------------------------------
        toolTip = "Creates a motion trail on the selected object.\n" \
                  "Zoo Hotkey: shift alt {"
        self.motionTrailBtn = elements.AlignedButton("Create Motion Trail",
                                                     icon="motionTrail",
                                                     toolTip=toolTip,
                                                     parent=self, )
        # Ghost Editor Window ----------------------------------
        toolTip = "Opens Maya's Ghost Editor Window.\n" \
                  "Zoo Hotkey: shift alt }"
        self.ghostEditorBtn = elements.AlignedButton("Open Ghost Editor",
                                                     icon="ghosting",
                                                     toolTip=toolTip,
                                                     parent=self)
        if mayaenv.mayaVersion() < 2022:
            self.ghostEditorBtn.setVisible(False)

        # --------------------------------------------------------------------------------------------
        #                                  PLAYBACK
        # --------------------------------------------------------------------------------------------
        # Play/Stop ----------------------------------
        toolTip = "Play/Pause animation toggle. \n" \
                  "Zoo Hotkey: alt v"
        self.playPauseBtn = elements.AlignedButton("Play/Pause",
                                                   icon="playSolid",
                                                   toolTip=toolTip)
        # Reverse ----------------------------------
        toolTip = "Reverse/Pause animation toggle. \n" \
                  "Zoo Hotkey: alt z"
        self.reverseBtn = elements.AlignedButton("Reverse",
                                                 icon="reverse",
                                                 toolTip=toolTip)
        # Step To Next Frame ----------------------------------
        toolTip = "Step to the next frame in the timeline. \n" \
                  "Zoo Hotkey: alt c"
        self.stepNextFrameBtn = elements.AlignedButton("Step To Next Frame",
                                                       icon="nextFrame",
                                                       toolTip=toolTip)
        # Step To Last Frame ----------------------------------
        toolTip = "Step to the last frame in the timeline. \n" \
                  "Zoo Hotkey: alt x"
        self.stepLastFrameBtn = elements.AlignedButton("Step To Last Frame",
                                                       icon="lastFrame",
                                                       toolTip=toolTip)
        # Step To Next Key ----------------------------------
        toolTip = "Step to the next Key Frame in the timeline. \n" \
                  "Zoo Hotkey: c"
        self.stepNextKeyBtn = elements.AlignedButton("Step To Next Key",
                                                     icon="nextKey",
                                                     toolTip=toolTip)
        # Step To Last Key ----------------------------------
        toolTip = "Step to the last Key Frame in the timeline. \n" \
                  "Zoo Hotkey: x"
        self.stepLastKeyBtn = elements.AlignedButton("Step To Last Key",
                                                     icon="lastKey",
                                                     toolTip=toolTip)
        # Step Forward 5 Frames ---------------------------------
        toolTip = "Step forward five frames in time. \n" \
                  "Zoo Hotkey: ctrl alt ."
        self.step5framesForwardsBtn = elements.AlignedButton("Step Forward 5 Frames",
                                                             icon="stepForwardFive",
                                                             toolTip=toolTip)
        # Step Backwards 5 Frames ---------------------------------
        toolTip = "Step backwards five frames in time. \n" \
                  "Zoo Hotkey: ctrl alt ."
        self.step5framesBackwardsBtn = elements.AlignedButton("Step Backwards 5 Frames",
                                                              icon="stepBackwardFive",
                                                              toolTip=toolTip)
        # --------------------------------------------------------------------------------------------
        #                                  TIMELINE
        # --------------------------------------------------------------------------------------------
        # Time Range Start ---------------------------------
        toolTip = "Sets the time-range start to the current time. \n" \
                  "Zoo Hotkey: ctrl shift alt <"
        self.timeRangeStartBtn = elements.AlignedButton("Set Time Range Start",
                                                        icon="timeRangeStart",
                                                        toolTip=toolTip)
        # Time Range End ---------------------------------
        toolTip = "Sets the time-range end to the current time. \n" \
                  "Zoo Hotkey: ctrl shift alt >"
        self.timeRangeEndBtn = elements.AlignedButton("Set Time Range End",
                                                      icon="timeRangeEnd",
                                                      toolTip=toolTip)
        # Time Playback Start ---------------------------------
        toolTip = "Sets the playback start to the current time. \n" \
                  "Zoo Hotkey: ctrl alt ,"
        self.playRangeStartBtn = elements.AlignedButton("Set Play Range Start",
                                                        icon="playRangeStart",
                                                        toolTip=toolTip)
        # Time Playback End ---------------------------------
        toolTip = "Sets the playback end to the current time. \n" \
                  "Zoo Hotkey: ctrl alt ."
        self.playRangeEndBtn = elements.AlignedButton("Set Play Range End",
                                                      icon="playRangeEnd",
                                                      toolTip=toolTip)


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
        # Change Rot Order Layout -----------------------------
        changeRotLayout = elements.hBoxLayout()
        changeRotLayout.addWidget(self.changeRotOrderCombo, 20)
        changeRotLayout.addWidget(self.changeRotOrderBtn, 1)
        # Select Combo Layout -----------------------------
        selectComboLayout = elements.hBoxLayout()
        selectComboLayout.addWidget(self.selectAnimCombo, 20)
        selectComboLayout.addWidget(self.selectAnimBtn, 1)
        # Grid Layout ----------------------------------------------------------
        gridTopLayout = elements.GridLayout(spacing=2)
        row = 0
        gridTopLayout.addWidget(self.animHoldBtn, row, 0)
        gridTopLayout.addWidget(self.deleteCurrentFrameBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.keyToggleVisBtn, row, 0)
        gridTopLayout.addWidget(self.resetAttrsBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.toggleControlCurveVisBtn, row, 0)
        gridTopLayout.addWidget(self.bakeKeysBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.motionTrailBtn, row, 0)
        gridTopLayout.addWidget(self.ghostEditorBtn, row, 1)
        row += 1
        gridTopLayout.setColumnStretch(0, 1)
        gridTopLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------
        mainLayout.addLayout(changeRotLayout)
        mainLayout.addLayout(selectComboLayout)
        mainLayout.addLayout(gridTopLayout)


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
                                         spacing=uic.SPACING)
        # Change Rot Order Layout -----------------------------
        changeRotLayout = elements.hBoxLayout()
        changeRotLayout.addWidget(self.changeRotOrderCombo, 20)
        changeRotLayout.addWidget(self.changeRotOrderBtn, 1)
        # Select Combo Layout -----------------------------
        selectComboLayout = elements.hBoxLayout()
        selectComboLayout.addWidget(self.selectAnimCombo, 20)
        selectComboLayout.addWidget(self.selectAnimBtn, 1)
        # Grid Layout -----------------------------
        gridTopLayout = elements.GridLayout(spacing=2)
        row = 0
        gridTopLayout.addWidget(self.setKeyChannelBtn, row, 0)
        gridTopLayout.addWidget(self.setKeyAllBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.animHoldBtn, row, 0)
        gridTopLayout.addWidget(self.deleteCurrentFrameBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.keyToggleVisBtn, row, 0)
        gridTopLayout.addWidget(self.resetAttrsBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.toggleControlCurveVisBtn, row, 0)
        gridTopLayout.addWidget(self.bakeKeysBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.motionTrailBtn, row, 0)
        gridTopLayout.addWidget(self.ghostEditorBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(elements.LabelDivider(text="Playback"), row, 0, 1, 2)
        row += 1
        gridTopLayout.addWidget(self.playPauseBtn, row, 0)
        gridTopLayout.addWidget(self.reverseBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.stepNextFrameBtn, row, 0)
        gridTopLayout.addWidget(self.stepLastFrameBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.stepNextKeyBtn, row, 0)
        gridTopLayout.addWidget(self.stepLastKeyBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.step5framesForwardsBtn, row, 0)
        gridTopLayout.addWidget(self.step5framesBackwardsBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(elements.LabelDivider(text="Timeline"), row, 0, 1, 2)
        row += 1
        gridTopLayout.addWidget(self.playRangeStartBtn, row, 0)
        gridTopLayout.addWidget(self.playRangeEndBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.timeRangeStartBtn, row, 0)
        gridTopLayout.addWidget(self.timeRangeEndBtn, row, 1)
        gridTopLayout.setColumnStretch(0, 1)
        gridTopLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------
        mainLayout.addLayout(changeRotLayout)
        # mainLayout.addWidget(elements.LabelDivider(text="Select"))
        mainLayout.addLayout(selectComboLayout)
        mainLayout.addLayout(gridTopLayout)
