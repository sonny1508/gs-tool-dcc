"""Keyframe related scripts.

Author: Andrew Silke

from zoo.libs.maya.cmds.animation import keyframes
keyframes.transferAnimationSelected()

"""

import maya.cmds as cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import attributes, namehandling


# -------------------
# TURNTABLE
# -------------------


def createTurntable(rotateGrp, start=0, end=200, spinValue=360, startValue=0, attr='rotateY',
                    tangent="spline", prePost="linear", setTimerange=True, reverse=False, angleOffset=0):
    """Creates a spinning object 360 degrees, useful for turntables

    :param rotateGrp: the group name to animate
    :type rotateGrp: str
    :param start: the start frame
    :type start: float
    :param end: the end frame
    :type end: float
    :param spinValue: the value to spin, usually 360
    :type spinValue: float
    :param startValue: the start value usually 0
    :type startValue: float
    :param attr: the attribute to animate, usually "rotateY"
    :type attr: str
    :param tangent: the tangent type "spline", "linear", "fast", "slow", "flat", "stepped", "step next" etc
    :type tangent: str
    :param prePost: the infinity option, linear forever?  "constant", "linear", "cycle", "cycleRelative" etc
    :type prePost: str
    :param setTimerange: do you want to set Maya's timerange to the in (+1) and out at the same time?
    :type setTimerange: bool
    :param angleOffset: the angle offset of the keyframes in degrees, will change the start rotation of the asset
    :type angleOffset: float
    :param reverse: reverses the spin direction
    :type reverse: bool
    :return rotateGrp: the grp/object now with keyframes
    :rtype rotateGrp: str
    """
    cmds.cutKey(rotateGrp, time=(), attribute=attr)  # delete if any keys on that attr
    startValue = startValue + angleOffset
    if reverse:  # spins the other way -360
        spinValue *= -1
    endValue = spinValue + angleOffset
    cmds.setKeyframe(rotateGrp, time=start, value=startValue, breakdown=0, attribute=attr,
                     inTangentType=tangent, outTangentType=tangent)
    cmds.setKeyframe(rotateGrp, time=end, value=endValue, breakdown=0, attribute=attr,
                     inTangentType=tangent, outTangentType=tangent)
    cmds.setInfinity(rotateGrp, preInfinite=prePost, postInfinite=prePost)
    if setTimerange:
        cmds.playbackOptions(minTime=start + 1, maxTime=end)  # +1 makes sure the cycle plays without repeated frame
    return rotateGrp


def turntableSelectedObj(start=0, end=200, spinValue=360, startValue=0, attr='rotateY', tangent="spline",
                         prePost="linear", setTimerange=True, angleOffset=0, reverse=False, message=True):
    """Creates a turntable by spinning the selected object/s by 360 degrees

    :param rotateGrp: the group name to animate
    :type rotateGrp: str
    :param start: the start frame
    :type start: float
    :param end: the end frame
    :type end: float
    :param spinValue: the value to spin, usually 360
    :type spinValue: float
    :param startValue: the start value usually 0
    :type startValue: float
    :param attr: the attribute to animate, usually "rotateY"
    :type attr: str
    :param tangent: the tangent type "spline", "linear", "fast", "slow", "flat", "stepped", "step next" etc
    :type tangent: str
    :param prePost: the infinity option, linear forever?  "constant", "linear", "cycle", "cycleRelative" etc
    :type prePost: str
    :param setTimerange: do you want to set Maya's timerange to the in (+1) and out at the same time?
    :type setTimerange: bool
    :param angleOffset: the angle offset of the keyframes in degrees, will change the start rotation of the asset
    :type angleOffset: float
    :param reverse: reverses the spin direction
    :type reverse: bool
    :param message: report the message to the user in Maya
    :type message: bool
    :return rotateObjs: the grp/objects now with keyframes
    :rtype rotateGrp: list
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        output.displayWarning("No Objects Selected. Please Select An Object/s")
        return
    for obj in selObjs:
        createTurntable(obj, start=start, end=end, spinValue=spinValue, startValue=startValue, attr=attr,
                        tangent=tangent, prePost=prePost, setTimerange=setTimerange, angleOffset=angleOffset,
                        reverse=reverse)
    if message:
        output.displayInfo("Turntable Create on:  {}".format(selObjs))
    return selObjs


def deleteTurntableSelected(attr="rotateY", returnToZeroRot=True, message=True):
    """Deletes a turntable animation of the selected obj/s. Ie. Simply deletes the animation on the rot y attribute

    :param attr: The attribute to delete all keys
    :type attr: str
    :param returnToZeroRot: Return the object to default zero?
    :type returnToZeroRot: bool
    :param message: Report the messages to the user in Maya?
    :type message: bool
    :return assetGrps: The group/s now with animation
    :rtype assetGrps: list
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        output.displayWarning("No Objects Selected. Please Select An Object/s")
        return
    for obj in selObjs:
        cmds.cutKey(obj, time=(-10000, 100000), attribute=attr)  # delete all keys rotY
    if returnToZeroRot:
        cmds.setAttr(".".join([obj, attr]), 0)
    if message:
        output.displayInfo("Turntable Keyframes deleted on:  {}".format(selObjs))
    return selObjs


# -------------------
# TOGGLE KEY VISIBILITY
# -------------------


def toggleAndKeyVisibility(message=True):
    """Inverts the visibility of an object in Maya and keys it's visibility attribute
    Works on selected objects. Example:

        "cube1.visibility True"
        becomes
        "cube1.visibility False"
        and the visibility attribute is also keyed

    """
    selObjs = cmds.ls(selection=True)
    for obj in selObjs:
        if not attributes.isSettable(obj, "visibility"):
            if message:
                output.displayWarning("The visibility of the object {} is locked or connected. "
                                      "Keyframe toggle skipped.".format(obj))
            continue
        if cmds.getAttr("{}.visibility".format(obj)):  # if visibility is True
            cmds.setAttr("{}.visibility".format(obj), 0)
        else:  # False so set visibility to True
            cmds.setAttr("{}.visibility".format(obj), 1)
        cmds.setKeyframe(obj, breakdown=False, hierarchy=False, attribute="visibility")


def transferAnimationLists(oldObjList, newObjList, message=True):
    """Transfers animation from one object list to another.

    :param oldObjList: Object/node list, the old objects with current animation
    :type oldObjList: list(str)
    :param newObjList: Object/node list, the new objects that will receive the animation.
    :type newObjList: list(str)
    :param message: Report a message to the user.
    :type message: bool
    """
    for i, oldNode in enumerate(oldObjList):
        if cmds.copyKey(oldNode):
            cmds.cutKey(newObjList[i], clear=True)
            cmds.pasteKey(newObjList[i])
    if message:
        output.displayInfo("Success: See Script Editor. Animation copied to "
                           "{}".format(namehandling.getShortNameList(newObjList)))


def transferAnimationSelected(message=True):
    """Transfers the animation of the first half of selected objects to the second half.

    Objects must be selected in order.

    :param message: Report a message to the user?
    :type message: bool
    """
    selObjs = cmds.ls(selection=True)

    if not selObjs:
        output.displayWarning("No objects were selected with animation to transfer")
        return False

    if (len(selObjs) % 2) != 0:  # Not even
        output.displayWarning("There is an odd number of objects selected, must be even")
        return False

    oldObjList = selObjs[:len(selObjs) // 2]
    newObjList = selObjs[len(selObjs) // 2:]

    if message:
        for i, jnt in enumerate(oldObjList):
            try:
                output.displayInfo("Animation Transfer: {} >> {}".format(jnt, newObjList[i]))
            except:
                pass

    transferAnimationLists(oldObjList, newObjList, message=True)


def copyPasteKeysCurveNode(sourceCurveNode, target, attr):
    """Copy from a maya animation curve node name to a target object and the given attribute.

    Curve node, target and attr must exist.

    :param sourceCurveNode: The name of the source curve node name "pCube1_translateX"
    :type sourceCurveNode: str
    :param target: The target object to paste the keys to
    :type target: str
    :param attr: The attribute to paste the anim to
    :type attr: str
    :return: Succeeded or not
    :rtype: bool
    """
    # Check attr not locked/connected
    if not attributes.isSettable(target, attr):
        return False
    # COpy/Paste keys
    cmds.copyKey(sourceCurveNode, time=(), option="curve")
    cmds.pasteKey(target, attribute=attr, option="replaceCompletely")
    return True


def copyPasteKeys(source, target, attr, targetAttr=None, start=0, end=1000, mode="replace",
                  maintainStartEnd=True, includeStaticValues=True):
    """Copy Paste keyframes with error checking if fails.

    paste modes are:
        "insert", "replace", "replaceCompletely", "merge", "scaleInsert," "scaleReplace", "scaleMerge",
        "fitInsert", "fitReplace", and "fitMerge"

    :param source: The source obj/node to have copied keys
    :type source: str
    :param target: The target obj/node to have pasted keys
    :type target: str
    :param attr: the attribute to copy and paste
    :type attr: str
    :param targetAttr: Optional target attribute if different from the attr
    :type targetAttr: str
    :param start: The start frame, ignored if maintainStartEnd
    :type start: float
    :param end: The end frame, ignored if maintainStartEnd
    :type end: float
    :param mode: The copy paste mode. "insert", "replace", "merge" etc see description.
    :type mode: str
    :param maintainStartEnd: Copies only the time-range from the copied attr, otherwise use start end
    :type maintainStartEnd: bool
    :param includeStaticValues: Will copy values that do not have keyframes
    :type includeStaticValues: bool

    :return keyPasted: True if keys were successfully pasted, False if not.
    :rtype keyPasted: bool
    """
    if not targetAttr:
        targetAttr = attr
    if maintainStartEnd:
        keys = cmds.keyframe(".".join([source, attr]), query=True)
        if keys:
            start = keys[0]
            end = keys[-1]
        else:  # No keyframes
            if includeStaticValues:
                if not attributes.isSettable(target, attr):
                    return False
                try:  # TODO more robust code for set attribute values
                    value = cmds.getAttr(".".join([source, attr]))
                    cmds.setAttr(".".join([target, attr]), value)
                except:  # attribute could not be set.
                    pass
            return False
    if not cmds.copyKey(source, time=(start, end), attribute=attr, option="curve"):
        return False
    # Check attr not locked/connected
    if not attributes.isSettable(target, attr):
        return False
    # Paste keys
    cmds.pasteKey(target, time=("{}:".format(start),), attribute=targetAttr, option=mode)
    return True
