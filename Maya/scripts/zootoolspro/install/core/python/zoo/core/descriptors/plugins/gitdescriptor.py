import os
import shutil
import stat
import tempfile

from zoo.core.util import git
from zoo.core import errors
from zoo.core.descriptors import descriptor
from zoo.core.util import zlogging
# most users wont have gitpython install so this import would fail
# This is important but would work under a dev env though.
# It's the responsibility of our code to ensure the
# necessary errors occurs
try:
    from zoo.core.util.git import gitwrapper
except ImportError as imper:
    gitwrapper = None

logger = zlogging.getLogger(__name__)


def _handleDeleteError(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


class GitDescriptor(descriptor.Descriptor):
    id = "git"
    requiredkeys = ("type", "version", "path")

    def __init__(self, config, descriptorDict):
        super(GitDescriptor, self).__init__(config, descriptorDict)
        self.path = descriptorDict["path"]
        self.version = descriptorDict["version"]
        self.link = descriptorDict.get("link", False)
        self.force = False

    def resolve(self, *args, **kwargs):
        # a support git path must end with '.git'
        if not self.path.endswith(".git"):
            raise SyntaxError("Supplied git path doesn't end with '.git'")
        # for git to successfully download and so we can early out of the download
        # we require the version and name along with the git path
        # this way we don't needlessly download the repo
        if all(i is not None for i in (self.version, self.name)):
            pkg = self.config.resolver.packageForDescriptor(self)
            # if the package already exists cache the package so the install
            # method will early out.
            if pkg is not None:
                self.package = pkg
        return True

    def install(self, **arguments):
        if self.package is not None or self.version is None:
            return

        if self.config.resolver.packageForDescriptor(self) is not None:
            return
        # grab a temp folder
        localFolder = tempfile.mkdtemp("zoo_git")
        gitFolder = os.path.join(localFolder, os.path.splitext(os.path.basename(self.path))[0])
        # ensure we have git install
        try:
            git.hasGit()
        except Exception:
            raise
        if gitwrapper is None:
            logger.error("Current environment doesn't have gitpython installed")
            raise errors.MissingGitPython()

        try:
            logger.debug("Cloning Path: {} to: {}".format(self.path, gitFolder))
            repo = gitwrapper.GitRepo.clone(self.path, localFolder)
            repo.checkout(self.version)
        except Exception:
            shutil.rmtree(localFolder, onerror=_handleDeleteError)
            raise
        package = self.config.resolver.packageFromPath(repo.repoPath)
        if package is None:
            shutil.rmtree(localFolder, onerror=_handleDeleteError)
            raise ValueError("Git Repo is not a zootools repo cancelling!")
        exists = self.config.resolver.existingPackage(package)
        if exists is not None:
            shutil.rmtree(localFolder, onerror=_handleDeleteError)
            self.package = exists
            raise ValueError("Package already exists: {}".format(str(exists)))

        self.name = package.name
        self.package = package
        destination = os.path.join(self.config.packagesPath, self.name, str(self.version))
        # ok we have finished download the git repo now copy it make sure its a package
        copyArgs = dict(package=package, destination=destination)
        if self.link:
            copyArgs["ignore"] = None
        installedPackage = package.copyTo(**copyArgs)
        # now clean up
        shutil.rmtree(localFolder, onerror=_handleDeleteError)
        # now make sure the environment is update to date
        self.config.resolver.cache[str(installedPackage)] = installedPackage
        if self.force:
            self._descriptorDict["type"] = "zootools"
            del self._descriptorDict["path"]
            self.config.resolver.updateEnvironmentDescriptorFromDict(self._descriptorDict)
        return True
