""" ---------- Zoo Selection Sets UI -------------
Zoo Selection Sets UI

"""

from zoovendor.Qt import QtWidgets, QtCore
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.apps.popupuis import selseticonpopup
from zoo.libs.maya.cmds.sets import selectionsets
from zoo.apps.toolsetsui.run import openToolset
from zoo.libs.pyqt import utils
from zoo.libs.iconlib import iconlib


UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
SSET_TRACKER_INST = selectionsets.ZooSelSetTrackerSingleton()  # tracks options for the session

SSET_COMBO_LIST_NONE = ["Selected Namespace", "Show All", "Custom Namespace", "----------------"]

SSET_COMBO_LIST = SSET_COMBO_LIST_NONE


class SelectionSets(toolsetwidget.ToolsetWidget):
    id = "selectionSets"
    info = "UI for managing Zoo Tools selection sets."
    uiData = {"label": "Zoo Selection Sets",
              "icon": "sets",
              "tooltip": "UI for managing Zoo Tools selection sets.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-zoo-selection-sets/"}
    defaultIcon = "sets"

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
        self._disableEnable()
        self._setComboFromTracker()
        self._updateNamespaceCombo()
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
        return super(SelectionSets, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(SelectionSets, self).widgets()

    # ------------------
    # UI
    # ------------------

    def _setComboFromTracker(self):
        option = SSET_TRACKER_INST.optionNamespace
        if option == "selected":
            self.properties.namespaceCombo.value = 0
        elif option == "all":
            self.properties.namespaceCombo.value = 1
        elif option == "custom":
            self.properties.namespaceCombo.value = 2
        elif ":" in option:
            self.properties.namespaceCombo.value = 2
            self.properties.namespaceText.value = SSET_TRACKER_INST.overrideNamespace

    def enterEvent(self, event):
        """When the cursor enters the UI update it"""
        self._setComboFromTracker()
        self._updateNamespaceCombo()
        self.updateFromProperties()

    def _disableEnable(self):
        """Enables and disables widgets depending on other widget states"""
        if self.properties.namespaceCombo.value > 1:
            self.compactWidget.namespaceText.setEnabled(True)
        else:
            self.compactWidget.namespaceText.setEnabled(False)

    def resetPriorityInt(self):
        """Updates the Set Priority text box to be 0"""
        self.properties.priorityText.value = 0
        self.updateFromProperties()

    # ------------------
    # UI - NAMESPACE
    # ------------------

    def _updateNamespaceCombo(self):
        """Update the namespace combo usually on mouse enter UI, updates all available namespaces"""
        curText = self.compactWidget.namespaceCombo.currentText()
        namespaces = selectionsets.sSetNamespacesInScene(selectionSets=True, objectSets=False, addColon=True)
        namespaces.sort(key=str.lower)
        comboList = SSET_COMBO_LIST_NONE + namespaces
        self.compactWidget.namespaceCombo.blockSignals(True)
        self.compactWidget.namespaceCombo.clear()
        self.compactWidget.namespaceCombo.addItems(comboList)
        if curText in comboList:
            index = [i for i, e in enumerate(comboList) if e == curText][0]  # returns the index of the current text.
        else:
            index = 0
        self.compactWidget.namespaceCombo.setIndex(index)
        self.compactWidget.namespaceCombo.blockSignals(False)

    def namespaceComboChanged(self):
        """The namespace combo is cahnged."""
        text = self.compactWidget.namespaceCombo.currentText()
        if self.properties.namespaceCombo.value == 0:
            SSET_TRACKER_INST.optionNamespace = "selected"
        elif self.properties.namespaceCombo.value == 1:
            SSET_TRACKER_INST.optionNamespace = "all"
        elif self.properties.namespaceCombo.value == 2:
            SSET_TRACKER_INST.optionNamespace = "custom"
        if self.properties.namespaceCombo.value > 3:
            self.properties.namespaceText.value = text[:-1]  # remove the ":"
            SSET_TRACKER_INST.optionNamespace = text
            SSET_TRACKER_INST.overrideNamespace = text[:-1]
        elif self.properties.namespaceCombo.value == 3:  # is the line
            self.properties.namespaceCombo.value = 2  # set as custom text
            SSET_TRACKER_INST.optionNamespace = "{}:".format(self.properties.namespaceText.value)
            SSET_TRACKER_INST.overrideNamespace = self.properties.namespaceText.value
        self._disableEnable()  # updates the textbox enable.

        if self.properties.namespaceCombo.value > 1:
            self.compactWidget.namespaceText.setFocus()
        else:
            self.properties.namespaceText.value = ""
        self.updateFromProperties()

    def namespaceTextChanged(self):
        """When the namespace text is changed"""
        SSET_TRACKER_INST.overrideNamespace = self.properties.namespaceText.value
        self.updateFromProperties()

    def insertNamespaceText(self):
        """Adds the namespace from selection in the scene"""
        self.properties.namespaceText.value = selectionsets.namespaceFromSelection()
        if self.properties.namespaceText.value:
            self.properties.namespaceCombo.value = 2  # set combo to "custom"
            self.compactWidget.namespaceText.setEnabled(True)
            SSET_TRACKER_INST.overrideNamespace = self.properties.namespaceText.value
            SSET_TRACKER_INST.optionNamespace = "custom"
        self.updateFromProperties()

    # ------------------
    # UI - ICON
    # ------------------

    def setIconByName(self, iconName):
        """Sets the icon from a string name"""
        icon = iconlib.Icon.icon(iconName, size=utils.dpiScale(32))
        self.compactWidget.openIconWindowBtn.setIcon(icon)

    def iconTextChanged(self):
        """When the icon textbox is changed"""
        icon = self.properties.iconNameText.value
        if not icon:
            self.setIconByName(self.defaultIcon)
            return
        self.setIconByName(icon)

    def global_receiveIcon(self, iconName):
        """Recieves an icon from other UIs"""
        self.properties.iconNameText.value = iconName
        self.setIconByName(iconName)
        self.updateFromProperties()

    def openIconPopup(self):
        """Opens the Selection Set Icon Popup Window"""
        selseticonpopup.iconWindow()

    def openIconToolset(self):
        """Opens the Selection Set Icon Popup Window"""
        openToolset("zooIcons", advancedMode=False)

    # ------------------
    # LOGIC
    # ------------------

    def addNodesSSet(self):
        """Adds the selected nodes to all selected sets"""
        selectionsets.addRemoveNodesSel(add=True, includeRegSets=True, message=True)

    def removeNodesSSet(self):
        """Adds the selected nodes to all selected sets"""
        selectionsets.addRemoveNodesSel(add=False, includeRegSets=True, message=True)

    def showSetMarkingMenu(self):
        """Show the selected selection sets in the Zoo Sel Sets Marking Menu"""
        selectionsets.setMarkingMenuVisSel(visibility=True, message=True)

    def hideSetMarkingMenu(self):
        """Hide the selected selection sets in the Zoo Sel Sets Marking Menu"""
        selectionsets.setMarkingMenuVisSel(visibility=False, message=True)

    def convertSelectionSet(self):
        """Converts selected object sets to selection sets"""
        selectionsets.setObjectSetAsSelectionSet_sel(selectionSet=True)

    def convertObjectSet(self):
        """Converts selected selection sets to object sets"""
        selectionsets.setObjectSetAsSelectionSet_sel(selectionSet=False)

    def setIconMarkingMenu(self):
        """Set the icon name for zoo marking menu on a selection set as a string attr. """
        selectionsets.setIconSel(self.properties.iconNameText.value)

    def setCyclePriority(self):
        """Sets the cycle priority on any selected selection set nodes."""
        selectionsets.setPriorityValueSel(priority=self.properties.priorityText.value, message=True)

    def selectAndCycleSets(self):
        """Selects the related or previous set, if pressed again will cycle through related sets"""
        SSET_TRACKER_INST.selectPrimarySet()

    def createSelectionSet(self):
        """Creates a selection set. """
        selseticonpopup.createSelectionSetWindow()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.createSelectionSetBtn.clicked.connect(self.createSelectionSet)
            widget.selectSelectionSetBtn.clicked.connect(self.selectAndCycleSets)
            widget.prioritySetBtn.clicked.connect(self.setCyclePriority)
            widget.refreshPriorityBtn.clicked.connect(self.resetPriorityInt)
            widget.showSetBtn.clicked.connect(self.showSetMarkingMenu)
            widget.hideSetBtn.clicked.connect(self.hideSetMarkingMenu)
            widget.convertSelSetBtn.clicked.connect(self.convertSelectionSet)
            widget.convertObjSetBtn.clicked.connect(self.convertObjectSet)
            widget.addSetBtn.clicked.connect(self.addNodesSSet)
            widget.removeSetBtn.clicked.connect(self.removeNodesSSet)
            widget.insertNamespaceBtn.clicked.connect(self.insertNamespaceText)
            widget.openIconWindowBtn.clicked.connect(self.openIconPopup)
            widget.setIconBtn.clicked.connect(self.setIconMarkingMenu)
            # combobox
            widget.namespaceCombo.itemChanged.connect(self.namespaceComboChanged)
            # Textbox
            widget.namespaceText.textModified.connect(self.namespaceTextChanged)
            widget.iconNameText.textModified.connect(self.iconTextChanged)
            # Right click on the icon button
            widget.setIconBtn.addAction("Open - Suggested Icons",
                                        mouseMenu=QtCore.Qt.RightButton,
                                        icon=iconlib.Icon.icon("windowBrowser"),
                                        connect=self.openIconPopup)
            widget.setIconBtn.addAction("Open - All Icons",
                                        mouseMenu=QtCore.Qt.RightButton,
                                        icon=iconlib.Icon.icon("windowBrowser"),
                                        connect=self.openIconToolset)


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
        # Add Btn ----------------------------------
        toolTip = "Add objects/nodes/components to a selection set. \n" \
                  "Select contents and a Selection Set in the Outliner to add. "
        self.addSetBtn = elements.AlignedButton("Add To Selection Set",
                                                icon="plusHollow",
                                                toolTip=toolTip)
        # Remove Btn ----------------------------------
        toolTip = "Removes objects/nodes/components to a selection set. \n" \
                  "Select contents and a Selection Set in the Outliner to remove. "
        self.removeSetBtn = elements.AlignedButton("Remove From Selection Set",
                                                   icon="minusHollow",
                                                   toolTip=toolTip)
        # Hide Btn ----------------------------------
        toolTip = "Hides a Selection Set from the Zoo Selection Set Marking Menu. \n" \
                  "Select a Selection Set from the Outliner and run to hide it in the menu. \n\n" \
                  "Zoo Selection Marking Menu: u (press hold) left-click"
        self.hideSetBtn = elements.AlignedButton("Hide Set In Marking Menu",
                                                 icon="invisible",
                                                 toolTip=toolTip)
        # Show Btn ----------------------------------
        toolTip = "Shows a Selection Set from the Zoo Selection Set Marking Menu. \n" \
                  "Select a Selection Set from the Outliner and run to show it in the menu. \n\n" \
                  "Zoo Selection Marking Menu: u (press hold) left-click"
        self.showSetBtn = elements.AlignedButton("Show Set In Marking Menu",
                                                 icon="eye",
                                                 toolTip=toolTip)
        # Convert Selection Set Btn ----------------------------------
        toolTip = "Convert an Object Set into a Selection Set. \n" \
                  "Select a Object Set from the Outliner to convert. "
        self.convertSelSetBtn = elements.AlignedButton("Convert To Selection Set",
                                                       icon="shaderSwap",
                                                       toolTip=toolTip)
        # Convert Object Set Btn ----------------------------------
        toolTip = "Convert a Selection Set into an Object Set. \n" \
                  "Select an Selection Set from the Outliner to convert. "
        self.convertObjSetBtn = elements.AlignedButton("Convert To Object Set",
                                                       icon="shaderSwap",
                                                       toolTip=toolTip)
        # Priority Text ----------------------------------
        toolTip = "Prioritise a set for cycling in the Zoo Marking Menu. \n" \
                  "A higher number makes the set more selectable while cycling. \n" \
                  "Select a Selection Set from the Outliner, set the priority number and assign. \n\n" \
                  "The selection should be assigned to single or multiple selection sets. \n" \
                  "Cycle Sets Zoo Hotkey: u (tap/release) & repeat"
        self.priorityText = elements.IntEdit(label="Set Priority",
                                             editText=3,
                                             toolTip=toolTip,
                                             editRatio=14,
                                             labelRatio=10)
        # Priority Btn ----------------------------------
        self.prioritySetBtn = elements.AlignedButton("Set Cycle Priority",
                                                     icon="renumber",
                                                     toolTip=toolTip)
        # Get Namespace ---------------------------------------
        tooltip = "Reset the cycle priority to zero."
        self.refreshPriorityBtn = elements.styledButton("",
                                                        "reload2",
                                                        toolTip=tooltip,
                                                        style=uic.BTN_TRANSPARENT_BG,
                                                        minWidth=20)
        # Namespace Text ----------------------------------
        toolTip = "Enter a namespace.  \n" \
                  "Matching sets will be shown in the marking menu. \n\n" \
                  "Zoo Selection Marking Menu: u (press hold) left-click"
        self.namespaceText = elements.StringEdit(label="Namespace",
                                                 toolTip=toolTip,
                                                 editRatio=14,
                                                 labelRatio=10)
        # Get Namespace ---------------------------------------
        tooltip = "Select a set or object and add it's namespace to the UI. "
        self.insertNamespaceBtn = elements.styledButton("",
                                                        "arrowLeft",
                                                        toolTip=tooltip,
                                                        style=uic.BTN_TRANSPARENT_BG,
                                                        minWidth=20)
        # Namespace Combo ----------------------------------
        toolTip = "Options for namespace filtering in the Zoo Selection Set Marking Menu. \n" \
                  " - Selected: Marking Menu shows only namespaces related to the current selection. \n" \
                  " - Show All: All selection sets will be shown in the Marking Menu. \n" \
                  " - Custom Namespace: Select or type a namespace into the UI. \n\n" \
                  "Zoo Selection Marking Menu: u (press hold) left-click"
        self.namespaceCombo = elements.ComboBoxRegular("",
                                                       items=SSET_COMBO_LIST,
                                                       toolTip=toolTip)
        # Icon Text ----------------------------------
        toolTip = "Type the name of a Zoo icon or enter an icon from the window. \n" \
                  "Note: To see all Zoo icons right-click on Set Icon In Marking Menu button.\n\n" \
                  "Icons will be seen in the Zoo Selection Set marking Menu. \n" \
                  "Zoo Selection Marking Menu: u (press hold) left-click"
        self.iconNameText = elements.StringEdit(label="Icon Name",
                                                toolTip=toolTip,
                                                editRatio=14,
                                                labelRatio=10)
        # Open Icon Window ---------------------------------------
        # Custom button that shows icons with their colors.
        tooltip = "Open the suggested Icons Window. \n" \
                  "Note: To see all Zoo icons right-click on Set Icon In Marking Menu button."
        self.openIconWindowBtn = QtWidgets.QToolButton(parent=self)
        iconSize = utils.dpiScale(16)
        icon = iconlib.Icon.icon("windowBrowser", size=utils.dpiScale(32))
        self.openIconWindowBtn.setIcon(icon)
        self.openIconWindowBtn.setToolTip(tooltip)
        self.openIconWindowBtn.setMinimumSize(QtCore.QSize(20, 20))
        self.openIconWindowBtn.setIconSize(QtCore.QSize(iconSize, iconSize))
        self.openIconWindowBtn.setToolTip(tooltip)
        # Set Icon Btn ----------------------------------
        toolTip = "Assigns the current icon to a Selection Set. \n" \
                  "Select a Selection Set in the Outliner window and run. \n\n" \
                  "Zoo Selection Marking Menu: u (press hold) left-click"
        self.setIconBtn = elements.AlignedButton("Set Icon In Marking Menu",
                                                 icon="checkMark",
                                                 toolTip=toolTip)
        # Create Selection Set ----------------------------------
        toolTip = "Create a new selection set. "
        self.createSelectionSetBtn = elements.styledButton("Create Selection Set",
                                                           icon="menu_sets",
                                                           toolTip=toolTip,
                                                           minWidth=uic.BTN_W_ICN_MED)
        # Select & Cycle Selection Set ----------------------------------
        toolTip = "Select and cycle through sets related to the current selection. \n\n" \
                  "The selection should be assigned to single or multiple selection sets. \n" \
                  "Cycle Sets Zoo Hotkey: u (tap/release) & repeat"
        self.selectSelectionSetBtn = elements.styledButton("Select Related/Cycle",
                                                           icon="cursorSelect",
                                                           toolTip=toolTip,
                                                           minWidth=uic.BTN_W_ICN_MED)


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
        # Priority Text Layout -----------------------------
        priorityTextLayout = elements.hBoxLayout()
        priorityTextLayout.addWidget(self.priorityText)
        priorityTextLayout.addWidget(self.refreshPriorityBtn)
        # NamespaceText Layout -----------------------------
        namespaceTextLayout = elements.hBoxLayout()
        namespaceTextLayout.addWidget(self.namespaceText)
        namespaceTextLayout.addWidget(self.insertNamespaceBtn)
        # NamespaceText Layout -----------------------------
        iconTextLayout = elements.hBoxLayout()
        iconTextLayout.addWidget(self.iconNameText)
        iconTextLayout.addWidget(self.openIconWindowBtn)

        # MM Grid Layout -----------------------------
        mmGridLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, 0, uic.SREG, 0))
        row = 0
        mmGridLayout.addLayout(iconTextLayout, row, 0)
        mmGridLayout.addWidget(self.setIconBtn, row, 1)
        row += 1
        mmGridLayout.addLayout(priorityTextLayout, row, 0)
        mmGridLayout.addWidget(self.prioritySetBtn, row, 1)
        row += 1
        mmGridLayout.addLayout(namespaceTextLayout, row, 0)
        mmGridLayout.addWidget(self.namespaceCombo, row, 1)
        row += 1
        mmGridLayout.addWidget(self.showSetBtn, row, 0)
        mmGridLayout.addWidget(self.hideSetBtn, row, 1)

        mmGridLayout.setColumnStretch(0, 1)
        mmGridLayout.setColumnStretch(1, 1)

        # Utils Grid Layout -----------------------------
        utilsGridLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, 0, uic.SREG, 0))
        utilsGridLayout.addWidget(self.addSetBtn, row, 0)
        utilsGridLayout.addWidget(self.removeSetBtn, row, 1)
        row += 1
        utilsGridLayout.addWidget(self.convertSelSetBtn, row, 0)
        utilsGridLayout.addWidget(self.convertObjSetBtn, row, 1)

        utilsGridLayout.setColumnStretch(0, 1)
        utilsGridLayout.setColumnStretch(1, 1)

        # Create Grid Layout -----------------------------
        createGridLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, 0, uic.SREG, 0))
        createGridLayout.addWidget(self.createSelectionSetBtn, row, 0)
        createGridLayout.addWidget(self.selectSelectionSetBtn, row, 1)

        createGridLayout.setColumnStretch(0, 1)
        createGridLayout.setColumnStretch(1, 1)

        # Add To Main Layout ---------------------------------------

        # Marking Menu Collapsable & Connections -------------------------------------
        markingMenuCollapsable = elements.CollapsableFrameThin("Marking Menu", collapsed=False)

        markingMenuCollapsable.hiderLayout.addLayout(mmGridLayout)
        markingMenuCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        mmCollapseLayout = elements.vBoxLayout(margins=(0, uic.SREG, 0, 0))  # adds top margin above title
        mmCollapseLayout.addWidget(markingMenuCollapsable)

        # Utils Menu Collapsable & Connections -------------------------------------
        utilsCollapsable = elements.CollapsableFrameThin("Utilities", collapsed=False)

        utilsCollapsable.hiderLayout.addLayout(utilsGridLayout)
        utilsCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        utilsCollapseLayout = elements.vBoxLayout(margins=(0, uic.SREG, 0, 0))  # adds top margin above title
        utilsCollapseLayout.addWidget(utilsCollapsable)

        # Create Menu Collapsable & Connections -------------------------------------
        createCollapsable = elements.CollapsableFrameThin("Create/Select", collapsed=False)

        createCollapsable.hiderLayout.addLayout(createGridLayout)
        createCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        createCollapseLayout = elements.vBoxLayout(margins=(0, uic.SREG, 0, 0))  # adds top margin above title
        createCollapseLayout.addWidget(createCollapsable)

        mainLayout.addLayout(mmCollapseLayout)
        mainLayout.addLayout(utilsCollapseLayout)
        mainLayout.addLayout(createCollapseLayout)


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
