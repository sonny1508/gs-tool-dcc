import os
import shutil

from zoo.libs.utils import filesystem
from zoo.preferences import prefinterface
from zoo.libs.utils import general

componentPathKey = "componentPaths"
buildScriptPathsKey = "buildScriptPaths"
templatePathsKey = "templatePaths"
templateSavePathKey = "templateSavePath"
exportPluginsKey = "exporterPluginPaths"
exportPluginOverridesKey = "exporterPluginOverrides"
requiredMayaPlugins = "required_maya_plugins"
namingPresetHierarchy = "namingPresetHierarchy"
namingPresetSavePath = "namingPresetSavePath"
namingPresetPaths = "namingPresetPaths"

LEGACY_TEMPLATE_FOLDER_NAMES = ["zoodefault"]


class HiveInterface(prefinterface.PreferenceInterface):
    """Preference interface class for hive"""

    id = "Hive"
    _relativePath = "prefs/maya/hive.pref"

    def upgradePreferences(self):
        """Upgrades the local preferences from the default preferences."""
        settings = self.settings()
        defaultSettings = self.preference.defaultPreferenceSettings(
            "zoo_hive", "maya/hive.pref"
        )
        plugins = settings.get("settings", {}).get(requiredMayaPlugins, [])
        defaultPlugins = defaultSettings["settings"].get(requiredMayaPlugins, [])
        settings.get("settings", {})[requiredMayaPlugins] = list(
            set(plugins).union(defaultPlugins)
        )
        general.merge(settings, defaultSettings, onlyMissingKeys=True)
        self.saveSettings()

    def upgradeAssets(self):
        shouldIncludeDefaults = self.settings(name="includeDefaultAssets") and self.preference.shouldCopyDefaultAssets

        templatesPath = self.defaultUserTemplatePath()
        buildScriptPath = self.defaultBuildScriptPath()
        exporterPath = self.defaultExportPluginPath()
        filesystem.ensureFolderExists(templatesPath)
        filesystem.ensureFolderExists(buildScriptPath)
        filesystem.ensureFolderExists(exporterPath)
        # generate the __init__.py if missing
        buildScriptInitPath = os.path.join(buildScriptPath, "__init__.py")
        exporterInitPath = os.path.join(exporterPath, "__init__.py")
        if not os.path.exists(buildScriptInitPath):
            with open(buildScriptInitPath, "w") as f:
                pass
        if not os.path.exists(exporterInitPath):
            with open(exporterInitPath, "w") as f:
                pass
        if not shouldIncludeDefaults:
            return
        # get the default hive assets containing templates and build scripts from the hive package
        assetPkg = self.repostoryAssetPath()

        # before we copy the default templates, remove anything old that we ship by default
        for defaultFolderName in (
            LEGACY_TEMPLATE_FOLDER_NAMES
        ):
            localFolder = os.path.join(templatesPath, defaultFolderName)
            if os.path.exists(localFolder):
                shutil.rmtree(localFolder)
        templateCustomPath = os.path.join(templatesPath, "custom")
        filesystem.ensureFolderExists(templateCustomPath)
        assetLocalFolder = os.path.join(self.preference.assetPath(), "hive")
        filesystem.copyDirectoryContents(
            assetPkg, assetLocalFolder, skipExist=True, overwriteModified=True
        )

    def defaultUserTemplatePath(self):
        """Returns the default hive template path for saving.

        We use the zootools assets/hive/templates path.

        :return: The absolute hive template path
        :rtype: str
        """
        return os.path.join(self.preference.assetPath(), "hive", "templates")

    def repostoryAssetPath(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

    def defaultExportPluginPath(self):
        """Returns the default hive export plugin path.

        We use the zootools assets/hive/exporters.

        :return: The absolute hive Exporters folder path.
        :rtype: str
        """
        return os.path.join(self.preference.assetPath(), "hive", "exporters")

    def defaultBuildScriptPath(self):
        return os.path.join(self.preference.assetPath(), "hive", "buildscripts")

    def defaultNamingConfigPath(self):
        return os.path.join(self.preference.assetPath(), "hive", "namingpresets")

    def userComponentPaths(self, root=None):
        """Returns the user component folder paths for the user.

        This doesn't include the environment variables value.

        :param root: The root name to search, if None then all roots will be searched until the relativePath is found.
        :type root: str
        :return: A list of folder paths.
        :rtype: list[str]
        """
        pref = self.settings(root=root)
        return pref["settings"].get(componentPathKey, [])

    def userBuildScriptPaths(self, root=None):
        """Returns the user build script folder paths for the user.

        This doesn't include the environment variables value.

        :param root: The root name to search, if None then all roots will be searched until the relativePath is found.
        :type root: str
        :return: A list of folder paths.
        :rtype: list[str]
        """
        buildScriptPaths = self.settings(root=root)["settings"].get(
            buildScriptPathsKey, []
        )
        defaultScripts = [self.defaultBuildScriptPath()]
        return list(set(buildScriptPaths).union(defaultScripts))

    def userBuildScripts(self, root=None):
        """Returns a list of build script ids which should always be used in rigs.

        :param root: The root name to search, if None then all roots will be searched until the relativePath is found.
        :type root: str
        :return: The build script plugin ids.
        :rtype: list[str]
        """
        pref = self.settings(root=root)
        return pref["settings"].get("buildScripts", [])

    def userTemplatePaths(self, root=None):
        """Returns the user template folder paths for the user.

        This doesn't include the environment variables value.

        :param root: The root name to search, if None then all roots will be searched until the relativePath is found.
        :type root: str
        :return: A list of folder paths.
        :rtype: list[str]
        """
        pref = self.settings(root=root)
        settings = pref["settings"].get(templatePathsKey)
        if not settings:
            settings = [self.defaultUserTemplatePath()]
        return settings

    def userTemplateSavePath(self, root=None):
        """Returns the component module paths for the user.

        This doesn't include the environment variables value.

        :param root: The root name to search, if None then all roots will be searched until the relativePath is found.
        :type root: str
        :return: The root folder path for saving templates
        :rtype: str
        """
        pref = self.settings(root=root)
        userSpec = pref["settings"].get(templateSavePathKey, "")
        resolved = os.path.expandvars(os.path.expanduser(userSpec))
        if not os.path.exists(resolved):
            userSpec = os.getenv("HIVE_TEMPLATE_SAVE_PATH", "")
            resolved = os.path.expandvars(os.path.expanduser(userSpec))
            if not os.path.exists(resolved):
                userSpec = self.defaultUserTemplatePath()
        return userSpec

    def exporterPluginPaths(self, root=None):
        """Returns the list of exporter plugin path hive is current using in the preferences.

        :param root: The root name to search, if None then all roots will be searched until the relativePath is found.
        :type root: str
        :rtype: list[str]
        """
        pref = self.settings(root=root)

        settings = pref["settings"].get(templatePathsKey)
        if not settings:
            settings = [self.defaultExportPluginPath()]
        return settings

    def exporterPluginOverrides(self, root=None):
        """Returns the exporter plugin id overrides done by the user.

        :param root: The root name to search, if None then all roots will be searched until the relativePath is found.
        :type root: str or None
        :return: The Mapping key is the exporter plugin id and the value is the remapped plugin id to use.
        :rtype: dict[str,str]
        """
        pref = self.settings(root=root)
        return pref["settings"].get(exportPluginOverridesKey, {})

    def namingPresetPaths(self, root=None):
        pref = self.settings(root=root)
        paths = pref["settings"].get(namingPresetPaths, [])
        return [self.defaultNamingConfigPath()] + paths

    def namingPresetHierarchy(self, root=None):
        pref = self.settings(root=root)
        return pref["settings"].get(namingPresetHierarchy, {})

    def namingPresetSavePath(self, root=None):
        pref = self.settings(root=root)
        return (
            pref["settings"].get(namingPresetSavePath) or self.defaultNamingConfigPath()
        )

    def setNamingPresetHierarchy(self, hierarchy, save=True):
        pref = self.settings(root=None)
        pref["settings"][namingPresetHierarchy] = hierarchy
        if save:
            pref.save()

    def setNamingPresetPaths(self, paths, save=True):
        pref = self.settings()
        pref["settings"][namingPresetPaths] = paths
        if save:
            pref.save()

    def setNamingPresetSavePath(self, path, save=True):
        defaultNamingPath = self.defaultNamingConfigPath()
        if os.path.normpath(path) == defaultNamingPath:
            return
        pref = self.settings()
        pref["settings"][namingPresetSavePath] = path
        if save:
            pref.save()

    def setUserBuildScripts(self, scriptIds, save=True):
        """Sets which build script plugins to use by default.

        :param scriptIds: The build script plugin ids to always use by default for every rig.
        :type scriptIds: list[str]
        :param save: Whether or not this change should immediately be save to disk.
        :type save: bool
        """
        pref = self.settings()
        pref["settings"]["buildScripts"] = scriptIds
        if save:
            pref.save()

    def setUserComponentPaths(self, paths, save=True):
        """Sets The user component paths for hive to search.

        :param paths: The list a folder paths
        :type paths: list[str]
        :param save: Save the paths to disk, default to True
        :type save: bool
        """
        pref = self.settings()
        pref["settings"][componentPathKey] = paths
        if save:
            pref.save()

    def setUserBuildScriptPaths(self, paths, save=True):
        """Sets The user build script paths for hive to search.

        :param paths: The list a folder paths
        :type paths: list[str]
        :param save: Save the paths to disk, default to True
        :type save: bool
        """
        pref = self.settings()

        pref["settings"][buildScriptPathsKey] = paths
        if save:
            pref.save()

    def setUserTemplatePaths(self, paths, save=True):
        """Sets The user template paths for hive to search.

        :param paths: The list a folder paths
        :type paths: list[str]
        :param save: Save the paths to disk, default to True
        :type save: bool
        """
        pref = self.settings()

        pref["settings"][templatePathsKey] = paths

        if save:
            pref.save()

    def setUserTemplateSavePath(self, path, save=True):
        """Sets The user template Save path.

        :param path: The absolute folder path where new templates will be saved.
        :type path: str
        :param save: Save the path to disk, default to True
        :type save: bool
        """
        pref = self.settings()
        currentSavePath = self.userTemplateSavePath()
        resolved = os.path.expandvars(os.path.expanduser(path))
        if not os.path.exists(resolved):
            return
        elif resolved == currentSavePath:
            return
        pref["settings"][templateSavePathKey] = path
        if save:
            pref.save()
