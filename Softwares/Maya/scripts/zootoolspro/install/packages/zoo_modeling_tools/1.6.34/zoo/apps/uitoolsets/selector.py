""" ---------- Selector -------------
A tool for select functions

Author: Andrew Silke
"""
from zoo.libs import iconlib
from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.hotkeys import definedhotkeys

from zoo.apps.tooltips import modelingtooltips as tt

from zoo.libs.maya.cmds.objutils import selection

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class Selector(toolsetwidget.ToolsetWidget):
    id = "selector"
    info = "Template file for building new GUIs."
    uiData = {"label": "Select Toolbox",
              "icon": "cursorSelect",
              "tooltip": "Template file for building new GUIs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-select/"}

    # ------------------
    # STARTUP
    # ------------------

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

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(Selector, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(Selector, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def selectModeMel(self):
        definedhotkeys.selectModeMel()

    def lassoSelectMel(self):
        definedhotkeys.lassoSelectMel()

    def paintSelectMel(self):
        definedhotkeys.paintSelectMel()

    def selectContiguousEdges(self):
        definedhotkeys.selectContiguousEdges()

    def selectShortestPathMel(self):
        definedhotkeys.selectShortestPathMel()

    def selectSimilarMel(self):
        definedhotkeys.selectSimilarMel()

    def selectContiguousEdgesOptions(self):
        definedhotkeys.selectContiguousEdgesOptions()

    def open_zooSelectionSets(self):
        definedhotkeys.open_zooSelectionSets()

    def grabToolMel(self):
        definedhotkeys.grabToolMel()

    def softSelectToggleMel(self):
        definedhotkeys.softSelectToggleMel()

    def softSelectVolume(self):
        definedhotkeys.softSelectVolume()

    def softSelectSurface(self):
        definedhotkeys.softSelectSurface()

    def toVerticesMel(self):
        definedhotkeys.toVerticesMel()

    def toVertexFacesMel(self):
        definedhotkeys.toVertexFacesMel()

    def toVertexPerimiterMel(self):
        definedhotkeys.toContainedFacesMel()

    def toEdgesMel(self):
        definedhotkeys.toEdgesMel()

    def toEdgeLoopMel(self):
        definedhotkeys.toEdgeLoopMel()

    def toEdgeRingMel(self):
        definedhotkeys.toEdgeRingMel()

    def toContainedEdgesMel(self):
        definedhotkeys.toContainedEdgesMel()

    def toEdgePerimiterMel(self):
        definedhotkeys.toEdgePerimiterMel()

    def toFacesMel(self):
        definedhotkeys.toContainedFacesMel()

    def toFacePathMel(self):
        definedhotkeys.toFacePathMel()

    def toContainedFacesMel(self):
        definedhotkeys.toContainedFacesMel()

    def toFacePerimiterMel(self):
        definedhotkeys.toFacePerimiterMel()

    def toFacePerimiterMel(self):
        definedhotkeys.toFacePerimiterMel()

    def toUVsMel(self):
        definedhotkeys.toUVsMel()

    def toUVShellMel(self):
        definedhotkeys.toUVShellMel()

    def toUVShellBorderMel(self):
        definedhotkeys.toUVShellBorderMel()

    def toUVPerimiterMel(self):
        definedhotkeys.toUVPerimiterMel()

    def toUVEdgeLoopMel(self):
        definedhotkeys.toUVEdgeLoopMel()

    def randomSelection(self):
        """Selects randomly from the current selection
        """
        selection.randomSelection(self.properties.selectRandomFloat.value)

    def growSelection(self):
        """Grow selection
        """
        selection.growSelection()

    def shrinkSelection(self):
        """Shrink selection
        """
        selection.shrinkSelection()

    def invertSelection(self):
        """Selects all children of the current selection
        """
        selection.invertSelection()

    def selectHierarchy(self):
        """Selects all children of the current selection
        """
        selection.selectHierarchy()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():  # both UIs
            widget.contiguousEdgeBtn.clicked.connect(self.selectContiguousEdges)
            widget.grabBtn.clicked.connect(self.grabToolMel)
            widget.openZooSelectionSetsBtn.clicked.connect(self.open_zooSelectionSets)
            widget.randomSelectBtn.clicked.connect(self.randomSelection)
            widget.growSelectionBtn.clicked.connect(self.growSelection)
            widget.shrinkSelectionBtn.clicked.connect(self.shrinkSelection)
            widget.selectHierarchyBtn.clicked.connect(self.selectHierarchy)
            widget.invertSelectionBtn.clicked.connect(self.invertSelection)
            # Right Click Menus --------------------
            # Select ------------------
            widget.contiguousEdgeBtn.createMenuItem(text="Sel Contiguous Edges (default)",
                                                    icon=iconlib.icon(":polyLoopEdge", size=uic.MAYA_BTN_ICON_SIZE),
                                                    connection=self.selectContiguousEdges)
            widget.contiguousEdgeBtn.createMenuItem(text="Open Contiguous Options",
                                                    icon=iconlib.icon("windowBrowser"),
                                                    connection=self.selectContiguousEdgesOptions)
            widget.contiguousEdgeBtn.createMenuItem(text="Select Shortest Path",
                                                    icon=iconlib.icon(":textureEditorShortestEdgePathLarge",
                                                                      size=uic.MAYA_BTN_ICON_SIZE),
                                                    connection=self.selectShortestPathMel)
            widget.contiguousEdgeBtn.createMenuItem(text="Select Similar",
                                                    icon=iconlib.icon(":selectSimilar", size=uic.MAYA_BTN_ICON_SIZE),
                                                    connection=self.selectSimilarMel)
            # Convert Select ------------------
            widget.convertBtn.createMenuItem(text="To Vertices",
                                             icon=iconlib.icon(":polyConvertToVertices", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toVerticesMel)
            widget.convertBtn.createMenuItem(text="To Vertex Faces",
                                             icon=iconlib.icon(":polyConvertToVertexFaces",
                                                               size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toVertexFacesMel)
            widget.convertBtn.createMenuItem(text="To Vertex Perimeter",
                                             icon=iconlib.icon(":polyConvertToVertexPerimeter",
                                                               size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toVertexPerimiterMel)
            widget.convertBtn.createMenuItem(text="To Edges",
                                             icon=iconlib.icon(":polyConvertToEdge", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toEdgesMel)
            widget.convertBtn.createMenuItem(text="To Edge Loop",
                                             icon=iconlib.icon(":polyConvertToEdgeLoop", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toEdgeLoopMel)
            widget.convertBtn.createMenuItem(text="To Edge Ring",
                                             icon=iconlib.icon(":polyConvertToEdgeRing", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toEdgeRingMel)
            widget.convertBtn.createMenuItem(text="To Contained Edges",
                                             icon=iconlib.icon(":polyConvertToContainedEdges",
                                                               size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toContainedEdgesMel)
            widget.convertBtn.createMenuItem(text="To Edge Perimeter",
                                             icon=iconlib.icon(":polyConvertToEdgePerimeter",
                                                               size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toEdgePerimiterMel)
            widget.convertBtn.createMenuItem(text="To Faces",
                                             icon=iconlib.icon(":polyConvertToFace", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toFacesMel)
            widget.convertBtn.createMenuItem(text="To Face Path",
                                             icon=iconlib.icon(":polyConvertToFacePath", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toFacePathMel)
            widget.convertBtn.createMenuItem(text="To Contained Faces",
                                             icon=iconlib.icon(":polyConvertToContainedFaces",
                                                               size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toContainedFacesMel)
            widget.convertBtn.createMenuItem(text="To Face Perimeter",
                                             icon=iconlib.icon(":polyConvertToFacePerimeter",
                                                               size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.toFacePerimiterMel)

        # ADVANCED UI --------------------------------
        self.advancedWidget.selectBtn.clicked.connect(self.selectModeMel)
        self.advancedWidget.softSelectBtn.clicked.connect(self.softSelectToggleMel)
        # Select ------------------
        self.advancedWidget.selectBtn.createMenuItem(text="Select Tool (Default)",
                                                     icon=iconlib.icon(":aselect", size=uic.MAYA_BTN_ICON_SIZE),
                                                     connection=self.selectModeMel)
        self.advancedWidget.selectBtn.createMenuItem(text="Lasso Select Tool",
                                                     icon=iconlib.icon(":lassoSelect", size=uic.MAYA_BTN_ICON_SIZE),
                                                     connection=self.lassoSelectMel)
        self.advancedWidget.selectBtn.createMenuItem(text="Paint Select Tool",
                                                     icon=iconlib.icon(":artPaintSelect", size=uic.MAYA_BTN_ICON_SIZE),
                                                     connection=self.paintSelectMel)
        # Soft Select ------------------
        self.advancedWidget.softSelectBtn.createMenuItem(text="Soft Select (Default)",
                                                         icon=iconlib.icon(":selectSurfaceBorder",
                                                                           size=uic.MAYA_BTN_ICON_SIZE),
                                                         connection=self.softSelectToggleMel)
        self.advancedWidget.softSelectBtn.createMenuItem(text="Set Volume Falloff",
                                                         icon=iconlib.icon(":selectSurfaceBorder",
                                                                           size=uic.MAYA_BTN_ICON_SIZE),
                                                         connection=self.softSelectVolume)
        self.advancedWidget.softSelectBtn.createMenuItem(text="Set Surface Falloff",
                                                         icon=iconlib.icon(":selectSurfaceBorder",
                                                                           size=uic.MAYA_BTN_ICON_SIZE),
                                                         connection=self.softSelectSurface)


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
        self.parent = parent
        toolTipDict = tt.selectToolbox()
        if uiMode == UI_MODE_ADVANCED:  # If compact mode then search all nodes
            # btn ---------------------------------------
            self.selectBtn = self.mayaBtn("Select Tool (Right-Click)", ":aselect", toolTipDict["select"])
            # btn ---------------------------------------
            self.softSelectBtn = self.mayaBtn("Soft Sel Tgl (Right-Click)", ":selectSurfaceBorder",
                                              toolTipDict["softSelect"])
        # btn ---------------------------------------
        self.grabBtn = self.mayaBtn("Grab (Move)", ":Grab", toolTipDict["grab"])
        # btn ---------------------------------------
        self.contiguousEdgeBtn = self.mayaBtn("Contiguous Edges (R-Click)", ":polyLoopEdge",
                                              toolTipDict["contiguousEdges"])
        # btn ---------------------------------------
        self.openZooSelectionSetsBtn = self.zooBtn("Open Zoo Selection Sets", "windowBrowser",
                                                   toolTipDict["openZooSelectSets"])
        # btn ---------------------------------------
        self.convertBtn = self.mayaBtn("Convert (Right Click)", ":polyConvertToVertices",
                                       toolTipDict["convertSelection"])
        # Label and Textbox ---------------------------------------
        tooltip = toolTipDict["selectRandom"]
        self.selectRandomFloat = elements.FloatEdit(label="Percentage",
                                                    editText=50,
                                                    toolTip=tooltip,
                                                    smallSlideDist=0.1,
                                                    slideDist=0.5,
                                                    largeSlideDist=5.0)
        # Randomize Button ---------------------------------------
        self.randomSelectBtn = self.zooBtn("Select Random", "randomSelect", toolTipDict["selectRandom"])
        # Grow Selection ---------------------------------
        self.growSelectionBtn = self.mayaBtn("Grow Selection", ":polyGrowSelection", toolTipDict["growSelection"])
        # Shrink Selection ---------------------------------
        self.shrinkSelectionBtn = self.mayaBtn("Shrink Selection", ":polyShrinkSelection",
                                               toolTipDict["shrinkSelection"])
        # Select Hierarchy ---------------------------------
        self.selectHierarchyBtn = self.mayaBtn("Select Hierarchy", ":selectByHierarchy",
                                               toolTipDict["selectHierarchy"])
        # Invert Selection ---------------------------------
        self.invertSelectionBtn = self.zooBtn("Invert Selection", "invert", toolTipDict["invertSelection"])

    def zooBtn(self, txt, icon, toolTip):
        """Regular aligned button with Zoo icon"""
        return elements.leftAlignedButton(txt,
                                          icon=iconlib.icon(icon,
                                                            size=utils.dpiScale(20)),
                                          toolTip=toolTip,
                                          parent=self.parent)

    def mayaBtn(self, txt, icon, toolTip):
        """Regular aligned button with a maya icon"""
        iconSize = utils.dpiScale(uic.MAYA_BTN_ICON_SIZE)
        return elements.leftAlignedButton(txt,
                                          icon=iconlib.icon(icon,
                                                            size=iconSize),
                                          padding=uic.MAYA_BTN_PADDING,
                                          toolTip=toolTip, parent=self.parent)


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
        # Grid Layout ----------------------------------------------------------
        gridTopLayout = elements.GridLayout(spacing=uic.SPACING)
        row = 0
        gridTopLayout.addWidget(self.grabBtn, row, 0)
        gridTopLayout.addWidget(self.contiguousEdgeBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.convertBtn, row, 0)
        gridTopLayout.addWidget(self.openZooSelectionSetsBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.growSelectionBtn, row, 0)
        gridTopLayout.addWidget(self.shrinkSelectionBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.invertSelectionBtn, row, 0)
        gridTopLayout.addWidget(self.selectHierarchyBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.selectRandomFloat, row, 0)
        gridTopLayout.addWidget(self.randomSelectBtn, row, 1)
        gridTopLayout.setColumnStretch(0, 1)
        gridTopLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------
        mainLayout.addLayout(gridTopLayout)


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
        # Grid Layout ----------------------------------------------------------
        gridTopLayout = elements.GridLayout(spacing=uic.SPACING)
        row = 0
        gridTopLayout.addWidget(self.selectBtn, row, 0)
        gridTopLayout.addWidget(self.contiguousEdgeBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.grabBtn, row, 0)
        gridTopLayout.addWidget(self.softSelectBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.convertBtn, row, 0)
        gridTopLayout.addWidget(self.openZooSelectionSetsBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.growSelectionBtn, row, 0)
        gridTopLayout.addWidget(self.shrinkSelectionBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.invertSelectionBtn, row, 0)
        gridTopLayout.addWidget(self.selectHierarchyBtn, row, 1)
        row += 1
        gridTopLayout.addWidget(self.selectRandomFloat, row, 0)
        gridTopLayout.addWidget(self.randomSelectBtn, row, 1)
        gridTopLayout.setColumnStretch(0, 1)
        gridTopLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------
        mainLayout.addLayout(gridTopLayout)
