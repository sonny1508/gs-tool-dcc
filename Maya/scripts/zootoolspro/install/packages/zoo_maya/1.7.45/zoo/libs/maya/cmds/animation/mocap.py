"""Creates a simple rig setup that enables the user to easily lock feet from a FK baked motion capture.


1. User bake feet in ik check for flipping

2. User scales the skeleton right size to match the leg height of the target character

3. UI builds the setup
    feetRetargetInstance.createSetup(cleanup=True)

4. User moves the feet loc grps manually to match the target feet positions

5. UI Constrains and checks
    feetRetargetInstance.constrainControls()

6. UI Bake out everything & Euler filter
    feetRetargetInstance.bakeControls()

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.animation import mocap
    feetRetargetInstance = mocap.MocapFeetRetargeter(startTime=0.0,
                                                     endTimeTime=100.0,
                                                     hips_source="mixamorig1:Hips",
                                                     footL_source="mixamorig1:LeftFoot",
                                                     footR_source="mixamorig1:RightFoot",
                                                     hips_target="spine_M_cog_anim",
                                                     footL_target="leg_L_foot_fk_anim",
                                                     footR_target="leg_R_foot_fk_anim")
    feetRetargetInstance.createSetup(cleanup=True)
    feetRetargetInstance.constrainControls()
    feetRetargetInstance.deleteControlConstraints()  # deletes the constraints
    feetRetargetInstance.bakeControls() # constraints must exist
    feetRetargetInstance.deleteSetup() # deletes the setup


"""
import ast

import maya.mel as mel
from maya import cmds

from zoo.libs.maya import zapi

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import namehandling, attributes, connections, objcolor
from zoo.libs.maya.cmds.animation import bakeanim, animlayers, generalanimation
from zoo.libs.maya.cmds.rig import controls, controlconstants

MOCAP_NETWORK_NODE = "zooMocapData_networkNode"
ATTR_SOURCE_M_AND_BAKE = "sourceMatchAndBakeData"
ATTR_TARGET_M_AND_BAKE = "targetMatchAndBakeData"


def selectedObject():
    """Selects and returns an object for use in the UI"""
    selObj = cmds.ls(selection=True)
    if not selObj:
        output.displayWarning("No object selected")
        return ""
    return selObj[0]


def createBoxControl(ctrlName, controlScale, color=(1.0, 0.0, 0.0)):
    """Creates a box control with a given name, scale and color

    :param ctrlName: The name of the control
    :type ctrlName: str
    :param controlScale: The size of the control
    :type controlScale: list(float, float, float)
    :param color: The color of the control
    :type color: tuple

    :return boxControl: The arrow ctrl transform node
    :rtype boxControl: str
    :return boxControlShape: The arrow ctrl shape node
    :rtype boxControlShape: str
    """
    boxControl = controls.createControlCurve(folderpath="",
                                             ctrlName=ctrlName,
                                             curveScale=controlScale,
                                             designName=controlconstants.CTRL_CUBE,
                                             addSuffix=False,
                                             shapeParent=None,
                                             rotateOffset=(90.0, 0.0, 0.0),
                                             trackScale=True,
                                             lineWidth=-1,
                                             rgbColor=color,
                                             addToUndo=True)[0]
    return boxControl


def createMocapNetworkNode():
    """Creates the mocap network node if it doesn't exist, returns the node name"""
    mocapNode = str(MOCAP_NETWORK_NODE)
    if not cmds.objExists(mocapNode):
        mocapNode = cmds.createNode('network', name=MOCAP_NETWORK_NODE)
    return mocapNode


def deleteMocapNetworkNode():
    """Deletes the mocap network node if it exists"""
    if cmds.objExists(MOCAP_NETWORK_NODE):
        cmds.delete(MOCAP_NETWORK_NODE)


def setMatchAndBakeToScene(sourceDict, targetDict):
    """Sets the match and bake data to the scene, adds the dictionaries to the mocap network node.

    :param sourceDict:
    :type sourceDict:
    :param targetDict:
    :type targetDict:
    """
    mocapNode = createMocapNetworkNode()
    if not cmds.attributeQuery(ATTR_SOURCE_M_AND_BAKE, node=mocapNode, exists=True):
        cmds.addAttr(mocapNode, longName=ATTR_SOURCE_M_AND_BAKE, dataType="string")
        cmds.addAttr(mocapNode, longName=ATTR_TARGET_M_AND_BAKE, dataType="string")
    cmds.setAttr("{}.{}".format(mocapNode, ATTR_SOURCE_M_AND_BAKE), str(sourceDict), type="string")
    cmds.setAttr("{}.{}".format(mocapNode, ATTR_TARGET_M_AND_BAKE), str(targetDict), type="string")


def matchAndBakeDataFromScene():
    """Returns the match and bake data from the scene, returns the source and target dictionaries"""
    if not cmds.objExists(MOCAP_NETWORK_NODE):
        return dict(), dict()
    if not cmds.attributeQuery(ATTR_SOURCE_M_AND_BAKE, node=MOCAP_NETWORK_NODE, exists=True):
        return dict(), dict()
    sourceDictStr = cmds.getAttr("{}.{}".format(MOCAP_NETWORK_NODE, ATTR_SOURCE_M_AND_BAKE))
    targetDictStr = cmds.getAttr("{}.{}".format(MOCAP_NETWORK_NODE, ATTR_TARGET_M_AND_BAKE))
    sourceDict = ast.literal_eval(sourceDictStr)
    targetDict = ast.literal_eval(targetDictStr)

    return sourceDict, targetDict


class MocapFeetRetargeter(object):
    """Creates a simple rig setup that enables the user to easily lock feet from a FK baked motion capture.

    """
    hipsMarker_name = "hips_marker_mocapTransferZoo"
    hipsMainGrp_name = "hips_mainGrp_mocapTransferZoo"
    hipsCtrl_name = "hips_offsetCtrl_move_mocapTransferZoo"
    footLMarker_name = "footL_marker_mocapTransferZoo"
    footRMarker_name = "footR_marker_mocapTransferZoo"
    footLCtrl_name = "footL_offsetCtrl_mocapTransferZoo"
    footRCtrl_name = "footR_offsetCtrl_mocapTransferZoo"
    yellow = (0.846, 0.792, 0.026)
    red = (0.953, 0.002, 0.181)
    blue = (0.0, 0.587, 0.829)

    def __init__(self,
                 startTime=0.0,
                 endTime=100.0,
                 hips_source="",
                 footL_source="",
                 footR_source="",
                 hips_target="",
                 footL_target="",
                 footR_target="",
                 controlScale=1.0):

        super(MocapFeetRetargeter, self).__init__()
        self.startTime = startTime
        self.endTime = endTime
        self.hips_source = hips_source
        self.footL_source = footL_source
        self.footR_source = footR_source
        self.hips_target = hips_target
        self.footL_target = footL_target
        self.footR_target = footR_target
        self.hips_marker = ""
        self.footL_marker = ""
        self.footR_marker = ""
        self.hipsConstraint = ""
        self.footLConstraint = ""
        self.footRConstraint = ""
        self.constraintList = [self.hipsConstraint, self.footLConstraint, self.footRConstraint]
        self.locConstraints = list()
        self.hipsMain_grp = ""
        self.controlScale = controlScale
        self.hips_ctrl = ""
        self.footL_ctrl = ""
        self.footR_ctrl = ""

    def validateObjs(self, logToScript=False):
        """Checks if the objects are valid and can be used in the setup.

        Returns True if objects are valid

        :param logToScript: Prints objects that pass the test to the script editor and opens it.
        :type logToScript: bool
        :return: Returns true if the objects are valid
        :rtype: bool
        """
        valid = True
        objList = [self.hips_source, self.footL_source, self.footR_source, self.hips_target, self.footL_target,
                   self.footR_target]
        if "" in objList:
            output.displayWarning("Object/s have no name, please enter a name.")
            return False

        for i, obj in enumerate(objList):
            if not cmds.objExists(obj):
                output.displayWarning("Object `{}` does not exist in the scene.".format(obj))
                valid = False
                continue
            else:
                if not namehandling.nameIsUnique(obj):
                    output.displayWarning("Object `{}` is not unique in the scene, "
                                          "another object exists with identical naming.".format(obj))
                    valid = False
                    continue
                if i > 2:  # Is a target object and needs to be constrained, cannot be locked
                    lockedAttrs = attributes.getLockedConnectedAttrs(obj,
                                                                     attrList=attributes.MAYA_TRANS_ROT_ATTRS,
                                                                     keyframes=False,
                                                                     constraints=False)
                    if lockedAttrs:
                        output.displayWarning("Object ``")
                        valid = False
                        continue
                if logToScript:
                    output.displayInfo("Object `obj` checks passed: Is valid.")
                    # open script editor
                    mel.eval("if (`scriptedPanel - q - exists scriptEditorPanel1`) "
                             "{scriptedPanel -e -tor scriptEditorPanel1; "
                             "showWindow scriptEditorPanel1Window; "
                             "selectCurrentExecuterControl;} "
                             "else {CommandWindow;}")
        return valid

    def _cleanup(self):
        """Clean/delete if setup already exists"""
        for obj in [self.hipsMarker_name, self.footLMarker_name, self.footRMarker_name, self.footLCtrl_name,
                    self.footRCtrl_name]:
            if cmds.objExists(obj):
                cmds.delete(obj)

    def _bakeMarkers(self):
        """Bakes the marker setup, usually after creation"""
        markers = [self.hips_marker, self.footL_marker, self.footR_marker, self.hipsMain_grp]
        animLayer = animlayers.firstSelectedAnimLayer(ignoreBaseLayer=True)  # first selected animation layer
        bakeanim.bakeAnimationLayers(markers,
                                     attributes.MAYA_TRANS_ROT_ATTRS,
                                     [self.startTime, self.endTime],
                                     1.0,
                                     animLayer,
                                     shapes=True, message=True)

    def _parent(self, obj, parent):
        """Parents the object to the parent and returns the full path name of the object"""
        objZapi = zapi.nodeByName(obj)
        cmds.parent(obj, parent)
        return objZapi.fullPathName()

    def _calculateScaleControls(self):
        hipsCtrlScale = [40.0 * self.controlScale, 15.0 * self.controlScale, 40.0 * self.controlScale]
        footCtrlScale = [12.0 * self.controlScale, 12.0 * self.controlScale, 12.0 * self.controlScale]
        return hipsCtrlScale, footCtrlScale

    def controlsScale(self):
        hips_ctrl, footL_ctrl, footR_ctrl = self.controls()
        if not hips_ctrl:
            return None
        # get the scale values of the controls zooScaleTrack_x
        currentScale = cmds.getAttr("{}.zooScaleTrack_x".format(hips_ctrl))
        if currentScale == 0.0:
            return 0.01
        return currentScale / 40.0

    def createSetup(self, cleanup=True, rotYtrack=True, bakeAndDelete=True):
        """Creates the setup hips and two feet.

        :param cleanup: deletes the previous setup automatically on build
        :type cleanup: bool
        :param rotYtrack: Includes the Y rotation of the setup on the feet. If off ignores rotation.
        :type rotYtrack: bool
        :param bakeAndDelete: If False will not bake the markers or delete the constraints
        :type bakeAndDelete: bool
        """
        self.locConstraints = list()
        if not self.validateObjs(logToScript=False):
            return  # errors have been reported

        if cleanup:
            self._cleanup()

        self.hips_marker = cmds.group(em=True, name=self.hipsMarker_name, empty=True)
        self.footL_marker = cmds.group(em=True, name=self.footLMarker_name, empty=True)
        self.footR_marker = cmds.group(em=True, name=self.footRMarker_name, empty=True)

        # create main group
        self.hipsMain_grp = cmds.group(em=True, name=self.hipsMainGrp_name, empty=True)

        # create controls
        if self.controlScale == 0.0:
            self.controlScale = 0.01
        hipsCtrlScale, footCtrlScale = self._calculateScaleControls()
        self.hips_ctrl = createBoxControl(self.hipsCtrl_name, hipsCtrlScale, color=self.yellow)
        self.footL_ctrl = createBoxControl(self.footLCtrl_name, footCtrlScale, color=self.red)
        self.footR_ctrl = createBoxControl(self.footRCtrl_name, footCtrlScale, color=self.blue)

        # parent controls
        self.hips_ctrl = self._parent(self.hips_ctrl, self.hipsMain_grp)
        self.footL_ctrl = self._parent(self.footL_ctrl, self.hipsMain_grp)
        self.footR_ctrl = self._parent(self.footR_ctrl, self.hipsMain_grp)

        # handle on and hips gimbal order to zxy
        cmds.setAttr("{}.displayHandle".format(self.hips_marker), True)
        objcolor.setColorShapeRgb(self.hips_marker, self.yellow, linear=True)
        cmds.setAttr("{}.displayHandle".format(self.footL_marker), True)
        objcolor.setColorShapeRgb(self.footL_marker, self.red, linear=True)
        cmds.setAttr("{}.displayHandle".format(self.footR_marker), True)
        objcolor.setColorShapeRgb(self.footR_marker, self.blue, linear=True)

        # zxy euler rotation orders
        for obj in [self.hipsMain_grp, self.hips_marker, self.footL_marker, self.footR_marker, self.hips_ctrl,
                    self.footL_ctrl, self.footR_ctrl]:
            cmds.setAttr("{}.rotateOrder".format(obj), 2)  # zxy rotation order

        # parent to grps
        self.hips_marker = self._parent(self.hips_marker, self.hips_ctrl)
        self.footL_marker = self._parent(self.footL_marker, self.footL_ctrl)
        self.footR_marker = self._parent(self.footR_marker, self.footR_ctrl)

        # match groups
        cmds.matchTransform(self.hipsMain_grp, self.hips_source, position=True, rotation=True)
        cmds.matchTransform(self.footL_ctrl, self.footL_source, position=True, rotation=True)
        cmds.matchTransform(self.footR_ctrl, self.footR_source, position=True, rotation=True)

        # Constrain the hips and two feet.
        self.locConstraints.append(cmds.parentConstraint(self.hips_source, self.hipsMain_grp, maintainOffset=False)[0])
        self.locConstraints.append(cmds.parentConstraint(self.hips_source, self.hips_marker, maintainOffset=False)[0])
        self.locConstraints.append(cmds.parentConstraint(self.footL_source, self.footL_marker, maintainOffset=False)[0])
        self.locConstraints.append(cmds.parentConstraint(self.footR_source, self.footR_marker, maintainOffset=False)[0])

        # hips remove the y translate and also x and z on rotate
        connections.breakAttrList(["{}.ty".format(self.hipsMain_grp),
                                   "{}.rx".format(self.hipsMain_grp),
                                   "{}.rz".format(self.hipsMain_grp)])

        if not rotYtrack:
            connections.breakAttrList(["{}.ry".format(self.hipsMain_grp)])

        if bakeAndDelete:
            self.bakeMarkersDelConstraints()

        # Select the feet controls
        cmds.select([self.footL_ctrl, self.footR_ctrl], replace=True)

    def controls(self):
        """Returns the control objects"""
        if self.hips_ctrl and self.footL_ctrl and self.footR_ctrl:
            if cmds.objExists(self.hips_ctrl) and cmds.objExists(self.footL_ctrl) and cmds.objExists(self.footR_ctrl):
                return self.hips_ctrl, self.footL_ctrl, self.footR_ctrl
        else:
            if cmds.objExists(self.hipsCtrl_name) and cmds.objExists(self.footLMarker_name) and cmds.objExists(
                    self.footLMarker_name):
                return self.hipsCtrl_name, self.footLCtrl_name, self.footRCtrl_name
        return "", "", ""

    def scaleControls(self, scale):
        """Scales the control objects

        :param scale: The scale value
        :type scale: float, float, float
        """
        hipsCtrl, footLCtrl, footRCtrl = self.controls()
        if not hipsCtrl:
            output.displayWarning("No controls found or are broken, please build or rebuild the setup.")
            return
        self.controlScale = scale
        hipsCtrlScale, footCtrlScale = self._calculateScaleControls()
        controls.scaleBreakConnectCtrlList([footLCtrl, footRCtrl], footCtrlScale, relative=False)
        controls.scaleBreakConnectCtrlList([hipsCtrl], hipsCtrlScale, relative=False)

    def bakeMarkersDelConstraints(self):
        """Bakes the markers and deletes the constraints"""
        if not self.locConstraints:
            output.displayWarning("No marker constraints were found.")
            return
        self._bakeMarkers()
        cmds.delete(self.locConstraints)

    def constrainControls(self):
        """Constrains the controls to the marker setup"""
        if not self.validateObjs(logToScript=False):
            return  # errors have been reported
        if not self.hips_marker:
            self.hips_marker = self.hipsMarker_name
        if not self.footL_marker:
            self.footL_marker = self.footLMarker_name
        if not self.footR_marker:
            self.footR_marker = self.footRMarker_name

        self.hipsConstraint = cmds.parentConstraint(self.hips_marker, self.hips_target, maintainOffset=True)[0]
        self.footLConstraint = cmds.parentConstraint(self.footL_marker, self.footL_target, maintainOffset=True)[0]
        self.footRConstraint = cmds.parentConstraint(self.footR_marker, self.footR_target, maintainOffset=True)[0]
        self.constraintList = [self.hipsConstraint, self.footLConstraint, self.footRConstraint]

    def validateConstraints(self):
        """Validate the constraints and return the valid constraints, empty list if None found."""
        constraintList = []
        success = False
        for constraint in self.constraintList:
            if cmds.objExists(constraint):
                constraintList.append(constraint)
                success = True
        if not success:  # Try to assume the names and get the constraints automagically
            controls = [self.hips_target, self.footL_target, self.footR_target]
            validControls = [ctrl for ctrl in controls if cmds.objExists(ctrl)]
            if validControls:
                constraintList = cmds.listRelatives(validControls, children=True, type="constraint",
                                                    allDescendents=False)
        return constraintList

    def deleteControlConstraints(self, message=True):
        """Deletes the constraints on the controls if the user wants to bail and re adjust"""
        validConstraints = self.validateConstraints()
        cmds.delete(validConstraints)
        if validConstraints and message:
            output.displayInfo("Control Constraints deleted")
        elif message:
            output.displayWarning("Control Constraints not found.")

    def bakeControls(self, eulerFilter=True, deleteSetup=True):
        """Bakes the controls

        :param eulerFilter: Runs the euler filter on the rotation curves of the baked controls
        :type eulerFilter: bool
        :param deleteSetup: Runs the euler filter on the rotation curves of the baked controls
        :type deleteSetup: bool
        """
        # Check if the constraints exist
        constraintList = self.validateConstraints()
        if not constraintList:
            output.displayInfo("The constraints do not exist, please constrain the controls first.")
            return

        # Error check controls are valid ------------
        controls = [self.hips_target, self.footL_target, self.footR_target]
        for ctrl in controls:
            if not ctrl:
                output.displayWarning("There are no target control objects. Please input into the UI")
                return
            if not cmds.objExists(ctrl):
                output.displayWarning(
                    "There are no target control object `{}` was not found in the scene.".format(ctrl))
                return

        # Do the bake -------------------
        animLayer = animlayers.firstSelectedAnimLayer(ignoreBaseLayer=True)  # first selected animation layer
        bakeanim.bakeAnimationLayers(controls,
                                     attributes.MAYA_TRANS_ROT_ATTRS,
                                     [self.startTime, self.endTime],
                                     1.0,
                                     animLayer,
                                     shapes=True, message=True)

        # Delete the constraints --------------
        cmds.delete(constraintList)

        # Euler filter controls -----------------------
        if eulerFilter:
            sel = cmds.ls(selection=True)
            cmds.select(controls, replace=True)
            generalanimation.eulerFilter()
            cmds.select(sel, replace=True)

        # Delete the setup ------------------
        if deleteSetup:
            self.deleteSetup()

    def deleteSetup(self):
        """Deletes the setup by deleting the top hips group only."""
        success = False
        if self.hipsMain_grp:
            cmds.delete(self.hipsMain_grp)
            success = True
        else:
            if cmds.objExists(self.hipsMainGrp_name):
                cmds.delete(self.hipsMainGrp_name)
                success = True
        if success:
            output.displayInfo("Success: The Foot Locker setup has been deleted.")
        else:
            output.displayWarning("Success: The Foot Locker setup could not be found.")
