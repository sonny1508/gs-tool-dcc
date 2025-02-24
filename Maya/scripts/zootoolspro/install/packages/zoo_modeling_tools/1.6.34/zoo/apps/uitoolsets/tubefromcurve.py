from zoovendor.Qt import QtWidgets, QtCore

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from maya import cmds
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.meta import metatubecurve
from zoo.libs.maya.meta import base
from zoo.libs.maya.cmds.modeling import paintfxtube
from zoo.libs.maya.cmds.objutils import curves
from zoo.libs.utils import output

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class TubeFromCurve(toolsetwidget.ToolsetWidget):
    id = "tubeFromCurve"
    info = "Template file for building new GUIs."
    uiData = {"label": "Tube From Curve",
              "icon": "createTube",
              "tooltip": "Template file for building new GUIs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-tube-from-curve/"}
    _metaNode = None
    _creatingCurve = None

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
        self._creatingCurve = None
        self.savedShape = None
        self.uiConnections()
        self.startSelectionCallback()  # start selection callback
        self.updateSelection()

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  GuiWidgets
        """
        return super(TubeFromCurve, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(TubeFromCurve, self).widgets()

    def selectionChanged(self, sel):
        """ Selection Changed callback event

        :param sel:
        :type sel:
        :return:
        :rtype:
        """
        if not sel:
            return
        self.updateSelection()

    def isFinishedCreatingCurve(self):
        """ Checks if creating curve is finished

        # Depreciated code but handy so leaving

        :return:
        :rtype:
        """
        if self._creatingCurve:
            if self.savedShape is None:
                self.savedShape = self.curveShape()  # can maybe simplify this?
            if self.savedShape:
                try:
                    if self.isCurveValid(self.savedShape):
                        self._creatingCurve = False
                        self.savedShape = None
                        return True
                except:  # should handle if it doesn't exist
                    pass
        return False

    def curveShape(self):
        """ Get Curve shape

        # Depreciated code but handy so leaving
        """
        sel = list(zapi.selected())
        curveTransform = sel[0] if len(sel) > 0 else None
        if curveTransform:
            shape = cmds.listRelatives(curveTransform.fullPathName(), shapes=True)
            if shape and len(shape) > 0 and zapi.nodeByName(shape[0]).typeName == "nurbsCurve":
                return shape[0]

    def isCurveValid(self, curve=None):
        """ Check if curve is valid for creating the tube on

        # Depreciated code but handy so leaving


        :param curve:
        :type curve:
        :return:
        :rtype:
        """
        if curve is None:
            curve = self.curveShape()
            if curve is None:
                return False

        if cmds.getAttr("{}.dispHull".format(curve)):  # Means it's not in the middle of creating
            return False

        numPts = len(cmds.getAttr(curve + ".cv[*]"))
        if numPts == 1:
            return False

        if numPts < 4:
            output.displayWarning("Not enough points in curve")
            return False

        return True

    def enterEvent(self, event):
        """ Update selection on enter event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        self.updateSelection()

    # ------------------
    # LOGIC
    # ------------------
    def updateSelection(self):
        """ Update metanode based on selection

        :return:
        :rtype:
        """
        if len(list(zapi.selected())) > 0:
            metaNodes = self.selectedMetaNodes()
            self._metaNode = metaNodes[-1] if len(metaNodes) > 0 else None  # type: metatubecurve.ZooTubeCurve
            if self._metaNode:
                metaAttrs = self._metaNode.tubeAttributes()
                if metaAttrs:
                    self.properties.radiusFloat.value = metaAttrs['radius']
                    self.properties.axisDivisionsInt.value = metaAttrs['axisDivisions']
                    self.properties.minClipFloat.value = metaAttrs['minClip']
                    self.properties.maxClipFloat.value = metaAttrs['maxClip']
                    self.properties.densityFloat.value = metaAttrs['density']
                    self.properties.polyLimitInt.value = metaAttrs['polyLimit']
                    self.updateFromProperties()

    def createCurveContext(self):
        """Enters the create curve context (user draws cvs).  Uses mel hardcoded 3 bezier curve.
        """
        curves.createCurveContext(degrees=3)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createTube(self):
        """ Create the tube based on the data

        :return:
        :rtype:
        """
        paintfxtube.paintFxTubeRigSelected(radius=self.properties.radiusFloat.value,
                                           tubeSections=self.properties.axisDivisionsInt.value,
                                           minClip=self.properties.minClipFloat.value,
                                           maxClip=self.properties.maxClipFloat.value,
                                           density=self.properties.densityFloat.value,
                                           polyLimit=self.properties.polyLimitInt.value)

    def radiusChanged(self):
        """ Radius Clicked

        :return:
        :rtype:
        """
        metaNodes = self.selectedMetaNodes()
        for meta in metaNodes:
            meta.setMetaAttributes(radius=self.properties.radiusFloat.value)

    def axisDivisionsChanged(self):
        """ Axis Divisions Changed

        :return:
        :rtype:
        """
        metaNodes = self.selectedMetaNodes()
        for meta in metaNodes:
            meta.setMetaAttributes(axisDiv=self.properties.axisDivisionsInt.value)

    def densityChanged(self):
        """ Density Changed

        :return:
        :rtype:
        """
        metaNodes = self.selectedMetaNodes()
        for meta in metaNodes:
            meta.setMetaAttributes(density=self.properties.densityFloat.value)

    def minClipChanged(self):
        """ Min Clip changed

        :return:
        :rtype:
        """
        metaNodes = self.selectedMetaNodes()
        for meta in metaNodes:
            meta.setMetaAttributes(minClip=self.properties.minClipFloat.value)

    def maxClipChanged(self):
        """ Max Clip Changed

        :return:
        :rtype:
        """
        metaNodes = self.selectedMetaNodes()
        for meta in metaNodes:
            meta.setMetaAttributes(maxClip=self.properties.maxClipFloat.value)

    def polyLimitChanged(self):
        """ Poly Limit Changed

        :return:
        :rtype:
        """
        metaNodes = self.selectedMetaNodes()
        for meta in metaNodes:
            meta.setMetaAttributes(polyLimit=self.properties.polyLimitInt.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def bakeBtnClicked(self):
        """ Bake button pressed

        :return:
        :rtype:
        """
        metaNodes = self.selectedMetaNodes()
        for meta in metaNodes:
            meta.bake()

        if not metaNodes:
            output.displayWarning("No tubes found, please select a setup.")

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteBtnClicked(self):
        """ Delete Button pressed

        :return:
        :rtype:
        """
        metaNodes = self.selectedMetaNodes()
        for meta in metaNodes:
            meta.deleteTube()

        if not metaNodes:
            output.displayWarning("No tubes found, please select part of a tube setup.")

    def selectedMetaNodes(self):
        """ Get selected metanodes

        :return:
        :rtype: list[metatubecurve.ZooTubeCurve]
        """
        return base.findRelatedMetaNodesByClassType(zapi.selected(),
                                                    metatubecurve.ZooTubeCurve.__name__)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        for widget in self.widgets():
            widget.createTubeBtn.clicked.connect(self.createTube)
            widget.curveCvBtn.clicked.connect(self.createCurveContext)
            widget.radiusFloat.numSliderChanged.connect(self.radiusChanged)
            widget.radiusFloat.sliderPressed.connect(self.openUndoChunk)
            widget.radiusFloat.sliderReleased.connect(self.closeUndoChunk)
            widget.axisDivisionsInt.numSliderChanged.connect(self.axisDivisionsChanged)
            widget.axisDivisionsInt.sliderPressed.connect(self.openUndoChunk)
            widget.axisDivisionsInt.sliderReleased.connect(self.closeUndoChunk)
            widget.densityFloat.numSliderChanged.connect(self.densityChanged)
            widget.densityFloat.sliderPressed.connect(self.openUndoChunk)
            widget.densityFloat.sliderReleased.connect(self.closeUndoChunk)
            widget.bakeTubeBtn.clicked.connect(self.bakeBtnClicked)
            widget.deleteBtn.clicked.connect(self.deleteBtnClicked)
            widget.maxClipFloat.numSliderChanged.connect(self.maxClipChanged)
            widget.maxClipFloat.sliderPressed.connect(self.openUndoChunk)
            widget.maxClipFloat.sliderReleased.connect(self.closeUndoChunk)

        self.advancedWidget.polyLimitInt.editingFinished.connect(self.polyLimitChanged)

        self.advancedWidget.minClipFloat.numSliderChanged.connect(self.minClipChanged)
        self.advancedWidget.minClipFloat.sliderPressed.connect(self.openUndoChunk)
        self.advancedWidget.minClipFloat.sliderReleased.connect(self.closeUndoChunk)

        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


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
        # Radius Float ---------------------------------------
        tooltip = "The radius of the tube."
        self.radiusFloat = elements.FloatSlider(label="Radius",
                                                defaultValue=0.5,
                                                toolTip=tooltip,
                                                sliderMax=5.0,
                                                sliderAccuracy=2000,
                                                dynamicMax=True)
        # Axis Divisions Float ---------------------------------------
        tooltip = "The amount of divisions around the axis of the tube"
        self.axisDivisionsInt = elements.IntSlider(label="Axis Divisions",
                                                   sliderMin=3,
                                                   defaultValue=12,
                                                   toolTip=tooltip,
                                                   sliderMax=24,
                                                   dynamicMax=True)
        # Density Float ---------------------------------------
        tooltip = "The density of the polygon count of the tube \n" \
                  "More dense is more polygons."
        self.densityFloat = elements.FloatSlider(label="Density",
                                                 defaultValue=2.0,
                                                 toolTip=tooltip,
                                                 sliderMax=10.0,
                                                 dynamicMax=True)
        # Max Float ---------------------------------------
        tooltip = "The minimum start point of the tube relative to the curve. "
        self.maxClipFloat = elements.FloatSlider(label="Max Clip",
                                                 defaultValue=1.0,
                                                 toolTip=tooltip,
                                                 sliderMax=1.0)
        if uiMode == UI_MODE_ADVANCED:
            # Min Float ---------------------------------------
            tooltip = "The minimum end point of the tube relative to the curve. "
            self.minClipFloat = elements.FloatSlider(label="Min Clip",
                                                     defaultValue=0.0,
                                                     toolTip=tooltip,
                                                     sliderMax=1.0)
            # Poly Limit Float ---------------------------------------
            tooltip = "The total polygon limit of the tube. \n " \
                      "Small values will limit the poly count. "
            self.polyLimitInt = elements.IntEdit(label="Poly Limit",
                                                 editText=200000,
                                                 toolTip=tooltip)
        # Create Button ---------------------------------------
        tooltip = "Select a curve and click to create a polygon tube rig"
        self.createTubeBtn = elements.styledButton("Create Tube",
                                                   icon="createTube",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_DEFAULT)
        # Bake Button ---------------------------------------
        tooltip = "Keeps the tube in it's current state while deleting the tube rig. \n" \
                  "Also cleans the mesh by removing it's tube attributes."
        self.bakeTubeBtn = elements.styledButton("Bake",
                                                 icon="bake",
                                                 toolTip=tooltip,
                                                 style=uic.BTN_DEFAULT,
                                                 minWidth=uic.BTN_W_ICN_MED)
        # Create CV Curve Button ------------------------------------
        toolTip = "Create a CV Curve (3 Cubic)"
        self.curveCvBtn = elements.styledButton("",
                                                "curveCv",
                                                toolTip=toolTip,
                                                parent=self,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Create CV Curve Button ------------------------------------
        toolTip = "Delete the tube setup including the mesh, leaves the original curve."
        self.deleteBtn = elements.styledButton("",
                                               "trash",
                                               toolTip=toolTip,
                                               parent=self,
                                               minWidth=uic.BTN_W_ICN_MED)


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
                                         spacing=uic.SREG)
        # Button Layout ---------------------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        buttonLayout.addWidget(self.createTubeBtn, 7)
        buttonLayout.addWidget(self.bakeTubeBtn, 3)
        buttonLayout.addWidget(self.deleteBtn, 1)
        buttonLayout.addWidget(self.curveCvBtn, 1)

        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.axisDivisionsInt)
        mainLayout.addWidget(self.radiusFloat)
        mainLayout.addWidget(self.densityFloat)
        mainLayout.addWidget(self.maxClipFloat)
        mainLayout.addLayout(buttonLayout)


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

        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(hSpacing=uic.SREG)
        gridLayout.addWidget(self.polyLimitInt, 1, 0)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Button Layout ---------------------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        buttonLayout.addWidget(self.createTubeBtn, 7)
        buttonLayout.addWidget(self.bakeTubeBtn, 3)
        buttonLayout.addWidget(self.deleteBtn, 1)
        buttonLayout.addWidget(self.curveCvBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.axisDivisionsInt)
        mainLayout.addWidget(self.radiusFloat)
        mainLayout.addWidget(self.densityFloat)
        mainLayout.addWidget(self.minClipFloat)
        mainLayout.addWidget(self.maxClipFloat)
        mainLayout.addLayout(gridLayout)
        mainLayout.addLayout(buttonLayout)
