from functools import partial

from maya import cmds
import maya.mel as mel

from zoovendor.Qt import QtWidgets, QtCore
from zoo.apps.toolsetsui.widgets import toolsetwidget

from zoo.libs import iconlib
from zoo.libs.utils import output
from zoo.libs.pyqt import uiconstants as uic, keyboardmouse
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.objutils import joints, locators
from zoo.libs.maya.cmds.rig import riggingmisc
from zoo.libs.maya.cmds.hotkeys import definedhotkeys as hk
from zoo.libs.maya.cmds.objutils import matrix
from zoo.libs.maya.cmds.modeling import create

# plane orient
from zoo.libs.commands import maya
from zoo.libs.maya.meta import base as meta

XYZ_LIST = ["X", "Y", "Z"]
XYZ_WITH_NEG_LIST = ["X", "Y", "Z", "-X", "-Y", "-Z"]
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
ROTATE_LIST = ["Rotate X", "Rotate Y", "Rotate Z"]

AXIS_VECTORS = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)]


class JointToolUI(toolsetwidget.ToolsetWidget):
    id = "jointTool"
    uiData = {"label": "Joint Tool Window",
              "icon": "skeleton",
              "tooltip": "Simple Align Joints Tool",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-joint-tool-window/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for UI change sizes
        self._coPlanarMeta = None  # meta node for the plane/arrow controls

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = CompactLayout(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        self.advancedWidget = AdvancedLayout(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self._onWorldUpChanged()  # shows/hides vis of the arrow and plane buttons
        self._updateUiJointSettings()  # updates the UI with the current joint settings radius and scale compensate
        self.uiConnections()
        self.startSelectionCallback()  # start selection callback
        # self.updateFromProperties() has been run in self._updateUiJointSettings()

    def defaultAction(self):
        """Double Click"""
        pass

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Used to store and update UI data

        For use in the GUI use:
            current value: self.properties.itemName.value
            default value (automatic): self.properties.itemName.default

        To connect Qt widgets to property methods use:
            self.toolsetWidget.linkProperty(self.widgetQtName, "itemName")

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [{"name": "rotateLra", "value": 45},
                {"name": "selHierarchyRadio", "value": 1},
                {"name": "globalDisplaySize", "value": 1},
                {"name": "jointRadiusFloat", "value": 1.0},
                {"name": "mirrorCombo", "value": 0},
                {"name": "rotateCombo", "value": 0}]

    # ------------------
    # CALLBACKS
    # ------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then still may be a component face selection TODO add this to internal callbacks maybe?
            selection = cmds.ls(selection=True)
            if not selection:  # then nothing is selected
                return
        self._updateUiJointSettings()

    # ------------------
    # UI
    # ------------------
    def enterEvent(self, event):
        """When the mouse enters the widget check that all nodes are intact in the scene"""
        self._startDelMeta()  # for plane and arrow modes

    def _updateUiJointSettings(self):
        """Updates the UI with the current joint settings"""
        jointGlobalScale, jointLocalRadius, scaleCompensate = joints.jointPropertiesSel()
        self.properties.globalDisplaySize.value = jointGlobalScale
        if jointLocalRadius:  # a joint is selected
            self.properties.jointRadiusFloat.value = jointLocalRadius
            self.properties.scaleCompensateRadio.value = scaleCompensate

        self.updateFromProperties()

    def resetUI(self):
        """Resets the orientation UI to the default state"""
        self.properties.rotateLra.value = 45.0
        self.properties.primaryAxisCombo.value = 0
        self.properties.secondaryAxisCombo.value = 1
        self.properties.worldUpAxisCombo.value = 1
        self.properties.rotateCombo.value = 0
        self.updateFromProperties()
        self._onWorldUpChanged()  # deletes meta and hides buttons if in plane or arrow modes.

    def _startDelMeta(self):
        """When the mouse enters the widget check that all nodes are intact in the scene"""
        worldUpInt = self.properties.worldUpAxisCombo.value
        if worldUpInt > 2:
            self._validateReferencePlane()
            self._validateMetaNode()
        else:  # just delete the plane and leave the meta
            if self._coPlanarMeta:
                self._coPlanarMeta.deleteReferencePlane()

    def _onSnapToProjectedCenter(self):
        for widget in self.widgets():  # both GUIs
            if widget.snapProjectedCenterOffBtn.isVisible():
                vis = False
            else:
                vis = True
            widget.snapProjectedCenterOffBtn.setVisible(vis)
            widget.snapProjectedCenterOnBtn.setVisible(not vis)

    def _onRollUpChanged(self):
        rollUpInt = self.properties.secondaryAxisCombo.value
        aimInt = self.properties.primaryAxisCombo.value
        if aimInt == rollUpInt:
            if rollUpInt == 0:
                self.properties.primaryAxisCombo.value = 2  # if X make Z
                self.properties.rotateCombo.value = 2  # set the rotate combo to the roll up to match
            else:
                self.properties.primaryAxisCombo.value = 0  # if Z or Y make X
                self.properties.rotateCombo.value = 0  # set the rotate combo to the roll up to match

        self.updateFromProperties()
        self._updateOrientButtons(self.properties.primaryAxisCombo.value, self.properties.secondaryAxisCombo.value)

    def _onAimChanged(self):
        rollUpInt = self.properties.secondaryAxisCombo.value
        aimInt = self.properties.primaryAxisCombo.value
        if aimInt == rollUpInt:
            if rollUpInt == 1:
                self.properties.secondaryAxisCombo.value = 2  # if Y make Z
            else:
                self.properties.secondaryAxisCombo.value = 1  # if Z or X make Y

        self.properties.rotateCombo.value = aimInt  # set the rotate combo to the roll up to match (arrow sml btns)

        self.updateFromProperties()
        self._updateOrientButtons(self.properties.primaryAxisCombo.value, self.properties.secondaryAxisCombo.value)

    def _updateOrientButtons(self, aimInt, rollUpInt):
        for widget in self.widgets():  # both GUIs
            widget.orientYPosBtn.setText("Orient Roll "
                                         "+{} (Aim {})".format(XYZ_LIST[rollUpInt], XYZ_WITH_NEG_LIST[aimInt]))
            widget.orientYNegBtn.setText("Orient Roll "
                                         "-{} (Aim {})".format(XYZ_LIST[rollUpInt], XYZ_WITH_NEG_LIST[aimInt]))

    def _onWorldUpChanged(self):
        """Shows the visibility of the arrow and plane buttons depending on the value of the worldUpAxisCombo
        Also will show or delete the meta nodes and reference plane/arrow
        """
        worldUpInt = self.properties.worldUpAxisCombo.value
        if worldUpInt <= 2:
            arrowVis = False
            planeVis = False
            either = False
        elif worldUpInt == 3:  # arrow
            arrowVis = True
            planeVis = False
            either = True
        else:  # plane
            arrowVis = False
            planeVis = True
            either = True

        for widget in self.widgets():  # both GUIs
            widget.selectPlaneArrowCtrlBtn.setVisible(either)
            widget.startEndArrowChainBtn.setVisible(arrowVis)
            widget.startEndChainBtn.setVisible(planeVis)
        self.toolsetWidget.treeWidget.updateTree()  # update the tree, UI update vertical size
        self.toolsetWidget.treeWidget.updateTree()  # needs twice to force size
        if self._coPlanarMeta:  # delete the ref plane/arrow if it exists as it's likely being switched to other mode
            self._coPlanarMeta.deleteReferencePlane()
        self._startDelMeta()

        if planeVis and self._coPlanarMeta:
            self._coPlanarMeta.setPositionSnap(True)
        elif arrowVis and self._coPlanarMeta:
            self._coPlanarMeta.setPositionSnap(False)

    def _populateUiFromMeta(self):
        if not self._coPlanarMeta:
            return
        refPlaneCtrl = self._coPlanarMeta.referencePlane()
        if refPlaneCtrl:
            self._coPlanarMeta.showReferencePlane()
        self.properties.primaryAxisCombo.value = self._coPlanarMeta.primaryAxis()
        primaryNeg = self._coPlanarMeta.negatePrimaryAxis()
        if primaryNeg:
            self.properties.primaryAxisCombo.value += 3
        self.properties.secondaryAxisCombo.value = self._coPlanarMeta.secondaryAxis()

        self.updateFromProperties()

    # ------------------
    # LOGIC PLANE/ARROW ORIENT
    # ------------------

    def _startPlaneMetaNode(self):
        coPlanarMetaNodes = meta.findMetaNodesByClassType("zooPlaneOrient")
        if not coPlanarMetaNodes:
            self._coPlanarMeta = maya.coPlanarAlign(create=True)
            self._createPlaneArrowFromUI(self._coPlanarMeta)
        else:
            if coPlanarMetaNodes[0].referencePlane() is None:
                self._createPlaneArrowFromUI(coPlanarMetaNodes[0])
            self._coPlanarMeta = coPlanarMetaNodes[0]
            self._populateUiFromMeta()

    def _createPlaneArrowFromUI(self, coPlanarMetaNode):
        if self.properties.worldUpAxisCombo.value == 3:  # arrow
            createPlane = False
        else:  # plane
            createPlane = True
        coPlanarMetaNode.createReferencePlane(createPlane=createPlane)

    def _validateReferencePlane(self):
        """Check the reference plane geo still exists in the scene"""
        if not self._coPlanarMeta:
            return
        if self._coPlanarMeta.referencePlaneExists():
            return
        # Plane doesn't exists so restart meta node
        self._coPlanarMeta.deleteAllReferencePlanesScene()  # clean other nodes left behind
        self._createPlaneArrowFromUI(self._coPlanarMeta)  # creates either a plane or arrow
        self._coPlanarMeta.updateReferencePlane()
        self._coPlanarMeta.showReferencePlane()

    def _validateMetaNode(self):
        """Check the meta node exists in the scene, used while opening a new scene for example."""
        if self._coPlanarMeta:
            if self._coPlanarMeta.exists():
                return
            self._coPlanarMeta.delete()
        self._startPlaneMetaNode()  # restart meta node
        self.updateFromProperties()

    def _deleteMetaPlane(self):
        if self._coPlanarMeta:
            self._coPlanarMeta.deleteReferencePlane()
            self._coPlanarMeta.delete()

    def _setStartEndNodes(self):
        """Select one or two joints to set the plane or arrow"""
        if self._coPlanarMeta:
            self._coPlanarMeta.setStartEndNodesSel(self)
        else:
            self._validateMetaNode()

    def _selectRefControl(self):
        if self._coPlanarMeta:
            self._coPlanarMeta.selectReferencePlane()

    # ------------------
    # LOGIC JOINTS ORIENT AND OTHER
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def alignJoint(self, alignUp=True):
        """Aligns the selected joints in the scene, option to orient children of the selected

        :param alignUp: point the axis up (True) or down (False) relative to the world axis
        :type alignUp: bool
        """
        if self.properties.worldUpAxisCombo.value == 4:  # plane
            self._alignJointWorldPlane(alignUp)  # plane snap position
        else:
            self._alignJointWorldVector(alignUp)  # orient only includes arrow ctrl

    def _alignJointWorldVector(self, alignUp=True):
        """Aligns the world up to be X Y or Z as per the worldUpAxisCombo

        :param alignUp: point the axis up (True) or down (False) relative to the world axis
        :type alignUp: bool
        """
        worldAxisInt = self.properties.worldUpAxisCombo.value
        worldUpAxisVector = AXIS_VECTORS[self.properties.worldUpAxisCombo.value]
        if self._coPlanarMeta:
            if worldAxisInt == 3:  # If Arrow then get its vector/normal
                worldUpAxisVector = self._coPlanarMeta.arrowPlaneNormal()
                if not worldUpAxisVector:
                    output.displayWarning("No arrow plane found, please create one.")
                    return
                worldUpAxisVector = tuple(worldUpAxisVector)  # convert from mVector to tuple type
        if alignUp:
            secondaryAxisVector = AXIS_VECTORS[self.properties.secondaryAxisCombo.value]
        else:
            secondaryAxisVector = AXIS_VECTORS[self.properties.secondaryAxisCombo.value + 3]  # makes negative

        joints.alignJointZooSel(primaryAxisVector=AXIS_VECTORS[self.properties.primaryAxisCombo.value],
                                secondaryAxisVector=secondaryAxisVector,
                                worldUpAxisVector=worldUpAxisVector,
                                orientChildren=self.properties.selHierarchyRadio.value)

    def _alignJointWorldPlane(self, alignUp=True):
        """Aligns to the plane, orients and snap positions the joints

        :param alignUp: Align up or down relative the plane up direction
        :type alignUp: bool
        """
        if not self._coPlanarMeta.startNode() or not self._coPlanarMeta.endNode():
            output.displayWarning("Nodes not found. Please add the start and end nodes into the UI. ")
            return
        if not self._coPlanarMeta:
            return

        primaryAxisInt = int(self.properties.primaryAxisCombo.value)
        secondaryAxisInt = int(self.properties.secondaryAxisCombo.value)

        # Set the meta node settings for the snap and orient ------------------------------------
        primaryNeg = False
        if primaryAxisInt > 2:  # then is negative
            primaryNeg = True
            primaryAxisInt = primaryAxisInt - 3
        self._coPlanarMeta.setNegatePrimaryAxis(primaryNeg)
        self._coPlanarMeta.setNegateSecondaryAxis(not alignUp)
        self._coPlanarMeta.setNegateAxisAlignedAxis(False)
        self._coPlanarMeta.setPrimaryAxis(primaryAxisInt)
        self._coPlanarMeta.setSecondaryAxis(secondaryAxisInt)

        # Do the align on multiple selected chains ------------------------------------
        joints.alignJointPlaneOrientSel(self._coPlanarMeta, orientChildren=self.properties.selHierarchyRadio.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def _matchRefPlaneArrowSel(self, position=False, rotation=False, scale=False):
        """Matches the ref control (arrow or plane) to the first selected object"""
        if not self._coPlanarMeta:
            return
        self._coPlanarMeta.matchRefPlaneToSel(position=position, rotation=rotation, scale=scale)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def _orientRefPlaneToAxis(self, axis="X"):
        """Orients the reference plane to the given axis

        :param axis: the axis to orient to, "X", "Y", "Z"
        :type axis: str
        """
        if not self._coPlanarMeta:
            return
        self._coPlanarMeta.orientRefPlaneToAxis(axis)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def LRAVisibility(self, visiblity=True):
        """Show the joints local rotation axis or LRA manipulators
        Can affect the children of selected with the checkbox settings

        :param visiblity: show the local rotation axis (True), or hide (False)
        :type visiblity: bool
        """
        if visiblity:
            joints.displayLocalRotationAxisSelected(children=self.properties.selHierarchyRadio.value, display=True,
                                                    message=False)
        else:
            joints.displayLocalRotationAxisSelected(children=self.properties.selHierarchyRadio.value, display=False,
                                                    message=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def zeroRotAxis(self):
        """Zeroes the rotation axis of the selected joints.  Useful if you've manually reoriented joints with their
        local rotation handles.
        """
        joints.zeroRotAxisSelected(zeroChildren=self.properties.selHierarchyRadio.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def alignJointToParent(self):
        """Aligns the selected joint to its parent
        """
        joints.alignJointToParentSelected()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def drawJoint(self, drawVis=True):
        """sets the joint draw vis to be `bone` or `None`
        """
        if not drawVis:
            joints.jointDrawNoneSelected(children=self.properties.selHierarchyRadio.value)
        else:
            joints.jointDrawBoneSelected(children=self.properties.selHierarchyRadio.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def drawJointAsJoint(self):
        """sets the joint draw vis to be `joint`
        """
        joints.jointDrawJointSelected(children=self.properties.selHierarchyRadio.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def drawAsMultiChildBox(self):
        """sets the joint draw vis to be `joint`
        """
        joints.jointDrawMultiBoxSelected(children=self.properties.selHierarchyRadio.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def jointScaleCompensate(self, value=True):
        joints.jointScaleCompensate(compensate=self.properties.scaleCompensateRadio.value,
                                    children=self.properties.selHierarchyRadio.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def editLRA(self, editLRA=True):
        """Enter component mode, switch on edit local rotation axis, turn handle vis on
        If editLRA False then turn of local rotation axis in component mode, exit component mode
        """
        joints.editComponentLRA(editLRA=editLRA)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def rotateLRA(self, neg=False):
        """ Rotate LRA

        :param neg:
        :type neg:
        :return:
        :rtype:
        """
        # for alt shift and ctrl keys with left click, alt (reset is not supported)
        multiplier, reset = keyboardmouse.ctrlShiftMultiplier(shiftMultiply=2.0, ctrlMultiply=0.5)
        if neg:
            rotateLra = -(self.properties.rotateLra.value * multiplier)
        else:
            rotateLra = self.properties.rotateLra.value * multiplier
        if self.properties.rotateCombo.value == 0:  # then X
            rot = [rotateLra, 0, 0]
        elif self.properties.rotateCombo.value == 1:
            rot = [0, rotateLra, 0]
        else:
            rot = [0, 0, rotateLra]
        joints.rotateLRASelection(rot, includeChildren=self.properties.selHierarchyRadio.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def mirrorJoint(self):
        """ Mirrors jnt/s across a given plane from the GUI

        :return:
        :rtype:
        """
        axisInt = self.properties.mirrorCombo.value
        if axisInt == 0:
            axis = "X"
        elif axisInt == 1:
            axis = "Y"
        else:
            axis = "Z"
        joints.mirrorJointSelected(axis,
                                   searchReplace=(["_L", "_R"], ["_lft", "_rgt"]),
                                   mirrorBehavior=self.properties.mirrorBehaviourRadio.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setJointRadius(self, null):
        """Sets the joint radius for selected joints"""
        joints.setJointRadiusSelected(self.properties.jointRadiusFloat.value,
                                      children=self.properties.selHierarchyRadio.value,
                                      message=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def displayJointSize(self, *args):
        # sets the global display size of joints
        cmds.jointDisplayScale(self.properties.globalDisplaySize.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createJoint(self):
        """Invokes the joint create tool"""
        mel.eval("JointTool;")

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createJointSelection(self):
        """Creates a joint at the center of the selection"""
        create.createPrimitiveAndMatch(primitive="joint")

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createJointsAtSelectionMulti(self):
        """Creates a joint at the center of every selected object"""
        create.createPrimitiveAndMatchMultiSel(primitive="joint")

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createPrimitiveMatchMultiParent(self):
        """Creates a joint at the center of every selected object"""
        create.createPrimitiveAndMatchMultiSel(primitive="joint", parent=True)

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[AdvancedLayout or CompactLayout]
        """
        return super(JointToolUI, self).widgets()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivot(self):
        """Marks the center of a selection with a tiny locator with display handles on.
        """
        riggingmisc.markCenterPivot()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivotLoc(self):
        """Marks the center of a selection with a locator."""
        locators.createLocatorAndMatch(name="", handle=False, locatorSize=1.0, message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivotMulti(self):
        """Marks the center of a selection with a locator with display handles on.
        """
        locators.createLocatorsMatchMany(name="", handle=True, locatorSize=0.1, message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def markPivotMultiLocators(self):
        """Marks the center of a selection with a locator with display handles on.
        """
        locators.createLocatorsMatchMany(name="", handle=False, locatorSize=1.0, message=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteAllPivots(self):
        """Deletes all marked locator pivots in the scene.
        """
        riggingmisc.deleteAllCenterPivots()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def snapToProjectedCenterOn(self):
        hk.snapToProjectedCenter(state=True)
        self._onSnapToProjectedCenter()  # update UI

    @toolsetwidget.ToolsetWidget.undoDecorator
    def snapToProjectedCenterOff(self):
        hk.snapToProjectedCenter(state=False)
        self._onSnapToProjectedCenter()  # update UI

    @toolsetwidget.ToolsetWidget.undoDecorator
    def freezeToMatrix(self):
        """Sets an objects translate, rotate to be zero and scale to be one."""
        matrix.srtToMatrixOffsetSel(children=self.properties.selHierarchyRadio.value, nodeType="joint")

    @toolsetwidget.ToolsetWidget.undoDecorator
    def resetMatrix(self):
        """Resets an objects Offset Matrix to be zero."""
        matrix.zeroMatrixOffsetSel(children=self.properties.selHierarchyRadio.value, nodeType="joint")

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        # handles the coPlanar close event
        self.toolsetClosed.connect(self._deleteMetaPlane)
        # handles the Toolset Window close event
        self.toolsetUi.closed.connect(self._deleteMetaPlane)
        for widget in self.widgets():  # both GUIs
            widget.orientYPosBtn.clicked.connect(partial(self.alignJoint, alignUp=True))
            widget.orientYNegBtn.clicked.connect(partial(self.alignJoint, alignUp=False))
            widget.startEndChainBtn.clicked.connect(self._setStartEndNodes)
            widget.startEndArrowChainBtn.clicked.connect(self._setStartEndNodes)
            widget.selectPlaneArrowCtrlBtn.clicked.connect(self._selectRefControl)
            widget.showLRABtn.clicked.connect(partial(self.LRAVisibility, visiblity=True))
            widget.hideLRABtn.clicked.connect(partial(self.LRAVisibility, visiblity=False))
            widget.rotateLraNegBtn.clicked.connect(partial(self.rotateLRA, neg=True))
            widget.rotateLraPosBtn.clicked.connect(partial(self.rotateLRA, neg=False))
            widget.resetUIBtn.clicked.connect(self.resetUI)
            widget.createJntBtn.clicked.connect(self.createJoint)
            widget.primaryAxisCombo.currentIndexChanged.connect(self._onAimChanged)
            widget.secondaryAxisCombo.currentIndexChanged.connect(self._onRollUpChanged)
            widget.worldUpAxisCombo.currentIndexChanged.connect(self._onWorldUpChanged)
            widget.markCenterPivotBtn.clicked.connect(self.markPivot)
            widget.snapProjectedCenterOnBtn.clicked.connect(self.snapToProjectedCenterOn)
            widget.snapProjectedCenterOffBtn.clicked.connect(self.snapToProjectedCenterOff)
            # Right Click Button Menus ------------
            widget.createJntBtn.addAction("Enter the `Create Joint Tool`",
                                          mouseMenu=QtCore.Qt.RightButton,
                                          icon=iconlib.icon("skeleton"),
                                          connect=self.createJoint)
            widget.createJntBtn.addAction("Create A Joint Center Selection",
                                          mouseMenu=QtCore.Qt.RightButton,
                                          icon=iconlib.icon("skeleton"),
                                          connect=self.createJointSelection)
            widget.createJntBtn.addAction("Create Joints Multi Selection",
                                          mouseMenu=QtCore.Qt.RightButton,
                                          icon=iconlib.icon("skeleton"),
                                          connect=self.createJointsAtSelectionMulti)
            widget.createJntBtn.addAction("Create Joints Multi Parent",
                                          mouseMenu=QtCore.Qt.RightButton,
                                          icon=iconlib.icon("skeleton"),
                                          connect=self.createPrimitiveMatchMultiParent)
            widget.startEndChainBtn.addAction("Position Start/End Selection",
                                              mouseMenu=QtCore.Qt.RightButton,
                                              icon=iconlib.icon("planeOrient"),
                                              connect=self._setStartEndNodes)
            widget.startEndArrowChainBtn.addAction("Position Start/End Selection",
                                                   mouseMenu=QtCore.Qt.RightButton,
                                                   icon=iconlib.icon("logoutarrow"),
                                                   connect=self._setStartEndNodes)
            for w in [widget.startEndChainBtn, widget.startEndArrowChainBtn]:
                w.addAction("Match Position To Selection",
                            mouseMenu=QtCore.Qt.RightButton,
                            icon=iconlib.icon("matchComponent"),
                            connect=partial(self._matchRefPlaneArrowSel, True, False, False))
                w.addAction("Match Rotation To Selection",
                            mouseMenu=QtCore.Qt.RightButton,
                            icon=iconlib.icon("matchComponent"),
                            connect=partial(self._matchRefPlaneArrowSel, False, True, False))
                w.addAction("Orient To X Axis",
                            mouseMenu=QtCore.Qt.RightButton,
                            icon=iconlib.icon("axis"),
                            connect=partial(self._orientRefPlaneToAxis, "X"))
                w.addAction("Orient To Y Axis",
                            mouseMenu=QtCore.Qt.RightButton,
                            icon=iconlib.icon("axis"),
                            connect=partial(self._orientRefPlaneToAxis, "Y"))
                w.addAction("Orient To Z Axis",
                            mouseMenu=QtCore.Qt.RightButton,
                            icon=iconlib.icon("axis"),
                            connect=partial(self._orientRefPlaneToAxis, "Z"))
            # Mark center pivot right click ----------------
            widget.markCenterPivotBtn.addAction("Mark Center Pivot - Regular",
                                                mouseMenu=QtCore.Qt.RightButton,
                                                icon=iconlib.icon("locator"),
                                                connect=self.markPivot)
            widget.markCenterPivotBtn.addAction("Mark Center Pivots - Many",
                                                mouseMenu=QtCore.Qt.RightButton,
                                                icon=iconlib.icon("locator"),
                                                connect=self.markPivotMulti)
            widget.markCenterPivotBtn.addAction("Mark Center Locator",
                                                mouseMenu=QtCore.Qt.RightButton,
                                                icon=iconlib.icon("locator"),
                                                connect=self.markPivotLoc)
            widget.markCenterPivotBtn.addAction("Mark Center Locators - Many",
                                                mouseMenu=QtCore.Qt.RightButton,
                                                icon=iconlib.icon("locator"),
                                                connect=self.markPivotMultiLocators)
            widget.markCenterPivotBtn.addAction("Delete Center Pivots",
                                                mouseMenu=QtCore.Qt.RightButton,
                                                icon=iconlib.icon("trash"),
                                                connect=self.deleteAllPivots)

        # Advanced widgets
        self.advancedWidget.mirrorBtn.clicked.connect(self.mirrorJoint)
        self.advancedWidget.zeroRotAxisBtn.clicked.connect(self.zeroRotAxis)
        self.advancedWidget.alignParentBtn.clicked.connect(self.alignJointToParent)
        self.advancedWidget.drawHideBtn.clicked.connect(partial(self.drawJoint, drawVis=False))
        self.advancedWidget.drawShowBtn.clicked.connect(partial(self.drawJoint, drawVis=True))
        self.advancedWidget.drawJointBtn.clicked.connect(self.drawJointAsJoint)
        self.advancedWidget.drawMultiChildBoxBtn.clicked.connect(self.drawAsMultiChildBox)
        self.advancedWidget.editLRABtn.clicked.connect(partial(self.editLRA, editLRA=True))
        self.advancedWidget.exitLRABtn.clicked.connect(partial(self.editLRA, editLRA=False))
        self.advancedWidget.jointRadiusFloat.textModified.connect(self.setJointRadius)
        self.advancedWidget.globalDisplaySizeTxt.textModified.connect(self.displayJointSize)
        self.advancedWidget.scaleCompensateRadio.toggled.connect(self.jointScaleCompensate)
        self.advancedWidget.freezeOffsetMatrixBtn.clicked.connect(self.freezeToMatrix)
        self.advancedWidget.resetOffsetMatrixBtn.clicked.connect(self.resetMatrix)
        # Callback methods
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: ZooRenamer
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)

        self.toolsetWidget = toolsetWidget
        self.properties = properties
        # Selected Hierarchy Radio Buttons ------------------------------------
        radioNameList = ["Selected", "Hierarchy"]
        radioToolTipList = ["Affects only the selected joints.",
                            "Affects the selected joints and all of it's child joints."]
        self.selHierarchyRadioWidget = elements.RadioButtonGroup(radioList=radioNameList,
                                                                 toolTipList=radioToolTipList,
                                                                 default=self.properties.selHierarchyRadio.value,
                                                                 parent=parent,
                                                                 margins=(uic.SVLRG2, 0, uic.SVLRG2, 0),
                                                                 spacing=uic.SXLRG)
        self.toolsetWidget.linkProperty(self.selHierarchyRadioWidget, "selHierarchyRadio")
        # Primary Axis Combo -------------------------------------------
        tooltip = "Set the primary axis, this is the axis that the joints will aim towards their children."
        self.primaryAxisCombo = elements.ComboBoxRegular(label="Aim Axis",
                                                         items=XYZ_WITH_NEG_LIST,
                                                         setIndex=0,
                                                         toolTip=tooltip,
                                                         parent=self)
        # Primary Axis Combo -------------------------------------------
        tooltip = "Set the secondary axis. The axis the joints roll towards relative to the `World Up` setting. \n" \
                  "To set the roll axis to the negative press the down button (below). "
        self.secondaryAxisCombo = elements.ComboBoxRegular(label="Roll Up",
                                                           items=XYZ_LIST,
                                                           setIndex=1,
                                                           toolTip=tooltip,
                                                           parent=self)
        # World Up Axis Combo -------------------------------------------
        tooltip = "The world up axis to use when orienting joints. \n\n" \
                  " - X: Up Axis points to the side (right) in world coordinates. \n" \
                  " - Y: Up Axis points up in world coordinates. \n" \
                  " - Z: Up Axis points to the front in world coordinates. \n" \
                  " - Up Ctrl: Builds an arrow control for interactive `world up` orientation. \n" \
                  " - Plane: Builds a plane control for both orient and position snapping. "
        self.worldUpAxisCombo = elements.ComboBoxRegular(label="World Up",
                                                         items=XYZ_LIST + ["Up Ctrl", "Plane"],
                                                         setIndex=1,
                                                         toolTip=tooltip,
                                                         parent=self)
        # Select Arrow Up -------------------------------------------
        toolTip = "Select the `Up Arrow/Plane Control` in the scene."
        self.selectPlaneArrowCtrlBtn = elements.AlignedButton("Select Control",
                                                              icon="cursorSelect",
                                                              toolTip=toolTip)
        # Start/End Match -------------------------------------------
        toolTip = "Select a start and end joint to position and orient the plane/arrow ctrl along a joint chain. \n" \
                  "The automatic start/end positioning should find the most accurate up direction for the joints. \n" \
                  "Right-click for more options including setting the plane to a given world axis."
        self.startEndArrowChainBtn = elements.AlignedButton("Position Ctrl (Right-Click)",
                                                            icon="logoutarrow",
                                                            toolTip=toolTip)
        self.startEndChainBtn = elements.AlignedButton("Position Ctrl (Right-Click)",
                                                       icon="planeOrient",
                                                       toolTip=toolTip)
        # Mark Center Pivot ---------------------------------------
        tooltip = "Marks the center of a selection with a locator.  \n " \
                  "For example an edge-ring or other component selection. \n" \
                  "Right-click for more options. \n" \
                  "- Mark Locator: Uses a regular locator rather than a handle/locator \n" \
                  "- Mark Multi: Places many locators at the center of each selected object."
        self.markCenterPivotBtn = elements.AlignedButton("Mark Center (Right Click)",
                                                         icon="locator",
                                                         toolTip=tooltip)
        # Snap Projected Center Pivot ---------------------------------------
        tooltip = "Turns Maya's `snap to projected center` on and off.  \n" \
                  "When on, all objects will snap to the center of the selected objects. \n" \
                  "You can also find this setting as a snap icon in Maya's top toolbar. "
        self.snapProjectedCenterOnBtn = elements.AlignedButton("Volume Snap (Turn On)",
                                                               icon="magnet",
                                                               toolTip=tooltip)
        self.snapProjectedCenterOffBtn = elements.AlignedButton("Volume Snap (Turn Off)",
                                                                icon="magnet",
                                                                toolTip=tooltip)
        self.snapProjectedCenterOffBtn.setVisible(False)
        # Orient Up Section -------------------------------------------
        toolTip = "Orient joints so that the roll axis orients `up` as per the `World Up` setting. \n" \
                  "The `Aim Axis` will aim toward the child joint, or if none exists, from its parent. \n\n" \
                  "World Up set to `Up Ctrl`:  Joint's roll will orient in the direction of the arrow ctrl. \n" \
                  "World Up set to `Plane`: Joints will both orient and position-snap to the \n" \
                  "plane ctrl. \n\n" \
                  "Select joints to orient (and or position) and run."
        self.orientYPosBtn = elements.AlignedButton("Orient Roll +Y (Aim X)",
                                                    icon="arrowUp",
                                                    toolTip=toolTip)
        toolTip = "Orient joints so that the roll axis orients `down` as per the `World Up` setting. \n" \
                  "The aim axis will aim toward it's child joint, or if none exists, from its parent. \n\n" \
                  "World Up set to `Up Ctrl`:  Joint's roll will orient in the direction of the arrow ctrl. \n" \
                  "World Up set to `Plane`: Joints will both orient and position-snap to the \n" \
                  "plane ctrl. \n\n" \
                  "Select joints to orient (and or position) and run."
        self.orientYNegBtn = elements.AlignedButton("Orient Roll -Y (Aim X)",
                                                    icon="arrowDown",
                                                    toolTip=toolTip)
        # Reset UI -------------------------------------------
        toolTip = "Resets the `Orient UI Elements` to the default values."
        self.resetUIBtn = elements.styledButton("",
                                                "reload2",
                                                toolTip=toolTip,
                                                parent=parent,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Display Local Rotation Axis Sectionn -------------------------------------------
        toolTip = "Show the local rotation axis on the selected joints/s. \n" \
                  "The rotation axis helps visualize joint orientation. "
        self.showLRABtn = elements.AlignedButton("Show Local Rotation Axis",
                                                 icon="axis",
                                                 toolTip=toolTip)
        toolTip = "Hide the local rotation axis on the selected joints/s."
        self.hideLRABtn = elements.AlignedButton("Hide Local Rotation Axis",
                                                 icon="axis",
                                                 toolTip=toolTip)
        # Rotate Section ------------------------------------
        toolTip = "Rotate the local rotation `roll axis` in degrees.\n\n" \
                  " Slow - Ctrl + Left Click: 22.5 degrees (default) \n" \
                  " Medium - Left Click: 45 degrees (default) \n" \
                  " Fast - Shift + Left Click: 90 degrees (default)\n\n" \
                  "Use the advanced mode to change the rotation axis and amount of rotation."
        self.rotateLraNegBtn = elements.styledButton("",
                                                     "arrowRotLeft",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     minWidth=uic.BTN_W_ICN_MED)
        self.rotateLraPosBtn = elements.styledButton("",
                                                     "arrowRotRight",
                                                     toolTip=toolTip,
                                                     parent=parent,
                                                     minWidth=uic.BTN_W_ICN_MED)
        # Create Joint btn ------------------------------------
        toolTip = "Enter the Create Joint Tool, left click in the viewport to draw joints. \n\n" \
                  "Right-click for options: \n" \
                  " - Enter Create Joint: left click in the viewport to draw joints. \n" \
                  " - Create Joint At Selection: Creates a single joint at the center of the selection.\n" \
                  " - Create Joints Multi Selection: Creates joints at the center of each selected object. \n" \
                  " - Create Joints Multi Parent: Creates joints at each selected object and parents to a chain."
        self.createJntBtn = elements.styledButton("Create Joint Tool (Right-Click)", "skeleton", parent,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_DEFAULT)
        if uiMode == UI_MODE_ADVANCED:
            # Scale compensate ------------------------------------
            tooltips = ["Child joints will scale with the parent. This is not the default behaviour.",
                        "Child joints will not scale with the parent. This is the default behaviour."]
            self.scaleCompensateRadio = elements.RadioButtonGroup(radioList=["Scale Compensate Off",
                                                                             "Scale Compensate On"],
                                                                  toolTipList=tooltips,
                                                                  default=1,
                                                                  margins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG))

            # Joint Size ------------------------------------
            toolTip = "Set the global joint display size, all joints in the scene are affected."
            self.globalDisplaySizeTxt = elements.FloatEdit("Scene Jnt Size",
                                                           self.properties.globalDisplaySize.value,
                                                           parent=parent,
                                                           toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.globalDisplaySizeTxt, "globalDisplaySize")

            toolTip = "Set the joint radius (display size) of the selected joints."
            self.jointRadiusFloat = elements.FloatEdit("Local Jnt Radius",
                                                       1.0,
                                                       parent=parent,
                                                       toolTip=toolTip)
            # Rotate text
            toolTip = "Rotate the local rotation axis by this angle in degrees."
            self.rotateLraTxt = elements.FloatEdit("",
                                                   self.properties.rotateLra.value,
                                                   parent=parent,
                                                   toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.rotateLraTxt, "rotateLra")
            # Rotation combo ------------------------------------
            toolTip = "Rotate around this axis. X, Y or Z?"
            self.rotateCombo = elements.ComboBoxRegular("Rot Axis",
                                                        items=XYZ_LIST,
                                                        setIndex=self.properties.rotateCombo.value,
                                                        parent=parent, toolTip=toolTip)
            # Mirror btns ------------------------------------
            tooltips = ["Joint orients are maintained relative to the joints on the mirror. \n"
                        "This mode can be used for IK legs or joints that need to rotate without mirrored behaviour. \n"
                        "This is not the default behaviour.",
                        "Mirror will flip the `aim axis` causing rotation in `object mode` to be mirrored. \n"
                        "The mode usually on most joints."
                        "This is the default behaviour."]
            self.mirrorBehaviourRadio = elements.RadioButtonGroup(radioList=["Mirror Orientation",
                                                                             "Mirror Behaviour"],
                                                                  toolTipList=tooltips,
                                                                  default=1,
                                                                  margins=(uic.SREG, 0, uic.SREG, uic.SREG))
            toolTip = "Set the mirror axis to mirror across. X, Y or Z?"
            self.mirrorCombo = elements.ComboBoxRegular("Mirror Axis",
                                                        items=XYZ_LIST,
                                                        setIndex=self.properties.mirrorCombo.value,
                                                        parent=parent, toolTip=toolTip)
            self.toolsetWidget.linkProperty(self.mirrorCombo, "mirrorCombo")
            toolTip = "Mirror the joints.  Select only the base of each joint chain to mirror."
            self.mirrorBtn = elements.AlignedButton("Mirror",
                                                    icon="symmetryTri",
                                                    toolTip=toolTip)
            # Edit LRA ------------------------------------
            toolTip = "Enter component mode and make the local rotation axis selectable\n" \
                      "so that the manipulators can be manually rotated."
            self.editLRABtn = elements.AlignedButton("Edit LRA",
                                                     icon="editSpanner",
                                                     toolTip=toolTip)
            toolTip = "Exit component mode into object mode and turn off the \n" \
                      "local rotation axis selectability. \n" \
                      "Note: To be safe always run Zero Rot Axis after exiting LRA mode."
            self.exitLRABtn = elements.AlignedButton("Exit LRA",
                                                     icon="exit",
                                                     toolTip=toolTip)
            # Joint Draw Section
            toolTip = "Set 'Draw Style' joint attribute to be 'Bone'. (Default Mode) \n" \
                      "Joints will be visualized with bones and lines connecting if a hierarchy."
            self.drawShowBtn = elements.AlignedButton("Bone",
                                                      icon="skeleton",
                                                      toolTip=toolTip)
            toolTip = "Set 'Draw Style' joint attribute to be 'None'. \n" \
                      "Joints become hidden no matter the visibility settings."
            self.drawHideBtn = elements.AlignedButton("None",
                                                      icon="skeletonHide",
                                                      toolTip=toolTip)
            toolTip = "Set 'Draw Style' joint attribute to be 'Joint'. \n" \
                      "Joints will be visualized with no connections between joints. "
            self.drawJointBtn = elements.AlignedButton("Joint",
                                                       icon="jointsOnCurve",
                                                       toolTip=toolTip)
            toolTip = "Set 'Draw Style' joint attribute to be 'Multi-Child Box'. \n" \
                      "Joints with multiple children will be visualized as `boxes`, otherwise as `bones`. \n" \
                      "This is not a common setting. "
            self.drawMultiChildBoxBtn = elements.AlignedButton("Multi-Box",
                                                               icon="cubeWire",
                                                               toolTip=toolTip)
            # Zero Children Section
            toolTip = "After manually reorienting a joints LRA, this button zeros the \n" \
                      "joints Rotate Axis attributes; this will keep the \n" \
                      "joints orientations predictable. \n" \
                      "Note: This button should be pressed after exiting LRA mode if \n" \
                      "modifications have been made."
            self.zeroRotAxisBtn = elements.AlignedButton("Zero Rot Axis",
                                                         icon="checkOnly",
                                                         toolTip=toolTip)
            # Align Joint To Parent Section
            toolTip = "Align the selected joint to its parent.  \n" \
                      "Useful for end joints that have no children to orient towards."
            self.alignParentBtn = elements.AlignedButton("Align To Parent",
                                                         icon="3dManipulator",
                                                         toolTip=toolTip)
            # Freeze Offset Matrix ---------------------------------------
            tooltip = "Freeze to Parent Offset Matrix \n" \
                      "Useful for zeroing joints without needing to group them. \n" \
                      "Sets an object's `translate`, `rotate` to zero and `scale` to one. \n" \
                      "Transfers `translate`, `rotate` and `scale` information to the `offsetParentMatrix`. \n" \
                      "Can be non-uniform issues with rotation after freezing, see `Modeler Freeze Matrix`. \n" \
                      "Supported in Maya 2020 and above"
            self.freezeOffsetMatrixBtn = elements.AlignedButton("Freeze To Offset Matrix",
                                                                icon="matrix",
                                                                toolTip=tooltip)
            # Reset Offset Matrix ---------------------------------------
            tooltip = "Resets an objects Offset Matrix to zero. \n" \
                      "Returns joints to normal state if the `Freeze To Offest Matrix` has been used. \n" \
                      "Maintains the objects translate, rotate and scale position. \n" \
                      "Supported in Maya 2020 and above"
            self.resetOffsetMatrixBtn = elements.AlignedButton("Unfreeze Offset Matrix",
                                                               icon="matrix",
                                                               toolTip=tooltip)
            # labels and dividers ------------------------------------
            self.createLabel = elements.Label("Create & Position", parent=parent, toolTip=toolTip, bold=True)
            self.createDivider = elements.Divider(parent=parent)
            self.orientLabel = elements.Label("Orient", parent=parent, toolTip=toolTip, bold=True)
            self.orientDivider = elements.Divider(parent=parent)
            self.mirrorLabel = elements.Label("Mirror", parent=parent, toolTip=toolTip, bold=True)
            self.mirrorDivider = elements.Divider(parent=parent)
            self.sizeLabel = elements.Label("Size", parent=parent, toolTip=toolTip, bold=True)
            self.sizeDivider = elements.Divider(parent=parent)


class CompactLayout(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(CompactLayout, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                            toolsetWidget=toolsetWidget)
        # Main Layout ------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD,
                                                      uic.WINBOTPAD,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SPACING)
        # Orient Up Section ------------------------------------
        axisLayout = elements.hBoxLayout(margins=(uic.SSML, uic.SSML, uic.SSML, 0), spacing=uic.SVLRG2)
        axisLayout.addWidget(self.primaryAxisCombo, 5)
        axisLayout.addWidget(self.secondaryAxisCombo, 5)
        axisLayout.addWidget(self.worldUpAxisCombo, 5)
        # Arrow/Plane Control Section ------------------------------------
        controlLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        controlLayout.addWidget(self.startEndArrowChainBtn)
        controlLayout.addWidget(self.startEndChainBtn)
        controlLayout.addWidget(self.selectPlaneArrowCtrlBtn)
        # Orient Up Section ------------------------------------
        orientBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        orientBtnLayout.addWidget(self.orientYPosBtn)
        orientBtnLayout.addWidget(self.orientYNegBtn)
        # Display Local Rotation Axis Section ------------------------------------
        displayBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        displayBtnLayout.addWidget(self.hideLRABtn)
        displayBtnLayout.addWidget(self.showLRABtn)
        # Snap Layout Section ------------------------------------
        snapLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        snapLayout.addWidget(self.markCenterPivotBtn)
        snapLayout.addWidget(self.snapProjectedCenterOnBtn)
        snapLayout.addWidget(self.snapProjectedCenterOffBtn)
        # Main button layout
        createBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        createBtnLayout.addWidget(self.createJntBtn, 10)
        createBtnLayout.addWidget(self.rotateLraNegBtn, 1)
        createBtnLayout.addWidget(self.rotateLraPosBtn, 1)
        createBtnLayout.addWidget(self.resetUIBtn, 1)
        # Add to main layout ------------------------------------
        contentsLayout.addWidget(self.selHierarchyRadioWidget)
        contentsLayout.addLayout(axisLayout)
        contentsLayout.addLayout(controlLayout)
        contentsLayout.addLayout(orientBtnLayout)
        contentsLayout.addLayout(displayBtnLayout)
        contentsLayout.addLayout(snapLayout)
        contentsLayout.addLayout(createBtnLayout)
        contentsLayout.addStretch(1)


class AdvancedLayout(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(AdvancedLayout, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                             toolsetWidget=toolsetWidget)
        # Main Layout ------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD,
                                                      uic.WINBOTPAD,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SPACING)
        # Orient Up Section ------------------------------------
        axisLayout = elements.hBoxLayout(margins=(uic.SSML, 0, uic.SSML, 0), spacing=uic.SVLRG2)
        axisLayout.addWidget(self.primaryAxisCombo, 5)
        axisLayout.addWidget(self.secondaryAxisCombo, 5)
        axisLayout.addWidget(self.worldUpAxisCombo, 5)
        # Arrow/Plane Control Section ------------------------------------
        controlLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        controlLayout.addWidget(self.startEndArrowChainBtn)
        controlLayout.addWidget(self.startEndChainBtn)
        controlLayout.addWidget(self.selectPlaneArrowCtrlBtn)
        # Apply Orient Secondary Section ------------------------------------
        orientBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        orientBtnLayout.addWidget(self.orientYPosBtn)
        orientBtnLayout.addWidget(self.orientYNegBtn)
        # Display Local Rotation Axis Section ------------------------------------
        displayBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG), spacing=uic.SPACING)
        displayBtnLayout.addWidget(self.hideLRABtn)
        displayBtnLayout.addWidget(self.showLRABtn)
        # Draw Joint Section ------------------------------------
        drawBtnLayout = elements.GridLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        drawBtnLayout.addWidget(self.drawShowBtn, 0, 0)
        drawBtnLayout.addWidget(self.drawHideBtn, 0, 1)
        drawBtnLayout.addWidget(self.drawJointBtn, 0, 2)
        drawBtnLayout.addWidget(self.drawMultiChildBoxBtn, 0, 3)
        # Edit LRA Section ------------------------------------
        editLraLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        editLraLayout.addWidget(self.editLRABtn, 1)
        editLraLayout.addWidget(self.exitLRABtn, 1)
        # zero self layout ------------------------------------
        zeroParentLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        zeroParentLayout.addWidget(self.alignParentBtn, 1)
        zeroParentLayout.addWidget(self.zeroRotAxisBtn, 1)
        # mirror layout ------------------------------------
        mirrorLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        mirrorLayout.addWidget(self.mirrorCombo, 1)
        mirrorLayout.addWidget(self.mirrorBtn, 1)
        # Rotate Btn Layout ------------------------------------
        rotateBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        rotateBtnLayout.addWidget(self.rotateLraNegBtn, 1)
        rotateBtnLayout.addWidget(self.rotateLraPosBtn, 1)
        rotateBtnLayout.addWidget(self.resetUIBtn, 1)
        # Rotate  Layout ------------------------------------
        rotateLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        rotateLayout.addWidget(self.rotateCombo, 10)
        rotateLayout.addWidget(self.rotateLraTxt, 6)
        rotateLayout.addLayout(rotateBtnLayout, 1)

        # size layout ------------------------------------
        sizeLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG), spacing=uic.SVLRG)
        sizeLayout.addWidget(self.globalDisplaySizeTxt, 1)
        sizeLayout.addWidget(self.jointRadiusFloat, 1)

        # label layouts ------------------------------------
        createLabelLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, uic.SREG), spacing=uic.SREG)
        createLabelLayout.addWidget(self.createLabel, 1)
        createLabelLayout.addWidget(self.createDivider, 10)

        orientLabelLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, uic.SSML), spacing=uic.SREG)
        orientLabelLayout.addWidget(self.orientLabel, 1)
        orientLabelLayout.addWidget(self.orientDivider, 10)

        mirrorLabelLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, uic.SREG), spacing=uic.SREG)
        mirrorLabelLayout.addWidget(self.mirrorLabel, 1)
        mirrorLabelLayout.addWidget(self.mirrorDivider, 10)

        sizeLabelLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, 0), spacing=uic.SREG)
        sizeLabelLayout.addWidget(self.sizeLabel, 1)
        sizeLabelLayout.addWidget(self.sizeDivider, 10)

        # Snap Layout Section ------------------------------------

        matrixLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG), spacing=uic.SPACING)
        matrixLayout.addWidget(self.freezeOffsetMatrixBtn)
        matrixLayout.addWidget(self.resetOffsetMatrixBtn)

        # Snap Layout Section ------------------------------------
        snapLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        snapLayout.addWidget(self.markCenterPivotBtn)
        snapLayout.addWidget(self.snapProjectedCenterOnBtn)
        snapLayout.addWidget(self.snapProjectedCenterOffBtn)

        # add to main layout ------------------------------------
        contentsLayout.addWidget(self.selHierarchyRadioWidget)
        contentsLayout.addLayout(orientLabelLayout)
        contentsLayout.addLayout(axisLayout)
        contentsLayout.addLayout(controlLayout)
        contentsLayout.addLayout(orientBtnLayout)
        contentsLayout.addLayout(editLraLayout)
        contentsLayout.addLayout(zeroParentLayout)
        contentsLayout.addLayout(rotateLayout)

        contentsLayout.addWidget(elements.LabelDivider(text="Draw Style"))
        contentsLayout.addLayout(drawBtnLayout)
        contentsLayout.addLayout(displayBtnLayout)

        contentsLayout.addLayout(mirrorLabelLayout)
        contentsLayout.addWidget(self.mirrorBehaviourRadio)
        contentsLayout.addLayout(mirrorLayout)

        contentsLayout.addLayout(sizeLabelLayout)
        contentsLayout.addWidget(self.scaleCompensateRadio)
        contentsLayout.addLayout(sizeLayout)

        contentsLayout.addWidget(elements.LabelDivider(text="Matrix & Offsets"))
        contentsLayout.addLayout(matrixLayout)

        contentsLayout.addLayout(createLabelLayout)
        contentsLayout.addLayout(snapLayout)
        contentsLayout.addWidget(self.createJntBtn)
        contentsLayout.addStretch(1)
