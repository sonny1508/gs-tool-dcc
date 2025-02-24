from zoo.libs.maya import zapi
from zoo.libs.hive.base.util import componentutils
from zoo.libs.hive import constants



def createAutoPoleGuideGraph(component, guideLayer, graphName, primaryIds, upVecId):
    """
    :param component: The component to create the auto pole guide graph for.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param guideLayer: The guide layer containing the guides.
    :type guideLayer: :class:`zoo.libs.hive.base.guides.GuideLayer`
    :param graphName: The name to give to the created graph.
    :type graphName: str
    :param primaryIds: The list of primary guide IDs.
    :type primaryIds: list[str]
    :param upVecId: The ID of the up vector guide.
    :type upVecId: str
    """
    guideLayer.deleteNamedGraph(graphName, component.configuration.graphRegistry())

    # note this is temp check for backwards compatibility
    # todo: add override method to support component upgrading versions
    # align the vchain guides with coplanar, align all others as normal
    uprGuide, midGuide, endGuide, upVecGuide, rootGuide = guideLayer.findGuides(
        *primaryIds + [upVecId, "root"]
    )
    if not upVecGuide.attribute("autoPoleVectorDistance"):
        upVecGuide.addAttribute(
            "autoPoleVectorDistance",
            Type=zapi.attrtypes.kMFnNumericFloat,
            default=20.0,
            value=20.0,
            min=0,
            channelBox=True,
        )
        upVecGuide.addAttribute(
            "autoPoleVectorDefaultPosition",
            Type=zapi.attrtypes.kMFnNumeric3Float,
            default=(0, 0, 0),
            value=(0, 0, 0),
            channelBox=True,
        )
        upVecGuide.addAttribute(
            "autoPoleVectorZeroDirection",
            Type=zapi.attrtypes.kMFnNumeric3Float,
            default=(0, 0, -1),
            value=(0, 0, -1),
            channelBox=True,
        )

    with zapi.lockStateAttrContext(
        upVecGuide,
        zapi.localTransformAttrs
        + [zapi.localRotateAttr, zapi.localTranslateAttr, zapi.localScaleAttr],
        False,
    ):
        upVecGuide.resetTransform(True, True, scale=False)

        graphRegistry = component.configuration.graphRegistry()
        graphData = graphRegistry.graph("autoPoleVector")
        graphData.name = graphName
        sceneGraph = componentutils.createGraphForComponent(
            component, guideLayer, graphData, track=True, createIONodes=False
        )
        sceneGraph.connectToInput("autoAlign", upVecGuide.autoAlign)
        sceneGraph.connectToInput("startWorldMatrix", uprGuide.worldMatrixPlug())
        sceneGraph.connectToInput("midWorldMatrix", midGuide.worldMatrixPlug())
        sceneGraph.connectToInput("endWorldMatrix", endGuide.worldMatrixPlug())
        sceneGraph.connectToInput(
            "parentInverseMatrix", rootGuide.worldInverseMatrixPlug()
        )
        sceneGraph.connectToInput("distance", upVecGuide.autoPoleVectorDistance)
        sceneGraph.connectToInput(
            "autoPoleVectorDefaultPosition",
            upVecGuide.autoPoleVectorDefaultPosition,
        )
        sceneGraph.connectToInput(
            "zeroAngleVector", upVecGuide.autoPoleVectorZeroDirection
        )
        sceneGraph.node("aimMatrix").secondaryMode.set(2)
        sceneGraph.setInputAttr("aimSecondaryInputAxis", zapi.Vector(0, 1, 0))
        sceneGraph.connectFromOutput("worldMatrix", [upVecGuide.offsetParentMatrix])
        sceneGraph.node("normalize").attribute("input2").set(zapi.Vector(0, 0, 0))
    # add the nodes to the container manually because this function is likely
    # run in alignGuides which doesn't automatically handle containers
    container = component.container()
    if container is not None:
        try:
            container.lock(False)
            container.addNodes(sceneGraph.nodes().values())
        except Exception:
            container.lock(True)


def createGuideAimConstraint(
    subsystem, hiveLayer, worldUpGuide, driven, driver, useWorldUpVecGuide=False
):
    """ Specialized function for two bone ik subsystem where the guide alignment needs to be live.

    :param subsystem: The component to create the aim constraint on.
    :type subsystem: :class:`zoo.libs.hive.base.basesubsystem.BaseSubsystem`
    :param hiveLayer: The Hive layer associated with the component.
    :type hiveLayer: :class:`zoo.libs.hive.base.hivenodes.HiveGuideLayer`
    :param worldUpGuide: The guide object that defines the world up vector.
    :type worldUpGuide: :class:`zoo.libs.hive.base.hivenodes.Guide`
    :param driven: The object that will be driven by the constraint.
    :type driven: :class:`zapi.DagNode`
    :param driver: The object that will drive the constraint.
    :type driver: :class:`zapi.DagNode`
    :param useWorldUpVecGuide: Flag indicating whether to use the worldUpGuide as the world up vector or \
    use object rotation. Defaults to False.
    :type useWorldUpVecGuide: bool
    :return: The created aim constraint and the vectorProduct node used for calculations.
    :rtype: [:class:`zapi.Constraint`, :class:`zapi.DagNode`]
    """
    aimVector = driven.attribute(constants.AUTOALIGNAIMVECTOR_ATTR)
    upVector = driven.attribute(constants.AUTOALIGNUPVECTOR_ATTR)

    worldUpVecAttr = worldUpGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR)

    kwargs = {
        "driven": driven,
        "constraintType": "aim",
        "drivers": {"targets": ((driver.fullPathName(False), driver),)},
        "maintainOffset": True,
        "trace": True,
        "worldUpObject": worldUpGuide.fullPathName(),
        "aimVector": list(aimVector.value()),
    }
    perpendicularVector = zapi.Vector(aimVector.value()) ^ zapi.Vector(upVector.value())
    kwargs["upVector"] = list(perpendicularVector)
    if useWorldUpVecGuide:
        kwargs["worldUpType"] = "object"

    else:
        kwargs["worldUpType"] = "objectrotation"
        kwargs["worldUpVector"] = list(worldUpVecAttr.value())
    const, utilities = zapi.buildConstraint(**kwargs)
    constraintNode = utilities[0]
    aimVector.connect(constraintNode.aimVector)
    vectorNode = zapi.createDG("perpendicularVectorNegative", "vectorProduct")
    vectorNode.operation.set(2)
    aimVector.connect(vectorNode.input1)
    upVector.connect(vectorNode.input2)
    vectorNode.output.connect(constraintNode.upVector)

    const.addUtilityNodes([vectorNode])
    container = subsystem.component.container()
    if container is not None:
        container.lock(False)
        container.addNodes([vectorNode, constraintNode])
        container.lock(True)
    hiveLayer.addExtraNode(vectorNode)
    hiveLayer.addExtraNodes(utilities)
    return const, vectorNode
