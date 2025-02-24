from zoo.libs.hive import api
from zoo.libs.hive.base import basesubsystem
from zoo.libs.maya import zapi


class IkFkBlendSubsystem(basesubsystem.BaseSubsystem):
    """The IkFkBlendSubsystem class handles the setup of the IK/FK blending system for a given component.


    :param component: The component instance for which the subsystem is being set up.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param outputJointIds: The ids of the output joints.
    :type outputJointIds: iterable[str]
    :param fkNodesIds: The ids of the FK controls.
    :type fkNodesIds: iterable[str]
    :param ikJointsIds: The names of the IK joints.
    :type ikJointsIds: iterable[str]
    :param nodeIds: The ids to be used to tag the blend node names.
    :type nodeIds: iterable[str]
    :param blendAttrName: The name of the attribute used to control the IK/FK blend.
    :type: blendAttrName: str
    :param parentNodeId: The id of the parent node.
    :type parentNodeId: str
    """

    def __init__(
        self,
        component,
        outputJointIds,
        fkNodesIds,
        ikJointsIds,
        nodeIds,
        blendAttrName,
        parentNodeId,
    ):
        super(IkFkBlendSubsystem, self).__init__(component)
        self.outputJointIds = outputJointIds
        self.fkNodes = fkNodesIds
        self.ikJoints = ikJointsIds
        self.nodeIds = nodeIds
        self.blendAttrName = blendAttrName
        self.parentNodeId = parentNodeId

    def setupRig(self, parentNode):
        if not self.active():
            return
        namer = self.component.namingConfiguration()
        comp = self.component
        rigLayer = comp.rigLayer()
        deformLayer = comp.deformLayer()
        blendAttr = rigLayer.controlPanel().attribute(self.blendAttrName)
        blendJoints = deformLayer.findJoints(*self.outputJointIds)
        ikJoints = rigLayer.findJoints(*self.ikJoints)
        fkNodes = rigLayer.findControls(*self.fkNodes)
        compName, compSide = self.component.name(), self.component.side()
        blendTransformParent = rigLayer.taggedNode(self.parentNodeId)
        for fkNode, ikNode, nodeId, joint in zip(
            fkNodes, ikJoints, self.nodeIds, blendJoints
        ):
            # create transform for the output of the ik/fk since our bind skeleton contains a joint Orient
            # and requires export compatibility
            blendTransform = zapi.createDag(
                namer.resolve(
                    "object",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "section": nodeId + "blend",
                        "type": "transform",
                    },
                ),
                "transform",
                parent=blendTransformParent,
            )
            blendTransform.setRotationOrder(fkNode.rotationOrder())
            rigLayer.addTaggedNode(blendTransform, nodeId)
            blendTransformParent = blendTransform
            self._blendTriNodes(
                rigLayer, blendTransform, joint, ikNode, fkNode, blendAttr, nodeId
            )

    def _blendTriNodes(self, rigLayer, blendOutput, driven, ik, fk, blendAttr, nodeId):
        """IKFK blending system for a single joint

        :param rigLayer:  The component rigLayer instance.
        :type rigLayer: :class:`api.HiveRigLayer`
        :param blendOutput: The output transform for the blended ik/fk.
        :type blendOutput: :class:`zapi.DagNode`
        :param driven: The joint to be driven by the ik/fk blend.
        :type driven: :class:`api.Joint`
        :param ik: The ik node.
        :type ik: :class:`zapi.DagNode`
        :param fk:  The Fk node.
        :type fk: :class:`zapi.DagNode`
        :param blendAttr: The attribute to drive the ik/fk blend.
        :type blendAttr: :class:`zapi.Plug`
        :param nodeId: The id that will be used to tag the blend node names.
        :type nodeId: str
        :return: The blend matrix node.
        :rtype: :class:`zapi.DGNode`
        """
        naming = self.component.namingConfiguration()
        # create the blendMatrix and connect to the offset parent Matrix
        # ensure transforms are reset in the process
        blendMat = zapi.createDG(
            naming.resolve(
                "object",
                {
                    "componentName": self.component.name(),
                    "side": self.component.side(),
                    "section": "{}IkFk".format(nodeId),
                    "type": "blendMatrix",
                },
            ),
            "blendMatrix",
        )
        localMtx = zapi.createDG(
            naming.resolve(
                "object",
                {
                    "componentName": self.component.name(),
                    "side": self.component.side(),
                    "section": "{}IkFkLocal".format(nodeId),
                    "type": "multMatrix",
                },
            ),
            "multMatrix",
        )
        blendMat.outputMatrix.connect(localMtx.matrixIn[0])
        blendOutput.parent().attribute("worldInverseMatrix")[0].connect(
            localMtx.matrixIn[1]
        )
        localMtx.matrixSum.connect(blendOutput.offsetParentMatrix)

        targetElement = blendMat.target[0]
        ik.attribute("worldMatrix")[0].connect(blendMat.inputMatrix)
        fk.attribute("worldMatrix")[0].connect(targetElement.child(0))
        blendAttr.connect(targetElement.child(2))  # weight attr
        # todo: replace with matrix based constraint, note have to handle jointOrient as offset
        _, constUtilities = api.buildConstraint(
            driven,
            drivers={"targets": (("", blendOutput),)},
            constraintType="point",
            maintainOffset=True,
        )
        rigLayer.addExtraNodes(constUtilities)
        _, constUtilities = api.buildConstraint(
            driven,
            drivers={"targets": (("", blendOutput),)},
            constraintType="orient",
            maintainOffset=True,
        )
        rigLayer.addExtraNodes(constUtilities)
        _, constUtilities = api.buildConstraint(
            driven,
            drivers={"targets": (("", blendOutput),)},
            constraintType="scale",
            maintainOffset=True,
        )
        rigLayer.addExtraNodes(constUtilities + [blendMat, localMtx])
        return blendMat
