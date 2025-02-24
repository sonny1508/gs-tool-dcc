from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.rig import reparentgrouptoggle


UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ReparentGroupToggle(toolsetwidget.ToolsetWidget):
    id = "reparentGroupToggle"
    info = "Toggle parent/unparent groups in and out of a hierarchy by name."
    uiData = {"label": "Reparent Group Toggle",
              "icon": "folderDown",
              "tooltip": "Toggle parent/unparent groups in and out of a hierarchy by name.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-reparent-group-toggle/"}

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
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype: GuiWidgets
        """
        return super(ReparentGroupToggle, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ReparentGroupToggle, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createReparentGroup(self):
        """Creates the reparent group
        """
        reparentgrouptoggle.createGroupToRigSelected(wildcardSuffix=self.properties.suffixTxt.value,
                                                     matchObject=self.properties.matchCheckBox.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def parentAllGroups(self):
        """Parents all reparent groups to their targets
        """
        reparentgrouptoggle.parentReparentGrpScene(parent=True,
                                                   wildcardSuffix=self.properties.suffixTxt.value,
                                                   matchObject=self.properties.matchCheckBox.value,
                                                   message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def unparentAllGroups(self):
        """Unparents all reparent groups to world
        """
        reparentgrouptoggle.parentReparentGrpScene(parent=False,
                                                   wildcardSuffix=self.properties.suffixTxt.value,
                                                   matchObject=self.properties.matchCheckBox.value,
                                                   message=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.createBtn.clicked.connect(self.createReparentGroup)
            widget.parentBtn.clicked.connect(self.parentAllGroups)
            widget.unparentBtn.clicked.connect(self.unparentAllGroups)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Create ---------------------------------------
        tooltip = "Creates an empty group match to a selected object named `objName_zooParentToRig`.  \n" \
                  "All groups matching this suffix can be either parented to the world or \n" \
                  "to their corresponding objName (prefix). \n" \
                  "Handy for parenting objects to third party autoriggers.\n\n" \
                  "This script relies on naming, all objects must have unique short names."
        self.createBtn = elements.styledButton("Create Reparent Group",
                                               icon="folderPlus",
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT)
        # Parent All In Scene ---------------------------------------
        tooltip = "Parents all groups in the scene with the suffix `*_zooParentToRig` to their \n" \
                  "corresponding prefix name. \n\n" \
                  "This script relies on naming, all objects must have unique short names."
        self.parentBtn = elements.AlignedButton("Parent All Grps",
                                               icon="folderDown",
                                               toolTip=tooltip)
        # Unparent All In Scene ---------------------------------------
        tooltip = "Unparents all groups in the scene with the suffix `*_zooParentToRig` to the world. \n\n" \
                  "This script relies on naming, all objects must have unique short names."
        self.unparentBtn = elements.AlignedButton("Unparent All Grps",
                                                 icon="folderUp",
                                                 toolTip=tooltip)
        if uiMode == UI_MODE_ADVANCED:
            # Wildcard Name ---------------------------------------
            tooltip = "Change the suffix name of the reparent groups"
            self.suffixTxt = elements.StringEdit(label="Suffix",
                                                 editText=reparentgrouptoggle.REPARENT_SUFFIX,
                                                 toolTip=tooltip,
                                                 labelRatio=1,
                                                 editRatio=4)
            # Match Checkbox ---------------------------------------
            tooltip = "Match groups to their target objects on creation and while parenting?"
            self.matchCheckBox = elements.CheckBox(label="Match",
                                                   checked=True,
                                                   toolTip=tooltip)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SPACING)
        # Main Layout ---------------------------------------
        parentLayout = elements.hBoxLayout(spacing=uic.SPACING)
        parentLayout.addWidget(self.parentBtn, 1)
        parentLayout.addWidget(self.unparentBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(parentLayout)
        mainLayout.addWidget(self.createBtn)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SPACING)
        # Name Layout ---------------------------------------
        nameLayout = elements.hBoxLayout()
        nameLayout.addWidget(self.suffixTxt, 5)
        nameLayout.addWidget(self.matchCheckBox, 2)
        # Parent Layout ---------------------------------------
        parentLayout = elements.hBoxLayout(margins=(0, uic.VSMLPAD, 0, 0), spacing=uic.SPACING)
        parentLayout.addWidget(self.parentBtn, 1)
        parentLayout.addWidget(self.unparentBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(nameLayout)
        mainLayout.addLayout(parentLayout)
        mainLayout.addWidget(self.createBtn)
