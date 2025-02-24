# -*- coding: utf-8 -*-

import math

from maya.api import OpenMaya as om2
from maya import OpenMaya as om1
from zoo.libs.utils import zoomath
from zoovendor.six.moves import range

# MVector for X-axis
XAXIS_VECTOR = om2.MVector(1, 0, 0)
# MVector for Y-axis
YAXIS_VECTOR = om2.MVector(0, 1, 0)
# MVector for Z-axis
ZAXIS_VECTOR = om2.MVector(0, 0, 1)

# Index for X-axis
XAXIS = 0
# Index for Y-axis
YAXIS = 1
# Index for Z-axis
ZAXIS = 2
# Index for -X-axis
NEGXAXIS = 3
# Index for -Y-axis
NEGYAXIS = 4
# Index for -Z-axis
NEGZAXIS = 5

# List of MVector by index
AXIS_VECTOR_BY_IDX = [XAXIS_VECTOR, YAXIS_VECTOR, ZAXIS_VECTOR, XAXIS_VECTOR * -1, YAXIS_VECTOR * -1, ZAXIS_VECTOR * -1]
# List of axis names by index
AXIS_NAME_BY_IDX = ["X", "Y", "Z", "X", "Y", "Z"]
AXIS_IDX_BY_NAME = {"X": 0, "Y": 1, "Z": 2}
AXIS_NAMES = ["X", "Y", "Z"]
MIRROR_PLANE_BY_AXIS = {"x": "yz", "y": "xz", "z": "xy"}
MIRROR_PLANE_INDEX_BY_NAME = {"xy": 0, "yz": 1, "xz": 2}
MIRROR_PLANE_AXIS_BY_INDEX = ["xy", "yz", "xz"]
MIRROR_BEHAVIOUR = 0
MIRROR_RELATIVE = 1
MIRROR_SCALE = 2
MIRROR_ORIENTATION = 3

def axisVectorByIdx(index):
    """Returns the axis vector by index

    :param index: The index of the axis between 0-2
    :type index: int
    :return: The Axis Vector eg. om2.MVector(1,0,0) for 0 index.
    :rtype: :class:`om2.MVector`
    """
    return om2.MVector(AXIS_VECTOR_BY_IDX[index])

def aimToNode(source, target, aimVector=None,
              upVector=None, worldUpVector=None, constrainAxis=om2.MVector(1, 1, 1)):
    """Function to aim one node at another using quaternions.

    :param source: node to aim towards the target node
    :type source: om2.MObject
    :param target: the node which the source will aim at
    :type target: om2.MObject
    :param aimVector: the om2.MVector for the aim axis defaults to om2.MVector(1.0,0.0,0.0)
    :type aimVector: om2.MVector
    :param upVector: the om2.MVector for the upVector axis defaults to om2.MVector(0.0,1.0,0.0)
    :type upVector: om2.MVector
    :param worldUpVector: Alternative World Up Vector.
    :type worldUpVector: :class:`om2.MVector`
    :param constrainAxis: The axis vector to constrain the aim on. ie. om2.MVector(0,1,1) will set X \
    rotation to 0.0. Same deal as mayas aim constraint.

    :type constrainAxis: :class:`om2.MVector`
    """
    targetDag = om2.MDagPath.getAPathTo(target)
    eyeDag = om2.MDagPath.getAPathTo(source)
    transformFn = om2.MFnTransform(eyeDag)
    eyePivotPos = transformFn.rotatePivot(om2.MSpace.kWorld)
    transformFn = om2.MFnTransform(targetDag)
    targetPivotPos = transformFn.rotatePivot(om2.MSpace.kWorld)

    rot = lookAt(eyePivotPos, targetPivotPos, aimVector, upVector, worldUpVector, constrainAxis)
    # align the aim
    transformFn.setObject(eyeDag)
    transformFn.setRotation(rot, om2.MSpace.kWorld)


def lookAt(sourcePosition,
           aimPosition, aimVector=None, upVector=None, worldUpVector=None,
           constrainAxis=om2.MVector(1, 1, 1)):
    """Function to aim one node at another using quaternions.

    :param sourcePosition: source position which acts as the eye.
    :type sourcePosition: :class:`om2.MVector`
    :param aimPosition: The target position to aim at.
    :type aimPosition: :class:`om2.MVector`
    :param aimVector: the om2.MVector for the aim axis defaults to om2.MVector(1.0,0.0,0.0)
    :type aimVector: :class:`om2.MVector`
    :param upVector: the om2.MVector for the upVector axis defaults to om2.MVector(0.0,1.0,0.0)
    :type upVector: :class:`om2.MVector`
    :param worldUpVector: Alternative World Up Vector.
    :type worldUpVector: :class:`om2.MVector`
    :param constrainAxis: The axis vector to constrain the aim on. ie. om2.MVector(0,1,1) will set X \
    rotation to 0.0. Same deal as mayas aim constraint.

    :type constrainAxis: :class:`om2.MVector`
    :rtype: :class:`om2.MQuaternion`

    Scene Node Structure::

                     + (upVector)
                   /
                  /
        (sourcePosition) o------ + (aimVector) (aimPosition)
                  \
                   +

    """
    eyeAim = om2.MVector(aimVector) or XAXIS_VECTOR
    eyeUp = om2.MVector(upVector) or YAXIS_VECTOR
    worldUp = worldUpVector or om1.MGlobal.upAxis()
    eyePivotPos = sourcePosition
    targetPivotPos = aimPosition

    aimVector = targetPivotPos - eyePivotPos
    eyeU = aimVector.normal()
    eyeW = (eyeU ^ om2.MVector(worldUp.x, worldUp.y, worldUp.z)).normal()
    eyeV = eyeW ^ eyeU
    quatU = om2.MQuaternion(eyeAim, eyeU)

    upRotated = eyeUp.rotateBy(quatU)
    try:
        angle = math.acos(zoomath.clamp(upRotated * eyeV, minValue=-1.0, maxValue=1.0))

    except (ZeroDivisionError, ValueError) as er:
        angle = 0.0 if sum(eyeUp) > 0 else -math.pi

    quatV = om2.MQuaternion(angle, eyeU)

    if not eyeV.isEquivalent(upRotated.rotateBy(quatV), 1.0e-5):
        angle = (2 * math.pi) - angle
        quatV = om2.MQuaternion(angle, eyeU)

    quatU *= quatV
    rot = quatU.asEulerRotation()
    if not constrainAxis.x:
        rot.x = 0.0
    if not constrainAxis.y:
        rot.y = 0.0
    if not constrainAxis.z:
        rot.z = 0.0

    return rot.asQuaternion()


def quaterionDot(qa, qb):
    """Computes the dot product of two quaternions.

    :param qa: The first quaternion.
    :type qa: :class:`om2.Quaternion`
    :param qb: The second quaternion.
    :type qb: :class:`om2.Quaternion`
    :return: The dot product of the two quaternions.
    :rtype: float
    """
    return qa.w * qb.w + qa.x * qb.x + qa.y * qb.y + qa.z * qb.z


def slerp(qa, qb, weight):
    """Interpolates between two quaternions using a spherical linear interpolation.

    :param qa: The starting quaternion.
    :type qa: :class:`om2.Quaternion`
    :param qb: The ending quaternion.
    :type qb: :class:`om2.Quaternion`
    :param weight: the weight of the second quaternion in the interpolation
    :type weight: float
    :return: The interpolated quaternion.
    :rtype: :class:`om2.Quaternion`
    """
    qc = om2.MQuaternion()
    dot = quaterionDot(qa, qb)
    if abs(dot >= 1.0):
        qc.w = qa.w
        qc.x = qa.x
        qc.y = qa.y
        qc.z = qa.z
        return qc
    halfTheta = math.acos(dot)
    sinhalfTheta = math.sqrt(1.0 - dot * dot)
    if zoomath.almostEqual(math.fabs(sinhalfTheta), 0.0, 2):
        qc.w = (qa.w * 0.5 + qb.w * 0.5)
        qc.x = (qa.x * 0.5 + qb.x * 0.5)
        qc.y = (qa.y * 0.5 + qb.y * 0.5)
        qc.z = (qa.z * 0.5 + qb.z * 0.5)
        return qc

    ratioA = math.sin((1.0 - weight) * halfTheta) / sinhalfTheta
    ratioB = math.sin(weight * halfTheta) / sinhalfTheta

    qc.w = (qa.w * ratioA + qb.w * ratioB)
    qc.x = (qa.x * ratioA + qb.x * ratioB)
    qc.y = (qa.y * ratioA + qb.y * ratioB)
    qc.z = (qa.z * ratioA + qb.z * ratioB)
    return qc


def toEulerXYZ(rotMatrix, degrees=False):
    """Convert rotation matrix to Euler XYZ angles.

    :param rotMatrix: The rotation matrix to convert.
    :type rotMatrix: :class:`om2.MMatrix`
    :param degrees: A flag to indicate if the output angles should be in degrees or radians
    :type degrees: bool
    :return: The converted Euler XYZ angles
    :rtype: :class:`om2.MEulerRotation`
    """
    rotXZ = rotMatrix[2]
    if zoomath.almostEqual(rotXZ, 1.0, 2):
        z = math.pi
        y = -math.pi * 0.5
        x = -z + math.atan2(-rotMatrix[4], -rotMatrix[7])
    elif zoomath.almostEqual(rotXZ, -1.0, 2):
        z = math.pi
        y = math.pi * 0.5
        x = z + math.atan2(rotMatrix[4], rotMatrix[7])
    else:
        y = -math.asin(rotXZ)
        cosY = math.cos(y)
        x = math.atan2(rotMatrix[6] * cosY, rotMatrix[10] * cosY)
        z = math.atan2(rotMatrix[1] * cosY, rotMatrix[0] * cosY)
    angles = x, y, z
    if degrees:
        return list(map(math.degrees, angles))
    return om2.MEulerRotation(angles)


def toEulerXZY(rotMatrix, degrees=False):
    """Convert rotation matrix to Euler XZY angles.

    :param rotMatrix: The rotation matrix to convert.
    :type rotMatrix: :class:`om2.MMatrix`
    :param degrees: A flag to indicate if the output angles should be in degrees or radians
    :type degrees: bool
    :return: The converted Euler XZY angles
    :rtype: :class:`om2.MEulerRotation`
    """

    rotYY = rotMatrix[1]
    z = math.asin(rotYY)
    cosZ = math.cos(z)

    x = math.atan2(-rotMatrix[9] * cosZ, rotMatrix[5] * cosZ)
    y = math.atan2(-rotMatrix[2] * cosZ, rotMatrix[0] * cosZ)

    angles = x, y, z

    if degrees:
        return list(map(math.degrees, angles))

    return om2.MEulerRotation(angles)


def toEulerYXZ(rotMatrix, degrees=False):
    """Convert rotation matrix to Euler XZY angles.

    :param rotMatrix: The rotation matrix to convert.
    :type rotMatrix: :class:`om2.MMatrix`
    :param degrees: A flag to indicate if the output angles should be in degrees or radians
    :type degrees: bool
    :return: The converted Euler XZY angles
    :rtype: :class:`om2.MEulerRotation`
    """
    rotZ = rotMatrix[6]
    x = math.asin(rotZ)
    cosX = math.cos(x)

    y = math.atan2(-rotMatrix[2] * cosX, rotMatrix[10] * cosX)
    z = math.atan2(-rotMatrix[4] * cosX, rotMatrix[5] * cosX)

    angles = x, y, z

    if degrees:
        return list(map(math.degrees, angles))

    return om2.MEulerRotation(angles)


def toEulerYZX(rotMatrix, degrees=False):
    """Convert rotation matrix to Euler YZX angles.

    :param rotMatrix: The rotation matrix to convert.
    :type rotMatrix: :class:`om2.MMatrix`
    :param degrees: A flag to indicate if the output angles should be in degrees or radians
    :type degrees: bool
    :return: The converted Euler YZX angles
    :rtype: :class:`om2.MEulerRotation`
    """
    rotYX = rotMatrix[4]
    z = -math.asin(rotYX)
    cosZ = math.cos(z)

    x = math.atan2(rotMatrix[6] * cosZ, rotMatrix[5] * cosZ)
    y = math.atan2(rotMatrix[8] * cosZ, rotMatrix[0] * cosZ)

    angles = x, y, z

    if degrees:
        return list(map(math.degrees, angles))

    return om2.MEulerRotation(angles)


def toEulerZXY(rotMatrix, degrees=False):
    """Convert rotation matrix to Euler ZXY angles.

    :param rotMatrix: The rotation matrix to convert.
    :type rotMatrix: :class:`om2.MMatrix`
    :param degrees: A flag to indicate if the output angles should be in degrees or radians
    :type degrees: bool
    :return: The converted Euler ZXY angles
    :rtype: :class:`om2.MEulerRotation`
    """
    rotZY = rotMatrix[9]
    x = -math.asin(rotZY)
    cosX = math.cos(x)

    z = math.atan2(rotMatrix[1] * cosX, rotMatrix[5] * cosX)
    y = math.atan2(rotMatrix[8] * cosX, rotMatrix[10] * cosX)

    angles = x, y, z

    if degrees:
        return list(map(math.degrees, angles))

    return om2.MEulerRotation(angles)


def toEulerZYX(rotMatrix, degrees=False):
    """Convert rotation matrix to Euler ZYX angles.

    :param rotMatrix: The rotation matrix to convert.
    :type rotMatrix: :class:`om2.MMatrix`
    :param degrees: A flag to indicate if the output angles should be in degrees or radians
    :type degrees: bool
    :return: The converted Euler ZYX angles
    :rtype: :class:`om2.MEulerRotation`
    """

    rotZX = rotMatrix[8]
    y = math.asin(rotZX)
    cosY = math.cos(y)

    x = math.atan2(-rotMatrix[9] * cosY, rotMatrix[10] * cosY)
    z = math.atan2(-rotMatrix[4] * cosY, rotMatrix[0] * cosY)

    angles = x, y, z

    if degrees:
        return list(map(math.degrees, angles))

    return om2.MEulerRotation(angles)


def toEulerFactory(rotMatrix, rotateOrder, degrees=False):
    """A factory function that returns the corresponding euler angles based on the provided rotate order.

   :param rotMatrix: The rotation matrix to convert.
   :type rotMatrix: :class:`om2.MMatrix`
   :param rotateOrder: The order of rotation for the euler angles. Can be one of\
   (kXYZ, kXZY, kYXZ, kYZX, kZXY, kZYX)
   :type rotateOrder: om2.MTransformationMatrix.kXYZ
   :param degrees: A flag to indicate if the output angles should be in degrees or radians
   :type degrees: bool
   :return: The converted Euler angles
   :rtype: :class:`om2.MEulerRotation`
   """
    if rotateOrder == om2.MTransformationMatrix.kXYZ:
        return toEulerXYZ(rotMatrix, degrees)
    elif rotateOrder == om2.MTransformationMatrix.kXZY:
        return toEulerXZY(rotMatrix, degrees)
    elif rotateOrder == om2.MTransformationMatrix.kYXZ:
        return toEulerYXZ(rotMatrix, degrees)
    elif rotateOrder == om2.MTransformationMatrix.kYZX:
        return toEulerYZX(rotMatrix, degrees)
    elif rotateOrder == om2.MTransformationMatrix.kZXY:
        return toEulerZXY(rotMatrix, degrees)
    return toEulerZYX(rotMatrix, degrees)


def mirrorXY(rotationMatrix):
    """Mirror a rotation matrix on the XY plane.

    :param rotationMatrix: the rotation matrix to mirror
    :type rotationMatrix: :class:`om2.MMatrix`
    :return: the mirrored rotation matrix
    :rtype: :class:`om2.MMatrix`
    """
    rotMat = om2.MMatrix(rotationMatrix)
    rotMat[0] *= -1
    rotMat[1] *= -1
    rotMat[4] *= -1
    rotMat[5] *= -1
    rotMat[8] *= -1
    rotMat[9] *= -1
    return rotMat


def mirrorYZ(rotationMatrix):
    """Mirror a rotation matrix on the YZ plane.

    :param rotationMatrix: the rotation matrix to mirror
    :type rotationMatrix: :class:`om2.MMatrix`
    :return: the mirrored rotation matrix
    :rtype: :class:`om2.MMatrix`
    """
    rotMat = om2.MMatrix(rotationMatrix)
    rotMat[1] *= -1
    rotMat[2] *= -1
    rotMat[5] *= -1
    rotMat[6] *= -1
    rotMat[9] *= -1
    rotMat[10] *= -1
    return rotMat


def mirrorXZ(rotationMatrix):
    """Mirror a rotation matrix on the XZ plane.

    :param rotationMatrix: the rotation matrix to mirror
    :type rotationMatrix: :class:`om2.MMatrix`
    :return: the mirrored rotation matrix
    :rtype: :class:`om2.MMatrix`
    """
    rotMat = om2.MMatrix(rotationMatrix)
    rotMat[0] *= -1
    rotMat[2] *= -1
    rotMat[4] *= -1
    rotMat[6] *= -1
    rotMat[8] *= -1
    rotMat[10] *= -1
    return rotMat


def angleBetween3Points(a, b, c):
    """Compute the angle between three points in degrees.

    :param a: The first point
    :type a: :class:`om2.Vector`
    :param b: The second point
    :type b: :class:`om2.Vector`
    :param c: The third point
    :type c: :class:`om2.Vector`
    :return: The angle between the three points
    :rtype: float
    """
    return math.degrees((b - a).normalize().angle((c - b).normalize()))

def angleBetween3PointsRadians(a, b, c):
    """Compute the angle between three points in radians.

    :param a: The first point
    :type a: :class:`om2.Vector`
    :param b: The second point
    :type b: :class:`om2.Vector`
    :param c: The third point
    :type c: :class:`om2.Vector`
    :return: The angle between the three points
    :rtype: float
    """
    return (b - a).normalize().angle((c - b).normalize())

def evenLinearPointDistribution(start, end, count):
    """Generator function which evenly distributes points along
    a straight line.

    Each returned point is the vector.

    :param start: The start vector
    :type start: :class:`zapi.Vector`
    :param end: The end vector
    :type end: :class:`zapi.Vector`
    :param count: the number of points to distribute
    :type count: int
    :return: The distributed vector
    :rtype: :class:`zapi.Vector`
    """
    directionVector = end - start
    fraction = directionVector.normal().length() / (count + 1)
    for n in range(1, count + 1):
        multiplier = fraction * n
        pos = start + (directionVector * multiplier)
        yield om2.MVector(pos), multiplier


def firstLastOffsetLinearPointDistribution(start, end, count, offset):
    """Same behaviour as :func:`evenLinearPointDistribution` but offsets
    the first and last point by the 'offset value'

    Each returned point is the vector.

    :param start: The start vector
    :type start: :class:`zapi.Vector`
    :param end: The end vector
    :type end: :class:`zapi.Vector`
    :param count: the number of points to distribute
    :type count: int
    :param offset: The value to offset the first and last points. \
    The offset is calculated from the fraction(direction*(fraction*offset))
    :return: The distributed vector
    :rtype: tuple[:class:`zapi.Vector`, float]
    """
    directionVector = end - start
    length = directionVector.normal().length()
    firstLastFraction = length / (count + 1)
    primaryFraction = length / (count - 1)
    multiplier = firstLastFraction * offset
    yield start + (directionVector * multiplier), multiplier

    for n in range(count - 2):
        multiplier = primaryFraction * (n + 1)
        pos = start + (directionVector * multiplier)
        yield pos, multiplier

    multiplier = 1.0 - firstLastFraction * offset
    yield start + (directionVector * multiplier), multiplier


def averagePosition(nodes):
    """Returns the average position on all provided nodes in workspace.

    :param nodes:
    :type nodes: list[:class:`zapi.DagNode`]
    :return:
    :rtype: :class:`om2.MVector`
    """
    count = len(nodes)

    # To avoid ZeroDivisionError  where the count is 0
    if count == 0:
        raise ValueError("Invalid number of nodes, must be above 0: provided: {}".format(count))

    center = om2.MVector()
    for i in nodes:
        center += i.translation(space=om2.MSpace.kWorld)
    center /= count
    return center


def averageNormalVector(nodes, axis):
    """Computes and returns the averaged normal based on the provided nodes rotations.

    :param nodes: The nodes to average
    :type nodes: list[:class:`zoo.libs.maya.zapi.DagNode`]
    :param axis: The axis to rotate around ie. om2.MVector(1,0,0)
    :type axis: :class:`om2.MVector`
    :return: The normalized averaged rotations as a vector.
    :rtype: :class:`om2.MVector`
    """
    upAxis = om1.MGlobal.upAxis()
    average = om2.MVector(upAxis.x, upAxis.y, upAxis.z)
    for node in nodes:
        worldOrient = node.rotation(space=om2.MSpace.kWorld)
        rotation = axis.rotateBy(worldOrient.asEulerRotation())
        average.x += rotation.x
        average.y += rotation.y
        average.z += rotation.z
    average.normalize()
    if average.x == 0 and average.y == 0 and average.z == 0:
        average.x = 1
    return average


def twoPointNormal(pointA, pointB, normal):
    """Based on two points and an additional normal vector return the plane normal.


    :param pointA: First Vector
    :type pointA: :class:`om2.MVector`
    :param pointB: Second Vector
    :type pointB: :class:`om2.MVector`
    :param normal: Additional normal which will be crossed with the distance vector
    :type normal: :class:`om2.MVector`
    :return: Plane Normal
    :rtype: :class:`om2.MVector`
    """
    lineVec = pointB - pointA

    # find the normal between the line formed by 2 points and the passed in normal
    firstNorm = (normal ^ lineVec).normalize()

    # now the cross between the line and firstNorm is the result
    return (firstNorm ^ lineVec).normalize()


def threePointNormal(pointA, pointB, pointC):
    """Same As :func:`twoPointNormal` but for three points.

    :param pointA: First Vector
    :type pointA: :class:`om2.MVector`
    :param pointB: Second Vector
    :type pointB: :class:`om2.MVector`
    :param pointC: Third Vector
    :type pointC: :class:`om2.MVector`
    :return: Normalized vector from three points
    :rtype: :class:`om2.MVector`
    """
    return ((pointC - pointB) ^ (pointB - pointA)).normalize()


def closestPointOnPlane(point, plane):
    """Returns the closet point on the given Plane(projecting the point on the plane).

    :param point: The point to project on to the plane.
    :type point: :class:`om2.MVector`
    :param plane: The plane instance to get the closest point.
    :type plane: :class:`om2.MPlane`
    :return: The closest point.
    :rtype: :class:`om2.MVector`
    """
    return point - (plane.normal() * plane.distanceToPoint(point, signed=True))


def indexOfLargest(iterable):
    """Returns the index of the largest absolute valued component in an iterable.

    :param iterable: An iterable of floating point values to search.
    :type iterable: iterable
    :rtype: int
    """
    iterable = [(x, n) for n, x in enumerate(map(abs, iterable))]
    iterable.sort()

    return iterable[-1][1]


def axisInDirection(matrix, compareVector, defaultAxis):
    """Returns the axis in integer form  0, 1, 2, 3, 4, 5

    0-2 is positive x,y,z while 3,4,5 is negative x,y,z

    The defaultAxis is returned if the compareVector is zero or too small to provide
    meaningful directionality.

    :param matrix: The source matrix
    :type matrix: :class:`om2.MMatrix`
    :param compareVector: the direction vector to compare the matrix to. ie. zapi.Vector(0,0,1)
    :type compareVector: :class:`om2.MVector`
    :param defaultAxis: The default axis index to use when ZeroDivisionError is raised
    :type defaultAxis: int
    :rtype: int
    """

    xPrime, yPrime, zPrime = basisVectorsFromMatrix(matrix)
    compareVector.normalize()
    try:
        dots = compareVector * xPrime.normalize(), compareVector * yPrime.normalize(), compareVector * zPrime.normalize(),
    except ZeroDivisionError:
        return defaultAxis
    idx = indexOfLargest(dots)
    if dots[idx] < 0:
        idx += 3
    return idx


def basisVectorsFromMatrix(matrix):
    """Returns 3  orthonormal basis vectors that represent the orientation of the given object.

    :param matrix: The matrix to return the orthonormal basis from
    :type matrix: :class:`om2.MMatrix`
    :rtype matrix: tuple[:class:`om2.MVector`, :class:`om2.MVector`, :class:`om2.MVector`]
    """
    return om2.MVector(matrix[0], matrix[1], matrix[2]), \
        om2.MVector(matrix[4], matrix[5], matrix[6]), \
        om2.MVector(matrix[8], matrix[9], matrix[10])

def basisXVectorFromMatrix(matrix):
    """Returns X  orthonormal basis vectors that represent the X rotation axis vector.

    :param matrix: The matrix to return the orthonormal basis from
    :type matrix: :class:`om2.MMatrix`
    :rtype matrix: :class:`om2.MVector`
    """
    return om2.MVector(matrix[0], matrix[1], matrix[2])

def basisYVectorFromMatrix(matrix):
    """Returns Y  orthonormal basis vectors that represent the X rotation axis vector.

    :param matrix: The matrix to return the orthonormal basis from
    :type matrix: :class:`om2.MMatrix`
    :rtype matrix: :class:`om2.MVector`
    """
    return om2.MVector(matrix[4], matrix[5], matrix[6])

def basisZVectorFromMatrix(matrix):
    """Returns Z  orthonormal basis vectors that represent the X rotation axis vector.

    :param matrix: The matrix to return the orthonormal basis from
    :type matrix: :class:`om2.MMatrix`
    :rtype matrix: :class:`om2.MVector`
    """
    return om2.MVector(matrix[8], matrix[9], matrix[10])

def alignToWorldAxis(matrix, rotationAxis=YAXIS, forwardAxis=ZAXIS_VECTOR, defaultAxisDirection=ZAXIS):
    """Returns the minimal viable single axis rotation to align to the forward axis.

    :param matrix: The reference Matrix to pull the rotation from commonly this is the worldMatrix
    :type matrix: :class:`om2.MMatrix`
    :param rotationAxis: The axis to rotate on. Defaults to `YAXIS`
    :type rotationAxis: int
    :param forwardAxis: The forward vector representing the axis, defaults to `ZAXIS_VECTOR`
    :type forwardAxis: :class:`om2.MVector`
    :param defaultAxisDirection: The default forwardAxis to use when a ZeroDivisionError occurs.
    :type defaultAxisDirection:  int
    :rtype: :class:` om2.MEulerRotation`
    """
    fwdAxis = axisInDirection(matrix, forwardAxis, defaultAxisDirection)
    basisVectors = basisVectorsFromMatrix(matrix)
    fwdVector = basisVectors[fwdAxis % 3]  # type: om2.MVector
    direction = -1 if fwdAxis > ZAXIS else 1
    fwdVector[rotationAxis] = 0.0
    fwdVector = fwdVector.normalize() * direction

    angle = fwdVector * forwardAxis
    angle = math.degrees(math.acos(angle)) * direction
    rot = om2.MEulerRotation()
    rot[rotationAxis] = math.radians(angle)
    return rot


def perpendicularAxisFromAlignVectors(aimVector, upVector):
    """Given an aim and up vector return which axis isn't being used and determine
    whether to get positive values from an incoming attribute whether it needs to be
    negated.

    ..  code-block:: python

        result = driverAxisFromAimUpVectors(om2.MVector(1,0,0), om2.MVector(0,1,0))
        # (2, True)  # 2 is the axis number therefore Z


    :param aimVector:
    :type aimVector:
    :param upVector:
    :type upVector:
    :return:
    :rtype: tuple[int, bool]
    """
    perpendicularVector = om2.MVector(aimVector) ^ om2.MVector(upVector)
    axisIndex = ZAXIS  # default to Z axis as that's the most common
    isNegative = isVectorNegative(perpendicularVector)

    for axisIndex, value in enumerate(perpendicularVector):
        if int(value) != 0:
            break

    return axisIndex, isNegative


def isVectorNegative(vector):
    """Whether the sum of the vector(x+y+z) is less then 0.0
    :param vector:
    :return:
    """
    return sum(vector) < 0.0


def primaryAxisNameFromVector(vector):
    """Internal function which returns the string name of the vector ie. X,Y,Z

    :param vector: The vector to check
    :type vector: :class:`zapi.Vector` or tuple
    :return: Vector Axis Name ie . X, Y or Z
    :rtype: str
    """
    if vector[0] != 0.0:
        return "X"
    elif vector[1] != 0.0:
        return "Y"
    return "Z"


def primaryAxisIndexFromVector(vector):
    """Internal function which returns the string name of the vector ie. X,Y,Z

    :param vector: The vector to check
    :type vector: :class:`zapi.Vector` or tuple
    :return: Vector Axis index
    :rtype: int
    """
    if vector[0] != 0.0:
        return 0
    elif vector[1] != 0.0:
        return 1
    return 2


def nonPrimaryAxisNamesFromVector(vector):
    """Given a vector, returns a list of the non-primary axes.
    The primary axis is the one with the largest absolute value.

    :param vector: The input vector.
    :type vector: :class:`om2.MVector`
    :return: List of non-primary axis names
    :rtype: list
    """
    primaryAxis = primaryAxisNameFromVector(vector)
    return {
        "X": ["Y", "Z"],
        "Y": ["X", "Z"],
        "Z": ["X", "Y"]
    }.get(primaryAxis)


def convertToSceneUnits(value):
    """Converts the value to the current maya scene UI unit. ie. meters, inches.

    .. note::
        Only current supports meters, inches and feet

    :param value: value to convert to the scene units.
    :type value: float or int or :class:`om2.MVector`
    :return: The newly converted value.
    :rtype: float or int or :class:`om2.MVector`
    """
    sceneUnits = om2.MDistance.uiUnit()
    if sceneUnits == om2.MDistance.kMeters:
        return value / 100.0
    elif sceneUnits == om2.MDistance.kInches:
        return value / 2.54
    elif sceneUnits == om2.MDistance.kFeet:
        return value / 30.48
    return value


def convertFromSceneUnits(value):
    """Converts the value from the current maya scene UI unit back to centimeters. ie. meters to cms, inches.

    .. note::
        Only current supports meters, inches and feet

    :param value: value to convert to the scene units.
    :type value: float or int or :class:`om2.MVector`
    :return: The newly converted value.
    :rtype: float or int or :class:`om2.MVector`
    """
    sceneUnits = om2.MDistance.uiUnit()
    if sceneUnits == om2.MDistance.kMeters:
        return value * 100.0
    elif sceneUnits == om2.MDistance.kInches:
        return value * 2.54
    elif sceneUnits == om2.MDistance.kFeet:
        return value * 30.48
    return value


def bezierGroups(values):
    """Groups a list of values into bezier chunks where the first and last tangents are two points and the middles
    are three points.

    :param values:
    :type values: list[list[]]

    my_list = [0, 1, 2, 3, 4, 5, 6]
    my_list = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    result = bezierChunks(my_list)
    print(result)
    #[[0, 1], [2, 3, 4], [5, 6, 7], [7, 8]]
    """
    chunks = []

    if len(values) <= 4:
        return [values[:2], values[2:]]

    chunks.append(values[:2])

    for i in range(2, len(values) - 2, 3):
        chunks.append(values[i:i + 3])

    chunks.append(values[-2:])

    return chunks

def bezierSections(values):
    """Groups a list of values into bezier chunks where the first and last tangents are two points and the middles
    are three points.

    :param values:
    :type values: list[list[]]

    my_list = [0, 1, 2, 3, 4, 5, 6]
    my_list = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    result = bezierChunks(my_list)
    print(result)
    #[[0, 1], [2, 3, 4], [5, 6, 7], [7, 8]]
    """
    chunks = []

    if len(values) <= 4:
        return [values[:2], values[2:]]

    chunks.append(values[:2])

    for i in range(2, len(values) - 2, 3):
        chunks.append(values[i:i + 3])

    chunks.append(values[-2:])

    return chunks


def bezierSegments(points):
    """Splits the points into bezier segments of 4 points each.

    :param points: List of values which represent cv points, this function only operates on the length on the \
    list provided and the values are returned.
    :type points: list[any]
    :return: List of curve segments formed by the Bezier curve. Each segment is represented as a list of control points.
    :rtype: list[list[any]]
    """
    results = []
    lastIndex = 0
    for i in range(len(points)):
        if i == 0:
            continue
        if (i % 3) == 0:
            results.append(points[lastIndex:i+1])
            lastIndex = i
    return results
