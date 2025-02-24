""" ---------- Constraint Toolbox UI (Multiple UI Modes) -------------


"""
from zoovendor.Qt import QtWidgets, QtCore

import maya.mel as mel
from maya import cmds

from zoo.libs.maya.cmds.objutils import constraints
import zoo.libs.maya.cmds.hotkeys.definedhotkeys as hk

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets import elements

from zoo.apps.tooltips import deformertooltips as tt

from zoo.libs.maya.cmds.objutils import locators, matching
from zoo.libs.maya.cmds.rig import riggingmisc

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ConstraintToolbox(toolsetwidget.ToolsetWidget):
    id = "constraintToolbox"
    info = "Maya constraint tools and hotkey trainer."
    uiData = {"label": "Constraint Toolbox",
              "icon": "link",
              "tooltip": "Maya constraint tools and hotkey trainer.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-constraint-toolbox/"}

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
        """ Currently active widget

        :return:
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(ConstraintToolbox, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ConstraintToolbox, self).widgets()

    # ------------------
    # LOGIC
    # ------------------
    @toolsetwidget.ToolsetWidget.undoDecorator
    def matchPosRot(self):
        cmds.matchTransform(cmds.ls(selection=True), pos=True, rot=True, scl=False, piv=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def matchPos(self):
        cmds.matchTransform(cmds.ls(selection=True), pos=True, rot=False, scl=False, piv=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def matchRot(self):
        cmds.matchTransform(cmds.ls(selection=True), pos=False, rot=True, scl=False, piv=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def matchScale(self):
        cmds.matchTransform(cmds.ls(selection=True), pos=False, rot=False, scl=True, piv=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def matchAll(self):
        cmds.matchTransform(cmds.ls(selection=True), pos=True, rot=True, scl=True, piv=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def matchPivot(self):
        cmds.matchTransform(cmds.ls(selection=True), pos=False, rot=False, scl=False, piv=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def groupZeroSelected(self):
        """Groups selected objs, matching a new group to each object and zero's the obj.  objNames can be long names.
        """
        matching.groupZeroObjSelection(freezeScale=True, message=True, removeSuffixName="")

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivot(self):
        """Marks the center of a selection with a tiny locator with display handles on.
        """
        riggingmisc.markCenterPivot()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivotLoc(self):
        """Marks the center of a selection with a locator."""
        locators.createLocatorAndMatch(name=riggingmisc.TEMP_PIVOT_PREFIX,
                                       handle=False, locatorSize=1.0, message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivotMulti(self):
        """Marks the center of a selection with a locator with display handles on.
        """
        locators.createLocatorsMatchMany(name=riggingmisc.TEMP_PIVOT_PREFIX,
                                         handle=True, locatorSize=0.1, message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivotMultiLocators(self):
        """Marks the center of a selection with a locator with display handles on.
        """
        locators.createLocatorsMatchMany(name=riggingmisc.TEMP_PIVOT_PREFIX,
                                         handle=False, locatorSize=1.0, message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteAllPivots(self):
        """Deletes all marked locator pivots in the scene.
        """
        riggingmisc.deleteAllCenterPivots()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def orientConstraint(self):
        maintainOffset = not self.properties.maintainObjectRadio.value
        cmds.orientConstraint(cmds.ls(selection=True), maintainOffset=maintainOffset)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def parentConstraint(self):
        maintainOffset = not self.properties.maintainObjectRadio.value
        cmds.parentConstraint(cmds.ls(selection=True), maintainOffset=maintainOffset)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def pointConstraint(self):
        maintainOffset = not self.properties.maintainObjectRadio.value
        cmds.pointConstraint(cmds.ls(selection=True), maintainOffset=maintainOffset)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def orientConstraint(self):
        maintainOffset = not self.properties.maintainObjectRadio.value
        cmds.orientConstraint(cmds.ls(selection=True), maintainOffset=maintainOffset)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def scaleConstraint(self):
        maintainOffset = not self.properties.maintainObjectRadio.value
        cmds.scaleConstraint(cmds.ls(selection=True), maintainOffset=maintainOffset)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def aimConstraint(self):
        mel.eval("performAimConstraint 0;")

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteConstraintsSelected(self):
        constraints.deleteConstraintsFromSelObj(message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectConstraintsSelected(self):
        constraints.selectConstraints()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def poleVectorConstraint(self):
        cmds.poleVectorConstraint(cmds.ls(selection=True))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def pointOnPolyConstraint(self):
        cmds.pointOnPolyConstraint(cmds.ls(selection=True))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def geoNormalConstraint(self):
        cmds.geometryConstraint(cmds.ls(selection=True))
        cmds.normalConstraint(cmds.ls(selection=True))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def curveConstraint(self):
        cmds.geometryConstraint(cmds.ls(selection=True))
        cmds.tangentConstraint(cmds.ls(selection=True))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def geoConstraint(self):
        cmds.geometryConstraint(cmds.ls(selection=True))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def normalConstraint(self):
        cmds.normalConstraint(cmds.ls(selection=True))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def geoNormalConstraint(self):
        cmds.geometryConstraint(cmds.ls(selection=True))
        cmds.normalConstraint(cmds.ls(selection=True))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def tangentConstraint(self):
        cmds.tangentConstraint(cmds.ls(selection=True))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def motionPath(self):
        mel.eval("AttachToPath")

    # ------------------
    # OPTIONS BOXES
    # ------------------

    def orientConstraintOptions(self):
        mel.eval("performOrientConstraint 1;")

    def parentConstraintOptions(self):
        mel.eval("performParentConstraint 1;")

    def pointConstraintOptions(self):
        mel.eval("performPointConstraint 1;")

    def aimConstraintOptions(self):
        mel.eval("performAimConstraint 1;")

    def normalConstraintOptions(self):
        mel.eval("performNormalConstraint 1")

    def tangentConstraintOptions(self):
        mel.eval("performTangentConstraint 1")

    def scaleConstraintOptions(self):
        mel.eval("performScaleConstraint 1")

    def pointOnPolyConstraintOptions(self):
        mel.eval("performPointOnPolyConstraint 1")

    def motionPathOptions(self):
        mel.eval("AttachToPathOptions")

    def openMotionPathRig(self):
        hk.open_motionPathRig(advancedMode=False)

    def openMatchAndBakeAnim(self):
        hk.open_matchBakeAnim(advancedMode=False)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            # Match -----------------------
            widget.matchPosRotBtn.clicked.connect(self.matchPosRot)
            widget.matchPositionBtn.clicked.connect(self.matchPos)
            widget.matchRotationBtn.clicked.connect(self.matchRot)
            widget.matchScaleBtn.clicked.connect(self.matchScale)
            widget.matchPivotBtn.clicked.connect(self.matchPivot)
            widget.groupZeroObject.clicked.connect(self.groupZeroSelected)
            widget.markCenterPivot.clicked.connect(self.markPivot)
            # Constraints -----------------------
            widget.parentConstraintBtn.clicked.connect(self.parentConstraint)
            widget.pointConstraintBtn.clicked.connect(self.pointConstraint)
            widget.orientConstraintBtn.clicked.connect(self.orientConstraint)
            widget.scaleConstraintBtn.clicked.connect(self.scaleConstraint)
            widget.aimConstraintBtn.clicked.connect(self.aimConstraint)
            widget.poleVectorConstraintBtn.clicked.connect(self.poleVectorConstraint)
            widget.pointOnPolyConstraintBtn.clicked.connect(self.pointOnPolyConstraint)
            widget.geometryConstraintBtn.clicked.connect(self.geoConstraint)
            widget.geoNormalConstraintBtn.clicked.connect(self.geoNormalConstraint)
            widget.curveConstraintBtn.clicked.connect(self.curveConstraint)
            widget.normalConstraintBtn.clicked.connect(self.normalConstraint)
            widget.motionPathBtn.clicked.connect(self.motionPath)
            widget.multiConstraintBtn.clicked.connect(self.openMatchAndBakeAnim)
            widget.selectBtn.clicked.connect(self.selectConstraintsSelected)
            widget.deleteBtn.clicked.connect(self.deleteConstraintsSelected)
            # RIGHT CLICKS -----------------------
            widget.markCenterPivot.createMenuItem(text="Mark Center Pivot - Regular",
                                                  icon=iconlib.icon("locator", size=uic.MAYA_BTN_ICON_SIZE),
                                                  connection=self.markPivot)
            widget.markCenterPivot.createMenuItem(text="Mark Center Pivot - Many",
                                                  icon=iconlib.icon("locator", size=uic.MAYA_BTN_ICON_SIZE),
                                                  connection=self.markPivotMulti)
            widget.markCenterPivot.createMenuItem(text="Mark Center Locator",
                                                  icon=iconlib.icon("locator", size=uic.MAYA_BTN_ICON_SIZE),
                                                  connection=self.markPivotLoc)
            widget.markCenterPivot.createMenuItem(text="Mark Center Locators - Many",
                                                  icon=iconlib.icon("locator", size=uic.MAYA_BTN_ICON_SIZE),
                                                  connection=self.markPivotMultiLocators)
            widget.markCenterPivot.createMenuItem(text="Delete All Pivots",
                                                  icon=iconlib.icon("trash", size=uic.MAYA_BTN_ICON_SIZE),
                                                  connection=self.deleteAllPivots)
            # Window Icon Constrain -----------------------
            windowIcon = iconlib.icon("windowBrowser", size=uic.ZOO_BTN_ICON_SIZE)
            # Parent Constrain -----------------------
            icon = iconlib.icon(":parentConstraint", size=uic.MAYA_BTN_ICON_SIZE)
            widget.parentConstraintBtn.createMenuItem(text="Parent Constraint (Default)", icon=icon,
                                                      connection=self.parentConstraint)
            widget.parentConstraintBtn.createMenuItem(text="Open Options Window", icon=windowIcon,
                                                      connection=self.parentConstraintOptions)
            # Point Constrain -----------------------
            icon = iconlib.icon(":pointConstraint", size=uic.MAYA_BTN_ICON_SIZE)
            widget.pointConstraintBtn.createMenuItem(text="Point Constraint (Default)", icon=icon,
                                                     connection=self.pointConstraint)
            widget.pointConstraintBtn.createMenuItem(text="Open Options Window", icon=windowIcon,
                                                     connection=self.pointConstraintOptions)
            # Orient Constrain -----------------------
            icon = iconlib.icon(":orientConstraint", size=uic.MAYA_BTN_ICON_SIZE)
            widget.orientConstraintBtn.createMenuItem(text="Orient Constraint (Default)", icon=icon,
                                                      connection=self.orientConstraint)
            widget.orientConstraintBtn.createMenuItem(text="Open Options Window", icon=windowIcon,
                                                      connection=self.orientConstraintOptions)
            # Scale Constrain -----------------------
            icon = iconlib.icon(":scaleConstraint", size=uic.MAYA_BTN_ICON_SIZE)
            widget.scaleConstraintBtn.createMenuItem(text="Scale Constraint (Default)", icon=icon,
                                                     connection=self.scaleConstraint)
            widget.scaleConstraintBtn.createMenuItem(text="Open Options Window", icon=windowIcon,
                                                     connection=self.scaleConstraintOptions)
            # Aim Constrain -----------------------
            icon = iconlib.icon(":aimConstraint", size=uic.MAYA_BTN_ICON_SIZE)
            widget.aimConstraintBtn.createMenuItem(text="Aim Constraint (Default)", icon=icon,
                                                   connection=self.aimConstraint)
            widget.aimConstraintBtn.createMenuItem(text="Open Options Window", icon=windowIcon,
                                                   connection=self.aimConstraintOptions)
            # Point On Poly Constrain -----------------------
            icon = iconlib.icon(":pointOnPolyConstraint", size=uic.MAYA_BTN_ICON_SIZE)
            widget.pointOnPolyConstraintBtn.createMenuItem(text="Point On Poly Constraint (Default)", icon=icon,
                                                           connection=self.pointOnPolyConstraint)
            widget.pointOnPolyConstraintBtn.createMenuItem(text="Open Options Window", icon=windowIcon,
                                                           connection=self.pointOnPolyConstraintOptions)
            # Normal Constrain -----------------------
            icon = iconlib.icon(":normalConstraint", size=uic.MAYA_BTN_ICON_SIZE)
            widget.normalConstraintBtn.createMenuItem(text="Normal Constraint (Default)", icon=icon,
                                                      connection=self.normalConstraint)
            widget.normalConstraintBtn.createMenuItem(text="Open Options Window", icon=windowIcon,
                                                      connection=self.normalConstraintOptions)
            # Motion Path -----------------------
            icon = iconlib.icon(":motionPath", size=uic.MAYA_BTN_ICON_SIZE)
            widget.motionPathBtn.createMenuItem(text="Attach To Motion Path (Default)", icon=icon,
                                                connection=self.motionPath)
            widget.motionPathBtn.createMenuItem(text="Open Motion Path Rig Window", icon=windowIcon,
                                                connection=self.openMotionPathRig)
            widget.motionPathBtn.createMenuItem(text="Open Options Window", icon=windowIcon,
                                                connection=self.motionPathOptions)


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
        toolTipDict = tt.constraintsToolbox()
        self.properties = properties
        # MAIN ----------------------------------------------------------------------------------
        # Match btns ---------------------------------------
        self.matchPosRotBtn = self.mayaBtn("Match Position/Rotation", ":teMatchPoses", toolTipDict["matchPosRot"])
        self.matchPositionBtn = self.noIconBtn("Pos", toolTipDict["matchPosition"])
        self.matchRotationBtn = self.noIconBtn("Rot", toolTipDict["matchRotation"])
        self.matchScaleBtn = self.noIconBtn("Scale", toolTipDict["matchScale"])
        self.matchPivotBtn = self.noIconBtn("Pivot", toolTipDict["matchPivot"])
        # Group and match pivot ---------------------
        self.groupZeroObject = self.mayaBtn("Group Zero Object/s", ":folder-new", toolTipDict["groupZeroObject"])
        self.markCenterPivot = self.mayaBtn("Mark Center (Right-Click)", ":locator", toolTipDict["markCenterPivot"])

        # Show Plane Radio Buttons ---------------------
        self.maintainObjectRadio = elements.RadioButtonGroup(radioList=["Maintain Object Position", "Move To Master"],
                                                             parent=self,
                                                             default=0,
                                                             toolTipList=toolTipDict["maintainOffset"],
                                                             margins=(uic.SVLRG2, uic.SREG, uic.SVLRG2, uic.SREG))
        # Constraint Buttons ---------------------
        self.parentConstraintBtn = self.mayaBtn("Parent Constraint (R-Click)", ":parentConstraint",
                                                toolTipDict["parentConstraint"])
        self.pointConstraintBtn = self.mayaBtn("Point Constraint (R-Click)", ":pointConstraint",
                                               toolTipDict["pointConstraint"])
        self.orientConstraintBtn = self.mayaBtn("Orient Constraint (R-Click)", ":orientConstraint",
                                                toolTipDict["orientConstraint"])
        self.scaleConstraintBtn = self.mayaBtn("Scale Constraint (R-Click)", ":scaleConstraint",
                                               toolTipDict["scaleConstraint"])
        self.aimConstraintBtn = self.mayaBtn("Aim Constraint (R-Click)", ":aimConstraint",
                                             toolTipDict["aimConstraint"])
        self.poleVectorConstraintBtn = self.mayaBtn("Pole Vector", ":poleVectorConstraint",
                                                    toolTipDict["poleVectorConstraint"])
        self.pointOnPolyConstraintBtn = self.mayaBtn("Point On Poly (R-Click)", ":pointOnPolyConstraint",
                                                     toolTipDict["pointOnPolyConstraint"])
        self.geometryConstraintBtn = self.mayaBtn("Geo Constraint", ":geometryConstraint",
                                                  toolTipDict["geometryConstraint"])
        self.curveConstraintBtn = self.mayaBtn("Curve Constraint", ":tangentConstraint",
                                               toolTipDict["tangentConstraint"])
        self.normalConstraintBtn = self.mayaBtn("Normal Constraint (R-Click)", ":normalConstraint",
                                                toolTipDict["normalConstraint"])
        self.geoNormalConstraintBtn = self.mayaBtn("Geo Normal Constraint", ":normalConstraint",
                                                   toolTipDict["geoNormalConstraint"])
        self.motionPathBtn = self.mayaBtn("Motion Path (R-Click)", ":motionPath",
                                          toolTipDict["motionPath"])
        self.multiConstraintBtn = self.mayaBtn("Multi Constraint Window", "checkList",
                                      toolTipDict["multiConstraint"])
        self.selectBtn = self.mayaBtn("Select", ":aselect",
                                      toolTipDict["select"])
        self.deleteBtn = self.mayaBtn("Delete", ":deleteActive",
                                      toolTipDict["delete"])

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

    def noIconBtn(self, txt, toolTip):
        """Regular aligned button with a no icon"""
        return elements.leftAlignedButton(txt, icon=None, padding=uic.NO_ICON_BTN_PADDING,
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
        # Match Pos Rot Layout -----------------------------
        matchPosRotLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        matchPosRotLayout.addWidget(self.matchPositionBtn, 1)
        matchPosRotLayout.addWidget(self.matchRotationBtn, 1)
        matchPosRotLayout.addWidget(self.matchScaleBtn, 1)
        matchPosRotLayout.addWidget(self.matchPivotBtn, 1)

        # Match Pos Rot Layout -----------------------------
        selectDeleteLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        selectDeleteLayout.addWidget(self.selectBtn, 1)
        selectDeleteLayout.addWidget(self.deleteBtn, 1)

        # Grid Layout -----------------------------
        matchLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        matchLayout.addWidget(self.matchPosRotBtn, row, 0)
        matchLayout.addLayout(matchPosRotLayout, row, 1)
        row += 1
        matchLayout.addWidget(self.groupZeroObject, row, 0)
        matchLayout.addWidget(self.markCenterPivot, row, 1)
        matchLayout.setColumnStretch(0, 1)
        matchLayout.setColumnStretch(1, 1)

        dividerLayout = elements.vBoxLayout(self, margins=(uic.SMLPAD, uic.SMLPAD, uic.SMLPAD, uic.SMLPAD))
        dividerLayout.addWidget(elements.Divider(parent=self))

        # Constraint Layout -----------------------------
        constraintLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        constraintLayout.addWidget(self.parentConstraintBtn, row, 0)
        constraintLayout.addWidget(self.pointConstraintBtn, row, 1)
        row += 1
        constraintLayout.addWidget(self.orientConstraintBtn, row, 0)
        constraintLayout.addWidget(self.scaleConstraintBtn, row, 1)
        row += 1
        constraintLayout.addLayout(dividerLayout, row, 0, 1, 2)
        row += 1
        constraintLayout.addWidget(self.aimConstraintBtn, row, 0)
        constraintLayout.addWidget(self.poleVectorConstraintBtn, row, 1)
        row += 1
        constraintLayout.addWidget(self.pointOnPolyConstraintBtn, row, 0)
        constraintLayout.addWidget(self.geometryConstraintBtn, row, 1)
        row += 1
        constraintLayout.addWidget(self.curveConstraintBtn, row, 0)
        constraintLayout.addWidget(self.normalConstraintBtn, row, 1)
        row += 1
        constraintLayout.addWidget(self.motionPathBtn, row, 0)
        constraintLayout.addWidget(self.geoNormalConstraintBtn, row, 1)
        row += 1
        constraintLayout.addWidget(self.multiConstraintBtn, row, 0)
        constraintLayout.addLayout(selectDeleteLayout, row, 1)

        constraintLayout.setColumnStretch(0, 1)
        constraintLayout.setColumnStretch(1, 1)

        # Sculpting Main -------------------------------------
        matchCollapsable = elements.CollapsableFrameThin("Match Objects", collapsed=False)
        matchCollapsable.hiderLayout.addLayout(matchLayout)
        matchCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        matchCollapsableLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        matchCollapsableLayout.addWidget(matchCollapsable)

        # Sculpting Misc -------------------------------------
        constraintCollapsable = elements.CollapsableFrameThin("Constrain Objects", collapsed=False)
        constraintCollapsable.hiderLayout.addWidget(self.maintainObjectRadio)
        constraintCollapsable.hiderLayout.addLayout(constraintLayout)
        constraintCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        constraintCollapsableLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        constraintCollapsableLayout.addWidget(constraintCollapsable)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(matchCollapsableLayout)
        mainLayout.addLayout(constraintCollapsableLayout)


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
        pass
