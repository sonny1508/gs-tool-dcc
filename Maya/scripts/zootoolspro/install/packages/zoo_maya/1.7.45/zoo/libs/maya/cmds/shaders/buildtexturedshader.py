"""

from zoo.libs.maya.cmds.shaders import buildtexturedshader
textureDict = buildtexturedshader.testTextureDictFromPath()  # test data
buildtexturedshader.buildTexturedShader(textureDict, shaderType="standardSurface", shaderName="")

"""

import os

from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.shaders import shadermulti

FOLDER_PATH = "D:/Dropbox/zoo_assets_silky/textures/Bricks074_1K-JPG"

TEST_LIST = ["Bricks074_1K_AmbientOcclusion.jpg", "Bricks074_1K_Color.jpg", "Bricks074_1K_Displacement.jpg",
             "Bricks074_1K_NormalDX.jpg", "Bricks074_1K_NormalGL.jpg", "Bricks074_1K_Roughness.jpg"]

NAME = "name"

DIFFUSE_WEIGHT_SRCH = "DiffuseWeight"
DIFFUSE_SRCH = "Color"
DIFFUSE_ROUGHNESS_SRCH = "DiffuseRoughness"
METALNESS_SRCH = "Metalness"

SPECULAR_WEIGHT_SRCH = "SpecularWeight"
SPECULAR_SRCH = "Specular"
SPECULAR_ROUGHNESS_SRCH = "Roughness"
SPECULAR_IOR_SRCH = "SpecularIOR"

COAT_WEIGHT_SRCH = "CoatWeight"
COAT_SRCH = "Coat"
COAT_ROUGHNESS_SRCH = "CoatRoughness"
COAT_IOR_SRCH = "CoatIOR"

EMISSION_WEIGHT_SRCH = "EmissionWeight"
EMISSION_SRCH = "Emission"

AO_SRCH = "AmbientOcclusion"
BUMP_SRCH = "Displacement"
NORMAL_SRCH = "NormalGL"

SEARCH_SUFFIX_LIST = [DIFFUSE_WEIGHT_SRCH, DIFFUSE_SRCH, DIFFUSE_ROUGHNESS_SRCH, METALNESS_SRCH, SPECULAR_WEIGHT_SRCH,
                      SPECULAR_SRCH, SPECULAR_ROUGHNESS_SRCH, SPECULAR_IOR_SRCH, COAT_WEIGHT_SRCH, COAT_SRCH,
                      COAT_ROUGHNESS_SRCH, COAT_IOR_SRCH, EMISSION_WEIGHT_SRCH, EMISSION_SRCH, AO_SRCH, BUMP_SRCH,
                      NORMAL_SRCH, NAME]

# TODO needs a dict where the search keys match with generic keys.
# TODO keys below should be more generic and in the shader constants

DIFFUSE_WEIGHT = "diffuseWeight"
DIFFUSE = "diffuse"
DIFFUSE_ROUGHNESS = "diffuseRoughness"
METALNESS = "metalness"

SPECULAR_WEIGHT = "specularWeight"
SPECULAR = "specular"
SPECULAR_ROUGHNESS = "specularRoughness"
SPECULAR_IOR = "specularIOR"

COAT_WEIGHT = "coatWeight"
COAT = "coat"
COAT_ROUGHNESS = "coatRoughness"
COAT_IOR = "coatIOR"

EMISSION_WEIGHT = "emissionWeight"
EMISSION = "emission"

AO = "ao"
BUMP = "bump"
NORMAL = "normal"


def textureDictFromPath(path, textureList, searchSuffixList):
    """Creates a dictionary of shader paths.  search suffix is the key and the path is the value.

    textureList is

    :param path: The path of the directory where the files live.
    :type path: str
    :param textureList: Filenames (not paths) of files on disk, some filenames may not be textures and will be ignored.
    :type textureList: list(str)
    :param searchSuffixList: A list of the available suffixes to find the textures by suffix.
    :type searchSuffixList: list(str)

    :return textureDict: A dictionary with search suffixing as keys and texture paths as values, might change
    :rtype textureDict: dict(str: str)
    """
    textureDict = dict()
    for txtr in textureList:
        txtrNoFilename = os.path.splitext(txtr)[0]
        for sfx in searchSuffixList:
            nameParts = txtrNoFilename.split("_")
            if sfx == nameParts[-1]:
                textureDict[NAME] = namehandling.stripSuffixExact(txtrNoFilename, nameParts[-1])
                textureDict[sfx] = os.path.join(path, txtr)
    return textureDict


def testTextureDictFromPath():
    """Creates a texture dict test data for testing
    """
    return textureDictFromPath(FOLDER_PATH, TEST_LIST, SEARCH_SUFFIX_LIST)


def buildTexturedShader(textureDict, shaderType="standardSurface", shaderName=""):
    """Creates a new shader with textures from a texture dictionary.

    :param textureDict: A dictionary with search suffixing as keys and texture paths as values, might change
    :type textureDict: dict(str: str)
    :param shaderType: The type of shader to build, supported shader types in shdrmultconstants
    :type shaderType: str
    :param shaderName: The optional name of the shader, if empty will create the shader name from the textures.
    :type shaderName: str

    :return shdInstance: A Zoo shader instance object
    :rtype shaderInstance: :class:`zoo.libs.maya.cmds.shaders.shadertypes.shaderbase.ShaderBase`
    :return txtr_nodes_dict: attrTypes are the keys and texture node lists are the values.
    :rtype txtr_nodes_dict: dict(str: list(str))
    """
    txtr_nodes_dict = dict()

    if not shaderName:
        shaderName = textureDict[NAME]

    # Create the shader ----------------
    shdInstance = shadermulti.createShaderInstanceType(shaderType, shaderName=shaderName)

    # Build the color textures ----------------
    if DIFFUSE_SRCH in textureDict.keys():
        txtr_nodes_dict[DIFFUSE] = shdInstance.setDiffuseTexture(textureDict[DIFFUSE_SRCH])
    if SPECULAR_SRCH in textureDict.keys():
        txtr_nodes_dict[SPECULAR] = shdInstance.setSpecColorTexture(textureDict[SPECULAR_SRCH])
    if COAT_SRCH in textureDict.keys():
        txtr_nodes_dict[COAT] = shdInstance.setCoatColorTexture(textureDict[COAT_SRCH])
    if EMISSION_SRCH in textureDict.keys():
        txtr_nodes_dict[EMISSION] = shdInstance.setEmissionColorTexture(textureDict[EMISSION_SRCH])

    # Build the scalar textures ----------------
    if DIFFUSE_WEIGHT_SRCH in textureDict.keys():
        txtr_nodes_dict[DIFFUSE_WEIGHT] = shdInstance.setDiffuseWeightTexture(textureDict[DIFFUSE_WEIGHT_SRCH])
    if DIFFUSE_ROUGHNESS_SRCH in textureDict.keys():
        txtr_nodes_dict[DIFFUSE_ROUGHNESS] = shdInstance.setDiffuseRoughnessTexture(textureDict[DIFFUSE_ROUGHNESS_SRCH])
    if SPECULAR_WEIGHT_SRCH in textureDict.keys():
        txtr_nodes_dict[SPECULAR_WEIGHT] = shdInstance.setSpecWeightTexture(textureDict[SPECULAR_WEIGHT_SRCH])
    if SPECULAR_ROUGHNESS_SRCH in textureDict.keys():
        txtr_nodes_dict[SPECULAR_ROUGHNESS] = shdInstance.setSpecRoughnessTexture(textureDict[SPECULAR_ROUGHNESS_SRCH])
    if SPECULAR_IOR_SRCH in textureDict.keys():
        txtr_nodes_dict[SPECULAR_IOR] = shdInstance.setSpecIORTexture(textureDict[SPECULAR_IOR_SRCH])
    if COAT_WEIGHT_SRCH in textureDict.keys():
        txtr_nodes_dict[COAT_WEIGHT] = shdInstance.setCoatWeightTexture(textureDict[COAT_WEIGHT_SRCH])
    if COAT_ROUGHNESS_SRCH in textureDict.keys():
        txtr_nodes_dict[COAT_ROUGHNESS] = shdInstance.setCoatRoughTexture(textureDict[COAT_ROUGHNESS_SRCH])
    if COAT_IOR_SRCH in textureDict.keys():
        txtr_nodes_dict[COAT_IOR] = shdInstance.setCoatIORTexture(textureDict[COAT_IOR_SRCH])
    if EMISSION_WEIGHT_SRCH in textureDict.keys():
        txtr_nodes_dict[EMISSION_WEIGHT] = shdInstance.setEmissionColorTexture(textureDict[EMISSION_WEIGHT_SRCH])

    return shdInstance, txtr_nodes_dict
