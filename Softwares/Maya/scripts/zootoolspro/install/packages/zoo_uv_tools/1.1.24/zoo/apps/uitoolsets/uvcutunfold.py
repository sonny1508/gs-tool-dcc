from functools import partial

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.utils import output

from zoo.libs.maya.cmds.objutils import uvtransfer
from zoo.libs.maya.cmds.uvs import uvmacros, uvfunctions
from maya import cmds

DISPLAY_MODES = uvfunctions.DISPLAY_MODES
UNFOLD_PLUGIN_NAME = uvfunctions.UNFOLD_PLUGIN_NAME

UI_MODE_COMPACT = 0
UI_MODE_MEDIUM = 1
UI_MODE_ADVANCED = 2
IMAGE_SIZES = ["32", "64", "128", "256", "512", "1024", "2048", "4096", "8192", "16384"]
IMAGE_SIZE_LABELS = ["Texture Size: 32", "Texture Size: 64", "Texture Size: 128", "Texture Size: 256",
                     "Texture Size: 512", "Texture Size: 1024", "Texture Size: 2048", "Texture Size: 4096",
                     "Texture Size: 8192", "Texture Size: 16384"]


class UvCutUnfold(toolsetwidget.ToolsetWidget):
    """Primary UV tools for cutting, projecting and unfolding.
    """
    id = "uvUnfold"
    uiData = {"label": "UV Toolbox",
              "icon": "unfold",
              "tooltip": "Primary UV tools for cutting, projecting and unfolding.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-uv-cut-unfold/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initmediumWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initmediumWidget(self):
        """Builds the Advanced GUI (self.mediumWidget) """
        self.mediumWidget = GuiMedium(parent=self, properties=self.properties, toolsetWidget=self)
        return self.mediumWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()
        self.toggleDisableEnable()  # auto set the disable values of all widgets

    def defaultAction(self):
        """Double Click"""
        pass

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  GuiWidgets
        """
        return super(UvCutUnfold, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(UvCutUnfold, self).widgets()

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Used to store and update UI data

        properties are auto-linked if the name matches the widget name

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [{"name": "delHistoryCheckBox", "value": False},
                {"name": "imageSizeCombo", "value": 2},
                {"name": "autoSeamUnfoldSlider", "value": 0.0}]

    def saveProperties(self):
        """Saves properties, keeps self.properties up to date with every widget change
        Overridden function which automates properties updates. Exposed here in case of extra functionality.

        properties are auto-linked if the name matches the widget name
        """
        super(UvCutUnfold, self).saveProperties()
        self.toggleDisableEnable()  # disable or enable widgets

    # ------------------
    # RIGHT CLICKS
    # ------------------

    def actions(self):
        """Right click menu and actions
        """
        return [
            {"type": "action",
             "name": "uv",
             "label": "Transfer UVs",
             "icon": "transferUVs",
             "tooltip": ""},
            {"type": "action",
             "name": "shader",
             "label": "Transfer Shader",
             "icon": "transferUVs",
             "tooltip": ""},
            {"type": "action",
             "name": "uv_shader",
             "label": "Transfer UVs & Shaders",
             "icon": "transferUVs",
             "tooltip": ""}
        ]

    @toolsetwidget.ToolsetWidget.undoDecorator
    def executeActions(self, action):
        """Right click actions on the main toolset icon

        :param action:
        :type action:
        """
        name = action['name']
        if name == "uv":
            uvtransfer.transferSelected(transferUvs=True, transferShader=False)
        elif name == "shader":
            uvtransfer.transferSelected(transferUvs=False, transferShader=True)
        elif name == "uv_shader":
            uvtransfer.transferSelected(transferUvs=True, transferShader=True)

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def loadUnfoldPlugin(self):
        message = "The Unfold 3d plugin is not loaded. Load now?"
        # parent is None to parent to Maya to fix stylesheet issues
        okPressed = elements.MessageBox.showOK(title="Load Unfold 3d Plugin", parent=None, message=message)
        return okPressed

    # ------------------
    # DISABLE/ENABLE WIDGETS
    # ------------------

    def toggleDisableEnable(self):
        """Will disable the name textbox with the autoName checkbox is off"""
        pass

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def openUvEditor(self):
        displayStyle = DISPLAY_MODES[self.properties.displayCombo.value]
        uvfunctions.openUVEditor(displayStyle=displayStyle)

    def setDisplayMode(self, index):
        displayStyle = DISPLAY_MODES[self.properties.displayCombo.value]
        uvfunctions.uvDisplayModePresets(displayStyle=displayStyle)

    def planarProjectionCamera(self):
        uvmacros.planarProjectionCamera()  # repeat and undo decorator

    def planarProjectionBestPlane(self):
        uvmacros.planarProjectionBestPlane()  # repeat and undo decorator

    def cutUVs(self):
        uvmacros.cutUVs()  # repeat and undo decorator

    def cutPerimeterUVs(self):
        uvmacros.cutPerimeterUVs()  # repeat and undo decorator

    def sewUVs(self):
        uvmacros.sewUVs()  # repeat and undo decorator

    @toolsetwidget.ToolsetWidget.undoDecorator
    def cutAndSewTool3d(self):
        uvfunctions.cutAndSewTool3d()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def autoSeamsUnfold(self):
        splitShells = self.properties.autoSeamUnfoldSlider.value
        mapSize = int(IMAGE_SIZES[self.properties.imageSizeCombo.value])
        uvfunctions.autoSeamsUnfoldSelection(splitShells=splitShells, cutPipes=1, select=1, mapSize=mapSize)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def unfoldUVs(self):
        # Check plugin has loaded
        loaded = cmds.pluginInfo(UNFOLD_PLUGIN_NAME, query=True, loaded=True)
        if not loaded:
            okPressed = self.loadUnfoldPlugin()
            if okPressed:
                cmds.loadPlugin(UNFOLD_PLUGIN_NAME)
                output.displayInfo("Please run the unfold tool now the plugin has loaded")
                return
            return
        # Run
        mapSize = int(IMAGE_SIZES[self.properties.imageSizeCombo.value])
        uvfunctions.regularUnfoldSelectionPackOption(mapsize=mapSize, roomspace=1)  # packs if in object mode

    @toolsetwidget.ToolsetWidget.undoDecorator
    def unfoldUVsDirection(self, dirType="horizontal"):
        uvfunctions.legacyUnfoldSelection(dirType=dirType)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def edgeUnwrapTube(self, mode="tube"):
        """Does the edge selection Tube Unwrap
        Select a single edge that is the seam for a tube and run.
        """
        if mode == "tube":
            uvmacros.unwrapTubeSelection(dirType="automatic",
                                         straightenLoops=True,
                                         unfold=True,
                                         straightenAngle=80,
                                         deleteHistory=self.properties.delHistoryCheckBox.value)
        else:
            uvmacros.unwrapGridShellSelection(dirType="automatic",
                                              straightenLoops=True,
                                              unfold=True,
                                              straightenAngle=80,
                                              deleteHistory=self.properties.delHistoryCheckBox.value)

    def symmetryBrush(self):
        uvmacros.symmetryBrush()  # repeat and undo decorator

    def orientToEdge(self):
        uvmacros.orientToEdge()  # repeat and undo decorator

    def orientToShell(self):
        uvmacros.orientToShell()  # repeat and undo decorator

    @toolsetwidget.ToolsetWidget.undoDecorator
    def layoutUvs(self):
        mapSize = int(IMAGE_SIZES[self.properties.imageSizeCombo.value])
        uvfunctions.layoutUvs(resolution=mapSize)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        for widget in self.widgets():
            widget.openUvBtn.clicked.connect(self.openUvEditor)
            widget.displayCombo.currentIndexChanged.connect(self.setDisplayMode)
            widget.planarProjCamBtn.clicked.connect(self.planarProjectionCamera)
            widget.unfoldBtn.clicked.connect(self.unfoldUVs)
            widget.cutSewToolBtn.clicked.connect(self.cutAndSewTool3d)
            widget.layoutBtn.clicked.connect(self.layoutUvs)
            widget.cutBtn.clicked.connect(self.cutUVs)
            widget.sewBtn.clicked.connect(self.sewUVs)
            widget.symmetryBrushBtn.clicked.connect(self.symmetryBrush)
            widget.orientEdgeBtn.clicked.connect(self.orientToEdge)
            widget.orientShellBtn.clicked.connect(self.orientToShell)
        # Medium
        self.mediumWidget.planarProjAutoBtn.clicked.connect(self.planarProjectionBestPlane)
        self.mediumWidget.unfoldTubeBtn.clicked.connect(partial(self.edgeUnwrapTube, mode="tube"))
        self.mediumWidget.unfoldGridBtn.clicked.connect(partial(self.edgeUnwrapTube, mode="grid"))
        self.mediumWidget.cutPerimeterBtn.clicked.connect(self.cutPerimeterUVs)
        self.mediumWidget.autoSeamUnfoldBtn.clicked.connect(self.autoSeamsUnfold)
        self.mediumWidget.unfoldHorizontalBtn.clicked.connect(partial(self.unfoldUVsDirection, dirType="horizontal"))
        self.mediumWidget.unfoldVerticalBtn.clicked.connect(partial(self.unfoldUVsDirection, dirType="vertical"))


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Open UV Editor Button ---------------------------------------
        toolTip = "Open Maya's UV Editor"
        self.openUvBtn = elements.AlignedButton("Open UV Editor",
                                                icon="uvEditor",
                                                toolTip=toolTip)
        # Display Combobox -----------------------------------------------------
        toolTip = "Change the UV display mode of the UV Editor \n" \
                  "Use 'middle-scroll' to quickly cycle through modes. \n" \
                  "Note: Presets may act unexpectedly due to Maya code issues."
        self.displayCombo = elements.ComboBoxRegular(label="",
                                                     items=DISPLAY_MODES,
                                                     toolTip=toolTip,
                                                     setIndex=2)
        # Planar Proj Camera Button ---------------------------------------
        toolTip = "Planar UV maps from the current camera. \n" \
                  "Click the channel box node in input history and press `T` \n" \
                  "to show the UV manipulator."
        self.planarProjCamBtn = elements.AlignedButton("Planar Projection Camera",
                                                       icon="planarCamera",
                                                       toolTip=toolTip)
        # 3d Cut And Sew Button ---------------------------------------
        toolTip = "Mayas 3d Cut and Sew Tool. \n\n" \
                  "  LMB - Cut by dragging along edges \n" \
                  "  Double Click - Cuts edgeloop \n" \
                  "  Ctrl LMB - Sew along edges \n" \
                  "  Shift Drag - Grows an edge loop \n" \
                  "  Shift Double Click - Cut to second edge \n" \
                  "  Tab - Highlights edgeloops \n" \
                  "  X - Cut highlighted edges \n" \
                  "  S - Sew highlighted edges \n" \
                  "  Right Click - Exit tool and marking menu"
        self.cutSewToolBtn = elements.AlignedButton("3d Cut/Sew Tool",
                                                    icon="knife",
                                                    toolTip=toolTip)
        # Unfold Main Button ---------------------------------------
        toolTip = "Unfold with Maya's Unfold 3d plugin. \n" \
                  "Also runs layout if not in component selection. \n" \
                  "Layout uses Texture Size to add 2 pixels between shells."
        self.unfoldBtn = elements.AlignedButton("Unfold",
                                                icon="unfold",
                                                toolTip=toolTip)
        # Layout Main Button ---------------------------------------
        toolTip = "Layout (Pack) objects into 0-1 UV space. \n" \
                  "Uses Texture Size to add 2 pixels between shells. \n" \
                  "Increasing Texture Size slows the pack calculation."
        self.layoutBtn = elements.AlignedButton("Layout",
                                                icon="layout",
                                                toolTip=toolTip)
        # Cut Button ---------------------------------------
        toolTip = "UV cuts edge selection, select edges and run."
        self.cutBtn = elements.AlignedButton("Cut",
                                             icon="cut",
                                             toolTip=toolTip)
        # Paste Button ---------------------------------------
        toolTip = "UV sews edge selection (opposite of cut), select cut edges and run."
        self.sewBtn = elements.AlignedButton("Sew",
                                             icon="sew",
                                             toolTip=toolTip)
        # Symmetry Brush Button ---------------------------------------
        toolTip = "Symmetry Brush mirrors shells with a brush paint. \n" \
                  "Zoo version automatically finds the shell symmetry direction and pivot \n" \
                  " - Select a shell center edge, and run the tool. \n" \
                  " - Select the same edge again and paint."
        self.symmetryBrushBtn = elements.AlignedButton("Symmetry Brush",
                                                       icon="symmetryTri",
                                                       toolTip=toolTip)
        # Orient To Edges Button ---------------------------------------
        toolTip = "Orient whole shell by selecting an edge. \n" \
                  "Will orient the whole shell so the edge becomes straight. \n" \
                  "- Select an edge and run."
        self.orientEdgeBtn = elements.AlignedButton("Orient To Edges",
                                                    icon="orientEdge",
                                                    toolTip=toolTip)
        # Image Size Combobox -----------------------------------------------------
        toolTip = "Texture size adjust Layout packing. \n" \
                  "Will add 2 pixels relative to the texture size between shells. \n" \
                  "Increasing Texture Size slows the pack calculation."
        self.imageSizeCombo = elements.ComboBoxRegular(label="",
                                                       items=IMAGE_SIZE_LABELS,
                                                       toolTip=toolTip,
                                                       setIndex=5,
                                                       boxRatio=7,
                                                       labelRatio=9)
        # Orient To Shells Button ---------------------------------------
        toolTip = "Orient shells automatically. \n" \
                  "Select an object or UV shell and run."
        self.orientShellBtn = elements.AlignedButton("Auto Orient Shells",
                                                     icon="orientShell",
                                                     toolTip=toolTip)
        if uiMode == UI_MODE_MEDIUM:
            # Planar Proj Camera Button ---------------------------------------
            toolTip = "Planar UV maps while keeping to the 'average normal' of the current selection. \n" \
                      "Usually used with face selection. \n" \
                      "Click the channel box node in input history and press `T` \n" \
                      "to show the UV manipulator."
            self.planarProjAutoBtn = elements.AlignedButton("Planar Projection Auto",
                                                            icon="planarAuto",
                                                            toolTip=toolTip)

            # Cut Border Button ---------------------------------------
            toolTip = "Cuts around the perimeter of the selection, usually a face selection."
            self.cutPerimeterBtn = elements.AlignedButton("Cut Perimeter",
                                                          icon="cutPerimeter",
                                                          toolTip=toolTip)
            # Auto Unfold Button ---------------------------------------
            toolTip = "Creates seams automatically on an object, also runs unfold and layout. \n" \
                      "Use the slider to create more seams."
            # Select Animated Nodes Button --------------------------
            self.autoSeamUnfoldBtn = elements.styledButton("",
                                                           icon="autoUnfold",
                                                           toolTip=toolTip,
                                                           minWidth=uic.BTN_W_ICN_MED)
            toolTip = "Split Tolerance slider for 'Auto Seam Unfold'. \n" \
                      "Empty slider creates less seams. \n" \
                      "Full slider creates more seams"
            self.autoSeamUnfoldSlider = elements.FloatSlider(label="Auto Unfold Amount",
                                                             defaultValue=0.5,
                                                             toolTip=toolTip)
            # Unfold Tube Button ---------------------------------------
            toolTip = "UV unwrap a quad tube. \n" \
                      "Select one edge length-ways down a tube, \n" \
                      "the edge will become the seam, then run."
            self.unfoldTubeBtn = elements.AlignedButton("Unfold Tube (By Edge)",
                                                        icon="unwrapTube",
                                                        toolTip=toolTip)
            # Unfold Shell Grid Button ---------------------------------------
            toolTip = "UV unwrap a quad grid shell, such as a road. \n" \
                      "Select one interior edge length-ways down a shell grid. \n" \
                      "Run the tool."
            self.unfoldGridBtn = elements.AlignedButton("Unfold Shell Grid (Edge)",
                                                        icon="checker",
                                                        toolTip=toolTip)
            # Unfold Direction Buttons ---------------------------------------
            toolTip = "Unfolds while restricting to the horizontal U axis only. \n" \
                      "Uses Maya's legacy unfold method."
            self.unfoldHorizontalBtn = elements.AlignedButton("Horizontal",
                                                              icon="arrowLeftRight",
                                                              toolTip=toolTip)
            toolTip = "Unfolds while restricting to the vertical V axis only. \n" \
                      "Uses Maya's legacy unfold method."
            self.unfoldVerticalBtn = elements.AlignedButton("Vertical",
                                                            icon="arrowUpDown",
                                                            toolTip=toolTip)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD, uic.REGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SPACING)
        # Grid Layout ---------------------------------------
        gridLayout = elements.GridLayout(spacing=uic.SPACING)
        row = 0
        gridLayout.addWidget(self.displayCombo, row, 0)
        gridLayout.addWidget(self.imageSizeCombo, row, 1)
        row += 1
        gridLayout.addWidget(self.openUvBtn, row, 0)
        gridLayout.addWidget(self.symmetryBrushBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.planarProjCamBtn, row, 0)
        gridLayout.addWidget(self.cutSewToolBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.cutBtn, row, 0)
        gridLayout.addWidget(self.sewBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.orientShellBtn, row, 0)
        gridLayout.addWidget(self.orientEdgeBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.unfoldBtn, row, 0)
        gridLayout.addWidget(self.layoutBtn, row, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(gridLayout)


class GuiMedium(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_MEDIUM, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_MEDIUM)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiMedium, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                        toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD, uic.REGPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Slider Layout -----------------------------
        sliderLayout = elements.hBoxLayout()
        sliderLayout.addWidget(self.autoSeamUnfoldSlider, 20)
        sliderLayout.addWidget(self.autoSeamUnfoldBtn, 1)
        # Grid Layout ---------------------------------------
        gridLayout = elements.GridLayout(spacing=uic.SPACING)
        row = 0
        gridLayout.addWidget(self.displayCombo, row, 0)
        gridLayout.addWidget(self.imageSizeCombo, row, 1)
        row += 1
        gridLayout.addWidget(self.openUvBtn, row, 0)
        gridLayout.addWidget(self.symmetryBrushBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.planarProjCamBtn, row, 0)
        gridLayout.addWidget(self.planarProjAutoBtn, row, 1)
        row += 1
        gridLayout.addWidget(elements.LabelDivider(text="Cut And Sew"), row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.cutSewToolBtn, row, 0)
        gridLayout.addWidget(self.cutPerimeterBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.cutBtn, row, 0)
        gridLayout.addWidget(self.sewBtn, row, 1)
        row += 1
        gridLayout.addWidget(elements.LabelDivider(text="Orient UVs"), row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.orientShellBtn, row, 0)
        gridLayout.addWidget(self.orientEdgeBtn, row, 1)
        row += 1
        gridLayout.addWidget(elements.LabelDivider(text="Unfold And Layout"), row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(sliderLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.unfoldVerticalBtn, row, 0)
        gridLayout.addWidget(self.unfoldHorizontalBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.unfoldTubeBtn, row, 0)
        gridLayout.addWidget(self.unfoldGridBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.unfoldBtn, row, 0)
        gridLayout.addWidget(self.layoutBtn, row, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(gridLayout)
