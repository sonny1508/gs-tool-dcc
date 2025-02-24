import os

from zoo.core import errors
from zoo.core.util import zlogging
from zoo.core.plugin import plugin, pluginmanager

logger = zlogging.getLogger(__name__)


class DescriptorRegistry(pluginmanager.PluginManager):
    """A registry for package version descriptors.

    This class is responsible for managing the descriptors used the zootools environment.
    It loads descriptors from a cache generated from the Zoo class Instance, and it can generate
    this cache on demand.

    :param interface: The plugin interface. Defaults to :class:`Descriptor`.
    :type interface: class
    :param variableName: The name of the variable to hold the plugins. Defaults to None.
    :type variableName: str
    """

    def __init__(self, config, interface=plugin.Plugin, variableName=None):
        super(DescriptorRegistry, self).__init__(interface, variableName,
                                                 name="descriptors")
        self._config = config
        self.currentDescriptorCache = {}

    def generateCache(self):
        """Generate the descriptor cache."""
        cache = self._config.resolver.loadEnvironmentFile()
        for name, descriptorDict in cache.items():
            descriptorPlugin = self.descriptorFromDict(descriptorDict)
            self.currentDescriptorCache[name] = descriptorPlugin

    def descriptorForPackages(self, *packageNames):
        """Get the descriptors for a given set of package names.

        :param packageNames: The names of the packages to get descriptors for.
        :type packageNames: tuple of str
        :return: The descriptor plugins for the given packages, or None if the package is not found.
        :rtype: list of :class:`Descriptor`
        """
        count = len(packageNames)
        foundPackages = [None] * count
        currentCache = self.currentDescriptorCache
        for index, name in enumerate(packageNames):
            descriptorPlugin = currentCache.get(name)
            if descriptorPlugin is None:
                continue
            foundPackages[packageNames.index(name)] = descriptorPlugin
        return foundPackages

    def descriptorFromDict(self, info):
        """Get the descriptor plugin for a given descriptor dictionary.

        :param info: The descriptor dictionary to get the plugin for.
        :type info: dict
        :return: The descriptor plugin for the given dictionary.
        :rtype: :class:`Descriptor`
        """
        requestedType = info.get("type")
        descriptorName = info.get("name")
        packageDescriptor = self.currentDescriptorCache.get(descriptorName)

        if packageDescriptor is not None:
            return packageDescriptor
        logger.debug("Resolve descriptor for requested info: {}".format(info))

        pluginObj = self.getPlugin(requestedType)
        if pluginObj is not None:
            return pluginObj(self._config, descriptorDict=info)
        raise NotImplementedError("Descriptor not supported: {}".format(info))

    def descriptorFromPath(self, location, descriptorInfo):
        """Returns the matching Descriptor object for the given path.

        :param location: The location of the package, can be any of the paths \
        supported by our descriptors. i.e a .git path, physical path etc
        :type location: str
        :param descriptorInfo: Descriptor dic see :class:`Descriptor` for more info.
        :type descriptorInfo: dict
        :return:
        :rtype: :class:`Descriptor`
        :raise: NotImplementedError
        """
        if location.endswith(".git") and not os.path.exists(location):
            descriptorInfo.update({"type": "git"})
            return self.getPlugin("git")(self._config, descriptorInfo)
        elif os.path.exists(location):
            # because the requested path is a physical
            # location we can parse the package and compose the descriptor
            # dict ourselves.
            pkg = self._config.resolver.packageFromPath(location)
            if not pkg:
                raise errors.InvalidPackagePath(location)
            descriptorInfo.update({"name": pkg.name,
                                   "version": str(pkg.version),
                                   "path": location,
                                   "type": "path"})

            # physical path on disk
            return self.getPlugin("path")(self._config,
                                          descriptorInfo)
        raise NotImplementedError("We don't currently support descriptor: {}".format(location))


class Descriptor(plugin.Plugin):
    """A descriptor represents an identifiable item that can be used to resolve or install dependencies.

    :param config: The zoo config instance
    :type config: :class:`zoo.core.manager.Zoo`
    :param descriptorDict: The Descriptor dict containing at least the type and name
    :type descriptorDict: dict
    """
    # descriptor type constants
    LOCAL_PATH = "path"
    ZOOTOOLS = "zootools"
    # class variables cache
    requiredkeys = ()

    def isDescriptorOfType(self, descriptorType):
        return self.type == descriptorType

    def __init__(self, config, descriptorDict, manager=None):
        super(Descriptor, self).__init__(manager)
        self.config = config
        self._descriptorDict = descriptorDict
        self.type = descriptorDict["type"]
        self.name = descriptorDict.get("name")
        # whether this package descriptor should be active in the project
        self.active = descriptorDict.get("active", True)
        self.version = ""
        self._package = None
        self._validate(descriptorDict)

    @property
    def package(self):
        """
        Returns the zoo package instance attached to this descriptor or None

        :return: The zoo package for the descriptor
        :rtype: :class:`zoo.core.packageresolver.package.Package` or None
        """
        return self._package

    @package.setter
    def package(self, pkg):
        """
        Returns the zoo package instance attached to this descriptor or None

        :param pkg: The zoo package for the descriptor
        :type pkg: :class:`zoo.core.packageresolver.package.Package`
        
        """
        self._package = pkg

    def serialize(self):
        return self._descriptorDict

    def __eq__(self, other):
        otherdict = other.serialize()
        return all(v == otherdict.get(k) for k, v in self.serialize().items())

    def __ne__(self, other):
        otherdict = other.serialize()
        return not any(v != otherdict.get(k) for k, v in self.serialize().items())

    def __repr__(self):
        return "<{}> Name: {}, Type: {}".format(self.__class__.__name__, self.name, str(self.type))

    def installed(self):
        if not self.package:
            return False
        existing = self.config.resolver.existingPackage(self.package)
        return existing is not None

    def _validate(self, descriptorDict):
        keys = set(descriptorDict.keys())
        requiredSet = set(self.requiredkeys)
        if not requiredSet.issubset(keys):
            missingKeys = requiredSet.difference(keys)
            raise errors.DescriptorMissingKeys("<{}>: {} Missing required Keys: {}".format(self.__class__.__name__,
                                                                                           self.name,
                                                                                           missingKeys))
        return True

    def resolve(self, *args, **kwargs):
        raise NotImplementedError()

    def install(self, **arguments):
        raise NotImplementedError()

    def uninstall(self, remove=False):
        if self.package is None:
            logger.debug("Descriptor: {} has no resolved package".format(self.name))
            return False
        pkgRoot = self.package.root
        self.config.resolver.removeDescriptorFromEnvironment(self)
        if remove:
            self.package.delete()
            versionedPackageDir = os.path.dirname(pkgRoot)
            if len(os.listdir(versionedPackageDir)) == 0:
                os.rmdir(versionedPackageDir)

        return True
