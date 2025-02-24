from zoo.libs.hive import api
from zoo.libs.hive.base import basesubsystem
from zoo.libs.hive.base.util import ikutils, componentutils
from zoo.libs.maya import zapi
from zoo.libs.maya.rig import align, skeletonutils
from zoo.libs.maya.utils import mayamath
from zoo.libs.utils import general

from maya import cmds


class TwoBoneIkBlendSubsystem(basesubsystem.BaseSubsystem):
    """The TwoBoneIkBlendSubsystem class represents a subsystem for blending two-bone inverse kinematics (IK) in a rig.


    :param component: The component associated with this subsystem.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param rootIkVisAttrName: The name of the attribute controlling the root IK visibility.
    :type rootIkVisAttrName: str
    :param endGuideAlignTargetGuide: The name of the guide to which the end guide should align.
    :type endGuideAlignTargetGuide: str
    :param resetEndGuideAlignment: Whether to reset the end guide alignment.
    :type resetEndGuideAlignment: bool
    :param flipAutoAlignUpVector: Whether to flip
    :type flipAutoAlignUpVector: bool
    """

    def __init__(
            self,
            component,
            primaryIds,
            rootIkVisAttrName,
            endGuideAlignTargetGuide,
            resetEndGuideAlignment=False,
            flipAutoAlignUpVector=False,
            worldEndRotation=False
    ):
        # todo: upVec id as provided input to class
        super(TwoBoneIkBlendSubsystem, self).__init__(component)
        self.primaryIds = primaryIds
        self.rootParentId = "parentSpace"
        self.rootIkVisCtrlName = rootIkVisAttrName
        self.worldEndRotation = worldEndRotation
        self._resetEndGuideAlignment = resetEndGuideAlignment
        self._flipAutoAlignUpVector = flipAutoAlignUpVector
        self._endGuideAlignTargetGuide = endGuideAlignTargetGuide
        self._ctrls = {}

    def matchTo(self, endIk, upVec, upVecGuideId):
        deformLayer = self.component.deformLayer()
        rigLayer = self.component.rigLayer()
        endIk, upVec = rigLayer.findControls(endIk, upVec)
        deformJoints = deformLayer.findJoints(*self.primaryIds)
        midGuide, upVecGuide = self.component.definition.guideLayer.findGuides(
            "mid", upVecGuideId
        )
        distance = (midGuide.translate - upVecGuide.translate).length()
        try:
            pvPosition = skeletonutils.poleVectorPosition(
                deformJoints[0].translation(),
                deformJoints[1].translation(),
                deformJoints[2].translation(),
                distance=distance,
            )
        except ValueError:
            pvPosition = deformJoints[1].translation()
        originalOffset = (
            rigLayer.settingNode("constants")
            .attribute("constant_ikfkEndOffset")
            .value()
        )
        endMatrix = (
                originalOffset.inverse()
                * deformJoints[2].worldMatrix()
                * endIk.parentInverseMatrix()
        )

        endIk.setMatrix(endMatrix)
        upVec.setTranslation(pvPosition, space=zapi.kWorldSpace)

        return {"controls": [endIk, upVec], "selectables": [endIk]}

    def prePlacePoleVectorSensibly(self):
        upVecGuideId = "upVec"
        rigLayer = self.component.rigLayer()
        pvCtrl = rigLayer.control(upVecGuideId)
        midGuide, upVecGuide = self.component.definition.guideLayer.findGuides(
            "mid", upVecGuideId
        )
        distance = (midGuide.translate - upVecGuide.translate).length()
        return {
            "upVecControl": pvCtrl,
            "upVectorDistance": distance,
            "joints": self.component.deformLayer().findJoints("upr", "mid", "end"),
            "transform": pvCtrl.worldMatrix(),
        }

    def placePoleVectorSensibly(self, info, keyRange=()):
        distance = info["upVectorDistance"]
        ctrl = info["upVecControl"]
        joints = info["joints"]
        pvPosition = skeletonutils.poleVectorPosition(
            joints[0].translation(),
            joints[1].translation(),
            joints[2].translation(),
            distance=distance,
        )
        ctrl.setTranslation(pvPosition, space=zapi.kWorldSpace)
        fullPathName = ctrl.fullPathName()
        if keyRange:
            cmds.setKeyframe(
                fullPathName,
                attribute=zapi.localTransformAttrs,
                time=keyRange,
            )

    def preAlignGuides(self):
        if not self.active():
            return [], []
        guideLayer = self.component.guideLayer()
        # align the vchain guides with coplanar, align all others as normal
        uprGuide, midGuide, endGuide, upVector = guideLayer.findGuides(*self.primaryIds + ["upVec"])
        vChainGuides = [uprGuide, midGuide, endGuide]

        constructedPlane = componentutils.worldUpVectorAsPlaneLegacy(
            uprGuide, endGuide
        )
        uprGuide.setLockStateOnAttributes(zapi.localRotateAttrs, False)
        midGuide.setLockStateOnAttributes(zapi.localRotateAttrs+zapi.localTransformAttrs, False)
        zapi.deleteConstraints([uprGuide, midGuide] + list(midGuide.iterSrts()))

        guides, matrices = [], []

        for currentGuide, targetGuide in align.alignNodesIterator(
                vChainGuides, constructedPlane, skipEnd=False
        ):
            if targetGuide is None or not currentGuide.autoAlign.asBool():
                continue

            upVector = currentGuide.autoAlignUpVector.value()
            aimVector = currentGuide.autoAlignAimVector.value()
            rot = mayamath.lookAt(
                currentGuide.translation(zapi.kWorldSpace),
                targetGuide.translation(zapi.kWorldSpace),
                aimVector=zapi.Vector(aimVector),
                upVector=zapi.Vector(upVector),
                worldUpVector=constructedPlane.normal(),
            )
            transform = currentGuide.transformationMatrix()
            transform.setRotation(rot)
            matrices.append(transform.asMatrix())
            guides.append(currentGuide)

        if endGuide.autoAlign.asBool():
            transform = endGuide.transformationMatrix()
            if self._resetEndGuideAlignment:
                midRotation = zapi.TransformationMatrix(matrices[-1]).rotation(
                    zapi.kWorldSpace
                )
                transform.setRotation(midRotation)
                matrices.append(transform.asMatrix())
                guides.append(endGuide)
            else:
                upVector = endGuide.autoAlignUpVector.value()
                aimVector = endGuide.autoAlignAimVector.value()
                child = guideLayer.guide(self._endGuideAlignTargetGuide)
                rot = mayamath.lookAt(
                    endGuide.translation(zapi.kWorldSpace),
                    child.translation(zapi.kWorldSpace),
                    aimVector=zapi.Vector(aimVector),
                    upVector=zapi.Vector(upVector),
                )
                transform.setRotation(rot)
                matrices.append(transform.asMatrix())
                guides.append(endGuide)
        return guides, matrices

    def postAlignGuides(self):
        if not self.active():
            return
        self._constructAutoAlignment(self.component.guideLayer())
        upVecDef = self.component.definition.guideLayer.guide("upVec")
        upVec = self.component.guideLayer().guide("upVec")
        upVec.setTranslation(upVecDef.translate, zapi.kWorldSpace)

    def setupGuide(self):
        if not self.active():
            return
        self._constructAutoAlignment(self.component.guideLayer())

    def preMirror(self, translate, rotate, parent):
        guideLayer = self.component.guideLayer()
        uprGuide, midGuide, endGuide = guideLayer.findGuides(*self.primaryIds)
        uprGuide.setLockStateOnAttributes(zapi.localRotateAttrs, False)
        midGuide.setLockStateOnAttributes(zapi.localTransformAttrs, False)
        zapi.deleteConstraints([uprGuide, midGuide] + list(midGuide.iterSrts()))

    def postMirror(self, translate, rotate, parent):
        pass

    def _constructAutoAlignment(self, guideLayer):
        uprGuide, midGuide, endGuide = guideLayer.findGuides(
            *self.primaryIds
        )

        # align the vchain guides with coplanar, align all others as normal
        midTranslation = midGuide.translation(zapi.kWorldSpace)
        uprGuide.setLockStateOnAttributes(zapi.localRotateAttrs, False)
        midGuide.setLockStateOnAttributes(zapi.localTransformAttrs, False)
        zapi.deleteConstraints([uprGuide, midGuide] + list(midGuide.iterSrts()))
        _, utilities = zapi.buildConstraint(midGuide.srt(),
                                            constraintType="point",
                                            drivers={"targets": (("upr", uprGuide),
                                                                 ("end", endGuide))},
                                            maintainOffset=False, trace=True)
        guideLayer.addExtraNodes(utilities)
        midGuide.setTranslation(midTranslation, zapi.kWorldSpace)

        ikutils.createGuideAimConstraint(self, guideLayer, endGuide, uprGuide, midGuide, useWorldUpVecGuide=True)
        ikutils.createGuideAimConstraint(self, guideLayer, uprGuide, midGuide, endGuide)

        ikutils.createAutoPoleGuideGraph(
            self.component,
            self.component.guideLayer(),
            "autoPoleVector",
            self.primaryIds,
            "upVec",
        )
        uprGuide.setLockStateOnAttributes(zapi.localRotateAttrs, True)
        midGuide.setLockStateOnAttributes(zapi.localRotateAttrs, True)

    def setupRig(self, parentNode):
        if not self.active():
            return

        rigLayer = self.component.rigLayer()
        controlPanel = self.component.controlPanel()
        inputLayer = self.component.inputLayer()
        definition = self.component.definition
        namer = self.component.namingConfiguration()
        guideLayerDef = definition.guideLayer
        ikGuides = guideLayerDef.findGuides(*self.primaryIds)
        rigLayerRoot = rigLayer.rootTransform()
        compName, compSide = self.component.name(), self.component.side()
        rootIn, ikEndIn, upVecIn = inputLayer.findInputNodes("upr", "endik", "upVec")

        # presize our data
        # todo: move to the definition
        ikJoints = [None] * 3  # type: list[None or api.Joint]

        ikParent = rigLayer.taggedNode(self.rootParentId)

        upvecGuide = guideLayerDef.guide("upVec")

        upVecName = namer.resolve(
            "controlName",
            {
                "componentName": compName,
                "side": compSide,
                "system": "poleVector",
                "id": upvecGuide.id,
                "type": "control",
            },
        )

        upVecCtrl = rigLayer.createControl(
            name=upVecName,
            id=upvecGuide.id,
            translate=upvecGuide.translate,
            rotate=(0.0, 0.0, 0.0, 1.0),
            parent=rigLayerRoot,
            shape=upvecGuide.shape,
            rotateOrder=upvecGuide.rotateOrder,
            selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
            srts=[{"name": "_".join([upVecName, "srt"]), "id": upvecGuide.id}],
        )

        self._ctrls[upvecGuide.id] = upVecCtrl

        for i, guide in enumerate(ikGuides):
            guideId = guide.id

            ikGuideId = guideId + api.constants.IKTYPE

            ikName = namer.resolve(
                "jointName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": ikGuideId,
                    "system": api.constants.IKTYPE,
                    "type": "joint",
                },
            )

            # ik
            ikJnt = rigLayer.createJoint(
                name=ikName,
                translate=guide.translate,
                rotate=guide.rotate,
                parent=ikParent,
                rotateOrder=guide.rotateOrder,
                id=ikGuideId,
            )
            ikJoints[i] = ikJnt
            ikParent = ikJnt

            # we are currently on the end guide
            guideName = guide.id
            if guideName == "end":
                ikName = namer.resolve(
                    "controlName",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "id": ikGuideId,
                        "system": api.constants.IKTYPE,
                        "type": "control",
                    },
                )
                ctrl = rigLayer.createControl(
                    name=ikName,
                    id=ikGuideId,
                    translate=guide.translate,
                    rotate=guide.rotate
                    if not self.worldEndRotation
                    else ikEndIn.rotation(space=zapi.kWorldSpace),
                    parent=rigLayerRoot,
                    rotateOrder=guide.rotateOrder,
                    shape=guide.shape,
                    shapeTransform=guide.shapeTransform,
                    selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                    srts=[{"name": "_".join([ikName, "srt"])}],
                )
                self._ctrls[ikGuideId] = ctrl

                const, constUtilities = api.buildConstraint(
                    ikJnt,
                    drivers={
                        "targets": (
                            (
                                ctrl.fullPathName(
                                    partialName=True, includeNamespace=False
                                ),
                                ctrl,
                            ),
                        )
                    },
                    constraintType="orient",
                    maintainOffset=True,
                )
                rigLayer.addExtraNodes(constUtilities)
                ctrl.connect("scale", ikJnt.attribute("scale"))

        # ikRoot control
        guide = ikGuides[0]
        baseikName = namer.resolve(
            "controlName",
            {
                "componentName": compName,
                "side": compSide,
                "system": api.constants.IKTYPE,
                "id": "baseik",
                "type": "control",
            },
        )
        ikRootCtrl = rigLayer.createControl(
            name=baseikName,
            id="baseik",
            translate=guide.translate,
            rotate=guide.rotate,
            parent=rigLayerRoot,
            rotateOrder=guide.rotateOrder,
            shape=guide.shape,
            shapeTransform=guide.shapeTransform,
            selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
            srts=[{"name": "_".join([baseikName, "srt"]), "id": "baseik"}],
        )
        controlPanel.attribute(self.rootIkVisCtrlName).connect(ikRootCtrl.visibility)
        ikRootCtrl.setLockStateOnAttributes(("rotate", "scale", "visibility"))
        ikRootCtrl.showHideAttributes(
            zapi.localRotateAttrs + zapi.localScaleAttrs, False
        )
        self._ctrls["baseik"] = ikRootCtrl
        const, constUtilities = api.buildConstraint(
            ikJoints[0],
            drivers={"targets": (("baseik", ikRootCtrl),)},
            constraintType="point",
            maintainOffset=True,
        )
        rigLayer.addExtraNodes(constUtilities)
        const, constUtilities = api.buildConstraint(
            ikJoints[0],
            drivers={"targets": (("baseik", ikRootCtrl),)},
            constraintType="orient",
            maintainOffset=True,
        )
        rigLayer.addExtraNodes(constUtilities)
        const, constUtilities = api.buildConstraint(
            ikRootCtrl.srt(),
            drivers={
                "targets": (
                    (
                        rootIn.fullPathName(partialName=True, includeNamespace=False),
                        rootIn,
                    ),
                )
            },
            constraintType="matrix",
            maintainOffset=True,
        )
        rigLayer.addExtraNodes(constUtilities)

        # take the scale from the Upr Input node and multiply that by the input for each IK srt other than baseIK
        # this will give us the scale support without reaching externally of the component IO
        endIkCtrl = self._ctrls["endik"]
        pvCtrl = self._ctrls["upVec"]

        rootScaleMatrix = zapi.createDG(
            namer.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": endIkCtrl.id(),
                    "type": "pickScale",
                },
            ),
            "pickMatrix",
        )
        rootScaleMatrix.useRotate = False
        rootScaleMatrix.useTranslate = False
        rootIn.attribute("worldMatrix")[0].connect(rootScaleMatrix.inputMatrix)
        # compute the offset
        endIkCtrl.srt().resetTransform()
        pvCtrl.srt().resetTransform()
        endIkScaleMulti = zapi.createMultMatrix(
            namer.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": endIkCtrl.id(),
                    "type": "rootScaleMult",
                },
            ),
            (rootScaleMatrix.outputMatrix, ikEndIn.attribute("worldMatrix")[0]),
            output=endIkCtrl.srt().offsetParentMatrix,
        )
        upvecScaleMulti = zapi.createMultMatrix(
            namer.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": pvCtrl.id(),
                    "type": "rootScaleMult",
                },
            ),
            (rootScaleMatrix.outputMatrix, upVecIn.attribute("worldMatrix")[0]),
            output=pvCtrl.srt().offsetParentMatrix,
        )
        rigLayer.addExtraNodes((endIkScaleMulti, upvecScaleMulti, rootScaleMatrix))

        ikJoints[1].preferredAngle = ikJoints[1].rotation()
        self._doIkSolve(ikJoints)
        # annotation between UpVector and mid control
        annName = namer.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "upvec",
                "type": "annotation",
            },
        )
        rigLayer.createAnnotation(
            annName, ikJoints[1], self._ctrls["upVec"], parent=rigLayerRoot
        )

    def _doIkSolve(self, ikJoints):
        definition = self.component.definition
        ikCtrls = self._ctrls
        handleParent = self._ctrls["endik"]
        namer = self.component.namingConfiguration()
        rigLayer = self.component.rigLayer()

        compName, compSide = self.component.name(), self.component.side()
        # # ikSolver happens last
        # maya iksolvers are, one solver for the whole rig so make sure we create it at the root namespace
        ikName = namer.resolve(
            "ikHandle",
            {
                "componentName": compName,
                "section": api.constants.IKTYPE,
                "side": compSide,
                "type": "ikHandle",
            },
        )
        ikHandle, ikEffector = api.createIkHandle(
            name=ikName,
            startJoint=ikJoints[0],
            endJoint=ikJoints[2],
            parent=handleParent,
        )
        rigLayer.addTaggedNode(ikHandle, "primaryLegIkHandle")
        upVecConstraint = api.nodeByName(
            cmds.poleVectorConstraint(
                ikCtrls["upVec"].fullPathName(), ikHandle.fullPathName()
            )[0]
        )
        ikHandle.hide()
        ikEffector.hide()

        controlPanel = self.component.controlPanel()
        controlPanel.connect("ikRoll", ikHandle.twist)
        # stretch, lock, slide
        hasStretch = definition.guideLayer.guideSetting("hasStretch").value
        if not hasStretch:
            return ikHandle
        self._setupStretch(
            rigLayer,
            ikJoints,
            definition.guideLayer.findGuides("mid", "end"),
            self._ctrls,
            self.component.inputLayer().inputNode("upr"),
        )

        rigLayer.addExtraNodes((upVecConstraint, ikHandle, ikEffector))
        return ikHandle

    def _setupStretch(self, rigLayer, ikJoints, guides, ctrls, rootInputNode):
        namingConfig = self.component.namingConfiguration()
        constantsNode = rigLayer.settingNode("constants")
        controlPanel = self.component.controlPanel()
        # bake in the initial lengths of the segments
        midToUprLen = ikJoints[1].translation(api.kTransformSpace).x
        midToLwrLen = ikJoints[2].translation(api.kTransformSpace).x
        constantsUprInit = constantsNode.constant_uprInitialLength
        constantsLwrInit = constantsNode.constant_lwrInitialLength
        constantsTotalInit = constantsNode.constant_totalInitLength
        constantsUprInit.set(midToUprLen)
        constantsLwrInit.set(midToLwrLen)
        constantsTotalInit.set(midToUprLen + midToLwrLen)
        # cache the controlPanel attrs
        stretchAttr = controlPanel.stretch
        upperStretch, lwrStretch = controlPanel.upperStretch, controlPanel.lowerStretch
        lockAttr = controlPanel.attribute("lock")
        minStretch, maxStretch = controlPanel.minStretch, controlPanel.maxStretch
        negate = mayamath.isVectorNegative(
            guides[0].attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
        )

        # First create the primary stretch between the start and end
        graphRegistry = self.component.configuration.graphRegistry()
        globalStretchGraphData = graphRegistry.graph(
            "ikGlobalStretchNeg" if negate else "ikGlobalStretch"
        )
        globalSegmentGraphData = graphRegistry.graph("ikSegmentScaleStretch")

        globalStretchGraph = self.createGraph(rigLayer, globalStretchGraphData)
        globalStretchGraph.connectToInput(
            "startWorldMtx", ctrls["baseik"].attribute("worldMatrix")[0]
        )
        globalStretchGraph.connectToInput(
            "endWorldMtx", ctrls["endik"].attribute("worldMatrix")[0]
        )
        globalStretchGraph.connectToInput("initialTotalLength", constantsTotalInit)
        globalStretchGraph.connectToInput("minStretch", minStretch)
        globalStretchGraph.connectToInput("maxStretch", maxStretch)
        outLengthPlug = globalStretchGraph.outputAttr("outLength")
        decomp = zapi.createDG(namingConfig.resolve("object",
                                                    {"componentName": self.component.name(),
                                                     "side": self.component.side(),
                                                     "section": "globalStretch",
                                                     "type": "decomposeMatrix"}), "decomposeMatrix")
        rootInputNode.worldMatrixPlug().connect(decomp.inputMatrix)
        globalStretchGraph.connectToInput("globalScale", decomp.outputScaleY)
        rigLayer.addExtraNode(decomp)
        segmentLengthPlugs = [constantsUprInit, constantsLwrInit]
        stretchAttrs = [upperStretch, lwrStretch]
        segmentCtrls = [ctrls["baseik"], ctrls["endik"]]
        upVector = ctrls["upVec"]

        # now loop over the segments and create the stretch graph for each
        for index, [startEnd, segmentTag] in enumerate(
                zip(general.chunks(ikJoints, 2, overlap=1), ["upr", "lwr"])
        ):
            _, outputNode = startEnd
            globalSegmentGraphData.name = globalSegmentGraphData.name + segmentTag
            sceneGraph = self.createGraph(rigLayer, globalSegmentGraphData, suffix=segmentTag)
            sceneGraph.connectToInput("globalStretchAmount", outLengthPlug)
            sceneGraph.connectToInput("initialLength", segmentLengthPlugs[index])
            sceneGraph.connectToInput("hasStretchAmount", stretchAttr)
            sceneGraph.connectToInput("lockAmount", lockAttr)
            sceneGraph.connectToInput("stretchAmount", stretchAttrs[index])
            sceneGraph.connectToInput(
                "poleVectorWorldMtx", upVector.attribute("worldMatrix")[0]
            )
            sceneGraph.connectToInput(
                "endWorldMtx", segmentCtrls[index].attribute("worldMatrix")[0]
            )
            sceneGraph.connectToInput("globalScale", decomp.outputScaleY)
            aimVector = (
                guides[index].attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
            )
            axisName = mayamath.primaryAxisNameFromVector(aimVector)
            sceneGraph.connectFromOutput(
                "outStretchSquash",
                [outputNode.attribute("translate{}".format(axisName))],
            )
