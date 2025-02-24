from zoo.core.util import zlogging
from zoo.libs.maya.meta import base
from zoo.core.plugin import plugin, pluginmanager
from zoo.core.util import classtypes
from zoo.libs.maya import zapi
from zoo.libs.maya.triggers import constants
from zoovendor import six

logger = zlogging.getLogger(__name__)


class NodeHasExistingCommand(Exception):
    pass


class NodeHasExistingTrigger(Exception):
    pass


class MissingRegisteredCommandOnNode(Exception):
    pass


@six.add_metaclass(classtypes.Singleton)
class TriggerRegistry(object):
    """Singleton class which manages all trigger commands
    """
    TRIGGER_ENV = constants.TRIGGER_ENV

    def __init__(self):
        super(TriggerRegistry, self).__init__()
        self.pluginManager = pluginmanager.PluginManager(interface=[TriggerCommand], variableName="id")
        self.pluginManager.registerByEnv(constants.TRIGGER_ENV)

    def commands(self):
        """

        :return:
        :rtype: dict[str, :class:`TriggerCommand`]
        """
        return self.pluginManager.plugins

    def commandTypes(self):
        """

        :return:
        :rtype: list[str]
        """
        return self.pluginManager.plugins.keys()

    def command(self, commandName):
        """

        :param commandName: the registered command unique id
        :type commandName: str
        :return:
        :rtype: callable[:class:`TriggerCommand`] or None
        """
        return self.pluginManager.plugins.get(commandName)


def commandFromNode(node):
    """Internal method to retrieve the command class object from the
    node. We don't initialize the command as we don't want to overhead
    in every query.

    :param node: The Node to find the command class on.
    :type node: :class:`zapi.DGNode`
    :return: the trigger command class, this is a uninitialized class
    :rtype: callable[:class:`TriggerCommand`] or None
    """

    triggerTypeAttr = node.attribute(constants.COMMANDTYPE_ATTR_NAME)
    if triggerTypeAttr is None:
        return
    triggerType = triggerTypeAttr.value()
    # backward compatibility
    if isinstance(triggerType, int):
        # triggerType = TriggerNode.upgradeNode(node)
        # todo: rolling update handling
        triggerType = "triggerMenu"

    return TriggerRegistry().command(triggerType)


def createTriggerForNode(node, commandName, modifier=None):
    """Creates a trigger on the node, see :class:`TriggerNode` for more information.

    This function is not undoable.

    :param node: The node to create the trigger on
    :type node: :class:`zapi.DGNode`
    :param commandName: The trigger unique identifier(id attribute).
    :type commandName: str
    :param modifier: The maya om2 modifier to use if you need to handle undo(inside MPXCommands).
    :type modifier: :class:`zapi.dgModifier` or None
    :return: the created trigger node class.
    :rtype: :class:`TriggerNode`
    :raise: :class:`NodeHasExistingTrigger`
    """
    reg = TriggerRegistry()
    command = reg.command(commandName)
    if TriggerNode.hasTrigger(node):
        raise NodeHasExistingTrigger("Node already has a trigger: {}".format(node))  # todo: custom error type
    trigger = TriggerNode(node)
    trigger.setCommand(command(trigger, reg.pluginManager), modifier=modifier)
    return trigger


class TriggerNode(object):
    """This encapsulates a single nodes trigger, includes the method to execute commands/menus"""
    TRIGGER_ATTR_NAME = constants.TRIGGER_ATTR_NAME
    COMMANDTYPE_ATTR_NAME = constants.COMMANDTYPE_ATTR_NAME
    TRIGGER_MENU_TYPE = constants.TRIGGER_MENU_TYPE
    TRIGGER_SELECTION_TYPE = constants.TRIGGER_SELECTION_TYPE
    # legacy types, used to upgrade old triggers
    LAYOUT_TYPE = constants.LAYOUT_TYPE
    DYNAMIC_TYPE = constants.DYNAMIC_TYPE

    @staticmethod
    def fromNode(node):
        """Cast the node to a triggerNode class.

        :param node: The node to cast
        :type node: :class:`zapi.DGNode`
        :return: The triggerNode for the specified node  or None if the node \
        isn't a triggerNode.
        :rtype: :class:`TriggerNode` or None
        """
        if not TriggerNode.hasTrigger(node, strict=True):
            return
        trigger = TriggerNode(node)
        command = commandFromNode(node)
        if command is None:
            raise MissingRegisteredCommandOnNode(node.fullPathName())
        trigger.setCommand(command(trigger, TriggerRegistry().pluginManager))
        return trigger

    @staticmethod
    def hasTrigger(node, strict=False):
        """Determines if the specified node contains a trigger or connected meta nodes
        has a trigger.

        :param node: The node to search.
        :type node: :class:`zapi.DGNode`
        :param strict: if true then only the the node will be searched not connections.
        :type strict: bool
        :rtype: bool
        """
        if node.hasAttribute(TriggerNode.TRIGGER_ATTR_NAME):
            return True
        if strict:
            return False
        # ok so its not on the node, check for a meta node node
        attachedMeta = base.getConnectedMetaNodes(node)
        for i in attachedMeta:
            if i.hasAttribute(TriggerNode.TRIGGER_ATTR_NAME):
                return True
        return False

    @staticmethod
    def hasCommandType(node, commandType):
        """Determines if the specified node has the trigger command class.

        :param node: The node to search.
        :type node: :class:`zapi.DGNode`
        :param commandType:
        :type commandType: callable[:class:`TriggerCommand`]
        :return: True if the node has the command type
        :rtype: bool
        """
        callableCommand = commandFromNode(node)
        if callableCommand is None:
            return False
        if issubclass(callableCommand, commandType) or callableCommand == commandType:
            return True
        return False

    def __init__(self, node):
        self._node = node  # type: zapi.DGNode
        self._command = None  # type: TriggerCommand

    def __repr__(self):
        return "<{}> command: {}, node: {}".format(self.__class__.__name__, self.command(), self._node)

    def __eq__(self, other):
        return self._node == other.node

    def __ne__(self, other):
        return self._node != other.node

    @property
    def node(self):
        """Returns the node instance this trigger is associated with

        :rtype: :class:`zapi.DGNode`
        """
        return self._node

    def setCommand(self, command, modifier=None, apply=True):
        """Sets the trigger command instance, with will result in trigger attributes being created.

        :param command: Command to set for this trigger Node, if a command already exists it will be \
        replaced with the specified command.

        :type command: :class:`TriggerCommand`
        :raise: :class:`NodeHasExistingCommand`
        """
        if self._command:
            raise NodeHasExistingCommand("{}: {}".format(command.id, self._node.fullPathName()))
        self._command = command
        if not self._node.hasAttribute(constants.TRIGGER_ATTR_NAME):
            self._createAttributes(modifier, apply=apply)
            self._command.onCreate(modifier=modifier)
            if apply and modifier is not None:
                modifier.doIt()

    def command(self):
        """Returns the TriggerCommand for the node or None if it doesn't have a command yet.

        :rtype: :class:`TriggerCommand`
        """
        return self._command

    def isCommandType(self, commandType):
        """Returns True if the current command is an instance of 'commandType' class.

        :param commandType: The commandType to check against
        :type commandType: callable[:class:`TriggerCommand`]
        :rtype: bool
        """
        command = self._command
        if not command:
            return False
        if isinstance(command, commandType):
            return True
        return False

    def isCommandBaseType(self, baseType):
        """

        :param baseType: The commandType to check against
        :type baseType: int
        :rtype: bool
        """
        command = self._command
        if not command:
            return False
        return command.baseType == baseType

    def deleteTriggers(self, modifier=None, apply=True):
        """Deletes the trigger from the node.
        :param modifier: The maya dg modifier to use, if None then this function isn't undoable
        :type modifier: :class:`zapi.dgModifier` or None
        :param apply: if True and a modifier is passed then doIt() will be called
        :type apply: bool
        """
        self._node.deleteAttribute(constants.TRIGGER_ATTR_NAME, mod=modifier)
        if modifier is not None and apply:
            modifier.doIt()

    def attributes(self):
        """Returns the list of attributes which will be added to the triggerNode,
        this method calls the commands attributes() function.

        :return: list of attributes flags in the same form as :func:`zapi.DGNode.addAttribute`
        :rtype: list[dict]
        """
        commandId = self._command.id if self._command else ""
        attrs = [
            {"name": constants.COMMANDTYPE_ATTR_NAME, "Type": zapi.attrtypes.kMFnDataString,
             "isArray": False, "value": commandId,
             "locked": True}

        ]
        if self._command:
            attrs.extend(self._command.attributes())
        return attrs

    def _createAttributes(self, modifier=None, apply=True):
        """Internal method which creates the trigger compound based on the command type.

        :param modifier: The maya modifier to use for undo.
        :type modifier: :class:`zapi.dgModifier`
        :param apply: Whether or not to apply the state changes to the modifier.
        :type apply: bool
        """
        if self._node.hasAttribute(constants.TRIGGER_ATTR_NAME):
            raise zapi.ExistingNodeAttributeError("Existing attribute")
        attrs = self.attributes()
        newAttributes = []
        for child in attrs:
            if self._node.hasAttribute(child["name"]):
                continue
            newAttributes.append(child)
        if not newAttributes:
            return
        self._node.addCompoundAttribute(constants.TRIGGER_ATTR_NAME, attrs, mod=modifier, apply=apply)
        if modifier is not None and apply:
            modifier.doIt()


class TriggerCommand(plugin.Plugin):
    baseType = constants.TRIGGER_BASE_TYPE_COMMAND
    # the trigger command plugin id, used in the registry and maya attribute metadata
    id = ""

    def __init__(self, trigger=None, manager=None):
        """

        :param trigger:
        :type trigger: :class:`TriggerNode` or None
        :param manager:
        :type manager: :class:`pluginmanager.PluginManager` or None
        """
        super(TriggerCommand, self).__init__(manager)
        self._trigger = trigger
        self._node = trigger.node  # type: zapi.DGNode

    def __repr__(self):
        return "<{}> id: {}".format(self.__class__.__name__, self.id)

    @property
    def node(self):
        """Returns the node attached to this trigger command.

        :rtype: :class:`zapi.DGNode`
        """
        return self._node

    def attributes(self):
        """Unique attributes for the command to be created on the node.

        :return: a list of attribute dicts in the same form as :func:`zapi.DGNode.addAttribute`
        :rtype: list[dict]
        """
        return []

    def onCreate(self, modifier=None):
        """The function  gets called when the command gets created on the node allowing for
        custom control of the command. It's recommended to only make changes of the modifier.

        :param modifier: The maya modifier that all changes will be applied too.
        :type modifier: :class:`zapi.dgModifier`
        :return:
        :rtype:
        """
        pass

    def execute(self, *args, **kwargs):
        raise NotImplementedError("Missing Method")


def connectedTriggerNodes(nodes, filterCls=None):
    """Generator function that returns all triggerNodes as DGNodes within the specified nodes list
    or any connected meta nodes in the network.

    :param nodes:
    :type nodes: list[:class:`zapi.DGNode`]
    :param filterCls:
    :type filterCls: callable[:class:`TriggerCommand`]
    :return:
    :rtype: Generator[:class:`zapi.DGNode`]
    """
    visited = []
    for n in nodes:
        if n in visited:
            continue
        visited.append(n)

        # first check on the current node
        if filterCls is None or (filterCls is not None and TriggerNode.hasCommandType(n, filterCls)):
            yield n

        # ok so its not on the node, check for a meta node node
        attachedMeta = base.getConnectedMetaNodes(n)
        for i in attachedMeta:
            if i not in visited and filterCls is None or (
                    filterCls is not None and TriggerNode.hasCommandType(i, filterCls)
            ):
                visited.append(i)
                yield i
