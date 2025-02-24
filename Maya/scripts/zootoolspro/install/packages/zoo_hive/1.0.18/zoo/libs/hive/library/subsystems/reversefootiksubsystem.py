import copy

from zoo.libs.hive.base import basesubsystem
from zoo.libs.hive.base.definition import defutils
from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath
from zoo.libs.hive import constants

FOOT_ANIM_ATTRS = [
    {
        "channelBox": True,
        "enums": ["FOOT_CTRL"],
        "isDynamic": True,
        "keyable": False,
        "locked": True,
        "name": "__",
        "Type": zapi.attrtypes.kMFnkEnumAttribute,
    },
    {
        "channelBox": False,
        "default": 0,
        "keyable": True,
        "max": 180,
        "min": -180,
        "name": "ballRoll",
        "Type": zapi.attrtypes.kMFnNumericFloat,
        "value": 0,
    },
    {
        "channelBox": False,
        "default": 0,
        "keyable": True,
        "max": 90,
        "min": -90,
        "name": "toeUpDown",
        "Type": zapi.attrtypes.kMFnUnitAttributeAngle,
        "value": 0,
    },
    {
        "channelBox": False,
        "default": 0,
        "keyable": True,
        "max": 90,
        "min": -90,
        "name": "toeSide",
        "Type": zapi.attrtypes.kMFnUnitAttributeAngle,
        "value": 0,
    },
    {
        "channelBox": False,
        "default": 0,
        "keyable": True,
        "max": 90,
        "min": -90,
        "name": "toeBank",
        "Type": zapi.attrtypes.kMFnUnitAttributeAngle,
        "value": 0,
    },
    {
        "channelBox": False,
        "default": 0,
        "keyable": True,
        "max": 90,
        "min": -90,
        "name": "sideBank",
        "Type": zapi.attrtypes.kMFnNumericFloat,
        "value": 0,
    },
    {
        "channelBox": False,
        "default": 0,
        "keyable": True,
        "max": 180,
        "min": -180,
        "name": "heelSideToSide",
        "Type": zapi.attrtypes.kMFnNumericFloat,
        "value": 0,
    },
]
FOOT_BREAK_ANIM_ATTR = {
    "channelBox": False,
    "default": 65,
    "keyable": True,
    "max": 180,
    "min": -180,
    "name": "footBreak",
    "Type": zapi.attrtypes.kMFnNumericFloat,
    "value": 65,
}
FOOT_VIS_ATTR = {
    "channelBox": True,
    "default": False,
    "keyable": False,
    "name": "ikFootCtrlVis",
    "Type": zapi.attrtypes.kMFnNumericBoolean,
    "value": False,
}


class ReverseFootIkSubSystem(basesubsystem.BaseSubsystem):
    """A subsystem for a reverse Foot IK

    :param component The component instance to act on.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param animAttributeFootBreakInsertAfter: The attribute name to insert the foot break attr after.
    :type animAttributeFootBreakInsertAfter: str
    :param animAttributeVisInsertAfter: The attribute name to insert the anim visibility attributes after.
    :type animAttributeVisInsertAfter: str
    """

    settingSwitchName = "hasFoot"

    def __init__(
        self, component, animAttributeFootBreakInsertAfter, animAttributeVisInsertAfter
    ):
        super(ReverseFootIkSubSystem, self).__init__(component)
        self.parentGuideId = "end"
        self.ballGuideId = "ball"
        self.toeGuideId = "toe"
        self.animAttributesInsertIndex = 0
        self.animAttributeFootBreakInsertAfter = animAttributeFootBreakInsertAfter
        self.animAttributeVisInsertAfter = animAttributeVisInsertAfter
        self._pivotGuideIdsForAlignToWorld = ("heel_piv", "outer_piv", "inner_piv")
        self.guideIds = (
            "heel_piv",
            "outer_piv",
            "inner_piv",
            "toeTip_piv",
            "ballroll_piv",
            "toeTap_piv",
            self.toeGuideId,
            self.ballGuideId,
        )

    def active(self):
        try:
            return self.component.definition.guideLayer.guideSetting(
                "hasReverseFoot"
            ).value
        except AttributeError:
            return True

    def preMatchTo(self):
        rigLayer = self.component.rigLayer()
        pivCtrls = rigLayer.findControls(
            "heel_piv",
            "outer_piv",
            "inner_piv",
            "toeTip_piv",
            "ballroll_piv",
            "toeTap_piv",
        )
        for pivCtrl in pivCtrls[:-1]:
            pivCtrl.resetTransform()

        # reset the ik attributes then set the toeTap pivot ctrl to the jnt transforms
        controlPanel = self.component.controlPanel()
        controlPanel.attribute("lock").set(0)
        controlPanel.ikRoll.set(0)
        controlPanel.ballRoll.set(0)
        controlPanel.sideBank.set(0)
        return {
            "ballMatrix": self.component.deformLayer().joint("ball").worldMatrix(),
            "controls": pivCtrls,
        }

    def matchTo(self, preMatchInfo):
        # reset the ik attributes then set the toeTap pivot ctrl to the jnt transforms
        controlPanel = self.component.controlPanel()
        preMatchInfo["controls"][-1].setWorldMatrix(preMatchInfo["ballMatrix"])
        return {
            "controls": preMatchInfo["controls"],
            "attributes": [
                controlPanel.attribute(i)
                for i in ("ikRoll", "ballRoll", "sideBank", "lock")
            ],
        }

    def deleteGuides(self):
        layer = self.component.definition.guideLayer
        deformLayer = self.component.definition.deformLayer
        layer.deleteGuides(*self.guideIds)
        deformLayer.deleteJoints(*self.guideIds)

    def preUpdateGuideSettings(self, settings):
        requestState = settings.get("hasReverseFoot")
        if requestState is None:
            return False, False

        if not requestState:
            self.deleteGuides()
        else:
            # regenerate the guides and the joints from the originalDefinition by a simple mem copy
            # then recompute the the worldMatrix for the guide and guide shape this is
            # so they're relative to whatever orientation the end guide is in.
            definition = self.component.definition
            origDefinition = self.component.definition.originalDefinition
            guideLayerDef = definition.guideLayer
            deformLayerDef = definition.deformLayer
            endGuide = guideLayerDef.guide(self.parentGuideId)
            origEndGuide = origDefinition.guideLayer.guide(self.parentGuideId)
            footGuides = copy.deepcopy(origEndGuide.children)
            joints = copy.deepcopy(
                origDefinition.deformLayer.joint(self.parentGuideId).children
            )
            endGuide.children = footGuides
            deformLayerDef.joint(self.parentGuideId).children = joints

            def _computeGuidePositions():
                currentEndGuide = endGuide.worldMatrix
                origWorldMtx = origEndGuide.worldMatrix.inverse()

                for origChild in endGuide.iterChildren():
                    origChildWorldMtx = origChild.worldMatrix
                    newWorld = origChildWorldMtx * origWorldMtx * currentEndGuide
                    origChild.worldMatrix = newWorld
                    currentShapeTransform = origChild.shapeTransform
                    shapeOffset = currentShapeTransform * origChildWorldMtx.inverse()
                    newShapeMtx = shapeOffset * currentEndGuide
                    origChild.shapeTransform = newShapeMtx
                    defutils.offsetGuideShapeCVs(
                        origChild["shape"], origWorldMtx, currentEndGuide
                    )

            _computeGuidePositions()

        return True, False

    def preAlignGuides(self):
        if not self.active():
            return [], []
        # ok we now need to align the other guides ensuring we skip the above nodes and twists
        layer = self.component.guideLayer()
        guides = layer.findGuides(*self._pivotGuideIdsForAlignToWorld)
        endGuide, ballGuide, toeGuide = layer.findGuides(
            self.parentGuideId, self.ballGuideId, self.toeGuideId
        )
        endGuidePos = endGuide.translation()
        ballGuideTarget = ballGuide.translation()
        ballGuideTarget.y = endGuidePos.y

        toeTipPivot = layer.guide("toeTip_piv")

        guidesToModify, matrices = [], []
        # for each pivot(inner outer, heel, toe tip) copy the alignment rotation between the end piv to ball
        # onto the pivots.
        for guide in guides:
            if not guide.autoAlign.asBool():
                continue
            transform = guide.transformationMatrix(space=zapi.kWorldSpace)
            rot = mayamath.lookAt(
                endGuidePos,
                ballGuideTarget,
                zapi.Vector(guide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value()),
                zapi.Vector(guide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value()),
                constrainAxis=zapi.Vector(1, 1, 1),
            )
            transform.setRotation(rot)
            matrices.append(transform.asMatrix())
            guidesToModify.append(guide)

        # aim the ball guide to the toe, we have multiple children here so manual is better
        if ballGuide.autoAlign.asBool():
            transform = ballGuide.transformationMatrix(space=zapi.kWorldSpace)
            rot = mayamath.lookAt(
                ballGuide.translation(),
                toeGuide.translation(),
                zapi.Vector(
                    ballGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value()
                ),
                zapi.Vector(
                    ballGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value()
                ),
                constrainAxis=zapi.Vector(1, 1, 1),
            )
            transform.setRotation(rot)
            ballGuideMatrix = transform.asMatrix()
            matrices.append(ballGuideMatrix)
            guidesToModify.append(ballGuide)

        else:
            ballGuideMatrix = ballGuide.worldMatrix()

        if toeGuide.autoAlign.asBool():
            # realign the toe guide by aiming at the ball with the primary aim vector inverted(*-1)
            # this is similar to just zero out but allowing manual and auto align vectors to be used.
            toeTransform = toeGuide.transformationMatrix(space=zapi.kWorldSpace)
            toeRotation = mayamath.lookAt(
                toeGuide.translation(),
                ballGuide.translation(),
                zapi.Vector(
                    toeGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value()
                )
                * -1,
                zapi.Vector(
                    toeGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value()
                ),
            )
            toeTransform.setRotation(toeRotation)
            toeMatrix = toeTransform.asMatrix()
            matrices.append(toeMatrix)
            guidesToModify.append(toeGuide)
        else:
            toeMatrix = toeGuide.worldMatrix()
        guidesToModify.append(toeTipPivot)
        matrices.append(toeMatrix)
        # we force auto align on the toe tip since it's always got to match the toe regardless
        toeTipPivot.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).set(
            toeGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value()
        )
        toeTipPivot.attribute(constants.AUTOALIGNUPVECTOR_ATTR).set(
            toeGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value()
        )
        # set the ball roll and toe tap alignment to the ball roll
        guidesToModify += layer.findGuides("ballroll_piv")

        matrices.append(ballGuideMatrix)
        # batch update the guides.
        # api.setGuidesWorldMatrix(guidesToModify, matrices)

        return guidesToModify, matrices

    def setupDeformLayer(self, parentJoint):
        if not self.active():
            deformLayer = self.component.definition.deformLayer
            deformLayer.deleteJoints(*self.guideIds)
            return

    def preSetupRig(self, parentNode):
        if not self.active():
            return
        defini = self.component.definition
        rigLayerDef = defini.rigLayer
        rigLayerDef.insertSettings(
            "controlPanel",
            self.animAttributesInsertIndex,
            FOOT_ANIM_ATTRS,
        )
        rigLayerDef.insertSettings(
            "controlPanel",
            rigLayerDef.settingIndex(
                "controlPanel", self.animAttributeFootBreakInsertAfter
            )
            + 1,
            [FOOT_BREAK_ANIM_ATTR],
        )
        rigLayerDef.insertSettings(
            "controlPanel",
            rigLayerDef.settingIndex("controlPanel", self.animAttributeVisInsertAfter)
            + 1,
            [FOOT_VIS_ATTR],
        )

    def setupRig(self, parentNode):
        if not self.active():
            return
        namer = self.component.namingConfiguration()
        rigLayer = self.component.rigLayer()
        controlPanel = self.component.controlPanel()
        definition = self.component.definition
        guideLayerDef = definition.guideLayer
        defGuides = {g.id: g for g in guideLayerDef.iterGuides()}
        heelPiv = defGuides["heel_piv"]
        toeTipPiv = defGuides["toeTip_piv"]
        ballRollPiv = defGuides["ballroll_piv"]
        innerPiv = defGuides["inner_piv"]
        outerPiv = defGuides["outer_piv"]
        ballDefinition = defGuides["ball"]
        toeDefinition = defGuides["toe"]

        endIk = rigLayer.joint("endik")

        ikJntParent = endIk
        blendAttr = controlPanel.attribute("ikfk")

        ikJoints = {}
        compName, compSide = self.component.name(), self.component.side()
        # generate the ball and toe joints and controls for both ik and fk
        for guide in (ballDefinition, toeDefinition):
            fkGuideId = guide.id + constants.FKTYPE
            ikGuideId = guide.id + constants.IKTYPE
            ikName = namer.resolve(
                "jointName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "system": constants.IKTYPE,
                    "id": ikGuideId,
                    "type": "joint",
                },
            )

            joint = rigLayer.createJoint(
                name=ikName,
                translate=guide.translate,
                rotate=guide.rotate,
                rotateOrder=guide.rotateOrder,
                parent=ikJntParent,
                id=ikGuideId,
            )
            ikJoints[ikGuideId] = joint
            ikJntParent = joint
            if guide.id == "ball":
                fkGuideName = namer.resolve(
                    "controlName",
                    {
                        "id": guide.id,
                        "componentName": compName,
                        "system": constants.FKTYPE,
                        "side": compSide,
                        "type": "control",
                    },
                )
                ctrl = rigLayer.createControl(
                    name=fkGuideName,
                    id=fkGuideId,
                    rotateOrder=guide.get("rotateOrder", 0),
                    translate=guide.get("translate", (0, 0, 0)),
                    rotate=guide.get("rotate", (0, 0, 0, 1)),
                    parent="endfk",
                    shape=guide.get("shape"),
                    selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                    srts=[{"name": "_".join([fkGuideName, "srt"])}],
                )
                blendAttr.connect(ctrl.visibility)
                ctrl.visibility.hide()

        # create the piv points
        # ballPivot buffer
        #   |-heelpivot
        #       |-outer_roll
        #           |-inner_roll
        #               |-toe_tip
        #                   |-toe_tap
        #                       |-ball->toe ikhandle
        #                   |-ball_roll
        #                       |-leg ikhandle
        #                       |-ankle->ball ikhandle
        #                   |-ball_anim
        pivots = {}
        parent = rigLayer.control("endik")
        heelId = heelPiv.id
        heelName = namer.resolve(
            "controlName",
            {
                "componentName": compName,
                "side": compSide,
                "system": constants.IKTYPE,
                "id": heelId,
                "type": "control",
            },
        )
        heelCtrl = rigLayer.createControl(
            name=heelName,
            id=heelId,
            rotateOrder=heelPiv.get("rotateOrder", 0),
            translate=heelPiv.get("translate", (0, 0, 0)),
            rotate=heelPiv.get("rotate", (0, 0, 0, 1)),
            parent=parent,
            shape=heelPiv.get("shape"),
            selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
            srts=[
                {"name": "_".join([heelName, "srt"])},
                {"name": "_".join([heelName, "attr", "srt"])},
            ],
        )
        parent = heelCtrl
        pivots[heelPiv.id] = heelCtrl

        for piv in (outerPiv, innerPiv, toeTipPiv, ballRollPiv):
            ctrlName = namer.resolve(
                "controlName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "system": constants.IKTYPE,
                    "id": piv.id,
                    "type": "control",
                },
            )
            ctrl = rigLayer.createControl(
                name=ctrlName,
                id=piv.id,
                rotateOrder=piv.get("rotateOrder", 0),
                translate=piv.get("translate", (0, 0, 0)),
                rotate=piv.get("rotate", (0, 0, 0, 1)),
                parent=parent,
                shape=piv.get("shape"),
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                srts=[
                    {"name": "_".join([ctrlName, "srt"])},
                    {"name": "_".join([ctrlName, "attr", "srt"])},
                ],
            )
            parent = ctrl
            pivots[piv.id] = ctrl

        toeTapName = namer.resolve(
            "controlName",
            {
                "componentName": compName,
                "side": compSide,
                "system": constants.IKTYPE,
                "id": "toeTap_piv",
                "type": "control",
            },
        )
        toeTap = rigLayer.createControl(
            name=toeTapName,
            id="toeTap_piv",
            rotateOrder=ballDefinition.get("rotateOrder", 0),
            translate=ballDefinition.get("translate", (0, 0, 0)),
            rotate=ballDefinition.get("rotate", (0, 0, 0, 1)),
            parent=pivots[toeTipPiv.id],
            shape=ballDefinition.get("shape"),
            selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
            srts=[
                {"name": "_".join([toeTapName, "srt"])},
                {"name": "_".join([toeTapName, "attr", "srt"])},
            ],
        )
        pivots["toeTap_piv"] = toeTap

        # deal with the ikSolves
        ballRoll = pivots[ballRollPiv.id]
        # rigLayer.addTaggedNode("ballIkHandle")
        # ikhandleArray = rigLayer.attribute("ikhandles")
        # ikhandleArray.element(0).sourceNode().setParent(ballRoll)
        ballIkJnt = ikJoints["ballik"]
        toeIkJnt = ikJoints["toeik"]
        for startjnt, endjnt, par in (
            (endIk, ballIkJnt, ballRoll),
            (ballIkJnt, toeIkJnt, toeTap),
        ):
            ikHandle, ikEffector = zapi.createIkHandle(
                name=namer.resolve(
                    "ikHandle",
                    {
                        "componentName": compName,
                        "section": endjnt.id(),
                        "side": compSide,
                        "type": "ikHandle",
                    },
                ),
                startJoint=startjnt,
                endJoint=endjnt,
                solverType=zapi.kIkSCSolveType,
                parent=par,
            )
            ikHandle.hide()
            ikEffector.hide()
            # handleElement = ikhandleArray.nextAvailableElementPlug()
            # ikHandle.message.connect(handleElement)

        footRollNodes = _createFootRoll(
            self.component, controlPanel, pivots, heelPiv, ballDefinition, toeTipPiv
        )
        sideRollNodes = _createSideRoll(controlPanel, pivots, innerPiv, outerPiv)
        heelToeNodes = _createHeelToeRolls(
            self.component, controlPanel, pivots, heelPiv, ballDefinition
        )
        visibilityNodes = _setupVisibility(self.component, controlPanel, pivots)
        rigLayer.addExtraNodes(footRollNodes)
        rigLayer.addExtraNodes(sideRollNodes)
        rigLayer.addExtraNodes(heelToeNodes)
        rigLayer.addExtraNodes(visibilityNodes)


def _setupVisibility(component, controlPanel, scenePivots):
    namer = component.namingConfiguration()
    compName, compSide = component.name(), component.side()
    footControlVis = controlPanel.attribute("ikFootCtrlVis")
    # construct vis ikfk + control vis logic nodes
    footControlVisSwitchLogic = zapi.logicFloat(
        controlPanel.ikfk,
        0.0,
        4,
        None,
        name=namer.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "footControlVis_equalGt",
                "type": "floatLogic",
            },
        ),
    )

    footControlVisSwitchNode = zapi.conditionFloat(
        footControlVis,
        0.0,
        footControlVisSwitchLogic.outBool,
        None,
        name=namer.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "footControlVis_cond",
                "type": "floatCondition",
            },
        ),
    )
    footControlVisSwitchPlug = footControlVisSwitchNode.outFloat

    for i in scenePivots.values():
        [footControlVisSwitchPlug.connect(obj.visibility) for obj in i.shapes()]
        i.showHideAttributes(
            zapi.localTranslateAttrs + zapi.localScaleAttrs + ["visibility"],
            state=False,
        )
        i.setLockStateOnAttributes(["translate", "scale", "visibility"])
    return footControlVisSwitchLogic, footControlVisSwitchNode


def _createHeelToeRolls(
    component, controlPanel, scenePivots, heelDefinition, ballDefinition
):
    naming = component.namingConfiguration()
    toeTapAttrTransform = scenePivots["toeTap_piv"].srt(1)
    heelGuideAimVector = heelDefinition.attribute(
        constants.AUTOALIGNAIMVECTOR_ATTR
    ).value
    heelGuideUpVector = heelDefinition.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value
    ballGuideAimVector = ballDefinition.attribute(
        constants.AUTOALIGNAIMVECTOR_ATTR
    ).value
    ballGuideUpVector = ballDefinition.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value
    heelPivot = scenePivots["heel_piv"].srt(1)
    compName, compSide = component.name(), component.side()

    outerDoubleLinear = setupRotationAxisDriver(
        "_".join([heelPivot.name(False), "invert"]),
        zapi.Vector(heelGuideAimVector),
        zapi.Vector(heelGuideUpVector),
        controlPanel.heelSideToSide,
        heelPivot,
        overrideInvert=True,
        useVector=1,
    )
    nodes = []
    if outerDoubleLinear:
        nodes.append(outerDoubleLinear)
    upDownDoubleLinear = setupRotationAxisDriver(
        naming.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "toeUpDown_invert",
                "type": "multDoubleLinear",
            },
        ),
        zapi.Vector(ballGuideAimVector),
        zapi.Vector(ballGuideUpVector),
        controlPanel.toeUpDown,
        toeTapAttrTransform,
        overrideInvert=True,
    )
    sideDoubleLinear = setupRotationAxisDriver(
        naming.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "toeSide_invert",
                "type": "multDoubleLinear",
            },
        ),
        zapi.Vector(ballGuideAimVector),
        zapi.Vector(ballGuideUpVector),
        controlPanel.toeSide,
        toeTapAttrTransform,
        overrideInvert=True,
        useVector=1,
    )
    bankDoubleLinear = setupRotationAxisDriver(
        naming.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "toeBank_invert",
                "type": "multDoubleLinear",
            },
        ),
        zapi.Vector(ballGuideAimVector),
        zapi.Vector(ballGuideUpVector),
        controlPanel.toeBank,
        toeTapAttrTransform,
        overrideInvert=False,
        useVector=0,
    )
    if upDownDoubleLinear:
        nodes.append(upDownDoubleLinear)
    if sideDoubleLinear:
        nodes.append(sideDoubleLinear)
    if bankDoubleLinear:
        nodes.append(bankDoubleLinear)

    return nodes


def _createSideRoll(controlPanel, scenePivots, innerPivDefinition, outputPivDefinition):
    sideRollPlug = controlPanel.attribute("sideBank")
    sideRollCond = zapi.conditionVector(
        sideRollPlug,
        0.0,
        (sideRollPlug, 0.0, 0.0),
        (0.0, sideRollPlug, 0.0),
        operation=4,
        name="sideBank_greater",
    )

    innerGuideAimVector = innerPivDefinition.attribute(
        constants.AUTOALIGNAIMVECTOR_ATTR
    ).value
    innerGuideUpVector = innerPivDefinition.attribute(
        constants.AUTOALIGNUPVECTOR_ATTR
    ).value
    outerGuideAimVector = outputPivDefinition.attribute(
        constants.AUTOALIGNAIMVECTOR_ATTR
    ).value
    outerGuideUpVector = outputPivDefinition.attribute(
        constants.AUTOALIGNUPVECTOR_ATTR
    ).value

    innerPiv = scenePivots["inner_piv"].srt(index=1)
    outerPiv = scenePivots["outer_piv"].srt(index=1)

    innerDoubleLinear = setupRotationAxisDriver(
        "_".join([innerPiv.name(False), "invert"]),
        zapi.Vector(innerGuideAimVector),
        zapi.Vector(outerGuideUpVector),
        sideRollCond.outColorG,
        innerPiv,
        overrideInvert=True,
        useVector=0,
    )
    outerDoubleLinear = setupRotationAxisDriver(
        "_".join([outerPiv.name(False), "invert"]),
        zapi.Vector(outerGuideAimVector),
        zapi.Vector(innerGuideUpVector),
        sideRollCond.outColorR,
        outerPiv,
        overrideInvert=True,
        useVector=0,
    )
    newNodes = [sideRollCond]
    if innerDoubleLinear:
        newNodes.append(innerDoubleLinear)
    if outerDoubleLinear:
        newNodes.append(outerDoubleLinear)

    return newNodes


def _createFootRoll(
    component,
    controlPanel,
    scenePivots,
    heelDefinition,
    ballRollDefinition,
    toeDefinition,
):
    """Sets up the reverse foot roll attributes in a way where we adapt to the auto alignment
    values making it possible to support multiple orientations.

    :param controlPanel:
    :type controlPanel: :class:`api.SettingsNode`
    :param scenePivots:
    :type scenePivots: dict[str, :class:`zapi.DagNode`]
    :param toeDefinition:
    :type toeDefinition: :class:`api.GuideDefinition`
    :type ballRollDefinition: :class:`api.GuideDefinition`
    :return:
    :rtype:
    """
    namer = component.namingConfiguration()
    compName, compSide = component.name(), component.side()

    createdNodes = []
    ballRollPiv = scenePivots["ballroll_piv"].srt(index=1)
    ballRollTipGuideAimVector = ballRollDefinition.attribute(
        constants.AUTOALIGNAIMVECTOR_ATTR
    ).value
    ballRollGuideUpVector = ballRollDefinition.attribute(
        constants.AUTOALIGNUPVECTOR_ATTR
    ).value
    heelGuideAimVector = heelDefinition.attribute(
        constants.AUTOALIGNAIMVECTOR_ATTR
    ).value
    heelGuideUpVector = heelDefinition.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value
    setRange = zapi.createSetRange(
        name=namer.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "ballPivBallRollBreak",
                "type": "setRange",
            },
        ),
        value=(controlPanel.ballRoll, controlPanel.ballRoll, controlPanel.ballRoll),
        min_=(0.0, 0.0, -180),
        max_=(180, controlPanel.footBreak, 0.0),
        oldMin=(controlPanel.footBreak, 0.0, -180),
        oldMax=(180, controlPanel.footBreak, 0.0),
    )
    # condition for toe tip
    ballRollBreak = zapi.conditionVector(
        controlPanel.ballRoll,
        controlPanel.footBreak,
        (setRange.outValueX, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        operation=2,
        name=namer.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "ballRollBreakGreatThan",
                "type": "condition",
            },
        ),
    )
    # condition for the heel, below zero rotation
    n = setupRotationAxisDriver(
        namer.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "heelRollInvert",
                "type": "multDoubleLinear",
            },
        ),
        zapi.Vector(heelGuideAimVector) * -1,
        zapi.Vector(heelGuideUpVector),
        setRange.outValueZ,
        scenePivots["heel_piv"].srt(1),
        overrideInvert=True,
    )
    if n is not None:
        createdNodes.append(n)

    # ball roll
    n = setupRotationAxisDriver(
        namer.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "ballRollInvert",
                "type": "multDoubleLinear",
            },
        ),
        zapi.Vector(ballRollTipGuideAimVector) * -1,
        zapi.Vector(ballRollGuideUpVector),
        setRange.outValueY,
        ballRollPiv,
    )
    if n is not None:
        createdNodes.append(n)

    createdNodes += [setRange, ballRollBreak]

    # post foot break rotation == toe rotation
    n = setupRotationAxisDriver(
        namer.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "ballRollToeInvert",
                "type": "multDoubleLinear",
            },
        ),
        toeDefinition.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value * -1.0,
        toeDefinition.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value,
        ballRollBreak.outColorR,
        scenePivots["toeTip_piv"].srt(index=1),
        # useVector=0
    )
    if n is not None:
        createdNodes.append(n)
    return createdNodes


def setupRotationAxisDriver(
    name,
    aimVector,
    upVector,
    inputPlug,
    outputTransformNode,
    overrideInvert=False,
    useVector=-1,
):
    """

    :param name:
    :type name:
    :param aimVector:
    :type aimVector:
    :param upVector:
    :type upVector:
    :param inputPlug:
    :type inputPlug:
    :param outputTransformNode:
    :type outputTransformNode:
    :param overrideInvert:
    :type overrideInvert:
    :param useVector:
    :type useVector:
    :return:
    :rtype:
    """
    axisIndex, isNegative = mayamath.perpendicularAxisFromAlignVectors(
        zapi.Vector(aimVector), zapi.Vector(upVector)
    )
    if useVector >= 0:
        attributeName = "rotate" + mayamath.primaryAxisNameFromVector(
            aimVector if useVector == 0 else upVector
        )
    else:
        attributeName = zapi.localRotateAttrs[axisIndex]
    outputAttr = inputPlug
    doubleLinear = None
    if isNegative and not overrideInvert:
        doubleLinear = zapi.createDG(name, "multDoubleLinear")
        outputAttr.connect(doubleLinear.input1)
        doubleLinear.input2.set(-1)
        outputAttr = doubleLinear.output
    outputAttr.connect(outputTransformNode.attribute(attributeName))
    return doubleLinear
