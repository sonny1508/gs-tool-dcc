from maya import cmds
from maya.api import OpenMaya as om2

from zoo.libs.maya import zapi
from zoo.libs.maya import triggers
from zoo.libs.maya.meta import base
from zoo.libs.maya.cmds.rig import additivefk, controls
from zoo.libs.maya.cmds.skin import skinreplacejoints
from zoo.libs.maya.cmds.objutils import namehandling


class ZooMetaAdditiveFk(base.MetaBase):
    """Class that builds and controls the meta network node setup for the Additive Fk setup

    Found in zoo.libs.maya.cmds.rig.additivefk
    """
    _default_attrs = [{"name": "jointList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
                      {"name": "jointAddFkList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute,
                       "isArray": True},
                      {"name": "jointBlendList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute,
                       "isArray": True},
                      {"name": "controlList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute,
                       "isArray": True},
                      {"name": "controlGrpList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute,
                       "isArray": True},
                      {"name": "jntExprNode", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "grpExprNode", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "pointConstraint", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "firstConstraint", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      # Attributes
                      {"name": "rigName", "value": "", "Type": zapi.attrtypes.kMFnDataString},
                      {"name": "scale", "value": 1, "Type": zapi.attrtypes.kMFnNumericFloat},
                      {"name": "oldName", "value": "", "Type": zapi.attrtypes.kMFnDataString},
                      {"name": "controlSpacing", "value": 1, "Type": zapi.attrtypes.kMFnNumericInt},
                      {"name": "controlsVisible", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
                      {"name": "jointVisible", "value": False, "Type": zapi.attrtypes.kMFnNumericBoolean},
                      {"name": "jointBlendVisible", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
                      {"name": "jointAddFkVisible", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean}]

    def metaAttributes(self):
        """Creates the dictionary as attributes if they don't already exist"""
        defaults = super(ZooMetaAdditiveFk, self).metaAttributes()
        defaults.extend(ZooMetaAdditiveFk._default_attrs)
        return defaults

    def connectAttributes(self, joints, addFkJntList, blendList, controls, controlGrps,
                          jntExprs, grpExprs, pointC, firstC):
        """ Connects the maya nodes to the meta node
        """
        for jnt in joints:
            jnt.message.connect(self.jointList.nextAvailableDestElementPlug())
        for jnt in addFkJntList:
            jnt.message.connect(self.jointAddFkList.nextAvailableDestElementPlug())
        for jnt in blendList:
            jnt.message.connect(self.jointBlendList.nextAvailableDestElementPlug())
        for ctrl in controls:
            ctrl.message.connect(self.controlList.nextAvailableDestElementPlug())
        for grp in controlGrps:
            grp.message.connect(self.controlGrpList.nextAvailableDestElementPlug())
        jntExprs.message.connect(self.jntExprNode)
        grpExprs.message.connect(self.grpExprNode)
        pointC.message.connect(self.pointConstraint)
        firstC.message.connect(self.firstConstraint)


    def createAdditiveFk(self, jointList, rigName="additive", controlSpacing=1, lockHideJoints=True,
                         transferSkinning=True, mod=None, markingMenu=True):
        """Builds the setup and connects all nodes to this meta node

        :param jointList: list of joints
        :type jointList: list(str)
        :param rigName: The name of the rig prefix
        :type rigName: str
        :param controlSpacing: The amount of joints between controls for the distributed FK
        :type controlSpacing: int
        :param transferSkinning: Transfer the skin weights from the original joints onto the blendJoints?
        :type transferSkinning: bool
        """
        # Create the setup
        additiveInstance = additivefk.AdditiveFk(jointList, rigName=rigName, controlSpacing=controlSpacing,
                                                 lockHideJoints=lockHideJoints)
        # Return the nodes
        addFkJntList, addFkBlendJntList, controlList, ctrlGroupList, jntExprNode, grpExprNode, \
        pointConstraint, firstConstraint = additiveInstance.allNodes()
        # Transfer skinning
        if transferSkinning:  # Transfer any skinning to the original joints\
            skinreplacejoints.replaceSkinJointMatrixList(jointList, addFkBlendJntList)
        # Convert to zapi nodes
        joints = list(zapi.nodesByNames(jointList))
        addFkJntList = list(zapi.nodesByNames(addFkJntList))
        addFkBlendJntList = list(zapi.nodesByNames(addFkBlendJntList))
        controlList = list(zapi.nodesByNames(controlList))
        ctrlGroupList = list(zapi.nodesByNames(ctrlGroupList))
        jntExprNode = zapi.nodeByName(jntExprNode)
        grpExprNode = zapi.nodeByName(grpExprNode)
        pointConstraint = zapi.nodeByName(pointConstraint)
        firstConstraint = zapi.nodeByName(firstConstraint)
        # Connect the attributes
        self.connectAttributes(joints, addFkJntList, addFkBlendJntList, controlList, ctrlGroupList,
                               jntExprNode, grpExprNode, pointConstraint, firstConstraint)

        # Set meta attributes
        self.controlSpacing.set(controlSpacing, None)  # type: zapi.Plug
        self.rigName.set(rigName, None)  # type: zapi.Plug
        self.oldName.set(rigName, None)  # type: zapi.Plug
        # Marking Menu
        if markingMenu:
            self.setupMarkingMenus()

    def setupMarkingMenus(self):
        """ Set up marking menus

        :return:
        :rtype:
        """

        controls = self.getControls()
        layoutId = "markingMenu.splinerig"
        triggers.createMenuTriggers(controls, menuId=layoutId)

    def selectBlendJoints(self):
        """ Selects the joints
        """
        cmds.select(zapi.fullNames(self.getBlendJoints()))

    def toggleControls(self):
        """ Toggle visibility of controls

        :return:
        :rtype:
        """
        controls = self.getControls()
        hidden = controls[0].isHidden()
        for c in controls:
            c.setVisible(hidden)

    def setControlsVisible(self, vis):
        """ Set controls visible

        :param vis: True if show, False if hide
        :type vis: bool
        """
        controls = self.getControls()
        for c in controls:
            c.setVisible(vis)

    def setScale(self, scl):
        """ Set scale

        :param scl: set the control scale to this value
        :type scl: float or zapi.Plug
        :return:
        :rtype:
        """
        self.scale = scl  # type: zapi.Plug
        rigControls = self.getControls()

        for ctrl in rigControls:
            scaleDefaults = ("zooScaleDefault_x", "zooScaleDefault_y", "zooScaleDefault_z")
            ctrlScale = [ctrl.attribute(sAttr).value()*scl for sAttr in scaleDefaults if ctrl.attribute(sAttr)]
            if ctrlScale:
                controls.scaleBreakConnectCtrl(ctrl.fullPathName(), ctrlScale, False)

    def controlsHidden(self):
        """ Return true if controls are hidden
        """
        return self.controlList[1].value().isHidden()

    def renameRig(self, name):
        """Renames the prefix of the entire rig, all nodes.

        Simply replaces the first prefix element in the name, so isn't super smart.

        :param name: The name prefix of the rig
        :type name: str
        """
        allNodes = self.getAllNodes(includeOrigJnts=False)
        namehandling.editIndexItemList(zapi.fullNames(allNodes), 0, text=name, mode=namehandling.EDIT_INDEX_REPLACE,
                                       separator="_", renameShape=True, message=False)
        self.oldName.set(self.rigName.value(), None)  # type: zapi.Plug
        self.rigName.set(name, None)  # type: zapi.Plug

    def getControlSpacing(self):
        return self.controlSpacing.value()

    def getJoints(self):
        """Returns regular joints as zapi nodes

        :return: list of zapi joint nodes
        :rtype: list(:class:`zapi.DGNode`)
        """
        return self.attributeNodes(self.jointList)

    def getStartEndJoint(self):
        """Returns the start joint and end joint as a string

        :return startJoint: The start joint name
        :rtype startJoint: :class:`zapi.DGNode`
        :return endJoint: The end joint name
        :rtype endJoint: :class:`zapi.DGNode`
        """
        joints = self.getJoints()
        return joints[0], joints[-1]

    def getAddFkJoints(self):
        """Returns the joints as zapi nodes

        :return: list of zapi joint nodes
        :rtype: list(:class:`zapi.DGNode`)
        """
        return self.attributeNodes(self.jointAddFkList)

    def getBlendJoints(self):
        """Returns the joints as zapi nodes

        :return: list of zapi joint nodes
        :rtype: list[:class:`zapi.DGNode`]
        """
        return self.attributeNodes(self.jointBlendList)

    def getControls(self):
        """Returns the joints as zapi nodes

        :return: list of zapi joint nodes
        :rtype: list[:class:`zapi.DGNode`]
        """
        return self.attributeNodes(self.controlList)

    def getCtrlGrps(self):
        """Returns the joints as zapi nodes

        :return: list of zapi joint nodes
        :rtype: list(:class:`zapi.DGNode`)
        """
        return self.attributeNodes(self.controlGrpList)

    def controlGroup(self):
        """ Returns the control Group

        :return:
        :rtype: :class:`zapi.DagNode`
        """
        return self.controlGrpList[0].value()

    def getDgNodes(self):
        """Returns the two expressions and point constraint as zapi nodes"""
        jntExpr = self.jntExprNode.source().node()
        grpExpr = self.grpExprNode.source().node()
        pointC = self.pointConstraint.source().node()
        try:  # Old versions don't have this node
            firstC = self.firstConstraint.source().node()
            return [jntExpr, grpExpr, pointC, firstC]
        except:
            return [jntExpr, grpExpr, pointC]

    def getAllNodes(self, includeOrigJnts=False):
        """Returns all nodes in the setup

        :param includeOrigJnts: Include the original joints? Usually its best to leave these in the scene
        :type includeOrigJnts: bool
        :return: list of all zapi nodes in the setup
        :rtype: list(:class:`zapi.DGNode`)
        """
        allNodes = self.getAddFkJoints() + self.getBlendJoints() + self.getControls() + self.getCtrlGrps() + \
                   self.getDgNodes()
        if includeOrigJnts:
            allNodes.append(self.getJoints())
        return allNodes

    def deleteSetup(self, transferSkinning=True, deleteOrigJnts=False, bake=False, message=True):
        """Deletes the Additive FK setup leaving the original joints only
        Also transfers any skinning on the blend joints back onto the original joints
        """
        transList = list()  # used while baking only
        rotList = list()
        scaleList = list()

        origJoints = self.getJoints()
        blendJoints = self.getBlendJoints()

        if bake:  # record values of the blend joints
            for blendJ in blendJoints:
                transList.append(cmds.getAttr("{}.translate".format(blendJ.fullPathName()))[0])
                rotList.append(cmds.getAttr("{}.rotate".format(blendJ.fullPathName()))[0])
                scaleList.append(cmds.getAttr("{}.scale".format(blendJ.fullPathName()))[0])

        if transferSkinning:  # Transfer any skinning to the original joints
            skinreplacejoints.replaceSkinJointMatrixList(zapi.fullNames(blendJoints),
                                                         zapi.fullNames(origJoints))
        # Delete
        firstJnt = origJoints[0]
        cmds.setAttr("{}.visibility".format(firstJnt.fullPathName()), keyable=True, lock=False)
        cmds.setAttr("{}.visibility".format(firstJnt.fullPathName()), True)
        cmds.delete(zapi.fullNames(self.getAllNodes(includeOrigJnts=deleteOrigJnts)))

        self.delete()  # Delete this meta node

        if bake:  # apply values to the remaining joints
            for i, joint in enumerate(origJoints):
                transList.append(cmds.setAttr("{}.translate".format(joint.fullPathName()),
                                              transList[i][0], transList[i][1], transList[i][2]))
                rotList.append(cmds.setAttr("{}.rotate".format(joint.fullPathName()),
                                            rotList[i][0], rotList[i][1], rotList[i][2]))
                scaleList.append(cmds.setAttr("{}.scale".format(joint.fullPathName()),
                                              scaleList[i][0], scaleList[i][1], scaleList[i][2]))

            if message:
                om2.MGlobal.displayInfo("Success: Additive FK Rig Baked")
        else:
            if message:
                om2.MGlobal.displayInfo("Success: Additive FK Rig Deleted")

