""" ---------- Motion Path Rig -------------
UI for creating motion path rigs.

Author: Andrew Silke
"""
from functools import partial

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.apps.toolsetsui import toolsetcallbacks
from zoo.libs.pyqt import uiconstants as uic, keyboardmouse
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output

from maya import cmds  # for callbacks
from zoo.libs.maya.cmds.objutils import curves
from zoo.libs.maya.cmds.rig import motionpaths
from zoo.libs.maya.cmds.meta import metamotionpathrig

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

XYZ_LIST = ["X", "Y", "Z", "-X", "-Y", "-Z"]
XYZ_LOWERCASE_LIST = ["x", "y", "z", "-x", "-y", "-z"]

WORLD_UP_TYPES = ["Scene Up", "Object Up", "Object Rotation", "Vector", "Normal"]


class MotionPathRig(toolsetwidget.ToolsetWidget):
    id = "motionPathRig"
    info = "Template file for building new GUIs."
    uiData = {"label": "Motion Path Rig",
              "icon": "motionPathRig",
              "tooltip": "Template file for building new GUIs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-motion-path-rig/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.toolsetWidget = self  # needed for callback decorators

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
        self.metaNodes = list()
        self.updateEnableDisable()
        self.updateSelection()
        self.uiConnections()
        self.startSelectionCallback()  # start selection callback

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
        return super(MotionPathRig, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(MotionPathRig, self).widgets()

    # ------------------
    # SELECTION CALLBACKS
    # ------------------

    def selectionChanged(self, selection):
        """ Selection Changed callback event

        :param selection:  The selection from zapi
        :type selection: selected objects, only dag objects not components
        """
        if not selection:  # then still may be a selection TODO add this to internal callbacks maybe?
            selection = cmds.ls(selection=True)  # catches component and node selections
            if not selection:  # then nothing is selected
                self.metaNodes = list()
                return
        self.updateSelection()

    def updateSelection(self):
        """ Update metanode based on selection
        """
        self.metaNodes = list(metamotionpathrig.selectedMetaNodes())
        if self.properties.upObjTxt.value and not self.metaNodes:
            self.properties.upObjTxt.value = ""
            self.properties.curveObjTxt.value = ""
            self.properties.worldUpTypeCombo.value = 3
        self.updateUI()

    def updateEnableDisable(self):
        """Hides and shows the axis combo boxes"""
        upObjectEnable = False
        upVectorEnable = False
        rotFollow = self.properties.followCheckbox.value
        upType = self.properties.worldUpTypeCombo.value
        if (upType == 1 or upType == 2) and rotFollow:
            upObjectEnable = True
        if (upType == 2 or upType == 3) and rotFollow:
            upVectorEnable = True
        if not rotFollow:
            self.properties.upVCtrlCheckbox.value = 0
        for widget in self.widgets():
            widget.upAxisCombo.setEnabled(rotFollow)
            widget.upVCtrlCheckbox.setEnabled(rotFollow)
            widget.followAxisCombo.setEnabled(rotFollow)
            widget.worldUpTypeCombo.setEnabled(rotFollow)
            widget.upVectorFloat.setEnabled(upVectorEnable)
            widget.upObjTxt.setEnabled(upObjectEnable)
            widget.upVCtrlScale.setEnabled(self.properties.upVCtrlCheckbox.value)
            widget.scaleVCtrlNegBtn.setEnabled(self.properties.upVCtrlCheckbox.value)
            widget.scaleVCtrlPosBtn.setEnabled(self.properties.upVCtrlCheckbox.value)
            widget.upVCtrlScale.setEnabled(self.properties.upVCtrlCheckbox.value)
            widget.addUpObjTxtBtn.setEnabled(upObjectEnable)
        self.updateFromProperties()
        self.updateTree(delayed=True)

    def _referenceCheck(self):
        """Checks for referenced and disables the group checkbox if so."""
        # Referenced creation check -----------
        referenced = False
        if metamotionpathrig.referenceSelectionCheck():  # then referenced objs found
            referenced = True
            self.properties.groupCheckbox.value = False
        for widget in self.widgets():
            widget.groupCheckbox.setDisabled(referenced)  # disabled if referenced object was found
        return referenced

    def updateUI(self):
        """Pulls from the first selected meta node and pulls data into the UI"""
        referenced = self._referenceCheck()
        # Bail if no meta -----------------
        if not self.metaNodes:
            self.updateEnableDisable()
            self.updateFromProperties()
            return
        # Uses the first meta node found ------------------
        self.properties.pathSlider.value = self.metaNodes[0].getPath()
        self.properties.upAxisCombo.value = XYZ_LOWERCASE_LIST.index(self.metaNodes[0].upAxis())
        self.properties.followAxisCombo.value = XYZ_LOWERCASE_LIST.index(self.metaNodes[0].followAxis())
        self.properties.constrainCheckbox.value = self.metaNodes[0].parentConstrained()
        self.properties.worldUpTypeCombo.value = self.metaNodes[0].worldUpType()
        self.properties.upVectorFloat.value = self.metaNodes[0].worldUpVector()
        self.properties.upObjTxt.value = self.metaNodes[0].worldUpObject()
        self.properties.curveObjTxt.value = self.metaNodes[0].getCurveStr()
        self.properties.upVCtrlCheckbox.value = self.metaNodes[0].upVectorControl()
        upVScale = self.metaNodes[0].upVCtrlScale()
        if upVScale:
            self.properties.upVCtrlScale.value = self.metaNodes[0].upVCtrlScale()
        if not referenced:
            self.properties.groupCheckbox.value = self.metaNodes[0].grouped()
        self.properties.followCheckbox.value = self.metaNodes[0].follow()
        self.updateEnableDisable()  # Show hide the combos based on the rotation follow state, updates the UI

    def updateUpVectorControlChange(self):
        if not self.properties.upVCtrlCheckbox.value:
            self.properties.worldUpTypeCombo.value = 3  # Update UI as meta has already been set
            self.properties.upVectorFloat.value = [0.0, 1.0, 0.0]
        else:
            self.properties.worldUpTypeCombo.value = 2  # type set to object up updateUI will do the rest if meta
        self.updateUI()

    # ------------------
    # MOUSE OVER UI
    # ------------------

    def enterEvent(self, event):
        """Update selection on enter event
        """
        self.updateSelection()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def upVectorControl(self, value=None):
        """Builds and deletes the upVector rig"""
        if not self.metaNodes:
            self.updateUpVectorControlChange()
            return
        for meta in self.metaNodes:
            meta.setUpVectorControl(self.properties.upVCtrlCheckbox.value)
        metamotionpathrig.selectControlObjs(self.metaNodes)
        self.updateUpVectorControlChange()

    def setPathAttr(self):
        """Sets the path attribute on selected meta, undo is handled by the slider"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.setPath(self.properties.pathSlider.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setKey(self):
        """Keys the control object at the current time with current settings"""
        # TODO: Handle auto key and key on release.
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.keyPath()  # keys at current time

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def reverseCurves(self):
        """Reverses the curves on the selected rigs"""
        if not self.metaNodes:
            return
        metamotionpathrig.reverseCurvesMetaNodes(self.metaNodes)
        metamotionpathrig.selectControlObjs(self.metaNodes)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def switchCurves(self):
        """Switches the selected motion path objects onto a new curve
        Select
        """
        metamotionpathrig.switchCurvesSelection()
        metamotionpathrig.selectControlObjs(self.metaNodes)

    def createCurveContext(self):
        """Enters the create curve context (user draws cvs).  Uses mel hardcoded 3 bezier curve.
        """
        curves.createCurveContext(degrees=3)

    def addCurveObject(self):
        """Adds a surface object to the UI from the scene"""
        curve = motionpaths.setCurveObjSelection()
        if not curve:
            return
        self.properties.curveObjTxt.value = curve
        # Add as zapi?
        self.updateFromProperties()
        if self.metaNodes:
            self.switchCurves()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def typeCurve(self, text=""):
        """Run when the text box is entered with a new name"""
        curve = motionpaths.setCurveObj(self.properties.curveObjTxt.value)
        if not curve:
            return
        if self.metaNodes:
            metamotionpathrig.switchCurves(curve, self.metaNodes)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetwidget.ToolsetWidget.undoDecorator
    def addUpObjectObject(self):
        """Adds an up object through the UI"""
        upObj = motionpaths.setUpObjSelection()
        if not upObj:
            return
        self.properties.upObjTxt.value = upObj
        # Add as zapi?
        self.updateFromProperties()
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.setWorldUpObject(self.properties.upObjTxt.value)

    def typeUpObject(self):
        """Run when the text box is entered with a new name"""
        if self.properties.upObjTxt.value == "":
            if not self.metaNodes:
                return
            for meta in self.metaNodes:
                meta.setWorldUpObject(self.properties.upObjTxt.value)
            return
        upObj = motionpaths.setUpObj(self.properties.upObjTxt.value)
        if not upObj:
            return
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.setWorldUpObject(self.properties.upObjTxt.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def scaleUpVCtrlBtns(self, positive=True):
        """UI function that scales all controls from any selected part of the rig, does not affect transform scale

        :param positive: is the scale bigger positive=True, or smaller positive=False
        :type positive: bool
        """
        multiplier, reset = keyboardmouse.ctrlShiftMultiplier()  # for alt shift and ctrl keys with left click
        scale = 5.0 * multiplier  # if control or shift is held down
        if positive:
            scale = 1 + (scale * .01)  # 1.0 becomes 1.05
        else:  # negative
            scale = 1 - (scale * .01)  # 1.0 becomes 0.95
        if not self.metaNodes:
            if not reset:
                self.properties.upVCtrlScale.value *= scale
            if reset:
                self.properties.upVCtrlScale.value = metamotionpathrig.UPV_CTRL_SCALE
            self.updateFromProperties()
            return
        for meta in self.metaNodes:  # Do the scale
            meta.setUpVCtrlRelScale(scale, reset=reset)
        self.updateUI()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def scaleUpVCtrl(self, value=None):
        if not self.metaNodes:
            return
        for meta in self.metaNodes:  # Do the scale
            meta.setUpVCtrlScale(self.properties.upVCtrlScale.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def setUpAxis(self, state):
        """Sets the up axis of all selected meta node rigs"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.setUpAxis(XYZ_LOWERCASE_LIST[self.properties.upAxisCombo.value])

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def setFollowAxis(self, state):
        """Sets the follow axis of all selected meta node rigs"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.setFollowAxis(XYZ_LOWERCASE_LIST[self.properties.followAxisCombo.value])
        metamotionpathrig.selectControlObjs(self.metaNodes)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def setWorldUpType(self, state):
        """Sets the world up type on all selected meta node rigs"""
        self.updateEnableDisable()
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.setWorldUpType(self.properties.worldUpTypeCombo.value)
        metamotionpathrig.selectControlObjs(self.metaNodes)
        self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def setWorldUpVector(self, value=None):
        """Sets the world up vector on all selected meta node rigs"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.setWorldUpVector(self.properties.upVectorFloat.value)
        metamotionpathrig.selectControlObjs(self.metaNodes)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def setParentConstraint(self, state=False):
        """Sets the "Constrained" state of the re, if changed the rif will completely rebuild"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.setParentConstrained(self.properties.constrainCheckbox.value)
        metamotionpathrig.selectControlObjs(self.metaNodes)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def setGrouped(self, state=False):
        """Sets the "grouped" state of the re, if changed the rif will completely rebuild"""
        if not self.metaNodes:
            return
        reference = False
        for meta in self.metaNodes:
            if not meta.isControlObjReferenced():  # not referenced so ok
                meta.setGrouped(self.properties.groupCheckbox.value)
            else:
                output.displayWarning("Object {} is referenced and cannot be grouped".format(meta.getControlObjStr()))
                reference = True
        if not reference:
            metamotionpathrig.selectControlObjs(self.metaNodes)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def setFollow(self, state=False):
        """Sets the "grouped" state of the re, if changed the rif will completely rebuild"""
        # Actually set the follow -------------
        if not self.metaNodes:
            self.updateEnableDisable()
            return
        for meta in self.metaNodes:
            meta.setFollow(self.properties.followCheckbox.value, message=True)
        metamotionpathrig.selectControlObjs(self.metaNodes)
        self.updateEnableDisable()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def motionPathRig(self):
        """"""
        self.metaNodes = \
            metamotionpathrig.buildMotionPathRigsSelection(curve=self.properties.curveObjTxt.value,
                                                           group=self.properties.groupCheckbox.value,
                                                           followAxis=XYZ_LOWERCASE_LIST[
                                                               self.properties.followAxisCombo.value],
                                                           upAxis=XYZ_LOWERCASE_LIST[
                                                               self.properties.upAxisCombo.value],
                                                           worldUpVector=self.properties.upVectorFloat.value,
                                                           worldUpObject=self.properties.upObjTxt.value,
                                                           worldUpType=self.properties.worldUpTypeCombo.value,
                                                           parentConstrain=self.properties.constrainCheckbox.value,
                                                           follow=self.properties.followCheckbox.value,
                                                           upVectorControl=self.properties.upVCtrlCheckbox.value,
                                                           upVScale=self.properties.upVCtrlScale.value,
                                                           message=True)
        if not self.metaNodes:
            return
        metamotionpathrig.selectControlObjs(self.metaNodes)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def deleteRigs(self):
        """Sets the follow axis of all selected meta node rigs"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.deleteRig()
        self.metaNodes = list()
        # deleting can leave behind the up vector control and curve in the UI so remove if remaining
        if self.properties.upObjTxt.value:
            self.properties.upObjTxt.value = ""
            self.properties.curveObjTxt.value = ""
            self.properties.worldUpTypeCombo.value = 3
            self.updateFromProperties()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            # Buttons
            widget.scaleVCtrlNegBtn.clicked.connect(partial(self.scaleUpVCtrlBtns, positive=False))
            widget.scaleVCtrlPosBtn.clicked.connect(partial(self.scaleUpVCtrlBtns, positive=True))
            widget.keyBtn.clicked.connect(self.setKey)
            widget.moPathSelBtn.clicked.connect(self.motionPathRig)
            widget.addCurveTxtBtn.clicked.connect(self.addCurveObject)
            widget.addUpObjTxtBtn.clicked.connect(self.addUpObjectObject)
            widget.curveCvBtn.clicked.connect(self.createCurveContext)
            widget.reverseBtn.clicked.connect(self.reverseCurves)
            widget.switchCurvesBtn.clicked.connect(self.switchCurves)
            widget.deleteBtn.clicked.connect(self.deleteRigs)
            # Combos
            widget.upAxisCombo.itemChanged.connect(self.setUpAxis)
            widget.followAxisCombo.itemChanged.connect(self.setFollowAxis)
            widget.worldUpTypeCombo.itemChanged.connect(self.setWorldUpType)
            # Checkboxes
            widget.constrainCheckbox.stateChanged.connect(self.setParentConstraint)
            widget.groupCheckbox.stateChanged.connect(self.setGrouped)
            widget.followCheckbox.stateChanged.connect(self.setFollow)
            widget.upVCtrlCheckbox.stateChanged.connect(self.upVectorControl)
            # Slider
            widget.pathSlider.numSliderChanged.connect(self.setPathAttr)
            widget.pathSlider.sliderPressed.connect(self.openUndoChunk)
            widget.pathSlider.sliderReleased.connect(self.closeUndoChunk)
            # Vector Float
            widget.upVectorFloat.textModified.connect(self.setWorldUpVector)
            widget.upVCtrlScale.textModified.connect(self.scaleUpVCtrl)
            # Text boxes
            # widget.upObjTxt.textModified.connect(self.typeUpObject)  # does not include sending an empty string
            widget.upObjTxt.editingFinished.connect(self.typeUpObject)  # includes sending empty string
            widget.curveObjTxt.textModified.connect(self.typeCurve)
        # connect callbacks
        self.selectionCallbacks.callback.connect(self.selectionChanged)
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


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
        # World Up Combo -------------------------------------------
        tooltip = "Set the world up vector by type: \n" \
                  " - Scene Up: Uses the scene up Y. \n" \
                  " - Object Up: Uses an object as an aim vector. \n" \
                  " - Object Rotation Up: Uses an objects rotation as the up. \n" \
                  " - Vector (World Up): Uses the x, y z textbox as a vector in world space. \n" \
                  " - Normal: Uses the point on curve normal direction."
        self.worldUpTypeCombo = elements.ComboBoxRegular("Up Type", items=WORLD_UP_TYPES, toolTip=tooltip,
                                                         labelRatio=10, boxRatio=23)
        # Up Vector -------------------------------------------
        tooltip = "The `Up Vector` (x, y, z) direction. Default 0.0, 1.0, 0,0 is `Y Up`.: \n" \
                  "Use with the Up Types: \n" \
                  " - Object Rotation Up: Specifies which axis of the object is the up direction. \n" \
                  " - Vector (World Up): Specifies the up vector in world coordinates. "
        self.upVectorFloat = elements.VectorLineEdit("", value=[0.0, 1.0, 0.0], toolTip=tooltip)
        # Up Object -------------------------------------------
        tooltip = "Specifies the up object. \n" \
                  "Used if the Up Type is set to `Object Up` or `Object Rotation Up` \n\n" \
                  "Note:  To assign to an existing rig, use shift-select to add select the object \n" \
                  "and then use the arrow button to enter the object. Supports multiple rig select."
        self.upObjTxt = elements.StringEdit(label="Up Object",
                                            editPlaceholder="Add Object",
                                            toolTip=tooltip,
                                            editRatio=52,
                                            labelRatio=10)
        tooltip = "Adds an Up Object from the scene, can be any object (transform node). \n" \
                  "Used if the Up Type is set to `Object Up` or `Object Rotation Up` \n\n" \
                  "Note:  To assign to an existing rig, use shift-select to add select the object \n" \
                  "and then use this button to enter the object. Supports multiple rig select."
        self.addUpObjTxtBtn = elements.styledButton("",
                                                    "arrowLeft",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15)
        # Curve Textbox and get btn ---------------------------------------
        tooltip = "Optionally add the name of the curve object for the animated objects to follow. \n" \
                  "If the name is not given the curve should be the last selected object."
        self.curveObjTxt = elements.StringEdit(label="Curve",
                                               editPlaceholder="Add Curve",
                                               toolTip=tooltip,
                                               editRatio=52,
                                               labelRatio=10)
        tooltip = "Select a curve object and press to add the name of a curve object."
        self.addCurveTxtBtn = elements.styledButton("",
                                                    "arrowLeft",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15)
        # Up Vector Control Checkbox ---------------------------------------
        tooltip = "Builds an `Up Vector` arrow control with the rig.  The control can be used to manually \n" \
                  "set and keyframe the up axis of the rig.  \n" \
                  "Useful in scenarios where the curve travels straight up and causes flipping. \n\n" \
                  "Note: Checking and unchecking this checkbox will build/delete the control on live rigs. "
        self.upVCtrlCheckbox = elements.CheckBox("Up Vector Control", checked=True, toolTip=tooltip,
                                                 right=False)
        # Up Vector Scale Textbox ---------------------------------------
        tooltip = "The absolute size of the `Up Vector Control`."
        self.upVCtrlScale = elements.FloatEdit("Up V Ctrl Scale", editText=metamotionpathrig.UPV_CTRL_SCALE,
                                               rounding=2, toolTip=tooltip)
        # Up Vector Scale Buttons ---------------------------------------
        toolTip = "Scales the `Up Vector Control` larger by 5%. Select any part of the rig. \n" \
                  "Hold shift for faster, ctrl for slower and alt for reset."
        self.scaleVCtrlPosBtn = elements.styledButton("",
                                                      "scaleUp",
                                                      toolTip=toolTip,
                                                      parent=self,
                                                      minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Scales the `Up Vector Control` smaller by 5%. Select any part of the rig. \n" \
                  "Hold shift for faster, ctrl for slower and alt for reset."
        self.scaleVCtrlNegBtn = elements.styledButton("",
                                                      "scaleDown",
                                                      toolTip=toolTip,
                                                      parent=self,
                                                      minWidth=uic.BTN_W_ICN_MED)
        # Group Checkbox ---------------------------------------
        tooltip = "Groups the control objects so they can be keyed on translation and rotation. \n" \
                  "Objects cannot be referenced children. \n" \
                  "Note: If greyed out some target objects may be referenced."
        self.groupCheckbox = elements.CheckBox("Group Control Obj", checked=False, toolTip=tooltip, right=False)
        # Follow Checkbox ---------------------------------------
        tooltip = "On: The Rotation will follow along the path.  \n" \
                  "Off:  The Rotation will not follow the path, \n" \
                  "only the translation will move with the path."
        self.followCheckbox = elements.CheckBox("Rotation Follow", checked=True, toolTip=tooltip, right=False)
        # Up Axis Combo ---------------------------------------
        tooltip = "The object's axis direction that faces up. \n" \
                  "Note: The up direction will depend on the `Up Type` settings \n" \
                  "found in the advanced section. "
        self.upAxisCombo = elements.ComboBoxRegular(label="Up",
                                                    items=XYZ_LIST,
                                                    setIndex=1,
                                                    toolTip=tooltip,
                                                    labelRatio=10,
                                                    boxRatio=24)
        # Follow Axis Combo ---------------------------------------
        tooltip = "The object's forward axis as it travels along the curve."
        self.followAxisCombo = elements.ComboBoxRegular(label="Follow",
                                                        items=XYZ_LIST,
                                                        setIndex=2,
                                                        toolTip=tooltip,
                                                        labelRatio=10,
                                                        boxRatio=24)
        # Slider ----------------------------------------
        tooltip = "Sets the `path` attribute on live rigs. "
        self.pathSlider = elements.FloatSlider(label="Path",
                                               defaultValue=0.0,
                                               toolTip=tooltip,
                                               labelBtnRatio=12,
                                               sliderRatio=20,
                                               labelRatio=14,
                                               editBoxRatio=20,
                                               decimalPlaces=3)
        # Key Btn ------------------------------------
        toolTip = "Keyframe the path attribute at the current time."
        self.keyBtn = elements.styledButton("",
                                            "key",
                                            toolTip=toolTip,
                                            parent=self,
                                            minWidth=uic.BTN_W_ICN_MED)
        # Create CV Curve Btn ------------------------------------
        toolTip = "Create a CV curve (3 Cubic). Click to create points after running."
        self.curveCvBtn = elements.styledButton("",
                                                "curveCv",
                                                toolTip=toolTip,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Reverse Curve Btn ------------------------------------
        toolTip = "Reverse the curve direction, select any existing rig and run."
        self.reverseBtn = elements.styledButton("",
                                                icon="reverseCurves",
                                                toolTip=toolTip,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Switch Curve Btn ------------------------------------
        toolTip = "Switch a rigs to a new curve \n" \
                  "1. Select existing motionPath rig object/s \n" \
                  "2. Select the new curve to transfer to. \n" \
                  "3. Run"
        self.switchCurvesBtn = elements.styledButton("",
                                                     icon="switchCurves",
                                                     toolTip=toolTip,
                                                     minWidth=uic.BTN_W_ICN_MED)
        # Animate Along Curve Btn ---------------------------------------
        toolTip = "Animates/rigs the selected objects along a curve with Maya's `motion path` nodes. \n" \
                  "New attributes are created on the selected objects for animation.  \n\n" \
                  " - Select objects/controls and then a path curve last, and run. \n" \
                  " - Or add a curve name in advanced UI mode, and select objects and run. \n\n" \
                  "Selected objects will be snapped to the curve, the objects can be animated with \n" \
                  "the new attribute named `path` in the channel box or within this UI."
        self.moPathSelBtn = elements.styledButton("Motion Path Rig",
                                                      icon="motionPathRig",
                                                      toolTip=toolTip,
                                                      style=uic.BTN_DEFAULT)
        # Parent Constrain -------------------------------------
        tooltip = "Parent constrains objects to motion path groups. \n" \
                  "Useful for referenced objects or objects inside hierarchies with offsets."
        self.constrainCheckbox = elements.CheckBox("Parent Constrain", checked=False, toolTip=tooltip)
        # Delete Rig Button ------------------------------------
        toolTip = "Deletes selected motion path rigs."
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
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Checkbox Layout --------------------------
        checkboxLayout = elements.hBoxLayout(spacing=uic.SVLRG, margins=(uic.SLRG, uic.SREG, uic.SLRG, uic.SREG))
        checkboxLayout.addWidget(self.followCheckbox, 1)
        checkboxLayout.addWidget(self.constrainCheckbox, 1)
        checkboxLayout.addWidget(self.groupCheckbox, 1)
        # scaleButton layout -----------------------------
        scaleButtonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        scaleButtonLayout.addWidget(self.scaleVCtrlNegBtn, 1)
        scaleButtonLayout.addWidget(self.scaleVCtrlPosBtn, 1)
        # Checkbox2 Layout --------------------------
        checkbox2Layout = elements.hBoxLayout(spacing=uic.SVLRG, margins=(uic.SLRG, uic.SREG, uic.SLRG, uic.SREG))
        checkbox2Layout.addWidget(self.upVCtrlCheckbox, 10)
        checkbox2Layout.addWidget(self.upVCtrlScale, 11)
        checkbox2Layout.addLayout(scaleButtonLayout, 1)
        # Slider Layout --------------------------
        sliderLayout = elements.hBoxLayout(spacing=uic.SPACING)
        sliderLayout.addWidget(self.pathSlider, 20)
        sliderLayout.addWidget(self.keyBtn, 1)
        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(vSpacing=uic.SPACING, hSpacing=uic.SVLRG)
        row = 0
        gridLayout.addWidget(self.upAxisCombo, row, 0)
        gridLayout.addWidget(self.followAxisCombo, row, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Button1 Layout ----------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        buttonLayout.addWidget(self.curveCvBtn, 1)
        buttonLayout.addWidget(self.reverseBtn, 1)
        buttonLayout.addWidget(self.switchCurvesBtn, 1)
        buttonLayout.addWidget(self.moPathSelBtn, 20)
        buttonLayout.addWidget(self.deleteBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(elements.LabelDivider("Rotation Object Up"))
        mainLayout.addLayout(gridLayout)
        mainLayout.addWidget(elements.LabelDivider("Rig Options"))
        mainLayout.addLayout(checkboxLayout)
        mainLayout.addLayout(checkbox2Layout)
        mainLayout.addWidget(elements.LabelDivider("Path Animation"))
        mainLayout.addLayout(sliderLayout)
        mainLayout.addLayout(buttonLayout)


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
        # World Up Layout ------------------------
        addWorldUpLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        addWorldUpLayout.addWidget(self.worldUpTypeCombo, 1)
        addWorldUpLayout.addWidget(self.upVectorFloat, 1)
        # Add World Up Object Layout ------------------------
        addUpObjLayout = elements.hBoxLayout(spacing=uic.SPACING)
        addUpObjLayout.addWidget(self.upObjTxt, 9)
        addUpObjLayout.addWidget(self.addUpObjTxtBtn, 1)
        # Add Curve Layout ------------------------
        addCurveLayout = elements.hBoxLayout(spacing=uic.SPACING)
        addCurveLayout.addWidget(self.curveObjTxt, 9)
        addCurveLayout.addWidget(self.addCurveTxtBtn, 1)
        # Checkbox Layout
        checkboxLayout = elements.hBoxLayout(spacing=uic.SVLRG, margins=(uic.SLRG, uic.SREG, uic.SLRG, uic.SREG))
        checkboxLayout.addWidget(self.followCheckbox, 1)
        checkboxLayout.addWidget(self.constrainCheckbox, 1)
        checkboxLayout.addWidget(self.groupCheckbox, 1)
        # Scale Button layout -----------------------------
        scaleButtonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        scaleButtonLayout.addWidget(self.scaleVCtrlNegBtn, 1)
        scaleButtonLayout.addWidget(self.scaleVCtrlPosBtn, 1)
        # Checkbox2 Layout --------------------------
        checkbox2Layout = elements.hBoxLayout(spacing=uic.SVLRG, margins=(uic.SLRG, 0, uic.SLRG, 0))
        checkbox2Layout.addWidget(self.upVCtrlCheckbox, 10)
        checkbox2Layout.addWidget(self.upVCtrlScale, 10)
        checkbox2Layout.addLayout(scaleButtonLayout, 1)
        # Slider Layout --------------------------
        sliderLayout = elements.hBoxLayout(spacing=uic.SPACING)
        sliderLayout.addWidget(self.pathSlider, 20)
        sliderLayout.addWidget(self.keyBtn, 1)
        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(vSpacing=uic.SPACING, hSpacing=uic.SVLRG)
        row = 0
        gridLayout.addWidget(self.upAxisCombo, row, 0)
        gridLayout.addWidget(self.followAxisCombo, row, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Button1 Layout ----------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        buttonLayout.addWidget(self.curveCvBtn, 1)
        buttonLayout.addWidget(self.reverseBtn, 1)
        buttonLayout.addWidget(self.switchCurvesBtn, 1)
        buttonLayout.addWidget(self.moPathSelBtn, 20)
        buttonLayout.addWidget(self.deleteBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(elements.LabelDivider("Rotation World Up"))
        mainLayout.addLayout(addWorldUpLayout)
        mainLayout.addLayout(addUpObjLayout)
        mainLayout.addLayout(checkbox2Layout)
        mainLayout.addWidget(elements.LabelDivider("Rotation Object Up"))
        mainLayout.addLayout(gridLayout)
        mainLayout.addWidget(elements.LabelDivider("Rig Options"))
        mainLayout.addLayout(addCurveLayout)
        mainLayout.addLayout(checkboxLayout)
        mainLayout.addWidget(elements.LabelDivider("Path Animation"))
        mainLayout.addLayout(sliderLayout)
        mainLayout.addLayout(buttonLayout)
