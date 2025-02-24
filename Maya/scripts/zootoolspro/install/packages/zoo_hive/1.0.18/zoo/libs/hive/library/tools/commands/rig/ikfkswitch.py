from zoo.libs.maya.mayacommand import command
from zoo.libs.maya import zapi
from zoo.core.util import zlogging
from zoo.libs.maya.api import anim
from maya.api import OpenMayaAnim as om2Anim
from maya import cmds


logger = zlogging.getLogger(__name__)


def _ikfkMatchFilterCallback(keys, ikfkAttr, requestedState):
    """Validates the keys to see if it requires a change based on the IKFK state

    :param node: The node to check
    :type node: :class:`zapi.DagNode`
    :param ikfkAttr: The ikfkBlend attribute
    :type ikfkAttr: :class:`Plug`
    :param requestedState:
    :type requestedState: The ikfk state that we're switching too.
    :return: The valid list of keys which need to be changed.
    :rtype: list[float]
    """
    validKeys = []
    currentUnit = anim.currentTimeInfo()["unit"]
    for key in keys:
        ctx = zapi.DGContext(zapi.Time(key, currentUnit))
        value = ikfkAttr.value(ctx)
        if value == requestedState:
            continue

        validKeys.append(key)

    return validKeys


class IKFKMatchCommand(command.ZooCommandMaya):
    """Switches between IK FK while matching the transforms of the jnts/controls.
    """
    id = "hive.rig.ikfkMatch"

    isUndoable = True
    isEnabled = True

    _cache = []  # {"state"}
    _allKeyTimes = []

    def resolveArguments(self, arguments):
        components = arguments["components"]
        frameRange = arguments["frameRange"]
        bakeEveryFrame = arguments["bakeEveryFrame"]
        cache = []
        allKeyTimes = set()
        requestedState = arguments["state"]

        # first gather the positions and ik fk state for undo
        for comp in components:
            if not hasattr(comp, "hasIkFk"):
                continue

            rigLayer = comp.rigLayer()
            controlPanel = comp.controlPanel()
            state = controlPanel.ikfk.value()

            if not requestedState:
                # controls which will be needing Undo, also will have keys removed
                ctrlIds = comp.ikControlIds
                # controls which we need to copy key frame times from ignore the value though
                keyFrameCtrls = comp.fkControlIds
            else:
                ctrlIds = comp.fkControlIds
                keyFrameCtrls = comp.ikControlIds

            ctrls = rigLayer.findControls(*ctrlIds)
            keyFrameCtrls = rigLayer.findControls(*keyFrameCtrls)

            undoData = {"state": state,
                        "component": comp
                        }
            compKeys = set()
            if frameRange:
                for ctrl, keyInfo in zapi.keyFramesForNodes(keyFrameCtrls, ["rotate", "translate", "scale", "ikfk"],
                                                            bakeEveryFrame=bakeEveryFrame,
                                                            frameRange=frameRange):
                    keys = keyInfo["keys"]
                    if keys:
                        compKeys.update(keys)
                compKeys = _ikfkMatchFilterCallback(compKeys, ikfkAttr=controlPanel.ikfk, requestedState=requestedState)
                if not compKeys:
                    continue
            for ctrl in ctrls:
                pos = ctrl.matrix()
                undoData.setdefault("transformCache", []).append((ctrl, pos))
            undoData["keys"] = sorted(compKeys)
            allKeyTimes.update(compKeys)
            cache.append(undoData)
        self._cache = cache
        self._allKeyTimes = sorted(allKeyTimes)
        return arguments

    def doIt(self, components=None, state=0, frameRange=None, bakeEveryFrame=True):
        selectables = []
        func = "switchToIk" if not state else "switchToFk"
        if frameRange is None:
            for info in self._cache:
                comp = info["component"]
                ikFkData = getattr(comp, func)()
                selectables.extend(ikFkData["selectables"])
        else:
            executedOnce = False
            # purge all current keys on the ctrls before we bake otherwise when we bake to current keys
            #  based on current space we'll skip certain keys.
            transformAttrs = ["translate", "rotate", "scale"]
            for info in self._cache:
                componentKeys = info["keys"]
                ranges = zapi.animation.frameRanges(componentKeys)
                ctrlNames = [ctrl.fullPathName() for ctrl, _ in info["transformCache"]]

                for frameRange in ranges:
                    cmds.cutKey(ctrlNames, time=frameRange, animation="objects",
                                attribute=transformAttrs, option="keys",
                                clear=1)

            with anim.maintainTime():
                for ctx in anim.iterFramesDGContext(self._allKeyTimes):
                    frame = ctx.getTime()
                    frameValue = frame.value
                    om2Anim.MAnimControl.setCurrentTime(frame)
                    for info in self._cache:
                        comp = info["component"]
                        if int(frameValue) not in info["keys"]:
                            continue
                        # ensure we're in the current space before we bake the frame otherwise we'll be baking to
                        # the same transform as the first frame.
                        controlPanel = info["component"].controlPanel()
                        switchAttr = controlPanel.attribute("ikfk")
                        switchAttr.set(not state)
                        if switchAttr.isAnimated():
                            cmds.setKeyframe(controlPanel.fullPathName(), attribute="ikfk",
                                             time=(frameValue, frameValue))
                        ikFkData = getattr(comp, func)()

                        # now keyframe transforms and extraAttrs ie. ballroll,ikfk etc
                        controlNames = [i.fullPathName() for i in ikFkData["controls"]]
                        extraAttrs = [(i.node().fullPathName(), i.partialName()) for
                                      i in ikFkData["attributes"]]
                        cmds.setKeyframe(controlNames, attribute=transformAttrs, time=(frameValue, frameValue))
                        for nodeName, attrName in extraAttrs:
                            cmds.setKeyframe(nodeName, attribute=attrName, time=(frameValue, frameValue))
                        if not executedOnce:
                            selectables.extend(ikFkData["selectables"])
                            executedOnce = True

        if selectables:
            zapi.select(selectables)

        return True

    def undoIt(self):
        for info in self._cache:
            comp = info["component"]
            if not comp:
                logger.error("Invalid undo state due to a component no longer existing!")
                continue
            oldState = info["state"]
            comp.controlPanel().ikfk.set(oldState)
            for ctrl, oldPos in info["transformCache"]:
                ctrl.setMatrix(oldPos)


class RecalculatePoleVectorCommand(command.ZooCommandMaya):
    """Switches between IK FK while matching the transforms of the jnts/controls.
    """
    id = "hive.rig.recalculatePoleVector"

    isUndoable = True
    isEnabled = True

    _cache = []
    _allKeyTimes = []
    _keyedObjectMapping = {}
    _modifier = None

    def resolveArguments(self, arguments):
        components = arguments["components"]
        cache = []

        frameRange = arguments.get("frameRange", [])
        bakeEveryFrame = arguments.get("bakeEveryFrame", True)
        if frameRange:
            frameRange[-1] = frameRange[-1] + 1
            allFramesWithinRange = range(*frameRange)

        # first gather the positions and ik fk state for undo
        allKeyTimes = set()
        keyedObjectMapping = {}
        for comp in components:
            if not hasattr(comp, "hasIkFk"):
                continue
            undoData = comp.prePlacePoleVectorSensibly()
            pvCtrl = undoData["upVecControl"]
            undoData["component"] = comp
            cache.append(undoData)
            if frameRange:
                controlAnim = zapi.keyFramesForNode(pvCtrl, ["rotate", "translate", "scale"],
                                                    defaultKeyFrames=allFramesWithinRange,
                                                    bakeEveryFrame=bakeEveryFrame,
                                                    frameRange=frameRange)
                keys = controlAnim["keys"]
                if keys:
                    allKeyTimes.update(keys)
                keyedObjectMapping[pvCtrl] = controlAnim
        self._allKeyTimes = sorted(allKeyTimes)
        self._keyedObjectMapping = keyedObjectMapping
        self._cache = cache
        return arguments

    def doIt(self, components=None, frameRange=None, bakeEveryFrame=True):
        self._modifier = zapi.dgModifier()
        if frameRange is None:
            for info in self._cache:
                info["component"].placePoleVectorSensibly(info)

        else:
            with anim.maintainTime():
                for ctx in anim.iterFramesDGContext(self._allKeyTimes):
                    frame = ctx.getTime()
                    currentFrameValue = frame.value
                    om2Anim.MAnimControl.setCurrentTime(frame)
                    for info in self._cache:
                        ctrl = info["upVecControl"]
                        keyFrames = self._keyedObjectMapping[ctrl]
                        if int(currentFrameValue) not in keyFrames["keys"]:
                            continue
                        info["component"].placePoleVectorSensibly(info, keyRange=(currentFrameValue, currentFrameValue))


        ctrls = [info["upVecControl"] for info in self._cache]
        zapi.select(ctrls, mod=self._modifier)
        return True

    def undoIt(self):
        for info in self._cache:
            ctrl = info["upVecControl"]
            ctrl.setWorldMatrix(info["transformCache"])
        self._modifier.undoIt()
