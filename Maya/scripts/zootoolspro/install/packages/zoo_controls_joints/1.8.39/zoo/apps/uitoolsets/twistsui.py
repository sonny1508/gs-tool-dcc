"""

"""
from functools import partial

from zoovendor.Qt import QtWidgets

from maya import cmds
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.utils import mayaenv
from zoo.libs.utils import output
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.rig import twists

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

AXIS_XYZ = ["x", "y", "z"]
MAYA_VERSION = float(mayaenv.mayaVersionNiceName())


class TwistExtractor(toolsetwidget.ToolsetWidget):
    id = "twistextractor"
    info = "Tool for rigging manual twist setups."
    uiData = {"label": "Twist Extractor",
              "icon": "twist",
              "tooltip": "Tool for rigging manual twist setups.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-twist-extractor/"}

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
        return super(TwistExtractor, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(TwistExtractor, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def createTwistExtractor(self):
        """Creates the setup"""
        if MAYA_VERSION < 2020.0:
            output.displayWarning("Twist Extractor is only available in Maya version 2020 and above.")
            return
        drivenStr = self.properties.drivenObjTextbox.value
        if cmds.objExists(drivenStr):
            driven = zapi.nodeByName(self.properties.drivenObjTextbox.value)
        else:
            driven = None
        twists.twistNodeNetwork(zapi.nodeByName(self.properties.driverATextbox.value),
                                zapi.nodeByName(self.properties.driverBTextbox.value),
                                drivenObj=driven,
                                drivenAttr=self.properties.drivenAttrTextbox.value,
                                axis=AXIS_XYZ[self.properties.axisCombo.value],
                                inverse=self.properties.invertCheckbox.value)

    def insertObjTest(self, textbox="A"):
        if MAYA_VERSION < 2020.0:
            output.displayWarning("Twist Extractor is only available in Maya version 2020 and above.")
            return
        obj = twists.obj()
        if obj:
            if textbox == "A":
                self.properties.driverATextbox.value = obj
            elif textbox == "B":
                self.properties.driverBTextbox.value = obj
            else: # textbox == "driven"
                self.properties.drivenObjTextbox.value = obj
            self.updateFromProperties()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.createTwistExtractorBtn.clicked.connect(self.createTwistExtractor)
            widget.insertDriverABtn.clicked.connect(partial(self.insertObjTest, textbox="A"))
            widget.insertDriverBBtn.clicked.connect(partial(self.insertObjTest, textbox="B"))
            widget.insertDrivenBtn.clicked.connect(partial(self.insertObjTest, textbox="driven"))


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
        # Driver A ---------------------------------------
        tooltip = "Enter the name of a driver A object (start twist)."
        self.driverATextbox = elements.StringEdit(label="Driver Object A",
                                                  editPlaceholder="shoulderJoint",
                                                  labelRatio=1,
                                                  editRatio=3,
                                                  toolTip=tooltip)
        # Driver B ---------------------------------------
        tooltip = "Enter the name of a driver B object (end twist)."
        self.driverBTextbox = elements.StringEdit(label="Driver Object A",
                                                  editPlaceholder="elbowJoint",
                                                  labelRatio=1,
                                                  editRatio=3,
                                                  toolTip=tooltip)
        # Driven Object ---------------------------------------
        tooltip = "Enter the name of a driven object (end twist)."
        self.drivenObjTextbox = elements.StringEdit(label="Driven Object",
                                                    editPlaceholder="",
                                                    labelRatio=10,
                                                    editRatio=13,
                                                    toolTip=tooltip)
        # Insert Driver A Object ---------------------------------------
        tooltip = "Select a object from the scene."
        self.insertDriverABtn = elements.styledButton("",
                                                      "arrowLeft",
                                                      self,
                                                      toolTip=tooltip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=15)
        # Insert Driver B Object ---------------------------------------
        tooltip = "Select a object from the scene."
        self.insertDriverBBtn = elements.styledButton("",
                                                      "arrowLeft",
                                                      self,
                                                      toolTip=tooltip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=15)
        # Insert Driven A Object ---------------------------------------
        tooltip = "Select a object from the scene."
        self.insertDrivenBtn = elements.styledButton("",
                                                     "arrowLeft",
                                                     self,
                                                     toolTip=tooltip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=15)

        # Driven Attribute ---------------------------------------
        tooltip = "Enter the name of a driven object (end twist)."
        self.drivenAttrTextbox = elements.StringEdit(label="Attribute",
                                                     editPlaceholder="",
                                                     labelRatio=1,
                                                     editRatio=3,
                                                     toolTip=tooltip)
        # Invert ---------------------------------------
        tooltip = "Invert the direction of the twist?."
        self.invertCheckbox = elements.CheckBox(label="Invert",
                                                toolTip=tooltip,
                                                right=True,
                                                labelRatio=1,
                                                boxRatio=2)
        # Invert ---------------------------------------
        tooltip = "Invert the direction of the twist?."
        self.axisCombo = elements.ComboBoxRegular(label="Axis",
                                                  items=AXIS_XYZ,
                                                  toolTip=tooltip,
                                                  labelRatio=10,
                                                  boxRatio=13)
        # Create Twist Extractor ---------------------------------------
        tooltip = "Creates a twist extractor accurate to -180 to +180 degrees "
        self.createTwistExtractorBtn = elements.styledButton("Create Twist Extractor",
                                                             icon="twist",
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
        # driverA --------------
        driverALayout = elements.hBoxLayout()
        driverALayout.addWidget(self.driverATextbox, 10)
        driverALayout.addWidget(self.insertDriverABtn, 1)
        # driverB --------------
        driverBLayout = elements.hBoxLayout()
        driverBLayout.addWidget(self.driverBTextbox, 10)
        driverBLayout.addWidget(self.insertDriverBBtn, 1)
        # driven --------------
        drivenLayout = elements.hBoxLayout()
        drivenLayout.addWidget(self.drivenObjTextbox, 10)
        drivenLayout.addWidget(self.insertDrivenBtn, 1)
        # driven attr --------------
        drivenAttrLayout = elements.hBoxLayout(spacing=uic.SLRG)
        drivenAttrLayout.addLayout(drivenLayout, 14)
        drivenAttrLayout.addWidget(self.drivenAttrTextbox, 10)
        # optionsLayout --------------
        optionsLayout = elements.hBoxLayout(spacing=uic.SXLRG)
        optionsLayout.addWidget(self.axisCombo, 12)
        optionsLayout.addWidget(self.invertCheckbox, 10)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(driverALayout)
        mainLayout.addLayout(driverBLayout)
        mainLayout.addWidget(elements.LabelDivider(text="Driven Object (Optional)"))
        mainLayout.addLayout(drivenAttrLayout)
        mainLayout.addWidget(elements.LabelDivider(text="Twist Options"))
        mainLayout.addLayout(optionsLayout)
        mainLayout.addWidget(self.createTwistExtractorBtn)


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
        mainLayout.addWidget(self.createTwistExtractorBtn)
