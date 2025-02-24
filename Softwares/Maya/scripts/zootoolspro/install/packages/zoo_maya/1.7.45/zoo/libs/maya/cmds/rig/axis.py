import maya.cmds as cmds

from zoo.libs.maya.cmds.objutils import scaleutils


def clampSmallValues(val, clampAmount=0.001):
    """Clamps stupidly small values such as 4.072996551253769e-15 and returns 0.0

    :param val: float value
    :type val: float
    :param clampAmount: tolerance of the small number
    :type clampAmount: float
    :return newValue: new value potentially clamped
    :rtype newValue: float
    """
    if not val == 0.0:
        if val > -clampAmount and val < clampAmount:
            return 0.0
    return val


def rangeDifferenceFloat(floatList):
    """Returns the range between the max and min values of a float list

    Example:

        [1.0, -1.0, 2.0]
        Returns 3.0

    :param floatList: A list of floats
    :type floatList: list(float)
    :return rangeValue: The difference between the highest and lowest numbers
    :rtype rangeValue: float
    """
    floatList.sort()
    return clampSmallValues(floatList[-1]) - clampSmallValues(floatList[0])


def rangeDifferenceXYZ(XYZList):
    """Gets the range values, distance between high and low) for an XYZ float list, could be RGB

    Example:

        [1.0, -10.0, 2.0], [-1.0, -1.0, 2.0], [2.0, 20.0, 2.0]
        Returns [3.0, 20.0, 0.0]

    :param XYZList: list of XYZ floats
    :type XYZList: list(list(float)))
    :return rangeList: the XYZ list now with range difference values
    :rtype rangeList: list(float)
    """
    xList = list()
    yList = list()
    zList = list()
    for xyz in XYZList:
        xList.append(xyz[0])
        yList.append(xyz[1])
        zList.append(xyz[2])
    return rangeDifferenceFloat(xList), rangeDifferenceFloat(yList), rangeDifferenceFloat(zList)


def getAxisFromBoundingBox(rangeXYZ, secondaryAxis=False):
    """Tries to guess a good axis orientation for an object list.

     If Up Axis (secondaryAxis=False):

        The shortest edge of a bounding box is the up axis

    If Secondary Axis (secondaryAxis=True):

        If the longest edge is "y", then will be "+z", else will return "+y

    Up axis is always positive.

    :param rangeXYZ: bounding box height width and length in Maya units [x, y, z] position values
    :type rangeXYZ: list(float)
    :return cogUpAxis: "+x", "+y", or "+z" the preferred up axis based on the shortest edge of the bounding box
    :rtype cogUpAxis: str
    """
    if rangeXYZ[0] > rangeXYZ[1] and rangeXYZ[0] > rangeXYZ[2]:  # X is smaller than Y is smaller than Z
        if not secondaryAxis:
            return "+x"
        else:
            return "+y"
    elif rangeXYZ[1] > rangeXYZ[0] and rangeXYZ[1] > rangeXYZ[2]:  # Smallest Y, X, longest is Z
        if not secondaryAxis:
            return "+y"
        else:
            return "+z"
    else:  # Smallest Z, X, longest is Y
        if not secondaryAxis:
            return "+z"
        else:
            return "+y"


def autoAxisBBoxObjList(objList, secondaryAxis=False):
    """Tries to guess a good axis orientation for an object list based on pivot world positions

    If Up Axis (secondaryAxis=False):

        The shortest edge of a bounding box is the up axis

    If Secondary Axis (secondaryAxis=True):

        If the longest edge is "y", then will be "+z", else will return "+y

    Up axis is always positive.

    :param objList: A list of Maya objects
    :type objList: list(str)
    :return cogUpAxis: "+x", "+y", or "+z" the preferred up axis based on the shortest edge of the bounding box
    :rtype cogUpAxis: str
    """
    positionList = list()
    for obj in objList:  # Get world positions of object pivots
        positionList.append(cmds.xform(obj, query=True, worldSpace=True, rotatePivot=True))
    rangeXYZ = rangeDifferenceXYZ(positionList)
    return getAxisFromBoundingBox(rangeXYZ, secondaryAxis)


def autoAxisBBoxObj(obj, secondaryAxis=False):
    """Tries to guess a good axis orientation for an object list based on an object's bounding box, usually a curve

    If Up Axis (secondaryAxis=False):

        The shortest edge of a bounding box is the up axis

    If Secondary Axis (secondaryAxis=True):

        If the longest edge is "y", then will be "+z", else will return "+y

    Up axis is always positive.

    Up axis is always positive.
    :param obj: A Maya object
    :type obj: str
    :return cogUpAxis: "+x", "+y", or "+z" the preferred up axis based on the shortest edge of the bounding box
    :rtype cogUpAxis: str
    """
    rawBoundingBox = scaleutils.getBoundingBoxNoChildren(obj, worldSpace=True)  # [-x, -y, -z, +x, +y, +z]
    rangeXYZ = scaleutils.getBoundingBoxHWL(rawBoundingBox)  # height width and length in Maya units [x, y, z]
    return getAxisFromBoundingBox(rangeXYZ, secondaryAxis)
