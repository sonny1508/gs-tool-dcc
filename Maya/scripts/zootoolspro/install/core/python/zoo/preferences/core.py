import os
import logging
import shutil
import timeit

from zoovendor import six
from zoo.core.plugin import pluginmanager
from zoo.core.tooldata import tooldata
from zoo.core.util import filesystem, pathutils
from zoo.preferences import prefinterface, errors, constants


logger = logging.getLogger(__name__)


class PreferenceManager(tooldata.ToolSet):
    """Preference Manager is responsible for discovery of preference folders/files
    and the management of said folders/files.

    See :ref:preinterface.PreferenceInterface: to know about how to handle interfacing to installed package
    preferences. These should be used when accessing preference files as a client of zootools prefs.

    These can be listed via :func:`PreferenceManager.interfaces` or :func:`PreferenceManager.Interface`
    to return a new instance.

    .. code-block:: python

        pref = PreferenceManager()
        # query the current root directories
        pref.roots  # OrderedDict

        # add a custom directory for the preferences, by default the user_preferences root is
        # already created but you can create another. Note: the order of the preferences
        # root directories specified in pref.roots matters for priority searching
        pref.addRoot("/MyCustomPrefererenceDirectory", root="custom_dir") # custom_dir is the root name

        # optional feature to copy all default preference to a root location
        pref.copyOriginalToRoot("custom_dir")

        # find a .pref and load it from disk
        # specifying the root will search and load the .pref relative to the root.
        # specifying root=None will search each root until the .pref is found
        obj = pref.findSetting("prefs/global/stylesheet", "user_preference")
        # a SettingsObject is always returned so do the following to validate
        if not obj.isValid(): print("handle invalid settings here")

        # get the fullpath to the file, though you shouldn't rename or move the file
        # since the preferences internally rely on the relative path, for this
        # reason there is no argument in the settingObject interface to rename.
        obj.path()

        # return the root Path object that it belongs too, remember the root
        # can change depending on which root its save to. see below
        obj.rootPath()
        # return the root name
        obj.root

        # make some change
        obj["settings"]["someSettings"] = {"name": "test"}

        # save the change to disk in place.
        obj.save()

        # save it to a different location.
        pref.createSetting(obj.relativePath, "custom_dir", obj)

    """

    DEFAULT_USER_PREFERENCE_NAME = "user_preferences"

    def __init__(self, configurationManager):
        super(PreferenceManager, self).__init__()

        self.extension = ".pref"
        self._interfaceManager = pluginmanager.PluginManager(
            interface=[prefinterface.PreferenceInterface],
            variableName="id",
            name="prefs",
        )
        self.configurationManager = configurationManager
        self._resolveInterfaces()
        self.transactions = {}  # "relativePath": :class:`transaction`
        self._resolveRootLocations()

    def _resolveRootLocations(self):
        rootsPath = self.configurationManager.preferenceRootsPath()
        if not os.path.exists(rootsPath):
            raise ValueError("Missing Preferences config file: {}".format(rootsPath))
        roots = filesystem.loadJson(rootsPath)
        for rootName, rootPath in roots.items():
            # handle default user preference path probably not super bad putting here
            # this should be the main entry point to root generation anyways
            if rootName == PreferenceManager.DEFAULT_USER_PREFERENCE_NAME:
                filesystem.ensureFolderExists(self._resolveRoot(rootPath))
            # If at this point any root specified don't exist error intentional to avoid
            # unintentional pathing
            self.addRoot(rootPath, rootName)

    def _resolveInterfaces(self):
        """Internal use only, resolves all interface classes.

        This works by looping all the repos finding the preferences/interface package path and using the
        zoo.core.plugin.pluginmanager.PluginManager class to handle registration
        """
        for prefPath in self.iterPackagePreferenceRoots():
            interfacePath = os.path.join(prefPath, constants.INTERFACE_FOLDER)
            if not os.path.exists(interfacePath):
                continue
            self._interfaceManager.registerByPackage(str(interfacePath))

    def hasInterface(self, name):
        """Returns whether an interface with the "name" exists.

        :param name: id variable on the interface class
        :type name: str
        :return: True if exists in the registry
        :rtype: bool
        """
        return self._interfaceManager.getPlugin(name) is not None

    def interface(self, name):
        """Returns the interface object.

        use the id * silky change

        An Interface is a class that contains method to communicate with the preferences data structures.
        Interfaces are the preferred use over direct access to the data.

        :param name: The interface class id
        :type name: str
        :rtype: :class:`zoo.preferences.prefinterface.PreferenceInterface`
        """
        interfacecls = self._interfaceManager.loadedPlugins.get(name)
        if interfacecls is None:
            interfacecls = self._interfaceManager.getPlugin(name)
            if interfacecls is None:
                raise ValueError("Missing interface by name: {}".format(name))
            return self._interfaceManager.loadPlugin(name, preference=self)

        return interfacecls

    def interfaces(self):
        """Returns all currently available interfaces names

        :rtype: list(idStr)
        """
        return self._interfaceManager.plugins.keys()

    def iterPackagePreferenceRoots(self):
        """Generator function which returns the preferences root folder directly
        under each package directory.

        This function should only be used for admin purposes and any modification
        under this root will not be maintained between package versions.

        ..code-block: python

            for root in preference.iterPackagePreferenceRoots:
                print(root) # packagePath/preferences


        :return: Generator function
        :rtype: Generator(str)
        """
        # get the default location which always stored just under the repo path
        for package in self.configurationManager.resolver.cache.values():
            # grab the preferences path for the package
            preferencesPath = os.path.join(package.root, constants.PREFERENCE_FOLDER)
            # ignore the package if doesn't exist
            if not os.path.exists(preferencesPath):
                continue

            yield preferencesPath

    def iterPackagePrefPath(self):
        """Generator Function which iterates over each installed package
        and returns the subdirectory of the preferences i.e. packagePath/preferences/prefs

        :rtype: str
        """
        for preferenceRoot in self.iterPackagePreferenceRoots():
            prefPath = os.path.join(preferenceRoot, "prefs")
            if not os.path.join(prefPath):
                continue
            yield prefPath

    def packagePreferenceRootLocation(self, packageName):
        """Returns the absolute path of the installed package preference root folder.
        
        :param packageName: The install package path
        :type packageName: str
        :raises ValueError: [description]
        :raises ValueError: Raised when either the package doesn't exist or the preferences \
            folder doesn't exist.
        :return: [description]
        :rtype: [type]
        """
        package = self.configurationManager.resolver.packageByName(packageName)
        if not package:
            msg = "Requested package '{}' doesn't exist within the current environment".format(
                packageName
            )
            logger.error(msg)
            raise ValueError(msg)
        preferencesPath = os.path.join(package.root, constants.PREFERENCE_FOLDER)
        # ignore the package if it doesn't exist
        if not os.path.exists(preferencesPath):
            msg = "Default preferences location doesn't exist at: {}".format(
                preferencesPath
            )
            logger.error(msg)
            raise ValueError(msg)
        return preferencesPath

    def packagePreferenceLocation(self, packageName):
        """Returns the installed package preference path by package name.

        :param packageName: The install package name
        :type: str
        :raise: ValueError
        """
        return os.path.join(self.packagePreferenceRootLocation(packageName), "prefs")

    def copyOriginalToRoot(self, root, force=False):
        """Method to copy the preference files and folders from each zoo repository into the default zoo_preference
        location

        :param root: The root name location which should be part of the instance
        :type root: str
        :param force: If True the file exists at the root location it will be overridden.
        :type force: bool
        """
        defaultLoc = self.root(root)
        for preferencesPath in self.iterPackagePreferenceRoots():
            prefRoot = os.path.join(preferencesPath, "prefs")
            startTime = timeit.default_timer()
            for root, dirs, files in os.walk(prefRoot):
                for f in files:
                    prefFile = os.path.join(root, f)
                    if not prefFile.endswith(constants.PREFERENCE_EXT):
                        continue
                    relativePath = pathutils.relativeTo(preferencesPath, prefFile)
                    destination = os.path.join(defaultLoc, relativePath)
                    if force or not os.path.exists(destination):
                        filesystem.ensureFolderExists(os.path.dirname(destination))
                        logger.debug(
                            "Transferring preference {} to destination: {}".format(
                                six.text_type(prefFile), destination
                            )
                        )
                        shutil.copy2(six.text_type(prefFile), destination)

            logger.debug(
                "Finished package preferences to: {},"
                " total Time: {}".format(root, timeit.default_timer() - startTime)
            )

    def moveRootLocation(self, root, destination):
        """ Physically moves the give root location to the destination directory.

        If the destination doesn't exist it will be created.

        :note: Using this function to move preferences requires a restart

        :param root: The root name location which should be part of the instance
        :type root: str
        :param destination: The absolute fullpath to the destination folder
        :type destination: str
        :return: first element is whether the root was copied, second element \
        is the original root location
        :rtype: (bool, str)
        :raise: RootDoesntExistsError
        :raise: OSError
        :raise: RootDestinationAlreadyExistsError
        """
        # this will raise a RootDoesntExistsError if the root is missing
        rootPath = self.root(root)
        destRoot = destination
        if os.path.exists(destRoot):
            raise errors.RootDestinationAlreadyExistsError(destRoot)
        shutil.copytree(rootPath, destRoot)
        self.setRootLocation(root, destination)
        try:
            logger.debug("Removing Root preferences path: {}".format(rootPath))
            shutil.rmtree(rootPath)
            logger.debug("Removed Source preferences path: {}".format(rootPath))
        except OSError:
            logger.error(
                "Failed to remove the preference root: {}".format(rootPath),
                exc_info=True
            )
            raise

    def setRootLocation(self, root, destination):
        """Will only set the root location, without moving any of the files.

        :param root: The root name location which should be part of the instance
        :type root: str
        :param destination: The absolute fullpath to the destination folder
        :type destination: str
        :return:
        """
        orig = self.roots[root]
        del self.roots[root]
        try:
            self.addRoot(destination, root)
        except Exception as e:
            self.roots[root] = orig
            raise e

    @classmethod
    def assetPath(cls):
        """Asset Path

        eg. ~/zoo_preferences/assets

        :return:
        """
        envPath = os.getenv(constants.ASSETS_PATH_ENV)
        if envPath:
            envPath = os.path.normpath(os.path.expandvars(os.path.expanduser(envPath)))
            if os.path.exists(envPath):
                return envPath
        return os.path.join(cls.defaultPreferencePath(), "assets")

    @property
    def shouldCopyDefaultAssets(self):
        """Returns whether the default assets should be copied to the user's assets folder.

        :rtype: bool
        """
        try:
            return bool(os.getenv("ZOO_ASSETS_NO_DEFAULTS", "0"))
        except TypeError:
            logger.error("ZOO_ASSETS_NO_DEFAULTS environment variable is not an integer")
            return False

    @classmethod
    def prefsPath(cls):
        """Prefs Path

        e.g. ~/zoo_preferences/prefs

        :return:
        """
        return os.path.join(cls.defaultPreferencePath(), "prefs")

    @classmethod
    def defaultPreferencePath(cls):
        """Zoo Preferences Path (zoo_preferences)

        Retrieves the path to the Zoo Tools User Preferences, if '~/zoo_preferences' then displays full path

        :return:
        """
        return os.path.normpath(preference.root("user_preferences"))

    def defaultPreferenceSettings(self, packageName, relativePath):
        """Returns the default preferences for the package.

        :param packageName: The package name currently in the environment.
        :type packageName: str
        :param relativePath: The relative path from the preferences folder under the \
        package root.
        :type relativePath: str
        :return: The SettingsObject for the preferences file or None
        :rtype: ::class:`zoo.core.tooldata.tooldata.SettingsObject` or None
        """
        packagePref = self.packagePreferenceLocation(packageName)
        obj = self.settingFromRootPath(relativePath, packagePref)
        if obj.isValid():
            return obj
        # todo: error

    def findSetting(self, relativePath, root, name=None, extension=None):
        """Searches the roots for the relativePath and returns the settingObject or if 'name' is provided then
        the value of the key(name) will be returned.

        :param relativePath: e.g. interface/stylesheet
        :type relativePath: str
        :param root: The root name to search, if None then all roots will be searched until the relativePath is found.
        :param name: the name to
        :type name: str
        :return: the settings value usually a standard python type. SettingObject or the value or 'name'
        :rtype: :class:`zoo.core.tooldata.tooldata.SettingObject`
        """
        mainFileSetting = super(PreferenceManager, self).findSetting(
            relativePath, root, extension=extension
        )
        if name is not None:
            settings = mainFileSetting.get(constants.SETTINGS_DEF_KEY, {})
            if name not in settings:
                raise errors.SettingsNameDoesntExistError(
                    "Failed to find setting: {} in file: {}".format(
                        name, mainFileSetting
                    )
                )
            return settings[name]
        return mainFileSetting


class Transaction(dict):
    """This class inherent's from dict() and re-implements the __getattribute__ and __setattr__ to provide the '.'
    syntax.
    The intention of the class is to track changes for a given item this may be an asset or shot for example.
    Any change made will be applied to this commit object instead of the item.
    It is the responsibility of the items class to handle applying to the commit object or the item.

    :note: not currently used, keeping it here as placeholder for the next update.
    """

    def __init__(self, **kwargs):
        super(Transaction, self).__init__()
        self.applyFromDict(kwargs, asDefault=True)

    def __getattribute__(self, item):
        try:
            keyvalue = self[item]
            return keyvalue.get("value", keyvalue.get("default"))
        except KeyError:
            return super(Transaction, self).__getattribute__(item)

    def __setattr__(self, key, value):
        self.setValue(key, value)

    def applyFromDict(self, data, asDefault=False):
        for key, value in data.items():
            self.setValue(key, value, asDefault=asDefault)

    def value(self, name):
        current = self.keyInfo(name)
        value = current.get("value")
        if value is None:
            return current["default"]
        return value

    def setValue(self, name, value, asDefault=False):
        current = self.get(name)
        if current is None:
            self[name] = {"default": value}
            return
        if asDefault:
            self[name]["default"] = value
            return
        # if the change value isn't the same as the default value
        if not self.isDefault(name, value):
            self[name]["value"] = value
            return
        self.revert(name)

    def keyInfo(self, name):
        current = self.get(name)
        assert current is not None, "No attribute by the name : {}".format(name)
        return current

    def changes(self):
        return {i: d.get("value", d.get("default")) for i, d in self.items()}

    def revert(self, name):
        current = self.keyInfo(name)
        self[name] = {"default": current["default"]}

    def revertAll(self):
        for i, d in self.data.items():
            self[i] = {"default": d["default"]}

    def isDefault(self, name, value):
        current = self.keyInfo(name)
        default = current.get("default")
        return default == value

    def hasChange(self, name):
        current = self.keyInfo(name)
        try:
            current["value"]
            return True
        except KeyError:
            return False


# global preference manager instance
preference = None # type: PreferenceManager


def currentInstance():
    """
    :rtype: :class:`PreferenceManager`
    """
    global preference
    return preference


def setInstance(instance):
    """
    :type instance: :class:`PreferenceManager`
    """
    global preference
    preference = instance
