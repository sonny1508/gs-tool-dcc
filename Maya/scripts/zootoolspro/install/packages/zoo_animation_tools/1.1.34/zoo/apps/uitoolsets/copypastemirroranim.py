""" ---------- Mirror Copy Paste Animation -------------

TODO: Add merge types

"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.animation import timerange

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

CYCLE_LIST = ["constant", "linear", "cycle", "cycleRelative", "oscillate"]
FLIP_PRESETS = ["No Mirror - Copy Only", "Mirror - World Controls/Joints", "Mirror - FK Regular"]
FLIP_PRESET_NONE = [False, False, False, False, False, False]
FLIP_PRESET_WORLD = [True, False, False, False, True, True]
FLIP_PRESET_FKREG = [True, True, True, False, False, False]
FLIP_VAL_LIST = [FLIP_PRESET_NONE, FLIP_PRESET_WORLD, FLIP_PRESET_FKREG]


class CopyPasteMirrorAnim(object):  # toolsetwidget.ToolsetWidget  Tool disabled
    id = "copyPasteMirrorAnim"
    info = "Copy and paste and mirror animation."
    uiData = {"label": "Copy/Paste (Mirror) Animation",
              "icon": "symmetryTri",
              "tooltip": "Mirror copy and paste animation.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-copy-paste-mirror-animation"
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
        return super(CopyPasteMirrorAnim, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(CopyPasteMirrorAnim, self).widgets()

    # ------------------
    # UI UPDATE
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

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def mirrorPasteAnimation(self):
        """Runs the tool.
        """
        pass
        return
        xxx(self.properties.startFloatEdit.value,
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
            widget.mirrorPasteAnimationBtn.clicked.connect(self.mirrorPasteAnimation)
            widget.presetFlipCombo.itemChanged.connect(self.setPreset)


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
        tooltip = "Opposite control offset amount in time. \n" \
                  "The pasted animation will be offset by this amount."
        self.offsetFloatEdit = elements.FloatEdit("Offset",
                                                  toolTip=tooltip,
                                                  editText=0.0,
                                                  labelRatio=1,
                                                  editRatio=2)
        # Mirror Control Panel Checkbox ---------------------------------------
        tooltip = "Include proxy attributes? These are attributes \n" \
                  "that may also belong to other objects."
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
        tooltip = ""
        self.presetFlipCombo = elements.ComboBoxRegular("Flip Presets",
                                                        items=FLIP_PRESETS,
                                                        setIndex=2,
                                                        labelRatio=8,
                                                        boxRatio=30,
                                                        margins=(uic.SMLPAD, 0, uic.SMLPAD, 0),
                                                        toolTip=tooltip)
        # Flip Channels Range Checkbox ---------------------------------------
        tooltip = ""
        self.translateLabel = elements.Label("Translate XYZ")
        self.translateXCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        self.translateYCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        self.translateZCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        self.rotateLabel = elements.Label("Rotate XYZ")
        self.rotateXCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        self.rotateYCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        self.rotateZCheckbox = elements.CheckBox("", checked=True, right=True, toolTip=tooltip)
        # Flip Custom Attributes ---------------------------------------
        tooltip = ""
        self.flipStringEdit = elements.StringEdit("Flip Custom",
                                                  editPlaceholder="attribute1, attribute2",
                                                  labelRatio=8,
                                                  editRatio=30,
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
        #  Clamp Button ---------------------------------------
        self.clampCurvesBtn = elements.AlignedButton("Clamp Time Curves",
                                                     icon="symmetryTri",
                                                     toolTip=tooltip)
        #  Thread End Button ---------------------------------------
        self.matchOuterTangentsBtn = elements.AlignedButton("Match Outer Tangents",
                                                            icon="symmetryTri",
                                                            toolTip=tooltip)
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
        # Mirror Animation To Opposite Control Button ---------------------------------------
        tooltip = "Copies, mirrors animation from first half of selected objects \n" \
                  "to the second half of selected objects \n" \
                  "The offset/mirror options are useful for cycles. \n" \
                  "Start and end frames should have identical poses for cycles. \n" \
                  "Example: 0-24 not 1-24"
        self.mirrorPasteAnimationBtn = elements.styledButton("Mirror Paste Animation - Selected Objects",
                                                             icon="symmetryTri",
                                                             toolTip=tooltip,
                                                             style=uic.BTN_DEFAULT)
        self.flipCollapsable = elements.CollapsableFrameThin("Mirror (Inverse/Flip) Attributes",
                                                             contentMargins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG),
                                                             contentSpacing=uic.SLRG,
                                                             collapsed=True)
        self.prePostCollapsable = elements.CollapsableFrameThin("Mirror Pre/Post Infinity",
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
                                         spacing=uic.SLRG)
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
        tangentLayout.addWidget(self.clampCurvesBtn, 1)
        tangentLayout.addWidget(self.matchOuterTangentsBtn, 1)
        # Button V Layout ---------------------------------------
        vButtonLayout = elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        vButtonLayout.addLayout(tangentLayout)
        vButtonLayout.addWidget(self.mirrorPasteAnimationBtn)
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
                                         spacing=uic.SLRG)
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
        # Flip String Layout ---------------------------------------
        flipStringLayout = elements.hBoxLayout(margins=(uic.SMLPAD, 0, uic.SMLPAD, 0))
        flipStringLayout.addWidget(self.flipStringEdit)
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
        # Infinite Layout ---------------------------------------
        infiniteLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        infiniteLayout.addWidget(self.toggleInfinityBtn, 1)
        infiniteLayout.addWidget(self.removeCycleAnimationBtn, 1)
        # Tangent Layout ---------------------------------------
        tangentLayout = elements.hBoxLayout(margins=(0, 0, 0, 0),
                                            spacing=uic.SPACING)
        tangentLayout.addWidget(self.clampCurvesBtn, 1)
        tangentLayout.addWidget(self.matchOuterTangentsBtn, 1)
        # Button V Layout ---------------------------------------
        vButtonLayout = elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        vButtonLayout.addLayout(infiniteLayout)
        vButtonLayout.addLayout(tangentLayout)
        vButtonLayout.addWidget(self.mirrorPasteAnimationBtn)
        #  Flip Collapsable ---------------------------------------
        self.flipCollapsable.addWidget(self.presetFlipCombo)
        self.flipCollapsable.addLayout(transRotLayout)
        self.flipCollapsable.addLayout(flipStringLayout)
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
