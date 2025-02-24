from datetime import datetime
import os
import shutil

import zipfile

from zoo.core.commands import action
from zoo.core.util import filesystem
from zoo.core import manager, errors, constants
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class Setup(action.Action):
    """
    This 'setup' Command installs zootools core package into the specified
    Directory, this command sets up the following folder structure:

    Resulting folder structure::

        |-Specified Root
            |-config
                |-env
            |-install
                |-core
                |-packages

    """
    id = "setup"

    def arguments(self, argParser):
        argParser.add_argument("--destination",
                               required=True,
                               type=str,
                               help="The destination for zootools to be installed too")
        argParser.add_argument("--zip",
                               required=False,
                               help="Alternative zootools installation to use",
                               type=str)
        argParser.add_argument("--app",
                               required=False,
                               help="Application name to install for ie. maya",
                               type=str)
        argParser.add_argument("--app_dir",
                               required=False,
                               help="Application directory ie. for maya it would be the modules location",
                               type=str)
        argParser.add_argument("--includeGit",
                               required=False,
                               help="If True then if a git folder exists under the core folder it will also be copied",
                               type=bool)
        argParser.add_argument("--force",
                               action="store_true",
                               help="If True and the destination path exists it will be removed before installing")
        argParser.add_argument("--buildVersion",
                               type=str,
                               required=False,
                               help="The build version to apply",
                               default="")

    def run(self):
        logger.debug("Validating root Path: {}".format(self.options.destination))
        destination = self.options.destination

        if os.path.exists(destination):

            if not self.options.force:
                raise ValueError("ZooProject Already exists at: {}".format(destination))

            logger.debug("Force option specified, starting back up")
            backupFolder = os.path.join(os.path.dirname(destination),
                                        "zootools_backup",
                                        datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
            # ensure the parent folder is created before we do the backup
            filesystem.ensureFolderExists(os.path.dirname(backupFolder))
            logger.debug("Copying old root folder, {} -> {}".format(destination, backupFolder))
            shutil.copytree(destination, backupFolder)
            logger.debug("Finished backup of old root")
            # trash the destination since we have already backed up
            try:
                shutil.rmtree(str(self.options.destination))
            except OSError:
                logger.error("Failed to remove destination path "
                             "possible due to it currently being open: {}".format(self.options.destination),
                             exc_info=True,
                             extra={"arguments": str(self.options)})
                raise

        logger.debug("Validating zip: {}".format(self.options.zip))
        if self.options.zip:
            if not os.path.exists(self.options.zip):
                raise errors.FileNotFoundError("Zip File specified doesn't exist: {}".format(self.options.zip))
            self._buildFromZip()
        else:
            try:
                self._buildZooFolderStructure()
            except OSError:
                logger.error("Failed to setup folder structure", exc_info=True)
                self._cleanup()
        self._installApplicationExtension()

    def _cleanup(self):
        if os.path.exists(self.options.destination):
            shutil.rmtree(self.options.destination)

    def _buildZooFolderStructure(self):
        installFolder = os.path.join(self.options.destination, "install")
        filesystem.ensureFolderExists(self.options.destination)
        filesystem.ensureFolderExists(os.path.join(self.options.destination, "config"))
        # copy our main repo over(current one)
        logger.debug("Recursively Copying config: {} -> {}".format(self.config.corePath,
                                                                   installFolder))
        args = {"src": self.config.corePath, "dst": os.path.join(installFolder, "core")}
        if not self.options.includeGit:
            args["ignore"] = shutil.ignore_patterns(".gitignore", "*.git", "__pycache__", ".vscode", ".idea")
        shutil.copytree(
            **args
        )
        pkgFolder = os.path.join(installFolder, "packages")
        logger.debug("Creating packages Folder: {}".format(pkgFolder))
        # construct the packages folder
        filesystem.ensureFolderExists(pkgFolder)
        installedCfg = manager.zooFromPath(self.options.destination)
        # now create the environment file if it doesn't already exist
        installedCfg.resolver.createEnvironmentFile()
        self._updatePreferences(installedCfg)
        buildVersion = self.options.buildVersion
        if not buildVersion:
            return installedCfg

        buildPackage = installedCfg.buildPackagePath()
        if not os.path.exists(buildPackage):
            packageData = {
                "version": buildVersion,
                "name": "zootoolsPro",
                "displayName": "Zoo Tools Pro"
            }
        else:
            packageData = filesystem.loadJson(buildPackage)
            packageData["version"] = buildVersion
        filesystem.saveJson(packageData, buildPackage, indent=4, sort_keys=True)

        return installedCfg

    def _updatePreferences(self, config):
        prefRoot = os.path.join(config.configPath, "env", "preference_roots.config")
        filesystem.saveJson({"user_preferences": constants.DEFAULT_PREFS_PATH}, prefRoot, indent=4, sort_keys=True)

    def _buildFromZip(self):
        installFolder = os.path.join(self.options.destination, "install")
        with zipfile.ZipFile(self.options.zip, "r") as zipRef:
            zipRef.extractall(self.options.destination)
        filesystem.ensureFolderExists(os.path.join(installFolder, "packages"))
        filesystem.ensureFolderExists(os.path.join(self.options.destination, "config"))
        installedCfg = manager.zooFromPath(self.options.destination)
        installedCfg.resolver.createEnvironmentFile()
        self._updatePreferences(installedCfg)

    def _installApplicationExtension(self):
        destinationPath = self.options.app_dir
        applicationType = self.options.app
        if applicationType == "maya":
            extensionsFolder = os.path.join(self.options.destination, "install", "core", "extensions", "maya")
            modLines = ["+ zootoolspro 2.0 {}\n".format(extensionsFolder),
                        "ZOOTOOLS_PRO_ROOT := ../../\n",
                        "scripts: ./Scripts\n"]
            logger.debug("Attempting to create modules Folder: {}".format(destinationPath))
            filesystem.ensureFolderExists(destinationPath)
            moduleFile = os.path.join(destinationPath, "zootoolspro.mod")
            logger.debug("Writing maya module file: {}".format(moduleFile))
            with open(moduleFile, "w") as f:
                f.writelines(modLines)
