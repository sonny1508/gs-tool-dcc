import os
import tempfile
import shutil

from zoo.core import manager, errors, constants
from zoo.core.commands import action
from zoo.core.util import zlogging
from zoo.core.util import filesystem

logger = zlogging.getLogger(__name__)


class BundlePackages(action.Action):
    id = "bundlePackages"

    def arguments(self, argParser):
        argParser.add_argument("--destination",
                               required=True,
                               help="The Zip file destination path, The parent directory will be created for you "
                                    "if it doesn't exist.",
                               type=str)
        argParser.add_argument("--buildVersion",
                               type=str,
                               required=False,
                               help="The build version to apply to the bundle.",
                               default="")
        argParser.add_argument("--clean",
                               help="If there's an existing destination path then remove it.",
                               action="store_true")

    def run(self):
        logger.debug("Starting to cache packages: arguments- {}".format(self.options.destination))
        if not self.options.destination:
            raise errors.MissingCliArgument("destination")
        if self.options.clean and os.path.exists(self.options.destination):
            shutil.rmtree(os.path.dirname(self.options.destination))
        loadedEnv = self.config.resolver.loadEnvironmentFile()
        packagesToBundle = []
        # preprocess requested packages to ensure correctness.
        for packageName, rawDescriptor in loadedEnv.items():
            rawDescriptor["name"] = packageName
            descriptor = self.config.descriptorFromDict(rawDescriptor)
            if descriptor.type != descriptor.ZOOTOOLS:  # todo: temp
                logger.error("Only descriptor types: {} supported when bundling".format(descriptor.ZOOTOOLS))
                raise errors.UnsupportedDescriptorType(descriptor)

            pkg = self.config.resolver.packageForDescriptor(descriptor)
            if not pkg:
                logger.error("Missing package: {}".format(pkg))
                raise errors.MissingPackageVersion(descriptor)
            packagesToBundle.append(pkg)

        # ok we're in the clear
        # create a temp dir
        tempDir = tempfile.mkdtemp()
        # construct a clean install using the current as the base
        installDir = os.path.join(tempDir, "zootoolspro")
        mayadir = os.path.join(tempDir, "maya")
        args = ["--app", "maya",
                "--app_dir", mayadir,
                "--destination", installDir,
                "--buildVersion", self.options.buildVersion]

        try:
            self.config.runCommand("setup", args)
            newConfig = manager.zooFromPath(installDir)
            # cache all packages using the current env
            # this is done by using the pathDescriptor with the copy, this way
            # its raw as possible without any bells and whistles like git.
            # now zip up the full zootoolspro root folder
            #
            newConfig.runCommand("cachePackages", [])

            for pkg in packagesToBundle:
                newConfig.runCommand("installPackage", ["--path", pkg.dirname()])
            filesystem.ensureFolderExists(os.path.dirname(self.options.destination))
            filesystem.zipdir(installDir,
                              self.options.destination,
                              constants.FILE_FILTER_EXCLUDE)
        except Exception:
            logger.error("Failed to setup and cache zootools",
                         exc_info=True)
            return False
        finally:
            shutil.rmtree(tempDir)

        return True
