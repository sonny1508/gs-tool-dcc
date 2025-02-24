import shutil
import os
import glob
import traceback

from maya import cmds
from maya.api import OpenMaya as om2
from zoo.core import api
from zoo.core.manager import currentConfig

from zoo.libs.maya.utils import general
from zoo.core.util import zlogging
from zoo.preferences.interfaces import coreinterfaces

logger = zlogging.getLogger(__name__)


class UninstallerCore(object):

    def __init__(self):
        super(UninstallerCore, self).__init__()
        self.coreInterface = coreinterfaces.coreInterface()

    def uninstall(self, zootools, assets, prefs, cache):
        """ Uninstall

        :param zootools:
        :param assets:
        :param prefs:
        :param customPackages:
        :return:
        """
        self._initVars()
        if cache:
            self.deletePythonCache()
        if zootools:
            self.deleteModFiles()
            cmds.unloadPlugin("zootools.py")
            self.deleteZooTools()
            self.deleteShelf()

        # Delete Mod (modFiles)
        if prefs:
            self.deletePrefs()  # this crashes maya for some reason

        if assets:
            self.deleteAssets()

        self.finishUp()
        return True

    def _initVars(self):
        """ Get all the required variables before disabling zoo tools

        :return:
        """
        self._zoo = currentConfig()
        self._prefsPath = self.coreInterface.prefsPath()
        self._zooPrefsRoot = self.coreInterface.defaultPreferencePath()
        self._resolver = api.currentConfig().resolver
        self._assetPath = self.coreInterface.assetPath()
        self._shelvesDir = general.userShelfDir()

    def deletePythonCache(self):
        """Deletes the zootools cache folder
        """
        cacheFolder = api.currentConfig().cacheFolderPath()
        if not os.path.exists(cacheFolder):
            return
        logger.info("Deleting cache folder: {}".format(cacheFolder))
        try:
            shutil.rmtree(cacheFolder)
        except (PermissionError, OSError):
            om2.MGlobal.displayWarning("Unable to delete cache folder due to permissions, "
                                       "please manually delete folder: {}".format(cacheFolder))

    def deletePrefs(self):

        logger.info("Delete preferences: '{}'".format(self._prefsPath))
        self.deleteFolder(self._prefsPath)

    def checkPreferenceFolder(self):
        # Delete prefs if there are no files left
        if len(os.listdir(self._zooPrefsRoot)) == 0:
            os.rmdir(self._zooPrefsRoot)

    def finishUp(self):
        """ Finish up the uninstall script

        :return:
        """
        self.checkPreferenceFolder()
        cmds.pluginInfo("zootools.py", remove=1, e=1)

    def deleteAssets(self):
        """ Delete the assets

        :return:
        """

        logger.info("Deleting assets: '{}'".format(self._assetPath))
        self.deleteFolder(self._assetPath)

    @classmethod
    def deleteFolder(cls, path):
        """ Delete folder if it exists

        :param path:
        :return:
        """

        if os.path.exists(path):
            try:
                shutil.rmtree(path, ignore_errors=False)
            except:

                import maya.api.OpenMaya as om2
                traceback.print_exc()
                om2.MGlobal.displayWarning("Unable to delete '{}'".format(path))

    def deleteZooTools(self):
        """ Delete zoo tools pro

        :return:
        """
        # Delete scripts (zooPath)
        zooPath = self._zoo.rootPath
        logger.info("Deleting ZooToolsPro: '{}'".format(zooPath))
        self.deleteFolder(zooPath)

    def deleteShelf(self):
        """ Deletes the zoo tools pro shelf

        :return:
        """
        shelfPath = os.path.join(self._shelvesDir, "shelf_ZooToolsPro.mel")
        if os.path.exists(shelfPath):
            os.remove(shelfPath)
            logger.info("Deleting ZooToolsPro shelf")

    def modDirs(self):
        return os.getenv("MAYA_MODULE_PATH").split(os.pathsep)

    def deleteModFiles(self):
        """ Delete the mod files

        :return:
        """
        modFiles = []
        modDirs = self.modDirs()
        for m in modDirs:
            mod = glob.glob(os.path.join(m, "zootoolspro.mod"))
            if mod:
                modFiles += mod

        # Delete all the mod files
        for m in modFiles:
            logger.info("Deleting Mod: '{}'".format(m))
            os.remove(m)
