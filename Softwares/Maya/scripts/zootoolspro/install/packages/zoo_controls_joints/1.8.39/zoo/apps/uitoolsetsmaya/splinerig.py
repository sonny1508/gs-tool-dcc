from functools import partial

from zoovendor.Qt import QtWidgets
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.maya.mayacommand import mayaexecutor as executor
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.core.util import zlogging
from zoo.libs.utils import output
from zoo.preferences.core import preference

from maya import cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.meta import metaadditivefk
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.meta import metasplinerig
from zoo.libs.maya.cmds.meta.metasplinerig import HIERARCHY_SWITCH
from zoo.libs.maya.meta import base
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.rig import splinebuilder
from zoo.libs.maya.cmds.objutils import namehandling, joints, curves, filtertypes, scaleutils
from zoo.libs.maya.triggers import blockSelectionCallbackDecorator

UP_AXIS_LIST = ["Auto", "+Y", "-Y", "+X", "-X", "+Z", "-Z"]
NEW_SPLINE_RIG = "<New Spline Rig>"

logger = zlogging.getLogger(__name__)


class DotsItems:
    SelectJoints = "Select Joints"
    SelectMeta = "Select Meta Node"
    Separator = "---"
    RebuildBaked = "Rebuild Current Pos"
    Duplicate = "Duplicate Rig"
    DeleteAll = "Delete All"
    ResetSettings = "Reset Settings"
    TogglePublish = "Rig Published"


class SplineRig(toolsetwidget.ToolsetWidget):
    id = "splineRig"
    info = "Builds a spline rig with various options"
    uiData = {"label": "Spline Rig",
              "icon": "splineRig",
              "tooltip": "Builds a spline rig with various options.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-spline-rig/"
              }

    _metaNode = None

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.useSelection = True

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """

        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.updateWidgets()
        self.startSelectionCallback()  # start selection callback
        self.uiConnections()
        self.updateSplineCombo()
        self.updateSelection()

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Overridden class

        :return:
        :rtype:  GuiCompact
        """
        return super(SplineRig, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiCompact]
        """
        return super(SplineRig, self).widgets()

    # ------------------
    # LOGIC
    # ------------------
    def updateWidgets(self, event=None):
        """ Update the widgets

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        :return:
        :rtype:
        """
        changed = False
        if event:
            if event.prevIndex == 1 and event.index == 0 and self.properties.controlsIntE.value != 5:
                changed = True

        if self.properties.controlsIntE.value != 5:  # disable the spine checkbox
            self.properties.spineCheckBox.value = False
            self.compactWidget.spineCheckBox.setEnabled(False)
        else:
            self.compactWidget.spineCheckBox.setEnabled(True)
        if self.properties.typeCombo.value == 0:  # enable spine checkbox
            self.compactWidget.controlsIntE.setEnabled(False)
            self.properties.controlsIntE.value = 5
            self.compactWidget.spineCheckBox.setEnabled(True)
        else:
            self.compactWidget.controlsIntE.setEnabled(True)

        self.properties.endJointStrE.data = self.properties.endJointStrE.get("data") or None
        self.properties.startJointStrE.data = self.properties.startJointStrE.get("data") or None
        self.updateFromProperties()

        if changed:
            self.rebuildRig()

    def inputStartJoint(self):
        """ Inputs a starting joint into the start textfield

        :return:
        :rtype:
        """
        selection = list(zapi.selected(filterTypes=(om2.MFn.kJoint)))

        if not selection:
            output.displayWarning("Please select a joint")
            return
        first = selection[0]
        self.setStartJointProp(first)
        self.properties.endJointStrE.data = self.properties.endJointStrE.get("data")
        startJoint = self.properties.startJointStrE.data  # type: zapi.DagNode
        endJoint = self.properties.endJointStrE.data  # type: zapi.DagNode

        # Clear out the end joint if it doesnt exist in the scene or if it is invalid
        if self.startJointExists() and self.endJointExists():
            if not splinebuilder.validStartEndJoint(startJoint.fullPathName(), endJoint.fullPathName(),
                                                    warning=False) or \
                    (endJoint and not endJoint.exists()):
                self.clearEndJointProp()
                self.currentWidget().endJointStrE.setText("")

        if not self.isStartJoint(startJoint):
            self.resetSplineCombo()
            self.setStartJointProp(first)
        self.updateFromProperties()

    def inputEndJoint(self):
        """ Inputs an end joint into the start textfield
        """
        selection = list(zapi.selected(filterTypes=(om2.MFn.kJoint)))
        if not selection:
            output.displayWarning("Please select a joint")
            return
        firstSel = selection[0]
        self.setEndJointProp(firstSel)
        startJoint = self.properties.startJointStrE.data  # type: zapi.DagNode
        endJoint = self.properties.endJointStrE.data  # type: zapi.DagNode

        # Clear startEdit if invalid
        if not splinebuilder.validStartEndJoint(startJoint.fullPathName(), endJoint.fullPathName(), warning=False) or \
                (startJoint and not startJoint.exists()):
            self.clearStartJointProp()
            self.currentWidget().startJointStrE.setText("")

        if not self.isEndJoint(endJoint):
            self.resetSplineCombo()
            self.setEndJointProp(firstSel)

        self.updateFromProperties()

    def startJoint(self):
        return self.properties.startJointStrE.data, self.properties.startJointStrE.value

    def endJoint(self):
        return self.properties.endJointStrE.data, self.properties.endJointStrE.value

    def isStartJoint(self, joint):
        """ If the joint is a start joint for any of the meta nodes in the scene

        :param joint:
        :type joint:
        :return:
        :rtype:
        """
        for m in self.metaNodes():
            if m.startJointNode() == joint:
                return True
        return False

    def isEndJoint(self, joint):
        """ If the joint is a end joint for any of the meta nodes in the scene

        :param joint:
        :type joint:
        :return:
        :rtype: bool
        """
        for m in self.metaNodes():
            if m.endJointNode() == joint:
                return True
        return False

    def startJointExists(self):
        """ Start Joint exists

        :return:
        :rtype:
        """
        self.properties.startJointStrE.data = self.properties.startJointStrE.get('data')
        startJoint = self.properties.startJointStrE.data
        if startJoint and startJoint.exists():
            return True
        return False

    def endJointExists(self):
        """ End joint exists

        :return:
        :rtype:
        """
        self.properties.endJointStrE.data = self.properties.endJointStrE.get('data')
        endJoint = self.properties.endJointStrE.data
        if endJoint and endJoint.exists():
            return True
        return False

    def setStartJointProp(self, node):
        """ Short hand to set start joint

        :param node:
        :type node: :class:`zapi.DagNode` or None
        :return:
        :rtype:
        """
        self.properties.startJointStrE.value = node.name() if node else ""
        self.properties.startJointStrE.data = node

    def clearStartJointProp(self):
        """ Empties self.properties.startJointStrE.value and data

        :return:
        :rtype:
        """
        self.setStartJointProp(None)

    def clearEndJointProp(self):
        """ Empties self.properties.endJointStrE.value and data

        :return:
        :rtype:
        """
        self.setEndJointProp(None)

    def setEndJointProp(self, node):
        """ Short hand to set end joint

        :param node:
        :type node: :class:`zapi.DagNode` or None
        :return:
        :rtype:
        """
        self.properties.endJointStrE.value = node.name() if node else ""
        self.properties.endJointStrE.data = node

    def resetSplineCombo(self):
        """ Reset the spline combo

        :return:
        :rtype:
        """
        self.currentWidget().splineCombo.setIndexInt(0)
        self.comboItalics()

    @blockSelectionCallbackDecorator
    def buildRig(self):
        """ Build Rig

        :return:
        :rtype:
        """
        self.blockCallbacks(True)
        metaAttrs = self.propertiesToMetaAttr()
        if metaAttrs is None:
            return

        if not self.validateInputs():  # messages already done in there
            return
        with scaleutils.sceneUnitsContext("cm"):
            self._metaNode = executor.execute("zoo.maya.splinerig.build", metaAttrs=metaAttrs,
                                              buildType=self.buildType())  # type: metasplinerig.MetaSplineRig

        self.blockCallbacks(False)
        if self._metaNode and self._metaNode.exists() and self._metaNode.cogControlNode() is not None:
            cmds.select(self._metaNode.cogControlNode().fullPathName())

    def validateInputs(self, message=True):
        """ Validate the inputs of splines or ik handles or joints

        :param message:
        :type message:
        :return:
        :rtype:
        """
        if self.buildType() == splinebuilder.BT_SPLINE:
            jointsSplineText = self.properties.jointsSplineEdit.get("value")
            jointsSpline = self.properties.jointsSplineEdit.get("data")
            if jointsSpline is None:
                output.displayWarning("A Curve must be entered into the UI")
                return False
            elif jointsSpline and not jointsSpline.exists():
                output.displayWarning("'{}' curve doesn't exist in scene.".format(jointsSplineText))
                return False


        elif self.buildType() == splinebuilder.BT_IKHANDLE:
            ikHandleText = self.properties.ikHandleEdit.get("value")
            ikHandle = self.properties.ikHandleEdit.get("data")
            if ikHandle is None:
                output.displayWarning("IK Spline Handle must have a value")
                return False
            elif ikHandle and not ikHandle.exists():
                output.displayWarning("'{}' IK Spline Handle doesn't exist in scene".format(ikHandleText))
                return False

        elif self.buildType() == splinebuilder.BT_STARTENDJOINT:

            startJointName = self.properties.startJointStrE.get("value")
            startJoint = self.properties.startJointStrE.get("data")
            endJointName = self.properties.endJointStrE.get("value")
            endJoint = self.properties.endJointStrE.get("data")

            if startJoint is None:
                output.displayWarning("Start joint must have a value")
                return False

            elif startJoint and not startJoint.exists():
                output.displayWarning("'{}' start joint doesn't exist in scene".format(startJointName))
                return False

            if endJoint is None:
                output.displayWarning("End joint must have a value")
                return False

            elif endJoint and not endJoint.exists():
                output.displayWarning("'{}' end joint doesn't exist in scene".format(endJointName))
                return False

        return True

    @blockSelectionCallbackDecorator
    def bakeRig(self):
        """ Bake the rig

        :return:
        :rtype:
        """
        metaNodes = self.currentMetaNodes()
        with scaleutils.sceneUnitsContext("cm"):
            for m in metaNodes:
                executor.execute("zoo.maya.splinerig.bake", meta=m)

    @blockSelectionCallbackDecorator
    def rebuildRig(self, event=None, message=False):
        """ Rebuilds the rig

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        :return:
        :rtype:
        """
        metaNodes = self.currentMetaNodes()
        metaAttrs = self.propertiesToMetaAttr()

        if not metaNodes:
            if message:
                output.displayWarning("No rig to rebuild, please select a Spline Rig.")
        if metaAttrs is None:
            return
        self.blockCallbacks(True)
        bake = not self.properties.rebuildRadioGrp.value
        for m in metaNodes:
            executor.execute("zoo.maya.splinerig.rebuild", meta=m, metaAttrs=metaAttrs, bake=bake)
        self.blockCallbacks(False)

    @blockSelectionCallbackDecorator
    def deleteRig(self):
        """ Delete Rig based on selection
        """
        metaNodes = self.currentMetaNodes()

        for m in metaNodes:
            executor.execute("zoo.maya.splinerig.delete", meta=m)

        self._metaNode = None
        self.updateSplineCombo()

    def currentMetaNodes(self):
        """ Includes the metanode in the combo and the selection

        :return:
        :rtype: list[:class:`metasplinerig.MetaSplineRig`]
        """
        selectedMetaNodes = self.selectedMetaNodes()  # if self.useSelection else []
        currentMeta = self.currentSplineRig()
        return [
                   currentMeta] + selectedMetaNodes if currentMeta and currentMeta not in selectedMetaNodes else selectedMetaNodes

    @blockSelectionCallbackDecorator
    def updateRig(self):
        """ Update rig based on properties from ui
        """
        metaNodes = self.currentMetaNodes()
        metaAttrs = self.propertiesToMetaAttr()

        if metaAttrs is None:
            return
        with scaleutils.sceneUnitsContext("cm"):
            for m in metaNodes:
                executor.execute("zoo.maya.splinerig.edit", meta=m, metaAttrs=metaAttrs)

        self.updateFromMeta(self.currentSplineRig())

    def updateSelection(self):
        """ Update metanode based on selection

        :return:
        :rtype:
        """
        selected = list(zapi.selected())
        if len(selected) == 0:
            return
        self.useSelection = True
        self.updateSplineCombo(useSelection=True)

        # Set the Ik Handle
        if self.ikHandleContext(selected[0]):  # ik handle context found, return
            return

        if self.curveContext():
            return

        addFkRig = self.selectedAdditiveFkRig()
        if addFkRig:
            self.properties.additiveFk.value = True
            self.properties.controlSpacingInt.value = addFkRig.getControlSpacing()
            self.updateFromProperties()

    def ikHandleContext(self, selected):
        """ handle the Ik handle context, save if needed

        :param selected:
        :type selected:
        :return:
        :rtype:
        """
        if cmds.currentCtx() == "ikSplineHandleContext" and selected.apiType() == om2.MFn.kIkHandle:
            self.setIkHandle(selected)
            return True

    def curveContext(self):
        """ Handle the curve context, save as needed

        :return:
        :rtype:
        """
        if cmds.currentCtx() == "curveContextCV":
            curve = self.selectedCurve()
            if curve:
                self.setJointsCurve(curve)

    def setJointsCurve(self, curve):
        """ Set the curve for the joints on curve mode

        :param curve:
        :type curve:
        :return:
        :rtype:
        """
        self.resetSplineCombo()
        self.properties.jointsSplineEdit.value = curve.name()
        self.properties.jointsSplineEdit.data = curve
        shape = zapi.nodeByName(filtertypes.filterTypeReturnShapes([curve.fullPathName()],
                                                                   shapeType="nurbsCurve")[0])
        self.properties.controlsIntE.value = len(shape.attribute('controlPoints'))
        if self.properties.controlsIntE.value != 5:
            self.properties.spineCheckBox.value = 0
            self.properties.typeCombo.value = 1
        self.updateWidgets()
        # self.updateFromProperties()

    def setIkHandle(self, ikHandle):
        """ Set the ik handle for the ik handle mode

        :param ikHandle:
        :type ikHandle: :class:`zapi.DagNode` or :class:`zapi.DGNode`
        :return:
        :rtype:
        """
        self.properties.ikHandleEdit.value = ikHandle.name()
        self.properties.ikHandleEdit.data = ikHandle
        self.resetSplineCombo()
        self.updateFromProperties()

    def updateFromMeta(self, m):
        """ Update properties from meta

        :param m:
        :type m: metasplinerig.MetaSplineRig
        :return:
        :rtype:
        """
        if m:
            metaAttrs = m.metaAttributeValues()
            if metaAttrs is None:
                return

            # self.properties.nameStrE.value = metaAttrs['rigName'] todo: update meta needs to update spline combo
            self.setStartJointProp(metaAttrs['startJoint'])
            self.setEndJointProp(metaAttrs['endJoint'])
            if metaAttrs['controlCount'] != 5:
                self.currentWidget().typeCombo.setIndex(1)
            self.properties.controlsIntE.value = metaAttrs['controlCount']
            self.properties.scaleFloatE.value = metaAttrs['scale']
            self.properties.fkCheckBox.value = metaAttrs['buildFk']
            self.properties.reverseCheckBox.value = metaAttrs['buildRevFk']
            self.properties.spineCheckBox.value = metaAttrs['buildSpine']
            self.properties.floatCheckBox.value = metaAttrs['buildFloat']
            self.properties.orientRootCombo.value = metaAttrs['orientRoot']
            # self.properties.controlSpacingInt.value = metaAttrs['controlSpacing']  # now found via the addFk meta
            self.properties.additiveFk.value = True if metaAttrs['additiveFkMeta'] else False
            self.properties.meshMenuCheckbox.value = m.meshHasMarkingMenus()
            self.updateFromProperties()
            self.updateHierarchySwitchCombo()
            # self.updateWidgets()

    def updateHierarchySwitchCombo(self):
        """ Update the hierarchy switch combo
        """
        m = self.currentSplineRig()
        if m:
            metaAttrs = m.metaAttributeValues()
            if metaAttrs is None:
                return

            self.properties.hierSwitchCombo.value = HIERARCHY_SWITCH.index(metaAttrs['hierarchySwitch'])
            self.properties.hierSwitchCombo.value = 1
            self.updateSingleProperty("hierSwitchCombo")

    def selectedMetaNodes(self):
        """ Get selected metanodes

        :return:
        :rtype: list[metasplinerig.MetaSplineRig]
        """

        selected = base.findRelatedMetaNodesByClassType(zapi.selected(),
                                                        metasplinerig.MetaSplineRig.__name__) or []
        return list(set(selected))  # return with duplicates removed

    def checkStartEndExist(self, message=True):
        """Checks if the joint start and end are valid and in the scene with messaging

        :return startJoint: String name of start joint if no zapi, if not found is ""
        :rtype startJoint: bool
        :return endJoint: String name of start joint if no zapi, if not found is ""
        :rtype endJoint: bool
        :return objType: "zapi" if a zapi node found, "str" if a string
        :rtype endJoint: str
        """
        startJointDag = self.properties.startJointStrE.data
        endJointDag = self.properties.endJointStrE.data
        if isinstance(startJointDag, zapi.DGNode) and isinstance(endJointDag, zapi.DGNode) and \
                startJointDag.exists() and endJointDag.exists():
            startJoint = self.properties.startJointStrE.data.fullPathName()
            endJoint = self.properties.endJointStrE.data.fullPathName()
            valid = splinebuilder.validStartEndJoint(startJoint, endJoint)
            if valid:
                return startJoint, endJoint, "zapi"
            else:
                return "", "", "zapi"

        # Try use the UI strings ----------------------
        startJ = self.properties.startJointStrE.value
        endJ = self.properties.endJointStrE.value
        if cmds.objExists(startJ):
            if not namehandling.nameIsUnique(startJ):
                if message:
                    output.displayWarning("Object {} does not have a unique name".format(startJ))
                return "", "", "str"
            else:
                if cmds.objExists(endJ):
                    if namehandling.nameIsUnique(startJ):
                        return startJ, endJ, "str"
                    else:
                        if message:
                            output.displayWarning("Object {} does not have a unique name".format(endJ))
                        return "", "", "str"
                else:
                    if message:
                        output.displayWarning("Object {} not found in scene".format(endJ))
                    return "", "", "str"
        # else
        if message:
            output.displayWarning("Object {} not found in scene".format(startJ))
        return "", "", "str"

    def updateStartEndJoints(self):
        """ Check and update the start and end joints.

        If

        :return:
        :rtype:
        """
        message = (self.buildType() == splinebuilder.BT_STARTENDJOINT)
        startJoint, endJoint, objType = self.checkStartEndExist(message)
        if not startJoint:
            if objType == "str":
                self.clearStartJointProp()
                self.clearEndJointProp()
                self.updateFromProperties()
            return  # joints are not valid

        if objType == "str":  # Update start end joint properties
            self.setStartJointProp(zapi.nodeByName(startJoint))
            self.setEndJointProp(zapi.nodeByName(endJoint))

    def updateIkHandle(self):
        """ Populate the ik handle property

        :return:
        :rtype:
        """
        ikHandleData = self.properties.ikHandleEdit.get("data")
        ikHandleName = self.properties.ikHandleEdit.value
        if ikHandleData is None:
            self.properties.ikHandleEdit.data = zapi.nodeByName(ikHandleName) if ikHandleName else None

    def propertiesToMetaAttr(self):
        """ Convert properties to meta attributes
        """

        if self.buildType() == splinebuilder.BT_STARTENDJOINT:
            self.updateStartEndJoints()
        self.properties.jointsSplineEdit.data = self.properties.jointsSplineEdit.get("data")
        self.updateIkHandle()

        propText = self.properties.splineCombo.currentText
        text = propText if propText != NEW_SPLINE_RIG else "splineRig"
        specialChars = ['<', '>']
        if any([s in text for s in specialChars]):
            text = "splineRig"  # use default if any special characters found

        return {'name': text,
                'startJoint': self.properties.startJointStrE.data,
                'endJoint': self.properties.endJointStrE.data,
                'controlCount': self.properties.controlsIntE.value,
                'scale': self.properties.scaleFloatE.value,
                'buildFk': self.properties.fkCheckBox.value,
                'buildRevFk': self.properties.reverseCheckBox.value,
                'buildSpine': self.properties.spineCheckBox.value,
                'buildFloat': self.properties.floatCheckBox.value,
                'orientRoot': self.properties.orientRootCombo.value,
                'hierarchySwitch': self.properties.hierSwitchCombo.currentData,
                'jointsSpline': self.properties.jointsSplineEdit.data,
                'upAxis': self.properties.upAxisCombo.value,
                'jointCount': self.properties.jointCountInt.value,
                'spacingWeight': self.properties.spacingWeightEdit.value,
                'reverseDirection': self.properties.reverseJointsCheckbox.value,
                'ikHandleBuild': self.properties.ikHandleEdit.data,
                'buildAdditiveFk': self.properties.additiveFk.value,
                'controlSpacing': self.properties.controlSpacingInt.value
                }

    def selectionChanged(self, sel):
        """ Selection Changed callback event

        :param sel:
        :type sel:
        :return:
        :rtype:
        """
        self.updateSelection()

    def updateFromProperties(self):
        """ Update from properties

        :return:
        :rtype:
        """
        super(SplineRig, self).updateFromProperties()
        self.comboItalics()
        if self.publishAction() and self.currentSplineRig():
            self.publishAction().setChecked(self.currentSplineRig().isPublished())

    def publishAction(self):
        """ Retrieves the publish action

        :return:
        :rtype: zoo.libs.pyqt.extended.searchablemenu.action.TaggedAction
        """
        return self.currentWidget().dotsMenu.property("publishAction")

    @blockSelectionCallbackDecorator
    def splineControlSwitch(self, event=None):
        """ Switch the spline controls

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        :return:
        :rtype:
        """
        metaNodes = self.currentMetaNodes()
        with scaleutils.sceneUnitsContext("cm"):
            for m in metaNodes:
                switched = executor.execute("zoo.maya.splinerig.switch", meta=m,
                                            switchTo=self.properties.hierSwitchCombo.currentData)
                if not switched:
                    self.currentWidget().hierSwitchCombo.setIndex(m.hierarchySwitchRigValue(), quiet=True)

    def numControlsModified(self):
        """ Number of controls modified

        :return:
        :rtype:
        """
        if self.properties.controlsIntE.value < 4:
            currentRig = self.currentSplineRig()
            if currentRig is None:
                return

            currentNum = currentRig.controlCount.value()
            logger.warning("Minumum controls is 4. Setting back to '{}'".format(currentNum))
            self.properties.controlsIntE.value = currentNum
            self.currentWidget().controlsIntE.setText(currentNum)
            return

        self.updateWidgets()
        self.rebuildRig()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def scaleControls(self):
        """ Scale the controls

        :return:
        :rtype:
        """
        if self.currentMetaNodes():
            [m.setScale(self.properties.scaleFloatE.value) for m in self.currentMetaNodes()]
        else:
            addFkRig = self.selectedAdditiveFkRig()
            if addFkRig:
                addFkRig.setScale(self.properties.scaleFloatE.value)

    def controlCheckBoxChanged(self):
        """ Control checkbox changed

        :return:
        :rtype:
        """
        m = self.currentSplineRig()

        if not m:
            return

        if len(m.controlTypes()) == 1:
            output.displayWarning("Must have atleast one control active")
            sender = self.sender()  # type: elements.CheckBox

            def checkboxChecked():
                orig = sender.signalsBlocked()
                sender.blockSignals(True)
                sender.setChecked(True)
                sender.blockSignals(orig)

            utils.singleShotTimer(checkboxChecked)

            return
        self.rebuildRig()

    def updateSplineCombo(self, useSelection=False):
        """ Updates the spline combo to the metanodes in the scene

        :return:
        :rtype:
        """
        selNodes = self.selectedMetaNodes()
        splineCombo = self.currentWidget().splineCombo
        metaNodes = self.metaNodes()
        currentMeta = self.currentSplineRig()
        self.properties.splineCombo.value = 0
        self.properties.splineCombo.values = NEW_SPLINE_RIG

        # Reload combo
        splineCombo.blockSignals(True)
        splineCombo.clear()
        splineCombo.addItem(NEW_SPLINE_RIG, None)
        splineCombo.addSeparator()
        splineCombo.addItems([m.rigNameStr() for m in metaNodes], metaNodes)
        splineCombo.blockSignals(False)

        comboMetaNodes = list(splineCombo.iterItemData())
        if len(selNodes) > 0 and useSelection:
            index = comboMetaNodes.index(selNodes[-1])  # use selection
        else:
            index = comboMetaNodes.index(currentMeta) if currentMeta is not None else 0  # use current meta instead

        # Update the widgets and ui
        splineCombo.setIndexInt(index)
        self.comboItalics()

        currentMeta = self.currentSplineRig()
        if currentMeta is not None:
            self.updateFromMeta(currentMeta)

    def comboItalics(self):
        """ Check if the spline rig combo needs to be italics or not

        :return:
        :rtype:
        """
        splineCombo = self.currentWidget().splineCombo
        font = splineCombo.comboEdit.edit.font()
        if splineCombo.currentIndexInt() == 0:
            font.setItalic(True)
        else:
            font.setItalic(False)
        splineCombo.comboEdit.edit.setFont(font)

    def currentSplineRig(self):
        """ Get the current spline rig meta node

        :return:
        :rtype: :class:`metasplinerig.MetaSplineRig`
        """
        meta = self.properties.splineCombo.currentData  # type: metasplinerig.MetaSplineRig
        if not isinstance(meta, zapi.DGNode):
            return

        return meta if meta.exists() else None

    @classmethod
    def metaNodes(cls):
        """ List of metanodes

        :return:
        :rtype: list[:class:`metasplinerig.MetaSplineRig`]
        """
        return base.findMetaNodesByClassType(metasplinerig.MetaSplineRig.__name__)

    def splineBuildComboChanged(self):
        """ Build combo changed
        """
        # Switch the ui and update the toolset widget size
        buildMode = self.currentWidget().buildMode
        buildMode.setCurrentIndex(self.properties.splineBuildCombo.value)
        self.updateTree()

    def buildType(self):
        """ Get the current build mode

        splinebuilder.BT_STARTENDJOINT, splinebuilder.BT_SPLINE, splinebuilder.BT_IKHANDLE

        :return:
        :rtype: int
        """
        return self.properties.splineBuildCombo.value

    def enterEvent(self, event):
        if not self.selectionCallbacks.callbacksBlocked():
            self.updateHierarchySwitchCombo()

    def splineComboChanged(self):
        self.useSelection = False

    def createCurveContext(self):
        """Enters the create curve context (user draws cvs).  Uses mel hardcoded 3 bezier curve."""
        curves.createCurveContext(degrees=3)

    def createSplineIkHandleContext(self):
        """ Create spline ik handle context

        :return:
        :rtype:
        """
        curves.splineIkHandleContext(spans=self.properties.controlsIntE.value - 3)

    def splineRenamed(self, event):
        """ Spline Renamed

        :param event:
        :type event:  zoo.libs.pyqt.extended.combobox.comboeditwidget.EditChangedEvent
        :return:
        :rtype:
        """
        if event.before == event.after:
            return

        allMeta = self.currentMetaNodes()
        text = self.currentWidget().splineCombo.currentText()

        for m in allMeta:
            executor.execute("zoo.maya.splinerig.rename", meta=m, name=text)

    def saveProperties(self, currentWidget=False):
        return super(SplineRig, self).saveProperties(currentWidget)

    def inputSplineJoints(self):
        """ Input the spline curve so we can generate the joints

        :return:
        :rtype:
        """

        curve = self.selectedCurve()
        if curve:
            self.setJointsCurve(curve)

    def selectedCurve(self, finishedOnly=True):
        """ Get selected curve

        :param finishedOnly: Returns curve only if its finished, if false it may return even if its not finished
        :type finishedOnly:
        :return:
        :rtype:
        """
        selected = list(zapi.selected())
        if len(selected) < 1:
            return
        selection = filtertypes.filterTypeReturnTransforms([selected[-1].fullPathName()], children=False,
                                                           shapeType="nurbsCurve")

        if len(selection) > 0:
            curve = zapi.nodeByName(selection[0])

            numPoints = len(curve.children()[0].attribute('controlPoints'))

            # Always returns if theres a curve and finishedOnly is false or only if the curve is finished
            if finishedOnly and numPoints > 1 or not finishedOnly:
                return curve

    def inputIkHandle(self):
        """ Input ik handle for the ui to use

        :return:
        :rtype:
        """
        handles = list(zapi.selected(filterTypes=(om2.MFn.kIkHandle)))
        if len(handles) > 0:
            self.setIkHandle(handles[0])

    def dotsMenuActionTriggered(self, action):
        """ Dots menu triggered

        :param action:
        :type action: zoo.libs.pyqt.extended.searchablemenu.action.TaggedAction
        :return:
        :rtype:
        """
        meta = self.currentSplineRig()
        if action.text() == DotsItems.SelectJoints:

            meta.selectJoints() if meta else None
        elif action.text() == DotsItems.SelectMeta:
            meta.selectMeta() if meta else None
        elif action.text() == DotsItems.Duplicate:
            self.blockCallbacks(True)
            executor.execute("zoo.maya.splinerig.duplicate", meta=meta)
            self.blockCallbacks(False)

        elif action.text() == DotsItems.RebuildBaked:
            metaNodes = self.currentMetaNodes()
            for m in metaNodes:
                executor.execute("zoo.maya.splinerig.rebuild", meta=m, bake=True)

        elif action.text() == DotsItems.DeleteAll:
            executor.execute("zoo.maya.splinerig.delete", meta=meta, deleteAll=True)

        elif action.text() == DotsItems.ResetSettings:
            self.blockCallbacks(True)
            self.resetProperties()
            self.updateRig()
            self.updateFromProperties()
            self.blockCallbacks(False)

        elif action.text() == DotsItems.TogglePublish:
            published = not meta.isPublished()
            meta.setPublished(published)
            self.currentWidget().dotsMenu.property("publishAction").setChecked(published)

    def getCheckControlSpacing(self):
        """Makes sure that the controlSpacingInt remains 1 or above"""
        if self.properties.controlSpacingInt.value < 1:
            self.properties.controlSpacingInt.value = 1
            self.updateFromProperties()
        return self.properties.controlSpacingInt.value

    @blockSelectionCallbackDecorator
    def rebuildAdditiveFk(self, data=None):
        """ Rebuilds an additive FK setup, usually when the `Control Spacing` is changed

        :return:
        :rtype:
        """

        if not self.properties.additiveFk.value:  # bail as Additive FK is not checked
            return
        splineMeta = self.currentSplineRig()
        addFkRig = self.selectedAdditiveFkRig()
        controlSpacing = self.getCheckControlSpacing()  # checks not 0 or negative value
        if splineMeta:  # Spline Rig exists, and checkbox is on so rebuild
            if splineMeta.additiveFkMetaNode():
                splineMeta.deleteAdditiveFkRig()
            addFkRig = executor.execute("zoo.maya.splinerig.buildAdditiveFk",
                                        meta=splineMeta,
                                        controlSpacing=controlSpacing)
        elif addFkRig:  # No Spline Rig exists, but addFk meta has been found so rebuild
            startJoint, endJoint = addFkRig.getStartEndJoint()  # get start and end joint from meta
            executor.execute("zoo.maya.additiveFk.delete",
                             meta=addFkRig)
            addFkRig = executor.execute("zoo.maya.additiveFk.build",
                                        startJoint=startJoint,
                                        endJoint=endJoint,
                                        controlSpacing=controlSpacing)
        # Set checkbox on, as it turns off
        self.properties.additiveFk.value = True
        self.properties.controlSpacingInt.value = controlSpacing  # goes out of sync, so force here
        self.updateFromProperties()
        addFkControls = zapi.fullNames(addFkRig.getControls())
        cmds.select(addFkControls, replace=True)

    def additiveFkStateChanged(self, checked):
        """ Additive FK Checkbox changed

        :param checked:
        :type checked:
        :return:
        :rtype:
        """
        splineMeta = self.currentSplineRig()
        addFkRig = self.selectedAdditiveFkRig()
        controlSpacing = self.getCheckControlSpacing()  # checks not 0 or negative value

        if checked:  # Build Add FK
            if not splineMeta:
                output.displayWarning("No Spline IK meta found, rig may not. Please build or select a Spline Rig.")
                return
            rigName = splineMeta.name()
            if splineMeta:  # Build with splineRigMeta
                if not splineMeta.additiveFkMetaNode():
                    addFkRig = executor.execute("zoo.maya.splinerig.buildAdditiveFk",
                                                meta=splineMeta,
                                                controlSpacing=controlSpacing,
                                                rigName=rigName)

            elif not addFkRig:  # No splineMeta or addFkMeta so build from scratch
                startJoint, sJntName = self.startJoint()
                endJoint, eJntName = self.endJoint()
                if startJoint and endJoint:
                    addFkRig = executor.execute("zoo.maya.additiveFk.build",
                                                startJoint=startJoint,
                                                endJoint=endJoint,
                                                controlSpacing=controlSpacing)
                else:  # joint start end not found
                    return
            # Select controls
            addFkControls = zapi.fullNames(addFkRig.getControls())
            cmds.undoInfo(stateWithoutFlush=False)
            cmds.select(addFkControls, replace=True)
            cmds.undoInfo(stateWithoutFlush=True)
            # Force UI Update
            self.properties.additiveFk.value = True
            self.updateFromProperties()
        else:  # Delete Add FK
            if splineMeta:
                if splineMeta.additiveFkMetaNode():
                    splineMeta.deleteAdditiveFkRig()
            elif addFkRig:
                executor.execute("zoo.maya.additiveFk.delete", meta=addFkRig)
            else:
                return
            # Force UI Update
            self.properties.additiveFk.value = False
            self.updateFromProperties()

    def selectedAdditiveFkRig(self):
        """ Get additive fk rig from selected

        :return addFkNode: additive fk meta node
        :rtype addFkNode: zoo.libs.maya.cmds.meta.metaadditivefk.ZooMetaAdditiveFk
        """
        selected = cmds.ls(selection=True)
        if selected:
            selected = zapi.nodeByName(selected[-1])
        else:
            return

        addFkNode = metaadditivefk.ZooMetaAdditiveFk.connectedMetaNodes(selected)
        if addFkNode:
            return addFkNode

    def meshMarkingMenuChecked(self, state):
        for m in self.currentMetaNodes():
            executor.execute("zoo.maya.splinerig.meshMarkingMenuActive", meta=m, active=state)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.bakeBtn.clicked.connect(self.bakeRig)
            widget.buildBtn.clicked.connect(self.buildRig)
            widget.rebuildBtn.clicked.connect(partial(self.rebuildRig, message=True))
            widget.getStartJntBtn.clicked.connect(self.inputStartJoint)
            widget.getEndJntBtn.clicked.connect(self.inputEndJoint)
            widget.typeCombo.itemChanged.connect(self.updateWidgets)
            widget.controlsIntE.textModified.connect(self.numControlsModified)

            widget.deleteBtn.clicked.connect(self.deleteRig)

            widget.fkCheckBox.stateChanged.connect(self.controlCheckBoxChanged)
            widget.reverseCheckBox.stateChanged.connect(self.controlCheckBoxChanged)
            widget.floatCheckBox.stateChanged.connect(self.controlCheckBoxChanged)
            widget.spineCheckBox.stateChanged.connect(self.controlCheckBoxChanged)

            widget.scaleFloatE.textModified.connect(lambda: self.scaleControls())
            widget.hierSwitchCombo.itemChanged.connect(self.splineControlSwitch)
            widget.orientRootCombo.itemChanged.connect(self.rebuildRig)
            widget.splineBuildCombo.itemChanged.connect(self.splineBuildComboChanged)
            widget.splineCombo.itemChanged.connect(self.splineComboChanged)
            widget.splineCombo.itemRenamed.connect(self.splineRenamed)
            widget.splineCombo.comboEdit.textChanged.connect(self.comboItalics)

            widget.curveCvBtn.clicked.connect(self.createCurveContext)
            widget.inputJointsSplineBtn.clicked.connect(self.inputSplineJoints)
            widget.ikHandleSelectBtn.clicked.connect(self.inputIkHandle)
            widget.ikHandleBtn.clicked.connect(self.createSplineIkHandleContext)
            widget.dotsMenu.actionTriggered.connect(self.dotsMenuActionTriggered)

            widget.additiveFk.stateChanged.connect(self.additiveFkStateChanged)
            widget.controlSpacingInt.textModified.connect(self.rebuildAdditiveFk)

            widget.meshMenuCheckbox.stateChanged.connect(self.meshMarkingMenuChecked)

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
        # Titles Dividers ---------------------------------------
        self.controlRigsTitle = elements.LabelDivider(text="Spline Rig Control Sets")
        self.splineControlsTitle = elements.LabelDivider(text="Spline Rig Options")
        self.additiveFkTitle = elements.LabelDivider(text="Additive FK Controls")
        tooltip = "Name or rename an existing rig."
        self.splineCombo = elements.ComboEditRename(label="Spline Rig", labelStretch=5, mainStretch=21,
                                                    primaryTooltip="Select an existing Spline Rig",
                                                    toolTip=tooltip)

        tooltip = "Select the object type to build the rig from. \n" \
                  " - Joints \n" \
                  " - Curve \n" \
                  " - Spline IK Handle"
        self.splineCombo.comboEdit.edit.setAlphanumericValidator()
        self.splineBuildCombo = elements.ComboBoxRegular(label="Specify",
                                                         items=["Curve", "Joints", "Spline IK Handle"],
                                                         labelRatio=6,
                                                         boxRatio=29,
                                                         toolTip=tooltip)
        toolsetWidget.addExtraProperties(self.splineCombo, ["currentData", "currentText"])
        self.splineCombo.addItem(NEW_SPLINE_RIG)

        self.buildMode = QtWidgets.QStackedWidget(parent=self)
        self.buildMode.sizeHint = lambda: self.buildMode.currentWidget().sizeHint()  # Make sure the stacked widget resizes correctly
        self.buildMode.minimumSizeHint = lambda: self.buildMode.currentWidget().minimumSizeHint()
        # Checkboxes ---------------------------------------
        tooltip = "A FK control setup will be built. \n " \
                  "Controls are parented to each other."
        self.fkCheckBox = elements.CheckBox(parent=self, label="FK Controls",
                                            checked=True,
                                            toolTip=tooltip)
        tooltip = "A Reverse FK control setup will be built. \n" \
                  "The controls will be parented backwards."
        self.reverseCheckBox = elements.CheckBox(parent=self, label="Reverse FK Controls",
                                                 checked=True,
                                                 toolTip=tooltip)
        tooltip = "A Floating control setup will be built. \n" \
                  "All controls will be parented to the root only. "
        self.floatCheckBox = elements.CheckBox(parent=self, label="Floating Controls",
                                               checked=True,
                                               toolTip=tooltip)
        tooltip = "A Spine control setup will be built. \n" \
                  "This setup is handy for character spine setups. \n" \
                  "Must have five controls for this option. "
        self.spineCheckBox = elements.CheckBox(parent=self, label="Spine Controls",
                                               checked=True,
                                               toolTip=tooltip)
        # Start Joint ---------------------------------------
        tooltip = "Specify the first joint in the joint chain. \n" \
                  "The base of the spline rig will start here."
        self.startJointStrE = elements.StringEdit(editPlaceholder="Enter Start joint",
                                                  editText="",
                                                  toolTip=tooltip,
                                                  editRatio=5,
                                                  labelRatio=1)

        # Get Start Joint ---------------------------------------
        toolTip = "Select the start joint and press to add to the UI."
        self.getStartJntBtn = elements.styledButton("",
                                                    "arrowLeft",
                                                    self,
                                                    toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=20)
        # End Joint ---------------------------------------
        tooltip = "Specify the last joint in the joint chain. \n" \
                  "The end of the spline rig will end here."
        self.endJointStrE = elements.StringEdit(editPlaceholder="End Joint",
                                                editText="",
                                                toolTip=tooltip,
                                                editRatio=21,
                                                labelRatio=5)
        # Get End Joint ---------------------------------------
        toolTip = "Select the end joint and press to add to the UI."
        self.getEndJntBtn = elements.styledButton("",
                                                  "arrowLeft",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=20)
        # Control Number ---------------------------------------
        tooltip = "The amount of controls to create \n" \
                  "To enable change the `Type` combo box to `Custom Count`. \n" \
                  "The `Spine` rig type can only be created with 5 controls."
        self.controlsIntE = elements.IntEdit(label="Controls",
                                             editText=5,
                                             toolTip=tooltip,
                                             editRatio=20,
                                             labelRatio=10)

        # Options Combo ---------------------------------------
        tooltip = "Build with five controls (standard) or switch to a custom count. \n" \
                  "Note: The character Spine type must be built with five controls."
        self.typeCombo = elements.ComboBoxRegular(label="Type",
                                                  items=["Spine 5 Ctrls", "Custom Count"],
                                                  toolTip=tooltip,
                                                  labelRatio=10,
                                                  boxRatio=20)
        # Switch Combo ---------------------------------------
        tooltip = "Space switches the controls on an existing rig."
        self.hierSwitchCombo = elements.ComboBoxRegular(label="Switch To",
                                                        items=["Spine Ctrls", "FK Controls", "Floating Ctrls",
                                                               "Reverse FK"],
                                                        itemData=HIERARCHY_SWITCH,
                                                        toolTip=tooltip,
                                                        labelRatio=12,
                                                        boxRatio=20)
        toolsetWidget.addExtraProperty(self.hierSwitchCombo, "currentData")
        # Menu Skin Checkbox ---------------------------------------
        tooltip = "If joints are skinned add a trigger menu onto skinned meshes. \n" \
                  "Can be refreshed by toggling after a rig has been built."
        self.meshMenuCheckbox = elements.CheckBox("Skin Mesh Menu",
                                                  right=True,
                                                  labelRatio=10,
                                                  boxRatio=1,
                                                  checked=True,
                                                  toolTip=tooltip)
        # Control Scale Int ---------------------------------------
        tooltip = "Sets the global scale of the rig controls."
        self.scaleFloatE = elements.FloatEdit(label="Ctrl Scale",
                                              editText=1.0,
                                              toolTip=tooltip,
                                              editRatio=20,
                                              labelRatio=10)
        # Additive FK checkbox ---------------------------------------
        tooltip = "Adds an `Additive FK` rig on top of the `Spline Rig`. \n" \
                  "The FK rig moves with the spline rig and offsets it further. \n" \
                  "Used for fine control and curling the tip of the rig.\n\n" \
                  "Note: Additive FK is a rig that is layered on top of Spline Rig \n" \
                  "and can be built separately. See help for more information"
        self.additiveFk = elements.CheckBox(parent=self, label="Additive FK Rig Layer",
                                            checked=False,
                                            toolTip=tooltip)
        # Control Spacing Add FK Int ---------------------------------------
        tooltip = "Builds a control on every nth joint for the Additive FK only.  \n" \
                  "Example: If 3 then will build a control on every third joint."
        self.controlSpacingInt = elements.IntEdit(label="Control Spacing",
                                                  editText=2,
                                                  toolTip=tooltip,
                                                  editRatio=7,
                                                  labelRatio=10)
        # Options Combo ---------------------------------------
        tooltip = "Orients the root control to face this direction. \n" \
                  "Automatic will detect the longest axis and aim \n" \
                  "positive in that direction. "
        self.orientRootCombo = elements.ComboBoxRegular(label="Orient Root",
                                                        items=UP_AXIS_LIST,
                                                        setIndex=0,
                                                        toolTip=tooltip,
                                                        labelRatio=12,
                                                        boxRatio=20)
        # Rebuild Radio Button ---------------------------------------
        tooltip = "Rebuild the rig at the `current` position/rotation/scale."
        tooltip2 = "Rebuild the rig at the `original` position/rotation/scale."
        self.rebuildRadioGrp = elements.RadioButtonGroup(radioList=["Rebuild Current Position",
                                                                    "Rebuild At Zero Position"],
                                                         toolTipList=[tooltip, tooltip2],
                                                         margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD))

        # Build Button ---------------------------------------
        tooltip = "Builds the Spline Rig based on the specified objects.  \n" \
                  "-Curve: Select A curve in the UI and run. \n" \
                  "-Joints: Select start & end joints in the UI and run. \n" \
                  "-Spline IK: Select the Ik handle in the UI and run."
        self.buildBtn = elements.styledButton("Build Spline Rig",
                                              icon="splineRig",
                                              toolTip=tooltip,
                                              style=uic.BTN_DEFAULT)
        # Rebuild Button ---------------------------------------
        tooltip = "Rebuilds the rig either in the current position \n " \
                  "or at initial zero position."
        self.rebuildBtn = elements.styledButton("Rebuild",
                                                icon="refresh",
                                                toolTip=tooltip,
                                                style=uic.BTN_DEFAULT,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Bake Button ---------------------------------------
        tooltip = "Deletes the rig while keeping the current joint positions. \n\n" \
                  "Note: Additive FK layer will be kept. \n" \
                  "To delete Additive FK after baking, uncheck while a control is \n" \
                  "selected or right-click on any Additive FK controls"
        self.bakeBtn = elements.styledButton("Bake",
                                             icon="bake",
                                             toolTip=tooltip,
                                             style=uic.BTN_DEFAULT,
                                             minWidth=uic.BTN_W_ICN_MED)
        # Delete Button ------------------------------------
        toolTip = "Deletes the rig and resets the joints to their initial positions. \n" \
                  "To `Delete All`, use the menu item in the dots menu. \n\n" \
                  "Note: Additive FK layer will be kept. \n" \
                  "To delete Additive FK after baking, uncheck while a control is \n" \
                  "selected or right-click on any Additive FK controls"
        self.deleteBtn = elements.styledButton("",
                                               "trash",
                                               toolTip=toolTip,
                                               parent=self,
                                               minWidth=uic.BTN_W_ICN_MED)

        # Allow the widgets to update for these two when updateFromProperties is run
        toolsetWidget.setAllowToolsetUpdate(self.splineBuildCombo)
        toolsetWidget.setAllowToolsetUpdate(self.typeCombo)

        self._dotsMenuWidget()
        self._jointsOnCurveWidgets()
        self._ikHandleWidgets()

    def _dotsMenuWidget(self):
        THEME_PREFS = preference.interface("core_interface")
        iconColor = THEME_PREFS.ICON_PRIMARY_COLOR
        self.dotsMenu = elements.IconMenuButton(parent=self)
        self.dotsMenu.setIconByName("menudots", size=16, colors=iconColor)
        self.dotsMenu.addAction(DotsItems.SelectJoints, icon="cursorSelect")
        self.dotsMenu.addAction(DotsItems.SelectMeta, icon="cube")
        self.dotsMenu.addSeparator()
        self.dotsMenu.addAction(DotsItems.RebuildBaked, icon="refresh")
        self.dotsMenu.addAction(DotsItems.Duplicate, icon="duplicate")
        self.dotsMenu.addSeparator()
        self.dotsMenu.addAction(DotsItems.DeleteAll, icon="trash")
        self.dotsMenu.addAction(DotsItems.ResetSettings, icon="reload2")
        publishAction = self.dotsMenu.addAction(DotsItems.TogglePublish, icon="reload2", checkable=True, checked=False)
        self.dotsMenu.setProperty("publishAction", publishAction)

    def _jointsOnCurveWidgets(self):
        """ Initialise the start end joints widgets

        :return:
        :rtype:
        """
        tooltip = "This is the secondary axis for all joints (joint Y axis up) \n" \
                  "The primary axis will always be +X  (points to next joint).\n\n" \
                  "`Auto` will intelligently choose the secondary axis. \n" \
                  "If the longest edge of the curve's bounding box is \n" \
                  "world y, will be `+Z`, otherwise it will be `+Y`"
        self.upAxisCombo = elements.ComboBoxRegular(label="World Up",
                                                    items=joints.AUTO_UP_VECTOR_POSNEG_LIST,
                                                    setIndex=0,
                                                    toolTip=tooltip,
                                                    boxRatio=2,
                                                    labelRatio=1)
        # Joint Count Int ---------------------------------------
        tooltip = "The number of joints to build along the curve."
        self.jointCountInt = elements.IntEdit(label="Count",
                                              editText=12,
                                              toolTip=tooltip,
                                              editRatio=11,
                                              labelRatio=6)
        # Spacing Weight Slider  ------------------------------------
        tooltip = "The spacing weight between the joints from one end of the curve or the other. \n" \
                  "A value of 0.0 will evenly space objects."
        self.spacingWeightEdit = elements.FloatEdit(label="Weight",
                                                    toolTip=tooltip,
                                                    labelRatio=6,
                                                    editRatio=11)
        tooltip = "Specify an existing curve to build the rig from."
        self.jointsSplineEdit = elements.StringEdit(label="Curve",
                                                    editPlaceholder="Create Spline and add it here",
                                                    editText="",
                                                    toolTip=tooltip,
                                                    editRatio=26,
                                                    labelRatio=7)
        tooltip = "Select a curve from the scene."
        self.inputJointsSplineBtn = elements.styledButton("",
                                                          "arrowLeft",
                                                          self,
                                                          toolTip=tooltip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=15)
        # Create CV Curve Button ------------------------------------
        toolTip = "Create a CV Curve (3 Cubic)"
        self.curveCvBtn = elements.styledButton("",
                                                "curveCv",
                                                toolTip=toolTip,
                                                parent=self,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Reverse Direction Checkbox ---------------------------------------
        tooltip = "Will reverse the direction the joints are built.  \n" \
                  "Note this will reverse the curve direction temporarily \n" \
                  "do not use if curve has history."
        self.reverseJointsCheckbox = elements.CheckBox(label="Reverse Dir",
                                                       toolTip=tooltip,
                                                       checked=False,
                                                       right=True,
                                                       boxRatio=2,
                                                       labelRatio=1)

    def _ikHandleWidgets(self):
        # Spline ---------------------------------------
        tooltip = "Specify the `Spline Ik Handle` for the rig."
        self.ikHandleEdit = elements.StringEdit(label="IK Handle",
                                                editPlaceholder="Enter the IK Handle",
                                                editText="",
                                                toolTip=tooltip,
                                                editRatio=18,
                                                labelRatio=5)
        # Get Spline  ---------------------------------------
        toolTip = "Select the `Spline Ik Handle` and press to add to the UI."
        self.ikHandleSelectBtn = elements.styledButton("",
                                                       "arrowLeft",
                                                       self,
                                                       toolTip=toolTip,
                                                       style=uic.BTN_TRANSPARENT_BG,
                                                       minWidth=15)

        toolTip = "Create Spline IK button, click the first and last joints to create."
        self.ikHandleBtn = elements.styledButton("",
                                                 "ikhandle",
                                                 self,
                                                 toolTip=toolTip,
                                                 minWidth=uic.BTN_W_ICN_MED)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties,
                                         toolsetWidget=toolsetWidget)
        self.themePref = preference.interface("core_interface")
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Grid Checkbox Layout --------------------------------------
        checkboxLayout = elements.GridLayout(margins=(uic.REGPAD, uic.SMLPAD, uic.REGPAD, uic.SMLPAD),
                                             spacing=uic.SVLRG)
        checkboxLayout.addWidget(self.fkCheckBox, 0, 0)
        checkboxLayout.addWidget(self.reverseCheckBox, 0, 1)
        checkboxLayout.addWidget(self.floatCheckBox, 1, 0)
        checkboxLayout.addWidget(self.spineCheckBox, 1, 1)
        checkboxLayout.setColumnStretch(0, 1)
        checkboxLayout.setColumnStretch(1, 1)
        # Orient Options Layout --------------------------------------
        controlComboLayout = elements.hBoxLayout(spacing=uic.SLRG)
        controlComboLayout.addWidget(self.typeCombo, 1)
        controlComboLayout.addWidget(self.hierSwitchCombo, 1)
        # Orient Options Layout --------------------------------------
        orientLayout = elements.hBoxLayout(spacing=uic.SLRG)
        orientLayout.addWidget(self.controlsIntE, 1)
        orientLayout.addWidget(self.orientRootCombo, 1)
        # Controls Layout --------------------------------------
        ctrlScaleLayout = elements.hBoxLayout(spacing=uic.SLRG)
        ctrlScaleLayout.addWidget(self.scaleFloatE, 1)
        ctrlScaleLayout.addWidget(self.meshMenuCheckbox, 1)
        # Additive FK Layout --------------------------------------
        addFkLayout = elements.hBoxLayout(spacing=uic.REGPAD)
        addFkLayout.addWidget(self.additiveFk, 1)
        addFkLayout.addWidget(self.controlSpacingInt, 1)
        # Button Layout --------------------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        buttonLayout.addWidget(self.buildBtn, 7)
        buttonLayout.addWidget(self.rebuildBtn, 3)
        buttonLayout.addWidget(self.bakeBtn, 3)
        buttonLayout.addWidget(self.deleteBtn, 1)

        # Build Mode Widget -------------------------------------
        self.buildMode.addWidget(self._jointsOnCurveWidget())
        self.buildMode.addWidget(self._startEndJointsWidget())
        self.buildMode.addWidget(self._splineIkHandleWidget())

        topLayout = elements.hBoxLayout()
        topLayout.addWidget(self.splineCombo)
        topLayout.addWidget(self.dotsMenu)

        # Rebuild Radio -------------------------------------
        rebuildRadioLayout = elements.hBoxLayout(margins=(0, 0, 0, 0))
        rebuildRadioLayout.addWidget(self.rebuildRadioGrp)

        # Main Layout --------------------------------------
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(elements.Divider())
        mainLayout.addWidget(self.splineBuildCombo)
        mainLayout.addWidget(self.buildMode)
        mainLayout.addWidget(self.controlRigsTitle)
        mainLayout.addLayout(checkboxLayout)

        mainLayout.addWidget(self.additiveFkTitle)
        additiveLayout = elements.hBoxLayout(margins=(uic.REGPAD, uic.SMLPAD, uic.REGPAD, 0),
                                             spacing=uic.SVLRG)
        additiveLayout.addLayout(addFkLayout)
        mainLayout.addLayout(additiveLayout)

        mainLayout.addWidget(self.splineControlsTitle)
        mainLayout.addLayout(controlComboLayout)
        mainLayout.addLayout(orientLayout)
        mainLayout.addLayout(ctrlScaleLayout)
        mainLayout.addLayout(rebuildRadioLayout)
        mainLayout.addLayout(buttonLayout)

    def _startEndJointsWidget(self):
        startJointWidget = QtWidgets.QWidget(self)
        startJointLayout = elements.hBoxLayout(margins=utils.marginsDpiScale(2, 0, 3, 0), spacing=0)
        startJointWidget.setLayout(startJointLayout)
        startJointLayout.addWidget(self.startJointStrE, 10)
        startJointLayout.addWidget(self.getStartJntBtn, 1)

        endJointWidget = QtWidgets.QWidget(self)
        endJointLayout = elements.hBoxLayout(margins=utils.marginsDpiScale(2, 0, 3, 0), spacing=0)
        endJointWidget.setLayout(endJointLayout)
        endJointLayout.addWidget(self.endJointStrE, 10)
        endJointLayout.addWidget(self.getEndJntBtn, 1)
        styleSheet = ".QWidget {{background-color: rgb{}; border-radius: {}px}}".format(str((38, 38, 38)),
                                                                                        self.themePref.ONE_PIXEL)
        endJointWidget.setStyleSheet(styleSheet)
        startJointWidget.setStyleSheet(styleSheet)

        # Start Layout --------------------------------------
        jointLayout = elements.hBoxLayout()

        jointLayout.addWidget(QtWidgets.QLabel("Joints"), 2)
        jointLayout.addWidget(startJointWidget, 5)
        jointLayout.addWidget(endJointWidget, 5)

        jointsMode = QtWidgets.QWidget(parent=self.buildMode)
        jointsModeLayout = elements.vBoxLayout()
        jointsModeLayout.addLayout(jointLayout)
        jointsModeLayout.addStretch()
        jointsMode.setLayout(jointsModeLayout)

        return jointsMode

    def _jointsOnCurveWidget(self):
        jointsOnCurveWidget = QtWidgets.QWidget(parent=self.buildMode)
        curveModeLayout = elements.vBoxLayout()
        editLayout = elements.hBoxLayout()
        editLayout.addWidget(self.jointsSplineEdit)
        editLayout.addWidget(self.inputJointsSplineBtn)
        editLayout.addWidget(self.curveCvBtn)
        # Name Layout ---------------------------------------
        nameLayout = elements.hBoxLayout()
        nameLayout.addWidget(self.spacingWeightEdit, 1)
        nameLayout.addWidget(self.reverseJointsCheckbox, 1)
        # Count Layout ---------------------------------------
        countLayout = elements.hBoxLayout()
        countLayout.addWidget(self.jointCountInt, 1)
        countLayout.addWidget(self.upAxisCombo, 1)
        # Button Layout ---------------------------------------
        curveModeLayout.addLayout(editLayout)
        curveModeLayout.addLayout(countLayout)
        curveModeLayout.addLayout(nameLayout)
        jointsOnCurveWidget.setLayout(curveModeLayout)
        return jointsOnCurveWidget

    def _splineIkHandleWidget(self):
        splineIkHandleWidget = QtWidgets.QWidget(parent=self.buildMode)
        existingCurveLayout = elements.vBoxLayout()
        curveLayout = elements.hBoxLayout()
        curveLayout.addWidget(self.ikHandleEdit, 10)
        curveLayout.addWidget(self.ikHandleSelectBtn, 1)
        curveLayout.addWidget(self.ikHandleBtn, 1)
        existingCurveLayout.addLayout(curveLayout)
        splineIkHandleWidget.setLayout(existingCurveLayout)
        return splineIkHandleWidget
