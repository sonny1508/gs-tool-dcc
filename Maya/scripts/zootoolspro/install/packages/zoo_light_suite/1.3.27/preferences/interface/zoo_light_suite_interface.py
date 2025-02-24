import glob
import os

from zoo.preferences.core import prefinterface
from zoo.libs.utils.general import compareDictionaries
from zoo.preferences.assets import BrowserPreference
from zoo.apps.light_suite import lightconstants as lc
from zoo.core.util import zlogging

from zoo.libs.general import exportglobals


PRESET_SUFFIX = [exportglobals.ZOOSCENESUFFIX]


logger = zlogging.getLogger(__name__)


class LightSuitePreference(prefinterface.PreferenceInterface):
    id = "light_suite_interface"
    _relativePath = "prefs/maya/zoo_light_suite.pref"

    def __init__(self, preference):
        super(LightSuitePreference, self).__init__(preference)
        self.skydomesPreference = BrowserPreference("light_suite_ibl_skydomes", self)
        self.skydomesPreference.fileTypes = self.iblSkydomeExtensionList()
        self.lightPresetsPreference = BrowserPreference("light_suite_light_presets", self)


    def updatePrefsKeys(self):
        """Updates .prefs keys if they are missing.  Useful for upgrading existing preferences"""
        lightLocalData = self.preference.findSetting(self._relativePath, None)  # light .prefs info

        lightDefaultData = self.preference.defaultPreferenceSettings("zoo_light_suite", "maya/zoo_light_suite")
        # Force upgrade if needed
        lightLocalDict = self.checkUpgradePrefs(lightLocalData, lightDefaultData)
        if not lightLocalDict:  # Will straight copy across the prefs file or is cool
            return
        # Do the compare on dictionaries
        target, messageLog = compareDictionaries(lightDefaultData["settings"], lightLocalDict)
        if messageLog:  # if keys have been updated
            lightLocalData.save(indent=True, sort=True)
            logger.info(messageLog)

    def checkUpgradePrefs(self, localData, defaultData):
        """Will upgrade the zoo_model_assets.prefs file by overwriting if the "settings" key does not exist

        Will only be needed if upgrading from in Zoo 2.2.3 or lower

        :param localData: The preference object for local model_assets data in zoo_preferences
        :type localData:
        :return camToolsLocalDict: The settings dictionary locally in zoo_preferences, now potentially updated
        :rtype assetsLocalDict: dict
        """
        try:
            x = localData[lc.PREFS_KEY_PRESETS]  # if this exists may need upgrading
        except:  # can ignore as not old file
            return dict()
        # File could be old so possibly upgrade
        try:
            assetsLocalDict = localData["settings"]
            return assetsLocalDict  # is ok, settings exist
        except:  # Upgrade from old prefs
            presetPath = localData[lc.PREFS_KEY_PRESETS]  # old path
            iblPath = localData[lc.PREFS_KEY_IBL]  # old path
            localData["settings"] = defaultData["settings"]  # add settings
            localData["settings"][lc.PREFS_KEY_PRESETS] = presetPath  # retain old path
            localData["settings"][lc.PREFS_KEY_IBL] = iblPath  # retain old path
            localData.save(indent=True, sort=True)
            logger.info("Upgraded user `Light Suite` settings")
            return localData["settings"]

    def iblSkydomeExtensionList(self, ignoreTxTex=False):
        """returns the current ibl image extension list

        Return Example:
            ["hdr", "tif", "tiff", "hdri", "exr", "ibl"]

        :param ignoreTxTex: If True do not return "tx" or "tex" file extensions
        :type ignoreTxTex: bool
        :return iblSkydomeExtensionList: A list of the current ibl skydome extensions in use from the preferences
        :rtype iblSkydomeExtensionList: list(str)
        """
        pref = self.settings(self._relativePath, root=None)
        settings = pref["settings"]
        iblSkydomeExtensionList = list()
        if settings[lc.PREFS_KEY_EXR]:
            iblSkydomeExtensionList.append("exr")
        if settings[lc.PREFS_KEY_HDR]:
            iblSkydomeExtensionList.append("hdr")
            iblSkydomeExtensionList.append("hdri")
        if settings[lc.PREFS_KEY_TIF]:
            iblSkydomeExtensionList.append("tif")
            iblSkydomeExtensionList.append("tiff")
        if settings[lc.PREFS_KEY_TEX] and not ignoreTxTex:
            iblSkydomeExtensionList.append("tex")
        if settings[lc.PREFS_KEY_TX] and not ignoreTxTex:
            iblSkydomeExtensionList.append("tx")
        return iblSkydomeExtensionList

    def iblSkydomeImageList(self, ignoreTxTex=False):
        """Lists all the images inside of the prefs IBL directory.
        Automatically filters images by the Hdr image types given in the preferences.

        Return Example:
            ["HDRIHaven_autoshop_01.hdr", "HDRI-SKIES_Sky092.exr", "HDRLabs_StadiumCenter.tif"]

        :param ignoreTxTex: If True do not return "tx" or "tex" file extensions
        :type ignoreTxTex: bool
        :return iblImageList: List of the IBL images inside of the iblQuickDir
        :rtype iblImageList: list
        """
        iblFolder = self.settings(self._relativePath, root=None, name=lc.PREFS_KEY_IBL)
        iblImageList = list()
        imageExtList = self.iblSkydomeExtensionList(ignoreTxTex=ignoreTxTex)
        if not os.path.isdir(iblFolder):  # check if directory actually exists
            return iblImageList
        for ext in imageExtList:  # find images in directory
            for filePath in glob.glob(os.path.join(iblFolder, "*.{}".format(ext))):
                iblImageList.append(os.path.basename(filePath))
        return iblImageList

    def lightPresetDirectory(self):
        return self.settings(self._relativePath, root=None, name=lc.PREFS_KEY_PRESETS)

    def skydomeDirectories(self):
        return [i.path for i in self.skydomesPreference.activeBrowserPaths()]

        # return self.settings(self._relativePath, root=None, name=lc.PREFS_KEY_IBL)

    def lightPresetZooSceneList(self):
        """Lists all of the light presets inside the Light Presets directory
        The light presets are files each with a single scene light setup

        Return Example:
            ["soft_sunsetSides.zooScene", "sun_redHarsh.zooScene", "sun_warmGlow.zooScene"]

        :return presetList: A list of .zooScene files each with a single scene light setup
        :rtype presetList: list(str)
        """
        lightPresetFolder = self.settings(self._relativePath, root=None, name=lc.PREFS_KEY_PRESETS)
        lightPresetList = list()
        if not os.path.isdir(lightPresetFolder):  # check if directory actually exists
            return lightPresetList  # emptyList and directory
        for ext in PRESET_SUFFIX:
            for filePath in glob.glob(os.path.join(lightPresetFolder, "*.{}".format(ext))):
                lightPresetList.append(os.path.basename(filePath))
        return lightPresetList
