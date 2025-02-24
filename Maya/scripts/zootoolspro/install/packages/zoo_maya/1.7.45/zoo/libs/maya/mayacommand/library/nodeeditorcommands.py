from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.qt import nodeeditor


class NodeAlignmentCommand(command.ZooCommandMaya):
    id = "zoo.maya.nodeEditor.alignment"
    isUndoable = True
    _previousNodePositions = None
    _nodeEditor = None

    def resolveArguments(self, arguments):
        editor = arguments.get("nodeEditor")

        if not editor:
            # defaults to the primary editor
            editor = nodeeditor.NodeEditorWrapper()
        nodes = editor.selectedNodeItems()
        self._nodeEditor = editor
        self._previousNodePositions = [(n, n.pos()) for n in nodes]
        if not arguments.get("align"):
            arguments["align"] = nodeeditor.ALIGN_LEFT
        if len(nodes) < 2:
            self.cancel("Must have more then 2 nodes selected! canceling command.")
        arguments.update({"nodeEditor": editor, "nodeItems": nodes})
        return arguments

    def doIt(self, nodeEditor=None, nodeItems=None, align=nodeeditor.ALIGN_LEFT):
        """Create the meta node based on the type parameter, if the type isn't specified then the baseMeta class will
        be used instead
        """
        if align == nodeeditor.ALIGN_LEFT:
            nodeEditor.alignLeft(nodeItems)
        elif align == nodeeditor.ALIGN_RIGHT:
            nodeEditor.alignRight(nodeItems)
        elif align == nodeeditor.ALIGN_TOP:
            nodeEditor.alignTop(nodeItems)
        elif align == nodeeditor.ALIGN_BOTTOM:
            nodeEditor.alignBottom(nodeItems)
        elif align == nodeeditor.ALIGN_CENTER_X:
            nodeEditor.alignCenterX(nodeItems)
        elif align == nodeeditor.ALIGN_CENTER_Y:
            nodeEditor.alignCenterY(nodeItems)
        elif align == nodeeditor.ALIGN_DIAGONALLY_LEFT_RIGHT:
            nodeEditor.alignItemsDiagonallyLeftToRight(nodeItems)
        elif align == nodeeditor.ALIGN_DIAGONALLY_RIGHT_LEFT:
            nodeEditor.alignItemsDiagonallyRightToLeft(nodeItems)
        return True

    def undoIt(self):
        if self._previousNodePositions is not None and self._nodeEditor.exists():
            for n, pos in self._previousNodePositions:
                n.setPos(pos)
