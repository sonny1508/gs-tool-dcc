import zoo.libs.toolsets.controls
from maya import cmds
from zoo.libs.toolsets.controls.controlscore import ControlsCore
from zoo.libs.maya.cmds.objutils import shapenodes, filtertypes, objcolor, namehandling
from zoo.libs.maya.cmds.rig import controls
from zoo.libs.pyqt import keyboardmouse
from zoo.libs.utils import output
from zoovendor.Qt import QtCore


class ControlsCoreMaya(ControlsCore):
    refreshThumbs = QtCore.Signal()

    def __init__(self, toolsetWidget):
        """

        :param toolsetWidget:
        :type: zoo.apps.uitoolsets.controlcreator.ControlCreator
        """

        super(ControlsCoreMaya, self).__init__(toolsetWidget)

    @property
    def properties(self):
        return self._toolset.properties

    def updateSelectedObjs(self, message=True, deselect=True):
        """Remembers the object selection so controls can be deselected while changing

        Updates self.selObjs

        :param message: Report the message to the user if nothing selected
        :type message: bool
        :param message: Deselect the objects after recording
        :type message: bool
        :return isSelection: False if nothing is selected
        :rtype isSelection: bool
        """
        newSelection = cmds.ls(selection=True, long=True)
        if newSelection:
            self.selObjs = newSelection
            # self.sendControlSelection()  # updates all windows
            self.sendControlSelection()
        if not self.selObjs:
            if message:
                output.displayWarning("Please select controls/curves.")
            return False
        if deselect:
            cmds.select(deselect=True)
        return True

    def saveControlsToLibrary(self, newControlName, directory):
        """

        :param newControlName:
        :return:
        """  # todo: create custom directory where everything is saved
        controls.saveControlSelected(newControlName, directory, message=True)

    def replaceCurves(self):
        """Replaces the curves of one shape node from another.  Last selected object remains with it's shape switched"""
        objList = self.filterCurveJoining()
        combinedObject = shapenodes.shapeNodeParentSafe(objList, replace=True, message=True,
                                                        selectObj=True, delShapeType="nurbsCurve")
        self.selObjs = [combinedObject]

    def filterCurveTransformsOnlyUpdateSelObj(self, disableHierarchy=False, deselect=True):

        if disableHierarchy:
            children = False
        else:
            children = self.properties.selHierarchyRadio.value
        """Return only transforms with curve shapes, also update the selection memory, self.selObjs"""
        if not self.updateSelectedObjs(message=False, deselect=deselect):  # updates self.selObjs
            return list()  # message reported
        # check shapes are curves and return the list
        if self.selObjs:  # check if objs exist as may have been deleted
            deletedObjs = list()
            for obj in self.selObjs:
                if not cmds.objExists(obj):
                    deletedObjs.append(obj)
            if deletedObjs:
                self.selObjs = [x for x in deletedObjs if x not in self.selObjs]
            if not self.selObjs:
                return list()
        return filtertypes.filterTypeReturnTransforms(self.selObjs,
                                                      children=children,
                                                      shapeType="nurbsCurve")

    def filterCurveJoining(self):
        """Filters the curves for joining, either combine or replace

        The first objects (not the last) must include nurbsCurves, and the last object must be a transform or joint
        If so then return the object list, otherwise returns an empty list
        :return objList: An object list now checked, will be empty if the filtering failed.
        :rtype objList: list(str)
        """
        # todo: static function maybe move somewhere else
        selObjs = cmds.ls(selection=True, long=True)
        firstObjs = selObjs[:-1]
        lastObject = selObjs[-1]
        nodeType = cmds.nodeType(lastObject)
        if nodeType != "transform" and nodeType != "joint":
            output.displayWarning("The last object must be an object (transform) or a joint, please reselect")
            return list()
        firstObjs = filtertypes.filterTypeReturnTransforms(firstObjs,
                                                           children=False,
                                                           shapeType="nurbsCurve")
        if not firstObjs:
            output.displayWarning("The first selected objects must have valid curve shapes, please reselect")
            return list()
        firstObjs.append(lastObject)
        objList = firstObjs
        return objList

    def scaleCVs(self, positive):
        """UI function that scales nurbs curve objects based on their CVs, will not affect transforms

        :param positive: is the scale bigger positive=True, or smaller positive=False
        :type positive: bool
        """
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # Then no shapes as nurbsCurves
            return
        multiplier, reset = keyboardmouse.ctrlShiftMultiplier()  # for alt shift and ctrl keys with left click
        scale = 5.0
        if reset:  # try to reset with the zoo scale tracker (if it exists)
            controls.scaleResetBrkCnctCtrlList(curveTransforms)
            cmds.select(deselect=True)
            return
        scale = scale * multiplier  # if control or shift is held down
        if positive:
            scale = 1 + (scale * .01)  # 5.0 becomes 1.05
        else:  # negative
            scale = 1 - (scale * .01)  # 5.0 becomes 0.95
        scaleComboIndex = 0
        if scaleComboIndex == 0:  # all xyz
            scaleXYZ = [scale, scale, scale]
        elif scaleComboIndex == 1:  # x only
            scaleXYZ = [scale, 1, 1]
        elif scaleComboIndex == 2:  # y only
            scaleXYZ = [1, scale, 1]
        else:  # z only
            scaleXYZ = [1, 1, scale]

        controls.scaleBreakConnectCtrlList(curveTransforms, scaleXYZ, relative=True)
        cmds.select(deselect=True)

    def rotateCVs(self, positive=True):
        """Rotates CVs by local space rotation"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        # for alt shift and ctrl keys with left click
        multiplier, reset = keyboardmouse.ctrlShiftMultiplier(shiftMultiply=2.0, ctrlMultiply=0.5)
        rotateComboInt = self.properties.rotateComboBox.value
        rotateOffset = 22.5
        multiplyOffset = rotateOffset * multiplier
        if reset:  # try to reset with the zoo scale tracker (if it exists)
            controls.rotateResetBrkCnctCtrlList(curveTransforms)
            cmds.select(deselect=True)
            return
        if not positive:
            multiplyOffset = -multiplyOffset
        if rotateComboInt == 0:  # X
            rotateXYZ = [multiplyOffset, 0, 0]
        elif rotateComboInt == 1:  # Y
            rotateXYZ = [0, multiplyOffset, 0]
        else:  # Z
            rotateXYZ = [0, 0, multiplyOffset]
        controls.rotateBreakConnectCtrlList(curveTransforms, rotateXYZ, relative=True)
        cmds.select(deselect=True)

    def absoluteScale(self, nullTxt=""):
        """Scales all controls from any selected part of the rig, to an exact size give by the GUI"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        scale = self.properties.scaleFloat.value
        controls.scaleBreakConnectCtrlList(curveTransforms, (scale, scale, scale), relative=False)
        # controls.scaleControlAbsoluteList((scale, scale, scale), curveTransforms)
        cmds.select(deselect=True)

    def offsetColorSelected(self, offsetTuple, resetClicked):
        """Offset the selected control color (and potential children) when the color is changed if there's a selection

        :param offsetTuple: The offset as (hue, saturation, value)
        :type offsetTuple: tuple
        :param resetClicked: Has the reset been activated (alt clicked)
        :type resetClicked: bool
        """
        if resetClicked:  # set default color
            self.colorSelected(0, 0, 0)
            return
        # filter curves ---------------
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        # Do the offset ------------------
        offsetFloat, hsvType = objcolor.convertHsvOffsetTuple(offsetTuple)
        controls.offsetHSVControlList(curveTransforms, offsetFloat, hsvType=hsvType, linear=True)

    def getColorSelected(self):
        """From selection get the color of the current control curve and change the GUI to that color"""
        curveTransformList = filtertypes.filterByNiceTypeKeepOrder(filtertypes.CURVE,
                                                                   searchHierarchy=False,
                                                                   selectionOnly=True,
                                                                   dag=False,
                                                                   removeMayaDefaults=False,
                                                                   transformsOnly=True,
                                                                   message=True)
        if not curveTransformList:
            output.displayWarning("Please select a curve object (transform)")
            return
        firstShapeNode = shapenodes.filterShapesInList(curveTransformList)[0]  # must be a curve
        color = objcolor.getRgbColor(firstShapeNode, hsv=False, linear=True)
        return color

    def selectControlsByColor(self, color=None, verbose=True):
        """Selects the controls that match the GUI color"""
        if not color:
            color = self.properties.colorSwatchBtn.value
        curveTransformList = filtertypes.filterByNiceTypeKeepOrder(filtertypes.CURVE,
                                                                   searchHierarchy=False,
                                                                   selectionOnly=False,
                                                                   dag=False,
                                                                   removeMayaDefaults=False,
                                                                   transformsOnly=True,
                                                                   message=True)
        if not curveTransformList:
            if verbose:
                output.displayWarning("No curve objects found in the scene")
            return
        objcolor.selectObjsByColor(curveTransformList, color, message=True)
        return curveTransformList

    def setControlLineWidth(self):
        """Changes the lineWidth attribute of a curve (control) making the lines appear thicker or thinner.

        Note: Don't add @undodecorator.undoDecorator, it doesn't need it"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        controls.setCurveLineThickness(curveTransforms, self.properties.lineWidthTxt.value)

    def freezeControlTracker(self):
        """Freezes the scale tracker attributes setting them to a scale of 1.0 no matter the current scale"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        controls.freezeScaleTrackerList(curveTransforms, message=True)

    def pureName(self):
        """ Pure name

        :return:
        """

        curveTransformList = filtertypes.filterByNiceTypeKeepOrder(filtertypes.CURVE,
                                                                   searchHierarchy=False,
                                                                   selectionOnly=True,
                                                                   dag=False,
                                                                   removeMayaDefaults=False,
                                                                   transformsOnly=True,
                                                                   message=True)
        if not curveTransformList:
            output.displayWarning("Please select a curve object (transform)")
            return
        pureName = namehandling.mayaNamePartTypes(curveTransformList[0])[2]  # return the short name, no namespace
        return pureName

    # ------------------------------------
    # MAIN LOGIC - BUILD
    # ------------------------------------

    def replaceWithShapeDesign(self, designName="", directory=None):
        if not designName:  # no image has been selected
            output.displayWarning("Please select an asset thumbnail image.")
            return
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        # directory = directory or self.defaultDirectory()

        rotateOffset = controls.ROTATE_UP_DICT[self.properties.orientVectorComboBox.value]
        controls.replaceControlCurves(curveTransforms,
                                      folderpath=directory,
                                      designName=designName,
                                      rotateOffset=rotateOffset,
                                      autoScale=True,
                                      message=False,
                                      maintainLineWidth=True)
        output.displayInfo("Controls changed to `{}`: {}".format(designName,
                                                                 namehandling.getShortNameList(
                                                                     curveTransforms)))

    def buildControlsAll(self, designName="", forceCreate=False, freeze=False, group=False, folderPath=None):
        """Builds all styles depending on the combo value

        Note: Undo is built into this function
        """
        selObjs = cmds.ls(selection=True, long=True)
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()

        if not designName:  # no image has been selected
            output.displayWarning("Please select an asset thumbnail image.")
            return
        if curveTransforms and not forceCreate:  # Replace don't build
            self.replaceWithShapeDesign(designName, folderPath)
            return
        # Build from scratch
        cmds.select(selObjs, replace=True)
        rotateOffset = controls.ROTATE_UP_DICT[self.properties.orientVectorComboBox.value]
        scale = [self.properties.scaleFloat.value, self.properties.scaleFloat.value, self.properties.scaleFloat.value]
        buildType = controls.CONTROL_BUILD_TYPE_LIST[self.properties.buildComboBox.value]
        controlList = controls.buildControlsGUI(buildType=buildType,
                                                folderpath=folderPath,
                                                designName=designName,
                                                rotateOffset=rotateOffset,
                                                scale=scale,
                                                children=self.properties.selHierarchyRadio.value,
                                                rgbColor=self.properties.colorSwatchBtn.value,
                                                postSelectControls=True,
                                                trackScale=True,
                                                lineWidth=-1,
                                                grp=group,
                                                freezeJnts=freeze,
                                                addToUndo=True)
        self.selObjs = controlList
        self.sendControlSelection()


    def colorSelected(self, color):
        """Change the selected control color (and potential children) when the color is changed if a selection"""
        curveTransforms = self.filterCurveTransformsOnlyUpdateSelObj()
        if not curveTransforms:  # then no shapes as nurbsCurves
            return
        controls.colorControlsList(curveTransforms, color, linear=True)
