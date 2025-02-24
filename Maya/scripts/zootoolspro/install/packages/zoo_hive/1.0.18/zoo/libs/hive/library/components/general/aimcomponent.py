from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath


class AimComponent(api.Component):
    creator = "David Sparrow"
    definitionName = "aimcomponent"
    uiData = {"icon": "componentAim", "iconColor": (), "displayName": "Aim"}

    def idMapping(self):
        deformIds = {"eye": "eye"}
        outputIds = {"eye": "root", "aim": "aim"}
        inputIds = {"eye": "root"}
        rigLayerIds = {"eye": "eye", "aim": "aim"}
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
                    id_=api.pathAsDefExpression(("self", "rigLayer", "eye")),
                    label="Eye",
                ),
                api.SpaceSwitchUIDriven(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "aim")),
                    label="Aim",
                ),
            ],
            "drivers": [
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "inputLayer", "root")),
                    label="Parent Component",
                    internal=True,
                ),
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "eye")),
                    label="Eye",
                ),
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "rigLayer", "aim")),
                    label="Aim",
                ),
            ],
        }

    def alignGuides(self):
        if not self.hasGuide():
            return
        guideLayer = self.guideLayer()
        eye, aim, upVec = guideLayer.findGuides("eye", "aim", "upVec")
        if not eye.autoAlign.asBool():
            return []
        upVector = eye.autoAlignUpVector.value()
        aimVector = eye.autoAlignAimVector.value()
        normal = (
            upVec.translation(zapi.kWorldSpace) - eye.translation(zapi.kWorldSpace)
        ).normalize()
        eyeQuat = mayamath.lookAt(
            sourcePosition=eye.translation(),
            aimPosition=aim.translation(),
            aimVector=zapi.Vector(aimVector),
            upVector=zapi.Vector(upVector),
            worldUpVector=normal
        )
        eyeMtx = eye.transformationMatrix()
        eyeMtx.setRotation(eyeQuat)

        aimQuat = mayamath.lookAt(
            sourcePosition=aim.translation(),
            aimPosition=eye.translation(),
            aimVector=zapi.Vector(aim.autoAlignAimVector.value()),
            upVector=zapi.Vector(aim.autoAlignUpVector.value()) ,

        )
        aimMtx = aim.transformationMatrix()
        aimMtx.setRotation(aimQuat)

        api.setGuidesWorldMatrix([eye, aim], [eyeMtx.asMatrix(), aimMtx.asMatrix()])

    def setupInputs(self):
        super(AimComponent, self).setupInputs()
        inputLayer = self.inputLayer()
        guideDef = self.definition
        rootIn = inputLayer.inputNode("root")
        rootMat = guideDef.guideLayer.guide("eye").transformationMatrix(scale=False)
        rootIn.setWorldMatrix(rootMat.asMatrix())

    def setupRig(self, parentNode):
        rigLayer = self.rigLayer()
        rigLayerTransform = rigLayer.rootTransform()
        deformLayer = self.deformLayer()
        outputLayer = self.outputLayer()
        inputLayer = self.inputLayer()
        namer = self.namingConfiguration()
        rootIn = inputLayer.inputNode("root")
        deformJoint = deformLayer.joint("eye")
        rootOut = outputLayer.outputNode("root")
        definition = self.definition
        guideLayer = definition.guideLayer
        eyeDef = guideLayer.guide("eye")
        compName, compSide = self.name(), self.side()
        extraNodes = []
        # create parent offset for deformLayer
        controls = {}
        for index, guidDef in enumerate((guideLayer.guide("aim"), eyeDef)):
            # create the control
            guideId = guidDef.id
            name = namer.resolve(
                "controlName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": guideId,
                    "type": "control",
                },
            )
            ctrl = rigLayer.createControl(
                name=name,
                id=guideId,
                rotateOrder=guidDef.get("rotateOrder", 0),
                translate=guidDef.get("translate", (0, 0, 0)),
                rotate=guidDef.get("rotate", (0, 0, 0, 1)),
                parent=None,
                shape=guidDef.get("shape"),
                selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                srts=[{"id": guideId, "name": "_".join([name, "srt"])}],
            )

            controls[guideId] = ctrl
            # # create the output node
            out = outputLayer.outputNode(guideId)
            if out is None:
                continue
            const, constUtilities = zapi.buildConstraint(
                out,
                {
                    "targets": (
                        (
                            ctrl.fullPathName(partialName=True, includeNamespace=True),
                            ctrl,
                        ),
                    )
                },
                constraintType="matrix",
                maintainOffset=False,
            )

            extraNodes.extend(constUtilities)

        aimDef = guideLayer.guide("upVec")
        aimUpVec = api.createDag(aimDef.name, "transform")
        aimUpVec.setWorldMatrix(api.Matrix(aimDef.worldMatrix))
        aimUpVec.setParent(rigLayerTransform)
        # constrain the UpVec to the root input that way it follows based on the incoming parent transform
        const, constUtilities = api.buildConstraint(
            aimUpVec,
            drivers={
                "targets": (
                    (
                        "",
                        rootIn,
                    ),
                )
            },
            maintainOffset=True,
            constraintType="matrix",
        )
        extraNodes.extend(constUtilities)
        # srt which will be constrained by the aim
        aimSpaceSrt = rigLayer.createSrtBuffer("eye", "_".join([eyeDef.name, "srt"]))
        aimControl = controls["aim"]
        aimControl.setLockStateOnAttributes(zapi.localScaleAttrs+zapi.localRotateAttrs, False)
        aimControl.showHideAttributes(zapi.localScaleAttrs+zapi.localRotateAttrs, False)
        const, constUtilities = api.buildConstraint(
            aimSpaceSrt,
            drivers={
                "targets": (
                    (
                        "",
                        aimControl,
                    ),
                )
            },
            constraintType="aim",
            worldUpType=1,
            aimVector=list(
                eyeDef.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
            ),
            worldUpObject=aimUpVec.fullPathName(),
            maintainOffset=True,
        )
        extraNodes.extend(constUtilities)
        rootEyeSrt = controls["eye"].srt()
        # bind deform joints to the ctrl
        extraNodes.extend(
            zapi.buildConstraint(
                deformJoint,
                {"targets": (("eye", controls["eye"]),)},
                constraintType="matrix",
                maintainOffset=True,
                trace=False,
                decompose=True
            )[1]
        )
        extraNodes.extend(
            zapi.buildConstraint(
                rootEyeSrt,
                {"targets": (("parent", rootIn),)},
                constraintType="matrix",
                maintainOffset=True,
                trace=False,
            )[1]
        )
        extraNodes.extend(
            zapi.buildConstraint(
                rootOut,
                {"targets": (("parent", deformJoint),)},
                constraintType="matrix",
                maintainOffset=True,
                trace=False,
            )[1]
        )
        rigLayer.addExtraNodes(extraNodes)
        pick = zapi.createDG("", "pickMatrix")
        pick.useTranslate.set(0)
        pick.useRotate.set(0)
        inputLayer.inputNode("root").worldMatrixPlug().connect(pick.inputMatrix)
        pick.outputMatrix.connect(aimControl.srt().offsetParentMatrix)

