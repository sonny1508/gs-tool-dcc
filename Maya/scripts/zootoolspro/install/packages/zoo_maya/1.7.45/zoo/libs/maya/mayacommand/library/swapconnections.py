from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.utils import gui
from zoo.libs.maya.api import nodes


class SwapConnectionsCommand(command.ZooCommandMaya):
    """This command Swaps the outgoing connections between two nodes
    """
    id = "zoo.maya.connections.swap.all"
    isUndoable = True
    _modifier = None

    def resolveArguments(self, arguments):
        plugs, sel = gui.selectedChannelboxAttributes()
        if len(sel) != 2:
            raise ValueError("Must have no more than 2 nodes selected")

        return {"source": sel[0], "target": sel[1], "plugs": plugs}

    def doIt(self, source=None, target=None, plugs=None):
        """

        :param source:
        :type source: :class:`om2.MObject`
        :param target:
        :type target: :class:`om2.MObject`
        :param plugs:
        :type plugs: list[`om2.MPlug`] or None
        :rtype: bool
        """
        self._modifier = nodes.swapOutgoingConnections(source, target, plugs)
        self._modifier.doIt()
        return True

    def undoIt(self):
        if self._modifier is not None:
            self._modifier.undoIt()
