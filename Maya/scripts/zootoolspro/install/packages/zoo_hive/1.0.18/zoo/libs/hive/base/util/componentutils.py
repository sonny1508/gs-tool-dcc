import contextlib
import math

from zoo.libs.hive import constants
from zoo.libs.hive.base.util import mirrorutils
from zoo.libs.hive.base import hivenodes
from zoo.libs.maya import zapi, triggers
from zoo.libs.maya.utils import mayamath


def mirror(component, guideLayer, translate=("x",), rotate="yz"):
    """Method to override how the mirroring of component guides are performed.

    By Default all guides,guideShapes and all srts are mirror with translation and rotation(if mirror attribute is
    True).
    :param component: The component instance to mirror.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param guideLayer: The guide Layer instance of the component.
    :type guideLayer: :class:`zoo.libs.hive.base.hivenodes.HiveGuideLayer`
    :param translate: The axis to mirror on ,default is ("x",).
    :type translate: tuple
    :param rotate: The mirror plane to mirror rotations on, supports "xy", "yz", "xz", defaults to "yz".
    :type rotate: str
    :return: A list of tuples with the first element of each tuple the hiveNode and the second element \
    the original world Matrix.
    :rtype: list(tuple(:class:`zapi.DagNode`, :class:`om2.MMatrix`))
    """
    mirrorGuides = {i.id(): i for i in guideLayer.iterGuides()}
    componentMirrorData = []
    componentRecoveryData = []
    for currentInfo, undoRecoveryData in mirrorutils.mirrorDataForComponent(
            component, mirrorGuides, translate=translate, rotate=rotate
    ):
        componentMirrorData.append(currentInfo)
        if undoRecoveryData:
            componentRecoveryData.append(undoRecoveryData)
    mirrorutils.setMirrorData(componentMirrorData)
    return componentRecoveryData


def createTriggers(node, layoutId):
    trigger = triggers.asTriggerNode(node)
    if trigger is not None:
        trigger.deleteTriggers()
    trigger = triggers.createTriggerForNode(node, "triggerMenu")
    trigger.command().setMenu(layoutId)


# note: probably should just pass the nodes into the function, would make it easier
def generateConnectionBindingIO(component):
    currentParent = component.parent()
    if not currentParent:
        return {}, None, {}
    idMapping = {
        v: k for k, v in component.idMapping()[constants.INPUT_LAYER_TYPE].items()
    }
    name, side = component.name(), component.side()
    childInputLayer = component.inputLayer()
    binding = {
        ":".join([name, side, idMapping.get(i.id(), i.id())]): i
        for i in component.inputLayer().inputs()
    }
    parentLayers = {}
    # deal with the parents
    parentIdMapping = {
        v: k for k, v in currentParent.idMapping()[constants.OUTPUT_LAYER_TYPE].items()
    }
    if currentParent:
        name, side = currentParent.name(), currentParent.side()
        outputLayer = currentParent.outputLayer()
        parentLayers[":".join([name, side])] = outputLayer
        for g in outputLayer.outputs():
            binding[":".join([name, side, parentIdMapping.get(g.id(), g.id())])] = g
    return binding, childInputLayer, parentLayers


def generateConnectionBindingGuide(component):
    binding = {}
    name, side = component.name(), component.side()
    childLayer = component.guideLayer()
    # grab the guides on the current component
    # we prioritize guide srts over the guide itself
    # for constraining purposes
    binding[":".join([name, side, "root"])] = childLayer.guide("root")

    # deal with the parents
    currentParent = component.parent()
    if currentParent:
        name, side = currentParent.name(), currentParent.side()
        layer = currentParent.guideLayer()
        for g in layer.iterGuides():
            binding[":".join([name, side, g.id()])] = g
    return binding, childLayer


@contextlib.contextmanager
def disconnectComponentsContext(components):
    """Context manager which disconnects the list of components temporarily.
    The function will yield once all components are disconnected.

    :param components: list of components to temporarily disconnect.
    :type components: list[:class:`zoo.libs.hive.base.component.Component`]
    """
    visited = set()
    for comp in components:
        if comp not in visited:
            comp.pin()
            visited.add(comp)

        for child in comp.children(depthLimit=1):
            if child in visited:
                continue
            visited.add(child)
            child.pin()
    yield
    for i in visited:
        i.unPin()


def createGuideLocator(
        guideLayer, namingConfig, namingRule, namingFieldValues, **kwargs
):
    """

    :param guideLayer:
    :type guideLayer: :class:`zoo.libs.hive.base.definition.GuideLayerDefinition`
    :param namingConfig:
    :type namingConfig: :class:`zoo.libs.naming.naming.NameManager`
    :param namingRule:
    :type namingRule: str
    :param namingFieldValues:
    :type namingFieldValues: dict[str, str]
    :param kwargs:
    :type kwargs:
    :return:
    :rtype: :class:`zoo.libs.hive.base.definition.GuideDefinition`
    """
    kwargs["pivotShape"] = "locator"
    kwargs["pivotColor"] = [0.477, 1, 0.073]
    namingFields = {"type": "guide"}
    namingFields.update(namingFieldValues)
    return guideLayer.createGuide(
        name=namingConfig.resolve(namingRule, namingFields), **kwargs
    )


def createGraphForComponent(
        component,
        layer,
        namedGraphData,
        sectionNameSuffix=None,
        track=True,
        createIONodes=False,
):
    """
    :param component:
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param layer: The Hive Layer to attach the graph to.
    :type layer: :class:`zoo.libs.hive.base.hivenodes.layers.HiveLayer`
    :param namedGraphData:
    :type namedGraphData:
    :param sectionNameSuffix:
    :type sectionNameSuffix: str
    :param track: Whether to track the graph in the layer.
    :type track: bool
    :param createIONodes:
    :type createIONodes: bool
    :return:
    :rtype: :class:`zoo.libs.hive.base.serialization.NamedDGGraph`
    """
    sectionNameSuffix = sectionNameSuffix or ""
    graph = layer.createNamedGraph(
        namedGraphData, track=track, createIONodes=createIONodes
    )
    config = component.namingConfiguration()
    modifier = zapi.dgModifier()
    for graphId, node in graph.nodes().items():
        newName = config.resolve(
            "object",
            {
                "componentName": component.name(),
                "side": component.side(),
                "section": graphId + sectionNameSuffix,
                "type": node.typeName,
            },
        )
        node.rename(newName, mod=modifier, apply=False)
    modifier.doIt()
    # extra nodes will call doIt as we pass the modifier
    layer.addExtraNodes(graph.nodes().values())
    return graph


def alignWorldUpVector(parentGuide, upVec, upVecRef, apply=True, offsetRotation=180.0):
    """
    :param parentGuide: The parent guide instance for the upVec to reference its transform.
    :type parentGuide: :class:`hivenodes.Guide`
    :param upVec: The World up Vector guide instance.
    :type upVec: :class:`hivenodes.Guide`
    :param upVecRef: The World up Vector guide instance.
    :type upVecRef: :class:`hivenodes.Guide`
    :param apply: Whether to apply the new transform to the upVec and upVecRef.
    :type apply: bool
    :return: The guide instances and the new matrices.
    :rtype: tuple[list[:class:`hivenodes.Guide`], list[:class:`zapi.Matrix`]]
    """
    rootPrimaryGuideTransform = parentGuide.transformationMatrix()
    rootPrimaryGuideTransform.setScale(upVec.scale(zapi.kWorldSpace), zapi.kWorldSpace)
    matrices, guides = [], []
    if upVec.attribute(constants.AUTOALIGN_ATTR).value():
        upVector = parentGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value()
        # different up axis requires different rotation offsets this is due to the default arrow shape
        # pointing down Z
        offsetTransform = zapi.TransformationMatrix()
        rot = zapi.EulerRotation()
        negative = mayamath.isVectorNegative(upVector)
        invert = 0 if negative else -1
        angle = math.radians(offsetRotation * invert)
        axisMap = {
            mayamath.XAXIS: (0, angle),
            mayamath.YAXIS: (0, angle),
            mayamath.ZAXIS: (0, math.radians(offsetRotation * (1 if negative else -1))),
        }
        remappedAxis, value = axisMap[mayamath.primaryAxisIndexFromVector(upVector)]
        rot[remappedAxis] = value
        offsetTransform.setRotation(rot)
        upTransform = offsetTransform.asMatrix() * rootPrimaryGuideTransform.asMatrix()
        matrices.append(upTransform)
        guides.append(upVec)
    else:
        upTransform = upVec.worldMatrix()

    refOffset = zapi.Matrix((1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, -1, 0, 1))
    matrices.append(refOffset * upTransform)
    guides.append(upVecRef)
    if apply:
        hivenodes.setGuidesWorldMatrix(guides, matrices)
    return guides, matrices


def worldUpVectorNormal(worldUpVec):
    """Compute the normal of a given worldUpVec guide definition.

    :param worldUpVec: The worldUpVec Guide definition
    :type worldUpVec: :class:`zoo.libs.hive.base.definition.GuideDefinition`
    :return: The normal vector of the worldUpVec.
    :rtype: :class:`zapi.Vector`
    """
    mtx = worldUpVec.worldMatrix
    vector = mayamath.basisYVectorFromMatrix(mtx) * -1
    return vector.normal()


def worldUpVectorAsPlane(worldUpVec):
    """Construct the Plane of a given worldUpVec guide definition.

    :param worldUpVec: Vector representing the world up direction.
    :type worldUpVec: :class:`zoo.libs.hive.base.definition.GuideDefinition`
    :return: The constructed plane.
    :rtype: :class:`zapi.Plane`
    """
    norm = worldUpVectorNormal(worldUpVec)
    constructedPlane = zapi.Plane()
    constructedPlane.setPlane(norm, -norm * worldUpVec.translate)
    return constructedPlane


def worldUpVectorNormalLegacy(worldUpVec):
    """Compute the normal of a given worldUpVec guide definition.

    :note..
        This is legacy function call :func:`worldUpVectorNormal` once
        we force guide serialization during autoAlign.

    :param worldUpVec: The input object representing the world up vector.
    :type worldUpVec: :class:`zoo.libs.maya.zapi.DagNode`
    :return: The normalized vector representing the world up vector.
    :rtype: :class:`zapi.Vector`
    """
    mtx = worldUpVec.worldMatrix()
    vectors = mayamath.basisVectorsFromMatrix(mtx)
    upVectorAlign = worldUpVec.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value()
    index = mayamath.primaryAxisIndexFromVector(upVectorAlign)
    return (vectors[index]).normal()


def worldUpVectorAsPlaneLegacy(worldUpVec, endGuide=None):
    """
    .. note:
        This is legacy function call :func:`worldUpVectorAsPlane` once
        we force guide serialization during autoAlign.

    :param worldUpVec: The input object representing the world up vector.
    :type worldUpVec: :class:`zoo.libs.maya.zapi.DagNode`
    :return: The constructed plane
    :rtype: zapi.Plane
    """
    worldUpVecPos = worldUpVec.translation(zapi.kWorldSpace)
    norm = worldUpVectorNormalLegacy(worldUpVec)
    constructedPlane = zapi.Plane()

    if endGuide is not None:
        aimVectorAlign = worldUpVec.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value()
        upVectorAlign = worldUpVec.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value()
        rotation = mayamath.lookAt(worldUpVecPos, endGuide.translation(zapi.kWorldSpace),
                                   aimVectorAlign, upVectorAlign,
                                   worldUpVector=norm)
        transform = zapi.TransformationMatrix()
        transform.setRotation(rotation)
        transform.setTranslation(worldUpVecPos, zapi.kWorldSpace)
        basisVectors = mayamath.basisVectorsFromMatrix(transform.asMatrix())
        norm = basisVectors[mayamath.primaryAxisIndexFromVector(upVectorAlign)]
    constructedPlane.setPlane(norm, -norm * worldUpVecPos)
    return constructedPlane


def createParentSpaceTransform(
        namingObject,
        compName,
        compSide,
        rootTransform,
        parentNode,
        rigLayer,
        rootInput,
        tagId="parentSpace",
        maintainOffset=True
):
    parentSpaceRig = zapi.createDag(
        namingObject.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": tagId,
                "type": "transform",
            },
        ),
        "transform",
        parent=rootTransform,
    )
    parentSpaceRig.setWorldMatrix(parentNode.worldMatrix())
    rigLayer.addTaggedNode(parentSpaceRig, tagId)
    rigLayer.addExtraNode(parentSpaceRig)
    const, constUtilities = zapi.buildConstraint(
        parentSpaceRig,
        drivers={
            "targets": (
                (
                    rootInput.fullPathName(partialName=True, includeNamespace=False),
                    rootInput,
                ),
            )
        },
        constraintType="matrix",
        maintainOffset=maintainOffset,
        trace=False,
    )
    rigLayer.addExtraNodes(constUtilities)
    return parentSpaceRig


def setupIkFkVisibility(
        namingObject,
        rigLayer,
        compName,
        compSide,
        fkCtrls,
        ikCtrls,
        annotation,
        ikRootCtrl,
        blendAttr,
):
    revNode = zapi.createReverse(
        namingObject.resolve(
            "object",
            {
                "componentName": compName,
                "side": compSide,
                "section": "ikfkVisSwitch",
                "type": "reverse",
            },
        ),
        inputs=[blendAttr],
        outputs=[],
    )

    revOutputX = revNode.outputX
    reverseVisSwitch = rigLayer.addAttribute(
        "reverseVisSwitch", Type=zapi.attrtypes.kMFnMessageAttribute
    )
    if annotation is not None:
        revOutputX.connect(annotation.visibility)
    revOutputX.connect(ikRootCtrl.visibility)
    revNode.message.connect(reverseVisSwitch)

    for i in ikCtrls:
        if not i:
            continue
        [revOutputX.connect(obj.visibility) for obj in i.shapes()]
    for i in fkCtrls:
        if not i:
            continue
        [blendAttr.connect(obj.visibility) for obj in i.shapes()]
    rigLayer.addExtraNodes([revNode])
    return revNode
