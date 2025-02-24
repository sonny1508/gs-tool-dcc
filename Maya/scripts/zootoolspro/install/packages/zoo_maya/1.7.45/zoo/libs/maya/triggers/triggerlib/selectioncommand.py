from zoo.libs.maya import zapi
from zoo.libs.maya.triggers import triggerbase, constants
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class TriggerSelectionBase(triggerbase.TriggerCommand):
    baseType = constants.TRIGGER_BASE_TYPE_SELECTION
    # The maya attribute name which contains our command id
    COMMAND_ATTR_NAME = constants.COMMAND_ATTR_NAME
    # The maya attribute name which links to other nodes for selection on trigger.
    COMMAND_CONNECT_ATTR_NAME = constants.COMMAND_CONNECT_ATTR_NAME

    def attributes(self):
        return [
            {"name": constants.COMMAND_ATTR_NAME,
             "Type": zapi.attrtypes.kMFnDataString,
             "isArray": False, "value": "",
             "locked": True},
            {"name": constants.COMMAND_CONNECT_ATTR_NAME,
             "Type": zapi.attrtypes.kMFnMessageAttribute,
             "isArray": True,
             "locked": False},
        ]

    def commandStr(self):
        """Returns the python command string which will be executed.

        :rtype: str
        """
        attr = self._node.attribute(constants.COMMAND_ATTR_NAME)
        return attr.value()

    def setCommandStr(self, commandStr, mod=None, apply=True):
        """Sets the python string which will be executed each time a node is selected.
        Execute once per node.

        :param commandStr: The python command string, must support exec() function
        :type commandStr: str
        :param mod: The modifier to use for undo
        :type mod: :class:`zapi.dgModifier`
        :param apply: whether to immediately apply the change.
        :type apply: bool
        """
        attr = self._node.attribute(constants.COMMAND_ATTR_NAME)
        try:
            attr.lock(False)
            attr.set(commandStr, mod=mod, apply=apply)
        finally:
            attr.lock(True)

    def addNodesToConnectables(self, nodes, mod=None):
        """Adds the list of specified nodes to the current command.
        This nodes will be selected each time the node of the current command is selected.

        :param nodes: the list of DGNodes to add.
        :type nodes: list[:class:`zapi.DGNode`]
        :param mod: The undo modifier to use
        :type mod: :class:`zapi.dgModifier`
        """
        currentNode = self._node
        attr = currentNode.attribute(constants.COMMAND_CONNECT_ATTR_NAME)
        # grab all current connected nodes so we only add the missing
        sourceNodes = []
        for element in attr:
            source = element.sourceNode()
            if source is not None:
                sourceNodes.append(source)
        # update the plug array to include the missing nodes
        for newNode in nodes:
            if newNode in sourceNodes or newNode == currentNode:
                continue
            newElement = attr.nextAvailableDestElementPlug()
            newNode.message.connect(newElement, mod=mod)
            # to correctly get the next available element we have to first connect
            # the current op
            if mod is not None:
                mod.doIt()

    def clearNodes(self, mod=None):
        """Removes all currently connected nodes for this command.

        :param mod: The undo modifier to use.
        :type mod: :class:`zapi.dgModifier`
        """
        attr = self._node.attribute(constants.COMMAND_CONNECT_ATTR_NAME)
        for element in attr:
            element.disconnectAll(source=True, destinations=False, modifier=mod)

    def connectedNodes(self):
        """Returns all the currently assigned nodes for selection(connected)

        :return: A generator which returns each currently connected node
        :rtype: generator[:class:`zapi.DGNode`]
        """
        attr = self._node.attribute(constants.COMMAND_CONNECT_ATTR_NAME)
        for element in attr:
            sourceNode = element.sourceNode()
            if sourceNode:
                yield sourceNode

    def commandLocals(self):
        """Custom command locals to pass to the commandStr, only used by subclasses.

        :rtype: dict[str, any]
        """
        return {}

    def _executeCommandStr(self):
        """The internal method executes the python command string which was set
        via setCommandStr.
        """
        cmdStr = self.commandStr()
        if not cmdStr:
            return
        globalsDict = self.commandLocals()
        globalsDict["self"] = self
        globalsDict["connected"] = list(self.connectedNodes())
        try:
            exec(cmdStr, globalsDict)
        except Exception:
            logger.error("Failed to execute trigger: {}".format(self.id), exc_info=True)

    def execute(self):
        self._executeCommandStr()


class SelectConnectedCommand(TriggerSelectionBase):
    """This command selects all currently connected nodes then runs the command string
    """
    id = "selectConnected"

    def execute(self):
        connected = list(self.connectedNodes())
        if connected:
            zapi.select(connected)
        super(SelectConnectedCommand, self).execute()
