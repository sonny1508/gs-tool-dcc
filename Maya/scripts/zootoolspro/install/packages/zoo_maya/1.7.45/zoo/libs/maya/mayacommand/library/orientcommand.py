from zoo.libs.maya import zapi
from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.utils import mayamath
from zoo.libs.maya.rig import align


class OrientNodesCommand(command.ZooCommandMaya):
    id = "zoo.maya.orientNodes"
    isUndoable = True
    useUndoChunk = True
    _transformCache = []

    def resolveArguments(self, arguments):
        nodes = arguments.get("nodes", [])
        if not arguments.get("nodes"):
            self.cancel("No valid no passed to command")
        elif len(nodes) < 2:
            self.cancel("Must pass at least 2 nodes to command")
        return arguments

    def doIt(self, nodes=None,
             primaryAxis=mayamath.XAXIS_VECTOR,
             secondaryAxis=mayamath.YAXIS_VECTOR,
             worldUpAxis=None,
             skipEnd=True):
        """Given the provided nodes each node will be aligned to the next in the list

        For the sake of flexibly in how to apply the rotations depending on
        client workflow and node types, all rotations will be applied directly to
        the world rotations , for joints their joint orient will be reset to zero.


        :param nodes: The full list of nodes from parent to child.
        :type nodes: list[:class:`zapi.DagNode`]
        :param worldUpAxis: The calculated Plane to align all nodes too.
        :type worldUpAxis: :class:`om2.MVector`
        :param primaryAxis: The primary(aim) axis for each node.
        :type primaryAxis: :class:`om2.MVector`
        :param secondaryAxis: The Secondary vector for all the nodes in the chain.
        :type secondaryAxis: :class:`om2.MVector`
        :param skipEnd: If True the last node will not be aligned.
        :type skipEnd: bool
        """
        self._transformCache = []
        for n in nodes:
            transform = [n.translation(space=zapi.kTransformSpace),
                         n.rotation(space=zapi.kTransformSpace, asQuaternion=False),
                         n.scale(space=zapi.kObjectSpace)]
            if n.hasFn(zapi.kNodeTypes.kJoint):
                transform.append(n.jointOrient.value())
            self._transformCache.append((n.handle(),
                                         transform))
        if not nodes:
            return False
        align.orientNodes(nodes, primaryAxis, secondaryAxis, worldUpAxis=worldUpAxis, skipEnd=skipEnd)

        return True

    def undoIt(self):
        for n, transform in self._transformCache:
            if not n.isValid() or not n.isAlive():
                continue
            zChild = zapi.nodeByObject(n.object())
            children = zChild.children(nodeTypes=(zapi.kNodeTypes.kJoint, zapi.kNodeTypes.kTransform))
            for ch in children:
                ch.setParent(None)
            zChild.setTranslation(transform[0], space=zapi.kTransformSpace)
            zChild.setRotation(transform[1], space=zapi.kTransformSpace)
            zChild.setScale(transform[2])
            if len(transform) == 4:
                zChild.jointOrient.set(transform[-1])
            for ch in children:
                ch.setParent(zChild)
