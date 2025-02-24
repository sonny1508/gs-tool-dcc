"""
todo: map mirrored components with meta data so we can know the axis to work on
"""

from collections import OrderedDict

from zoo.libs.hive.library.components.arm import armcomponent
from zoo.libs.hive import api
from zoo.libs.hive.library.subsystems import (
    twoboneiksubsystem,
    fksubsystem,
    reversefootiksubsystem,
    ikfkblendsubsystem,
    twistsubsystem,
    bendysubsystem,
    volumepreservation,
)


class LegComponent(armcomponent.ArmComponent):
    creator = "David Sparrow"
    definitionName = "legcomponent"
    uiData = {"icon": "componentLeg", "iconColor": (), "displayName": "Leg"}
    # determines whether the 'end' guide should be world aligned vs align to parent/child
    worldEndRotation = True
    # guide which to world align to ie. the ball
    worldEndAimGuideId = "ball"
    rootIkVisCtrlName = "ikHipsCtrlVis"
    _pivotGuideIdsForAlignToWorld = ("heel_piv", "outer_piv", "inner_piv")
    _resetEndGuideAlignment = False
    _endGuideAlignTargetGuide = "ball"
    _alignWorldUpRotationOffset = 180
    fkControlIds = ["uprfk", "midfk", "endfk"]
    deformJointIds = ["upr", "mid", "end"]
    fixMidJointMMLabel = "Fix Knee"
    _spaceSwitchDrivers = armcomponent.ArmComponent._spaceSwitchDrivers + [
        api.SpaceSwitchUIDriver(id_="ballFk", label="Ball FK")
    ]
    twistFlipFirstSegmentRotations = True

    def idMapping(self):
        mapping = super(LegComponent, self).idMapping()
        foot = self.subsystems()["foot"]
        if not foot.active():
            return
        d = {"ball": "ballroll_piv"}
        d.update({k: k for k in foot.guideIds})
        mapping[api.constants.RIG_LAYER_TYPE].update(d)
        mapping[api.constants.OUTPUT_LAYER_TYPE]["ball"] = "ball"
        mapping[api.constants.DEFORM_LAYER_TYPE].update({"ball": "ball", "toe": "toe"})
        return mapping

    def createSubSystems(self):
        guideLayerDef = self.definition.guideLayer  # type: api.GuideLayerDefinition
        ikGuideIds = [i + api.constants.IKTYPE for i in self.deformJointIds]
        systems = OrderedDict()
        systems["ik"] = twoboneiksubsystem.TwoBoneIkBlendSubsystem(
            self,
            self.deformJointIds,
            self.rootIkVisCtrlName,
            endGuideAlignTargetGuide=self._endGuideAlignTargetGuide,
            worldEndRotation=self.worldEndRotation,
        )
        systems["fk"] = fksubsystem.FKSubsystem(
            self, self.deformJointIds, self.fkControlIds, "parentSpace"
        )
        systems["foot"] = reversefootiksubsystem.ReverseFootIkSubSystem(
            self,
            animAttributeFootBreakInsertAfter="lock",
            animAttributeVisInsertAfter="ikHipsCtrlVis",
        )
        systems["ikFk"] = ikfkblendsubsystem.IkFkBlendSubsystem(
            self,
            outputJointIds=self.deformJointIds + ["ball"],
            fkNodesIds=self.fkControlIds + ["ballfk"],
            ikJointsIds=ikGuideIds + ["ballik"],
            nodeIds=self.deformJointIds + ["ballfk"],
            blendAttrName="ikfk",
            parentNodeId="parentSpace",
        )
        # add twists and bendy
        guideSettings = guideLayerDef.guideSettings(
            "uprSegmentCount",
            "lwrSegmentCount",
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

        # if we have bendy we will have volume , we need to modify internal space switching to come after the volume
        if hasBendy:
            displayVolume = guideSettings["displayVolumeAttrsChannelBox"].value
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

    def alignGuides(self):
        guides, matrices = [], []
        systems = [
            system
            for name, system in self.subsystems().items()
            if name in ("ik", "twists", "bendy", "foot") and system.active()
        ]
        for system in systems:
            gui, mats = system.preAlignGuides()
            guides.extend(gui)
            matrices.extend(mats)
        if guides and matrices:
            api.setGuidesWorldMatrix(guides, matrices)
        for system in systems:
            system.postAlignGuides()



    def setupRig(self, parentNode):
        super(LegComponent, self).setupRig(parentNode)
        rigLayer = self.rigLayer()
        rigLayer.taggedNode("primaryLegIkHandle").setParent(
            rigLayer.control("ballroll_piv")
        )

    def switchToIk(self):
        subsystems = self.subsystems()
        ikSystem = subsystems["ik"]
        footPreMatchInfo = {}
        if subsystems["foot"].active():
            footPreMatchInfo = subsystems["foot"].preMatchTo()
        ikfkData = ikSystem.matchTo(*list(self.ikControlIds) + ["upVec"])
        if subsystems["foot"].active():
            data = subsystems["foot"].matchTo(footPreMatchInfo)
            ikfkData["controls"].extend(data["controls"])
        ikfkAttr = self.controlPanel().attribute("ikfk")
        ikfkAttr.set(0)
        ikfkData["attributes"] = [ikfkAttr]
        return ikfkData

    def switchToFk(self):
        # to switch to fk just grab the bind skeleton transforms
        # and apply the transform to the fk controls
        deformLayer = self.deformLayer()
        deformJnts = deformLayer.findJoints(*list(self.deformJointIds) + ["ball"])
        subsystems = self.subsystems()
        subsystems["fk"].fkIds = list(subsystems["fk"].fkIds) + ["ballfk"]
        data = subsystems["fk"].matchTo(deformJnts)
        data["selectables"] = [data["controls"][-2]]

        ikfkAttr = self.controlPanel().attribute("ikfk")
        ikfkAttr.set(1)
        data["attributes"] = [ikfkAttr]
        return data
