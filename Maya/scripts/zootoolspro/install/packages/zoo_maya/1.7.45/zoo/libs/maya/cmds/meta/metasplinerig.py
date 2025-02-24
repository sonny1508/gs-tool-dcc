import uuid

import os

import math

from maya import cmds

import maya.api.OpenMaya as om2
from zoo.libs.maya.mayacommand.library.additivefk import additivefkbuild
from zoovendor import six

from zoo.libs.maya.mayacommand import mayaexecutor as executor
from zoo.libs.maya import zapi
from zoo.libs.maya.api import deformers
from zoo.libs.maya.cmds.objutils import namehandling, joints, connections
from zoo.libs.maya.cmds.rig import splinebuilder, controls, splines
from zoo.libs.maya import triggers
from zoo.libs.maya.meta import base
from zoo.libs.maya.cmds.rig import splinerigswitcher
from zoo.libs.utils import filesystem
from zoo.libs.maya.cmds.meta import metaadditivefk

UP_AXIS_LIST = ["+Y", "-Y", "+X", "-X", "+Z", "-Z"]
HIERARCHY_SWITCH = ['spine', 'fk', 'float', 'revFk']


class MetaSplineRig(base.MetaBase):
    """Class that controls the meta network node setup for the duplicate on curve functionality

    Found in zoo.libs.maya.cmds.rig.splines
    """
    id = "MetaSplineRig"
    _default_attrs = [
        {"name": "startJoint", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "endJoint", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},

        {"name": "splineIkList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "splineSolver", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "clusterList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "fkControlList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "fkGroupList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "revfkControlList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "revfkGroupList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "floatControlList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "floatGroupList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "spineControlList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "spineRotControl", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "spineOtherConstraintList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "cogControl", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "cogGroup", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "scaleGroup", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "scaleMultiplyNode", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "scaleGroupConstraint", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "rigGrp", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "multStretchNodes", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "maintainScaleNodes", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "curveInfo", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "ikHandleBuild", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "jointsSpline", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "additiveFkMeta", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "meshes", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},

        # Attributes
        {"name": "rigName", "value": "", "Type": zapi.attrtypes.kMFnDataString},
        {"name": "oldName", "value": "", "Type": zapi.attrtypes.kMFnDataString},
        {"name": "buildFk", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "needsRebuild", "value": False, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "buildRevFk", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "buildFloat", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "buildSpine", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "buildAdditiveFk", "value": False, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "orientRoot", "value": 0, "Type": zapi.attrtypes.kMFnNumericInt},
        {"name": "controlSpacing", "value": 1, "Type": zapi.attrtypes.kMFnNumericInt},
        {"name": "rigType", "value": 0, "Type": zapi.attrtypes.kMFnNumericInt},
        {"name": "scale", "value": 1.0, "Type": zapi.attrtypes.kMFnNumericFloat},
        {"name": "controlCount", "value": 5, "Type": zapi.attrtypes.kMFnNumericInt},
        {"name": "hierarchySwitch", "value": "", "Type": zapi.attrtypes.kMFnDataString},
        {"name": "boundJointMatrices", "value": None, "Type": zapi.attrtypes.kMFnDataMatrix, "isArray": True},
        {"name": "published", "value": False, "Type": zapi.attrtypes.kMFnNumericBoolean},

    ]

    def __init__(self, node=None, name=None, initDefaults=True, lock=False,
                 jointList=None, startJoint="", endJoint="", controlCount=5, scale=1.0, buildFk=True,
                 buildRevFk=True, buildSpine=True, buildFloat=True, cogUpAxis="+y", orientRoot=0,
                 hierarchySwitch='spine',
                 jointsSpline=None, ikHandleBuild=None, buildType=0, buildAdditiveFk=False, controlSpacing=1, mod=None,
                 **attrs):

        if not node:
            name = name or attrs.get('rigName', "")
            name = self.generateUniqueName(name)
            metaAttrs = dict(locals())  # Get all the parameters
            metaAttrs.pop('self')
            metaName = name + "_meta"

        super(MetaSplineRig, self).__init__(node=node, name=name, initDefaults=initDefaults, lock=lock, mod=mod)
        if not node:
            if ikHandleBuild and buildType == splinebuilder.BT_IKHANDLE:
                startJoint, endJoint = joints.jointsFromIkHandle(ikHandleBuild)

            self.setMetaAttributes(**metaAttrs)
            if startJoint and endJoint:
                self.setStartJoint(startJoint, rebuild=False, mod=mod)
                self.setEndJoint(endJoint, rebuild=False, mod=mod)
                self.bindJointDefaults(mod=mod)
            self.setRigName(name, mod=mod)

    def metaAttributes(self):
        """Creates the dictionary as attributes if they don't already exist"""
        defaults = super(MetaSplineRig, self).metaAttributes()
        defaults.extend(MetaSplineRig._default_attrs)

        return defaults

    def generateUniqueName(self, name=""):
        """ Generates a unique rig name, if its already unique it will return name

        :return:
        :rtype: str
        """
        metaNames = self.metaNodeRigNames()
        while name in metaNames:
            name = namehandling.incrementName(name)

        return name

    def flatten(self, l):
        """ Flattens a list

        [[1,2,3], [1,2,3]] --> [1, 2 ,3, 1, 2, 3]


        :param l:
        :type l:
        :return:
        :rtype:
        """
        return [item for sublist in l for item in sublist]

    def connectAttributes(self, **attrs):
        """ Connects the maya nodes to the meta node
        """
        mod = attrs.get('mod')

        # Do the ones with the dag node lists first
        dagList = ['splineIkList', 'clusterList', 'fkControlList', 'fkGroupList',
                   'revfkControlList', 'revfkGroupList', 'floatControlList',
                   'floatGroupList', 'spineControlList', 'spineRotControl', 'spineOtherConstraintList',
                   'scaleGroupConstraint', 'multStretchNodes', 'maintainScaleNodes']
        for attr in dagList:
            self.clearMessageAttrs(attr)
            self.connectNodesToMessageAttr(attrs.get(attr, []), attr, mod)

        # Then the single nodes
        dagNodes = ['scaleMultiplyNode', 'cogGroup', 'scaleGroup', 'cogControl',
                    'splineSolver', 'rigGrp', 'curveInfo', 'startJoint', 'endJoint']
        for attr in dagNodes:
            node = attrs.get(attr)
            [o.delete(modifier=mod) for o in self.attribute(attr)]
            if node:
                self.connectNodeToMessageAttr(node, attr, mod)

        if mod:
            mod.doIt()
        self.setupMarkingMenus()

    def setupMarkingMenus(self, includeMesh=True):
        """Set up marking menus

        :param includeMesh: Add marking menu to the skinned meshes too?
        :type includeMesh: bool
        """
        mmNodes = self.allControls()
        layoutId = "markingMenu.splinerig"
        if mmNodes:
            triggers.createMenuTriggers(mmNodes, menuId=layoutId)

        if includeMesh:
            self.setMeshMarkingMenuActive(True)

    def setMeshMarkingMenuActive(self, active, mod=None):
        """ Set marking menus for

        :param active:
        :type active:
        :return:
        :rtype:
        """
        if active:
            layoutId = "markingMenu.splinerig"
            meshes = self.skinnedMeshes(self.additiveFkMetaNode())
            if meshes:
                triggers.createMenuTriggers(meshes, menuId=layoutId)
        else:
            self.deleteMeshMarkingMenus(mod=mod)

        if mod:
            mod.doIt()

    def deleteMeshMarkingMenus(self, mod):
        for m in self.savedMeshes():
            trigger = triggers.TriggerNode.fromNode(m)
            if trigger is not None:
                trigger.deleteTriggers()
        self.clearMessageAttrs("meshes", mod)

    def meshHasMarkingMenus(self):
        """ Returns true if has saved meshes

        :return:
        :rtype:
        """
        for m in self.meshes:
            sourceNode = m.sourceNode()
            if sourceNode is None:
                continue
            if triggers.TriggerNode.hasTrigger(sourceNode):
                return True
        return False

    def bindJointDefaults(self, mod=None):
        """ Bind the defaults positions/rotations for the joints
        """
        if mod:
            mod.doIt()  # Make sure the joints have been set first

        if self.startJointNode() and self.endJointNode():
            for i, j in enumerate(self.joints()):
                self.boundJointMatrices[i].set(j.worldMatrix(), mod)

    def setMetaAttributes(self, mod=None, **metaAttrs):
        """ Sets the setup's attributes usually from the UI. Will not update rig automatically
        """
        self.buildFk.set(metaAttrs['buildFk'], mod)  # type: zapi.Plug
        self.buildRevFk.set(metaAttrs['buildRevFk'], mod)
        self.buildFloat.set(metaAttrs['buildFloat'], mod)  # type: zapi.Plug
        self.buildSpine.set(metaAttrs['buildSpine'], mod)  # type: zapi.Plug
        self.orientRoot.set(metaAttrs['orientRoot'], mod)  # type: zapi.Plug
        self.scale.set(metaAttrs['scale'], mod)  # type: zapi.Plug
        self.controlCount.set(metaAttrs['controlCount'], mod)  # type: zapi.Plug
        self.hierarchySwitch.set(metaAttrs['hierarchySwitch'], mod)  # type: zapi.Plug
        self.controlSpacing.set(metaAttrs['controlSpacing'], mod)  # type: zapi.Plug

        if metaAttrs.get('buildAdditiveFk'):
            self.buildAdditiveFk.set(True, mod)

        if metaAttrs['jointsSpline'] and metaAttrs['jointsSpline'].exists():
            metaAttrs['jointsSpline'].message.connect(self.jointsSpline, mod)

        if metaAttrs['ikHandleBuild'] and metaAttrs['ikHandleBuild'].exists():
            metaAttrs['ikHandleBuild'].message.connect(self.ikHandleBuild, mod)

    def _renameRig(self, newName, mod=None):
        """ Renames the rig

        Internal function to rename the rig. Don't use this one, use .setRigName() instead.

        :param newName:
        :type newName: str or zapi.Plug
        :return:
        :rtype:
        """
        nodes = self.allMessageNodes()

        # Add children as well (only 1 level deep)
        for n in list(nodes):
            if type(n) is zapi.DagNode:
                nodes += n.children()
        nodes += self.joints()  # add joints
        nodes = list(set(nodes))  # Make unique

        for n in nodes:
            if n is None:
                continue

            try:
                i = n.name().index('_')
                if i != -1:
                    n.rename("{}_{}".format(newName, n.name()[i + 1:]), maintainNamespace=True, mod=mod)
            except ValueError:  # '_' not found ignoring
                pass

        self.rename(newName, mod=mod)
        addFkMeta = self.additiveFkMetaNode()
        if addFkMeta:
            addFkMeta.renameRig(newName)
        self.oldName = newName

    @classmethod
    def metaNodeRigNames(cls):
        """ Gets the rig names in the scene based on available metanodes

        :return:
        :rtype:
        """
        rigNames = []
        for n in base.findMetaNodesByClassType(MetaSplineRig.__name__):
            rigNames.append(n.rigName.value())
        return rigNames

    def allMessageNodes(self, includeDefault=False):
        """ Gets all the rig nodes

        :return:
        :rtype: list[zapi.DagNode or zapi.DGNode]
        """

        # Most likely its the message attributes
        metaAttrs = self.metaAttributes()
        messageAttrs = [m['name'] for m in metaAttrs if m['Type'] == zapi.attrtypes.kMFnMessageAttribute and (
                "zooMMeta" not in m['name'] and includeDefault is False)]

        nodes = []  # type: list[zapi.DGNode]
        for m in messageAttrs:
            attr = self.attribute(m)
            if attr.isArray:
                for a in attr:
                    sourceNode = a.sourceNode()
                    if sourceNode is None:
                        continue
                    nodes.append(sourceNode)
                continue
            sourceNode = attr.sourceNode()
            if sourceNode is None:
                continue
            nodes.append(sourceNode)

        return nodes

    def setControlCount(self, c, rebuild=True):
        """ Set number of controls

        :param c: New control count
        :type c: int or zapi.Plug
        :return:
        :rtype:
        """
        self.controlCount = c
        if rebuild:
            self.rebuild()

    def setScale(self, scl):
        """ Set scale

        :param scl: set the control scale to this value
        :type scl: float or :class:`zapi.Plug`
        :return:
        :rtype:
        """
        self.scale = scl  # type: zapi.Plug
        rigControls = self.allControls()
        for ctrl in rigControls:
            scaleDefaults = ("zooScaleDefault_x", "zooScaleDefault_y", "zooScaleDefault_z")
            ctrlScale = [ctrl.attribute(sAttr).value() * scl for sAttr in scaleDefaults if ctrl.attribute(sAttr)]
            if ctrlScale:
                controls.scaleBreakConnectCtrl(ctrl.fullPathName(), ctrlScale, False)

        self.setAdditiveFkScale(scl)

    def setAdditiveFkScale(self, scl):
        """ Set the scale of the additive fk

        :param scl: set the control scale to this value
        :type scl: float or :class:`zapi.Plug`
        :return:
        :rtype:
        """
        if self.additiveFkMetaExists():
            self.additiveFkMetaNode().setScale(scl)

    def setPublished(self, pub):
        """ Sets published (hides marking menu items for users)

        :param pub:
        :type pub:
        :return:
        :rtype:
        """
        self.published = pub

    def isPublished(self):
        """ Is published

        :return:
        :rtype: bool
        """
        return self.published.value()

    def allControls(self):
        """ All controls in the rig

        :return:
        :rtype: list[:class:`zapi.DagNode`]
        """
        ctrls = [ctrl.value() for ctrl in self.spineControlList if ctrl is not None]
        ctrls += [ctrl.value() for ctrl in self.spineRotControl if ctrl is not None]
        ctrls += [ctrl.value() for ctrl in self.revfkControlList if ctrl is not None]
        ctrls += [ctrl.value() for ctrl in self.fkControlList if ctrl is not None]
        ctrls += [ctrl.value() for ctrl in self.floatControlList if ctrl is not None]
        ctrls += [self.cogControl.value()]
        ctrls = [i for i in ctrls if i is not None]
        return ctrls

    def currentControls(self, includeCog=True):
        """Get the current controls in the current mode.

        :return: All the controls as zapi objects in the current mode.
        :rtype: list[:class:`zapi.DagNode`]
        """
        currentMode = self.currentHierarchyModeStr()
        ret = []
        if currentMode == splines.SPINE:
            ret += [ctrl.value() for ctrl in self.spineControlList] + [ctrl.value() for ctrl in self.spineRotControl]
        elif currentMode == splines.FK:
            ret += [ctrl.value() for ctrl in self.fkControlList]
        elif currentMode == splines.FLOAT:
            ret += [ctrl.value() for ctrl in self.floatControlList]
        elif currentMode == splines.REVFK:
            ret += [ctrl.value() for ctrl in self.revfkControlList]

        if includeCog:
            ret.append(self.cogControlNode())
        ret = [i for i in ret if i is not None]
        return ret

    def setOrientRoot(self, orient, updateRig=True):
        """ Set the orient root setting

        :param orient:
        :type orient: str or zapi.Plug
        :return:
        :rtype:
        """
        self.orientRoot = orient
        if updateRig:
            self.updateRig()

    def setBuildSpine(self, b, rebuildRig=True):
        """ Set the rig to build the spine

        :param b:
        :type b: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.buildSpine = b
        if rebuildRig:
            self.rebuildRig()

    def setRigName(self, name, mod=None, force=True):
        """ Set the rig name

        :param name:
        :type name: str or zapi.Plug
        :return:
        :rtype:
        """
        name = name or "splineRig"

        if name == self.rigName.value() and not force:
            return  # name is same ignoring
        name = self.generateUniqueName(name)
        self.rigName.set(name, mod)  # type: zapi.Plug
        self._renameRig(name, mod=mod)

    def setBuildFloat(self, b, rebuildRig=True):
        """ Set the rig to build floating controls

        :param b:
        :type b: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.buildFloat = b
        if rebuildRig:
            self.rebuildRig()

    def setBuildReverseFKControls(self, b, rebuildRig=True):
        """ Set the rig to build teh reverse fk controls

        :param b:
        :type b: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.buildRevFk = b
        if rebuildRig:
            self.rebuildRig()

    def setBuildFK(self, b, rebuildRig=True):
        """ Set the rig to build the FK controls

        :param b:
        :type b: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.buildSpine = b
        if rebuildRig:
            self.rebuildRig()

    def setStartJoint(self, startJoint, rebuild=True, mod=None):
        """ Set the start joint

        :param startJoint:
        :type startJoint: str or zapi.Plug
        :return:
        :rtype:
        """
        if isinstance(startJoint, six.string_types):
            startJoint = zapi.nodeByName(startJoint)
        startJoint.message.connect(self.startJoint, mod=mod)
        if rebuild:
            self.rebuild()

    def setEndJoint(self, endJoint, rebuild=True, mod=None):
        """ Set the end joint

        :param endJoint:
        :type endJoint: str or zapi.Plug
        :return:
        :rtype:
        """
        if isinstance(endJoint, six.string_types):
            endJoint = zapi.nodeByName(endJoint)
        endJoint.message.connect(self.endJoint, mod=mod)
        if rebuild:
            self.rebuild()

    def setHierarchySwitch(self, hierSwitch, updateRig=True):
        """ Set the hierarchy

        :param hType: Needs to be string
        :type hType: str or zapi.Plug
        :return:
        :rtype:
        """
        self.hierarchySwitch = hierSwitch
        if updateRig:
            self.updateRig()

    def buildAdditiveFkRig(self, mod=None, controlSpacing=1, rigName=""):
        """ Build additive Fk Rig

        :param mod:
        :type mod:
        :param controlSpacing: Build the controls on every nth joint
        :type controlSpacing: int
        :return additiveFkMeta: The addFk meta node
        :rtype additiveFkMeta: :class:`zapi.DagNode`
        """
        if not rigName:
            rigName = self.name()  # builds same name as the current spline rig

        cmd = additivefkbuild.AdditiveFKBuildCommand()
        additiveFkMeta = cmd.runArguments(joints=self.joints(),
                                          controlSpacing=controlSpacing,
                                          rigName=rigName)
        self.setAdditiveFk(additiveFkMeta, mod)
        self.controlSpacing.set(controlSpacing, mod)  # set SplineRig meta attr controlSpacing
        additiveFkMeta.controlGroup().setParent(self.rigGroupNode(), mod)
        self.setAdditiveFkScale(self.scale.value())
        return additiveFkMeta, cmd

    def deleteAdditiveFkRig(self):
        """ Delete additive fk rig

        :return:
        :rtype:
        """
        executor.execute("zoo.maya.additiveFk.delete", meta=self.additiveFkMetaNode())

    def setAdditiveFk(self, additiveFkMeta, mod=None):
        """ Sets the additive FK meta node

        :param additiveFkMeta: Connects the new additive fk meta node to this one
        :type additiveFkMeta: :class:`metaadditivefk.ZooMetaAdditiveFk`
        :return:
        :rtype:
        """

        additiveFkMeta.message.connect(self.additiveFkMeta, mod=mod)
        additiveFkMeta.addMetaParent(self, mod=mod)
        # self.connectNodesToMessageAttr(additiveFkMeta.getControls(), attr="additiveFkControls", mod=mod)

    def additiveFkMetaNode(self):
        """ Additive FK Meta node

        :return: Returns the meta node of the additive zoo meta
        :rtype: :class:`metaadditivefk.ZooMetaAdditiveFk`
        """
        dag = self.additiveFkMeta.value()
        if dag:
            return metaadditivefk.ZooMetaAdditiveFk(node=dag.object())

    def additiveFkDag(self):
        """ Additive FK dag node

        :return:
        :rtype: :class:`zapi.DagNode`
        """
        return self.additiveFkMeta.value()

    def additiveFkMetaExists(self):
        """ Returns true if additive fk meta node exists

        :return:
        :rtype:
        """
        return self.additiveFkMeta.value() is not None

    def joints(self):
        """ Gets all the joints in between start and end

        :return:
        :rtype: list[zapi.DagNode]
        """
        startJoint = self.startJoint.value()
        endJoint = self.endJoint.value()
        ret = []
        joint = startJoint
        while joint != endJoint or joint is None:
            ret.append(joint)
            children = joint.children()
            if len(children):
                joint = children[0]

        ret.append(endJoint)
        return ret

    def selectJoints(self):
        """ Selects the skin joints, if the addFk joints exist then select those as a priority
        """
        addFkMeta = self.additiveFkMetaNode()
        if addFkMeta:
            addFkMeta.selectBlendJoints()
        else:
            cmds.select(zapi.fullNames(self.joints()))

    def selectMeta(self):
        """ Select Meta

        :return:
        :rtype:
        """
        cmds.select(self.fullPathName())

    def bake(self, keepMeta=False, mod=None, showSpline=False):
        """Bakes the objects, leaving them in the current position while deleting the rig

        :param keepMeta:
        :type keepMeta:
        :param mod:
        :type mod:
        :param showSpline: Set to true if rebuilding, keeps the original curve hidden if exists
        :type showSpline: bool
        """
        rigName = self.fullPathName()

        for joint in self.joints():  # joints need to disconnect first otherwise scale is set to zero
            j = joint.fullPathName()  # TODO zapi disconnect code?
            connections.breakAttr("{}.scaleY".format(j))
            connections.breakAttr("{}.scaleZ".format(j))

        # Show AddFk rig if hidden
        addFkMeta = self.additiveFkMetaNode()
        if addFkMeta:
            addFkMeta.setControlsVisible(True)

        # Delete everything else
        rigGroup = self.rigGrp.value()

        if rigGroup:
            startJoint = self.startJoint.value()  # type: zapi.DagNode
            startJoint.setParent(rigGroup.parent(), mod=mod)  # Unparent joints from group
            if self.additiveFkMetaExists():
                self.detachAdditiveFk(mod=mod)
            delNodes = [o.value() for o in self.multStretchNodes] + [self.scaleMultiplyNode.value()] + \
                       [self.curveInfo.value(), rigGroup] + [o.value() for o in self.maintainScaleNodes]
            exclude = ["BlendTwoAttr"]
            for dn in delNodes:
                if any([e for e in exclude if e in dn.name()]):
                    continue
                if dn:
                    dn.delete()

        if self.jointsSpline.sourceNode() and not showSpline:
            self.jointsSpline.sourceNode().show()

        if not keepMeta:
            self.delete(mod)

        om2.MGlobal.displayInfo("Success: Rig baked: {}".format(rigName))

    def build(self, bindDefaultJoints=True, buildType=splinebuilder.BT_STARTENDJOINT, mod=None):
        """ Build based on source objects and curve

        :param bindDefaultJoints:
        :type bindDefaultJoints:
        :param buildType:
        :type buildType:
        :param mod:
        :type mod: om2.MDGModifier
        :return:
        :rtype:
        """

        if buildType == splinebuilder.BT_STARTENDJOINT:
            valid = splinebuilder.validStartEndJoint(self.startJoint.value().fullPathName(),
                                                     self.endJoint.value().fullPathName())

            if not valid:
                return

        if bindDefaultJoints:
            self.bindJointDefaults(mod=mod)
        curve = self.jointsSpline.sourceNode()
        if curve:
            curve.hide(mod=mod, apply=False)

        if self.orientRoot.value():  # is an int value so if not 0
            cogUpAxis = UP_AXIS_LIST[self.orientRoot.value() - 1].lower()  # add one to account for Auto in combobox
        else:  # is 0
            cogUpAxis = "Auto"
        ikHandleBuild = self.ikHandleBuild.value()

        splineInstance, nodes = splinebuilder.buildSpineJoints(rigName=self.rigName.value(),
                                                               startJoint=self.startJoint.value().fullPathName(),
                                                               endJoint=self.endJoint.value().fullPathName(),
                                                               controlCount=self.controlCount.value(),
                                                               scale=self.scale.value(),
                                                               buildFk=self.buildFk.value(),
                                                               buildRevFk=self.buildRevFk.value(),
                                                               buildSpine=self.buildSpine.value(),
                                                               buildFloat=self.buildFloat.value(),
                                                               cogUpAxis=cogUpAxis,
                                                               buildType=buildType,
                                                               ikHandleBuild=ikHandleBuild,
                                                               message=False,
                                                               addToUndo=False,
                                                               splineCurve=curve)

        if buildType == splinebuilder.BT_IKHANDLE:  # need to update the controls
            self.controlCount = splineInstance.controlCount
            self.buildSpine = splineInstance.spine

        connectAttrs = {"splineIkList": splineInstance.splineIkList,
                        "splineSolver": splineInstance.splineSolver,
                        "clusterList": list(zapi.nodesByNames(self.flatten(splineInstance.clusterList))),
                        "fkControlList": splineInstance.fkControlList,
                        "fkGroupList": splineInstance.fkGroupList,
                        "revfkControlList": splineInstance.revfkControlList,
                        "revfkGroupList": splineInstance.revfkGroupList,
                        "floatControlList": splineInstance.floatControlList,
                        "floatGroupList": splineInstance.floatGroupList,
                        "spineControlList": splineInstance.spineControlList,
                        "spineRotControl": splineInstance.spineRotControl,
                        "curveInfo": zapi.nodeByName(splineInstance.curveInfo),
                        "spineOtherConstraintList": splineInstance.spineOtherConstraintList,
                        "cogControl": splineInstance.cogControl,
                        "cogGroup": splineInstance.cogGroup,
                        "scaleGroup": zapi.nodeByName(splineInstance.scaleGroup),
                        "scaleMultiplyNode": zapi.nodeByName(splineInstance.scaleMultiplyNode),
                        "scaleGroupConstraint": list(zapi.nodesByNames(splineInstance.scaleGroupConstraint)),
                        "multStretchNodes": list(zapi.nodesByNames(splineInstance.buildStretchyNodes)),
                        "maintainScaleNodes": list(zapi.nodesByNames(splineInstance.maintainScaleNodes)),
                        "rigGrp": splineInstance.rigGrp,
                        "startJoint": self.startJoint.value(),
                        "endJoint": self.endJoint.value()}

        self.connectAttributes(mod=mod, **connectAttrs)
        # Build the Additive Fk rig as well

        # Check to see if it already exists
        self._setupAdditiveFk(mod)

    def _setupAdditiveFk(self, mod):
        """ Set up addtiive fk it it hasn't been set up

        :param mod:
        :return:
        """
        additiveFkMeta = metaadditivefk.ZooMetaAdditiveFk.connectedMetaNodes(self.startJointNode())

        if self.buildAdditiveFk.value() is True and not additiveFkMeta:
            self.buildAdditiveFkRig(mod=mod, controlSpacing=self.controlSpacing.value())

        elif additiveFkMeta:
            self.setAdditiveFk(additiveFkMeta, mod)
            additiveFkMeta.controlGroup().setParent(self.rigGroupNode(), mod)
            additiveFkMeta.jointAddFkList[0].value().setParent(self.rigGroupNode(), mod)
            additiveFkMeta.jointBlendList[0].value().setParent(self.rigGroupNode(), mod)

    def connectNodesToMessageAttr(self, nodes, attr, mod=None):
        """ Connect nodes

        :param nodes:
        :type nodes:
        :param attr:
        :type attr:
        :param mod:
        :type mod:
        :return:
        :rtype:
        """
        for i, ob in enumerate(nodes):
            try:
                ob.message.connect(self.attribute(attr)[i], mod=mod)
            except AttributeError as e:
                raise AttributeError("{}, {}".format(e, ob))

    def clearMessageAttrs(self, attr, mod=None):
        """
        todo: can probably be moved to plug or base class
        todo: mod needs to work

        :return:
        :rtype:
        """
        [o.delete() for o in self.attribute(attr)]

    def connectNodeToMessageAttr(self, node, attr, mod=None):

        try:
            node.message.connect(self.attribute(attr), mod=mod)
        except AttributeError as e:
            raise AttributeError("{}, node: {}, dagNode: {}".format(e, node, attr))

    def skinnedMeshes(self, addFkMeta):
        """Returns the skinned meshes if any are skinned to the joints

        :param addFkMeta:
        :type addFkMeta:
        :return:
        :rtype:
        """
        skinClusterList = self.skinClusters(addFkMeta)
        attr = "meshes"
        connectedMeshes = deformers.skinClustersConnectedMeshes(skinClusterList)
        if connectedMeshes:
            self.clearMessageAttrs(attr)
            self.connectNodesToMessageAttr(connectedMeshes, attr)
        return connectedMeshes

    def skinClusters(self, addFkMeta):
        """Returns the skin clusters if any are skinned to the joints

        :param addFkMeta:
        :type addFkMeta:
        :return:
        :rtype:
        """
        if addFkMeta:  # Check for skin on blend joints and spline rig joints
            joints = addFkMeta.getBlendJoints() + self.joints()
            return deformers.skinClustersFromJoints(joints)
        else:  # Check skin  on spline rig joints
            return deformers.skinClustersFromJoints(self.joints())

    def duplicateRig(self):
        """ Duplicate rig

        :type mod: om2.MDGModifier
        :return: Returns the new duplicated meta
        :rtype: MetaSplineRig
        """
        addFkMeta = self.additiveFkMetaNode()
        skinClusterList = self.skinClusters(addFkMeta)

        exportSel = [self.fullPathName(), self.rigGrp.value().fullPathName()]  # todo: get mesh
        if skinClusterList:
            skinClusters = zapi.fullNames(skinClusterList)
            for clstr in skinClusters:
                exportSel.append(clstr)
                # Bug in 2022 and 2023 doesn't export skinned geo nodes unless they are selected
                skinGeoList = cmds.skinCluster(clstr, query=True, geometry=True)
                if skinGeoList:
                    exportSel += skinGeoList
        cmds.select(exportSel)

        tempDir = filesystem.getTempDir()
        randText = "splineRig" + str(uuid.uuid4())[:3]
        randText.replace('-', '')
        path = os.path.join(tempDir, "{}.ma".format(randText)).replace("\\", "\\\\")

        cmds.file(path, force=True, options="v=0;", type="mayaAscii", preserveReferences=True, exportSelected=True)
        cmds.file(path, i=True, type="mayaAscii", ignoreVersion=True, renameAll=True, mergeNamespacesOnClash=False,
                  usingNamespaces=True, options="v=0;", namespace=randText,
                  preserveReferences=True, importTimeRange="combine")

        meta = None  # type: MetaSplineRig
        for m in self.metaNodesInScene():
            if randText in str(m.name(includeNamespace=True)):
                meta = m  # type: MetaSplineRig

        meta.setRigName(self.rigNameStr())
        namehandling.deleteNamespaces([meta.rigGrp.value().fullPathName()], renameShape=True, message=False)
        # maya name parts
        cmds.select(meta.cogControlNode().fullPathName())
        return meta

    def switchControls(self, ctrls):
        """ Switch to control type and match

        :param ctrls:
        :type ctrls:
        :return:
        :rtype:
        """

        switched = splinerigswitcher.switchMatchSplineMode(ctrls,
                                                           meta=self,
                                                           switchObj=self.cogControl.value().fullPathName(),
                                                           selectControls=True)
        self.setCurrentControlVis(vis=True)
        if switched:
            self.hierarchySwitch = ctrls
        return switched

    def toggleControls(self):
        """ Toggle Controls

        :return:
        :rtype:
        """
        controls = self.currentControls(includeCog=False)
        hidden = self.controlsHidden()
        for ctrl in controls:
            if not ctrl.isLocked and ctrl.attribute("visibility").source() is None:
                cmds.setAttr("{}.visibility".format(ctrl.fullPathName()), hidden)

    def toggleControlsAdditiveFk(self):
        """ Toggle controls additive FK

        :return:
        :rtype:
        """
        addFkMeta = self.additiveFkMetaNode()
        if addFkMeta:
            addFkMeta.toggleControls()

    def additiveFkControlsHidden(self):
        """ Return true if additive fk controls hidden, false otherwise

        :return:
        :rtype:
        """
        return self.additiveFkMetaNode().controlsHidden()

    def controlsHidden(self):
        """ Controls hidden. Just checks the first one for now

        :return: Are the controls hidden in the scene
        :rtype: bool
        """
        controls = self.currentControls(includeCog=False)
        return controls[0].isHidden()

    def setCurrentControlVis(self, vis, includeCog=False):
        """ Set the current control visibility

        :param vis: True if visible, false otherwise
        :type vis:
        :param includeCog:
        :type includeCog:
        :return:
        :rtype:
        """
        controls = self.currentControls(includeCog=includeCog)
        for ctrl in controls:
            if not ctrl.isLocked and ctrl.attribute("visibility").source() is None:
                cmds.setAttr("{}.visibility".format(ctrl.fullPathName()), vis)

    def rebuild(self, selectLast=True, bake=False, message=True, mod=None):
        """ Rebuild curve based

        :param mod:
        :type mod: om2.MDagModifier
        :param selectLast: Selects the last object after rebuild
        :type selectLast: bool
        :return: Returns last selected object if it is related to the metanode
        :rtype:
        """
        selected = []
        if selectLast:
            selected = zapi.fullNames(zapi.selected())

        # todo: deprecated

        if bake:
            self.bake(keepMeta=True, mod=mod)
        else:
            self.deleteRig(keepMeta=True, mod=mod, message=False)
        if mod:
            mod.doIt()

        rebind = bake
        self.build(bindDefaultJoints=rebind, mod=mod)
        if mod:
            mod.doIt()
        if message:
            om2.MGlobal.displayInfo("Success: Spline Rig Rebuilt")

        if selectLast:
            try:
                if mod:
                    mod.pythonCommandToExecute("from maya import cmds;cmds.select({})".format(selected))
                    mod.doIt()
                else:
                    cmds.select(selected)
            except ValueError:
                pass

    def updateAttributes(self):
        """ Update attributes from rig
        """
        switch = self.hierarchySwitchRigValue()
        if switch is not None:
            self.hierarchySwitch = HIERARCHY_SWITCH[switch]

    def hierarchySwitchRigValue(self):
        """Combo int value for the GUI assuming there is four items in the combo box

        'spine' = 0
        'fk' = 1
        'float' = 2
        'revFk = 3

        :return comboModeInt: The GUI Switch To Combo int value of the current hierarchy mode
        :rtype comboModeInt: int
        """
        if self.cogControl.value() and self.cogControl.value().attribute("hierarchySwitch"):
            strMode = cmds.getAttr("{}.hierarchySwitch".format(self.cogControl.value().fullPathName()), asString=True)
            return HIERARCHY_SWITCH.index(strMode)

    def currentHierarchyModeStr(self):
        """Returns a string of the current mode

        :return currentMode: Either 'spine', 'fk', 'float', or 'revFk'
        :rtype currentMode: str
        """
        if self.cogControl.value() and self.cogControl.value().attribute("hierarchySwitch"):
            return cmds.getAttr("{}.hierarchySwitch".format(self.cogControl.value().fullPathName()), asString=True)
        # If there aren't multiple rigs then need to test to see which controls are present.
        if self.spineControlList.numConnectedElements() != 0:
            return splines.SPINE
        elif self.fkControlList.numConnectedElements() != 0:
            return splines.FK
        elif self.floatControlList.numConnectedElements() != 0:
            return splines.FLOAT
        elif self.revfkControlList.numConnectedElements() != 0:
            return splines.REVFK

    def objectIndex(self, obj):
        """ Gets the index of object

        :param obj:
        :type obj:
        :return:
        :rtype:
        """
        if obj is None:
            return

        for i, objects in enumerate(self.objectList):
            if objects.value() == obj:
                return i

    def controlTypes(self):
        """ Control types available as strings

        :return controlTypeList: A list of control types that exist on the rig Eg ['spine', 'revFk']
        :rtype controlTypeList: list[str]
        """
        ret = ['spine'] if self.buildSpine.value() else []
        ret += ['fk'] if self.buildFk.value() else []
        ret += ['float'] if self.buildFloat.value() else []
        ret += ['revFk'] if self.buildRevFk.value() else []
        return ret

    def setOriginalObjectVis(self, visibility):
        """Show or hide the visibility of the original object

        :param visibility: True is show hide is False
        :type visibility: bool
        """
        try:  # unsure how to test more efficiently
            sourceObjects = [o.value().fullPathName() for o in self.sourceObjects]
        except ValueError:
            om2.MGlobal.displayWarning("No original objects found to be shown/hidden, might have been deleted. "
                                       "Metanode: {}".format(self))
            return
        if self.sourceGroup:  # also may have been deleted
            sourceGrp = self.sourceNode(self.sourceGroup).fullPathName()
            cmds.showHidden(sourceGrp)
        shortNameSources = cmds.ls(sourceObjects, shortNames=True)  # unique or short names
        if visibility:
            cmds.showHidden(sourceObjects)
            om2.MGlobal.displayInfo("Objects shown: {}".format(shortNameSources))
        else:
            cmds.hide(sourceObjects)
            om2.MGlobal.displayInfo("Objects hidden: {}".format(shortNameSources))

    def origObjVisiblity(self):
        """Returns the visibility of the first source object

        :return visible:  True is visible, False if hidden
        :rtype visible: bool
        """
        if not self.sourceObjects:  # probably should never fail
            return None
        firstOrigObj = self.sourceNode(self.sourceObjects[0])
        if not firstOrigObj:
            return None
        return firstOrigObj.visibility.asBool()

    def detachAdditiveFk(self, mod=None):
        """ Detach the additive Fk rig so the meta can be deleted or baked

        :param mod:
        :type mod:
        :return:
        :rtype:
        """

        addFkMeta = self.additiveFkMetaNode()
        if addFkMeta:  # Unparent the additive FK Meta
            toMove = [addFkMeta.controlGroup(),
                      addFkMeta.jointAddFkList[0].value(),
                      addFkMeta.jointBlendList[0].value()]
            for m in toMove:
                m.setParent(self.rigGroupNode().parent(), mod=mod)
            mod.disconnect(self.additiveFkDag().message.plug(), self.additiveFkMeta.plug())
            addFkMeta.removeParent(self, mod=mod)
            mod.doIt()

    def deleteRig(self, keepMeta=False, deleteAll=False, mod=None, message=True, showSpline=False):
        """ Delete the rig

        :param mod:
        :type mod: om2.MDGModifier
        :param deleteAll: Includes the mesh and joints
        :type deleteAll: bool
        :param showSpline: Set to true if rebuilding, note only controls vis of the original curve
        :type showSpline: bool
        :return:
        :rtype:
        """
        rigName = self.fullPathName()

        if not self.exists():
            return
        mod = mod or om2.MDagModifier()

        rigGrp = self.rigGrp.value()  # type: zapi.DagNode

        # Show AddFk rig if hidden
        addFkMeta = self.additiveFkMetaNode()
        if addFkMeta:
            addFkMeta.setControlsVisible(True)

        if self.curveInfo.value():
            self.curveInfo.value().delete(mod=mod)

        if rigGrp:

            exclude = [self.startJoint.value(),  # Exclude from deletion
                       self.endJoint.value(),
                       self.splineSolver.value()]

            # Unparent start Joint
            startJoint = self.startJointNode()
            startJoint.setParent(rigGrp.parent(), mod=mod)

            # Unparent additive FK
            if self.additiveFkMetaExists():
                self.detachAdditiveFk(mod=mod)

            # Dont need to include the saved meshes
            exclude += self.savedMeshes()
            # return
            self.rigGrp.value().delete(mod=mod)
            messageNodes = self.allMessageNodes()

            if self.jointsSpline.sourceNode() and not deleteAll:
                exclude.append(self.jointsSpline.value())
                if not showSpline:
                    self.jointsSplineNode().show(mod=mod)
            elif deleteAll:
                if addFkMeta:  # delete the additive FK
                    addFkMeta.deleteSetup(True)

                meshes = deformers.jointConnectedMeshes(startJoint)
                [m.delete(mod=mod) for m in meshes]
                startJoint.delete(mod=mod)

            mod.doIt()
            for n in messageNodes:
                if n and n.exists() and n not in exclude:
                    n.delete(mod=mod)

            # Reset joints
            if not deleteAll:
                self.resetJoints()

        if not keepMeta:
            self.delete(mod=mod)
        om2.MGlobal.displayInfo("Success: Rig deleted: {}".format(rigName))

    def resetJoints(self, mod=None):
        """ Resets joints to bound matrix positions

        :return:
        :rtype:
        """
        joints = self.joints()
        for i, j in enumerate(joints):
            cmds.xform(j.fullPathName(), matrix=self.boundJointMatrices[i].value(), worldSpace=True)

    def savedMeshes(self):
        return [m.value() for m in self.meshes]

    def enumNum(self, enumStr):
        """ Gets the number from the enum str eg "fk=1" ==> int(1)

        :param enumStr:
        :type enumStr:
        :return:
        :rtype:
        """
        return int(enumStr.split("=")[1])

    def updateRig(self, metaAttrs=None, mod=None):
        """ Update rig

        :param mod:
        :type mod: om2.MDGModifier
        :return:
        :rtype:
        """

        needsRebuild = self.checkNeedsRebuild(metaAttrs)
        self.setMetaAttributes(**metaAttrs)
        if needsRebuild:
            self.rebuild()

    def checkNeedsRebuild(self, metaAttrs):
        needsRebuild = False

        # check = [(self.buildSpine.value(),metaAttrs['buildSpine'])]
        check = ['buildFk', 'buildRevFk', 'buildSpine', 'buildFloat',
                 'controlCount']  # todo: do weight and reverse dir, world up
        for c in check:
            attr = metaAttrs.get('buildSpine')
            if self.attribute(c).value() != attr and attr is not None:
                needsRebuild = True

        return needsRebuild

    def metaAttributeValues(self):
        """ Get the Meta attributes to populate the ui

        :return:
        :rtype:
        """
        if not self.exists():
            return None
        self.updateAttributes()
        attrs = [attr['name'] for attr in self._default_attrs]
        metaAttrs = {}
        for a in attrs:
            metaAttrs[a] = self.attribute(a).value()
        return metaAttrs

    def rigGroupNode(self):
        """ The main rig group

        :return:
        :rtype: :class:`zapi.DagNode`
        """
        return self.rigGrp.value()

    def cogControlNode(self):
        """ Cog Control Value

        :return:
        :rtype: :class:`zapi.DagNode`
        """
        return self.cogControl.value()

    def rigNameStr(self):
        """ Get rig name

        :return:
        :rtype: str
        """
        return self.rigName.value()

    def startJointNode(self):
        """ Start Joint node

        :return:
        :rtype: :class:`zapi.DagNode`
        """

        return self.startJoint.value()

    def endJointNode(self):
        """ End Joint node

        :return:
        :rtype: :class:`zapi.DagNode`
        """

        return self.endJoint.value()

    def jointsSplineNode(self):
        """ Joints Spline Node

        :return:
        :rtype: :class:`zapi.DagNode`
        """
        return self.jointsSpline.value()
