# Renderers -----------------------------
ARNOLD = "Arnold"
REDSHIFT = "Redshift"
RENDERMAN = "Renderman"
VIEWPORT2 = "Viewport"  # todo "Viewport" should become "Maya" and be phased out
VRAY = "VRay"
MAYA = "Maya"
UNKNOWN = ""
ALL = "All"

# Renderer lists -----------------------------
RENDERER_NICE_NAMES = [ARNOLD, REDSHIFT, RENDERMAN]  # Old list for older UIs
DFLT_RNDR_LIST = [MAYA, ARNOLD, REDSHIFT, RENDERMAN, VRAY]  # New list for newer UIs

# Browser filters ----------------------------
RENDERER_BROWSER_FILTERS = {MAYA: [MAYA, "maya", "BLNN", "STRD", "PHNG", "PNGE", "LMBT", "RAMP", "standardSurface",
                                   "Blinn", "Phong", "PhongE", "Lambert", "Ramp", "blinn", "phong", "phongE",
                                   "lambert"],
                            ARNOLD: [ARNOLD, "arnold", "ARN", "Arnold", "aiStandardSurface", "STRD", "standardSurface"],
                            REDSHIFT: [REDSHIFT, "redshift", "Redshift", "redshiftMaterial", "RedshiftMaterial"],
                            RENDERMAN: [RENDERMAN, "renderman", "PXR", "Renderman", "pxrSurface", "PxrSurface"],
                            VRAY: [VRAY, "vray", "v-ray", "V-Ray", "V-ray", "VRAY", "VRay", "STRD", "standardSurface"]}

# Icon and nice-names for renderIconMenus -------------------
DFLT_RNDR_MODES = [("arnold", ARNOLD), ("redshift", REDSHIFT), ("renderman", RENDERMAN)]  # older UIs
RENDERER_ICONS_LIST = [("maya", MAYA), ("arnold", ARNOLD), ("vray", VRAY), ("redshift", REDSHIFT),
                       ("renderman", RENDERMAN)]  # Newer UIs
RENDERER_ICONS_LIST_ALL = [("checkMark", ALL)] + RENDERER_ICONS_LIST  # Used in .MA and .MB browser filters

RENDERER_ICONS_DICT = {REDSHIFT: "redshift",
                       RENDERMAN: "renderman",
                       ARNOLD: "arnold",
                       VRAY: "vray",
                       MAYA: "maya"}

# Plugins -------------------
RENDERER_PLUGIN = {REDSHIFT: "redshift4maya",
                   RENDERMAN: "RenderMan_for_Maya",
                   ARNOLD: "mtoa",
                   VRAY: "vrayformaya"}

# Renderer Suffixing -----------------------------
RENDERER_SUFFIX = {ARNOLD: "ARN",
                   REDSHIFT: "RS",
                   RENDERMAN: "PXR",
                   VRAY: "VRAY",
                   MAYA: "MAYA"
                   }  # not a great list better to use shader types for suffixing in many cases
RENDERER_SUFFIX_DICT = dict(RENDERER_SUFFIX)  # todo duplicated old code should be only one suffix dict
RENDERER_SUFFIX_DICT[VIEWPORT2] = "VP2"  # adds the viewport suffix, technically it's not a renderer shader suffix

# ----------- SHADER TYPES ------------------------
# todo: should be in shader constants not in renderer constants as are shaders
# Maya ------------------
SHAD_TYPE_BLINN = "blinn"
SHAD_TYPE_LAMBERT = "lambert"
SHAD_TYPE_PHONG = "phong"
SHAD_TYPE_PHONGE = "phongE"
SHAD_TYPE_STANDARD = "standardSurface"
# Arnold ------------------
SHAD_TYPE_AISTANDARD = "aiStandardSurface"
# Redshift ------------------
SHAD_TYPE_REDSHIFTM = "redshiftMaterial"
# Renderman ------------------
SHAD_TYPE_PXRSURFACE = "pxrSurface"
SHAD_TYPE_PXRLAYER = "pxrLayerSurface"

# Default Shaders that come with Maya ---------------------
# todo: move to shader constants
DEFAULT_MAYA_SHADER_TYPES = [SHAD_TYPE_LAMBERT, SHAD_TYPE_BLINN, SHAD_TYPE_STANDARD, SHAD_TYPE_PHONG, SHAD_TYPE_PHONGE,
                             "rampShader", "anisotropic", "ShaderfxShader", "StingrayPBS", "hairPhysicalShader",
                             "hairTubeShader", "layeredShader", "oceanShader", "shadingMap", "surfaceShader",
                             "useBackground"]
# Zoo Supported Shader Types -------------------------
MAYA_SHADER_TYPES = [SHAD_TYPE_LAMBERT, SHAD_TYPE_BLINN, SHAD_TYPE_STANDARD, SHAD_TYPE_PHONG, SHAD_TYPE_PHONGE]
RENDERMAN_SHADER_TYPES = [SHAD_TYPE_PXRSURFACE, SHAD_TYPE_PXRLAYER]
ARNOLD_SHADER_TYPES = [SHAD_TYPE_AISTANDARD]
REDSHIFT_SHADER_TYPES = [SHAD_TYPE_REDSHIFTM]

# All zoo supported shader types in a dict by renderer --------------------
RENDERER_SHAD_TYPES = {MAYA: MAYA_SHADER_TYPES,
                       REDSHIFT: REDSHIFT_SHADER_TYPES,
                       RENDERMAN: RENDERMAN_SHADER_TYPES,
                       ARNOLD: ARNOLD_SHADER_TYPES}

RENDERER_COLORSPACES = ["scene-linear Rec.709-sRGB", "ACEScg", "ACES2065-1", "scene-linear DCI-P3 D65", "Rec.2020"]
DISPLAY_MODES = ["ACES 1.0 SDR-video", "Un-tone-mapped", "Unity neutral tone-map", "Log", "Raw"]
