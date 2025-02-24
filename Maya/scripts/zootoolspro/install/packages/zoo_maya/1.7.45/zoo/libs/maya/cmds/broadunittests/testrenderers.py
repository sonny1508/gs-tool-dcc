"""

from zoo.libs.maya.cmds.broadunittests import testrenderers

"""

import os

import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.assets import assetsimportexport
from zoo.libs.maya.cmds.renderer import rendererload, exportabcshaderlights
from zoo.libs.general import exportglobals
from zoo.apps.model_assets import assetconstants as ac
from zoo.apps.light_suite import lightconstants as lc
from zoo.libs.maya.cmds.lighting import renderertransferlights
from zoo.preferences.core import preference

RENDERER_LIST = exportglobals.SUPPORTEDRENDERERLIST

ASSET_LIST = ["c3dc/h_c3dc_nataliePose", "c3dc/h_c3dc_roboRun", "statues/h_stue_apolloBelvedere",
              "sculptBase/sb_h_faceReg", "backgrounds/bg_base-cylinderWoodBlack", "community/cartoon_tv_van"]
LIGHT_PRESET_LIST = ["assetDefault", "skydomePure_bloubergsunrise_2", "zz_watch_softGrey", "zz_watchSunsetPink"]


# -------------------------------
# ASSETS
# -------------------------------

def getAssetPath():
    modelAssetsPrefsData = preference.findSetting(ac.RELATIVE_PREFS_FILE, None)  # model asset .prefs info
    if not modelAssetsPrefsData.isValid():  # should be very rare
        raise Exception("Error ---> The preferences object is not valid")
    return modelAssetsPrefsData["settings"][ac.PREFS_KEY_MODEL_ASSETS]


def importReplaceAsset(path, assetName, renderer):
    if not rendererload.getRendererIsLoaded(renderer):
        rendererload.loadRenderer(renderer)
    # import asset
    fileName = ".".join([assetName, exportabcshaderlights.ZOOSCENESUFFIX])
    allNodes = assetsimportexport.importZooSceneAsAsset(os.path.join(path, fileName),
                                                        renderer,
                                                        replaceAssets=True,
                                                        importAbc=True,
                                                        importShaders=True,
                                                        importLights=True,
                                                        replaceShaders=False,
                                                        addShaderSuffix=True,
                                                        importSubDInfo=True,
                                                        replaceRoots=True,
                                                        turnStart=0,
                                                        turnEnd=0,
                                                        turnOffset=0.0,
                                                        loopAbc=True,
                                                        replaceByType=True,
                                                        rotYOffset=0.0,
                                                        scaleOffset=1.0)
    if allNodes:
        return True
    return False


def testImportChangeAssetsRenderer(renderer):
    """Tests importing of assets for the given renderer"""
    om2.MGlobal.displayInfo("\n\n---------- IMPORT ASSETS: {} -----------".format(renderer))
    assetPath = getAssetPath()
    if not assetPath:
        return
    # Import
    for assetName in ASSET_LIST:
        if not importReplaceAsset(assetPath, assetName, renderer):
            raise Exception("Error ---> Asset not imported {} {}".format(assetName, renderer))
        om2.MGlobal.displayInfo("log ---> Asset Imported: {} {}".format(assetName, renderer))
        # Delete imported asset
        assetName = assetName.split("/")[-1]  # because assets are now all in folders
        assetName = assetName.replace("-", "_")
        assetName = assetName.replace(" ", "_")
        assetsimportexport.deleteZooAssetSelected(uiSelectedName=assetName)
        om2.MGlobal.displayInfo("log ---> Asset Deleted: {} {}".format(assetName, renderer))


def testImportAssetAllRenderers(skipRenderers=[]):
    """Tests importing of assets for each renderer"""
    om2.MGlobal.displayInfo("\n\n\n"
                            "=============================== IMPORT ASSETS IN ALL RENDERERS START "
                            "=========================")
    for renderer in RENDERER_LIST:
        if renderer in skipRenderers:
            continue
        testImportChangeAssetsRenderer(renderer)
    om2.MGlobal.displayInfo("\n\n\n")
    if skipRenderers:
        om2.MGlobal.displayInfo("Note: Skipped Renderers: {}".format(skipRenderers))
    om2.MGlobal.displayInfo("#### SUCCESS IMPORTED ASSETS FOR ALL RENDERERS ####\n\n\n")

# -------------------------------
# LIGHT PRESETS
# -------------------------------

def getLightPresetPath():
    lightPresetsPrefsData = preference.findSetting(lc.RELATIVE_PREFS_FILE, None)  # model asset .prefs info
    if not lightPresetsPrefsData.isValid():  # should be very rare
        raise Exception("Error ---> The light preferences object is not valid")
    return lightPresetsPrefsData["settings"][lc.PREFS_KEY_PRESETS]


def importLightPreset(path, lightPresetName, renderer):
    if not rendererload.getRendererIsLoaded(renderer):
        rendererload.loadRenderer(renderer)
    # import asset
    fileName = ".".join([lightPresetName, exportabcshaderlights.ZOOSCENESUFFIX])
    exportabcshaderlights.importLightPreset(os.path.join(path, fileName),  renderer,  True)


def testLightPresetsRenderer(renderer):
    """Tests importing of assets for the given renderer"""
    om2.MGlobal.displayInfo("\n\n---------- IMPORT LIGHT PRESETS: {} -----------".format(renderer))
    lightPresetPath = getLightPresetPath()
    if not lightPresetPath:
        return
    # Import
    for lightPresetName in LIGHT_PRESET_LIST:
        importLightPreset(lightPresetPath, lightPresetName, renderer)
        om2.MGlobal.displayInfo("log ---> Light Preset Imported: {} {}".format(lightPresetName, renderer))
        # Delete imported asset
        renderertransferlights.deleteAllLightsInScene(renderer, message=False)
        om2.MGlobal.displayInfo("log ---> All Lights Deleted: {}".format(renderer))


def testLightPresetsAllRenderers(skipRenderers=[]):
    """Tests importing of assets for each renderer"""
    om2.MGlobal.displayInfo("\n\n\n"
                            "=============================== IMPORT LIGHT PRESETS IN ALL RENDERERS START "
                            "=========================")
    for renderer in RENDERER_LIST:
        if renderer in skipRenderers:
            continue
        testLightPresetsRenderer(renderer)
    om2.MGlobal.displayInfo("\n\n\n")
    if skipRenderers:
        om2.MGlobal.displayInfo("Note: Skipped Renderers: {}".format(skipRenderers))
    om2.MGlobal.displayInfo("#### SUCCESS IMPORTED LIGHT PRESETS FOR ALL RENDERERS ####\n\n\n")

