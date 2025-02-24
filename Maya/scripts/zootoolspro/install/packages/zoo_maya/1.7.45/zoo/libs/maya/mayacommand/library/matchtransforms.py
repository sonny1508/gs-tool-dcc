from maya import cmds

from zoo.libs.maya.api import anim
from zoo.libs.maya.mayacommand import command
from zoo.libs.maya import zapi


class MatchTransformsCommand(command.ZooCommandMaya):
    """Given a list of nodes match the transforms of the second half to the first ie. 5->1 6->2
    """
    id = "zoo.maya.matchTransforms"
    isUndoable = True
    _nodeData = []
    _frameCache = {}  # DagNode: list[frameNum]

    def resolveArguments(self, arguments):
        useTranslate, useRotate, useScale = arguments["translate"], arguments["rotate"], arguments["scale"]
        nodes = [i for i in arguments.get("nodes") if i.hasFn(zapi.kNodeTypes.kDagNode)]
        # grab the length of the node list dropping the last index if it's an odd number
        nodesLength = len(nodes)
        if nodesLength < 2:
            self.cancel("Invalid Number of provided nodes, must be more than 1")
        nodesLength = nodesLength if nodesLength % 2 == 0 else nodesLength - 1

        data = []
        visited = {}
        # first element of each chunk is the parent
        for parent, child in zip(nodes[:int(nodesLength * 0.5)], nodes[int(nodesLength * 0.5):]):
            childName = child.fullPathName()
            if childName in visited:
                continue
            visited[childName] = child
            parentWorld = parent.transformationMatrix()
            currentChildWorld = child.transformationMatrix()
            if not useScale:
                parentWorld.setScale(currentChildWorld.scale(zapi.kWorldSpace), zapi.kWorldSpace)
            if not useTranslate:
                parentWorld.setTranslation(currentChildWorld.translation(zapi.kWorldSpace), zapi.kWorldSpace)
            if not useRotate:
                parentWorld.setRotation(currentChildWorld.rotation(asQuaternion=True))
            data.append(((parent, child), parentWorld, currentChildWorld))

        self._nodeData = data
        return arguments

    def doIt(self, nodes=None, translate=True, rotate=True, scale=True):
        for chunk, parentWorld, _ in self._nodeData:
            chunk[1].setWorldMatrix(parentWorld)

    def undoIt(self):
        for chunk, _, childWorld in self._nodeData:
            chunk[1].setWorldMatrix(childWorld)


class MatchTransformsBakeCommand(command.ZooCommandMaya):
    """Given a list of nodes match the transforms of the second half to the first ie. 5->1 6->2 over the
    provided frame Range, if the frame range isn't provided then the min max range will come from the individual
    nodes existing keyframes.
    """
    id = "zoo.maya.matchTransformsBake"
    isUndoable = True

    _nodeData = []
    _frameCache = {}
    _allKeyTimes = []

    def resolveArguments(self, arguments):
        useTranslate, useRotate, useScale = arguments["translate"], arguments["rotate"], arguments["scale"]
        bakeEveryFrame = arguments["bakeEveryFrame"]
        frameRange = arguments["frameRange"]
        nodes = [i for i in arguments.get("nodes") if i.hasFn(zapi.kNodeTypes.kDagNode)]
        # grab the length of the node list dropping the last index if it's an odd number
        nodesLength = len(nodes)
        if nodesLength < 2:
            self.cancel("Invalid Number of provided nodes, must be more than 1")
        nodesLength = nodesLength if nodesLength % 2 == 0 else nodesLength - 1

        data = []
        visited = {}
        frameCache = {}
        # used to optimize the keyGeneration to avoid doing this for every node
        allKeyFrames = frameRange or []
        if allKeyFrames:
            allKeyFrames = list(allKeyFrames)
            allKeyFrames[-1] = allKeyFrames[-1] + 1
            allKeyFrames = list(range(*tuple(allKeyFrames)))
        allFrames = set()
        # first element of each chunk is the parent
        for parent, child in zip(nodes[:int(nodesLength * 0.5)], nodes[int(nodesLength * 0.5):]):
            childName = child.fullPathName()
            if childName in visited:
                continue
            visited[childName] = child

            keyInfo = zapi.keyFramesForNode(parent, attributes=["rotate", "translate", "scale"],
                                            defaultKeyFrames=allKeyFrames,
                                            bakeEveryFrame=bakeEveryFrame, frameRange=frameRange)
            frameCache[child] = {"keys": keyInfo["keys"],
                                 "parent": parent,
                                 "matrices": []}
            allFrames.update(keyInfo["keys"])
            data.append((child, child.worldMatrix()))

        self._allKeyTimes = sorted(allFrames)
        _perKeyCache = {}
        for frameNum, ctx in enumerate(anim.iterFramesDGContext(self._allKeyTimes)):
            frameValue = ctx.getTime().value
            # matrixCache = {}
            for child, info in frameCache.items():
                keys = info["keys"]
                if frameValue not in keys:
                    continue
                parentWorld = zapi.TransformationMatrix(info["parent"].worldMatrix(ctx))
                currentChildWorld = zapi.TransformationMatrix(child.worldMatrix(ctx))
                if not useScale:
                    parentWorld.setScale(currentChildWorld.scale(zapi.kWorldSpace), zapi.kWorldSpace)
                if not useTranslate:
                    parentWorld.setTranslation(currentChildWorld.translation(zapi.kWorldSpace), zapi.kWorldSpace)
                if not useRotate:
                    parentWorld.setRotation(currentChildWorld.rotation(asQuaternion=True))
                frameCache[child]["matrices"].append(parentWorld)
        # now grab the
        self._nodeData = data
        self._frameCache = frameCache

        return arguments

    def doIt(self, nodes=None, translate=True, rotate=True, scale=True, bakeEveryFrame=False, frameRange=None):
        # purge all current keys on the ctrls before we bake otherwise when we bake to current keys
        #  based on current space we'll skip certain keys.
        transformAttrs = ["translate", "rotate", "scale"]
        for frameCacheChild, frameCacheInfo in self._frameCache.items():
            keys = frameCacheInfo["keys"]
            cmds.cutKey(frameCacheChild.fullPathName(), index=(min(keys), max(keys)),
                        attribute=transformAttrs, option="keys", clear=1)



        with anim.maintainTime():
            for frameIndex, ctx in enumerate(anim.iterFramesDGContext(self._allKeyTimes)):
                frame = ctx.getTime()
                frameNo = frame.value
                for frameCacheChild, frameCacheInfo in self._frameCache.items():
                    keys = frameCacheInfo["keys"]
                    if frameNo not in keys:
                        continue
                    frameMatrix = frameCacheInfo["matrices"][frameIndex]
                    frameCacheChild.setWorldMatrix(frameMatrix)
                    nodeName = frameCacheChild.fullPathName()
                    for i in ("translate", "rotate", "scale"):
                        cmds.setKeyframe(nodeName, attribute=i, time=(frameNo, frameNo))

    def undoIt(self):
        for child, worldMatrix in self._nodeData:
            child.setWorldMatrix(worldMatrix)
