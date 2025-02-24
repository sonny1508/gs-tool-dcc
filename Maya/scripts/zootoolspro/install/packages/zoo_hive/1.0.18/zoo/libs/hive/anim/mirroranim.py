"""Hive Mirror/symmetry copy/poste and Animation related tool code.

from zoo.libs.hive.anim import mirroranim
mirroranim.mirrorPasteHiveCtrlsSel(0, 24.0, offset=0.0, mirrorControlPanel=True, preCycle="cycle",
                               postCycle="cycle", limitRange=False)

"""

from collections import OrderedDict

from zoo.libs.maya import zapi
from zoo.libs.utils import output

from zoo.libs.hive import api as hiveapi
from zoo.libs.hive.anim.mirrorconstants import FLIP_ATTR_DICT, CENTER_FLIP_ATTR_DICT

from zoo.libs.maya.cmds.objutils import attributes
from zoo.libs.maya.cmds.animation import mirroranimation


# ---------------------------
# FLIP/MIRROR ANIM FUNCTIONS
# ---------------------------


def componentsAndIds():
    """Simple helper function that outputs the name of the selected controls, their components and IDs.

        from zoo.libs.hive.anim import mirror
        mirror.componentsAndIds()

    """
    selNodes = list(zapi.selected(filterTypes=zapi.kTransform))
    for node in selNodes:
        components = hiveapi.componentsFromNodes([node])
        component = list(components.keys())[0]
        output.displayInfo("---------------")
        output.displayInfo("Control: {}".format(node.fullPathName()))
        output.displayInfo("Component: {}".format(component.componentType))
        output.displayInfo("Side: {}".format(component.side()))
        output.displayInfo("ID: {}".format(hiveapi.ControlNode(node.object()).id()))


def selectedControlsIds():
    """Returns selected controls as zapi objects and their control ids

    :return:
    :rtype:
    """
    selIds = list()
    selControls = list()
    selNodes = list(zapi.selected(filterTypes=zapi.kTransform))

    for node in selNodes:
        controlId = hiveapi.ControlNode(node.object()).id()
        if not controlId or not node.hasFn(zapi.kNodeTypes.kTransform):
            continue
        selControls.append(node)
        selIds.append(controlId)

    return selControls, selIds


def controlPair(control, controlId):
    """From the animation control return information about the opposite control:

        targetCtrl: opposite control as zapi
        sourceComponent: The control's component as a python object
        targetComponent: The opposite control's component as a python object

    If none found returns three None types.

    :param control: control object as zapi will filter if not a control.
    :type control: :class:`zapi.DagNode`
    :param controlId: The name of the controls ID
    :type controlId: str
    :return oppositeInfo: Opposite information, see documentation.
    :rtype oppositeInfo: tuple()
    """
    components = hiveapi.componentsFromNodes([control])
    if not components:
        return None, None, None
    sourceComponent = list(components.keys())[0]  # first key will be the component object
    oppositeSideLabel = sourceComponent.namingConfiguration().field("sideSymmetry").valueForKey(sourceComponent.side())
    if not oppositeSideLabel:
        return None, None, None
    targetComponent = sourceComponent.rig.component(sourceComponent.name(), oppositeSideLabel)
    if not targetComponent:
        return None, None, None
    targetCtrl = targetComponent.rigLayer().control(controlId)
    if not targetCtrl:
        return None, None, None
    return targetCtrl, sourceComponent, targetComponent


def filterCenterControl(control):
    """Returns the control as a hiveApi component if it is a center node, else returns None

    :param control: The control as a zapi node
    :type control: :class:`zapi.DagNode`
    :return: The component object if it is a center control, else None
    :rtype: :class:`hiveapi.Component`
    """
    components = hiveapi.componentsFromNodes([control])
    if not components:
        return None
    component = list(components.keys())[0]
    if component.side() in ["C", "c", "M", "m", "ctr", "mid", "middle"]:
        return component
    return None


def controlPairDicts(controls, ids, message=True, removeDuplicates=False):
    """Returns lists of the anim control curve lists opposites (target controls) if they exist as a pairDictList.

    Returns a list of dicts, each dict has contents:

        "source": source controls as zapi node
        "target": target controls as zapi node
        "id": ids as str "endIk"
        "sourceComponent": source component object
        "targetComponent": source component object
        "componentType": component type as str "leg"

    :param controls: A list of source control as list(zapi)
    :type controls: list(:class:`zapi.DagNode`)
    :param ids: A list of string IDs ["endIk", "fk00"]
    :type ids: list(str)
    :param message: If True will report messages to the user
    :type message: bool
    :param removeDuplicates: If True will remove duplicates for flipping, only one control will be recorded for flip
    :type removeDuplicates: bool
    :return pairDictList: matching lists containing source/target controls, components, types and IDs.
    :rtype pairDictList: list(dict())
    """
    pairDictList = list()
    pairCheckList = list()  # for ignoring duplicates while flipping
    # iterate over all controls ---------------------
    for i, ctrl in enumerate(controls):
        targetCtrl, sourceComponent, targetComponent = controlPair(ctrl, ids[i])
        if not targetCtrl:
            if message:
                output.displayWarning("Skipping `{}`, no opposite found".format(ctrl.fullPathName(partialName=True)))
            continue
        if targetCtrl in controls:  # User has selected both pairs, use only one.
            if not removeDuplicates:
                output.displayWarning("Two mirrored controls selected. Select only one control per type, "
                                      "the control will be mirrored to its opposite.")
                return list()
            else:
                if ctrl in pairCheckList:  # ignore as is already added
                    continue
                pairCheckList.append(targetCtrl)
        # Opposite control found so add dict to pair list -------------------
        pairDictList.append({"source": ctrl,
                             "target": targetCtrl,
                             "sourceComponent": sourceComponent,
                             "targetComponent": targetComponent,
                             "id": ids[i],
                             "componentType": sourceComponent.componentType})
    return pairDictList


def flipAttrs(flipAttrDict, componentType, idVal):
    """Returns the flip attribute list from the flipAttrDict

    Usually FLIP_ATTR_DICT or CENTER_FLIP_ATTR_DICT

    :param flipAttrDict: the flip attribute dictionary FLIP_ATTR_DICT or CENTER_FLIP_ATTR_DICT
    :type flipAttrDict: dict
    :param componentType: The component type eg "armcomponent"
    :type componentType: str
    :param idVal: The Hive ID of the control eg "endIk"
    :type idVal: str
    :return: A list of attributes to flip
    :rtype: list(str)
    """
    flipAttrList = list()
    if componentType in flipAttrDict:
        compDict = flipAttrDict[componentType]
        if idVal in compDict:
            flipAttrList = compDict[idVal]
        else:  # Remove trail number from ID and try again ie "FK00" > "FK" or "lwrTwistOffset04" > "lwrTwistOffset"
            idTrailNumber = idVal.rstrip('0123456789')
            if idTrailNumber in compDict:
                flipAttrList = compDict[idTrailNumber]
    return flipAttrList


def mirrorPasteHiveCtrls(source, target, componentType, idVal, startFrame, endFrame, offset=0.0, preCycle="cycle",
                         postCycle="cycle", limitRange=False, animation=True):
    """

    :param source: The source control as zapi
    :type source: :class:`zapi.DagNode`
    :param target: The target control as zapi
    :type target: :class:`zapi.DagNode`
    :param componentType: The name of the Hive rig component type eg "armcomponent"
    :type componentType: str
    :param idVal: The Hive string id of the control "endIk"
    :type idVal: str
    :param startFrame: The start frame of the cycle (should match end pose)
    :type startFrame: float
    :param endFrame: The end frame of the cycle (should match start pose)
    :type endFrame: float
    :param offset: The offset in frames to offset the target animation.
    :type offset: float
    :param preCycle: The type of cycle to apply pre-infinity
    :type preCycle: str
    :param postCycle: The type of cycle to apply post-infinity
    :type postCycle: str
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    :param animation: If True then will copy the animation, if False will only copy ie for flipping
    :type animation: bool
    """
    # Build the flip attribute list from mirrorconstants.FLIP_ATTR_DICT ----------------
    flipAttrList = flipAttrs(FLIP_ATTR_DICT, componentType, idVal)

    # Get the attribute list from the channel box ignore proxies ---------------------
    attrList = attributes.channelBoxAttrs(source.fullPathName(), settableOnly=True, includeProxyAttrs=False)

    # Do the mirror ----------------------------
    if animation:
        mirroranimation.mirrorPasteAnimAttrs(source.fullPathName(),
                                             target.fullPathName(),
                                             attrList,
                                             startFrame,
                                             endFrame,
                                             mode="replace",
                                             offset=offset,
                                             flipCurveAttrs=flipAttrList,
                                             cyclePre=preCycle,
                                             cyclePost=postCycle,
                                             limitRange=limitRange)
    else:  # flip the pose, attrs only
        mirroranimation.mirrorPoseLeftRight(source.fullPathName(),
                                            target.fullPathName(),
                                            attrList,
                                            flipCurveAttrs=flipAttrList)


def mirrorPasteHiveCtrlsDict(pairDictList, startFrame, endFrame, offset=1.0, mirrorControlPanel=True, preCycle="cycle",
                             postCycle="cycle", limitRange=False):
    """PairDictList is a list of dicts, each dict has contents:

        "source": source controls as zapi node
        "target": target controls as zapi node
        "id": ids as str "endIk"
        "sourceComponent": source component object
        "targetComponent": source component object
        "componentType": component type as str "leg"

    :param pairDictList: pairDictList a list of dicts with information about the pairs to mirror (see description)
    :type pairDictList: list(dict)
    :param startFrame: The start frame of the cycle (should match end pose)
    :type startFrame: float
    :param endFrame: The end frame of the cycle (should match start pose)
    :type endFrame: float
    :param offset: The offset in frames to offset the target animation.
    :type offset: float
    :param mirrorControlPanel:
    :type mirrorControlPanel: bool
    :param preCycle: The type of cycle to apply pre-infinity
    :type preCycle: str
    :param postCycle: The type of cycle to apply post-infinity
    :type postCycle: str
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    """
    sourceComponents = list()
    targetComponents = list()

    # Mirror the controls and ignore proxy attributes (as they are Control Panel attrs) -----------------
    for pairDict in pairDictList:
        mirrorPasteHiveCtrls(pairDict["source"],
                             pairDict["target"],
                             pairDict["componentType"],
                             pairDict["id"],
                             startFrame,
                             endFrame,
                             offset=offset,
                             preCycle=preCycle,
                             postCycle=postCycle,
                             limitRange=limitRange)

    # Mirror the ControlPanel attrs ---------------------------------------------------------
    if not mirrorControlPanel:
        return

    # For controlPanels remove component duplicates and keep order --------------
    for pairDict in pairDictList:
        sourceComponents.append(pairDict["sourceComponent"])
        targetComponents.append(pairDict["targetComponent"])

    # remove duplicates --------
    sourceComponents = list(OrderedDict.fromkeys(sourceComponents))
    targetComponents = list(OrderedDict.fromkeys(targetComponents))

    # Iterate over components for the control panel settings -------------
    for i, sourceComp in enumerate(sourceComponents):
        sourceControlPanel = sourceComp.controlPanel()
        targetControlPanel = targetComponents[i].controlPanel()
        if targetControlPanel and sourceControlPanel:
            # Mirror the Hive control panel nodes
            mirrorPasteHiveCtrls(sourceControlPanel,
                                 targetControlPanel,
                                 sourceComp.componentType,
                                 "controlPanel",
                                 startFrame,
                                 endFrame,
                                 offset=offset,
                                 preCycle=preCycle,
                                 postCycle=postCycle,
                                 limitRange=limitRange)


def mirrorPasteHiveCtrlsSel(startFrame, endFrame, offset=0.0, mirrorControlPanel=True, preCycle="cycle",
                            postCycle="cycle", limitRange=False):
    """Main function that mirrors a Hive selected control to its opposite side.

    :param startFrame: The start frame of the cycle (should match end pose)
    :type startFrame: float
    :param endFrame: The end frame of the cycle (should match start pose)
    :type endFrame: float
    :param offset: The offset in frames to offset the target animation.
    :type offset: float
    :param mirrorControlPanel: Include the proxy attribtues in the mirror (Hive's control panel)
    :type mirrorControlPanel: bool
    :param preCycle: The type of cycle to apply pre-infinity
    :type preCycle: str
    :param postCycle: The type of cycle to apply post-infinity
    :type postCycle: str
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    """
    # TODO use the new cacheHiveControlsDict() function to get the components and control information
    controls, ids = selectedControlsIds()
    if not controls:
        output.displayWarning("No Hive controls selected")
        return
    pairDictList = controlPairDicts(controls, ids)
    if not pairDictList:
        return  # message reported
    mirrorPasteHiveCtrlsDict(pairDictList, startFrame, endFrame, offset=offset, mirrorControlPanel=mirrorControlPanel,
                             preCycle=preCycle, postCycle=postCycle, limitRange=limitRange)

    # Report success message -----------------
    controlList = list()
    for pairDict in pairDictList:
        controlList.append(pairDict["target"].fullPathName(partialName=True))
    output.displayInfo("Mirrored Animation: {}".format(controlList))
    output.displayInfo("Success: Items with pasted mirrored animation (see Script Editor for details)")


# ------------------------------------------------------------------------------------------------------
# FULL CHARACTER FLIP MIRRORING
# ------------------------------------------------------------------------------------------------------

def flipCenterControl(componentType, control, idVal, animation=False, settableOnly=True, includeProxyAttrs=False,
                      startFrame=0.0, endFrame=24.0, limitRange=False, cyclePre="cycle", cyclePost="cycle"):
    """Flips the center control based on its id in the CENTER_FLIP_ATTR_DICT

    :param componentType: The component type eg "armcomponent"
    :type componentType: str
    :param control: The name of the control as a zapi node
    :type control: :class:`zapi.DagNode`
    :param idVal: The Hive ID of the control eg "endIk"
    :type idVal: str
    :param animation: If True will flip the animation, if False will only flip the pose
    :type animation: bool
    :param settableOnly: Only include settable attributes in the flip Left/Right
    :type settableOnly: bool
    :param includeProxyAttrs: On the flip (Left/Right), include the proxy attributes (Hive's control panel)
    :type includeProxyAttrs: bool
    :param startFrame: The start frame of the cycle if animation = True, affects limit range
    :type startFrame: float
    :param endFrame: The end frame of the cycle if animation = True, affects limit range
    :type endFrame: float
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    """
    flipAttrList = flipAttrs(CENTER_FLIP_ATTR_DICT, componentType, idVal)
    if not flipAttrList:
        return
    # Do the flip ----------------------------
    if not animation:
        mirroranimation.flipCenterObject(control.fullPathName(), flipAttrList)
    else:
        attrList = attributes.channelBoxAttrs(control.fullPathName(), settableOnly=settableOnly,
                                              includeProxyAttrs=includeProxyAttrs)
        mirroranimation.flipCenterObjectAnimation(control.fullPathName(), attrList, flipAttrList, startFrame=startFrame,
                                                  endFrame=endFrame, limitRange=limitRange, cyclePre=cyclePre,
                                                  cyclePost=cyclePost)


def flipTwoNodes(nodeA, nodeB, componentType, animation, controlId, settableAttrsOnly, proxyAttrs, flip):
    """Flips nodeA's pose to its opposite side.

    Flip if flip = True, otherwise mirrors the control.

    :param nodeA: The source control as zapi node
    :type nodeA: :class:`zapi.DagNode`
    :param nodeB: The target control as zapi node
    :type nodeB: :class:`zapi.DagNode`
    :param componentType: The component type eg "armcomponent"
    :type componentType: str
    :param controlId: The Hive ID of the control eg "endIk"
    :type controlId: str
    :param settableAttrsOnly: Only include settable attributes in the flip Left/Right
    :type settableAttrsOnly: bool
    :param proxyAttrs: On the flip (Left/Right), include the proxy attributes
    :type proxyAttrs: bool
    """
    attrList = attributes.channelBoxAttrs(nodeA.fullPathName(),
                                          settableOnly=settableAttrsOnly,
                                          includeProxyAttrs=proxyAttrs)
    flipAttrList = flipAttrs(FLIP_ATTR_DICT, componentType, controlId)

    if not animation:
        mirroranimation.mirrorPoseLeftRight(nodeA.fullPathName(),
                                            nodeB.fullPathName(),
                                            attrList,
                                            flip=flip,
                                            flipCurveAttrs=flipAttrList)
    else:
        mirroranimation.flipAnimation(nodeA.fullPathName(),
                                      nodeB.fullPathName(),
                                      attrList,
                                      flip=flip,
                                      flipCurveAttrs=flipAttrList)


def flipPoseCtrls(allControlsDict, flip=True, proxyAttrs=False, settableAttrsOnly=True, flipControlPanel=True,
                  includeProxyAttrs=False, animation=False, startFrame=0.0, endFrame=24.0, limitRange=False,
                  cyclePost="cycle", cyclePre="cycle"):
    """Flips the selected Hive controls to their opposite side.

    If flip is True is a flip mirror, otherwise it's a copy mirror, left is copied to right.

    Center controls will always be flipped.

    :param allControlsDict: A list of source control as list(zapi)
    :type allControlsDict: list(:class:`zapi.DagNode`)
    :param flip: If True will flip the source object to be the target objects values (only left/right)
    :type flip: bool
    :param proxyAttrs: On the flip (Left/Right), include the proxy attributes (Hive's control panel)
    :type proxyAttrs: bool
    :param settableAttrsOnly: Only include settable attributes in the flip Left/Right
    :type settableAttrsOnly: bool
    :param flipControlPanel: If True will flip the control panel node of each component too
    :type flipControlPanel: bool

    :param animation: If True will flip the animation, if False will only flip the pose
    :type animation: bool
    :param startFrame: The start frame of the cycle (should match end pose)
    :type startFrame: float
    :param endFrame: The end frame of the cycle (should match start pose)
    :type endFrame: float
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    """
    sideDict = dict()
    centerComponents = list()
    pairComponents = list()

    # Flip Mirror the center controls and record sideDict pairs ---------------------
    for key, controlInfo in allControlsDict.items():
        if controlInfo["oppositeSide"]:  # is not a center control
            sideDict[key] = dict(controlInfo)
            continue
        if not flip:
            continue
        component = controlInfo["component"]
        control = controlInfo["control"]
        controlId = controlInfo["controlId"]
        flipCenterControl(component.componentType, control, controlId, animation=animation,
                          settableOnly=settableAttrsOnly, includeProxyAttrs=includeProxyAttrs,
                          startFrame=startFrame, endFrame=endFrame, limitRange=limitRange, cyclePost=cyclePost,
                          cyclePre=cyclePre)
        centerComponents.append(component)

    # Flip/Mirror Center Control Panels ---------------------
    if flipControlPanel and centerComponents:
        controlPanel = controlInfo["component"].controlPanel()
        if controlPanel:
            flipCenterControl(component.componentType, controlPanel, "controlPanel", animation=animation,
                              settableOnly=settableAttrsOnly, includeProxyAttrs=includeProxyAttrs,
                              startFrame=startFrame, endFrame=endFrame, limitRange=limitRange, cyclePost=cyclePost,
                              cyclePre=cyclePre)

    # Flip/Mirror Side Controls ---------------------
    if sideDict:
        for key, controlInfo in sideDict.items():
            if controlInfo["controlOpposite"]:  # opposite control may be None
                flipTwoNodes(controlInfo["control"],
                             controlInfo["controlOpposite"],
                             controlInfo["component"].componentType,
                             animation,
                             controlInfo["controlId"],
                             settableAttrsOnly, proxyAttrs, flip)
                pairComponents.append((controlInfo["component"], controlInfo["componentOpposite"]))

    # Flip Mirror the Control Panels ---------------------
    if pairComponents and flipControlPanel:
        pairComponents = list(set(pairComponents))  # remove duplicates
        for component, oppositeComponent in pairComponents:
            controlPanel = component.controlPanel()
            if controlPanel:
                flipTwoNodes(component.controlPanel(),
                             oppositeComponent.controlPanel(),
                             component.componentType,
                             animation,
                             "controlPanel",
                             settableAttrsOnly, proxyAttrs, flip)


def flipPoseCtrlsSelected(flip=True, proxyAttrs=False, settableAttrsOnly=True, animation=False, startFrame=0.0,
                          endFrame=24.0, limitRange=False, cyclePost=None, cyclePre=None):
    """Flips the selected Hive controls to their opposite side.

    If flip is True is a flip mirror, otherwise it's a copy mirror, left is copied to right.

    Center controls will always be flipped.

    :param flip: If True will flip the source object to be the target objects values (only left/right)
    :type flip: bool
    :param proxyAttrs: On the flip (Left/Right), include the proxy attributes (Hive's control panel), usually not
    :type proxyAttrs: bool
    :param settableAttrsOnly: Only include settable attributes in the flip Left/Right
    :type settableAttrsOnly: bool
    :param animation: If True will flip the animation, if False will only flip the pose
    :type animation: bool
    :param startFrame: The start frame of the cycle, only if animation, affects limit range
    :type startFrame: float
    :param endFrame: The end frame of the cycle, only if animation, affects limit range
    :type endFrame: float
    :param limitRange: If True then will force the copied animation on the target to start and end at the same frames.
    :type limitRange: bool
    :param cyclePost: The type of cycle to apply post-infinity only if animation, None, "cycle", "cycleOffset"
    :type cyclePost: str
    :param cyclePre: The type of cycle to apply pre-infinity only if animation, None, "cycle", "cycleOffset"
    :type cyclePre: str
    """
    allControlsDict = cacheHiveControlsDict(skipOpposite=flip)
    if not allControlsDict:
        output.displayWarning("No Hive controls selected")
        return
    flipPoseCtrls(allControlsDict, flip=flip, proxyAttrs=proxyAttrs, settableAttrsOnly=settableAttrsOnly,
                  animation=animation, startFrame=startFrame, endFrame=endFrame, limitRange=limitRange,
                  cyclePost=cyclePost, cyclePre=cyclePre)


def flipPoseCtrlsAll(flip=True, proxyAttrs=False, settableAttrsOnly=True):
    """Flips all Hive controls to their opposite side.

    If flip is True is a flip mirror, otherwise it's a copy mirror, left is copied to right.

    Center controls will always be flipped.

    :param flip: If True will flip the source object to be the target objects values (only left/right)
    :type flip: bool
    :param proxyAttrs: On the flip (Left/Right), include the proxy attributes (Hive's control panel)
    :type proxyAttrs: bool
    :param settableAttrsOnly: Only include settable attributes in the flip Left/Right
    :type settableAttrsOnly: bool
    """
    pass
    return  # Not implemented yet


def cacheHiveControlsDict(skipOpposite=False):
    """Creates a dictionary of all the selected Hive controls and their information.

    This cached information can be used for mirroring, flipping, and other operations.

    Example:

    {'arm:L:bendyMid01': {
                      'rigLayer': <HiveRigLayer> n1:arm_L_rigLayer_meta,
                      'component': <ArmComponent>-arm:L,
                      'componentTokenKey': 'arm:L',
                      'control': <DagNode> |n1:natalie_hrc|somePath|n1:arm_L_bendyMid01_bendy_anim,
                      'controlId': 'bendyMid01',
                      'controlPanel': <SettingsNode> n1:arm_L_controlPanel_settings,
                      'oppositeSide': 'R',
                      'side': 'L',
                      'oppositeTokenKey': 'arm:R',
                      }}

    :return: A dictionary of all the selected Hive controls and their information.
    :rtype: dict(dict)
    """
    keyList = list()
    allControlsDict = dict()
    controlDict = dict()

    components = hiveapi.componentsFromSelected()
    if not components:
        output.displayWarning("No Hive controls selected")
        return dict()
    for component, controls in components.items():
        componentOpposite = None
        rigName = component.rig.name()
        namespace = component.namespace()
        if namespace != ":":
            rigName = ":".join((namespace, rigName))

        componentTokenKey = component.serializedTokenKey()
        rigLayer = component.rigLayer()
        componentTokenKeyOpposite = None

        currentSide = componentTokenKey.split(":")[1]
        oppositeSide = component.namingConfiguration().field("sideSymmetry").valueForKey(component.side())

        if oppositeSide:
            tokenParts = componentTokenKey.split(":")
            tokenParts[1] = oppositeSide
            componentTokenKeyOpposite = ":".join(tokenParts)
            componentOpposite = component.rig.component(component.name(), oppositeSide)

        for control in controls:
            oppositeKey = ""
            controlOpposite = None
            try:
                controlId = hiveapi.ControlNode(control.object()).id()
            except RuntimeError:  # not a control node, could be a controlPanel node or other
                continue
            key = ":".join((rigName, componentTokenKey, controlId))
            if componentTokenKeyOpposite:
                oppositeKey = ":".join((rigName, componentTokenKeyOpposite, controlId))

            if oppositeKey in keyList and skipOpposite:
                continue
            if componentOpposite:
                try:  # opposite control may not exists twists etc
                    controlOpposite = componentOpposite.rigLayer().control(controlId)
                except:
                    pass
            controlDict["rigLayer"] = rigLayer
            controlDict["component"] = component
            controlDict["componentOpposite"] = componentOpposite
            controlDict["control"] = control
            controlDict["controlOpposite"] = controlOpposite
            controlDict["controlId"] = controlId
            controlDict["componentTokenKey"] = componentTokenKey
            controlDict["oppositeTokenKey"] = componentTokenKeyOpposite
            controlDict["side"] = currentSide
            controlDict["oppositeSide"] = oppositeSide
            allControlsDict[key] = dict(controlDict)
            keyList.append(key)

    return allControlsDict
