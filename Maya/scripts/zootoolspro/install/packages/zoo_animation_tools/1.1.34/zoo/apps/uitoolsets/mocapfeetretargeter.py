""" Lock Feet tool for motion capture retargeting.

"""
from functools import partial

from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs import iconlib
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic, keyboardmouse
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output
from zoo.libs.maya.cmds.animation import mocap, timerange

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
TIME_RANGE_COMBO_LIST = ["Playback Range", "Full Animation Range", "Custom Frame Range"]


class MocapFeetRetargeter(toolsetwidget.ToolsetWidget):
    id = "mocapFeetRetargeter"
    info = "A lock feet tool for motion capture retargeting."
    uiData = {"label": "Mocap Feet Retargeter",
              "icon": "legWalk",
              "tooltip": "A lock feet tool for motion capture retargeting",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-mocap-feet-retargeter/"}

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
        self.footLockInstance = None  # mocap.FootLocker()
        self.rangeComboChanged()
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
        return super(MocapFeetRetargeter, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(MocapFeetRetargeter, self).widgets()

    # ------------------
    # UI
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

    def addHipsSource(self):
        self.properties.sourceHipsStr.value = mocap.selectedObject()
        self.updateFromProperties()

    def addFootLSource(self):
        self.properties.sourceFootLStr.value = mocap.selectedObject()
        self.updateFromProperties()

    def addFootRSource(self):
        self.properties.sourceFootRStr.value = mocap.selectedObject()
        self.updateFromProperties()

    def addTargetHips(self):
        self.properties.targetHipsStr.value = mocap.selectedObject()
        self.updateFromProperties()

    def addTargetFootL(self):
        self.properties.targetFootLStr.value = mocap.selectedObject()
        self.updateFromProperties()

    def addTargetFootR(self):
        self.properties.targetFootRStr.value = mocap.selectedObject()
        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    def _updateInstance(self):
        timeRange = self.properties.startEndFrameFloat.value
        self.footLockInstance = mocap.MocapFeetRetargeter(startTime=timeRange[0],
                                                          endTime=timeRange[1],
                                                          hips_source=self.properties.sourceHipsStr.value,
                                                          footL_source=self.properties.sourceFootLStr.value,
                                                          footR_source=self.properties.sourceFootRStr.value,
                                                          hips_target=self.properties.targetHipsStr.value,
                                                          footL_target=self.properties.targetFootLStr.value,
                                                          footR_target=self.properties.targetFootRStr.value)

    def createSetup(self):
        self._updateInstance()
        self.footLockInstance.createSetup(cleanup=True,
                                          rotYtrack=self.properties.rotYCheckbox.value)

    def createSetupKeepConstraints(self):
        self._updateInstance()
        self.footLockInstance.createSetup(cleanup=True,
                                          rotYtrack=self.properties.rotYCheckbox.value,
                                          bakeAndDelete=False)

    def scaleControls(self):
        if not self.footLockInstance:
            self._updateInstance()
        self.footLockInstance.scaleControls(self.properties.controlSizeFloat.value)

    def scaleBtnPressed(self, positive=True):
        if not self.footLockInstance:
            self._updateInstance()
        scale = self.footLockInstance.controlsScale()
        if scale is None:  # controls not found
            output.displayWarning("Hip control has not been found, please build or rebuild the setup")
            return

        multiplier, reset = keyboardmouse.ctrlShiftMultiplier()  # for alt shift and ctrl keys with left click
        scaleMult = 5.0
        if reset:  # try to reset with the zoo scale tracker (if it exists)
            newScale = 1.0
        else:
            scaleMult = scaleMult * multiplier  # if control or shift is held down
            if positive:
                newScale = scale + (scaleMult * .01)  # 5.0 becomes 1.05
            else:  # negative
                newScale = scale - (scaleMult * .01)  # 5.0 becomes 0.95
        self.footLockInstance.scaleControls(newScale)
        self.properties.controlSizeFloat.value = newScale
        self.updateFromProperties()

    def bakeLocDelConstraints(self):
        if not self.footLockInstance:
            self._updateInstance()
        self.footLockInstance.bakeMarkersDelConstraints()

    def deleteSetup(self):
        if self.footLockInstance is None:
            self._updateInstance()
        self.footLockInstance.deleteSetup()

    def constrainControls(self):
        if self.footLockInstance is None:
            self._updateInstance()
        self.footLockInstance.constrainControls()

    def deleteControlConstraints(self):
        if self.footLockInstance is None:
            self._updateInstance()
        self.footLockInstance.deleteControlConstraints()

    def bakeAndRemoveSetup(self):
        if self.footLockInstance is None:
            self._updateInstance()
        self.footLockInstance.bakeControls()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.rangeOptionsCombo.itemChanged.connect(self.rangeComboChanged)
            widget.createSetupBtn.clicked.connect(self.createSetup)
            widget.deleteSetupBtn.clicked.connect(self.deleteSetup)
            widget.constrainTargetBtn.clicked.connect(self.constrainControls)
            widget.deleteConstraintTargetBtn.clicked.connect(self.deleteControlConstraints)
            widget.bakeAndRemoveSetupBtn.clicked.connect(self.bakeAndRemoveSetup)
            # add object buttons
            widget.sourceHipsBtn.clicked.connect(self.addHipsSource)
            widget.sourceFootLBtn.clicked.connect(self.addFootLSource)
            widget.sourceFootRBtn.clicked.connect(self.addFootRSource)
            widget.targetHipsBtn.clicked.connect(self.addTargetHips)
            widget.targetFootLBtn.clicked.connect(self.addTargetFootL)
            widget.targetFootRBtn.clicked.connect(self.addTargetFootR)
            # Scale controls
            widget.controlSizeFloat.textModified.connect(self.scaleControls)
            widget.scalePosBtn.clicked.connect(partial(self.scaleBtnPressed, positive=True))
            widget.scaleNegBtn.clicked.connect(partial(self.scaleBtnPressed, positive=False))
            # Right Clicks
            widget.createSetupBtn.addAction("Create Setup Keep Constraints",
                                            mouseMenu=QtCore.Qt.RightButton,
                                            icon=iconlib.icon("legWalk"),
                                            connect=self.createSetupKeepConstraints)
            widget.createSetupBtn.addAction("Bake And Delete Locator Constraints",
                                            mouseMenu=QtCore.Qt.RightButton,
                                            icon=iconlib.icon("bake"),
                                            connect=self.bakeLocDelConstraints)


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
        # Time Range -------------------------------------------
        tooltip = "Set the time range to bake. Enable by setting to `Custom Frame Range`"
        self.startEndFrameFloat = elements.VectorLineEdit(label="Start/End",
                                                          value=(1.0, 100.0),
                                                          axis=("start", "end"),
                                                          toolTip=tooltip,
                                                          editRatio=2,
                                                          labelRatio=1)
        # Use Time Slider Range Combo ----------------------------------
        tooltip = "Choose the time range to bake. Channel Box selection only. \n" \
                  " - Playback Range: Frames in the timeline while playing. \n" \
                  " - Full Animation Range: All frames in the min/max time slider setting. \n" \
                  " - Custom Range: User start and end frame."
        self.rangeOptionsCombo = elements.ComboBoxRegular(items=TIME_RANGE_COMBO_LIST,
                                                          setIndex=0,
                                                          toolTip=tooltip)
        # Rot Y Checkbox -------------------------------------------
        tooltip = "Check this setting on when the character not always facing one direction. Turning for example. \n" \
                  "In instances such as walk cycles and front facing animation you may prefer to switch this off. \n\n" \
                  "On: The Foot Offset will pivot around the hip Y rotation. Usually recommended. \n" \
                  "Off: No rotation from the hips will be passed onto the foot offset animation."
        self.rotYCheckbox = elements.CheckBox(label="Inherit Hips Rot Y",
                                              checked=True,
                                              toolTip=tooltip)
        # Control Size Float -------------------------------------------
        tooltip = "Scale the size of the control curves after the setup has been been built (Step 4)."
        self.controlSizeFloat = elements.FloatEdit(label="Control Size",
                                                   editText=1.0,
                                                   toolTip=tooltip
                                                   )
        toolTip = "Scale the controls larger.\n\n" \
                  " Shift: Fast\n" \
                  " Ctrl: Slow, " \
                  " Alt: Reset."
        self.scalePosBtn = elements.styledButton("",
                                                 "scaleUp",
                                                 toolTip=toolTip,
                                                 parent=self,
                                                 minWidth=uic.BTN_W_ICN_MED,
                                                 style=uic.BTN_TRANSPARENT_BG)
        toolTip = "Scale the controls smaller.\n\n" \
                  " Shift: Fast\n" \
                  " Ctrl: Slow, " \
                  " Alt: Reset."
        self.scaleNegBtn = elements.styledButton("",
                                                 "scaleDown",
                                                 toolTip=toolTip,
                                                 parent=self,
                                                 minWidth=uic.BTN_W_ICN_MED,
                                                 style=uic.BTN_TRANSPARENT_BG)
        # Source Text ---------------------------------------
        tooltip = "Select and add the mocap skeleton's hip joint, base of the spine."
        self.sourceHipsStr = elements.StringEdit(label="Hips",
                                                 editPlaceholder="MocapHips_jnt",
                                                 toolTip=tooltip,
                                                 labelRatio=1,
                                                 editRatio=2)
        self.sourceHipsBtn = elements.styledButton("",
                                                   "arrowLeft",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_TRANSPARENT_BG,
                                                   minWidth=15)
        tooltip = "Select and add the mocap skeleton's left foot joint. Usually the ankle joint."
        self.sourceFootLStr = elements.StringEdit(label="Foot L",
                                                  editPlaceholder="MocapFootL_jnt",
                                                  toolTip=tooltip,
                                                  labelRatio=1,
                                                  editRatio=2)
        self.sourceFootLBtn = elements.styledButton("",
                                                    "arrowLeft",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15)
        tooltip = "Select and add the mocap skeleton's right foot joint. Usually the ankle joint."
        self.sourceFootRStr = elements.StringEdit(label="Foot R",
                                                  editPlaceholder="MocapFootR_jnt",
                                                  toolTip=tooltip,
                                                  labelRatio=1,
                                                  editRatio=2)
        self.sourceFootRBtn = elements.styledButton("",
                                                    "arrowLeft",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15)
        # Target Text ---------------------------------------
        tooltip = "Select and add the rigs root/hips/cog control. The main hip control that moves the character."
        self.targetHipsStr = elements.StringEdit(label="",
                                                 editPlaceholder="Hips_ctrl",
                                                 toolTip=tooltip,
                                                 labelRatio=1,
                                                 editRatio=2)
        self.targetHipsBtn = elements.styledButton("",
                                                   "arrowLeft",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_TRANSPARENT_BG,
                                                   minWidth=15)
        tooltip = "Select and add the rig's left foot control. Usually the ankle control."
        self.targetFootLStr = elements.StringEdit(label="",
                                                  editPlaceholder="IkFootL_ctrl",
                                                  toolTip=tooltip,
                                                  labelRatio=1,
                                                  editRatio=2)
        self.targetFootLBtn = elements.styledButton("",
                                                    "arrowLeft",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15)
        tooltip = "Select and add the rig's right foot control. Usually the ankle control."
        self.targetFootRStr = elements.StringEdit(label="",
                                                  editPlaceholder="IkFootR_ctrl",
                                                  toolTip=tooltip,
                                                  labelRatio=1,
                                                  editRatio=2)
        self.targetFootRBtn = elements.styledButton("",
                                                    "arrowLeft",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15)
        # Create Setup Button ---------------------------------------
        tooltip = "Creates and bakes the `Foot Retarget Setup`. \n\n" \
                  "Build the setup on the first frame of the animation. \n" \
                  "After the setup has been built, move the feet controls to better match the rig's feet position. \n\n" \
                  "Right-Click for individual create and bake steps."
        self.createSetupBtn = elements.AlignedButton("4. Create The Foot Lock Setup",
                                                     icon="legWalk",
                                                     toolTip=tooltip)
        # Delete Setup Button ---------------------------------------
        tooltip = ("Deletes The Foot Lock Setup. \n"
                   "This will delete the setup's controls from the scene.")
        self.deleteSetupBtn = elements.styledButton("",
                                                    icon="trash",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_DEFAULT)
        # Constrain Controls Button ---------------------------------------
        tooltip = ("Constrains the rig controls to the foot lock setup. \n"
                   "This will constrain the rig controls to the setup after the setup has been built and positioned. \n"
                   "The rig controls will now follow the mocap feet. Playback and test the animation. \n"
                   "After constraining you may key the offset controls to better lock or fix intersections.")

        self.constrainTargetBtn = elements.AlignedButton("6. Constrain The Target Controls",
                                                         icon="link",
                                                         toolTip=tooltip)
        # Delete Constraints Button ---------------------------------------
        tooltip = "Delete rig constraints that match the retarget setup."
        self.deleteConstraintTargetBtn = elements.styledButton("",
                                                               icon="trash",
                                                               toolTip=tooltip,
                                                               style=uic.BTN_DEFAULT)
        # Bake And Remove Setup Button ---------------------------------------
        tooltip = ("Bakes the rig's animation and deletes the `Retarget Setup` from the scene. \n"
                   "After baking you may also delete the mocap skeleton from the scene. ")
        self.bakeAndRemoveSetupBtn = elements.AlignedButton("8. Bake And Remove The Setup",
                                                            icon="bake",
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
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Time Range Layout -----------------------------
        timeRangeLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        timeRangeLayout.addWidget(self.rangeOptionsCombo, 1)
        timeRangeLayout.addWidget(self.startEndFrameFloat, 1)
        # ctrlSize Layout ---------------------------------------
        ctrlSizeLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        ctrlSizeLayout.addWidget(self.controlSizeFloat, 20)
        ctrlSizeLayout.addWidget(self.scalePosBtn, 1)
        ctrlSizeLayout.addWidget(self.scaleNegBtn, 1)
        # Options2 Layout ---------------------------------------
        options2Layout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        options2Layout.addLayout(ctrlSizeLayout, 1)
        options2Layout.addWidget(self.rotYCheckbox, 1)
        # Options Layout ---------------------------------------
        optionsLayout = elements.vBoxLayout(margins=(5, 0, 5, 0), spacing=uic.SREG)
        optionsLayout.addLayout(timeRangeLayout)
        optionsLayout.addLayout(options2Layout)

        # Source Layouts ---------------------------------------
        sourceHipsLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        sourceHipsLayout.addWidget(self.sourceHipsStr, 20)
        sourceHipsLayout.addWidget(self.sourceHipsBtn, 1)
        sourceHipsLayout.addWidget(self.targetHipsStr, 14)
        sourceHipsLayout.addWidget(self.targetHipsBtn, 1)
        sourceFootLLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        sourceFootLLayout.addWidget(self.sourceFootLStr, 20)
        sourceFootLLayout.addWidget(self.sourceFootLBtn, 1)
        sourceFootLLayout.addWidget(self.targetFootLStr, 14)
        sourceFootLLayout.addWidget(self.targetFootLBtn, 1)
        sourceFootRLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        sourceFootRLayout.addWidget(self.sourceFootRStr, 20)
        sourceFootRLayout.addWidget(self.sourceFootRBtn, 1)
        sourceFootRLayout.addWidget(self.targetFootRStr, 14)
        sourceFootRLayout.addWidget(self.targetFootRBtn, 1)
        # Create Setup Layout ---------------------------------------
        createSetupLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        createSetupLayout.addWidget(self.createSetupBtn, 20)
        createSetupLayout.addWidget(self.deleteSetupBtn, 1)
        # Constraint Layouts ---------------------------------------
        constraintLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        constraintLayout.addWidget(self.constrainTargetBtn, 20)
        constraintLayout.addWidget(self.deleteConstraintTargetBtn, 1)

        # Label 1 Layout ---------------------------------------
        label1Layout = elements.hBoxLayout(margins=(10, 5, 0, 5), spacing=uic.SPACING)
        tooltip = ("Before using this tool, use the `Bake & Match Animation` tool to transfer \n"
                   "the motion of the mocap skeleton's mocap to the rig in FK mode.\n\n"
                   "See the tools help page `?` icon for more information and video workflow.")
        label1Layout.addWidget(elements.Label("1. Bake Mocap To FK Controls.  Use The `Match & Bake Anim` Tool",
                                              toolTip=tooltip))
        # Label 2 Layout ---------------------------------------
        label2Layout = elements.hBoxLayout(margins=(10, 5, 0, 5), spacing=uic.SPACING)
        tooltip = ("Switch the rig to IK mode and bake the FK controls to the IK controls. \n\n"
                   "On Hive rigs select both feet controls, and activate the right-click menu: \n"
                   " > IK FK Match > IK Bake Timeline")
        label2Layout.addWidget(elements.Label("2. On The Rig Switch And Bake The Leg FK Controls To IK",
                                              toolTip=tooltip))
        # Label 3 Layout ---------------------------------------
        label3Layout = elements.hBoxLayout(margins=(10, 5, 0, 5), spacing=uic.SPACING)
        tooltip = ("Group the motion-capture skeleton and scale it so the leg and \n"
                   "hip height best matches the control rig's hip and leg size. \n"
                   "The upper body/spine size should be ignored.")
        label3Layout.addWidget(elements.Label("3. Scale The Mocap Skeleton Leg/Hips To Match The Rig",
                                              toolTip=tooltip))
        # Label 4 Layout ---------------------------------------
        label4Layout = elements.hBoxLayout(margins=(10, 5, 0, 5), spacing=uic.SPACING)
        tooltip = ("On the first frame of the animation, after the Retarget Setup has been built, \n"
                   "move the retarget foot cube controls to match each of the control rig's foot/ankle positions. \n"
                   "Do not move the handles, only move the cube controls. \n"
                   "Optionally you may adjust the hip control too.")
        label4Layout.addWidget(elements.Label("5. Move The Foot Ctrls To Better Match Rig Feet. Frame 1",
                                              toolTip=tooltip))
        # Label 5 Layout ---------------------------------------
        label5Layout = elements.hBoxLayout(margins=(10, 5, 0, 5), spacing=uic.SPACING)
        tooltip = "You can now move or keyframe the Retarget Setup's `hip` and `foot` controls to fix intersections."
        label5Layout.addWidget(elements.Label("7. Move or Keyframe The Foot/Hip Ctrls To Match/Lock Feet",
                                              toolTip=tooltip))

        # sourceTarget Layout ---------------------------------------
        sourceTargetLayout = elements.vBoxLayout(margins=(5, 0, 5, 0), spacing=uic.SREG)
        sourceTargetLayout.addLayout(sourceHipsLayout)
        sourceTargetLayout.addLayout(sourceFootLLayout)
        sourceTargetLayout.addLayout(sourceFootRLayout)

        # button layout ---------------------------------------
        buttonLayout = elements.vBoxLayout(margins=(5, 0, 5, 0), spacing=uic.SREG)
        buttonLayout.addLayout(label1Layout)
        buttonLayout.addLayout(label2Layout)
        buttonLayout.addLayout(label3Layout)
        buttonLayout.addLayout(createSetupLayout)
        buttonLayout.addLayout(label4Layout)
        buttonLayout.addLayout(constraintLayout)
        buttonLayout.addLayout(label5Layout)
        buttonLayout.addWidget(self.bakeAndRemoveSetupBtn)

        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(elements.LabelDivider("Options"))
        mainLayout.addLayout(optionsLayout)
        mainLayout.addWidget(elements.LabelDivider("Source And Target Objects"))
        mainLayout.addLayout(sourceTargetLayout)
        mainLayout.addWidget(elements.LabelDivider("Workflow"))
        mainLayout.addLayout(buttonLayout)


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
        mainLayout.addWidget(self.aLabelAndTextbox)
        mainLayout.addWidget(self.aBtn)
