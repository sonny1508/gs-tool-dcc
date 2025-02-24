from zoo.libs.hive import api
from zoo.libs.maya import zapi

_GODNODE_ID = "godnode"


class GodNodeComponent(api.Component):
    creator = "David Sparrow"
    description = "This component is the master ctrl of all rigs"
    definitionName = "godnodecomponent"
    uiData = {"icon": "circle", "iconColor": (), "displayName": "God Node"}

    def idMapping(self):
        deformIds = {"rootMotion": "godnode",
                     "offset": "godnode",
                     "godnode": "godnode"}
        outputIds = {"godnode": "godnode",
                     "offset": "offset",
                     "rootMotion": "rootMotion"}
        inputIds = {"godnode": "godnode"}
        rigLayerIds = {"godnode": "godnode",
                       "offset": "offset",
                       "rootMotion": "rootMotion"}
        return {api.constants.DEFORM_LAYER_TYPE: deformIds,
                api.constants.INPUT_LAYER_TYPE: inputIds,
                api.constants.OUTPUT_LAYER_TYPE: outputIds,
                api.constants.RIG_LAYER_TYPE: rigLayerIds}

    def spaceSwitchUIData(self):
        drivers = []
        guideLayerDef = self.definition.guideLayer
        for guide in guideLayerDef.iterGuides(includeRoot=False):
            drivers.append(api.SpaceSwitchUIDriver(id_=api.pathAsDefExpression(("self", "rigLayer", guide.id)),
                                                   label=guide.name))
        return {
            "driven": [],
            "drivers": drivers
        }

    def postSetupGuide(self):
        super(GodNodeComponent, self).postSetupGuide()
        # overridden to setup guide visibility

        guideLayer = self.guideLayer()
        guideSettings = guideLayer.guideSettings()
        godnodeGuide, offsetGuide, rootMotion = guideLayer.findGuides("godnode", "offset", "rootMotion")

        for shape in godnodeGuide.iterShapes():

            vis = shape.visibility
            if vis.isDestination or vis.isLocked:
                continue
            guideSettings.godNodeVis.connect(vis)
        for shape in offsetGuide.iterShapes():
            vis = shape.visibility
            if vis.isDestination or vis.isLocked:
                continue
            guideSettings.offsetVis.connect(vis)
        for shape in rootMotion.iterShapes():
            vis = shape.visibility
            if vis.isDestination or vis.isLocked:
                continue
            guideSettings.rootMotionVis.connect(vis)
    def setupInputs(self):
        super(GodNodeComponent, self).setupInputs()
        definition = self.definition
        inputLayer = self.inputLayer()
        godNodeDef = definition.guideLayer.guide("godnode")

        inputNode = inputLayer.inputNode(godNodeDef.id)
        upVecInMatrix = godNodeDef.transformationMatrix(scale=False)
        inputNode.setWorldMatrix(upVecInMatrix.asMatrix())

    def setupDeformLayer(self, parentJoint=None):
        # build skin joints if any
        definition = self.definition
        deformLayerDef = definition.deformLayer
        guideLayerDef = definition.guideLayer
        requiresJoint = guideLayerDef.guideSetting("rootJoint").value
        hasExistingJoint = deformLayerDef.joint(_GODNODE_ID)
        if requiresJoint and not hasExistingJoint:
            guideDef = guideLayerDef.guide("godnode")

            deformLayerDef.createJoint(name=guideDef.name,
                                       id=_GODNODE_ID,
                                       rotateOrder=guideDef.get("rotateOrder", 0),
                                       translate=guideDef.get("translate", (0, 0, 0)),
                                       rotate=guideDef.get("rotate", (0, 0, 0, 1)),
                                       parent=None
                                       )
        elif not requiresJoint and hasExistingJoint:
            deformLayerDef.deleteJoints(_GODNODE_ID)

        super(GodNodeComponent, self).setupDeformLayer(parentNode=parentJoint)

    def setupSelectionSet(self, deformLayer, deformJoints):
        # do nothing as we don't want the root to be displayed as a skinned joint
        return []

    def setupOutputs(self, parentNode):
        definition = self.definition
        guideLayer = definition.guideLayer
        outputLayerDef = definition.outputLayer
        requiresJoint = guideLayer.guideSetting("rootJoint").value
        if not requiresJoint:
            outputLayerDef.deleteOutputs("rootMotion")
            outputLayer = self.outputLayer()
            if outputLayer is not None:
                outputLayer.deleteOutput("rootMotion")
        else:
            name = self.namingConfiguration().resolve("outputName", {"componentName": self.name(),
                                                                     "side": self.side(),
                                                                     "id": "rootMotion",
                                                                     "type": "output"})
            outputLayerDef.createOutput(id="rootMotion",
                                        name=name,
                                        hiveType="output",
                                        parent="offset"
                                        )
        super(GodNodeComponent, self).setupOutputs(parentNode)

    def setupRig(self, parentNode):
        guideLayerDef = self.definition.guideLayer
        controlPanel = self.controlPanel()
        rigLayer = self.rigLayer()
        inputLayer = self.inputLayer()
        ctrls = {}
        requiresJoint = guideLayerDef.guideSetting("rootJoint").value
        naming = self.namingConfiguration()
        compName, side = self.name(), self.side()
        for guide in guideLayerDef.iterGuides(False):
            if guide.id == "rootMotion" and not requiresJoint:
                continue
            name = naming.resolve("controlName", {"componentName": compName,
                                                  "side": side,
                                                  "id": guide.id,
                                                  "type": "control"})
            cont = rigLayer.createControl(name=name,
                                          id=guide.id,
                                          translate=guide.translate,
                                          rotate=guide.rotate,
                                          parent=guide.parent,
                                          shape=guide.shape,
                                          rotateOrder=guide.rotateOrder,
                                          selectionChildHighlighting=self.configuration.selectionChildHighlighting)

            ctrls[guide.id] = cont
            srt = rigLayer.createSrtBuffer(guide.id, "_".join([cont.name(False), "srt"]))

            inputNode = inputLayer.inputNode(guide.id)
            if not inputNode:
                continue
            inputNode.attribute("worldMatrix")[0].connect(srt.offsetParentMatrix)
            srt.resetTransform()
        controlPanel.displayOffset.connect(ctrls["offset"].visibility)
        ctrls["offset"].visibility.hide()
        if requiresJoint:
            # bind the root joint to the root motion ctrl
            rootJoint = self.deformLayer().joint(_GODNODE_ID)
            rootMotionCtrl = ctrls["rootMotion"]
            controlPanel.displayRootMotion.connect(rootMotionCtrl.visibility)
            rootMotionCtrl.visibility.hide()

            constraint, constUtilities = zapi.buildConstraint(rootJoint,
                                                              drivers={"targets": (
                                                                  (rootMotionCtrl.fullPathName(partialName=True,
                                                                                               includeNamespace=False),
                                                                   rootMotionCtrl),)},
                                                              constraintType="matrix",
                                                              maintainOffset=False,
                                                              decompose=True)
            rigLayer.addExtraNodes(constUtilities)

    def postSetupRig(self, parentNode):
        outputLayer = self.outputLayer()
        rigLayer = self.rigLayer()
        outputs = outputLayer.findOutputNodes(_GODNODE_ID, "offset", "rootMotion")
        ctrls = rigLayer.findControls(_GODNODE_ID, "offset", "rootMotion")
        for index, outputCtrl in enumerate(zip(outputs, ctrls)):
            output, control = outputCtrl
            if control is None:
                continue
            if index == 0:
                const, constUtilities = api.buildConstraint(output,
                                                            drivers={"targets": ((control.fullPathName(partialName=True,
                                                                                                       includeNamespace=False),
                                                                                  control),)},
                                                            constraintType="matrix",
                                                            maintainOffset=False)
                rigLayer.addExtraNodes(constUtilities)
            else:
                control.attribute("matrix").connect(output.offsetParentMatrix)
                output.resetTransform()
        super(GodNodeComponent, self).postSetupRig(parentNode)
