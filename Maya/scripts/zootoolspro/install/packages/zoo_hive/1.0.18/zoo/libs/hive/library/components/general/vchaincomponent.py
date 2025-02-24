from collections import OrderedDict

from zoo.libs.hive import api
from zoo.libs.hive.library.subsystems import ikfkblendsubsystem, fksubsystem, twoboneiksubsystem
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath
from maya.api import OpenMaya as om2

STRETCH_ATTRS = ("stretch", "maxStretch", "minStretch", "upperStretch", "lowerStretch")


class VChainComponent(api.Component):
    creator = "David Sparrow"
    definitionName = "vchaincomponent"
    uiData = {"icon": "componentVChain", "iconColor": (), "displayName": "VChain"}
    worldEndRotation = False
    worldEndAimGuideId = ""
    # used by the marking menu to determine whether to build the ikfk matching actions.
    hasIkFk = True
    rootIkVisCtrlName = "ikUprCtrlVis"

    # used internally to determine if the end guide should have default alignment behaviour
    # i.e. align to child vs matching parent rotations
    _resetEndGuideAlignment = True
    # Target guide for the end guide when _resetEndGuideAlignment is False
    _endGuideAlignTargetGuide = ""

    ikControlIds = ("endik", "upVec")
    fkControlIds = ("uprfk", "midfk", "endfk")
    deformJointIds = ("upr", "mid", "end")
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
                          ]

    def createSubSystems(self):
        ikGuideIds = [i + api.constants.IKTYPE for i in self.deformJointIds]
        systems = OrderedDict()
        systems["ik"] = twoboneiksubsystem.TwoBoneIkBlendSubsystem(self,
                                                                   list(self.deformJointIds),
                                                                   self.rootIkVisCtrlName,
                                                                   self._endGuideAlignTargetGuide,
                                                                   worldEndRotation=True,
                                                                   resetEndGuideAlignment=True)
        systems["fk"] = fksubsystem.FKSubsystem(self,
                                                self.deformJointIds,
                                                self.fkControlIds,
                                                "parentSpace"
                                                )
        systems["ikFk"] = ikfkblendsubsystem.IkFkBlendSubsystem(self,
                                                                self.deformJointIds,
                                                                self.fkControlIds,
                                                                ikGuideIds,
                                                                self.deformJointIds,
                                                                "ikfk",
                                                                "parentSpace"
                                                                )
        return systems

    def idMapping(self):
        deformIds = {"upr": "upr", "mid": "mid", "end": "end"}
        outputIds = {"upr": "upr", "mid": "mid", "end": "end"}
        inputIds = {"upr": "upr", "end": "end", "upVec": "upVec"}
        rigLayerIds = {"upVec": "upVec"}
        return {
            api.constants.DEFORM_LAYER_TYPE: deformIds,
            api.constants.INPUT_LAYER_TYPE: inputIds,
            api.constants.OUTPUT_LAYER_TYPE: outputIds,
            api.constants.RIG_LAYER_TYPE: rigLayerIds,
        }

    def spaceSwitchUIData(self):
        driven = self._spaceSwitchDriven
        # internal drivers ie. parent and World Space
        drivers = [
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

        drivers += list(self._spaceSwitchDrivers)

        return {"driven": driven, "drivers": drivers}

    def setupGuide(self):
        super(VChainComponent, self).setupGuide()
        for subSystem in self.subsystems().values():
            if subSystem.active():
                subSystem.setupGuide()

    def alignGuides(self):
        if not self.hasGuide():
            return False
        system = self.subsystems()["ik"]
        gui, mats = system.preAlignGuides()
        if gui and mats:
            api.setGuidesWorldMatrix(gui, mats)
        system.postAlignGuides()

    def preMirror(self, translate=("x",), rotate="yz", parent=om2.MObject.kNullObj):
        if not self.hasGuide():
            return []
        ikSystem = self.subsystems()["ik"]
        if ikSystem.active():
            ikSystem.preMirror(translate, rotate, parent)

    def postMirror(self, translate=("x",), rotate="yz", parent=om2.MObject.kNullObj):
        if not self.hasGuide():
            return []
        ikSystem = self.subsystems()["ik"]
        if ikSystem.active():
            ikSystem.postMirror(translate, rotate, parent)

    def setupInputs(self):
        super(VChainComponent, self).setupInputs()
        # bind the inputs and outputs to the deform joints
        inputLayer = self.inputLayer()
        rootIn, upVecIn, ikEndIn = inputLayer.findInputNodes("upr", "upVec", "endik")
        guideLayerDef = self.definition.guideLayer
        rootInMatrix = guideLayerDef.guide("upr").transformationMatrix(scale=False)
        # We don't propagate scale from the guide
        rootIn.setWorldMatrix(rootInMatrix.asMatrix())
        alignToWorldSetting = guideLayerDef.guideSetting("alignIkEndToWorld")
        alignToWorld = alignToWorldSetting.value if alignToWorldSetting is not None else False
        # We don't propagate scale from the guide
        if alignToWorld:
            ikEndInMatrix = guideLayerDef.guide("end").transformationMatrix(rotate=False, scale=False)
        elif not self.worldEndRotation:
            ikEndInMatrix = guideLayerDef.guide("end").transformationMatrix(scale=False)

        else:
            aimGuide, endGuide = guideLayerDef.findGuides(
                self.worldEndAimGuideId, "end"
            )
            rot = mayamath.lookAt(
                zapi.Vector(endGuide.translate),
                zapi.Vector(aimGuide.translate),
                mayamath.ZAXIS_VECTOR,
                mayamath.YAXIS_VECTOR,
                constrainAxis=zapi.Vector(0, 1, 1),
            )
            ikEndInMatrix = endGuide.transformationMatrix(rotate=False, scale=False)
            ikEndInMatrix.setRotation(rot)

        ikEndIn.setWorldMatrix(ikEndInMatrix.asMatrix())
        upVecInMatrix = guideLayerDef.guide("upVec").transformationMatrix(
            rotate=False, scale=False
        )
        upVecIn.setWorldMatrix(upVecInMatrix.asMatrix())

    def setupOutputs(self, parentNode):
        for subSystem in self.subsystems().values():
            if subSystem.active():
                subSystem.setupOutputs(parentNode)

        super(VChainComponent, self).setupOutputs(parentNode)
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
            output.setRotationOrder(driverJoint.rotationOrder())

    def preSetupRig(self, parentNode):
        """Overridden to handle stretch state, where we remove or add the anim stretch attributes.

        :param parentNode:
        :type parentNode: :class:`zapi.DagNode`
        """
        # stretch, lock, slide
        definition = self.definition
        hasStretch = definition.guideLayer.guideSetting("hasStretch").value
        rigLayer = definition.rigLayer  # type: api.RigLayerDefinition
        if not hasStretch:
            rigLayer.deleteSettings("controlPanel", STRETCH_ATTRS)
        else:
            orig = (
                self.definition.originalDefinition.rigLayer
            )  # type: api.RigLayerDefinition
            lastInsertName = "ikfk"
            for sett in STRETCH_ATTRS:
                origSetting = orig.setting("controlPanel", sett)
                if origSetting:
                    rigLayer.insertSettingByName(
                        "controlPanel", lastInsertName, origSetting, before=False
                    )
                    lastInsertName = origSetting.name
        super(VChainComponent, self).preSetupRig(parentNode)

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
        api.componentutils.createParentSpaceTransform(namer,
                                                      compName,
                                                      compSide,
                                                      rootTransform,
                                                      parentNode,
                                                      rigLayer,
                                                      rootIn)
        self._runSetupRigSubsystems(parentNode)

        fkCtrls = rigLayer.findControls(*self.fkControlIds)
        ikCtrls = rigLayer.findControls("baseik", "upVec", "endik")
        ikRootSrt = rigLayer.control("baseik").srt()
        annotation = rigLayer.annotation(rigLayer.joint("midik"), rigLayer.control("upVec"))
        api.componentutils.setupIkFkVisibility(self.namingConfiguration(),
                                               rigLayer,
                                               compName, compSide,
                                               fkCtrls, ikCtrls, annotation, ikRootSrt, blendAttr
                                               )

        endIkCtrl = rigLayer.control("endik")

        # for ikfk matching we need the initial matrix offset
        originalOffset = endIkCtrl.offsetMatrix(
            rigLayer.control("endfk"), zapi.kWorldSpace
        )
        rigLayer.settingNode("constants").attribute("constant_ikfkEndOffset").set(
            originalOffset
        )
    def _runSetupRigSubsystems(self, parentNode):
        for subSystem in self.subsystems().values():
            if subSystem.active():
                subSystem.setupRig(parentNode)

    def switchToIk(self):
        ikSystem = self.subsystems()["ik"]
        data = ikSystem.matchTo(*list(self.ikControlIds) + ["upVec"])
        ikfkAttr = self.controlPanel().attribute("ikfk")
        ikfkAttr.set(0)
        data["attributes"] = [ikfkAttr]
        return data

    def switchToFk(self):
        data = self.subsystems()["fk"].matchTo(self.deformLayer().findJoints(*self.deformJointIds))
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