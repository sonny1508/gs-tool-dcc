import os
import sys
import inspect

# Get the directory of the current script
current_file = inspect.getframeinfo(inspect.currentframe()).filename
current_dir = os.path.dirname(os.path.abspath(current_file))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# GSPipeline launches tools by exec'ing scripts, so _core is not on sys.path either
core_dir = os.path.join(os.path.dirname(parent_dir), '_core')
if core_dir not in sys.path:
    sys.path.append(core_dir)

# Detect Python version
PY3 = sys.version_info[0] >= 3

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance

except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance

from functools import partial
import json
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import gs_style
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


class ContentScroll(QtWidgets.QScrollArea):
    """Scroll area that asks for all of its content.

    The window then opens big enough to show everything, and this only scrolls
    when the screen is too short for that.
    """

    def __init__(self, content):
        super(ContentScroll, self).__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        gs_style.style_scrollbar(self.verticalScrollBar())
        self.setWidget(content)

    def sizeHint(self):
        self.ensurePolished()
        frame = 2 * self.frameWidth()
        content = self.widget().sizeHint()
        # Room for the scrollbar either way, so showing one never clips a row
        return QtCore.QSize(
            content.width() + frame + self.verticalScrollBar().sizeHint().width(),
            content.height() + frame)

    def minimumSizeHint(self):
        return QtCore.QSize(self.sizeHint().width(), 80)


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
    commandRunButton = {}
    # How many columns each category's rows split into, to save height
    rowColumns = 2
    # The log always gets this much; on a short screen the sections scroll instead
    logHeight = 280
    # Allowance for the title bar when capping the window to the screen
    windowChrome = 40

    # Categories whose commands change the scene rather than report on it
    actionCategories = ('Actions', 'Delete')
    LOG_COLOURS = gs_style.LOG_COLOURS
    actionStatus = {'changed': 'ok', 'error': 'error'}

    # What a check's result type means inside a mesh: how to name one, and the
    # selection mask that shows it. A "nodes" result has nothing inside to select.
    componentFormats = {
        "uv": ".map[{}]",
        "vertex": ".vtx[{}]",
        "edge": ".e[{}]",
        "polygon": ".f[{}]",
    }
    componentMasks = {
        "uv": "polymeshUV",
        "vertex": "vertex",
        "edge": "edge",
        "polygon": "facet",
    }

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
        self.setWindowTitle("Model Checker v{}".format(self.version))
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

        # Maximize / fullscreen drop the size lock until they are undone
        self.sizeReleased = False

        # Revert points at one undo chunk, and only the most recent one
        self.revertChunk = None
        self.revertCommands = []
        # This tool's own selections since then, which Revert can step back over
        self.revertSelects = []
        self.actionCounter = 0
        self.chunkDepth = 0
        self.currentChunk = None

        # Maya announces nothing when its undo stack changes, so look while it matters
        self.revertTimer = QtCore.QTimer(self)
        self.revertTimer.setInterval(500)
        self.revertTimer.timeout.connect(self.checkRevertPoint)

        mainWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(mainWidget)
        mainLayout = QtWidgets.QVBoxLayout(mainWidget)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(6)
        self.measureChecksPanel()
        self.sections = ContentScroll(self.buildSections())
        mainLayout.addWidget(self.sections)
        mainLayout.addLayout(self.buildTickButtons())
        mainLayout.addWidget(self.buildRunButton())
        mainLayout.addWidget(self.buildContextUI(), 1)
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
        # The report sits in a box at the bottom, with the contexts to its left
        panel = QtWidgets.QGroupBox("Log")
        report = QtWidgets.QVBoxLayout(panel)
        contextWidget = QtWidgets.QWidget()
        contextWidgetLayout = QtWidgets.QVBoxLayout()
        contextWidgetLayout.setContentsMargins(0, 0, 0, 0)
        contextWidget.setLayout(contextWidgetLayout)
        self.contextTable = QtWidgets.QTableWidget()
        contextWidgetLayout.addWidget(self.contextTable)
        contextButtonLayout = QtWidgets.QGridLayout()

        addContextsBtn = QtWidgets.QPushButton("Add Contexts")
        removeContextsBtn = QtWidgets.QPushButton("Remove Contexts")
        checkSelectedContextsBtn = QtWidgets.QPushButton("Run Selected Contexts")
        checkAllContextsBtn = QtWidgets.QPushButton("Run All Contexts")
        addContextsBtn.clicked.connect(self.addSelectedNodesAsNewContexts)
        removeContextsBtn.clicked.connect(self.removeSelectedContexts)
        checkSelectedContextsBtn.clicked.connect(self.sanityCheckSelected)
        checkAllContextsBtn.clicked.connect(self.sanityCheckAll)
        contextWidgetLayout.addLayout(contextButtonLayout)
        contextButtonLayout.addWidget(addContextsBtn, 0, 0)
        contextButtonLayout.addWidget(removeContextsBtn, 0, 1)
        contextButtonLayout.addWidget(checkSelectedContextsBtn, 1, 0)
        contextButtonLayout.addWidget(checkAllContextsBtn, 1, 1)

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
        gs_style.style_scrollbar(self.reportOutputUI.verticalScrollBar())

        self.consolidatedCheck = QtWidgets.QCheckBox("Consolidated Display")
        self.consolidatedCheck.setChecked(True)
        self.consolidatedCheck.setToolTip(
            "On: one line per object with its issue count.\n"
            "Off: every node checked and every issue listed.")

        # Contexts start folded away; drag the divider at the left edge to open them
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(contextWidget)
        splitter.addWidget(self.reportOutputUI)
        splitter.setSizes([0, 1])
        report.addWidget(self.consolidatedCheck)
        report.addWidget(splitter, 1)
        report.addLayout(self.buildLogButtons())
        panel.setMinimumHeight(self.logHeight)

        # Set the Selection context as the current context by default
        self.contextTable.setCurrentItem(self.contextTable.item(0, 1))
        self.currentContextUUID = "Selection"

        return panel

    def buildLogButtons(self):
        """What can be done with the last run. Each greys out, saying why, when
        there is nothing for it to do."""
        self.selectErrorsButton = QtWidgets.QPushButton("Select Errors")
        self.selectErrorsButton.clicked.connect(self.selectErrors)
        self.selectObjectsButton = QtWidgets.QPushButton("Select Objects")
        self.selectObjectsButton.clicked.connect(self.selectObjects)
        self.revertButton = QtWidgets.QPushButton("Revert")
        self.revertButton.clicked.connect(self.revertAction)
        self.updateRevertButton()
        clearButton = QtWidgets.QPushButton("Clear")
        clearButton.clicked.connect(self.clearCurrentReport)

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(4)
        layout.addWidget(self.selectErrorsButton)
        layout.addWidget(self.selectObjectsButton)
        layout.addWidget(self.revertButton)
        layout.addWidget(clearButton)
        return layout

    def buildSections(self):
        """Every category in reading order: the checks, then the actions."""
        content = QtWidgets.QWidget()
        categories = QtWidgets.QVBoxLayout(content)
        categories.setContentsMargins(4, 4, 4, 4)
        categories.setSpacing(4)
        for category in self.getCategories(self.commandsList):
            self.buildCategory(category, categories)
        categories.addStretch()
        return content

    def buildCategory(self, category, parentLayout):
        self.categoryWidget[category] = QtWidgets.QWidget()
        self.categoryLayout[category] = QtWidgets.QGridLayout()
        self.categoryLayout[category].setContentsMargins(0, 0, 0, 4)
        self.categoryLayout[category].setHorizontalSpacing(12)
        self.categoryLayout[category].setVerticalSpacing(2)
        self.categoryWidget[category].setLayout(self.categoryLayout[category])
        self.categoryHeader[category] = QtWidgets.QHBoxLayout()
        self.categoryHeader[category].setSpacing(2)

        button = QtWidgets.QPushButton(category[0].upper() + category[1:])
        button.setToolTip("Tick or untick everything in this category")
        font = button.font()
        font.setBold(True)
        button.setFont(font)
        button.clicked.connect(lambda checked=False, cat=category: self.checkCategory(cat))
        self.categoryButton[category] = button

        collapse = QtWidgets.QToolButton()
        collapse.setArrowType(QtCore.Qt.DownArrow)
        collapse.setToolTip("Fold this category away")
        collapse.clicked.connect(lambda checked=False, cat=category: self.toggleUI(cat))
        self.categoryCollapse[category] = collapse

        self.categoryHeader[category].addWidget(button)
        self.categoryHeader[category].addWidget(collapse)
        parentLayout.addLayout(self.categoryHeader[category])
        parentLayout.addWidget(self.categoryWidget[category])

        # Down one column and then the next, so each reads as a list. Every column
        # stretches, used or not, which lines them up from one category to the next.
        names = sorted(name for name in self.commandsList
                       if self.commandsList[name]['category'] == category)
        rowsPerColumn = (len(names) + self.rowColumns - 1) // self.rowColumns
        for index, name in enumerate(names):
            self.buildCommandRow(name)
            self.categoryLayout[category].addWidget(
                self.commandWidget[name], index % rowsPerColumn, index // rowsPerColumn)
        for column in range(self.rowColumns):
            self.categoryLayout[category].setColumnStretch(column, 1)

    def buildCommandRow(self, name):
        label = self.commandsList[name]['label']
        isAction = self.commandsList[name].get('isAction', False)

        self.commandWidget[name] = QtWidgets.QWidget()
        self.commandWidget[name].setMaximumHeight(40)
        self.commandLayout[name] = QtWidgets.QHBoxLayout()

        self.commandWidget[name].setLayout(self.commandLayout[name])

        self.commandLayout[name].setSpacing(4)
        self.commandLayout[name].setContentsMargins(0, 0, 0, 0)
        self.commandWidget[name].setStyleSheet(
            "padding: 0px; margin: 0px;")
        self.commandLabel[name] = QtWidgets.QLabel(label)
        self.commandLabel[name].setMinimumWidth(self.labelWidth)
        self.commandCheckBox[name] = QtWidgets.QCheckBox()

        self.commandCheckBox[name].setChecked(False)
        self.commandCheckBox[name].setMaximumWidth(20)
        self.commandCheckBox[name].toggled.connect(self.updateClashes)

        self.commandRunButton[name] = QtWidgets.QPushButton("Run")
        self.commandRunButton[name].setMaximumWidth(40)
        self.commandRunButton[name].clicked.connect(
            lambda checked=False, cmd=name: self.oneOfs(cmd))

        # The label takes the slack, so the buttons line up on the column's right edge
        self.commandLayout[name].addWidget(self.commandLabel[name], 1)
        self.commandLayout[name].addWidget(self.commandCheckBox[name])
        self.commandLayout[name].addWidget(self.commandRunButton[name])

        if isAction:
            self.commandRunButton[name].setToolTip(
                self.commandsList[name].get('tooltip')
                or ("Changes the whole scene, ignoring your selection"
                    if self.commandsList[name].get('isGlobal', False)
                    else "Changes the objects in the current context"))

    def buildTickButtons(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(4)

        uncheckAllButton = QtWidgets.QPushButton("Uncheck All")
        uncheckAllButton.clicked.connect(self.uncheckAll)
        layout.addWidget(uncheckAllButton)

        invertCheckButton = QtWidgets.QPushButton("Invert")
        invertCheckButton.setToolTip("Flips the checks. Actions stay as they are.")
        invertCheckButton.clicked.connect(self.invertCheck)
        layout.addWidget(invertCheckButton)

        checkAllButton = QtWidgets.QPushButton("Check All")
        checkAllButton.setToolTip("Ticks all the checks. Actions stay as they are.")
        checkAllButton.clicked.connect(self.checkAll)
        layout.addWidget(checkAllButton)
        return layout

    def buildRunButton(self):
        button = QtWidgets.QPushButton("Run on Selected")
        button.setToolTip(
            "Runs everything ticked on your selection, or on the whole scene if "
            "nothing is selected.\nActions go first, so the checks report on the result.")
        button.setMinimumHeight(36)
        gs_style.style_button(button, gs_style.STUDIO_RED)
        button.clicked.connect(self.sanityCheckChecked)
        return button

    def commandNames(self, actions):
        """The commands in one column: the actions, or the checks."""
        return [name for name in self.commandsList
                if self.commandsList[name].get('isAction', False) == actions]

    def updateClashes(self):
        """Grey out any check that a ticked action could only make fail."""
        blockedBy = {}
        for name in self.commandNames(True):
            if self.commandCheckBox[name].isChecked():
                for check in self.commandsList[name].get('clashes', ()):
                    blockedBy[check] = self.commandsList[name]['label']

        for name in self.commandNames(False):
            blocked = name in blockedBy
            if blocked:
                self.commandCheckBox[name].setChecked(False)
                self.setRowStatus(name)
            self.commandWidget[name].setEnabled(not blocked)
            self.commandWidget[name].setToolTip(
                "Off while {} is ticked, since that action would fail this check.".format(
                    blockedBy[name]) if blocked else "")

    def setRowStatus(self, name, level=None):
        """Colour a row's label by result; no level means the default text colour."""
        colour = self.LOG_COLOURS.get(level)
        self.commandLabel[name].setStyleSheet(
            "color: {};".format(colour) if colour else "")
    
    def textWidth(self, metrics, text):
        """QFontMetrics.width() was replaced by horizontalAdvance() in newer Qt."""
        if hasattr(metrics, "horizontalAdvance"):
            return metrics.horizontalAdvance(text)
        return metrics.width(text)

    def measureChecksPanel(self):
        """Fit the row labels to the text they hold, so the columns line up."""
        metrics = self.fontMetrics()
        self.labelWidth = max(
            self.textWidth(metrics, self.commandsList[name]['label'])
            for name in self.commandsList) + 8

    def currentScreen(self):
        return (QtWidgets.QApplication.screenAt(self.frameGeometry().center())
                or QtWidgets.QApplication.primaryScreen())

    def contentSize(self):
        """All of the content, but no taller than the screen. The sections take
        any shortfall by scrolling."""
        self.sections.updateGeometry()
        layout = self.centralWidget().layout()
        layout.activate()
        hint = layout.sizeHint()
        screen = self.currentScreen()
        if not screen:
            return hint
        available = screen.availableGeometry().height() - self.windowChrome
        return QtCore.QSize(hint.width(), min(hint.height(), available))

    def keepOnScreen(self):
        """A window this tall must not open past the bottom of the screen."""
        screen = self.currentScreen()
        if screen:
            overflow = self.frameGeometry().bottom() - screen.availableGeometry().bottom()
            if overflow > 0:
                self.move(self.x(), self.y() - overflow)

    def pinSize(self):
        """Hold the window at its content size - no dragging it out of shape."""
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

    def showEvent(self, event):
        super(UI, self).showEvent(event)
        # Everything is polished by now, so correct the size measured before it was
        if not self.sizeReleased:
            self.pinSize()
            self.keepOnScreen()

    def closeEvent(self, event):
        self.saveSettings()
        self.clearRevertPoint()
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
        # Checks only: ticking the actions too would put Cleanup and every Delete
        # one click away from running on the whole scene
        for command in self.commandNames(False):
            self.commandCheckBox[command].setChecked(True)

    def toggleUI(self, category):
        state = self.categoryWidget[category].isVisible()
        self.categoryCollapse[category].setArrowType(
            QtCore.Qt.RightArrow if state else QtCore.Qt.DownArrow)
        self.categoryWidget[category].setVisible(not state)
        # The window fits its content, so folding means less to scroll, then a shorter window
        if not self.sizeReleased:
            self.pinSize()
            self.keepOnScreen()

    def uncheckAll(self):
        for name in self.commandsList:
            self.commandCheckBox[name].setChecked(False)

    def invertCheck(self):
        for name in self.commandNames(False):
            self.commandCheckBox[name].setChecked(
                not self.commandCheckBox[name].isChecked())

    def clearCurrentReport(self):
        self.clearReportOnContext(self.currentContextUUID)

    def clearReportOnContext(self, contextUUID):
        context = self.contexts[contextUUID]
        context["diagnostics"] = {}
        self.clearRowFromItem(context['tableItem'])
        self.clearRowResults()
        self.updateSelectButtons()
        self.reportOutputUI.clear()

    def clearRowResults(self):
        for command in self.commandsList.keys():
            self.setRowStatus(command)

    def checkCategory(self, category):
        uncheckedCategoryButtons = []
        categoryButtons = []
        for name in self.commandsList.keys():
            if (self.commandsList[name]['category'] == category
                    and self.commandWidget[name].isEnabled()):
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
        
        try:
            # Run the command with the appropriate nodes
            newDiagnostics = self.commandToRun([command], nodes)
            if command in newDiagnostics:
                # The log only ever holds the last button press, so one row's
                # Run is how to get at just that check's errors
                self.contexts[self.currentContextUUID]['diagnostics'] = newDiagnostics
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
        checks = [cmd for cmd in commands if cmd not in actions]
        if not actions:
            return self.runCommands(checks, nodes)

        chunkName = self.beginActionChunk()
        try:
            diagnostics = self.runCommands(actions, nodes)
        finally:
            self.endActionChunk()

        # An action that found nothing to do leaves the undo stack untouched, so
        # it neither gains a revert point nor destroys the one already there
        changed = [cmd for cmd in actions
                   if self.actionOutcome(diagnostics.get(cmd, {})) == 'changed']
        if changed:
            self.addRevertPoint(chunkName, changed)

        # Actions first: a check needs to report on the scene they leave behind, and
        # the component ids it hands to Select Error Nodes must still be valid
        if checks:
            diagnostics.update(self.runCommands(checks, nodes))
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
                    if resultType in self.componentFormats:
                        diagnostics[command]["counts"] = {
                            uuid: self.meshCounts(uuid) for uuid in errors}

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
        for uuid in uuids:
            nodeName = cmds.ls(uuid)
            if nodeName:
                for component in uuids[uuid]:
                    outputErrors.append(nodeName[0] + self.componentFormats[type].format(component))
        return outputErrors

    def createReport(self, uuid):
        context = self.contexts[uuid]
        diagnostics = context['diagnostics']
        nodes = context['nodes']
        name = context['name']
        self.reportOutputUI.clear()
        lastFailed = None
        consolidated = self.consolidatedCheck.isChecked()
        okColour = self.LOG_COLOURS['ok']
        errorColour = self.LOG_COLOURS['error']
        html = "<h2>{}</h2>".format(name)
        self.updateSelectButtons()

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
            self.clearRowResults()
            html += "{} - No tests run in this context.".format(self.contexts[self.currentContextUUID]['name'])
            self.reportOutputUI.setHtml(html)
            return

        for error in sorted(self.commandsList.keys()):
            if error not in diagnostics:
                self.setRowStatus(error)
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
                self.setRowStatus(error, self.actionStatus.get(outcome))
            else:
                self.setRowStatus(error, 'error' if failed else 'ok')

            label = self.commandsList[error]['label']
            
            if lastFailed != failed and lastFailed is not None or (failed is True and lastFailed is True):
                html += "<br>"
            lastFailed = failed
            
            if isAction:
                if outcome == 'changed':
                    html += "&#10752; {}<font color={}> [ CHANGED ]</font><br>".format(label, okColour)
                elif outcome == 'error':
                    html += "&#10752; {}<font color={}> [ ERROR ]</font><br>".format(label, errorColour)
                    html += "&#9492;&#9472; {}<br>".format(entry.get('error', ''))
                else:
                    html += "{} [ NOTHING TO DO ]<br>".format(label)
            else:
                if failed:  # Check failed
                    html += "&#10752; {}<font color={}> [ FAILED ]</font><br>".format(label, errorColour)
                else:  # Check succeeded
                    html += "{}<font color={}> [ SUCCESS ]</font><br>".format(label, okColour)
            
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
                            html += "&#9492;&#9472; {} - <font color={}>{} {}</font><br>".format(node, okColour, store[node], word)
                        else:
                            word = "issues" if store[node] > 1 else "issue"
                            html += "&#9492;&#9472; {} - <font color={}>{} {}</font><br>".format(node, errorColour, store[node], word)
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
            self.sanityCheck(["Global"], True)

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
        checkedCommands = [name for name in self.commandsList
                           if self.commandCheckBox[name].isChecked()]

        if not checkedCommands:
            cmds.warning("Tick at least one check or action first.")
            return

        # Every context's actions belong to one chunk, so Revert undoes the
        # whole run rather than just whichever context happened to be last
        hasActions = any(self.commandsList[name].get('isAction', False)
                         for name in checkedCommands)
        if hasActions:
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
            if hasActions:
                self.endActionChunk()

        # Show the report for the last context
        self.setRowFromUUID(self.currentContextUUID)

    def failedChecks(self):
        """The results in the log that found something. Actions aren't errors."""
        diagnostics = self.contexts[self.currentContextUUID]['diagnostics']
        return [entry for name, entry in diagnostics.items()
                if not self.commandsList.get(name, {}).get('isAction', False)
                and entry.get('uuids')]

    def updateSelectButtons(self):
        """Select Objects needs any error, Select Errors one inside a mesh."""
        diagnostics = self.contexts[self.currentContextUUID]['diagnostics']
        failed = self.failedChecks()
        inMesh = any(entry['type'] in self.componentFormats for entry in failed)
        ranCheck = any(not self.commandsList.get(name, {}).get('isAction', False)
                       for name in diagnostics)
        idle = "Nothing to select." if ranCheck else "Run a check first."

        self.selectObjectsButton.setEnabled(bool(failed))
        self.selectObjectsButton.setToolTip(
            "Selects every object with an error." if failed else idle)

        self.selectErrorsButton.setEnabled(inMesh)
        if inMesh:
            self.selectErrorsButton.setToolTip(
                "Selects the vertices, edges, faces and UVs the checks found.")
        elif failed:
            self.selectErrorsButton.setToolTip(
                "These checks are about whole objects: use Select Objects.")
        else:
            self.selectErrorsButton.setToolTip(idle)

    def meshCounts(self, uuid):
        """How much a mesh had, which is what its component ids depend on."""
        return cmds.polyEvaluate(
            cmds.ls(uuid)[0], vertex=True, edge=True, face=True, uv=True)

    def selectObjects(self):
        uuids = set()
        for entry in self.failedChecks():
            uuids.update(entry['uuids'])
        objects = cmds.ls(list(uuids), long=True)
        if not objects:
            cmds.warning("The objects were deleted since the check.")
            return
        cmds.selectMode(object=True)
        self.selectAsUndoStep(objects)

    def selectErrors(self):
        components = []
        masks = set()
        skipped = False
        for entry in self.failedChecks():
            kind = entry['type']
            if kind not in self.componentFormats:
                continue
            for uuid, ids in entry['uuids'].items():
                # Ids only mean anything on the mesh as it was checked
                name = cmds.ls(uuid)
                if not name or self.meshCounts(uuid) != entry['counts'][uuid]:
                    skipped = True
                    continue
                components.extend(name[0] + self.componentFormats[kind].format(i) for i in ids)
                masks.add(self.componentMasks[kind])

        if not components:
            cmds.warning("The objects changed since the check. Run it again.")
            return
        cmds.selectMode(component=True)
        cmds.selectType(allComponents=False)
        cmds.selectType(**{mask: True for mask in masks})
        self.selectAsUndoStep(components)
        if skipped:
            cmds.warning("Some objects changed since the check. Run it again for those.")

    def selectAsUndoStep(self, items):
        """Select as one named undo step, like a click in the viewport, except
        that Revert knows it is safe to step back over."""
        self.checkRevertPoint()
        self.actionCounter += 1
        chunkName = "modelChecker_select_{}".format(self.actionCounter)
        cmds.undoInfo(openChunk=True, chunkName=chunkName)
        try:
            cmds.select(items, replace=True)
        finally:
            cmds.undoInfo(closeChunk=True)
        if self.revertChunk:
            self.revertSelects.append(chunkName)

    def addRevertPoint(self, chunkName, actions):
        """Point Revert at the run that just finished.

        A new chunk replaces the old revert point; the same chunk seen again
        (one run spanning several contexts) adds to it.
        """
        if chunkName != self.revertChunk:
            self.revertChunk = chunkName
            self.revertCommands = []
            self.revertSelects = []
        for command in actions:
            if command not in self.revertCommands:
                self.revertCommands.append(command)
        self.revertTimer.start()
        self.updateRevertButton()

    def clearRevertPoint(self, tooltip="Run an action first."):
        self.revertChunk = None
        self.revertCommands = []
        self.revertSelects = []
        self.revertTimer.stop()
        self.updateRevertButton(tooltip)

    def updateRevertButton(self, tooltip="Run an action first."):
        """Only the actions from the most recent run can be reverted."""
        self.revertButton.setEnabled(bool(self.revertChunk))
        if self.revertChunk:
            labels = [self.commandsList[cmd]['label'] for cmd in self.revertCommands
                      if cmd in self.commandsList]
            tooltip = "Undoes the last run of: {}".format(", ".join(labels))
        self.revertButton.setToolTip(tooltip)

    def checkRevertPoint(self):
        """Grey Revert out once something else has landed on the undo stack.

        Anything done in Maya since the run sits above its chunk, so undoing
        would quietly throw that away instead. Fail closed when unsure.
        """
        if not self.revertChunk or self.chunkDepth:
            return
        top = self.undoStackTop()
        if (not cmds.undoInfo(query=True, state=True)
                or (top != self.revertChunk and top not in self.revertSelects)):
            self.clearRevertPoint(
                "The scene has changed since the last action. Use Maya's own undo.")

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

    def revertAction(self):
        """Undo the last action run, but only while it is still on top."""
        self.checkRevertPoint()
        if not self.revertChunk:
            return

        reverted = list(self.revertCommands)
        while self.undoStackTop() in self.revertSelects:
            cmds.undo()
        cmds.undo()
        self.clearRevertPoint()

        # The results described a scene state that no longer exists, and that
        # goes for the checks as well, since they ran after the actions
        diagnostics = self.contexts[self.currentContextUUID]['diagnostics']
        for cmd in reverted + self.commandNames(False):
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
        settings['consolidatedLog'] = self.consolidatedCheck.isChecked()
        settings['commands'] = {}
        for name in self.commandsList:
            settings['commands'][name] = self.commandCheckBox[name].isChecked()
        cmds.optionVar(sv=("modelCheckerSettings", json.dumps(settings)))
    
    def loadSettings(self):
        settings = cmds.optionVar(q="modelCheckerSettings")
        if settings:
            try:
                settings = json.loads(settings)
                # A new key: the old "consolidated" is saved as off for anyone who
                # opened the tool while that was the default
                self.consolidatedCheck.setChecked(settings.get('consolidatedLog', True))
                if 'commands' in settings:
                    for name, checked in settings['commands'].items():
                        # Only set checked state if the command still exists
                        if name in self.commandCheckBox:
                            self.commandCheckBox[name].setChecked(checked)
            except:
                # If there's any error parsing settings, just ignore them
                cmds.warning("Error loading modelChecker settings, using defaults")

    def setRowFromItem(self, item):
        passed, total = self.countErrors(self.contexts[self.currentContextUUID]['diagnostics'])
        colour = self.LOG_COLOURS['ok' if passed == total else 'error']
        row = item.row()
        for column in range(self.contextTable.columnCount()):
            self.contextTable.item(row, column).setForeground(
                QtGui.QBrush(QtGui.QColor(colour)))

        nodesItem = self.contextTable.item(row, 2)
        testItem = self.contextTable.item(row, 3)

        nodesItem.setText(str(len(self.contexts[self.currentContextUUID]['nodes'])))
        testItem.setText("{}/{}".format(passed, total))

    def clearRowFromItem(self, item):
        row = item.row()
        for column in range(self.contextTable.columnCount()):
            self.contextTable.item(row, column).setForeground(
                self.contextTable.palette().text())
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