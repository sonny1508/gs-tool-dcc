import copy
import math

from collections import namedtuple

from zoo.libs.hive.base.definition import definitionnodes
from zoo.libs.hive.base.serialization import dggraph
from zoo.libs.hive import constants
from zoo.libs.hive.base import hivenodes, definition, basesubsystem
from zoo.libs.hive.base.util import componentutils, twistutils
from zoo.libs.maya import zapi
from zoo.libs.maya.api import curves
from zoo.libs.maya.rig import align, skeletonutils
from zoo.libs.maya.utils import mayamath, mayaenv
from zoo.libs.utils import zoomath, general

Bendy3PointPrimarySrts = namedtuple("Bendy3PointPrimarySrts", ["start", "mid", "end"])

# static animation attributes
ANIM_ROUND_ATTRS = [
    {
        "name": "______",
        "value": 0,
        "enums": ["BENDY"],
        "keyable": False,
        "locked": True,
        "channelBox": True,
        "Type": zapi.attrtypes.kMFnkEnumAttribute,
    },
    {
        "name": "roundnessAuto",
        "value": 0,
        "default": 0,
        "min": 0,
        "max": 1,
        "channelBox": False,
        "keyable": True,
        "locked": False,
    },
    {
        "name": "roundnessMaintainLength",
        "value": 1,
        "default": 1,
        "min": 0,
        "max": 1,
        "channelBox": False,
        "keyable": True,
        "locked": False,
    },
    {
        "name": "roundnessMaxAngle",
        "value": 120.0,
        "default": 120.0,
        "min": 0.001,
        "max": 180.0,
        "channelBox": False,
        "keyable": True,
        "locked": False,
    },
    {
        "name": "_______",
        "value": 0,
        "enums": ["TANGENTS"],
        "keyable": False,
        "locked": True,
        "channelBox": True,
        "Type": zapi.attrtypes.kMFnkEnumAttribute,
    },
]
# static visibility attributes
RIG_VIS_ATTRS = [
    {
        "channelBox": True,
        "default": False,
        "keyable": False,
        "locked": False,
        "name": "showCurveTemplate",
        "Type": zapi.attrtypes.kMFnNumericBoolean,
        "value": False,
    },
    {
        "channelBox": True,
        "default": False,
        "keyable": False,
        "locked": False,
        "name": "primaryBendyVis",
        "Type": zapi.attrtypes.kMFnNumericBoolean,
        "value": False,
    },
    {
        "channelBox": True,
        "default": False,
        "keyable": False,
        "locked": False,
        "name": "secondaryBendyVis",
        "Type": zapi.attrtypes.kMFnNumericBoolean,
        "value": False,
    },
    {
        "channelBox": True,
        "default": False,
        "keyable": False,
        "locked": False,
        "name": "tertiaryBendyVis",
        "Type": zapi.attrtypes.kMFnNumericBoolean,
        "value": False,
    },
]
# tangent control color
BENDY_TANGENT_CTRL_COLOR = (1.0, 0.563, 0.375)
# primary bendy control color i.e. elbow bendy
BENDY_CTRL_COLOR = (0.950, 0.385, 0.142)
BENDY_SEGMENT_MID_POS_MULTIPLIER = zapi.Vector(1.4, 1.4, 1.4)
# distance multiplier of the segments length which becomes the auto roundness target offset.
BENDY_AUTO_DISTANCE_MULTIPLIER = 0.4
ROUNDNESS_ANGLE_FRACTION = 0.025


class BendySubSystem(basesubsystem.BaseSubsystem):
    """The BendySubSystem class is a helper class for the creation and management of bendy segments in a rig system.

    :param component: The component that the bendy subsystem is associated with
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param primaryIds: list of primary guide ids for the bendy subsystem to build on top of.
    :type primaryIds: list[str]
    :param segmentPrefixes: list of prefixes of the segments.
    :type segmentPrefixes: list[str]
    :param segmentCounts: list of joint counts of the segments in the segment groups.
    :type segmentCounts: list[int]
    :todo: volume preservation
    """

    settingSwitchName = "hasBendy"

    class SetupRigState(object):
        """Internal use only , Used for storing build state between internal build methods to help
        keep things tidy.
        """

        def __init__(self):
            self.controlPanel = None  # type: hivenodes.SettingsNode or None
            self.rigLayer = None  # type: hivenodes.HiveRigLayer  or None
            self.guideLayerDef = None  # type: hivenodes.HiveGuideLayer  or None
            self.curves = []  # type: list[zapi.NurbsCurve]
            self.guideDefs = {}  # type: dict[str, definitionnodes.GuideDefinition]
            self.createdCtrls = {}  # type: dict[str, hivenodes.ControlNode]
            self.primarySrtOutputs = []  # type: list[zapi.DagNode]
            # per primary bendy ctrl i.e. elbow tangent graphs, split between `positionGraphs` and `rotationGraphs`
            self.tangentGraphs = []  # type: list[dggraph.NamedDGGraph]
            # per segment mid control dgGraph
            self.segmentMidGraphs = (
                []
            )  # type: list[dggraph.NamedDGGraph] # primaryMidBendyCtrls graph
            # per primary bendy ctrl i.e. elbow bendy ctrl
            self.primaryBendyCtrlGraphs = (
                []
            )  # type: list[tuple[dggraph.NamedDGGraph, Bendy3PointPrimarySrts]]
            self.upVectors = []
            # determines if the mid segment ctrl translation directions needs to be inverted for auto roundness
            self.midSegmentCtrlMultiplier = []
            self.componentName = ""
            self.componentSide = ""
            self.parentNode = None  # type: zapi.DagNode  or None
            self.namingConfig = None  # :class:`naming.NamingManager`  or None
            self.constantsNode = None  # type: hivenodes.SettingsNode  or None
            mayaVersion2023 = mayaenv.mayaVersion() >= 2023
            # contains all guide align settings
            self.guideAlignmentSettings = {}  # type: dict[str, dict[str, zapi.Vector]]
            self.primaryBendyCtrlGraphId = (
                "primaryMidBendyCtrls"
                if mayaVersion2023
                else "primaryMidBendyCtrlsPre2023"
            )
            self.segmentMidCtrlGraphId = "primaryMidBendyRoundness"
            # primary bendy In/Out tangent graph
            self.tangentMidGraphId = (
                "bendyTangent" if mayaVersion2023 else "bendyTangentPre2023"
            )
            # the start/end joint chain tangent graph.
            self.startEndTangentGraphRotationId = (
                "bendySegmentEndTangentRot"
                if mayaVersion2023
                else "bendySegmentEndTangentRotPre2023"
            )
            self.guideAlignGraphId = (
                "twistGuideAlign" if mayaVersion2023 else "twistGuideAlignPre2023"
            )
            self.guideAlignGraphName = "twistGuideAlign"  # used for graph instances
            self.twistMotionGraphId = "bendyMotionPath"
            self.angleBetweenGraphId = "angleBetweenBlend"
            self.midSegmentPointRoundnessGraphId = (
                "midSegmentPointRoundness"
                if mayaVersion2023
                else "midSegmentPointRoundnessPre2023"
            )

    def __init__(
        self,
        component,
        primaryIds,
        segmentPrefixes,
        segmentCounts,
        animAttributesInsertAfterName,
        visibilityAttributesInsertAfterName,
    ):
        super(BendySubSystem, self).__init__(component)
        self.primaryIds = primaryIds
        # [[segmentIdOne], [segmentIdTwo]]
        self.segmentTwistPrefixes = segmentPrefixes
        self.segmentTwistCounts = segmentCounts
        self.segmentTwistIds = []
        self.segmentTwistOffsetIds = []
        self.animAttributesInsertAfterName = animAttributesInsertAfterName
        self.visibilityAttributesInsertAfterName = visibilityAttributesInsertAfterName
        self.rigState = (
            BendySubSystem.SetupRigState()
        )  # type: BendySubSystem.SetupRigState
        for index, count in enumerate(segmentCounts):
            prefix = segmentPrefixes[index]
            segmentIds = [prefix + str(i).zfill(2) for i in range(count)]
            self.segmentTwistIds.append(segmentIds)
            self.segmentTwistOffsetIds.append("{}Offset".format(prefix))

    def active(self):
        """Whether this subsystem should build,align etc. This is based on the required "hasBendy"
        setting.

        :rtype: bool
        """
        return self.component.definition.guideLayer.guideSetting(
            self.settingSwitchName
        ).value

    def segmentMidControlIdByIndex(self, number):
        """Returns the Control/guide id for the segment mid control.

        :param number: The index number of the segment.
        :type number: int
        :return: The ID of the mid control for the segment.
        :rtype: str
        """
        return "bendyMid{}".format(str(number).zfill(2))

    def tangentInControlIdByIndex(self, number):
        """Returns the In tangent control/guide id for the provided number

        :param number: The index of the control.
        :type number: int
        :return: The ID of the tangent control with the given index.
        :rtype: str
        """
        return "tangent{}In".format(str(number).zfill(2))

    def tangentOutControlIdByIndex(self, number):
        """Returns the Out tangent control/guide id for the provided number

        :param number: The index of the control.
        :type number: int
        :return: The ID of the tangent control with the given index.
        :rtype: str
        """
        return "tangent{}Out".format(str(number).zfill(2))

    def primaryBendyControlIdByIndex(self, number):
        """Returns the control/guide id for the primary bendy control for the provided number.

        This id corresponds to the the controls where the elbow/knee would be.

        :param number: The index of the bendy control.
        :type number: int
        :return: The ID of the primary bendy control.
        :rtype: str
        """
        return "bendy{}".format(str(number).zfill(2))

    def controlIds(self, includePrimary=True):
        for index, primary in enumerate(self.primaryIds[:-1]):
            if index == 0:
                yield self.tangentOutControlIdByIndex(index)
                yield self.segmentMidControlIdByIndex(index)
                yield self.tangentInControlIdByIndex(index + 1)
            else:
                if includePrimary:
                    yield self.primaryBendyControlIdByIndex(index)
                yield self.tangentOutControlIdByIndex(index)
                yield self.segmentMidControlIdByIndex(index)
                yield self.tangentInControlIdByIndex(index + 1)

    def curvePointControlIds(self):
        return (
            [self.primaryIds[0]]
            + [i for i in self.controlIds() if "bendyMid" not in i]
            + [self.primaryIds[-1]]
        )

    def roundnessMultiplierSettingName(self, bendyId):
        """Get the setting name for the roundness multiplier of a primary bendy control

        :param bendyId: The ID of the bendy node.
        :type bendyId: str
        :return: The setting name for the roundness multiplier.
        :rtype: str
        """
        return bendyId + "RoundnessMultiplier"

    def deleteGuides(self):
        layer = self.component.definition.guideLayer
        ctrlIds = list(self.controlIds())

        sceneLayer = self.component.guideLayer()
        graphRegistry = self.component.configuration.graphRegistry()

        for ctrlId in ctrlIds:
            sceneLayer.deleteNamedGraph(
                self.rigState.guideAlignGraphName + ctrlId, graphRegistry
            )
        layer.deleteSettings(["{}Position".format(ctrlId) for ctrlId in ctrlIds])
        layer.deleteGuides(*ctrlIds)

    def preAlignGuides(self):
        if not self.active():
            return [], []
        layer = self.component.guideLayer()
        constructedPlane = componentutils.worldUpVectorAsPlaneLegacy(
            layer.guide(self.primaryIds[0])
        )

        normal = constructedPlane.normal()
        matrices, guides = [], []

        for index, primaryId in enumerate(self.primaryIds[1:-1]):
            primaryGuide = layer.guide(primaryId)
            bendyId = self.primaryBendyControlIdByIndex(index + 1)
            bendyGuide = layer.guide(bendyId)
            if not bendyGuide.attribute(constants.AUTOALIGN_ATTR).value():
                continue
            upVector = bendyGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value()
            aimVector = bendyGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value()
            aimGuide = layer.guide(self.primaryIds[index + 2])
            negate = -1 if mayamath.isVectorNegative(upVector) else 1
            rot = mayamath.lookAt(
                primaryGuide.translation(space=zapi.kWorldSpace),
                aimGuide.translation(space=zapi.kWorldSpace),
                aimVector=aimVector,
                upVector=upVector * negate,
                worldUpVector=normal,
            )
            transform = bendyGuide.transformationMatrix(space=zapi.kWorldSpace)
            transform.setRotation(rot)
            transform.setTranslation(
                primaryGuide.translation(space=zapi.kWorldSpace), zapi.kWorldSpace
            )

            guides.append(layer.guide(bendyId))
            matrices.append(transform.asMatrix())
        return guides, matrices

    def preUpdateGuideSettings(self, settings):
        if not settings.get("hasBendy", True):
            if not self.active():
                return False, False
            return False, False
        guideLayerDef = self.component.definition.guideLayer
        hasBendy = settings.get(
            self.settingSwitchName,
            guideLayerDef.guideSetting(self.settingSwitchName).value,
        )
        requiresRebuild = self.settingSwitchName in settings
        if not hasBendy:
            self.deleteGuides()

        return requiresRebuild, requiresRebuild

    def preSetupGuide(self):
        if not self.active():
            return

        compDef = self.component.definition
        guideLayerDef = compDef.guideLayer  # type: definition.GuideLayerDefinition

        primaryGuides = guideLayerDef.findGuides(*self.primaryIds)
        naming = self.component.namingConfiguration()
        compName, compSide = self.component.name(), self.component.side()
        # default shape transform from the lib requires a 90 rotation so it points down the chain
        shapeTransform = zapi.TransformationMatrix()
        shapeTransform.setRotation(zapi.EulerRotation(0, 0, math.pi * 0.5))
        shapeTransform.setScale((2.2, 2.2, 2.2), zapi.kWorldSpace)
        shapeTransform = shapeTransform.asMatrix()

        for index, primary in enumerate(primaryGuides[1:-1]):
            bendyCtrlId = self.primaryBendyControlIdByIndex(index + 1)
            upVector = primary.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value
            aimVector = primary.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value
            if sum(aimVector) < 0:
                aimVector *= -1
            targetGuide = guideLayerDef.guide(self.primaryIds[index + 2])
            rot = mayamath.lookAt(
                primary.translate, targetGuide.translate, aimVector, upVector
            )
            transform = primary.transformationMatrix()
            transform.setRotation(rot)
            shapeTransformWorld = zapi.TransformationMatrix(
                shapeTransform * primary.worldMatrix
            )
            componentutils.createGuideLocator(
                guideLayerDef,
                naming,
                "twistControlName",
                {"componentName": compName, "side": compSide, "id": bendyCtrlId},
                translate=list(transform.translation(zapi.kWorldSpace)),
                rotate=list(transform.rotation(asQuaternion=True)),
                scale=list(transform.scale(zapi.kWorldSpace)),
                id=bendyCtrlId,
                parent=primary.id,
                shape="square_bev",
                color=BENDY_CTRL_COLOR,
                shapeTransform={
                    "translate": list(
                        shapeTransformWorld.translation(zapi.kWorldSpace)
                    ),
                    "rotate": list(shapeTransformWorld.rotation(asQuaternion=True)),
                    "scale": list(shapeTransformWorld.scale(zapi.kWorldSpace)),
                },
                attributes=[
                    {"name": "visibility", "value": False, "locked": True},
                    {
                        "name": constants.AUTOALIGNAIMVECTOR_ATTR,
                        "Type": zapi.attrtypes.kMFnNumeric3Double,
                        "value": list(aimVector),
                    },
                    {
                        "name": constants.AUTOALIGNUPVECTOR_ATTR,
                        "Type": zapi.attrtypes.kMFnNumeric3Double,
                        "value": list(upVector),
                    },
                    {
                        "name": constants.MIRROR_BEHAVIOUR_ATTR,
                        "Type": zapi.attrtypes.kMFnkEnumAttribute,
                        "value": constants.MIRROR_BEHAVIOURS_TYPES.index("Relative"),
                    },
                ],
            )
            # now create the fraction attribute setting
            setting = definition.AttributeDefinition(
                name=self.roundnessMultiplierSettingName(bendyCtrlId),
                Type=zapi.attrtypes.kMFnNumericFloat,
                value=ROUNDNESS_ANGLE_FRACTION,
                default=ROUNDNESS_ANGLE_FRACTION,
                keyable=False,
                channelBox=True,
            )

            guideLayerDef.addGuideSetting(setting)
        # for each segment generate the mid ctrls, outTangent and inTangent
        for index, segment in enumerate(self.segmentTwistIds):
            self._createSegmentGuides(
                guideLayerDef, primaryGuides, naming, compName, compSide, index
            )

    def setupGuide(self):
        if not self.active():
            return
        guideLayer = self.component.guideLayer()
        primaryGuides = guideLayer.findGuides(*self.primaryIds)
        graph = self.component.configuration.graphRegistry().graph(
            self.rigState.guideAlignGraphId
        )
        # worldUpVectorGuide = guideLayer.guide("worldUpVec")
        settingsNode = guideLayer.guideSettings()
        graphRegistry = self.component.configuration.graphRegistry()
        # force the primary bendy guides to have the visibility off
        for index, primaryId in enumerate(self.primaryIds[1:-1]):
            bendyCtrlId = self.primaryBendyControlIdByIndex(index + 1)
            visAttr = guideLayer.guide(bendyCtrlId).visibility
            visAttr.set(False)
            visAttr.lock(True)

        for index, twistId in enumerate(self.segmentTwistIds):
            bendyCtrlId = self.segmentMidControlIdByIndex(index)
            tangentOutId = self.tangentOutControlIdByIndex(index)
            tangentInId = self.tangentInControlIdByIndex(index + 1)
            guideLayer.deleteNamedGraph(graph.name + tangentInId, graphRegistry)
            guideLayer.deleteNamedGraph(graph.name + bendyCtrlId, graphRegistry)
            guideLayer.deleteNamedGraph(graph.name + tangentOutId, graphRegistry)

        for index, segmentIds in enumerate(self.segmentTwistIds):
            bendyCtrlId = self.segmentMidControlIdByIndex(index)
            tangentOutId = self.tangentOutControlIdByIndex(index)
            tangentInId = self.tangentInControlIdByIndex(index + 1)
            guides = guideLayer.findGuides(tangentOutId, bendyCtrlId, tangentInId)
            tangentInPoint, tangentOutPoint = (
                tangentInId + "Position",
                tangentOutId + "Position",
            )
            midPoint = bendyCtrlId + "Position"
            startGuide, endGuide = primaryGuides[index], primaryGuides[index + 1]
            index = 0
            for guide, blendFactor, aimTarget, minMax in zip(
                guides,
                (tangentOutPoint, midPoint, tangentInPoint),
                (endGuide, endGuide, endGuide),
                ((0.0, 0.5), (0.0, 1.0), (0.5, 1.0)),
            ):
                guide.resetTransform(scale=False)
                graphInstance = copy.copy(graph)
                graphInstance.name += guide.id()
                sceneGraph = self.createGraph(guideLayer, graphInstance)
                sceneGraph.connectToInput(
                    "aimVector", guide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR)
                )
                sceneGraph.connectToInput(
                    "upVector", guide.attribute(constants.AUTOALIGNUPVECTOR_ATTR)
                )
                sceneGraph.connectToInput(
                    "upVectorX", guide.attribute(constants.AUTOALIGNUPVECTOR_ATTR + "X")
                )
                sceneGraph.connectToInput(
                    "upVectorY", guide.attribute(constants.AUTOALIGNUPVECTOR_ATTR + "Y")
                )
                sceneGraph.connectToInput(
                    "upVectorZ", guide.attribute(constants.AUTOALIGNUPVECTOR_ATTR + "Z")
                )
                sceneGraph.connectToInput(
                    "positionBlend", settingsNode.attribute(blendFactor)
                )
                sceneGraph.setInputAttr("blendTranslate", 1.0)
                sceneGraph.setInputAttr("blendRotate", 0.0)
                sceneGraph.setInputAttr("blendScale", 0.0)
                sceneGraph.setInputAttr("blendOutputMin", minMax[0])
                sceneGraph.setInputAttr("blendOutputMax", minMax[1])
                sceneGraph.setInputAttr(
                    "worldUpBasisMultiplier", zapi.Vector(1.0, 1.0, 1.0) if index !=0 else zapi.Vector(-1.0, -1.0, -1.0)
                )
                sceneGraph.connectToInput(
                    "aimTargetMtx", aimTarget.attribute("worldMatrix")[0]
                )
                sceneGraph.connectToInput(
                    "inputMtx", startGuide.attribute("worldMatrix")[0]
                )
                sceneGraph.connectToInput(
                    "targetInputMtx", aimTarget.attribute("worldMatrix")[0]
                )
                sceneGraph.connectToInput(
                    "upVectorParentMtx", startGuide.worldMatrixPlug()
                )
                sceneGraph.connectToInput(
                    "upVectorTargetMtx", startGuide.attribute("worldMatrix")[0]
                )
                sceneGraph.connectToInput(
                    "parentInverseMtx",
                    guide.parent().attribute("worldInverseMatrix")[0],
                )
                sceneGraph.setInputAttr("inputPickMatScale", True)
                sceneGraph.setInputAttr("targetPickMatScale", False)
                sceneGraph.connectFromOutput("outputMatrix", [guide.offsetParentMatrix])
                guide.setLockStateOnAttributes(
                    zapi.localRotateAttrs + zapi.localTranslateAttrs, True
                )  # enforce lock state
                index += 1

    def _createSegmentGuides(
        self, guideLayerDef, guides, namingConfig, compName, compSide, index
    ):
        """Creation method for per segment guide definitions.

        :param guideLayerDef: The component guide layer Definition instance.
        :type guideLayerDef: :class:`api.GuideLayerDefinition`
        :param guides: The full list of primary guides for the component. Used for position and aim vectors reference.
        :type guides: list[:class:`api.GuideDefinition`]
        :param namingConfig: The component naming configuration
        :type namingConfig:
        :param compName: The component name
        :type compName: str
        :param compSide: The component side
        :type compSide: str
        :param index: The segment index
        :type index: int
        """
        bendyCtrlId = self.segmentMidControlIdByIndex(index)
        tangentOutId = self.tangentOutControlIdByIndex(index)
        tangentInId = self.tangentInControlIdByIndex(index + 1)
        startGuide, endGuide = guides[index], guides[index + 1]
        # compute the positions for each guide
        tangentOutPoint = zoomath.lerp(startGuide.translate, endGuide.translate, 0.25)
        midPoint = zoomath.lerp(startGuide.translate, endGuide.translate, 0.5)
        tangentInPoint = zoomath.lerp(startGuide.translate, endGuide.translate, 0.75)

        startAim = startGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value
        startUp = startGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value
        aimPrimary = int(startAim[mayamath.primaryAxisIndexFromVector(startAim)])

        midTransform = startGuide.transformationMatrix()
        midTransform.setTranslation(midPoint, zapi.kWorldSpace)
        midTransform.setScale(startGuide.scale, zapi.kWorldSpace)
        # compute the rotation alignment up vectors
        outTangentAim = startAim if aimPrimary < 0 else startAim * -1
        outTangentUp = startUp * -1
        inTangentAim = startAim * -1 if aimPrimary < 0 else startAim
        inTangentUp = startUp
        outTangentRot = mayamath.lookAt(
            tangentInPoint, endGuide.translate, outTangentAim, outTangentUp
        )
        tangentOutTransform = zapi.TransformationMatrix(midTransform)
        tangentOutTransform.setTranslation(tangentOutPoint, zapi.kWorldSpace)
        tangentOutTransform.setRotation(outTangentRot)

        midMat = midTransform.asMatrix()

        tangentInTransform = zapi.TransformationMatrix(midTransform)
        tangentInTransform.setTranslation(tangentInPoint, zapi.kWorldSpace)
        # default shape transform from the lib requires a 90 rotation so it points down the chain
        shapeTransform = zapi.TransformationMatrix()
        shapeTransform.setRotation(zapi.EulerRotation(0, 0, math.pi * 0.5))
        shapeTransform.setScale((2.2, 2.2, 2.2), zapi.kWorldSpace)
        shapeTransform = shapeTransform.asMatrix()

        for guideId, matrix, aimUp, shape, color in zip(
            (tangentOutId, bendyCtrlId, tangentInId),
            (tangentOutTransform.asMatrix(), midMat, tangentInTransform.asMatrix()),
            (
                (outTangentAim, outTangentUp),
                (inTangentAim, inTangentUp),
                (inTangentAim, inTangentUp),
            ),
            ("square_target", "square_bev", "square_target"),
            (BENDY_TANGENT_CTRL_COLOR, BENDY_CTRL_COLOR, BENDY_TANGENT_CTRL_COLOR),
        ):
            transform = zapi.TransformationMatrix(matrix)
            shapeTransformWorld = zapi.TransformationMatrix(shapeTransform * matrix)
            componentutils.createGuideLocator(
                guideLayerDef,
                namingConfig,
                "twistControlName",
                {"componentName": compName, "side": compSide, "id": guideId},
                id=guideId,
                parent=startGuide.id,
                shape=shape,
                color=color,
                translate=list(transform.translation(zapi.kWorldSpace)),
                rotate=list(transform.rotation(asQuaternion=True)),
                scale=list(transform.scale(zapi.kWorldSpace)),
                shapeTransform={
                    "translate": list(
                        shapeTransformWorld.translation(zapi.kWorldSpace)
                    ),
                    "rotate": list(shapeTransformWorld.rotation(asQuaternion=True)),
                    "scale": list(shapeTransformWorld.scale(zapi.kWorldSpace)),
                },
                attributes=[
                    {
                        "name": constants.AUTOALIGNAIMVECTOR_ATTR,
                        "Type": zapi.attrtypes.kMFnNumeric3Double,
                        "value": list(aimUp[0]),
                    },
                    {
                        "name": constants.AUTOALIGNUPVECTOR_ATTR,
                        "Type": zapi.attrtypes.kMFnNumeric3Double,
                        "value": list(aimUp[1]),
                    },
                    {
                        "name": constants.MIRROR_BEHAVIOUR_ATTR,
                        "Type": zapi.attrtypes.kMFnkEnumAttribute,
                        "value": constants.MIRROR_BEHAVIOURS_TYPES.index("Relative"),
                    },
                ],
            )
            setting = definition.AttributeDefinition(
                name=guideId + "Position",
                Type=zapi.attrtypes.kMFnNumericFloat,
                value=0.5,
                default=0.5,
                min=0.0,
                max=1.0,
                keyable=False,
                channelBox=True,
            )

            guideLayerDef.addGuideSetting(setting)

    def preSetupRig(self, parentNode):
        if not self.active():
            return
        # pre-build anim attributes
        defini = self.component.definition
        rigLayerDef = defini.rigLayer
        bendySettings = list(ANIM_ROUND_ATTRS)

        for index, segment in enumerate(self.segmentTwistIds):
            bendySettings.append(
                {
                    "name": "tangent{}DistOut".format(str(index).zfill(2)),
                    "value": 0.0,
                    "default": 0.0,
                    "channelBox": False,
                    "keyable": True,
                    "locked": False,
                }
            )
            bendySettings.append(
                {
                    "name": "tangent{}DistIn".format(str(index + 1).zfill(2)),
                    "value": 0.0,
                    "default": 0.0,
                    "channelBox": False,
                    "keyable": True,
                    "locked": False,
                }
            )
        bendySettings.append(
            {
                "name": "tangentAutoDist",
                "value": 1,
                "default": 1,
                "min": 0,
                "max": 1,
                "channelBox": False,
                "keyable": True,
                "locked": False,
            }
        )
        rigLayerDef.insertSettings(
            constants.CONTROL_PANEL_TYPE,
            rigLayerDef.settingIndex("controlPanel", self.animAttributesInsertAfterName)
            + 1,
            bendySettings,
        )

        rigLayerDef.insertSettings(
            constants.CONTROL_PANEL_TYPE,
            rigLayerDef.settingIndex(
                constants.CONTROL_PANEL_TYPE, self.visibilityAttributesInsertAfterName
            )
            + 1,
            RIG_VIS_ATTRS,
        )

        # pre build constants
        controlIds = list(self.controlIds())
        settings = []
        for bendyMidId in [i for i in controlIds if "bendyMid" in i]:
            settings.append(
                {
                    "name": "{}LocalTargetOffset".format(bendyMidId),
                    "Type": zapi.attrtypes.kMFnDataMatrix,
                }
            )
        for ctrlId in self.primaryIds:
            settings.append(
                {
                    "name": "{}UpVectorOffset".format(ctrlId),
                    "Type": zapi.attrtypes.kMFnDataMatrix,
                }
            )
        rigLayerDef.addSettings("constants", settings)

    def setupRig(self, parentNode):
        if not self.active():
            return
        compName, compSide = self.component.name(), self.component.side()
        definition = self.component.definition
        guideLayerDef = definition.guideLayer
        layers = self.component.meta.layersById(
            (constants.RIG_LAYER_TYPE, constants.GUIDE_LAYER_TYPE)
        )
        rigLayer = layers[constants.RIG_LAYER_TYPE]  # type: hivenodes.HiveRigLayer
        controlPanel = rigLayer.controlPanel()
        rootTransform = rigLayer.rootTransform()
        constantsNode = rigLayer.settingNode("constants")
        namingConfig = self.component.namingConfiguration()

        # list of ikfkBlend Output transform nodes
        primaryOutputNodes = rigLayer.findTaggedNodes(*self.primaryIds)

        # generate bendy hrc node under rigLayerRoot
        bendyHrc = zapi.createDag(
            namingConfig.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": "bendy",
                    "type": "hrc",
                },
            ),
            "transform",
            parent=rootTransform,
        )
        state = self.rigState
        state.rigLayer = rigLayer
        state.guideLayerDef = guideLayerDef
        state.controlPanel = controlPanel
        state.primarySrtOutputs = primaryOutputNodes
        state.componentName = compName
        state.componentSide = compSide
        state.parentNode = bendyHrc
        state.namingConfig = namingConfig
        state.constantsNode = constantsNode
        state.createdCtrls = {i.id(): i for i in rigLayer.iterControls()}
        # gather all the alignment vectors for easier access and better readability
        for guide in guideLayerDef.iterGuides(includeRoot=False):
            aimVector = guide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value
            upVector = guide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value
            # aimVector *= 1 if behaviour == 0 else -1
            state.guideAlignmentSettings[guide.id] = {
                "upVector": upVector,
                "aimVector": aimVector,
                "upAxisName": mayamath.primaryAxisNameFromVector(upVector),
                "aimAxisName": mayamath.primaryAxisNameFromVector(aimVector),
            }
        self._setupControls(state)
        self._createUpVectors(state)
        self._setupPrimaryBendyCtrls(state)
        self._setupSegmentMidCtrls(state)
        self._setupSegmentMidTangentControls(state)
        self._setupStartEndTangents(state)
        curveNodes = self._setupBendyCurve(state)
        self._setupMotionPath(state, curveNodes)
        self._addGraphNodesToMetaData(state)
        self._lockTransforms(state)

    def _lockTransforms(self, state):
        """
        :type state: :class:`BendySubSystem.SetupRigState`
        """
        for ctrl in state.rigLayer.findControls(*list(self.controlIds())):
            for attr in zapi.localRotateAttrs + zapi.localScaleAttrs:
                ctrl.attribute(attr).lock(True)

    def _addGraphNodesToMetaData(self, state):
        """
        :type state: :class:`BendySubSystem.SetupRigState`
        """
        for graph in state.segmentMidGraphs + state.tangentGraphs:
            state.rigLayer.addExtraNodes(graph.nodes().values())
        for graph, _ in state.primaryBendyCtrlGraphs:
            state.rigLayer.addExtraNodes(graph.nodes().values())

    def _setupMotionPath(self, state, curveNodes):
        """
        :type state: :class:`BendySubSystem.SetupRigState`
        """

        def _createMotionGraphSetup(guide, crvMfn, twistGraphs, twistOffsetWorldMtx):
            guideId = guide.id
            ctrl = state.createdCtrls[guideId]
            srt = ctrl.srt()
            srt.resetTransform()
            aimVector = guide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value
            upVector = guide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value
            _, param = crvMfn.closestPoint(
                zapi.Point(guide.translate), tolerance=0.1, space=zapi.kWorldSpace
            )
            twistOutputGraph = twistGraphs[index]
            attr = twistOutputGraph.outputAttr("outputRotate")
            for i in attr.destinations():
                attr.disconnect(i)
            graphData = copy.copy(motionPathGraph)
            graphData.name += guideId
            sceneGraph = self.createGraph(state.rigLayer, graphData)
            crv.worldSpace[0].connect(sceneGraph.node("motionPath").geometryPath)
            sceneGraph.setInputAttr("motionUValue", param)
            sceneGraph.setInputAttr("motionFractionMode", False)
            sceneGraph.setInputAttr(
                "motionFrontAxis", mayamath.primaryAxisIndexFromVector(aimVector)
            )
            sceneGraph.setInputAttr(
                "motionUpAxis", mayamath.primaryAxisIndexFromVector(upVector)
            )
            sceneGraph.setInputAttr("motionWorldUpType", 2)
            sceneGraph.setInputAttr("motionWorldUpVector", upVector)
            sceneGraph.connectToInput("motionWorldUpMatrix", twistOffsetWorldMtx)
            sceneGraph.connectToInput(
                "motionFrontTwist", twistOutputGraph.outputAttr("outputRotate")
            )
            sceneGraph.connectToInput(
                "parentWorldInvMtx", srt.parent().attribute("worldInverseMatrix")[0]
            )

            invertUp, invertAim = mayamath.isVectorNegative(
                upVector
            ), mayamath.isVectorNegative(aimVector)
            sceneGraph.setInputAttr("motionInverseFront", invertAim)
            sceneGraph.setInputAttr("motionInverseUp", invertUp)
            restPosePlug = twistutils._findGuideInputOffsetTransformElement(
                inputGuideOffsetNode, guideId
            )
            sceneGraph.connectToInput("restPoseLocalMtx", restPosePlug.child(1))
            sceneGraph.connectFromOutput("outputMatrix", [srt.offsetParentMatrix])

        inputGuideOffsetNode = self.component.inputLayer().settingNode(
            constants.INPUT_GUIDE_OFFSET_NODE_NAME
        )
        graphRegistry = self.component.configuration.graphRegistry()
        motionPathGraph = graphRegistry.graph(state.twistMotionGraphId)
        for segmentIndex, segmentIds in enumerate(self.segmentTwistIds):
            crv = curveNodes[segmentIndex].shapes()[0]
            crvMfn = crv.mfn()
            twistOutputGraphs = state.rigLayer.findNamedGraphs(
                graphRegistry, ["twistOffsetCtrlRotation" + i for i in segmentIds]
            )
            twistOffsetWorldMtx = state.createdCtrls[
                self.segmentTwistOffsetIds[segmentIndex]
            ].attribute("worldMatrix")[0]
            # get the twist
            segmentGuides = [state.guideDefs[i] for i in segmentIds]
            for index, guide in enumerate(segmentGuides):
                _createMotionGraphSetup(
                    guide, crvMfn, twistOutputGraphs, twistOffsetWorldMtx
                )
                # todo: create the squash and stretch graph

    def _setupBendyCurve(self, state):
        """
        :type state: :class:`BendySubSystem.SetupRigState`
        """
        # generate bendy curve from control points
        curvePointIds = self.curvePointControlIds()

        segments = mayamath.bezierSegments(curvePointIds)
        extras = []
        curveNodes = []
        for segIndex, segment in enumerate(segments):
            curvePoints = [
                guide.translate for guide in state.guideLayerDef.findGuides(*segment)
            ]
            # generate curve from the ids. primaryid,segmentId,primaryId
            curveNode = zapi.nodeByObject(
                curves.createBezierCurve(
                    state.namingConfig.resolve(
                        "object",
                        {
                            "componentName": state.componentName,
                            "side": state.componentSide,
                            "section": "bendy{}".format(str(segIndex).zfill(2)),
                            "type": "curve",
                        },
                    ),
                    curvePoints,
                )
            )
            curveNode.setParent(state.parentNode)
            curveNodes.append(curveNode)
            extras.append(curveNode)
            visAttr = state.controlPanel.showCurveTemplate
            for shape in curveNode.iterShapes():
                shape.template.set(True)
                visAttr.connect(shape.visibility)
                for i in range(len(curvePoints)):
                    shape.anchorSmoothness[i].set(1)
                    shape.anchorWeighting[i].set(1)

            for index, ctrlId in enumerate(segment):
                control = state.createdCtrls.get(
                    ctrlId, state.rigLayer.taggedNode(ctrlId)
                )
                mtx = zapi.createDG(
                    state.namingConfig.resolve(
                        "object",
                        {
                            "componentName": state.componentName,
                            "side": state.componentSide,
                            "section": "{}outTranslate".format(ctrlId),
                            "type": "decomposeMatrix",
                        },
                    ),
                    "decomposeMatrix",
                )
                control.attribute("worldMatrix")[0].connect(mtx.inputMatrix)
                mtx.outputTranslate.connect(shape.controlPoints[index])
                extras.append(mtx)
        state.rigLayer.addExtraNodes(extras)
        state.curves = curveNodes

        return curveNodes

    def _setupControls(self, state):
        """
        :type state: :class:`BendySubSystem.SetupRigState`
        """
        selectionHighlighting = self.component.configuration.selectionChildHighlighting
        state.guideDefs = {
            guide.id: guide
            for guide in state.guideLayerDef.iterGuides(includeRoot=False)
        }
        ctrls = list(self.controlIds())
        total = len(ctrls)
        for index, ctrlId in enumerate(ctrls):
            guideDef = state.guideLayerDef.guide(ctrlId)
            name = state.namingConfig.resolve(
                "controlName",
                {
                    "componentName": state.componentName,
                    "side": state.componentSide,
                    "system": "bendy",
                    "id": guideDef.id,
                    "type": "control",
                },
            )
            srts = []
            if index != 0 and index != total - 1:
                srts = [{"id": guideDef.id, "name": "_".join([name, "srt"])}]
            ctrl = state.rigLayer.createControl(
                name=name,
                id=guideDef.id,
                translate=guideDef.translate,
                rotate=guideDef.rotate,
                parent=state.parentNode,
                rotateOrder=guideDef.rotateOrder,
                shape=guideDef.shape,
                shapeTransform=guideDef.shapeTransform,
                selectionChildHighlighting=selectionHighlighting,
                srts=srts,
            )
            state.createdCtrls[guideDef.id] = ctrl
            state.guideDefs[guideDef.id] = guideDef

    def _setupPrimaryBendyCtrls(self, state):
        """
        :type state: :class:`BendySubSystem.SetupRigState`
        """
        midBendyGraphDef = self.component.configuration.graphRegistry().graph(
            state.segmentMidCtrlGraphId
        )
        inputGuideOffsetNode = self.component.inputLayer().settingNode(
            constants.INPUT_GUIDE_OFFSET_NODE_NAME
        )

        roundnessMaintainLength = state.controlPanel.attribute(
            "roundnessMaintainLength"
        )
        roundnessAuto = state.controlPanel.attribute("roundnessAuto")
        visibilitySwitch = state.controlPanel.secondaryBendyVis
        # We need to figure out which direction each two segments need to bend.
        # This is so we can change the roundness push direction of each primary bendy ctrl and angle
        # on an animal style quad the lower half would be push towards the pole vector which is the opposite
        # ['upr', 'mid', 'ankle'] ['mid', 'ankle', 'end']
        pointIds = general.chunks(self.primaryIds, 3, overlap=2)

        for index, guideIds in enumerate(pointIds):
            # angle is solved using the basisVector of the mid-guide matrix based on alignment
            alignmentGuide = state.guideDefs[
                self.primaryBendyControlIdByIndex(index + 1)
            ]
            worldMatrix = alignmentGuide.worldMatrix
            basisVectors = mayamath.basisVectorsFromMatrix(worldMatrix)
            aimVec = alignmentGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value
            upVec = alignmentGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value
            alignmentVector = basisVectors[
                mayamath.perpendicularAxisFromAlignVectors(aimVec, upVec)[0]
            ]
            positions = [state.guideDefs[i].translate for i in guideIds]
            hypotenuseVector = skeletonutils.hypotenuseMidPointVector(*positions)

            angle = alignmentVector.angle(hypotenuseVector)
            # when we're greater than 1.0 than the current bendy segments need to be flipped, i.e animal quad
            state.midSegmentCtrlMultiplier.append(-1.0 if angle > 1.0 else 1.0)

        # create all primary mid-bendy ctrls i.e. elbow
        for index, primaryId in enumerate(self.primaryIds[1:-1]):
            bendyCtrlId = self.primaryBendyControlIdByIndex(index + 1)
            bendyUpVectorAxisName = state.guideAlignmentSettings[bendyCtrlId][
                "upAxisName"
            ]
            startSegmentPrimaryOutputSrt = state.primarySrtOutputs[index]
            midPrimaryOutputSrt = state.primarySrtOutputs[index + 1]
            endSegmentPrimaryOutputSrt = state.primarySrtOutputs[index + 2]
            bendyMidCtrl = state.createdCtrls[bendyCtrlId]
            bendyMidCtrlSrt = bendyMidCtrl.srt(0)
            bendyMidCtrlSrt.resetTransform()
            visibilitySwitch.connect(bendyMidCtrlSrt.visibility)

            # drive the ctrl by the mid primary ctrl ie. elbow
            midPrimaryOutputSrtMtx = midPrimaryOutputSrt.attribute("worldMatrix")[0]
            restPosePlug = twistutils._findGuideInputOffsetTransformElement(
                inputGuideOffsetNode, bendyCtrlId
            )
            createInvertRotationOffset(
                state,
                bendyCtrlId,
                restPosePlug.child(1),
                midPrimaryOutputSrtMtx,
                bendyMidCtrlSrt.offsetParentMatrix,
            )

            midGraph = copy.deepcopy(midBendyGraphDef)
            midGraph.name = midBendyGraphDef.name + str(index)
            newGraph = self.createGraph(state.rigLayer, midGraph)
            # connect up decompose matrices
            newGraph.connectToInput(
                "primaryStartSrtWorldMtx",
                startSegmentPrimaryOutputSrt.attribute("worldMatrix")[0],
            )
            newGraph.connectToInput("primaryMidSrtWorldMtx", midPrimaryOutputSrtMtx)
            newGraph.connectToInput(
                "primaryEndSrtWorldMtx",
                endSegmentPrimaryOutputSrt.attribute("worldMatrix")[0],
            )
            newGraph.connectToInput("roundnessMaintainLength", roundnessMaintainLength)
            newGraph.connectToInput("roundnessAuto", roundnessAuto)
            newGraph.connectFromOutput(
                "bendyCtrlLocalOffset", [bendyMidCtrl.offsetParentMatrix]
            )
            newGraph.connectFromOutput(
                "segmentAngleHalf",
                [bendyMidCtrlSrt.attribute("rotate{}".format(bendyUpVectorAxisName))],
            )
            newGraph.node("roundnessMidBlend").input[0].set(0.0)
            newGraph.node("roundnessMidTranslateTotal").input[0].set(0.0)
            # calculate the default angle and cache that to the constants node
            angleBetween = mayamath.angleBetween3Points(
                startSegmentPrimaryOutputSrt.translation(),
                midPrimaryOutputSrt.translation(),
                endSegmentPrimaryOutputSrt.translation(),
            )
            #   first create the angle constants attribute
            angleAttr = state.constantsNode.addAttribute(
                bendyCtrlId + "DefaultAngle",
                Type=zapi.attrtypes.kMFnNumericDouble,
                value=angleBetween,
            )
            newGraph.connectToInput("segmentDefaultAngle", angleAttr)
            userMultiplier = state.guideLayerDef.guideSetting(
                self.roundnessMultiplierSettingName(bendyCtrlId)
            )
            userMultiplier = (
                userMultiplier.value
                if userMultiplier is not None
                else ROUNDNESS_ANGLE_FRACTION
            )
            # if the up vector of the mid is negative, we need to flip the direction that
            # the mid-control will auto rotate and translate for roundness
            angleMultiplier = state.midSegmentCtrlMultiplier[index]

            roundAngleRotHalf = 0.5 * angleMultiplier
            fraction = userMultiplier * angleMultiplier

            newGraph.setInputAttr(
                "roundAngleTranslateFraction",
                fraction,
            )

            newGraph.setInputAttr("roundAngleRotHalf", roundAngleRotHalf)
            state.primaryBendyCtrlGraphs.append(
                (
                    newGraph,
                    Bendy3PointPrimarySrts(
                        startSegmentPrimaryOutputSrt,
                        midPrimaryOutputSrt,
                        endSegmentPrimaryOutputSrt,
                    ),
                )
            )

    def _setupSegmentMidCtrls(self, state):
        """
        :type state: :class:`BendySubSystem.SetupRigState`
        """
        bendyMidCtrls = [i for i in self.controlIds() if "bendyMid" in i]
        # up vectors for each segment which is every second upVector to skip the tangents.
        upVectors = list(range(0, len(state.upVectors), 2))
        # new graphs for 2 segment angle and per sub segment roundness graphs
        # first the angle which is shared
        chainAngleGraphDef = self.component.configuration.graphRegistry().graph(
            state.angleBetweenGraphId
        )
        # now the graph which is use per segment which handles position/rotation
        midPointGraphDef = self.component.configuration.graphRegistry().graph(
            state.midSegmentPointRoundnessGraphId
        )
        # notes
        # roundness requires 2 segments so that the angle between can be calculated for auto roundness
        # The last segment of each segment pair is reused for the next segment ie. quadleg has 3 segment
        # and 2 angle between graphs while a biped arm has 2 segments and 1 angle between graph
        midSegmentCtrlGroups = list(general.chunks(bendyMidCtrls, size=2, overlap=1))

        roundnessAutoAttr = state.controlPanel.attribute("roundnessAuto")
        roundnessMaxAngle = state.controlPanel.attribute("roundnessMaxAngle")
        visibilitySwitch = state.controlPanel.primaryBendyVis
        # unique index for the sub loop graph, unique to full limb
        segmentGraphIndex = 0
        for index, ctrls in enumerate(midSegmentCtrlGroups):
            primaryBendyCtrlId = self.primaryBendyControlIdByIndex(index + 1)
            primaryBendyCtrl = state.createdCtrls[
                primaryBendyCtrlId
            ]  # eg. the knee bendy

            primaryGraph, primaryNodes = state.primaryBendyCtrlGraphs[index]
            primaryBendyCtrlNext = primaryNodes.end
            if index != len(midSegmentCtrlGroups) - 1:
                primaryBendyCtrlNext = state.createdCtrls[
                    self.primaryBendyControlIdByIndex(index + 2)
                ]
            # so create the angle between graph for the 2 segment Section and 2 midPoint graphs
            angleGraph = copy.deepcopy(chainAngleGraphDef)
            angleGraph.name = chainAngleGraphDef.name + str(index)
            angleSceneGraph = self.createGraph(state.rigLayer, angleGraph)
            angleSceneGraph.connectToInput(
                "startMtx", primaryNodes.start.worldMatrixPlug()
            )
            angleSceneGraph.connectToInput("midMtx", primaryBendyCtrl.worldMatrixPlug())
            angleSceneGraph.connectToInput(
                "endMtx", primaryBendyCtrlNext.worldMatrixPlug()
            )
            angleSceneGraph.connectToInput("maxAngle", roundnessMaxAngle)
            angleSceneGraph.connectToInput("blender", roundnessAutoAttr)

            for ctrlIndex, ctrlId in enumerate(ctrls):
                if index != 0 and ctrlIndex == 0:
                    continue
                control = state.rigLayer.control(ctrlId)
                controlSrt = control.srt(0)
                controlSrt.resetTransform()
                primaryStart, primaryEnd = primaryNodes.start, primaryNodes.mid
                # if where the last ctrl just use the primary end
                if ctrlIndex == 0:
                    primaryEnd = primaryBendyCtrl
                else:
                    primaryEnd = primaryBendyCtrlNext
                    primaryStart = primaryBendyCtrl
                _visAttr = control.visibility
                visibilitySwitch.connect(_visAttr)
                _visAttr.hide()
                upVector = state.guideAlignmentSettings[ctrlId]["upVector"]
                aimVector = state.guideAlignmentSettings[ctrlId]["aimVector"]
                axisIndex, isNegative = mayamath.perpendicularAxisFromAlignVectors(
                    aimVector, upVector
                )
                localTargetOffsetConstAttr = state.constantsNode.attribute(
                    "{}LocalTargetOffset".format(ctrlId)
                )

                midPointGraph = copy.deepcopy(midPointGraphDef)
                midPointGraph.name = midPointGraphDef.name + str(segmentGraphIndex)
                midPointSceneGraph = self.createGraph(state.rigLayer, midPointGraph)
                midPointSceneGraph.setInputAttr("blendWeightsDummy", 0.0)
                midPointSceneGraph.setInputAttr("positionBlend", 0.5)

                startMidRotAimMatrix = midPointSceneGraph.node("midSegmentRotation")
                startMidRotAimMatrix.primary.child(0).set(aimVector)  # PrimaryInputAxis
                startMidRotAimMatrix.secondary.child(0).set(
                    upVector
                )  # secondaryInputAxis

                midPointSceneGraph.connectToInput(
                    "startWorldMatrix", primaryStart.worldMatrixPlug()
                )
                midPointSceneGraph.connectToInput(
                    "roundnessLocalOffset", localTargetOffsetConstAttr
                )
                midPointSceneGraph.connectToInput(
                    "endWorldMatrix", primaryEnd.worldMatrixPlug()
                )
                midPointSceneGraph.connectToInput(
                    "offsetBlend", angleSceneGraph.outputAttr("outputAngle")
                )
                midPointSceneGraph.connectFromOutput(
                    "outputRoundnessMtx", [controlSrt.offsetParentMatrix]
                )
                midPointSceneGraph.connectToInput(
                    "upVectorMtx", state.upVectors[upVectors[segmentGraphIndex]]
                )
                state.segmentMidGraphs.append(midPointSceneGraph)
                dist = (
                    primaryEnd.translation() - primaryStart.translation()
                ).length() * BENDY_AUTO_DISTANCE_MULTIPLIER

                vec = (
                    (mayamath.AXIS_VECTOR_BY_IDX[axisIndex] * dist)
                    * state.midSegmentCtrlMultiplier[index]
                    * -1
                )
                transform = zapi.TransformationMatrix()
                transform.setTranslation(vec, zapi.kWorldSpace)
                localTargetOffsetConstAttr.set(transform.asMatrix())
                segmentGraphIndex += 1

    def _createUpVectors(self, state):
        """

        :type state: :class:`BendySubSystem.SetupRigState`
        """
        constantsNode = state.constantsNode

        def calculate(bendyCtrlId, primaryId):
            upVector = state.guideAlignmentSettings[bendyCtrlId]["upVector"]
            upVector = upVector * 10
            offset = zapi.Matrix(
                (
                    1,
                    0,
                    0,
                    0,
                    0,
                    1,
                    0,
                    0,
                    0,
                    0,
                    1,
                    0,
                    upVector[0],
                    upVector[1],
                    upVector[2],
                    1,
                )
            )
            offsetMtx = constantsNode.attribute("{}UpVectorOffset".format(primaryId))
            offsetMtx.set(offset)
            return offsetMtx

        offsetMtx = calculate(self.primaryBendyControlIdByIndex(1), self.primaryIds[0])
        mtx = _createUpVectorMatrix(
            offsetMtx, state.primarySrtOutputs[0].attribute("worldMatrix")[0]
        )
        state.upVectors.append(mtx)
        for index, primaryId in enumerate(self.primaryIds[1:-1]):
            bendyCtrlId = self.primaryBendyControlIdByIndex(index + 1)
            bendyCtrlMtx = state.createdCtrls[bendyCtrlId].attribute("worldMatrix")[0]
            offsetMtx = calculate(bendyCtrlId, primaryId)

            mtx = _createUpVectorSplitMatrix(
                calculate(bendyCtrlId, self.primaryIds[index]),
                state.primarySrtOutputs[index].attribute("worldMatrix")[0],
                bendyCtrlMtx,
            )

            state.upVectors.append(mtx)
            mtx = _createUpVectorMatrix(offsetMtx, bendyCtrlMtx)
            state.upVectors.append(mtx)

        offsetMtx = calculate(
            self.primaryBendyControlIdByIndex(len(self.primaryIds) - 2),
            self.primaryIds[-2],
        )

        mtx = _createUpVectorSplitMatrix(
            offsetMtx,
            state.primarySrtOutputs[-2].attribute("worldMatrix")[0],
            state.primarySrtOutputs[-1].attribute("worldMatrix")[0],
        )

        state.upVectors.append(mtx)

    def _setupSegmentMidTangentControls(self, state):
        """
        :type state: :class:`BendySubSystem.SetupRigState`
        """
        namingConfig = state.namingConfig
        reg = self.component.configuration.graphRegistry()
        bendyTangentPositionGraph = reg.graph(
            state.tangentMidGraphId
        )  # state.tangentGraphPositionName)
        autoBlendAttr = state.controlPanel.attribute("roundnessAuto")
        visibilitySwitch = state.controlPanel.tertiaryBendyVis
        globalTangentIndex = 0
        for index, [_, graph] in enumerate(
            zip(self.primaryIds[1:-1], state.primaryBendyCtrlGraphs)
        ):
            tangentInId = self.tangentInControlIdByIndex(index + 1)
            tangentOutId = self.tangentOutControlIdByIndex(index + 1)
            bendyCtrlId = self.primaryBendyControlIdByIndex(index + 1)
            upVectors = state.upVectors[index + 1], state.upVectors[index + 2]

            startSegMidControl = state.createdCtrls[
                self.segmentMidControlIdByIndex(index)
            ]
            endSegMidControl = state.createdCtrls[
                self.segmentMidControlIdByIndex(index + 1)
            ]
            tangentGuides = state.guideDefs[tangentInId], state.guideDefs[tangentOutId]

            tangentInCtrl, tangentOutCtrl = (
                state.createdCtrls[tangentInId],
                state.createdCtrls[tangentOutId],
            )
            tangentInCtrlSrt, tangentOutCtrlSrt = (
                tangentInCtrl.srt(),
                tangentOutCtrl.srt(),
            )
            visibilitySwitch.connect(tangentInCtrl.visibility)
            visibilitySwitch.connect(tangentOutCtrl.visibility)
            tangentInCtrl.visibility.hide()
            tangentOutCtrl.visibility.hide()

            primaryBendyCtrl = state.createdCtrls[
                bendyCtrlId
            ]  # contains the start, mid, end segment srts
            midPrimaryOut = graph[1].mid
            primaryOutputScaleAttrs = graph[0].outputAttr(
                "primaryStartSrtWorldScale"
            ), graph[0].outputAttr("primaryEndSrtWorldScale")
            tangentInCtrlSrt.resetTransform()
            tangentOutCtrlSrt.resetTransform()

            bendyWorldMtx = primaryBendyCtrl.attribute("worldMatrix")[0]

            # create the srt which will handle auto bendy state, todo: do this in the createControls method
            state.rigLayer.createSrtBuffer(
                tangentInId,
                "_".join([tangentInCtrl.name(includeNamespace=False), "auto", "srt"]),
            )
            state.rigLayer.createSrtBuffer(
                tangentOutId,
                "_".join([tangentOutCtrl.name(includeNamespace=False), "auto", "srt"]),
            )
            # create the worldMatrix network.
            bendyMidTranslateOnly = zapi.createDG(
                namingConfig.resolve(
                    "object",
                    {
                        "componentName": state.componentName,
                        "side": state.componentSide,
                        "section": "{}TranslateOnly".format(bendyCtrlId),
                        "type": "pickMatrix",
                    },
                ),
                "pickMatrix",
            )
            primaryMidTranslateOnly = zapi.createDG(
                namingConfig.resolve(
                    "object",
                    {
                        "componentName": state.componentName,
                        "side": state.componentSide,
                        "section": "{}TranslateOnly".format(
                            midPrimaryOut.name(includeNamespace=False)
                        ),
                        "type": "pickMatrix",
                    },
                ),
                "pickMatrix",
            )
            srtFinalMtx = zapi.createDG(
                namingConfig.resolve(
                    "object",
                    {
                        "componentName": state.componentName,
                        "side": state.componentSide,
                        "section": "bendy",
                        "type": "multMatrix",
                    },
                ),
                "multMatrix",
            )
            # setup the top level srt for the control
            bendyMidTranslateOnly.useRotate.set(False)
            bendyMidTranslateOnly.useScale.set(False)
            bendyMidTranslateOnly.useShear.set(False)
            primaryMidTranslateOnly.useTranslate.set(False)
            primaryMidTranslateOnly.useScale.set(False)
            primaryMidTranslateOnly.useShear.set(False)

            bendyWorldMtx.connect(bendyMidTranslateOnly.inputMatrix)
            bendyWorldMtx.connect(primaryMidTranslateOnly.inputMatrix)
            primaryMidTranslateOnly.outputMatrix.connect(srtFinalMtx.matrixIn[0])
            bendyMidTranslateOnly.outputMatrix.connect(srtFinalMtx.matrixIn[1])
            srtFinalMtx.matrixSum.connect(tangentInCtrlSrt.offsetParentMatrix)
            srtFinalMtx.matrixSum.connect(tangentOutCtrlSrt.offsetParentMatrix)
            invert = mayamath.isVectorNegative(
                state.guideAlignmentSettings[bendyCtrlId]["aimVector"]
            )

            for tangentIndex, [
                tangent,
                tangentName,
                midSegmentControl,
                segmentGraphIndex,
            ] in enumerate(
                zip(
                    (tangentInCtrl, tangentOutCtrl),
                    ("In", "Out"),
                    (startSegMidControl, endSegMidControl),
                    (index, index + 1),
                )
            ):
                primaryBendyGraph = state.segmentMidGraphs[segmentGraphIndex]
                idIndex = str(index + 1).zfill(2)
                tangentGraph = copy.deepcopy(bendyTangentPositionGraph)
                tangentGraph.name = (
                    tangentGraph.name
                    + tangentName
                    + state.componentSide
                    + str(globalTangentIndex)
                )
                tangentGuide = tangentGuides[tangentIndex]
                upVector = state.guideAlignmentSettings[tangentGuide.id]["upVector"]
                aimVector = state.guideAlignmentSettings[tangentGuide.id]["aimVector"]
                distAttr = state.controlPanel.attribute(
                    "tangent{}Dist{}".format(idIndex, tangentName)
                )
                guidePositionDist = state.guideLayerDef.guideSetting(
                    tangent.id() + "Position"
                ).value
                graph = self.createGraph(state.rigLayer, tangentGraph)
                halfDistNode, tangentDistCompNode, target = graph.findNodes(
                    "tangentHalfDist", "tangentDistMtx", "tangentRoundnessAimTarget"
                )
                # in tangent is up the joint chain which is negative of the bendy ctrl position
                targetAimVector = aimVector * -1
                offset = zapi.Matrix(
                    (
                        1,
                        0,
                        0,
                        0,
                        0,
                        1,
                        0,
                        0,
                        0,
                        0,
                        1,
                        0,
                        targetAimVector[0],
                        targetAimVector[1],
                        targetAimVector[2],
                        1,
                    )
                )
                target.setWorldMatrix(offset * primaryBendyCtrl.worldMatrix())
                target.setParent(primaryBendyCtrl)
                graph.setInputAttr("autoRoundessWeightsDummy", 0.0)
                graph.connectToInput("bendyCtrlWorldMtx", bendyWorldMtx)
                graph.connectToInput("scale", primaryOutputScaleAttrs[tangentIndex])
                graph.connectToInput("tangentDistance", distAttr)
                graph.connectToInput("autoRoundnessWeight", autoBlendAttr)
                guidePositionDist *= -1
                targetUpVector = zapi.Vector(upVector) * -1.0

                if not mayamath.isVectorNegative(aimVector):
                    aimVector *= -1
                    targetUpVector = upVector
                graph.setInputAttr("tangentDistanceOffset", guidePositionDist)

                # set the min/max depending on orientations
                minValue, maxValue = zapi.Vector(-99999, -99999, -99999), zapi.Vector(
                    99999, 99999, 99999
                )
                dirVec = zapi.Vector(1.0, 1.0, 1.0)
                dirVec[mayamath.primaryAxisIndexFromVector(aimVector)] = -1
                axisIndex, _ = mayamath.perpendicularAxisFromAlignVectors(
                    aimVector, upVector
                )
                if invert:
                    maxValue[axisIndex] = 0.0
                else:
                    minValue[axisIndex] = 0.0

                graph.setInputAttr("distanceMin", minValue)
                graph.setInputAttr("distanceMax", maxValue)
                graph.setInputAttr(
                    "distanceMultiplier", BENDY_SEGMENT_MID_POS_MULTIPLIER
                )
                graph.setInputAttr("aimVector", aimVector)
                graph.setInputAttr("upVector", upVector)
                graph.setInputAttr("targetUpVector", targetUpVector)
                graph.setInputAttr(
                    "directionVector", dirVec
                )  # flips the translation along the chain
                graph.connectToInput("upVectorWorldMtx", upVectors[tangentIndex])
                graph.connectToInput(
                    "parentInverseMtx", tangent.srt().attribute("worldInverseMatrix")[0]
                )
                graph.connectToInput(
                    "segmentMidWorldMtx",
                    primaryBendyGraph.outputAttr("outputNoRoundnessMtx"),
                )
                graph.connectToInput(
                    "segmentCtrlWorldInvMtx",
                    midSegmentControl.attribute("worldInverseMatrix")[0],
                )
                halfDistNode.output.connect(
                    tangentDistCompNode.attribute(
                        "inputTranslate{}".format(
                            mayamath.primaryAxisNameFromVector(aimVector)
                        )
                    )
                )
                graph.connectFromOutput(
                    "outputLocalOffsetMtx", [tangent.attribute("offsetParentMatrix")]
                )
                graph.connectFromOutput(
                    "outputRotationMtx", [tangent.srt(1).offsetParentMatrix]
                )
                state.tangentGraphs.append(graph)
                globalTangentIndex += 1

    def _setupStartEndTangents(self, state):
        """
        :type state: :class:`BendySubSystem.SetupRigState`
        """
        reg = self.component.configuration.graphRegistry()

        controlIds = list(self.controlIds())
        primaryStartSrt, primaryMidSrt, primaryEndSrt = (
            state.primarySrtOutputs[0],
            state.primarySrtOutputs[-2],
            state.primarySrtOutputs[-1],
        )
        startTangentCtrl, endTangentCtrl = (
            state.createdCtrls[controlIds[0]],
            state.createdCtrls[controlIds[-1]],
        )
        # bind the srts position
        primaryStartSrt.attribute("worldMatrix")[0].connect(
            startTangentCtrl.attribute("offsetParentMatrix")
        )
        tangentRefGraphs = [
            {
                "upVectorGraph": state.segmentMidGraphs[0],
                "primarySrtDecomp": state.primaryBendyCtrlGraphs[0][0].outputAttr(
                    "primaryStartSrtWorldScale"
                ),
                "translateRotMtx": state.segmentMidGraphs[0].outputAttr(
                    "bendyStartCtrlTROnlyWorldMtx"
                ),
                "aimTarget": state.tangentGraphs[0].outputAttr("outputTargetWorldMtx"),
                "primaryNode": primaryStartSrt,
                "primaryGuideId": self.primaryIds[0],
                "startSegmentGuideId": self.primaryIds[0],
                "startSegmentBlendSrt": primaryStartSrt,
                "bendyGuideId": controlIds[1],
            },
            {
                "upVectorGraph": state.segmentMidGraphs[-1],
                "primarySrtDecomp": state.primaryBendyCtrlGraphs[-1][0].outputAttr(
                    "primaryMidSrtWorldScale"
                ),
                "translateRotMtx": state.segmentMidGraphs[-1].outputAttr(
                    "bendyEndCtrlTROnlyWorldMtx"
                ),
                "aimTarget": state.tangentGraphs[-1].outputAttr("outputTargetWorldMtx"),
                "primaryNode": primaryEndSrt,
                "primaryGuideId": self.primaryIds[-1],
                "startSegmentGuideId": self.primaryIds[-2],
                "startSegmentBlendSrt": primaryMidSrt,
                "bendyGuideId": controlIds[-2],
            },
        ]
        upVectorIndices = (0, -1)
        tangentNameIndices = (
            ("Out", "00"),
            ("In", str(len(self.segmentTwistCounts)).zfill(2)),
        )
        visibilitySwitch = state.controlPanel.tertiaryBendyVis
        for index, tangent in enumerate((startTangentCtrl, endTangentCtrl)):
            visibilitySwitch.connect(tangent.visibility)
            tangent.visibility.hide()
            tangent.resetTransform()
            refGraphs = tangentRefGraphs[index]
            tangentNameSuffix, tangentIndex = tangentNameIndices[index]
            segmentPrimaryControl = primaryStartSrt if index == 0 else primaryEndSrt
            dataGraph = reg.graph(state.startEndTangentGraphRotationId)
            dataGraph.name = "".join((dataGraph.id, str(index)))
            rotationGraph = self.createGraph(state.rigLayer, dataGraph)

            tangentGuide = state.guideDefs[tangent.id()]
            primaryRefGuide = state.guideDefs[refGraphs["primaryGuideId"]]
            upVector = state.guideAlignmentSettings[tangent.id()]["upVector"]
            aimVector = state.guideAlignmentSettings[tangent.id()]["aimVector"]
            alignmentMultiplier = -1 if bool(index) else 1
            rotationGraph.setInputAttr("aimVector", aimVector * alignmentMultiplier)
            rotationGraph.setInputAttr("upVector", upVector)
            rotationGraph.setInputAttr(
                "blendWeightsDummy", 0
            )  # because blendMatrix resets on connecting matrix grr.
            # now the ctrl offset
            rotationGraph.connectToInput(
                "segmentAutoMidTargetWorldMtx", refGraphs["aimTarget"]
            )
            rotationGraph.connectToInput(
                "driverTransRotateMtx",
                segmentPrimaryControl.attribute("worldMatrix")[0],
            )
            rotationGraph.connectFromOutput(
                "tangentLocalOffsetMtx", [tangent.attribute("offsetParentMatrix")]
            )
            rotationGraph.connectToInput(
                "upVectorMtx", state.upVectors[upVectorIndices[index]]
            )

            guidePositionDist = state.guideLayerDef.guideSetting(
                tangent.id() + "Position"
            ).value
            tangentDistance = (
                tangentGuide.translate - primaryRefGuide.translate
            ).length()

            rotationGraph.setInputAttr("defaultCtrlDistance", tangentDistance)
            rotationGraph.setInputAttr(
                "tangentDistanceOffsetFraction", guidePositionDist
            )
            distAttr = state.controlPanel.attribute(
                "tangent{}Dist{}".format(tangentIndex, tangentNameSuffix)
            )
            rotationGraph.connectToInput("tangentDistance", distAttr)
            rotationGraph.setInputAttr("tangentDistanceHalf", -0.5)
            distNode, offsetNode = rotationGraph.findNodes(
                "tangentDistance", "localOffset"
            )
            distNode.output.disconnectAll()
            aimVectorName = mayamath.primaryAxisNameFromVector(aimVector)
            distNode.output.connect(
                offsetNode.attribute("inputTranslate{}".format(aimVectorName))
            )


def createInvertRotationOffset(
    bendyState, controlId, restMatrix, sourceWorldMtx, outMatrixPlug
):
    pickMatrix = zapi.createDG(
        bendyState.namingConfig.resolve(
            "object",
            {
                "componentName": bendyState.componentName,
                "side": bendyState.componentSide,
                "section": "{}localNoScale".format(controlId),
                "type": "pickMatrix",
            },
        ),
        "pickMatrix",
    )
    multMatrix = zapi.createDG(
        bendyState.namingConfig.resolve(
            "object",
            {
                "componentName": bendyState.componentName,
                "side": bendyState.componentSide,
                "section": "{}flippedWorldRot".format(controlId),
                "type": "multMatrix",
            },
        ),
        "multMatrix",
    )
    pickMatrix.useScale.set(0)
    pickMatrix.useShear.set(0)
    restMatrix.connect(pickMatrix.inputMatrix)
    pickMatrix.outputMatrix.connect(multMatrix.matrixIn[0])
    sourceWorldMtx.connect(multMatrix.matrixIn[1])
    multMatrix.matrixSum.connect(outMatrixPlug)
    return pickMatrix, multMatrix


def _createUpVectorMatrix(offsetMatrix, worldMatrixA):
    multMtx = zapi.createDG("upVectorMtx", "multMatrix")
    offsetMatrix.connect(multMtx.matrixIn[0])
    worldMatrixA.connect(multMtx.matrixIn[1])
    return multMtx.matrixSum


def _createUpVectorSplitMatrix(offsetMatrix, rotationMatrixPlug, translationMatrixPlug):
    multMtx = zapi.createDG("upVectorMtx", "multMatrix")
    upVectorTrans = zapi.createDG("upVectorTranslation", "pickMatrix")
    upVectorRot = zapi.createDG("upVectorRotation", "pickMatrix")
    offsetMatrix.connect(multMtx.matrixIn[0])
    upVectorRot.outputMatrix.connect(multMtx.matrixIn[1])
    upVectorTrans.outputMatrix.connect(multMtx.matrixIn[2])
    rotationMatrixPlug.connect(upVectorRot.inputMatrix)
    translationMatrixPlug.connect(upVectorTrans.inputMatrix)
    for i in (upVectorTrans, upVectorRot):
        i.useScale.set(0)
        i.useShear.set(0)
    upVectorTrans.useRotate.set(0)
    upVectorRot.useTranslate.set(0)
    return multMtx.matrixSum
