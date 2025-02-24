from zoo.libs.maya.mayacommand import mayaexecutor as executor
from zoo.preferences.interfaces import coreinterfaces

from maya import cmds
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.objutils import curves
from zoo.libs.maya.cmds.meta import metaduplicateoncurve
from zoo.libs.maya.meta import base
from zoovendor.Qt import QtWidgets, QtCore

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

# Dots Menu
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton
from zoo.libs.utils import output
from zoo.libs import iconlib
from zoo.libs.pyqt import utils


UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

DFLT_MULTIPLE = 20
DFLT_DUPLICATE_COMBO = 0
DFLT_AXIS_COMBO = 2
DFLT_FOLLOW_AXIS_COMBO = 4
DFLT_START_POSITION = 0.0
DFLT_END_POSITION = 1.0
DFLT_START_SCALE = 1.0
DFLT_END_SCALE = 1.0
DFLT_START_ROLL = 0.0
DFLT_START_HEAD = 0.0
DFLT_START_TILT = 0.0
DFLT_END_ROLL = 0.0
DFLT_END_HEAD = 0.0
DFLT_END_TILT = 0.0
DFLT_SPACING = 0.0
DFLT_FOLLOW = True
DFLT_FRACTION = True
DFLT_GROUP = True
DFLT_WEIGHT_POS = True
DFLT_WEIGHT_ROT = True
DFLT_WEIGHT_SCALE = True

HIGH_MULTIPLE = 100


class CurveDuplicate(toolsetwidget.ToolsetWidget):
    id = "curveDuplicate"
    info = "Duplicates objects along a curve."
    uiData = {"label": "Duplicate Along Curve",
              "icon": "objectsOnCurve",
              "tooltip": "Duplicates objects along a curve.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-duplicate-along-curve/"
              }

    _metaNode = None  # type: metaduplicateoncurve.MetaDuplicateOnCurve

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
        self.startSelectionCallback()  # start selection callback
        self.updateSelection()

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  GuiWidgets
        """
        return super(CurveDuplicate, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(CurveDuplicate, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def updateSelection(self):
        """ Update metanode based on selection

        :return:
        :rtype:
        """
        if len(list(zapi.selected())) == 0:
            return
        metaNodes = self.selectedMetaNodes()

        if not metaNodes:
            return
        self._metaNode = metaNodes[-1] if len(metaNodes) > 0 else None
        if self._metaNode:
            metaAttrs = self._metaNode.getMetaAttributes()
            if metaAttrs:
                self.properties.multipleInt.value = metaAttrs["multiple"]

                self.properties.upAxisCombo.value = self.strToAxisCombo(metaAttrs["upAxis"], metaAttrs["inverseUp"])
                self.properties.followAxisCombo.value = self.strToAxisCombo(metaAttrs["followAxis"],
                                                                            metaAttrs["inverseFollow"])

                self.properties.startPosFloat.value = metaAttrs["startPosition"]
                self.properties.endPosFloat.value = metaAttrs["endPosition"]
                self.properties.duplicateInstanceCombo.value = metaAttrs["instanced"]
                self.properties.scaleStartFloat.value = metaAttrs["startScale"][0]
                self.properties.scaleEndFloat.value = metaAttrs["endScale"][0]
                self.properties.spacingWeightFSlider.value = metaAttrs["weight"]
                self.properties.rollStartFloat.value = metaAttrs["startRotation"][0]
                self.properties.headingStartFloat.value = metaAttrs["startRotation"][1]
                self.properties.tiltStartFloat.value = metaAttrs["startRotation"][2]
                self.properties.rollEndFloat.value = metaAttrs["endRotation"][0]
                self.properties.headingEndFloat.value = metaAttrs["endRotation"][1]
                self.properties.tiltEndFloat.value = metaAttrs["endRotation"][2]

                self.properties.followModeCheckbox.value = metaAttrs["followRotation"]
                self.properties.groupGeoCheckbox.value = metaAttrs["groupAllGeo"]
                self.properties.fractionModeCheckbox.value = metaAttrs["fractionMode"]
                self.properties.weightPositionCheckbox.value = metaAttrs["weightPosition"]
                self.properties.weightRotationCheckbox.value = metaAttrs["weightRotation"]
                self.properties.weightScaleCheckbox.value = metaAttrs["weightScale"]
                # dots menu Show Original checkbox (not using properties)
                for widget in self.widgets():
                    if metaAttrs["origObjVis"] is not None:  # can be None, must be True or False to set
                        widget.dotsMenu.enabledAction.setChecked(metaAttrs["origObjVis"])

                self.updateFromProperties()

    def strToAxisCombo(self, axisStr, inverse):
        """ String plus inverse to combo index

        :param axisStr:
        :type axisStr:
        :param inverse:
        :type inverse:
        :return:
        :rtype:
        """
        axisStr = "-" + axisStr.upper() if inverse else "+" + axisStr.upper()
        return metaduplicateoncurve.AXIS_LIST.index(axisStr)

    def selectedMetaNodes(self):
        """ Get selected metanodes

        :return:
        :rtype: list[metaduplicateoncurve.MetaDuplicateOnCurve]
        """

        selected = base.findRelatedMetaNodesByClassType(zapi.selected(),
                                                        metaduplicateoncurve.MetaDuplicateOnCurve.__name__)

        return selected

    def selectionChanged(self, sel):
        """ Selection Changed callback event

        :param sel:
        :type sel:
        :return:
        :rtype:
        """
        self.updateSelection()

    def enterEvent(self, event):
        """

        :param event:
        :type event:
        :return:
        :rtype:
        """
        self.updateSelection()

    def createCurveContext(self):
        """Enters the create curve context (user draws cvs).  Uses mel hardcoded 3 bezier curve.
        """

        curves.createCurveContext(degrees=3)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def duplicateAlignObjects(self):
        """ Run the duplicate

        :return:
        :rtype:
        """
        metaNode = metaduplicateoncurve.MetaDuplicateOnCurve(**self.propertiesToMetaAttr())
        if self.checkMaxMultiple():
            metaNode.buildSelected()

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
            output.displayWarning("No curve duplicate setups found. Please select part of a setup")

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteBtnClicked(self):
        """ Delete Button pressed

        :return:
        :rtype:
        """
        metaNodes = self.selectedMetaNodes()
        for meta in metaNodes:
            meta.deleteRig()

        self.updateSelection()

        if not metaNodes:
            output.displayWarning("No curve setups found. Please select part of a setup.")

    @toolsetwidget.ToolsetWidget.undoDecorator
    def updateCurve(self, *args, **kwargs):
        """ Updates curve based on selected metanode data
        """
        metaNodes = self.selectedMetaNodes()

        if metaNodes:
            metaNodes = self.uniqueCurvesOnly(metaNodes)
            for m in metaNodes:
                executor.execute("zoo.maya.duplicateoncurve.edit", meta=m, metaAttrs=self.propertiesToMetaAttr())

    def uniqueCurvesOnly(self, metaNodes):
        """ If metanodes have the same curve, use only the first one

        :param metaNodes:
        :type metaNodes:
        :return:
        :rtype:
        """
        curves = []
        remove = []
        for m in metaNodes:
            if m.curve.value() in curves:
                remove.append(m)
                continue
            curves.append(m.curve.value())
        [metaNodes.remove(r) for r in remove]
        return metaNodes

    def updateMetaNodes(self, metaNodes):
        """ Update the meta node attributes from the toolset properties

        :param metaNode:
        :type metaNode: list[metaduplicateoncurve.MetaDuplicateOnCurve]
        :return:
        :rtype:
        """
        if metaNodes:
            for m in metaNodes:
                self.updateMetaNode(m)

    def updateMetaNode(self, metaNode):
        """ Update the meta node attributes from the toolset properties

        :param metaNode:
        :type metaNode: metaduplicateoncurve.MetaDuplicateOnCurve
        :return:
        :rtype:
        """
        metaNode.setMetaAttributes(**self.propertiesToMetaAttr())

    def propertiesToMetaAttr(self):
        """ Return the properties to something the metanode can use

        :return:
        :rtype:
        """
        # Follow Axis and Up Axis
        upAxis, upAxisInvert, followAxis, followAxisInvert = metaduplicateoncurve.MetaDuplicateOnCurve.upFollowAxis(
            self.properties.upAxisCombo.value,
            self.properties.followAxisCombo.value)
        metaAttrs = {'multiple': self.properties.multipleInt.value,
                     'instanced': bool(self.properties.duplicateInstanceCombo.value),
                     'startPosition': self.properties.startPosFloat.value,
                     'endPosition': self.properties.endPosFloat.value,
                     'weight': self.properties.spacingWeightFSlider.value,
                     'weightScale': self.properties.weightScaleCheckbox.value,
                     'weightPosition': self.properties.weightPositionCheckbox.value,
                     'weightRotation': self.properties.weightRotationCheckbox.value,
                     'startRotation': (self.properties.rollStartFloat.value,
                                       self.properties.headingStartFloat.value,
                                       self.properties.tiltStartFloat.value),
                     'endRotation': (self.properties.rollEndFloat.value,
                                     self.properties.headingEndFloat.value,
                                     self.properties.tiltEndFloat.value),
                     'startScale': [self.properties.scaleStartFloat.value for i in range(3)],
                     'endScale': [self.properties.scaleEndFloat.value for i in range(3)],
                     'upAxis': upAxis,
                     'followAxis': followAxis,
                     'inverseUp': upAxisInvert,
                     'inverseFollow': followAxisInvert,
                     'fractionMode': self.properties.fractionModeCheckbox.value,
                     'groupAllGeo': self.properties.groupGeoCheckbox.value,
                     'followRotation': self.properties.followModeCheckbox.value,
                     'worldUpType': "objectrotation",
                     'autoWorldUpV': True
                     }

        return metaAttrs

    def rebuildCurve(self):
        """ Rebuilds the curve based on meta data
        """
        metaNodes = self.selectedMetaNodes()
        if not metaNodes:
            return
        self.updateMetaNodes(metaNodes)
        selected = None

        # Run the update
        if self.checkMaxMultiple():
            for m in metaNodes:
                select = m.rebuild(selectLast=False)  # False so we can select later
                selected = selected or select

        if selected:
            cmds.select(selected.fullPathName())

    def checkMaxMultiple(self):
        """ Check if its within the multiple range. Warn if larger

        :return:
        :rtype:
        """
        pressed = "A"
        if self.properties.multipleInt.value > HIGH_MULTIPLE:
            pressed = elements.MessageBox.showQuestion(parent=self, title="Slow Operation",
                                                       message="More than {} set for multiple. Potentially slow operation. Continue?".format(
                                                           HIGH_MULTIPLE))

        if pressed == "A":
            return True

    def resetSettings(self):
        """Resets the UI to the default settings, will update any selected objects
        """
        # values
        self.properties.multipleInt.value = DFLT_MULTIPLE
        self.properties.duplicateInstanceCombo.value = DFLT_DUPLICATE_COMBO
        self.properties.upAxisCombo.value = DFLT_AXIS_COMBO
        self.properties.followAxisCombo.value = DFLT_FOLLOW_AXIS_COMBO
        self.properties.startPosFloat.value = DFLT_START_POSITION
        self.properties.endPosFloat.value = DFLT_END_POSITION
        self.properties.scaleStartFloat.value = DFLT_START_SCALE
        self.properties.scaleEndFloat.value = DFLT_END_SCALE
        self.properties.spacingWeightFSlider.value = DFLT_SPACING
        self.properties.rollStartFloat.value = DFLT_START_ROLL
        self.properties.headingStartFloat.value = DFLT_START_HEAD
        self.properties.tiltStartFloat.value = DFLT_START_TILT
        self.properties.rollEndFloat.value = DFLT_END_ROLL
        self.properties.headingEndFloat.value = DFLT_END_HEAD
        self.properties.tiltEndFloat.value = DFLT_END_TILT
        # checkboxes
        self.properties.followModeCheckbox.value = DFLT_FOLLOW
        self.properties.groupGeoCheckbox.value = DFLT_GROUP
        self.properties.fractionModeCheckbox.value = DFLT_FRACTION
        self.properties.weightPositionCheckbox.value = DFLT_WEIGHT_POS
        self.properties.weightRotationCheckbox.value = DFLT_WEIGHT_ROT
        self.properties.weightScaleCheckbox.value = DFLT_WEIGHT_SCALE
        # update
        self.updateCurve()
        self.updateFromProperties()
        # message
        output.displayInfo("Settings Reset: Duplicate Along Curve")

    def updateCurveStart(self):
        self.updateCurve()
        self.openUndoChunk()

    def updateCurveFinished(self):
        self.updateCurve()
        self.closeUndoChunk()

    def showHideOriginal(self, action):
        visibility = action.isChecked()
        metaNodes = self.selectedMetaNodes()
        if not metaNodes:
            return
        for meta in metaNodes:
            meta.setOriginalObjectVis(visibility)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        openCloseChunks = []  # type: list[elements.FloatSlider]
        updateCurveSignals = []
        rebuildCurve = []

        for widget in self.widgets():
            widget.alignObjectsBtn.clicked.connect(self.duplicateAlignObjects)
            widget.curveCvBtn.clicked.connect(self.createCurveContext)
            widget.bakeTubeBtn.clicked.connect(self.bakeBtnClicked)
            widget.deleteBtn.clicked.connect(self.deleteBtnClicked)

            rebuildCurve += [widget.multipleInt.textModified,
                             widget.duplicateInstanceCombo.itemChanged]
            updateCurveSignals += [widget.startPosFloat.numSliderChanged, widget.endPosFloat.numSliderChanged,
                                   widget.rollStartFloat.numSliderChanged, widget.rollEndFloat.numSliderChanged,
                                   widget.scaleStartFloat.numSliderChanged, widget.scaleEndFloat.numSliderChanged,
                                   widget.upAxisCombo.itemChanged, widget.followAxisCombo.itemChanged,
                                   widget.spacingWeightFSlider.numSliderChanged]

            openCloseChunks += [widget.startPosFloat, widget.endPosFloat, widget.rollStartFloat,
                                widget.rollEndFloat, widget.scaleStartFloat, widget.scaleEndFloat,
                                widget.spacingWeightFSlider]

            # Dots Menu
            widget.dotsMenu.resetSettings.connect(self.resetSettings)
            widget.dotsMenu.showOriginal.connect(self.showHideOriginal)

        updateCurveSignals += [self.advancedWidget.headingStartFloat.numSliderChanged,
                               self.advancedWidget.headingEndFloat.numSliderChanged,
                               self.advancedWidget.tiltStartFloat.numSliderChanged,
                               self.advancedWidget.tiltEndFloat.numSliderChanged]

        openCloseChunks += [self.advancedWidget.tiltStartFloat, self.advancedWidget.tiltEndFloat,
                            self.advancedWidget.headingEndFloat, self.advancedWidget.headingStartFloat,
                            ]
        rebuildCurve.append(self.advancedWidget.groupGeoCheckbox.stateChanged)

        self.advancedWidget.followModeCheckbox.stateChanged.connect(lambda x: self.updateCurve())
        self.advancedWidget.fractionModeCheckbox.stateChanged.connect(lambda x: self.updateCurve())
        self.advancedWidget.weightRotationCheckbox.stateChanged.connect(lambda x: self.updateCurve())
        self.advancedWidget.weightPositionCheckbox.stateChanged.connect(lambda x: self.updateCurve())
        self.advancedWidget.weightScaleCheckbox.stateChanged.connect(lambda x: self.updateCurve())

        # Add slider open close undo chunks to the pressed and released
        for w in openCloseChunks:
            w.sliderPressed.connect(self.updateCurveStart)
            w.sliderReleased.connect(self.updateCurveFinished)

        # Update Curve widgets
        for signal in updateCurveSignals:
            signal.connect(self.updateCurve)

        for signal in rebuildCurve:
            signal.connect(self.rebuildCurve)

        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
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
        # Dots Menu -------------------------------------------
        self.dotsMenu = DotsMenu()
        # Multiple Textbox ---------------------------------------
        tooltip = "Duplicate or Instance the object/s by this amount. *Will rebuild rig"
        self.multipleInt = elements.IntEdit(label="Multiple*",
                                            editText=DFLT_MULTIPLE,
                                            toolTip=tooltip,
                                            editRatio=2,
                                            labelRatio=1,
                                            updateOnSlideTick=False)
        # Instance Textbox ---------------------------------------
        tooltip = "Duplicate or Instance objects? *Will rebuild rig"
        self.duplicateInstanceCombo = elements.ComboBoxRegular(label="",
                                                               items=["Duplicate", "Instance"],
                                                               toolTip=tooltip)
        # Object Up Textbox ---------------------------------------
        tooltip = "Set the object's up axis"
        self.upAxisCombo = elements.ComboBoxRegular(label="Up",
                                                    items=metaduplicateoncurve.AXIS_LIST,
                                                    toolTip=tooltip,
                                                    setIndex=DFLT_AXIS_COMBO,
                                                    boxRatio=2,
                                                    labelRatio=1)
        # Object Up Textbox ---------------------------------------
        tooltip = "Set the object's follow axis"
        self.followAxisCombo = elements.ComboBoxRegular(label="Follow",
                                                        items=metaduplicateoncurve.AXIS_LIST,
                                                        toolTip=tooltip,
                                                        setIndex=DFLT_FOLLOW_AXIS_COMBO,
                                                        boxRatio=2,
                                                        labelRatio=1)
        # Start End Titles ---------------------------------------
        self.startTitle = elements.LabelDivider(text="Start")
        self.endTitle = elements.LabelDivider(text="End")
        self.objectAxisTitle = elements.LabelDivider(text="Object Axis")
        # Start Position Textbox ---------------------------------------
        tooltip = "The starting position along the curve. \n" \
                  "The value is either a fraction (0.0 - 1.0) or a distance value. \n" \
                  "See the `Position As Fraction` checkbox."
        self.startPosFloat = elements.FloatSlider(label="",
                                                  defaultValue=DFLT_START_POSITION,
                                                  toolTip=tooltip,
                                                  sliderMin=0.0,
                                                  sliderMax=1.0,
                                                  sliderRatio=2,
                                                  dynamicMax=True
                                                  )
        # End Position Textbox ---------------------------------------
        tooltip = "The end position along the curve. \n" \
                  "The value is either a faction (0.0 - 1.0) or a distance value. \n" \
                  "See the `Position As Fraction` checkbox."
        self.endPosFloat = elements.FloatSlider(label="",
                                                defaultValue=DFLT_END_POSITION,
                                                toolTip=tooltip,
                                                sliderMin=0.0,
                                                sliderMax=1.0,
                                                sliderRatio=2,
                                                dynamicMax=True
                                                )
        # Roll Start Textbox ---------------------------------------
        tooltip = "The start roll rotation value"
        self.rollStartFloat = elements.FloatSlider(label=DFLT_START_ROLL,
                                                   defaultValue=0.0,
                                                   toolTip=tooltip,
                                                   sliderMin=0.0,
                                                   sliderMax=360.0,
                                                   sliderRatio=2,
                                                   dynamicMax=True
                                                   )
        # Roll End Textbox ---------------------------------------
        tooltip = "The end roll rotation value"
        self.rollEndFloat = elements.FloatSlider(label="",
                                                 defaultValue=DFLT_END_ROLL,
                                                 toolTip=tooltip,
                                                 sliderMin=0.0,
                                                 sliderMax=360.0,
                                                 sliderRatio=2,
                                                 dynamicMax=True,
                                                 dynamicMin=True
                                                 )
        # Scale Start Textbox ---------------------------------------
        tooltip = "The start scale value"
        self.scaleStartFloat = elements.FloatSlider(label="",
                                                    defaultValue=DFLT_START_SCALE,
                                                    toolTip=tooltip,
                                                    sliderMin=0.0,
                                                    sliderMax=2.0,
                                                    sliderRatio=2,
                                                    dynamicMax=True
                                                    )
        # Scale End Textbox ---------------------------------------
        tooltip = "The end scale value"
        self.scaleEndFloat = elements.FloatSlider(label="",
                                                  defaultValue=DFLT_END_SCALE,
                                                  toolTip=tooltip,
                                                  sliderMin=0.0,
                                                  sliderMax=2.0,

                                                  sliderRatio=2,
                                                  dynamicMax=True
                                                  )
        # Spacing Weight Slider  ------------------------------------
        tooltip = "The spacing weight between object from one end of the curve or the other. \n" \
                  "A value of 0.0 will evenly space objects."
        self.spacingWeightFSlider = elements.FloatSlider(label="Weight",
                                                         defaultValue=DFLT_SPACING,
                                                         toolTip=tooltip,
                                                         sliderMin=-2.0,
                                                         sliderMax=2.0,
                                                         labelRatio=1,
                                                         editBoxRatio=2,
                                                         sliderAccuracy=300,
                                                         dynamicMax=True,
                                                         dynamicMin=True)

        # Create CV Curve Button ------------------------------------
        toolTip = "Create a CV Curve (3 Cubic). \n" \
                  "Click to create points after entering the tool."
        self.curveCvBtn = elements.styledButton("",
                                                "curveCv",
                                                toolTip=toolTip,
                                                parent=self,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Align Button ---------------------------------------
        tooltip = "Select object or objects and then a NURBS curve. \n" \
                  "The first selected object/s will be duplicated/instanced \n " \
                  "and aligned to the curve."
        self.alignObjectsBtn = elements.styledButton("Align/Duplicate Objects",
                                                     icon="objectsOnCurve",
                                                     toolTip=tooltip,
                                                     style=uic.BTN_DEFAULT)

        # Bake Button ---------------------------------------
        tooltip = "Keeps the it's current state while deleting the rig."
        self.bakeTubeBtn = elements.styledButton("Bake",
                                                 icon="bake",
                                                 toolTip=tooltip,
                                                 style=uic.BTN_DEFAULT,
                                                 minWidth=uic.BTN_W_ICN_MED)

        # Delete curve setup ------------------------------------
        toolTip = "Delete the duplicate on curve setup, leaves the original curve."
        self.deleteBtn = elements.styledButton("",
                                               "trash",
                                               toolTip=toolTip,
                                               parent=self,
                                               minWidth=uic.BTN_W_ICN_MED)

        # Weight Position Checkbox ---------------------------------------
        self.weightTitle = elements.LabelDivider(text="Weight Spacing")

        if uiMode == UI_MODE_ADVANCED:
            # Follow Checkbox ---------------------------------------
            tooltip = "Orient the object/s along the curve?"
            self.followModeCheckbox = elements.CheckBox(label="Follow Rotation",
                                                        toolTip=tooltip,
                                                        checked=DFLT_FOLLOW)
            # Fraction Checkbox ---------------------------------------
            tooltip = "On: Position textbox of 1.0 represents the full curve length and 0.5 is half way. \n" \
                      "Off: The position textbox will be in Maya units, usually cms though  \n " \
                      "curve CVs must be equally spaced"
            self.fractionModeCheckbox = elements.CheckBox(label="Fraction Mode",
                                                          toolTip=tooltip,
                                                          checked=DFLT_FRACTION)

            # Group Geo Checkbox ---------------------------------------
            tooltip = "Will group the geo in a group called `curveName_objs_grp`. *Will Rebuild rig"
            self.groupGeoCheckbox = elements.CheckBox(label="Group All Geo",
                                                      toolTip=tooltip,
                                                      checked=DFLT_GROUP)
            # Tilt Start Textbox ---------------------------------------
            tooltip = "The start heading rotation value"
            self.tiltStartFloat = elements.FloatSlider(label="",
                                                       defaultValue=DFLT_START_TILT,
                                                       toolTip=tooltip,
                                                       sliderMin=0.0,
                                                       sliderMax=360.0,
                                                       sliderRatio=2,
                                                       dynamicMax=True,
                                                       dynamicMin=True
                                                       )
            # Tilt End Textbox ---------------------------------------
            tooltip = "The end tilt rotation value"
            self.tiltEndFloat = elements.FloatSlider(label="",
                                                     defaultValue=DFLT_END_TILT,
                                                     toolTip=tooltip,
                                                     sliderMin=0.0,
                                                     sliderMax=360.0,
                                                     sliderRatio=2,
                                                     dynamicMax=True,
                                                     dynamicMin=True
                                                     )
            # Heading Start Textbox ---------------------------------------
            tooltip = "The start heading rotation value"
            self.headingStartFloat = elements.FloatSlider(label="",
                                                          defaultValue=DFLT_START_HEAD,
                                                          toolTip=tooltip,
                                                          sliderMin=0.0,
                                                          sliderMax=360.0,
                                                          sliderRatio=2,
                                                          dynamicMax=True,
                                                          dynamicMin=True
                                                          )
            # Heading End Textbox ---------------------------------------
            tooltip = "The end heading rotation value"
            self.headingEndFloat = elements.FloatSlider(label="",
                                                        defaultValue=DFLT_END_HEAD,
                                                        toolTip=tooltip,
                                                        sliderMin=0.0,
                                                        sliderMax=360.0,
                                                        sliderRatio=2,
                                                        dynamicMax=True,
                                                        dynamicMin=True
                                                        )

            # Weight Position Checkbox ---------------------------------------
            tooltip = "The weight slider will affect position spacing"
            self.weightPositionCheckbox = elements.CheckBox(label="Weight Position",
                                                            toolTip=tooltip,
                                                            checked=DFLT_WEIGHT_POS)
            # Weight Position Checkbox ---------------------------------------
            tooltip = "The weight slider will affect rotation offsets"
            self.weightRotationCheckbox = elements.CheckBox(label="Weight Rotation",
                                                            toolTip=tooltip,
                                                            checked=DFLT_WEIGHT_ROT)
            # Weight Scale Checkbox ---------------------------------------
            tooltip = "The weight slider will affect scale offsets"
            self.weightScaleCheckbox = elements.CheckBox(label="Weight Scale",
                                                         toolTip=tooltip,
                                                         checked=DFLT_WEIGHT_SCALE)


class DotsMenu(IconMenuButton):
    menuIcon = "menudots"
    resetSettings = QtCore.Signal()
    showOriginal = QtCore.Signal(object)
    _iconColor = None
    def __init__(self, parent=None, networkEnabled=False):
        """
        """
        super(DotsMenu, self).__init__(parent=parent)
        self.networkEnabled = networkEnabled
        if DotsMenu._iconColor is None:
            DotsMenu._iconColor = coreinterfaces.coreInterface().ICON_PRIMARY_COLOR
        self.setIconByName(self.menuIcon, size=16, colors=DotsMenu._iconColor)
        self.setMenuAlign(QtCore.Qt.AlignRight)
        self.setToolTip("File menu. NCloth Wrinkle Creator.")
        # Build the static menu
        # Reset To Defaults --------------------------------------
        reloadIcon = iconlib.iconColorized("reload2", utils.dpiScale(16))
        self.addAction("Reset Settings", connect=lambda: self.resetSettings.emit(), icon=reloadIcon)
        self.addSeparator()
        # Reset To Defaults --------------------------------------
        self.enabledAction = self.addAction("Show Original",
                                            connect=lambda x: self.showOriginal.emit(x),
                                            checkable=True,
                                            checked=self.networkEnabled)


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
        # Multiply Layout ---------------------------------------
        multiplyLayout = elements.hBoxLayout()
        multiplyLayout.addWidget(self.multipleInt, 8)
        duplicateDotsLayout = elements.hBoxLayout()
        duplicateDotsLayout.addWidget(self.duplicateInstanceCombo, 7)
        duplicateDotsLayout.addWidget(self.dotsMenu, 1)
        multiplyLayout.addLayout(duplicateDotsLayout, 8)
        # Up Axis Layout ---------------------------------------
        upAxisLayout = elements.hBoxLayout()
        upAxisLayout.addWidget(self.upAxisCombo, 1)
        upAxisLayout.addWidget(self.followAxisCombo, 1)
        # Start end title Layout ---------------------------------------
        titleLayout = elements.hBoxLayout()
        titleLayout.addSpacing(utils.dpiScale(2))
        titleLayout.addWidget(elements.Divider(), 1)
        titleLayout.addWidget(self.startTitle, 3)
        titleLayout.addWidget(self.endTitle, 3)
        # Start end Pos Layout ---------------------------------------
        posLayout = elements.hBoxLayout()
        posLayout.addWidget(QtWidgets.QLabel("Position"), 1)
        posLayout.addWidget(self.startPosFloat, 3)
        posLayout.addWidget(self.endPosFloat, 3)
        # Start end roll Layout ---------------------------------------
        rollLayout = elements.hBoxLayout()
        rollLayout.addWidget(QtWidgets.QLabel("Roll"), 1)
        rollLayout.addWidget(self.rollStartFloat, 3)
        rollLayout.addWidget(self.rollEndFloat, 3)
        # Start end Scale Layout ---------------------------------------
        scaleLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG))
        scaleLayout.addWidget(QtWidgets.QLabel("Scale"), 1)
        scaleLayout.addWidget(self.scaleStartFloat, 3)
        scaleLayout.addWidget(self.scaleEndFloat, 3)
        # Button Layout ---------------------------------------
        btnLayout = elements.hBoxLayout(spacing=uic.SPACING)
        btnLayout.addWidget(self.alignObjectsBtn, 7)
        btnLayout.addWidget(self.bakeTubeBtn, 3)
        btnLayout.addWidget(self.deleteBtn, 1)
        btnLayout.addWidget(self.curveCvBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(multiplyLayout)
        mainLayout.addWidget(self.objectAxisTitle)
        mainLayout.addLayout(upAxisLayout)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(posLayout)
        mainLayout.addLayout(rollLayout)
        mainLayout.addLayout(scaleLayout)
        mainLayout.addWidget(self.weightTitle)
        mainLayout.addWidget(self.spacingWeightFSlider)
        mainLayout.addLayout(btnLayout)


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
        # Follow Fraction Layout ---------------------------------------
        followLayout = elements.hBoxLayout(margins=(uic.SLRG, uic.SREG, uic.SLRG, uic.SLRG), spacing=uic.SVLRG)
        followLayout.addWidget(self.followModeCheckbox, 1)
        followLayout.addWidget(self.fractionModeCheckbox, 1)
        followLayout.addWidget(self.groupGeoCheckbox, 1)
        # Multiply Layout ---------------------------------------
        multiplyLayout = elements.hBoxLayout()
        multiplyLayout.addWidget(self.multipleInt, 8)
        duplicateDotsLayout = elements.hBoxLayout()
        duplicateDotsLayout.addWidget(self.duplicateInstanceCombo, 7)
        duplicateDotsLayout.addWidget(self.dotsMenu, 1)
        multiplyLayout.addLayout(duplicateDotsLayout, 8)
        # Up Axis Layout ---------------------------------------
        upAxisLayout = elements.hBoxLayout()
        upAxisLayout.addWidget(self.upAxisCombo, 1)
        upAxisLayout.addWidget(self.followAxisCombo, 1)
        # Start end title Layout ---------------------------------------
        titleLayout = elements.hBoxLayout()
        titleLayout.addSpacing(utils.dpiScale(2))
        titleLayout.addWidget(elements.Divider(), 1)
        titleLayout.addWidget(self.startTitle, 3)
        titleLayout.addWidget(self.endTitle, 3)
        # Start end Pos Layout ---------------------------------------
        posLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG))
        posLayout.addWidget(QtWidgets.QLabel("Position"), 1)
        posLayout.addWidget(self.startPosFloat, 3)
        posLayout.addWidget(self.endPosFloat, 3)
        # Start end roll Layout ---------------------------------------
        rollLayout = elements.hBoxLayout()
        rollLayout.addWidget(QtWidgets.QLabel("Roll"), 1)
        rollLayout.addWidget(self.rollStartFloat, 3)
        rollLayout.addWidget(self.rollEndFloat, 3)
        # Start end Heading Layout ---------------------------------------
        headingLayout = elements.hBoxLayout()
        headingLayout.addWidget(QtWidgets.QLabel("Heading"), 1)
        headingLayout.addWidget(self.headingStartFloat, 3)
        headingLayout.addWidget(self.headingEndFloat, 3)
        # Start end Tilt Layout ---------------------------------------
        tiltLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG))
        tiltLayout.addWidget(QtWidgets.QLabel("Tilt"), 1)
        tiltLayout.addWidget(self.tiltStartFloat, 3)
        tiltLayout.addWidget(self.tiltEndFloat, 3)
        # Start end Scale Layout ---------------------------------------
        scaleLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG))
        scaleLayout.addWidget(QtWidgets.QLabel("Scale"), 1)
        scaleLayout.addWidget(self.scaleStartFloat, 3)
        scaleLayout.addWidget(self.scaleEndFloat, 3)
        # Keep Live Layout ---------------------------------------
        weightCheckLayout = elements.hBoxLayout(margins=(uic.SLRG, uic.SREG, uic.SLRG, uic.SREG))
        weightCheckLayout.addWidget(self.weightPositionCheckbox, 1)
        weightCheckLayout.addWidget(self.weightRotationCheckbox, 1)
        weightCheckLayout.addWidget(self.weightScaleCheckbox, 1)
        # Slider Layout ---------------------------------------
        sliderLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG))
        sliderLayout.addWidget(self.spacingWeightFSlider)
        # Button Layout ---------------------------------------
        btnLayout = elements.hBoxLayout(spacing=uic.SPACING)
        btnLayout.addWidget(self.alignObjectsBtn, 7)
        btnLayout.addWidget(self.bakeTubeBtn, 3)
        btnLayout.addWidget(self.deleteBtn, 1)
        btnLayout.addWidget(self.curveCvBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(followLayout)
        mainLayout.addLayout(multiplyLayout)
        mainLayout.addWidget(self.objectAxisTitle)
        mainLayout.addLayout(upAxisLayout)
        mainLayout.addLayout(titleLayout)
        mainLayout.addLayout(posLayout)
        mainLayout.addLayout(rollLayout)
        mainLayout.addLayout(headingLayout)
        mainLayout.addLayout(tiltLayout)
        mainLayout.addLayout(scaleLayout)
        mainLayout.addWidget(self.weightTitle)
        mainLayout.addLayout(weightCheckLayout)
        mainLayout.addLayout(sliderLayout)

        mainLayout.addLayout(btnLayout)
