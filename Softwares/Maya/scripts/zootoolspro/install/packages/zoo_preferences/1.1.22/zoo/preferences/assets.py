import inspect
import os
import uuid

from zoovendor import six

from zoo.core import manager
from zoo.core.tooldata.tooldata import DirectoryPath
from zoo.libs.utils import filesystem
from zoo.core.util import pathutils
from zoo.preferences import core as prefcore

from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class AssetPreference(object):
    _defaultItems = None

    def __init__(self, assetFolder, preferenceInterface, buildAssets=True):
        """ The Asset preference class.

        :param assetFolder: The asset folder name  eg. "maya_shaders",
        :type preferenceInterface:
        :param preferenceInterface:
        """
        self._assetFolder = assetFolder
        self.preferenceInterface = preferenceInterface
        self.preference = self.preferenceInterface.preference

    def buildAssetDirectories(self):
        """ Creates the asset directory if it is missing.

        This should be overridden

        :return:
        """
        pass

    def hasOldAssets(self):
        """ To be overridden

        :return:
        """
        return False

    def zooPrefsPath(self):
        """ The assets folder specific to this user and for this preference.

        .. code-block::
            eg.
            /zoo_preferences/assets/shaders
            /zoo_preferences/assets/maya_scenes

        :return: Path to folder asset folder eg. /<..>/zoo_preferences/assets/shaders
        """

        return pathutils.normpath(os.path.join(self.userAssetRoot(), self._assetFolder))

    def zooPrefsDefaultsPath(self):
        """ Path to default asset in zoo_preference

        :return:
        :rtype:
        """
        return os.path.join(self.zooPrefsPath(), "defaults")

    def userAssetRoot(self):
        """ Full Path to the user assets folder  eg. <..>/zoo_preferences/assets

        eg. <..>/zoo_preferences/assets

        :return:
        """
        userPrefsPath = str(self.preference.root("user_preferences"))
        assetsPath = os.path.join(userPrefsPath, "assets")
        if not os.path.isdir(assetsPath):
            os.makedirs(assetsPath)

        return assetsPath

    def copyDefaultAssets(self, path):
        """ Copies default assets into target path, only if it exists

        :param path:
        :return:
        """
        defaultAssetsPath = self.defaultAssetsPath()
        if not os.path.exists(defaultAssetsPath):
            logger.debug(
                "Warning: Copy Default Assets: '{}' doesn't exist for ''".format(defaultAssetsPath, self._assetFolder))
            return

        filesystem.copyDirectoryContents(defaultAssetsPath, path)
        logger.debug("Default assets copied: '{}' --> '{}'".format(defaultAssetsPath, path))
        return path

    def defaultAssetsPath(self):
        """ The default assets saved in this repository (zoo package)
        Should be generally located at

        {self}/preferences/assets/<assetFolder>
        eg {self}/preferences/assets/shaders

        """
        packagePath = self.currentPackagePath()
        return os.path.join(packagePath, "preferences", "assets", self._assetFolder)

    def currentPackagePath(self):
        """ Returns the current package root path

        For instance:
            "D:\\Code\\zootoolspro\\zoo_preferences"
            "D:\\Code\\zootoolspro\\zoo_pyside"

        :return: Returns the path of the current package
        :rtype: str
        """
        classFile = inspect.getfile(self.preferenceInterface.__class__)

        for directory in filesystem.iterParentPath(classFile):
            zooPackage = os.path.join(directory, "zoo_package.json")
            if os.path.exists(zooPackage):
                pkg = manager.currentConfig().resolver.packageFromPath(zooPackage)
                return pkg.root

        return None

    def defaultAssetItems(self, refresh=False):
        """ Get the default items from the default directory

        :param refresh:
        :return:
        """
        if not refresh and self._defaultItems is not None:
            return self._defaultItems

        defaultPath = self.defaultAssetsPath()
        if os.path.exists(defaultPath):
            pathutils.filesInDirectory(defaultPath, ext=False)
            self._defaultItems = pathutils.filesInDirectory(defaultPath, ext=False)
            return self._defaultItems


class BrowserPreference(AssetPreference):
    # The name of the keys within the json document
    __browserFolders = "browserFolders"
    __activeFolders = "activeFolders"
    __activeCategories = "activeCategories"
    __categories = "browserCategories"
    _browserUniformIcons = "browserUniformIcons"

    def __init__(self, assetFolder, preferenceInterface, buildAssets=True, fileTypes=None, autoFillFolders=True,
                 selectedIndices=None, copyDefaults=True):
        """ Preference interface for UIs that utilize minibrowsers

        :param assetFolder:
        :param preferenceInterface:
        :param buildAssets:
        :param fileTypes:
        :param autoFillFolders: Automatically find folders in the asset folder and fill the preferences
        :param selectedIndices:
        :param copyDefaults:
        """
        super(BrowserPreference, self).__init__(assetFolder, preferenceInterface, buildAssets)
        self._selectedIndices = selectedIndices
        self.fileTypes = fileTypes or []
        self.autoFillFolders = autoFillFolders
        self._copyDefaults = copyDefaults and prefcore.currentInstance().shouldCopyDefaultAssets
        if buildAssets:
            self.buildAssetDirectories()

    def buildAssetDirectories(self):
        """ Build the asset directories.

        There is a lot of specific code here to check the folders within the asset folder.
        For instance if the folder is empty, create it. If there are folders in there,
        don't use the base folder and so on.



        :return:
        """

        folderPaths = self.browserFolderPaths()
        assetsPath = self.userAssetRoot()
        filesystem.ensureFolderExists(assetsPath)
        # Check if need to use old preferences
        self._updateOldSettings()

        zooPrefs = self.zooPrefsPath()
        logger.debug("Building asset directories for: {}".format(zooPrefs))

        # If using old settings just add that to the preferences and call it a day
        if os.path.exists(zooPrefs) and \
                (self.hasOldAssets() or not self.autoFillFolders or self.assetFolderEmpty()) \
                and len(folderPaths) == 0:
            filesystem.ensureFolderExists(zooPrefs)
            self._initDefaultDirectory()
            return

        if not os.path.exists(zooPrefs):
            filesystem.ensureFolderExists(zooPrefs)
            self._initDefaultDirectory()

        # Automatically add all the folders in the asset folder,
        # Note: setActiveDirectories will handle the saving
        self.refreshAssetFolders(setActive=False, save=True)

        # Remove base folder
        if not self.hasOldAssets() and len(self.browserFolderPaths()) > 1:
            logger.debug("Removing base folder: {}".format(self.zooPrefsPath()))
            self.removeBrowserFolder(self.zooPrefsPath())

        # Select Only certain indices if required, and if it is new
        if self._selectedIndices:
            browserPaths = self.activeBrowserPaths()
            browserPaths = browserPaths if len(browserPaths) > 0 else self.browserFolderPaths()

            paths = [browserPaths[i] for i in self._selectedIndices]
            self.setActiveDirectories(paths)
        else:
            # Otherwise just select the new found folders
            newPaths = [d for d in self.browserFolderPaths() if d not in folderPaths]
            self.setActiveDirectories(self.activeBrowserPaths() + newPaths)

    def refreshAssetFolders(self, setActive=True, save=True):
        """ Retrieves folders in Assets folder in preferences.

        Detects all the folders in the asset folder and set/save the settings.

        :param setActive: Sets the new folders as active
        :type setActive: bool
        :param save: If True will save the preferences.
        :type save: bool
        :return:
        """
        logger.debug("Refresh asset folders (setActive={})".format(setActive))
        folderPaths = self.browserFolderPaths()

        dirs = [folder.path for folder in folderPaths]  # Use the current folders
        if self._copyDefaults:
            path = self.copyDefaultAssets(self.zooPrefsDefaultsPath())
            if path:
                dirs.append(path)

        # If autofill folders is true, add the folders in the subdirectory
        zooPrefs = self.zooPrefsPath()
        if self.autoFillFolders:
            newFolders = [os.path.join(zooPrefs, f) for f in os.listdir(zooPrefs) if
                          os.path.isdir(
                              os.path.join(zooPrefs, f)) and "_fileDependencies" not in f and not f.startswith(".")]
            dirs += newFolders
            logger.debug("autoFillFolders: Adding new folders: {}".format(newFolders))
            dirs = sorted(list(set(dirs)))  # List sorted and dups removed

        # Add directory paths to the browsers
        newDirs = [DirectoryPath(path=d) for d in dirs if self.directoryPath(d) is None]

        self.addBrowserDirectories(newDirs, save=save)

        zooPrefs = self.zooPrefsPath()
        # Create the "./default" directory, if base exists and no subfolders
        if os.path.exists(zooPrefs) and not len(dirs) > 0:
            self._initDefaultDirectory()

        # Only select the ones that are new
        if setActive:
            newPaths = [d for d in newDirs if d not in folderPaths]
            self.setActiveDirectories(self.activeBrowserPaths() + newPaths)

    def assetFolderEmpty(self):
        """ Checks if the init folder is empty

        :return:
        """
        zooPrefs = self.zooPrefsPath()
        return not len(os.listdir(zooPrefs)) > 0

    def _initDefaultDirectory(self, setActive=True):
        """ Init default directory

        :return:
        """
        logger.debug("Initialize Default Directory: {}".format(self.zooPrefsPath()))
        d = DirectoryPath(path=self.zooPrefsPath())
        self._browserFolder[:] = [d.serialize()]
        if setActive:
            self.setActiveDirectory(d)

    def hasOldAssets(self):
        """ Check to see if there are any old assets

        :return:
        """
        zooPrefs = self.zooPrefsPath()

        onlyfiles = [f for f in os.listdir(zooPrefs) if os.path.isfile(os.path.join(zooPrefs, f))]

        exts = [os.path.splitext(f)[1][1:] for f in onlyfiles]
        for e in exts:
            if e in self.fileTypes:
                return True

        return False

    def settings(self):
        """ Return the settings

        :return:
        """
        return self.preferenceInterface.settings()["settings"]

    def _updateOldSettings(self):
        """ Update the older settings

        :return:
        """
        settings = self.settings()
        # Clear out old data
        if isinstance(settings.get(self._browserUniformIcons), bool):
            settings[self._browserUniformIcons] = []
            logger.debug("Removing old settings: '{}'".format(self._browserUniformIcons))

        if isinstance(self._browserFolderRoot, list):
            settings[self.__browserFolders] = {}
            logger.debug("Removing old settings: '{}'".format(self.__browserFolders))

        if isinstance(settings.get(self.__activeFolders), list):
            settings[self.__activeFolders] = {}
            logger.debug("Removing old settings: '{}'".format(self.__activeFolders))
        if self.__categories not in settings:
            settings[self.__categories] = {}

    def setBrowserUniformIcons(self, uniform, save=True):
        """ Set the browser uniform icons setting

        :param uniform:
        :param save:
        :return:
        """

        self._initUniformIcons()
        self.settings()[self._browserUniformIcons][self._assetFolder] = uniform
        if save:
            self.saveSettings()

    def _initUniformIcons(self):
        """ Init uniform icons if not initiated

        :return:
        """
        logger.debug("Initialize uniform icons for '{}'".format(self._assetFolder))
        browserUniformIcons = self.settings().get(self._browserUniformIcons)

        if not browserUniformIcons:
            self.settings()[self._browserUniformIcons] = {}

        uniformIcons = self.settings()[self._browserUniformIcons].get(self._assetFolder, None)
        if not uniformIcons:
            self.settings()[self._browserUniformIcons][self._assetFolder] = True

        self.saveSettings()

    def browserUniformIcons(self):
        """ Browser uniform icons

        :return:
        """
        self._initUniformIcons()
        return self.settings()[self._browserUniformIcons][self._assetFolder]

    def browserFolderPaths(self):
        """ Retrieve the DirectoryPath objects of all the folders which holds the folder path, alias and id

        :return:
        :rtype: list[:class:`DirectoryPath`]
        """

        return [DirectoryPath(pref=f) for f in self._browserFolder]

    def activeBrowserPaths(self):
        """ Retrieve all the active browser paths as DirectoryPath

        :return:
        :rtype:  list[:class:`DirectoryPath`]
        """
        activeFolders = self.settings()[self.__activeFolders][self._assetFolder]
        return [f for f in self.browserFolderPaths() if f.id in activeFolders]

    def categories(self):
        return self.settings().get(self.__categories, {}).get(self._assetFolder, [])

    def updateCategory(self, categoryId, data, save=True):
        updated = False
        for cat in self.settings()[self.__categories].setdefault(self._assetFolder, []):
            if cat["id"] == categoryId:
                cat.update(data)
                updated = True
        if save and updated:
            self.saveSettings()

    def createCategory(self, name, categoryId, parent, children):
        return {
            "id": categoryId or str(uuid.uuid4())[:6],
            "alias": name,
            "parent": parent,
            "children": children
        }

    def addCategory(self, category, save=True):
        self.settings()[self.__categories].setdefault(self._assetFolder, []).append(category)
        if save:
            self.saveSettings()

    def addCategories(self, categories, save=True):
        existing = {i["id"]: i for i in self.categories()}
        for cat in categories:
            existingCat = existing.get(cat["id"])
            if existingCat is not None:
                existingCat["alias"] = cat["alias"]
                existingCat["parent"] = cat["parent"]
                existingCat["children"] = cat["children"]
                continue
            existing[cat["id"]] = cat
            self.addCategory(cat, save=False)
        if save:
            self.saveSettings()

    def setActiveCategories(self, categoryIds, save=True):
        settings = self.settings()
        settings.setdefault(self.__activeCategories, {})[self._assetFolder] = categoryIds
        if save:
            self.saveSettings()

    def activeCategories(self):
        return self.settings().get(self.__activeCategories, {}).get(self._assetFolder, [])

    def removeCategory(self, categoryId, save=True):
        categories = self.settings()[self.__categories].get(self._assetFolder, [])
        for index, cat in enumerate(self.settings()[self.__categories].get(self._assetFolder, [])):
            if cat["id"] == categoryId:
                del categories[index]
                return True
        if save:
            self.saveSettings()
        return False

    def clearCategories(self, save=True):
        self.settings()[self.__categories][self._assetFolder] = []
        if save:
            self.saveSettings()

    @property
    def _browserFolder(self):
        """ The browser folder settings

        :return:
        :rtype: list[dict]
        """

        browserFolder = self._browserFolderRoot.get(self._assetFolder)
        if browserFolder is None:
            self._browserFolderRoot[self._assetFolder] = []

        return self._browserFolderRoot[self._assetFolder]

    def removeBrowserFolder(self, path):
        """ Remove browser folder

        :param path:
        :return:
        """
        for p in self._browserFolder:
            if os.path.normpath(path) == os.path.normpath(p["path"]):
                self._browserFolder.remove(p)
                return

    def setActiveDirectories(self, directories, save=True):
        """ Set active directories

        :param directories:
        :type directories: list[DirectoryPath]
        :return:
        """
        self.settings()[self.__activeFolders][self._assetFolder] = [d.id for d in directories]
        if save:
            self.saveSettings()

    def setActiveDirectory(self, directory, clear=True):
        """ Sets the active directory

        :param directory:
        :param clear:
        :return:
        """
        logger.debug("Set Active Directory: '{}'".format(directory))

        activeFolderSettings = self._activeFolders
        if clear:
            activeFolderSettings[:] = []
        activeFolderSettings.append(directory.id)
        self.saveSettings()

    def addBrowserDirectory(self, directory, save=True):
        """ Add browser directory

        :param directory:
        :param save:
        :type directory: :class:`DirectoryPath`
        :return:
        """
        if isinstance(directory, DirectoryPath):
            for d in self.browserFolderPaths():
                if d == directory:  # Duplicate found, ignoring
                    logger.debug(
                        "Duplicate folders found while adding browser directory, ignoring. '{}'".format(d.alias))
                    return False
            assetFolder = self._browserFolderRoot[self._assetFolder]
            assetFolder.append(directory.serialize())

            logger.debug("Adding Browser Directory: '{}': {}".format(self._assetFolder, directory))
            if save:
                self.saveSettings()
            return True
        else:
            raise TypeError("{} must be of type DirectoryPath".format(directory))

    def addBrowserDirectories(self, directories, save=True):
        """ Add list of browser directories

        :param directories:  :class:`DirectoryPath`
        :param save:
        :return:
        """
        logger.debug("Add Browser Directories: {}:  {}".format(self._assetFolder, directories))
        for d in directories:
            self.addBrowserDirectory(d, save=False)
        if save:
            self.saveSettings()

    def addActiveDirectory(self, directory, save=True):
        """ Add active directory

        :param directory:
        :param save:
        :return:
        """
        activeId = None
        if isinstance(directory, DirectoryPath):
            activeId = directory.id

        elif isinstance(directory, six.string_types):
            activeId = self.directoryPath(directory).id

        if activeId:
            self.settings()[self.__activeFolders][self._assetFolder].append(activeId)
            if save:
                self.saveSettings()

    @property
    def _activeFolderRoot(self):
        """ Get the active folder from the settings

        :return:
        """
        activeFolders = self.settings().get(self.__activeFolders)
        if activeFolders is None:
            self.settings()[self.__activeFolders] = {}

        return self.settings().get(self.__activeFolders)

    @property
    def _activeFolders(self):
        """ Get active folders from the settings

        :return:
        """
        if not self._activeFolderRoot.get(self._assetFolder):
            self._activeFolderRoot[self._assetFolder] = []
        return self._activeFolderRoot.get(self._assetFolder)

    def directoryPathById(self, directoryId):
        for dp in self._browserFolder:
            if dp["id"] == directoryId:
                return dp

    def directoryPath(self, path):
        """ Returns directory path by given path

        :param path:
        :type path: str
        :return:
        :rtype: DirectoryPath
        """

        for dp in self._browserFolder:
            if pathutils.normpath(dp["path"]) == pathutils.normpath(path):
                return DirectoryPath(pref=dp)

    def removeBrowserDirectory(self, directory, save=True):
        """ Remove browser directory

        :param directory:
        :param save:
        :return:
        """
        dp = self.directoryPath(directory)

        self.removeBrowserFolderById(dp.id)
        logger.debug("Removing browser folder. (directory='{}', save='{}') ".format(directory, save))

        if save:
            self.saveSettings()

    def saveSettings(self, indent=True, sort=False):
        """ Save setting for the browser preferences

        :param indent:
        :param sort:
        :return:
        """
        self._cleanUpActives()  # todo handle this
        logger.debug("Saving settings for BrowserPreference: '{}'. (indent='{}', sort='{}') ".format(self._assetFolder,
                                                                                                     indent, sort))

        return self.preferenceInterface.saveSettings(indent, sort)

    def _cleanUpActives(self):
        """ Remove old active ID's that don't exist anymore

        :return:
        """
        remove = []
        ids = [f["id"] for f in self._browserFolder]
        for d in self._activeFolders:
            if d not in ids:
                remove.append(d)

        logger.debug("Removing old active IDs: {}".format(str(remove)))

        for r in remove:
            self._activeFolders.remove(r)

    def removeBrowserFolderById(self, id):
        """ Remove browser folder by Id

        :param id:
        :return:
        """
        folderSettings = self._browserFolder
        for i, bf in enumerate(folderSettings):
            if bf["id"] == id:
                try:
                    self._activeFolders.remove(id)
                except ValueError:
                    pass
                return folderSettings.pop(i)

    def setBrowserDirectories(self, directories, saveSettings=False):
        """ Set browser directories

        :param directories: List of directories as strings or `DirectoryPaths`
        :type directories: list[:class:`str` or :class:`DirectoryPath`]
        :return:
        """
        # Convert string list to DirectoryPath List
        if directories and len(directories) > 0:
            firstDir = directories[0]
            if isinstance(firstDir, six.string_types):
                directories = [DirectoryPath(path=d) for d in directories]

        # Using slice here so we don't break any references to self._browserFolder
        self._browserFolder[:] = [d.serialize() for d in directories]
        if saveSettings:
            self.saveSettings()
        self._cleanUpActives()

    @property
    def _browserFolderRoot(self):
        """ Browser Folder root

        :return:
        :rtype: dict
        """
        if not self.settings().get(self.__browserFolders):
            self.settings()[self.__browserFolders] = {}

        return self.settings()[self.__browserFolders]

    def _saveSettings(self):
        """ Save Preference settings

        :return:
        """
        self.preferenceInterface.saveSettings()

    def setDirectoryAlias(self, dirPath, save=True):
        """ DirectoryPath object with the modified alias

        :param dirPath:
        :type dirPath: DirectoryPath
        :return:
        """
        for f in self._browserFolder:
            if f["id"] == dirPath.id:
                f.update(dirPath.serialize())
                break

        if save:
            self.saveSettings()

    def clearBrowserDirectories(self, save=True):
        """ Clear the browser directories

        :param save:
        :return:
        """
        self._browserFolder[:] = []  # clear browser folder settings
        if save:
            self.saveSettings()
