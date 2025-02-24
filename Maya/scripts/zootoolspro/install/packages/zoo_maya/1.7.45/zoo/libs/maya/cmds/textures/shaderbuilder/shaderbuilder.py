"""Module for building shaders with textures from external applications with various naming conventions.

This module is a WIP and will be upgraded/refactored.

# build a shader from textures from a single directory
from zoo.libs.maya.cmds.textures.shaderbuilder import shaderbuilder
shaderbuilder.buildShaderAndTextures(shaderType="standardSurface", files=FILES)

# build many shaders from sub directories.
from zoo.libs.maya.cmds.textures.shaderbuilder import shaderbuilder
directory = "C:/Users/userName/Documents/zoo_preferences/assets/maya_shaders/polyHaven"
shaderbuilder.buildShadersTextures(directory=directory)

# lookdev kit must be loaded for constant nodes.
"""

from maya import cmds
import os

from zoo.libs.utils import output
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.shaders import shadermulti, shdmultconstants
from zoo.libs.maya.cmds.textures.filetexturetypes import mayafiletexture
from zoo.libs.maya.cmds.textures.normaltypes import normalmaya

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".tga", ".exr")

DIRECTORY = r"C:\Users\Andrew Silke\Documents\zoo_preferences\assets\maya_shaders\polyHaven\cleanPebbles_STRD"
FILES = ["clean_pebbles_ao_2k.jpg", "clean_pebbles_arm_2k.jpg", "clean_pebbles_diff_2k.jpg",
         "clean_pebbles_disp_2k.jpg", "clean_pebbles_nor_dx_2k.jpg", "clean_pebbles_nor_gl_2k.jpg",
         "clean_pebbles_rough_2k.jpg"]

DIFFUSE_WEIGHT = "diffuseWeight"
DIFFUSE_COLOR = "diffuseColor"
ALBEDO_COLOR = "albedoColor"
DIFFUSE_ROUGHNESS = "diffuseRoughness"
METALNESS = "metalness"
SPECULAR_WEIGHT = "specularWeight"
SPECULAR_COLOR = "specularColor"
SPECULAR_ROUGHNESS = "specularRoughness"
SPECULAR_IOR = "specularIor"
COAT_WEIGHT = "coatWeight"
COAT_COLOR = "coatColor"
COAT_ROUGHNESS = "coatRoughness"
COAT_IOR = "coatIor"
EMISSION = "emissionColor"
EMISSION_WEIGHT = "emissionWight"
NORMAL = "normal"
BUMP = "bump"
DISPLACEMENT_BW = "displacementBw"
DISPLACEMENT_VECTOR = "displacementVector"
AO = "ao"
ARM = "arm"
TRANSLUCENT = "translucent"
TRANSPARENT = "transparent"
OPACITY = "opacity"

PRESET_POLY_HAVEN = "PolyHaven.com"
PRESET_SUBSTANCE = "Substance Painter"

PRESET_LIST = [PRESET_SUBSTANCE, PRESET_POLY_HAVEN]

POLY_HAVEN_DICT = {DIFFUSE_WEIGHT: [],
                   DIFFUSE_COLOR: ["diff", "col", "col_1", "col_2", "coll1", "coll2"],
                   ALBEDO_COLOR: ["albedo"],
                   DIFFUSE_ROUGHNESS: [],
                   METALNESS: ["metal"],
                   SPECULAR_WEIGHT: [],
                   SPECULAR_COLOR: ["spec"],
                   SPECULAR_ROUGHNESS: ["rough"],
                   SPECULAR_IOR: [],
                   COAT_WEIGHT: [],
                   COAT_COLOR: [],
                   COAT_ROUGHNESS: [],
                   COAT_IOR: [],
                   EMISSION: [],
                   EMISSION_WEIGHT: [],
                   NORMAL: ["nor_gl"],
                   BUMP: ["bump"],
                   DISPLACEMENT_BW: ["disp"],
                   DISPLACEMENT_VECTOR: [],
                   AO: ["ao"],
                   ARM: ["arm"],
                   TRANSLUCENT: ["translucent"],
                   TRANSPARENT: [],
                   OPACITY: []}

SUBSTANCE_DICT = {DIFFUSE_WEIGHT: [],
                  DIFFUSE_COLOR: ["BaseColor"],
                  ALBEDO_COLOR: ["BaseColor"],
                  DIFFUSE_ROUGHNESS: [],
                  METALNESS: ["Metalness"],
                  SPECULAR_WEIGHT: [],
                  SPECULAR_COLOR: [],
                  SPECULAR_ROUGHNESS: ["Roughness"],
                  SPECULAR_IOR: [],
                  COAT_WEIGHT: [],
                  COAT_COLOR: [],
                  COAT_ROUGHNESS: [],
                  COAT_IOR: [],
                  EMISSION: ["Emission"],
                  EMISSION_WEIGHT: [],
                  NORMAL: ["Normal"],
                  BUMP: ["Height"],
                  DISPLACEMENT_BW: [],
                  DISPLACEMENT_VECTOR: [],
                  AO: [],
                  ARM: [],
                  TRANSLUCENT: [],
                  TRANSPARENT: [],
                  OPACITY: ["Opacity"]}

PRESET_DICT = {PRESET_POLY_HAVEN: POLY_HAVEN_DICT,
               PRESET_SUBSTANCE: SUBSTANCE_DICT}


def shaderNamePolyHaven(filesNoExt):
    if "nor_gl" in filesNoExt[0] or "nor_dx" in filesNoExt[0]:  # otherwise suffix is _diff_2k etc 2 deep.
        return filesNoExt[0].split("_")[:-3]
    else:
        return filesNoExt[0].split("_")[:-2]


def fileTypesPolyHaven(files, filesNoExt):
    fileTypesDict = dict()
    for i, fileNoExt in enumerate(filesNoExt):
        for key in POLY_HAVEN_DICT:
            suffixList = POLY_HAVEN_DICT[key]
            if not suffixList:
                continue
            for suffix in suffixList:
                if suffix in fileNoExt:
                    fileTypesDict[key] = files[i]
                    continue
    return fileTypesDict


class ShaderTextureBuilder(object):
    def __init__(self):
        super(ShaderTextureBuilder, self).__init__()
        self.loadLookdevKit()
        self.filesNoExt = list()
        self.files = list()
        self.directory = ""
        self.shaderType = "standardSurface"
        self.shaderInst = None
        self.preset = ""
        self.fileTypesDict = dict()
        self.shaderName = ""
        self.diffuseTxtr = None
        self.builderInstances = list()

    def loadLookdevKit(self):
        if not cmds.pluginInfo('lookdevKit', query=True, loaded=True):
            cmds.loadPlugin('lookdevKit')

    def setShaderInstance(self, shaderInstance):
        self.shaderInst = shaderInstance

    def setPreset(self, preset=PRESET_POLY_HAVEN):
        self.preset = preset

    def setShaderType(self, shaderType):
        """
        :param shaderType: the type of shader eg. standardSurface
        :type shaderType: str
        """
        self.shaderType = shaderType

    # --------------
    # Handle Files
    # --------------

    def processFiles(self, files, directory):
        self.files = files
        self.directory = directory
        self._stripExtensions()  # generates self.filesNoExt
        self._shaderNameFromFiles()  # generates self.shaderName
        if not self.shaderName:  # Failed to find name from images
            return False
        self._extractFileTypes()  # generates self.fileTypesDict, keys as attributes value is each file with extension.
        if not self.fileTypesDict:
            return False
        return True

    def _shaderNameFromFiles(self):
        shaderNameParts = shaderNamePolyHaven(self.filesNoExt)
        if not shaderNameParts:
            # output.displayWarning("Images are not compatible in directory `{}`".format(self.directory))
            return ""
        # Build name ----------------------
        self.shaderName = shaderNameParts[0]
        for part in shaderNameParts[1:]:
            self.shaderName += part.capitalize()
        suffix = shdmultconstants.SHADERTYPE_SUFFIX_DICT[self.shaderType]
        self.shaderName += "_{}".format(suffix)

    def _stripExtensions(self):
        for file in self.files:
            self.filesNoExt.append(os.path.splitext(file)[0])

    def _extractFileTypes(self):
        self.fileTypesDict = fileTypesPolyHaven(self.files, self.filesNoExt)  # keys attributes value each file

    # --------------
    # Build Textures
    # --------------

    def mergeDiffuseAlbedo(self):
        if ALBEDO_COLOR in self.fileTypesDict:
            self.fileTypesDict[DIFFUSE_COLOR] = self.fileTypesDict[ALBEDO_COLOR]

    def buildShaders(self, diffuseColor=(0.5, 0.5, 0.5), combineNormalBump=True, includeAO=True, includeArm=True):
        """Creates all the textures as per the self.fileTypesDict contents.
        """
        layeredTextName = ""
        self.mergeDiffuseAlbedo()
        fileDict = self.fileTypesDict
        if SPECULAR_COLOR in fileDict:
            self.specColorTxtr = self.texture(SPECULAR_COLOR, self.shaderInst.specularColorAttr)
            self.builderInstances.append(self.specColorTxtr)
        else:
            self.shaderInst.setSpecColor([1.0, 1.0, 1.0])
        if (ARM in fileDict and includeArm and includeAO) or (AO in fileDict and includeAO):
            # connect and build the layered texture in the diffuse slot
            layeredTextName = self.layeredTexture(DIFFUSE_COLOR, self.shaderInst.diffuseColorAttr)
            # build and connect diffuse to the layered texture in at index 1
            if DIFFUSE_COLOR in fileDict:
                self.diffuseTxtr = self.colorToLayeredTexture(DIFFUSE_COLOR, layeredTextName, txtrIndex=2)
                self.builderInstances.append(self.diffuseTxtr)
        if ARM in fileDict and includeArm:  # ARM Texture should be built first as builds the layered texture node.
            self.armTxtr = self.armTexture(layeredTextName, includeAO)
            self.builderInstances.append(self.armTxtr)
        if (DIFFUSE_COLOR in fileDict and AO not in fileDict and ARM not in fileDict) or (
                DIFFUSE_COLOR in fileDict and not includeAO):
            self.diffuseTxtr = self.texture(DIFFUSE_COLOR, self.shaderInst.diffuseColorAttr)
            self.builderInstances.append(self.diffuseTxtr)
        elif not self.diffuseTxtr and layeredTextName:  # build color constant layeredTexture
            diffuseConstantColor = self.constantToLayeredTexture(DIFFUSE_COLOR, layeredTextName, txtrIndex=2)
            cmds.setAttr("{}.inColor".format(diffuseConstantColor),
                         diffuseColor[0], diffuseColor[1], diffuseColor[2], type="double3")
        elif not self.diffuseTxtr and not layeredTextName:
            self.shaderInst.setDiffuseSrgb(diffuseColor)
        if (SPECULAR_ROUGHNESS in fileDict and ARM not in fileDict) or (
                SPECULAR_ROUGHNESS in fileDict and not includeArm):
            self.roughnessTxtr = self.texture(SPECULAR_ROUGHNESS, self.shaderInst.specularRoughnessAttr, scalar=True)
            self.builderInstances.append(self.roughnessTxtr)
        if (METALNESS in fileDict and ARM not in fileDict) or (METALNESS in fileDict and not includeArm):
            self.metalnessTxtr = self.texture(METALNESS, self.shaderInst.metalnessAttr, scalar=True)
            self.builderInstances.append(self.metalnessTxtr)
        if AO in fileDict and ARM not in fileDict and includeAO:
            self.aoTxtr = self.colorToLayeredTexture(AO, layeredTextName, txtrIndex=1, removeEmptyTexture=False)
            self.builderInstances.append(self.aoTxtr)
        # Bump Normal Map ----------------------------------
        if NORMAL in fileDict and BUMP not in fileDict:
            self.normalTxtr = self.normalBumpTexture(NORMAL, normal=True, autoConnect=True)
            self.builderInstances.append(self.normalTxtr)
        elif BUMP in fileDict and NORMAL not in fileDict:
            self.bumpTxtr, bump2dNode = self.normalBumpTexture(BUMP, normal=False, autoConnect=True)
            self.builderInstances.append(self.bumpTxtr)
        elif NORMAL in fileDict and BUMP in fileDict:  # both bump and normal map exists so use a mixer.
            self.normalTxtr = self.normalBumpTexture(NORMAL, normal=True, autoConnect=True)
            self.builderInstances.append(self.normalTxtr)
            if combineNormalBump:  # cannot be seen in the viewport
                self.bumpTxtr = self.normalBumpTexture(BUMP, normal=False, autoConnect=False)
                cmds.connectAttr("{}.outNormal".format(self.bumpTxtr.name()),
                                 "{}.normalCamera".format(self.normalTxtr.name()))
                self.builderInstances.append(self.bumpTxtr)
        # Connect attrs to network node --------------------------------------------------------------

    def texture(self, nameType, masterAttribute, scalar=False):
        """Creates a color texture and plugs it into the masterAttribute

        :param nameType:
        :type nameType:
        :param masterAttribute:
        :type masterAttribute:
        :return:
        :rtype:
        """
        textureInst = mayafiletexture.MayaFileTexture(masterAttribute=masterAttribute,
                                                      masterNode=self.shaderInst.node,
                                                      textureName="_".join([self.shaderName, nameType]),
                                                      create=True,
                                                      scalar=scalar)
        textureInst.setPath(os.path.join(self.directory, self.fileTypesDict[nameType]))
        if scalar:
            textureInst.setColorSpace("Raw")
        return textureInst

    def normalBumpTexture(self, nameType, normal=False, autoConnect=True):
        """Normal or bump with no mixer

        :param nameType:
        :type nameType:
        :param normal:
        :type normal:
        :return:
        :rtype:
        """
        normalType = "normal" if normal else "bump"  # if normal then "normal"
        # Create bump/normal network
        normalBumpTxtrInst = normalmaya.NormalMaya(normalName=self.shaderName, normalType=normalType, create=True)
        normalBumpTxtrInst.setPath(os.path.join(self.directory, self.fileTypesDict[nameType]))  # texture path
        if autoConnect:
            normalBumpTxtrInst.connectOut(self.shaderInst)  # connects the normal/bump to the shader
        return normalBumpTxtrInst

    def colorToLayeredTexture(self, nameType, layeredTexture, txtrIndex=1, removeEmptyTexture=True):
        """Creates a color texture and plugs it into the txtrIndex of a layered shader

        :param nameType:
        :type nameType: str
        :param layeredTexture:
        :type layeredTexture: str
        :param txtrIndex:
        :type txtrIndex: int
        :param removeEmptyTexture:
        :type removeEmptyTexture: bool
        :return textureInst: textureInst
        :rtype textureInst: object
        """
        textureInst = mayafiletexture.MayaFileTexture(textureName="_".join([self.shaderName, nameType]), create=True)
        textureInst.setPath(os.path.join(self.directory, self.fileTypesDict[nameType]))
        cmds.connectAttr("{}.outColor".format(textureInst.name()),
                         "{}.inputs[{}].color".format(layeredTexture, str(txtrIndex)))
        if removeEmptyTexture:
            cmds.removeMultiInstance("{}.inputs[0]".format(layeredTexture), b=True)  # break = True
        return textureInst

    def constantToLayeredTexture(self, nameType, layeredTexture, txtrIndex=2):
        """Creates a constant color and plugs it into the txtrIndex of a layered shader

        :param nameType:
        :type nameType: str
        :param layeredTexture:
        :type layeredTexture: str
        :param txtrIndex:
        :type txtrIndex: int
        :return colorConstantName: colorConstantName
        :rtype colorConstantName: str
        """
        colorConstantName = cmds.shadingNode("colorConstant",
                                             asUtility=True, name="_".join([self.shaderName,
                                                                            "{}Constant".format(nameType)]))
        cmds.connectAttr("{}.outColor".format(colorConstantName),
                         "{}.inputs[{}].color".format(layeredTexture, str(txtrIndex)))  # usually slot 2
        return colorConstantName

    def armTexture(self, layeredTexture, includeA0=True):
        """Creates an ARM texture and connects to AO (layered texture), Roughness and Metalness.

        :param layeredTexture:
        :type layeredTexture: str
        :return textureInst: textureInst
        :rtype textureInst: object
        """
        textureInst = mayafiletexture.MayaFileTexture(textureName="_".join([self.shaderName, ARM]),
                                                      create=True)
        textureInst.setColorSpace("Raw")
        textureInst.setPath(os.path.join(self.directory, self.fileTypesDict[ARM]))
        if layeredTexture and includeA0:  # Connect AO ----------------------------
            # Constant node to layered texture
            colorConstantName = cmds.shadingNode("colorConstant",
                                                 asUtility=True, name="_".join([self.shaderName, "AOConstant"]))
            for col in ["R", "G", "B"]:  # connect to the color constant as layered texture needs a color not scalar.
                cmds.connectAttr("{}.outColorR".format(textureInst.name()),
                                 "{}.inColor.inColor{}".format(colorConstantName, col))
            cmds.connectAttr("{}.outColor".format(colorConstantName),
                             "{}.inputs[1].color".format(layeredTexture))  # connect color constant to layered texture
            cmds.setAttr("{}.inputs[1].blendMode".format(layeredTexture), 6)
        # Roughness ------------------------
        cmds.connectAttr("{}.outColorG".format(textureInst.name()),
                         ".".join([self.shaderName, self.shaderInst.specularRoughnessAttr]))
        # Metalness ------------------------
        cmds.connectAttr("{}.outColorB".format(textureInst.name()),
                         ".".join([self.shaderName, self.shaderInst.metalnessAttr]))
        return textureInst

    def layeredTexture(self, nameType, masterAttr, scalar=False):
        """Creates a layered texture and plugs it into the masterAttr

        :param nameType:
        :type nameType: str
        :param masterAttr:
        :type masterAttr: str
        :param scalar:
        :type scalar: bool
        :return:
        :rtype: str
        """
        layeredTextureName = cmds.shadingNode("layeredTexture",
                                              asUtility=True, name="_".join([self.shaderName, "layer", nameType]))
        outAttr = "outColor"
        if scalar:
            outAttr = "outAlpha"
        cmds.connectAttr(".".join([layeredTextureName, outAttr]),
                         ".".join([self.shaderName, masterAttr]))
        return layeredTextureName


def prepDirectory(directory, imageFilters, preset=PRESET_POLY_HAVEN, shaderType="standardSurface", message=True):
    """Generates all the shader instance and shader name from a single directory.

    :param directory:
    :type directory:
    :param imageFilters:
    :type imageFilters:
    :param preset:
    :type preset:
    :param shaderType:
    :type shaderType:
    :param message:
    :type message:
    :return:
    :rtype:
    """
    files = next(os.walk(directory), (None, None, []))[2]  # [] if no file
    files = [file for file in files if file.endswith(imageFilters)]
    if not files:
        if message:
            pass
            # output.displayWarning("No files found in directory `{}`".format(directory))
        return (None, "")  # Failed and warnings already given
    shaderBuilderInst = ShaderTextureBuilder()
    shaderBuilderInst.setShaderType(shaderType)
    shaderBuilderInst.setPreset(preset)  # likely will change
    if not shaderBuilderInst.processFiles(files, directory):
        return (None, "")  # Failed and warnings already given
    shaderName = shaderBuilderInst.shaderName
    return shaderBuilderInst, shaderName


def buildShaderAndTextures(directory, preset=PRESET_POLY_HAVEN, shaderType="standardSurface",
                           imageFilters=IMAGE_EXTS, diffuseColor=(0.5, 0.5, 0.5), combineNormalBump=True,
                           includeAO=True, includeArm=True, message=True):
    shaderBuilderInst, shaderName = prepDirectory(directory, imageFilters, preset=preset,
                                                  shaderType=shaderType, message=message)
    if not shaderBuilderInst:
        output.displayInfo("No shader could be built from `{}`".format(directory))
        return (None, "")
    # Passed so build the shader -----------------------
    shaderInst = shadermulti.createShaderInstanceType(shaderType, shaderName=shaderName)
    shaderBuilderInst.setShaderInstance(shaderInst)
    # Build the textures -----------------------
    shaderBuilderInst.buildShaders(diffuseColor=diffuseColor, combineNormalBump=combineNormalBump, includeAO=includeAO,
                                   includeArm=includeArm)
    if message:
        output.displayInfo("Success: Shader `{}` created with textures".format(shaderName))
    return shaderBuilderInst, shaderName


def generateSubdirectories(directory, directoryCountLimit=2001, message=True):
    """Returns a list of subdirectories including the root directory too.  Empty list if directory not found.

    :param directory: The root directory to search from
    :type directory: str
    :param message: Report a message to the user?
    :type message: bool
    :return directories: a list of subdirectories including the root directory too.
    :rtype directories: list(str)
    """
    count = 0
    directories = []
    if not directory:
        if message:
            output.displayWarning("No directory given. Please enter a path to a directory.")
        return []
    if not os.path.isdir(directory):
        if message:
            output.displayWarning("The directory does not exist. ``".format(directory))
        return []
    for dctry, dirs, files in os.walk(directory):
        for subdir in dirs:
            count += 1
            directories.append(os.path.join(dctry, subdir))
            if count > directoryCountLimit:
                return directories
    directories.append(directory)
    return directories


def previewShaders(directory, preset=PRESET_POLY_HAVEN, shaderType="standardSurface", imageFilters=IMAGE_EXTS,
                   message=True):
    """Generates a list of shaders that will be created from the current directory.

    :param directory:
    :type directory: str
    :param preset:
    :type preset: str
    :param shaderType:
    :type shaderType: str
    :param imageFilters:
    :type imageFilters: list(str)
    :param message:
    :type message: bool
    :return shaderList: A list of shaders that will be created from the directory if they are to be built.
    :rtype shaderList: list(str)
    """
    shaderList = list()
    directoryCountLimit = 2000
    directories = generateSubdirectories(directory, directoryCountLimit=directoryCountLimit, message=True)
    if len(directories) > directoryCountLimit - 1:
        output.displayWarning("This folder contains more than 2000 sub-directories and is too large")
        return list()
    if not directories:  # messages given
        return list()
    for dir in directories:
        shaderBuilderInst, shaderName = prepDirectory(dir, imageFilters, preset=preset,
                                                      shaderType=shaderType, message=message)
        if not shaderName:
            continue
        shaderList.append(shaderName)
    if shaderList:
        shaderCount = len(shaderList)
        output.displayInfo("{} shaders will be built under "
                           "the current directory. {}".format(str(shaderCount), shaderList))
    else:
        output.displayInfo("No shaders were found from textures under the current directory".format(directory))
    return shaderList


def buildShadersTextures(directory, preset=PRESET_POLY_HAVEN, shaderType="standardSurface",
                         imageFilters=IMAGE_EXTS, diffuseColor=(0.5, 0.5, 0.5), combineNormalBump=True, includeAO=True,
                         includeArm=True, message=True):
    """Main function that builds shaders from a given directory, walks sub directories and can build many shaders.

    :param directory:
    :type directory:
    :param preset:
    :type preset:
    :param shaderType:
    :type shaderType:
    :param imageFilters:
    :type imageFilters:
    :param diffuseColor:
    :type diffuseColor:
    :param combineNormalBump:
    :type combineNormalBump:
    :param includeAO:
    :type includeAO:
    :param includeArm:
    :type includeArm:
    :param message:
    :type message:
    :return:
    :rtype:
    """
    shaderList = list()
    directoryCountLimit = 2000
    directories = generateSubdirectories(directory, directoryCountLimit=2000, message=True)
    if not directories:  # messages given
        return
    if len(directories) > directoryCountLimit - 1:
        output.displayWarning("This folder contains more than 2000 sub-directories and is too large")
        return list()
    for dir in directories:
        if message:
            output.displayInfo("Building shader from directory: {}".format(dir))
        shaderBuilderInst, shaderName = buildShaderAndTextures(dir, preset=preset, shaderType=shaderType,
                                                               imageFilters=imageFilters, diffuseColor=diffuseColor,
                                                               combineNormalBump=combineNormalBump, includeAO=includeAO,
                                                               includeArm=includeArm, message=message)
        if shaderName:
            shaderList.append(shaderName)

    shaderCount = len(shaderList)
    if shaderCount:
        output.displayInfo("Success: {} shaders have been created: {}".format(str(shaderCount), shaderList))
    else:
        output.displayWarning("No shaders have been created. Could no build shaders from: {}".format(directory))
