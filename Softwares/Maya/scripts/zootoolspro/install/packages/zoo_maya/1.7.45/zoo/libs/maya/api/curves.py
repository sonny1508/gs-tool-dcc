import copy

from maya import cmds
from maya.api import OpenMaya as om2

from zoovendor.six.moves import range

from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import plugs
from zoo.libs.maya.utils import mayamath
from zoo.libs.utils import zoomath

shapeInfo = {
    "cvs": (),
    "degree": 3,
    "form": 1,
    "knots": (),
    "matrix": (
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ),
    "outlinerColor": (0.0, 0.0, 0.0),
    "overrideColorRGB": (0.0, 0.0, 0.0),
    "overrideEnabled": False,
    "overrideRGBColors": False,
    "useOutlinerColor": False,
}


def getCurveData(shape, space=om2.MSpace.kObject, includeColours=True):
    """From a given NurbsCurve shape node serialize the cvs positions, knots, degree, form rgb colours

    :param shape: MObject that represents the NurbsCurve shape
    :return: dict
    :param space:
    :type space: om2.MSpace

    .. code-block:: python

        nurbsCurve = cmds.circle()[1]
        # requires an MObject of the shape node
        data = curve_utils.getCurveData(api.asMObject(nurbsCurve))

    """
    if isinstance(shape, om2.MObject):
        shape = om2.MFnDagNode(shape).getPath()
    curve = om2.MFnNurbsCurve(shape)
    try:
        curve.numCVs
    # protects against a shape with no cvs which maya raises a RuntimeError
    # mfnNurbsCurve has no option to check if it has cvs without an error
    # hopefully this stops a potential crash
    except RuntimeError:
        return {}
    data = nodes.getNodeColourData(shape.node()) if includeColours else {}
    # so we can deserialize in world which maya does in to steps
    data.update(
        {
            "knots": tuple(curve.knots()),
            "cvs": tuple(map(tuple, curve.cvPositions(space))),
            "degree": curve.degree,
            "form": curve.form,
            "matrix": tuple(nodes.getWorldMatrix(curve.object())),
        }
    )
    return data


def createCurveShape(parent, data, space=om2.MSpace.kObject, mod=None):
    """Create a specified nurbs curves based on the data.

    :param parent: The transform that takes ownership of the shapes, if None is supplied then one will be created
    :type parent: MObject
    :param data: `{"shapeName": {"cvs": [], "knots":[], "degree": 0, "form": int, "matrix": []}}`
    :type data: dict
    :param space: om2.MSpace
    :type space: int
    :return: A 2 tuple the first element is the MObject of the parent and the second is a list \
    of mobjects represents the shapes created.

    :rtype: iterable[:class:`om2.MObject`, list[:class:`om2.MObject`]]
    """
    parentInverseMatrix = om2.MMatrix()
    if parent is None:
        parent = om2.MObject.kNullObj
    elif parent != om2.MObject.kNullObj:
        parentInverseMatrix = nodes.getWorldInverseMatrix(parent)
    newCurve = om2.MFnNurbsCurve()
    modifier = om2.MDGModifier()
    newShapes = []
    for shapeName, curveData in iter(data.items()):
        cvs = om2.MPointArray(
            curveData["cvs"]
        )  # om2 allows a list of lists which converts to om2.Point per element
        knots = curveData["knots"]
        degree = curveData["degree"]
        form = curveData["form"]
        enabled = curveData.get("overrideEnabled", False)
        if space == om2.MSpace.kWorld and parent != om2.MObject.kNullObj:
            for i in range(len(cvs)):
                cvs[i] *= parentInverseMatrix
        shape = newCurve.create(cvs, knots, degree, form, False, False, parent)
        newShapes.append(shape)
        if parent == om2.MObject.kNullObj and shape.apiType() == om2.MFn.kTransform:
            parent = shape
        if enabled:
            colours = curveData["overrideColorRGB"]
            outlinerColour = curveData.get("outlinerColor")
            # backwards compatibility with existing serialized curve data.
            # the outliner colour needs to be float3 not float4 but getNodeColor return MColor ie. float4
            if outlinerColour and len(outlinerColour) > 3:
                outlinerColour = outlinerColour[:-1]
            nodes.setNodeColour(
                newCurve.object(),
                colours,
                outlinerColour=outlinerColour,
                useOutlinerColour=curveData.get("useOutlinerColor", False),
                mod=modifier,
            )
    modifier.doIt()
    return parent, newShapes


def createCurveFromPoints(name, points, shapeDict=None, parent=None):
    shapeDict = shapeDict or copy.deepcopy(shapeInfo)
    # create the shape name
    if not name.endswith("shape"):
        name = name + "Shape"
    deg = shapeDict["degree"]
    shapeDict["cvs"] = points
    knots = shapeDict.get("knots")
    if not knots:
        if deg == 1:  # linear
            shapeDict["knots"] = tuple(range(len(points)))
        elif deg == 3:
            ncvs = len(points)
            # append two zeros to the front of the knot count so it lines up with maya specs
            # (ncvs - deg) + 2 * deg - 1
            knots = [0, 0] + list(range(ncvs))
            # remap the last two indices to match the third from last
            knots[-2] = knots[len(knots) - deg]
            knots[-1] = knots[len(knots) - deg]

            shapeDict["knots"] = knots

    return createCurveShape(parent, {name: shapeDict})


def createBezierCurve(name, points, degree=3, knots=None, parent=None):
    """Creates a Bezier curve from the provided points and degree and returns an om2.MObject.

    :param name: The name for the curve
    :type name: str
    :param points: 2D list of point positions.
    :type points: list[list[float, float, float]]
    :param degree: The curve degree, default is 3.
    :type degree: int
    :param knots: point knots, must be len(points) + degree -1. If None knots will be auto generated.
    :type knots: list[float] or None
    :param parent: The parent transform for the curve, if None a new transform is created.
    :type parent: :class:`om2.MObject` or None
    :return: The curve as a MObject.
    :rtype: :class:`om2.MObject`
    """
    knots = knots or []
    if not knots:
        knotsIndex = -1
        for i in range(len(points) + degree - 1):
            if i % degree == 0:
                knotsIndex += 1
            knots.append(float(knotsIndex))

    kwargs = {
        "name": name,
        "point": points,
        "degree": degree,
        "bezier": True,
        "knot": knots,
    }
    args = []
    if parent is not None:
        args.append(nodes.nameFromMObject(parent))
    return nodes.asMObject(cmds.curve(*args, **kwargs))


def serializeCurve(node, space=om2.MSpace.kObject, includeColours=True):
    """From a given transform serialize the shapes curve data and return a dict compatible
    with Json.

    :param node: The MObject that represents the transform above the nurbsCurves
    :type node: MObject
    :return: returns the dict of data from the shapes
    :rtype: dict
    """
    shapes = nodes.shapes(
        om2.MFnDagNode(node).getPath(), filterTypes=(om2.MFn.kNurbsCurve,)
    )
    data = {}
    for shape in shapes:
        dag = om2.MFnDagNode(shape.node())
        isIntermediate = dag.isIntermediateObject
        if not isIntermediate:
            curveData = getCurveData(shape, space=space, includeColours=includeColours)
            if not curveData:
                continue
            curveData["outlinerColor"] = tuple(curveData.get("outlinerColor", ()))[:-1]
            curveData["overrideColorRGB"] = tuple(
                curveData.get("overrideColorRGB", ())
            )[:-1]
            data[om2.MNamespace.stripNamespaceFromName(dag.name())] = curveData

    return data


def mirrorCurveCvs(curveObj, axis="x", space=None):
    """Mirrors the the curves transform shape cvs by a axis in a specified space

    :param curveObj: The curves transform to mirror
    :type curveObj: mobject
    :param axis: the axis the mirror on, accepts: 'x', 'y', 'z'
    :type axis: str
    :param space: the space to mirror by, accepts: MSpace.kObject, MSpace.kWorld, default: MSpace.kObject
    :type space: int

    :Example:

            nurbsCurve = cmds.circle()[0]
            mirrorCurveCvs(api.asMObject(nurbsCurve), axis='y', space=om.MSpace.kObject)

    """
    space = space or om2.MSpace.kObject

    axis = axis.lower()
    axisDict = {"x": 0, "y": 1, "z": 2}
    axisToMirror = set(axisDict[ax] for ax in axis)

    shapes = nodes.shapes(om2.MFnDagNode(curveObj).getPath())
    for shape in shapes:
        curve = om2.MFnNurbsCurve(shape)
        cvs = curve.cvPositions(space=space)
        # invert the cvs MPoints based on the axis
        for i, point in enumerate(iter(cvs)):
            for ax in axisToMirror:
                point[ax] *= -1
            cvs[i] = point
        curve.setCVPositions(cvs)
        curve.updateCurve()


def iterCurvePoints(dagPath, count, space=om2.MSpace.kObject):
    """Generator Function to iterate and return the position, normal and tangent for the curve with the given point count.

    :param dagPath: the dagPath to the curve shape node
    :type dagPath: om2.MDagPath
    :param count: the point count to generate
    :type count: int
    :param space: the coordinate space to query the point data
    :type space: om2.MSpace
    :return: The first element is the Position, second is the normal, third is the tangent
    :rtype: tuple(MVector, MVector, MVector)
    """
    crvFn = om2.MFnNurbsCurve(dagPath)
    length = crvFn.length()
    dist = length / float(count - 1)  # account for end point
    current = 0.001
    maxParam = crvFn.findParamFromLength(length)
    defaultNormal = [1.0, 0.0, 0.0]
    defaultTangent = [0.0, 1.0, 0.0]
    for i in range(count):
        param = crvFn.findParamFromLength(current)
        # maya fails to get the normal when the param is the maxparam so we sample with a slight offset
        if param == maxParam:
            param = maxParam - 0.0001
        point = om2.MVector(crvFn.getPointAtParam(param, space=space))
        # in case where the curve is flat eg. directly up +y
        # this causes a runtimeError in which case the normal is [1.0,0.0,0.0] and tangent [0.0,1.0,0.0]
        try:
            yield point, crvFn.normal(param, space=space), crvFn.tangent(
                param, space=space
            )
        except RuntimeError:
            yield point, defaultNormal, defaultTangent
        current += dist


def matchCurves(driver, targets, space=om2.MSpace.kObject):
    """Function that matches the curves from the driver to all the targets.

    :param driver: the transform node of the shape to match
    :type driver: om2.MObject
    :param targets: A list of transform that will have the shapes replaced
    :type targets: list(om2.MObject) or tuple(om2.MObject)
    """
    driverdata = serializeCurve(driver, space)
    shapes = []
    for target in targets:
        targetShapes = [
            nodes.nameFromMObject(i.node())
            for i in nodes.iterShapes(om2.MDagPath.getAPathTo(target))
        ]
        if targetShapes:
            cmds.delete(targetShapes)
        shapes.extend(createCurveShape(target, driverdata, space=space)[1])
    return shapes


def curveCvs(dagPath, space=om2.MSpace.kObject):
    """Generator Function to iterate and return the position, normal and tangent for the curve with the given point count.

    :param dagPath: the dagPath to the curve shape node
    :type dagPath: om2.MDagPath
    :param space: the coordinate space to query the point data
    :type space: om2.MSpace
    :return: The first element is the Position, second is the normal, third is the tangent
    :rtype: tuple(om2.MPoint)
    """
    return om2.MFnNurbsCurve(dagPath).cvPositions(space=space)


def iterCurveParams(dagPath, count, initialOffset=0.1):
    """Generator Function to iterate and return the Parameter

    :param dagPath: the dagPath to the curve shape node
    :type dagPath: om2.MDagPath
    :param count: the Number of params to loop
    :type count: int
    :return: The curve param value
    :rtype: list[float]
    """
    crvFn = om2.MFnNurbsCurve(dagPath)
    length = crvFn.length()
    dist = length / float(count - 1)  # account for end point
    current = initialOffset
    for i in range(count):
        yield crvFn.findParamFromLength(current)
        current += dist


def attachNodeToCurveAtParam(curve, node, param, name, rotate=True, fractionMode=False):
    """Attaches the given node to the curve using a motion path node.

    :param curve: nurbsCurve Shape to attach to
    :type curve: om2.MObject
    :param node: the node to attach to the curve
    :type node: om2.MObject
    :param param: the parameter float value along the curve
    :type param: float
    :param name: the motion path node name to use
    :type name: str
    :param rotate: Whether to connect rotation from the motion path to the node.
    :type rotate: bool
    :param fractionMode: True if the motion path should use fractionMode(0.1) vs False(0-2)
    :type fractionMode: bool
    :return: motion path node
    :rtype: om2.MObject
    """
    nodeFn = om2.MFnDependencyNode(node)
    crvFn = om2.MFnDependencyNode(curve)
    mp = nodes.createDGNode(name, "motionPath")
    mpFn = om2.MFnDependencyNode(mp)
    if rotate:
        plugs.connectVectorPlugs(
            mpFn.findPlug("rotate", False),
            nodeFn.findPlug("rotate", False),
            (True, True, True),
        )
    plugs.connectVectorPlugs(
        mpFn.findPlug("allCoordinates", False),
        nodeFn.findPlug("translate", False),
        (True, True, True),
    )
    crvWorld = crvFn.findPlug("worldSpace", False)
    plugs.connectPlugs(
        crvWorld.elementByLogicalIndex(0), mpFn.findPlug("geometryPath", False)
    )
    mpFn.findPlug("uValue", False).setFloat(param)
    mpFn.findPlug("frontAxis", False).setInt(0)
    mpFn.findPlug("upAxis", False).setInt(1)
    mpFn.findPlug("fractionMode", False).setBool(fractionMode)
    return mp


def createMotionPath(curve, param, name,fractionMode=False):
    crvFn = om2.MFnDependencyNode(curve)
    mp = nodes.createDGNode(name, "motionPath")
    mpFn = om2.MFnDependencyNode(mp)
    crvWorld = crvFn.findPlug("worldSpace", False)
    plugs.connectPlugs(
        crvWorld.elementByLogicalIndex(0), mpFn.findPlug("geometryPath", False)
    )
    mpFn.findPlug("uValue", False).setFloat(param)
    mpFn.findPlug("frontAxis", False).setInt(0)
    mpFn.findPlug("upAxis", False).setInt(1)
    mpFn.findPlug("fractionMode", False).setBool(fractionMode)
    return mp


def iterGenerateSrtAlongCurve(
    dagPath, count, name, rotate=True, fractionMode=False, nodeType="transform"
):
    """Generator function to iterate the curve and attach transform nodes to the curve using a motionPath

    :param dagPath: the dagpath to the nurbscurve shape node
    :type dagPath: om2.MDagPath
    :param count: the number of transforms
    :type count: int
    :param name: the name for the transform, the motionpath will have the same name plus "_mp"
    :type name: str
    :param rotate: Whether to connect rotation from the motion path to the SRT.
    :type rotate: bool
    :param fractionMode: True if the motion path should use fractionMode(0.1) vs False(0-2)
    :type fractionMode: bool
    :return: Python Generator  first element is the created transform node, the second is the motionpath node
    :rtype: Generate(tuple(om2.MObject, om2.MObject))
    """
    curveNode = dagPath.node()
    if fractionMode:
        iterator = zoomath.lerpCount(0, 1, count)
    else:
        iterator = iterCurveParams(dagPath, count)

    for index, param in enumerate(iterator):
        transform = nodes.createDagNode(name, nodeType)
        motionPath = attachNodeToCurveAtParam(
            curveNode,
            transform,
            param,
            "_".join([name, "mp"]),
            rotate=rotate,
            fractionMode=fractionMode,
        )
        yield transform, motionPath


def rotationsAlongCurve(curveShape, count, aimVector, upVector, worldUpVector):
    """Returns the position and rotation along the curve incrementally based on the `jointCount` provided.

    :param curveShape: The NurbsCurve shape DagPath to use.
    :type curveShape: :class:`om2.MDagPath`
    :param count: The number of points along the curve to use.
    :type count: int
    :param aimVector: The primary axis to align along the curve. ie. `om2.MVector(1.0,0.0,0.0)`
    :type aimVector: :class:`om2.MVector`
    :param upVector: The upVector axis to use. ie. `om2.MVector(0.0,1.0,0.0)`
    :type upVector: :class:`om2.MVector`
    :param worldUpVector: The secondary world up Vector to use. ie. `om2.MVector(0.0,0.0,1.0)`
    :type worldUpVector: :class:`om2.MVector`
    :return: Returns a generator containing the position and rotation.
    :rtype: tuple[:class:`om2.MVector`, :class:`om2.MQuaternion`]
    """
    positions = [
        point
        for point, _, __ in iterCurvePoints(curveShape, count, space=om2.MSpace.kWorld)
    ]
    lastIndex = count - 1
    previousRotation = om2.MQuaternion()
    for index, position in enumerate(positions):
        if index == lastIndex:
            rotation = previousRotation
        else:
            rotation = mayamath.lookAt(
                position,
                positions[index + 1],
                aimVector=aimVector,
                upVector=upVector,
                worldUpVector=worldUpVector,
            )
        previousRotation = rotation
        yield position, rotation
