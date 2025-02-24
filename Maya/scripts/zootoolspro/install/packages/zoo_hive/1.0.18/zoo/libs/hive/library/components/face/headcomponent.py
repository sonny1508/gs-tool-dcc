from zoo.libs.hive import api
from zoo.libs.maya import zapi


class HeadComponent(api.Component):
    creator = "David Sparrow"
    description = "This component contains the neck and head controls"
    definitionName = "headcomponent"
    uiData = {"icon": "head", "iconColor": (), "displayName": "Head"}

    def idMapping(self):
        deformIds = {"head": "head", "neck": "neck"}
        outputIds = {"head": "head", "neck": "neck"}
        inputIds = {"neck": "neck"}
        rigLayerIds = {"head": "head", "neck": "neck"}
        return {
            api.constants.DEFORM_LAYER_TYPE: deformIds,
            api.constants.INPUT_LAYER_TYPE: inputIds,
            api.constants.OUTPUT_LAYER_TYPE: outputIds,
            api.constants.RIG_LAYER_TYPE: rigLayerIds,
        }

    def spaceSwitchUIData(self):

        drivers = [
            api.SpaceSwitchUIDriver(
                id_=api.pathAsDefExpression(("self", "inputLayer", "neck")),
                label="Parent Component",
                internal=True,
            ),
            api.SpaceSwitchUIDriver(
                id_=api.pathAsDefExpression(("self", "inputLayer", "world")),
                label="World Space",
                internal=True,
            ),
        ]
        driven = [
            api.SpaceSwitchUIDriven(
                id_=api.pathAsDefExpression(("self", "rigLayer", "head")), label="Head"
            ),
            api.SpaceSwitchUIDriven(
                id_=api.pathAsDefExpression(("self", "rigLayer", "neck")), label="Neck"
            ),
        ]
        drivers += [api.SpaceSwitchUIDriver(**i.serialize()) for i in driven]

        return {"driven": driven, "drivers": drivers}

    def setupInputs(self):
        super(HeadComponent, self).setupInputs()
        inputLayer = self.inputLayer()
        guideDef = self.definition
        worldIn, parentIn = inputLayer.findInputNodes("world", "neck")
        neckMat = guideDef.guideLayer.guide("neck").transformationMatrix(scale=False)
        neckMatrix = neckMat.asMatrix()
        parentIn.setWorldMatrix(neckMatrix)
        worldIn.setWorldMatrix(neckMatrix)

    def setupOutputs(self, parentNode):
        super(HeadComponent, self).setupOutputs(parentNode)
        # connect the outputs to deform layer
        layer = self.outputLayer()
        joints = {jnt.id(): jnt for jnt in self.deformLayer().joints()}
        for index, output in enumerate(layer.outputs()):
            driverJoint = joints.get(output.id())

            if index == 0:
                const, constUtilities = api.buildConstraint(
                    output,
                    drivers={
                        "targets": (
                            (
                                driverJoint.fullPathName(
                                    partialName=True, includeNamespace=False
                                ),
                                driverJoint,
                            ),
                        )
                    },
                    constraintType="matrix",
                    maintainOffset=False,
                )
                layer.addExtraNodes(constUtilities)
            else:
                driverJoint.attribute("matrix").connect(output.offsetParentMatrix)
                output.resetTransform()

    def setupRig(self, parentNode):
        inputLayer = self.inputLayer()
        rigLayer = self.rigLayer()
        definition = self.definition
        guideLayerDef = definition.guideLayer
        naming = self.namingConfiguration()
        compName, compSide = self.name(), self.side()
        # predefine nodes
        parentIn = inputLayer.inputNode("neck")
        # parentIn.resetTransform()
        ctrlRoot = zapi.createDag(
            "parentSpace", "transform", parent=rigLayer.rootTransform()
        )
        neckDef, headDef = guideLayerDef.findGuides("neck", "head")
        ctrlRoot.setWorldMatrix(neckDef.transformationMatrix(scale=False).asMatrix())
        rigLayer.addExtraNode(ctrlRoot)

        # bind the parent Space to the parent_in input
        const, constUtilities = zapi.buildConstraint(
            ctrlRoot,
            {
                "targets": (("", parentIn),),
            },
            constraintType="matrix",
            maintainOffset=True,
            trace=False,
        )
        rigLayer.addExtraNodes(constUtilities)

        # neck control
        neckDef.name = naming.resolve(
            "controlName",
            {
                "componentName": compName,
                "side": compSide,
                "id": neckDef.id,
                "type": "control",
            },
        )

        neckControl = rigLayer.createControl(
            name=neckDef.name,
            id=neckDef.id,
            rotateOrder=neckDef.get("rotateOrder", 0),
            translate=neckDef.get("translate", (0, 0, 0)),
            rotate=neckDef.get("rotate", (0, 0, 0, 1)),
            parent=ctrlRoot,
            shape=neckDef.get("shape"),
            selectionChildHighlighting=self.configuration.selectionChildHighlighting,
            srts=[{"id": neckDef.id, "name": "_".join([neckDef.name, "srt"])}],
        )
        # head control
        headDef.name = naming.resolve(
            "controlName",
            {
                "componentName": compName,
                "side": compSide,
                "id": headDef.id,
                "type": "control",
            },
        )
        headControl = rigLayer.createControl(
            name=headDef.name,
            id=headDef.id,
            rotateOrder=headDef.get("rotateOrder", 0),
            translate=headDef.get("translate", (0, 0, 0)),
            rotate=headDef.get("rotate", (0, 0, 0, 1)),
            parent=headDef.parent,
            shape=headDef.get("shape"),
            selectionChildHighlighting=self.configuration.selectionChildHighlighting,
            srts=[{"id": neckDef.id, "name": "_".join([neckDef.name, "srt"])}]
        )

        # bind the outputs to deform joints
        deformLayer = self.deformLayer()
        neckJnt, headJnt = deformLayer.findJoints("neck", "head")

        _buildConstraint(neckJnt, neckControl, rigLayer)
        _buildConstraint(headJnt, headControl, rigLayer)


def _buildConstraint(driven, driver, rigLayer):

    _, constUtilities = api.buildConstraint(
        driven,
        drivers={"targets": (("", driver),)},
        constraintType="matrix",
        maintainOffset=True,
        decompose=True,
    )
    rigLayer.addExtraNodes(constUtilities)
