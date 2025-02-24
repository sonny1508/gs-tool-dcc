import os
import shutil
import tempfile
import zipfile

from zoo.core.util import zlogging

from zoo.core import errors
from zoo.core.commands import action
from zoo.core.packageresolver import package

logger = zlogging.getLogger(__name__)


class InstallPackage(action.Action):
    """Installs the given Package path into the current zoo environment.

    A package can be provided either as a physical storage path or a git
    path and tag.

    """
    id = "installPackage"

    def arguments(self, argParser):
        argParser.add_argument("--path",
                               required=True,
                               type=str,
                               help="Path to either a physical disk location or a https://*/*/*.git path."
                                    "If provide a git path then arguments 'name' and 'tag' should be specified")
        argParser.add_argument("--name",
                               required=False,
                               type=str,
                               help="The name of the package, valid only if 'path' argument is git path")
        argParser.add_argument("--tag",
                               required=False,
                               type=str,
                               help="The git tag to use.")
        argParser.add_argument("--inPlace",
                               action="store_true",
                               help="Valid only if 'path' argument is a physical path. if True then the"
                                    "specified path will be used directly else the package will be copied")

    def run(self):
        path = self.options.path
        tag = self.options.tag
        name = self.options.name
        if not path:
            raise errors.MissingCliArgument("path")

        if path.endswith(".git"):
            if not tag:
                raise errors.MissingCliArgument("tag")
            elif not name:
                raise errors.MissingCliArgument("name")
            descriptorDict = {"path": path,
                              "version": tag,
                              "name": name}
        elif path.endswith(".zip"):
            if not zipfile.is_zipfile(path):
                return
            outputDirectory = tempfile.mkdtemp()
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(outputDirectory)
            installed = False
            for folder in os.listdir(outputDirectory):
                absPath = os.path.join(outputDirectory, folder)
                if not os.path.isdir(absPath) or not package.isPackageDirectory(absPath):
                    continue
                if self._install(absPath, {"path": absPath}):
                    installed = True
            shutil.rmtree(outputDirectory)
            return installed
        else:
            descriptorDict = {"path": path}

        return self._install(path, descriptorDict)

    def _install(self, path, descriptorDict):
        logger.debug("Running Install command: {}".format(path))
        descriptor = self.config.descriptorFromPath(path, descriptorDict)
        try:
            descriptor.resolve()
        except ValueError:
            logger.error("Failed to resolve descriptor: {}".format(descriptorDict),
                         exc_info=True, extra=descriptorDict)
            return False
        if not descriptor.installed():
            # todo: add this behaviour to the lib.
            self.config._descriptorLib.currentDescriptorCache[descriptor.name] = descriptor
            return descriptor.install(inPlace=self.options.inPlace)
        return False
