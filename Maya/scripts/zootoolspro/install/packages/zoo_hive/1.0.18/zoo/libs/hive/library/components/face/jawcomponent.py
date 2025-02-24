from zoo.libs.hive import api
from zoo.libs.maya import zapi


class JawComponent(api.Component):
    creator = "DavidSparrow"
    description = "The Triple Jaw component which contains top lip, bottom lip and jaw"
    definitionName = "jaw"
    uiData = {
        "icon": "componentJaw",
        "iconColor": (),
        "displayName": "Jaw",
        "tooltip": description,
    }

    def idMapping(self):
        deformIds = {
            "topLip": "topLip",
            "jaw": "jaw",
            "chin": "chin",
            "botLip": "botLip",
        }
        outputIds = {
            "topLip": "topLip",
            "jaw": "jaw",
            "chin": "chin",
            "botLip": "botLip",
        }
        inputIds = {"jaw": "rootIn"}
        rigLayerIds = {
            "topLip": "topLip",
            "jaw": "jaw",
            "chin": "chin",
            "rotAll": "rotAll",
            "botLip": "botLip",
        }
        return {
            api.constants.DEFORM_LAYER_TYPE: deformIds,
            api.constants.INPUT_LAYER_TYPE: inputIds,
            api.constants.OUTPUT_LAYER_TYPE: outputIds,
            api.constants.RIG_LAYER_TYPE: rigLayerIds,
        }

    def spaceSwitchUIData(self):

        return {
            "driven": [
                api.SpaceSwitchUIDriven(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "rotAll")),
                    label="Rotate All",
                ),
                api.SpaceSwitchUIDriven(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "Jaw")),
                    label="Jaw",
                ),
                api.SpaceSwitchUIDriven(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "topLip")),
                    label="Top Lip",
                ),
                api.SpaceSwitchUIDriven(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "botLip")),
                    label="Bottom Lip",
                ),
                api.SpaceSwitchUIDriven(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "chin")),
                    label="Chin",
                ),
            ],
            "drivers": [
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "inputLayer", "root")),
                    label="Parent Component",
                    internal=True,
                ),
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "rotAll")),
                    label="Rotate All",
                ),
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "Jaw")),
                    label="Jaw",
                ),
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "topLip")),
                    label="Top Lip",
                ),
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "botLip")),
                    label="Bottom Lip",
                ),
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "chin")),
                    label="Chin",
                ),
            ],
        }

    def alignGuides(self):
        guideLayer = self.guideLayer()
        guidesToModify, matrices = [], []
        guides = {i.id(): i for i in guideLayer.iterGuides(includeRoot=True)}
        aimMapping = (
            (guides["jaw"], guides["chin"]),
            (guides["chin"], guides["jaw"]),
            (guides["topLip"], guides["jaw"]),
            (guides["botLip"], guides["jaw"]),
        )

        rootRotation = guides["root"].rotation(zapi.kWorldSpace, asQuaternion=True)
        for sourceGuide, targetGuide in aimMapping:
            if not sourceGuide.autoAlign.asBool():
                continue
            currentMatrix = sourceGuide.transformationMatrix()
            currentMatrix.setRotation(rootRotation)
            matrices.append(currentMatrix.asMatrix())
            guidesToModify.append(sourceGuide)
        if matrices:
            matrices.append(matrices[0])
            guidesToModify.append(guides["rotAll"])
            api.setGuidesWorldMatrix(guidesToModify, matrices)

    def setupInputs(self):
        super(JawComponent, self).setupInputs()
        inputLayer = self.inputLayer()
        guideDef = self.definition
        worldIn = inputLayer.inputNode("root")
        trans = guideDef.guideLayer.guide("jaw").transformationMatrix(scale=False)
        worldIn.setWorldMatrix(trans.asMatrix())

    def setupRig(self, parentNode):
        rigLayer = self.rigLayer()
        deformLayer = self.deformLayer()
        inputLayer = self.inputLayer()
        outputLayer = self.outputLayer()
        guideLayerDef = self.definition.guideLayer
        naming = self.namingConfiguration()
        outputs = {i.id(): i for i in outputLayer.outputs()}
        compName, compSide = self.name(), self.side()
        _ctrls = {}
        guides = {i.id: i for i in guideLayerDef.iterGuides(includeRoot=False)}
        controlTranslation = guides["jaw"].translate
        parentMap = (
            ("rotAll", "root"),
            ("jaw", "rotAll"),
            ("topLip", "rotAll"),
            ("chin", "jaw"),
            ("botLip", "jaw"),
        )
        for guideId, parent in parentMap:
            guidDef = guides[guideId]
            # create the control
            guidDef.name = naming.resolve(
                "controlName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": guidDef.id,
                    "type": "control",
                },
            )
            ctrl = rigLayer.createControl(
                name=guidDef.name,
                id=guideId,
                rotateOrder=guidDef.get("rotateOrder", 0),
                translate=controlTranslation,
                rotate=guidDef.rotate,
                parent=parent,
                shape=guidDef.get("shape"),
                selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                srts=[{"name": "_".join([guidDef.name, "srt"])}],
            )
            _ctrls[guideId] = ctrl

            output = outputs.get(guideId)
            if not output:
                continue
            if guideId in ("topLip", "jaw"):
                ctrl.worldMatrixPlug().connect(output.offsetParentMatrix)
            else:
                ctrl.attribute("matrix").connect(output.offsetParentMatrix)
            output.resetTransform()
            jnt = deformLayer.joint(guideId)
            if not jnt:
                continue

            const, constUtilities = api.buildConstraint(
                jnt,
                drivers={
                    "targets": (
                        (
                            ctrl.fullPathName(partialName=True, includeNamespace=False),
                            ctrl,
                        ),
                    )
                },
                constraintType="matrix",
                decompose=True,
                maintainOffset=True,
            )
            rigLayer.addExtraNodes(constUtilities)

        rootCtrl = _ctrls["rotAll"]
        # bind the root input node
        rootInput = inputLayer.inputNode("root")
        zapi.buildConstraint(
            rootCtrl.srt(),
            drivers={"targets": ((rootInput.name(includeNamespace=False), rootInput),)},
            maintainOffset=True,
            constraintType="matrix",
            trace=False,
        )

    def setupSelectionSet(self, deformLayer, deformJoints):
        """Overridden to ignore the chin and root jnts.

        :param deformLayer: The deformLayer instance
        :type deformLayer: :class:`layers.HiveDeformLayer`
        :param deformJoints: The joint id to joint map.
        :type deformJoints: dict[str, :class:`hnodes.Joint`]
        """
        return [v for k, v in deformJoints.items() if k != "jaw"]
