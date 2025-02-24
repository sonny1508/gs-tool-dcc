import os

from zoo.apps.camera_tools import cameraconstants as cc
from zoo.core.util import zlogging

from zoo.preferences.prefinterface import PreferenceInterface
from zoo.preferences.assets import BrowserPreference

logger = zlogging.getLogger(__name__)
from zoo.libs.utils.general import compareDictionaries


class CameraToolsPreferences(PreferenceInterface):
    id = "camera_tools_interface"
    _relativePath = "prefs/maya/zoo_camera_tools.pref"
    _settings = None


    def __init__(self, preference):
        super(CameraToolsPreferences, self).__init__(preference)
        self.imagePlaneAssets = BrowserPreference("image_planes", self, fileTypes=["png", "jpg"],
                                                  selectedIndices=[0])


    def updatePrefsKeys(self):
        """ Update preference keys

        Updates .prefs keys if they are missing.  Useful for upgrading existing preferences

        :return:
        """

        cameraToolsLocalData = self.preference.findSetting(cc.RELATIVE_PREFS_FILE, None)  # camera .prefs info
        cameraToolsDefaultData = self.preference.defaultPreferenceSettings("zoo_camera_tools", "maya/zoo_camera_tools")
        # Force upgrade if needed
        camToolsLocalDict = self.checkUpgradePrefs(cameraToolsLocalData, cameraToolsDefaultData)
        if not camToolsLocalDict:  # Will straight copy across the prefs file or is cool
            return
        # Do the compare on dictionaries
        target, messageLog = compareDictionaries(cameraToolsDefaultData["settings"], camToolsLocalDict)
        if messageLog:  # if keys have been updated
            cameraToolsLocalData.save(indent=True, sort=True)
            logger.info(messageLog)

    def checkUpgradePrefs(self, localData, defaultData):
        """Will upgrade the zoo_camera_tools.prefs file by overwriting if the "settings" key does not exist

        Will only be needed if upgrading from in Zoo 2.2.3 or lower

        :param localData: The preference object for local camera_tools data in zoo_preferences
        :type localData:
        :return camToolsLocalDict: The settings dictionary locally in zoo_preferences, now potentially updated
        :rtype camToolsLocalDict: dict
        """
        try:
            x = localData[cc.PREFS_KEY_IMAGEPLANE]  # if this exists may need upgrading
        except:  # can ignore as not old file
            return dict()
        try:
            camToolsLocalDict = localData["settings"]
            return camToolsLocalDict
        except:  # Upgrade from old prefs
            path = localData[cc.PREFS_KEY_IMAGEPLANE]  # old path
            localData["settings"] = defaultData["settings"]  # add settings
            localData["settings"][cc.PREFS_KEY_IMAGEPLANE] = path  # retain old path
            localData.save(indent=True, sort=True)
            logger.info("Upgraded user `Camera Tools` settings")
            return localData["settings"]