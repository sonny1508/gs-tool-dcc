from collections import OrderedDict

from maya import cmds
from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.api import curves
from zoo.libs.maya.utils import mayamath
from zoo.libs.utils import zoomath


class SpineIkComponent(api.Component):
    creator = "David Sparrow"
    definitionName = "spineIk"
    uiData = {"icon": "componentSpine", "iconColor": (), "displayName": "Spine IK"}
    _jointNumPrefix = "bind"
    _fkNumPrefix = "fk"
    _ikSplineNumPrefix = "spineIk"
    _guideCurveInfluenceIds = (
        "startCurvePiv",
        "tweaker00",
        "tweaker01",
        "tweaker02",
        "endCurvePiv",
    )

    _splineCrvAttributeName = "splineIkCrv"
    _animSquashCurveAttrName = "ikSplineSquashCrv"
    _stretchOffLimitAttrName = "stretchOffLimit"
    # static control ids
    _controlIds = (
        "cog",
        "hipSwing",
        "cogGimbal",
        "hips",
        "ctrl02",
        "tweaker01",
        "tweaker02",
        "tweaker00",
    )
    _triggerGuideSettings = ("jointCount", "fkCtrlCount")
    _controlIdsWithSpaces = (
        "cog",
        "hipSwing",
        "hips",
        "fk00",
        "fk01",  # ,
        # "ctrl02"
    )

    _fkCtrlVisAttr = "fkCtrlVis"
    _ikCtrlVisAttr = "ikCtrlVis"
    _tweakerCtrlVisAttr = "tweakerCtrlVis"

    @classmethod
    def jointIdForNumber(cls, number):
        return cls._jointNumPrefix + str(number).zfill(2)

    @classmethod
    def ikSplineJointIdForNumber(cls, number):
        return cls._ikSplineNumPrefix + str(number).zfill(2)

    @classmethod
    def fkGuideIdForNumber(cls, number):
        return cls._fkNumPrefix + str(number).zfill(2)

    def animCurve(self):
        return self.meta.sourceNodeByName(self._animSquashCurveAttrName)

    def idMapping(self):
        """Returns the guide id to joint id mapping"""
        guideLayer = self.definition.guideLayer
        bindJointCount = guideLayer.guideSetting("jointCount").value

        deformIds = {}
        outputIds = {}
        inputIds = {}
        rigLayerIds = {i: i for i in self._controlIds}
        for index in range(bindJointCount):
            jntId = self.jointIdForNumber(index)
            deformIds[jntId] = jntId
            outputIds[jntId] = jntId

        for index in range(guideLayer.guideSetting("fkCtrlCount").value):
            ctrlId = self.fkGuideIdForNumber(index)
            rigLayerIds[ctrlId] = ctrlId

        return {
            api.constants.DEFORM_LAYER_TYPE: deformIds,
            api.constants.INPUT_LAYER_TYPE: inputIds,
            api.constants.OUTPUT_LAYER_TYPE: outputIds,
            api.constants.RIG_LAYER_TYPE: rigLayerIds,
        }

    def spaceSwitchUIData(self):
        driven = []
        drivers = [
            api.SpaceSwitchUIDriver(
                id_=api.pathAsDefExpression(("self", "inputLayer", "parent")),
                label="Parent Component",
                internal=True,
            ),
            api.SpaceSwitchUIDriver(
                id_=api.pathAsDefExpression(("self", "inputLayer", "world")),
                label="World Space",
                internal=True,
            ),
        ]

        guideLayerDef = self.definition.guideLayer
        drivenIds = [
            "cog",
            "cogGimbal",
            "hips",
            "hipSwing",
            "ctrl02",
            "tweaker00",
            "tweaker01",
            "tweaker02",
        ]
        fkCount = guideLayerDef.guideSetting("fkCtrlCount").value
        drivenIds.extend(self.fkGuideIdForNumber(i) for i in range(fkCount))
        excludeDrivers = ("worldUpVec", "worldUpVecRef", "startCurvePiv", "endCurvePiv")
        # setup driver ui list but rename "fk" to "ctrl" to match our default naming
        for guide in guideLayerDef.iterGuides(includeRoot=False):
            guideId = guide.id
            if guideId in excludeDrivers:
                continue
            name = guide.name
            if guideId.startswith("fk"):
                name = guide.name.replace("fk", "ctrl")
            drivers.append(
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "rigLayer", guideId)),
                    label=name,
                )
            )
        # setup driven ui list but rename "fk" to "ctrl" to match our default naming
        for guide in guideLayerDef.findGuides(*drivenIds):
            guideId = guide.id
            name = guide.name
            if guideId.startswith("fk"):
                name = guide.name.replace("fk", "ctrl")
            driven.append(
                api.SpaceSwitchUIDriven(
                    id_=api.pathAsDefExpression(("self", "rigLayer", guideId)),
                    label=name,
                )
            )

        return {"driven": driven, "drivers": drivers}

    def updateGuideSettings(self, settings):

        originalGuideSettings = super(SpineIkComponent, self).updateGuideSettings(
            settings
        )
        if any(i in settings for i in self._triggerGuideSettings):
            # ensure the definition contains the latest scene state.
            # todo: starting to think we need to proxy the component class
            self.serializeFromScene(layerIds=api.constants.GUIDE_LAYER_TYPE)
            self.deleteGuide()
            self.rig.buildGuides([self])

        return originalGuideSettings

    def preSetupGuide(self):
        # generateFk guides between the cog position the mid ikControl and parent the tweaker01 to the last
        # generatedFK guide
        nameConfig = self.namingConfiguration()
        guideLayer = self.definition.guideLayer
        fkCtrlCount = guideLayer.guideSetting("fkCtrlCount").value
        bindJointCount = guideLayer.guideSetting("jointCount").value
        fkGuides = [
            i
            for i in guideLayer.iterGuides(includeRoot=False)
            if i.id.startswith(self._fkNumPrefix)
        ]
        bindGuides = [
            i
            for i in guideLayer.iterGuides(includeRoot=False)
            if i.id.startswith(self._jointNumPrefix)
        ]

        currentFkGuideCount = max(0, len(fkGuides))
        currentBindGuideCount = max(0, len(bindGuides))

        fkParentGuide = guideLayer.guide("startCurvePiv")
        # handle FK
        # if the definition is the same as the required then just call the base
        # this will happen on a rebuild with a single guide count difference
        if currentFkGuideCount != fkCtrlCount:
            # case where the new count is less than the current, in this case we just
            # delete the definition for the guide from the end.
            if fkCtrlCount < currentFkGuideCount:
                fkParentGuide = fkGuides[fkCtrlCount].id
                guideLayer.deleteGuides(fkParentGuide)

            else:
                # the parent for the fk is the end guide ie -1
                if currentFkGuideCount:
                    fkParentGuide = fkGuides[-1]
                self._createFkGuides(
                    guideLayer,
                    nameConfig,
                    parentGuide=fkParentGuide,
                    fkGuides=fkGuides,
                    count=fkCtrlCount,
                )
        # handle Bind skeleton guides
        bindParent = guideLayer.guide("root")
        # if the definition is the same as the required then just call the base
        # this will happen on a rebuild with a single guide count difference
        if currentBindGuideCount != bindJointCount:
            attrsToDelete = []
            for attr in list(guideLayer.iterGuideSettings()):
                if attr.name.endswith("Distance"):
                    attrsToDelete.append(attr.name)
            guideLayer.deleteSettings(attrsToDelete)
            # case where the new count is less than the current, in this case we just
            # delete the definition for the guide from the end.
            if bindJointCount < currentBindGuideCount:
                bindParent = bindGuides[bindJointCount].id
                guideLayer.deleteGuides(bindParent)
                # lerp and update the guide settings. 2.0 is the parameter length of mayas nurbs curve
                for index, uValue in enumerate(
                    zoomath.lerpCount(0.0, 1.0, bindJointCount)
                ):
                    guideId = self.jointIdForNumber(index)
                    self._createOrUpdateDistanceGuideSetting(
                        guideLayer, guideId, uValue
                    )

            else:

                # the parent for the fk is the end guide ie -1
                if currentBindGuideCount:
                    bindParent = bindGuides[-1]
                _, __ = self._createBindGuides(
                    guideLayer,
                    nameConfig,
                    parentGuide=bindParent,
                    bindGuides=bindGuides,
                    count=bindJointCount,
                )

        super(SpineIkComponent, self).preSetupGuide()

    def _createOrUpdateDistanceGuideSetting(self, guideLayer, guideId, value):
        """internal helper method to generate the distance setting for a bind guide.
        This will either create one or update the existing definition value.

        :type guideLayer: :class:`api.GuideLayerDefinition`
        :type guideId: str
        :type value: float
        """
        distanceSettingName = "{}Distance".format(guideId)
        existingSetting = guideLayer.guideSetting(distanceSettingName)
        if not existingSetting:
            distanceSetting = api.AttributeDefinition(
                name="{}Distance".format(guideId),
                Type=zapi.attrtypes.kMFnNumericFloat,
                channelBox=True,
                keyable=False,
                value=value,
                max=1,
                min=0,
                default=value,
            )
            guideLayer.addGuideSetting(distanceSetting)
        else:
            existingSetting.value = value
            existingSetting.default = value

    def _createBindGuides(self, guideLayer, nameConfig, parentGuide, bindGuides, count):
        """

        :param guideLayer:
        :type guideLayer: :class:`api.GuideLayerDefinition`
        :param nameConfig:
        :type nameConfig:
        :param parentGuide:
        :type parentGuide:
        :param bindGuides:
        :type bindGuides:
        :param count:
        :type count:
        :return:
        :rtype:
        """
        bindGuidesIdMap = {i.id: i for i in bindGuides}

        compName, compSide = self.name(), self.side()
        guides = []
        # bind guides
        for index, value in enumerate(zoomath.lerpCount(0, 1, count)):
            guideId = self.jointIdForNumber(index)
            existingGuide = bindGuidesIdMap.get(guideId)

            transform = parentGuide.worldMatrix
            if not existingGuide:
                name = nameConfig.resolve(
                    "guideName",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "id": guideId,
                        "type": "guide",
                    },
                )
                existingGuide = self._createGuide(
                    guideLayer,
                    name=name,
                    guideId=guideId,
                    worldMatrix=transform,
                    rotationOrder=parentGuide.rotateOrder,
                    parent=parentGuide.id,
                    shape=None,
                )
            else:
                form = zapi.TransformationMatrix(transform)
                existingGuide.translate = list(form.translation(zapi.kWorldSpace))
                existingGuide.rotate = list(form.rotation(asQuaternion=True))
                existingGuide.scale = list(form.scale(zapi.kWorldSpace))
                existingGuide.shapeTransform = dict(
                    translate = list(form.translation(zapi.kWorldSpace)),
                    rotate = list(form.rotation(asQuaternion=True)),
                    scale = list(form.scale(zapi.kWorldSpace))
                )
            self._createOrUpdateDistanceGuideSetting(guideLayer, guideId, value)

            guides.append(existingGuide)
            parentGuide = existingGuide
        return parentGuide, guides

    def _createFkGuides(self, guideLayer, nameConfig, parentGuide, fkGuides, count):
        fkGuidesIdMap = {i.id: i for i in fkGuides}
        sceneLayer = self.guideLayer()
        sceneGuides = {i.id(): i for i in sceneLayer.iterGuides(includeRoot=False)}
        fkCtrls = []
        compName, compSide = self.name(), self.side()
        startPosition, endPosition = (
            guideLayer.guide("cog").translate,
            guideLayer.guide("tweaker02").translate,
        )
        parentId = "root"
        # fk guides
        for index, [position, _] in enumerate(
            mayamath.firstLastOffsetLinearPointDistribution(
                zapi.Vector(startPosition), zapi.Vector(endPosition), count, offset=0.0
            )
        ):
            guideId = self.fkGuideIdForNumber(index)
            existingGuideDef = fkGuidesIdMap.get(guideId)
            existingSceneGuide = sceneGuides.get(guideId)
            transform = zapi.TransformationMatrix()
            transform.setTranslation(position, zapi.kWorldSpace)
            if not existingGuideDef:
                name = nameConfig.resolve(
                    "guideName",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "id": guideId,
                        "type": "guide",
                    },
                )
                existingGuideDef = self._createGuide(
                    guideLayer,
                    name=name,
                    guideId=guideId,
                    worldMatrix=transform,
                    rotationOrder=parentGuide.rotateOrder,
                    pivotColor=[0.25, 1, 0],
                    parent=parentId,
                    pivotShape="cube",
                )
            else:
                existingGuideDef.worldMatrix = transform.asMatrix()
            if existingSceneGuide:
                existingSceneGuide.setWorldMatrix(transform.asMatrix())
                existingSceneGuide.shapeNode().resetTransform(
                    translate=True, rotate=True, scale=False
                )
            fkCtrls.append(existingGuideDef)
            parentGuide = existingGuideDef
            parentId = parentGuide.id
        tweaker01 = sceneLayer.guide("tweaker01")
        if tweaker01 is not None:
            transform = zapi.TransformationMatrix(fkCtrls[-1].worldMatrix)
            tweaker01.setTranslation(
                transform.translation(zapi.kWorldSpace), zapi.kWorldSpace
            )
        return parentGuide, fkCtrls

    def _createGuide(
        self,
        guideLayer,
        name,
        guideId,
        parent,
        worldMatrix,
        rotationOrder,
        pivotColor=api.constants.DEFAULT_GUIDE_PIVOT_COLOR,
        shape="circle",
        pivotShape="sphere",
    ):
        """

        :param guideLayer:
        :type guideLayer: :class:`api.GuideDefinition`
        :param name:
        :type name: str
        :param guideId:
        :type guideId: str
        :param parent:
        :type parent: str
        :param worldMatrix:
        :type worldMatrix: :class:`zapi.Matrix`
        :param rotationOrder:
        :type rotationOrder: int
        :param pivotColor:
        :type pivotColor: tuple
        :return:
        :rtype: :class:`api.GuideDefinition`
        """
        transform = zapi.TransformationMatrix(worldMatrix)

        return guideLayer.createGuide(
            name=name,
            shape=shape,
            id=guideId,
            parent=parent,
            color=(0.0, 0.5, 0.5),
            rotationOrder=rotationOrder,
            pivotShape=pivotShape,
            # cast to list because we don't auto do this in the definition just yet
            translate=list(transform.translation(zapi.kWorldSpace)),
            rotation=list(transform.rotation(asQuaternion=True)),
            scale=list(transform.scale(zapi.kWorldSpace)),
            selectionChildHighlighting=self.configuration.selectionChildHighlighting,
            shapeTransform=dict(
                translate=list(transform.translation(zapi.kWorldSpace)),
                rotation=list(transform.rotation(asQuaternion=True)),
                scale=list(transform.scale(zapi.kWorldSpace)),
            ),
            srts=[{"name": "_".join((guideId, "piv", "srt"))}],
            pivotColor=pivotColor,
        )

    def _purgeGuideMotionPaths(self, srtAttr, motionPathAttr):
        # delete any existing spline srts because it's much easier than diffing the scene.
        modifier = zapi.dagModifier()
        for splineSrtElement in srtAttr:
            sourceNode = splineSrtElement.sourceNode()
            if sourceNode is not None:
                sourceNode.delete(mod=modifier, apply=False)
        # delete any existing spline motionPaths because it's much easier than diffing the scene.
        for splineMotionPathsAttr in motionPathAttr:
            sourceNode = splineMotionPathsAttr.sourceNode()
            if sourceNode is not None:
                sourceNode.delete(mod=modifier, apply=False)
        modifier.doIt()

    def postSetupGuide(self):
        """Overridden to add the spline curve and bind the joint guides to spline via motionPath"""
        guideLayer = self.guideLayer()
        nameConfig = self.namingConfiguration()
        guideLayerTransform = guideLayer.rootTransform()
        jointCount = self.definition.guideLayer.guideSetting("jointCount").value
        bindGuides = [
            i
            for i in guideLayer.iterGuides(includeRoot=False)
            if i.id().startswith(self._jointNumPrefix)
        ]
        settingsNode = guideLayer.guideSettings()
        curve, extras = api.splineutils.createCurveFromDefinition(
            self.definition,
            layer=guideLayer,
            influences=guideLayer.findGuides(*self._guideCurveInfluenceIds),
            parent=guideLayerTransform,
            attributeName=self._splineCrvAttributeName,
            curveName="spineSpline_crv",
            namingObject=nameConfig,
            namingRule="object",
            curveVisControlAttr=settingsNode.showCurveTemplate,
        )
        animCurveSquashSettingAttr = self.meta.addAttribute(
            self._animSquashCurveAttrName, Type=zapi.attrtypes.kMFnMessageAttribute
        )
        # track the srts created for attaching the spline
        splineSrtAttr = guideLayer.addAttribute(
            "splineSrts", Type=zapi.attrtypes.kMFnMessageAttribute, isArray=True
        )
        splineMotionPathsAttr = guideLayer.addAttribute(
            "splineMotionPaths", Type=zapi.attrtypes.kMFnMessageAttribute, isArray=True
        )
        squashCurve = animCurveSquashSettingAttr.sourceNode()  # type: zapi.AnimCurve
        if squashCurve is None:
            # create the animation squash curve node which the user can interact with
            squashCurve = api.splineutils.createSquashGuideCurve(
                nameConfig.resolve(
                    "object",
                    {
                        "componentName": self.name(),
                        "side": self.side(),
                        "section": "squashCurve",
                        "type": "animCurve",
                    },
                ),
                [0, jointCount - 1, jointCount],
                [0, -1, 0],
            )
            self.meta.connectToByPlug(animCurveSquashSettingAttr, squashCurve)
            container = self.container()
            if container is not None:
                container.addNode(squashCurve)
                container.publishNode(squashCurve)
        else:
            keyCount = jointCount - 1
            squashCurve.addKeysWithTangents(
                [0, keyCount * 0.5, keyCount],
                [0, -1, 0],
                tangentInTypeArray=[
                    zapi.kTangentLinear,
                    zapi.kTangentClamped,
                    zapi.kTangentLinear,
                ],
                tangentOutTypeArray=[
                    zapi.kTangentLinear,
                    zapi.kTangentClamped,
                    zapi.kTangentLinear,
                ],
                convertUnits=False,
                keepExistingKeys=False,
            )

        guideLayer.addExtraNodes(extras + [curve])

        self._purgeGuideMotionPaths(splineSrtAttr, splineMotionPathsAttr)
        self._createMotionPaths(
            guideLayer,
            settingsNode,
            guideLayerTransform,
            bindGuides,
            curve,
            splineSrtAttr,
            splineMotionPathsAttr,
            jointCount,
        )

        cmds.displaySmoothness(curve.fullPathName(), polygonObject=1, pointsWire=16)
        # now connect the custom visibility switches
        guidesVisNodes = guideLayer.findGuides(
            "cogGimbal", "hipSwing", self.fkGuideIdForNumber(0)
        )
        cogGimbalVis = settingsNode.cogGimbalVis
        hipSwingVis = settingsNode.hipSwingVis
        fkVis = settingsNode.attribute("fkVis")
        for visAttr, c in zip([cogGimbalVis, hipSwingVis, fkVis], guidesVisNodes):
            for shape in c.pivotShapes():
                visAttr.connect(shape.visibility)
        for i in guideLayer.guide("startCurvePiv").pivotShapes():
            i.visibility.set(0)
            i.visibility.lock(True)
        self._createSpaceSwitches()
        super(SpineIkComponent, self).postSetupGuide()

    def _createMotionPaths(
        self,
        guideLayer,
        settingsNode,
        guideLayerTransform,
        bindGuides,
        curve,
        splineSrtAttr,
        splineMotionPathsAttr,
        jointCount,
    ):
        worldUpVectorGuide = guideLayer.guide("worldUpVec")
        for bindGuide, [srtTransform, motionPath] in zip(
            bindGuides,
            curves.iterGenerateSrtAlongCurve(
                curve.shapes()[0].dagPath(),
                jointCount,
                "bindGuideSrt",
                rotate=True,
                fractionMode=True,
            ),
        ):
            aimVector = bindGuide.autoAlignAimVector.value()
            upVector = bindGuide.autoAlignUpVector.value()
            axisIndex, invert = mayamath.perpendicularAxisFromAlignVectors(
                aimVector, upVector
            )
            motionPathUpVector = mayamath.AXIS_VECTOR_BY_IDX[axisIndex]
            bindId = bindGuide.id()
            motionPath = zapi.DGNode(motionPath)
            srtTransform = zapi.nodeByObject(srtTransform)
            motionPath.worldUpType.set(2)
            motionPath.worldUpVector.set(motionPathUpVector)
            worldUpVectorGuide.attribute("worldMatrix")[0].connect(
                motionPath.worldUpMatrix
            )
            srtTransform.setParent(guideLayerTransform)
            guideLayer.connectToByPlug(
                splineSrtAttr.nextAvailableDestElementPlug(), srtTransform
            )
            guideLayer.connectToByPlug(
                splineMotionPathsAttr.nextAvailableDestElementPlug(), motionPath
            )
            guideSrt = bindGuide.srt()
            guideSrt.setWorldMatrix(srtTransform.worldMatrix())
            with zapi.lockStateAttrContext(bindGuide, zapi.localTransformAttrs, False):
                bindGuide.resetTransform(scale=False)
            bindGuide.setLockStateOnAttributes(
                zapi.localTransformAttrs, True
            )  # enforce lock state
            _buildJntConstraint(
                guideSrt,
                [srtTransform],
                guideLayer,
                scale=False,
                constraintType=(
                    "parent"
                    if bindId
                    not in (
                        self.jointIdForNumber(0),
                        self.jointIdForNumber(jointCount - 1),
                    )
                    else "point"
                ),
            )
            guideLayer.addExtraNodes((motionPath, srtTransform))

            distanceSetting = settingsNode.attribute(
                "{}Distance".format(bindGuide.id())
            )
            if distanceSetting.value() == 0.0:
                distanceSetting.set(motionPath.uValue.value().value)
            distanceSetting.connect(motionPath.uValue)

    def _createSpaceSwitches(self):
        guideLayer = self.guideLayer()
        definition = self.definition
        drivers = [
            {
                "label": "parent",
                "driver": api.constants.ATTR_EXPR_INHERIT_TOKEN,
                "permissions": {
                    "allowDriverChange": False,
                    "allowRename": False,
                    "value": True,
                },
            },
            {
                "label": "world",
                "driver": api.pathAsDefExpression(("self", "inputLayer", "world")),
                "permissions": {
                    "allowDriverChange": False,
                    "allowRename": False,
                    "value": True,
                },
            },
        ]
        cogAsDriver = {
            "label": "cog",
            "driver": api.pathAsDefExpression(("self", "rigLayer", "cog")),
            "permissions": {
                "allowDriverChange": False,
                "allowRename": False,
                "value": True,
            },
        }
        # remove old ctrl02 space from hive 1.0.0b3 which we replaced with the parent space in self._setupCtrlSpaceSwitch for now
        definition.removeSpaceSwitch("ctrl02_rotSpace")
        # now create the spaces
        insertAfter = "ctrl02_space"
        for index, guide in enumerate(
            guideLayer.findGuides(*self._controlIdsWithSpaces)
        ):
            guideDrivers = list(drivers)
            if index != 0:
                guideDrivers.append(cogAsDriver)
            _createSpace(definition, guide, guideDrivers, insertAfter)
        # temp removal
        # create the world, parent
        # ctrl02Guide = guideLayer.guide("ctrl02")
        # _createSpace(definition, ctrl02Guide, drivers, insertAfter, spaceType="point",
        #              prefix="transSpace")

    def alignGuides(self):
        """
        cog -> chest
        copy cog rotation -> gimbal/hipSwing
        copy cog rotation -> fkEnd
        hips -> -chest
        chest -> -cog
        fk# exclude end -> fk end
        bind guides child align
        """
        guideLayer = self.guideLayer()
        allGuides = list(guideLayer.iterGuides(includeRoot=False))
        allGuidesMap = {i.id(): i for i in allGuides}
        manualGuides = {
            guide.id(): guide for guide in allGuides if guide.id() in self._controlIds
        }  # type: dict[str, api.Guide]
        fkGuides = [
            guide for guide in allGuides if guide.id().startswith(self._fkNumPrefix)
        ]
        bindGuides = [
            guide for guide in allGuides if guide.id().startswith(self._jointNumPrefix)
        ]

        # pre cache guide access to keep things clean
        cogGuide = manualGuides["cog"]
        cogGimbalGuide = manualGuides["cogGimbal"]
        hipSwingGuide = manualGuides["hipSwing"]
        chestGuide = manualGuides["ctrl02"]
        hipsGuide = manualGuides["hips"]
        tweaker02Guide = manualGuides["tweaker02"]
        tweaker01Guide = manualGuides["tweaker01"]
        tweaker00Guide = manualGuides["tweaker00"]
        baseCurveGuide = allGuidesMap["startCurvePiv"]
        startJointPosition = allGuidesMap[self.jointIdForNumber(00)].translation()
        endJointPosition = allGuidesMap[
            self.jointIdForNumber(len(bindGuides) - 1)
        ].translation()
        chestPosition = chestGuide.translation()
        cogPosition = cogGuide.translation()
        hipSwingPosition = hipSwingGuide.translation()
        # generate the worldUpVector which for lookat algorthim purposes we need to transform
        # it to the world plane on Y
        worldUpRot = allGuidesMap["worldUpVec"]
        worldUpAim = allGuidesMap["worldUpVecRef"]
        worldUpVector = worldUpAim.translation(
            zapi.kWorldSpace
        ) - worldUpRot.translation(zapi.kWorldSpace)

        aimSettings = [
            (cogGuide, cogPosition, chestPosition),
            (cogGimbalGuide, cogPosition, chestPosition),
            (chestGuide, chestPosition, baseCurveGuide.translation(zapi.kWorldSpace)),
            (hipsGuide, hipsGuide.translation(), chestPosition),
            (hipSwingGuide, hipSwingPosition, chestPosition),
            (tweaker02Guide, tweaker02Guide.translation(), endJointPosition),
            (tweaker00Guide, tweaker00Guide.translation(), startJointPosition),
            (tweaker01Guide, tweaker01Guide.translation(), endJointPosition),
        ]
        guidesToAlign = []
        # list of matrices which are set on the guides , taking into account of the auto align
        matricesToSet = []
        # same list of matrices but ignoring auto align , used as reference by other guides which
        # require aligning
        matrices = []
        # cog, chest,hips alignment.
        for guide, source, target in aimSettings:

            if not guide.autoAlign.value():
                continue
            cogTransform = guide.transformationMatrix()
            cogRotation = mayamath.lookAt(
                sourcePosition=source,
                aimPosition=target,
                aimVector=zapi.Vector(guide.autoAlignAimVector.value()),
                upVector=zapi.Vector(guide.autoAlignUpVector.value()),
                worldUpVector=worldUpVector,
            )
            cogTransform.setRotation(cogRotation)

            guidesToAlign.append(guide)
            matricesToSet.append(cogTransform.asMatrix())
        guidesToAlign.append(cogGimbalGuide)
        matricesToSet.append(cogGuide.worldMatrix())
        # bind skeleton guides
        for index, bind in enumerate(bindGuides):
            childGuide = None
            for childGuide in bind.iterChildGuides(recursive=False):
                break

            if childGuide is None:
                rotation = zapi.TransformationMatrix(matrices[-1]).rotation(
                    asQuaternion=True
                )
            else:
                rotation = mayamath.lookAt(
                    sourcePosition=bind.translation(),
                    aimPosition=bindGuides[index + 1].translation(),
                    aimVector=zapi.Vector(bind.autoAlignAimVector.value()),
                    upVector=zapi.Vector(bind.autoAlignUpVector.value()),
                    worldUpVector=worldUpVector,
                )
            bindTransform = bind.transformationMatrix()
            bindTransform.setRotation(rotation)
            matrices.append(bindTransform.asMatrix())
            # we do this after we've determined the transform that way the next joint has a reference point
            # when needed.
            if not bind.autoAlign.value():
                continue
            guidesToAlign.append(bind)
            matricesToSet.append(bindTransform.asMatrix())

        # fkGuides
        for index, guide in enumerate(fkGuides):
            if index == len(fkGuides) - 1:
                rotation = zapi.TransformationMatrix(matrices[-1]).rotation(
                    asQuaternion=True
                )
            else:
                rotation = mayamath.lookAt(
                    sourcePosition=guide.translation(),
                    aimPosition=fkGuides[index + 1].translation(),
                    aimVector=zapi.Vector(guide.autoAlignAimVector.value()),
                    upVector=zapi.Vector(guide.autoAlignUpVector.value()),
                    worldUpVector=worldUpVector,
                )
            bindTransform = guide.transformationMatrix()
            bindTransform.setRotation(rotation)
            matrices.append(bindTransform.asMatrix())
            # we do this after we've determined the transform that way the next joint has a reference fkGuide
            # when needed.
            if not guide.autoAlign.value():
                continue
            guidesToAlign.append(guide)
            matricesToSet.append(bindTransform.asMatrix())

        api.setGuidesWorldMatrix(
            guidesToAlign, matricesToSet, skipLockedTransforms=False
        )

    def setupInputs(self):
        super(SpineIkComponent, self).setupInputs()
        transform = self.definition.guideLayer.guide("cog").transformationMatrix(
            translate=True, rotate=True, scale=False
        )

        self.inputLayer().inputNode("parent").setWorldMatrix(transform.asMatrix())

    def setupDeformLayer(self, parentJoint=None):
        nameConfig = self.namingConfiguration()
        # build skin joints if any
        definition = self.definition
        deformLayerDef = definition.deformLayer
        guideLayer = definition.guideLayer

        compName, compSide = self.name(), self.side()
        parentNode = None
        deformLayerDef.clearJoints()
        for guide in guideLayer.iterGuides(includeRoot=False):
            guideId = guide.id
            if not guideId.startswith(self._jointNumPrefix):
                continue
            name = nameConfig.resolve(
                "skinJointName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": guideId,
                    "type": "joint",
                },
            )
            deformLayerDef.createJoint(
                name=name,
                id=guideId,
                translate=guide.translate,
                rotate=guide.rotate,
                rotateOrder=guide.rotateOrder,
                parent=parentNode,
            )
            parentNode = guide.id

        super(SpineIkComponent, self).setupDeformLayer(parentJoint)

    def setupOutputs(self, parentNode):

        deformLayer = self.definition.deformLayer  # type: api.DeformLayerDefinition
        outputLayer = self.definition.outputLayer  # type: api.OutputLayerDefinition
        nameConfig = self.namingConfiguration()
        compName, compSide = self.name(), self.side()
        parent = None
        outputLayer.clearOutputs()
        for jnt in deformLayer.iterDeformJoints():
            jntId = jnt.id
            name = nameConfig.resolve(
                "outputName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": jntId,
                    "type": "joint",
                },
            )
            outputLayer.createOutput(id=jntId, name=name, parent=parent)
        super(SpineIkComponent, self).setupOutputs(parentNode)
        self._connectOutputs()

    def _connectOutputs(self):
        # connect the outputs  to deform layer
        layer = self.outputLayer()
        joints = {jnt.id(): jnt for jnt in self.deformLayer().joints()}
        for index, output in enumerate(layer.outputs()):
            driverJoint = joints.get(output.id())
            output.setWorldMatrix(driverJoint.worldMatrix())

    def preSetupRig(self, parentNode):
        rigLayerDef = self.definition.rigLayer
        guideLayerDef = self.definition.guideLayer
        animCurve = self.animCurve()
        jointCount = guideLayerDef.guideSetting("jointCount").value
        fkCtrlCount = guideLayerDef.guideSetting("fkCtrlCount").value
        insertAfter = "globalVolume"
        for i in reversed(range(jointCount)):
            settingName = "".join(("volume", str(i).zfill(2)))
            value = animCurve.mfn().evaluate(zapi.Time(i, zapi.Time.k24FPS)) * -1
            rigLayerDef.insertSettingByName(
                "controlPanel",
                insertAfter,
                api.AttributeDefinition(
                    name=settingName,
                    value=value,
                    min=0,
                    default=value,
                    channelBox=False,
                    keyable=True,
                    Type=zapi.attrtypes.kMFnNumericFloat,
                ),
            )
            insertAfter = settingName
        fkCtrlVisInsertAfter = "ctrl02Vis"
        for i in reversed(range(fkCtrlCount)):
            settingName = "".join(("ctrl", str(i).zfill(2), "Vis"))
            rigLayerDef.insertSettingByName(
                "controlPanel",
                fkCtrlVisInsertAfter,
                api.AttributeDefinition(
                    name=settingName,
                    value=True,
                    default=True,
                    channelBox=True,
                    keyable=False,
                    Type=zapi.attrtypes.kMFnNumericBoolean,
                ),
            )
            fkCtrlVisInsertAfter = settingName

        super(SpineIkComponent, self).preSetupRig(parentNode)

    def setupRig(self, parentNode):
        rigLayer = self.rigLayer()
        deformLayer = self.deformLayer()
        inputLayer = self.inputLayer()
        controlPanel = self.controlPanel()
        definition = self.definition
        guideLayerDef = definition.guideLayer
        naming = self.namingConfiguration()
        rigLayerRoot = rigLayer.rootTransform()
        compName, compSide = self.name(), self.side()
        highlighting = self.configuration.selectionChildHighlighting

        tweaker01AutoFollow = controlPanel.tweak01Follow
        bindJoints = list(deformLayer.iterJoints())
        bindJointsMap = {i.id(): i for i in bindJoints}
        splineIkJointCount = definition.guideLayer.guideSetting("ikJointCount").value
        fkCtrlCount = definition.guideLayer.guideSetting("fkCtrlCount").value
        parentInputNode = inputLayer.inputNode("parent")
        firstBindGuide = guideLayerDef.guide(self.jointIdForNumber(0))
        hierarchyParenting = OrderedDict(
            {
                "hipSwing": "cogGimbal",
                "tweaker00": "hips",
                "tweaker02": "ctrl02",
                "hips": "hipSwing",
                self.fkGuideIdForNumber(0): "cogGimbal",
                "ctrl02": self.fkGuideIdForNumber(fkCtrlCount - 1),
            }
        )
        # sorted in appropriate creation order so parenting based on guides while creating just
        # works
        _guideControlsIds = ["cog", "cogGimbal", "hipSwing", "hips", "tweaker00"]
        _guideControlsIds.extend(
            [
                i.id
                for i in guideLayerDef.iterGuides(includeRoot=False)
                if i.id.startswith(self._fkNumPrefix)
            ]
        )
        _guideControlsIds.extend(["ctrl02", "tweaker02", "tweaker01"])
        # we need to force segmentScaleCompensate on due to squash
        createdCtrls = {}
        for bindJnt in bindJoints[1:]:
            bindJnt.segmentScaleCompensate.set(1)

        guides = OrderedDict(
            (i.id, i) for i in guideLayerDef.findGuides(*_guideControlsIds)
        )
        # generate the controls minus fk handle them separately
        for index, guidDef in enumerate(guides.values()):
            ctrlName = naming.resolve(
                "controlName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": guidDef.id,
                    "type": "control",
                },
            )

            ctrl = rigLayer.createControl(
                parent=hierarchyParenting.get(guidDef.id, guidDef.parent),
                name=ctrlName,
                id=guidDef.id,
                translate=guidDef.translate,
                rotate=guidDef.rotate,
                shape=guidDef.shape,
                rotateOrder=guidDef.rotateOrder,
                selectionChildHighlighting=highlighting,
                srts=[{"id": guidDef.id, "name": "_".join([ctrlName, "srt"])}],
            )
            createdCtrls[guidDef.id] = ctrl

        # create the worldUpVec with an identity matrix relative to the bindJoint 0
        # parent it to the hip
        worldUpVec = guideLayerDef.guide("worldUpVec")
        ctrlName = naming.resolve(
            "controlName",
            {
                "componentName": compName,
                "side": compSide,
                "id": worldUpVec.id,
                "type": "control",
            },
        )

        worldUpVectorCtrl = rigLayer.createControl(
            parent="hips",
            name=ctrlName,
            id=worldUpVec.id,
            translate=bindJoints[0].translation(space=zapi.kWorldSpace),
            rotate=zapi.Quaternion(),
            shape=worldUpVec.shape,
            rotateOrder=worldUpVec.rotateOrder,
            selectionChildHighlighting=highlighting,
            srts=[{"name": "_".join((ctrlName, "srt")), "id": worldUpVec.id}],
        )
        createdCtrls[worldUpVec.id] = worldUpVectorCtrl

        ctrl02Control = createdCtrls["ctrl02"]
        startCurveTransform = zapi.createDag(
            naming.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": "startCurveManip",
                    "type": "srt",
                },
            ),
            "transform",
            parent=createdCtrls["hips"],
        )
        endCurveTransform = zapi.createDag(
            naming.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": "endCurveManip",
                    "type": "srt",
                },
            ),
            "transform",
            parent=createdCtrls["ctrl02"],
        )
        startCurveTransform.setTranslation(
            bindJointsMap[self.jointIdForNumber(0)].translation(),
            space=zapi.kWorldSpace,
        )
        endCurveTransform.setTranslation(
            bindJointsMap[self.jointIdForNumber(len(bindJoints) - 1)].translation(),
            space=zapi.kWorldSpace,
        )

        createdCtrls[self.fkGuideIdForNumber(0)].setParent(
            createdCtrls["cogGimbal"], useSrt=True
        )
        ctrl02Control.setParent(
            createdCtrls[self.fkGuideIdForNumber(fkCtrlCount - 1)], useSrt=True
        )
        _curveInfluenceIds = ("tweaker00", "tweaker01", "tweaker02")
        _curveInfluence = (
            [startCurveTransform]
            + rigLayer.findControls(*_curveInfluenceIds)
            + [endCurveTransform]
        )

        # build the ik joints and curve
        spline, extras = api.splineutils.createCurveFromDefinition(
            self.definition,
            rigLayer,
            influences=_curveInfluence,
            parent=rigLayerRoot,
            attributeName=self._splineCrvAttributeName,
            curveName="spineSpline_crv",
            namingObject=naming,
            namingRule="object",
            curveVisControlAttr=controlPanel.attribute("showCurveTemplate"),
        )

        jointAimVector = firstBindGuide.attribute("autoAlignAimVector").value
        jointUpVector = firstBindGuide.attribute("autoAlignUpVector").value

        ikSplineJoints, parentSpaceSrt, globalScaleComp, stretchOutput = (
            api.splineutils.createIkSplineJoints(
                self,
                rigLayer,
                controlPanel,
                parentInputNode,
                spline,
                splineIkJointCount,
                aimVector=jointAimVector,
                upVector=jointUpVector,
                parent=rigLayerRoot,
                stretchOffLimitAttrName=self._stretchOffLimitAttrName,
            )
        )
        splineIkName = naming.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "splineIk",
                "type": "ikHandle",
            },
        )

        ikHandle, ikEffector = api.splineutils.createIkSpline(
            splineIkName,
            rigLayerRoot,
            worldUpVectorCtrl,
            ctrl02Control,
            spline,
            jointAimVector,
            jointUpVector,
            ikSplineJoints,
        )
        extraNodes = api.splineutils.createSquash(
            naming,
            bindJoints,
            len(bindJoints),
            rigLayer.settingNode("constants"),
            controlPanel,
            stretchOutput,
            compName,
            compSide,
        )

        rigLayer.addExtraNodes(extraNodes)
        createdCtrls["cog"].setParent(parentSpaceSrt)

        self._setupVisibility(controlPanel, createdCtrls, fkCtrlCount)
        tweaker01Srt = createdCtrls["tweaker01"].srt()
        extras = _createBlendMatrix(
            createdCtrls["tweaker01"].srt(),
            createdCtrls[self.fkGuideIdForNumber(fkCtrlCount - 1)],
            [createdCtrls["hipSwing"], ctrl02Control],
            tweaker01AutoFollow,
            naming,
            compName,
            compSide,
        )
        tweaker01Srt.resetTransform()

        rigLayer.addExtraNodes(extras)
        # bind the first bind joint to the hip ctrl
        const, constUtilities = zapi.buildConstraint(
            bindJoints[0],
            drivers={
                "targets": (
                    (
                        createdCtrls["hips"].fullPathName(
                            partialName=True, includeNamespace=False
                        ),
                        createdCtrls["hips"],
                    ),
                )
            },
            constraintType="parent",
            maintainOffset=True,
            trace=False,
        )
        rigLayer.addExtraNodes(constUtilities)

        tweakerExtras = self._setupTweakers(
            controlPanel, guides, createdCtrls, bindJoints
        )

        rigLayer.addExtraNodes((ikHandle, ikEffector))
        rigLayer.addExtraNodes(tweakerExtras)

        self._bindIkToBind(rigLayer, bindJoints, bindJointsMap, ikSplineJoints)

        ikEnd = ikSplineJoints[-1]
        bindEnd = bindJoints[-1]

        pointConstraint, pointUtilities = api.buildConstraint(
            bindEnd,
            drivers={"targets": (("", ikEnd),)},
            constraintType="point",
            maintainOffset=True,
            trace=False,
        )
        orientConstraint, orientUtilities = api.buildConstraint(
            bindEnd,
            drivers={"targets": (("", ikEnd),)},
            constraintType="orient",
            maintainOffset=True,
            trace=False,
        )
        rigLayer.addExtraNodes(pointUtilities + orientUtilities)
        # drive the output 0 by the hip anim with an offset
        outLayer = self.outputLayer()
        # bind all outputs handling global scale
        globalOutScale = globalScaleComp.attribute("outputScale")
        for outputNode in outLayer.outputs():
            outputNode.resetTransform()
            rigLayer.addExtraNodes(
                _createOutputTransformNetwork(
                    naming,
                    compName,
                    compSide,
                    bindJointsMap[outputNode.id()],
                    globalOutScale,
                    outputNode,
                )
            )
        self._setupCtrlSpaceSwitch(rigLayer, createdCtrls, controlPanel)

    def _setupCtrlSpaceSwitch(self, rigLayer, controls, controlPanel):
        """Temp solution to the spaceswitching framework limitations.

        Todo: replace this with the new space switch framework once that's done.

        :param rigLayer:
        :type rigLayer: :class:`api.HiveRigLayer`
        :param controls:
        :type controls: list[:class:``]
        :param controlPanel:
        :type controlPanel: :class:``
        """
        worldInput = self.inputLayer().inputNode("world")
        fkCtrlCount = self.definition.guideLayer.guideSetting("fkCtrlCount").value
        orientWorldTransform = zapi.createDag(
            "_".join([controls["ctrl02"].name(), "orientWorld"]),
            "transform",
            parent=controls[self.fkGuideIdForNumber(fkCtrlCount - 1)],
        )
        const, utils = zapi.buildConstraint(
            orientWorldTransform,
            drivers={"targets": (("", worldInput),)},
            constraintType="orient",
            trace=False,
            maintainOffset=True,
        )
        rigLayer.addExtraNodes(utils)
        orientWorldTransform.setRotationOrder(controls["ctrl02"].rotationOrder())
        orientWorldTransform.setWorldMatrix(controls["ctrl02"].worldMatrix())
        spaceSrt = rigLayer.createSrtBuffer(
            "ctrl02", "_".join([controls["ctrl02"].name(), "space"])
        )

        spaceConstraint, utils = zapi.buildConstraint(
            spaceSrt,
            drivers={
                "targets": (
                    ("parentAll", None),
                    ("worldAll", worldInput),
                    ("worldOrient", orientWorldTransform),
                ),
                "attributeName": "ctrl02_space",
                "spaceNode": controlPanel,
            },
            constraintType="parent",
            trace=True,
            maintainOffset=True,
        )
        rigLayer.addSpaceSwitchNode(spaceSrt, "ctrl02_space")
        rigLayer.addExtraNode(orientWorldTransform)
        rigLayer.addExtraNodes(utils)

    def _setupVisibility(self, controlPanel, controls, fkCtrlCount):
        visSwitchPlug = controlPanel.cogGimbalVis
        tweaker02CtrlVisPlug = controlPanel.tweaker02Vis
        midTweakVisPlug = controlPanel.tweaker01Vis
        botTweakerCtrlVisPlug = controlPanel.tweaker00Vis
        ctrl02Vis = controlPanel.ctrl02Vis
        swingCtrlVis = controlPanel.hipSwingVis
        upVecCtrlVis = controlPanel.upVectorVis

        hipCtrlVisPlug = controlPanel.hipsVis
        for shape in controls["cogGimbal"].iterShapes():
            visSwitchPlug.connect(shape.visibility)
        visMap = [
            (controls["tweaker01"], midTweakVisPlug),
            (controls["hips"], hipCtrlVisPlug),
            (controls["tweaker00"], botTweakerCtrlVisPlug),
            (controls["tweaker02"], tweaker02CtrlVisPlug),
            (controls["ctrl02"], ctrl02Vis),
            (controls["hipSwing"], swingCtrlVis),
            (controls["worldUpVec"], upVecCtrlVis),
        ]
        for index in reversed(range(fkCtrlCount)):
            settingName = "".join(("ctrl", str(index).zfill(2), "Vis"))
            visMap.append(
                (
                    controls[self.fkGuideIdForNumber(index)],
                    controlPanel.attribute(settingName),
                )
            )

        for ctrl, plug in visMap:
            for shape in ctrl.iterShapes():
                plug.connect(shape.visibility)

    def _setupTweakers(self, controlPanel, guides, controls, joints):
        # figure out the distance between the chest and the tweaker and make that the default value
        tweaker02 = controls["tweaker02"]
        hipTweaker = controls["tweaker00"]
        tweaker02Distance = (
            joints[-1].translation(zapi.kWorldSpace) - guides["tweaker02"].translate
        ).length()
        tweaker02Srt = tweaker02.srt()
        tweaker02Srt.setTranslation(
            joints[-1].translation(zapi.kWorldSpace), zapi.kWorldSpace
        )
        controlPanel.chestTangent.setDefault(tweaker02Distance)
        controlPanel.chestTangent.set(tweaker02Distance)

        # figure out the aim vector so we translate on the correct axis
        chestAimVector = guides["tweaker02"].attribute("autoAlignAimVector").value
        tweaker02AimName = mayamath.primaryAxisNameFromVector(chestAimVector)

        hipTweakerDistance = (
            joints[0].translation(zapi.kWorldSpace) - guides["tweaker00"].translate
        ).length()
        hipTweakerSrt = hipTweaker.srt()
        hipTweakerSrt.setTranslation(
            joints[0].translation(zapi.kWorldSpace), zapi.kWorldSpace
        )
        controlPanel.hipTangent.setDefault(hipTweakerDistance)
        controlPanel.hipTangent.set(hipTweakerDistance)
        # figure out the aim vector so we translate on the correct axis
        hipSwingAimVector = guides["tweaker00"].attribute("autoAlignAimVector").value
        hipTweakerAimName = mayamath.primaryAxisNameFromVector(hipSwingAimVector)

        # bind the tangent attributes to the tweakerControls
        chestTangentComposeMtx = zapi.createDG("chestTangentCompose", "composeMatrix")
        hipSwingTangentComposeMtx = zapi.createDG(
            "hipSwingTangentCompose", "composeMatrix"
        )
        chestTangentComposeMtx.outputMatrix.connect(tweaker02.offsetParentMatrix)
        hipSwingTangentComposeMtx.outputMatrix.connect(hipTweaker.offsetParentMatrix)

        hipSwingTweakAnimPlug = controlPanel.hipTangent
        chestTweakAnimPlug = controlPanel.chestTangent
        # if aim vector has a negative then flip the sign so the translation goes up the spine
        if any(i > 0 for i in hipSwingAimVector):
            double = zapi.createDG("tweaker00Negate", "multDoubleLinear")
            double.input2.set(-1)
            hipSwingTweakAnimPlug.connect(double.input1)
            hipSwingTweakAnimPlug = double.output
        # now do the chest
        if any(i > 0 for i in chestAimVector):
            double = zapi.createDG("tweaker02Negate", "multDoubleLinear")
            double.input2.set(-1)
            chestTweakAnimPlug.connect(double.input1)
            chestTweakAnimPlug = double.output
        hipSwingTweakAnimPlug.connect(
            hipSwingTangentComposeMtx.attribute(
                "inputTranslate{}".format(hipTweakerAimName)
            )
        )
        chestTweakAnimPlug.connect(
            chestTangentComposeMtx.attribute(
                "inputTranslate{}".format(tweaker02AimName)
            )
        )
        return chestTangentComposeMtx, hipSwingTangentComposeMtx

    def _bindIkToBind(self, rigLayer, bindJoints, bindJointsMap, ikJoints):
        for bindIndex in range(1, len(bindJoints) - 1):
            bindJntId = self.jointIdForNumber(bindIndex)
            bindJnt = bindJointsMap[bindJntId]
            bindPosition = bindJnt.translation()
            positions = []
            for index, ikJnt in enumerate(ikJoints[:-1]):
                positions.append((bindPosition - ikJnt.translation()).length())
            splineJnt = ikJoints[positions.index(min(positions))]
            _buildJntConstraint(bindJnt, [splineJnt], rigLayer, scale=False)

    def postSetupRig(self, parentNode):
        rigLayer = self.rigLayer()
        attributeNames = zapi.localScaleAttrs + ["scale"]
        splineNode = rigLayer.sourceNodeByName(self._splineCrvAttributeName)
        for i in rigLayer.iterControls():
            i.showHideAttributes(attributeNames, state=False)
            i.setLockStateOnAttributes(attributeNames, state=True)

        cmds.displaySmoothness(
            splineNode.fullPathName(), polygonObject=1, pointsWire=16
        )

        super(SpineIkComponent, self).postSetupRig(parentNode)


def _createOutputTransformNetwork(
    namingObject, compName, compSide, sourceNode, globalScaleOutScaleAttr, outputNode
):
    sourceDecomp = zapi.createDG(
        namingObject.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "",
                "type": "decomposeMatrix",
            },
        ),
        "decomposeMatrix",
    )
    transform = zapi.createDG(
        namingObject.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "",
                "type": "composeMatrix",
            },
        ),
        "composeMatrix",
    )
    sourceNode.attribute("worldMatrix")[0].connect(sourceDecomp.inputMatrix)
    sourceDecomp.outputTranslate.connect(transform.inputTranslate)
    sourceDecomp.outputRotate.connect(transform.inputRotate)
    globalScaleOutScaleAttr.connect(transform.inputScale)
    transform.outputMatrix.connect(outputNode.offsetParentMatrix)

    return sourceDecomp, transform


def _buildJntConstraint(driven, targets, layer, scale=True, constraintType="parent"):
    targets = [
        (i.fullPathName(partialName=True, includeNamespace=False), i) for i in targets
    ]
    parentConstraint, parentUtilities = api.buildConstraint(
        driven,
        drivers={"targets": targets},
        constraintType=constraintType,
        maintainOffset=True,
        trace=False,
    )
    scaleConstraint, scaleUtilities = None, []
    if scale:
        scaleConstraint, scaleUtilities = api.buildConstraint(
            driven,
            drivers={"targets": targets},
            constraintType="scale",
            maintainOffset=True,
            trace=False,
        )

    layer.addExtraNodes(parentUtilities + scaleUtilities)
    return parentConstraint, scaleConstraint


def _createBlendMatrix(
    driven, inputNode, targets, weightAttribute, naming, componentName, side
):
    # todo: standardize this into our zapi constraint
    parentWorldInv = driven.parent().attribute("worldInverseMatrix")[0]
    blendMatrix = zapi.createDG("blendMatrix", "blendMatrix")
    inputNode.attribute("worldMatrix")[0].connect(blendMatrix.inputMatrix)
    secondaryWeightFloat = zapi.createDG("weightBlend", "floatMath")
    secondaryWeightFloat.floatA.set(0.5)
    secondaryWeightFloat.operation.set(2)
    weightAttribute.connect(secondaryWeightFloat.floatB)
    weightAttribute.connect(blendMatrix.target[0].child(2))
    extras = [blendMatrix, secondaryWeightFloat]
    for index, target in enumerate(targets):
        targetOffset = target.offsetMatrix(driven)
        name = naming.resolve(
            "object",
            {
                "componentName": componentName,
                "side": side,
                "section": "".join((target.id(), "midBlend")),
                "type": "multMatrix",
            },
        )
        targetOffsetMtxNode = zapi.createDG(name, "multMatrix")
        targetOffsetMtxNode.matrixIn[0].set(targetOffset)
        target.attribute("worldMatrix")[0].connect(targetOffsetMtxNode.matrixIn[1])
        parentWorldInv.connect(targetOffsetMtxNode.matrixIn[2])
        targetOffsetMtxNode.matrixSum.connect(blendMatrix.target[index].child(0))
        if index != 0:
            secondaryWeightFloat.outFloat.connect(
                blendMatrix.target[index].child(2)
            )  # weight
        extras.append(targetOffsetMtxNode)

    blendMatrix.outputMatrix.connect(driven.offsetParentMatrix)
    return extras


def _createSpace(
    definition, guide, drivers, insertAfter, spaceType="orient", prefix="rotSpace"
):
    """Helper Function which generates a space switch definition for a guide.

    :param definition: The component definition instance.
    :type definition: :class:`api.Definition`
    :param guide: The scene Guide
    :type guide: :class:`api.Guide`
    :param drivers:
    :type drivers: list[:class:`api.SpaceSwitchDriverDefinition`]
    :param insertAfter:
    :type insertAfter: str
    :param spaceType:
    :type spaceType: str
    :param prefix:
    :type prefix: str
    :return:
    :rtype: :class:`api.SpaceSwitchDefinition`
    """
    guideId = guide.id()
    hasSpace = guide.attribute("hasSpaceSwitch")

    spaceName = "_".join((guideId, prefix))
    if hasSpace is None:
        guide.addAttribute(
            name="hasSpaceSwitch",
            Type=zapi.attrtypes.kMFnNumericBoolean,
            default=True,
            value=True,
            channelBox=True,
            keyable=False,
        )
    else:
        hasSpace = hasSpace.value()
        if not hasSpace:
            return
    drivers = list(drivers)
    newSpace = definition.createSpaceSwitch(
        label=spaceName,
        drivenId=api.pathAsDefExpression(("self", "rigLayer", guideId)),
        constraintType=spaceType,
        controlPanelFilter={
            "default": "parent",
            "insertAfter": insertAfter,
            "group": {"name": "___", "label": "space"},
        },
        permissions={"allowRename": False, "value": True},
        drivers=drivers,
    )
    return newSpace
