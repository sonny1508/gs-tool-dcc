import os
import sys
import inspect

# Get the directory of the current script
current_file = inspect.getframeinfo(inspect.currentframe()).filename
current_dir = os.path.dirname(os.path.abspath(current_file))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Detect Python version
PY3 = sys.version_info[0] >= 3

IS_PYSIDE_6 = None

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance
    IS_PYSIDE_6 = True

except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance
    IS_PYSIDE_6 = False

from functools import partial
import json
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import Model_Checker.modelChecker_commands as mcc
import Model_Checker.modelChecker_list as mcl
from Model_Checker.__version__ import __version__

# Qt's "no maximum" sentinel, used to release the window size lock
QWIDGETSIZE_MAX = 16777215


def getMainWindow():
    mainWindowPtr = omui.MQtUtil.mainWindow()
    # Handle pointer conversion based on Python version
    if PY3:
        mainWindow = wrapInstance(int(mainWindowPtr), QtWidgets.QWidget)
    else:
        # In Python 2, we need to explicitly use long for the pointer
        mainWindow = wrapInstance(long(mainWindowPtr), QtWidgets.QWidget)
    return mainWindow


class UI(QtWidgets.QMainWindow):
    qmwInstance = None
    version = __version__
    commandsList = mcl.mcCommandsList
    categoryLayout = {}
    categoryWidget = {}
    categoryButton = {}
    categoryHeader = {}
    categoryCollapse = {}
    commandWidget = {}
    commandLayout = {}
    commandLabel = {}
    commandCheckBox = {}
    errorNodesButton = {}
    commandRunButton = {}
    revertButton = {}
    errorButtonLabel = "Select Error Nodes"
    logPanelWidth = 640
    windowChrome = 16

    # Categories whose commands change the scene rather than report on it
    actionCategories = ('Actions', 'Delete')
    checkCategoryColor = "#8fa8bd"
    actionCategoryColor = "#d9a55c"
    actionLabelStyles = {
        'changed': 'background-color: #446644;',
        'idle': 'background-color: #4a4a52;',
        'error': 'background-color: #664444;',
    }
    revertButtonStyle = (
        "QPushButton { background-color: #8a6534; color: #f2e4d0; }"
        "QPushButton:disabled { background-color: #3d3d3d; color: #6e6e6e; }")

    @classmethod
    def show_UI(cls):
        if not cls.qmwInstance:
            cls.qmwInstance = UI()
        if cls.qmwInstance.isHidden():
            cls.qmwInstance.show()
        else:
            cls.qmwInstance.raise_()
            cls.qmwInstance.activateWindow()

    def __init__(self, parent=getMainWindow()):
        super(UI, self).__init__(parent)

        self.setObjectName("ModelCheckerUI")
        self.setWindowTitle("Model Checker {}".format(self.version))
        self.diagnostics = {}
        
        # Start with Selection as the default context
        self.currentContextUUID = "Selection"
        
        # Initialize contexts
        self.contexts = {
            "Selection": {
                "name": "(Default) Selection",
                "diagnostics": {},
                "nodes": [],
            },
            "Global": {
                "name": "(Default) Global",
                "diagnostics": {},
                "nodes": [],
            },
        }
        self.contextRowItems = {}

        # The window is pinned to its content, so track what that content is
        self.logVisible = False
        self.sizeReleased = False

        # Revert points at one undo chunk, and only the most recent one
        self.revertChunk = None
        self.revertCommands = []
        self.actionCounter = 0
        self.chunkDepth = 0
        self.currentChunk = None

        mainWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(mainWidget)
        mainLayout = QtWidgets.QVBoxLayout(mainWidget)
        mainLayout.setContentsMargins(4, 4, 4, 4)
        report = self.buildContextUI()
        checks = self.buildChecksList()
        left = QtWidgets.QWidget()
        right = QtWidgets.QWidget()
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        left.setLayout(checks)
        right.setLayout(report)
        mainLayout.addWidget(splitter)

        # The log panel is opt-in - the checks list alone is what most artists need
        self.logPanel = right
        self.toggleLogButton.toggled.connect(self.toggleLog)
        self.logPanel.setVisible(False)
        self.pinSize()
        self.loadSettings()
        
        # Initialize the default context and create report
        self.createReport("Selection")
        self.consolidatedCheck.stateChanged.connect(self.changeConsolidated)

    def checkSelected(self):
        indexes = self.contextTable.selectionModel().selectedRows()
        for index in indexes:
            rowIdx = index.row()
            contextItem = self.contextTable.item(rowIdx, 1)
            if rowIdx > 1:
                contextItem.setCheckState(QtCore.Qt.Checked)
            else:
                cmds.warning("{} is managed by the modelChecker.".format(contextItem.text()))
    
    def uncheckSelected(self):
        indexes = self.contextTable.selectionModel().selectedRows()
        for index in indexes:
            rowIdx = index.row()
            if rowIdx > 1:
                contextItem = self.contextTable.item(rowIdx, 1)
                contextItem.setCheckState(QtCore.Qt.Unchecked)


    def addSelectedNodesAsNewContexts(self):
        selectedNodes = cmds.ls(selection=True)
        lastContext = None
        for node in selectedNodes:
            parent = self.checkForParent(node)
            if parent:
                msgBox = QtWidgets.QMessageBox()    
                msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                msgBox.setWindowTitle("Warning")
                msgBox.setText("The node you are trying to add ({}) is already part of a context ({}). Do you still wish to add this node as a context? (Not recommended)".format(node, parent))
                msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                returnValue = msgBox.exec_()
                if returnValue == QtWidgets.QMessageBox.Ok:
                    lastContext = self.addNodeAsContext(node)
            else:
                lastContext = self.addNodeAsContext(node)
        if lastContext:
            self.setRowFromUUID(lastContext)
            

    def addNodeAsContext(self, node):
        uuid = cmds.ls(node, uuid=True)[0]
        allDescendants = self.selectHierachy([uuid])
        uuidItem = QtWidgets.QTableWidgetItem(uuid)

        self.contexts[uuid] = {
            "name": node,
            "diagnostics": {},
            "nodes": allDescendants,
            "tableItem": uuidItem,
        }
        contextItem = QtWidgets.QTableWidgetItem(node)
        nodesItem = QtWidgets.QTableWidgetItem(str(len(allDescendants)))
        testsItem = QtWidgets.QTableWidgetItem("0")
        newRowIdx = self.contextTable.rowCount()
        self.contextTable.insertRow(newRowIdx)
        
        self.contextTable.setItem(newRowIdx, 0, uuidItem)
        self.contextTable.setItem(newRowIdx, 1, contextItem)
        self.contextTable.setItem(newRowIdx, 2, nodesItem)
        self.contextTable.setItem(newRowIdx, 3, testsItem)

        return uuid

    def checkForParent(self, node):
        currentNode = [node]
        while currentNode:
            if currentNode:
                uuid = cmds.ls(currentNode[0], uuid=True)[0]
                if uuid in self.contexts:
                    return currentNode[0]
            currentNode = cmds.listRelatives(currentNode, parent=True)


    def removeSelectedContexts(self):
        idxs = self.contextTable.selectionModel().selectedRows()
        for idx in sorted(idxs, reverse=True):
            uuid = self.contextTable.item(idx.row(), 0).text()            
            if uuid == "Global" or uuid == "Selection":
                continue
            
            node = self.contextTable.item(idx.row(), 1).text()
            try:
                self.contextTable.removeRow(idx.row())
                self.contexts.pop(uuid)
            except:
                cmds.warning("Failed to remove context: {}".format(node))

        if self.currentContextUUID not in self.contexts:        
            lastContext = list(self.contexts.keys())[-1]
            self.setRowFromUUID(lastContext)

    def setCurrentContext(self, row):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.NoModifier:
            uuid = self.contextTable.item(row, 0).text()
            self.currentContextUUID = uuid
            
            # Refresh selection context if that's what was selected
            if uuid == "Selection":
                selectedNodes = cmds.ls(selection=True, uuid=True, typ="transform")
                self.contexts["Selection"]["nodes"] = self.selectHierachy(selectedNodes) if selectedNodes else []
            # Refresh Global context
            elif uuid == "Global":
                self.contexts["Global"]["nodes"] = self.filterGetAllNodes()
            # Handle custom contexts - make sure the root node still exists
            elif uuid != "Global" and uuid != "Selection":
                nodeName = cmds.ls(uuid, uuid=True)
                if nodeName:
                    self.contextTable.item(row, 1).setText(nodeName[0])
                else:
                    self.contextTable.item(row, 1).setText("Root node seems to be missing!")
                    
            # Update the report with the current context
            self.createReport(uuid)
    
    def setRowFromUUID(self, uuid):
        tableItem = self.contexts[uuid]['tableItem']
        row = self.contextTable.row(tableItem)
        self.contextTable.setCurrentItem(self.contextTable.item(row, 0))
        self.setCurrentContext(row)

    def itemSelectionChanged(self):
        if not self.contextTable.selectionModel().selectedRows():
            if self.currentContextUUID in self.contexts:
                self.setRowFromUUID(self.currentContextUUID)

    def buildContextUI(self):
        report = QtWidgets.QVBoxLayout()
        contextWidget = QtWidgets.QWidget()
        contextWidgetLayout = QtWidgets.QVBoxLayout()
        contextWidget.setLayout(contextWidgetLayout)
        self.contextTable = QtWidgets.QTableWidget()
        contextWidgetLayout.addWidget(self.contextTable)
        contextButtonLayout = QtWidgets.QHBoxLayout()

        addContextsBtn = QtWidgets.QPushButton("Add Contexts")
        removeContextsBtn = QtWidgets.QPushButton("Remove Contexts")
        checkSelectedContextsBtn = QtWidgets.QPushButton("Run Checks on Selected Contexts")
        checkAllContextsBtn = QtWidgets.QPushButton("Run Checks on All Added Contexts")
        addContextsBtn.clicked.connect(self.addSelectedNodesAsNewContexts)
        removeContextsBtn.clicked.connect(self.removeSelectedContexts)
        checkSelectedContextsBtn.clicked.connect(self.sanityCheckSelected)
        checkAllContextsBtn.clicked.connect(self.sanityCheckAll)
        contextWidgetLayout.addLayout(contextButtonLayout)
        contextButtonLayout.addWidget(addContextsBtn)
        contextButtonLayout.addWidget(removeContextsBtn)
        contextButtonLayout.addWidget(checkSelectedContextsBtn)
        contextButtonLayout.addWidget(checkAllContextsBtn)

        self.contextTable.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.contextTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        defaultContexts = ["Selection", "Global"]
        contextHeaders = ['UUID', 'CONTEXT', 'NODES', 'TESTS']
        self.contextTable.setColumnCount(len(contextHeaders))
        self.contextTable.setHorizontalHeaderLabels(contextHeaders)
        self.contextTable.verticalHeader().setVisible(False)
        self.contextTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.contextTable.cellClicked.connect(self.setCurrentContext)
        self.contextTable.itemSelectionChanged.connect(self.itemSelectionChanged)

        for idx, context in enumerate(defaultContexts):
            uuidItem = QtWidgets.QTableWidgetItem(context)
            contextItem = QtWidgets.QTableWidgetItem("(Default) {}".format(context))
            self.contexts[context]['tableItem'] = uuidItem 
            nodesItem = QtWidgets.QTableWidgetItem("0")
            testsItem = QtWidgets.QTableWidgetItem("0")
            uuidItem.setFlags(uuidItem.flags() & ~QtCore.Qt.ItemIsEditable)
            contextItem.setFlags(contextItem.flags() & ~QtCore.Qt.ItemIsEditable)
            nodesItem.setFlags(nodesItem.flags() & ~QtCore.Qt.ItemIsEditable)
            testsItem.setFlags(testsItem.flags() & ~QtCore.Qt.ItemIsEditable)

            # Initialize node counts 
            if context == "Selection":
                selectedNodes = cmds.ls(selection=True, uuid=True, typ="transform")
                self.contexts[context]['nodes'] = self.selectHierachy(selectedNodes) if selectedNodes else []
                self.contexts[context]['nodesCount'] = len(self.contexts[context]['nodes'])
            else:
                allNodes = self.filterGetAllNodes()
                self.contexts[context]['nodes'] = allNodes
                self.contexts[context]['nodesCount'] = len(allNodes)

            self.contextTable.insertRow(idx)
            self.contextTable.setItem(idx, 0, uuidItem)
            self.contextTable.setItem(idx, 1, contextItem)
            self.contextTable.setItem(idx, 2, nodesItem)
            self.contextTable.setItem(idx, 3, testsItem)

            # Update the node count display
            self.contextTable.item(idx, 2).setText(str(self.contexts[context]['nodesCount']))

        self.contextTable.setColumnHidden(0, True)
        self.contextTable.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.reportOutputUI = QtWidgets.QTextEdit()
        self.reportOutputUI.setReadOnly(True)
        self.reportOutputUI.setMinimumWidth(600)

        self.runCurrentButton = QtWidgets.QPushButton("Run Current")
        self.runAllCheckedButton = QtWidgets.QPushButton("Run Checks on Selected / All")
        self.consolidatedCheck = QtWidgets.QCheckBox()

        clearButton = QtWidgets.QPushButton("Clear")
        clearButton.setMaximumWidth(150)
        
        settingsLayout = QtWidgets.QHBoxLayout()
        settingsLayout.addWidget(QtWidgets.QLabel("Consolidated display: "))
        settingsLayout.addStretch()
        settingsLayout.addWidget(self.consolidatedCheck)
        
        runLayout = QtWidgets.QHBoxLayout()
        runLayout.addWidget(QtWidgets.QLabel("Report: "))
        runLayout.addWidget(clearButton)
        runLayout.addWidget(self.runAllCheckedButton)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.addWidget(contextWidget)
        splitter.addWidget(self.reportOutputUI)
        splitter.setSizes([0, 1])
        report.addLayout(settingsLayout)
        report.addWidget(splitter)
        report.addLayout(runLayout)
        self.runAllCheckedButton.clicked.connect(self.sanityCheckChecked)
        clearButton.clicked.connect(self.clearCurrentReport)


        # Set the Selection context as the current context by default
        self.contextTable.setCurrentItem(self.contextTable.item(0, 1))
        self.currentContextUUID = "Selection"

        return report

    def buildChecksList(self):
        # Create a scroll area to contain all checks
        self.measureChecksPanel()

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setMinimumWidth(self.checksPanelWidth)
        
        # The window height is fixed, so leave the buttons below their room
        scrollArea.setMinimumHeight(max(300, self.fixedHeight - 80))
        
        # Create a container widget for the scroll area
        scrollContent = QtWidgets.QWidget()
        scrollArea.setWidget(scrollContent)
        
        # Create the main layout for all checks
        checks = QtWidgets.QVBoxLayout(scrollContent)
        checks.setContentsMargins(5, 5, 5, 5)
        
        # Get categories with special ones at the end
        category = self.getCategories(self.commandsList)
        
        for obj in category:
            self.categoryWidget[obj] = QtWidgets.QWidget()
            self.categoryLayout[obj] = QtWidgets.QVBoxLayout()
            self.categoryHeader[obj] = QtWidgets.QHBoxLayout()
            self.categoryButton[obj] = QtWidgets.QPushButton(obj)
            self.categoryCollapse[obj] = QtWidgets.QPushButton(u'\u2193')

            # Use method to create stable callback for toggleUI
            def make_toggle_callback(cat_name):
                return lambda: self.toggleUI(cat_name)
            
            # Use method to create stable callback for checkCategory
            def make_category_callback(cat_name):
                return lambda: self.checkCategory(cat_name)
            
            self.categoryCollapse[obj].clicked.connect(make_toggle_callback(obj))
            self.categoryCollapse[obj].setMaximumWidth(30)
            
            # Actions and checks are told apart at a glance by header colour
            headerColor = (self.actionCategoryColor
                           if obj in self.actionCategories
                           else self.checkCategoryColor)
            self.categoryButton[obj].setStyleSheet(
                "background-color: " + headerColor + ";"
                "text-transform: uppercase;"
                "color: #000000;"
                "font-size: 18px;")
                    
            self.categoryButton[obj].clicked.connect(make_category_callback(obj))
            
            self.categoryHeader[obj].addWidget(self.categoryButton[obj])
            self.categoryHeader[obj].addWidget(self.categoryCollapse[obj])
            self.categoryWidget[obj].setLayout(self.categoryLayout[obj])
            checks.addLayout(self.categoryHeader[obj])
            checks.addWidget(self.categoryWidget[obj])

        # Add commands to categories
        # Instance dicts: a reloaded module must not keep stale widgets around,
        # since an absent key is what marks a row as an action row
        self.errorNodesButton = {}
        self.revertButton = {}

        for name in sorted(self.commandsList.keys()):
            label = self.commandsList[name]['label']
            category = self.commandsList[name]['category']
            isAction = self.commandsList[name].get('isAction', False)

            self.commandWidget[name] = QtWidgets.QWidget()
            self.commandWidget[name].setMaximumHeight(40)
            self.commandLayout[name] = QtWidgets.QHBoxLayout()

            self.categoryLayout[category].addWidget(self.commandWidget[name])
            self.commandWidget[name].setLayout(self.commandLayout[name])

            self.commandLayout[name].setSpacing(4)
            self.commandLayout[name].setContentsMargins(0, 0, 0, 0)
            self.commandWidget[name].setStyleSheet(
                "padding: 0px; margin: 0px;")
            self.commandLabel[name] = QtWidgets.QLabel(label)
            self.commandLabel[name].setFixedWidth(self.labelWidth)
            self.commandCheckBox[name] = QtWidgets.QCheckBox()

            self.commandCheckBox[name].setChecked(False)
            self.commandCheckBox[name].setMaximumWidth(20)

            self.commandRunButton[name] = QtWidgets.QPushButton("Run")
            self.commandRunButton[name].setMaximumWidth(40)

            # Create a custom handler for this specific command
            def make_cmd_handler(cmd_name):
                return lambda: self.oneOfs(cmd_name)
            
            def make_revert_handler(cmd_name):
                return lambda: self.revertAction(cmd_name)

            # Connect using our custom handler
            self.commandRunButton[name].clicked.connect(make_cmd_handler(name))

            self.commandLayout[name].addWidget(self.commandLabel[name])
            self.commandLayout[name].addWidget(self.commandCheckBox[name])
            self.commandLayout[name].addWidget(self.commandRunButton[name])

            if isAction:
                # Nothing useful to select on an action, so Revert takes the slot
                self.revertButton[name] = QtWidgets.QPushButton("Revert")
                self.revertButton[name].setEnabled(False)
                self.revertButton[name].setFixedWidth(self.errorButtonWidth)
                self.revertButton[name].setStyleSheet(self.revertButtonStyle)
                self.revertButton[name].clicked.connect(make_revert_handler(name))
                self.commandLayout[name].addWidget(self.revertButton[name])

                self.commandRunButton[name].setToolTip(
                    "Changes the whole scene, ignoring your selection"
                    if self.commandsList[name].get('isGlobal', False)
                    else "Changes the objects in the current context")
            else:
                self.errorNodesButton[name] = QtWidgets.QPushButton(
                    self.errorButtonLabel)
                self.errorNodesButton[name].setEnabled(False)
                self.errorNodesButton[name].setFixedWidth(self.errorButtonWidth)
                self.commandLayout[name].addWidget(self.errorNodesButton[name])

            self.commandLayout[name].addStretch()
        
        # Create a wrapper layout that will hold the scroll area
        wrapperLayout = QtWidgets.QVBoxLayout()
        wrapperLayout.setContentsMargins(0, 0, 0, 0)
        wrapperLayout.addWidget(scrollArea)
        
        # Add the check/uncheck all buttons at the bottom of the wrapper layout
        checks.addStretch()
        checkButtonsLayout = QtWidgets.QHBoxLayout()

        checks.addLayout(checkButtonsLayout)

        uncheckAllButton = QtWidgets.QPushButton("Uncheck All")
        uncheckAllButton.clicked.connect(self.uncheckAll)

        invertCheckButton = QtWidgets.QPushButton("Invert")
        invertCheckButton.clicked.connect(self.invertCheck)
        failedCheckButton = QtWidgets.QPushButton("Check Failed Only")
        failedCheckButton.clicked.connect(self.selectFailed)

        checkAllButton = QtWidgets.QPushButton("Check All")
        checkAllButton.clicked.connect(self.checkAll)
        checkButtonsLayout.addWidget(uncheckAllButton)
        checkButtonsLayout.addWidget(invertCheckButton)
        checkButtonsLayout.addWidget(failedCheckButton)

        checkButtonsLayout.addWidget(checkAllButton)

        self.toggleLogButton = QtWidgets.QPushButton("Show Log")
        self.toggleLogButton.setCheckable(True)
        self.toggleLogButton.setChecked(False)
        wrapperLayout.addWidget(self.toggleLogButton)

        return wrapperLayout
    
    def textWidth(self, metrics, text):
        """QFontMetrics.width() was replaced by horizontalAdvance() in newer Qt."""
        if hasattr(metrics, "horizontalAdvance"):
            return metrics.horizontalAdvance(text)
        return metrics.width(text)

    def measureChecksPanel(self):
        """Size the checks panel to the text it holds so it wastes no width."""
        metrics = self.fontMetrics()
        self.labelWidth = max(
            self.textWidth(metrics, self.commandsList[name]['label'])
            for name in self.commandsList) + 8
        self.errorButtonWidth = self.textWidth(metrics, self.errorButtonLabel) + 24

        # Tall enough to show most checks, but never taller than the screen
        screen = QtWidgets.QApplication.primaryScreen()
        available = screen.availableGeometry().height() if screen else 900
        self.fixedHeight = max(600, min(900, available - 80))

        # label + checkbox + run button + select button + spacing, margins, scrollbar
        self.checksPanelWidth = (
            self.labelWidth + 20 + 40 + self.errorButtonWidth + 12 + 20 + 24)

    def toggleLog(self, visible):
        """Show or hide the report panel on the right."""
        self.logVisible = visible
        self.logPanel.setVisible(visible)
        self.toggleLogButton.setText("Hide Log" if visible else "Show Log")
        if not self.sizeReleased:
            self.pinSize()

    def contentSize(self):
        """The size the window wants, which only the log panel changes."""
        width = self.checksPanelWidth + self.windowChrome
        if self.logVisible:
            width += self.logPanelWidth
        return QtCore.QSize(width, self.fixedHeight)

    def pinSize(self):
        """Hold the window at its content size - no dragging it out of shape.

        Explicit min/max also beat the layout's minimum, which is what kept the
        window at full width after the log panel was hidden again.
        """
        self.sizeReleased = False
        self.setFixedSize(self.contentSize())

    def releaseSize(self):
        """Drop the lock so maximize / fullscreen can use the whole screen."""
        self.sizeReleased = True
        self.setMinimumSize(0, 0)
        self.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)

    def changeEvent(self, event):
        super(UI, self).changeEvent(event)
        if event.type() != QtCore.QEvent.WindowStateChange or self.isMinimized():
            return
        expanded = self.isMaximized() or self.isFullScreen()
        if expanded and not self.sizeReleased:
            self.releaseSize()
            # The lock clamped the state change, so ask for it again now
            reapply = self.showFullScreen if self.isFullScreen() else self.showMaximized
            QtCore.QTimer.singleShot(0, reapply)
        elif not expanded and self.sizeReleased:
            self.pinSize()

    def closeEvent(self, event):
        self.saveSettings()
        super(UI, self).closeEvent(event)

    def getCategories(self, commands):
        # Extract all categories
        allCategories = set()
        for command in commands.values():
            allCategories.add(command['category'])
        
        # Convert to list and sort alphabetically, but with special handling
        categories = []
        special_categories = []
        
        for cat in allCategories:
            if cat in self.actionCategories:
                special_categories.append(cat)
            else:
                categories.append(cat)
        
        # Sort each list
        categories.sort(key=str.lower)
        special_categories.sort(key=str.lower)
        
        # Append special categories at the end
        categories.extend(special_categories)
        
        return categories

    def checkState(self, name):
        return self.commandCheckBox[name].checkState()

    def checkAll(self):
        for command in self.commandsList:
            self.commandCheckBox[command].setChecked(True)

    def toggleUI(self, category):
        state = self.categoryWidget[category].isVisible()
        buttonLabel = u'\u21B5' if state else u'\u2193'
        self.categoryCollapse[category].setText(buttonLabel)
        self.categoryWidget[category].setVisible(not state)

    def uncheckAll(self):
        for name in self.commandsList:
            self.commandCheckBox[name].setChecked(False)

    def invertCheck(self):
        for name in self.commandsList.keys():
            self.commandCheckBox[name].setChecked(
                not self.commandCheckBox[name].isChecked())
    
    def clearCurrentReport(self):
        self.clearReportOnContext(self.currentContextUUID)

    def clearReportOnContext(self, contextUUID):
        context = self.contexts[contextUUID]
        context["diagnostics"] = {}
        context["diagnostics"]["nodes"] = 0
        context["diagnostics"]["tests"] = 0
        self.clearRowFromItem(context['tableItem'])
        for command in self.commandsList.keys():
            if command in self.errorNodesButton:
                self.errorNodesButton[command].setEnabled(False)
            self.commandLabel[command].setStyleSheet('background-color: none;')
        self.reportOutputUI.clear()


    def checkCategory(self, category):
        uncheckedCategoryButtons = []
        categoryButtons = []
        for name in self.commandsList.keys():
            if self.commandsList[name]['category'] == category:
                categoryButtons.append(name)
                if self.commandCheckBox[name].isChecked():
                    uncheckedCategoryButtons.append(name)

        for category in categoryButtons:
            checked = len(uncheckedCategoryButtons) != len(categoryButtons)
            self.commandCheckBox[category].setChecked(checked)

    def filterGetAllNodes(self):
        allNodes = cmds.ls(transforms=True, long=True)
        allUsuableNodes = []
        for node in allNodes:
            if node not in {'|front', '|persp', '|top', '|side'}:
                uuid = cmds.ls(node, uuid=True)[0]
                allUsuableNodes.append(uuid)
        return allUsuableNodes
    
    def oneOfs(self, command):
        """Execute a single command when the Run button is clicked."""
        # Check if the command exists
        if command not in self.commandsList:
            cmds.warning("Unknown command: {}".format(command))
            return
        
        # Check if this is an action command
        isAction = self.commandsList[command].get('isAction', False)
        
        # Check if this is a global command (operates on entire scene)
        isGlobal = self.commandsList[command].get('isGlobal', False)
        
        # Determine which nodes to use based on context and isGlobal flag
        if isGlobal:
            # For global commands, always use all scene nodes
            nodes = self.filterGetAllNodes()
            contextDesc = "ALL OBJECTS in the scene (global command)"
        else:
            # For normal commands, use the current context
            if self.currentContextUUID == "Selection":
                # Get fresh selection
                selectedNodes = cmds.ls(selection=True, uuid=True, typ="transform")
                if not selectedNodes:
                    cmds.warning("No objects selected")
                    return
                # Update nodes for selection context
                nodes = self.selectHierachy(selectedNodes)
                self.contexts["Selection"]["nodes"] = nodes
                contextDesc = "the SELECTED objects"
            elif self.currentContextUUID == "Global":
                # Use all scene nodes
                nodes = self.filterGetAllNodes()
                self.contexts["Global"]["nodes"] = nodes
                contextDesc = "ALL OBJECTS in the scene"
            else:
                # Custom context - use nodes from that context
                nodes = self.contexts[self.currentContextUUID]['nodes']
                # Verify nodes still exist
                nodes = [node for node in nodes if cmds.ls(node, uuid=True)]
                if not nodes:
                    cmds.warning("No valid nodes found in context: {}".format(
                        self.contexts[self.currentContextUUID]["name"]))
                    return
                contextDesc = "objects in context: {}".format(self.contexts[self.currentContextUUID]['name'])
        
        # Show confirmation for action commands
        # if isAction:
        #     msgBox = QtWidgets.QMessageBox()
        #     msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        #     msgBox.setWindowTitle("Warning: Action will modify your scene")
        #     msgBox.setText("The action '{}' will modify {} ({} objects). Continue?".format(
        #         self.commandsList[command]['label'], 
        #         contextDesc,
        #         len(nodes)))
        #     msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        #     returnValue = msgBox.exec_()
        #     if returnValue != QtWidgets.QMessageBox.Ok:
        #         return
        
        # Get diagnostics for the current context
        diagnostics = self.contexts[self.currentContextUUID]['diagnostics']
        
        try:
            # Run the command with the appropriate nodes
            newDiagnostics = self.commandToRun([command], nodes)
            if command in newDiagnostics:
                diagnostics[command] = newDiagnostics[command]
                # Update the report
                self.createReport(self.currentContextUUID)
            else:
                cmds.warning("Command failed to return diagnostic information: {}".format(command))
        except Exception as e:
            cmds.warning("Error running command '{}': {}".format(command, str(e)))

    def commandToRun(self, commands, nodes):
        """Run the commands, bracketing scene changes in a single undo chunk.

        One chunk per run is what makes Revert possible: deletes cannot be
        rebuilt by hand, so we lean on Maya's undo stack instead.
        """
        actions = [cmd for cmd in commands
                   if self.commandsList.get(cmd, {}).get('isAction', False)]
        if not actions:
            return self.runCommands(commands, nodes)

        chunkName = self.beginActionChunk()
        try:
            diagnostics = self.runCommands(commands, nodes)
        finally:
            self.endActionChunk()

        # An action that found nothing to do leaves the undo stack untouched, so
        # it neither gains a revert point nor destroys the one already there
        changed = [cmd for cmd in actions
                   if self.actionOutcome(diagnostics.get(cmd, {})) == 'changed']
        if changed:
            self.addRevertPoint(chunkName, changed)
        return diagnostics

    def beginActionChunk(self):
        """Open a named undo chunk, or join the one already open."""
        self.chunkDepth += 1
        if self.chunkDepth == 1:
            self.actionCounter += 1
            self.currentChunk = "modelChecker_{}".format(self.actionCounter)
            cmds.undoInfo(openChunk=True, chunkName=self.currentChunk)
        return self.currentChunk

    def endActionChunk(self):
        """Close the chunk once the outermost caller is done with it."""
        self.chunkDepth = max(0, self.chunkDepth - 1)
        if self.chunkDepth == 0:
            cmds.undoInfo(closeChunk=True)

    def runCommands(self, commands, nodes):
        """Execute the given commands on the specified nodes."""
        diagnostics = {}
        SLMesh = om.MSelectionList()
        
        # Filter nodes to ensure they exist
        nodes = [node for node in nodes if cmds.ls(node, uuid=True)] 
        if not nodes:
            cmds.warning("No valid nodes to process")
            return {}
            
        longNodeNames = []
        for node in nodes:
            nodeName = cmds.ls(node, uuid=True)
            if nodeName:
                longNodeNames.append(nodeName[0])
        
        # Populate selection list with mesh objects
        for nodeName in longNodeNames:
            try:
                shapes = cmds.listRelatives(nodeName, shapes=True, typ="mesh")
                if shapes:
                    SLMesh.add(nodeName)  # Add node name, not UUID
            except Exception as e:
                cmds.warning("Error adding node to selection: {}".format(str(e)))
        
        # Execute each command
        for command in commands:
            try:
                # Get the actual function
                func = getattr(mcc, command, None)
                if func is None:
                    cmds.warning("Command function not found: {}".format(command))
                    continue
                    
                # Call the command function
                resultType, errors = func(nodes, SLMesh)
                if resultType == "custom":
                    # Names of things that no longer exist, so they cannot be
                    # looked up as scene nodes - pass them straight through
                    diagnostics[command] = {
                        "type": resultType, "uuids": [], "data": errors}
                else:
                    diagnostics[command] = {"type": resultType, "uuids": errors}

            except Exception as e:
                import traceback
                cmds.warning("Error running command '{}': {}".format(command, str(e)))
                traceback.print_exc()
                diagnostics[command] = {
                    "type": "nodes", "uuids": [], "error": str(e)}
        
        SLMesh.clear()
        return diagnostics

    # def runAction(self, actionName):
    #     """Run an action on selected objects or context nodes"""
    #     # Store original selection
    #     orig_selection = cmds.ls(selection=True)
        
    #     # Get nodes from context if needed
    #     contextUUID = self.currentContextUUID
    #     useContextNodes = (contextUUID != "Selection" and self.contexts[contextUUID]['nodes'])
        
    #     # Run the action
    #     try:
    #         if useContextNodes:
    #             nodes = self.contexts[contextUUID]['nodes']
    #             print(f"Running {actionName} on {len(nodes)} nodes from context '{self.contexts[contextUUID]['name']}'")
    #             getattr(mcc, actionName)(nodes)
    #         else:
    #             print(f"Running {actionName} on current selection")
    #             getattr(mcc, actionName)()
    #     except Exception as e:
    #         cmds.warning(f"Error running action '{actionName}': {str(e)}")
        
    #     # Restore selection
    #     cmds.select(orig_selection, replace=True)

    def parseErrors(self, errors):
        uuids = errors.get('uuids', [])
        type = errors.get('type', '')

        # Handle custom return type for actions
        if type == 'custom' and 'data' in errors:
            return errors['data']  # Just return the custom data directly

        if type == 'nodes':
            nodes = []
            for node in uuids:
                curNode = cmds.ls(node)
                if curNode:
                    nodes.append(curNode[0])
            return nodes
        
        outputErrors = []
        typeMapping = {
            "uv": ".map[{}]",
            "vertex": ".vtx[{}]",
            "edge": ".e[{}]",
            "polygon": ".f[{}]",
        }
        
        for uuid in uuids:
            nodeName = cmds.ls(uuid)
            if nodeName:
                for component in uuids[uuid]:
                    outputErrors.append(nodeName[0] + typeMapping[type].format(component))
        return outputErrors

    def createReport(self, uuid):
        context = self.contexts[uuid]
        diagnostics = context['diagnostics']
        nodes = context['nodes']
        name = context['name']
        self.reportOutputUI.clear()
        lastFailed = None
        consolidated = self.consolidatedCheck.isChecked()
        html = "<h2>{}</h2>".format(name)

        # Disconnect all previous button signals
        for cmd in self.errorNodesButton:
            try:
                self.errorNodesButton[cmd].clicked.disconnect()
            except:
                pass

        if consolidated or not nodes:
            plural = '' if len(nodes) == 1 else 's'
            html += "&#10752; Node{} checked: {}<br><br>".format(plural, len(nodes))
        else:
            html += "&#10752; Nodes checked:<br>"
            for node in nodes:
                nodeName = cmds.ls(node)
                if nodeName:
                    html += "&#9492;&#9472; {}<br>".format(nodeName[0])
            html += "<br><br>"
            
        if len(diagnostics) == 0:
            html += "{} - No tests run in this context.".format(self.contexts[self.currentContextUUID]['name'])
            self.reportOutputUI.setHtml(html)
            return

        for error in sorted(self.commandsList.keys()):
            if error not in diagnostics:
                if error in self.errorNodesButton:
                    self.errorNodesButton[error].setEnabled(False)
                self.commandLabel[error].setStyleSheet('background-color: none;')
                continue
            
            # Check if this is an action command
            isAction = self.commandsList[error].get('isAction', False)
            entry = diagnostics[error]
            parsedErrors = self.parseErrors(entry)
            outcome = self.actionOutcome(entry) if isAction else None

            # For checks, "failed" means there are errors
            # For actions, only a real error is a failure - finding nothing to
            # do is a perfectly good outcome
            if isAction:
                failed = outcome != 'changed'
            else:
                # For checks, having nodes means failure
                failed = len(parsedErrors) != 0
            
            # Update UI based on success/failure
            if isAction:
                # Action rows carry a Revert button instead, and its state comes
                # from the undo stack rather than from these diagnostics
                self.commandLabel[error].setStyleSheet(
                    self.actionLabelStyles[outcome])
            else:
                if failed:  # Check failed (errors found)
                    self.errorNodesButton[error].setEnabled(True)
                    error_data = diagnostics[error]  # Create local var to avoid reference issues
                    self.errorNodesButton[error].clicked.connect(
                        lambda checked=False, err=error_data: self.selectErrorNodes(err))
                    self.commandLabel[error].setStyleSheet('background-color: #664444;')
                else:  # Check succeeded (no errors)
                    self.errorNodesButton[error].setEnabled(False)
                    self.commandLabel[error].setStyleSheet('background-color: #446644;')
            
            label = self.commandsList[error]['label']
            
            if lastFailed != failed and lastFailed is not None or (failed is True and lastFailed is True):
                html += "<br>"
            lastFailed = failed
            
            if isAction:
                if outcome == 'changed':
                    html += "&#10752; {}<font color=#64a65a> [ CHANGED ]</font><br>".format(label)
                elif outcome == 'error':
                    html += "&#10752; {}<font color=#9c4f4f> [ ERROR ]</font><br>".format(label)
                    html += "&#9492;&#9472; {}<br>".format(entry.get('error', ''))
                else:
                    html += "{}<font color=#9a9a9a> [ NOTHING TO DO ]</font><br>".format(label)
            else:
                if failed:  # Check failed
                    html += "&#10752; {}<font color=#9c4f4f> [ FAILED ]</font><br>".format(label)
                else:  # Check succeeded
                    html += "{}<font color=#64a65a> [ SUCCESS ]</font><br>".format(label)
            
            # Show nodes for successful actions or failed checks
            if (isAction and not failed) or (not isAction and failed):
                if (consolidated and len(parsedErrors) > 0
                        and entry.get('type') != 'custom'):
                    store = {}
                    for node in parsedErrors:
                        name = node.split(".")[0] if "." in node else node
                        store[name] = store.get(name, 0) + 1

                    for node in store:
                        if isAction:
                            word = "nodes modified" if store[node] > 1 else "node modified"
                            html += "&#9492;&#9472; {} - <font color=#64a65a>{} {}</font><br>".format(node, store[node], word)
                        else:
                            word = "issues" if store[node] > 1 else "issue"
                            html += "&#9492;&#9472; {} - <font color=#9c4f4f>{} {}</font><br>".format(node, store[node], word)
                else:
                    for node in parsedErrors:
                        html += "&#9492;&#9472; {}<br>".format(node)
                        
        self.reportOutputUI.insertHtml(html)

    def changeConsolidated(self):
        self.createReport(self.currentContextUUID)

    def selectHierachy(self, nodes):
        hierachy = set()
        for node in nodes:
            nodeName = cmds.ls(node, uuid=True, long=True)[0]
            children = cmds.listRelatives(nodeName, typ="transform", allDescendents=True, fullPath=True)
            if children:
                uuids = [cmds.ls(child, uuid=True)[0] for child in children]
                hierachy.update(uuids)                
            hierachy.add(node)
        return list(hierachy)

    def sanityCheckChecked(self):
        if cmds.ls(selection=True, typ="transform", long=True):
            self.sanityCheck(["Selection"], True)
        else:
            self.sanityCheck(["Global"])

    def sanityCheckAll(self):
        contextsUuids = []
        rowCount = self.contextTable.rowCount()
        for rowIdx in range(rowCount):
            uuidItem = self.contextTable.item(rowIdx, 0)
            uuid = uuidItem.text()
            if uuid == 'Global' or uuid == 'Selection':
                continue
            contextsUuids.append(uuid)
        self.sanityCheck(contextsUuids, False)


    def sanityCheckSelected(self):
        contextsUuids = []
        indexes = self.contextTable.selectionModel().selectedRows()
        for index in indexes:
            rowIdx = index.row()
            uuidItem = self.contextTable.item(rowIdx, 0)
            uuid = uuidItem.text()
            contextsUuids.append(uuid)
        self.sanityCheck(contextsUuids, False)

    def sanityCheck(self, contextsUuids, refreshSelection=True):
        checkedCommands = []
        
        for name in self.commandsList:
            if self.commandCheckBox[name].isChecked():
                checkedCommands.append(name)

        if not checkedCommands:
            cmds.warning("No commands checked")
            return
        
        # Identify action commands
        actionCommands = []
        for cmd in checkedCommands:
            if self.commandsList.get(cmd, {}).get('isAction', False):
                actionCommands.append(cmd)
        
        # If there are action commands, ask for confirmation
        # if actionCommands:
        #     actionLabels = [self.commandsList[cmd]['label'] for cmd in actionCommands]
        #     actionMessage = "The following actions will modify your scene:\n- " + "\n- ".join(actionLabels)
        #     actionMessage += "\n\nDo you want to continue?"
            
        #     msgBox = QtWidgets.QMessageBox()
        #     msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        #     msgBox.setWindowTitle("Warning: Actions will modify your scene")
        #     msgBox.setText(actionMessage)
        #     msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        #     returnValue = msgBox.exec_()
            
        #     if returnValue != QtWidgets.QMessageBox.Ok:
        #         return
        
        # Every context's actions belong to one chunk, so Revert undoes the
        # whole run rather than just whichever context happened to be last
        if actionCommands:
            self.beginActionChunk()
        try:
            # Process each context
            for contextUUID in contextsUuids:
                # Always get fresh nodes for Selection context
                if contextUUID == "Selection":
                    if refreshSelection:
                        selectedNodes = cmds.ls(selection=True, uuid=True, typ="transform")
                        if not selectedNodes:
                            cmds.warning("No objects selected")
                            return
                        nodes = self.selectHierachy(selectedNodes)
                        # Update the selection context nodes
                        self.contexts["Selection"]["nodes"] = nodes
                    else:
                        nodes = self.contexts[contextUUID]['nodes']
                    
                # Always get fresh nodes for Global context
                elif contextUUID == "Global":
                    if refreshSelection:
                        nodes = self.filterGetAllNodes()
                        # Update the global context nodes
                        self.contexts["Global"]["nodes"] = nodes
                    else:
                        nodes = self.contexts[contextUUID]['nodes']
                else:
                    nodes = self.contexts[contextUUID]['nodes']
            
                # Ensure nodes still exist
                nodes = [uuid for uuid in nodes if cmds.ls(uuid, uuid=True)]

                if not nodes:
                    cmds.warning("No nodes to check in context: {}".format(
                        self.contexts[contextUUID]["name"]))
                    continue
            
                # Update the UI to show we're running
                row = self.contexts[contextUUID]['tableItem'].row()
                self.contextTable.item(row, 3).setText("Running...")
            
                # Run commands and update results
                diagnostics = self.commandToRun(checkedCommands, nodes)
                self.contexts[contextUUID]['nodes'] = nodes
                self.contexts[contextUUID]['diagnostics'] = diagnostics
                self.currentContextUUID = contextUUID
                self.setRowFromItem(self.contexts[contextUUID]['tableItem'])
        finally:
            if actionCommands:
                self.endActionChunk()

        # Show the report for the last context
        self.setRowFromUUID(self.currentContextUUID)

    def selectErrorNodes(self, errors):
        cmds.select(self.parseErrors(errors))

    def addRevertPoint(self, chunkName, actions):
        """Point the Revert buttons at the run that just finished.

        A new chunk replaces the old revert point; the same chunk seen again
        (one run spanning several contexts) adds to it.
        """
        if chunkName != self.revertChunk:
            self.revertChunk = chunkName
            self.revertCommands = []
        for command in actions:
            if command not in self.revertCommands:
                self.revertCommands.append(command)
        self.updateRevertButtons()

    def clearRevertPoint(self):
        self.revertChunk = None
        self.revertCommands = []
        self.updateRevertButtons()

    def updateRevertButtons(self):
        """Only the actions from the most recent run can be reverted."""
        labels = [self.commandsList[cmd]['label'] for cmd in self.revertCommands
                  if cmd in self.commandsList]
        tooltip = "Undo the last run of: {}".format(", ".join(labels))
        for name, button in self.revertButton.items():
            enabled = name in self.revertCommands
            button.setEnabled(enabled)
            button.setToolTip(tooltip if enabled else "Nothing left to revert")

    def actionOutcome(self, entry):
        """How an action run went: 'error', 'changed', or 'idle' for a no-op."""
        if not entry:
            return 'idle'
        if entry.get('error'):
            return 'error'
        return 'changed' if self.parseErrors(entry) else 'idle'

    def undoStackTop(self):
        """Name of the next item on the undo stack, or None if Maya will not say.

        A named chunk reports its own chunk name here, which is what lets us
        tell our own run apart from anything the artist did afterwards.
        """
        try:
            return cmds.undoInfo(query=True, undoName=True)
        except Exception:
            return None

    def revertAction(self, command):
        """Undo the last action run, but only while it is still on top."""
        if not self.revertChunk or command not in self.revertCommands:
            return

        if not cmds.undoInfo(query=True, state=True):
            cmds.warning("Maya's undo queue is off, so nothing can be reverted.")
            self.clearRevertPoint()
            return

        # Anything done in Maya since the run sits above our chunk, so undoing
        # would quietly throw that away instead. Fail closed when unsure.
        top = self.undoStackTop()
        if top != self.revertChunk:
            cmds.warning(
                "The scene has changed since that action ran, so it can no "
                "longer be reverted from here. Use Maya's own undo instead.")
            self.clearRevertPoint()
            return

        reverted = list(self.revertCommands)
        cmds.undo()
        self.clearRevertPoint()

        # The results described a scene state that no longer exists
        diagnostics = self.contexts[self.currentContextUUID]['diagnostics']
        for cmd in reverted:
            diagnostics.pop(cmd, None)
        self.createReport(self.currentContextUUID)
    
    def countErrors(self, diagnostics):
        count = 0
        for error in diagnostics:
            isAction = self.commandsList.get(error, {}).get('isAction', False)
            
            if isAction:
                # Nothing to do is still a pass; only a raised error is not
                if self.actionOutcome(diagnostics[error]) != 'error':
                    count += 1
            else:
                # For checks, success means no errors
                if not diagnostics[error]['uuids']:
                    count += 1
        
        return (count, len(diagnostics))

    def saveSettings(self):
        settings = {}
        settings['consolidated'] = self.consolidatedCheck.isChecked()
        settings['commands'] = {}
        for name in self.commandsList:
            settings['commands'][name] = self.commandCheckBox[name].isChecked()
        cmds.optionVar(sv=("modelCheckerSettings", json.dumps(settings)))
    
    def loadSettings(self):
        settings = cmds.optionVar(q="modelCheckerSettings")
        if settings:
            try:
                settings = json.loads(settings)
                self.consolidatedCheck.setChecked(settings.get('consolidated', False))
                if 'commands' in settings:
                    for name, checked in settings['commands'].items():
                        # Only set checked state if the command still exists
                        if name in self.commandCheckBox:
                            self.commandCheckBox[name].setChecked(checked)
            except:
                # If there's any error parsing settings, just ignore them
                cmds.warning("Error loading modelChecker settings, using defaults")
                    
    def selectFailed(self):
        diagnostics  = self.contexts[self.currentContextUUID]['diagnostics']
        for name in self.commandsList.keys():
            failed = name in diagnostics and len(diagnostics[name]) > 0
            self.commandCheckBox[name].setChecked(failed)
    
    def setRowFromItem(self, item):
        passed, total = self.countErrors(self.contexts[self.currentContextUUID]['diagnostics'])
        color = "#446644" if passed == total else "#664444"
        row = item.row()
        for column in range(self.contextTable.columnCount()):
            if IS_PYSIDE_6:
                self.contextTable.item(row, column).setBackground(QtGui.QColor(color))
            else:
                self.contextTable.item(row, column).setBackgroundColor(QtGui.QColor(color))
            
        nodesItem = self.contextTable.item(row, 2)
        testItem = self.contextTable.item(row, 3)

        nodesItem.setText(str(len(self.contexts[self.currentContextUUID]['nodes'])))
        testItem.setText("{}/{}".format(passed, total))

    def clearRowFromItem(self, item):
        row = item.row()
        for column in range(self.contextTable.columnCount()):
            if IS_PYSIDE_6:
                self.contextTable.item(row, column).setBackground(QtGui.QColor(0,0,0,0))
            else:
                self.contextTable.item(row, column).setBackgroundColor(QtGui.QColor(0,0,0,0))
        testItem = self.contextTable.item(row, 3)
        testItem.setText("0")
    

if __name__ == '__main__':
    try:
        win.close()
    except:
        pass
    win = UI(parent=getMainWindow())
    win.show()
    win.raise_()