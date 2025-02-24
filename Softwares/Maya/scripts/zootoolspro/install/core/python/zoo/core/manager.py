import os
import ctypes
import sys

try:
    # only accessible on windows
    from ctypes.wintypes import MAX_PATH
except (ImportError, ValueError):
    MAX_PATH = 260

from zoo.core import errors
from zoo.core.commands import loader, action
from zoo.core.packageresolver import resolver
from zoo.core.descriptors import descriptor
from zoo.core import constants
from zoo.core.util import env, filesystem
from zoo.core.plugin import pluginmanager, coreplugin
from zoo.core.util import zlogging
from zoo.core import engine

logger = zlogging.getLogger(__name__)


class Zoo(object):
    """Zoo class is the main entry point for operating on any part of zoo tools.

    :param zooPath: The root location of zootools root folder ie. the one above the installation folder.
    :type zooPath: str
    :raise: :class:`errors.FileNotFoundError`
    """

    def __init__(self, zooPath):
        """ Initializes the default paths for zootools

        Raises :class:`errors.FileNotFoundError` in the case where the provided
        pat doesn't exist.
        """
        if not os.path.exists(zooPath):
            raise errors.FileNotFoundError(zooPath)
        zooPaths = _resolveZooPathsFromPath(zooPath)
        logger.debug("Initializing zootools from zooPath: {}: {}".format(zooPath, zooPaths),
                     extra=zooPaths)
        self._rootPath = zooPaths["root"]  # type: str
        self._corePath = zooPaths["core"]  # type: str
        self._pyFolderPath = zooPaths["python"]  # type: str
        self._configPath = zooPaths["config"]  # type: str
        self._packagesPath = zooPaths["packages"]  # type: str
        self._resolver = resolver.Environment(self)
        self._commandLibCache = pluginmanager.PluginManager([action.Action],
                                                            variableName="id",
                                                            name="cliCommand")
        self._commandLibCache.registerByEnv(constants.COMMANDLIBRARY_ENV)
        # zoo tools core plugins for extending startup and other behaviour
        # self._corePluginsManager = pluginmanager.PluginManager([coreplugin.CorePlugin],
        #                                                        variableName="id",
        #                                                        name="corePlugins")
        # self._corePluginsManager.registerPaths([os.path.join(self._configPath, "plugins")])

        self._descriptorLib = descriptor.DescriptorRegistry(self, [descriptor.Descriptor],
                                                            variableName="id")
        self._descriptorLib.registerByEnv("ZOO_DESCRIPTOR_PATH")
        self._descriptorLib.generateCache()

    def coreVersion(self):
        """Returns core(this) package version string.

        :return: coreVersion ie. "1.0.0"
        :rtype: str
        """
        package = os.path.join(self._corePath, "zoo_package.json")
        packageInfo = filesystem.loadJson(package)
        return packageInfo["version"]

    def buildVersion(self):
        """Returns the Zoo Tools build version string.

        :return: buildVersion ie. "1.0.0"
        :rtype: str
        """
        package = self.buildPackagePath()
        if not os.path.exists(package):
            return "DEV"
        buildPackage = filesystem.loadJson(package)
        return buildPackage.get("version", "DEV")

    def buildPackagePath(self):
        """Returns the fullPath to the zoo_package.json which is the build package.

        :return: str
        """
        return os.path.join(self._rootPath, "zoo_package.json")

    @property
    def isAdmin(self):
        """Returns whether the current user is in admin mode.

        :return: True if admin.
        :rtype: bool
        """
        try:
            return bool(int(os.getenv(constants.ZOO_ADMIN, "0")))
        except TypeError:
            return False

    @isAdmin.setter
    def isAdmin(self, state):
        """Sets whether Zootools is in Admin mode for the current instance.

        By Having this set to True it allows tools to either allow or
        decline certain user behaviour.

        :param state: True if admin.
        :type state: bool
        """
        logger.info("Zoo Admin mode has been set to: {}".format(state))
        os.environ[constants.ZOO_ADMIN] = str(int(state))

    @property
    def commands(self):
        """Returns the executable cli commands dict cache.

        :return: Plugin manager instance
        :rtype: dict
        """
        return self._commandLibCache

    @property
    def rootPath(self):
        """Returns the root path of zootools.

        The root path directory is the folder above the installation folder

        :return: The root folder of zootools.
        :rtype: str
        """
        return self._rootPath

    @property
    def configPath(self):
        """Returns the config folder which sits below the root.

        :return: The config folder for zootools.
        :rtype: str
        """
        return self._configPath

    @property
    def corePath(self):
        """The core folder of zootools which is relative to the root under the
        installation folder.

         The core folder houses internal logic of zootools package management.

        :return: The core folder
        :rtype: str
        """
        return self._corePath

    @property
    def packagesPath(self):
        """Returns the package repository path under the zootools/install folder.

        This folder is the location for all installed packages.
        Each package Housed here is in the form of::

            Packages
                - packageName
                    - packageVersion(LooseVersion)
                        -code

        :return: The package's folder.
        :rtype: str
        """
        return self._packagesPath

    @property
    def pythonPath(self):
        """Returns the python folder path under the core installation.

        :return: The "python" folder path.
        :rtype: str
        """
        return self._pyFolderPath

    @property
    def resolver(self):
        """Returns the environment resolver instance which contains the package cache.

        :return: The Environment Resolver instance
        :rtype: :class:`resolver.Environment`
        """
        return self._resolver

    @property
    def commandLibrary(self):
        """Returns the CLI command plugin manager instance.

        Only one is created per Zoo session

        :rtype: :class:`pluginmanager.PluginManager`
        """
        return self._commandLibCache

    @property
    def descriptorLibrary(self):
        """Returns the descriptor types plugin manager instance.

        Only one is created per Zoo session

        :rtype: :class:`descriptor.DescriptorRegistry`
        """
        return self._descriptorLib

    def preferenceRootsPath(self):
        """Returns the preferences roots config file path in the installRoot/config/env folder.

        :rtype: str
        """
        return os.path.join(self.configPath, "env", "preference_roots.config")

    def preferenceRootsConfig(self):
        """Loads and returns the preference_roots file contents as a dict

        :rtype: dict
        """
        return filesystem.loadJson(self.preferenceRootsPath())

    def cacheFolderPath(self):
        """Returns the current Zoo tools cache folder.

        The cache folder is used to store temporary data like pip installed libraries, logs, temp export files etc.

        :rtype: str
        """
        cacheEnv = os.getenv(constants.CACHE_FOLDER_PATH_ENV)
        if cacheEnv is None:
            return _patchRootPath(os.path.join(self.preferenceRootsConfig()["user_preferences"], "cache"))
        return os.path.expandvars(os.path.expanduser(cacheEnv))

    def sitePackagesPath(self):
        """Returns the site packages folder path where zootools installs pip packages when needed.
        This path is python version dependent.

        :rtype: str
        """
        cacheFolder = self.cacheFolderPath()
        pythonVersion = ".".join(map(str, sys.version_info[:3]))
        return os.path.abspath(os.path.join(cacheFolder, "site-packages", pythonVersion))

    def descriptorFromDict(self, descriptorDict):
        """Helper method which calls for :func:`zoo.core.descriptors.descriptor.descriptorFromDict`

        :param descriptorDict: See :func:`zoo.core.descriptors.descriptor.descriptorFromDict` for more info
        :type descriptorDict: dict
        :return: The corresponding Descriptor instance
        :rtype: :class:`zoo.core.descriptors.descriptor.Descriptor`
        """
        return self._descriptorLib.descriptorFromDict(descriptorDict)

    def descriptorForPackageName(self, name):
        """Returns the matching descriptor instance for the package name.

        :param name: The zoo package name to find.
        :type name: str
        :return: The descriptor or None
        :rtype: :class:`zoo.core.descriptors.descriptor.Descriptor` or None
        """
        plugins = self._descriptorLib.descriptorForPackages(name)
        if plugins:
            return plugins[0]  # backwards compat for now

    def descriptorsForPackageNames(self, *names):
        """Returns the matching descriptor instances for the package names.

        :param names: The zoo package names to find.
        :type names: tuple[str]
        :return: The descriptor or None
        :rtype: list[:class:`zoo.core.descriptors.descriptor.Descriptor` or None]
        """
        return self._descriptorLib.descriptorForPackages(*names)

    def descriptorFromPath(self, location, descriptorDict):
        """Given absolute path and descriptor dict return the matching Descriptor instance.

        :param location: The absolute path to the package.
        :type location: str
        :param descriptorDict: The descriptor
        :type descriptorDict: dict
        :rtype: :class:`zoo.core.descriptors.descriptor.Descriptor` or None
        """
        return self._descriptorLib.descriptorFromPath(location, descriptorDict)

    def runCommand(self, commandName, arguments):
        """Run's the specified CLI command.

        User runCommand("commandName", ["--help"]) to get the command help.

        :param commandName: The command ID name.
        :type commandName: str
        :param arguments: List of cls commands to pass to the command.
        :type arguments: list[str]
        :return: True if the command was run.
        :rtype: bool
        """
        commandObj = self._commandLibCache.getPlugin(commandName)
        if not commandObj:
            return
        argumentsCopy = list(arguments)
        if commandName not in arguments:
            argumentsCopy.insert(0, commandName)
        argumentParser, subParser = loader.createRootParser()
        instance = commandObj(config=self)
        instance.processArguments(subParser)

        args = argumentParser.parse_args(argumentsCopy)

        return args.func(args)

    def shutdown(self):
        """Shutdown Method for zootools excluding Host application plugin related code.
        """
        engine.shutdownEngine()
        self.resolver.shutdown()
        # clear out the sys.modules of all zoo modules currently in memory
        from zoo.core.util import flush
        flush.reloadZoo()
        from zoo.preferences import core
        flush.flushUnder(os.path.dirname(core.__file__))
        setCurrentConfig(None)

    def reload(self):
        """Reloads all of zootools python packages, libraries, environment variables.

        :return: A New Zoo Manager instance.
        :rtype: :class:`Zoo`
        """
        root = self.rootPath
        self.shutdown()
        cfg = zooFromPath(root)
        cfg.resolver.resolveFromPath(cfg.resolver.environmentPath())
        return cfg


# global storage of zoo config,
# note: im not all that happy with globals but we need a way
# to handle caching of the environment to avoid re-calculating
# packages. I would also like to avoid singletons here.
_ZOO_CONFIG_CACHE = None


def currentConfig():
    """Returns the :class:`Zoo` instance currently initialized globally.

    If this func returns None call :func:`zooFromPath`.

    :return: The currently initialized :class:`Zoo`
    :rtype: :class:`Zoo` or None
    """
    global _ZOO_CONFIG_CACHE
    return _ZOO_CONFIG_CACHE


def setCurrentConfig(config):
    """Sets the :class:`Zoo` global instance.

    :warning: This overrides the global instanced :class:`Zoo` instance.

    If you need to run multiple instances in parallel use :func:`zooConfig`
    """

    global _ZOO_CONFIG_CACHE
    _ZOO_CONFIG_CACHE = config


def zooFromPath(path):
    """Returns the zootools instance for the given root path.

    :param path: The root path of zootools to initialize, \
    See :class:`Zoo` for more information.
    :type path: str
    :return: The zoo instance.
    :rtype: :class:`Zoo`
    """
    assert os.path.exists(path), "Path doesn't exist: {}".format(path)
    cfg = Zoo(path)
    setCurrentConfig(cfg)

    return cfg


def _resolveZooPathsFromPath(path):
    """ Internal function which resolves the zootools main paths

    Resolves "root","config","core","packages"
    :todo  config, package folders to be part of the environment and applied here.
    """
    logger.debug("Resolving zootools from supplied path: {}".format(path))
    installFolder = os.path.join(path, "install")
    cfgFolder = os.path.join(path, constants.CONFIG_FOLDER_NAME)
    pkgFolder = os.path.join(path, "install", constants.PKG_FOLDER_NAME)
    outputPaths = dict(config=cfgFolder,
                       packages=pkgFolder,
                       root=path
                       )
    if os.path.exists(installFolder):
        logger.debug("Folder Install Folder: {}".format(installFolder))
        outputPaths["python"] = os.path.join(installFolder, "core", "python")
        outputPaths["core"] = os.path.join(installFolder, "core")
    else:
        # ok one last check by walk two folders up an check to see
        # if the install folder exists, if not we assume we're running vanilla.
        # path is the core folder python folder here
        walkedRoot = os.path.abspath(os.path.join(path, "..", ".."))
        walkedInstallFolder = os.path.abspath(os.path.join(walkedRoot, "install"))
        if os.path.exists(walkedInstallFolder):
            logger.debug("Found root folder: {}".format(walkedRoot))
            outputPaths["root"] = walkedRoot
            outputPaths["core"] = os.path.join(walkedInstallFolder, "core")
            outputPaths["python"] = os.path.join(walkedInstallFolder, "core", "python")
            outputPaths["config"] = os.path.join(walkedRoot, constants.CONFIG_FOLDER_NAME)
            outputPaths["packages"] = os.path.join(walkedInstallFolder, constants.PKG_FOLDER_NAME)
        else:
            logger.debug("Couldn't find install folder, falling back to base install solution: {}".format(path))
            # in this case the install folder doesn't exist at all and
            # we're running in uninstall vanilla state, in which
            # case initialize zootools without the folders at all
            outputPaths["config"] = ""
            outputPaths["core"] = path
            outputPaths["python"] = os.path.join(path, "python")
            outputPaths["packages"] = ""
    env.addToEnv(constants.COMMANDLIBRARY_ENV,
                 [os.path.join(outputPaths["python"], "zoo", "core", "commands", "library")])
    env.addToEnv(constants.ZOO_DESCRIPTOR_PATH,
                 [os.path.join(outputPaths["python"], "zoo", "core", "descriptors", "plugins")])
    return outputPaths


def _patchRootPath(rootPath):
    """Patch for zootools preferences path with the use of "~" where python now prioritizes USERPROFILE
    over HOME which happens to affect maya 2022 and below which sets the USERPROFILE to ~/Documents but
    maya 2023 is set to ~/ so this patches it globally across zoo only if "~" is the first character and
    it's windows ensuring that the existing prefs and updating/new installations are maintained.
    """
    if env.isWindows() and rootPath.startswith("~"):
        parts = os.path.normpath(rootPath).split(os.path.sep)
        dll = ctypes.windll.shell32

        buf = ctypes.create_unicode_buffer(MAX_PATH + 1)
        # note: 0x0005 is CSIDL_PERSONAL from win32com.shell.shellcon module but that doesn't come with python :(
        if dll.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
            return os.path.join(buf.value, *parts[1:])
    return os.path.expanduser(rootPath)
