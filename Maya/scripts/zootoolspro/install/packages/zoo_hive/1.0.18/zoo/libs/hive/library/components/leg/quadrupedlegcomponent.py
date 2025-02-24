import itertools
from collections import OrderedDict

from zoo.core.util import strutils
from zoo.libs.hive.base import component
from zoo.libs.hive import api
from zoo.libs.hive.library.subsystems import (
    quadlegsubsystem,
    fksubsystem,
    ikfkblendsubsystem,
    reversefootiksubsystem,
    twistsubsystem,
    bendysubsystem,
    volumepreservation,
)
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath

from maya.api import OpenMaya as om2


class QuadLegComponent(component.Component):
    """Creates a quadruped leg component with an optional foot.

    ..note:
        When handling alignment of the end guide, There are a few different behaviors
        expected to happen.
        #. When the Foot is present and alignIkEndToWorld is False(default) then the
        endIk control will align to the ball guide in world.

        # If alignIkEndToWorld is True then the endIk control will have it's worldMatrix
        set to identity effectively aligning it to the world.

        #. If AutoAlign on the end guide is False then The end guide will use whatever
        the current end guide rotation is.
        Fk will always be whatever the end guide rotation is.
    """
    creator = "David Sparrow"
    definitionName = "quadLeg"
    uiData = {"icon": "componentLeg", "iconColor": (), "displayName": "Quad Leg"}
    _primaryIds = ["upr", "mid", "ankle", "end"]
    _fkControlsIds = [i + api.constants.FKTYPE for i in _primaryIds]
    # aligns the end input/guide to point to the worldEndAimGuideId
    worldEndRotation = True
    worldEndAimGuideId = "ball"
    twistFlipFirstSegmentRotations = True
    _alignWorldUpRotationOffset = 180
    bendyAnimAttrsInsertAfterName = "ikRoll"
    bendyVisAttributesInsertAfterName = "twistCtrlsVis"
    # used by the marking menu to determine whether to build the ikfk matching actions.
    hasIkFk = True
    ikControlIds = (
        "end" + api.constants.IKTYPE,
        "base" + api.constants.IKTYPE,
        "ankle" + api.constants.IKTYPE,
        "upVec",
        "upVecLwr",
    )
    fkControlIds = ("uprfk", "midfk", "anklefk", "endfk")
    deformJointIds = ("upr", "mid", "ankle", "end")
    fixMidJointMMLabel = "Fix Mid"
    # driven space switches
    _spaceSwitchDriven = [
        api.SpaceSwitchUIDriven(
            id_=api.pathAsDefExpression(("self", "rigLayer", "endik")), label="End IK"
        ),
        api.SpaceSwitchUIDriven(
            id_=api.pathAsDefExpression(("self", "rigLayer", "baseik")), label="Base IK"
        ),
        api.SpaceSwitchUIDriven(
            id_=api.pathAsDefExpression(("self", "rigLayer", "upVec")),
            label="Pole Vector",
        ),
        api.SpaceSwitchUIDriven(
            id_=api.pathAsDefExpression(("self", "rigLayer", "upVecLwr")),
            label="Pole Vector Lower",
        ),
        api.SpaceSwitchUIDriven(
            id_=api.pathAsDefExpression(("self", "rigLayer", "uprfk")), label="FK"
        ),
    ]
    # drivers for space switching
    _spaceSwitchDrivers = [
        api.SpaceSwitchUIDriver(**i.serialize()) for i in _spaceSwitchDriven
    ] + [
        api.SpaceSwitchUIDriver(
            id_=api.pathAsDefExpression(("self", "rigLayer", "midfk")), label="Mid FK"
        ),
        api.SpaceSwitchUIDriver(
            id_=api.pathAsDefExpression(("self", "rigLayer", "endfk")), label="End FK"
        ),
        api.SpaceSwitchUIDriver(
            id_=api.pathAsDefExpression(("self", "inputLayer", "upr")),
            label="Parent Component",
            internal=True,
        ),
        api.SpaceSwitchUIDriver(
            id_=api.pathAsDefExpression(("self", "inputLayer", "world")),
            label="World Space",
            internal=True,
        ),
    ]

    def createSubSystems(self):
        guideLayerDef = self.definition.guideLayer  # type: api.GuideLayerDefinition
        # add twists and bendy
        guideSettings = guideLayerDef.guideSettings(
            "uprSegmentCount",
            "lwrSegmentCount",
            "ankleSegmentCount",
            "hasTwists",
            "hasBendy",
            "displayVolumeAttrsChannelBox",
            "alignIkEndToWorld",
        )
        systems = OrderedDict()
        systems["ik"] = quadlegsubsystem.QuadLegSubSystem(
            self, self._primaryIds, worldEndRotation=guideSettings["alignIkEndToWorld"].value
        )
        systems["fk"] = fksubsystem.FKSubsystem(
            self, self._primaryIds, self._fkControlsIds, "parentSpace"
        )
        footSystem = reversefootiksubsystem.ReverseFootIkSubSystem(
            self,
            animAttributeFootBreakInsertAfter="ikLwrAngleBias",
            animAttributeVisInsertAfter="ikHipsCtrlVis",
        )
        systems["foot"] = footSystem
        primaryIdsForBlend = list(self._primaryIds)
        fkIdsForBlend = list(self._fkControlsIds)

        if footSystem.active():
            primaryIdsForBlend.append("ball")
            fkIdsForBlend.append("ballfk")

        systems["ikfkBlend"] = ikfkblendsubsystem.IkFkBlendSubsystem(
            self,
            outputJointIds=primaryIdsForBlend,
            fkNodesIds=fkIdsForBlend,
            ikJointsIds=[i + api.constants.IKTYPE for i in primaryIdsForBlend],
            nodeIds=primaryIdsForBlend,
            blendAttrName="ikfk",
            parentNodeId="parentSpace",
        )

        hasBendy = guideSettings["hasBendy"].value
        counts = [
            guideSettings["uprSegmentCount"].value,
            guideSettings["lwrSegmentCount"].value,
            guideSettings["ankleSegmentCount"].value,
        ]
        twistSystem = twistsubsystem.TwistSubSystem(
            self,
            self._primaryIds,
            rigDistributionStartIds=("upr", "ankle", "end"),
            segmentPrefixes=["uprTwist", "lwrTwist", "ankleTwist"],
            segmentCounts=counts,
            segmentSettingPrefixes=["upr", "lwr", "ankle"],
            twistReverseFractions=[True, False, False],
            buildTranslation=not hasBendy,
        )
        twistSystem.twistFlipFirstSegmentRotations = self.twistFlipFirstSegmentRotations
        systems["twists"] = twistSystem
        systems["bendy"] = bendysubsystem.BendySubSystem(
            self,
            self._primaryIds,
            ["uprTwist", "lwrTwist", "ankleTwist"],
            counts,
            self.bendyAnimAttrsInsertAfterName,
            self.bendyVisAttributesInsertAfterName,
        )
        # if we have bendy we will have volume , we need to modify internal space switching to come after the volume
        if hasBendy:
            lastTwistId = twistSystem.segmentTwistIds[-1][-1]
            for space in self.definition.spaceSwitching:
                panelFilter = space.get("controlPanelFilter", {})
                group = panelFilter.get("group", {})
                if not group:
                    continue
                current = group.get("insertAfter", "")
                if current == "lock":
                    panelFilter["group"]["insertAfter"] = "volume_{}".format(
                        lastTwistId
                    )

        # if we have bendy we will have volume , we need to modify internal space switching to come after the volume
        if hasBendy:
            lastTwistId = twistSystem.segmentTwistIds[-1][-1]
            systems["bendy"].bendyAnimAttrsInsertAfterName = lastTwistId
            constants = (
                ("constants", "constant_uprInitialLength"),
                ("constants", "constant_lwrInitialLength"),
                ("constants", "constant_ankleInitialLength"),
            )

            displayVolume = guideSettings["displayVolumeAttrsChannelBox"].value

            for i, name in enumerate(("uprVolume", "lwrVolume", "ankleVolume")):
                volume = volumepreservation.VolumePreservationSubsystem(
                    self,
                    twistSystem.segmentTwistIds[i],
                    twistSystem.segmentTwistIds[i],
                    "hasBendy",
                    initializeLengthConstantAttr=constants[i],
                    reverseVolumeValues=i == 1,
                    showVolumeAttrsInChannelBox=displayVolume,
                )

                insertAfter = (
                    "ikRoll"
                    if i == 0
                    else "volume_{}".format(twistSystem.segmentTwistIds[i - 1][-1])
                )
                volume.attrsInsertAfterName = insertAfter

                systems[name] = volume
        return systems

    def idMapping(self):
        mapping = super(QuadLegComponent, self).idMapping()
        systems = self.subsystems()
        if systems["twists"].active():
            twistIds = systems["twists"].segmentTwistIds
            twistMapping = {k: k for k in itertools.chain(*twistIds)}
            mapping[api.constants.DEFORM_LAYER_TYPE].update(twistMapping)
            mapping[api.constants.OUTPUT_LAYER_TYPE].update(twistMapping)
            mapping[api.constants.RIG_LAYER_TYPE].update(twistMapping)
            mapping[api.constants.RIG_LAYER_TYPE].update(
                {k: k for k in systems["twists"].segmentTwistOffsetIds}
            )
            # update rigLayer with bendy
        if self.definition.guideLayer.guideSetting("hasBendy").value:
            mapping[api.constants.RIG_LAYER_TYPE].update(
                {k: k for k in self.subsystems()["bendy"].controlIds()}
            )

        if not systems["foot"].active():
            return mapping
        d = {"ball": "ballroll_piv"}
        d.update({k: k for k in systems["foot"].guideIds})
        mapping[api.constants.RIG_LAYER_TYPE].update(d)
        mapping[api.constants.OUTPUT_LAYER_TYPE]["ball"] = "ball"
        mapping[api.constants.DEFORM_LAYER_TYPE].update({"ball": "ball", "toe": "toe"})
        return mapping

    def spaceSwitchUIData(self):
        driven = self._spaceSwitchDriven
        drivers = list(self._spaceSwitchDrivers)
        drivers += [
            api.SpaceSwitchUIDriver(
                id_=api.pathAsDefExpression(["self", "rigLayer", i]),
                label=strutils.titleCase(i),
            )
            for i in itertools.chain(*self.twistIds(False))
        ]

        return {"driven": driven, "drivers": drivers}

    def twistIds(self, ignoreHasTwistsFlag=False):
        """Returns the internal hive ids for the twists.

        :param ignoreHasTwistsFlag: if True, then we return an empty list for the segments
        if there's hasTwists setting is False.

        :type ignoreHasTwistsFlag: bool
        :return:
        :rtype: list[list[str]]
        """
        twistSystem = self.subsystems()["twists"]
        if twistSystem is not None and twistSystem.active() or ignoreHasTwistsFlag:
            return twistSystem.segmentTwistIds
        return []

    def bendyIds(self, ignoreHasBendyFlag=False):
        """Returns the internal hive ids for bendy controls/guides.

        :param ignoreHasBendyFlag: if True then we return a empty list and bendy is active.
        :type ignoreHasBendyFlag: bool
        :return:
        :rtype: list[str]
        """
        bendySystem = self.subsystems().get("bendy")
        if bendySystem is not None and bendySystem.active() or ignoreHasBendyFlag:
            return list(bendySystem.controlIds())
        return []

    def updateGuideSettings(self, settings):
        """Updates the vchain component which may require a rebuild.

        When any twist setting has changed we re-construct the twist guides from scratch.

        :param settings: The Guide setting name and the value to change.
        :type settings: dict[str, any]
        :return: Returns the the current settings on the definition before the change happened.
        :rtype: dict[str, any]
        """
        self.serializeFromScene(
            layerIds=(api.constants.GUIDE_LAYER_TYPE,)
        )  # ensure the definition contains the latest scene state.

        requiresRebuilds = []
        runPostUpdates = []
        for subSystem in self.subsystems().values():
            requiresRebuild, runPostUpdate = subSystem.preUpdateGuideSettings(settings)
            if requiresRebuild:
                requiresRebuilds.append(subSystem)
            if runPostUpdate:
                runPostUpdates.append(subSystem)
        originalGuideSettings = super(QuadLegComponent, self).updateGuideSettings(
            settings
        )

        if requiresRebuilds:
            self.rig.buildGuides([self])

        for subSystem in runPostUpdates:
            subSystem.postUpdateGuideSettings(settings)

        return originalGuideSettings

    def preSetupGuide(self):
        guideLayerDef = self.definition.guideLayer
        worldUp, worldUpVecRef = guideLayerDef.findGuides("worldUpVec", "worldUpVecRef")
        # for upgrading reasons and the fact we don't have a dedicated tool for it we need to delete the worldUp
        if worldUp is not None:
            parentGuide = guideLayerDef.guide(worldUp.parent)
            parentGuide.deleteChild(worldUp.id)

        for subSystem in self.subsystems().values():
            if subSystem.active():
                subSystem.preSetupGuide()
            else:
                subSystem.deleteGuides()
        super(QuadLegComponent, self).preSetupGuide()

    def setupGuide(self):
        super(QuadLegComponent, self).setupGuide()
        for subSystem in self.subsystems().values():
            if subSystem.active():
                subSystem.setupGuide()

    def postSetupGuide(self):
        for name, subSystem in self.subsystems().items():
            if subSystem.active():
                subSystem.postSetupGuide()
        super(QuadLegComponent, self).postSetupGuide()

    def alignGuides(self):
        guides, matrices = [], []
        systems = [
            system
            for name, system in self.subsystems().items()
            if name in ("ik", "foot", "twists", "bendy") and system.active()
        ]
        for system in systems:
            gui, mats = system.preAlignGuides()
            guides.extend(gui)
            matrices.extend(mats)

        api.setGuidesWorldMatrix(guides, matrices)

        for system in systems:
            system.postAlignGuides()

    def preMirror(self, translate=("x",), rotate="yz", parent=om2.MObject.kNullObj):
        if not self.hasGuide():
            return []
        iksystem = self.subsystems()["ik"]
        if iksystem.active():
            iksystem.preMirror(translate, rotate, parent)

    def postMirror(self, translate=("x",), rotate="yz", parent=om2.MObject.kNullObj):
        if not self.hasGuide():
            return []
        iksystem = self.subsystems()["ik"]
        if iksystem.active():
            iksystem.postMirror(translate, rotate, parent)

    def setupInputs(self):
        super(QuadLegComponent, self).setupInputs()
        # bind the inputs and outputs to the deform joints
        inputLayer = self.inputLayer()
        rootIn, upVecIn, ikEndIn = inputLayer.findInputNodes("upr", "upVec", "endik")
        guideLayerDef = self.definition.guideLayer
        rootInMatrix = guideLayerDef.guide("upr").transformationMatrix(scale=False)
        # We don't propagate scale from the guide
        rootIn.setWorldMatrix(rootInMatrix.asMatrix())
        alignToWorldSetting = guideLayerDef.guideSetting("alignIkEndToWorld")
        alignToWorld = (
            alignToWorldSetting.value if alignToWorldSetting is not None else False
        )
        endGuide = guideLayerDef.guide("end")
        # We don't propagate scale from the guide
        if alignToWorld:
            ikEndInMatrix = endGuide.transformationMatrix(
                rotate=False, scale=False
            )
        elif not self.worldEndRotation or not endGuide.attribute(api.constants.AUTOALIGN_ATTR).value:
            ikEndInMatrix = guideLayerDef.guide("end").transformationMatrix(scale=False)
        else:
            guideIds = self.worldEndAimGuideId, "end"
            upVector = mayamath.YAXIS_VECTOR
            if not self.subsystems()["foot"].active():
                guideIds = ("ankle", "end")
                upVector = -mayamath.YAXIS_VECTOR
            aimGuide, endGuide = guideLayerDef.findGuides(*guideIds)
            rot = mayamath.lookAt(
                zapi.Vector(endGuide.translate),
                zapi.Vector(aimGuide.translate),
                mayamath.ZAXIS_VECTOR,
                upVector,
                constrainAxis=zapi.Vector(0, 1, 1),
            )
            ikEndInMatrix = endGuide.transformationMatrix(rotate=False, scale=False)
            ikEndInMatrix.setRotation(rot)

        ikEndIn.setWorldMatrix(ikEndInMatrix.asMatrix())
        upVecInMatrix = guideLayerDef.guide("upVec").transformationMatrix(
            rotate=False, scale=False
        )
        upVecIn.setWorldMatrix(upVecInMatrix.asMatrix())

    def setupDeformLayer(self, parentNode=None):
        for subSystem in self.subsystems().values():
            subSystem.setupDeformLayer(parentNode)

        super(QuadLegComponent, self).setupDeformLayer(parentNode)

    def setupOutputs(self, parentNode):
        for subSystem in self.subsystems().values():
            subSystem.setupOutputs(parentNode)

        super(QuadLegComponent, self).setupOutputs(parentNode)
        joints = {i.id(): i for i in self.deformLayer().iterJoints()}
        rootTransform = self.outputLayer().rootTransform()
        layer = self.outputLayer()
        for index, output in enumerate(layer.outputs()):
            driverJoint = joints.get(output.id())
            if driverJoint is None:
                continue
            if output.parent() == rootTransform:
                driverJoint.worldMatrixPlug().connect(output.offsetParentMatrix)
            else:
                driverJoint.attribute("matrix").connect(output.offsetParentMatrix)
            output.resetTransform()

    def preSetupRig(self, parentNode):
        """Here we generate the constants node and attributes for the twists.

        Note: at this point no scene state is changed
        """
        for subSystem in self.subsystems().values():
            subSystem.preSetupRig(parentNode)

        super(QuadLegComponent, self).preSetupRig(parentNode)

    def setupRig(self, parentNode):
        rigLayer = self.rigLayer()
        controlPanel = self.controlPanel()
        inputLayer = self.inputLayer()
        definition = self.definition
        guideLayerDef = definition.guideLayer
        rootTransform = rigLayer.rootTransform()
        compName, compSide = self.name(), self.side()
        # presize our data
        rootIn = inputLayer.inputNode("upr")

        namer = self.namingConfiguration()
        blendAttr = controlPanel.ikfk
        blendAttr.setFloat(guideLayerDef.guideSetting("ikfk_default").value)

        api.componentutils.createParentSpaceTransform(
            namer, compName, compSide, rootTransform, parentNode, rigLayer, rootIn
        )
        subsystems = self.subsystems()
        for name, subSystem in subsystems.items():
            if not subSystem.active():
                continue
            if name == "uprVolume":
                subSystem.curveNode = subsystems["bendy"].rigState.curves[0]
            if name == "lwrVolume":
                subSystem.curveNode = subsystems["bendy"].rigState.curves[1]
            if name == "ankleVolume":
                subSystem.curveNode = subsystems["bendy"].rigState.curves[2]
            subSystem.setupRig(parentNode)

        # get the appropriate ik parent, we do this after subsystems because the foot subsystem
        # is run after the spring
        endIkCtrl = rigLayer.control("endik")
        if subsystems["foot"].active():
            ikParent = rigLayer.control("ballroll_piv")
        else:
            ikParent = endIkCtrl
        rigLayer.taggedNode("springIk").setParent(ikParent)
        fkCtrls = rigLayer.findControls(*self._fkControlsIds)
        ikCtrls = rigLayer.findControls(*self.ikControlIds)
        ikRootSrt = rigLayer.control("baseik").srt()
        annotation = rigLayer.annotation(
            rigLayer.joint("midik"), rigLayer.control("upVecLwr")
        )
        api.componentutils.setupIkFkVisibility(
            self.namingConfiguration(),
            rigLayer,
            compName,
            compSide,
            fkCtrls,
            ikCtrls,
            annotation,
            ikRootSrt,
            blendAttr,
        )
        # for ikfk matching we need the initial matrix offset
        originalOffset = endIkCtrl.offsetMatrix(
            rigLayer.control("endfk"), zapi.kWorldSpace
        )
        rigLayer.settingNode("constants").attribute("constant_ikfkEndOffset").set(
            originalOffset
        )

    def switchToIk(self):
        subsystems = self.subsystems()
        footPreMatchInfo = {}
        if subsystems["foot"].active():
            footPreMatchInfo = subsystems["foot"].preMatchTo()
        ikfkData = subsystems["ik"].matchTo()
        if subsystems["foot"].active():
            data = subsystems["foot"].matchTo(footPreMatchInfo)
            ikfkData["controls"].extend(data["controls"])
            ikfkData.setdefault("attributes", []).extend(data["attributes"])
        ikfkAttr = self.controlPanel().attribute("ikfk")
        ikfkAttr.set(0)
        ikfkData.setdefault("attributes", []).append(ikfkAttr)
        return ikfkData

    def switchToFk(self):
        # to switch to fk just grab the bind skeleton transforms
        # and apply the transform to the fk controls
        deformLayer = self.deformLayer()
        subsystems = self.subsystems()
        deformIds = list(self.deformJointIds)

        if subsystems["foot"].active():
            deformIds.append("ball")
            subsystems["fk"].fkIds.append("ballfk")
        deformJnts = deformLayer.findJoints(*deformIds)
        data = subsystems["fk"].matchTo(deformJnts)
        data["selectables"] = [data["controls"][3]]
        ikfkAttr = self.controlPanel().attribute("ikfk")
        ikfkAttr.set(1)
        data["attributes"] = [ikfkAttr]
        return data

    def prePlacePoleVectorSensibly(self):
        subsystems = self.subsystems()
        if subsystems["ik"].active():
            return subsystems["ik"].prePlacePoleVectorSensibly()

    def placePoleVectorSensibly(self, info, keyRange=()):
        subsystems = self.subsystems()
        if subsystems["ik"].active():
            return subsystems["ik"].placePoleVectorSensibly(info, keyRange)

    def squashCurve(self):
        return self.meta.sourceNodeByName("squashCurveNode")
