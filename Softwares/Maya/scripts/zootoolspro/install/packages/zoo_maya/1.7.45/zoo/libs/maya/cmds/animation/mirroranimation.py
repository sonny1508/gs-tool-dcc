"""Mirror/symmetry copy/poste animation related code.


    from zoo.libs.maya.cmds.animation import mirroranimation
    source = "pCube_L"
    target = "pCube_R"
    flipCurveAttrs = ["translateX", "rotateY", "rotateZ"]
    mirroranimation.mirrorPasteAnimObj(source, target, 1.0, 25.0, cyclePre="cycle", cyclePost="cycle", mode="replace",
                                      flipCurveAttrs=flipCurveAttrs, offset=0.0, matchRange=False, proxyAttrs=True)

"""

from maya import cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import attributes, selection
from zoo.libs.maya.cmds.animation import keyframes, bakeanim

FLIP_STANDARD_WORLD = ["translateX", "rotateY", "rotateZ"]
FLIP_STANDARD_FK = ["translateX", "translateY", "translateZ"]

ANIM_TRANSFER_GRP = "animTransferZoo_grp"


def limitRangeKeys(obj, attrList, startFrame, endFrame):
    animCurves = list()
    # limit the range of keys on the target (cleanup extra frame to be the same as start and end)
    for attr in attrList:
        animCurve = ".".join([obj, attr])
        if cmds.keyframe(animCurve, query=True, keyframeCount=True):  # Has keys
            animCurves.append(".".join([obj, attr]))
    if animCurves:
        bakeanim.bakeLimitKeysToTimerange(startFrame, endFrame, animCurves)


def mirrorPasteAnimAttrs(source, target, attrList, startFrame, endFrame, mode="replace", offset=0.0,
                         flipCurveAttrs=None, cyclePre="cycle", cyclePost="cycle", limitRange=False,
                         includeStaticValues=True):
    """Copy/pastes animation from a source to target and can potentially flip attributes and offset for cycles.

    :param source: The source object to copy animation from
    :type source: str
    :param target: The target object to copy animation to
    :type target: str
    :param attrList: A list of attribute names to copy
    :type attrList: list(str)
    :param startFrame: The start frame of the cycle, should match the first frame
    :type startFrame: float
    :param endFrame: The end frame of the cycle, should match the first frame
    :type endFrame: float
    :param mode: The paste mode, "replace" by default see cmds.pasteKey() option documentation
    :type mode: str
    :param offset: The amount of frames to offset the pasted animation.
    :type offset: float
    :param flipCurveAttrs: Attributes to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(str)
    :param cyclePre: The mode of the pre cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePre: str
    :param cyclePost: The mode of the post cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePost: str
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool

    :return success:  Did the copy/paste succeed?
    :rtype success: bool
    """
    animCurves = list()
    if not flipCurveAttrs:
        flipCurveAttrs = list()
    success = False

    for attr in attrList:
        targetCurve = ".".join([target, attr])
        if mode == "replace":
            # Remove existing keys on target
            cmds.cutKey(target, time=(-10000, 100000), attribute=attr)  # Delete if all keys before paste

        # Copy/paste the keys, static values and flip ----------------
        if keyframes.copyPasteKeys(source, target, attr, start=startFrame, end=endFrame, mode=mode,
                                   includeStaticValues=includeStaticValues):  # If copied keys
            if attr in flipCurveAttrs:  # Flip curves
                cmds.scaleKey(targetCurve, time=(), valueScale=-1.0, valuePivot=0.0)
            if offset:  # Offset frames
                cmds.keyframe(targetCurve, time=(), edit=True, relative=True, timeChange=offset)
            success = True
        else:  # Flip static value if float
            if attr in flipCurveAttrs:  # Flip curves
                value = cmds.getAttr(".".join([source, attr]))
                if isinstance(value, float):
                    try:
                        cmds.setAttr(".".join([target, attr]), value * -1.0)
                    except:
                        pass

    # Set to cycle pre post
    cmds.setInfinity(target, attribute=attrList, preInfinite=cyclePre, postInfinite=cyclePost)

    if limitRange:  # limit the range of keys on the target (cleanup extra frame to be the same as start and end)
        limitRangeKeys(target, attrList, startFrame, endFrame)

    return success


def mirrorPoseLeftRight(source, target, attrList, flip=True, flipCurveAttrs=None):
    """Takes the current pose of the source object and mirrors it to the target object.

    flipCurveAttrs is a list of attributes to flip (scale -1.0) around zero value.

    :param source: The source object
    :type source: str
    :param target: The target object
    :type target: str
    :param attrList: A list of attribute names to copy
    :type attrList: list(str)
    :param flip: If True then will flip the attributes, switches the left and right values. If False will copy only.
    :type flip: bool
    :param flipCurveAttrs: Attributes to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(str)
    """
    oppositeValue = 0.0
    for attr in attrList:
        if flip:
            oppositeValue = cmds.getAttr(".".join([target, attr]))
        value = cmds.getAttr(".".join([source, attr]))
        if isinstance(value, float):
            try:
                if flipCurveAttrs:
                    if attr in flipCurveAttrs:
                        cmds.setAttr(".".join([target, attr]), value * -1.0)
                        if flip:
                            cmds.setAttr(".".join([source, attr]), oppositeValue * -1.0)
                        continue
                cmds.setAttr(".".join([target, attr]), value)
                if flip:
                    cmds.setAttr(".".join([source, attr]), oppositeValue)
            except:
                pass


def pasteAndFlipAttrAnim(target, attr, sourceCurve, sourceVal, flipCurveAttrs=None):
    """Pastes and potentially flips the animation from a sourceCurve to a target.attribute.

    :param target: Target node to paste the animation to
    :type target: str
    :param attr: the attribute to paste the animation to
    :type attr: str
    :param sourceCurve: The source curve to copy from, maya node name.
    :type sourceCurve: str
    :param sourceVal: The static value to paste if no sourceCurve
    :type sourceVal: float
    :param flipCurveAttrs: A list of the curves to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(float)
    """
    if not sourceCurve:  # Then paste as static value -----------------------------------
        if cmds.keyframe(target, attribute=attr, query=True, keyframeCount=True):  # Has keys
            cmds.cutKey(target, time=(), attribute=attr)  # Delete all keys
        if attr in flipCurveAttrs:
            cmds.setAttr(".".join([target, attr]), sourceVal * -1.0)
        else:
            cmds.setAttr(".".join([target, attr]), sourceVal)
        return
    # Copy/paste the animation ---------------------------------------------------
    keyframes.copyPasteKeysCurveNode(sourceCurve, target, attr)

    if flipCurveAttrs:
        if attr in flipCurveAttrs:  # then invert
            cmds.scaleKey(target, attribute=attr, valueScale=-1.0, valuePivot=0.0)


def flipAnimationAttr(source, target, attr, flip=True, flipCurveAttrs=None):
    """Flips or mirrors an animated pair of objects, leftFoot.translateX to rightFoot.translateX for example.

    If flip is False will mirror the opposite side only. If flip is True will flip both sides.

    :param source: The source node/object name to copy the animation from
    :type source: str
    :param target: The target node/object name to paste the animation to
    :type target: str
    :param attr: The attribute to copy and paste
    :type attr: str
    :param flip: Flip will copy the animation from the target to the source as well, otherwise is a mirror copy only.
    :type flip: bool
    :param flipCurveAttrs: A list of the curves to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(str)
    """
    targetValue = None
    sourceValue = None
    targetDupCurve = ""

    if not cmds.attributeQuery(attr, node=target, exists=True):  # check if the attribute exists
        return

    # Copy the data, depending if static value or anim curve --------------------------------
    sourceOrigCurve = cmds.keyframe(".".join([source, attr]), query=True, name=True)
    if not sourceOrigCurve:  # get the static value
        sourceValue = cmds.getAttr(".".join([source, attr]))
    if flip:
        targetOrigCurve = cmds.keyframe(".".join([target, attr]), query=True, name=True)
        if not targetOrigCurve:  # get the static value
            targetValue = cmds.getAttr(".".join([target, attr]))
        else:
            targetDupCurve = cmds.duplicate(targetOrigCurve)[0]

    # Paste the animation To Target -------------------------
    pasteAndFlipAttrAnim(target, attr, sourceOrigCurve, sourceValue,
                         flipCurveAttrs=flipCurveAttrs)

    if not flip:
        return

    # Paste the animation To Source (if flipping) -------------------------
    pasteAndFlipAttrAnim(source, attr, targetDupCurve, targetValue,
                         flipCurveAttrs=flipCurveAttrs)

    if targetDupCurve:  # cleanup
        cmds.delete(targetDupCurve)


def flipAnimation(source, target, attrList, flip=True, flipCurveAttrs=None):
    """Flips or mirrors an animated pair of objects, leftFoot to rightFoot for example.

    If flip is False will mirror the opposite side only. If flip is True will flip both sides.

    :param source: The source node/object name to copy the animation from
    :type source: str
    :param target: The target node/object name to paste the animation to
    :type target: str
    :param attrList: A list of the attributes to copy and paste
    :type attrList: list(str)
    :param flip: Flip will copy the animation from the target to the source as well, otherwise is a mirror copy only.
    :type flip: bool
    :param flipCurveAttrs: A list of the curves to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(str)
    """
    for attr in attrList:
        flipAnimationAttr(source, target, attr, flip=flip, flipCurveAttrs=flipCurveAttrs)


def flipCenterObject(obj, flipCurveAttrs):
    """Flips center object attributes around zero value.

    :param obj: The object who's attributes can be flipped
    :type obj: str
    :param flipCurveAttrs: A list of attributes to reverse
    :type flipCurveAttrs: list(str)
    """
    for attr in flipCurveAttrs:
        value = cmds.getAttr(".".join([obj, attr]))
        if isinstance(value, float):
            try:
                cmds.setAttr(".".join([obj, attr]), value * -1.0)
            except:
                pass


def flipCenterObjectAnimation(obj, attrList, flipCurveAttrs, startFrame, endFrame, cyclePre=None, cyclePost=None,
                              limitRange=False):
    """Flips the flipCurveAttrs around zero value for the object and cycles the animation.

    Optional set range and cyclePre and cyclePost modes.

    :param obj: The object who's attributes can be flipped
    :type obj: str
    :param attrList: A list of attribute names to copy
    :type attrList: list(str)
    :param flipCurveAttrs: List of attributes to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(str)
    :param startFrame: The start frame only used while limiting the range
    :type startFrame: float
    :param endFrame: The end frame only used while limiting the range
    :type endFrame: float
    :param cyclePre: pre cycle mode, see cmds.setInfinity() documentation.  None, "cycle", "constant", "stepped"
    :type cyclePre: str
    :param cyclePost: post cycle mode, see cmds.setInfinity() documentation.  None, "cycle", "constant", "stepped"
    :type cyclePost: str
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    """
    for attr in flipCurveAttrs:
        targetCurve = ".".join([obj, attr])
        # Test has animation
        if cmds.keyframe(targetCurve, query=True, keyframeCount=True):  # Has keys
            cmds.scaleKey(targetCurve, time=(), valueScale=-1.0, valuePivot=0.0)
            if cyclePre and cyclePost:
                cmds.setInfinity(obj, attribute=attr, preInfinite=cyclePre, postInfinite=cyclePost)
        else:  # No Animation so flip the static value
            value = cmds.getAttr(targetCurve)
            if isinstance(value, float):
                try:
                    cmds.setAttr(targetCurve, value * -1.0)
                except:
                    pass

    if limitRange:  # limit the range of keys on the target (cleanup extra frame to be the same as start and end)
        limitRangeKeys(obj, attrList, startFrame, endFrame)


def mirrorPasteAnimObj(source, target, startFrame, endFrame, cyclePre="cycle", cyclePost="cycle", mode="replace",
                       flipCurveAttrs=None, offset=0.0, limitRange=False, proxyAttrs=True):
    """Copy/pastes animation from a source to target and can potentially flip attributes and offset for cycles.

    This function uses channel box attributes for the mirror/copy/paste.

    :param source: The source object to copy animation from
    :type source: str
    :param target: The target object to copy animation to
    :type target: str
    :param startFrame: The start frame of the cycle, should match the first frame
    :type startFrame: float
    :param endFrame: The end frame of the cycle, should match the first frame
    :type endFrame: float
    :param cyclePre: The mode of the pre cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePre: str
    :param cyclePost: The mode of the post cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePost: str
    :param mode: The paste mode, "replace" by default see cmds.pasteKey() option documentation
    :type mode: str
    :param flipCurveAttrs: Attributes to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(str)
    :param offset: The amount of frames to offset the pasted animation.
    :type offset: float
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    :param proxyAttrs: If True the includes proxy attributes in the copy/paste
    :type proxyAttrs: bool

    :return success:  Did the copy/paste succeed?
    :rtype success: bool
    """
    # Get all channel box attributes
    attrList = attributes.channelBoxAttrs(source, settableOnly=True, includeProxyAttrs=proxyAttrs)
    # Mirror cycle obj
    return mirrorPasteAnimAttrs(source, target, attrList, startFrame, endFrame, mode=mode, offset=offset,
                                flipCurveAttrs=flipCurveAttrs, cyclePre=cyclePre, cyclePost=cyclePost,
                                limitRange=limitRange)


def mirrorPasteAnimSel(startFrame, endFrame, cyclePre="cycle", cyclePost="cycle", mode="replace",
                       flipCurveAttrs=None, offset=0.0, limitRange=False, proxyAttrs=True, includeStaticValues=True,
                       message=True):
    """

    :param startFrame: The start frame of the cycle, should match the first frame
    :type startFrame: float
    :param endFrame: The end frame of the cycle, should match the first frame
    :type endFrame: float
    :param cyclePre: The mode of the pre cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePre: str
    :param cyclePost: The mode of the post cycle, see cmds.setInfinity() documentation.  "cycle" "constant" "stepped"
    :type cyclePost: str
    :param mode: The paste mode, "replace" by default see cmds.pasteKey() option documentation
    :type mode: str
    :param flipCurveAttrs: Attributes to flip (scale -1.0) around zero value.
    :type flipCurveAttrs: list(str)
    :param offset: The amount of frames to offset the pasted animation.
    :type offset: float
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    :param proxyAttrs: If True the includes proxy attributes in the copy/paste
    :type proxyAttrs: bool
    :param includeStaticValues: If True copies/flips even if there are no keyframes.
    :type includeStaticValues: bool
    :param message: Report messages to the user?
    :type message: bool
    """
    success = False
    selObjs = cmds.ls(selection=True, type="transform")
    if not selObjs:
        if message:
            output.displayWarning("No objects have been selected")
        return
    if len(selObjs) == 1:
        if message:
            output.displayWarning("Please select more than one object, "
                                  "the first half of the selection will be copied to the second half.")
        return
    # Get optional channel box selection --------
    selAttrs = cmds.channelBox('mainChannelBox', q=True, sma=True) or cmds.channelBox('mainChannelBox', q=True,
                                                                                      sha=True)
    # Arrange the selected objects in pairs ----------------------
    sourceObs, targetObjs = selection.selectionPairs(oddEven=False, forceEvenSelection=True, type="transform")
    if not sourceObs:
        return  # warning already given
    # Do the mirror ----------------------
    for i, source in enumerate(sourceObs):
        if not selAttrs:
            result = mirrorPasteAnimObj(source, targetObjs[i], startFrame, endFrame, cyclePre=cyclePre,
                                        cyclePost=cyclePost, mode=mode, flipCurveAttrs=flipCurveAttrs, offset=offset,
                                        limitRange=limitRange, proxyAttrs=proxyAttrs)
        else:
            result = mirrorPasteAnimAttrs(source, targetObjs[i], selAttrs, startFrame, endFrame, mode=mode,
                                          offset=offset, flipCurveAttrs=flipCurveAttrs, cyclePre=cyclePre,
                                          cyclePost=cyclePost, limitRange=limitRange,
                                          includeStaticValues=includeStaticValues)
        if result:
            success = True
    if message:
        if success:
            output.displayInfo("Success: Animation copied.")
