from zoo.libs.maya import zapi
from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.meta import base as meta

from maya.api import OpenMaya as om2


class CoPlanarCommand(command.ZooCommandMaya):
    id = "zoo.maya.planeOrient"
    isUndoable = True
    useUndoChunk = True
    _modifier = None
    _metaNode = None  # type: om2.MObjectHandle
    _transformCache = []

    def resolveArguments(self, arguments):
        if arguments.get("create"):
            return arguments
        elif arguments.get("align"):
            if not arguments.get("metaNode"):
                self.cancel("No MetaNode found")
            self._metaNode = arguments.get("metaNode").handle()

        return arguments

    def doIt(self, create=False, align=True, metaNode=None, skipEnd=False):
        """Create the meta node based on the type parameter, if the type isn't specified then the baseMeta class will
        be used instead

        """
        self._transformCache = []
        if create:
            _modifier = om2.MDGModifier()
            return meta.createNodeByType("zooPlaneOrient", mod=_modifier)
        else:
            if not self._metaNode.isValid() or not self._metaNode.isAlive():
                return False
            metaNode = meta.metaNodeByHandle(self._metaNode)
            nodes = metaNode.nodes()
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
            metaNode.projectAndAlign(skipEnd=skipEnd)

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
