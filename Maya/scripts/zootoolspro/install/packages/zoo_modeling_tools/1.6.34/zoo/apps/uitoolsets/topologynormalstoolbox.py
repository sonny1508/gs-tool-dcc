""" ---------- Topology And Normal Toolbox (Multiple UI Modes) -------------

"""

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output
from zoovendor.Qt import QtWidgets
from zoo.libs.maya.cmds.hotkeys import definedhotkeys
from zoo.apps.tooltips import modelingtooltips as tt
from zoo.libs.maya.utils import mayaenv

MAYA_VERSION = mayaenv.mayaVersion()

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class TopologyNormalsToolbox(toolsetwidget.ToolsetWidget):
    id = "topologyNormalsToolbox"
    info = "Maya topology and normals tools and hotkey trainer."
    uiData = {"label": "Topology And Normals Toolbox",
              "icon": "grid",
              "tooltip": "Maya topology and normals tools and hotkey trainer.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-topology-and-normals-toolbox/"}

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
        return super(TopologyNormalsToolbox, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(TopologyNormalsToolbox, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def smoothMeshDisplayOnMel(self):
        definedhotkeys.smoothMeshDisplayOnMel()

    def smoothMeshDisplayHullMel(self):
        definedhotkeys.smoothMeshDisplayHullMel()

    def smoothMeshDisplayOffMel(self):
        definedhotkeys.smoothMeshDisplayOffMel()

    def smoothMeshPreviewToPolygonsMel(self):
        definedhotkeys.smoothMeshPreviewToPolygonsMel()
        definedhotkeys.smoothMeshPreviewToPolygonsMel()

    def open_subDSmoothControl(self):
        definedhotkeys.open_subDSmoothControl()

    def smoothPolyMel(self):
        definedhotkeys.smoothPolyMel()

    def smoothMeshPreviewToPolygonsMel(self):
        definedhotkeys.smoothMeshPreviewToPolygonsMel()

    def divideMel(self):
        definedhotkeys.divideMel()

    def retopologizeMel(self):
        definedhotkeys.retopologizeMel()

    def retopologizeOptionsMel(self):
        definedhotkeys.retopologizeOptionsMel()

    def remeshMel(self):
        definedhotkeys.remeshMel()

    def remeshOptionsMel(self):
        definedhotkeys.remeshOptionsMel()

    def reduceMel(self):
        definedhotkeys.reduceMel()

    def reduceOptionsMel(self):
        definedhotkeys.reduceOptionsMel()

    def unSmoothMel(self):
        if MAYA_VERSION < 2024:
            output.displayWarning("The Unsmooth Tool is only available in Maya 2024 and above. ")
            return
        definedhotkeys.unSmoothMel()

    def unSmoothOptionsMel(self):
        if MAYA_VERSION < 2024:
            output.displayWarning("The Unsmooth Tool is only available in Maya 2024 and above. ")
            return
        definedhotkeys.unSmoothOptionsMel()

    def triangulateMel(self):
        definedhotkeys.triangulateMel()

    def quadragulateMel(self):
        definedhotkeys.quadragulateMel()

    def creaseToolMel(self):
        definedhotkeys.creaseToolMel()

    def uncreaseAll(self):
        definedhotkeys.uncreaseAll()

    def selectCreasedEdges(self):
        definedhotkeys.selectCreasedEdges()

    def spinEdgeMel(self):
        definedhotkeys.spinEdgeMel()

    # -------------------
    # NORMALS
    # -------------------

    def softenEdgesMel(self):
        definedhotkeys.softenEdgesMel()

    def hardenEdgesMel(self):
        definedhotkeys.hardenEdgesMel()

    def unlockVertexNormalsMel(self):
        definedhotkeys.unlockVertexNormalsMel()

    def lockVertexNormalsMel(self):
        definedhotkeys.lockVertexNormalsMel()

    def conformFaceNormalsMel(self):
        definedhotkeys.conformFaceNormalsMel()

    def reverseFaceNormalsMel(self):
        definedhotkeys.reverseFaceNormalsMel()

    def averageVertexNormalsMel(self):
        definedhotkeys.averageVertexNormalsMel()

    def vertexNormalToolMel(self):
        definedhotkeys.vertexNormalToolMel()

    def transferVertexNormalsWorld(self):
        definedhotkeys.transferVertexNormalsWorld()

    def transferVertexNormalsLocal(self):
        definedhotkeys.transferVertexNormalsLocal()

    def transferVertexNormalsUv(self):
        definedhotkeys.transferVertexNormalsUv()

    def transferVertexNormalsComponent(self):
        definedhotkeys.transferVertexNormalsComponent()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        browserIcon = iconlib.iconColorized("windowBrowser", color=uic.DEFAULT_ICON_COLOR)
        for widget in self.widgets():  # Both UI Modes
            # Create Objects -----------------------
            widget.polySmoothBtn.clicked.connect(self.smoothPolyMel)
            widget.divideBtn.clicked.connect(self.divideMel)
            widget.retopologizeBtn.clicked.connect(self.retopologizeMel)
            widget.remeshBtn.clicked.connect(self.remeshMel)
            widget.reduceBtn.clicked.connect(self.reduceMel)
            widget.unsmoothBtn.clicked.connect(self.unSmoothMel)
            widget.triangulateBtn.clicked.connect(self.triangulateMel)
            widget.quadrangulateBtn.clicked.connect(self.quadragulateMel)
            # Normals ------------------------------
            widget.softNormalsBtn.clicked.connect(self.softenEdgesMel)
            widget.hardNormalsBtn.clicked.connect(self.hardenEdgesMel)
            widget.reverseNormalsBtn.clicked.connect(self.reverseFaceNormalsMel)
            widget.conformNormalsBtn.clicked.connect(self.conformFaceNormalsMel)
            # Right Click Menus --------------------
            # retopology ------------------
            widget.retopologizeBtn.createMenuItem(text="Retopology (Default)",
                                                  icon=iconlib.icon(":polyRetopo"),
                                                  connection=self.retopologizeMel)
            widget.retopologizeBtn.createMenuItem(text="Retopology (Options Window)",
                                                  icon=browserIcon,
                                                  connection=self.retopologizeOptionsMel)
            # remesh ----------------------
            widget.remeshBtn.createMenuItem(text="Remesh (Default)",
                                            icon=iconlib.icon(":polyRemesh"),
                                            connection=self.remeshMel)
            widget.remeshBtn.createMenuItem(text="Remesh (Options Window)",
                                            icon=browserIcon,
                                            connection=self.remeshOptionsMel)
            # reduce ----------------------
            widget.reduceBtn.createMenuItem(text="Reduce (Default)",
                                            icon=iconlib.icon(":polyReduce"),
                                            connection=self.reduceMel)
            widget.reduceBtn.createMenuItem(text="Reduce (Options Window)",
                                            icon=browserIcon,
                                            connection=self.reduceOptionsMel)
        # ADVANCED MODE -----------------------
        self.advancedWidget.subDSmoothOnBtn.clicked.connect(self.smoothMeshDisplayOnMel)
        self.advancedWidget.subDSmoothOffBtn.clicked.connect(self.smoothMeshDisplayOffMel)
        self.advancedWidget.creaseBtn.clicked.connect(self.creaseToolMel)
        self.advancedWidget.spinBtn.clicked.connect(self.spinEdgeMel)
        self.advancedWidget.unlockNormalsBtn.clicked.connect(self.unlockVertexNormalsMel)
        self.advancedWidget.averageNormalsBtn.clicked.connect(self.averageVertexNormalsMel)
        self.advancedWidget.normalToolBtn.clicked.connect(self.vertexNormalToolMel)
        self.advancedWidget.transferVertNormalsBtn.clicked.connect(self.transferVertexNormalsWorld)
        # Right Click Menus --------------------
        # SubD Smooth ------------------
        self.advancedWidget.subDSmoothOnBtn.createMenuItem(text="Smooth Mesh On (Default)",
                                                           icon=iconlib.iconColorized("sphere",
                                                                                      color=uic.DEFAULT_ICON_COLOR),
                                                           connection=self.smoothMeshDisplayOnMel)
        self.advancedWidget.subDSmoothOnBtn.createMenuItem(text="Smooth Mesh Hull",
                                                           icon=iconlib.iconColorized("menu_cube", color=uic.DEFAULT_ICON_COLOR),
                                                           connection=self.smoothMeshDisplayHullMel)
        self.advancedWidget.subDSmoothOnBtn.createMenuItem(text="Smooth Mesh Off",
                                                           icon=iconlib.iconColorized("cubeWire",
                                                                                      color=uic.DEFAULT_ICON_COLOR),
                                                           connection=self.smoothMeshDisplayOffMel)
        self.advancedWidget.subDSmoothOnBtn.createMenuItem(text="Smooth Mesh Preview To Polygons",
                                                           icon=iconlib.icon(":meshToPolygons"),
                                                           connection=self.smoothMeshPreviewToPolygonsMel)
        self.advancedWidget.subDSmoothOnBtn.createMenuItem(text="Open SubD Smooth Control",
                                                           icon=iconlib.iconColorized("windowBrowser", color=uic.DEFAULT_ICON_COLOR),
                                                           connection=self.open_subDSmoothControl)
        # Crease -----------------------
        self.advancedWidget.creaseBtn.createMenuItem(text="Crease Tool (Default)",
                                                     icon=iconlib.icon(":polyCrease", size=uic.MAYA_BTN_ICON_SIZE),
                                                     connection=self.creaseToolMel)
        self.advancedWidget.creaseBtn.createMenuItem(text="Remove Creases (Delete Crease Node/s)",
                                                     icon=iconlib.icon(":polyCrease"),
                                                     connection=self.uncreaseAll)
        self.advancedWidget.creaseBtn.createMenuItem(text="Select Creased Edges",
                                                     icon=iconlib.icon(":polyCrease"),
                                                     connection=self.selectCreasedEdges)
        # unlock vertex normals -------
        self.advancedWidget.unlockNormalsBtn.createMenuItem(text="Unlock Normals (Default)",
                                                            icon=iconlib.icon(":polyNormalUnlock"),
                                                            connection=self.creaseToolMel)
        self.advancedWidget.unlockNormalsBtn.createMenuItem(text="Lock Normals",
                                                            icon=iconlib.icon(":polyNormalUnlock"),
                                                            connection=self.uncreaseAll)
        # unlock vertex normals -------
        self.advancedWidget.transferVertNormalsBtn.createMenuItem(text="Transfer Normals World (Default)",
                                                                  icon=iconlib.icon(":polyNormalSetToFace"),
                                                                  connection=self.transferVertexNormalsWorld)
        self.advancedWidget.transferVertNormalsBtn.createMenuItem(text="Transfer Normals Local",
                                                                  icon=iconlib.icon(":polyNormalSetToFace"),
                                                                  connection=self.transferVertexNormalsLocal)
        self.advancedWidget.transferVertNormalsBtn.createMenuItem(text="Transfer Normals UV",
                                                                  icon=iconlib.icon(":polyNormalSetToFace"),
                                                                  connection=self.transferVertexNormalsUv)
        self.advancedWidget.transferVertNormalsBtn.createMenuItem(text="Transfer Normals Component",
                                                                  icon=iconlib.icon(":polyNormalSetToFace"),
                                                                  connection=self.transferVertexNormalsComponent)


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
        self.parent = parent
        self.properties = properties
        toolTipDict = tt.topologyAndNormalsToolbox()
        # TOPOLOGY ----------------------------------------------------------------------------------
        if uiMode == UI_MODE_ADVANCED:
            # zoo btn ---------------------------------------
            self.subDSmoothOnBtn = self.zooBtn("Smooth On (Right-Click)", "sphere", toolTipDict["subDSmoothOn"])
            # zoo btn ---------------------------------------
            self.subDSmoothOffBtn = self.zooBtn("Smooth Mesh Off", "cubeWire", toolTipDict["subDSmoothOff"])
        # maya btn---------------------------------------
        self.polySmoothBtn = self.mayaBtn("Poly Smooth", ":polySmooth", toolTipDict["polySmooth"])
        # maya btn---------------------------------------
        self.divideBtn = self.mayaBtn("Divide", ":polySmooth", toolTipDict["divide"])
        # maya btn---------------------------------------
        self.retopologizeBtn = self.mayaBtn("Retopologize (Right-Click)", ":polyRetopo", toolTipDict["retopologize"])
        # maya btn---------------------------------------
        txtLabel = "Un-Smooth"
        if MAYA_VERSION < 2024:
            txtLabel = "Un-Smooth (2024 Only)"
        self.unsmoothBtn = self.mayaBtn(txtLabel, ":polySmooth", toolTipDict["unSmooth"])
        # maya btn---------------------------------------
        self.reduceBtn = self.mayaBtn("Reduce (Right-Click)", ":polyReduce", toolTipDict["reduce"])
        # maya btn---------------------------------------
        self.triangulateBtn = self.mayaBtn("Triangulate", ":polyTriangulate", toolTipDict["triangulate"])
        # maya btn---------------------------------------
        self.quadrangulateBtn = self.mayaBtn("Quadrangulate", ":polyQuad", toolTipDict["quadrangulate"])
        # maya btn---------------------------------------
        self.remeshBtn = self.mayaBtn("Remesh (Right-Click)", ":polyRemesh", toolTipDict["remesh"])
        if MAYA_VERSION < 2020:
            self.retopologizeBtn.setVisible(False)
            self.remeshBtn.setVisible(False)
        if uiMode == UI_MODE_ADVANCED:
            # maya btn---------------------------------------
            self.creaseBtn = self.mayaBtn("Crease SubD ( Right-click )", ":polyCrease", toolTipDict["creaseSubD"])
            # maya btn---------------------------------------
            self.spinBtn = self.mayaBtn("Spin Edge", ":polySpinEdgeForward", toolTipDict["spinEdge"])
        # NORMALS ----------------------------------------------------------------------------------
        self.softNormalsBtn = self.mayaBtn("Soften Edges (V Normals)", ":polySoftEdge", toolTipDict["softenEdges"])
        # maya btn---------------------------------------
        self.hardNormalsBtn = self.mayaBtn("Harden Edges (V Normals)", ":polyHardEdge", toolTipDict["hardenEdges"])
        # maya btn---------------------------------------
        self.conformNormalsBtn = self.mayaBtn("Conform Face Normals", ":polyNormalsConform",
                                              toolTipDict["conformFaceNormals"])
        # maya btn---------------------------------------
        self.reverseNormalsBtn = self.mayaBtn("Reverse Face Normals", ":polyNormal", toolTipDict["reverseFaceNormals"])
        if uiMode == UI_MODE_ADVANCED:
            # maya btn---------------------------------------
            self.unlockNormalsBtn = self.mayaBtn("Unlock Vert Normals (RC)", ":polyNormalUnlock",
                                                 toolTipDict["unlockVertexNormals"])
            # maya btn---------------------------------------
            self.averageNormalsBtn = self.mayaBtn("Average Vertex Normals", ":polyNormalAverage",
                                                  toolTipDict["averageVertexNormals"])
            # maya btn---------------------------------------
            self.normalToolBtn = self.mayaBtn("Vertex Normal Tool", ":polyNormalSetAngle",
                                              toolTipDict["vertexNormalTool"])
            # maya btn---------------------------------------
            self.transferVertNormalsBtn = self.mayaBtn("Transfer Vert Nrml (RC)", ":polyNormalSetToFace",
                                                       toolTipDict["transferVertexNormals"])

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
                                         spacing=uic.SREG)
        # Grid Layout -----------------------------
        topologyLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        topologyLayout.addWidget(self.polySmoothBtn, row, 0)
        topologyLayout.addWidget(self.divideBtn, row, 1)
        row += 1
        topologyLayout.addWidget(self.unsmoothBtn, row, 0)
        topologyLayout.addWidget(self.reduceBtn, row, 1)
        row += 1
        topologyLayout.addWidget(self.retopologizeBtn, row, 0)
        topologyLayout.addWidget(self.remeshBtn, row, 1)
        row += 1
        topologyLayout.addWidget(self.triangulateBtn, row, 0)
        topologyLayout.addWidget(self.quadrangulateBtn, row, 1)

        # Grid Layout -----------------------------
        normalsLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        normalsLayout.addWidget(self.conformNormalsBtn, row, 0)
        normalsLayout.addWidget(self.reverseNormalsBtn, row, 1)
        row += 1
        normalsLayout.addWidget(self.softNormalsBtn, row, 0)
        normalsLayout.addWidget(self.hardNormalsBtn, row, 1)

        normalsLayout.setColumnStretch(0, 1)
        normalsLayout.setColumnStretch(1, 1)

        # Modify Collapsable & Connections -------------------------------------
        topologyCollapsable = elements.CollapsableFrameThin("Topology", collapsed=False)

        topologyCollapsable.hiderLayout.addLayout(topologyLayout)
        topologyCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        topologyCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        topologyCollapseLayout.addWidget(topologyCollapsable)

        # Utils Menu Collapsable & Connections -------------------------------------
        normalsCollapsable = elements.CollapsableFrameThin("Face & Vertex Normals", collapsed=False)

        normalsCollapsable.hiderLayout.addLayout(normalsLayout)
        normalsCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        normalsCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        normalsCollapseLayout.addWidget(normalsCollapsable)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(topologyCollapseLayout)
        mainLayout.addLayout(normalsCollapseLayout)


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
        topologyLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        topologyLayout.addWidget(self.subDSmoothOffBtn, row, 0)
        topologyLayout.addWidget(self.subDSmoothOnBtn, row, 1)
        row += 1
        topologyLayout.addWidget(self.polySmoothBtn, row, 0)
        topologyLayout.addWidget(self.divideBtn, row, 1)
        row += 1
        topologyLayout.addWidget(self.unsmoothBtn, row, 0)
        topologyLayout.addWidget(self.reduceBtn, row, 1)
        row += 1
        topologyLayout.addWidget(self.retopologizeBtn, row, 0)
        topologyLayout.addWidget(self.remeshBtn, row, 1)
        row += 1
        topologyLayout.addWidget(self.triangulateBtn, row, 0)
        topologyLayout.addWidget(self.quadrangulateBtn, row, 1)
        row += 1
        topologyLayout.addWidget(self.creaseBtn, row, 0)
        topologyLayout.addWidget(self.spinBtn, row, 1)

        # Grid Layout -----------------------------
        normalsLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        normalsLayout.addWidget(self.conformNormalsBtn, row, 0)
        normalsLayout.addWidget(self.reverseNormalsBtn, row, 1)
        row += 1
        normalsLayout.addWidget(self.softNormalsBtn, row, 0)
        normalsLayout.addWidget(self.hardNormalsBtn, row, 1)
        row += 1
        normalsLayout.addWidget(self.unlockNormalsBtn, row, 0)
        normalsLayout.addWidget(self.averageNormalsBtn, row, 1)
        row += 1
        normalsLayout.addWidget(self.normalToolBtn, row, 0)
        normalsLayout.addWidget(self.transferVertNormalsBtn, row, 1)

        normalsLayout.setColumnStretch(0, 1)
        normalsLayout.setColumnStretch(1, 1)

        # Modify Collapsable & Connections -------------------------------------
        topologyCollapsable = elements.CollapsableFrameThin("Topology", collapsed=False)

        topologyCollapsable.hiderLayout.addLayout(topologyLayout)
        topologyCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        topologyCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        topologyCollapseLayout.addWidget(topologyCollapsable)

        # Utils Menu Collapsable & Connections -------------------------------------
        normalsCollapsable = elements.CollapsableFrameThin("Face & Vertex Normals", collapsed=False)

        normalsCollapsable.hiderLayout.addLayout(normalsLayout)
        normalsCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        normalsCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        normalsCollapseLayout.addWidget(normalsCollapsable)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(topologyCollapseLayout)
        mainLayout.addLayout(normalsCollapseLayout)
