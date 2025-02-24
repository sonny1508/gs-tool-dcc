"""
Example code:

    from zoo.libs.maya.cmds.rig import splinebuilder
    rigName = "rigX"
    jointList = ["joint1", "joint2","joint3", "joint4", "joint5", "joint6", "joint7", "joint8", "joint9"]
    splinebuilder.buildSpine(rigName, jointList, controlCount=5, scale=1.0)

"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import joints, namehandling, attributes
from zoo.libs.maya.cmds.rig import splines, deformers, axis
from zoo.libs.maya.utils import general

BT_SPLINE = 0
BT_STARTENDJOINT = 1
BT_IKHANDLE = 2

PROXY_ATTR_LIST = ["squash", "stretch", "hierarchySwitch", "twist", "roll", "offset"]


class SplineBuilder(object):
    """Main class that builds the spline rig with multiple control types and various switching functionality
    """

    def __init__(self, rigName, jointList, controlCount=5, scale=1.0, fk=True, revFk=True, flt=True, spine=True,
                 stretchy=True, cogUpAxis="Auto", message=True, buildType=BT_STARTENDJOINT, ikHandleBuild=None,
                 addToUndo=True, splineCurve=None, useProvidedCurve=False):
        """The variables required for the spline rig builder

        :param rigName: the name of the rig part, this is the suffix so could be "spine", "ponyTail2" or "tail"
        :type rigName: str
        :param jointList: names of the joints
        :type jointList: list
        :param controlCount: the amount of controls you wish to build. Must be 5 for the spine controls
        :type controlCount: int
        :param scale: the overall scale of the rig as a multiplier, will scale controls etc
        :type scale: float
        :param fk: do you want to build the fk controls?
        :type fk: bool
        :param revFk:  do you want to build the revFk controls?
        :type revFk: bool
        :param flt: do you want to build the flt controls?
        :type flt: bool
        :param spine: do you want to build the spine controls?
        :type spine: bool
        :param cogUpAxis: The up axis of the cog control, "+y" or "-x" etc, "Auto" will figure the axis automatically.
        :type cogUpAxis: str
        :param message: report the message to the user?
        :type message: bool
        :param buildType: Build from a curve or joints or ikHandle, see globals BT_STARTENDJOINT etc
        :type buildType: str
        :param ikHandleBuild: The ikHandle to build the rig ontop of if buildType is BT_IKHANDLE
        :type ikHandleBuild: str
        """
        self.rigName = rigName
        self.jointList = jointList
        self.controlCount = controlCount
        self.scale = scale
        self.fk = fk
        self.revFk = revFk
        self.flt = flt
        self.spine = spine
        self.stretchy = stretchy
        self.cogUpAxis = cogUpAxis
        self.ikHandleBuild = ikHandleBuild
        self.addToUndo = addToUndo
        self.splineCurve = splineCurve
        self.useProvidedCurve = useProvidedCurve
        self.buildAll(buildType=buildType, message=message)

    def _jointScales(self):
        """Gets the scale of each joint and creates the list self.jointScales"""
        self.jointScales = list()
        for jnt in self.jointList:
            self.jointScales.append(cmds.getAttr("{}.scale".format(jnt))[0])

    def _autoOrientAxis(self):
        """Will try to guess a good axis orientation for the spline rig based on the world position of list of clusters.
        """
        objList = list()
        for clstrTuple in self.clusterList:
            objList.append(clstrTuple[1])  # transform of the cluster
        self.cogUpAxis = axis.autoAxisBBoxObjList(objList)

    def _buildControls(self):
        """Builds the control curves
        """
        self.cogControl, self.cogGroup = splines.buildSplineCogControl(self.rigName, self.clusterList,
                                                                       scale=self.scale, upAxis=self.cogUpAxis,
                                                                       addToUndo=self.addToUndo)
        self.fkControlList = list()
        self.fkGroupList = list()
        if self.fk:  # fk controls
            self.fkControlList, \
            self.fkGroupList = splines.buildControlsSplineFk(self.rigName, self.clusterList, scale=self.scale,
                                                             orientGlobalVectorObj=self.cogControl,
                                                             addToUndo=self.addToUndo)
        self.revfkControlList = list()
        self.revfkGroupList = list()
        if self.revFk:  # revFk controls
            self.revfkControlList, \
            self.revfkGroupList = splines.buildControlsSplineRevfk(self.rigName, self.clusterList, scale=self.scale,
                                                                   orientGlobalVectorObj=self.cogControl,
                                                                   addToUndo=self.addToUndo)
        self.floatControlList = list()
        self.floatGroupList = list()
        if self.flt:  # float controls
            self.floatControlList, \
            self.floatGroupList = splines.buildControlsSplineFloat(self.rigName, self.clusterList, scale=self.scale,
                                                                   orientGlobalVectorObj=self.cogControl,
                                                                   addToUndo=self.addToUndo)
        self.spineControlList = list()
        self.spineGroupList = list()
        self.spineOtherConstraintList = list()
        self.spineRotControl = ""
        if self.spine:  # spine controls
            self.spineControlList, \
            self.spineGroupList, \
            self.spineOtherConstraintList, \
            self.spineRotControl = splines.buildControlsSplineSpine(self.rigName, self.clusterList, scale=self.scale,
                                                                    orientGlobalVectorObj=self.cogControl,
                                                                    addToUndo=self.addToUndo)
        return
        # up vector controls
        self.upVBaseCtrl, \
        self.upVBaseGroup, \
        self.upVEndCtrl, \
        self.upVEndGroup = splines.buildSplineUpVectors(self.rigName, self.clusterList, suffixName="upV",
                                                           scale=self.scale, addToUndo=self.addToUndo)

    def _ikHandleData(self, ikHandle):
        """ Retrieve the ik handle data from the ik handle

        :param ikHandle:
        :type ikHandle: :class:`zoo.libs.maya.zapi.base.DagNode`
        :return:
        :rtype:
        """
        effector = ikHandle.attribute("endEffector").value()
        startJoint, endJoint = joints.jointsFromIkHandle(ikHandle)
        curve = ikHandle.attribute("inCurve").source().node()

        self.jointList = joints.getJointChain(startJoint.fullPathName(), endJoint.fullPathName())
        self.splineIkList = [ikHandle, effector, curve]
        self.splineSolver = ikHandle.attribute("ikSolver").value()
        self.controlCount = curve.attribute("spans").value() + 3
        if self.controlCount != 5:
            self.spine = False

    def _buildStretchy(self):
        """Builds the squash and stretch setup
        """
        self.curveInfo, \
        self.splineMultiplyNode, \
        self.splineMultiplyNode2, \
        self.splineStretchBlendTwoAttr, \
        self.splineSquashBlendTwoAttr, \
        self.multiplyStretchNodes, \
        self.maintainScaleNodes = splines.createStretchy(self.splineIkList[2].fullPathName(), self.jointList,
                                                         forceMaintainNodes=True)
        # create and connect attributes
        splines.stretchyConnectCntrlAttributes(self.splineStretchBlendTwoAttr, self.splineSquashBlendTwoAttr,
                                               self.cogControl)
        # Hookup scale to world size so the rig can be scaled
        self.scaleGroup, \
        self.scaleMultiplyNode, \
        self.scaleGroupConstraint = splines.stretchyWorldScaleMod(self.cogControl,
                                                                  self.splineMultiplyNode2,
                                                                  self.rigName)

        self.buildStretchyNodes = [self.splineMultiplyNode, self.splineMultiplyNode2, self.splineStretchBlendTwoAttr,
                                   self.splineSquashBlendTwoAttr] + self.multiplyStretchNodes

    def _getStartEndVector(self):
        """Returns the start and end vector of the start joint and the end joint"""
        startVector = cmds.xform(self.jointList[0], worldSpace=True, matrix=True, query=True)[8:11]
        endVector = cmds.xform(self.jointList[-1], worldSpace=True, matrix=True, query=True)[8:11]
        return startVector, endVector

    def _buildAdvancedTwist(self, startVector=(0, 0, -1), endVector=(0, 0, -1)):
        """Builds the spline ik advanced twist

        :param startVector: The up twist vector of the start control
        :type startVector: tuple
        :param endVector: The up twist vector of the end control
        :type endVector: tuple
        """
        splines.advancedSplineIkTwist(self.splineIkList[0].fullPathName(),
                                      (self.clusterList[0])[1],
                                      (self.clusterList[-1])[1],
                                      startVector=startVector,
                                      endVector=endVector)

    def firstLastControls(self):
        """Returns the first and the last controls of the first available control set"""
        if self.fkControlList:
            return self.fkControlList[0], self.fkControlList[-1]
        elif self.floatControlList:
            return self.floatControlList[0], self.floatControlList[-1]
        elif self.revfkControlList:
            return self.revfkControlList[0], self.revfkControlList[-1]
        elif self.spineControlList:
            return self.spineControlList[0], self.spineControlList[-1]
        else:
            return "", ""

    def _constrainToControls(self):
        pureClusterList = list()  # filter the clusters because they are in little lists? why?
        for i, clusterPack in enumerate(self.clusterList):
            pureClusterList.append((self.clusterList[i])[1])
        spineControl = ""
        if self.spineRotControl:  # spine exists
            spineControl = self.spineRotControl[0]
        self.controlEnumList, \
        self.driverAttr, \
        self.hchySwitchCondPnts, \
        self.hchySwitchCondVis, \
        self.objConstraintList = splines.constrainToControls(self.fkControlList, self.fkGroupList,
                                                             self.revfkControlList, self.revfkGroupList,
                                                             self.floatControlList, self.floatGroupList,
                                                             self.spineControlList, self.spineGroupList,
                                                             pureClusterList, self.cogControl, self.rigName,
                                                             spineControl)
        return
        # PoleVector Constrain
        firstControl, lastControl = self.firstLastControls()
        if firstControl:  # Match pole vectors to the control and constrain to the clusters
            cmds.matchTransform(self.upVBaseGroup.fullPathName(), firstControl.fullPathName(), rotation=True,
                                position=True)
            cmds.matchTransform(self.upVEndGroup.fullPathName(), lastControl.fullPathName(), rotation=True,
                                position=True)
            self.upVpBaseConstraint = cmds.parentConstraint(self.clusterList[0][1], self.upVBaseGroup.fullPathName(),
                                                    maintainOffset=True)[0]
            self.upVpEndConstraint = cmds.parentConstraint(self.clusterList[-1][1], self.upVEndGroup.fullPathName(),
                                                   maintainOffset=True)[0]

    def _scaleAttrsOnCog(self):
        """Adds the JntScaleY01 and JntScaleZ01 attributes on the COG control"""
        cogCntrl = self.cogControl.fullPathName()
        for i, multiplyNode in enumerate(self.maintainScaleNodes):
            numberSt = str(i + 1).zfill(2)  # 2 padding
            # Create YZ attribute on COG
            cmds.addAttr(cogCntrl, longName="jntScaleY{}".format(numberSt), attributeType='float', keyable=True,
                         defaultValue=self.jointScales[i][1])
            cmds.addAttr(cogCntrl, longName="jntScaleZ{}".format(numberSt), attributeType='float', keyable=True,
                         defaultValue=self.jointScales[i][2])
            cmds.connectAttr('{}.{}'.format(cogCntrl, "jntScaleY{}".format(numberSt)),
                             '{}.{}'.format(multiplyNode, "input2Y"), force=True)
            cmds.connectAttr('{}.{}'.format(cogCntrl, "jntScaleZ{}".format(numberSt)),
                             '{}.{}'.format(multiplyNode, "input2Z"), force=True)

    def _addCogAttrs(self):
        """Adds twist, offset and roll attributes to the cog control"""
        splineIkHandle = self.splineIkList[0].fullPathName()
        cogCntrl = self.cogControl.fullPathName()
        cmds.select(cogCntrl, replace=True)
        cmds.addAttr(cogCntrl, longName='twist', attributeType='float', keyable=True, defaultValue=0)
        cmds.addAttr(cogCntrl, longName='roll', attributeType='float', keyable=True, defaultValue=0)
        cmds.addAttr(cogCntrl, longName='offset', attributeType='float', keyable=True, defaultValue=0)
        cmds.connectAttr('{}.twist'.format(cogCntrl), '{}.twist'.format(splineIkHandle), force=True)
        cmds.connectAttr('{}.roll'.format(cogCntrl), '{}.roll'.format(splineIkHandle), force=True)
        cmds.connectAttr('{}.offset'.format(cogCntrl), '{}.offset'.format(splineIkHandle), force=True)
        if self.stretchy:
            self._scaleAttrsOnCog()

    def _allControls(self, includeCog=False):
        """Returns all the controls in one zapi list

        :param includeCog: Will also include the cog control
        :type includeCog: bool
        :return controlList: A list of all the controls
        :rtype controlList: list(zapi.DagNode)
        """
        controlList = list()
        if self.spineControlList:
            controlList = self.spineControlList + [self.spineRotControl[0]]
        if self.fkControlList:
            controlList += self.fkControlList
        if self.floatControlList:
            controlList += self.floatControlList
        if self.revfkControlList:
            controlList += self.revfkControlList
        if includeCog:
            controlList.append(self.cogControl)
        return controlList

    def _visNonKeyableControls(self):
        """Sets all control visibility attributes to be non-keyable
        """
        for control in self._allControls(includeCog=True):
            cmds.setAttr("{}.visibility".format(control), keyable=False)
            cmds.setAttr("{}.visibility".format(control), channelBox=True)

    def _addProxyAttrs(self):
        """Adds the proxy attributes to all controls, from the master which is the cogControl"""
        cogCntrl = self.cogControl.fullPathName()
        attrList = list(PROXY_ATTR_LIST)
        #  Hierarchy Attr may not exist if only one set of controls
        if not cmds.attributeQuery("hierarchySwitch", node=self.cogControl.fullPathName(), exists=True):
            attrList.pop(attrList.index("hierarchySwitch"))
        # Build proxies
        for control in self._allControls():
            for attr in attrList:
                attributes.addProxyAttribute(control.fullPathName(), cogCntrl, attr)

    def _cleanupRig(self):
        """Cleans up the entire rig"""
        # Visibility controls: Hide or non-keyable.
        if self.spineControlList:  # Hide visibility on the middle spine control
            cmds.setAttr("{}.visibility".format(self.spineRotControl[0].fullPathName()), keyable=False)
        for controlList in [self.fkControlList, self.revfkControlList, self.floatControlList, self.spineControlList]:
            if controlList:
                for ctrl in controlList:
                    cmds.setAttr("{}.visibility".format(ctrl.fullPathName()), keyable=False, channelBox=True)
        # Cleanup and parent into groups
        self.rigGrp = splines.cleanupSplineRig(self.fkGroupList, self.revfkGroupList, self.floatGroupList,
                                               self.spineGroupList, self.clusterList, self.rigName, self.splineIkList,
                                               self.splineSolver, self.jointList, self.spineRotControl, self.cogControl,
                                               self.cogGroup, self.scaleGroup)

    def returnAllNodes(self):
        """Returns all nodes collected in this class

        :return allNodes: A list of nodes and lists of nodes
        :rtype allNodes: list
        """
        return self.splineIkList, self.splineSolver, self.clusterList, self.fkControlList, self.fkGroupList, \
               self.revfkControlList, self.revfkGroupList, self.floatControlList, self.floatGroupList, \
               self.spineControlList, self.spineRotControl, self.spineOtherConstraintList, self.cogControl, \
               self.cogGroup, self.scaleGroup, self.scaleMultiplyNode, self.scaleGroupConstraint, \
               self.rigGrp, self.maintainScaleNodes

    def buildAll(self, buildType, autoOrientRoot=False, message=True):
        """Main method that builds the spline rig

        :param buildType: Specify Type to build from see globals BT_STARTENDJOINT, BT_SPLINE, BT_IKHANDLE
        :type buildType: int
        :param autoOrientRoot: If True will best guess the Orient Root up axis from the cluster positions
        :type autoOrientRoot: bool
        :param message: Report messages to the user?
        :type message: bool
        """
        self._jointScales()  # builds the list of scale values self.jointScales
        startVector, endVector = self._getStartEndVector()  # gets the initial start joint and end joint Z vectors
        self.ikVector = tuple()
        # Spline ik
        if buildType == BT_STARTENDJOINT or buildType == BT_SPLINE:
            self.splineIkList, self.splineSolver = splines.createSplineIk(self.rigName, self.jointList,
                                                                          curveSpans=self.controlCount - 3,
                                                                          curve=self.splineCurve if self.useProvidedCurve else None)
        elif buildType == BT_IKHANDLE:
            if not self.ikHandleBuild:
                om2.MGlobal.displayWarning("IK handle must be specified if build type is IK Handle")
                return
            self._ikHandleData(self.ikHandleBuild)
        self.clusterList = deformers.createClustersOnCurve(self.rigName,
                                                           self.splineIkList[2].fullPathName())  # clusters
        if self.cogUpAxis == "Auto":  # sets the self.cogUpAxis to an axis such as "+y"
            self._autoOrientAxis()
        self._buildControls()  # Controls
        if self.stretchy:  # Stretchy
            self._buildStretchy()
        self._buildAdvancedTwist(startVector=startVector, endVector=endVector)  # Advanced twist
        self._constrainToControls()  # The constraint setup to the controls
        self._addCogAttrs()  # Adds twist, offset and roll attrs and scale
        self._visNonKeyableControls()  # sets all control visibility to be non keyable
        self._addProxyAttrs()  # Adds the proxy attributes to all controls, master is cog
        self._cleanupRig()  # Cleanup the outliner
        if message:
            om2.MGlobal.displayInfo("Success: Spline rig built")


def validStartEndJoint(startJoint, endJoint, warning=True):
    """UI help function to check if the user has added the start and end joint correctly.

    Checks if endJoint is a descendant of (parented somewhere under the) startJoint

    :return valid: True if the end Joint is a descendant of startJoint
    :rtype valid: bool
    """
    endJoint = namehandling.getLongNameFromShort(endJoint)
    children = cmds.listRelatives(startJoint, allDescendents=True, fullPath=True)
    if not children:
        if warning:
            om2.MGlobal.displayWarning("The Start Joint has no children, "
                                       "the End Joint must be a descendant of the Start Joint.")
        return False
    if not endJoint in children:
        if warning:
            om2.MGlobal.displayWarning("The End Joint is not a descendant of the Start Joint,"
                                       "the End Joint must under the Start Joint.")
        return False
    return True


@general.undoDecorator
def buildSpineJoints(rigName, jointList=None, startJoint="", endJoint="", controlCount=5, scale=1.0, buildFk=True,
                     buildRevFk=True, buildSpine=True, buildFloat=True, cogUpAxis="Auto", message=True, buildType=0,
                     ikHandleBuild=None, addToUndo=True, splineCurve=None):
    """Builds the spine rig

    :param rigName: The name of the rig
    :type rigName: str
    :param jointList: list of joints to add to the spline
    :type jointList: list(str)
    :param controlCount: The amount of controls to build, will be 5 if a spine
    :type controlCount: int
    :param scale: The scale of the rig, affects the controls
    :type scale: float
    :param buildFk: Builds the Fk controls part of the rig
    :type buildFk: bool
    :param buildRevFk: Builds the Reverse Fk controls part of the rig
    :type buildRevFk: bool
    :param buildSpine: Builds the Spine controls part of the rig
    :type buildSpine: bool
    :param buildFloat: Builds the Floating controls part of the rig
    :type buildFloat: bool
    :param cogUpAxis: The up axis of the cog control, "+y" or "-x" etc, "Auto" will figure the axis automatically.
    :type cogUpAxis: str
    :return splineInstance: The instance of the spline class
    :rtype splineInstance: object
    :return allNodes: See splineBuilder.returnAllNodes() for all nodes
    :rtype splineInstance:
    """
    # TODO: Error checking Maybe UI should sort this out? --------------------------------------------
    if not buildFk and not buildRevFk and not buildSpine and not buildFloat:
        om2.MGlobal.displayWarning("A rig type must be selected to build.  Please check a Control Rig.")
        return None, None
    if not jointList:
        if not cmds.objExists(startJoint):
            om2.MGlobal.displayWarning("The start joint `{}` does not exist".format(startJoint))
            return
        if endJoint:
            if not cmds.objExists(endJoint):
                om2.MGlobal.displayWarning("The end joint `{}` does not exist".format(endJoint))
                return
        if not startJoint:
            om2.MGlobal.displayWarning("Please specify a starting joint.")
            return
        # Check the start joint is a joint
        if cmds.nodeType(startJoint) != "joint":
            om2.MGlobal.displayWarning("`{}` is not a joint.  Please specify a joint name.".format(startJoint))
            return
        if endJoint and cmds.nodeType(endJoint) != "joint":
            om2.MGlobal.displayWarning("`{}` is not a joint.  Please specify a joint name.".format(endJoint))
            return
        jointList = joints.getJointChain(startJoint, endJoint)  # Extrapolates the joint chain
        if not jointList:  # Can happen if the end joint is not a child of the start joint.
            om2.MGlobal.displayWarning("The specified joints do not form a legitimate joint chain, "
                                       "try reversing the start/end entries, or check your scene.")
            return
    # Checks passed so build the rig  ------------------------------------------------------------------
    splineInstance = SplineBuilder(rigName, jointList, controlCount=controlCount, scale=scale, fk=buildFk,
                                   revFk=buildRevFk, spine=buildSpine, flt=buildFloat, cogUpAxis=cogUpAxis,
                                   message=message, buildType=buildType, ikHandleBuild=ikHandleBuild,
                                   addToUndo=addToUndo, splineCurve=splineCurve)
    return splineInstance, splineInstance.returnAllNodes()


if __name__ == "__main__":
    rigName = "rigX"
    jointList = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7", "joint8", "joint9"]
    buildSpineJoints(rigName, jointList, controlCount=5, scale=1.0)
