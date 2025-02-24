from zoo.core.util import zlogging

from zoo.core import errors
from zoo.core.commands import action


logger = zlogging.getLogger(__name__)


class CachePackages(action.Action):
    """Cache package will ensure all packages defined in the environment has been installed,
    downloaded locally into the packages directory.
    """
    id = "cachePackages"

    def run(self):
        logger.debug("Starting to cache packages")
        loadedEnv = self.config.resolver.loadEnvironmentFile()
        for packageName, rawDescriptor in loadedEnv.items():
            rawDescriptor["name"] = packageName
            descriptor = self.config.descriptorFromDict(rawDescriptor)
            try:
                descriptor.resolve()
                descriptor.install()
            except errors.PackageAlreadyExists:
                logger.debug("Package: {} already exists, skipping.".format(descriptor.package))
                continue

