from zoo.libs.hive import api
from zoo.libs.hive.base import basesubsystem
from zoo.libs.hive.base.util import ikutils, componentutils
from zoo.libs.maya import zapi
from zoo.libs.maya.rig import align, skeletonutils

from zoo.libs.maya.utils import mayamath
from zoo.libs.utils import general as genutils
from maya import cmds, mel


class QuadLegSubSystem(basesubsystem.BaseSubsystem):
    """
    :param component:
    :type component: :class:`api.Component`
    :param worldEndRotation: whether the IK end control should orient to world relative to the toe
    """

    def __init__(self, component, primaryIds, worldEndRotation=True):
        super(QuadLegSubSystem, self).__init__(component)
        self.primaryIds = primaryIds
        self.ikCtrlIds = ["end", "baseik", "ankle"]
        self.inputNodeIds = ["upr", "endik", "upVec"]
        self.upVecIds = ["upVec", "upVecLwr"]
        self.worldEndRotation = worldEndRotation
        self.rootIkVisCtrlName = "ikHipsCtrlVis"
        self.poleVectorVisName = "poleVectorVis"
        self.rootParentId = "parentSpace"
        self._resetEndGuideAlignment = False
        self._endGuideAlignTargetGuide = "ball"
        self.mainIkParent = None

    def setupGuide(self):
        if not self.active():
            return
        guideLayer = self.component.guideLayer()
        # for backwards compatible, we delete the baseik guide shape
        shapeNode = guideLayer.guide("base" + api.constants.IKTYPE).shapeNode()
        if shapeNode:
            shapeNode.delete()
        self._constructAutoAlignment(guideLayer)

    def preMirror(self, translate, rotate, parent):
        guideLayer = self.component.guideLayer()
        uprGuide, midGuide, ankle, _ = guideLayer.findGuides(*self.primaryIds)
        uprGuide.setLockStateOnAttributes(zapi.localRotateAttrs, False)
        midGuide.setLockStateOnAttributes(zapi.localRotateAttrs, False)
        ankle.setLockStateOnAttributes(zapi.localTransformAttrs, False)
        zapi.deleteConstraints([uprGuide, midGuide, ankle] + list(ankle.iterSrts()))

    def _constructAutoAlignment(self, guideLayer):
        uprGuide, midGuide, ankle, endGuide = guideLayer.findGuides(*self.primaryIds)
        # align the vchain guides with coplanar, align all others as normal
        uprGuide.setLockStateOnAttributes(zapi.localRotateAttrs, False)
        midGuide.setLockStateOnAttributes(zapi.localRotateAttrs, False)
        ankle.setLockStateOnAttributes(zapi.localTransformAttrs, False)
        zapi.deleteConstraints([uprGuide, midGuide, ankle] + list(ankle.iterSrts()))

        _createAutoAlignSystem(
            self, uprGuide, midGuide, ankle, endGuide, guideLayer.guide("root")
        )
        ikutils.createAutoPoleGuideGraph(
            self.component,
            guideLayer,
            "autoPoleVectorUpr",
            self.primaryIds[:2] + [self.primaryIds[-1]],
            self.upVecIds[0],
        )
        uprGuide.setLockStateOnAttributes(zapi.localRotateAttrs, True)
        midGuide.setLockStateOnAttributes(zapi.localRotateAttrs, True)
        ankle.setLockStateOnAttributes(zapi.localRotateAttrs, True)

    def preAlignGuides(self):
        if not self.active():
            return
        guideLayer = self.component.guideLayer()
        # align the vchain guides with coplanar, align all others as normal
        uprGuide, midGuide, ankle, endGuide = guideLayer.findGuides(*self.primaryIds)
        baseikGuide, hockGuide = guideLayer.findGuides(*["baseik", "hock"])
        vChainGuides = [uprGuide, midGuide, ankle, endGuide]

        constructedPlane = componentutils.worldUpVectorAsPlaneLegacy(uprGuide, endGuide)
        uprGuide.setLockStateOnAttributes(zapi.localRotateAttrs, False)
        midGuide.setLockStateOnAttributes(zapi.localRotateAttrs, False)
        ankle.setLockStateOnAttributes(zapi.localTransformAttrs, False)
        zapi.deleteConstraints([uprGuide, midGuide, ankle] + list(ankle.iterSrts()))
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

        def _alignEndGuideToParent(transform, guide):
            midRotation = zapi.TransformationMatrix(matrices[-1]).rotation(
                zapi.kWorldSpace
            )
            transform.setRotation(midRotation)
            return guide, transform.asMatrix()

        def _computeEndGuideAlignment():
            transform = endGuide.transformationMatrix()
            if self._resetEndGuideAlignment:
                _, mat = _alignEndGuideToParent(transform, endGuide)
                return mat
            child = guideLayer.guide(self._endGuideAlignTargetGuide)
            if child is None:
                _, mat = _alignEndGuideToParent(transform, endGuide)
                return mat
            else:
                rot = mayamath.lookAt(
                    endGuide.translation(zapi.kWorldSpace),
                    child.translation(zapi.kWorldSpace),
                    aimVector=endGuide.autoAlignAimVector.value(),
                    upVector=endGuide.autoAlignUpVector.value(),
                )
                transform.setRotation(rot)
                return transform.asMatrix()

        # hock always needs the same rotation as the end guide so we always compute the matrix
        endMatrix = _computeEndGuideAlignment()
        if endGuide.autoAlign.asBool():
            matrices.append(endMatrix)
            guides.append(endGuide)

        # set the hock guide to the same rotation as the end guide
        guides.append(hockGuide)
        matrices.append(endMatrix)
        # set the base ik guide to the same rotation as the upr guide
        guides.append(baseikGuide)
        matrices.append(matrices[0])
        return guides, matrices

    def postAlignGuides(self):
        if not self.active():
            return

        self._constructAutoAlignment(self.component.guideLayer())
        upVecDef = self.component.definition.guideLayer.guide("upVec")
        upVec = self.component.guideLayer().guide("upVec")
        upVec.setTranslation(upVecDef.translate, zapi.kWorldSpace)
        upVecLwrGuide = self.component.guideLayer().guide("upVecLwr")
        upVecLwrGuide.resetTransform()

    def setupRig(self, parentNode):
        """
        :param parentNode: The parent node to which the rig will be connected to.
        :type parentNode: :class:`zapi.DagNode`
        """
        if not self.active():
            return
        mel.eval(
            "ikSpringSolver;"
        )  # hack around spring solver not correctly loading with cmds.loadPlugin
        # quad has 2 ikHandles first is the primary which goes between upr and ankle ik joints then another between
        # the second ikChain upr and end
        comp = self.component
        naming = comp.namingConfiguration()
        rigLayer = comp.rigLayer()
        inputLayer = comp.inputLayer()
        compName, compSide = comp.name(), comp.side()

        rigRootTransform = rigLayer.rootTransform()
        guideLayerDef = comp.definition.guideLayer
        guideDefs = guideLayerDef.findGuides(*self.primaryIds)
        rootIn, ikEndIn, upVecIn = inputLayer.findInputNodes(*self.inputNodeIds)

        springJoints = self._createSpringIkJoints(
            rigLayer, naming, compName, compSide, guideDefs, rigRootTransform
        )
        ikJoints = self._createIkJoints(
            rigLayer, naming, compName, compSide, guideDefs, springJoints[0]
        )

        ctrls = self._createIkControls(
            rigLayer,
            guideLayerDef,
            naming,
            compName,
            compSide,
            ikEndIn,
            rigRootTransform,
        )

        ctrls.update(
            self._createPoleVectorControls(
                rigLayer, guideLayerDef, naming, compName, compSide, rigRootTransform
            )
        )

        springIk = self._createSpringSolver(
            rigLayer,
            naming,
            compName,
            compSide,
            (springJoints[0], springJoints[-1]),
            ctrls,
            parent=self.mainIkParent,
        )
        secondaryIk = self._createUprIkSolver(
            rigLayer,
            naming,
            compName,
            compSide,
            (ikJoints[0], ikJoints[2]),
            ctrls,
            parent=ctrls["ankleik"],
        )
        pvCtrl = ctrls["upVec"]
        pvLwrCtrl = ctrls["upVecLwr"]
        endIkCtrl = ctrls["endik"]
        ikRootCtrl = ctrls["baseik"]

        self._bindAnkleCtrl(rigLayer, ctrls["ankleik"], springJoints[-2])
        _, constUtilities = zapi.buildConstraint(
            ikJoints[-1],
            drivers={"targets": (("", endIkCtrl),)},
            constraintType="orient",
            maintainOffset=True,
        )
        rigLayer.addExtraNodes(constUtilities)
        const, constUtilities = zapi.buildConstraint(
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
        rootScaleMatrix = zapi.createDG(
            naming.resolve(
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
        endIkCtrlCurrentWorldMatrix = endIkCtrl.srt().worldMatrix()
        # endIkCtrl.srt().resetTransform()
        pvCtrl.srt().resetTransform()
        pvLwrCtrl.srt().resetTransform()
        endIkScaleMulti = zapi.createMultMatrix(
            naming.resolve(
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
        endIkCtrl.srt().setWorldMatrix(endIkCtrlCurrentWorldMatrix)
        upvecLwrScaleMulti = zapi.createMultMatrix(
            naming.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": pvLwrCtrl.id(),
                    "type": "rootScaleMult",
                },
            ),
            (rootScaleMatrix.outputMatrix, upVecIn.attribute("worldMatrix")[0]),
            output=pvLwrCtrl.srt().offsetParentMatrix,
        )
        rigLayer.addExtraNodes((endIkScaleMulti, upvecLwrScaleMulti, rootScaleMatrix))

        self._createAnkleIkSolver(
            rigLayer,
            startJoint=ikJoints[-2],
            ankleCtrl=ctrls["ankleik"],
            drivenGuide=guideDefs[-2],
        )

        self._bindBaseIK(
            rigLayer,
            rigLayer.controlPanel(),
            ctrls["baseik"],
            springJoints[0],
            rootIn,
        )

        self._setupStretch(
            rigLayer, ikJoints, springJoints, guideDefs, ctrls, rootIn, "primary"
        )
        rigLayer.addTaggedNode(springIk, "springIk")
        rigLayer.addTaggedNode(secondaryIk, "secondaryIk")

        controlPanel = self.component.controlPanel()
        ikRollAttr = controlPanel.ikRoll
        ikRollAttr.connect(springIk.twist)

        # annotation between UpVector and mid control
        annName = naming.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "upvec",
                "type": "annotation",
            },
        )
        rigLayer.createAnnotation(
            annName, ikJoints[1], ctrls["upVecLwr"], parent=rigRootTransform
        )

    def _bindAnkleCtrl(self, rigLayer, ctrl, parentJoint):
        """Bind the ankle control to the parent joint.

        :param rigLayer: The rig layer object to add the extra nodes to.
        :type rigLayer: :class:`zoo.libs.hive.api.HiveRigLayer`
        :param ctrl: The ankle control object.
        :type ctrl: :class:`zoo.libs.hive.api.ControlNode`
        :param parentJoint: The parent joint to bind the ankle control to.
        :type parentJoint: :class:`zapi.DagNode`
        """
        _, utilities = zapi.buildConstraint(
            ctrl.srt(),
            {"targets": (("", parentJoint),)},
            maintainOffset=True,
            constraintType="matrix",
        )
        rigLayer.addExtraNodes(utilities)

    def _bindBaseIK(self, rigLayer, controlPanel, baseIkCtrl, springJoint, inputNode):
        """Binds the Spring joint to the base ik control.

        :param rigLayer: The rig layer to bind the base IK to.
        :type rigLayer: :class:`zoo.libs.hive.api.HiveRigLayer`
        :param controlPanel: The control panel for the rig.
        :type controlPanel: :class:`zoo.libs.hive.api.SettingsNode`
        :param baseIkCtrl: The base IK control.
        :type baseIkCtrl: :class:`zoo.libs.hive.api.ControlNode`
        :param springJoint: The spring joint to bind to.
        :type springJoint: :class:`zoo.libs.hive.api.Joint`
        :param inputNode: The input node for the base IK control.
        :type inputNode: :class:`zoo.libs.hive.api.InputNode`
        """
        controlPanel.attribute(self.rootIkVisCtrlName).connect(baseIkCtrl.visibility)
        baseIkCtrl.setLockStateOnAttributes(("rotate", "scale", "visibility"))
        baseIkCtrl.showHideAttributes(
            zapi.localRotateAttrs + zapi.localScaleAttrs, False
        )
        const, constUtilities = zapi.buildConstraint(
            springJoint,
            drivers={"targets": (("", baseIkCtrl),)},
            constraintType="point",
            maintainOffset=True,
        )
        rigLayer.addExtraNodes(constUtilities)
        _, constUtilities = zapi.buildConstraint(
            springJoint,
            drivers={"targets": (("", inputNode),)},
            constraintType="scale",
            maintainOffset=True,
        )
        rigLayer.addExtraNodes(constUtilities)

    def _createIkControls(
        self, rigLayer, guideLayerDef, naming, compName, compSide, endInput, parent
    ):
        ctrls = {}
        ctrlIds = []
        for i in self.ikCtrlIds:
            if i == "ankle":
                ctrlIds.append("hock")
            else:
                ctrlIds.append(i)
        startGuide = guideLayerDef.guide(self.primaryIds[0])
        ctrlDefs = {
            definition.id: definition
            for definition in guideLayerDef.findGuides(*ctrlIds)
        }
        # ikCtrls
        for guideId, ctrlDef in ctrlDefs.items():
            ctrlId = guideId if guideId != "hock" else "ankle"
            if not ctrlId.lower().endswith(api.constants.IKTYPE):
                ctrlId = ctrlId + api.constants.IKTYPE
            ctrlShape = (
                ctrlDef.shape
                if ctrlId != "base" + api.constants.IKTYPE
                else startGuide.shape
            )

            ctrlName = naming.resolve(
                "controlName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": ctrlId,
                    "system": api.constants.IKTYPE,
                    "type": "control",
                },
            )
            if ctrlId == "endik":
                rotation = endInput.rotation(space=zapi.kWorldSpace)
            else:
                rotation = ctrlDef.rotate
            # create the foot Control
            ikCtrl = rigLayer.createControl(
                name=ctrlName,
                id=ctrlId,
                translate=ctrlDef.translate,
                rotate=rotation,
                parent=parent,
                rotateOrder=ctrlDef.rotateOrder,
                shape=ctrlShape,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                srts=[{"name": "_".join([ctrlDef.id, "srt"])}],
            )
            ctrls[ctrlId] = ikCtrl
        ctrls["ankleik"].setLockStateOnAttributes(("translate", "scale", "visibility"))
        ctrls["ankleik"].showHideAttributes(
            zapi.localTranslateAttrs + zapi.localScaleAttrs + ["visibility"], False
        )
        return ctrls

    def _createPoleVectorControls(
        self, rigLayer, guideLayerDef, naming, compName, compSide, parent
    ):
        ctrls = {}
        ctrlParent = parent
        controlPanel = self.component.controlPanel()
        # pole vector controls
        for ctrlDef in guideLayerDef.findGuides(*reversed(self.upVecIds)):
            ctrlId = ctrlDef.id

            ctrlName = naming.resolve(
                "controlName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": ctrlDef.id,
                    "system": api.constants.IKTYPE,
                    "type": "control",
                },
            )
            # create the foot Control
            ikCtrl = rigLayer.createControl(
                name=ctrlName,
                id=ctrlId,
                translate=ctrlDef.translate,
                rotate=zapi.Quaternion(),  # orient upVecs to world
                parent=ctrlParent,
                rotateOrder=ctrlDef.rotateOrder,
                shape=ctrlDef.shape,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                srts=[{"name": "_".join([ctrlDef.id, "srt"])}],
            )
            if ctrlId == "upVec":
                controlPanel.attribute(self.poleVectorVisName).connect(
                    ikCtrl.visibility
                )
            ikCtrl.setLockStateOnAttributes(("rotate", "scale", "visibility"))
            ikCtrl.showHideAttributes(
                zapi.localRotateAttrs + zapi.localScaleAttrs, False
            )
            ctrlParent = ctrlDef.id
            ctrls[ctrlId] = ikCtrl
        return ctrls

    def _createIkJoints(self, rigLayer, naming, compName, compSide, guideDefs, parent):
        """Creates the IK joints for the secondary chain.

        :param rigLayer: The hive Rig layer instance.
        :type rigLayer: :class:`zoo.libs.hive.api.HiveRigLayer`
        :param naming: The naming configuration for the component.
        :type naming: :class:`zoo.libs.naming.naming.NameManager``
        :param compName: The component name.
        :type compName: str
        :param compSide: The component side name.
        :type compSide: str
        :param guideDefs:
        :type guideDefs: list[:class:`zoo.libs.hive.api.GuideDefinition`]
        :param parent: The parent node for the root joint
        :type parent: :class:`zapi.DagNode`
        :return: The list of created ik joints in the same order as the guideDefs.
        :rtype: list[:class:`zoo.libs.hive.api.Joint`]
        """
        ikJoints = []
        ikParent = parent
        # generate the main ik joints which will also be used for blending
        for i, guide in enumerate(guideDefs):
            guideId = guide.id
            ikGuideId = guideId + api.constants.IKTYPE

            ikName = naming.resolve(
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
            ikJoints.append(ikJnt)
            ikParent = ikJnt

        return ikJoints

    def _createSpringIkJoints(
        self, rigLayer, naming, compName, compSide, guideDefs, parent
    ):
        """Creates the spring ik joints for the primary chain.

        :param rigLayer: The hive Rig layer instance.
        :type rigLayer: :class:`zoo.libs.hive.api.HiveRigLayer`
        :param naming: The naming configuration for the component.
        :type naming: :class:`zoo.libs.naming.naming.NameManager``
        :param compName: The component name.
        :type compName: str
        :param compSide: The component side name.
        :type compSide: str
        :param guideDefs:
        :type guideDefs: list[:class:`zoo.libs.hive.api.GuideDefinition`]
        :param parent: The parent node for the root joint
        :type parent: :class:`zapi.DagNode`
        :return: The list of created spring joints in the same order as the guideDefs.
        :rtype: list[:class:`zoo.libs.hive.api.Joint`]
        """
        ikJoints = []
        ikParent = parent
        # generate the main ik joints which will also be used for blending
        for i in range(0, len(guideDefs)):
            guide = guideDefs[i]
            guideId = guide.id
            ikGuideId = guideId + "Spring"

            ikName = naming.resolve(
                "jointName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": guideId,
                    "system": "Spring",
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
            ikJoints.append(ikJnt)
            ikParent = ikJnt

        return ikJoints

    def _createUprIkSolver(
        self, rigLayer, naming, compName, compSide, startEndJoints, ikCtrls, parent
    ):
        solverName = naming.resolve(
            "object",
            {
                "componentName": compName,
                "section": "secondary",
                "side": compSide,
                "type": "ikHandleRP",
            },
        )
        ikHandle, ikEffector = zapi.createIkHandle(
            name=solverName,
            startJoint=startEndJoints[0],
            endJoint=startEndJoints[1],
            parent=parent,
        )
        upVecConstraint = zapi.nodeByName(
            cmds.poleVectorConstraint(
                ikCtrls["upVec"].fullPathName(), ikHandle.fullPathName()
            )[0]
        )
        rigLayer.addExtraNodes((ikHandle, ikEffector, upVecConstraint))
        controlPanel = self.component.controlPanel()
        ikRollAttr = controlPanel.ikRoll
        currentAngle = (
            startEndJoints[0]
            .rotation(zapi.kTransformSpace, asQuaternion=True)
            .asAxisAngle()[1]
        )
        # if the ik flipped due to the Pole Vector, it's likely because the mid-joint is the opposite direction,
        # this is still valid, so we flip the twist if the angle is not 0. Useful for a mech leg or insects
        if currentAngle != 0.0:
            flip = zapi.createDG(
                naming.resolve(
                    "object",
                    {
                        "componentName": compName,
                        "section": "twistDefault",
                        "side": compSide,
                        "type": "addDoubleLinear",
                    },
                ),
                "addDoubleLinear",
            )
            ikRollAttr.connect(flip.input1)
            flip.input2.set(180.0)
            flip.output.connect(ikHandle.twist)
            rigLayer.addExtraNode(flip)
            rigLayer.settingNode("constants").attribute(
                "constant_isIKPoleVectorInverted"
            ).set(True)

        else:
            ikRollAttr.connect(ikHandle.twist)
        ikHandle.hide()
        ikEffector.hide()
        rigLayer.addExtraNodes((ikHandle, ikEffector))

        return ikHandle

    def _createSpringSolver(
        self, rigLayer, naming, compName, compSide, startEndJoints, ikCtrls, parent
    ):
        solverName = naming.resolve(
            "object",
            {
                "componentName": compName,
                "section": "primary",
                "side": compSide,
                "type": "ikHandleSpring",
            },
        )
        ikHandle, ikEffector = zapi.createIkHandle(
            name=solverName,
            startJoint=startEndJoints[0],
            endJoint=startEndJoints[1],
            parent=parent,
            solverType=zapi.kIkSpringSolveType,
            autoPriority=True,
        )

        upVecConstraint = zapi.nodeByName(
            cmds.poleVectorConstraint(
                ikCtrls["upVecLwr"].fullPathName(), ikHandle.fullPathName()
            )[0]
        )
        rigLayer.addExtraNodes((ikHandle, ikEffector, upVecConstraint))
        ikHandle.hide()
        ikEffector.hide()
        rigLayer.addExtraNodes((ikHandle, ikEffector))

        controlPanel = self.component.controlPanel()
        controlPanel.ikUprAngleBias.connect(ikHandle.springAngleBias[0].child(1))
        controlPanel.ikLwrAngleBias.connect(ikHandle.springAngleBias[1].child(1))
        ikHandle.springAngleBias[1].child(0).set(1.0)
        return ikHandle

    def _createAnkleIkSolver(self, rigLayer, startJoint, ankleCtrl, drivenGuide):
        _, utilities = zapi.buildConstraint(
            startJoint,
            drivers={"targets": (("", ankleCtrl),)},
            constraintType="aim",
            maintainOffset=True,
            aimVector=list(
                drivenGuide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
            ),
            upVector=list(
                drivenGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
            ),
            worldUpVector=list(
                drivenGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
            ),
            worldUpType="objectrotation",
            worldUpObject=ankleCtrl.fullPathName(),
        )

        rigLayer.addExtraNodes(utilities)

    def _setupStretch(
        self,
        rigLayer,
        ikJoints,
        splineJoints,
        guides,
        ctrls,
        rootInputNode,
        graphSuffix,
    ):
        inputLayer = self.component.inputLayer()
        inputSettings = inputLayer.settingNode(api.constants.INPUT_OFFSET_ATTR_NAME)

        def _findInputRestMatrix():
            for guideRestTransformPlug in inputSettings.attribute("transforms"):
                if guideRestTransformPlug.child(0).value() == "end":
                    return guideRestTransformPlug.child(1)

        constantsNode = rigLayer.settingNode("constants")
        controlPanel = self.component.controlPanel()
        legGuides = {i.id: i for i in guides}

        # bake in the initial lengths of the segments
        uprNeg = mayamath.isVectorNegative(
            legGuides["upr"].attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
        )
        midNeg = mayamath.isVectorNegative(
            legGuides["mid"].attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
        )
        endNeg = mayamath.isVectorNegative(
            legGuides["ankle"].attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
        )
        midToUprLen = (
            legGuides["upr"].translate - legGuides["mid"].translate
        ).length() * (-1.0 if uprNeg else 1.0)
        midToLwrLen = (
            legGuides["mid"].translate - legGuides["ankle"].translate
        ).length() * (-1.0 if midNeg else 1.0)
        endToAnkleLen = (
            legGuides["ankle"].translate - legGuides["end"].translate
        ).length() * (-1.0 if endNeg else 1.0)

        constantsUprInit = constantsNode.constant_uprInitialLength
        constantsLwrInit = constantsNode.constant_lwrInitialLength
        constantsAnkleInit = constantsNode.constant_ankleInitialLength
        constantsTotalInit = constantsNode.constant_totalInitLength
        constantsUprInit.set(midToUprLen)
        constantsLwrInit.set(midToLwrLen)
        constantsAnkleInit.set(endToAnkleLen)
        constantsTotalInit.set(midToUprLen + midToLwrLen + endToAnkleLen)
        # cache the controlPanel attrs
        stretchAttr = controlPanel.stretch
        upperStretch, lwrStretch, ankleStretch = (
            controlPanel.upperStretch,
            controlPanel.lowerStretch,
            controlPanel.ankleStretch,
        )
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
        globalStretchGraphData.name = globalStretchGraphData.name + graphSuffix
        # first and second segment stretch is basically identical to the arm etc so reuse the graph
        firstSecondSegmentGraphData = graphRegistry.graph("ikSegmentScaleStretch")
        # Last segment doesn't use lock at the moment so this is a unique graph
        lastSegmentGraph = graphRegistry.graph("quadAnkleIkSegmentScaleStretch")
        lastSegmentGraph.name = globalStretchGraphData.name + graphSuffix

        globalStretchGraph = self.createGraph(rigLayer, globalStretchGraphData)
        globalStretchGraph.connectToInput(
            "startWorldMtx", ctrls["baseik"].attribute("worldMatrix")[0]
        )
        globalStretchGraph.connectToInput(
            "endWorldMtx", ctrls["endik"].attribute("worldMatrix")[0]
        )
        globalStretchGraph.connectToInput("initialTotalLength", constantsTotalInit)
        globalStretchGraph.connectToInput(
            "globalScale", rootInputNode.attribute("scale")[1]
        )
        globalStretchGraph.connectToInput("minStretch", minStretch)
        globalStretchGraph.connectToInput("maxStretch", maxStretch)
        outLengthPlug = globalStretchGraph.outputAttr("outLength")

        segmentLengthPlugs = [constantsUprInit, constantsLwrInit, constantsAnkleInit]
        stretchAttrs = [upperStretch, lwrStretch, ankleStretch]
        upVector = ctrls["upVec"]
        springJointsChunks = list(genutils.chunks(splineJoints, 2, overlap=1))

        # this graph computes the position of the ankle joint based the ankle anim ctrl
        # output matrix gets fed into the ankle graph

        positionGraph = self.createGraph(
            rigLayer, graphRegistry.graph("quadLegAnklePosition"), suffix="ankle"
        )
        positionGraph.connectToInput("inputMtx", ctrls["ankleik"].worldMatrixPlug())
        positionGraph.connectToInput("restMtx", _findInputRestMatrix())

        # now loop over the first 2 segments and create the stretch graph for each
        for index, [startEnd, segmentTag] in enumerate(
            zip(genutils.chunks(ikJoints[:-1], 2, overlap=1), ["upr", "lwr"])
        ):
            _, ikOutputNode = startEnd
            _, springOutputNode = springJointsChunks[index]
            firstSecondSegmentGraphData.name = (
                firstSecondSegmentGraphData.name + segmentTag
            )
            sceneGraph = self.createGraph(
                rigLayer, firstSecondSegmentGraphData, suffix=segmentTag
            )
            sceneGraph.connectToInput("globalStretchAmount", outLengthPlug)
            sceneGraph.connectToInput("initialLength", segmentLengthPlugs[index])
            sceneGraph.connectToInput("hasStretchAmount", stretchAttr)
            sceneGraph.connectToInput("lockAmount", lockAttr)
            sceneGraph.connectToInput("stretchAmount", stretchAttrs[index])
            sceneGraph.connectToInput(
                "poleVectorWorldMtx", upVector.attribute("worldMatrix")[0]
            )
            if index == 1:
                sceneGraph.connectToInput(
                    "endWorldMtx", positionGraph.outputAttr("outputMtx")
                )
            else:
                sceneGraph.connectToInput(
                    "endWorldMtx", ctrls["baseik"].attribute("worldMatrix")[0]
                )
            aimVector = (
                guides[index].attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
            )
            axisName = "translate{}".format(
                mayamath.primaryAxisNameFromVector(aimVector)
            )
            sceneGraph.connectFromOutput(
                "outStretchSquash", [ikOutputNode.attribute(axisName)]
            )
            sceneGraph.connectFromOutput(
                "outStretch", [springOutputNode.attribute(axisName)]
            )

        # last segment graph which doesn't have lock behaviour for now
        lastSceneGraph = self.createGraph(rigLayer, lastSegmentGraph, suffix="ankle")
        lastSceneGraph.connectToInput("globalStretchAmount", outLengthPlug)
        lastSceneGraph.connectToInput("initialLength", constantsAnkleInit)
        lastSceneGraph.connectToInput("hasStretchAmount", stretchAttr)
        lastSceneGraph.connectToInput("lockAmount", lockAttr)
        lastSceneGraph.connectToInput("stretchAmount", ankleStretch)

        aimVector = guides[-1].attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
        axisName = "translate{}".format(mayamath.primaryAxisNameFromVector(aimVector))

        lastSceneGraph.connectFromOutput(
            "outStretch",
            [splineJoints[-1].attribute(axisName), ikJoints[-1].attribute(axisName)],
        )

    def matchTo(self):
        deformLayer = self.component.deformLayer()
        rigLayer = self.component.rigLayer()
        constantsNode = rigLayer.settingNode("constants")
        guideLayerDef = self.component.definition.guideLayer
        # probably a temp hack for ctrl ids that don't have the iktype suffix
        ikIds = []
        for ikId in self.ikCtrlIds:
            if not ikId.lower().endswith(api.constants.IKTYPE):
                ikId = ikId + api.constants.IKTYPE
            ikIds.append(ikId)

        ikCtrls = {i.id(): i for i in rigLayer.findControls(*ikIds + self.upVecIds)}
        deformJoints = deformLayer.findJoints(*self.primaryIds)
        endGuide, midGuide, upVecGuide = guideLayerDef.findGuides(
            self.primaryIds[-1], self.primaryIds[1], "upVecLwr"
        )
        endIk, upVec, upVecLwr = (
            ikCtrls["end" + api.constants.IKTYPE],
            ikCtrls["upVec"],
            ikCtrls["upVecLwr"],
        )
        # if the secondary ik required flipping then we need to flip the pole vector here aka invert the distance
        distance = (midGuide.translate - upVecGuide.translate).length()
        invertDistance = constantsNode.attribute(
            "constant_isIKPoleVectorInverted"
        ).value()

        distance *= -1.0 if invertDistance else 1.0
        try:
            pvPosition = skeletonutils.poleVectorPosition(
                deformJoints[0].translation(),
                deformJoints[1].translation(),
                deformJoints[-1].translation(),
                distance=distance,
            )
        except ValueError:
            pvPosition = deformJoints[1].translation()
        originalOffset = constantsNode.attribute("constant_ikfkEndOffset").value()

        endMatrix = (
            originalOffset.inverse()
            * deformJoints[-1].worldMatrix()
            * endIk.parentInverseMatrix()
        )

        endIk.setMatrix(endMatrix)
        upVecLwr.setTranslation(pvPosition, space=zapi.kWorldSpace)
        upVec.resetTransform()
        # now configure the ankle IK
        # to compute the rotation relative to the parent we need to build a Normal from the end joint
        # perpendicular rotation axis aka. by default would be Z rotation axis. This normal is used
        # as the worldUpVector for the lookAt function. The aim vector is inverted due to the rotation
        # being the foot alignment typical X.
        endPos = deformJoints[-1].translation(zapi.kWorldSpace)
        ankleIKCtrl = ikCtrls["ankle" + api.constants.IKTYPE]
        # get the normal
        endWorldMtx = deformJoints[-1].worldMatrix()
        basisVectors = mayamath.basisVectorsFromMatrix(endWorldMtx)
        aimVector = endGuide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
        upVector = endGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
        index, _ = mayamath.perpendicularAxisFromAlignVectors(aimVector, upVector)
        normal = basisVectors[index]
        # compute the rotation
        worldRotation = mayamath.lookAt(
            endPos,
            deformJoints[-2].translation(zapi.kWorldSpace),
            aimVector * -1.0,
            upVector,
            normal,
        )

        transform = zapi.TransformationMatrix(worldRotation.asMatrix())
        transform.setTranslation(endPos, zapi.kWorldSpace)
        transform = ankleIKCtrl.parent().matrix() * transform.asMatrix()
        ankleIKCtrl.setWorldMatrix(transform)

        return {"controls": [endIk, upVec, upVecLwr], "selectables": [endIk]}

    def prePlacePoleVectorSensibly(self):
        upVecGuideId = "upVecLwr"
        rigLayer = self.component.rigLayer()
        pvCtrl = rigLayer.control(upVecGuideId)
        constantsNode = rigLayer.settingNode("constants")
        invertDistance = constantsNode.attribute(
            "constant_isIKPoleVectorInverted"
        ).value()
        midGuide, upVecGuide = self.component.definition.guideLayer.findGuides(
            "mid", upVecGuideId
        )
        distance = (midGuide.translate - upVecGuide.translate).length()

        distance *= -1.0 if invertDistance else 1.0
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


def _createAutoAlignSystem(
    subsystem, uprGuide, midGuide, ankleGuide, endGuide, rootGuide
):
    """

    :param subsystem: The quad leg system instance.
    :type subsystem: :class:`QuadLegSubSystem`
    :param uprGuide:
    :type uprGuide: :class:`zoo.libs.hive.api.Guide`
    :param midGuide:
    :type midGuide: :class:`zoo.libs.hive.api.Guide`
    :param ankleGuide:
    :type ankleGuide: :class:`zoo.libs.hive.api.Guide`
    :param endGuide:
    :type endGuide: :class:`zoo.libs.hive.api.Guide`
    :return:
    :rtype:
    """
    midPos = midGuide.translation(zapi.kWorldSpace)
    anklePos = ankleGuide.worldMatrix()
    topAnkleSrt = ankleGuide.srt(0)
    ankleSrt = ankleGuide.srt(1)
    anklePos = zapi.TransformationMatrix(anklePos)
    anklePos.setScale(ankleGuide.attribute("scale").value(), zapi.kWorldSpace)
    topAnkleSrt.setTranslation(anklePos.translation(zapi.kWorldSpace))
    topAnkleSrt.setRotation(anklePos.rotation(asQuaternion=True))
    ankleGuide.setTranslation(anklePos.translation(zapi.kWorldSpace))
    ankleGuide.setRotation(anklePos.rotation(asQuaternion=True))

    guideLayer = subsystem.component.guideLayer()
    layerRoot = guideLayer.rootTransform()
    # create reference nodes for constraints as this gets around cyclic dependencies with this whole hack
    uprGuideRef = zapi.createDag(
        uprGuide.name(includeNamespace=False) + "ConstRef",
        "transform",
        parent=layerRoot,
    )
    midGuideRef = zapi.createDag(
        midGuide.name(includeNamespace=False) + "ConstRef",
        "transform",
        parent=layerRoot,
    )
    endGuideRef = zapi.createDag(
        endGuide.name(includeNamespace=False) + "ConstRef",
        "transform",
        parent=layerRoot,
    )

    for guideRef, guide in zip(
        (uprGuideRef, midGuideRef, endGuideRef), (uprGuide, midGuide, endGuide)
    ):
        zapi.buildConstraint(
            guideRef,
            drivers={"targets": (("ref", guide),)},
            constraintType="point",
            maintainOffset=False,
        )
    # component center point
    _, utilities = zapi.buildConstraint(
        topAnkleSrt,
        constraintType="point",
        drivers={"targets": (("upr", uprGuide), ("end", endGuide))},
        maintainOffset=False,
        trace=True,
    )
    uprMidDist = zapi.distanceBetween(uprGuideRef, midGuideRef, name="uprMidDist")
    midEndDist = zapi.distanceBetween(midGuideRef, endGuideRef, name="midEndDist")
    midEndDist.distance.connect(utilities[0].target[0].child(4))  # weight
    uprMidDist.distance.connect(utilities[0].target[1].child(4))  # weight
    guideLayer.addExtraNodes(utilities)
    # mid ankle center point
    _, utilities = zapi.buildConstraint(
        ankleSrt,
        constraintType="point",
        drivers={"targets": (("mid", midGuide), ("end", endGuide))},
        maintainOffset=False,
        trace=True,
    )
    midGuide.setTranslation(midPos, space=zapi.kWorldSpace)
    ankleGuide.setWorldMatrix(anklePos)
    perpendicularAxisNode = zapi.createDG("perpendicularAxis", "vectorProduct")
    perpendicularAxisInvNode = zapi.createDG(
        "perpendicularAxisInvert", "multiplyDivide"
    )
    perpendicularAxisNode.operation.set(2)
    perpendicularAxisInvNode.input2.set((-1.0, -1.0, -1.0))
    ankleAimVector = ankleGuide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR)
    ankleUpVector = ankleGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR)
    perpendicularAxisNode.output.connect(perpendicularAxisInvNode.input1)
    ankleAimVector.connect(perpendicularAxisNode.input1)
    ankleUpVector.connect(perpendicularAxisNode.input2)
    _createAimConstraint(
        topAnkleSrt,
        midGuide,
        perpendicularAxisInvNode.output,
        ankleAimVector,
        endGuide,
        upType="object",
    )

    _createAimConstraint(
        ankleGuide,
        endGuide,
        ankleAimVector,
        ankleUpVector,
        midGuide,
        upType="object",
    )

    aimVector = midGuide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR)
    upVector = midGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR)
    _createAimConstraint(midGuide, ankleGuide, aimVector, upVector, topAnkleSrt)

    aimVector = uprGuide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR)
    upVector = uprGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR)
    _createAimConstraint(
        uprGuide, midGuide, aimVector, upVector, endGuide, upType="object"
    )

    ankleGuide.setLockStateOnAttributes(
        [
            zapi.localTranslateAttrs[
                mayamath.primaryAxisIndexFromVector(ankleUpVector.value())
            ]
        ],
        True,
    )


def _createAimConstraint(
    driven,
    target,
    aimVector,
    upVector,
    worldUpObject,
    upType="objectrotation",
    worldUpVector=None,
):
    aimVectorValue = aimVector.value()
    upVectorValue = upVector.value()
    if worldUpVector is None:
        worldUpVector = list(
            mayamath.AXIS_VECTOR_BY_IDX[
                mayamath.perpendicularAxisFromAlignVectors(
                    aimVectorValue, upVectorValue
                )[0]
            ]
        )
    _, utilities = zapi.buildConstraint(
        driven,
        constraintType="aim",
        drivers={"targets": ((target.name(includeNamespace=False), target),)},
        maintainOffset=True,
        trace=True,
        worldUpType=upType,
        worldUpObject=worldUpObject.fullPathName(),
        worldUpVector=worldUpVector,
        aimVector=list(aimVectorValue),
        upVector=list(upVectorValue),
    )

    return utilities
