""" ---------- Rigging Misc -------------
A tool UI for miscellaneous rigging tools that don't fit in other common areas.




"""

from zoovendor.Qt import QtWidgets, QtCore

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.iconlib import iconlib

from zoo.libs.maya.cmds.objutils import alignutils, locators
from zoo.libs.maya.cmds.rig import riggingmisc, follicles

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

ALIGN_OBJECTS_LIST = ["Rot/Trans", "Translation", "Rotation", "Scale", "Pivot", "All"]


class RiggingMisc(toolsetwidget.ToolsetWidget):
    id = "riggingMisc"
    info = "Assorted rigging tools."
    uiData = {"label": "Rigging Miscellaneous",
              "icon": "robotArm",
              "tooltip": "Assorted rigging tools.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-rigging-miscellaneous/"}

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
        return super(RiggingMisc, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(RiggingMisc, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def matchObjects(self):
        """Match objects to each other"""
        optionsInt = self.properties.matchObjectsCombo.value
        if optionsInt == 0:
            alignutils.matchAllSelection(translate=True, rotate=True, message=True)
        elif optionsInt == 1:
            alignutils.matchAllSelection(translate=True, message=True)
        elif optionsInt == 2:
            alignutils.matchAllSelection(rotate=True, message=True)
        elif optionsInt == 3:
            alignutils.matchAllSelection(scale=True, message=True)
        elif optionsInt == 4:
            alignutils.matchAllSelection(pivot=True, message=True)
        elif optionsInt == 5:
            alignutils.matchAllSelection(translate=True, rotate=True, scale=True, pivot=True, message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivot(self):
        """Marks the center of a selection with a tiny locator with display handles on.
        """
        riggingmisc.markCenterPivot()

    def markPivotLoc(self):
        """Marks the center of a selection with a locator."""
        locators.createLocatorAndMatch(name="", handle=False, locatorSize=1.0, message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivotMulti(self):
        """Marks the center of a selection with a locator with display handles on.
        """
        locators.createLocatorsMatchMany(name="", handle=True, locatorSize=0.1, message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivotMultiLocators(self):
        """Marks the center of a selection with a locator with display handles on.
        """
        locators.createLocatorsMatchMany(name="", handle=False, locatorSize=1.0, message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteAllPivots(self):
        """Deletes all marked locator pivots in the scene.
        """
        riggingmisc.deleteAllCenterPivots()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectHighlightOff(self):
        """Selection Highlighting off for selected objs
        """
        riggingmisc.selectionHighlightSelected(highlight=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectHighlightOn(self):
        """Selection Highlighting on for selected objs
        """
        riggingmisc.selectionHighlightSelected(highlight=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def bakeNamespaces(self):
        """Deletes all marked locator pivots in the scene.
        """
        riggingmisc.bakeNamespaces()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def connectFollicle(self):
        """Connects a follicle to a new mesh, old meshes are replaced.
        """
        follicles.connectFollicleToSelMesh()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.matchObjectsBtn.clicked.connect(self.matchObjects)
            widget.markCenterPivotBtn.clicked.connect(self.markPivot)
            widget.deleteMarkedPivotsBtn.clicked.connect(self.deleteAllPivots)
            widget.selectionHighlightOffBtn.clicked.connect(self.selectHighlightOff)
            widget.selectionHighlightOnBtn.clicked.connect(self.selectHighlightOn)
            widget.bakeNamespacesBtn.clicked.connect(self.bakeNamespaces)
            widget.connectFollicleBtn.clicked.connect(self.connectFollicle)
            # Right click on the icon button
            widget.markCenterPivotBtn.addAction("Mark Center Pivot - Regular",
                                                mouseMenu=QtCore.Qt.RightButton,
                                                icon=iconlib.Icon.icon("locator"),
                                                connect=self.markPivot)
            widget.markCenterPivotBtn.addAction("Mark Center Pivots - Many",
                                                mouseMenu=QtCore.Qt.RightButton,
                                                icon=iconlib.Icon.icon("locator"),
                                                connect=self.markPivotMulti)
            widget.markCenterPivotBtn.addAction("Mark Center Locator",
                                                mouseMenu=QtCore.Qt.RightButton,
                                                icon=iconlib.Icon.icon("locator"),
                                                connect=self.markPivotLoc)
            widget.markCenterPivotBtn.addAction("Mark Center Locators - Many",
                                                mouseMenu=QtCore.Qt.RightButton,
                                                icon=iconlib.Icon.icon("locator"),
                                                connect=self.markPivotMultiLocators)


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
        # Mark Center Pivot ---------------------------------------
        tooltip = "Marks the center of a selection with a locator.  \n " \
                  "For example an edge-ring or other component selection. \n" \
                  "Right-click for more options. \n" \
                  "- Mark Locator: Uses a regular locator rather than a handle/locator \n" \
                  "- Mark Multi: Places many locators at the center of each selected object."
        self.markCenterPivotBtn = elements.AlignedButton("Mark Center (Right Click)",
                                                         icon="locator",
                                                         toolTip=tooltip)
        # Delete Marked Pivots ---------------------------------------
        tooltip = "Deletes all the pivot locator markers in the scene. "
        self.deleteMarkedPivotsBtn = elements.AlignedButton("Delete All Marked Pivots",
                                                            icon="trash",
                                                            toolTip=tooltip)
        # Match Objects Combo ---------------------------------------
        toolTip = "Match Objects Options \n" \
                  "  1. Rot/Trans: Match Rotation and Translation \n" \
                  "  2. Translation: Match Translation Only \n" \
                  "  3. Rotation: Match Rotation Only \n" \
                  "  4. Scale: Match Scale Only \n" \
                  "  5. Pivot: Match Pivot Only \n" \
                  "  6. All: Match Translate, Rotate, Scale and Pivot\n\n" \
                  "Zoo Hotkey: shift v (marking menu)"
        self.matchObjectsCombo = elements.ComboBoxRegular(label="Match Type",
                                                          items=ALIGN_OBJECTS_LIST,
                                                          toolTip=toolTip,
                                                          boxRatio=15,
                                                          labelRatio=10)
        # Match Objects Button ---------------------------------------
        toolTip = "Matches multiple objects to the last selected.  \n" \
                  "  1. Select multiple objects \n" \
                  "  2. Run the tool \n" \
                  "First objects will be matched to the last. \n" \
                  "Uses the `Match Type` drop down settings\n\n" \
                  "Zoo Hotkey: shift v (marking menu)"
        self.matchObjectsBtn = elements.AlignedButton("Match Objects",
                                                      icon="magnet",
                                                      toolTip=toolTip)

        # Selection Highlighting Off ---------------------------------------
        tooltip = "Turns selection highlighting off for all children of the selected object/s. \n" \
                  "Children will not be highlighted on selection. \n\n" \
                  "Requires: \n" \
                  "Preferences > Settings > Selection > Selection Child Highlighting > Use Obj Setting"
        self.selectionHighlightOffBtn = elements.AlignedButton("Selection Highlight Off",
                                                               icon="cursorSelect",
                                                               toolTip=tooltip)
        # Selection Highlighting On ---------------------------------------
        tooltip = "Turns selection highlighting on for all children of the selected object/s. \n" \
                  "Children will always be highlighted on selection. \n\n" \
                  "Requires: \n" \
                  "Preferences > Settings > Selection > Selection Child Highlighting > Use Obj Setting"
        self.selectionHighlightOnBtn = elements.AlignedButton("Selection Highlight On",
                                                              icon="cursorSelect",
                                                              toolTip=tooltip)
        # Bake Namespaces Underscore ---------------------------------------
        tooltip = "Replaces `:` characters in names with `_` for safe game engine export. "
        self.bakeNamespacesBtn = elements.AlignedButton("Bake Namespaces Selected",
                                                        icon="bake",
                                                        toolTip=tooltip)
        # Connect Follicle Button ---------------------------------------
        tooltip = "Connects selected follicle/s to a new mesh. \n" \
                  "If the follicle is already connected to a mesh then will transfer. \n" \
                  "Select follicle/s first then the mesh last and run."
        self.connectFollicleBtn = elements.AlignedButton("Connect Follicle > Mesh",
                                                         icon="bake",
                                                         toolTip=tooltip)


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
                                         spacing=uic.SPACING)
        # Align Objects Layout --------------------------
        alignObjLayout = elements.hBoxLayout(spacing=uic.SPACING)
        alignObjLayout.addWidget(self.matchObjectsCombo, 1)
        alignObjLayout.addWidget(self.matchObjectsBtn, 1)
        # Grid Layout ---------------------------------------
        gridLayout = elements.GridLayout(spacing=uic.SPACING)  # 2 spacing
        row = 0
        gridLayout.addWidget(self.markCenterPivotBtn, row, 0)
        gridLayout.addWidget(self.deleteMarkedPivotsBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.selectionHighlightOffBtn, row, 0)
        gridLayout.addWidget(self.selectionHighlightOnBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.bakeNamespacesBtn, row, 0)
        gridLayout.addWidget(self.connectFollicleBtn, row, 1)
        # Keep grid columns 50/50 sized
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(alignObjLayout)
        mainLayout.addLayout(gridLayout)


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
                                         spacing=uic.SPACING)
        # Align Objects Layout --------------------------
        alignObjLayout = elements.hBoxLayout(spacing=uic.SPACING)
        alignObjLayout.addWidget(self.matchObjectsCombo, 1)
        alignObjLayout.addWidget(self.matchObjectsBtn, 1)
        # Grid Layout ---------------------------------------
        gridLayout = elements.GridLayout(spacing=uic.SPACING)  # 2 spacing
        row = 0
        gridLayout.addWidget(self.markCenterPivotBtn, row, 0)
        gridLayout.addWidget(self.deleteMarkedPivotsBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.selectionHighlightOffBtn, row, 0)
        gridLayout.addWidget(self.selectionHighlightOnBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.bakeNamespacesBtn, row, 0)
        gridLayout.addWidget(self.connectFollicleBtn, row, 1)
        # Keep grid columns 50/50 sized
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(alignObjLayout)
        mainLayout.addLayout(gridLayout)
