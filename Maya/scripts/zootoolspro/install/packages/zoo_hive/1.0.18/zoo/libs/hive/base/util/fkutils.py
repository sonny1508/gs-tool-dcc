import math

from zoo.libs.maya import zapi
from zoo.libs.hive import constants


def _findParentNode(node, visitedNodes):
    """Walks up the parent chain until it finds a node that has already been visited.

    :param node: The node to start from.
    :type node: :class:`zapi.DagNode`
    :param visitedNodes:
    :type visitedNodes: dict[:class:`DagNode`, str]
    :return: The Hive id of the parent node.
    :rtype: str
    """
    if node.apiType() == zapi.kJoint:
        for n in node.iterParents():
            if n.apiType() == zapi.kJoint:
                nodeId = visitedNodes.get(n)
                if nodeId:
                    return nodeId
        else:
            return "root"
    return visitedNodes.get(node.parent(), "root")


def transformsToFkGuides(rig, component, transforms, guideScale=1.0):
    """Providing a list of transforms, create a FK chain component with the same number of guides
    and matches the transforms.

    :param rig: The rig Instance to add the component too.
    :type rig: :class:`zoo.libs.hive.base.rig.Rig`
    :param component:
    :type component: :class:`api.component`
    :param transforms:
    :type transforms: list[:class:`zapi.DagNode`]
    :return:
    :rtype: :class:`zoo.libs.hive.base.component.Component`
    """

    component.definition.guideLayer.guideSetting("jointCount").value = len(list(transforms))
    guideLayerDef = component.definition.guideLayer
    # first remove any existing guides except the root, since the default comp has 3
    rootGuide = guideLayerDef.guide("root")
    rootGuide.children = []
    rootGuide.translate = list(transforms[0].translation(space=zapi.kWorldSpace))
    rootGuide.rotate = list(transforms[0].rotation(space=zapi.kWorldSpace))
    rootGuide.scale = (rootGuide.scale[0]*guideScale, rootGuide.scale[1]*guideScale, rootGuide.scale[2]*guideScale)
    try:
        del rootGuide["matrix"]
    except KeyError:
        pass
    rootGuide.worldMatrix = rootGuide.transformationMatrix().asMatrix()
    guideIdPrefix = constants.FKTYPE
    guides = {}  # zapiJnt: id
    preTransform = zapi.TransformationMatrix()
    preTransform.setRotation(zapi.EulerRotation(0.0, 0.0, math.pi * 0.5))
    for index, jnt in enumerate(transforms):
        guideId = guideIdPrefix + str(index).zfill(2)
        guides[jnt] = guideId
        parentId = _findParentNode(jnt, guides)

        # preRotate by 90 on Z to make the shape face the correct direction(down the chain)
        transform = preTransform.asMatrix() * jnt.transformationMatrix().asMatrix()
        rot = zapi.TransformationMatrix(transform).rotation(asQuaternion=True)
        guideLayerDef.createGuide(name=jnt.name(),
                                  rotateOrder=jnt.rotationOrder(),
                                  shape="circle",
                                  color=(0.0, 0.5, 0.5),
                                  id=guideId,
                                  parent=parentId,
                                  translate=list(jnt.translation(space=zapi.kWorldSpace)),
                                  rotate=list(jnt.rotation(space=zapi.kWorldSpace)),
                                  scale=(guideScale, guideScale, guideScale),
                                  selectionChildHighlighting=rig.configuration.selectionChildHighlighting,
                                  shapeTransform={
                                      "rotate": list(rot),
                                      "translate": list(jnt.translation(space=zapi.kWorldSpace)),
                                      "scale": (guideScale, guideScale, guideScale),
                                      "rotateOrder": jnt.rotationOrder()},
                                  attributes=[{"name": "autoAlign",
                                               "value": False,
                                               "Type": zapi.attrtypes.kMFnNumericBoolean}]
                                  )
    guideLayerDef.guideSetting("manualOrient").value = True
