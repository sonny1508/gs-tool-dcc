from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.modeling import pivots
from zoo.libs.maya.cmds.objutils import alignutils
from zoo.libs.maya.cmds.objutils import constraints

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

CENTER_SPACE_LIST = ["World Center", "Parent", "Object Center"]
ALIGN_OBJECTS_LIST = ["Rot/Trans", "Translation", "Rotation", "Scale", "Pivot", "All"]


class ModelingAlign(toolsetwidget.ToolsetWidget):
    id = "modelingAlign"
    info = "Alignment tools for modeling."
    uiData = {"label": "Align Toolbox",
              "icon": "alignTool",
              "tooltip": "Template file for building new GUIs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-modeling-align/"
              }

    # ------------------
    # STARTUP
    # ------------------


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


    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype: GuiWidgets
        """
        return super(ModelingAlign, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ModelingAlign, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def centerPivotWorld(self, worldSpace=True):
        """Centers the pivot of all selected objects at the world center or local space center ie parent zero.
        """
        combo = self.properties.centerWorldCombo.value
        if combo == 0:
            pivots.centerPivotWorldSel(message=True)
        elif combo == 1:
            # match pivot to parent
            pivots.matchPivotParentSel(message=True)
        else:
            # center pivot
            pivots.centerPivotSelected()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def placeObjectOnGround(self):
        """Centers the pivot of all selected objects at the world center or local space center ie parent zero.
        """
        alignutils.placeObjectOnGroundSel()

    def snapTogetherTool(self):
        """Enters Maya's Snap Together Tool"""
        alignutils.mayaSnapTogetherTool()

    def alignTool(self):
        """Enters Maya's Align Tool"""
        alignutils.mayaAlignTool()

    def snapPointToPoint(self):
        """Enters Maya's Align Tool"""
        alignutils.snapPointToPoint()

    def snap2PointsTo2Points(self):
        """Enters Maya's Align Tool"""
        alignutils.snap2PointsTo2Points()

    def snap3PointsTo3Points(self):
        """Enters Maya's Align Tool"""
        alignutils.snap3PointsTo3Points()

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

    def addSurfaceObject(self):
        """Adds a surface object to the UI from the scene"""
        geo = constraints.setSurfaceObj()
        if not geo:
            return
        self.properties.placeOnSurfaceTxt.value = geo
        self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def placeOnSurface(self):
        constraints.constrainObjsToSurfaceSelection(surface=self.properties.placeOnSurfaceTxt.value,
                                                    deleteConstraint=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for w in self.widgets():
            w.centerWorldBtn.clicked.connect(self.centerPivotWorld)
            w.placeOnGroundBtn.clicked.connect(self.placeObjectOnGround)
            w.alignToolBtn.clicked.connect(self.alignTool)
            w.snapTogetherBtn.clicked.connect(self.snapTogetherTool)
            w.matchObjectsBtn.clicked.connect(self.matchObjects)
            w.snapAlignOneBtn.clicked.connect(self.snapPointToPoint)
            w.snapAlignTwoBtn.clicked.connect(self.snap2PointsTo2Points)
            w.snapAlignThreeBtn.clicked.connect(self.snap3PointsTo3Points)
            w.placeOnSurfaceBtn.clicked.connect(self.placeOnSurface)
            w.placeOnSurfaceAddTxtBtn.clicked.connect(self.addSurfaceObject)


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
        # Pivot Space Combo ---------------------------------------
        toolTip = "Center the pivot to \n" \
                  "  1. World Space: Pivot centers in the middle of the world. \n" \
                  "  2. Local Space: Pivot centers at the zero position of it's parent."
        self.centerWorldCombo = elements.ComboBoxRegular(label="Move Pivot",
                                                         items=CENTER_SPACE_LIST,
                                                         toolTip=toolTip,
                                                         boxRatio=15,
                                                         labelRatio=10)
        # Center World Pivot ---------------------------------------
        toolTip = "Center the pivot/s of the selected object at the center of the world or local space."
        self.centerWorldBtn = elements.AlignedButton("Center Pivot",
                                                     icon="focusAim",
                                                     toolTip=toolTip)
        # Match Objects Combo ---------------------------------------
        toolTip = "Match Objects Options \n" \
                  "  1. Rot/Trans: Match Rotation and Translation \n" \
                  "  2. Translation: Match Translation Only \n" \
                  "  3. Rotation: Match Rotation Only \n" \
                  "  4. Scale: Match Scale Only \n" \
                  "  5. Pivot: Match Pivot Only \n" \
                  "  6. All: Match Translate, Rotate, Scale and Pivot"
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
                  "Uses the `Match Type` drop down settings"
        self.matchObjectsBtn = elements.AlignedButton("Match Objects",
                                                      icon="magnet",
                                                      toolTip=toolTip)
        # Align Tool ---------------------------------------
        toolTip = "Activates Maya's `Align Tool`"
        self.alignToolBtn = elements.AlignedButton("Align Tool",
                                                   icon="alignTool",
                                                   toolTip=toolTip)
        # Snap Together Tool ---------------------------------------
        toolTip = "Activates Maya's `Snap Together Tool` \n" \
                  "  1. Click and drag on a surface of one object. \n" \
                  "  2. Then click and drag on another object \n" \
                  "  3. Press Enter"
        self.snapTogetherBtn = elements.AlignedButton("Snap Together Tool",
                                                      icon="snapTogether",
                                                      toolTip=toolTip)
        # Snap Align 1 ---------------------------------------
        toolTip = "Select two objects and select a point on each object. \n" \
                  "Run and the first object will be snapped to the last."
        self.snapAlignOneBtn = elements.AlignedButton("Snap Align One Point",
                                                      icon="snapAlignOne",
                                                      toolTip=toolTip)
        # Snap Align 2 ---------------------------------------
        toolTip = "Select two objects and select two points on each object. \n" \
                  "Run and the first object will be snapped to the last."
        self.snapAlignTwoBtn = elements.AlignedButton("Snap Align Two Points",
                                                      icon="snapAlignTwo",
                                                      toolTip=toolTip)
        # Snap Align 3 ---------------------------------------
        toolTip = "Select two objects and select three points on each object. \n" \
                  "Run and the first object will be snapped to the last."
        self.snapAlignThreeBtn = elements.AlignedButton("Snap Align Three Points",
                                                        icon="snapAlignThree",
                                                        toolTip=toolTip)
        # Place Object On Ground ---------------------------------------
        toolTip = "Places object's bounding box on the world ground place.  Zero Y."
        self.placeOnGroundBtn = elements.AlignedButton("Place On Ground Zero Y ",
                                                       icon="verticalAlignBottom",
                                                       toolTip=toolTip)
        # Surface Align Text ---------------------------------------
        toolTip = "Enter the geometry for object snapping.  \n" \
                  "For the `Place Objects On Surface` button"
        self.placeOnSurfaceTxt = elements.StringEdit(label="",
                                                     editPlaceholder="Select Surface Object",
                                                     editText="",
                                                     toolTip=toolTip)
        # Surface Assign Text ---------------------------------------
        toolTip = "Set the base geometry for object snapping. \n" \
                  "Select a mesh or nurbs surface and run."
        self.placeOnSurfaceAddTxtBtn = elements.styledButton("",
                                                             "arrowLeft",
                                                             toolTip=toolTip,
                                                             style=uic.BTN_TRANSPARENT_BG,
                                                             minWidth=15)
        toolTip = "Snap the selected objects to another mesh or nurbs surface. \n" \
                  "Note: If no surface has been added in the UI then the tool will use \n" \
                  "the last selected object as the surface object. "
        # Surface Align Button ---------------------------------------
        self.placeOnSurfaceBtn = elements.AlignedButton("Place Objects On Surface",
                                                        icon="verticalAlignBottom",
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
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SPACING)
        # Pivot Layout ----------------------------
        pivotLayout = elements.hBoxLayout(spacing=uic.SPACING)
        pivotLayout.addWidget(self.centerWorldCombo, 1)
        pivotLayout.addWidget(self.centerWorldBtn, 1)
        # Align Objects Layout --------------------------
        alignObjLayout = elements.hBoxLayout(spacing=uic.SPACING)
        alignObjLayout.addWidget(self.matchObjectsCombo, 1)
        alignObjLayout.addWidget(self.matchObjectsBtn, 1)
        # surfaceTextLayout
        surfaceTextLayout = elements.hBoxLayout(spacing=uic.SPACING)
        surfaceTextLayout.addWidget(self.placeOnSurfaceTxt, 9)
        surfaceTextLayout.addWidget(self.placeOnSurfaceAddTxtBtn, 1)
        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(spacing=uic.SPACING)
        row = 0
        gridLayout.addLayout(surfaceTextLayout, row, 0)
        gridLayout.addWidget(self.placeOnSurfaceBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.alignToolBtn, row, 0)
        gridLayout.addWidget(self.placeOnGroundBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.snapAlignOneBtn, row, 0)
        gridLayout.addWidget(self.snapAlignTwoBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.snapAlignThreeBtn, row, 0)
        gridLayout.addWidget(self.snapTogetherBtn, row, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(pivotLayout)
        mainLayout.addLayout(alignObjLayout)
        mainLayout.addLayout(gridLayout)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Pivot Layout ----------------------------
        pivotLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SSML))
        pivotLayout.addWidget(self.centerWorldCombo, 1)
        pivotLayout.addWidget(self.centerWorldBtn, 1)
        # Align Objects Layout --------------------------
        alignObjLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SSML))
        alignObjLayout.addWidget(self.matchObjectsCombo, 1)
        alignObjLayout.addWidget(self.matchObjectsBtn, 1)
        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(hSpacing=uic.SVLRG)
        gridLayout.addWidget(self.alignToolBtn, 2, 0)
        gridLayout.addWidget(self.placeOnGroundBtn, 2, 1)
        gridLayout.addWidget(self.snapAlignOneBtn, 3, 0)
        gridLayout.addWidget(self.snapAlignTwoBtn, 3, 1)
        gridLayout.addWidget(self.snapAlignThreeBtn, 4, 0)
        gridLayout.addWidget(self.snapTogetherBtn, 4, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(pivotLayout)
        mainLayout.addLayout(alignObjLayout)
        mainLayout.addLayout(gridLayout)
