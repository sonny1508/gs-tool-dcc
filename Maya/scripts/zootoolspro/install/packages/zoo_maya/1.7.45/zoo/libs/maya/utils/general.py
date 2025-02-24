"""General maya functions

Example use:

.. code-block:: python

    from zoo.libs.maya.utils import general
    lockSelectedNodes(unlock=False, message=True)

"""


import os
import re
from contextlib import contextmanager
import functools

from maya import cmds
from maya.OpenMaya import MGlobal
from maya.api import OpenMaya as om2
from zoo.core.util import zlogging
from zoo.libs.maya.utils import mayaenv

logger = zlogging.zooLogger
SAFE_NAME_REGEX = re.compile(r'^[a-zA-Z_|]\w*$')


def isSafeName(name):
    """Determines if the provided name is safe for use as a node name.

    A name isn't valid if it doesn't start with a letter, or contains any invalid characters.

    :param name: The name to check
    :type name: str
    :return: True if the name is valid, False otherwise
    :rtype: bool
    """
    return bool(SAFE_NAME_REGEX.match(name))


def mayaUpVector():
    """Gets the current world up vector

    :rtype: om1.MVector
    """
    return MGlobal.upAxis()


def upAxis():
    """Returns the current world up axis in str form.

    :return: returns x,y or z
    :rtype: str
    """
    if isYAxisUp():
        return "y"
    elif isZAxisUp():
        return "z"
    return "x"


def isYAxisUp():
    """Returns True if y is world up

    :return: bool
    """
    return MGlobal.isYAxisUp()


def isZAxisUp():
    """Returns True if Z is world up

    :return: bool
    """
    return MGlobal.isZAxisUp()


def isXAxisUp():
    """Returns True if x is world up

    :return: bool
    """
    return not isYAxisUp() and not isZAxisUp()


def loadPlugin(pluginPath):
    """Loads the given maya plugin path can be .mll or .py

    :param pluginPath: the absolute fullpath file path to the plugin
    :type pluginPath: str
    :rtype: bool
    """
    try:
        if not isPluginLoaded(pluginPath):
            cmds.loadPlugin(pluginPath)
    except RuntimeError:
        logger.debug("Could not load plugin->{}".format(pluginPath))
        return False
    return True


def unloadPlugin(pluginPath):
    """unLoads the given maya plugin name can be .mll or .py

    :param pluginPath: Maya plugin name
    :type pluginPath: str
    :rtype: bool
    """
    try:
        if isPluginLoaded(pluginPath):
            cmds.unloadPlugin(pluginPath)
    except RuntimeError:
        logger.debug("Could not load plugin->{}".format(pluginPath))
        return False
    return False


def isPluginLoaded(pluginPath):
    """Returns True if the given plugin name is loaded
    """
    return cmds.pluginInfo(pluginPath, q=True, loaded=True)


def getMayaPlugins():
    location = mayaenv.getMayaLocation(mayaenv.mayaVersion())
    plugins = set()
    for path in [i for i in mayaenv.mayaPluginPaths() if i.startswith(location) and os.path.isdir(i)]:
        for x in os.listdir(path):
            if os.path.isfile(os.path.join(path, x)) and isPluginLoaded(path):
                plugins.add(x)
    return list(plugins)


def loadAllMayaPlugins():
    logger.debug("loading All plugins")
    for plugin in getMayaPlugins():
        loadPlugin(plugin)
    logger.debug("loaded all plugins")


def unLoadMayaPlugins():
    logger.debug("unloading All plugins")
    for plugin in getMayaPlugins():
        unloadPlugin(plugin)
    logger.debug("unloaded all plugins")


def removeUnknownPlugins(message=True):
    """Removes unknown plugins from the scene.

    :param message: report the message to the user
    :type message: bool
    :return: A set of the removed plugins
    :rtype: set[str]
    """
    removedPlugins = set()
    for pluginName in cmds.unknownPlugin(query=True, list=True) or []:
        cmds.unknownPlugin(pluginName, remove=True)
        removedPlugins.add(pluginName)
    if message and removedPlugins:
        om2.MGlobal.displayInfo("Success Plugin/s Deleted: {}".format(removedPlugins))
    if message and not removedPlugins:
        om2.MGlobal.displayWarning("No Unknown Plugin/s Found")
    return removedPlugins


def deleteUnknownNodes(message=True):
    """Deletes nodes of unknown type, usually plugins that are missing or not installed.

    Also see removeUnknownPlugins()

    :param message: Report a message to the user?
    :type message: bool
    :return: Unknown nodes that were deleted and not deleted.
    :rtype: tuple[[str], [str]]
    """
    unknownNodes = cmds.ls(type="unknown")
    nodesDeleted = list()
    nodesNotDeleted = list()
    for node in unknownNodes:
        if not cmds.objExists(node):
            continue
        cmds.lockNode(node, lock=False)
        try:
            cmds.delete(node)
            nodesDeleted.append(node)
        except ValueError:
            nodesNotDeleted.append(node)
    if message:
        if not nodesNotDeleted and nodesDeleted:
            om2.MGlobal.displayInfo("Success Nodes Deleted: {}".format(nodesDeleted))
        elif not nodesDeleted and nodesNotDeleted:
            om2.MGlobal.displayWarning("Warning nodes couldn't be deleted: {}".format(nodesDeleted))
        elif nodesDeleted and nodesNotDeleted:
            om2.MGlobal.displayInfo("Nodes Deleted: {}".format(nodesDeleted))
            om2.MGlobal.displayWarning("Nodes couldn't be deleted: {}".format(nodesDeleted))
            om2.MGlobal.displayWarning("Warning Some nodes couldn't be deleted see script editor")
        else:
            om2.MGlobal.displayInfo("No Nodes Were Deleted")
    return nodesDeleted, nodesNotDeleted


def deleteTurtlePluginScene(removeShelf=True, message=True):
    """Removes Turtle from the scene, unloads the plugin and deletes the shelf too.

    :param removeShelf: If True delete the Turtle shelf
    :type removeShelf: bool
    :param message: report a message to the user?
    :type message: bool
    :return: If True Turtle was removed
    :rtype: bool
    """
    turtleDeleted = False

    if isPluginLoaded("Turtle"):
        # Delete turtle nodes
        types = cmds.pluginInfo('Turtle', dependNode=True, q=True)
        nodes = cmds.ls(type=types, long=True)
        if nodes:
            cmds.lockNode(nodes, lock=False)
            cmds.delete(nodes)
        cmds.flushUndo()

        # unload will remove other turtle nodes, though should be sorted by the mel eval
        turtleDeleted = True
        cmds.unloadPlugin("Turtle", force=True)

    if removeShelf:  # kill the TURTLE shelf
        if deleteShelf('TURTLE'):
            turtleDeleted = True

    if message:
        if turtleDeleted:
            om2.MGlobal.displayInfo("Success Turtle has been removed")
        else:
            om2.MGlobal.displayWarning("Turtle not found")
    return turtleDeleted


def deleteShelf(name):
    """ Deletes maya shelf

    :param name: Name of shelf
    :type name: str
    :return: Returns true if deleted, False otherwise
    """
    shelves = cmds.tabLayout("ShelfLayout", query=True, childArray=True)
    if name in shelves:
        cmds.deleteUI(name, layout=True)
        return True
    return False


def lockSelectedNodes(unlock=False, message=True):
    """Locks or unlocks the selected nodes, Maya locked nodes are nodes that can't be deleted.

    :param unlock: unlock the nodes instead of locking?
    :type unlock: bool
    :param message: Report a message to the user?
    :type message: bool
    :return: nodes that were unlocked
    :rtype: list(str)
    """
    nodes = cmds.ls(selection=True)
    for node in nodes:
        cmds.lockNode(node, lock=not unlock)
    if message:
        if unlock:
            om2.MGlobal.displayInfo("Nodes Unlocked: {}".format(nodes))
        else:
            om2.MGlobal.displayInfo("Nodes locked: {}".format(nodes))
    return nodes


@contextmanager
def namespaceContext(namespace):
    """Context manager which temporarily sets the current namespace, if the namespace doesn't exist
    it will be created.

    :param namespace: The maya Namespace to use, ie. "MyNamespace" or ":MyNamespace"
    :type namespace: str
    """
    currentNamespace = om2.MNamespace.currentNamespace()
    existingNamespaces = om2.MNamespace.getNamespaces(currentNamespace, True)
    validNamespace = namespace if namespace.startswith(":") else ":{}".format(namespace)
    if currentNamespace != validNamespace and validNamespace not in existingNamespaces and validNamespace != om2.MNamespace.rootNamespace():
        try:
            om2.MNamespace.addNamespace(validNamespace)
        except RuntimeError:
            logger.error("Failed to create namespace: {}, existing namespaces: {}".format(validNamespace,
                                                                                          existingNamespaces),
                         exc_info=True)
            om2.MNamespace.setCurrentNamespace(currentNamespace)
            raise
    om2.MNamespace.setCurrentNamespace(validNamespace)
    try:
        yield
    finally:
        om2.MNamespace.setCurrentNamespace(currentNamespace)


@contextmanager
def tempNamespaceContext(namespace):
    """Creates a temporary namespace that only lives for the life time of the scope

    :param namespace: The Temporary maya Namespace to use, ie. "tempNamespace" or ":tempNamespace"
    :type namespace: str
    """
    currentNamespace = om2.MNamespace.currentNamespace()
    existingNamespaces = om2.MNamespace.getNamespaces(currentNamespace, True)
    validNamespace = namespace if namespace.startswith(":") else ":{}".format(namespace)
    if currentNamespace != validNamespace and validNamespace not in existingNamespaces and validNamespace != om2.MNamespace.rootNamespace():
        try:
            om2.MNamespace.addNamespace(validNamespace)
        except RuntimeError:
            logger.error("Failed to create namespace: {}, existing namespaces: {}".format(validNamespace,
                                                                                          existingNamespaces),
                         exc_info=True)
            om2.MNamespace.setCurrentNamespace(currentNamespace)
            raise
    om2.MNamespace.setCurrentNamespace(validNamespace)
    try:
        yield
    finally:
        om2.MNamespace.moveNamespace(validNamespace, om2.MNamespace.rootNamespace(), True)
        om2.MNamespace.removeNamespace(validNamespace)


def generateUniqueNamespace(name):
    """Generates a unique namespace based on the current scene state in the form of name, name01, name02.

    If the provided namespace is already unique it will be returned as is.

    :param name: The prefix for the namespace
    :type name: str
    :return: The unique name.
    :rtype: str
    """
    uniqueName = name
    index = 1
    while om2.MNamespace.namespaceExists(uniqueName):
        uniqueName = name + str(index).zfill(2)
        index += 1
    return uniqueName


@contextmanager
def isolatedNodes(nodes, panel):
    """Context manager for isolating `nodes` in maya model `panel`

    :param nodes: A list of node fullpaths to isolate
    :type nodes: seq(str)
    :param panel: The maya model panel
    :type panel: str
    """

    cmds.isolateSelect(panel, state=True)
    for obj in nodes:
        cmds.isolateSelect(panel, addDagObject=obj)
    yield
    cmds.isolateSelect(panel, state=False)


@contextmanager
def maintainSelectionContext():
    """Context manager which maintains the current selection
    """
    currentSelection = cmds.ls(sl=True, long=True)
    try:
        yield
    finally:
        if currentSelection:
            # the client function may have deleted nodes/components and maya
            # will fail the whole command if even one object isn't valid.
            cmds.select([i for i in currentSelection if cmds.objExists(i)])


def maintainSelectionDecorator(func):
    """Decorator to maintain the current selection.
    """

    @functools.wraps(func)
    def inner(*args, **kwargs):
        # we're using cmds over api here because we don't currently support components(edges,faces etc)
        currentSelection = cmds.ls(sl=True, long=True)
        try:
            return func(*args, **kwargs)
        finally:
            if currentSelection:
                # the client function may have deleted nodes/components and maya
                # will fail the whole command if even one object isn't valid.
                cmds.select([i for i in currentSelection if cmds.objExists(i)])

    return inner


def undoDecorator(func):
    """Allows all cmds, mel commands perform by the  the ``func`` into
    a single undo operation.

    .. code-block:: python

        @undoDecorator
        def myoperationFunc():
            pass

    """

    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            cmds.undoInfo(openChunk=True, chunkName=func.__name__)
            return func(*args, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True)

    return inner


@contextmanager
def undoContext(name=None):
    """Context manager for maya undo.

    .. code-block:: python

        with undoContext:
            cmds.polyCube()
            cmds.sphere()

    """
    try:
        cmds.undoInfo(openChunk=True, chunkName=name or "")
        yield
    finally:
        cmds.undoInfo(closeChunk=True)


def openUndoChunk(name=None):
    """Opens a Maya undo chunk
    """
    cmds.undoInfo(openChunk=True, chunkName=name or "")


def closeUndoChunk(name=None):
    """Opens a Maya undo chunk
    """
    cmds.undoInfo(closeChunk=True, chunkName=name or "")


class _CommandRepeatStorage(object):
    """Internal storage class only.

    Stores the repeat function command.
    """
    _functionToRepeat = None

    @staticmethod
    def runCurrentRepeatCommand():
        """Executes the current repeat function if any.
        """
        func = _CommandRepeatStorage._functionToRepeat
        if func is not None:
            func()

    @staticmethod
    def setRepeatCommand(func, args, kwargs):
        """Sets the current repeat function.

        :param func: The repeat function.
        :type func: callable
        :param args: The arguments to pass to the repeat function when executing.
        :type args: tuple
        :param kwargs: The keyword arguments to pass to the repeat function when executing.
        :type kwargs: dict
        """
        _CommandRepeatStorage._functionToRepeat = functools.partial(func, *args, **kwargs)

    @staticmethod
    def flush():
        """Clears the current repeat function.
        """
        _CommandRepeatStorage._functionToRepeat = None


def createRepeatCommandForFunc(func, *args, **kwargs):
    """Function which updates mayas repeat last command with the provide function.

    .. Note:: Only functions/staticmethods/classmethods are supported.


    .. code-block:: python

        def testFunction(argOne, keyword=None):
            print(argOne, keyword)

        createRepeatCommandForFunc(testFunction, "helloworld", keyword=0)

    :param func: The function for the user repeat(hotkey: g or editMenu: repeat Last)
    :type func: callable
    :param args: The arguments to pass to the repeat function
    :type args: tuple
    :param kwargs: The keyword arguments to pass to the repeat function.
    :type kwargs: dict
    """
    # set up the function storage to run the new requested function
    _CommandRepeatStorage.setRepeatCommand(func, args, kwargs)
    # create the mel command string for the python function, note that we have to use mel to
    # bind to repeat last command.
    command = 'python(\"import {};{}.{}\");'.format(__name__,
                                                    __name__,
                                                    "_CommandRepeatStorage.runCurrentRepeatCommand()"
                                                    )
    cmds.repeatLast(addCommand=command, addCommandLabel=func.__name__)


def createRepeatLastCommandDecorator(function):
    """Decorator function which updates the maya repeat command with the decorated function.

    .. note:: All args/kwargs of the decorated function will be passed to the repeat command
    .. note:: Only functions/staticmethods/classmethods are supported.

    .. code-block:: python

        @createRepeatLastCommandDecorator
        def testFunction():
            print("test function")

    """
    def innerFunction(*args, **kwargs):
        result = function(*args, **kwargs)
        createRepeatCommandForFunc(function, *args, **kwargs)
        return result

    return innerFunction


def userShelfDir():
    """ Path to shelf

    :return:
    """
    return cmds.internalVar(userShelfDir=1)


def mayaAppDir():
    """ The Maya preference folder

    Windows Vista, Windows 7, and Windows 8

    \\Users\\<username>\\Documents\\Maya
    Mac OS X

    ~<username>/Library/Preferences/Autodesk/Maya
    Linux (64-bit)

    ~<username>/Maya


    :return:
    """
    return cmds.internalVar(userAppDir=1)
