import copy
import itertools

from zoo.libs.hive.base.util import twistutils
from zoo.libs.hive.base import hivenodes, basesubsystem
from zoo.libs.hive import constants
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayaenv


class TwistSubSystem(basesubsystem.BaseSubsystem):
    """The TwistSubSystem class is a helper class for the creation and management of twist segments in a rig system.

    :param component: The component that the bendy subsystem is associated with
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param primaryIds: list of primary guide ids for the bendy subsystem to build on top of.
    :type primaryIds: list[str]
    :param segmentPrefixes: list of prefixes of the segments.
    :type segmentPrefixes: list[str]
    :param segmentCounts: list of joint counts of the segments in the segment groups.
    :type segmentCounts: list[int]
    :param segmentSettingPrefixes: A list of prefixes for each segment's setting name.
    :type segmentSettingPrefixes: list[str]
    """

    settingSwitchName = "hasTwists"
    twistConstantsNodeName = "twistConstants"

    def __init__(
            self,
            component,
            primaryIds,
            rigDistributionStartIds,
            segmentPrefixes,
            segmentCounts,
            segmentSettingPrefixes,
            twistReverseFractions,
            buildTranslation=True,
            buildRotation=True,
            buildScale=True
    ):
        super(TwistSubSystem, self).__init__(component)
        self.primaryIds = primaryIds
        # guide ids where twists calculations will start from
        self.rigDistributionStartIds = rigDistributionStartIds
        self.twistReverseFractions = twistReverseFractions
        # [[segmentIdOne], [segmentIdTwo]]
        self.segmentTwistPrefixes = segmentPrefixes
        self.segmentTwistCounts = segmentCounts
        self.segmentTwistIds = []
        self.segmentTwistOffsetIds = []
        self.buildTranslation = buildTranslation
        self.buildRotation = buildRotation
        self.buildScale = buildScale
        for index, count in enumerate(segmentCounts):
            prefix = segmentPrefixes[index]
            segmentIds = [prefix + str(i).zfill(2) for i in range(count)]
            self.segmentTwistOffsetIds.append("{}Offset".format(prefix))
            self.segmentTwistIds.append(segmentIds)
        # guide setting name for each segment ie. uprSegmentCount, lwrSegmentCount
        self.segmentCountSettingNames = [
            "{}SegmentCount".format(prefix) for prefix in segmentSettingPrefixes
        ]  # type: list[str]
        self.distributionType = "linear"
        self._guideAlignGraphId = (
            "twistGuideAlign"
            if mayaenv.mayaVersion() > 2022
            else "twistGuideAlignPre2023"
        )
        self._guideAlignGraphName = "twistGuideAlign"  # used for graph instance name
        self.twistFlipFirstSegmentRotations = False

    def active(self):
        return self.component.definition.guideLayer.guideSetting(
            self.settingSwitchName
        ).value

    def _guideTwistIdsIgnoreSettings(self):
        guideLayer = self.component.definition.guideLayer
        twistIds = itertools.chain(*self.segmentTwistIds)

        for guide in guideLayer.findGuides(*twistIds):
            if guide is not None:
                yield guide.id

    def _deformTwistIdsIgnoreSettings(self):
        definition = self.component.definition
        deformLayer = definition.deformLayer

        twistIds = itertools.chain(*self.segmentTwistIds)

        for jnt in deformLayer.findJoints(*twistIds):
            if jnt is not None:
                yield jnt.id

    def deleteGuides(self):
        layer = self.component.definition.guideLayer
        twistIds = list(self._guideTwistIdsIgnoreSettings())
        layer.deleteGuides(*twistIds + self.segmentTwistOffsetIds)
        sceneLayer = self.component.guideLayer()
        graphRegistry = self.component.configuration.graphRegistry()
        for twistId in twistIds:
            sceneLayer.deleteNamedGraph(
                self._guideAlignGraphName + twistId, graphRegistry
            )
        layer.deleteSettings(twistIds)

    def preUpdateGuideSettings(self, settings):
        if settings.get("hasTwists") is None and not self.active():
            return False, False
        definition = self.component.definition
        guideLayerDef = definition.guideLayer

        # first thing we need to do is purge any guide settings for twists we no longer need
        # then purge the guides which aren't needed then rebuild the missing
        hasTwists = settings.get(
            self.settingSwitchName,
            guideLayerDef.guideSetting(self.settingSwitchName).value,
        )
        requiresRebuild = any(
            i in settings
            for i in self.segmentCountSettingNames + [self.settingSwitchName]
        )
        runPostUpdate = requiresRebuild or "distributionType" in settings

        twistsToDelete = []
        twistIds = self.segmentTwistIds
        if hasTwists:
            # diff what we have in the definition with the new count and add the twists which need deleting to the
            # list for deleting further down
            for index, settingCountName in enumerate(self.segmentCountSettingNames):
                requestedCountChange = settings.get(settingCountName)
                if not requestedCountChange:
                    continue
                segmentIDs = twistIds[index]
                currentCount = len(segmentIDs)
                countDiff = currentCount - requestedCountChange

                if countDiff > 0:
                    twistsToDelete.extend(segmentIDs[currentCount - countDiff:])
                self.segmentTwistCounts[index] = requestedCountChange
        else:
            twistsToDelete.extend(
                list(itertools.chain(*twistIds)) + self.segmentTwistOffsetIds
            )

        if twistsToDelete:
            guideLayerDef.deleteSettings(twistsToDelete)
            guideLayerDef.deleteGuides(*twistsToDelete)
            definition.deformLayer.deleteJoints(*twistsToDelete)
            definition.outputLayer.deleteOutputs(*twistsToDelete)
            sceneLayer = self.component.guideLayer()
            graphRegistry = self.component.configuration.graphRegistry()
            for twistId in twistsToDelete:
                sceneLayer.deleteNamedGraph(
                    self._guideAlignGraphName + twistId, graphRegistry
                )
        # return True will tell the component to rerun buildGuides for this component
        return requiresRebuild, runPostUpdate

    def postUpdateGuideSettings(self, settings):
        if not self.active():
            return
        # here we need to decide whether we need to update the scene, some settings don't require updates ie.
        # ikfkDefault
        definition = self.component.definition
        guideLayerDef = definition.guideLayer
        distType = settings.get("distributionType")
        sceneLayer = self.component.guideLayer()

        countChanged = False
        for index, settingCountName in enumerate(self.segmentCountSettingNames):
            requestedCountChange = settings.get(settingCountName)
            if not requestedCountChange:
                continue
            countChanged = True
            break
        # update the scene twist transforms which need to happen after any new guides have been added
        # or guides removed
        if countChanged or distType is not None:
            guideSettingsNode = sceneLayer.guideSettings()
            for index, count in enumerate(self.segmentTwistCounts):
                startGuide, endGuide = guideLayerDef.findGuides(
                    self.primaryIds[index], self.primaryIds[index + 1]
                )
                # we first update the twist attributes then align the scene nodes
                twistutils.updateSceneGuideAttributes(
                    self.segmentTwistPrefixes[index],
                    guideSettingsNode,
                    guideLayerDef,
                    startGuide.translate,
                    endGuide.translate,
                    count,
                    reverseFractions=index == 0,
                )

    def preSetupGuide(self):
        if not self.active():
            return
        definition = self.component.definition
        guideLayerDef = definition.guideLayer  # type: definition.GuideLayerDefinition

        primaryGuides = guideLayerDef.findGuides(*self.primaryIds)
        naming = self.component.namingConfiguration()
        compName, compSide = self.component.name(), self.component.side()

        for index, offset in enumerate(self.segmentTwistOffsetIds):
            driverGuide = primaryGuides[index]
            guideLayerDef.createGuide(
                id=offset,
                name=naming.resolve(
                    "twistControlName",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "id": offset,
                        "type": "guide",
                    },
                ),
                worldMatrix=driverGuide.worldMatrix,
                parent=driverGuide.id,
                attributes=[{"name": "visibility", "value": False, "locked": True}],
                shape="arrow_1_thinbev",
                shapeTransform={"worldMatrix": list(driverGuide.worldMatrix)},
            )

        for index, count in enumerate(self.segmentTwistCounts):
            start = primaryGuides[index]
            end = primaryGuides[index + 1]
            # setup first segment
            twistutils.generateTwistSegmentGuides(
                self.component,
                guideLayerDef,
                count,
                startPos=start.translate,
                endPos=end.translate,
                parentGuide=start,
                twistPrefix=self.segmentTwistPrefixes[index],
                reverseFractions=index == 0,
            )

    def setupGuide(self):
        if not self.active():
            return
        guideLayer = self.component.guideLayer()
        graphRegistry = self.component.configuration.graphRegistry()
        graph = graphRegistry.graph(self._guideAlignGraphId)

        settingsNode = guideLayer.guideSettings()
        # first purge the twist graphs and then rebuild, this allows for a clean slate also helps
        # with auto upgrading.
        for twistId in itertools.chain(*self.segmentTwistIds):
            guideLayer.deleteNamedGraph(graph.name + twistId, graphRegistry)

        for index, segmentIds in enumerate(self.segmentTwistIds):
            startPrimaryGuideId, endPrimaryGuideId = (
                self.primaryIds[index],
                self.primaryIds[index + 1],
            )
            twistGuides = guideLayer.findGuides(*segmentIds)
            startGuide, endGuide = guideLayer.findGuides(
                startPrimaryGuideId, endPrimaryGuideId
            )
            # upr and lwr segment twists are reversed so flip the source nodes here
            if index == 0:
                targetInputMtx, inputMatrix, upVectorRef = (
                    startGuide,
                    endGuide,
                    startGuide,
                )
            else:
                targetInputMtx, inputMatrix, upVectorRef = (
                    endGuide,
                    startGuide,
                    startGuide,
                )

            for twistGuide in twistGuides:
                with zapi.lockStateAttrContext(
                        twistGuide, zapi.localTransformAttrs, False
                ):
                    twistGuide.resetTransform(scale=False)
                graphInstance = copy.copy(graph)
                graphInstance.name += twistGuide.id()
                sceneGraph = self.createGraph(guideLayer, graphInstance)
                sceneGraph.connectToInput(
                    "aimTargetMtx", endGuide.attribute("worldMatrix")[0]
                )
                sceneGraph.connectToInput(
                    "inputMtx", inputMatrix.attribute("worldMatrix")[0]
                )
                sceneGraph.connectToInput(
                    "targetInputMtx", targetInputMtx.attribute("worldMatrix")[0]
                )
                sceneGraph.connectToInput(
                    "aimVector", twistGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR)
                )
                sceneGraph.connectToInput(
                    "upVector", twistGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR)
                )
                sceneGraph.connectToInput(
                    "upVectorX",
                    twistGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR + "X"),
                )
                sceneGraph.connectToInput(
                    "upVectorY",
                    twistGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR + "Y"),
                )
                sceneGraph.connectToInput(
                    "upVectorZ",
                    twistGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR + "Z"),
                )
                sceneGraph.connectToInput(
                    "positionBlend", settingsNode.attribute(twistGuide.id())
                )
                sceneGraph.setInputAttr("blendTranslate", 1.0)
                sceneGraph.setInputAttr("blendRotate", 0.0)
                sceneGraph.setInputAttr("blendScale", 0.0)
                sceneGraph.setInputAttr("worldUpBasisMultiplier", zapi.Vector(1.0, 1.0, 1.0))
                if index != 0:
                    sceneGraph.setInputAttr("inputPickMatScale", True)
                    sceneGraph.setInputAttr("targetPickMatScale", False)
                sceneGraph.connectToInput(
                    "alignBehaviour",
                    twistGuide.attribute(constants.MIRROR_BEHAVIOUR_ATTR),
                )
                sceneGraph.connectToInput(
                    "upVectorParentMtx", startGuide.worldMatrixPlug()
                )
                sceneGraph.connectToInput(
                    "parentInverseMtx",
                    twistGuide.parent().attribute("worldInverseMatrix")[0],
                )
                sceneGraph.connectFromOutput(
                    "outputMatrix", [twistGuide.offsetParentMatrix]
                )
                twistGuide.setLockStateOnAttributes(
                    zapi.localTranslateAttrs + zapi.localRotateAttrs, True
                )  # enforce lock state

    def preAlignGuides(self):
        if not self.active():
            return [], []
        # match the offset guides to the right primary nodes
        layer = self.component.guideLayer()
        primaryGuides = layer.findGuides(*self.primaryIds)
        offsets = layer.findGuides(*self.segmentTwistOffsetIds)

        matrices, guides = [], []
        # all offsets align the first guide of the segment except for the last offset which aligns to the last
        for i, offsetGuide in enumerate(offsets[:-1]):
            guides.append(offsetGuide)
            matrices.append(primaryGuides[i].worldMatrix())
        matrices.append(primaryGuides[-1].worldMatrix())
        guides.append(offsets[-1])
        for segmentIds in self.segmentTwistIds:

            guide = layer.guide(segmentIds)
            if guide:
                guides.append(guide)
                matrices.append(guide.worldMatrix())
        # hivenodes.setGuidesWorldMatrix(guides, matrices)

        return guides, matrices

    def setupDeformLayer(self, parentJoint):
        definition = self.component.definition
        deformLayerDef = definition.deformLayer
        if not self.active():
            deformLayerDef.deleteJoints(*itertools.chain(self.segmentTwistIds))
            return
        # delete the existing joint defs, so we hive can delete the extra joints if needed
        guideLayerDef = definition.guideLayer
        deformLayerDef.deleteJoints(*tuple(self._deformTwistIdsIgnoreSettings()))
        for index, segment in enumerate(self.segmentTwistIds):
            twistGuideDefs = guideLayerDef.findGuides(*segment)
            twistutils.generateTwistJointsFromGuides(
                self.component,
                deformLayerDef,
                twistGuideDefs,
                guideLayerDef.guide(self.primaryIds[index]),
            )

    def setupOutputs(self, parentNode):
        if not self.active():
            return
        definition = self.component.definition
        guideLayerDef = definition.guideLayer  # type: definition.GuideLayerDefinition
        outputLayerDef = (
            definition.outputLayer
        )  # type: definition.OutputLayerDefinition
        naming = self.component.namingConfiguration()
        compName, compSide = self.component.name(), self.component.side()

        for index, segment in enumerate(self.segmentTwistIds):
            twistGuideDefs = guideLayerDef.findGuides(*segment)
            for twistGuide in twistGuideDefs:
                if outputLayerDef.output(twistGuide.id) is not None:
                    continue
                outputLayerDef.createOutput(
                    id=twistGuide.id,
                    name=naming.resolve(
                        "outputName",
                        {
                            "id": twistGuide.id,
                            "componentName": compName,
                            "side": compSide,
                            "type": "hiveOutput",
                        },
                    ),
                    parent=twistGuide.parent,
                    rotateOrder=twistGuide.rotateOrder,
                    worldMatrix=twistGuide.worldMatrix,
                )

    def preSetupRig(self, parentNode):
        """Here we generate the constants node and attributes for the twists.

        Note: at this point no scene state is changed
        """
        if not self.active():
            return
        guideLayerDef = self.component.definition.guideLayer
        rigLayer = self.component.definition.rigLayer
        flattenedTwistIds = list(itertools.chain(*self.segmentTwistIds))
        guideLayerSettings = guideLayerDef.guideSettings(*flattenedTwistIds)

        for settingId, guideSetting in guideLayerSettings.items():
            rigLayer.addSetting(
                "twistConstants",
                name=settingId,
                Type=guideSetting.Type,
                value=guideSetting.value,
            )
        for segmentPrefix in self.segmentTwistPrefixes:
            rigLayer.addSetting(
                "twistConstants",
                name="{}OffsetMatrix".format(segmentPrefix),
                Type=zapi.attrtypes.kMFnDataMatrix,
            )
        rigLayer.addSetting(
            constants.CONTROL_PANEL_TYPE,
            name="twistCtrlsVis",
            value=False,
            channelBox=True,
            keyable=False,
            Type=zapi.attrtypes.kMFnNumericBoolean,
        )

    def setupRig(self, parentNode):
        if not self.active():
            return
        self._doTwistSetup()

    def _doTwistSetup(self):
        """Generates the twist controls bound to the bind skeleton.
        This includes a master offset ctrl and per twist control.
        """
        component = self.component
        definition = component.definition
        guideLayer = definition.guideLayer
        controlPanel = component.controlPanel()
        deformLayer = component.deformLayer()
        rigLayer = component.rigLayer()

        twistOffsetGuides = guideLayer.findGuides(*self.segmentTwistOffsetIds)
        distributionStartGuides = guideLayer.findGuides(*self.rigDistributionStartIds)

        ctrlVisPlug = controlPanel.attribute("twistCtrlsVis")
        twistConstants = rigLayer.settingNode("twistConstants")

        for index, segment in enumerate(self.segmentTwistIds):
            prefix = self.segmentTwistPrefixes[index]
            offsetGuide = twistOffsetGuides[index]
            joints = deformLayer.findJoints(*segment)
            offsetPlug = twistConstants.attribute("{}OffsetMatrix".format(prefix))
            primaryStart, primaryEnd = rigLayer.findTaggedNodes(
                self.primaryIds[index], self.primaryIds[index + 1]
            )

            # create the Upr decompose
            twistControls, extras = twistutils.rigTwistJoints(
                component,
                rigLayer,
                guideLayer,
                twistOffsetGuide=offsetGuide,
                startGuide=distributionStartGuides[index],
                startEndSrt=(primaryStart, primaryEnd),
                twistJoints=joints,
                settingsNode=twistConstants,
                offsetMatrixPlug=offsetPlug,
                ctrlVisPlug=ctrlVisPlug,
                reverseFractions=self.twistReverseFractions[index],
                buildTranslation=self.buildTranslation,
            )
            for twistJoint, twistControl in zip(joints, twistControls):
                const, constUtilities = zapi.buildConstraint(twistJoint,
                                                             drivers={"targets": (
                                                                 (twistControl.fullPathName(partialName=True,
                                                                                            includeNamespace=False),
                                                                  twistControl),)},
                                                             constraintType="matrix",
                                                             decompose=True,
                                                             maintainOffset=False,
                                                             skipScale=(self.buildScale,
                                                                        self.buildScale,
                                                                        self.buildScale))

                rigLayer.addExtraNodes(constUtilities)
            rigLayer.addExtraNodes(extras)
