""" ---------- Toolset Boiler Plate (Multiple UI Modes) -------------
The following code is a template (boiler plate) for building Zoo Toolset GUIs that multiple UI modes.

Multiple UI modes include compact and medium or advanced modes.

This UI will use Compact and Advanced Modes.

The code gets more complicated while dealing with UI Modes.

"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.objutils import attributes

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ChannelBoxManager(toolsetwidget.ToolsetWidget):
    id = "channelBoxManager"
    info = "Manages Channel Box attributes."
    uiData = {"label": "Channel Box Manager",
              "icon": "channelbox",
              "tooltip": "Manages Channel Box attributes.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-channel-box-manager"}

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
        return super(ChannelBoxManager, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ChannelBoxManager, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def openAddAttrWindow(self):
        """Opens Maya's Add Attribute Window
        """
        attributes.openAddAttrWindow()

    def openEditAttrWindow(self):
        """Opens Maya's Edit Attribute Window
        """
        attributes.openEditAttrWindow()

    def openDeleteAttrWindow(self):
        """Opens Maya's Delete Attribute Window
        """
        attributes.openDeleteAttrWindow()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteSelectedAttr(self):
        """deletes the selected attr in the channel box.
        """
        attributes.deleteAttributeSel()

    def shuffleAttributeUp(self):
        """Shuffles selected channel box attributes up.  No undo.
        """
        attributes.shuffleAttrChannelBoxSel(up=True)

    def shuffleAttributeDown(self):
        """Shuffles selected channel box attributes down.  No undo.
        """
        attributes.shuffleAttrChannelBoxSel(up=False)

    def addSeparatorAttr(self):
        """
        """
        labelName = self.properties.separatorTxt.value
        attributes.labelAttrSel(labelName, message=True)

    def addDriverObject(self):
        """
        """
        obj, attr = attributes.lastNodeAttrFromSel(parent=True)
        if not obj:  # Message already given
            return
        self.properties.driverObjTxt.value = obj
        self.properties.driverAttrTxt.value = attr
        self.updateFromProperties()

    def addDrivenObjs(self):
        objsString = attributes.selObjsCommaSeparated()
        if objsString:
            self.properties.drivenObjTxt.value = objsString
            self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createProxyAttr(self):
        attributes.addProxyAttributeSel(self.properties.driverObjTxt.value,
                                        self.properties.driverAttrTxt.value,
                                        drivenNodeText=self.properties.drivenObjTxt.value,
                                        drivenAttr=self.properties.drivenAttrTxt.value,
                                        channelBox=True,
                                        nonKeyable=False)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.openAddAttrWindowBtn.clicked.connect(self.openAddAttrWindow)
            widget.openEditAttrWindowBtn.clicked.connect(self.openEditAttrWindow)
            widget.openDelAttrWindowBtn.clicked.connect(self.openDeleteAttrWindow)
            widget.deleteAttrBtn.clicked.connect(self.deleteSelectedAttr)

            widget.shuffleAttrUp.clicked.connect(self.shuffleAttributeUp)
            widget.shuffleAttrDown.clicked.connect(self.shuffleAttributeDown)

            widget.separatorBtn.clicked.connect(self.addSeparatorAttr)

            widget.addDriverTextBtn.clicked.connect(self.addDriverObject)
            widget.addDrivenTextBtn.clicked.connect(self.addDrivenObjs)
            widget.createProxyAttrBtn.clicked.connect(self.createProxyAttr)


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
        tooltip = "Select/highlight attribute name/s in the Channel Box and press to shuffle up/dwn." \
                  "Note: There is no undo on this tool."

        # Open Add Attribute ---------------------------------------
        tooltip = "Opens Maya's Add Attribute window."
        self.openAddAttrWindowBtn = elements.styledButton("Open Add Attr Window",
                                                          icon="windowBrowser",
                                                          toolTip=tooltip,
                                                          style=uic.BTN_LABEL_SML)
        # Open Edit Attribute ---------------------------------------
        tooltip = "Opens Maya's Edit Attribute window."
        self.openEditAttrWindowBtn = elements.styledButton("Open Edit Attr Window",
                                                           icon="windowBrowser",
                                                           toolTip=tooltip,
                                                           style=uic.BTN_LABEL_SML)

        # Open Delete Attribute ---------------------------------------
        tooltip = "Opens Maya's Delete Attribute window."
        self.openDelAttrWindowBtn = elements.styledButton("Open Delete Attr Window",
                                                          icon="windowBrowser",
                                                          toolTip=tooltip,
                                                          style=uic.BTN_LABEL_SML)
        # Delete Attribute ---------------------------------------
        tooltip = "Deletes any selected attributes in the channel box."
        self.deleteAttrBtn = elements.styledButton("Delete Selected Attr",
                                                   icon="trash",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_LABEL_SML)
        # Shuffle Label ----------------------------------------------------------------------------
        tooltip = "Highlight an attribute name/s in the Channel Box and press to shuffle down."
        self.shuffleLabel = elements.Label(text="Shuffle Selected Channel Box Attributes",
                                           toolTip=tooltip)
        # Shuffle up Button --------------
        self.shuffleAttrUp = elements.styledButton("",
                                                   icon="arrowUp",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_LABEL_SML)
        # Shuffle down Button -----------------
        self.shuffleAttrDown = elements.styledButton("",
                                                     icon="arrowDown",
                                                     toolTip=tooltip,
                                                     style=uic.BTN_LABEL_SML)
        # Add Separator Attr ---------------------------------------
        tooltip = "Add the name of the new label, select object/s then press to create an attribute separator. "
        self.separatorTxt = elements.StringEdit(label="Add Separator Attribute ",
                                                editPlaceholder="LabelName",
                                                toolTip=tooltip,
                                                labelRatio=10,
                                                editRatio=14)
        self.separatorBtn = elements.styledButton("",
                                                  icon="plusHollow",
                                                  toolTip=tooltip,
                                                  style=uic.BTN_LABEL_SML)
        # Add Proxy Driver Attr ---------------------------------------
        tooltip = "The driver object name."
        self.driverObjTxt = elements.StringEdit(label="Driver Obj",
                                                editPlaceholder="object",
                                                toolTip=tooltip,
                                                labelRatio=10,
                                                editRatio=15)
        tooltip = "The driver object's attribute name."
        self.driverAttrTxt = elements.StringEdit(label="Driver Attr",
                                                 editPlaceholder="attrName",
                                                 toolTip=tooltip,
                                                 labelRatio=10,
                                                 editRatio=15)
        tooltip = "Adds the selected object into the text fields.  \n" \
                  "Select an attribute in the channel box to also add the attribute name. "
        self.addDriverTextBtn = elements.styledButton("",
                                                      icon="arrowLeft",
                                                      toolTip=tooltip,
                                                      style=uic.BTN_TRANSPARENT_BG)
        # Add Proxy Driven Attr ---------------------------------------
        tooltip = "The object name that the proxy will be created. \n" \
                  "If left empty the currently selected object will be used. "
        self.drivenObjTxt = elements.StringEdit(label="Proxy Obj/s",
                                                editPlaceholder="selection",
                                                toolTip=tooltip,
                                                labelRatio=10,
                                                editRatio=15)
        tooltip = "The name of the proxy attribute to be created. \n" \
                  "If left empty the original attribute's name will be used. "
        self.drivenAttrTxt = elements.StringEdit(label="Proxy Attr",
                                                 editPlaceholder="optional",
                                                 toolTip=tooltip,
                                                 labelRatio=10,
                                                 editRatio=15)
        tooltip = "Adds the selected object into the proxy object text field. "
        self.addDrivenTextBtn = elements.styledButton("",
                                                      icon="arrowLeft",
                                                      toolTip=tooltip,
                                                      style=uic.BTN_TRANSPARENT_BG)
        tooltip = "Creates a proxy attribute using the text settings. \n" \
                  "If the bottom section is left empty then will attempt to use \n" \
                  "the selected object and the driver attribute name. "
        self.createProxyAttrBtn = elements.styledButton("Create Proxy Attribute",
                                                        icon="magnet",
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
        # shuffle layout ----------
        shuffleLayout = elements.hBoxLayout(spacing=uic.SREG, margins=(uic.SREG, 0, uic.SREG, 0))
        shuffleLayout.addWidget(self.shuffleLabel, 20)
        shuffleLayout.addWidget(self.shuffleAttrUp, 1)
        shuffleLayout.addWidget(self.shuffleAttrDown, 1)

        # Attribute Windows Layout -------------------------------
        attrWindowLayout = elements.GridLayout(hSpacing=uic.SVLRG2,
                                               vSpacing=8,
                                               margins=(uic.SREG, 0, uic.SREG, 0))
        row = 0
        attrWindowLayout.addWidget(self.openAddAttrWindowBtn, row, 0)
        attrWindowLayout.addWidget(self.openEditAttrWindowBtn, row, 1)
        row += 1
        attrWindowLayout.addWidget(self.openDelAttrWindowBtn, row, 0)
        attrWindowLayout.addWidget(self.deleteAttrBtn, row, 1)
        # Keep grid columns 50/50 sized
        attrWindowLayout.setColumnStretch(0, 1)
        attrWindowLayout.setColumnStretch(1, 1)
        # Separator layout ----------
        separatorLayout = elements.hBoxLayout(spacing=uic.SREG, margins=(uic.SREG, uic.SREG, uic.SREG, 0))
        separatorLayout.addWidget(self.separatorTxt, 20)
        separatorLayout.addWidget(self.separatorBtn, 1)
        # Driver layout ----------
        driverAttrLayout = elements.hBoxLayout(spacing=uic.SREG, margins=(uic.SREG, 0, uic.SREG, 0))
        driverAttrLayout.addWidget(self.driverObjTxt, 10)
        driverAttrLayout.addWidget(self.driverAttrTxt, 10)
        driverAttrLayout.addWidget(self.addDriverTextBtn, 1)
        # Driver layout ----------
        drivenAttrLayout = elements.hBoxLayout(spacing=uic.SREG, margins=(uic.SREG, 0, uic.SREG, 0))
        drivenAttrLayout.addWidget(self.drivenObjTxt, 10)
        drivenAttrLayout.addWidget(self.drivenAttrTxt, 10)
        drivenAttrLayout.addWidget(self.addDrivenTextBtn, 1)
        # Proxy Button layout ----------
        proxyBtnLayout = elements.hBoxLayout(spacing=uic.SREG, margins=(uic.SREG, 0, uic.SREG, 0))
        proxyBtnLayout.addWidget(self.createProxyAttrBtn, 10)

        # Attribute Windows Collapsable ----------
        attrWindowsCollapsable = elements.CollapsableFrameThin("Attribute Windows")
        attrWindowsCollapsable.hiderLayout.addLayout(attrWindowLayout)
        attrWindowsCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        # Attribute Tools Collapsable ----------
        attrToolsCollapsable = elements.CollapsableFrameThin("Attribute Tools")
        attrToolsCollapsable.hiderLayout.addLayout(shuffleLayout)
        attrToolsCollapsable.hiderLayout.addLayout(separatorLayout)
        attrToolsCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        # Proxy Attribute Collapsable ----------
        proxyAttrCollapsable = elements.CollapsableFrameThin("Create Proxy Attribute", collapsed=True)
        proxyAttrCollapsable.addLayout(driverAttrLayout)
        proxyAttrCollapsable.addLayout(drivenAttrLayout)
        proxyAttrCollapsable.addLayout(proxyBtnLayout)
        proxyAttrCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)

        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(attrWindowsCollapsable)
        mainLayout.addWidget(attrToolsCollapsable)
        mainLayout.addWidget(proxyAttrCollapsable)


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
        mainLayout.addWidget(self.shuffleAttrUp)
