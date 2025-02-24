from maya.api import OpenMaya as om2

from zoo.core.util import zlogging
from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import plugs

logger = zlogging.getLogger(__name__)


def poleVectorPosition(start, mid, end, distance=-1.0):
    """This function gets the position of the pole vector from 3 MVectors

    :param start: the start vector
    :type start: MVector
    :param mid: the mid vector
    :type mid: MVector
    :param end: the end vector
    :type end: MVector
    :param distance: The pole vector distance from the mid-position along the normal, if -1 then the distance \
    from the start and mid will be used.

    :type: distance: float
    :return: the vector position of the pole vector
    :rtype: MVector
    :raises ValueError: Raises When the mid point and the projection vector are the same
    """

    line = end - start
    point = mid - start

    scaleValue = (line * point) / (line * line)
    projVec = line * scaleValue + start

    if tuple(round(i, 3) for i in projVec) == tuple(round(i, 3) for i in mid):
        raise ValueError("No valid angle to calculate")

    return (mid - projVec).normal() * distance + mid

def hypotenuseMidPointVector(start, mid, end):
    """This function gets the Vector between the provided mid-point and the hypotenuse mid-point

    :param start: the start vector.
    :type start: :class:`om2.MVector`
    :param mid: the mid-vector.
    :type mid: :class:`om2.MVector`
    :param end: the end vector.
    :type end: :class:`om2.MVector`
    :return: Vector between the provided mid-point and the hypotenuse mid-point
    :rtype: :class:`om2.MVector`
    :raises ValueError: Raises When the mid-point and the projection vector are the same
    """

    line = end - start
    point = mid - start

    scaleValue = (line * point) / (line * line)
    projVec = line * scaleValue + start

    if tuple(round(i, 3) for i in projVec) == tuple(round(i, 3) for i in mid):
        raise ValueError("No valid angle to calculate")

    return projVec - mid

def convertToNode(node, parent, prefix, nodeType="joint"):
    """Converts a node into a joint but does not delete the node ,
    transfers matrix over as well

    :param node: mobject, the node that will be converted
    :param parent: mobject to the transform to parent to
    :param prefix: str, the str value to give to the start of the node name
    :param nodeType: str, the node type to convert to. must be a dag type node
    :return: mObject, the mobject of the joint
    """
    jnt = nodes.createDagNode(nodeType, prefix + nodes.nameFromMObject(node, partialName=True), parent=parent)
    plugs.setPlugValue(om2.MFnDagNode(jnt).findPlug("worldMatrix", False), nodes.getWorldMatrix(node))

    return jnt


def convertToSkeleton(rootNode, prefix="skel_", parentObj=None):
    """Converts a hierarchy of nodes into joints that have the same transform,
    with their name prefixed with the "prefix" arg.

    :param rootNode: anything under this node gets converted.
    :type rootNode: :class:`om2.MObject`
    :param prefix: The name to add to the node name .
    :type prefix: str
    :param parentObj: The node to parent to skeleton to.
    :type parentObj: :class:`om2.MObject`
    :return: MObject
    """
    if parentObj is None:
        parentObj = nodes.getParent(rootNode)
    j = convertToNode(rootNode, parentObj, prefix)
    for c in nodes.getChildren(rootNode):
        convertToSkeleton(c, prefix, j)
    return j


def jointLength(joint):
    """Retrieves the length of the child by subtracting the position of the parent joint

    :param joint: The joint to query.
    :type joint: :class:`om2.MObject`
    :return: The length of the joint
    :rtype: float
    """
    jointFn = om2.MFnDagNode(joint)
    parent = jointFn.parent()
    if nodes.isSceneRoot(parent):
        return 0.0
    parentPos = nodes.getTranslation(parent, space=om2.MSpace.kWorld)
    jointPos = nodes.getTranslation(joint, space=om2.MSpace.kWorld)
    return (jointPos - parentPos).length()


def chainLength(start, end):
    """Returns the Total length between the specified start and end joints.

    :param start: The start joint which must be the parent of the specified end.
    :type start: :class:`om2.MObject`
    :param end: The end joint which must be a child of the specified start.
    :type end: :class:`om2.MObject`
    :return: The total length
    :rtype: float
    """
    joints = [end]
    for i in nodes.iterParents(end):
        if i.apiType() == om2.MFn.kJoint:
            joints.append(i)
            if i == start:
                break
    joints.reverse()
    total = 0
    for j in iter(joints):
        total += jointLength(j)

    return total


def jointRoot(node, depthLimit=256):
    """Walks the parent hierarchy starting from the provided node and returns the root joint.

    :param node: The joint to find root from.
    :type node: :class:`om2.MObject` or None
    :param depthLimit: The depth limit to travel before exiting if the root isn't found first. Defaults to 256.
    :type depthLimit: int
    :return: The root joint.
    :rtype: :class:`om2.MObject`
    """
    parent = node
    while parent is not None or parent.apiType() == om2.MFn.kJoint or depthLimit > 1:
        parent = nodes.getParent(parent)
        depthLimit -= 1
    return parent
