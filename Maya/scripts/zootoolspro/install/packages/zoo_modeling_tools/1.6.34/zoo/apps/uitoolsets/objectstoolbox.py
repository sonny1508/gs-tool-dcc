""" ---------- Objects Toolbox (Multiple UI Modes) -------------

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


class ObjectsToolbox(toolsetwidget.ToolsetWidget):
    id = "objectsToolbox"
    info = "Maya modeling object tools and hotkey trainer."
    uiData = {"label": "Objects Toolbox",
              "icon": "cubeWire",
              "tooltip": "Maya modeling object tools and hotkey trainer.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-objects-toolbox/"}

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
        return super(ObjectsToolbox, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ObjectsToolbox, self).widgets()

    # ------------------
    # LOGIC - CREATE OBJECTS
    # ------------------

    def createPolygonSphereMel(self):
        definedhotkeys.createPolygonSphereMel()

    def createPolygonCubeMel(self):
        definedhotkeys.createPolygonCubeMel()

    def createPolygonCylinderMel(self):
        definedhotkeys.createPolygonCylinderMel()

    def createPolygonPlaneMel(self):
        definedhotkeys.createPolygonPlaneMel()

    def createPolygonTorusMel(self):
        definedhotkeys.createPolygonTorusMel()

    def createPolygonConeMel(self):
        definedhotkeys.createPolygonConeMel()

    def createPolygonDiskMel(self):
        definedhotkeys.createPolygonDiskMel()

    def createPolygonFacesMel(self):
        definedhotkeys.createPolygonFacesMel()

    def createPlatnonicSolidMel(self):
        definedhotkeys.createPlatnonicSolidMel()

    def createPolygonPyramidMel(self):
        definedhotkeys.createPolygonPyramidMel()

    def createPolygonPrismMel(self):
        definedhotkeys.createPolygonPrismMel()

    def createPolygonPipeMel(self):
        definedhotkeys.createPolygonPipeMel()

    def createPolygonHelixMel(self):
        definedhotkeys.createPolygonHelixMel()

    def createPolygonGearMel(self):
        definedhotkeys.createPolygonGearMel()

    def createPolygonSoccerBallMel(self):
        definedhotkeys.createPolygonSoccerBallMel()

    def createPolygonSuperEllipseMel(self):
        definedhotkeys.createPolygonSuperEllipseMel()

    def createPolygonSphericalHarmonicsMel(self):
        definedhotkeys.createPolygonSphericalHarmonicsMel()

    def createPolygonUltraShapeMel(self):
        definedhotkeys.createPolygonUltraShapeMel()

    def createSweepMeshMel(self):
        definedhotkeys.createSweepMeshMel()

    def createPolygonTypeMel(self):
        definedhotkeys.createPolygonTypeMel()

    def createPolygonSVGMel(self):
        definedhotkeys.createPolygonSVGMel()

    # ------------------
    # LOGIC - OPERATE WITH OBJECTS
    # ------------------

    def duplicateMel(self):
        definedhotkeys.duplicateMel()

    def duplicateOffsetMel(self):
        definedhotkeys.duplicateOffsetMel()

    def duplicateInputGraphMel(self):
        definedhotkeys.duplicateInputGraphMel()

    def duplicateInputConnectionsMel(self):
        definedhotkeys.duplicateInputConnectionsMel()

    def duplicateFaceMel(self):
        definedhotkeys.duplicateFaceMel()

    def duplicateOpenOptionsMel(self):
        definedhotkeys.duplicateOpenOptionsMel()

    def instance(self):
        definedhotkeys.instance()

    def uninstance(self):
        definedhotkeys.uninstanceSelected()

    def boolDifferenceATakeBMel(self):
        definedhotkeys.boolDifferenceATakeBMel()

    def boolDifferenceBTakeAMel(self):
        definedhotkeys.boolDifferenceBTakeAMel()

    def boolUnionMel(self):
        definedhotkeys.boolUnionMel()

    def boolIntersectionMel(self):
        definedhotkeys.boolIntersectionMel()

    def boolSiceMel(self):
        definedhotkeys.boolSiceMel()

    def boolHolePunchMel(self):
        definedhotkeys.boolHolePunchMel()

    def boolCutOutMel(self):
        definedhotkeys.boolCutOutMel()

    def boolSplitEdgesMel(self):
        definedhotkeys.boolSplitEdgesMel()

    def combineMel(self):
        definedhotkeys.combineMel()

    def separateMel(self):
        definedhotkeys.separateMel()

    def extractMel(self):
        definedhotkeys.extractMel()

    def parentMel(self):
        definedhotkeys.parentMel()

    def unparentMel(self):
        definedhotkeys.unparentMel()

    def groupMel(self):
        definedhotkeys.groupMel()

    def ungroupMel(self):
        definedhotkeys.ungroupMel()

    # ------------------
    # LOGIC - MODIFY OBJECTS
    # ------------------

    def toggleEditPivotMel(self):
        definedhotkeys.toggleEditPivotMel()

    def bakePivotMel(self):
        definedhotkeys.bakePivotMel()

    def matchPivot(self):
        definedhotkeys.matchPivot()

    def centerPivotMel(self):
        definedhotkeys.centerPivotMel()

    def freezeTransformationsMel(self):
        definedhotkeys.freezeTransformationsMel()

    def unfreezeTransformations(self):
        definedhotkeys.unfreezeTransformations()

    def deleteHistoryMel(self):
        definedhotkeys.deleteHistoryMel()

    def deleteNonDeformerHistoryMel(self):
        definedhotkeys.deleteNonDeformerHistoryMel()

    def freezeMatrixModeller(self):
        definedhotkeys.freezeMatrixModeller()

    def freezeMatrixAll(self):
        definedhotkeys.freezeMatrixAll()

    def unfreezeMatrix(self):
        definedhotkeys.unfreezeMatrix()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():  # BOTH UI MODES
            widget.instanceBtn.clicked.connect(self.instance)
            widget.uninstanceBtn.clicked.connect(self.uninstance)
            widget.booleanBtn.clicked.connect(self.boolDifferenceATakeBMel)
            widget.combineBtn.clicked.connect(self.combineMel)
            widget.separateBtn.clicked.connect(self.separateMel)
            widget.extractBtn.clicked.connect(self.extractMel)
            # Modify -----------------------
            widget.matrixFreezeBtn.clicked.connect(self.freezeMatrixModeller)
            widget.unfreezeMatrixBtn.clicked.connect(self.unfreezeMatrix)
            # RIGHT CLICKS -----------------------
            # Booleans -----------------------
            widget.booleanBtn.createMenuItem(text="Difference (A-B) (Default)",
                                             icon=iconlib.icon(":polyBooleansDifference",
                                                               size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.boolDifferenceATakeBMel)
            widget.booleanBtn.createMenuItem(text="Difference (B-A)",
                                             icon=iconlib.icon(":Bool_BMinusA",
                                                               size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.boolDifferenceBTakeAMel)
            widget.booleanBtn.createMenuItem(text="Union",
                                             icon=iconlib.icon(":polyBooleansUnion",
                                                               size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.boolUnionMel)
            widget.booleanBtn.createMenuItem(text="Itersection",
                                             icon=iconlib.icon(":polyBooleansIntersection",
                                                               size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.boolIntersectionMel)
            widget.booleanBtn.createMenuItem(text="Slice",
                                             icon=iconlib.icon(":Bool_Slice", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.boolSiceMel)
            widget.booleanBtn.createMenuItem(text="Hole Punch",
                                             icon=iconlib.icon(":Bool_HolePunch", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.boolHolePunchMel)
            widget.booleanBtn.createMenuItem(text="Cut Out",
                                             icon=iconlib.icon(":Bool_CutOut", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.boolCutOutMel)
            widget.booleanBtn.createMenuItem(text="Split Edges",
                                             icon=iconlib.icon(":Bool_SplitEdges", size=uic.MAYA_BTN_ICON_SIZE),
                                             connection=self.boolSplitEdgesMel)
            # Matrix Freeze Right Clicks -----------------------
            widget.matrixFreezeBtn.createMenuItem(text="Freeze Matrix Modeller (Default)",
                                                  icon=iconlib.icon(":DeleteHistory", size=uic.MAYA_BTN_ICON_SIZE),
                                                  connection=self.freezeMatrixModeller)
            widget.matrixFreezeBtn.createMenuItem(text="Freeze Matrix Keep Scale Space",
                                                  icon=iconlib.icon(":DeleteHistory", size=uic.MAYA_BTN_ICON_SIZE),
                                                  connection=self.freezeMatrixAll)
            # Duplicate Right Clicks -----------------------
            widget.duplicateBtn.createMenuItem(text="Duplicate Selected Only (Default)",
                                               icon=iconlib.icon("duplicateMaya"),
                                               connection=self.duplicateMel)
            widget.duplicateBtn.createMenuItem(text="Duplicate & Input Connected Node Graph",
                                               icon=iconlib.icon("duplicateMaya"),
                                               connection=self.duplicateInputGraphMel)
            widget.duplicateBtn.createMenuItem(text="Duplicate Share Input Connections",
                                               icon=iconlib.icon("duplicateMaya"),
                                               connection=self.duplicateInputConnectionsMel)
            widget.duplicateBtn.createMenuItem(text="Duplicate Face Selection",
                                               icon=iconlib.icon("duplicateMaya"),
                                               connection=self.duplicateFaceMel)
            widget.duplicateBtn.createMenuItem(text="Open Duplicate Options",
                                               icon=iconlib.icon("windowBrowser"),
                                               connection=self.duplicateOpenOptionsMel)
        # ADVANCED MODE -------------------------------------------------------
        # Create Objects -----------------------
        self.advancedWidget.sphereBtn.clicked.connect(self.createPolygonSphereMel)
        self.advancedWidget.cubeBtn.clicked.connect(self.createPolygonCubeMel)
        self.advancedWidget.cylinderBtn.clicked.connect(self.createPolygonCylinderMel)
        self.advancedWidget.planeBtn.clicked.connect(self.createPolygonPlaneMel)
        self.advancedWidget.torusBtn.clicked.connect(self.createPolygonTorusMel)
        self.advancedWidget.coneBtn.clicked.connect(self.createPolygonConeMel)
        self.advancedWidget.createPolygonBtn.clicked.connect(self.createPolygonFacesMel)
        self.advancedWidget.sweepMeshBtn.clicked.connect(self.createSweepMeshMel)
        self.advancedWidget.typeBtn.clicked.connect(self.createPolygonTypeMel)
        # Operate On Objects -----------------------
        self.advancedWidget.duplicateBtn.clicked.connect(self.duplicateMel)
        self.advancedWidget.duplicateOffsetBtn.clicked.connect(self.duplicateOffsetMel)
        self.advancedWidget.parentBtn.clicked.connect(self.parentMel)
        self.advancedWidget.unparentBtn.clicked.connect(self.unparentMel)
        self.advancedWidget.groupBtn.clicked.connect(self.groupMel)
        self.advancedWidget.ungroupBtn.clicked.connect(self.ungroupMel)
        self.advancedWidget.editPivotBtn.clicked.connect(self.toggleEditPivotMel)
        self.advancedWidget.centerPivotBtn.clicked.connect(self.centerPivotMel)
        self.advancedWidget.freezeBtn.clicked.connect(self.freezeTransformationsMel)
        self.advancedWidget.deleteHistoryBtn.clicked.connect(self.deleteHistoryMel)
        # RIGHT CLICKS -----------------------
        # Create Objects -----------------------
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Disk",
                                                       icon=iconlib.icon(":polyDisc", size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonDiskMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Pyramid",
                                                       icon=iconlib.icon(":polyPyramid", size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonPyramidMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Pipe",
                                                       icon=iconlib.icon(":polyPipe", size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonPipeMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Prism",
                                                       icon=iconlib.icon(":polyPrism", size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonPrismMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Helix",
                                                       icon=iconlib.icon(":polyHelix", size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonHelixMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Gear",
                                                       icon=iconlib.icon(":polyGear", size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonGearMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Soccer Ball", icon=iconlib.icon(":polySoccerBall",
                                                                                                    size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonSoccerBallMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Platonic Solid",
                                                       icon=iconlib.icon(":polyPlatonicSolid",
                                                                         size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPlatnonicSolidMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create SVG",
                                                       icon=iconlib.icon(":polySVG", size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonSVGMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Super Ellipse",
                                                       icon=iconlib.icon(":polySuperEllipse",
                                                                         size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonSuperEllipseMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Spherical Harmonics",
                                                       icon=iconlib.icon(":polySphericalHarmonics",
                                                                         size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonSphericalHarmonicsMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        self.advancedWidget.dotsMenuBtn.createMenuItem(text="Create Ultra Shape", icon=iconlib.icon(":polyUltraShape",
                                                                                                    size=uic.MAYA_BTN_ICON_SIZE),
                                                       connection=self.createPolygonUltraShapeMel,
                                                       mouseClick=QtCore.Qt.LeftButton)
        # Toggle Edit Pivot Right Clicks -----------------------
        self.advancedWidget.editPivotBtn.createMenuItem(text="Toggle Edit Pivot (Default)",
                                                        icon=iconlib.icon(":CenterPivot", size=uic.MAYA_BTN_ICON_SIZE),
                                                        connection=self.toggleEditPivotMel)
        self.advancedWidget.editPivotBtn.createMenuItem(text="Bake Pivot",
                                                        icon=iconlib.icon(":CenterPivot", size=uic.MAYA_BTN_ICON_SIZE),
                                                        connection=self.bakePivotMel)
        # Center Pivot Right Clicks -----------------------
        self.advancedWidget.centerPivotBtn.createMenuItem(text="Center Pivot (Default)",
                                                          icon=iconlib.icon(":CenterPivot",
                                                                            size=uic.MAYA_BTN_ICON_SIZE),
                                                          connection=self.toggleEditPivotMel)
        self.advancedWidget.centerPivotBtn.createMenuItem(text="Match Pivot (First To Last)",
                                                          icon=iconlib.icon(":CenterPivot",
                                                                            size=uic.MAYA_BTN_ICON_SIZE),
                                                          connection=self.matchPivot)
        # Delete History Right Clicks -----------------------
        self.advancedWidget.deleteHistoryBtn.createMenuItem(text="Delete History (All) (Default)",
                                                            icon=iconlib.icon(":DeleteHistory",
                                                                              size=uic.MAYA_BTN_ICON_SIZE),
                                                            connection=self.deleteHistoryMel)
        self.advancedWidget.deleteHistoryBtn.createMenuItem(text="Delete Non-Deformer History",
                                                            icon=iconlib.icon(":DeleteHistory",
                                                                              size=uic.MAYA_BTN_ICON_SIZE),
                                                            connection=self.deleteNonDeformerHistoryMel)
        # Freeze Right Clicks -----------------------
        self.advancedWidget.freezeBtn.createMenuItem(text="Freeze Transformations (Default)",
                                                     icon=iconlib.icon(":FreezeTransform", size=uic.MAYA_BTN_ICON_SIZE),
                                                     connection=self.freezeTransformationsMel)
        self.advancedWidget.freezeBtn.createMenuItem(text="Freeze (Translation)",
                                                     icon=iconlib.icon(":FreezeTransform", size=uic.MAYA_BTN_ICON_SIZE),
                                                     connection=self.freezeTransformationsMel)
        self.advancedWidget.freezeBtn.createMenuItem(text="Freeze (Rotation)",
                                                     icon=iconlib.icon(":FreezeTransform", size=uic.MAYA_BTN_ICON_SIZE),
                                                     connection=self.freezeTransformationsMel)
        self.advancedWidget.freezeBtn.createMenuItem(text="Freeze (Scale)",
                                                     icon=iconlib.icon(":FreezeTransform", size=uic.MAYA_BTN_ICON_SIZE),
                                                     connection=self.freezeTransformationsMel)
        self.advancedWidget.freezeBtn.createMenuItem(text="Unfreeze",
                                                     icon=iconlib.icon(":FreezeTransform", size=uic.MAYA_BTN_ICON_SIZE),
                                                     connection=self.unfreezeTransformations)


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
        toolTipDict = tt.objectToolbox()
        if uiMode == UI_MODE_ADVANCED:
            # OBJECTS ----------------------------------------------------------------------------------
            # maya icon btn ---------------------------------------
            self.sphereBtn = self.mayaIconBtn(":polySphere", toolTipDict["createSphere"])
            # maya icon btn ---------------------------------------
            self.cubeBtn = self.mayaIconBtn(":polyCube", toolTipDict["createCube"])
            # maya icon btn ---------------------------------------
            self.cylinderBtn = self.mayaIconBtn(":polyCylinder", toolTipDict["createCylinder"])
            # maya icon btn ---------------------------------------
            self.planeBtn = self.mayaIconBtn(":polyMesh", toolTipDict["createPlane"])
            # maya icon btn ---------------------------------------
            self.torusBtn = self.mayaIconBtn(":polyTorus", toolTipDict["createTorus"])
            # maya icon btn ---------------------------------------
            self.coneBtn = self.mayaIconBtn(":polyCone", toolTipDict["createCone"])
            # maya icon btn ---------------------------------------
            self.createPolygonBtn = self.mayaIconBtn(":polyCreateFacet", toolTipDict["createPolygon"])
            # zoo icon btn ---------------------------------------
            self.sweepMeshBtn = self.zooIconBtn("sweepMeshMaya", toolTipDict["createSweepMesh"])
            # maya icon btn ---------------------------------------
            self.typeBtn = self.mayaIconBtn(":polyType", toolTipDict["createType"])
            # Dots menu btn ---------------------------------------
            toolTip = "Left-click for more create primitive options."
            self.dotsMenuBtn = elements.leftAlignedButton("", icon=iconlib.icon("menudots", utils.dpiScale(20)),
                                                          toolTip=toolTip, parent=parent,
                                                          padding=(7, 4, 4, 4),
                                                          transparentBg=True, alignment="center")
        # zoo btn ---------------------------------------
        self.duplicateBtn = self.zooBtn("Duplicate (Right-Click)", "duplicateMaya", toolTipDict["duplicate"])
        # zoo btn ---------------------------------------
        self.duplicateOffsetBtn = self.zooBtn("Duplicate Offset", "duplicateMaya", toolTipDict["duplicateOffset"])
        # zoo btn ---------------------------------------
        self.instanceBtn = self.zooBtn("Instance", "duplicateMaya", toolTipDict["instance"])
        # maya btn ---------------------------------------
        self.uninstanceBtn = self.mayaBtn("Uninstance", ":instanceToObject", toolTipDict["uninstance"])
        # maya btn---------------------------------------
        self.combineBtn = self.mayaBtn("Combine", ":polyUnite", toolTipDict["combine"])
        # maya btn---------------------------------------
        self.extractBtn = self.mayaBtn("Extract", ":polyDuplicateFacet", toolTipDict["extract"])
        # maya btn---------------------------------------
        self.separateBtn = self.mayaBtn("Separate", ":polySeparate", toolTipDict["separate"])
        # maya btn---------------------------------------
        self.booleanBtn = self.mayaBtn("Boolean (Right-Click)", ":polyBooleansDifference", toolTipDict["boolean"])
        if uiMode == UI_MODE_ADVANCED:
            # maya btn---------------------------------------
            self.parentBtn = self.mayaBtn("Parent", ":parent", toolTipDict["parent"])
            # maya btn---------------------------------------
            self.unparentBtn = self.mayaBtn("Unparent", ":unparent", toolTipDict["unparent"])
            # maya btn---------------------------------------
            self.groupBtn = self.mayaBtn("Group", ":group", toolTipDict["group"])
            # maya btn---------------------------------------
            self.ungroupBtn = self.mayaBtn("Ungroup", ":ungroup", toolTipDict["ungroup"])
            # maya btn---------------------------------------
            self.editPivotBtn = self.mayaBtn("Toggle Edit Pivot (R-C)", ":CenterPivot", toolTipDict["toggleEditPivot"])
            # maya btn---------------------------------------
            self.centerPivotBtn = self.mayaBtn("Center Pivot (Right-Click)", ":CenterPivot", toolTipDict["centerPivot"])
            # maya btn---------------------------------------
            self.freezeBtn = self.mayaBtn("Freeze (Right-Click)", ":FreezeTransform", toolTipDict["Freeze"])
            # maya btn---------------------------------------
            self.deleteHistoryBtn = self.mayaBtn("Delete History (Right-Click)", ":DeleteHistory",
                                                 toolTipDict["deleteHistory"])

        # maya btn---------------------------------------
        toolTip = toolTipDict["freezeMatrix"]
        self.matrixFreezeBtn = self.mayaBtn("Freeze Matrix (Right-Click)", ":Freeze", toolTip)
        # maya btn---------------------------------------
        toolTip = toolTipDict["unfreezeMatrix"]
        self.unfreezeMatrixBtn = self.mayaBtn("Unfreeze Matrix", ":freezeSelected", toolTip)

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

    def mayaIconBtn(self, icon, toolTip):
        """Icon button with a maya icon"""
        iconSize = utils.dpiScale(uic.MAYA_BTN_ICON_SIZE)
        return elements.leftAlignedButton("",
                                          icon=iconlib.icon(icon,
                                                            size=iconSize),
                                          padding=uic.MAYA_BTN_PADDING,
                                          toolTip=toolTip, parent=self.parent,
                                          alignment="center", transparentBg=True)

    def zooIconBtn(self, icon, toolTip):
        return elements.leftAlignedButton("",
                                          icon=iconlib.icon(icon,
                                                            size=utils.dpiScale(20)),
                                          toolTip=toolTip,
                                          parent=self.parent,
                                          padding=(7, 4, 4, 4),
                                          transparentBg=True,
                                          alignment="center")


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

        # Objects Layout -----------------------------
        objectsLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        objectsLayout.addWidget(self.duplicateBtn, row, 0)
        objectsLayout.addWidget(self.duplicateOffsetBtn, row, 1)
        row += 1
        objectsLayout.addWidget(self.instanceBtn, row, 0)
        objectsLayout.addWidget(self.uninstanceBtn, row, 1)
        row += 1
        objectsLayout.addWidget(self.booleanBtn, row, 0)
        objectsLayout.addWidget(self.combineBtn, row, 1)
        row += 1
        objectsLayout.addWidget(self.extractBtn, row, 0)
        objectsLayout.addWidget(self.separateBtn, row, 1)

        objectsLayout.setColumnStretch(0, 1)
        objectsLayout.setColumnStretch(1, 1)

        # Modify Layout -----------------------------
        modifyLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        modifyLayout.addWidget(self.matrixFreezeBtn, row, 0)
        modifyLayout.addWidget(self.unfreezeMatrixBtn, row, 1)
        modifyLayout.setColumnStretch(0, 1)
        modifyLayout.setColumnStretch(1, 1)

        # Modify Collapsable & Connections -------------------------------------
        objectsCollapsable = elements.CollapsableFrameThin("Objects", collapsed=False)
        objectsCollapsable.hiderLayout.addLayout(objectsLayout)
        objectsCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        objectsCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        objectsCollapseLayout.addWidget(objectsCollapsable)

        # Utils Menu Collapsable & Connections -------------------------------------
        modifyCollapsable = elements.CollapsableFrameThin("Modify", collapsed=False)

        modifyCollapsable.hiderLayout.addLayout(modifyLayout)
        modifyCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        modifyCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        modifyCollapseLayout.addWidget(modifyCollapsable)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(objectsCollapseLayout)
        mainLayout.addLayout(modifyCollapseLayout)


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

        # Primitives Layout -----------------------------
        primitivesLayout = elements.hBoxLayout(spacing=uic.SPACING)
        primitivesLayout.addWidget(self.sphereBtn)
        primitivesLayout.addWidget(self.cubeBtn)
        primitivesLayout.addWidget(self.cylinderBtn)
        primitivesLayout.addWidget(self.planeBtn)
        primitivesLayout.addWidget(self.torusBtn)
        primitivesLayout.addWidget(self.coneBtn)
        primitivesLayout.addWidget(self.createPolygonBtn)
        primitivesLayout.addWidget(self.sweepMeshBtn)
        primitivesLayout.addWidget(self.typeBtn)
        primitivesLayout.addWidget(self.dotsMenuBtn)

        # Objects Layout -----------------------------
        objectsLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        objectsLayout.addWidget(self.duplicateBtn, row, 0)
        objectsLayout.addWidget(self.duplicateOffsetBtn, row, 1)
        row += 1
        objectsLayout.addWidget(self.instanceBtn, row, 0)
        objectsLayout.addWidget(self.uninstanceBtn, row, 1)
        row += 1
        objectsLayout.addWidget(self.booleanBtn, row, 0)
        objectsLayout.addWidget(self.combineBtn, row, 1)
        row += 1
        objectsLayout.addWidget(self.extractBtn, row, 0)
        objectsLayout.addWidget(self.separateBtn, row, 1)
        row += 1
        objectsLayout.addWidget(self.parentBtn, row, 0)
        objectsLayout.addWidget(self.unparentBtn, row, 1)
        row += 1
        objectsLayout.addWidget(self.groupBtn, row, 0)
        objectsLayout.addWidget(self.ungroupBtn, row, 1)
        objectsLayout.setColumnStretch(0, 1)
        objectsLayout.setColumnStretch(1, 1)

        # Modify Layout -----------------------------
        modifyLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        modifyLayout.addWidget(self.editPivotBtn, row, 0)
        modifyLayout.addWidget(self.centerPivotBtn, row, 1)
        row += 1
        modifyLayout.addWidget(self.freezeBtn, row, 0)
        modifyLayout.addWidget(self.deleteHistoryBtn, row, 1)
        row += 1
        modifyLayout.addWidget(self.matrixFreezeBtn, row, 0)
        modifyLayout.addWidget(self.unfreezeMatrixBtn, row, 1)
        modifyLayout.setColumnStretch(0, 1)
        modifyLayout.setColumnStretch(1, 1)

        # Modify Collapsable & Connections -------------------------------------
        objectsCollapsable = elements.CollapsableFrameThin("Objects", collapsed=False)
        objectsCollapsable.hiderLayout.addLayout(primitivesLayout)
        objectsCollapsable.hiderLayout.addLayout(objectsLayout)
        objectsCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        objectsCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        objectsCollapseLayout.addWidget(objectsCollapsable)

        # Utils Menu Collapsable & Connections -------------------------------------
        modifyCollapsable = elements.CollapsableFrameThin("Modify", collapsed=False)

        modifyCollapsable.hiderLayout.addLayout(modifyLayout)
        modifyCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        modifyCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        modifyCollapseLayout.addWidget(modifyCollapsable)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(objectsCollapseLayout)
        mainLayout.addLayout(modifyCollapseLayout)
