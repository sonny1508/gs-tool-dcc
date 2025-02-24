import functools

import contextlib
from zoo.libs.maya.utils import general
from zoo.libs.maya.api import callbacks
from zoo.libs.maya import zapi
from zoo.libs.maya.triggers import triggerbase, constants


CURRENT_SELECTION_CALLBACK = None  # type: callbacks.CallbackSelection


def createSelectionCallback():
    """Creates the maya selection callback
    """
    global CURRENT_SELECTION_CALLBACK
    if CURRENT_SELECTION_CALLBACK is not None:
        if CURRENT_SELECTION_CALLBACK.currentCallbackState:
            return
        CURRENT_SELECTION_CALLBACK.start()
        return

    callback = callbacks.CallbackSelection(_onSelectionCallback)
    CURRENT_SELECTION_CALLBACK = callback
    callback.start()


def removeSelectionCallback():
    """Removes the maya trigger selection callback
    """
    global CURRENT_SELECTION_CALLBACK
    if CURRENT_SELECTION_CALLBACK is None:
        return
    CURRENT_SELECTION_CALLBACK.stop()


def toggleSelectionCallback():
    """Toggle the selection callback state, currently used in artist palette
    trigger toggle.
    """
    if CURRENT_SELECTION_CALLBACK is None:
        createSelectionCallback()
    else:
        removeSelectionCallback()


@contextlib.contextmanager
def blockSelectionCallback():
    """context manager(with statement) which blocks the selection
    callback for the scope.
    """
    if CURRENT_SELECTION_CALLBACK is not None:
        currentlyActive = CURRENT_SELECTION_CALLBACK.currentCallbackState
        try:
            if currentlyActive:
                removeSelectionCallback()
            yield
        finally:
            if currentlyActive:
                createSelectionCallback()
    else:
        yield


def blockSelectionCallbackDecorator(func):
    """Decorator function which blocks the maya selection callback
    """

    @functools.wraps(func)
    def inner(*args, **kwargs):
        if CURRENT_SELECTION_CALLBACK is not None:

            currentlyActive = CURRENT_SELECTION_CALLBACK.currentCallbackState
            try:
                if currentlyActive:
                    removeSelectionCallback()
                return func(*args, **kwargs)
            finally:
                if currentlyActive:
                    createSelectionCallback()
        else:
            return func(*args, **kwargs)

    return inner


def _onSelectionCallback(selection):
    """Internal method which is called by the moya callback which simply runs
    :func:`executeTriggerFromNodes`
    :param selection:
    :type selection:
    :return:
    :rtype:
    """
    selection = [zapi.nodeByObject(i.object()) for i in selection]
    if selection:
        executeTriggerFromNodes(selection)


@general.undoDecorator
def executeTriggerFromNodes(nodes):
    """Primary function which executes the trigger command for each node provided.

    :param nodes: The list of nodes which require their commands executed.
    :type nodes: list[:class:`zapi.DGNode`]
    """
    triggers = []
    for node in nodes:
        if node.hasAttribute("_trig_version"):
            continue
        triggers.append(triggerbase.TriggerNode.fromNode(node))
    if not triggers:
        return
    for trigger in triggers:
        if trigger is None or not trigger.isCommandBaseType(constants.TRIGGER_BASE_TYPE_SELECTION):
            continue
        cmd = trigger.command()
        if cmd:
            cmd.execute()


def executeTriggersFromSelection():
    """Function which gathers will selected nodes and executes all valid selection triggers.

    """
    selectedNodes = zapi.selected()
    if selectedNodes:
        executeTriggerFromNodes(selectedNodes)
