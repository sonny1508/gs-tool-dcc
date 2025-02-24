__all__ = [
    "pathAsDefExpression",
    "attributeRefToSceneNode",
    "splitAttrExpression",
    "componentTokenFromExpression"
]

import re

from zoo.libs.hive import constants
from zoo.libs.hive.base import errors
from zoo.core.util import zlogging
from zoo.libs.utils import general

if general.TYPE_CHECKING:
    from zoo.libs.maya import zapi


logger = zlogging.getLogger(__name__)

DEFINITION_VALUE_REF_PATTERN = re.compile(r"(?:\@{(.*)\})")


def splitAttrExpression(expression):
    """Given an attribute expression return the individual parts as a list.

    :param expression: The attribute expression to parse i.e. "{@self.inputLayer.upr}".
    :type expression: str
    :return: list containing the individuals parts from the expression i.e. ["self", "inputLayer", "upr"]
    :rtype: list[str]
    """
    for i in DEFINITION_VALUE_REF_PATTERN.findall(expression):
        return i.split(".")
    return []


def componentTokenFromExpression(expression):
    """Return the component token from the attribute expression.

    :param expression: The attribute expression to parse into a component instance.
    :type expression: str
    :return: The component token ie. "self" will return from an expression in the form of "@{self.inputLayer.upr}"
    :rtype: str
    """
    parts = splitAttrExpression(expression)
    if parts:
        return parts[0].split(":")
    return parts


def pathAsDefExpression(pathParts):
    """Surrounds the provided iterable of strings with the definition attribute expression "@{strs}".

    .. code-block:: python

        result = pathAsDefExpression(("self", "inputLayer", "upr"))
        # result == "@{self.inputLayer.upr}"

    :param pathParts: [self, inputLayer, upr]
    :type pathParts: iterable[str]
    :return: The expression str for the string parts.
    :rtype: str
    """
    return "@{" + ".".join(pathParts) + "}"


def attributeRefToSceneNode(rig, component, referenceExpr):
    """Returns the scene node or the component from an attribute expression.

    @{self.inputLayer.world} # returns the input node "world" dagNode
    @{self} # returns the component

    :param rig: The rig instance which this expression needs to be resolved against.
    :type rig: :class:`zoo.libs.hive.base.rig.Rig`
    :param component: The current component which will act as the "self" token of the expression if it exists.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param referenceExpr:
    :type referenceExpr: str
    :rtype: tuple[:class:`zoo.libs.hive.base.component.Component`, :class:`zapi.DagNode`]
    """
    parts = splitAttrExpression(referenceExpr)
    componentTag = parts[0]
    if componentTag == "inherit":
        return None, None
    elif componentTag != "self":
        # resolve the component from the rig
        component = rig.component(*componentTag.split(":"))
        if not component:
            raise errors.InvalidDefinitionAttrExpression(referenceExpr)
    elif len(parts) == 1:
        if componentTag == "self":
            return component, None
    try:
        layerType = parts[1]
        nodeId = parts[2]
    except IndexError:
        raise errors.InvalidDefinitionAttrExpression(referenceExpr)

    try:
        if layerType == constants.INPUTLAYER_DEF_KEY:
            sceneLayer = component.inputLayer()
            return component, sceneLayer.inputNode(nodeId)
        elif layerType == constants.OUTPUTLAYER_DEF_KEY:
            sceneLayer = component.outputLayer()
            return component, sceneLayer.outputNode(nodeId)
        elif layerType == constants.RIGLAYER_DEF_KEY:
            sceneLayer = component.rigLayer()
            return component, sceneLayer.control(nodeId)
        elif layerType == constants.DEFORMLAYER_DEF_KEY:
            sceneLayer = component.deformLayer()
            return component, sceneLayer.joint(nodeId)
        elif layerType == constants.GUIDE_LAYER_TYPE:
            sceneLayer = component.guideLayer()
            return component, sceneLayer.guide(nodeId)
    except (errors.MissingControlError, errors.InvalidInputNodeMetaData,
            errors.InvalidOutputNodeMetaData):
        logger.warning("Missing Node '{}' for expression {}".format(nodeId, referenceExpr))
        return component, None
    return None, None
