from zoo.libs.maya.mayacommand import command


class ZooResetTransform(command.ZooCommandMaya):
    """Reset's all provided node transforms in transform space.
    """
    id = "zoo.nodes.resetTransform"
    isUndoable = True
    _nodesTransforms = None

    def resolveArguments(self, arguments):
        nodes = arguments.get("nodes")
        if not nodes:
            self.cancel("Please provide at least one node!")
        valid = []
        for n in iter(nodes):
            # skip invalid nodes
            if not n:
                continue
            matrix = n.matrix()
            valid.append((n, matrix))
        self._nodesTransforms = valid
        if not valid:
            self.cancel("No valid node to rename, either the nodes don't exist or the names are the same")
        return {"nodes": tuple(valid)}

    def doIt(self, nodes=None, translate=True, rotate=True, scale=True):
        """
        :param nodes: a list of DagNodes to have their transforms reset
        :type nodes: list[:class:`zoo.libs.maya.zapi.DagNode`]
        :param translate: If True reset the translation channel
        :type translate: bool
        :param rotate: If True reset the rotation channel
        :type rotate: bool
        :param scale: If True reset the scale channel
        :type scale: tuple[float]
        """
        for n, _ in self._nodesTransforms:
            n.resetTransform(translate, rotate, scale)

    def undoIt(self):
        for n, origTransform in self._nodesTransforms:
            if n:
                n.setMatrix(origTransform)
            return True
        return False
