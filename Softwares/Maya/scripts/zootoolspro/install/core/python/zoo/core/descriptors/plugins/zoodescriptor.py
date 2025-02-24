from zoo.core import errors
from zoo.core.descriptors import descriptor
from zoo.core.util import zlogging


logger = zlogging.getLogger(__name__)


class ZooDescriptor(descriptor.Descriptor):
    """Zoo distributable descriptor
    """
    id = "zootools"
    requiredKeys = ("version", "name", "type")

    def __init__(self, config, descriptorDict):
        super(ZooDescriptor, self).__init__(config, descriptorDict)
        self.version = descriptorDict["version"]

    def resolve(self, *args, **kwargs):
        logger.debug("Resolving zootools descriptor: {}-{}".format(self.name, self.version))
        existingPackage = self.config.resolver.packageForDescriptor(self)
        if not existingPackage:
            raise errors.MissingPackageVersion("Missing package: {}".format(self.name))
        self.package = existingPackage
        return True

    def install(self, **arguments):
        if self.package:
            logger.debug("Package: {} already exists, skipping install".format(self.name))
            # self.as
            # self.config.resolver.bakePackageToEnv(self.package)
            return True
        raise NotImplementedError("We Don't currently support downloading internal packages")
