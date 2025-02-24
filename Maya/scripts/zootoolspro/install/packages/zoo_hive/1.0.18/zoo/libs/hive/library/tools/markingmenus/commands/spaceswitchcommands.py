from zoo.libs.utils import output
from zoo.core.util import zlogging
from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.meta import base as metabase
from zoo.libs.maya.api import anim
from zoo.libs.maya.cmds.animation import timerange
from zoo.libs.maya import zapi
from zoo.libs.hive import api
from maya.api import OpenMayaAnim as om2Anim
from maya import cmds


logger = zlogging.getLogger(__name__)


class HiveSpaceSwitch(menu.MarkingMenuCommand):
    """MM Command which allows switching spaces.
    """
    id = "hiveSpaceSwitch"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {"icon": "axis",
                "bold": False,
                "italic": False,
                "optionBox": False
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        # first cache all the node worldMatrices so we can set it back after we switch the attribute
        matrixCache = []
        for drivenNode in arguments["spaceNodes"]:  # :class:`zapi.DagNode`
            metaNodes = metabase.getConnectedMetaNodes(drivenNode)  # type: list[metabase.MetaBase]
            if not metaNodes:
                return
            hiveLayer = metaNodes[0]  # type: api.HiveRigLayer
            # rigLayer class has the required api to get the control from a given srt node
            if hiveLayer.isClassType(api.HiveRigLayer):
                controlNode = hiveLayer.controlForSrt(drivenNode)
                matrix = controlNode.worldMatrix()
                matrixCache.append((matrix, controlNode))
        if matrixCache:
            index = arguments["index"]
            # set the space switch attribute, we can have multiple components hence the loop
            for attr in arguments["controllerAttributes"]:
                cmds.setAttr(attr.name(), index)

            for matrix, node in matrixCache:
                cmds.xform(node.fullPathName(), m=matrix, ws=True)
            output.displayInfo("Completed space switching.")


class HiveSpaceSwitchBake(menu.MarkingMenuCommand):
    """MM Command which bakes space switch over a frame range.
    """
    id = "hiveSpaceSwitchBake"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        icon = "bake" if arguments["bakeEveryFrame"] else "key"
        return {"icon": icon,
                "bold": False,
                "italic": False,
                "optionBox": False
                }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """

        # node cache
        controlNodesCache = []
        # first cache all the node worldMatrices, so we can set it back after we switch the attribute
        startAndEndRange = list(map(int, timerange.getSelectedOrCurrentFrameRange()))
        startAndEndRange[-1] = startAndEndRange[-1] + 1
        frameRange = range(*startAndEndRange)
        bakeFrameFrame = arguments["bakeEveryFrame"]
        allKeyTimes = set()
        keyedObjectMapping = {}

        for drivenNode in arguments["spaceNodes"]:  # :class:`zapi.DagNode`
            metaNodes = metabase.getConnectedMetaNodes(drivenNode)  # type: list[metabase.MetaBase]
            if not metaNodes:
                return
            hiveLayer = metaNodes[0]  # type: api.HiveRigLayer
            # rigLayer class has the required api to get the control from a given srt node
            if not hiveLayer.isClassType(api.HiveRigLayer):
                continue
            controlNode = hiveLayer.controlForSrt(drivenNode)
            controlNodesCache.append(controlNode)
            controlAnim = zapi.keyFramesForNode(controlNode, ["rotate", "translate", "scale"],
                                                frameRange, bakeEveryFrame=bakeFrameFrame,
                                                frameRange=startAndEndRange)
            keys = controlAnim["keys"]
            if keys:
                allKeyTimes.update(keys)
            keyedObjectMapping[controlNode] = controlAnim

        allKeyTimes = sorted(allKeyTimes)
        # now loop the frame range
        spaceIndex = arguments["index"]
        with anim.maintainTime():
            frameCache = []
            # due to the fact maya doesn't correctly evaluate the next frame after we set the world matrix
            # we pre-evaluate the world matrix and for each node we grab the keyframes for TRS attributes.
            for frameNum, ctx in enumerate(anim.iterFramesDGContext(allKeyTimes)):

                matrixCache = [None] * len(controlNodesCache)
                # grab the current frames worldMatrices so we can set it back once we switch space
                for index in range(len(controlNodesCache)):
                    controlNode = controlNodesCache[index]
                    matrixCache[index] = (controlNode, controlNode.worldMatrix(ctx))
                frameCache.append(matrixCache)
            # loop back over the range and this time set the world matrix and set the keys.
            for frameIndex, ctx in enumerate(anim.iterFramesDGContext(allKeyTimes)):
                frame = ctx.getTime()
                frameNo = frame.value
                om2Anim.MAnimControl.setCurrentTime(frame)
                matrixCache = frameCache[frameIndex]

                if not matrixCache:
                    continue

                for attr in arguments["controllerAttributes"]:
                    attr.set(spaceIndex)
                    if attr.isAnimated():
                        cmds.setKeyframe(attr.node().fullPathName(), attribute=attr.partialName(useFullAttributePath=False),
                                         time=(frameNo, frameNo))


                for node, matrix in matrixCache:
                    keyMap = keyedObjectMapping[node]
                    nodeName = keyMap["name"]
                    if frameNo in keyMap["keys"]:
                        cmds.xform(nodeName, m=matrix, worldSpace=True)
                        for i in ("translate", "rotate", "scale"):
                            cmds.setKeyframe(nodeName, attribute=i, time=(frameNo, frameNo))

            for attr in arguments["controllerAttributes"]:
                cmds.setAttr(attr.name(), spaceIndex)

        output.displayInfo("Completed space switching.")
