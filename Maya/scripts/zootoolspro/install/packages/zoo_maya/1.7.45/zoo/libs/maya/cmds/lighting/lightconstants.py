"""Light constants

.. code-block:: python

    from zoo.libs.maya.cmds.lighting import lightconstants
    lightconstants.DEFAULT_SKYDOME_PATH  # is the path to the default HDRI texture image

Author Andrew Silke
"""
from zoo.libs.general import exportglobals
from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERER_SUFFIX, RENDERER_ICONS_LIST, RENDERER_ICONS_DICT
from zoo.libs.maya.cmds.assets import assetsconstants

# Generic keys ---------------------
NAME = "gName"
INTENSITY = "gIntensity"
TEMPERATURE = "gTemperature"
TEMPONOFF = "gTempOnOff"
LIGHTCOLOR = "gLightColor_srgb"
SHAPE = "gShape"
LIGHTVISIBILITY = "gLightVisibility"
EXPOSURE = "gExposure"

# Area Light Generic Attrs ---------------------
AREA_NAME = NAME
AREA_SHAPE = SHAPE
AREA_INTENSITY = INTENSITY
AREA_EXPOSURE = EXPOSURE
AREA_LIGHTCOLOR = LIGHTCOLOR
AREA_TEMPERATURE = TEMPERATURE
AREA_TEMPONOFF = TEMPONOFF
AREA_NORMALIZE = "gNormalize"
AREA_LIGHTVISIBILITY = LIGHTVISIBILITY
AREA_ROTATE = "gRotate"
AREA_TRANSLATE = "gTranslate"
AREA_SCALE = "gScale"

AREA_DEFAULT_VALUES = {AREA_NAME: "area",
                       AREA_INTENSITY: 1.0,
                       AREA_EXPOSURE: 16.0,
                       AREA_ROTATE: [0.0, 0.0, 0.0],
                       AREA_TRANSLATE: [0.0, 0.0, 0.0],
                       AREA_SCALE: [20.0, 20.0, 20.0],
                       AREA_SHAPE: 0,
                       AREA_NORMALIZE: True,
                       AREA_LIGHTVISIBILITY: False,
                       AREA_LIGHTCOLOR: [1.0, 1.0, 1.0],
                       AREA_TEMPONOFF: False,
                       AREA_TEMPERATURE: 6500.0}

# Directional Generic Attrs ---------------------
DIR_NAME = NAME
DIR_SHAPE = "gShape"
DIR_INTENSITY = INTENSITY
DIR_LIGHTCOLOR = LIGHTCOLOR
DIR_TEMPERATURE = TEMPERATURE
DIR_TEMPONOFF = TEMPONOFF
DIR_ANGLE_SOFT = "gAngleSoft"
DIR_ROTATE = "gRotate"
DIR_TRANSLATE = "gTranslate"
DIR_SCALE = "gScale"

DIR_DEFAULT_VALUES = {DIR_NAME: "directional",
                      DIR_INTENSITY: 1.0,
                      DIR_ROTATE: [0.0, 0.0, 0.0],
                      DIR_TRANSLATE: [0.0, 0.0, 0.0],
                      DIR_SCALE: [10.0, 10.0, 10.0],
                      DIR_SHAPE: 0,
                      DIR_ANGLE_SOFT: 2.0,
                      DIR_LIGHTCOLOR: [1.0, 1.0, 1.0],
                      DIR_TEMPONOFF: False,
                      DIR_TEMPERATURE: 6500.0}

# HDRI Skydome Generic Attrs ---------------------

HDRI_NAME = NAME
HDRI_SHAPE = "gShape"
HDRI_INTENSITY = INTENSITY
HDRI_EXPOSURE = EXPOSURE
HDRI_LIGHTVISIBILITY = LIGHTVISIBILITY
HDRI_INVERT = "gInvert"
HDRI_TEXTURE = "gTexture"
HDRI_TINT = "gTint"
HDRI_ROTATE = "gRotate"
HDRI_TRANSLATE = "gTranslate"
HDRI_SCALE = "gScale"

HDRI_DEFAULT_VALUES = {HDRI_NAME: "hdriSkydome",
                       HDRI_INTENSITY: 1.0,
                       HDRI_ROTATE: [0.0, 0.0, 0.0],
                       HDRI_TRANSLATE: [0.0, 0.0, 0.0],
                       HDRI_SCALE: [1.0, 1.0, 1.0],
                       HDRI_TEXTURE: "",
                       HDRI_INVERT: False,
                       HDRI_LIGHTVISIBILITY: True,
                       HDRI_TINT: [1.0, 1.0, 1.0]}

LIGHTS_GROUP_NAME = "Lights_grp"

# RENDERER GLOBALS ---------------
MAYA = exportglobals.MAYA
REDSHIFT = exportglobals.REDSHIFT  # "Redshift"
RENDERMAN = exportglobals.RENDERMAN
ARNOLD = exportglobals.ARNOLD
VRAY = exportglobals.VRAY
GENERIC = exportglobals.GENERIC

AREALIGHTS = exportglobals.AREALIGHTS
IBLSKYDOMES = exportglobals.IBLSKYDOMES
DIRECTIONALS = exportglobals.DIRECTIONALS

# Area Light Types ---------------
SHAPE_ATTR_ENUM_LIST = ["rectangle", "disc", "sphere", "cylinder"]
SHAPE_ATTR_ENUM_LIST_NICE = ["Rectangle", "Disc", "Sphere", "Cylinder"]

# note Renderman has more than one light type for other shapes
RENDERERAREALIGHTS = {REDSHIFT: "RedshiftPhysicalLight",
                      RENDERMAN: ["PxrRectLight", "PxrSphereLight", "PxrDiskLight"],
                      ARNOLD: "aiAreaLight",
                      VRAY: "VRayLightRectShape",
                      MAYA: "areaLight"}

AREA_TYPES = [RENDERERAREALIGHTS[REDSHIFT], RENDERERAREALIGHTS[ARNOLD], "PxrRectLight", "PxrSphereLight",
              "PxrDiskLight", RENDERERAREALIGHTS[VRAY], RENDERERAREALIGHTS[MAYA]]

AREA_RENDERER_SUPPORTED = [ARNOLD, REDSHIFT, VRAY, RENDERMAN]

AREA_TYPES_RENDERER = {"RedshiftPhysicalLight": REDSHIFT,
                       "PxrRectLight": RENDERMAN,
                       "PxrSphereLight": RENDERMAN,
                       "PxrDiskLight": RENDERMAN,
                       "aiAreaLight": ARNOLD,
                       "VRayLightRectShape": VRAY,
                       "areaLight": MAYA}

# Directional Light Types ---------------

RENDERERDIRECTIONALLIGHTS = {REDSHIFT: "RedshiftPhysicalLight",
                             RENDERMAN: "PxrDistantLight",
                             ARNOLD: "directionalLight",
                             VRAY: "VRaySunShape",
                             MAYA: "directionalLight"}

DIRECTIONAL_TYPES = [RENDERERDIRECTIONALLIGHTS[REDSHIFT], RENDERERDIRECTIONALLIGHTS[ARNOLD],
                     RENDERERDIRECTIONALLIGHTS[RENDERMAN], RENDERERDIRECTIONALLIGHTS[VRAY],
                     RENDERERDIRECTIONALLIGHTS[MAYA]]

DIRECTIONAL_RENDERER_SUPPORTED = [ARNOLD, REDSHIFT, VRAY, RENDERMAN]

DIRECTIONAL_TYPES_RENDERER = {"RedshiftPhysicalLight": REDSHIFT,
                              "PxrDistantLight": RENDERMAN,
                              "directionalLight": [ARNOLD, MAYA],
                              "VRaySunShape": VRAY}

DIRECTIONAL_TRACKER_ATTR = "zooRendererTracker"

# HDRI Skydome Light Types ---------------

RENDERERSKYDOMELIGHTS = {REDSHIFT: "RedshiftDomeLight",
                         RENDERMAN: "PxrDomeLight",
                         ARNOLD: "aiSkyDomeLight",
                         VRAY: "VRayLightDomeShape"}

SKYDOME_TYPES = [RENDERERSKYDOMELIGHTS[ARNOLD], RENDERERSKYDOMELIGHTS[REDSHIFT], RENDERERSKYDOMELIGHTS[VRAY],
                 RENDERERSKYDOMELIGHTS[RENDERMAN]]

SKYDOME_RENDERER_SUPPORTED = [ARNOLD, REDSHIFT, VRAY, RENDERMAN]

SKYDOME_TYPES_RENDERER = {"RedshiftDomeLight": REDSHIFT,
                          "PxrDomeLight": RENDERMAN,
                          "aiSkyDomeLight": ARNOLD,
                          "VRayLightDomeShape": VRAY}

RENDERER_SUFFIX["Generic"] = "lgtLc"

# --------------------
# LIGHT DICT KEYS
# --------------------
GENERICLIGHTATTRDICT = {AREA_INTENSITY: "intensity",
                        AREA_EXPOSURE: "exposure",
                        AREA_LIGHTCOLOR: "color",
                        AREA_TEMPERATURE: "temperature",
                        AREA_TEMPONOFF: "tempOnOff",
                        AREA_NORMALIZE: "normalize",
                        AREA_SHAPE: "areaShape",
                        AREA_LIGHTVISIBILITY: "lightVis"}

GENERIC_DIRECTIONAL_ATTR_DICT = {DIR_INTENSITY: "intensity",
                                 DIR_LIGHTCOLOR: "color",
                                 DIR_TEMPERATURE: "temperature",
                                 DIR_TEMPONOFF: "tempOnOff",
                                 DIR_ANGLE_SOFT: "angleSoft"}

# --------------------
# IBL Light dict keys
# --------------------

GENERICSKYDOMEATTRDICT = {HDRI_INTENSITY: "intensity",
                          HDRI_EXPOSURE: "exposure",
                          HDRI_SHAPE: "areaShape",
                          HDRI_LIGHTVISIBILITY: "lightVis",
                          HDRI_TEXTURE: "IblTexturePath"}

# --------------------
# IBL Internal Textures
# --------------------

# Zoo Internal HDRI textures
HDR_PLATZ_PATH = assetsconstants.HDR_F_PUMPS_PATH  # Full path to internal texture
HDR_PLATZ_INT_MULT = assetsconstants.HDR_PLATZ_INT_MULT  # intensity multiplier eg 2.2
HDR_PLATZ_ROT_OFFSET = assetsconstants.HDR_PLATZ_ROT_OFFSET  # rotation offset eg 60.0

HDR_F_PUMPS_PATH = assetsconstants.HDR_F_PUMPS_PATH
HDR_F_PUMPS_INT_MULT = assetsconstants.HDR_F_PUMPS_INT_MULT
HDR_F_PUMPS_ROT_OFFSET = assetsconstants.HDR_F_PUMPS_ROT_OFFSET

HDR_F_PUMPS_BW_PATH = assetsconstants.HDR_F_PUMPS_BW_PATH
HDR_F_PUMPS_BW_INT_MULT = assetsconstants.HDR_F_PUMPS_BW_INT_MULT
HDR_F_PUMPS_BW_ROT_OFFSET = assetsconstants.HDR_F_PUMPS_BW_ROT_OFFSET

HDR_WINTER_F_PATH = assetsconstants.HDR_WINTER_F_PATH
HDR_WINTER_F_INT_MULT = assetsconstants.HDR_WINTER_F_INT_MULT
HDR_WINTER_F_ROT_OFFSET = assetsconstants.HDR_WINTER_F_ROT_OFFSET

DEFAULT_SKYDOME_PATH = assetsconstants.DEFAULT_SKYDOME_PATH  # city platz
DEFAULT_SKYDOME_INT_MULT = assetsconstants.DEFAULT_SKYDOME_INT_MULT
DEFAULT_SKYDOME_ROT_OFFSET = assetsconstants.DEFAULT_SKYDOME_ROT_OFFSET

# --------------------
# Light Preset Internal Files - Dictionaries with the preset path and HDRI overriddes.
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
