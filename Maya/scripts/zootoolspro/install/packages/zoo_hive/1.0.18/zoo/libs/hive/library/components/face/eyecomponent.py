from collections import OrderedDict

from zoo.libs.hive import api
from maya.api import OpenMaya as om2
from zoo.libs.hive.library.subsystems import eyelidsubsystem


class EyeComponent(api.Component):
    creator = "David Sparrow"
    description = "This component contains the neck and head controls"
    definitionName = "eyecomponent"
    uiData = {"icon": "head", "iconColor": (), "displayName": "Eye"}
    betaVersion = True

    def idMapping(self):
        subsystems = self.subsystems()
        lidSystem = subsystems["lids"]  # type: eyelidsubsystem.EyeLidsSubsystem
        rigLayerIds = {"eye": "eye", "eyeMain": "eyeMain", "pupil": "pupil", "iris": "iris"}
        deformIds = {"eye": "eye", "pupil": "pupil", "iris": "iris"}
        for curveId in eyelidsubsystem.CURVE_IDS:
            for ctrlId in (
                    lidSystem.guideCtrlIdsForCurve(curveId)
                    + [lidSystem.guidePrimaryCtrlIdForCurve(curveId)]
                    + lidSystem.startEndGuideCtrlIds(curveId)
            ):
                rigLayerIds[ctrlId] = ctrlId
            for jntId in lidSystem.startEndGuideJntIds(
                    curveId
            ) + lidSystem.guideJointIdsForCurve(curveId):
                deformIds[jntId] = jntId

        outputIds = {"eye": "eye", "neck": "neck"}
        inputIds = {"eyeTarget": "eyeTarget", "eye": "parent"}

        return {
            api.constants.DEFORM_LAYER_TYPE: deformIds,
            api.constants.INPUT_LAYER_TYPE: inputIds,
            api.constants.OUTPUT_LAYER_TYPE: outputIds,
            api.constants.RIG_LAYER_TYPE: rigLayerIds,
        }

    def createSubSystems(self):
        guideLayerDef = self.definition.guideLayer  # type: api.GuideLayerDefinition
        jntGuideSettings = guideLayerDef.guideSettings(
            *list(eyelidsubsystem.JOINT_COUNT_SETTING_NAMES)
        )
        hasPupilSetting = guideLayerDef.guideSetting("hasPupilIris")
        hasPupil = False
        if hasPupilSetting:
            hasPupil = hasPupilSetting.value

        systems = OrderedDict()
        systems["lids"] = eyelidsubsystem.EyeLidsSubsystem(
            self, jntGuideSettings, hasPupil
        )
        return systems

    def spaceSwitchUIData(self):
        drivers = []
        driven = [
            api.SpaceSwitchUIDriven(
                id_=api.pathAsDefExpression(("self", "rigLayer", "eyeTarget")),
                label="Eye Target",
            )
        ]

        for system in self.subsystems().values():
            system.driven = driven
            system.drivers = drivers

        return {"driven": driven, "drivers": drivers}

    def alignGuides(self):
        guides, matrices = [], []
        systems = list(self.subsystems().values())
        for system in systems:
            gui, mats = system.preAlignGuides()
            guides.extend(gui)
            matrices.extend(mats)
        if guides and matrices:
            api.setGuidesWorldMatrix(guides, matrices)
        for system in systems:
            system.postAlignGuides()

        return True

    def updateGuideSettings(self, settings):
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
        super(EyeComponent, self).updateGuideSettings(settings)
        if requiresRebuilds:
            self.rig.buildGuides([self])

        for subSystem in runPostUpdates:
            subSystem.postUpdateGuideSettings(settings)

    def preMirror(self, translate=("x",), rotate="yz", parent=om2.MObject.kNullObj):
        if not self.hasGuide():
            return []
        for system in self.subsystems().values():
            system.preMirror(translate, rotate, parent)

    def postMirror(self, translate=("x",), rotate="yz", parent=om2.MObject.kNullObj):
        if not self.hasGuide():
            return []
        for system in self.subsystems().values():
            system.postMirror(translate, rotate, parent)

    def preSetupGuide(self):
        for system in self.subsystems().values():
            system.preSetupGuide()
        super(EyeComponent, self).preSetupGuide()

    def setupGuide(self):
        for system in self.subsystems().values():
            system.setupGuide()

    def postSetupGuide(self):
        for system in self.subsystems().values():
            system.postSetupGuide()
        super(EyeComponent, self).postSetupGuide()

    def setupInputs(self):
        super(EyeComponent, self).setupInputs()
        for system in self.subsystems().values():
            system.setupInputs()

    def setupOutputs(self, parentNode):
        super(EyeComponent, self).setupOutputs(parentNode)
        for system in self.subsystems().values():
            system.setupOutputs(parentNode)

    def setupDeformLayer(self, parentNode=None):
        for system in self.subsystems().values():
            system.setupDeformLayer(parentNode)
        super(EyeComponent, self).setupDeformLayer(parentNode)

    def postSetupDeform(self, parentJoint):
        for system in self.subsystems().values():
            system.postSetupDeform(parentJoint)
        super(EyeComponent, self).postSetupDeform(parentJoint)

    def preSetupRig(self, parentNode):
        for system in self.subsystems().values():
            system.preSetupRig(parentNode)
        super(EyeComponent, self).preSetupRig(parentNode)

    def setupRig(self, parentNode):
        for system in self.subsystems().values():
            system.setupRig(parentNode)

    def postSetupRig(self, parentNode):
        for subSystem in self.subsystems().values():
            subSystem.postSetupRig(parentNode)

        super(EyeComponent, self).postSetupRig(parentNode)

    def postPolish(self):
        rigLayer = self.rigLayer()
        displayLayer = self.rig.controlDisplayLayer()
        nodes = []
        for curveId in eyelidsubsystem.CURVE_IDS:
            curveNode = rigLayer.taggedNode(curveId)
            if curveNode is None:
                continue
            nodes.append(curveNode)
        if nodes:
            displayLayer.addNodes(nodes)
        super(EyeComponent, self).postPolish()

    def setupSelectionSet(self, deformLayer, deformJoints):
        # when we have twist joints skip the upr/mid joints
        ignoredSkinJoints = ("eyeScale",)
        return [n for i, n in deformJoints.items() if i not in ignoredSkinJoints]
