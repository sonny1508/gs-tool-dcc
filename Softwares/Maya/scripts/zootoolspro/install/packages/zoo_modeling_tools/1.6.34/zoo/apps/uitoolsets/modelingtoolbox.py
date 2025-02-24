""" ---------- Modeling Toolbox (Multiple UI Modes) -------------

"""

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets, QtCore
from zoo.libs.maya.cmds.hotkeys import definedhotkeys
from zoo.apps.tooltips import modelingtooltips as tt

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ModelingToolbox(toolsetwidget.ToolsetWidget):
    id = "modelingToolbox"
    info = "Maya modeling tools and hotkey trainer."
    uiData = {"label": "Modeling Toolbox",
              "icon": "toolsets",
              "tooltip": "Maya modeling tools and hotkey trainer.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-modeling-toolbox/"}

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
        return super(ModelingToolbox, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ModelingToolbox, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def extrudeToolMel(self):
        definedhotkeys.extrudeToolMel()

    def createCvCurveTool(self):
        definedhotkeys.createCvCurveTool()

    def bevelToolMel(self):
        definedhotkeys.bevelToolMel()

    def bevelToolMelRounded(self):
        definedhotkeys.bevelToolMelRounded()

    def bevelToolMelChamferOff(self):
        definedhotkeys.bevelToolMelChamferOff()

    def quadDrawToolMel(self):
        definedhotkeys.quadDrawToolMel()

    def makeLiveMelQuadDraw(self):
        definedhotkeys.makeLiveMelQuadDraw()

    def makeLiveMel(self):
        definedhotkeys.makeLiveMel()

    def makeLiveOffMel(self):
        definedhotkeys.makeLiveOffMel()

    def bridgeToolMel(self):
        definedhotkeys.bridgeToolMel()

    def fillHoleToolMel(self):
        definedhotkeys.fillHoleToolMel()

    def appendToolMel(self):
        definedhotkeys.appendToolMel()

    def wedgeToolMel(self):
        definedhotkeys.wedgeToolMel()

    def chamferVertexToolMel(self):
        definedhotkeys.chamferVertexToolMel()

    def multiCutToolMel(self):
        definedhotkeys.multiCutToolMel()

    def edgeFlowToolMel(self):
        definedhotkeys.edgeFlowToolMel()

    def connectToolMel(self):
        definedhotkeys.connectToolMel()

    def edgeLoopToFromToolMel(self):
        definedhotkeys.edgeLoopToFromToolMel()

    def offsetEdgeLoopToolMel(self):
        definedhotkeys.offsetEdgeLoopToolMel()

    def pokeToolMel(self):
        definedhotkeys.pokeToolMel()

    def mergeCenterToolMel(self):
        definedhotkeys.mergeCenterToolMel()

    def mergeToVertToolMel(self):
        definedhotkeys.mergeToVertToolMel()

    def mergeToleranceToolMel(self):
        definedhotkeys.mergeToleranceToolMel()

    def collapseEdgeRingToolMel(self):
        definedhotkeys.collapseEdgeRingToolMel()

    def deleteEdgeToolMel(self):
        definedhotkeys.deleteEdgeToolMel()

    def makeHoleToolMel(self):
        definedhotkeys.makeHoleToolMel()

    def circularizeToolMel(self):
        definedhotkeys.circularizeToolMel()

    def spinEdgeToolMel(self):
        definedhotkeys.spinEdgeToolMel()

    def conformToolMel(self):
        definedhotkeys.conformToolMel()

    def averageVerticesToolMel(self):
        definedhotkeys.averageVerticesToolMel()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():  # Both UI modes
            widget.extrudeBtn.clicked.connect(self.extrudeToolMel)
            widget.bevelBtn.clicked.connect(self.bevelToolMel)
            widget.quadDrawBtn.clicked.connect(self.quadDrawToolMel)
            widget.bridgeBtn.clicked.connect(self.bridgeToolMel)
            widget.multicutBtn.clicked.connect(self.multiCutToolMel)
            widget.edgeFlowBtn.clicked.connect(self.edgeFlowToolMel)
            widget.connectBtn.clicked.connect(self.connectToolMel)
            widget.edgeLoopToFromBtn.clicked.connect(self.edgeLoopToFromToolMel)
            widget.mergeCenterBtn.clicked.connect(self.mergeCenterToolMel)
            widget.mergeToVertBtn.clicked.connect(self.mergeToVertToolMel)
            widget.mergeToleranceBtn.clicked.connect(self.mergeToleranceToolMel)
            widget.collapseEdgeBtn.clicked.connect(self.collapseEdgeRingToolMel)
            widget.circularizeBtn.clicked.connect(self.circularizeToolMel)
            widget.spinBtn.clicked.connect(self.spinEdgeToolMel)
            widget.conformBtn.clicked.connect(self.conformToolMel)
            widget.averageBtn.clicked.connect(self.averageVerticesToolMel)
            # RIGHT CLICKS -----------------------
            # Extrude -----------------------
            widget.extrudeBtn.createMenuItem(text="Extrude (default)",
                                             icon=iconlib.icon(":polyExtrudeFacet", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.extrudeToolMel,
                                             mouseClick=QtCore.Qt.RightButton)
            widget.extrudeBtn.createMenuItem(text="Create NURBS Curve",
                                             icon=iconlib.icon(":curveCV", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.createCvCurveTool,
                                             mouseClick=QtCore.Qt.RightButton)
            # Bevel -----------------------
            widget.bevelBtn.createMenuItem(text="Bevel (default)",
                                           icon=iconlib.icon(":polyBevel", size=uic.MAYA_BTN_ICON_SIZE),
                                           connection=self.bevelToolMel,
                                           mouseClick=QtCore.Qt.RightButton)
            widget.bevelBtn.createMenuItem(text="Bevel Rounded Edge",
                                           icon=iconlib.icon(":polyBevel", size=uic.MAYA_BTN_ICON_SIZE),
                                           connection=self.bevelToolMelRounded,
                                           mouseClick=QtCore.Qt.RightButton)
            widget.bevelBtn.createMenuItem(text="Bevel Chamfer Off",
                                           icon=iconlib.icon(":polyBevel", size=uic.MAYA_BTN_ICON_SIZE),
                                           connection=self.bevelToolMelChamferOff,
                                           mouseClick=QtCore.Qt.RightButton)
            # Quad Draw -----------------------
            widget.quadDrawBtn.createMenuItem(text="Quad Draw (default)",
                                              icon=iconlib.icon(":quadDraw_NEX32", size=uic.MAYA_BTN_ICON_SIZE),
                                              connection=self.quadDrawToolMel,
                                              mouseClick=QtCore.Qt.RightButton)
            widget.quadDrawBtn.createMenuItem(text="Make Live (On Selected) > Quad Draw",
                                              icon=iconlib.icon(":makeLive", size=uic.MAYA_BTN_ICON_SIZE),
                                              connection=self.makeLiveMelQuadDraw,
                                              mouseClick=QtCore.Qt.RightButton)
            widget.quadDrawBtn.createMenuItem(text="Make Live (Off)",
                                              icon=iconlib.icon(":makeLive", size=uic.MAYA_BTN_ICON_SIZE),
                                              connection=self.makeLiveOffMel,
                                              mouseClick=QtCore.Qt.RightButton)
            # Conform -----------------------
            widget.conformBtn.createMenuItem(text="Conform Polygons (default)",
                                             icon=iconlib.icon(":polyNormalsConform", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.conformToolMel,
                                             mouseClick=QtCore.Qt.RightButton)
            widget.conformBtn.createMenuItem(text="Make Live (On Selected)  ",
                                             icon=iconlib.icon(":makeLive", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.makeLiveMel,
                                             mouseClick=QtCore.Qt.RightButton)
            widget.conformBtn.createMenuItem(text="Make Live (Off)",
                                             icon=iconlib.icon(":makeLive", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.makeLiveOffMel,
                                             mouseClick=QtCore.Qt.RightButton)
        # ADVANCED MODE -----------------------
        self.advancedWidget.fillHoleBtn.clicked.connect(self.fillHoleToolMel)
        self.advancedWidget.appendBtn.clicked.connect(self.appendToolMel)
        self.advancedWidget.wedgeBtn.clicked.connect(self.wedgeToolMel)
        self.advancedWidget.chamferVertexBtn.clicked.connect(self.chamferVertexToolMel)
        self.advancedWidget.offsetEdgeLoopBtn.clicked.connect(self.offsetEdgeLoopToolMel)
        self.advancedWidget.pokeBtn.clicked.connect(self.pokeToolMel)
        self.advancedWidget.deleteEdgeBtn.clicked.connect(self.deleteEdgeToolMel)
        self.advancedWidget.makeHoleBtn.clicked.connect(self.makeHoleToolMel)


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
        self.parent = parent
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        toolTipDict = tt.modelingToolbox()
        # CREATE ----------------------------------------------------------------------------------
        # maya btn ---------------------------------------
        self.extrudeBtn = self.mayaBtn("Extrude (Right-Click)", ":polyExtrudeFacet", toolTipDict["extrude"])
        # maya btn ---------------------------------------
        self.bevelBtn = self.mayaBtn("Bevel (Right-Click)", ":polyBevel", toolTipDict["bevel"])
        # maya btn ---------------------------------------
        self.bridgeBtn = self.mayaBtn("Bridge", ":polyBridge", toolTipDict["bridge"])
        # maya btn ---------------------------------------
        self.quadDrawBtn = self.mayaBtn("Quad Draw (Right Click)", ":quadDraw_NEX32", toolTipDict["quadDraw"])

        if uiMode == UI_MODE_ADVANCED:
            # maya btn ---------------------------------------
            self.appendBtn = self.mayaBtn("Append", ":polyAppendFacet", toolTipDict["append"])
            # maya btn ---------------------------------------
            self.fillHoleBtn = self.mayaBtn("Fill Hole", ":polyCloseBorder", toolTipDict["fillHole"])
            # maya btn ---------------------------------------
            self.wedgeBtn = self.mayaBtn("Wedge", ":polyWedgeFace", toolTipDict["wedge"])
            # maya btn ---------------------------------------
            self.chamferVertexBtn = self.mayaBtn("Chamfer Vertex", ":polyChamfer", toolTipDict["chamferVertex"])
        # CUT ----------------------------------------------------------------------------------
        # maya btn ---------------------------------------
        self.multicutBtn = self.mayaBtn("Multi Cut", ":multiCut_NEX32", toolTipDict["multiCut"])
        # maya btn ---------------------------------------
        self.edgeFlowBtn = self.mayaBtn("Edge Flow", ":polyEditEdgeFlow", toolTipDict["edgeFlow"])
        # maya btn ---------------------------------------
        self.edgeLoopToFromBtn = self.mayaBtn("Edge Loop To/From", ":polyLoopEdge", toolTipDict["edgeLoopToFrom"])
        if uiMode == UI_MODE_ADVANCED:
            # maya btn ---------------------------------------
            self.offsetEdgeLoopBtn = self.mayaBtn("Offset Edge Loop", ":polyLoopEdge", toolTipDict["offsetEdgeLoop"])
            # maya btn ---------------------------------------
            self.pokeBtn = self.mayaBtn("Poke", ":polyPoke", toolTipDict["poke"])
            # maya btn ---------------------------------------
            self.makeHoleBtn = self.mayaBtn("Make Hole", ":polyMergeFacet", toolTipDict["makeHole"])
        # REMOVE ----------------------------------------------------------------------------------
        # maya btn ---------------------------------------
        self.mergeCenterBtn = self.mayaBtn("Merge Center", ":polyMergeToCenter", toolTipDict["mergeCenter"])
        # maya btn ---------------------------------------
        self.mergeToVertBtn = self.mayaBtn("Merge To Vert", ":polyMergeVertex", toolTipDict["mergeToVert"])
        # maya btn ---------------------------------------
        self.mergeToleranceBtn = self.mayaBtn("Merge Tolerance", ":polyMerge", toolTipDict["mergeTolerance"])
        if uiMode == UI_MODE_ADVANCED:
            # maya btn ---------------------------------------
            self.deleteEdgeBtn = self.mayaBtn("Delete Edge", ":polyDelEdgeVertex", toolTipDict["deleteEdge"])
        # maya btn ---------------------------------------
        self.collapseEdgeBtn = self.mayaBtn("Collapse Edge Ring", ":polyCollapseEdge", toolTipDict["collapseEdgeRing"])
        # MISC HISTORY ----------------------------------------------------------------------------------
        # maya btn ---------------------------------------
        self.circularizeBtn = self.mayaBtn("Circularize", ":polyCollapseEdge", toolTipDict["circularize"])
        # maya btn ---------------------------------------
        self.spinBtn = self.mayaBtn("Spin Edge", ":polySpinEdgeForward", toolTipDict["spinEdge"])
        # maya btn ---------------------------------------
        self.averageBtn = self.mayaBtn("Average Vertices", ":polyAverageVertex", toolTipDict["averageVertices"])
        # maya btn ---------------------------------------
        self.conformBtn = self.mayaBtn("Conform (Right-Click)", ":polyNormalsConform", toolTipDict["conform"])
        # maya btn ---------------------------------------
        self.connectBtn = self.mayaBtn("Connect", ":connect_NEX32", toolTipDict["connect"])

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
                                         spacing=uic.SREG)

        # Grid Layout -----------------------------
        createAddLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        createAddLayout.addWidget(self.extrudeBtn, row, 0)
        createAddLayout.addWidget(self.bevelBtn, row, 1)
        row += 1
        createAddLayout.addWidget(self.quadDrawBtn, row, 0)
        createAddLayout.addWidget(self.bridgeBtn, row, 1)
        createAddLayout.setColumnStretch(0, 1)
        createAddLayout.setColumnStretch(1, 1)

        cutLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        cutLayout.addWidget(self.multicutBtn, row, 0)
        cutLayout.addWidget(self.edgeFlowBtn, row, 1)
        row += 1
        cutLayout.addWidget(self.connectBtn, row, 0)
        cutLayout.addWidget(self.edgeLoopToFromBtn, row, 1)
        cutLayout.setColumnStretch(0, 1)
        cutLayout.setColumnStretch(1, 1)

        mergeRemoveLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        mergeRemoveLayout.addWidget(self.mergeCenterBtn, row, 0)
        mergeRemoveLayout.addWidget(self.mergeToVertBtn, row, 1)
        row += 1
        mergeRemoveLayout.addWidget(self.mergeToleranceBtn, row, 0)
        mergeRemoveLayout.addWidget(self.collapseEdgeBtn, row, 1)
        mergeRemoveLayout.setColumnStretch(0, 1)
        mergeRemoveLayout.setColumnStretch(1, 1)

        miscLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        miscLayout.addWidget(self.circularizeBtn, row, 0)
        miscLayout.addWidget(self.spinBtn, row, 1)
        row += 1
        miscLayout.addWidget(self.averageBtn, row, 1)
        miscLayout.addWidget(self.conformBtn, row, 0)
        miscLayout.setColumnStretch(0, 1)
        miscLayout.setColumnStretch(1, 1)

        # Add To Main Layout ---------------------------------------
        # Modify Collapsable & Connections -------------------------------------
        createAddCollapsable = elements.CollapsableFrameThin("Create/Add (Faces)", collapsed=False)

        createAddCollapsable.hiderLayout.addLayout(createAddLayout)
        createAddCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        createAddCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        createAddCollapseLayout.addWidget(createAddCollapsable)

        # Utils Menu Collapsable & Connections -------------------------------------
        cutCollapsable = elements.CollapsableFrameThin("Cut", collapsed=False)

        cutCollapsable.hiderLayout.addLayout(cutLayout)
        cutCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        cutCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        cutCollapseLayout.addWidget(cutCollapsable)

        # Merge Remove -------------------------------------
        mergeCollapsable = elements.CollapsableFrameThin("Merge Remove", collapsed=False)

        mergeCollapsable.hiderLayout.addLayout(mergeRemoveLayout)
        mergeCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        mergeCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        mergeCollapseLayout.addWidget(mergeCollapsable)

        # Misc -------------------------------------
        misCollapsable = elements.CollapsableFrameThin("Misc", collapsed=False)

        misCollapsable.hiderLayout.addLayout(miscLayout)
        misCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        miscCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        miscCollapseLayout.addWidget(misCollapsable)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(createAddCollapseLayout)
        mainLayout.addLayout(cutCollapseLayout)
        mainLayout.addLayout(mergeCollapseLayout)
        mainLayout.addLayout(miscCollapseLayout)


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

        # Grid Layout -----------------------------
        createAddLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        createAddLayout.addWidget(self.extrudeBtn, row, 0)
        createAddLayout.addWidget(self.bevelBtn, row, 1)
        row += 1
        createAddLayout.addWidget(self.quadDrawBtn, row, 0)
        createAddLayout.addWidget(self.bridgeBtn, row, 1)
        row += 1
        createAddLayout.addWidget(self.fillHoleBtn, row, 0)
        createAddLayout.addWidget(self.appendBtn, row, 1)
        row += 1
        createAddLayout.addWidget(self.wedgeBtn, row, 0)
        createAddLayout.addWidget(self.chamferVertexBtn, row, 1)
        createAddLayout.setColumnStretch(0, 1)
        createAddLayout.setColumnStretch(1, 1)

        cutLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        cutLayout.addWidget(self.multicutBtn, row, 0)
        cutLayout.addWidget(self.edgeFlowBtn, row, 1)
        row += 1
        cutLayout.addWidget(self.connectBtn, row, 0)
        cutLayout.addWidget(self.edgeLoopToFromBtn, row, 1)
        row += 1
        cutLayout.addWidget(self.offsetEdgeLoopBtn, row, 0)
        cutLayout.addWidget(self.pokeBtn, row, 1)
        cutLayout.setColumnStretch(0, 1)
        cutLayout.setColumnStretch(1, 1)

        mergeRemoveLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        mergeRemoveLayout.addWidget(self.mergeCenterBtn, row, 0)
        mergeRemoveLayout.addWidget(self.mergeToVertBtn, row, 1)
        row += 1
        mergeRemoveLayout.addWidget(self.mergeToleranceBtn, row, 0)
        mergeRemoveLayout.addWidget(self.collapseEdgeBtn, row, 1)
        row += 1
        mergeRemoveLayout.addWidget(self.deleteEdgeBtn, row, 0)
        mergeRemoveLayout.addWidget(self.makeHoleBtn, row, 1)
        mergeRemoveLayout.setColumnStretch(0, 1)
        mergeRemoveLayout.setColumnStretch(1, 1)

        miscLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        miscLayout.addWidget(self.circularizeBtn, row, 0)
        miscLayout.addWidget(self.spinBtn, row, 1)
        row += 1
        miscLayout.addWidget(self.averageBtn, row, 1)
        miscLayout.addWidget(self.conformBtn, row, 0)
        miscLayout.setColumnStretch(0, 1)
        miscLayout.setColumnStretch(1, 1)

        # Add To Main Layout ---------------------------------------
        # Modify Collapsable & Connections -------------------------------------
        createAddCollapsable = elements.CollapsableFrameThin("Create/Add (Faces)", collapsed=False)

        createAddCollapsable.hiderLayout.addLayout(createAddLayout)
        createAddCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        createAddCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        createAddCollapseLayout.addWidget(createAddCollapsable)

        # Utils Menu Collapsable & Connections -------------------------------------
        cutCollapsable = elements.CollapsableFrameThin("Cut", collapsed=False)

        cutCollapsable.hiderLayout.addLayout(cutLayout)
        cutCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        cutCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        cutCollapseLayout.addWidget(cutCollapsable)

        # Merge Remove -------------------------------------
        mergeCollapsable = elements.CollapsableFrameThin("Merge Remove", collapsed=False)

        mergeCollapsable.hiderLayout.addLayout(mergeRemoveLayout)
        mergeCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        mergeCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        mergeCollapseLayout.addWidget(mergeCollapsable)

        # Misc -------------------------------------
        misCollapsable = elements.CollapsableFrameThin("Misc", collapsed=False)

        misCollapsable.hiderLayout.addLayout(miscLayout)
        misCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        miscCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        miscCollapseLayout.addWidget(misCollapsable)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(createAddCollapseLayout)
        mainLayout.addLayout(cutCollapseLayout)
        mainLayout.addLayout(mergeCollapseLayout)
        mainLayout.addLayout(miscCollapseLayout)
