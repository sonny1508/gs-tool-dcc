__all__ = (
    "buildConstraint",
    "CONSTRAINT_TYPES",
    "CONSTRAINT_ATTR_NAME",
    "ZOOCONSTRAINT_TYPE_ATTR_NAME",
    "ZOOCONSTRAINT_KWARGS_ATTR_NAME",
    "ZOOCONSTRAINT_CONTROLLER_ATTR_NAME",
    "ZOOCONSTRAINT_CONTROL_ATTR_NAME",
    "ZOOCONSTRAINT_TARGETS_ATTR_NAME",
    "ZOOCONSTRAINT_SPACELABEL_ATTR_NAME",
    "ZOOCONSTRAINT_SPACETARGET_ATTR_NAME",
    "ZOOCONSTRAINT_NODES_ATTR_NAME",
    "hasConstraint",
    "iterConstraints",
    "findConstraint",
    "deleteConstraintMapAttribute",
    "deleteConstraints",
)

import json
from collections import OrderedDict
from zoovendor import six
from maya.api import OpenMaya as om2
from maya import cmds
from zoo.libs.maya.utils import mayaenv
from zoo.libs.maya.api import nodes, attrtypes
from zoo.libs.maya.zapi import base, nodecreation

# constant mapping between maya api constraint types and maya cmds string types
CONSTRAINT_TYPES = ("parent", "point", "orient", "scale", "aim", "matrix")

CONSTRAINT_ATTR_NAME = "zooConstraint"
ZOOCONSTRAINT_TYPE_ATTR_NAME = "zooConstraintType"
ZOOCONSTRAINT_KWARGS_ATTR_NAME = "zooConstraintKwargs"
ZOOCONSTRAINT_CONTROLLER_ATTR_NAME = "zooConstraintController"
ZOOCONSTRAINT_CONTROL_ATTR_NAME = "zooConstraintControlAttrName"
ZOOCONSTRAINT_TARGETS_ATTR_NAME = "zooConstraintTargets"
ZOOCONSTRAINT_SPACELABEL_ATTR_NAME = "zooConstraintSpaceLabel"
ZOOCONSTRAINT_SPACETARGET_ATTR_NAME = "zooConstraintSpaceTarget"
ZOOCONSTRAINT_NODES_ATTR_NAME = "zooConstraintNodes"
# zoo constraint compound indices
ZOOCONSTRAINT_TYPE_IDX = 0
ZOOCONSTRAINT_KWARGS_IDX = 1
ZOOCONSTRAINT_CONTROLLER_IDX = 2
ZOOCONSTRAINT_CONTROLATTRNAME_IDX = 3
ZOOCONSTRAINT_TARGETS_IDX = 4
ZOOCONSTRAINT_SPACELABEL_IDX = 0
ZOOCONSTRAINT_SPACETARGET_IDX = 1
ZOOCONSTRAINT_NODES_IDX = 5


def buildConstraint(driven, drivers, constraintType="parent", trace=True, **kwargs):
    """This function builds a space switching constraint.

    Currently, Supporting types of::

    #. kParentConstraint
    #. kPointConstraint
    #. kOrientConstraint
    #. kScaleConstraint
    #. kMatrixConstraint, However doesn't support space switching.

    :param driven: The transform to drive
    :param driven: :class:`zapi.DagNode`
    :param drivers: A dict containing the target information(see below example)
    :param drivers: dict or None
    :param constraintType: The constraint type :see above: `CONSTRAINT_TYPES`
    :type constraintType: str
    :param trace: Whether the constraint and all nodes created should be tracked via metaData.
    :type trace: bool
    :param kwargs: The constraint extra arguments to use ie. maintainOffset etc.
    :type kwargs: dict
    :keyword maintainOffset (bool): Whether to maintain the offset transformation.
    :rtype: tuple[:class:`Constraint`, list[:class:`base.DagNode`]]

    .. code-block: python

        from zoo.libs.maya import zapi

        targets = []
        for n in ("locator1", "locator2", "locator3"):
            targets.append((n, zapi.createDag(n, "locator")))
        spaceNode =zapi.createDag("control", "locator")
        drivenNode = zapi.createDag("driven", "locator")

        spaces = {"spaceNode": spaceNode,
                    "attributeName": "parentSpace", "targets": targets}
        constraint, utilties = zapi.buildConstraint(drivenNode, drivers=spaces)

        # lets add to the existing system
        spaces = {"spaceNode": spaceNode, "attributeName": "parentSpace", "targets": (
                 ("locator8", zapi.createDag("locator8", "locator")),)}

        constraint, utilties = zapi.buildConstraint(drivenNode, drivers=spaces)


    """
    # make sure we support the constraint type the user wants
    assert (
        constraintType in CONSTRAINT_TYPES
    ), "No Constraint of type: {}, supported".format(constraintType)
    constraintAttr = None
    if trace:
        attrName = drivers.get("attributeName", "")
        for lastConstraint in iterConstraints(driven):
            if attrName and attrName == lastConstraint.controllerAttrName():
                utilities = lastConstraint.build(drivers, **kwargs)
                return lastConstraint, utilities
            constraintAttr = lastConstraint.plugElement
        if constraintAttr is None:
            constraintAttr = addConstraintAttribute(driven)[0]
        else:
            latestConstraintIndex = constraintAttr.logicalIndex()
            constraintAttr = driven.attribute(CONSTRAINT_ATTR_NAME)[
                latestConstraintIndex + 1
            ]

    constraint = createConstraintFactory(
        constraintType, driven, constraintAttr, trace=trace
    )

    return constraint, constraint.build(drivers, **kwargs)


class Constraint(object):
    """
    :param driven:
    :type driven: :class:`base.DagNode` or None
    :param plugElement:
    :type plugElement: :class:`base.Plug` or None
    :param trace: Whether the constraint and all nodes created should be tracked via metaData.
    :type trace: bool
    :raise ValueError:
    """

    id = ""

    def __init__(self, driven=None, plugElement=None, trace=True):
        if driven and not plugElement or (plugElement and not driven):
            raise ValueError(
                "if driven or plugElement is specified then both need to be specified"
            )
        self._trace = trace
        self._driven = driven
        self.plugElement = plugElement
        self.constraintNode = None

    def build(self, drivers, **constraintKwargs):
        raise NotImplementedError("Build method must be implemented in subclasses")

    def delete(self, mod=None, apply=True):
        for targetPlug in self.plugElement.child(ZOOCONSTRAINT_NODES_IDX):
            sourcePlug = targetPlug.source()
            if not sourcePlug:
                continue
            utilNode = sourcePlug.node()
            # disconnect connections from utilities
            for sourcePlug, destPlug in utilNode.iterConnections(True, False):
                sourcePlug.disconnect(destPlug, modifier=mod, apply=apply)
            # delete utilities
            utilNode.delete(mod=mod, apply=True)

        controllerNode = self.plugElement.child(
            ZOOCONSTRAINT_CONTROLLER_IDX
        ).sourceNode()
        if controllerNode is not None:
            attrName = self.plugElement.child(ZOOCONSTRAINT_CONTROLATTRNAME_IDX).value()
            controlAttr = controllerNode.attribute(attrName)
            if controlAttr is not None:
                # add the attr deletion to the existing modifier, so we batch delete
                controlAttr.delete(modifier=mod, apply=False)
        if mod is not None:
            mod.doIt()
        # remove multi instance element plug
        try:
            self.plugElement.delete(modifier=mod, apply=True)
        except Exception:
            if mod is not None:
                mod.doIt()
            return True
        return True

    def driven(self):
        return self._driven

    def setDriven(self, node, plugElement):
        self._driven = node
        self.plugElement = plugElement

    def addUtilityNodes(self, nodes):
        if self.plugElement is None:
            return
        for n in nodes:
            element = self.plugElement.child(
                ZOOCONSTRAINT_NODES_IDX
            ).nextAvailableDestElementPlug()
            n.message.connect(element)

    def addUtilityNode(self, node):
        if self.plugElement is None:
            return
        element = self.plugElement.child(
            ZOOCONSTRAINT_NODES_IDX
        ).nextAvailableDestElementPlug()
        node.message.connect(element)

    def utilityNodes(self):
        if self.plugElement is None:
            return
        for targetPlug in self.plugElement.child(ZOOCONSTRAINT_NODES_IDX):
            sourcePlug = targetPlug.source()
            if not sourcePlug:
                continue
            utilNode = sourcePlug.node()
            if utilNode is None:
                continue
            yield utilNode

    def drivers(self):
        if self.plugElement is None:
            return
        for targetElement in self.plugElement.child(ZOOCONSTRAINT_TARGETS_IDX):
            sourceNode = targetElement.child(ZOOCONSTRAINT_SPACETARGET_IDX).sourceNode()
            label = targetElement.child(ZOOCONSTRAINT_SPACELABEL_IDX).value()
            if label:
                yield label, sourceNode

    def hasTarget(self, node):
        for _, target in self.drivers():
            if target == node:
                return True
        return False

    def hasTargetLabel(self, label):
        if self.plugElement is None:
            return
        for targetElement in self.plugElement.child(ZOOCONSTRAINT_TARGETS_IDX):
            if targetElement.child(ZOOCONSTRAINT_SPACELABEL_IDX).value() == label:
                return True
        return False

    def controllerAttrName(self):
        """Returns the attribute name which controls this constraint if any

        :rtype: str
        """
        plugElement = self.plugElement
        if plugElement is None:
            return ""
        return plugElement.child(ZOOCONSTRAINT_CONTROLATTRNAME_IDX).value()

    def controller(self):
        plugElement = self.plugElement
        if plugElement is None:
            return {"node": None, "attr": None}
        sourcePlug = plugElement.child(ZOOCONSTRAINT_CONTROLLER_IDX).source()
        if sourcePlug is None:
            return {"node": None, "attr": None}
        controller = sourcePlug.node()
        return {
            "node": controller,
            "attr": sourcePlug.node().attribute(
                plugElement.child(ZOOCONSTRAINT_CONTROLATTRNAME_IDX).value()
            ),
        }

    def serialize(self):
        plugElement = self.plugElement
        if not plugElement:
            return {}
        sources = plugElement[ZOOCONSTRAINT_TARGETS_IDX]
        kwargsStr = plugElement[ZOOCONSTRAINT_KWARGS_IDX].value()
        try:
            kwargs = json.loads(kwargsStr)
        except ValueError:
            kwargs = {}
        targets = []
        for source in sources:
            label = source.child(ZOOCONSTRAINT_SPACELABEL_IDX).value()
            target = source.child(ZOOCONSTRAINT_SPACETARGET_IDX).sourceNode()
            if not target:
                continue
            targets.append((label, target))
        if not targets:
            return {}
        controllerSource = plugElement.child(ZOOCONSTRAINT_CONTROLLER_IDX).source()
        controllerNode = None
        if controllerSource is not None:
            controllerNode = controllerSource.node()
        mapping = {
            "targets": targets,
            "kwargs": kwargs,
            "controller": (
                controllerNode,
                plugElement.child(ZOOCONSTRAINT_CONTROLATTRNAME_IDX).value(),
            ),
            "type": self.id,
        }
        return mapping


class ParentConstraint(Constraint):
    id = "parent"
    constraintTargetIndex = 1
    # cmds function name
    _constraintFunc = "parentConstraint"

    def preConstructConstraint(self, driven, targetNodes, kwargs):
        pass

    def postConstructConstraint(self, driven, targetNodes, constraint, kwargs):
        pass

    def build(self, drivers, **constraintKwargs):
        spaceNode = drivers.get("spaceNode")
        attrName = drivers.get("attributeName", "parent")
        targetInfo = drivers["targets"]
        defaultDriverLabel = drivers.get("label", "")

        # generate a single consolidated target structure with target label and node.
        # this replaces any existing label with the new node.
        # We also ignore rebuilding the constraint if the request is the same as the current targets.
        newTargetStructure = OrderedDict(self.drivers())
        newTargetStructure.update(OrderedDict(targetInfo))
        requiresUpdate = False
        for index, (requestLabel, requestNode) in enumerate(targetInfo):
            existingTarget = newTargetStructure.get(requestLabel)
            if existingTarget is not None or existingTarget != requestNode:
                requiresUpdate = True

            newTargetStructure[requestLabel] = requestNode
        if not requiresUpdate:
            return []

        # sort out the condition nodes second term,
        # when a target node is set to None it means the target inherents from its Dag transform
        # not from another node in different Dag branch.
        indexing = [
            index
            for index, (requestLabel, requestNode) in enumerate(targetInfo)
            if requestNode
        ]  # type: list[int]

        if self._trace:
            self.delete()

        driven = self.driven()
        # create the constraint
        cmdsFunc = getattr(cmds, self._constraintFunc)
        # constraint kwargs keys can come through as unicode but maya 2020 doesn't support unicode with cmds so convert
        constraintKwargs = {six.ensure_str(k): v for k, v in constraintKwargs.items()}
        targetNodes = [target for _, target in newTargetStructure.items() if target]
        self.preConstructConstraint(driven, targetNodes, constraintKwargs)
        # build the cmds kwargs and construct the constraint.
        constraint = cmdsFunc(
            [target.fullPathName() for target in targetNodes],
            driven.fullPathName(),
            **constraintKwargs
        )[0]
        constraint = base.nodeByName(constraint)
        self.postConstructConstraint(driven, targetNodes, constraint, constraintKwargs)

        self.constraintNode = constraint
        # in this case no space switching is needed, so we exit early
        if not spaceNode:
            if self._trace:
                addConstraintMap(
                    targetInfo,
                    driven,
                    None,
                    "",
                    [constraint],
                    self.id,
                    metaElementPlug=self.plugElement,
                    kwargsMap=constraintKwargs,
                )
            return [constraint]
        # if we have been provided a spaceNode, which will contain our switch, otherwise ignore the setup of a switch
        # and just return the constraint.
        # spaceNode.deleteAttribute(attrName)
        spaceAttr = spaceNode.attribute(attrName)
        try:
            defaultIndex = list(newTargetStructure.keys()).index(defaultDriverLabel)
        except ValueError:
            defaultIndex = 0
        if spaceAttr is not None:
            spaceAttr.setFields(list(newTargetStructure.keys()))
        else:
            spaceAttr = spaceNode.addAttribute(
                attrName,
                Type=base.attrtypes.kMFnkEnumAttribute,
                keyable=True,
                channelBox=False,
                locked=False,
                enums=list(newTargetStructure.keys()),
                default=defaultIndex,
                value=defaultIndex,
            )

        targetArray = constraint.target
        sourceShortName = constraint.fullPathName(
            partialName=True, includeNamespace=False
        )
        conditions = []
        constraintTargetWeightIndex = self.constraintTargetIndex
        # first iterate over the target array on the constraint.target[0]
        for index, targetElement in enumerate(targetArray):
            # target[0].targetWeight
            targetElementWeight = targetElement.child(constraintTargetWeightIndex)
            # the actual weight plug we connect too normally.
            targetWeightSource = targetElementWeight.source()
            # just in case the target weight plug is disconnected
            if targetWeightSource is None:
                targetWeightSource = targetElementWeight

            # figure out what the index is from the labels this way it's based on the enum
            targetNode = targetElement.child(0).source().node()
            targetShortName = targetNode.fullPathName(
                partialName=True, includeNamespace=False
            )
            # create the condition node and do the connections
            condition = nodecreation.conditionVector(
                firstTerm=spaceAttr,
                secondTerm=float(indexing[index]),
                colorIfTrue=(1.0, 0.0, 0.0),
                colorIfFalse=(0.0, 0.0, 0.0),
                operation=0,
                name="_".join([targetShortName, sourceShortName, self.id, "space"]),
            )
            condition.outColorR.connect(targetWeightSource)
            conditions.append(condition)
        if self._trace:
            addConstraintMap(
                targetInfo,
                driven,
                spaceNode,
                attrName,
                conditions + [constraint],
                self.id,
                metaElementPlug=self.plugElement,
                kwargsMap=constraintKwargs,
            )
        return conditions + [constraint]


class PointConstraint(ParentConstraint):
    id = "point"
    constraintTargetIndex = 4
    _constraintFunc = "pointConstraint"

    def preConstructConstraint(self, driven, targetNodes, kwargs):
        # point constraint maintain offset has a strange bug we're when adding multiple
        # targets with maintain offset will introduce incorrect offset so here to manage the
        # translation offset ourselves
        firstTarget = targetNodes[0]
        if kwargs.get("maintainOffset"):
            self.translationOffset = driven.translation(
                space=base.kWorldSpace
            ) - firstTarget.translation(base.kWorldSpace)

    def postConstructConstraint(self, driven, targetNodes, constraint, kwargs):
        if kwargs.get("maintainOffset"):
            constraint.offset.set(self.translationOffset)


class OrientConstraint(ParentConstraint):
    id = "orient"
    constraintTargetIndex = 4
    _constraintFunc = "orientConstraint"


class ScaleConstraint(ParentConstraint):
    id = "scale"
    constraintTargetIndex = 2
    _constraintFunc = "scaleConstraint"


class AimConstraint(ParentConstraint):
    id = "aim"
    constraintTargetIndex = 4
    _constraintFunc = "aimConstraint"


class MatrixConstraint(Constraint):
    id = "matrix"

    def build(self, drivers, decompose=False, **constraintKwargs):
        if mayaenv.mayaVersion() >= 2020 and not decompose:
            return _buildOffsetParentMatrixConstraint(
                self.id, self.driven(), drivers, self._trace, **constraintKwargs
            )
        return _buildMultMatrixConstraint(
            self.id, self.driven(), drivers, self._trace, **constraintKwargs
        )


def _buildOffsetParentMatrixConstraint(
    constraintId, driven, drivers, trace=True, **constraintKwargs
):
    maintainOffset = constraintKwargs.get("maintainOffset", False)
    skipScale = constraintKwargs.get("skipScale", [False, False, False])
    skipRotate = constraintKwargs.get("skipRotate", [False, False, False])
    skipTranslate = constraintKwargs.get("skipTranslate", [False, False, False])
    name = driven.fullPathName(partialName=True, includeNamespace=False)
    targetInfo = drivers["targets"]
    targetLabels, targetNodes = zip(*targetInfo)
    driver = targetNodes[0]  # temp
    composename = "_".join([name, "pickMtx"])
    skipScale = any(i for i in skipScale)
    skipTranslate = any(i for i in skipTranslate)
    skipRotate = any(i for i in skipRotate)
    utilties = []
    currentWorldMatrix = driven.worldMatrix()
    if any((skipScale, skipTranslate, skipRotate)):
        mat = base.createDG(composename, "pickMatrix")
        driver.attribute("worldMatrix")[0].connect(mat.inputMatrix)

        mat.useRotate = not skipRotate
        mat.useScale = not skipScale
        mat.useTranslate = not skipTranslate
        mat.outputMatrix.connect(driven.offsetParentMatrix)
        utilties.append(mat)
    else:
        driver.attribute("worldMatrix")[0].connect(driven.offsetParentMatrix)

    if maintainOffset:
        driven.setMatrix(
            currentWorldMatrix * driven.offsetParentMatrix.value().inverse()
        )
    else:
        driven.resetTransform(translate=True, rotate=True, scale=True)
    if trace:
        addConstraintMap(
            targetInfo,
            driven,
            None,
            "",
            utilties,
            constraintId,
            None,
            kwargsMap=constraintKwargs,
        )
    return utilties


def _buildMultMatrixConstraint(
    constraintId, driven, drivers, trace=True, **constraintKwargs
):
    """Decompose matrix constraint to translate, rotate, scale
    :param constraintId:
    :type constraintId:
    :param driven:
    :type driven:
    :param drivers:
    :type drivers:
    :param trace:
    :type trace:
    :param constraintKwargs:
    :type constraintKwargs:
    :return:
    :rtype:
    """
    maintainOffset = constraintKwargs.get("maintainOffset", False)
    skipScale = constraintKwargs.get("skipScale") or (True, True, True)
    skipRotate = constraintKwargs.get("skipRotate") or (True, True, True)
    skipTranslate = constraintKwargs.get("skipTranslate") or (True, True, True)
    name = driven.fullPathName(partialName=True, includeNamespace=False)
    targetInfo = drivers["targets"]
    targetLabels, targetNodes = zip(*targetInfo)
    driver = targetNodes[0]  # temp

    isJnt = driven.apiType() == om2.MFn.kJoint
    drivenParent = driven.parent()
    if drivenParent:
        parentWorldMtx = drivenParent.worldMatrixPlug()
    else:
        parentWorldMtx = driven.parentMatrix[0].value()

    offset = nodes.getOffsetMatrix(driver.object(), driven.object())

    def composeJointMatrixTSGraph():
        """Builds the translate and scale graph"""
        if all(not i for i in skipTranslate) and all(not i for i in skipScale):
            return []
        if maintainOffset:
            inputs = [offset, driver.worldMatrixPlug()]
        else:
            inputs = [driver.worldMatrixPlug()]
        if drivenParent is not None:
            inputs.append(drivenParent.worldInverseMatrixPlug())
        multMatrix = nodecreation.createMultMatrix(
            name + "_outputTSMat", inputs=inputs, output=None
        )
        decompose = nodecreation.createDecompose(
            name + "outputTSDecomp",
            inputMatrixPlug=multMatrix.matrixSum,
            destination=driven,
            translateValues=skipTranslate,
            scaleValues=skipScale,
            rotationValues=(False, False, False),
        )
        driver.rotateOrder.connect(decompose.inputRotateOrder)
        return [multMatrix, decompose]

    def composeJointMatrixRotGraph():
        """Builds the rotation graph handling jointOrient"""
        if all(not i for i in skipRotate):
            return []
        jntOrient = base.EulerRotation(driven.jointOrient.value())
        transform = base.TransformationMatrix()
        transform.setRotation(jntOrient)
        extras = []
        if drivenParent is not None:
            jointOrientMatInv = base.createDG(name + "_orientMatInv", "inverseMatrix")
            jointOrientMat = nodecreation.createMultMatrix(
                name + "_orientMat",
                inputs=(transform.asMatrix(), parentWorldMtx),
                output=jointOrientMatInv.inputMatrix,
            )
            orientOffset = jointOrientMatInv.outputMatrix
            extras = [jointOrientMat, jointOrientMatInv]
        else:
            orientOffset = transform.asMatrixInverse()

        jointLocalMat = nodecreation.createMultMatrix(
            name + "_localRotMtx",
            inputs=(offset, driver.worldMatrixPlug(), orientOffset),
            output=None,
        )
        decompose = nodecreation.createDecompose(
            name + "_outputRotMtx",
            inputMatrixPlug=jointLocalMat.matrixSum,
            destination=driven,
            translateValues=(False, False, False),
            scaleValues=(False, False, False),
            rotationValues=skipRotate or (),
        )
        driver.rotateOrder.connect(decompose.inputRotateOrder)
        extras.extend([jointLocalMat, decompose])
        return extras

    utilities = []
    if isJnt:
        utilities.extend(composeJointMatrixRotGraph())
        utilities.extend(composeJointMatrixTSGraph())
    else:
        if maintainOffset:
            offset = nodes.getOffsetMatrix(driver.object(), driven.object())
            inputs = [offset, driver.attribute("worldMatrix")[0]]
            if drivenParent is not None:
                inputs.append(drivenParent.worldInverseMatrixPlug())
            offsetName = "_".join([name, "wMtxOffset"])
            multMatrix = nodecreation.createMultMatrix(
                offsetName, inputs=inputs, output=None
            )
            outputPlug = multMatrix.matrixSum
            utilities.append(multMatrix)
        else:
            outputPlug = driver.attribute("worldMatrix")[0]
        composeName = "_".join([name, "wMtxCompose"])
        decompose = nodecreation.createDecompose(
            composeName,
            destination=driven,
            translateValues=skipTranslate or (),
            scaleValues=skipScale or (),
            rotationValues=skipRotate or (),
        )
        utilities.append(decompose)
        driver.rotateOrder.connect(decompose.inputRotateOrder)
        outputPlug.connect(decompose.inputMatrix)
    if trace:
        addConstraintMap(
            targetInfo,
            driven,
            None,
            "",
            utilities,
            constraintId,
            None,
            kwargsMap=constraintKwargs,
        )
    return utilities


# temp
def createConstraintFactory(constraintType, drivenNode, constraintMetaPlug, trace=True):
    constObj = CONSTRAINT_PLUGINS.get(constraintType)
    if constObj is None:
        raise NotImplementedError(
            "Constraint Type : {} not supported".format(constraintType)
        )
    instance = constObj(trace=trace)
    instance.setDriven(drivenNode, constraintMetaPlug)
    return instance


def findConstraint(node, constraintType):
    """Searches the upstream graph one level  in search for the corresponding kConstraintType

    :param node: The node to search upstream from
    :type node: :class:`base.DagNode`
    :param constraintType:
    :type constraintType: str
    :return: Constraint class instance.
    :rtype: :class:`Constraint`
    """
    for plugElement in node.zooConstraint:
        typeValue = plugElement.child(0).value()
        if typeValue != constraintType:
            continue
        return createConstraintFactory(constraintType, node, plugElement)


def hasConstraint(node):
    """Determines if this node is constrained by another, this is done by checking the constraints compound attribute

    :param node: the node to search for attached constraints
    :type node: :class:`base.DagNode`
    :rtype: bool
    """
    # exit early when iterConstraints returns something
    for i in iterConstraints(node):
        return True
    return False


def iterConstraints(node):
    """Generator function that loops over the attached constraints, this is done
    by iterating over the compound array attribute `constraints`.

    :param node: The node to iterate, this node should already have the compound attribute
    :type node: :class:`base.DagNode`
    :return: First element is a list a driven transforms, the second is a list of \
    utility nodes used to create the constraint.
    :rtype: list[:class:`Constraint`]
    """
    array = node.attribute(CONSTRAINT_ATTR_NAME)  # type: base.Plug or None
    if array is None:
        return
    for plugElement in array:
        typeValue = plugElement.child(0).value()
        if not typeValue:
            continue
        yield createConstraintFactory(typeValue, node, plugElement)


def addConstraintAttribute(node):
    """Creates and returns the 'constraints' compound attribute, which is used to store all incoming constraints
    no matter how they are created. If the attribute exists then that will be returned.

    :param node: The node to have the constraint compound attribute.
    :type node: :class:`base.DagNode`
    :return: Return's the constraint compound attribute.
    :rtype: :class:`om2.MPlug` or :class:`base.Plug`

    Resulting Attribute structure
    zooConstraint[]
                |- zooConstraintType  # str, constraintType ie. parent, matrix, scale, point etc.
                |- zooConstraintKwargs # json string , kwargs passed directly to the constraint class
                |- zooConstraintController # message attribute linked to the constraint switch controller
                |- zooConstraintControlAttrName # constraint controller attribute name , used for lookups
                |- zooConstraintTargets[]
                                |-constraintSpaceLabel # target label for the controller attribute enum
                                |-constraintSpaceTarget # message attribute linked to the target node ie. transform
                |- zooConstraintNodes[] # utility nodes, ie. parentConstraint node
    """

    if node.hasAttribute(CONSTRAINT_ATTR_NAME):
        return node.zooConstraint
    constraintPlug = node.addCompoundAttribute(
        name=CONSTRAINT_ATTR_NAME,
        Type=attrtypes.kMFnCompoundAttribute,
        isArray=True,
        attrMap=[
            {"name": ZOOCONSTRAINT_TYPE_ATTR_NAME, "Type": attrtypes.kMFnDataString},
            {
                "name": ZOOCONSTRAINT_KWARGS_ATTR_NAME,
                "Type": attrtypes.kMFnDataString,
                "isArray": False,
            },
            {
                "name": ZOOCONSTRAINT_CONTROLLER_ATTR_NAME,
                "Type": attrtypes.kMFnMessageAttribute,
                "isArray": False,
            },
            {
                "name": ZOOCONSTRAINT_CONTROL_ATTR_NAME,
                "Type": attrtypes.kMFnDataString,
                "isArray": False,
            },
            {
                "name": ZOOCONSTRAINT_TARGETS_ATTR_NAME,
                "Type": attrtypes.kMFnCompoundAttribute,
                "isArray": True,
                "children": [
                    {
                        "name": ZOOCONSTRAINT_SPACELABEL_ATTR_NAME,
                        "Type": attrtypes.kMFnDataString,
                    },
                    {
                        "name": ZOOCONSTRAINT_SPACETARGET_ATTR_NAME,
                        "Type": attrtypes.kMFnMessageAttribute,
                    },
                ],
            },
            {
                "name": ZOOCONSTRAINT_NODES_ATTR_NAME,
                "Type": attrtypes.kMFnMessageAttribute,
                "isArray": True,
            },
        ],
    )
    return constraintPlug


def deleteConstraints(objects, modifier=None):
    modifier = modifier or om2.MDagModifier()
    for n in objects:
        for constraint in iterConstraints(n):
            constraint.delete(modifier, apply=False)
        # call doIt because deleteConstraintMapAttribute disconnects from the maya nodes which doesn't
        # exist anymore which raises InternalError
        modifier.doIt()
        deleteConstraintMapAttribute(n, modifier=modifier)
    return modifier


def deleteConstraintMapAttribute(node, modifier=None):
    """Removes the constraint metaData if present on the provided node.

    The metadata is found if the `zooConstraint` attribute is found.

    :param node: The node the remove the metadata from.
    :type node: :class:`zapi.DgNode`
    :param modifier: The Modifier instance to use.
    :type modifier: :class:`zapi.dgModifier` or None
    :return: The provided modifier instance or the newly created one.
    :rtype: :class:`zapi.dgModifier` or None
    """
    constraintAttr = node.attribute(CONSTRAINT_ATTR_NAME)
    if constraintAttr is None:
        return modifier

    # first check to make sure theres no connections
    modifier = modifier or om2.MDGModifier()
    if constraintAttr.numConnectedElements() > 0:
        for attribute in constraintAttr:
            if attribute.numConnectedChildren() < 1:
                continue
            targetAttr = attribute.child(4)
            controllerAttr = attribute.child(2)
            extraNodesAttr = attribute.child(5)
            controllerAttr.disconnectAll(modifier=modifier)
            if targetAttr.numConnectedElements() > 0:
                for element in targetAttr:
                    if element.numConnectedChildren() < 1:
                        continue
                    element.child(1).disconnectAll(modifier=modifier)
            if extraNodesAttr.numConnectedElements() < 1:
                continue
            for element in extraNodesAttr:
                element.disconnectAll(modifier=modifier)
    modifier.doIt()  # disconnect on a separate pass to delete otherwise an internal failure occurs
    constraintAttr.delete(modifier=modifier)

    return modifier


def addConstraintMap(
    drivers,
    driven,
    controller,
    controllerAttrName,
    utilities,
    constraintType,
    metaElementPlug,
    kwargsMap=None,
):
    """Adds a mapping of drivers and utilities to the constraint compound array attribute"""
    kwargsMap = kwargsMap or {}
    compoundPlug = addConstraintAttribute(driven)
    if not metaElementPlug:
        # find the next array element not used
        for element in compoundPlug:
            elementConstraintType = element.child(ZOOCONSTRAINT_TYPE_IDX).value()
            if not elementConstraintType or elementConstraintType == constraintType:
                metaElementPlug = element
                break
        if metaElementPlug is None:
            metaElementPlug = compoundPlug[0]
    constraintTypePlug = metaElementPlug.child(ZOOCONSTRAINT_TYPE_IDX)
    kwargsPlug = metaElementPlug.child(ZOOCONSTRAINT_KWARGS_IDX)
    # connect to controller and name if it's specified
    if controller is not None:
        controllerPlug = metaElementPlug.child(ZOOCONSTRAINT_CONTROLLER_IDX)
        controllerNamePlug = metaElementPlug.child(ZOOCONSTRAINT_CONTROLATTRNAME_IDX)
        controller.message.connect(controllerPlug)
        controllerNamePlug.set(controllerAttrName)

    targetsPlug = metaElementPlug.child(ZOOCONSTRAINT_TARGETS_IDX)
    constraintsPlug = metaElementPlug.child(ZOOCONSTRAINT_NODES_IDX)
    constraintTypePlug.set(constraintType)
    kwargsPlug.set(json.dumps(kwargsMap))
    # connect the drivers and set the driver labels
    index = 0
    driverElement = targetsPlug.nextAvailableDestElementPlug()
    for driverLabel, driver in drivers:
        index += 1
        driverElement.child(ZOOCONSTRAINT_SPACELABEL_IDX).set(driverLabel)
        if driver:
            driver.message.connect(driverElement.child(ZOOCONSTRAINT_SPACETARGET_IDX))

        driverElement = targetsPlug[index]
    # connect to labels
    for constraintNode in utilities:
        constraintNode.message.connect(constraintsPlug.nextAvailableDestElementPlug())

    return compoundPlug


def serializeConstraints(node):
    """Serializes all attached zoo constraints to the provided node.

    :param node:
    :type node: :class:`base.DagNode`
    :return: A list of constraint dictionaries
    :rtype: list[dict]
    """
    constraints = []
    if not node.hasAttribute(CONSTRAINT_ATTR_NAME):
        return constraints
    for constraint in iterConstraints(node):
        constraintInfo = constraint.serialize()
        if not constraintInfo:
            continue
        constraints.append(constraintInfo)
    return constraints


CONSTRAINT_PLUGINS = {
    "parent": ParentConstraint,
    "point": PointConstraint,
    "scale": ScaleConstraint,
    "orient": OrientConstraint,
    "aim": AimConstraint,
    "matrix": MatrixConstraint,
}
