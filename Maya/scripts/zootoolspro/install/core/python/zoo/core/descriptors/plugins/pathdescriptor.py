import os

from zoo.core import errors
from zoo.core import constants
from zoo.core.descriptors import descriptor
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class PathDescriptor(descriptor.Descriptor):
    id = "path"
    requiredkeys = ("name", "type", "path")

    def __init__(self, config, descriptorDict):
        super(PathDescriptor, self).__init__(config, descriptorDict)
        self._path = descriptorDict["path"]

    @property
    def path(self):
        return os.path.normpath(os.path.expandvars(self._path.replace(constants.INSTALL_FOLDER_TOKEN,
                                                                      self.config.rootPath)))

    @path.setter
    def path(self, value):
        self._path = value

    def resolve(self):
        # a path descriptor only contains a path so we need to first resolve
        # the package inside
        package = self.config.resolver.packageFromPath(self.path)
        if package is None:
            logger.warning(
                "The specified package does not exist, please check your configuration: {}".format(self.path))
            return False
        self.package = package
        self.version = package.version
        return True

    def install(self, **arguments):
        # if the supplied package(dealt with in the resolve method), fails
        # to find a valid package from the given path
        # we'll forcibly raise an error
        if self.package is None:
            raise errors.InvalidPackagePath(self.path)
        if self.installed():
            raise errors.PackageAlreadyExists(self.package)
        inplaceInstall = arguments.get("inPlace")
        logger.debug("Running path descriptor: {}.install with arguments: {}".format(self.name, arguments))
        packageDirectory = os.path.join(self.config.packagesPath, self.name, str(self.package.version))
        if not inplaceInstall:
            try:
                installedPkg = self.package.copyTo(self.package, packageDirectory)
                logger.debug("Finished copying: {}->{}".format(self.package, packageDirectory))
            except OSError:
                logger.error("Failed to copy package: {} to destination: {}".format(self.package.name,
                                                                                    packageDirectory),
                             exc_info=True)
                return False
            del self._descriptorDict["path"]
            self._descriptorDict.update({"type": "zootools",
                                         "version": str(self.package.version),
                                         })
        else:
            installedPkg = self.config.resolver.packageFromPath(self.path)
        self.config.resolver.cache[str(installedPkg)] = installedPkg
        self.config.resolver.updateEnvironmentDescriptorFromDict(self._descriptorDict)
        return True
