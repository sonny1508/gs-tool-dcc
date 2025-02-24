""" ---------- Replace Joint Weights -------------

"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.skin import skinreplacejoints

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ReplaceJointWeights(toolsetwidget.ToolsetWidget):
    id = "replacejointweights"
    info = "Transfers skinning between joints."
    uiData = {"label": "Replace Joint Weights",
              "icon": "replaceJointWeights",
              "tooltip": "Transfers skinning between joints.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-replace-joint-weights/"
              }

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
        return super(ReplaceJointWeights, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ReplaceJointWeights, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def skinReplaceJoints(self):
        """Does the replace with suffix prefix see skinreplacejoints.replaceJointsMatrixSuffix() for documentation
        """
        skinreplacejoints.replaceJointsMatrixSuffix(boundText=self.properties.boundTxt.value,
                                                    replaceText=self.properties.replaceTxt.value,
                                                    prefix=not self.properties.suffixPrefixRadioGrp.value,
                                                    message=True)

    def skinReplaceJointsSel(self):
        """Does the replace via selection see skinreplacejoints.replaceJointsMatrixSel() for documentation
        """
        skinreplacejoints.replaceJointsMatrixSel(message=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.transferSuffixPrefixBtn.clicked.connect(self.skinReplaceJoints)
            widget.transferSelBtn.clicked.connect(self.skinReplaceJointsSel)


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
        # Radio Suffix Prefix ------------------------------------------
        tooltips = ["Text will search for prefixes `text_*` in both names.",
                    "Text will search for suffixes `*_text` in both names."]
        self.suffixPrefixRadioGrp = elements.RadioButtonGroup(["Names are Prefixed", "Names are Suffixed"],
                                                              toolTipList=tooltips,
                                                              default=0,
                                                              margins=(uic.SXLRG, uic.SREG, uic.SLRG, uic.SREG))
        # Bound Joint Text ---------------------------------------------
        toolTip = "The suffix/prefix name of the currently bound joints. \n" \
                  "Joint's named with this suffix or prefix will be replaced with new joints. \n" \
                  "Names must be unique in the scene."
        self.boundTxt = elements.StringEdit(label="Old Search",
                                            editText="OLD",
                                            toolTip=toolTip,
                                            labelRatio=2,
                                            editRatio=5)
        # Replace Joint Text -------------------------------------------
        tooltip = "The suffix/prefix name of the new joints to replace the skin weights. \n" \
                  "Joint's named with this suffix or prefix will replace the bound joints. \n" \
                  "Names must be unique in the scene."
        self.replaceTxt = elements.StringEdit(label="New Search",
                                              editText="NEW",
                                              toolTip=tooltip,
                                              labelRatio=2,
                                              editRatio=5)
        # Transfer Suffix Prefix ---------------------------------------
        tooltip = "Replaces all old joint weights with new joints in the scene. \n" \
                  "Searches the scene for joints by either the suffix or prefix names. \n" \
                  "Use names that are unique in the scene."
        self.transferSuffixPrefixBtn = elements.styledButton("Replace Suffix/Prefix",
                                                             icon="replaceJointWeights",
                                                             toolTip=tooltip,
                                                             style=uic.BTN_DEFAULT)
        # Transfer Selection ---------------------------------------
        tooltip = "Replaces the currently selected joints in order. \n" \
                  "Select old joints in order first. \n" \
                  "Then select new joints and run."
        self.transferSelBtn = elements.styledButton("Replace Selected Joints",
                                                             icon="replaceJointWeights",
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
        # Suffix Row ---------------------------------------
        suffixLayout = elements.hBoxLayout(spacing=uic.SREG)
        suffixLayout.addWidget(self.boundTxt)
        suffixLayout.addWidget(self.replaceTxt)
        # Button Layout ---------------------------------------
        btnLayout = elements.hBoxLayout(spacing=uic.SREG)
        btnLayout.addWidget(self.transferSuffixPrefixBtn)
        btnLayout.addWidget(self.transferSelBtn)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.suffixPrefixRadioGrp)
        mainLayout.addLayout(suffixLayout)
        mainLayout.addLayout(btnLayout)


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
        mainLayout.addWidget(self.transferSuffixPrefixBtn)
