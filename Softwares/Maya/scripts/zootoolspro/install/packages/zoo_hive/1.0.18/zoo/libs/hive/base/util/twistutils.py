# encoding=utf8
"""
Twist Utils
-----------

Utility functions for building,updating and aligning twists segments.

    - For building guides use  :func:`generateTwistSegmentGuides` for each segment needed.
    - For building the joints use :func:`generateTwistJointsFromGuides` for each segment.
    - For building the animation Rig use :func:`rigTwistJoints` for each segment.
    - To update the distribution settings in the scene use :func:`updateSceneGuideAttributes`

"""
from zoo.libs.hive.base import definition
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath
from zoo.libs.utils import general
from zoo.libs.hive import constants
from zoo.libs.hive.base.util import componentutils

if general.TYPE_CHECKING:
    from zoo.libs.hive import api

DISTRIBUTION_TYPE_LINEAR = 0
DISTRIBUTION_TYPE_OFFSET = 1

GRAPH_DEBUG = False


def updateSceneGuideAttributes(twistPrefix, guideSettingsNode, guideLayerDefinition, startPos,
                               endPos, count, reverseFractions=False):
    """Updates the twist guide settings nodes attributes with new distributed values which is
    used for aligning guides.

    :param twistPrefix: the twist prefix name for all twist guides.
    :type twistPrefix: str
    :param guideSettingsNode: The guide settings node attached to the components guideLayer.
    :type guideSettingsNode: :class:`api.SettingsNode`
    :param guideLayerDefinition: The component guideLayer definition instance \
    This Function will modify the layer in place.

    :type guideLayerDefinition: :class:`api.GuideLayerDefinition`
    :param startPos: the start position vector in world space to start the twist generation.
    :type startPos: :class:`zapi.Vector`
    :param endPos: The end position vector in world space to start the twist generation.
    :type endPos: :class:`zapi.Vector`
    :param count: The number of guides to generate.
    :type count: int
    :param reverseFractions: If  reverseFractions is True then the node network will be changed \
    so that the twist starts at the start joint useful for  UprArm/UprLeg segments.

    :type reverseFractions: bool
    """
    distributionSettings = guideLayerDefinition.guideSettings("distributionType", "linearFirstLastOffset")
    for index, pos in generateTwistPositions(distributionSettings["distributionType"].value,
                                             distributionSettings["linearFirstLastOffset"].value,
                                             count,
                                             startPos,
                                             endPos
                                             ):
        multiplier = pos[1]
        # reverse the twist fraction, used in situations where the twist needs less influence near the driver.
        multiplier = 1.0 - multiplier if reverseFractions else multiplier

        index = str(index).zfill(2)
        guidId = "".join((twistPrefix, index))
        guideSettingsNode.attribute(guidId).set(multiplier)


def generateTwistPositions(distributionType,
                           linearFirstLastOffset,
                           count,
                           startPos, endPos,
                           ):
    linearDistType = distributionType == DISTRIBUTION_TYPE_LINEAR
    if linearDistType:
        distFunc = mayamath.evenLinearPointDistribution(start=startPos, end=endPos, count=count)
    else:
        distFunc = mayamath.firstLastOffsetLinearPointDistribution(start=startPos, end=endPos, count=count,
                                                                   offset=linearFirstLastOffset)

    for index, pos in enumerate(distFunc):
        yield index, pos


def generateTwistSegmentGuides(component,
                               guideLayerDefinition,
                               count,
                               startPos, endPos,
                               parentGuide,
                               twistPrefix,
                               reverseFractions=False):
    """ Guide generation function for one segment.

    This will generate twists in a evenly spaced way from the start position to the end position.
    If distributionType from the guide settings is `linearFirstLastOffset` then the first and
    last guides will have their positions offset instead.

    If `reverseFractions` is True then the fractions from start to end will be reversed so that
    the fraction 0.25 becomes 0.75(1.0-fraction). This should be used when the twist driver
    is the parent guide/joint ie. uprArm/leg. False for lwrArm.

    :param component: The Component instance
    :type component: :class:`api.Component`
    :param guideLayerDefinition: The component guideLayer definition instance \
    This Function will modify the layer in place.

    :type guideLayerDefinition: :class:`api.GuideLayerDefinition`
    :param count: The number of guides to generate.
    :type count: int
    :param startPos: the start position vector in world space to start the twist generation.
    :type startPos: :class:`zapi.Vector`
    :param endPos: The end position vector in world space to start the twist generation.
    :type endPos: :class:`zapi.Vector`
    :param parentGuide: The Parent guide which the twists will be parented too.
    :type parentGuide: :class:`api.GuideDefinition`
    :param twistPrefix: the twist prefix name for all twist guides.
    :type twistPrefix: str
    :param reverseFractions: If True the Fractions will be reverse . \
    ie. twist 2 fraction 0.25 will become 0.75.(1.0-fraction).

    :type reverseFractions: bool

    """
    configuration = component.configuration
    distributionSettings = guideLayerDefinition.guideSettings("distributionType", "linearFirstLastOffset")
    selectionHighlighting = configuration.selectionChildHighlighting
    namingConfig = component.namingConfiguration()
    compName, compSide = component.name(), component.side()

    for index, pos in generateTwistPositions(distributionSettings["distributionType"].value,
                                             distributionSettings["linearFirstLastOffset"].value,
                                             count,
                                             startPos,
                                             endPos
                                             ):
        position, multiplier = pos

        # reverse the twist fraction, used in situations where the twist needs less influence near the driver.
        multiplier = 1.0 - multiplier if reverseFractions else multiplier

        index = str(index).zfill(2)
        guidId = "".join((twistPrefix, index))
        name = namingConfig.resolve("guideName", {"componentName": compName, "side": compSide,
                                                  "id": guidId,
                                                  "type": "guide"})
        aimVector = parentGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).value
        upVector = parentGuide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).value
        # create the guide definition and parent it to the parentGuide then generate the twist fraction setting.
        guideLayerDefinition.createGuide(name=name,
                                         id=guidId,
                                         parent=parentGuide.id,
                                         color=(0.0, 0.5, 0.5),
                                         selectionChildHighlighting=selectionHighlighting,
                                         translate=list(position),
                                         rotate=parentGuide.rotate,
                                         shape="circle",
                                         scale=(0.5, 0.5, 0.5),
                                         attributes=[{"name": constants.MIRROR_ATTR, "value": True},
                                                     {"name": constants.AUTOALIGNAIMVECTOR_ATTR,
                                                      "Type": zapi.attrtypes.kMFnNumeric3Double,
                                                      "value": list(aimVector)},
                                                     {"name": constants.AUTOALIGNUPVECTOR_ATTR,
                                                      "Type": zapi.attrtypes.kMFnNumeric3Double,
                                                      "value": list(upVector)}
                                                     ],
                                         shapeTransform={"translate": list(position),
                                                         "rotate": list(parentGuide.rotate)})
        setting = guideLayerDefinition.guideSetting(guidId)
        if setting is None:
            # create the guide twist settings
            settingDef = definition.AttributeDefinition(name=guidId,
                                                        Type=zapi.attrtypes.kMFnNumericFloat,
                                                        value=multiplier,
                                                        # if not linearDistType and index not in (0, count - 1) else 0.0,
                                                        keyable=False,
                                                        channelBox=True)
            guideLayerDefinition.addGuideSetting(settingDef)


def generateTwistJointsFromGuides(component, deformLayerDef, twistGuides, startJointDef):
    """Generates the joint definitions from the provided twist guide definitions.

    :param component: The Component instance
    :type component: :class:`api.Component`
    :param deformLayerDef: The deform layer definition where the joints will be generated
    :type deformLayerDef: :class:`api.DeformLayerDefinition`
    :param twistGuides: The twist guide definitions which the joints will be generated from.
    :type twistGuides: list[:class:`api.GuideDefinition`]
    :param startJointDef: The start guide ie. the parent guide.
    :type startJointDef: :class:`api.GuideDefinition`

    """
    compName, compSide = component.name(), component.side()
    namingConfig = component.namingConfiguration()
    for guide in twistGuides:
        deformLayerDef.createJoint(name=namingConfig.resolve("skinJointName", {"componentName": compName,
                                                                               "side": compSide, "id": guide.id,
                                                                               "type": "joint"}),
                                   id=guide.id,
                                   rotateOrder=guide.get("rotateOrder", 0),
                                   translate=guide.get("translate", (0, 0, 0)),
                                   rotate=startJointDef.rotate,
                                   parent=startJointDef.id)


def createReverseTwistSegmentServer(startNode,
                                    endNode, offsetControl, rootTransform, restWorldMatrix, primaryAxisName,
                                    naming, compName, compSide):
    """Reverse's the solver so that the twist is computed from the start joint not the end.
    e.g.The upper arm starts at the shoulder and interpolates to the elbow.

    :param startNode: The start node which the twist will be computed from.
    :type startNode: :class:`zapi.DagNode`
    :param endNode: The end node for the twist calculation.
    :type endNode: :class:`zapi.DagNode`
    :param offsetControl: The Twist Offset control node associated with the twist rig segment.
    :type offsetControl: :class:`zapi.DagNode`
    :param rootTransform: The root transform node for the twist rig.
    :type rootTransform: :class:`zapi.DagNode`
    :param restWorldMatrix: The world matrix for the rest pose of the twist rig.
    :type restWorldMatrix: :class:`zapi.Plug`
    :param primaryAxisName: The name of the primary axis for rotation.
    :type primaryAxisName: str
    :param naming: The naming resolver for the component.
    :type naming: :class:`naming.Naming`
    :param compName: The name of the component.
    :type compName: str
    :param compSide: The side name of the component.
    :type compSide: str

    :return: The output plug for the twist rotation and a list of created nodes.
    :rtype: tuple(:class:`zapi.Plug`, list[:class:`zapi.DGNode`])
    :note: This function only Creates the Twist Server, not the interpolation network.
    """
    # upr arm/leg requires different math due to upr joint being the driver and the child joint being the ref
    # todo: replace with a quatToEuler once we get a stable solution for the upr arm/leg
    parentNode = startNode.parent()
    startJointName = startNode.name()

    # Create nodes for the twist rig
    twistServer = zapi.createDag(naming.resolve("object", {"componentName": compName,
                                                           "side": compSide,
                                                           "section": startJointName + "TwistServer",
                                                           "type": "joint"}),
                                 "joint", parent=rootTransform)

    ikPickTrans = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                          "side": compSide,
                                                          "section": startJointName + "onlyTranslate",
                                                          "type": "pickMatrix"}),
                                "pickMatrix")
    restIkPickTrans = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                              "side": compSide,
                                                              "section": startJointName + "noScale",
                                                              "type": "pickMatrix"}),
                                    "pickMatrix")
    ikMult = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                     "side": compSide,
                                                     "section": startJointName + "ikHandle",
                                                     "type": "multMatrix"}),
                           "multMatrix")

    # Connect nodes in the twist rig network
    startNode.attribute("matrix").connect(ikPickTrans.inputMatrix)
    restIkPickTrans.useScale.set(0)
    restIkPickTrans.useShear.set(0)
    ikPickTrans.useRotate.set(0)
    ikPickTrans.useScale.set(0)
    ikPickTrans.useShear.set(0)
    ikPickTrans.outputMatrix.connect(ikMult.matrixIn[1])
    restWorldMatrix.connect(restIkPickTrans.inputMatrix)
    restIkPickTrans.outputMatrix.connect(ikMult.matrixIn[0])
    startNode.worldMatrixPlug().connect(twistServer.offsetParentMatrix)

    # Position the server joint at the end joint but maintain the start rotations.
    endTransform = endNode.transformationMatrix()
    endTransform.setRotation(zapi.Quaternion())
    endTransform.setScale(zapi.Vector(1, 1, 1), zapi.kWorldSpace)
    twistServer.setMatrix(endTransform.asMatrix() * startNode.attribute("worldInverseMatrix")[0].value())
    twistServer.jointOrient.set(twistServer.rotation())
    twistServer.resetTransform(False, True)

    # Build constraint and hide the twist server
    const, constUtilities = zapi.buildConstraint(driven=offsetControl,
                                                 drivers={"targets": ((None, startNode),)},
                                                 constraintType="matrix",
                                                 maintainOffset=True, trace=False)
    twistServer.hide()

    # Create additional nodes for IK handling
    tempJnt = zapi.createDag("tempTwistJnt", "joint", parent=twistServer)
    tempJnt.setWorldMatrix(startNode.worldMatrix())

    ikHandle, effector = zapi.createIkHandle(naming.resolve("ikHandle", {"section": startJointName + "server",
                                                                         "componentName": compName,
                                                                         "side": compSide,
                                                                         "type": "ikHandle"}),
                                             twistServer, tempJnt, solverType="ikSCsolver",
                                             parent=parentNode)
    ikHandle.hide()
    effector.hide()
    ikMult.matrixSum.connect(ikHandle.offsetParentMatrix)
    ikHandle.resetTransform()
    outputPlug = twistServer.attribute("rotate{}".format(primaryAxisName))

    return outputPlug, [ikHandle, effector, twistServer, ikPickTrans, restIkPickTrans, ikMult] + constUtilities


def createStandardTwistServer(startNode,
                              endNode,
                              offsetControl,
                              offsetMatrixPlug,
                              primaryAxisName,
                              twistOffsetId,
                              component,
                              rigLayer
                              ):
    """Standard solver so that the twist is computed from the end joint not the start.
    e.g.The lower arm starts at the wrist and interpolates to the elbow.

    :param offsetMatrixPlug: The joint segment matrix plug which will store the calculated offset matrix.
    :type offsetMatrixPlug: :class:`api.Plug`
    :param startNode: The start node which the twist will be computed from.
    :type startNode: :class:`zapi.DagNode`
    :param endNode: The end node for the twist calculation.
    :type endNode: :class:`zapi.DagNode`
    :param offsetControl: The Twist Offset control node associated with the twist rig segment.
    :type offsetControl: :class:`zapi.DagNode`
    :param primaryAxisName: The name of the primary axis for rotation.
    :type primaryAxisName: str
    :param twistOffsetId: The primary twist offset control id used from naming.
    :type twistOffsetId: str
    :param component: The Component Instance.
    :type component: :class:`api.Component`
    :param rigLayer: The components RigLayer node.
    :type rigLayer: :class:`api.HiveRigLayer`
    :return: The output plug for the twist rotation and a list of created nodes.
    :rtype: tuple(:class:`zapi.Plug`, list[:class:`zapi.DGNode`])
    :note: This function only Creates the Twist Server, not the interpolation network.
    """
    graphRegistry = component.configuration.graphRegistry()
    primaryAimVectorAxisIdx = mayamath.AXIS_IDX_BY_NAME[primaryAxisName]
    offsetControl.resetTransform()
    offsetMatrix = (endNode.worldMatrix() * startNode.worldMatrix().inverse()).inverse()
    offsetMatrixPlug.set(offsetMatrix)
    graphName = "distributedTwist"
    distTwistDrivenMtxPlug = endNode.worldMatrixPlug()
    distTwistInvMatrixPlug = startNode.worldInverseMatrixPlug()
    twistOffsetGraphData = graphRegistry.graph("twistOffsetCtrl")
    twistOffsetGraphData.name += twistOffsetId
    # set up the offset ctrl matrix by taking the rotation/scale from the mid-joint
    # for the translation we multiply the world matrices of the end and mid-joint
    # and connect to result to the offsetParentMatrix to the offset control
    twistOffsetGraph = componentutils.createGraphForComponent(component, rigLayer, twistOffsetGraphData, track=True,
                                                              createIONodes=GRAPH_DEBUG)
    twistOffsetGraph.connectToInput("driverSrtWorldMtx", startNode.worldMatrixPlug())
    twistOffsetGraph.connectToInput("drivenSrtWorldMtx", endNode.worldMatrixPlug())
    twistOffsetGraph.connectFromOutput("outputMatrix",
                                       [offsetControl.attribute("offsetParentMatrix")])

    twistGraphData = graphRegistry.graph(graphName)
    twistGraphData.name += twistOffsetId
    twistGraph = componentutils.createGraphForComponent(component, rigLayer, twistGraphData, track=True,
                                                        createIONodes=GRAPH_DEBUG)
    twistGraph.connectToInput("drivenSrtWorldMtx", distTwistDrivenMtxPlug)
    twistGraph.connectToInput("driverSrtWorldInvMtx", distTwistInvMatrixPlug)
    twistGraph.connectToInput("twistOffsetRestPose", offsetMatrixPlug)
    if primaryAimVectorAxisIdx != mayamath.XAXIS:
        # default axis is X, but they need to change based on the primaryAxis
        twistGraph.node("twistOffsetEuler").inputQuatX.disconnectAll()
        twistGraph.node("twistOffsetEuler").attribute(
            "inputQuat{}".format(primaryAxisName)).disconnectAll()
    twistGraph.setInputAttr("negateTwistVector", zapi.Vector(-1, -1, -1))
    outputPlug = twistGraph.outputAttr("outputRotation").child(primaryAimVectorAxisIdx)
    return outputPlug, list(twistGraph.nodes().values())


def _createTwistControl(offsetControl,
                        twistGuideDef,
                        twistOffsetValuePlug,
                        twistServerPlug,
                        component,
                        jointId,
                        parent,
                        rigLayer,
                        naming,
                        compName, compSide,
                        ):
    """

    :param offsetControl: The Twist Offset control node associated with the twist rig segment.
    :type offsetControl: :class:`zapi.DagNode`
    :param twistGuideDef:
    :type twistGuideDef:
    :param twistOffsetValuePlug:
    :type twistOffsetValuePlug:
    :param twistServerPlug:
    :type twistServerPlug:
    :param component: The Component Instance.
    :type component: :class:`api.Component`
    :param jointId:
    :type jointId:
    :param parent:
    :type parent:
    :param rigLayer: The components RigLayer node.
    :type rigLayer: :class:`api.HiveRigLayer`
    :param naming: The naming resolver for the component.
    :type naming: :class:`naming.Naming`
    :param compName: The name of the component.
    :type compName: str
    :param compSide: The side name of the component.
    :type compSide: str
    :return: The output plug for the twist rotation, The graph compute graph and a list of created nodes.
    :rtype: tuple(:class:`zapi.Plug`, :class:`dggraph.DGGraph`, list[:class:`zapi.DGNode`])
    """
    aimVector = twistGuideDef.attribute(constants.AUTOALIGNAIMVECTOR_ATTR)
    aimVector = zapi.Vector(constants.DEFAULT_AIM_VECTOR) if aimVector is None else zapi.Vector(aimVector["value"])
    guideId = twistGuideDef.id

    aimVectorAttrName = "rotate" + mayamath.primaryAxisNameFromVector(aimVector)

    ctrlName = naming.resolve("twistControlName", {"componentName": compName, "side": compSide,
                                                   "id": guideId, "type": "control"})
    twistControl = rigLayer.createControl(id=guideId,
                                          name=ctrlName,
                                          shape=twistGuideDef.shape,
                                          translate=twistGuideDef.translate,
                                          rotate=twistGuideDef.rotate,
                                          rotateOrder=twistGuideDef.rotateOrder,
                                          parent=parent)
    controlSrt = rigLayer.createSrtBuffer(guideId, name="_".join([twistControl.name(), "srt"]))
    controlSrt.resetTransform()

    twistCtrlRot = component.configuration.graphRegistry().graph("twistOffsetCtrlRotation")
    twistCtrlRot.name += jointId
    graph = componentutils.createGraphForComponent(component, rigLayer, twistCtrlRot, track=True,
                                                   createIONodes=GRAPH_DEBUG)
    graph.connectToInput("driverRot", twistServerPlug)
    graph.connectToInput("twistCtrlRot", offsetControl.attribute(aimVectorAttrName))
    graph.connectToInput("restPoseDistance", twistOffsetValuePlug)
    graph.connectFromOutput("outputRotate", [controlSrt.attribute(aimVectorAttrName)])

    twistControl.showHideAttributes(["visibility"], False)
    return twistControl, graph, list(graph.nodes().values())


def _createTwistControlTranslation(startNode, endNode, guideId, naming, compName, compSide,
                                   restWorldMatrixPlug,
                                   offsetControl,
                                   twistControlSrt,
                                   twistOffsetValuePlug,
                                   aimVector,
                                   invert):
    startWorldMatrixPlug = startNode.worldMatrixPlug()
    endWorldMatrixPlug = endNode.worldMatrixPlug()
    offsetBlend = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                          "side": compSide,
                                                          "section": guideId,
                                                          "type": "blendMatrix"}),
                                "blendMatrix")
    aimMatrix = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                        "side": compSide,
                                                        "section": guideId,
                                                        "type": "aimMatrix"}), "aimMatrix")
    localOffsetMult = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                              "side": compSide,
                                                              "section": guideId + "localOffset",
                                                              "type": "multMatrix"}), "multMatrix")
    localOffsetPick = zapi.createDG(naming.resolve("object", {"componentName": compName,
                                                              "side": compSide,
                                                              "section": guideId + "localOffset",
                                                              "type": "pickMatrix"}), "pickMatrix")
    startWorldMatrixPlug.connect(offsetBlend.inputMatrix)
    offsetBlend.outputMatrix.connect(aimMatrix.inputMatrix)
    aimMatrix.outputMatrix.connect(localOffsetMult.matrixIn[1])
    restWorldMatrixPlug.connect(localOffsetPick.inputMatrix)
    localOffsetPick.outputMatrix.connect(localOffsetMult.matrixIn[0])
    startNode.worldInverseMatrixPlug().connect(localOffsetMult.matrixIn[2])
    prim = aimMatrix.primary
    secondary = aimMatrix.secondary
    endWorldMatrixPlug.connect(prim.child(3))
    offsetControl.worldMatrixPlug().connect(secondary.child(3))
    prim.child(1).set(1)  # mode
    prim.child(0).set(aimVector)  # inputAxis
    secondary.child(1).set(1)  # mode
    secondary.child(0).set((0, 0, 0))  # inputAxis
    localOffsetPick.useTranslate.set(0)
    localOffsetPick.useScale.set(0)
    localOffsetPick.useShear.set(0)

    targetElement = offsetBlend.target[0]
    endWorldMatrixPlug.connect(targetElement.child(0))  # targetMatrix
    targetElement.child(2).set(1.0 - twistOffsetValuePlug.value() if invert else twistOffsetValuePlug.value())
    targetElement.child(3).set(False)  # scale
    targetElement.child(5).set(False)  # shear
    targetElement.child(6).set(False)  # rotate
    localOffsetMult.matrixSum.connect(twistControlSrt.offsetParentMatrix)
    return offsetBlend, aimMatrix, localOffsetMult, localOffsetPick


def rigTwistJoints(component, rigLayer, guideLayer,
                   twistOffsetGuide, startGuide, startEndSrt, twistJoints,
                   settingsNode, offsetMatrixPlug, ctrlVisPlug,
                   reverseFractions=False, buildTranslation=True):
    """The function is responsible for generating the live twist calculation for the anim rig.

    todo.. This whole function needs rewriting as it's a mess.

    :type component: :class:`api.Component`
    :param rigLayer: The components RigLayer node
    :type rigLayer: :class:`api.HiveRigLayer`
    :param guideLayer: The Components guideLayer node
    :type guideLayer: :class:`api.GuideLayerDefinition`
    :param twistOffsetGuide: The primary twist offset guide node.
    :type  twistOffsetGuide: :class:`zapi.DagNode`
    :param startGuide: The start joint for twists.
    :type startGuide: :class:`api.GuideDefinition`
    :param twistJoints: Ordered sequence of joints from first to last.
    :type twistJoints: list[class:`api.Joint`]
    :param settingsNode: The settings node which contains will twist fractions
    :type settingsNode: :class:`api.SettingsNode`
    :param offsetMatrixPlug: The joint segment matrix plug which will store the calculated offset matrix.
    :type offsetMatrixPlug: :class:`api.Plug`
    :param reverseFractions: If  reverseFractions is True then the node network will be changed \
    so that the twist starts at the start joint useful for  UprArm/UprLeg segments.

    :type reverseFractions: bool
    :return: All created DG maths Nodes.
    :rtype: list[:class:`zapi.DGNode`]

    Node network::

             twistOffsetAnim ────────────────────┐
                                                 │
             twistServer ──────────┐             │
                                   ▼             ▼
             Percentage ─────────► Multi ──────► AddRotation──────┐
                                                                  │
                                                                  │
             Start  ─────────┐                                    │
                             ▼                                    ▼
                             blend ─────────►   Aim   ──────────► Control
                             ▲
              End  ──────────┘

    """

    naming = component.namingConfiguration()
    inputGuideOffsetNode = component.inputLayer().settingNode(constants.INPUT_GUIDE_OFFSET_NODE_NAME)
    compName, compSide = component.name(), component.side()
    offsetId = twistOffsetGuide.id
    startOutSrt, endOutSrt = startEndSrt
    extras = []

    offset = rigLayer.createControl(id=offsetId,
                                    name=naming.resolve("twistControlName",
                                                        {"componentName": compName, "side": compSide,
                                                         "id": twistOffsetGuide.id, "type": "control"}),
                                    translate=twistOffsetGuide.translate,
                                    rotate=twistOffsetGuide.rotate,
                                    rotateOrder=twistOffsetGuide.rotateOrder)
    ctrlVisPlug.connect(offset.visibility)
    offset.visibility.hide()

    aimVector = startGuide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR)
    aimVector = zapi.Vector(constants.DEFAULT_AIM_VECTOR) if aimVector is None else zapi.Vector(aimVector["value"])
    primaryAimVectorAxisName = mayamath.primaryAxisNameFromVector(aimVector)

    if reverseFractions:
        # first get the rest pose matrix for the twist offset control from the input offset node.
        resetWorldMatrix = _findGuideInputOffsetTransformElement(inputGuideOffsetNode, startGuide.id).child(1)
        serverOutputPlug, _extras = createReverseTwistSegmentServer(startNode=startOutSrt,
                                                                    endNode=endOutSrt,
                                                                    offsetControl=offset,
                                                                    rootTransform=rigLayer.rootTransform(),
                                                                    restWorldMatrix=resetWorldMatrix,
                                                                    primaryAxisName=primaryAimVectorAxisName,
                                                                    naming=naming,
                                                                    compName=compName,
                                                                    compSide=compSide
                                                                    )
    else:
        serverOutputPlug, _extras = createStandardTwistServer(startNode=startOutSrt,
                                                              endNode=endOutSrt,
                                                              offsetControl=offset,
                                                              offsetMatrixPlug=offsetMatrixPlug,
                                                              primaryAxisName=primaryAimVectorAxisName,
                                                              twistOffsetId=offsetId,
                                                              component=component,
                                                              rigLayer=rigLayer
                                                              )
        extras += _extras

    # we delay shape creation until after all math ops that way we can apply the shape in worldSpace without
    # having to worry about the change in the transformation
    shapeData = twistOffsetGuide.shape
    if shapeData:
        offset.addShapeFromData(shapeData, space=zapi.kWorldSpace, replace=True)

    rotationOutputGraphs = []
    twistControls = []
    for jnt in twistJoints:
        jntId = jnt.id()
        restWorldMatrix = _findGuideInputOffsetTransformElement(inputGuideOffsetNode, jntId).child(1)
        guideDef = guideLayer.guide(jntId)
        offsetValuePlug = settingsNode.attribute(jntId)

        twistControl, graph, _extras = _createTwistControl(offsetControl=offset,
                                                           twistGuideDef=guideDef,
                                                           twistOffsetValuePlug=offsetValuePlug,
                                                           twistServerPlug=serverOutputPlug,
                                                           component=component,
                                                           jointId=jnt.id(),
                                                           parent=startOutSrt,
                                                           rigLayer=rigLayer,
                                                           naming=naming,
                                                           compName=compName,
                                                           compSide=compSide)
        if buildTranslation:
            extras.extend(
                _createTwistControlTranslation(startOutSrt, endOutSrt, guideDef.id, naming, compName, compSide,
                                               restWorldMatrix, offset, twistControl.srt(),
                                               offsetValuePlug,
                                               aimVector, reverseFractions))
        ctrlVisPlug.connect(twistControl.visibility)
        extras.extend(_extras)
        twistControls.append(twistControl)
        rotationOutputGraphs.append(graph)

    return twistControls, extras




def _findGuideInputOffsetTransformElement(offsetNode, guideId):
    for transformElement in offsetNode.attribute("transforms"):
        if transformElement.child(0).value() == guideId:
            return transformElement
