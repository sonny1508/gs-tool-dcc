import itertools
from collections import OrderedDict

from zoo.libs.hive import api
from zoo.core.util import strutils
from zoo.libs.hive.library.components.general import vchaincomponent
from zoo.libs.hive.library.subsystems import (
    bendysubsystem,
    twistsubsystem,
    volumepreservation,
)


class ArmComponent(vchaincomponent.VChainComponent):
    creator = "David Sparrow"
    definitionName = "armcomponent"
    uiData = {"icon": "componentVChain", "iconColor": (), "displayName": "Arm"}
    rootIkVisCtrlName = "ikShldrCtrlVis"
    fixMidJointMMLabel = "Fix Elbow"
    _primaryIds = ["upr", "mid", "end"]
    _alignWorldUpRotationOffset = 180
    bendyAnimAttrsInsertAfterName = "ikRoll"
    bendyVisAttributesInsertAfterName = "twistCtrlsVis"
    twistFlipFirstSegmentRotations = False

    def createSubSystems(self):
        """Creates the subsystems for the current component and returns them in an OrderedDict.

        :return: OrderedDict with keys of the subsystem names and values of the corresponding subsystem object
        :rtype: OrderedDict

        Example return value:
        {
            "twists": :class:`zoo.libs.hive.library.subsystems.twistsubsystem.TwistSubSystem`,
            "bendy": :class:`zoo.libs.hive.library.subsystems.bendysubsystem.BendySubSystem`
        }
        """
        systems = super(ArmComponent, self).createSubSystems()
        guideLayerDef = self.definition.guideLayer  # type: api.GuideLayerDefinition

        guideSettings = guideLayerDef.guideSettings(
            "uprSegmentCount",
            "lwrSegmentCount",
            "hasTwists",
            "hasBendy",
            "displayVolumeAttrsChannelBox",
        )
        counts = [
            guideSettings["uprSegmentCount"].value,
            guideSettings["lwrSegmentCount"].value,
        ]

        hasBendy = guideSettings["hasBendy"].value

        twistSystem = twistsubsystem.TwistSubSystem(
            self,
            self._primaryIds,
            rigDistributionStartIds=("upr", "end"),
            segmentPrefixes=["uprTwist", "lwrTwist"],
            segmentCounts=counts,
            segmentSettingPrefixes=["upr", "lwr"],
            twistReverseFractions=[True, False],
            buildTranslation=not hasBendy,
            buildScale=False,
        )
        twistSystem.twistFlipFirstSegmentRotations = self.twistFlipFirstSegmentRotations
        systems["twists"] = twistSystem
        systems["bendy"] = bendysubsystem.BendySubSystem(
            self,
            self._primaryIds,
            ["uprTwist", "lwrTwist"],
            counts,
            self.bendyAnimAttrsInsertAfterName,
            self.bendyVisAttributesInsertAfterName,
        )
        displayVolume = guideSettings["displayVolumeAttrsChannelBox"].value
        # if we have bendy we will have volume , we need to modify internal space switching to come after the volume
        if hasBendy:
            lastTwistId = twistSystem.segmentTwistIds[-1][-1]

            constants = (
                ("constants", "constant_uprInitialLength"),
                ("constants", "constant_lwrInitialLength"),
            )
            systems["bendy"].bendyAnimAttrsInsertAfterName = lastTwistId
            for i, name in enumerate(("uprVolume", "lwrVolume")):
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
        mapping = super(ArmComponent, self).idMapping()
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

        return mapping

    def spaceSwitchUIData(self):
        baseData = super(ArmComponent, self).spaceSwitchUIData()

        # twist drivers
        baseData["drivers"] += [
            api.SpaceSwitchUIDriver(
                id_=api.pathAsDefExpression(["self", "rigLayer", i]),
                label=strutils.titleCase(i),
            )
            for i in itertools.chain(*self.twistIds(False))
        ]
        return baseData

    def twistIds(self, ignoreHasTwistsFlag=False):
        """Returns the internal hive ids for the twists.

        :param ignoreHasTwistsFlag: if True then we return a empty list for the upr and lwr /
        segments if there's hasTwists settings is False.

        :type ignoreHasTwistsFlag: bool
        :return:
        :rtype: list[list[str]]
        """
        twistSystem = self.subsystems().get("twists")
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

        :todo: maintain existing twist guides to keep guide shape nodes.

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
        originalGuideSettings = super(ArmComponent, self).updateGuideSettings(settings)

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

        super(ArmComponent, self).preSetupGuide()

    def postSetupGuide(self):
        for subSystem in self.subsystems().values():
            if subSystem.active():
                subSystem.postSetupGuide()

        super(ArmComponent, self).postSetupGuide()

    def alignGuides(self):
        guides, matrices = [], []
        systems = [
            system
            for name, system in self.subsystems().items()
            if name in ("ik", "twists", "bendy") and system.active()
        ]
        for system in systems:
            gui, mats = system.preAlignGuides()
            guides.extend(gui)
            matrices.extend(mats)
        if guides and matrices:
            api.setGuidesWorldMatrix(guides, matrices)
        for system in systems:
            system.postAlignGuides()

        return True

    def setupDeformLayer(self, parentNode=None):
        for subSystem in self.subsystems().values():
            subSystem.setupDeformLayer(parentNode)

        super(ArmComponent, self).setupDeformLayer(parentNode)

    def postSetupDeform(self, parentJoint):
        super(ArmComponent, self).postSetupDeform(parentJoint)
        twistIds = self.twistIds(False)
        if not twistIds:
            return
        outputLayer = self.outputLayer()
        deformLayer = self.deformLayer()

        ids = list(itertools.chain(*twistIds))

        joints = deformLayer.findJoints(*ids)

        for index, (driver, drivenId) in enumerate(zip(joints, ids)):
            if driver is None:
                continue
            driven = outputLayer.outputNode(drivenId)
            # local space matrix
            driver.attribute("matrix").connect(driven.offsetParentMatrix)
            driven.resetTransform()
            driver.rotateOrder.connect(driven.rotateOrder)

    def setupSelectionSet(self, deformLayer, deformJoints):
        # when we have twist joints skip the upr/mid joints
        settings = self.definition.guideLayer.guideSettings("hasTwists", "hasBendy")
        if settings["hasTwists"].value or settings["hasBendy"].value:
            ignoredSkinJoints = ("upr", "mid")
            return [n for i, n in deformJoints.items() if i not in ignoredSkinJoints]
        return list(deformJoints.values())

    def preSetupRig(self, parentNode):
        """Here we generate the constants node and attributes for the twists.

        Note: at this point no scene state is changed
        """
        for subSystem in self.subsystems().values():
            if subSystem.active():
                subSystem.preSetupRig(parentNode)

        super(ArmComponent, self).preSetupRig(parentNode)


    def _runSetupRigSubsystems(self, parentNode):
        subsystems = self.subsystems()
        for name, subSystem in subsystems.items():
            if not subSystem.active():
                continue
            if name == "uprVolume":
                subSystem.curveNode = subsystems["bendy"].rigState.curves[0]
            if name == "lwrVolume":
                subSystem.curveNode = subsystems["bendy"].rigState.curves[1]
            subSystem.setupRig(parentNode)

    def squashCurve(self):
        return self.meta.sourceNodeByName("squashCurveNode")
