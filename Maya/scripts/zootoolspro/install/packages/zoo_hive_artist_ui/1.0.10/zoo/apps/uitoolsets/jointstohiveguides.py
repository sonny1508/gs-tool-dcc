""" ---------- Joints To Hive Guides -------------


"""
from maya import cmds
import maya.mel as mel

from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs import iconlib
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.hotkeys import definedhotkeys
from zoo.libs.utils import output
from zoo.libs.hive import api as hiveapi
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.objutils import joints, objhandling
from zoo.libs.hive.base.util import fkutils
from zoo.libs.hive.base import rig
from zoo.libs.maya.cmds.modeling import create

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

SIDE_DICT = {"L": "L",
             "l": "l",
             "R": "R",
             "r": "r",
             "M": "M",
             "m": "m",
             "c": "c",
             "C": "C",
             "LEFT": "left",
             "left": "left",
             "RIGHT": "RIGHT",
             "right": "right",
             "middle": "mid",
             "ctr": "ctr"
             }

SIDE_LIST = ["M", "L", "R", "middle", "ctr", "m", "c", "C", "LEFT", "left", "l", "RIGHT", "right", "r"]


class JointsToHiveGuides(toolsetwidget.ToolsetWidget):
    id = "jointsToHiveGuides"
    info = "UI for converting a joint chain to Hive FK Guide component."
    uiData = {"label": "Joints To Hive Guides",
              "icon": "hiveJointsToGuides",
              "tooltip": "UI for converting a joint chain to Hive FK Guide component.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-joints-to-hive-guides/"}

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
        self.uiConnections()
        self._rigStateChanged()

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
        return super(JointsToHiveGuides, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(JointsToHiveGuides, self).widgets()

    # -------------------
    # UPDATE UI
    # -------------------

    def createJoint(self):
        """Invokes the joint create tool"""
        mel.eval("JointTool;")

    def createJointSelection(self):
        """Creates a joint at the center of the selection"""
        create.createPrimitiveAndMatch(primitive="joint")

    def createJointsAtSelectionMulti(self):
        """Creates a joint at the center of every selected object"""
        create.createPrimitiveAndMatchMultiSel(primitive="joint")

    def createPrimitiveMatchMultiParent(self):
        """Creates a joint at the center of every selected object"""
        create.createPrimitiveAndMatchMultiSel(primitive="joint", parent=True)

    def openJointToolWindow(self):
        """Opens the joint tool window"""
        definedhotkeys.open_jointTool(advancedMode=False)

    # -------------------
    # HIVE CORE
    # -------------------

    def updateRigs(self, rigs):
        oldPropertyValue = self.compactWidget.rigListCombo.currentText()
        self.compactWidget.rigListCombo.clear()
        self.compactWidget.rigListCombo.addItems([i.name() for i in rigs])
        self.compactWidget.rigListCombo.setToText(oldPropertyValue)

    def sceneRigs(self):
        """

        :return:
        :rtype: list[:class:`zoo.libs.hive.base.rig.Rig`]
        """
        return list(hiveapi.iterSceneRigs())

    def _rigStateChanged(self):
        sceneRigs = self.sceneRigs()
        self.updateRigs(sceneRigs)

    def _currentRigChangedFromArtistUI(self, rigName):
        self.setCurrentRig(rigName)

    def setCurrentRig(self, rigName):
        self.compactWidget.rigListCombo.setToText(rigName)

    # ------------------
    # LOGIC
    # ------------------

    def jointsToHive(self):
        # Find Selected Joints ------------------
        side = self.compactWidget.sideList[self.properties.sideComboBox.value]
        componentName = self.properties.componentNameTxt.value
        selJoints = cmds.ls(selection=True, type="joint", long=True)
        if not selJoints:
            output.displayWarning("Nothing selected. Please select joints.")
            return
        if not componentName:
            output.displayWarning("No component name entered, please enter a component name.")
            return
        if self.properties.selHierarchyRadioWidget.value:
            selJoints = joints.filterChildJointList(selJoints)
            # Sort the joints into correct hierarchy order
            rootJoints = objhandling.getRootObjectsFromList(selJoints)
            if len(rootJoints) > 1:
                output.displayWarning("More than one root joint selected. Please select a single joint chain.")
                return
            if len(selJoints) > 1:
                selJoints = joints.getJointChain(rootJoints[0], endJoint="")  # sorts the joints
        # Joints to Zapi ------------------
        zapiJnts = list(zapi.nodesByNames(selJoints))
        # Joints to Hive ------------------
        r = hiveapi.Rig()
        currentRig = self.compactWidget.rigListCombo.currentText()
        if not currentRig:
            r = rig.Rig()
            r.startSession("HiveRig", namespace="")  # Creates a new Hive rig
        else:
            r.startSession(currentRig)
        component = r.createComponent("fkchain", componentName, SIDE_DICT[side])

        fkutils.transformsToFkGuides(r, component, zapiJnts,
                                     guideScale=self.properties.scaleFloat.value)
        r.buildGuides()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.jointsToHiveBtn.clicked.connect(self.jointsToHive)
            widget.openJointToolWindowBtn.clicked.connect(self.openJointToolWindow)
            widget.createJntBtn.clicked.connect(self.createJoint)
            # Right Click Menu
            widget.createJntBtn.addAction("Enter the `Create Joint Tool`",
                                          mouseMenu=QtCore.Qt.RightButton,
                                          icon=iconlib.icon("skeleton"),
                                          connect=self.createJoint)
            widget.createJntBtn.addAction("Create A Joint At Selection",
                                          mouseMenu=QtCore.Qt.RightButton,
                                          icon=iconlib.icon("skeleton"),
                                          connect=self.createJointSelection)
            widget.createJntBtn.addAction("Create Joints Multi Selection",
                                          mouseMenu=QtCore.Qt.RightButton,
                                          icon=iconlib.icon("skeleton"),
                                          connect=self.createJointsAtSelectionMulti)
            widget.createJntBtn.addAction("Create Joints Multi Parent",
                                          mouseMenu=QtCore.Qt.RightButton,
                                          icon=iconlib.icon("skeleton"),
                                          connect=self.createPrimitiveMatchMultiParent)
            widget.createJntBtn.addAction("Open The Joint Tool Window",
                                          mouseMenu=QtCore.Qt.RightButton,
                                          icon=iconlib.icon("windowBrowser"),
                                          connect=self.openJointToolWindow)


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
        # Selected Hierarchy Radio Buttons ------------------------------------
        radioNameList = ["Selected", "Hierarchy"]
        radioToolTipList = ["Affects only the selected joints.",
                            "Affects the selected joints and all of it's child joints."]
        self.selHierarchyRadioWidget = elements.RadioButtonGroup(radioList=radioNameList,
                                                                 toolTipList=radioToolTipList,
                                                                 default=1,
                                                                 parent=parent,
                                                                 margins=(uic.SVLRG2, 0, uic.SVLRG2, 0),
                                                                 spacing=uic.SXLRG)
        # Rig Combo -----------------------------
        toolTip = "Select the Hive rig from the scene to export. \n" \
                  "If none are available, please build a rig in the Hive UI."
        self.rigListCombo = elements.ComboBoxRegular("Rig Name",
                                                     items=[],
                                                     parent=self,
                                                     labelRatio=10,
                                                     boxRatio=20,
                                                     toolTip=toolTip)
        # Component Name -----------------------------
        toolTip = "The name of the new FK Component that will be created."
        self.componentNameTxt = elements.StringEdit(label="New Compnt",
                                                    editText="fkChain",
                                                    parent=self,
                                                    labelRatio=10,
                                                    editRatio=20,
                                                    toolTip=toolTip)
        # Scale Float -----------------------------
        toolTip = "The per guide scale of the new Hive FK Component."
        self.scaleFloat = elements.FloatEdit(label="Scale",
                                             editText=1.0,
                                             labelRatio=1,
                                             editRatio=2,
                                             parent=parent,
                                             toolTip=toolTip)
        # Side Combo -----------------------------
        field = hiveapi.Configuration().findNamingConfigForType("zootoolsProGlobalConfig").field("side")
        self.sideList = sorted(list([i.name for i in field.keyValues()]))
        toolTip = "Select the side convention for the new component, left right or middle. \n" \
                  "Sides can be changed after creation in the Hive UI."
        self.sideComboBox = elements.ComboBoxRegular("Side",
                                                     self.sideList,
                                                     setIndex=3,
                                                     labelRatio=1,
                                                     boxRatio=2,
                                                     parent=self,
                                                     toolTip=toolTip)

        # Convert Selected Joints ---------------------------------------
        tooltip = "Converts the selected joints to a new Hive FK component. \n" \
                  "Supports joints with multiple branches. "
        self.jointsToHiveBtn = elements.styledButton("Joints To Hive FK Component",
                                                     icon="hiveJointsToGuides",
                                                     toolTip=tooltip,
                                                     style=uic.BTN_DEFAULT)
        # Build Layout ---------------------------------------
        tooltip = "Create Joint Tool. \n" \
                  "Right-click for more options."
        self.createJntBtn = elements.styledButton("",
                                                  icon="skeleton",
                                                  toolTip=tooltip,
                                                  style=uic.BTN_DEFAULT,
                                                  minWidth=35)
        # Build Layout ---------------------------------------
        tooltip = "Open the Joint Tool Window \n" \
                  "for full joint alignment options."
        self.openJointToolWindowBtn = elements.styledButton("",
                                                            icon="windowBrowser",
                                                            toolTip=tooltip,
                                                            style=uic.BTN_DEFAULT,
                                                            minWidth=35)


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
        # RigName Scale Layout -----------------------
        nameScaleLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(0, 0, 0, 0))
        nameScaleLayout.addWidget(self.rigListCombo, 2)
        nameScaleLayout.addWidget(self.scaleFloat, 1)
        # Component Name Layout -----------------------
        componentLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(0, 0, 0, 0))
        componentLayout.addWidget(self.componentNameTxt, 2)
        componentLayout.addWidget(self.sideComboBox, 1)
        # Button Layout -----------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING, margins=(0, 0, 0, 0))
        buttonLayout.addWidget(self.jointsToHiveBtn, 20)
        buttonLayout.addWidget(self.createJntBtn, 1)
        buttonLayout.addWidget(self.openJointToolWindowBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.selHierarchyRadioWidget)
        mainLayout.addLayout(nameScaleLayout)
        mainLayout.addLayout(componentLayout)
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
        mainLayout.addWidget(self.jointsToHiveBtn)
