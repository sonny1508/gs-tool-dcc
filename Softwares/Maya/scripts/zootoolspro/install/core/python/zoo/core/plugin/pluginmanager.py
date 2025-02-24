"""This module contains the primary plugin manager framework which is used
throughout zootools from toolsets, hive, MayaCommand, artist palette, the list
is rather extensive.
"""

import inspect
import os

from zoo.core.plugin import plugin
from zoo.core.util import modules
from zoo.core.util import zlogging

try:
    from inspect import getfullargspec
except ImportError:
    from inspect import getargspec as getfullargspec


class PluginManager(object):
    """This class manages a group of plugin instance's in local scope therefore allowing
    the client to create as many plugin manager instances with varying interfaces as needed.
    It's your responsible to manage the lifetime of the manager.

    Plugins can be treated in two ways for a class instance.

    #. Client managed lifetime, The plugin manager simply filters plugins without instantiation. \
        Therefore you handle the lifetime of the plugin instance, but we store the callable.

    #. Plugin singletons but scoped locally to the manager instance. Allows plugin classes \
        to be instantiated once and reused.

    To load a singleton of a plugin use :func:`loadPlugin`, after this call any calls to :func:`getPlugin`
    will result in the same instance being returned. :func:`getPlugin`. Default behaviour of
    :func:`getPlugin` gets the loaded plugin instance and if that's not found returns the callable class.

    For registering plugins.

    #. To register a class as a plugin use :func:`registerPlugin`.
    #. To automatically discover plugin classes from a module object use :func:`registerByModule`.
    #. To register any class which meets the interface filter by module or folder path use \
        :func:`registerPaths`.
    #. To register all valid paths from an environment variable use :func:`registerByEnv`

    .. code-block:: python

        from zoo.core.plugin import pluginmanager, plugin

        class MyPlugin(plugin.Plugin):
            uid = "myPlugin"
            def __init__(self):
                pass

        # Interface here just tells the manager when registering plugins ensure it's a subclass
        # of this object. You can use your own base class which doesn't inherent from Plugin if
        # you like. variableName is the class variable to use for the key in the cache.
        # Defaults to use the className if not provided.
        manager = pluginmanager.PluginManager(interface=[plugin.Plugin], variableName="uid")
        manager.registerPlugin(MyPlugin)

        # Since we're using the base class from the example it's going to register the class Name
        # it's best to use the :param:`variableName` argument.
        pluginObject = manager.getPlugin("myPlugin")
        pluginInstance = pluginObject() # lifetime is handle by us

        # loads the plugin class ie. calls __init__
        myPluginSingleton = manager.loadPlugin("myPlugin")

        # getPlugin will now always return the same instance.
        manager.getPlugin("myPlugin") == myPluginSingleton
        # result: True

    :param interface: A list of base class which will become the plugin interface \
    for all plugins for the manager, this is used solely to filter classes out.

    :type interface:list[callable]
    :param variableName: The class variable name to become the UUID of the class within the cache\
    if none is specified the UUID will be the class name.

    :type variableName: str
    """

    def __init__(self, interface=None, variableName=None, name=None):
        interface = interface or [plugin.Plugin]
        modulePath = self.__class__.__module__
        if name:
            self.name = ".".join([modulePath, name + "PluginManager"])
        else:
            self.name = ".".join([modulePath, self.__class__.__name__])
        self.plugins = {}
        # register the plugin names by the variable, if its missing fallback to the class name
        self.variableName = variableName or ""
        self.interfaces = interface
        self.loadedPlugins = {}  # {className or variableName: instance}
        self.basePaths = []
        self.logger = zlogging.getLogger(self.name)

    def registerByEnv(self, env):
        """Recursively registers all found plugins based on the paths specified in the environment
        variable. Each must be separated by os.pathsep

        :param env: The environment variable key
        :type env: str
        """
        paths = os.environ.get(env, "").split(os.pathsep)
        self.logger.debug("Loading plugins for paths from env: {}, {}".format(env, paths))

        if paths:
            self.registerPaths(paths)

    def registerPaths(self, paths):
        """This function is a helper function to register a list of paths.

        :param paths: A list of module or package paths, see registerByModule() and \
        registerByPackage() for the path format.
        :type paths: list(str)
        """
        self.basePaths.extend(paths)
        visited = set()
        for path in paths:
            path = os.path.expandvars(path)
            if not path:
                continue
            elif os.path.isfile(path):
                # remove the extension of the file name, so we can deal with py/pyc
                basename = os.extsep.join(path.split(os.extsep)[:-1])
            else:
                basename = path
            if basename in visited:
                continue
            visited.add(basename)
            if os.path.isdir(path):
                self.registerByPackage(path)
            else:
                self.registerPath(path)

    def registerPath(self, modulePath):
        """Registers the given python module path.

        :param modulePath: The absolute full path to a python module
        :type modulePath: str
        :return: Module Object
        """
        importedModule = None

        if os.path.isfile(modulePath):
            if not modules.validModulePath(modulePath):
                return importedModule
            self.logger.debug("Loading plugin from file: {}".format(modulePath))
            dottedPath = modules.asDottedPath(modulePath)
            if dottedPath:
                try:
                    importedModule = modules.importModule(dottedPath)
                except ImportError:
                    self.logger.warning(
                        "Failed to import plugin as a dotted path: {}, falling back to basename".format(modulePath))
            else:
                try:
                    importedModule = modules.importModule(modulePath)
                except ImportError:
                    self.logger.error("Failed to import Plugin module: {}, skipped Load".format(modulePath),
                                      exc_info=True)
                    return importedModule

        elif modules.isDottedPath(modulePath):
            try:
                importedModule = modules.importModule(modulePath)
            except ImportError:
                self.logger.error("Failed to import Plugin module: {}, skipped Load".format(modulePath), exc_info=True)
                return importedModule
        if importedModule:
            self.registerByModule(importedModule)
        return importedModule

    def registerByModule(self, module):
        """ This function registry a module by search all class members of the module and registers any class that is an
        instance of the plugin class 'zoo.core.plugin.plugin.Plugin'

        :param module: the module path to registry, the path is a '.' separated path eg. zoo.libs.apps.tooldefinitions
        :type module: str
        """
        if inspect.ismodule(module):
            for member in modules.iterMembers(module, predicate=inspect.isclass):
                self.registerPlugin(member[1])

    def registerByPackage(self, pkg):
        """This function is similar to registerByModule() but works on packages, this is an expensive operation as it
        requires a recursive search by importing all submodules and searching them.

        :param pkg: The package path to register eg. zoo.libs.apps works with absolute paths as well.
        :type pkg: str
        """
        for subModule in modules.iterModules(pkg):
            if subModule.endswith(".pyc"):
                continue
            self.registerPath(subModule)

    def registerPlugin(self, classObj):
        """Registers a plugin instance to the manager.

        :param classObj: The plugin instance to registry.
        :type classObj: callable
        """
        for interface in self.interfaces:
            name = getattr(classObj, self.variableName) if hasattr(classObj, self.variableName) else classObj.__name__
            if name not in self.plugins and issubclass(classObj, interface):

                # ignore subclasses which don't have a valid name,
                # when working with the variable Name it may end up being empty, so we ignore
                if not name:
                    continue
                self.logger.debug("registering plugin -> {}".format(name))
                self.plugins[str(name)] = classObj

    def loadPlugin(self, pluginName, **kwargs):
        """Loads a given plugin by name. eg plugin(manager=self)

        :param pluginName: The plugin to load by name.
        :type pluginName: str
        """
        tool = self.plugins.get(pluginName)
        if not tool:
            return
        self.logger.debug("Loading Plugin -> {}".format(pluginName))
        # pass the manager into the plugin, this is so we have access to any global info
        spec = getfullargspec(tool.__init__)
        # python 3 and 2 support
        try:
            keywords = spec.kwonlyargs
        except AttributeError:
            keywords = spec.keywords
        args = spec.args

        if (args and "manager" in args) or (keywords and "manager" in keywords):
            kwargs["manager"] = self
        try:
            newTool = tool(**kwargs)
        except Exception:
            self.logger.error("Failed to load plugin: {}, arguments: {}".format(pluginName, kwargs),
                              exc_info=True)
            return

        self.loadedPlugins[pluginName] = newTool
        self.loadedPlugins[pluginName].isLoaded = True
        return self.loadedPlugins[pluginName]

    def loadAllPlugins(self, **pluginArguments):
        """Loops over all registered plugins and calls them eg. plugin(manager=self)
        """
        for pluginName in self.plugins:
            self.loadPlugin(pluginName, **pluginArguments)

    def getPlugin(self, name):
        """Returns the plugin instance by name, first checks to see if it's already
        loaded and return the instance otherwise returns the plugin callable or None

        :param name: the name of the plugin
        :type name: str
        :return: Returns the plugin isinstance or None
        :rtype: Plugin instance or None
        """
        plug = self.loadedPlugins.get(name)
        if plug is None:
            return self.plugins.get(name)
        return plug

    def unload(self, name):
        """Unloads a plugin by name from the manager by simply remove it from the cache.

        :param name: The name of the registered plugin class.
        :type name: str
        :return: Return True if the plugin was successfully unloaded.
        :rtype: bool
        """
        loadedPlugin = self.loadedPlugins.get(name)
        if loadedPlugin and loadedPlugin.isLoaded:
            self.loadedPlugins.pop(name)
            return True
        return False

    def unloadAllPlugins(self):
        """Unloads all currently loaded plugins from the registry.
        """
        self.loadedPlugins = {}
