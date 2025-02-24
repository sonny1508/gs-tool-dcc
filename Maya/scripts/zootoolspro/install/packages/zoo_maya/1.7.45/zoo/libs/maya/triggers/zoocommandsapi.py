"""This Modules contains the primary undo API for triggers.

Each function simply calls the matching zooCommand
"""
from zoo.libs.maya.mayacommand import mayaexecutor as executor


def createMenuTriggers(nodes, menuId, triggerCommandId=None):
    """Undoable function which creates the same menu trigger every node provided.

    :param nodes: The list of nodes to add the trigger too.
    :type nodes: list[:class:`zapi.DGNode`]
    :param menuId: the layout Id or dynamic marking menu id
    :type menuId: str
    :param triggerCommandId: The trigger command id to use, If none it will use the default menu.
    :type triggerCommandId: str or None
    :return: A list of triggerNode classes which were created.
    :rtype: list[:class:`zoo.libs.maya.triggers.TriggerNode`]
    """
    return executor.execute("zoo.maya.createMenuTriggers",
                            nodes=nodes,
                            triggerType=triggerCommandId or "triggerMenu",
                            menuId=menuId)


def createSelectionTrigger(nodes, commandStr=None, connectables=None, triggerCommandId=None):
    """Undoable function which creates the same Selection trigger every node provided.

    :param nodes: The list of nodes to add the trigger too.
    :type nodes: list[:class:`zapi.DGNode`]
    :param commandStr: The python command string, must support exec() function
    :type commandStr: str
    :param connectables:  Adds the list of specified nodes to the current command.
    :type connectables: list[:class:`zapi.DGNode`]
    :param triggerCommandId: The trigger command id to use, If none it will use the 'selectConnected'.
    :type triggerCommandId: str or None
    :return: A list of triggerNode classes which were created.
    :rtype: list[:class:`zoo.libs.maya.triggers.TriggerNode`]
    """
    return executor.execute("zoo.maya.createSelectionTriggers",
                            nodes=nodes,
                            triggerType=triggerCommandId or "selectConnected",
                            commandStr=commandStr or "",
                            connectables=connectables or [])


def deleteTriggers(nodes):
    """Deletes the triggers on all nodes specified.

    :param nodes: The list node DGNodes to remove triggers from.
    :type nodes: list[:class:`zapi.DGNode`]
    """
    return executor.execute("zoo.maya.deleteTriggers",
                            nodes=nodes)
