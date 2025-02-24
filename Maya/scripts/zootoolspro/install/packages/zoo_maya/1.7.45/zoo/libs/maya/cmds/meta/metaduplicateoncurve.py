import math

from maya import cmds

import maya.api.OpenMaya as om2
from zoo.libs.maya.mayacommand import mayaexecutor as executor

from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.objutils import filtertypes, namehandling
from zoo.libs.maya.cmds.rig import splines, duplicatealongcurve
from zoo.libs.maya.meta import base

AXIS_INDEX = {'x': 0, 'y': 1, 'z': 2}
AXIS_LIST = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]


class MetaDuplicateOnCurve(base.MetaBase):
    """Class that controls the meta network node setup for the duplicate on curve functionality

    Found in zoo.libs.maya.cmds.rig.splines
    """
    Axis = ["+X", "-X", "+Y", "-Y", "+Z", "-Z"]

    _default_attrs = [
        {"name": "sourceObjects", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "sourceGroup", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, },
        {"name": "objectList", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "curve", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "rigGroup", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "upVGroup", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "motionPaths", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute, "isArray": True},
        {"name": "objGroup", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
        {"name": "upVArrow", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},

        # Attributes
        {"name": "multiple", "value": 20, "Type": zapi.attrtypes.kMFnNumericInt},
        {"name": "startPosition", "value": 0.0, "Type": zapi.attrtypes.kMFnNumericFloat},
        {"name": "endPosition", "value": 1.0, "Type": zapi.attrtypes.kMFnNumericFloat},
        {"name": "startRotation", "value": (0, 0, 0), "Type": zapi.attrtypes.kMFnNumeric3Float},
        {"name": "endRotation", "value": (0, 0, 0), "Type": zapi.attrtypes.kMFnNumeric3Float},
        {"name": "startScale", "value": (1.0, 1.0, 1.0), "Type": zapi.attrtypes.kMFnNumeric3Float},
        {"name": "endScale", "value": (1.0, 1.0, 1.0), "Type": zapi.attrtypes.kMFnNumeric3Float},
        {"name": "weight", "value": 0.0, "Type": zapi.attrtypes.kMFnNumericFloat},
        {"name": "weightPosition", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "weightRotation", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "weightScale", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "instanced", "value": False, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "upAxis", "value": "z", "Type": zapi.attrtypes.kMFnDataString},
        {"name": "followAxis", "value": "y", "Type": zapi.attrtypes.kMFnDataString},
        {"name": "inverseUp", "value": False, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "inverseFollow", "value": False, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "followRotation", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "fractionMode", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
        {"name": "groupAllGeo", "value": True, "Type": zapi.attrtypes.kMFnNumericBoolean},
    ]

    def __init__(self, node=None, name=None, initDefaults=True, lock=False, multiple=5, deleteMotionPaths=False,
                 weight=0.0,
                 startPosition=0.0,
                 endPosition=1.0, startRotation=(0, 0, 0), endRotation=(0, 0, 0),
                 startScale=(1.0, 1.0, 1.0),
                 endScale=(1.0, 1.0, 1.0), worldUpVector=(0, 1, 0),
                 followRotation=True, worldUpType=splines.WORLD_UP_SCENE, groupAllGeo=True, instanced=False,
                 upAxis="z", motionPName="moPth", worldUpObject="", followAxis="y",
                 fractionMode=True,
                 inverseFollow=False, inverseUp=False, weightPosition=True, weightRotation=True,
                 weightScale=True, autoWorldUpV=False):


        if not node:
            metaAttrs = dict(locals())  # Get all the parameters
            metaAttrs.pop('self')
            name = name or self.generateUniqueName()
        super(MetaDuplicateOnCurve, self).__init__(node=node, name=name, initDefaults=initDefaults, lock=lock)
        if not node:
            self.setMetaAttributes(**metaAttrs)


    def metaAttributes(self):
        """Creates the dictionary as attributes if they don't already exist"""
        defaults = super(MetaDuplicateOnCurve, self).metaAttributes()
        defaults.extend(MetaDuplicateOnCurve._default_attrs)

        return defaults

    @classmethod
    def generateUniqueName(cls, name=""):
        """ Get selected curve name

        :return:
        :rtype:
        """
        return namehandling.nonUniqueNameNumber("{}duplicateOnCurve_meta".format(name))

    def connectAttributes(self, **attrs):
        """ Connects the maya nodes to the meta node
        """
        mod = attrs.get('mod')
        # Connect Source objects
        sourceGroup = attrs.get('sourceGroup')
        [o.delete(modifier=mod) for o in self.sourceGroup]
        if sourceGroup:
            sourceGroup.message.connect(self.sourceGroup, mod=mod)

        [o.delete() for o in self.sourceObjects]
        for i, ob in enumerate(attrs['sourceObjects']):
            #ob.message.connect(self.sourceObjects.nextAvailableDestElementPlug(), mod=mod)
            ob.message.connect(self.sourceObjects[i], mod=mod)

        # Motion Path nodes
        [m.delete(modifier=mod) for m in self.motionPaths]
        for i, m in enumerate(attrs['motionPathNodes']):
            #m.message.connect(self.motionPaths.nextAvailableDestElementPlug())
            m.message.connect(self.motionPaths[i], mod=mod)

        # Duplicated object list
        [m.delete(modifier=mod) for m in self.objectList]
        for i, o in enumerate(attrs['objectList']):
            #o.message.connect(self.objectList.nextAvailableDestElementPlug(), mod=mod)
            o.message.connect(self.objectList[i], mod=mod)

        # Spline Curve
        attrs['splineCurve'].message.connect(self.curve, mod=mod)

        # Other Groups
        attrs['upVGrp'].message.connect(self.upVGroup, mod=mod)
        if attrs['rigGroup']:
            attrs['rigGroup'].message.connect(self.rigGroup, mod=mod)

        if attrs['group']:
            attrs['group'].message.connect(self.objGroup, mod=mod)
        attrs['upVArrow'].message.connect(self.upVArrow, mod=mod)

    def setMetaAttributes(self, **metaAttrs):
        """ Sets the setup's attributes usually from the UI
        """

        mod = metaAttrs.get('mod')
        self.multiple.set(metaAttrs['multiple'], mod) # type: zapi.Plug
        self.instanced.set(metaAttrs['instanced'], mod)  # type: zapi.Plug
        self.upAxis.set(metaAttrs['upAxis'], mod)
        self.followAxis.set(metaAttrs['followAxis'], mod)  # type: zapi.Plug
        self.startPosition.set(metaAttrs['startPosition'], mod)  # type: zapi.Plug
        self.endPosition.set(metaAttrs['endPosition'], mod)  # type: zapi.Plug
        self.weight.set(metaAttrs['weight'], mod)  # type: zapi.Plug
        self.weightScale.set(metaAttrs['weightScale'], mod)  # type: zapi.Plug
        self.weightPosition.set(metaAttrs['weightPosition'], mod)  # type: zapi.Plug
        self.weightRotation.set(metaAttrs['weightRotation'], mod)  # type: zapi.Plug
        self.startRotation.set(metaAttrs['startRotation'], mod)  # type: zapi.Plug
        self.endRotation.set(metaAttrs['endRotation'], mod)  # type: zapi.Plug
        self.startScale.set(metaAttrs['startScale'], mod)  # type: zapi.Plug
        self.endScale.set(metaAttrs['endScale'], mod)  # type: zapi.Plug
        self.inverseUp.set(metaAttrs['inverseUp'], mod)  # type: zapi.Plug
        self.inverseFollow.set(metaAttrs['inverseFollow'], mod)  # type: zapi.Plug
        self.followRotation.set(metaAttrs['followRotation'], mod)  # type: zapi.Plug
        self.groupAllGeo.set(metaAttrs['groupAllGeo'], mod)  # type: zapi.Plug
        self.fractionMode.set(metaAttrs['fractionMode'], mod)  # type: zapi.Plug

    def setMultiple(self, m, rebuild=True):
        """ Set number of objects on curve. Will rebuild

        :param m:
        :type m: int or zapi.Plug
        :return:
        :rtype:
        """
        self.multiple = m
        if rebuild:
            self.rebuild()

    def setInstanced(self, ins, rebuild=True):
        """ Set instanced or duplicate. Will rebuild

        :param ins:
        :type ins: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.instanced = ins  # type: zapi.Plug
        if rebuild:
            self.rebuild()

    def updateFromRig(self):
        """ Update attributes

        :return:
        :rtype:
        """
        pass

    def setFollowAxis(self, axis, updateCurve=True):
        """ Set follow Axis

        :param axis:
        :type axis:
        :return: str or zapi.Plug
        :rtype:
        """
        self.followAxis = axis
        if updateCurve:
            self.updateCurve()

    def setUpAxis(self, axis, updateCurve=True):
        """ Set Up Axis

        :param axis:
        :type axis:
        :return: str or zapi.Plug
        :rtype:
        """
        self.upAxis = axis
        if updateCurve:
            self.updateCurve()

    def setStartPosition(self, pos, updateCurve=True):
        """ Set start position

        :param pos:
        :type pos: float or zapi.Plug
        :return:
        :rtype:
        """
        self.startPosition = pos  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setEndPosition(self, pos, updateCurve=True):
        """ Set end position

        :param pos:
        :type pos: float or zapi.Plug
        :return:
        :rtype:
        """
        self.endPosition = pos  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setWeight(self, w, updateCurve=True):
        """ Set weighting of objects on curve

        :param w:
        :type w: float or zapi.Plug
        :return:
        :rtype:
        """
        self.weight = w  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setWeightScale(self, ws, updateCurve=True):
        """ Weight Scale Active

        :param ws:
        :type ws: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.weightScale = ws  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setWeightPosition(self, posActive, updateCurve=True):
        """ Weight Position active

        :param posActive:
        :type posActive: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.weightPosition = posActive  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setWeightRotation(self, rotActive, updateCurve=True):
        """ Weight Rotation

        :param rotActive:
        :type rotActive: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.weightRotation = rotActive  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setInverseUp(self, up, updateCurve=True):
        """ Inverse Up

        :param up:
        :type up: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.inverseUp = up  # type: zapi.Plug
        self.updateCurve()

    def setInverseFollow(self, f, updateCurve=True):
        """ Inverse Follow

        :param f:
        :type f: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.inverseFollow = f  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setFollowRotation(self, rot, updateCurve=True):
        """ Follow Rotation

        :param rot:
        :type rot: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.followRotation = rot  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setGroupAllGeo(self, g, updateCurve=True):
        """ Group All Geo (when generating)

        :param g:
        :type g: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.groupAllGeo.set(g)
        if updateCurve:
            self.rebuild()

    def setFractionMode(self, f, updateCurve=True):
        """ Set fraction mode

        :param f:
        :type f: bool or zapi.Plug
        :return:
        :rtype:
        """
        self.fractionMode.set(f)
        if updateCurve:
            self.updateCurve()

    def setStartRotation(self, rot, updateCurve=True):
        """ Set start rotation

        :param rot:
        :type rot: list[float] or  or zapi.Plug
        :return:
        :rtype:
        """
        self.startRotation = rot  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setEndRotation(self, rot, updateCurve=True):
        """ Set end rotation

        :param rot:
        :type rot: list[float]  or zapi.Plug
        :return:
        :rtype:
        """
        self.endRotation = rot  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setStartScale(self, scl, updateCurve=True):
        """ Set Start scale

        :param scl:
        :type scl: list[float] or zapi.Plug
        :return:
        :rtype:
        """
        self.startScale = scl  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def setEndScale(self, scl, updateCurve=True):
        """ Set end scale

        :param scl:
        :type scl: list[float] or zapi.Plug
        :return:
        :rtype:
        """
        self.endScale = scl  # type: zapi.Plug
        if updateCurve:
            self.updateCurve()

    def bake(self):
        """ Bakes the objects, leaving them in the current position while deleting the rig
        """

        rigGroup = self.sourceNode(self.rigGroup)
        objGroup = self.sourceNode(self.objGroup)
        curve = self.sourceNode(self.curve)

        [self.sourceNode(m).delete() for m in self.motionPaths if self.sourceNode(m)]
        self.sourceNode(self.upVGroup).delete() if self.upVGroup.source() else None

        if rigGroup:
            if objGroup:
                objGroup.setParent(rigGroup.parent())

            [s.value().setParent(rigGroup.parent()) for s in self.sourceObjects]
            curve.setParent(rigGroup.parent())
            rigGroup.delete()
        self.sourceGroup.value().delete() if self.sourceGroup.source() else None
        cmds.showHidden([o.value().fullPathName() for o in self.sourceObjects])
        self.delete()

    def buildSelected(self):
        """ Build based on the curve that is selected in maya

        :return:
        :rtype:
        """
        selObjs = list(zapi.selected())
        if not selObjs or len(selObjs) < 2:
            om2.MGlobal.displayWarning(
                "Selection incorrect.  Please select an object or objects and a curve last, or .build() must have arguments")
            return
        splineCurve = selObjs[-1]
        if not filtertypes.filterTypeReturnTransforms([splineCurve.fullPathName()], children=False,
                                                      shapeType="nurbsCurve"):
            om2.MGlobal.displayWarning("The last selected object must be a NURBS curve")
            return
        del selObjs[-1]
        cmds.select(splineCurve.fullPathName())  # Select curve

        executor.execute("zoo.maya.duplicateoncurve.build",
                         meta=self, sourceObjects=selObjs, curve=splineCurve)

    def build(self, sourceObjects, curve, rename=True):
        """ Build based on source objects and curve

        :param sourceObjects: Source objects to duplicate along the curve
        :type sourceObjects: list[str] or list[zapi.DagNode] or list[zapi.DgNode] or str or zapi.DagNode
        :param curve: The curve to duplicate along
        :type curve: str or zapi.DagNode or zapi.DgNode
        :param rename: Rename metanode to use curve
        :type rename: bool
        :return:
        :rtype:
        """

        # convert to list
        if type(sourceObjects) is not list:
            sourceObjects = [sourceObjects]
        # Convert to zapi
        if type(sourceObjects[0]) is str:
            sourceObjects = list(zapi.nodesByNames(sourceObjects))
        # Convert to zapi
        if type(curve) is str:
            curve = zapi.nodeByName(curve)
        ret = duplicatealongcurve.DuplicateAlongCurveCore.duplicateAlongCurve(sourceObjects, curve,
                                                                              multiplyObjects=self.multiple.value(),
                                                                              spacingStart=self.startPosition.value(),
                                                                              spacingEnd=self.endPosition.value(),
                                                                              rotationStart=self.startRotation.value(),
                                                                              rotationEnd=self.endRotation.value(),
                                                                              scaleStart=self.startScale.value(),
                                                                              scaleEnd=self.endScale.value(),
                                                                              instance=self.instanced.value(),
                                                                              follow=self.followAxis.value(),
                                                                              fractionMode=self.fractionMode.value(),
                                                                              upAxis=self.upAxis.value(),
                                                                              followAxis=self.followAxis.value(),
                                                                              group=self.groupAllGeo.value(),
                                                                              inverseFront=self.inverseFollow.value(),
                                                                              inverseUp=self.inverseUp.value(),
                                                                              spacingWeight=self.weight.value(),
                                                                              weightPosition=self.weightPosition.value(),
                                                                              weightRotation=self.weightRotation.value(),
                                                                              weightScale=self.weightScale.value(),
                                                                              worldUpType="objectrotation",
                                                                              autoWorldUpV=True,
                                                                              message=True)

        self.connectAttributes(**ret)
        if rename:
            name = self.generateUniqueName(curve.fullPathName()+"_")
            self.rename(name)



        return ret

    def rebuild(self, selectLast=True):
        """ Rebuild curve based

        :param selectLast: Selects the last object after rebuild
        :type selectLast: bool
        :return: Returns last selected object if it is related to the metanode
        :rtype:
        """
        lastSelectedObject = list(zapi.selected())[-1]
        lastSelectedObjectName = lastSelectedObject.fullPathName()
        selIndex = self.objectIndex(lastSelectedObject)

        # Get source objects
        try:  # sourceObjects may be deleted
            sourceObjects = [o.value() for o in self.sourceObjects]
        except ValueError:
            om2.MGlobal.displayWarning("No Original Object Found:  Source Objects might have been deleted and "
                                       "cannot rebuild.  Metanode: {}".format(self))
            return

        self.deleteRig(keepMeta=True)
        self.build(sourceObjects, self.curve.value())

        # select last index if there's any
        if selIndex:
            if selIndex < len(self.objectList):
                lastSelectedObjectName = self.objectList[selIndex].value().fullPathName()
            else:  # select the last one if its larger than whats available
                lastSelectedObjectName = self.objectList[-1].value().fullPathName()

        # Last selected
        if selectLast:
            cmds.select(lastSelectedObjectName)


        return zapi.nodeByName(lastSelectedObjectName)

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

    def setOriginalObjectVis(self, visibility):
        """Show or hide the visibility of the original object

        :param visibility: True is show hide is False
        :type visibility: bool
        """
        try:
            sourceObjects = [o.value().fullPathName() for o in self.sourceObjects]
        except ValueError:
            om2.MGlobal.displayWarning("No original objects found to be shown/hidden, might have been deleted. "
                                       "Metanode: {}".format(self))
            return

        if self.sourceGroup.value():  # also may have been deleted
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

    def deleteRig(self, keepMeta=False, mod=None):
        """ Delete the rig

        :return:
        :rtype:
        """
        if not self.exists():
            return

        rigGroup = self.rigGroup.value()

        curve = self.sourceNode(self.curve)
        if curve is not None and rigGroup is not None:
            curve.setParent(rigGroup.parent())

        if rigGroup is not None:
            [s.value().setParent(rigGroup.parent()) for s in self.sourceObjects]
            rigGroup.delete()
        else:
            # Delete the objects instead
            [obj.source().node().delete() for obj in self.objectList if obj.source()]
            self.upVGroup.source().node().delete() if self.upVGroup.source() else None

        [m.source().node().delete() for m in self.motionPaths if m.source()]

        self.sourceGroup.source().node().delete() if self.sourceGroup.source() else None
        cmds.showHidden([o.value().fullPathName() for o in self.sourceObjects])

        if not keepMeta:
            self.delete()

    def updateCurve(self, mod=None):
        """ Update curve

        :param mod:
        :type mod: om2.MDGModifier
        :return:
        :rtype:
        """
        posList, rotList, sclList = splines.calculateRangeSpacing(self.weight.value(), len(self.objectList),
                                                                  self.startPosition.value(),
                                                                  self.endPosition.value(),
                                                                  self.startRotation.value(),
                                                                  self.endRotation.value(),
                                                                  self.startScale.value(), self.endScale.value(),
                                                                  self.weightPosition.value(),
                                                                  self.weightRotation.value(),
                                                                  self.weightScale.value())
        origScale = self.sourceObjects[0].value().attribute("scale")
        resetObjRot = False
        useCmds = False
        for i, mp in enumerate(self.motionPaths):
            motionPath = mp.value()
            mpFullName = motionPath.fullPathName()
            if not useCmds:
                motionPath.setAttribute("fractionMode", self.fractionMode.value(), mod=mod)
                uValue = posList[i]
                if self.fractionMode.value():
                    uValue = min(1, uValue)
                motionPath.setAttribute("uValue", uValue, mod=mod, apply=False)
                motionPath.setAttribute("frontTwist", math.radians(rotList[i][0]), mod=mod, apply=False)
                motionPath.setAttribute("upTwist", math.radians(rotList[i][1]), mod=mod, apply=False)
                motionPath.setAttribute("sideTwist", math.radians(rotList[i][2]), mod=mod, apply=False)
                motionPath.setAttribute("frontAxis", AXIS_INDEX[self.followAxis.value()], mod=mod, apply=False)
                motionPath.setAttribute("upAxis", AXIS_INDEX[self.upAxis.value()], mod=mod, apply=False)
                motionPath.setAttribute("inverseUp", self.inverseUp.value(), mod=mod, apply=False)
                motionPath.setAttribute("inverseFront", self.inverseFollow.value(), mod=mod, apply=False)
                motionPath.setAttribute("follow", self.followRotation.value(), mod=mod, apply=False)

            else:
                cmds.setAttr("{}.fractionMode".format(mpFullName), self.fractionMode.value())
                uValue = posList[i]
                if self.fractionMode.value():
                    uValue = min(1, uValue)
                cmds.setAttr("{}.uValue".format(mpFullName), uValue)
                cmds.setAttr("{}.frontTwist".format(mpFullName), rotList[i][0])
                cmds.setAttr("{}.upTwist".format(mpFullName), rotList[i][1])
                cmds.setAttr("{}.sideTwist".format(mpFullName), rotList[i][2])
                cmds.setAttr("{}.frontAxis".format(mpFullName), AXIS_INDEX[self.followAxis.value()])
                cmds.setAttr("{}.upAxis".format(mpFullName), AXIS_INDEX[self.upAxis.value()])
                cmds.setAttr("{}.inverseUp".format(mpFullName), self.inverseUp.value())
                cmds.setAttr("{}.inverseFront".format(mpFullName), self.inverseFollow.value())
                cmds.setAttr("{}.follow".format(mpFullName), self.followRotation.value())

            if not self.followRotation.value():
                resetObjRot = True

        for i, o in enumerate(self.objectList):
            obj = o.value()
            if mod:
                mod.pythonCommandToExecute("from maya import cmds;cmds.scale({}, {}, {}, \"{}\", absolute=True)".format(sclList[i][0],
                                                                                              sclList[i][1],
                                                                                              sclList[i][2],
                                                                                              obj.fullPathName()))
            else:
                cmds.scale(sclList[i][0], sclList[i][1], sclList[i][2], obj.fullPathName(), absolute=True)
            if resetObjRot:  # Resets the object rotation to use the original source objects rotations
                # todo: work with multiple source objects
                rot = ['{}rad'.format(r.asFloat()) for r in self.sourceObjects[0].value().attribute("rotate")]
                if mod:
                    mod.pythonCommandToExecute("from maya import cmds;cmds.rotate({}, {}, {}, \"{}\", absolute=True)".format(rot[0],
                                                                                                   rot[1],
                                                                                                   rot[2],
                                                                                                   obj.fullPathName()))
                else:
                    cmds.rotate(rot[0], rot[1], rot[2], obj.fullPathName(), absolute=True)

    @classmethod
    def upFollowAxis(cls, upAxis, followAxis):
        """Helper function for extracting upAxis, upAxisInvert, followAxis, followAxisInvert from the UI combobox's

        Takes the AXIS_LIST and returns the expected variables
        """
        upAxisInvert = False
        followAxisInvert = False

        upAxis = AXIS_LIST[upAxis].lower()
        followAxis = AXIS_LIST[followAxis].lower()

        plusMinusUp = upAxis[0]
        plusMinusFollow = followAxis[0]

        if plusMinusUp == "-":
            upAxisInvert = True
        if plusMinusFollow == "-":
            followAxisInvert = True

        upAxis = upAxis[1]
        followAxis = followAxis[1]

        return upAxis, upAxisInvert, followAxis, followAxisInvert

    def getMetaAttributes(self):
        """ Get the Meta attributes to populate the ui

        :return:
        :rtype:
        """
        return {
            "multiple": self.multiple.asInt(),
            "instanced": self.instanced.asBool(),
            "upAxis": self.upAxis.asString(),
            "followAxis": self.followAxis.asString(),
            "inverseUp": self.inverseUp.asBool(),
            "inverseFollow": self.inverseFollow.asBool(),
            "startPosition": self.startPosition.asFloat(),
            "endPosition": self.endPosition.asFloat(),
            "startRotation": [self.startRotation[i].asFloat() for i in range(3)],
            "endRotation": [self.endRotation[i].asFloat() for i in range(3)],
            "startScale": [self.startScale[i].asFloat() for i in range(3)],
            "endScale": [self.endScale[i].asFloat() for i in range(3)],
            "weight": self.weight.asFloat(),
            "weightPosition": self.weightPosition.asBool(),
            "weightRotation": self.weightRotation.asBool(),
            "weightScale": self.weightScale.asBool(),
            "followRotation": self.followRotation.value(),
            "groupAllGeo": self.groupAllGeo.value(),
            "fractionMode": self.fractionMode.value(),
            "origObjVis": self.origObjVisiblity(),

        }
