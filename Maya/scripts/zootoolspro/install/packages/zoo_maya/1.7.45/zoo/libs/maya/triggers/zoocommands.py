from zoo.libs.maya.triggers import triggerbase
from zoo.libs.maya.mayacommand import command
from zoo.libs.maya import zapi


class CreateMenuTriggersCommand(command.ZooCommandMaya):
    """This command creates a TriggerMenu for each node provided.
    """

    id = "zoo.maya.createMenuTriggers"
    isUndoable = True
    modifier = None

    def resolveArguments(self, arguments):
        nodes = list(arguments.get("nodes"))
        if not nodes:
            self.cancel("Missing Nodes argument")
        triggerType = arguments.get("triggerType", "")
        if triggerType not in triggerbase.TriggerRegistry().commandTypes():
            self.cancel("{} is not a registered trigger type".format(triggerType))
        validNodes = []
        for n in nodes:
            if n is None:
                continue
            if not isinstance(n, zapi.DGNode):
                self.cancel("Node is not of type: zapi.DGNode: {}".format(n))
            if triggerbase.TriggerNode.hasTrigger(n):
                continue
            validNodes.append(n)
        arguments["nodes"] = validNodes
        return arguments

    def doIt(self, nodes=None, triggerType=None, menuId=None):
        """Create the meta node based on the type parameter, if the type isn't specified then the baseMeta class will
        be used instead

        """
        self.modifier = zapi.dgModifier()
        triggers = []
        for node in nodes:
            trigger = triggerbase.createTriggerForNode(node,
                                                       commandName=triggerType,
                                                       modifier=self.modifier)
            self.modifier.doIt()
            if menuId is not None:
                trigger.command().setMenu(menuId)
            triggers.append(trigger)
        self.modifier.doIt()
        return triggers

    def undoIt(self):
        self.modifier.undoIt()


class DeleteTriggersCommand(command.ZooCommandMaya):
    """The Command deletes the current trigger on all specified nodes
    """

    id = "zoo.maya.deleteTriggers"
    isUndoable = True

    modifier = None
    _triggers = []

    def resolveArguments(self, arguments):
        nodes = list(arguments.get("nodes"))

        if not nodes:
            self.cancel("Missing Nodes argument")
        triggers = []
        validNodes = []

        for n in nodes:
            if n is None:
                continue
            if not isinstance(n, zapi.DGNode):
                self.cancel("Node is not of type: zapi.DGNode: {}".format(n))
            trigger = triggerbase.TriggerNode.fromNode(n)
            if trigger is not None:
                triggers.append(trigger)
                validNodes.append(n)
        self._triggers = triggers
        arguments["nodes"] = validNodes
        return arguments

    def doIt(self, nodes=None):
        self.modifier = zapi.dgModifier()
        for trigger in self._triggers:
            trigger.deleteTriggers(self.modifier)
        self.modifier.doIt()

    def undoIt(self):
        self.modifier.undoIt()


class CreateSelectionTriggersCommand(command.ZooCommandMaya):
    """The Command creates selection based trigger command for each node provided.
    """

    id = "zoo.maya.createSelectionTriggers"
    isUndoable = True
    modifier = None
    _triggers = []

    def resolveArguments(self, arguments):
        nodes = list(arguments.get("nodes"))
        if not nodes:
            self.cancel("Missing Nodes argument")
        triggerType = arguments.get("triggerType", "")
        if triggerType not in triggerbase.TriggerRegistry().commandTypes():
            self.cancel("{} is not a registered trigger type".format(triggerType))
        validNodes = []
        for n in nodes:
            if n is None:
                continue
            if not isinstance(n, zapi.DGNode):
                self.cancel("Node is not of type: zapi.DGNode: {}".format(type(n)))
            if triggerbase.TriggerNode.hasTrigger(n):
                continue
            validNodes.append(n)
        validSelectables = [n for n in arguments.get("connectables", []) if isinstance(n, zapi.DGNode) and n is not None]
        arguments["nodes"] = validNodes
        arguments["connectables"] = validSelectables
        return arguments

    def doIt(self, nodes=None, triggerType=None, commandStr=None, connectables=None):
        self.modifier = zapi.dgModifier()
        triggers = []
        for node in nodes:
            trigger = triggerbase.createTriggerForNode(node,
                                                       commandName=triggerType,
                                                       modifier=self.modifier)
            if commandStr is not None:
                trigger.command().setCommandStr(commandStr, mod=self.modifier)
            if connectables:
                trigger.command().addNodesToConnectables(connectables, mod=self.modifier)

            triggers.append(trigger)
        self.modifier.doIt()
        return triggers

    def undoIt(self):
        self.modifier.undoIt()
