"""Misc shader constants

from zoo.libs.maya.cmds.shaders import shdmultconstants
shdmultconstants.ARNOLD

Author: Andrew Silke
"""

from zoo.libs.maya.utils import mayaenv
from zoo.libs.maya.cmds.renderer import rendererconstants

MAYA_VERSION = mayaenv.mayaVersion()  # whole numbers (int) 2020 etc

# Renderers ----------------
ARNOLD = rendererconstants.ARNOLD
RENDERMAN = rendererconstants.RENDERMAN
REDSHIFT = rendererconstants.REDSHIFT
VRAY = rendererconstants.VRAY
MAYA = rendererconstants.MAYA
UNKNOWN = rendererconstants.UNKNOWN

# Default Shader Values ----------------
DEFAULT_SHADER_NAME = "shader_01"

DIFFUSE_DEFAULT = [0.735, 0.735, 0.735]
DIFFUSE_WEIGHT_DEFAULT = 1.0
DIFFUSE_ROUGHNESS_DEFAULT = 0.0
METALNESS_DEFAULT = 0.0
SPECULAR_DEFAULT = [1.0, 1.0, 1.0]
SPECULAR_WEIGHT_DEFAULT = 1.0
ROUGHNESS_DEFAULT = 0.5
IOR_DEFAULT = 1.5
COAT_COLOR_DEFAULT = [1.0, 1.0, 1.0]
COAT_ROUGH_DEFAULT = 0.1
COAT_WEIGHT_DEFAULT = 0.0
COAT_IOR_DEFAULT = 1.5
EMISSION_DEFAULT = [0.0, 0.0, 0.0]
EMISSION_WEIGHT_DEFAULT = 0.0

# Maya Shaders ----------------
STANDARD_SURFACE = "standardSurface"
LAMBERT = "lambert"
BLINN = "blinn"
PHONG = "phong"
PHONGE = "phongE"

# Arnold Shaders ----------------
AI_STANDARD_SURFACE = "aiStandardSurface"

# VRay Shaders ----------------
VRAY_MTL = "VRayMtl"

# Redshift Shaders ----------------
REDSHIFT_MATERIAL = "RedshiftMaterial"

# Renderman Shaders ----------------
PXR_SURFACE = "PxrSurface"
PXR_LAYER_SURFACE = "PxrLayerSurface"

MAYA_DEFAULT_SHADER = STANDARD_SURFACE
if MAYA_VERSION < 2020:
    MAYA_DEFAULT_SHADER = BLINN

# Shader Lists ---------------------
MAYA_SHADER_LIST = [STANDARD_SURFACE, LAMBERT, BLINN, PHONG, PHONGE]
if MAYA_VERSION < 2020:
    MAYA_SHADER_LIST = [LAMBERT, BLINN, PHONG, PHONGE]

SHADER_TYPE_LIST = [STANDARD_SURFACE, LAMBERT, BLINN, PHONG, PHONGE, AI_STANDARD_SURFACE, VRAY_MTL,
                    REDSHIFT_MATERIAL, PXR_SURFACE]
if MAYA_VERSION < 2020:
    SHADER_TYPE_LIST = [LAMBERT, BLINN, PHONG, PHONGE, AI_STANDARD_SURFACE, VRAY_MTL,
                        REDSHIFT_MATERIAL, PXR_SURFACE]

RENDERER_ICONS_LIST = rendererconstants.RENDERER_ICONS_LIST  # with Maya and VRay
RENDERER_ICONS_DICT = rendererconstants.RENDERER_ICONS_DICT

# Shader Suffixing ---------------------
STRD_SUFFIX = "STRD"
ARN_SUFFIX = "ARN"
VRAY_SUFFIX = "VRAY"
RS_SUFFIX = "RS"
PXR_SUFFIX = "PXR"
LMBT_SUFFIX = "LMBT"
BLNN_SUFFIX = "BLNN"
PHNG_SUFFIX = "PHNG"
PNGE_SUFFIX = "PNGE"

# Render shader suffix  #todo should be phased out and no longer used, old shader model, use SHADERTYPE_SUFFIX_DICT
SHADER_SUFFIX_DICT = {REDSHIFT: RS_SUFFIX,
                      ARNOLD: ARN_SUFFIX,
                      RENDERMAN: PXR_SUFFIX}

SHADERTYPE_SUFFIX_DICT = {STANDARD_SURFACE: STRD_SUFFIX,
                          AI_STANDARD_SURFACE: ARN_SUFFIX,
                          VRAY_MTL: VRAY_SUFFIX,
                          REDSHIFT_MATERIAL: RS_SUFFIX,
                          PXR_SURFACE: PXR_SUFFIX,
                          LAMBERT: LMBT_SUFFIX,
                          BLINN: BLNN_SUFFIX,
                          PHONG: PHNG_SUFFIX,
                          PHONGE: PNGE_SUFFIX}
if MAYA_VERSION < 2020:
    SHADERTYPE_SUFFIX_DICT = {AI_STANDARD_SURFACE: ARN_SUFFIX,
                              VRAY_MTL: VRAY_SUFFIX,
                              REDSHIFT_MATERIAL: RS_SUFFIX,
                              PXR_SURFACE: PXR_SUFFIX,
                              LAMBERT: LMBT_SUFFIX,
                              BLINN: BLNN_SUFFIX,
                              PHONG: PHNG_SUFFIX,
                              PHONGE: PNGE_SUFFIX}

SHADERTYPE_RENDERER = {STANDARD_SURFACE: MAYA,
                       AI_STANDARD_SURFACE: ARNOLD,
                       VRAY_MTL: VRAY,
                       REDSHIFT_MATERIAL: REDSHIFT,
                       PXR_SURFACE: RENDERMAN,
                       LAMBERT: MAYA,
                       BLINN: MAYA,
                       PHONG: MAYA,
                       PHONGE: MAYA}
if MAYA_VERSION < 2020:
    SHADERTYPE_RENDERER = {AI_STANDARD_SURFACE: ARNOLD,
                           VRAY_MTL: VRAY,
                           REDSHIFT_MATERIAL: REDSHIFT,
                           PXR_SURFACE: RENDERMAN,
                           LAMBERT: MAYA,
                           BLINN: MAYA,
                           PHONG: MAYA,
                           PHONGE: MAYA}

RENDERER_SHADERS_DICT = {MAYA: MAYA_SHADER_LIST,
                         ARNOLD: [AI_STANDARD_SURFACE],
                         VRAY: [VRAY_MTL],
                         REDSHIFT: [REDSHIFT_MATERIAL],
                         RENDERMAN: [PXR_SURFACE, PXR_LAYER_SURFACE],
                         }

RENDERER_DEFAULT_SHADER = {MAYA: MAYA_DEFAULT_SHADER,
                           ARNOLD: AI_STANDARD_SURFACE,
                           VRAY: VRAY_MTL,
                           REDSHIFT: REDSHIFT_MATERIAL,
                           RENDERMAN: PXR_SURFACE
                           }

# ----------------------------
# GENERIC SHADER DICT DICT KEYS
# ----------------------------
DIFFUSE = 'gDiffuseColor_srgb'
DIFFUSEWEIGHT = 'gDiffuseWeight'
DIFFUSEROUGHNESS = 'gDiffuseRoughness'
METALNESS = 'gMetalness'
SPECWEIGHT = 'gSpecWeight'
SPECCOLOR = 'gSpecColor_srgb'
SPECROUGHNESS = 'gSpecRoughness'
SPECIOR = 'gSpecIor'
COATCOLOR = 'gCoatColor_srgb'
COATWEIGHT = 'gCoatWeight'
COATROUGHNESS = 'gCoatRoughness'
COATIOR = 'gCoatIor'
EMISSION = 'gEmission_srgb'
EMISSIONWEIGHT = 'gEmissionWeight'

# ----------------------------
# SHADER PRESET DICT OVERRIDES (in marking menu)
# ----------------------------

# Designed to override shaders with existing colors, ie missing color attribute
# Plain Overrides
PRESET_PLAIN = {DIFFUSEROUGHNESS: 0.0,
                SPECWEIGHT: 0.0,
                METALNESS: 0.0,
                SPECCOLOR: [1.0, 1.0, 1.0],
                SPECROUGHNESS: 0.2,
                SPECIOR: 1.5,
                COATCOLOR: [1.0, 1.0, 1.0],
                COATWEIGHT: 0.0,
                COATROUGHNESS: 0.1,
                COATIOR: 1.5}
# Cloth Rough Overrides
PRESET_CLOTH_ROUGH = {DIFFUSEROUGHNESS: 1.0,
                      METALNESS: 0.0,
                      SPECWEIGHT: 1.0,
                      SPECCOLOR: [1.0, 1.0, 1.0],
                      SPECROUGHNESS: 0.8,
                      SPECIOR: 1.5,
                      COATCOLOR: [1.0, 1.0, 1.0],
                      COATWEIGHT: 0.0,
                      COATROUGHNESS: 0.1,
                      COATIOR: 1.5}
# Plastic Shiny Overrides
PRESET_PLASTIC_SHINE = {DIFFUSEROUGHNESS: 0.0,
                        SPECWEIGHT: 1.0,
                        METALNESS: 0.0,
                        SPECCOLOR: [1.0, 1.0, 1.0],
                        SPECROUGHNESS: 0.1,
                        SPECIOR: 1.5,
                        COATCOLOR: [1.0, 1.0, 1.0],
                        COATWEIGHT: 0.0,
                        COATROUGHNESS: 0.1,
                        COATIOR: 1.5}
# Plastic Rough
PRESET_PLASTIC_ROUGH = {DIFFUSEROUGHNESS: 0.0,
                        SPECWEIGHT: 1.0,
                        METALNESS: 0.0,
                        SPECCOLOR: [1.0, 1.0, 1.0],
                        SPECROUGHNESS: 0.5,
                        SPECIOR: 1.5,
                        COATCOLOR: [1.0, 1.0, 1.0],
                        COATWEIGHT: 0.0,
                        COATROUGHNESS: 0.1,
                        COATIOR: 1.5}
# Shiny Metal
PRESET_METAL_SHINE = {DIFFUSEROUGHNESS: 0.0,
                      SPECWEIGHT: 1.0,
                      METALNESS: 0.9,
                      SPECCOLOR: [1.0, 1.0, 1.0],
                      SPECROUGHNESS: 0.1,
                      SPECIOR: 1.5,
                      COATCOLOR: [1.0, 1.0, 1.0],
                      COATWEIGHT: 0.0,
                      COATROUGHNESS: 0.1,
                      COATIOR: 1.5}
# Rough Metal
PRESET_METAL_ROUGH = {DIFFUSEROUGHNESS: 0.0,
                      SPECWEIGHT: 1.0,
                      METALNESS: 0.9,
                      SPECCOLOR: [1.0, 1.0, 1.0],
                      SPECROUGHNESS: 0.5,
                      SPECIOR: 1.5,
                      COATCOLOR: [1.0, 1.0, 1.0],
                      COATWEIGHT: 0.0,
                      COATROUGHNESS: 0.1,
                      COATIOR: 1.5}
# Car Paint
PRESET_CAR_PAINT = {DIFFUSEROUGHNESS: 0.0,
                    SPECWEIGHT: 1.0,
                    METALNESS: 0.7,
                    SPECCOLOR: [1.0, 1.0, 1.0],
                    SPECROUGHNESS: 0.5,
                    SPECIOR: 1.5,
                    COATCOLOR: [1.0, 1.0, 1.0],
                    COATWEIGHT: 1.0,
                    COATROUGHNESS: 0.1,
                    COATIOR: 1.5}

# ----------------------------
# OLD SHADER SYSTEM CONSTANTS
# ----------------------------

ATTR_KEY_LIST = [DIFFUSE, DIFFUSEWEIGHT, DIFFUSEROUGHNESS,
                 SPECWEIGHT, SPECCOLOR, SPECROUGHNESS, SPECIOR,
                 METALNESS,
                 COATCOLOR, COATWEIGHT, COATROUGHNESS, COATIOR,
                 EMISSION, EMISSIONWEIGHT]  # USED IN OLD SYSTEM ONLY

GEN_KEY_LIST = [DIFFUSE, DIFFUSEWEIGHT,
                SPECWEIGHT, SPECCOLOR, SPECROUGHNESS, SPECIOR,
                COATCOLOR, COATWEIGHT, COATROUGHNESS, COATIOR]  # USED IN OLD SYSTEM ONLY

# Default keys for simple textures
TEXTURE_NODE = "textureNode"  # The name of the node connected to the shader
TEXTURE_SOURCE_ATTRIBUTE = "textureSourceAttr"  # The source attribute of the texture connecting to the shader
TEXTURE_DESTINATION_GEN_KEY = "textureDestinationGenKey"

SHADERMATCHPREFIX = "duplctS"

SHADERNAME = "shaderName"
OBJECTSFACES = "objectFaces"
ATTRSHADERDICT = "attributesShaderDict"

ATTRS_REDSHIFT_MATERIAL = {DIFFUSE: "diffuse_color",
                           DIFFUSEWEIGHT: "diffuse_weight",
                           SPECWEIGHT: "refl_weight",
                           SPECCOLOR: "refl_color",
                           SPECROUGHNESS: "refl_roughness",
                           SPECIOR: "refl_ior",
                           COATCOLOR: "coat_color",
                           COATWEIGHT: "coat_weight",
                           COATROUGHNESS: "coat_roughness",
                           COATIOR: "coat_ior"}  # METALNESS: "refl_metalness",

ATTRS_AI_STANDARD_SURFACE = {DIFFUSE: "baseColor",
                             DIFFUSEWEIGHT: "base",
                             SPECWEIGHT: "specular",
                             SPECCOLOR: "specularColor",
                             SPECROUGHNESS: "specularRoughness",
                             SPECIOR: "specularIOR",
                             COATCOLOR: "coatColor",
                             COATWEIGHT: "coat",
                             COATROUGHNESS: "coatRoughness",
                             COATIOR: "coatIOR"}  # METALNESS: "metalness",

ATTRS_PXR_SURFACE = {DIFFUSE: "diffuseColor",
                     DIFFUSEWEIGHT: "diffuseGain",
                     SPECWEIGHT: SPECWEIGHT,  # doesn't exist!!
                     SPECCOLOR: "specularEdgeColor",
                     SPECROUGHNESS: "specularRoughness",
                     SPECIOR: "specularIor",
                     COATCOLOR: "clearcoatEdgeColor",
                     COATWEIGHT: COATWEIGHT,  # doesn't exist!!
                     COATROUGHNESS: "clearcoatRoughness",
                     COATIOR: "clearcoatIor"}  # METALNESS: METALNESS,  # doesn't exist!!

# Displacement Dictionary keys for attributes and values
DISP_ATTR_TYPE = "type"
DISP_ATTR_DIVISIONS = "divisions"
DISP_ATTR_SCALE = "scale"
DISP_ATTR_AUTOBUMP = "autoBump"
DISP_ATTR_IMAGEPATH = "imagePath"
DISP_ATTR_BOUNDS = "bounds"
DISP_ATTR_RENDERER = "zooRenderer"

# Displacement Network globals, network names and attributes
NW_DISPLACE_NODE = "zooDisplacementNetwork"
NW_DISPLACE_MESH_ATTR = "zooDisplaceMeshConnect"
NW_DISPLACE_SG_ATTR = "zooDisplaceSGConnect"
NW_DISPLACE_FILE_ATTR = "zooDisplaceFileConnect"
NW_DISPLACE_PLACE2D_ATTR = "zooDisplacePlace2dConnect"
NW_DISPLACE_NODE_ATTR = "zooDisplaceNode"

NW_ATTR_LIST = [NW_DISPLACE_MESH_ATTR, NW_DISPLACE_SG_ATTR, NW_DISPLACE_FILE_ATTR, NW_DISPLACE_PLACE2D_ATTR,
                NW_DISPLACE_NODE_ATTR]
