import maya.cmds as cmds

from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.rig import controls
from zoo.libs.maya.cmds.objutils import namehandling

AXIS_LIST = ["X", "Y", "Z"]


class AdditiveFk(object):
    """Builds two extra joint chains with controls for additive FK.  this is a setup that layers an fk chain ontop \
    of another, useful for spline ik etc.

    Note: Best to build additive fk with the metaNode, see zoo.libs.maya.cmds.meta.metaadditivefk

    Example:

        from zoo.libs.maya.cmds.meta import metaadditivefk
        jointList = ["joint1", "joint2", "joint3", "joint4"]
        additiveFkInstance = metaadditivefk.ZooMetaAdditiveFk()
        additiveFkInstance.createAdditiveFk(jointList, rigName="additive", controlSpacing=1, lockHideJoints=True)
    """

    def __init__(self, jointList, rigName="additive", controlSpacing=1, lockHideJoints=True):
        # TODO better distributed translate?
        self.rigName = rigName
        self.jointList = jointList
        self.ctrlSpacing = controlSpacing
        self._buildJointChains()  # Builds both new joint chains, self.addFkJntList and self.addFkBlendJntList
        self._renameJointLists()  # Joints need to be renamed as they have been duplicated
        self._createControls()  # Creates but does not connect
        self._addJointsTogether()  # Does the additive rotation and connects scale
        if self.ctrlSpacing == 1:  # Connect controls - Controls on every joint
            self._connectControlsSingle()
        else:  # Connect controls - Controls are spaced
            self._connectControlsSpaced()
        self._parentControls()
        self._cleanup(lockHideJoints=lockHideJoints)

    def _buildJointChains(self):
        """Creates two new joint chains by duplicating the incoming joint list.

        Could be more robust by building and matching joints.

        self.addFkJntList: The additive FK joint chain, rotation will be zeroed
        self.addFkBlendJntList: The blender joint chain that follows the controls
        """
        self.addFkJntList = cmds.duplicate(self.jointList, renameChildren=True, name="zoo_temp_addFKJ")
        if cmds.objectType(self.addFkJntList[-1]) == "ikEffector":  # can be a dead ikEffector
            cmds.delete(self.addFkJntList[-1])
            del self.addFkJntList[-1]
        self.addFkBlendJntList = cmds.duplicate(self.addFkJntList, renameChildren=True, name="zoo_temp_blendJ")
        for jnt in self.addFkJntList:  # zero the additive ik chain's rotation
            cmds.setAttr("{}.rotate".format(jnt), 0.0, 0.0, 0.0)

    def _renameJointLists(self):
        """Renames the new joint lists, easier to do here because the joints have been duplicated"""
        for i, jnt in enumerate(self.addFkBlendJntList):
            pad = str(i + 1).zfill(2)  # padding
            self.addFkBlendJntList[i] = namehandling.safeRename(jnt, "_".join([self.rigName,
                                                                               "blend",
                                                                               pad,
                                                                               "jnt"]))
            self.addFkJntList[i] = namehandling.safeRename(self.addFkJntList[i], "_".join([self.rigName,
                                                                                           "addFk",
                                                                                           pad,
                                                                                           "jnt"]))

    def _expressionPosSingle(self, exprLines):
        """This method affects translation of the blend joints, driven by controls
        Assumes controls are on every joint"""
        for i, jnt in enumerate(self.jointList):  # Create expression text
            for x, axis in enumerate(AXIS_LIST):
                if i:  # Translation: blend = jntX + controlOffsetX
                    exprLines.append("{0}.translate{2} = {1}.translate{2} "
                                     "+ {3}.translate{2};".format(self.addFkBlendJntList[i],
                                                                  jnt,
                                                                  axis,
                                                                  self.matchCtrlList[i]))
        return exprLines

    def expressionPosSpaced(self, exprLines):
        """This method affects translation of the blend joints, driven by controls
        Assumes controls are spaced"""
        ctrlCount = -1
        for i, jnt in enumerate(self.jointList):  # Create expression text
            if i % self.ctrlSpacing == 0:  # Control and joint match
                ctrlCount += 1
                for x, axis in enumerate(AXIS_LIST):
                    if i:  # Translation: blend = jntX + controlOffsetX
                        exprLines.append("{0}.translate{2} = {1}.translate{2} "
                                         "+ {3}.translate{2};".format(self.addFkBlendJntList[i],
                                                                      jnt,
                                                                      axis,
                                                                      self.controlList[ctrlCount]))
            else:  # Control and joints don't match, so direct connect
                cmds.connectAttr("{}.translate".format(jnt), "{}.translate".format(self.addFkBlendJntList[i]))
        return exprLines

    def _addJointsTogether(self):
        """Drives the blend joints.

        Rotation:
            Drives the rotation of the blend joints additively from the original and addFk joints
            Creates an expression node self.jntExprNode

        Scale:
            Direct connects scale of the blend joints to the original joints. No blending.
            Direct connects the scale

        Translation:
            Drives the blend joint's translation where appropriate from controls.
        """
        exprLines = list()
        for i, jnt in enumerate(self.jointList):  # Create expression text
            for x, axis in enumerate(AXIS_LIST):
                # Rotation: blend = jntX + addFkJntX
                exprLines.append("{0}.rotate{3} = {1}.rotate{3} + {2}.rotate{3};".format(self.addFkBlendJntList[i],
                                                                                         jnt,
                                                                                         self.addFkJntList[i],
                                                                                         axis))
            # Direct connect scale
            cmds.connectAttr("{}.scale".format(jnt), "{}.scale".format(self.addFkBlendJntList[i]))
        # Add translation lines of code to expression text
        if self.ctrlSpacing == 1:
            exprLines = self._expressionPosSingle(exprLines)
        else:
            exprLines = self.expressionPosSpaced(exprLines)
        # Point constraint, first control/blend joint
        self.pointConstraint = cmds.pointConstraint([self.controlList[0], self.addFkBlendJntList[0]],
                                                    maintainOffset=False)[0]
        # Create expression
        self.jntExprNode = cmds.expression(string='\n'.join(exprLines), name="{}_addFKJntExp".format(self.rigName))

    def _createControls(self):
        """Creates and names the controls but doesn't connect them

        Also creates self.matchControlList and self.matchGrpList these lists may have duplicates in the case of the \
        spacing of controls ie in the case of self.ctrlSpacing of 2 then [control1, control1, control2, control2]
        """
        overrideName = "_".join([self.rigName, "addFk"])
        self.controlList, self.ctrlGroupList = controls.createControlsMatchList(self.jointList[::self.ctrlSpacing],
                                                                                overrideName=overrideName,
                                                                                rotateOffset=(0, 0, 90))
        if self.ctrlSpacing == 1:  # Controls on every joint, so match lists are identical
            self.matchCtrlList = self.controlList
            self.matchGrpList = self.ctrlGroupList
        else:
            self.matchCtrlList = list()
            self.matchGrpList = list()
            ctrlCount = -1
            for i, jnt in enumerate(self.jointList):
                if i % self.ctrlSpacing == 0:  # match control
                    ctrlCount += 1
                self.matchCtrlList.append(self.controlList[ctrlCount])
                self.matchGrpList.append(self.ctrlGroupList[ctrlCount])

        for i, control in enumerate(self.matchCtrlList):
            cmds.connectAttr("{}.rotateOrder".format(control), "{}.rotateOrder".format(self.addFkBlendJntList[i]))

    def _connectControlsSingle(self):
        """Connect the controls to drive the addFk joints, assuming there is no spacing on controls"""
        for i, addFkJnt in enumerate(self.addFkJntList):
            cmds.connectAttr("{}.rotate".format(self.controlList[i]), "{}.rotate".format(addFkJnt), force=True)
            if i:
                cmds.connectAttr("{}.translate".format(self.jointList[i]),
                                 "{}.translate".format(self.ctrlGroupList[i]), force=True)
        # Note: This expression is not used, easier to build it empty for meta nodes
        self.grpExprNode = cmds.expression(string='', name="{}_addFKGrpExp".format(self.rigName))

    def _connectControlsSpaced(self):
        """Connect the controls to drive the addFk joints, assuming there is spacing on the controls"""
        exprLines = list()
        ctrlCount = -1
        for i, addFkJnt in enumerate(self.addFkJntList):
            if i % self.ctrlSpacing == 0:  # match control
                ctrlCount += 1
                if i:  # control's grps move when joint chain is moved
                    cmds.connectAttr("{}.translate".format(self.jointList[i]),
                                     "{}.translate".format(self.ctrlGroupList[ctrlCount]), force=True)
            for axis in AXIS_LIST:
                exprLines.append("{0}.rotate{2} = {1}.rotate{2} / {3};".format(addFkJnt,
                                                                               self.matchCtrlList[i],
                                                                               axis,
                                                                               str(self.ctrlSpacing)))
        self.grpExprNode = cmds.expression(string='\n'.join(exprLines), name="{}_addFKGrpExp".format(self.rigName))

    def _parentControlsSingle(self):
        """Parent the controls into the hierarchy, no spacing on controls"""
        for i, ctrlGrp in enumerate(self.ctrlGroupList):
            if not i:
                continue
            cmds.parent(ctrlGrp, self.addFkBlendJntList[i - 1])

    def _parentControlsSpaced(self):
        """Parent the controls into the hierarchy, spacing on controls"""
        for i, ctrlGrp in enumerate(self.ctrlGroupList):
            if not i:
                continue
            jntCount = i * self.ctrlSpacing - 1
            cmds.parent(ctrlGrp, self.addFkBlendJntList[jntCount])

    def _parentControls(self):
        """Parent the controls into the hierarchy, uses zapi to track long name changes"""
        ctrlGroups = list(zapi.nodesByNames(self.ctrlGroupList))
        controls = list(zapi.nodesByNames(self.controlList))
        if self.ctrlSpacing == 1:
            self._parentControlsSingle()
        else:
            self._parentControlsSpaced()
        # First control constraint
        self.firstConstraint = cmds.parentConstraint([self.jointList[0], self.ctrlGroupList[0]], maintainOffset=True)[0]
        self.ctrlGroupList = zapi.fullNames(ctrlGroups)
        self.controlList = zapi.fullNames(controls)

    def _cleanup(self, lockHideJoints=True):
        if lockHideJoints:
            try:
                cmds.setAttr("{}.visibility".format(self.addFkJntList[0]), 0, keyable=False, lock=True)
                cmds.setAttr("{}.visibility".format(self.jointList[0]), 0, keyable=False, lock=True)
            except RuntimeError as e:
                if 'locked' in str(e):
                    pass

    def allNodes(self):
        """Returns all nodes in the setup as strings

        :return: All nodes in the rig
        :rtype: list(str)
        """
        return self.addFkJntList, self.addFkBlendJntList, self.controlList, self.ctrlGroupList, self.jntExprNode, \
               self.grpExprNode, self.pointConstraint, self.firstConstraint
