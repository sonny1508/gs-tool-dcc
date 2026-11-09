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
import traceback
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import gs_style
import Model_Checker.modelChecker_commands as mcc
import Model_Checker.modelChecker_debug as mcd
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
    debugViews = mcl.mcDebugViews
    commandWidget = {}
    commandLayout = {}
    commandButton = {}
    commandCheckBox = {}
    commandSelectButton = {}
    # How many columns each category's rows split into, to save height
    rowColumns = 2
    # The log always gets this much; on a short screen the sections scroll instead
    logHeight = 280
    actionButtonHeight = 20
    # Allowance for the title bar when capping the window to the screen
    windowChrome = 40

    # Categories whose commands change the scene rather than report on it
    actionCategories = ('Actions', 'Delete')
    LOG_COLOURS = gs_style.LOG_COLOURS

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
        self.revertCommand = None
        # This tool's own selections since then, which Revert can step back over
        self.revertSelects = []
        self.actionCounter = 0

        # Maya announces nothing when its undo stack changes, so look while it matters
        self.revertTimer = QtCore.QTimer(self)
        self.revertTimer.setInterval(500)
        self.revertTimer.timeout.connect(self.checkRevertPoint)

        mainWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(mainWidget)
        mainLayout = QtWidgets.QVBoxLayout(mainWidget)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(8)
        self.measureChecksPanel()
        self.sections = ContentScroll(self.buildChecks())
        mainLayout.addWidget(self.sections)
        mainLayout.addLayout(self.buildTickButtons())
        mainLayout.addWidget(self.buildRunButton())
        mainLayout.addLayout(self.buildActions())
        mainLayout.addLayout(self.buildDebug())
        mainLayout.addWidget(self.buildContextUI(), 1)
        self.pinSize()
        self.loadSettings()
        # A view outlives the window that switched it on, and can be switched
        # off by a scene change, so the buttons follow the views and not the clicks
        mcd.addListener(self.syncDebugButtons)
        self.syncDebugButtons()
        
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
                selectedNodes = self.selectionUuids()
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
                selectedNodes = self.selectionUuids()
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
        # With the report's own size hint out of it, the log asks for exactly this
        # much, instead of drifting up to the hint whenever there is room
        splitter.setSizePolicy(
            splitter.sizePolicy().horizontalPolicy(), QtWidgets.QSizePolicy.Ignored)
        panel.setMinimumHeight(self.logHeight)

        # Set the Selection context as the current context by default
        self.contextTable.setCurrentItem(self.contextTable.item(0, 1))
        self.currentContextUUID = "Selection"

        return panel

    def buildLogButtons(self):
        """What can be done with the log as a whole. Each greys out, saying why,
        when there is nothing for it to do."""
        self.selectObjectsButton = QtWidgets.QPushButton("Select Objects")
        self.selectObjectsButton.clicked.connect(self.selectObjects)
        self.revertButton = QtWidgets.QPushButton("Revert")
        self.revertButton.clicked.connect(self.revertAction)
        self.updateRevertButton()
        clearButton = QtWidgets.QPushButton("Clear")
        clearButton.clicked.connect(self.clearCurrentReport)

        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(8)
        layout.addWidget(self.selectObjectsButton)
        layout.addWidget(self.revertButton)
        layout.addWidget(clearButton)
        return layout

    def buildChecks(self):
        """The categories that report on the scene, which tick and Run on Selected work on."""
        content = QtWidgets.QWidget()
        categories = QtWidgets.QVBoxLayout(content)
        categories.setContentsMargins(4, 4, 4, 4)
        categories.setSpacing(4)
        names = set(self.commandsList[name]['category'] for name in self.shownNames())
        for category in sorted(names - set(self.actionCategories), key=str.lower):
            self.buildCategory(category, categories)
        categories.addStretch()
        return content

    def buildActions(self):
        """The categories that change the scene, one click each."""
        categories = QtWidgets.QVBoxLayout()
        categories.setSpacing(4)
        for category in self.actionCategories:
            self.buildCategory(category, categories)
        return categories

    def buildDebug(self):
        """Toggles for the debug views, which change how the viewport draws. One
        is on at a time; modelChecker_debug switches the others off, and the
        buttons follow it."""
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(4)
        header, grid = self.buildSection("Debug", layout)
        header.addWidget(self.sectionTitle("Debug", clickable=False))

        self.debugButtons = {}
        names = sorted(self.debugViews)
        rowsPerColumn = (len(names) + self.rowColumns - 1) // self.rowColumns
        for index, name in enumerate(names):
            button = QtWidgets.QPushButton(self.debugViews[name]['label'])
            button.setCheckable(True)
            button.setFixedHeight(self.actionButtonHeight)
            button.setToolTip(self.debugViews[name]['tooltip'])
            gs_style.style_toggle(button)
            # PySide6 calls this with no arguments, so the button is asked
            # whether it is on rather than told by the signal
            button.clicked.connect(
                lambda checked=False, view=name: self.toggleDebugView(view))
            self.debugButtons[name] = button
            grid.addWidget(button, index % rowsPerColumn, index // rowsPerColumn)
        for column in range(self.rowColumns):
            grid.setColumnStretch(column, 1)
        return layout

    def toggleDebugView(self, view):
        # Qt has already flipped the button by the time it says it was clicked
        on = self.debugButtons[view].isChecked()
        try:
            mcd.setView(view, on)
        except Exception as e:
            traceback.print_exc()
            cmds.warning("Could not switch {}: {}. See the Script Editor.".format(
                self.debugViews[view]['label'], str(e)))
        self.syncDebugButtons()

    def syncDebugButtons(self):
        for name, button in self.debugButtons.items():
            button.setChecked(mcd.isOn(name))

    def buildSection(self, category, parentLayout):
        """A section's header row and the grid of rows under it, added to
        `parentLayout`. Returns both, for the caller to fill."""
        self.categoryWidget[category] = QtWidgets.QWidget()
        self.categoryLayout[category] = QtWidgets.QGridLayout()
        # Set in from the header, so that the rows read as inside its section
        self.categoryLayout[category].setContentsMargins(8, 2, 8, 6)
        self.categoryLayout[category].setHorizontalSpacing(16)
        self.categoryLayout[category].setVerticalSpacing(4)
        self.categoryWidget[category].setLayout(self.categoryLayout[category])
        self.categoryHeader[category] = QtWidgets.QHBoxLayout()
        self.categoryHeader[category].setSpacing(0)
        parentLayout.addLayout(self.categoryHeader[category])
        parentLayout.addWidget(self.categoryWidget[category])
        return self.categoryHeader[category], self.categoryLayout[category]

    def sectionTitle(self, text, clickable):
        button = QtWidgets.QPushButton(text[0].upper() + text[1:])
        font = button.font()
        font.setBold(True)
        button.setFont(font)
        gs_style.style_section_header(button)
        if not clickable:
            # Only a title, looking like the other headers: there is nothing to tick
            # in here, and these sections are always in view, so they don't fold
            button.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            button.setFocusPolicy(QtCore.Qt.NoFocus)
        return button

    def buildCategory(self, category, parentLayout):
        self.buildSection(category, parentLayout)
        isAction = category in self.actionCategories
        button = self.sectionTitle(category, clickable=not isAction)
        self.categoryButton[category] = button
        self.categoryHeader[category].addWidget(button)

        if not isAction:
            button.setToolTip("Tick or untick everything in this category")
            button.clicked.connect(lambda checked=False, cat=category: self.checkCategory(cat))

            collapse = QtWidgets.QToolButton()
            collapse.setArrowType(QtCore.Qt.DownArrow)
            collapse.setToolTip("Fold this category away")
            # As tall as the title beside it, so the two make one unbroken band
            collapse.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
            gs_style.style_section_header(collapse)
            collapse.clicked.connect(lambda checked=False, cat=category: self.toggleUI(cat))
            self.categoryCollapse[category] = collapse
            self.categoryHeader[category].addWidget(collapse)

        # Down one column and then the next, so each reads as a list. Every column
        # stretches, used or not, which lines them up from one category to the next.
        names = sorted(name for name in self.shownNames()
                       if self.commandsList[name]['category'] == category)
        rowsPerColumn = (len(names) + self.rowColumns - 1) // self.rowColumns
        for index, name in enumerate(names):
            row = self.buildActionButton(name) if isAction else self.buildCheckRow(name)
            self.categoryLayout[category].addWidget(
                row, index % rowsPerColumn, index // rowsPerColumn)
        for column in range(self.rowColumns):
            self.categoryLayout[category].setColumnStretch(column, 1)

    def buildActionButton(self, name):
        button = QtWidgets.QPushButton(self.commandsList[name]['label'])
        button.setFixedHeight(self.actionButtonHeight)
        button.setToolTip(
            self.commandsList[name].get('tooltip')
            or ("Runs on the whole scene, ignoring your selection."
                if self.commandsList[name].get('isGlobal', False)
                else "Runs on your selection."))
        button.clicked.connect(lambda checked=False, cmd=name: self.runAction(cmd))
        return button

    def buildCheckRow(self, name):
        """A tick box for Run on Selected, the check itself as a button that runs
        it there and then, and Select Errors for what it found."""
        self.commandWidget[name] = QtWidgets.QWidget()
        self.commandWidget[name].setMaximumHeight(40)
        self.commandLayout[name] = QtWidgets.QHBoxLayout()
        self.commandWidget[name].setLayout(self.commandLayout[name])
        self.commandLayout[name].setSpacing(6)
        self.commandLayout[name].setContentsMargins(0, 0, 0, 0)

        self.commandCheckBox[name] = QtWidgets.QCheckBox()
        self.commandCheckBox[name].setChecked(False)
        self.commandCheckBox[name].setToolTip("Tick to include it in Run on Selected.")

        button = QtWidgets.QPushButton(self.commandsList[name]['label'])
        button.setMinimumWidth(self.labelWidth)
        button.setFixedHeight(self.actionButtonHeight)
        button.setToolTip(self.commandsList[name].get('tooltip', ''))
        button.clicked.connect(lambda checked=False, cmd=name: self.oneOfs(cmd))
        self.commandButton[name] = button

        self.commandSelectButton[name] = QtWidgets.QPushButton("Select Errors")
        self.commandSelectButton[name].setFixedWidth(self.selectWidth)
        self.commandSelectButton[name].setFixedHeight(self.actionButtonHeight)
        self.commandSelectButton[name].clicked.connect(
            lambda checked=False, cmd=name: self.selectErrors(cmd))

        # The check takes the slack, so Select Errors lines up on the column's right edge
        self.commandLayout[name].addWidget(self.commandCheckBox[name])
        self.commandLayout[name].addWidget(button, 1)
        self.commandLayout[name].addWidget(self.commandSelectButton[name])
        return self.commandWidget[name]

    def buildTickButtons(self):
        # "Tick", not "Check": every row is a check button now, and "Check All"
        # would read as running them all
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(8)

        uncheckAllButton = QtWidgets.QPushButton("Untick All")
        uncheckAllButton.clicked.connect(self.uncheckAll)
        layout.addWidget(uncheckAllButton)

        invertCheckButton = QtWidgets.QPushButton("Invert")
        invertCheckButton.clicked.connect(self.invertCheck)
        layout.addWidget(invertCheckButton)

        checkAllButton = QtWidgets.QPushButton("Tick All")
        checkAllButton.clicked.connect(self.checkAll)
        layout.addWidget(checkAllButton)
        return layout

    def buildRunButton(self):
        button = QtWidgets.QPushButton("Run on Selected")
        button.setToolTip(
            "Runs the ticked checks on your selection, or on the whole scene if "
            "nothing is selected.")
        button.setMinimumHeight(36)
        gs_style.style_button(button, gs_style.STUDIO_RED)
        button.clicked.connect(self.sanityCheckChecked)
        return button

    def shownNames(self):
        """The commands on the window. A hidden one still works, but has no button."""
        return [name for name in self.commandsList
                if not self.commandsList[name].get('hidden', False)]

    def checkNames(self):
        """The commands with a row: those that report rather than change the scene."""
        return [name for name in self.shownNames()
                if not self.commandsList[name].get('isAction', False)]

    def checkFailed(self, entry):
        """Whether a check's result found something, or the check itself broke."""
        return bool(entry.get('uuids') or entry.get('data') or entry.get('error'))

    def commandTitle(self, name):
        """A command's name away from its section, where "History" alone could be
        either the check or the delete."""
        label = self.commandsList[name]['label']
        if self.commandsList[name]['category'] == 'Delete':
            return "Delete {}".format(label)
        return label

    def setRowStatus(self, name, level=None):
        """Colour a check button's text by result; no level means the default colour."""
        colour = self.LOG_COLOURS.get(level)
        self.commandButton[name].setStyleSheet(
            "QPushButton {{ color: {}; }}".format(colour) if colour else "")
    
    def textWidth(self, metrics, text):
        """QFontMetrics.width() was replaced by horizontalAdvance() in newer Qt."""
        if hasattr(metrics, "horizontalAdvance"):
            return metrics.horizontalAdvance(text)
        return metrics.width(text)

    def measureChecksPanel(self):
        """Fit the check buttons to the text they hold, so the columns line up."""
        metrics = self.fontMetrics()
        self.labelWidth = max(
            self.textWidth(metrics, self.commandsList[name]['label'])
            for name in self.checkNames()) + 24
        self.selectWidth = self.textWidth(metrics, "Select Errors") + 24

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
        # With the window gone there is no button left to switch a view off
        mcd.removeListener(self.syncDebugButtons)
        mcd.turnAllOff()
        super(UI, self).closeEvent(event)

    def checkState(self, name):
        return self.commandCheckBox[name].checkState()

    def checkAll(self):
        for command in self.checkNames():
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
        for name in self.checkNames():
            self.commandCheckBox[name].setChecked(False)

    def invertCheck(self):
        for name in self.checkNames():
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
        for command in self.checkNames():
            self.setRowStatus(command)

    def checkCategory(self, category):
        uncheckedCategoryButtons = []
        categoryButtons = []
        for name in self.checkNames():
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
    
    def selectionUuids(self):
        """The selected objects, counting a component as the object it is on, so
        that Select Errors doesn't leave the next click with nothing selected."""
        selected = cmds.ls(selection=True, objectsOnly=True, long=True)
        if not selected:
            return []
        objects = set(cmds.ls(selected, transforms=True, long=True))
        shapes = cmds.ls(selected, shapes=True, long=True)
        if shapes:
            objects.update(cmds.listRelatives(shapes, parent=True, fullPath=True) or [])
        return cmds.ls(list(objects), uuid=True) if objects else []

    def oneOfs(self, command):
        """Run one check on the current context. Only its own result changes, so
        the other rows keep theirs, and their Select Errors."""
        if self.commandsList[command].get('isGlobal', False):
            # Looks at the whole scene whatever is selected, so it needs no selection
            nodes = self.filterGetAllNodes()
        elif self.currentContextUUID == "Selection":
            # Get fresh selection
            selectedNodes = self.selectionUuids()
            if not selectedNodes:
                cmds.warning("No objects selected")
                return
            # Update nodes for selection context
            nodes = self.selectHierachy(selectedNodes)
            self.contexts["Selection"]["nodes"] = nodes
        elif self.currentContextUUID == "Global":
            # Use all scene nodes
            nodes = self.filterGetAllNodes()
            self.contexts["Global"]["nodes"] = nodes
        else:
            # Custom context - use nodes from that context
            nodes = self.contexts[self.currentContextUUID]['nodes']
            # Verify nodes still exist
            nodes = [node for node in nodes if cmds.ls(node, uuid=True)]
            if not nodes:
                cmds.warning("No valid nodes found in context: {}".format(
                    self.contexts[self.currentContextUUID]["name"]))
                return

        try:
            # Run the command with the appropriate nodes
            newDiagnostics = self.runCommands([command], nodes)
            if command in newDiagnostics:
                self.contexts[self.currentContextUUID]['diagnostics'].update(newDiagnostics)
                # Update the report
                self.createReport(self.currentContextUUID)
            else:
                cmds.warning("Command failed to return diagnostic information: {}".format(command))
        except Exception as e:
            cmds.warning("Error running command '{}': {}".format(command, str(e)))

    def runAction(self, command):
        """Change the scene, as one click and one undo chunk.

        One chunk per click is what makes Revert possible: deletes cannot be
        rebuilt by hand, so we lean on Maya's undo stack instead.
        """
        # Always what is selected now, never the context of the last check: an
        # unconfirmed change must not reach past what the artist is looking at
        if self.commandsList[command].get('isGlobal', False):
            nodes = self.filterGetAllNodes()
        else:
            selectedNodes = self.selectionUuids()
            if not selectedNodes:
                cmds.warning("Select the objects for {} first.".format(
                    self.commandTitle(command)))
                return
            nodes = self.selectHierachy(selectedNodes)

        self.actionCounter += 1
        chunkName = "modelChecker_{}".format(self.actionCounter)
        cmds.undoInfo(openChunk=True, chunkName=chunkName)
        try:
            newDiagnostics = self.runCommands([command], nodes)
        finally:
            cmds.undoInfo(closeChunk=True)

        # An action that found nothing to do leaves the undo stack untouched, so
        # it neither gains a revert point nor destroys the one already there
        if self.actionOutcome(newDiagnostics.get(command, {})) == 'changed':
            self.addRevertPoint(chunkName, command)

        # The checks keep their results. Taken out first so that this one goes
        # back in as the newest, which is the one the log shows on top
        diagnostics = self.contexts[self.currentContextUUID]['diagnostics']
        diagnostics.pop(command, None)
        diagnostics.update(newDiagnostics)
        self.createReport(self.currentContextUUID)

    def runCommands(self, commands, nodes):
        """Execute the given commands on the specified nodes."""
        diagnostics = {}
        SLMesh = om.MSelectionList()
        
        # Filter nodes to ensure they exist. A scene-wide command doesn't need any.
        nodes = [node for node in nodes if cmds.ls(node, uuid=True)]
        if not nodes and not all(self.commandsList[command].get('isGlobal', False)
                                 for command in commands):
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

        self.clearRowResults()
        # The newest action goes on top, where the result of a click can't be missed
        actions = [error for error in reversed(list(diagnostics))
                   if self.commandsList[error].get('isAction', False)]
        checks = sorted(error for error in diagnostics if error not in actions)

        for error in actions + checks:
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
                # A check fails on what it found, and on breaking: a check that
                # couldn't look must never read as a pass
                failed = self.checkFailed(entry)
            
            # Update UI based on success/failure
            if not isAction:
                self.setRowStatus(error, 'error' if failed else 'ok')

            label = self.commandTitle(error)

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
                if entry.get('error'):
                    html += "&#10752; {}<font color={}> [ ERROR ]</font><br>".format(label, errorColour)
                    html += "&#9492;&#9472; Could not run, see the Script Editor.<br>"
                elif failed:  # Check failed
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
        self.reportOutputUI.moveCursor(QtGui.QTextCursor.Start)

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
        if self.selectionUuids():
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
        checkedCommands = [name for name in self.checkNames()
                           if self.commandCheckBox[name].isChecked()]

        if not checkedCommands:
            cmds.warning("Tick at least one check first.")
            return

        # Process each context
        for contextUUID in contextsUuids:
            # Always get fresh nodes for Selection context
            if contextUUID == "Selection":
                if refreshSelection:
                    selectedNodes = self.selectionUuids()
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
            diagnostics = self.runCommands(checkedCommands, nodes)
            self.contexts[contextUUID]['nodes'] = nodes
            self.contexts[contextUUID]['diagnostics'] = diagnostics
            self.currentContextUUID = contextUUID
            self.setRowFromItem(self.contexts[contextUUID]['tableItem'])

        # Show the report for the last context
        self.setRowFromUUID(self.currentContextUUID)

    def failedChecks(self):
        """The results in the log that found something. Actions aren't errors."""
        diagnostics = self.contexts[self.currentContextUUID]['diagnostics']
        return [entry for name, entry in diagnostics.items()
                if not self.commandsList.get(name, {}).get('isAction', False)
                and entry.get('uuids')]

    def updateSelectButtons(self):
        """A row's Select Errors needs that check to have found something, Select
        Objects any of them to have."""
        diagnostics = self.contexts[self.currentContextUUID]['diagnostics']
        ranCheck = False
        for name in self.checkNames():
            entry = diagnostics.get(name)
            button = self.commandSelectButton[name]
            button.setEnabled(bool(entry and entry.get('uuids')))
            if not entry:
                button.setToolTip("Run this check first.")
                continue
            ranCheck = True
            if entry.get('data'):
                # Scene Cleanup: what it finds isn't objects, and Cleanup fixes it
                button.setToolTip("Nothing to select. Press Cleanup to fix it.")
            elif not entry.get('uuids'):
                button.setToolTip("Nothing to select.")
            elif entry['type'] in self.componentFormats:
                button.setToolTip("Selects what this check found inside the meshes.")
            else:
                button.setToolTip("Selects the objects this check found.")

        failed = self.failedChecks()
        self.selectObjectsButton.setEnabled(bool(failed))
        if failed:
            self.selectObjectsButton.setToolTip("Selects every object with an error.")
        else:
            self.selectObjectsButton.setToolTip(
                "Nothing to select." if ranCheck else "Run a check first.")

    def meshCounts(self, uuid):
        """How much a mesh had, which is what its component ids depend on."""
        return cmds.polyEvaluate(
            cmds.ls(uuid)[0], vertex=True, edge=True, face=True, uv=True)

    def selectObjects(self):
        uuids = set()
        for entry in self.failedChecks():
            uuids.update(entry['uuids'])
        self.selectNodes(uuids)

    def selectNodes(self, uuids):
        objects = cmds.ls(list(uuids), long=True)
        if not objects:
            cmds.warning("The objects were deleted since the check.")
            return
        cmds.selectMode(object=True)
        self.selectAsUndoStep(objects)

    def selectErrors(self, command):
        """Select what one check found: inside the meshes where it can, or the
        objects themselves where the result is about whole objects."""
        entry = self.contexts[self.currentContextUUID]['diagnostics'].get(command)
        if not entry or not entry.get('uuids'):
            return
        kind = entry['type']
        if kind not in self.componentFormats:
            self.selectNodes(entry['uuids'])
            return

        components = []
        skipped = False
        for uuid, ids in entry['uuids'].items():
            # Ids only mean anything on the mesh as it was checked
            name = cmds.ls(uuid)
            if not name or self.meshCounts(uuid) != entry['counts'][uuid]:
                skipped = True
                continue
            components.extend(name[0] + self.componentFormats[kind].format(i) for i in ids)

        if not components:
            cmds.warning("The objects changed since the check. Run it again.")
            return
        cmds.selectMode(component=True)
        cmds.selectType(allComponents=False)
        cmds.selectType(**{self.componentMasks[kind]: True})
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

    def addRevertPoint(self, chunkName, command):
        """Point Revert at the action that just ran, in place of any before it."""
        self.revertChunk = chunkName
        self.revertCommand = command
        self.revertSelects = []
        self.revertTimer.start()
        self.updateRevertButton()

    def clearRevertPoint(self, tooltip="Run an action first."):
        self.revertChunk = None
        self.revertCommand = None
        self.revertSelects = []
        self.revertTimer.stop()
        self.updateRevertButton(tooltip)

    def updateRevertButton(self, tooltip="Run an action first."):
        """Only the most recent action can be reverted."""
        self.revertButton.setEnabled(bool(self.revertChunk))
        if self.revertChunk:
            tooltip = "Undoes {}.".format(self.commandTitle(self.revertCommand))
        self.revertButton.setToolTip(tooltip)

    def checkRevertPoint(self):
        """Grey Revert out once something else has landed on the undo stack.

        Anything done in Maya since the run sits above its chunk, so undoing
        would quietly throw that away instead. Fail closed when unsure.
        """
        if not self.revertChunk:
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

        reverted = self.revertCommand
        while self.undoStackTop() in self.revertSelects:
            cmds.undo()
        cmds.undo()
        self.clearRevertPoint()

        # The action's line described a change that is gone. So may the checks,
        # if they ran again after it, and a pass that no longer holds is the worst
        # thing to leave up, so they go as well
        diagnostics = self.contexts[self.currentContextUUID]['diagnostics']
        for cmd in [reverted] + self.checkNames():
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
                if not self.checkFailed(diagnostics[error]):
                    count += 1
        
        return (count, len(diagnostics))

    def saveSettings(self):
        settings = {}
        settings['consolidatedLog'] = self.consolidatedCheck.isChecked()
        settings['commands'] = {}
        for name in self.checkNames():
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