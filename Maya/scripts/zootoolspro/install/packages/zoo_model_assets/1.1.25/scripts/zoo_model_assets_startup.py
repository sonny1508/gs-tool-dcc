"""
Startup function:

    builds the default asset directories if they don't exist

"""
import logging

logger = logging.getLogger("Zoo Model Assets Startup")


def startup(package):
    """Creates the assets folders if they don't exist

    1. Creates folder if it doesn't exist:
        userPath/zoo_preferences/assets/model_assets

    2. Upgrades .pref to "settings" if upgrading from 2.2.3 or lower

    3. Updates .pref dictionary keys if any are missing"""
    from zoo.apps.model_assets import assetconstants
    from zoo.preferences.core import preference
    from zoo.libs.utils.general import compareDictionaries
    preference.interface("model_assets_interface")
    preference.interface("maya_scenes_interface")
    updatePrefsKeys(assetconstants, compareDictionaries, preference)
    updateMayaPrefsKeys(assetconstants, compareDictionaries, preference)


def updatePrefsKeys(assetConstants, compareDictionariesFunc, preference):
    """Updates .prefs keys if they are missing.  Useful for upgrading existing preferences"""
    modelAssetsLocalData = preference.findSetting(assetConstants.RELATIVE_PREFS_FILE, None)  # camera .prefs info
    modelAssetsDefaultData = preference.defaultPreferenceSettings("zoo_model_assets", "maya/zoo_model_assets")
    # Force upgrade if needed
    modelAssetsLocalDict = checkUpgradePrefs(modelAssetsLocalData, modelAssetsDefaultData, preference)
    if not modelAssetsLocalDict:  # Will straight copy across the prefs file or is cool
        return
    # Do the compare on dictionaries
    target, messageLog = compareDictionariesFunc(modelAssetsDefaultData["settings"], modelAssetsLocalDict)
    if messageLog:  # if keys have been updated
        modelAssetsLocalData.save(indent=True, sort=True)
        logger.info(messageLog)


def updateMayaPrefsKeys(assetConstants, compareDictionariesFunc, preference):
    """Updates .prefs keys if they are missing.  Useful for upgrading existing preferences"""
    modelAssetsLocalData = preference.findSetting(assetConstants.RELATIVE_MAYA_PREFS_FILE, None)  # camera .prefs info
    modelAssetsDefaultData = preference.defaultPreferenceSettings("zoo_model_assets", "maya/zoo_maya_scenes")
    # Force upgrade if needed
    modelAssetsLocalDict = checkUpgradePrefsMayaScenes(modelAssetsLocalData, modelAssetsDefaultData, preference)
    if not modelAssetsLocalDict:  # Will straight copy across the prefs file or is cool
        return
    # Do the compare on dictionaries
    target, messageLog = compareDictionariesFunc(modelAssetsDefaultData["settings"], modelAssetsLocalDict)
    if messageLog:  # if keys have been updated
        modelAssetsLocalData.save(indent=True, sort=True)
        logger.info(messageLog)


def checkUpgradePrefsMayaScenes(localData, defaultData, assetConstants):
    try:
        x = localData[assetConstants.PREFS_KEY_MAYA_SCENES]  # if this exists may need upgrading
    except:  # can ignore as not old file
        return dict()
        # File could be old so possibly upgrade
    try:
        assetsLocalDict = localData["settings"]
        return assetsLocalDict
    except:  # Upgrade from old prefs
        path = localData[assetConstants.PREFS_KEY_MAYA_SCENES]  # old path

        localData["settings"] = defaultData["settings"]  # add settings
        localData["settings"][assetConstants.PREFS_KEY_MAYA_SCENES] = path  # retain old path
        localData.save(indent=True, sort=True)
        return localData["settings"]


def checkUpgradePrefs(localData, defaultData, assetConstants):
    """Will upgrade the zoo_model_assets.prefs file by overwriting if the "settings" key does not exist

    Will only be needed if upgrading from in Zoo 2.2.3 or lower

    :param localData: The preference object for local model_assets data in zoo_preferences
    :type localData:
    :return camToolsLocalDict: The settings dictionary locally in zoo_preferences, now potentially updated
    :rtype assetsLocalDict: dict
    """
    try:
        x = localData[assetConstants.PREFS_KEY_MODEL_ASSETS]  # if this exists may need upgrading
    except:  # can ignore as not old file
        return dict()
    # File could be old so possibly upgrade
    try:
        assetsLocalDict = localData["settings"]
        return assetsLocalDict
    except:  # Upgrade from old prefs
        path = localData[assetConstants.PREFS_KEY_MODEL_ASSETS]  # old path

        localData["settings"] = defaultData["settings"]  # add settings
        localData["settings"][assetConstants.PREFS_KEY_MODEL_ASSETS] = path  # retain old path
        localData.save(indent=True, sort=True)
        return localData["settings"]
