from zoo.libs.hive import api
from zoo.libs.maya import zapi

_DEFORM_IGNORE_IDS = ("hips", "gimbal")


class SpineComponent(api.Component):
    creator = "David Sparrow"
    definitionName = "spineFk"
    uiData = {"icon": "componentSpine", "iconColor": (), "displayName": "Spine FK"}
    _jointNumPrefix = "bind"
    _guideNumPrefix = "fk"
    _translationAxis = zapi.Vector(0, 1, 0)
    _firstIndexRotationOrder = zapi.kRotateOrder_ZXY

    @classmethod
    def jointIdForNumber(cls, number):
        return cls._jointNumPrefix + str(number).zfill(2)

    @classmethod
    def fkGuideIdForNumber(cls, number):
        return "fk" + str(number).zfill(2)

    def idMapping(self):
        """Returns the guide id to joint id mapping, this is used during"""
        fkCount = self.definition.guideLayer.guideSetting("jointCount").value

        deformIds = {"cog": "cog", "hips": "", "gimbal": ""}
        outputIds = {}
        inputIds = {}
        rigLayerIds = {}
        for index in range(fkCount):
            guideId = self.fkGuideIdForNumber(index)
            jntId = self.jointIdForNumber(index)
            deformIds[guideId] = jntId
            outputIds[guideId] = jntId
            rigLayerIds[guideId] = guideId

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

        for guide in guideLayerDef.iterGuides(includeRoot=False):
            driven.append(
                api.SpaceSwitchUIDriven(
                    id_=api.pathAsDefExpression(("self", "rigLayer", guide.id)),
                    label=guide.name,
                )
            )
            drivers.append(
                api.SpaceSwitchUIDriver(
                    id_=api.pathAsDefExpression(("self", "rigLayer", guide.id)),
                    label=guide.name,
                )
            )

        return {"driven": driven, "drivers": drivers}

    def updateGuideSettings(self, settings):
        originalGuideSettings = super(SpineComponent, self).updateGuideSettings(
            settings
        )
        if "jointCount" in settings and self.hasGuide():
            # ensure the definition contains the latest scene state.
            self.serializeFromScene(layerIds=api.constants.GUIDE_LAYER_TYPE)
            self.deleteGuide()
            self.rig.buildGuides([self])
        return originalGuideSettings

    def preSetupGuide(self):
        definition = self.definition
        guideLayerDef = definition.guideLayer  # type: api.GuideLayerDefinition
        # includes the cog so if 5 then 4 fk 1 cog plus hips,gimbal
        count = guideLayerDef.guideSetting("jointCount").value
        guides = list(guideLayerDef.iterGuides(includeRoot=False))
        guideIds = {guid.id for guid in guides}
        currentGuideCount = max(
            0, len(guides) - 2
        )  # 2 is for gimbal, hips which don't have joints, cog does
        naming = self.namingConfiguration()
        compName, compSide = self.name(), self.side()
        # if the definition is the same as the required then just call the base
        # this will happen on a rebuild with a single guide count difference
        if currentGuideCount == count:
            return super(SpineComponent, self).preSetupGuide()
        # case where the new count is less than the current, in this case we just
        # delete the definition for the guide from the end.
        elif count < currentGuideCount:
            parentGuide = guides[count + 2].id
            guideLayerDef.deleteGuides(parentGuide)
            return super(SpineComponent, self).preSetupGuide()

        # gets hit if the user is requesting new set of guides
        root = guideLayerDef.guide("root")
        parent, parentDef = "root", root
        # the parent for the fk is the end guide ie -1
        if currentGuideCount:
            parentDef = guides[-1]
            parent = parentDef.id
        _createGuideDefs = {parent: parentDef}
        rootTransform = root.transformationMatrix()
        for index, guideId in enumerate(("cog", "gimbal", "hips")):
            if guideId in guideIds:
                continue
            rotationOrder = (
                self._firstIndexRotationOrder if index == 0 else zapi.kRotateOrder_XYZ
            )
            name = naming.resolve(
                "guideName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": guideId,
                    "type": "guide",
                },
            )
            matrix = zapi.TransformationMatrix()
            worldMtx = rootTransform
            newGuide = self._createFKGuide(
                guideLayerDef,
                name,
                guideId,
                parent,
                worldMtx.asMatrix(),
                matrix.asMatrix(),
                rotationOrder,
            )
            parent = guideId
            parentDef = newGuide
            _createGuideDefs[parent] = parentDef
            if guideId == "hips":
                parent = "gimbal"
                parentDef = _createGuideDefs["gimbal"]

        for x in range(max(0, currentGuideCount - 1), count - 1):
            rotationOrder = (
                self._firstIndexRotationOrder if x == 0 else zapi.kRotateOrder_XYZ
            )
            guidId = self.fkGuideIdForNumber(x)
            name = naming.resolve(
                "guideName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": guidId,
                    "type": "guide",
                },
            )
            matrix = zapi.TransformationMatrix()
            worldMtx = zapi.TransformationMatrix()

            try:
                # create an offset from the parent node to the current. with the guides we can just multiply the
                # local matrix by the worldMatrix
                parentWorld = zapi.Matrix(parentDef.worldMatrix)
                parentLocal = zapi.Matrix(parentDef.matrix)
                transform = zapi.TransformationMatrix(parentLocal * parentWorld)
                worldMtx.setTranslation(transform.translation(zapi.kWorldSpace), zapi.kWorldSpace)
                worldMtx.setRotation(zapi.TransformationMatrix(parentWorld).rotation(zapi.kWorldSpace))
                matrix.setTranslation(zapi.TransformationMatrix(parentLocal).translation(zapi.kObjectSpace),
                                      zapi.kObjectSpace)
            except (AttributeError, KeyError) as er:
                worldMtx.setTranslation(self._translationAxis * x,
                                        zapi.kWorldSpace)
                worldMtx.setRotation(zapi.EulerRotation(0.0, 0.0, 0.0))
                matrix.setTranslation(self._translationAxis, zapi.kObjectSpace)

            newGuide = self._createFKGuide(
                guideLayerDef,
                name,
                guidId,
                parent,
                worldMtx.asMatrix(),
                matrix.asMatrix(),
                rotationOrder,
            )
            parent = guidId
            parentDef = newGuide

        return super(SpineComponent, self).preSetupGuide()

    def _createFKGuide(
        self, guideLayer, name, guideId, parent, worldMatrix, localMatrix, rotationOrder
    ):
        shapeMatrix = zapi.TransformationMatrix(worldMatrix)
        newGuide = guideLayer.createGuide(name=name,
                                          shape="circle",
                                          id=guideId,
                                          parent=parent,
                                          color=(0.0, 0.5, 0.5),
                                          rotationOrder=rotationOrder,
                                          # cast to list because we don't auto do this in the definition just yet
                                          worldMatrix=list(worldMatrix),
                                          selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                                          shapeTransform={
                                              "translate": list(shapeMatrix.translation(zapi.kWorldSpace)),
                                              "rotate": list(shapeMatrix.rotation(asQuaternion=True)),
                                              "scale": list(shapeMatrix.scale(zapi.kWorldSpace))
                                          },
                                          srts=[{"name": "_".join((guideId, "piv", "srt"))}]
                                          )

        return newGuide

    def alignGuides(self):
        changed = super(SpineComponent, self).alignGuides()
        if not changed:
            return False
        layer = self.guideLayer()
        cog, gimbal, hips = layer.findGuides("cog", "gimbal", "hips")
        cogMatrix = cog.worldMatrix()
        guidesToModify = [gimbal, hips]
        matrices = [cogMatrix, cogMatrix]

        # batch update the guides.
        api.setGuidesWorldMatrix(guidesToModify, matrices)

        return True

    def postSetupGuide(self):
        super(SpineComponent, self).postSetupGuide()
        guideLayer = self.guideLayer()
        definition = self.definition
        currentSpaceSwitchLabels = set(i.label for i in definition.spaceSwitching)
        validSpaces = set()
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
        for index, guide in enumerate(guideLayer.iterGuides(includeRoot=False)):
            guideId = guide.id()
            if guideId in ("gimbal", "hips"):
                for shape in guide.iterShapes():
                    vis = shape.visibility  # type: zapi.Plug
                    if vis.isConnected:
                        continue
                    with zapi.lockStateAttrContext(shape, ("visibility",), False):
                        vis.set(False)
                        vis.lock(True)
            hasSpace = guide.attribute("hasSpaceSwitch")

            spaceName = "_".join((guideId, "space"))
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
                    continue
            drivers = list(drivers)
            if index != 0:
                drivers.append(cogAsDriver)
            newSpace = definition.createSpaceSwitch(
                label=spaceName,
                drivenId=api.pathAsDefExpression(("self", "rigLayer", guideId)),
                constraintType="orient",
                controlPanelFilter={
                    "default": "parent",
                    "group": {"name": "_", "label": "Space"},
                },
                permissions={"allowRename": False, "value": True},
                drivers=drivers,
            )
            if newSpace is not None:
                validSpaces.add(newSpace.label)

        for spaceLabel in currentSpaceSwitchLabels.difference(validSpaces):
            definition.removeSpaceSwitch(spaceLabel)

    def setupInputs(self):
        definition = self.definition
        guideLayerDef = definition.guideLayer
        if not guideLayerDef.hasGuides():
            super(SpineComponent, self).setupInputs()
            return
        super(SpineComponent, self).setupInputs()
        cogDef = guideLayerDef.guide("cog")
        layer = self.inputLayer()
        inputNode = layer.inputNode("parent")
        tMatrix = cogDef.transformationMatrix(scale=False)
        # We don't propagate scale from the guide
        inputNode.setWorldMatrix(tMatrix.asMatrix())

    def setupDeformLayer(self, parentJoint=None):
        # build skin joints if any
        definition = self.definition
        deformLayerDef = definition.deformLayer
        deformLayerDef.dag = []
        parentId = None
        index = 0
        for guide in definition.guideLayer.iterGuides(includeRoot=False):
            jntId = guide.id
            if jntId in _DEFORM_IGNORE_IDS:
                continue
            if jntId != "cog":
                jntId = self.jointIdForNumber(index)
                index += 1
            deformLayerDef.createJoint(
                name=guide.name,
                id=jntId,
                rotateOrder=guide.get("rotateOrder", 0),
                translate=guide.get("translate", (0, 0, 0)),
                rotate=guide.get("rotate", (0, 0, 0, 1)),
                parent=parentId,
            )
            parentId = jntId

        super(SpineComponent, self).setupDeformLayer(parentNode=parentJoint)

    def setupOutputs(self, parentNode):
        definition = self.definition
        outputLayerDef = definition.outputLayer
        # delete any outputs which no longer have matching guides
        joints = {i["id"]: i for i in definition.deformLayer.iterDeformJoints()}
        currentOutputs = {i["id"]: i for i in outputLayerDef.iterOutputs()}
        for outId, out in currentOutputs.items():  # type: str, api.OutputDefinition
            if outId in joints:
                continue
            currentOutputs[out.parent].deleteChild(outId)
        naming = self.namingConfiguration()
        compName, compSide = self.name(), self.side()
        # for each guide we create an output
        for index, jntDef in enumerate(definition.deformLayer.iterDeformJoints()):
            jntId = jntDef.id
            outputLayerDef.createOutput(
                name=naming.resolve(
                    "outputName",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "id": jntId,
                        "type": "output",
                    },
                ),
                id=jntId,
                parent=jntDef.parent,
                rotateOrder=jntDef.rotateOrder,
            )
        super(SpineComponent, self).setupOutputs(parentNode)
        self._connectOutputs()

    def _connectOutputs(self):
        # connect the outputs to the deform layer
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

    def preSetupRig(self, parentNode):
        spaceSwitches = {i.label: i for i in self.definition.spaceSwitching}
        for guide in self.definition.guideLayer.iterGuides(includeRoot=False):
            hasSpace = guide.attribute("hasSpaceSwitch")
            if not hasSpace:
                continue
            spaceSwitch = spaceSwitches.get("_".join((guide.id, "space")))
            if not spaceSwitch:
                continue
            spaceSwitch.active = hasSpace.value
        super(SpineComponent, self).preSetupRig(parentNode)

    def setupRig(self, parentNode):
        rigLayer = self.rigLayer()
        controlPanel = self.controlPanel()
        definition = self.definition
        naming = self.namingConfiguration()
        rigLayerRoot = rigLayer.rootTransform()
        compName, compSide = self.name(), self.side()
        highlighting = self.configuration.selectionChildHighlighting
        createdCtrls = {}
        for index, guidDef in enumerate(
            definition.guideLayer.iterGuides(includeRoot=False)
        ):
            guideParent = guidDef.parent
            if not guideParent or guideParent == "root":
                ctrlParent = rigLayerRoot
            else:
                ctrlParent = rigLayer.control(guideParent)
            # create the control
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
                parent=ctrlParent,
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

        visSwitchPlug = controlPanel.cogGimbalVis
        for shape in createdCtrls["gimbal"].iterShapes():
            visSwitchPlug.connect(shape.visibility)

    def postSetupRig(self, parentNode):
        deformLayer = self.deformLayer()
        inputLayer = self.inputLayer()
        rigLayer = self.rigLayer()
        extras = []
        joints = {i.id(): i for i in deformLayer.iterJoints()}
        rootInputNode = inputLayer.inputNode("parent")
        ctrls = {ctrl.id(): ctrl for ctrl in rigLayer.iterControls()}
        # this is basically temp until we add Ik

        # bind the hip ctrl to the cog joint then each fk ctrl to the bind## joint.
        hipCtrl = ctrls["hips"]
        cogJoint = joints["cog"]
        parent = _buildJntConstraint(driven=cogJoint, targets=(("hips", hipCtrl),))
        extras.extend(list(parent.utilityNodes()))
        idMapping = self.idMapping()[api.constants.DEFORM_LAYER_TYPE]
        # bind the ## joints
        for ctrlId, ctrl in ctrls.items():
            if not ctrlId.startswith(self._guideNumPrefix):
                continue
            jntId = idMapping[ctrlId]
            jnt = joints[jntId]
            parent = _buildJntConstraint(driven=jnt, targets=((ctrlId, ctrl),))
            extras.extend(list(parent.utilityNodes()))
        # bind the cog(root) ctrl to the parent input node
        const, constUtilities = zapi.buildConstraint(
            ctrls["cog"].srt(),
            drivers={"targets": (("cog", rootInputNode),)},
            constraintType="matrix",
            maintainOffset=True,
            trace=False,
        )
        extras.extend(constUtilities)

        rigLayer.addExtraNodes(extras)
        super(SpineComponent, self).postSetupRig(parentNode)


def _buildJntConstraint(driven, targets):
    parentConstraint, _ = api.buildConstraint(
        driven,
        drivers={"targets": targets},
        constraintType="matrix",
        maintainOffset=True,
        decompose=True,
        trace=False,
    )

    return parentConstraint
