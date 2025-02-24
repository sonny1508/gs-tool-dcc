import math

from zoo.libs.maya.utils import mayamath
from zoo.libs.maya import zapi
from maya.api import OpenMaya as om2

TWO_POINT_NORMAL = 0
THREE_POINT_NORMAL = 1


def createPolyPlaneFromPlane(name, plane, position=None, template=True, **kwargs):
    """Creates a PolyPlane based on the provided MPlane and position.

    .. code-block:: python

        name="testPlane"
        plane = om2.MPlane()
        plane.setPlane(om2.MVector(0,1,0), 10)
        mesh = createPolyPlaneFromPlane(name, plane)

    :param name: The name for the polyPlane
    :type name: str
    :param plane: The MPlane instance
    :type plane: :class:`om2.MPlane`
    :param position: if None then the position we be the center point of the MPlane.
    :type position: :class:`zapi.Vector`
    :param template: Sets the state of the template draw mode of the plane
    :type template: bool
    :return: The Transform of the created polyPlane
    :rtype: :class:`zapi.DagNode`
    """
    rotation = planeNormalToRotation(position or zapi.Vector(), plane)
    mesh = zapi.createPolyPlane(name, createUVs=False, constructionHistory=False, **kwargs)[0]
    if position:
        mesh.setTranslation(position)
    mesh.setRotation(rotation)
    mesh.template.set(int(template))
    return mesh


def constructPlaneFromPositions(positionVectors, nodes, rotateAxis=mayamath.ZAXIS_VECTOR):
    """Constructs a MPlane instance based on the averaged normal of the nodes rotations.

    :param positionVectors: either a list of 3 vectors for a 3 point normal or 2 vectors
    :type positionVectors: list[:class:`om2.MVector`, :class:`om2.MVector`, :class:`om2.MVector`]
    :param nodes: a list of nodes which will have their rotations read to attempt to figure out the best normal \
    direction  e.g. uses the rotation to flip the normal.
    :type nodes: list[:class:`DagNode`]
    :return: The construct plane based on the provided points
    :rtype: :class:`om2.MPlane`
    """
    planeA = om2.MPlane()
    norm = om2.MVector(om2.MVector.kXaxisVector)
    if len(positionVectors) == 3:
        norm = mayamath.threePointNormal(*positionVectors)

    elif len(positionVectors) > 3:
        averagePos = mayamath.averagePosition(nodes)

        norm = mayamath.threePointNormal(nodes[0].translation(space=zapi.kWorldSpace),
                                         averagePos,
                                         nodes[-1].translation(space=zapi.kWorldSpace))
    else:
        # Calculate Plane Normal
        for i in range(len(positionVectors)):
            curr = zapi.Vector(positionVectors[i][0], positionVectors[i][1], positionVectors[i][2])
            prev = zapi.Vector(positionVectors[i - 1][0], positionVectors[i - 1][1], positionVectors[i - 1][2])
            norm += zapi.Vector((prev.z + curr.z) * (prev.y - curr.y),
                                (prev.x + curr.x) * (prev.z - curr.z),
                                (prev.y + curr.y) * (prev.x - curr.x))
        # Normalize result
        norm.normalize()
    averageNormal = mayamath.averageNormalVector(nodes, rotateAxis)

    if norm * averageNormal < 0:
        norm *= -1
    planeA.setPlane(norm, -norm * positionVectors[0])
    return planeA


def alignNodesIterator(nodes, plane, skipEnd=True):
    """Generator function that loops each node protects it's position in the world and returns
    each node, and it's target.

    This functions will handle setting translations while compensating for hierarchy state.
    The order of returned nodes will be in reverse(from child -> parent) of the provide list.

    .. code-block:: python

        nodes = list(zapi.selected()) # in this example we're expecting to use 3 nodes only
        currentPositions = [i.translation(space=zapi.kWorldSpace) for i in nodes]
        plane = constructPlaneFromNodes(currentPositions)
        for node, target in alignNodesIterator(nodes, plane):
            # do something ie. custom alignment

    :param nodes: The list of nodes to align
    :type nodes: list[:class:`zapi.DagNode`]
    :param plane: The MPlane where each node will be protected on too.
    :type plane: :class:`om2.MPlane`
    :return: first element is the node to set alignment, second element is the target node
    :rtype: generator[:class:`zapi.DagNode`, :class:`zapi.DagNode`]
    """
    nodeArray = nodes[:-1] if skipEnd else nodes  # skip the end node

    childMap = {}
    changeMap = []
    lastIndex = len(nodeArray) - 1
    # we need to first unparent everything(we'll reparent at the end) so we can change the positions and orientations
    for index, currentNode in enumerate(reversed(nodeArray)):
        children = currentNode.children((zapi.kNodeTypes.kTransform, zapi.kNodeTypes.kJoint))
        childMap[currentNode] = children
        for child in children:
            child.setParent(None)
    # now we update all positions and orientations
    for index, currentNode in enumerate(nodeArray):
        translation = currentNode.translation(space=zapi.kWorldSpace)
        if index == lastIndex:

            targetNode = nodes[index + 1] if skipEnd else None
            newTranslation = translation if skipEnd else mayamath.closestPointOnPlane(translation, plane)
        else:
            targetNode = nodes[index + 1]
            # re position the node to ensure it's on the plane
            newTranslation = mayamath.closestPointOnPlane(translation, plane)
        currentNode.setTranslation(newTranslation, space=zapi.kWorldSpace)
        changeMap.append((currentNode, targetNode, newTranslation))

    # now yield so the client can do whatever  i.e. align, then reparent back together
    for currentNode, targetNode, newTranslation in changeMap:
        yield currentNode, targetNode
        for child in childMap[currentNode]:
            child.setParent(currentNode)


def orientNodesIterator(nodes):
    """Generator function that loops each node, and it's target.

    :type nodes: list[:class:`zapi.DagNode`]
    :return: first element is the node to set alignment, second element is the target node
    :rtype: generator[:class:`zapi.DagNode`, :class:`zapi.DagNode`]
    """
    childMap = {}
    changeMap = []
    # we need to first unparent everything(we'll reparent at the end) so we can change the positions and orientations
    for index, currentNode in enumerate(reversed(nodes)):
        children = currentNode.children((zapi.kNodeTypes.kTransform, zapi.kNodeTypes.kJoint))
        childMap[currentNode] = children
        for child in children:
            child.setParent(None)

    # now we update all positions and orientations
    lastIndex = len(nodes) - 1
    for index, currentNode in enumerate(nodes):
        if not childMap[currentNode] or index == lastIndex:
            targetNode = None
        else:
            targetNode = nodes[index + 1]
        changeMap.append((currentNode, targetNode))
    # now yield so the client can do whatever  i.e. align, then re-parent back together
    for currentNode, targetNode in changeMap:
        yield currentNode, targetNode
        for child in childMap[currentNode]:
            child.setParent(currentNode)


def alignHierarchy(start, end, plane, primaryAxis, secondaryAxis):
    """ Aligns and positions every node between start and end so they sit on the plane.


    :param start: The start node .
    :type start: :class:`zapi.DagNode`
    :param end: The end node.
    :type end: :class:`zapi.DagNode`
    :param plane: The calculated Plane to align all nodes too.
    :type plane: :class:`om2.MPlane`
    :param primaryAxis: The primary(aim) axis for each node.
    :type primaryAxis: :class:`om2.MVector`
    :param secondaryAxis: The Secondary vector for all the nodes in the chain.
    :type secondaryAxis: :class:`om2.MVector`
    """
    # we work in reverse order
    currentJoint = end
    startParent = start.parent()
    nodeChain = []
    while currentJoint != startParent:
        currentJointParent = currentJoint.parent()
        nodeChain.insert(0, currentJoint)
        currentJoint = currentJointParent
    projectAndOrientNodes(nodeChain, plane, primaryAxis, secondaryAxis)


def projectAndOrientNodes(nodes, plane, primaryAxis, secondaryAxis, skipEnd=True):
    """Given the provided nodes each node will be protected on to the plane
    and have its rotations aligned.

    For the sake of flexibly in how to apply the rotations depending on
    client workflow and node types, all rotations will be applied directly to
    the world rotations , for joints their joint orient will be reset to zero.


    :param nodes: The full list of nodes from parent to child.
    :type nodes: list[:class:`zapi.DagNode`]
    :param plane: The calculated Plane to align all nodes too.
    :type plane: :class:`om2.MPlane`
    :param primaryAxis: The primary(aim) axis for each node.
    :type primaryAxis: :class:`om2.MVector`
    :param secondaryAxis: The Secondary vector for all the nodes in the chain.
    :type secondaryAxis: :class:`om2.MVector`
    :param skipEnd: If True the last node will not be aligned.
    :type skipEnd: bool
    """
    joints = []
    # first position all nodes to new locations then in the last loop create to the new rotations
    for currentNode, targetNode in alignNodesIterator(nodes, plane, skipEnd=skipEnd):
        if skipEnd and targetNode is None:
            continue
        # joints have to be handled differently when resetting to zero as
        # we need to include the jointOrient... eek.
        if currentNode.object().hasFn(zapi.kNodeTypes.kJoint):
            # zero out the joint as it's the end joint with no children
            currentNode.setRotation(zapi.EulerRotation(), zapi.kTransformSpace)
            currentNode.setScale(zapi.Vector(1.0, 1.0, 1.0))
            currentNode.jointOrient.set(zapi.Vector())
            currentNode.rotateAxis.set(zapi.Vector())
        if targetNode is None:
            currentNode.resetTransform(translate=False, scale=False, rotate=True)
            continue
        rot = mayamath.lookAt(currentNode.translation(space=zapi.kWorldSpace),
                              targetNode.translation(space=zapi.kWorldSpace),
                              aimVector=primaryAxis,
                              upVector=secondaryAxis,
                              worldUpVector=plane.normal())
        if currentNode.object().hasFn(zapi.kNodeTypes.kJoint):
            currentNode.setRotation(rot, space=zapi.kWorldSpace)
            joints.append(currentNode)
        else:
            currentNode.setRotation(rot, space=zapi.kWorldSpace)


def orientNodes(nodes, primaryAxis, secondaryAxis, worldUpAxis, skipEnd=True):
    """Given the provided nodes each node will be aligned to the next in the list

    For the sake of flexibly in how to apply the rotations depending on
    client workflow and node types, all rotations will be applied directly to
    the world rotations , for joints their joint orient will be reset to zero.


    :param nodes: The full list of nodes from parent to child.
    :type nodes: list[:class:`zapi.DagNode`]
    :param worldUpAxis: The calculated Plane to align all nodes too.
    :type worldUpAxis: :class:`om2.MVector`
    :param primaryAxis: The primary(aim) axis for each node.
    :type primaryAxis: :class:`om2.MVector`
    :param secondaryAxis: The Secondary vector for all the nodes in the chain.
    :type secondaryAxis: :class:`om2.MVector`
    :param skipEnd: If True the last node will not be aligned.
    :type skipEnd: bool
    """
    joints = []
    # first position all nodes to new locations then in the last loop create to the new rotations
    for currentNode, targetNode in orientNodesIterator(nodes):
        if skipEnd and targetNode is None:
            continue
        # joints have to be handled differently when resetting to zero as
        # we need to include the jointOrient... eek.
        if currentNode.object().hasFn(zapi.kNodeTypes.kJoint):
            # zero out the joint as it's the end joint with no children
            currentNode.setRotation(zapi.EulerRotation(), zapi.kTransformSpace)
            currentNode.jointOrient.set(zapi.Vector())
            currentNode.rotateAxis.set(zapi.Vector())
            currentNode.setScale(zapi.Vector(1.0, 1.0, 1.0))

        if targetNode is None:
            currentNode.resetTransform(translate=False, scale=False, rotate=True)
            continue
        rot = mayamath.lookAt(currentNode.translation(space=zapi.kWorldSpace),
                              targetNode.translation(space=zapi.kWorldSpace),
                              aimVector=primaryAxis,
                              upVector=secondaryAxis,
                              worldUpVector=worldUpAxis)
        if currentNode.object().hasFn(zapi.kNodeTypes.kJoint):
            currentNode.setRotation(rot, space=zapi.kWorldSpace)
            joints.append(currentNode)
        else:
            currentNode.setRotation(rot, space=zapi.kWorldSpace)


def worldAxisToRotation(axis, invert=False, rotateOrder=zapi.kRotateOrder_XYZ):
    """ Given an axis, return the world rotation to align to that axis.

    :param axis: Axis index to align to e.g. mayamath.XAXIS
    :type axis: int
    :param invert: Whether to invert the rotation.
    :type invert: bool
    :param rotateOrder: The rotation order to use. e.g. zapi.kRotateOrder_XYZ
    :type rotateOrder: int
    :return: The world rotation to align to the axis.
    :rtype: :class:`zapi.EulerRotation`
    """
    normalDir = zapi.Vector()
    degree90 = math.pi * 0.5
    if axis == mayamath.XAXIS:
        # -90 points down X hence reversed logic
        normalDir[2] = -degree90 if not invert else degree90
    # positive Y is just 0 all axis but flip 180 if invert
    elif axis == mayamath.YAXIS and invert:
        normalDir[0] = math.pi
    elif axis == mayamath.ZAXIS:
        # -90 points down Z hence reversed logic
        normalDir[0] = degree90 if not invert else -degree90

    return zapi.EulerRotation(normalDir, rotateOrder)


def planeNormalToRotation(sourcePosition, plane):
    """ Given a source position and a plane, return the world rotation to align to that plane.

    :param sourcePosition: The source position to align to the plane.
    :type sourcePosition: :class:`zapi.Vector`
    :param plane: The plane to align to.
    :type plane: :class:`zapi.Plane`
    :return: The worldRotation which aligns to the plane.
    :rtype: :class:`zapi.EulerRotation`
    """
    aimPos = sourcePosition + plane.normal()
    return mayamath.lookAt(sourcePosition, aimPos, zapi.Vector(0, 1, 0), zapi.Vector(1, 0, 0), zapi.Vector(0, 0, 1))


def matrixToPlane(matrix):
    """Given a world matrix this extracts the Y rotation and returns a MPlane.

    :param matrix: The world matrix to extract the rotation from.
    :type matrix: :class:`zapi.Vector`
    :return: The plane from the matrix.
    :rtype: :class:`zapi.Plane`
    """
    normal = zapi.Vector(matrix[4], matrix[5], matrix[6]).normalize()
    distance = -normal * zapi.Vector(matrix[-4], matrix[-3], matrix[-2])
    return zapi.Plane().setPlane(normal, distance)
