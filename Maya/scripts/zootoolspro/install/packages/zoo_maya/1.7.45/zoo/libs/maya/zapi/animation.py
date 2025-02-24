import math, contextlib
from maya.api import OpenMayaAnim as om2Anim
from maya.api import OpenMaya as om2
from zoo.libs.maya.api import anim, constants
from zoo.libs.maya.zapi import base
from zoo.libs.utils import zoomath

from maya import cmds

HALF_PI = math.pi * 0.5


def gimbalTolerance(obj, ctx=om2.MDGContext.kNormal):
    """ Determines the gimbal tolerance value between 0 and 1 for the current Rotation Order.

    :param obj: The node to check.
    :type obj: :class:`zapi.DagNode`
    :return: A value between 0 and 1
    :param ctx: The time MDGContext instance to use other MDGContext.kNormal
    :type ctx: :class:`om2.MDGContext`
    :rtype: float
    """
    rotationOrder = constants.kRotateOrderNames[obj.rotationOrder()]
    rotateAttr = obj.attribute("rotate{}".format(rotationOrder[1].upper()))
    value = rotateAttr.value(ctx=ctx).value
    return abs(((value + HALF_PI) % math.pi) - HALF_PI) / HALF_PI


def allGimbalTolerances(obj, frames=None, step=1):
    """Determines the gimbal tolerance value between 0 and 1 for all rotation Orders.

    If Frames is specified then an average is calculated for each rotationOrder across all
    Specified frames.

    :param obj: The Object to query gimbal on.
    :type obj: :class:`zapi.DagNode`
    :param frames: The individual frames to query ie. [0,1,2,3], if None then only the current state is queried.
    :type frames: list[int]
    :param step: The amount of keys to skip between samples.
    :type step: int
    :rtype: list[float]
    """
    with autoKeyKeyFrameContext(False):
        originalRotOrder = obj.rotationOrder()
        try:
            if frames:
                totalTolerances = []
                for frameIndex, ctx in enumerate(anim.iterFramesDGContext(frames, step)):
                    frameTolerances = [0.0] * len(constants.kRotateOrders)
                    for order in constants.kRotateOrders:
                        obj.setRotationOrder(order)
                        frameTolerances[order] = gimbalTolerance(obj, ctx)  # order is 0-5 so we just reuse
                    totalTolerances.append(frameTolerances)
                # avg each rotation order across all frames.
                tolerances = [zoomath.mean([frame[i] for frame in totalTolerances]) for i in constants.kRotateOrders]
            else:
                # no frames specified so just do the current state
                tolerances = [0.0] * len(constants.kRotateOrders)
                for order in constants.kRotateOrders:
                    obj.setRotationOrder(order)
                    tolerances[order] = gimbalTolerance(obj)
        finally:
            obj.setRotationOrder(originalRotOrder)
    return tolerances


def setRotationOrderOverFrames(nodes, rotationOrder, bakeEveryFrame=False, frameRange=None):
    """ Change the rotation order of the specified nodes while preserving animation.

    .. code-block:: python

        from zoo.libs.maya import zapi
        # to set to XYZ
        setRotationOrderOverFrames(zapi.selected(), zapi.kRotateOrder_XYZ)

    .. note:: you should run this inside of your own undo chunk

    :param nodes: A list of Dag Nodes ie. transforms to convert
    :type nodes: iterable[:class:`DagNode`]
    :param rotationOrder: a rotation order to set to ie.zapi.kRotateOrder_XYZ
    :type rotationOrder: int
    :param bakeEveryFrame: If True then all frames between the start and end will be baked.
    :type bakeEveryFrame: bool
    :param frameRange: The start and end range to bake, defaults to None so only existing keys we be \
    updated.
    :type: list[int, int]
    """
    rotationOrderName = constants.kRotateOrderNames[rotationOrder]
    allKeyTimes = set()
    unKeyedObjs = set()
    keyedObjectMapping = {}  # zapi.dagNode: {"keys":[float], "rotationOrder": 0, "name": ""}
    # first cache existing keyframes and rotation orders which will be used to loop over
    for obj, nodeKeyInfo in keyFramesForNodes(nodes, ["rotate", "rotateOrder"], bakeEveryFrame, frameRange):
        if nodeKeyInfo["keys"]:
            allKeyTimes.update(nodeKeyInfo["keys"])
            keyedObjectMapping[obj] = nodeKeyInfo
        else:
            unKeyedObjs.add(nodeKeyInfo["name"])
    # change rotation order for keyed objects
    if keyedObjectMapping:
        allKeyTimes = list(allKeyTimes)
        allKeyTimes.sort()
        with anim.maintainTime():
            # force set key frames on all rotation attributes so that we're true to the original state.
            for ctx in anim.iterFramesDGContext(allKeyTimes):
                frameTime = ctx.getTime()
                frame = frameTime.value
                om2Anim.MAnimControl.setCurrentTime(frameTime)
                for obj, info in keyedObjectMapping.items():
                    if frame not in info["keys"]:
                        continue
                    objName = info["name"]
                    cmds.setKeyframe(objName, attribute='rotate', preserveCurveShape=True, respectKeyable=True)
                    if obj.rotateOrder.isAnimated():
                        cmds.setKeyframe(objName, attribute='rotateOrder', preserveCurveShape=True)
            # actual reordering and keyframing to new rotation values
            for ctx in anim.iterFramesDGContext(allKeyTimes):
                frameTime = ctx.getTime()
                frame = frameTime.value
                om2Anim.MAnimControl.setCurrentTime(frameTime)
                for obj, info in keyedObjectMapping.items():
                    if frame not in info["keys"]:
                        continue
                    objName = info["name"]
                    obj.setRotationOrder(rotationOrder)
                    # cmds.setKeyframe(objName, attribute='rotate', preserveCurveShape=True, respectKeyable=True)
                    cmds.setKeyframe(objName, attribute='rotate', preserveCurveShape=True, respectKeyable=True)
                    if obj.rotateOrder.isAnimated():
                        cmds.setKeyframe(objName, attribute='rotateOrder', preserveCurveShape=True)
                    # reset to original rotationOrder so on next frame we have the original anim.
                    obj.setRotationOrder(rotateOrder=info["rotationOrder"], preserve=False)

        # we do this via cmds to get undo
        for each in keyedObjectMapping.values():
            cmds.xform(each["name"], preserve=False, rotateOrder=rotationOrderName)
        cmds.filterCurve([o["name"] for o in keyedObjectMapping.values()])

    for obj in unKeyedObjs:
        cmds.xform(obj, preserve=True, rotateOrder=rotationOrderName)


def keyFramesForNodes(objects, attributes, bakeEveryFrame=False, frameRange=None):
    """For each node yield the appropriate keyframes and rotationOrder.

    See :func:`keyFramesForNode` for details.

    :param objects: A list of Dag Nodes ie. transforms to convert
    :type objects: iterable[:class:`DagNode`]
    :param attributes: The list of attributes to take into account of when reading keyframes.
    :type attributes: list[str]
    :param bakeEveryFrame: If True then all frames between the start and end will be baked.
    :type bakeEveryFrame: bool
    :param frameRange: The start and end range to bake, defaults to None so only existing keys we be \
    updated.
    :type frameRange: list[int, int]
    :return: A generator function where each element contain a dict of {"keys": [], "rotationOrder": int, "name": ""}
    :rtype: iterable[dict]
    """
    allKeyFrames = frameRange or []
    if allKeyFrames:
        allKeyFrames = list(allKeyFrames)
        allKeyFrames[-1] = allKeyFrames[-1] + 1
        allKeyFrames = list(range(*tuple(allKeyFrames)))

    # first cache existing keyframes and rotation orders which will be used to loop over
    for obj in objects:
        yield obj, keyFramesForNode(obj,
                                    attributes=attributes,
                                    defaultKeyFrames=allKeyFrames,
                                    bakeEveryFrame=bakeEveryFrame,
                                    frameRange=frameRange
                                    )


def keyFramesForNode(node, attributes, defaultKeyFrames=None, bakeEveryFrame=False, frameRange=None):
    """Returns the key frames, rotationOrder and name for the node based on the provided arguments.

    .. note::

        When bakeEveryFrame is True and frameRange is not None then the provided default is returned. This is
        Due to the need to cache the key list to optimise the function across multiple requests.
        When frameRange is None and BakeEveryFrame is True then the function will query the min and max keyFrames
        for the attributes and return all keyFrames on whole numbers between them.

    :param node: The animated node to read.
    :type node: :class:`base.DagNode`
    :param attributes: The list of attributes to take into account of when reading keyframes.
    :type attributes: list[str]
    :param defaultKeyFrames: Default keyframes to use when bakeEveryFrame is True and provided frameRange.
    :type defaultKeyFrames: list[int] or None
    :param bakeEveryFrame: If True then all frames between the start and end will be baked.
    :type bakeEveryFrame: bool
    :param frameRange: The start and end range to bake, defaults to None so only existing keys we be \
    updated.
    :type frameRange: list[int, int]
    :return: Returns a dict containing a unique flat list of keys for the provided attributes, \
    the rotationOrder for the node and the node name
    :rtype: dict
    """
    defaultKeyFrames = defaultKeyFrames or []
    objName = node.fullPathName()
    if bakeEveryFrame:
        # grab every frame between the specified frame range
        if frameRange:
            rotKeys = defaultKeyFrames
        else:
            # grab every frame between the min and max keys
            rotKeys = cmds.keyframe(objName, attribute=attributes, query=True, timeChange=True)
            if rotKeys:
                rotKeys = list(range(int(min(rotKeys)), int(max(rotKeys)) + 1))
    # not baking every frame just the keys within the specified range
    elif frameRange:
        rotKeys = cmds.keyframe(objName, time=tuple(frameRange), attribute=attributes, query=True, timeChange=True)
    # otherwise grab the all current keys
    else:
        rotKeys = cmds.keyframe(objName, attribute=attributes, query=True, timeChange=True)

    return {"keys": set(rotKeys or []),
            "rotationOrder": node.rotationOrder(),
            "name": objName
            }


@contextlib.contextmanager
def autoKeyKeyFrameContext(state=False):
    """Context manager for autoKeyKeyframe.

    Example:
        with autoKeyKeyFrameContext():
            cmds.setAttr("pCube1.tx", 10)
            cmds.setAttr("pCube1.ty", 10)
            cmds.setAttr("pCube1.tz", 10)
    """
    currentAutoState = cmds.autoKeyframe(state=state, q=True)
    if currentAutoState == state:
        yield
        return
    try:
        cmds.autoKeyframe(state=state)
        yield
    finally:
        cmds.autoKeyframe(state=currentAutoState)


def frameRanges(frames):
    """Generate a list of frame ranges from a given list of frames.

    :param frames: List of frames.
    :type frames: list
    :return: List of frame ranges.
    :rtype: list
    """
    frameRange = []
    startFrame = frames[0]

    for i in range(1, len(frames)):
        if frames[i] != frames[i - 1] + 1:
            frameRange.append((startFrame, frames[i - 1]))
            startFrame = frames[i]

    # Add the last range
    frameRange.append((startFrame, frames[-1]))

    return frameRange
