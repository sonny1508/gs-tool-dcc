from maya import cmds
import random

from zoo.libs.maya.cmds.objutils import attributes
from zoo.libs.utils import output


def offsetAttrValue(obj, attr, offsetValue, min, max, current=0.0, absolute=False):
    """Offsets an attribute by the offset value which is somewhere between 0.0-1.0

    Used by the scale attribute when the scale random amount needs to be uniform for all attributes
    """
    if not absolute:
        newValue = ((max - min) * offsetValue) + current + min
    else:
        newValue = ((max - min) * offsetValue) + min
    cmds.setAttr(".".join([obj, attr]), newValue)


def randomizeAttr(obj, attr, min, max, current=0.0, absolute=False):
    """Randomizes an attribute in either absolute or relative mode:

        min = 0.0
        max = 10.0
        current = 20.0
        absolute = False
        Result is 23.556 (random between 20.0 and 30.0)

    Must be float attributes

    :param obj: The maya object string name
    :type obj: str
    :param attr: The name of the attribute to randomize
    :type attr: str
    :param min: The minimum range value
    :type min: float
    :param max: The maximum range value
    :type max: float
    :param current: The current value if absolute is False (relative mode)
    :type current: float
    :param absolute: If True mode is absolute, if False relative mode
    :type absolute: bool
    """
    if max - min == 0.0:  # no range so don't randomize
        return
    if not absolute:
        min = min + current
        max = max + current
    cmds.setAttr(".".join([obj, attr]), random.uniform(min, max))


def randomizeAttrList(obj, attrList, min, max, uniformScale=True, absolute=False):
    """Randomizes a list of attributes with both relative/absolute and uniform modes.

    :param obj: The maya object string name
    :type obj: str
    :param attrList: A list of Maya attribute names, currently must be floats.
    :type attrList: list(str)
    :param min: The minimum range value
    :type min: float
    :param max: The maximum range value
    :type max: float
    :param uniformScale: If True, will scale the scale attributes by the same amount for each attribute
    :type uniformScale: bool
    :param absolute: If True mode is absolute, if False relative mode
    :type absolute: bool
    """
    attrCurValueList = list()
    if not absolute:
        for attr in attrList:
            attrCurValueList.append(cmds.getAttr(".".join([obj, attr])))
    else:
        attrCurValueList = [0.0 for i in range(len(attrList))]  # a list with every value zero

    # Do the randomize -----------------------------
    if uniformScale:  # randomizes the same amount for all scale attributes
        offsetValue = random.random()
        for i, attr in enumerate(attrList):
            offsetAttrValue(obj, attr, offsetValue,
                            min,
                            max,
                            current=attrCurValueList[i],
                            absolute=absolute)
    else:  # each attribute is scaled randomly so will be non-uniform scale
        for i, attr in enumerate(attrList):
            randomizeAttr(obj, attr,
                          min,
                          max,
                          current=attrCurValueList[i],
                          absolute=absolute)


def randomizeRotObj(obj, randRotate=False, randTranslate=False, randScale=False, randOther=False, absolute=False,
                    translateMinMax=((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
                    rotateMinMax=((0.0, 0.0, 0.0), (45.0, 45.0, 45.0)),
                    scaleMinMax=((0.0, 0.0, 0.0), (5.0, 5.0, 5.0)),
                    otherMinMax=(0.0, 1.0),
                    otherAttrName="",
                    uniformScale=True):
    """Randomizes an object with options for rotate, translate, scale and other.

        min = 0.0
        max = 10.0
        current = 20.0
        absolute = False
        Result is 23.556 (random between 20.0 and 30.0)

    :param obj: The maya object string name
    :type obj: str
    :param randRotate: Randomize the rotation?
    :type randRotate: bool
    :param randTranslate: Randomize the translation?
    :type randTranslate: bool
    :param randScale: Randomize the scale?
    :type randScale: bool
    :param randOther: Randomize a user inputed attribute?
    :type randOther: bool
    :param translateMinMax: The min/max translate values
    :type translateMinMax: tuple(tuple)
    :param rotateMinMax: The min/max rotation values
    :type rotateMinMax: tuple(tuple)
    :param scaleMinMax: The min/max scale values
    :type scaleMinMax: tuple(tuple)
    :param otherMinMax: The min/max other values
    :type otherMinMax: tuple
    :param otherAttrName: the name of the user inputed attribute if there is one
    :type otherAttrName: str
    :param uniformScale: If True, will scale the scale attributes by the same amount for each axis
    :type uniformScale: bool
    """
    scaleCurrent = (0.0, 0.0, 0.0)
    rotateCurrent = (0.0, 0.0, 0.0)
    translateCurrent = (0.0, 0.0, 0.0)
    otherCurrent = 0.0
    # Absolute/Relative
    if not absolute:
        if randRotate:
            rotateCurrent = cmds.getAttr(".".join([obj, "rotate"]))[0]
        if randTranslate:
            translateCurrent = cmds.getAttr(".".join([obj, "translate"]))[0]
        if randScale:
            scaleCurrent = cmds.getAttr(".".join([obj, "scale"]))[0]
        if randOther:
            otherCurrent = cmds.getAttr(".".join([obj, otherAttrName]))
    # Do the randomize
    if randTranslate:
        for i, attr in enumerate(attributes.MAYA_TRANSLATE_ATTRS):
            randomizeAttr(obj, attr,
                          translateMinMax[0][i],
                          translateMinMax[1][i],
                          current=translateCurrent[i],
                          absolute=absolute)
    if randRotate:
        for i, attr in enumerate(attributes.MAYA_ROTATE_ATTRS):
            randomizeAttr(obj, attr,
                          rotateMinMax[0][i],
                          rotateMinMax[1][i],
                          current=rotateCurrent[i],
                          absolute=absolute)
    if randScale:
        if uniformScale:  # randomizes the same amount for all scale attributes
            offsetValue = random.random()
            for i, attr in enumerate(attributes.MAYA_SCALE_ATTRS):
                offsetAttrValue(obj, attr, offsetValue,
                                scaleMinMax[0][i],
                                scaleMinMax[1][i],
                                current=scaleCurrent[i],
                                absolute=absolute)
        else:  # each attribute is scaled randomly so will be non-uniform scale
            for i, attr in enumerate(attributes.MAYA_SCALE_ATTRS):
                randomizeAttr(obj, attr,
                              scaleMinMax[0][i],
                              scaleMinMax[1][i],
                              current=scaleCurrent[i],
                              absolute=absolute)
    if randOther and otherAttrName:
        randomizeAttr(obj, otherAttrName,
                      otherMinMax[0],
                      otherMinMax[1],
                      current=otherCurrent,
                      absolute=absolute)


def randomizeRotObjList(objList,
                        randRotate=False,
                        randTranslate=False,
                        randScale=False,
                        randOther=False,
                        translateMinMax=((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
                        rotateMinMax=((0.0, 0.0, 0.0), (45.0, 45.0, 45.0)),
                        scaleMinMax=((0.0, 0.0, 0.0), (5.0, 5.0, 5.0)),
                        otherMinMax=(0.0, 1.0),
                        otherAttrName="",
                        absolute=False,
                        uniformScale=True,
                        message=True):
    """Randomizes an object list with options for rotate, translate, scale and other.

        min = 0.0
        max = 10.0
        current = 20.0
        absolute = False
        Result is 23.556 (random between 20.0 and 30.0)

    :param objList: A list of Maya object string names
    :type objList: list(str)
    :param randRotate: Randomize the rotation?
    :type randRotate: bool
    :param randTranslate: Randomize the translation?
    :type randTranslate: bool
    :param randScale: Randomize the scale?
    :type randScale: bool
    :param randOther: Randomize a user inputed attribute?
    :type randOther: bool
    :param translateMinMax: The min/max translate values
    :type translateMinMax: tuple(tuple)
    :param rotateMinMax: The min/max rotation values
    :type rotateMinMax: tuple(tuple)
    :param scaleMinMax: The min/max scale values
    :type scaleMinMax: tuple(tuple)
    :param otherMinMax: The min/max other values
    :type otherMinMax: tuple
    :param otherAttrName: the name of the user inputed attribute if there is one
    :type otherAttrName: str
    :param uniformScale: If True, will scale the scale attributes by the same amount for each axis
    :type uniformScale: bool
    :param message: Report a message to the user?
    :type message: bool
    """
    for obj in objList:
        randomizeRotObj(obj,
                        randRotate=randRotate,
                        randTranslate=randTranslate,
                        randScale=randScale,
                        randOther=randOther,
                        translateMinMax=translateMinMax,
                        rotateMinMax=rotateMinMax,
                        scaleMinMax=scaleMinMax,
                        otherMinMax=otherMinMax,
                        otherAttrName=otherAttrName,
                        absolute=absolute,
                        uniformScale=uniformScale)
    if message:
        output.displayInfo("Objects randomized")


def randomObjSelection(randRotate=False,
                       randTranslate=False,
                       randScale=False,
                       randOther=False,
                       translateMinMax=((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
                       rotateMinMax=((0.0, 0.0, 0.0), (45.0, 45.0, 45.0)),
                       scaleMinMax=((0.0, 0.0, 0.0), (5.0, 5.0, 5.0)),
                       otherMinMax=(0.0, 1.0),
                       otherAttrName="",
                       absolute=False,
                       uniformScale=True,
                       message=True):
    """Randomizes any selected objects with options for rotate, translate, scale and other.

        min = 0.0
        max = 10.0
        current = 20.0
        absolute = False
        Result is 23.556 (random between 20.0 and 30.0)

    :param randRotate: Randomize the rotation?
    :type randRotate: bool
    :param randTranslate: Randomize the translation?
    :type randTranslate: bool
    :param randScale: Randomize the scale?
    :type randScale: bool
    :param randOther: Randomize a user inputed attribute?
    :type randOther: bool
    :param translateMinMax: The min/max translate values
    :type translateMinMax: tuple(tuple)
    :param rotateMinMax: The min/max rotation values
    :type rotateMinMax: tuple(tuple)
    :param scaleMinMax: The min/max scale values
    :type scaleMinMax: tuple(tuple)
    :param otherMinMax: The min/max other values
    :type otherMinMax: tuple
    :param otherAttrName: the name of the user inputed attribute if there is one
    :type otherAttrName: str
    :param uniformScale: If True, will scale the scale attributes by the same amount for each axis
    :type uniformScale: bool
    :param message: Report a message to the user?
    :type message: bool
    """
    selObjs = cmds.ls(selection=True)
    if len(selObjs) == 0:
        output.displayWarning("Please select objects to randomize")
        return
    if not randTranslate and not randScale and not randOther and not randRotate:
        output.displayWarning("Please check on one randomize mode")
        return
    randomizeRotObjList(selObjs, randRotate=randRotate, randTranslate=randTranslate, randScale=randScale,
                        randOther=randOther,
                        translateMinMax=translateMinMax, rotateMinMax=rotateMinMax, scaleMinMax=scaleMinMax,
                        otherMinMax=otherMinMax, otherAttrName=otherAttrName, absolute=absolute,
                        uniformScale=uniformScale, message=True)


def randomAttrChannelSelection(minMax, absolute=False, uniformScale=False, message=True):
    selObjs = cmds.ls(selection=True)
    if len(selObjs) == 0:
        if message:
            output.displayWarning("Please select objects to randomize")
        return
    selAttrs = cmds.channelBox('mainChannelBox', q=True, sma=True) or cmds.channelBox('mainChannelBox', q=True,
                                                                                      sha=True)
    if not selAttrs:
        if message:
            output.displayWarning("Please select attributes in the channel box to randomize")
        return
    # Do the randomize ---------------------------------------
    for obj in selObjs:
        randomizeAttrList(obj, selAttrs, minMax[0], minMax[1], uniformScale=uniformScale, absolute=absolute)
