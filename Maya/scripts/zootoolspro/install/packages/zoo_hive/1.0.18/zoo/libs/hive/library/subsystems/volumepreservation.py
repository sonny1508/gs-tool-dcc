from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.hive.base import basesubsystem, definition
from zoo.libs.utils import zoomath


class VolumePreservationSubsystem(basesubsystem.BaseSubsystem):
    """
    """

    def __init__(self, component, ctrlIds, jointIds,
                 activeStateAttrName,
                 initializeLengthConstantAttr=(),
                 reverseVolumeValues=False,
                 showVolumeAttrsInChannelBox=False):
        super(VolumePreservationSubsystem, self).__init__(component)
        self.ctrlIds = ctrlIds
        self.jointIds = jointIds
        self.volumeAttrName = "globalVolume"
        self.volumeMultiplierAttrPrefix = "volume"
        self.curveNode = None
        self.reverseVolumeValues = reverseVolumeValues
        self.attrsInsertAfterName = "lowerStretch"
        self.animCurveSquashSettingAttr = "squashCurveNode"
        self.showVolumeAttrsInChannelBoxName = "displayVolumeAttrsChannelBox"
        self.showVolumeAttrsInChannelBox = showVolumeAttrsInChannelBox
        # used to determine if this subsystem should be active
        self.activeStateAttrName = activeStateAttrName
        # tuple first element the constant node id, second element the attrName
        self.initialLengthConstantAttr = initializeLengthConstantAttr

    def active(self):
        """Whether this subsystem should build,align etc. This is based on the required "activeStateAttrName" variable.

        :rtype: bool
        """
        return self.component.definition.guideLayer.guideSetting(
            self.activeStateAttrName
        ).value

    def squashCurve(self):
        return self.component.meta.sourceNodeByName(self.animCurveSquashSettingAttr)

    def postSetupGuide(self):
        if not self.active():
            return
        animCurveSquashSettingAttr = self.component.meta.addAttribute(self.animCurveSquashSettingAttr,
                                                                      Type=zapi.attrtypes.kMFnMessageAttribute)
        squashCurve = animCurveSquashSettingAttr.sourceNode()  # type: zapi.AnimCurve
        keyCount = len(self.jointIds) - 1

        if squashCurve is None:
            namingConfig = self.component.namingConfiguration()
            # create the animation squash curve node which the user can interact with
            squashCurve = api.splineutils.createSquashGuideCurve(
                namingConfig.resolve("object", {"componentName": self.component.name(),
                                                "side": self.component.side(),
                                                "section": "squashCurve",
                                                "type": "animCurve"},
                                     ), [0, keyCount * 0.5, keyCount], [0, 0.8, 1])
            self.component.meta.connectToByPlug(animCurveSquashSettingAttr, squashCurve)
            container = self.component.container()
            if container is not None:
                container.addNode(squashCurve)
                container.publishNode(squashCurve)

    def preSetupRig(self, parentNode):
        if not self.active():
            return
        settings = [
            {
                "name": "________",
                "value": 0,
                "enums": ["VOLUME"],
                "keyable": False,
                "locked": True,
                "channelBox": True,
                "Type": zapi.attrtypes.kMFnkEnumAttribute,
            },
            {
                "name": self.volumeAttrName,
                "Type": zapi.attrtypes.kMFnNumericFloat,
                "channelBox": False,
                "default": 0,
                "keyable": True,
                "max": 1.0,
                "min": 0.0,
                "value": 0
            }]

        settings.extend(self._createSquashCurveSettings())
        rigLayerDef = self.component.definition.rigLayer
        rigLayerDef.insertSettings(api.constants.CONTROL_PANEL_TYPE,
                                   rigLayerDef.settingIndex("controlPanel",
                                                            self.attrsInsertAfterName) + 1,
                                   settings)

    def _createSquashCurveSettings(self):
        squashCurve = self.squashCurve()
        constantSettings = []
        values = [squashCurve.mfn().evaluate(zapi.Time(i, zapi.Time.k24FPS)) for i in range(len(self.ctrlIds))]
        if self.reverseVolumeValues:
            values.reverse()
        for i, ctrlId in enumerate(self.ctrlIds):
            name = "_".join((self.volumeMultiplierAttrPrefix, ctrlId))
            kwargs = {"name": name,
                      "Type": zapi.attrtypes.kMFnNumericFloat,
                      "value": values[i]}
            if self.showVolumeAttrsInChannelBox:
                kwargs["channelBox"] = True
                kwargs["keyable"] = True

            constantSettings.append(kwargs)
        return constantSettings

    def setupRig(self, parentNode):
        if not self.active():
            return

        graphReg = self.component.configuration.graphRegistry()
        dataGraphRep = graphReg.graph("bendySquash")
        graphNameCache = dataGraphRep.name
        rigLayer = self.component.rigLayer()
        deformLayer = self.component.deformLayer()
        curve = self.curveNode.shapes()[0]
        ctrls = rigLayer.findControls(*self.ctrlIds)
        joints = deformLayer.findJoints(*self.jointIds)
        count = len(joints)
        curveOut = curve.attribute("worldSpace")[0]
        curveInfo = zapi.createDG(curve.name() + "_length", "curveInfo")
        curveOut.connect(curveInfo.inputCurve)
        curveInfoOutput = curveInfo.attribute("arcLength")

        extras = [curveInfo]
        constantsNode = rigLayer.settingNode(self.initialLengthConstantAttr[0])
        controlPanel = rigLayer.controlPanel()
        initialLengthAttribute = constantsNode.attribute(self.initialLengthConstantAttr[1])
        # invert the length otherwise doing a power of in the squash graph will be nan
        if initialLengthAttribute.value() < 0:
            double = zapi.createDG(initialLengthAttribute.name() + "abs", "multDoubleLinear")
            double.input2.set(-1)
            initialLengthAttribute.connect(double.input1)
            initialLengthAttribute = double.output
            extras.append(double)

        rigLayer.addExtraNodes(extras)
        animVolumeAttr = controlPanel.attribute(self.volumeAttrName)
        squashPlugs = []
        for ctrlId in self.ctrlIds:
            squashPlug = controlPanel.attribute("_".join((self.volumeMultiplierAttrPrefix, ctrlId)))
            squashPlugs.append(squashPlug)
        index = 0
        count = len(self.ctrlIds)
        positionValues = [value for value in zoomath.lerpCount(0, 1, count)] if count > 1 else [1.0]
        for ctrlId, twistJoint, ctrl in zip(self.ctrlIds, joints, ctrls):
            # squashPlug = squashPlugs[index]
            dataGraphRep.name = graphNameCache + ctrlId
            graph = self.createGraph(rigLayer, dataGraphRep, suffix=ctrlId)
            graph.connectToInput("globalScale", ctrl.worldMatrixPlug())
            graph.connectToInput("localScale", ctrl.attribute("scale"))
            lengthInput = graph.inputAttr("curveLength")[0]
            curveInfoOutput.connect(lengthInput[0])
            curveInfoOutput.connect(lengthInput[1])
            curveInfoOutput.connect(lengthInput[2])
            graph.setInputAttr("squashValue", index)
            graph.setInputAttr("squashMinMax", count)
            graph.setInputAttr("squashValueMultiplier", 0.2)
            graph.connectToInput("volume", animVolumeAttr)
            graph.connectToInput("initialLength", initialLengthAttribute)
            graph.connectFromOutput("outScale", [twistJoint.attribute("scale")])
            self._dumpCurveData(positionValues, squashPlugs, graph.node("bendyScaleCache"))
            index += 1

    def _dumpCurveData(self, positions, volumeAttrs, remap):
        for index, [pos, vol] in enumerate(zip(positions, volumeAttrs)):
            valueElement = remap.value[index]
            valueElement.child(0).set(pos)
            vol.connect(valueElement.child(1))
            valueElement.child(2).set(3)
