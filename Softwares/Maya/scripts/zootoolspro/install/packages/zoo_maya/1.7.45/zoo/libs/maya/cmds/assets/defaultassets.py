"""Module  related to default internal assets included withing the Zoo Tools Pro scripts folder.
Light Presets, HDRI skydome texture paths, control curves etc.

.. code-block:: python

    from zoo.libs.maya.cmds.assets import defaultassets
    defaultassets.importLightPresetAutoRenderer()

Author Andrew Silke
"""

import os

from maya import cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.assets import assetsimportexport, assetsconstants
from zoo.libs.maya.cmds.cameras import cameras
from zoo.libs.maya.cmds.renderer import exportabcshaderlights
from zoo.libs.maya.cmds.lighting import renderertransferlights
from zoo.libs.maya.cmds.display import viewportmodes
from zoo.libs.maya.cmds.lighting import lightsmultihdri, lightconstants
from zoo.libs.maya.cmds.shaders import shdmultconstants, shadermultirenderer as shdmult
from zoo.libs.maya.cmds.rig import controls
from zoo.libs.maya.cmds.renderer import multirenderersettings

# ---------------------------
# Internal Asset Folders
# ---------------------------
PREFERENCES_FOLDER_NAME = assetsconstants.PREFERENCES_FOLDER_NAME  # preferences directory
ASSETS_FOLDER_NAME = assetsconstants.ASSETS_FOLDER_NAME  # main assets dir under the internal preferences folder
CONTROL_SHAPES_FOLDER_NAME = assetsconstants.CONTROL_SHAPES_FOLDER_NAME  # the name of the control shapes folder under assets
MODEL_ASSETS_FOLDER_NAME = assetsconstants.MODEL_ASSETS_FOLDER_NAME  # the name of the model assets folder under assets
HDR_SKYDOMES_FOLDER_NAME = assetsconstants.HDR_SKYDOMES_FOLDER_NAME
LIGHT_PRESETS_FOLDER_NAME = assetsconstants.LIGHT_PRESETS_FOLDER_NAME
SHADERS_FOLDER_NAME = assetsconstants.SHADERS_FOLDER_NAME

# ---------------------------
# Paths To Asset Folders
# ---------------------------
CONTROL_SHAPES_PATH = assetsconstants.CONTROL_SHAPES_PATH
MODEL_ASSETS_PATH = assetsconstants.MODEL_ASSETS_PATH
HDR_SKYDOMES_PATH = assetsconstants.HDR_SKYDOMES_PATH
LIGHT_PRESETS_PATH = assetsconstants.LIGHT_PRESETS_PATH
SHADERS_PATH = assetsconstants.SHADERS_PATH

# ---------------------------
# Default Asset Names. Usually file names.
# ---------------------------
CONTROL_CIRCLE = assetsconstants.CONTROL_CIRCLE
CONTROL_CUBE = assetsconstants.CONTROL_CUBE
CONTROL_SPHERE = assetsconstants.CONTROL_SPHERE

ASSET_SHADER_BOT = assetsconstants.ASSET_SHADER_BOT
ASSET_LIGHT_SCENE = assetsconstants.ASSET_LIGHT_SCENE
ASSET_CYC_GREY_SCENE = assetsconstants.ASSET_CYC_GREY_SCENE
ASSET_CYC_DARK_SCENE = assetsconstants.ASSET_CYC_DARK_SCENE
ASSET_MACBETH_BALLS = assetsconstants.ASSET_MACBETH_BALLS

LIGHT_PRESET_ASSET_DEFAULT = assetsconstants.LIGHT_PRESET_ASSET_DEFAULT
LIGHT_PRESET_THREE_POINT = assetsconstants.LIGHT_PRESET_THREE_POINT
LIGHT_PRESET_THREE_POINT_DARK = assetsconstants.LIGHT_PRESET_THREE_POINT_DARK
LIGHT_PRESET_F_PUMPS = assetsconstants.LIGHT_PRESET_F_PUMPS
LIGHT_PRESET_WINTER_F = assetsconstants.LIGHT_PRESET_WINTER_F
LIGHT_PRESET_RED_AQUA_RIM = assetsconstants.LIGHT_PRESET_RED_AQUA_RIM
LIGHT_PRESET_SOFT_TOP = assetsconstants.LIGHT_PRESET_SOFT_TOP
LIGHT_PRESET_SOFT_TOP_RIM = assetsconstants.LIGHT_PRESET_SOFT_TOP_RIM

HDR_F_PUMPS = assetsconstants.HDR_F_PUMPS
HDR_F_PUMPS_ROT_OFFSET = assetsconstants.HDR_F_PUMPS_ROT_OFFSET
HDR_F_PUMPS_INT_MULT = assetsconstants.HDR_F_PUMPS_INT_MULT

HDR_F_PUMPS_BW = assetsconstants.HDR_F_PUMPS_BW
HDR_F_PUMPS_BW_ROT_OFFSET = assetsconstants.HDR_F_PUMPS_BW_ROT_OFFSET
HDR_F_PUMPS_BW_INT_MULT = assetsconstants.HDR_F_PUMPS_BW_INT_MULT

HDR_WINTER_F = assetsconstants.HDR_WINTER_F
HDR_WINTER_F_ROT_OFFSET = assetsconstants.HDR_WINTER_F_ROT_OFFSET
HDR_WINTER_F_INT_MULT = assetsconstants.HDR_WINTER_F_INT_MULT

HDR_PLATZ = assetsconstants.HDR_PLATZ
HDR_PLATZ_ROT_OFFSET = assetsconstants.HDR_PLATZ_ROT_OFFSET
HDR_PLATZ_INT_MULT = assetsconstants.HDR_PLATZ_INT_MULT

SHADERS_SKIN_DARK_BACKLIT = assetsconstants.SHADERS_SKIN_DARK_BACKLIT
SHADERS_DARK_BACKGROUND = assetsconstants.SHADERS_DARK_BACKGROUND

# ---------------------------
# Camera Types
# ---------------------------
CAMTYPE_DEFAULT = assetsconstants.CAMTYPE_DEFAULT
CAMTYPE_HDR = assetsconstants.CAMTYPE_HDR
CAMTYPE_CONTROL = assetsconstants.CAMTYPE_CONTROL

# ---------------------------
# Default Renderer
# ---------------------------
RENDERER = assetsconstants.RENDERER  # Not used by UIs, just for testing

# ---------------------------
# Full Asset Paths
# ---------------------------
DEFAULT_LIGHT_PRESET_PATH = assetsconstants.DEFAULT_LIGHT_PRESET_PATH  # bw factory pumps
WINTER_F_LIGHT_PRESET_PATH = assetsconstants.WINTER_F_LIGHT_PRESET_PATH  # Default IBL no changes
ASSET_LIGHTPRESET_PATH = assetsconstants.ASSET_LIGHTPRESET_PATH  # rim studio
THREE_POINT_LIGHT_PRESET_PATH = assetsconstants.THREE_POINT_LIGHT_PRESET_PATH  # three point soft
THREE_POINT_DRK_LIGHT_PRESET_PATH = assetsconstants.THREE_POINT_DRK_LIGHT_PRESET_PATH  # three point dark
RED_AQUA_RIM_LIGHT_PRESET_PATH = assetsconstants.RED_AQUA_RIM_LIGHT_PRESET_PATH  # three point soft
SOFT_TOP_LIGHT_PRESET_PATH = assetsconstants.SOFT_TOP_LIGHT_PRESET_PATH  # three point soft
SOFT_TOP_RIM_LIGHT_PRESET_PATH = assetsconstants.SOFT_TOP_RIM_LIGHT_PRESET_PATH  # three point soft

# --------------------
# Light Preset Internal Files as Dictionaries
# --------------------

PRESET_DEFAULT = assetsconstants.PRESET_DEFAULT  # this is the factory pump bw with rims
PRESET_THREEPOINT = assetsconstants.PRESET_THREEPOINT
PRESET_THREEPOINTDRK = assetsconstants.PRESET_THREEPOINTDRK
PRESET_SOFTTOP = assetsconstants.PRESET_SOFTTOP
PRESET_REDAQUA = assetsconstants.PRESET_REDAQUA
PRESET_FACTORYCOLOR = assetsconstants.PRESET_FACTORYCOLOR
PRESET_FACTORYGREY = assetsconstants.PRESET_FACTORYGREY
PRESET_WINTER = assetsconstants.PRESET_WINTER
PRESET_CITYPLATZ = assetsconstants.PRESET_CITYPLATZ  # this is the default city platz


# ---------------------------
# HELPER FUNCTIONS
# ---------------------------


def importZooSceneDefault(fullPath, renderer, replaceByType=False):
    """Imports a zoo scene file with default settings for the current renderer

    :param fullPath: The fullpath to the .zooScene file
    :type fullPath: str
    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param replaceByType: Will replace assets by type and delete previous shaders of the same name
    :type replaceByType: str
    """
    assetsimportexport.importZooSceneAsAsset(fullPath,
                                             renderer,
                                             replaceAssets=replaceByType,
                                             importAbc=True,
                                             importShaders=True,
                                             importLights=True,
                                             addShaderSuffix=True,
                                             importSubDInfo=True,
                                             replaceRoots=True,
                                             turnStart=0,
                                             turnEnd=0,
                                             turnOffset=0.0,
                                             loopAbc=False,
                                             rotYOffset=0,
                                             scaleOffset=1.0)


def renderStatsAttrs(geoShape, castsShadows=None, receiveShadows=True, holdOut=None, motionBlur=None,
                     primaryVisibility=None, smoothShading=None, visibleInReflections=None, visibleInRefractions=None,
                     doubleSided=None, opposite=None):
    """Sets attribute values for the render stats on an object's shape node

    :param geoShape: A geometry shape node name
    :type geoShape: list(str)
    """
    if castsShadows is not None:
        cmds.setAttr("{}.castsShadows".format(geoShape), castsShadows)
    if receiveShadows is not None:
        cmds.setAttr("{}.receiveShadows".format(geoShape), receiveShadows)
    if holdOut is not None:
        cmds.setAttr("{}.holdOut".format(geoShape), holdOut)
    if motionBlur is not None:
        cmds.setAttr("{}.motionBlur".format(geoShape), motionBlur)
    if primaryVisibility is not None:
        cmds.setAttr("{}.primaryVisibility".format(geoShape), primaryVisibility)
    if smoothShading is not None:
        cmds.setAttr("{}.smoothShading".format(geoShape), smoothShading)
    if visibleInReflections is not None:
        cmds.setAttr("{}.visibleInReflections".format(geoShape), visibleInReflections)
    if visibleInRefractions is not None:
        cmds.setAttr("{}.visibleInRefractions".format(geoShape), visibleInRefractions)
    if doubleSided is not None:
        cmds.setAttr("{}.doubleSided".format(geoShape), doubleSided)
    if opposite is not None:
        cmds.setAttr("{}.opposite".format(geoShape), opposite)


def renderStatsAttrsList(geoShapeList, castsShadows=None, receiveShadows=True, holdOut=None, motionBlur=None,
                         primaryVisibility=None, smoothShading=None, visibleInReflections=None,
                         visibleInRefractions=None,
                         doubleSided=None, opposite=None):
    """Sets attribute values for the render stats on an object's shape node

    :param geoShapeList: A list of geometry shape nodes
    :type geoShapeList: list(str)
    """
    for geoShape in geoShapeList:
        renderStatsAttrs(geoShape, castsShadows=castsShadows, receiveShadows=receiveShadows, holdOut=holdOut,
                         motionBlur=motionBlur, primaryVisibility=primaryVisibility, smoothShading=smoothShading,
                         visibleInReflections=visibleInReflections, visibleInRefractions=visibleInRefractions,
                         doubleSided=doubleSided, opposite=opposite)


def createDefaultCamera(type=CAMTYPE_DEFAULT):
    """Creates a default camera for scenes based on the type

    type:

        CAMTYPE_DEFAULT = "default"
        CAMTYPE_HDR = "hdr"
        CAMTYPE_CONTROL = "control"

    :param type: The type of asset the camera is for, "default", "hdr", "control"
    :type type: str
    :return cameraTransform: The camera transform node name
    :rtype cameraTransform: str
    :return cameraShape: The camera shape node name
    :rtype cameraShape: str
    """
    # check camera to see if it exists
    cameraTransform, cameraShape = cameras.createCameraZxy(message=True)
    if type == CAMTYPE_DEFAULT:
        cmds.move(0, 75, 700, cameraTransform, absolute=True)
        cmds.setAttr("{}.focalLength".format(cameraShape), 80)
        cmds.setAttr("{}.centerOfInterest".format(cameraShape), 720)
    elif type == CAMTYPE_HDR:
        cmds.setAttr("{}.focalLength".format(cameraShape), 12)
    elif type == CAMTYPE_CONTROL:
        cmds.setAttr("{}.orthographic".format(cameraShape), 1)
        cmds.setAttr("{}.orthographicWidth".format(cameraShape), 2.5)
        cmds.setAttr("{}.rotateX".format(cameraTransform), -45.0)
        cmds.setAttr("{}.rotateY".format(cameraTransform), 45.0)
        cmds.move(0, 0, 4, cameraTransform, objectSpace=True)
    return cameraTransform, cameraShape


def setCameraResolution(cameraShape="cameraShape1", width=520, height=520, clipPlanes=(0.9, 5000.0), antiAlias=True,
                        grid=False, setRes=True):
    """Sets the camera film gate and scene resolution (render globals render image width height)

    Also sets up the display of the camera clip planes and anti aliasing

    :param cameraShape: The name of the camera shape node
    :type cameraShape: str
    :param width: The width in pixels of the render globals render image size
    :type width: int
    :param height: The height in pixels of the render globals render image size
    :type height: int
    :param clipPlanes: The viewport display clipping planes
    :type clipPlanes: tuple(int)
    :param antiAlias: Anti alias the viewport?
    :type antiAlias: bool
    :param grid: Show the grid in the viewport?
    :type grid: bool
    """
    # Set Render Globals -----------------------------
    if setRes:
        cameras.setGlobalsWidthHeight(width, height)
    if cameraShape:
        # Set Camera -----------------------------
        cameras.setZooResolutionGate(cameraShape, resolutionGate=True)
        cameras.setCamFitResGate(cameraShape, fitResolutionGate=cameras.CAM_FIT_RES_OVERSCAN)
        # Look Through ----------------------------
        camTransform = cmds.listRelatives(cameraShape, parent=True)[0]
        cmds.lookThru(camTransform)
        if not grid:  # Then hide the grid
            panel = viewportmodes.panelUnderPointerOrFocus(viewport3d=True, message=False)
            cmds.modelEditor(panel, edit=1, grid=False)
    # Set Clip Planes Anti Aliasing -----------------------------------------
    cameras.setCurrCamClipPlanes(clipPlanes[0], clipPlanes[1])
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", antiAlias)  # Anti-aliasing on


def importLightPreset(renderer=RENDERER, lightPresetPath=DEFAULT_LIGHT_PRESET_PATH, hdrImage=HDR_F_PUMPS_BW,
                      showIbl=False, hdrIntMult=1.0, hdrRotOffset=0.0, message=False):
    """Import a light preset from a folder path and image with basic kwargs.

    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param lightPresetPath: The full path to the folder of the light presets
    :type lightPresetPath: str
    :param hdrImage: The HDR Image name with extension
    :type hdrImage: str
    :param showIbl: Render the Skydome in the background?
    :type showIbl: bool
    """
    exportabcshaderlights.importLightPreset(lightPresetPath, renderer, True)  # builds the HDRI if None
    hdriInstances = lightsmultihdri.hdriInstancesFromScene(message=False)
    if not hdriInstances:
        return
    # If IBL exists set values -------------
    hdriInstances[0].setRotateAndOffset((0.0, 45.0, 0.0), hdrRotOffset)
    hdriInstances[0].setIntensityAndMultiply(1.0, hdrIntMult)
    hdriInstances[0].setBackgroundVis(showIbl)
    if hdrImage:  # Override with internal HDR lores image apply multiply and offset values
        imagePath = os.path.join(HDR_SKYDOMES_PATH, hdrImage)  # Low internal path
        hdriInstances[0].setImagePath(imagePath)
    if message:
        output.displayInfo("Success: Light Preset Imported")


def importLightPresetAutoRenderer(internalLightDict=PRESET_DEFAULT, showIbl=False, message=True):
    """Import a light preset from a folder path and image with basic kwargs.  Automatically uses the Zoo set renderer

        multirenderersettings.currentRenderer()

    :param internalLightDict: The full path to the folder of the light presets,see assetsconstants.PRESET_DEFAULT
    :type internalLightDict: dict
    :param showIbl: Render the Skydome in the background?
    :type showIbl: bool
    :param message: Report a message to the user
    :type message: bool
    """
    importLightPreset(renderer=multirenderersettings.currentRenderer(),
                      lightPresetPath=internalLightDict["path"],
                      hdrImage=internalLightDict["hdriPath"],
                      showIbl=showIbl,
                      hdrIntMult=internalLightDict["intMult"],
                      hdrRotOffset=internalLightDict["rotOffset"],
                      message=message)


# ---------------------------
# BUILD SCENE - MAIN FUNCTIONS
# ---------------------------


def buildDefaultLightSceneCyc(renderer=RENDERER, lightPresetPath=DEFAULT_LIGHT_PRESET_PATH, message=True):
    """Builds a default Light Presets scene for thumbnail rendering

    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param lightPresetPath: The full path to the .zooScene file
    :type lightPresetPath:
    :param message: Report messages to the user?
    :type message: bool
    """
    # Import Assets Settings -----------------------------
    importZooSceneDefault(os.path.join(MODEL_ASSETS_PATH, ASSET_SHADER_BOT), renderer)  # Shader Bot
    importZooSceneDefault(os.path.join(MODEL_ASSETS_PATH, ASSET_LIGHT_SCENE), renderer)  # Light Scene
    # Render Stat Settings -----------------------------
    renderStatsAttrs("lineDontRenderShape", castsShadows=False, receiveShadows=False, holdOut=False, motionBlur=False,
                     primaryVisibility=False, smoothShading=False, visibleInReflections=False,
                     visibleInRefractions=False, doubleSided=False, opposite=False)
    sphereList = ["ball_reflect_geoShape", "ball_greyMatte_geoShape", "ball_greyPlastic_geoShape",
                  "ball_greyPlastic_geo1Shape"]
    renderStatsAttrsList(sphereList, castsShadows=False, receiveShadows=False)
    renderStatsAttrs("lowerFloor_geoShape", primaryVisibility=False)
    renderStatsAttrs("cyc_geoShape", castsShadows=False)
    # Optional Light Preset -----------------------------
    if lightPresetPath:  # create a light preset and change the skydome to off
        importLightPreset(renderer=renderer, lightPresetPath=DEFAULT_LIGHT_PRESET_PATH, hdrImage=HDR_F_PUMPS_BW)
    # Set Camera, Resolution and Globals -----------------------------
    setCameraResolution()
    # Set renderer defaults -----------------------
    multirenderersettings.setDefaultRenderSettings(renderer=renderer)
    # Message -----------------------------
    if message:
        output.displayInfo("Success: Light Presets render thumbnail scene created")


def buildDefaultHDRIScene(renderer=RENDERER, message=True):
    """Builds a default HDRI Skydome scene for thumbnail rendering

    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param message: Report messages to the user?
    :type message: bool
    """
    # Import light Preset with HDR
    skydomeName = "_".join([lightconstants.HDRI_DEFAULT_VALUES[lightconstants.HDRI_NAME],
                            shdmultconstants.SHADER_SUFFIX_DICT[renderer]])
    renderertransferlights.createSkydomeLightRenderer(skydomeName, renderer, warningState=False, cleanup=False,
                                                      setZXY=True)
    # Set Camera, Resolution and Globals -----------------------------
    cameraTransform, cameraShape = createDefaultCamera(type=CAMTYPE_HDR)
    cmds.setAttr("{}.rotateX".format(cameraTransform), 25)
    setCameraResolution(cameraShape=cameraShape)
    cameras.openTearOffCam(camera='persp')
    # Select Skydome ------------------
    cmds.select(skydomeName, replace=True)
    # Set renderer defaults -----------------------
    multirenderersettings.setDefaultRenderSettings(renderer=renderer)
    # Message -----------------------------
    if message:
        output.displayInfo("Success: HDR Skydome render thumbnail scene created")


def buildDefaultAssetsSceneCyc(renderer=RENDERER,
                               assetDirPath=MODEL_ASSETS_PATH,
                               assetZooScene=ASSET_CYC_DARK_SCENE,
                               lightPresetPath=ASSET_LIGHTPRESET_PATH,
                               hdrImage=HDR_F_PUMPS_BW,
                               hdrIntMult=1.0,
                               hdrRotOffset=0.0,
                               buildCamera=True,
                               buildBot=False,
                               setRes=True,
                               replaceByType=False,
                               setDefaultRenderSet=True,
                               darkShader=True,
                               message=True):
    """Builds a default Model Assets scene for thumbnail rendering

    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param message: Report messages to the user?
    :type message: bool
    """
    if renderer == shdmultconstants.MAYA or renderer == "All":
        output.displayWarning("Renderer is currently set to `{}`, will build for `Arnold`".format(renderer))
        renderer = shdmultconstants.ARNOLD
    if assetZooScene:
        # Import Cyc
        importZooSceneDefault(os.path.join(assetDirPath, assetZooScene), renderer, replaceByType=replaceByType)
        if darkShader:
            # Add dark shader -----------------------------
            zooScenePath = os.path.join(SHADERS_PATH, SHADERS_DARK_BACKGROUND)
            shaderName = "cycStudio_{}".format(shdmultconstants.SHADER_SUFFIX_DICT[renderer])
            shaderType = shdmult.RENDERERSHADERS[renderer][0]
            exportabcshaderlights.setShaderAttrsZooScene(zooScenePath,
                                                         shaderName,
                                                         shaderType,
                                                         renameToZooName=False,
                                                         message=message)
    if buildBot:  # Shader Bot
        importZooSceneDefault(os.path.join(MODEL_ASSETS_PATH, ASSET_SHADER_BOT), renderer, replaceByType=replaceByType)
    if lightPresetPath:  # Light Preset
        importLightPreset(renderer=renderer, lightPresetPath=lightPresetPath, hdrImage=hdrImage, hdrIntMult=hdrIntMult,
                          hdrRotOffset=hdrRotOffset)
    # Set Camera, Resolution and Globals -----------------------------
    if buildCamera:
        cameraTransform, cameraShape = createDefaultCamera(type=CAMTYPE_DEFAULT)
        setCameraResolution(cameraShape=cameraShape, setRes=setRes)
    if setDefaultRenderSet:
        # Set renderer defaults -----------------------
        multirenderersettings.setDefaultRenderSettings(renderer=renderer)
    # Message -----------------------------
    if message:
        output.displayInfo("Success: Asset render thumbnail scene created")


def buildDefaultShaderSceneCyc(renderer=RENDERER, message=True):
    """Builds a default Shader Preset scene for thumbnail rendering

    :param renderer: The renderer nicename to set the lights and shaders for
    :type renderer: str
    :param message: Report messages to the user?
    :type message: bool
    """
    # Import Cyc and Shader Bot -----------------------------
    importZooSceneDefault(os.path.join(MODEL_ASSETS_PATH, ASSET_CYC_GREY_SCENE), renderer)  # Cyc Grey
    importZooSceneDefault(os.path.join(MODEL_ASSETS_PATH, ASSET_SHADER_BOT), renderer)  # Shader Bot
    # Light Preset -----------------------------
    importLightPreset(renderer=renderer, lightPresetPath=DEFAULT_LIGHT_PRESET_PATH, hdrImage=HDR_F_PUMPS_BW)
    # Set Camera, Resolution and Globals -----------------------------
    cameraTransform, cameraShape = createDefaultCamera(type=CAMTYPE_DEFAULT)
    setCameraResolution(cameraShape=cameraShape)
    # Add a shader on shader bot -----------------------------
    zooScenePath = os.path.join(SHADERS_PATH, SHADERS_SKIN_DARK_BACKLIT)
    shaderName = "greyClearCoatSubtle_{}".format(shdmultconstants.SHADER_SUFFIX_DICT[renderer])
    shaderType = shdmult.RENDERERSHADERS[renderer][0]
    exportabcshaderlights.setShaderAttrsZooScene(zooScenePath,
                                                 shaderName,
                                                 shaderType,
                                                 renameToZooName=False,
                                                 message=message)
    # Move shader bot framing -----------------------------
    cmds.move(-4.0, 0.0, 0.0, "shaderBot_package_grp", absolute=True)
    # Set renderer defaults -----------------------
    multirenderersettings.setDefaultRenderSettings(renderer=renderer)
    # Message -----------------------------
    if message:
        output.displayInfo("Success: Shader Preset render thumbnail scene created")


def buildDefaultControlsScene(message=True):
    """Builds a default Control Shape scene for thumbnail rendering

    :param message: Report messages to the user?
    :type message: bool
    """
    # Build a Control Circle
    controls.buildControlsGUI(buildType=controls.CONTROL_BUILD_TYPE_LIST[1],
                              folderpath=CONTROL_SHAPES_PATH,
                              designName=CONTROL_CIRCLE,
                              rotateOffset=(0, -90, 0),
                              scale=(1.0, 1.0, 1.0),
                              children=False,
                              rgbColor=(0.16, 0.3, 0.875),
                              postSelectControls=True,
                              trackScale=True,
                              lineWidth=6,
                              grp=True,
                              freezeJnts=False)
    # Set Camera, Resolution and Globals -----------------------------
    cameraTransform, cameraShape = createDefaultCamera(type=CAMTYPE_CONTROL)
    setCameraResolution(cameraShape=cameraShape)
    # Message -----------------------------
    if message:
        output.displayInfo("Success: Control Shape thumbnail Scene Created")
