"""Converts shaders from one type to another.

New style shader code uses zoo's shader instances.

from zoo.libs.maya.cmds.shaders import convertshaders
convertshaders.convertShaderSelection(convertToShaderType="standardSurface", reassign=True, message=True)

convertshaders.swatchColorsToNewRenderSpaceScene()

"""
import os

from maya import cmds

from zoo.libs.utils import output

from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.shaders import shdmultconstants as shdm
from zoo.libs.maya.cmds.shaders import shaderutils, shadermulti
from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERER_PLUGIN
from zoo.libs.maya.cmds.shaders.shdmultconstants import SHADERTYPE_SUFFIX_DICT, RENDERER_SHADERS_DICT, MAYA
from zoo.libs.maya.utils import mayacolors
from zoo.libs.maya.utils import mayaenv

MAYA_VERSION = mayaenv.mayaVersion()  # whole numbers (int) 2020 etc:

# -------------------
# CORRECT SHADERS
# -------------------


def boolWeightAttr(weight, color):
    """While converting, the final shader may miss a weight attribute, so before setting force the color to have \
    the weight factored into it already. So force the weight to be either one or zero.

    :param weight: The weight attribute in a shader pair (weight/color)
    :type weight: float
    :param color: The color attribute in a shader pair (weight/color)
    :type color: list(float)

    :return weight: The resulting weight attribute in a shader pair (weight/color)
    :rtype weight: float
    :return color: The resulting color attribute in a shader pair (weight/color)
    :rtype color: list(float)
    """
    if weight == 0.0:  # set all emission to zero
        color = [0.0, 0.0, 0.0]
    else:  # multiply color by the weight and set weight to one
        color = [color[0] * weight,
                 color[1] * weight,
                 color[2] * weight]
        weight = 1.0
    return weight, color


def correctMissingWeight(color):
    """Shaders that are getting converted may be missing a weight attribute, so set it to be 1.0 if color or 0.0 if not

    :param color: The color attribute in a shader pair (weight/color)
    :type color: list(float)

    :return weight: The resulting weight attribute in a shader pair (weight/color)
    :rtype weight: float
    """
    if color == [0.0, 0.0, 0.0]:
        return 0.0
    else:
        return 1.0


def correctShaderPairAttr(attrDict, weightKey, colorKey):
    """While converting, shaders commonly are missing a weight attribute.
    Eg. diffuseColor and diffuseWeight, the diffuseWeight attribute may be missing.

    While converting either:

        1. The existing shader is missing a weight attr
        2. The destination (newly converted) shader is missing a weight attr

    The function corrects both by setting the existing weight value to be either 1.0 or 0.0.

    It also corrects color values if weight is set to a number in between zero and one.
    Eg. weight is 0.34 so adjusts the color accordingly and sets the weight to one.

    :param attrDict: A shader dictionary of values generic shader keys with values as per shdm
    :type attrDict: dict(str)
    :param weightKey: The dictionary key of the weight eg. "gDiffuseWeight"
    :type weightKey: str
    :param colorKey: The dictionary key of the color eg. gDiffuseColor_srgb
    :type colorKey: str

    :return attrDict: The corrected shader dictionary of values generic shader keys with values as per shdm
    :rtype attrDict: dict(str)
    """
    if weightKey in attrDict.keys() and colorKey in attrDict.keys():  # set emission weight 1.0 or 0.0
        attrDict[weightKey], attrDict[colorKey] = boolWeightAttr(attrDict[weightKey],
                                                                 attrDict[colorKey])
    else:
        if colorKey in attrDict.keys():  # then no weight so set it to be 0.0 if no color or 1.0 if color
            attrDict[weightKey] = correctMissingWeight(attrDict[colorKey])
    return attrDict


def correctAttrs(attrDict, fromShaderInst, newShaderInst):
    """Corrects shader pairs ready for applying the converted values. See correctShaderPairAttr() for more info.

    :param attrDict: A shader dictionary of values generic shader keys with values as per shdm
    :type attrDict: dict(str)
    :param fromShaderInst: The shader instance that is being converted
    :type fromShaderInst: shaderbase.ShaderBase
    :param newShaderInst: The newly created shader instance
    :type newShaderInst: shaderbase.ShaderBase

    :return attrDict: The corrected shader dictionary of values generic shader keys with values as per shdm
    :rtype attrDict: dict(str)
    """
    # Diffuse & Diffuse Weight ---------------------
    if not fromShaderInst.diffuseWeightAttr or not newShaderInst.diffuseColorAttr:  # then bool weight to 1.0 or 0.0
        attrDict = correctShaderPairAttr(attrDict, shdm.DIFFUSEWEIGHT, shdm.DIFFUSE)

    # Specular & Specular Weight ---------------------
    if not fromShaderInst.specularWeightAttr or not newShaderInst.specularColorAttr:  # then bool weight to 1.0 or 0.0
        attrDict = correctShaderPairAttr(attrDict, shdm.SPECWEIGHT, shdm.SPECCOLOR)

    # Coat & Coat Weight ---------------------
    # skip coat as weirdness if color is not bright, for arnold and surface standard in viewport
    # if not fromShaderInst.coatWeightAttr or not newShaderInst.coatcolorAttr:  # then bool weight to 1.0 or 0.0
    # attrDict = correctShaderPairAttr(attrDict, shdm.COATWEIGHT, shdm.COATCOLOR)

    # Emission & Emission Weight ---------------------
    if not fromShaderInst.emissionWeightAttr or not newShaderInst.emissionWeightAttr:  # then bool weight to 1.0 or 0.0
        attrDict = correctShaderPairAttr(attrDict, shdm.EMISSIONWEIGHT, shdm.EMISSION)

    return attrDict


def selectedShaders(message=True):
    """returns selected shaders in the scene as shader instances. None if None found

    :param message: report a message to the user
    :type message: bool
    :return shaders: A list of shader names
    :rtype shaders: list(str)
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if message:
            output.displayWarning("No shaders have been selected, please select shaders.")
        return []
    shaders = shaderutils.getShadersSelected()
    if not shaders:
        if message:
            output.displayWarning("No shaders were found in the selected objects.")
        return []
    return shaders


# -------------------
# CONVERT SHADERS
# -------------------


def convertShader(shaderName, convertToShaderType="standardSurface", reassign=True, removeShaders=False,
                  maintainConnections=True, message=True):
    """Converts a shader to a new shader type, supports attributes and not textures atm.

    Supports shdm.SHADER_TYPE_LIST:

        "standardSurface" "lambert", "blinn", "phong", "phongE", "aiStandardSurface",
        "VRayMtl", "RedshiftMaterial", "PxrSurface"

    :param shaderName: The name of the shader to convert
    :type shaderName: str
    :param convertToShaderType: The new shader type eg "aiStandardSurface" see shdm.SHADERTYPE_SUFFIX_DICT
    :type convertToShaderType: str
    :param reassign: Reassign the shader assignments to geometry after creating?
    :type reassign: bool
    :param removeShaders: Delete the previous shaders after converting?
    :type removeShaders: bool
    :param maintainConnections: Maintains any previous connections, copy pastes old textures into new shader.
    :type maintainConnections: bool
    :param message: Report a message to the user?
    :type message: bool
    :return shaderInstance: A zoo shader instance of the newly created shader
    :rtype shaderInstance: shaderbase.ShaderBase
    """
    connectionDict = dict()
    # Create Instance of the "from" shader ------------------------------------------------------
    fromShaderInst = shadermulti.shaderInstanceFromShader(shaderName)
    if fromShaderInst is None:
        if message:
            output.displayWarning("Shader type `{}` could not be converted, "
                                  "it is not supported".format(convertToShaderType))
        return None

    if fromShaderInst.nodetype == convertToShaderType:
        if message:
            output.displayWarning("Shader type `{}` is already correct".format(convertToShaderType))
        return fromShaderInst

    if maintainConnections:  # Copies textures from the old shader
        connectionDict = fromShaderInst.connectedAttrs()

    # Shader To Instance ------------------------------------------------------
    shaderName = fromShaderInst.shaderName()
    shadNoSuffix = shadermulti.removeShaderSuffix(shaderName)
    suffix = shdm.SHADERTYPE_SUFFIX_DICT[convertToShaderType]

    # Create New Instance ----------------------------------------------------
    newShaderInst = shadermulti.createShaderInstanceType(convertToShaderType,
                                                         shaderName="_".join([shadNoSuffix, suffix]))
    if newShaderInst is None:
        if message:
            output.displayWarning("Shader type `{}` could not be created".format(convertToShaderType))
        return None

    # Get attributes from existing shader ------------------------------------------------------
    attrDict = fromShaderInst.shaderValues(removeNone=True)

    # Fix potentially missing dict values -----------------------------------------------------
    attrDict = correctAttrs(attrDict, fromShaderInst, newShaderInst)

    # Set attributes on new shader ------------------------------------------------------
    newShaderInst.setFromDict(attrDict, apply=True)

    if maintainConnections:  # Pastes textures from the old shader back to the new
        newShaderInst.connectAttrs(connectionDict, message=False)

    # Reassign New Shader to Geo ------------------------------------------------------
    if reassign:
        geo = shaderutils.getObjectsFacesAssignedToShader(fromShaderInst.shaderName(), longName=True)
        if geo is not None:
            shaderutils.assignShader(geo, newShaderInst.shaderName())

    # Delete original shader -------------------------------
    if removeShaders:
        fromShaderInst.deleteShader()

    # Message ------------------------------------------------------
    if message:
        output.displayInfo("Shader `{}` has been converted to `{}`".format(fromShaderInst.shaderName(),
                                                                           newShaderInst.shaderName()))
    return newShaderInst


def convertShaderList(shaderList, convertToShaderType="standardSurface", reassign=True, removeShaders=False,
                      maintainConnections=True, message=True):
    """Converts a shader list to a new shader type, supports attributes and not textures atm.

    Supports shdm.SHADER_TYPE_LIST:

        "standardSurface" "lambert", "blinn", "phong", "phongE", "aiStandardSurface",
        "VRayMtl", "RedshiftMaterial", "PxrSurface"

    :param shaderList: A list of maya shader names
    :type shaderList: list(str)
    :param convertToShaderType: The new shader type eg "aiStandardSurface" see shdm.SHADERTYPE_SUFFIX_DICT
    :type convertToShaderType: str
    :param reassign: Reassign the shader assignments to geometry after creating?
    :type reassign: bool
    :param removeShaders: Delete the previous shaders after converting?
    :type removeShaders: bool
    :param maintainConnections: Maintains any previous connections, copy pastes old textures into new shader.
    :type maintainConnections: bool
    :param message: Report a message to the user?
    :type message: bool
    :return shaderInstances: A list of zoo shader instance of the newly created shader
    :rtype shaderInstances: list(shaderbase.ShaderBase)
    """
    shaderInstances = list()
    for shader in shaderList:
        shaderInst = convertShader(shader, convertToShaderType=convertToShaderType, reassign=reassign,
                                   removeShaders=removeShaders, maintainConnections=maintainConnections,
                                   message=message)
        if shaderInst:
            shaderInstances.append(shaderInst)
    return shaderInstances


def convertShaderSelection(convertToShaderType="standardSurface", reassign=True, removeShaders=False,
                           maintainConnections=True, message=True):
    """Converts a selected shaders or objects to a new shader type, supports attributes and no textures atm.

    Supports shdm.SHADER_TYPE_LIST:

        "standardSurface" "lambert", "blinn", "phong", "phongE", "aiStandardSurface",
        "VRayMtl", "RedshiftMaterial", "PxrSurface"

    :param convertToShaderType: The new shader type eg "aiStandardSurface" see shdm.SHADERTYPE_SUFFIX_DICT
    :type convertToShaderType: str
    :param reassign: Reassign the shader assignments to geometry after creating?
    :type reassign: bool
    :param removeShaders: Delete the previous shaders after converting?
    :type removeShaders: bool
    :param maintainConnections: Maintains any previous connections, copy pastes old textures into new shader.
    :type maintainConnections: bool
    :param message: Report a message to the user?
    :type message: bool
    :return shaderInstances: A list of zoo shader instance of the newly created shader
    :rtype shaderInstances: list(shaderbase.ShaderBase)
    """
    shaders = selectedShaders(message=message)
    if not shaders:
        return None

    shadInsts = convertShaderList(shaders, convertToShaderType=convertToShaderType, reassign=reassign,
                                  removeShaders=removeShaders, maintainConnections=maintainConnections, message=False)
    if message and shadInsts:
        shaderNames = list()
        for inst in shadInsts:
            shaderNames.append(inst.shaderName())
        output.displayInfo("Shaders successfully converted: {}".format(shaderNames))
    elif message and not shadInsts:
        output.displayWarning("No shaders were converted.")
    return shadInsts


def convertShaderScene(convertToShaderType="standardSurface", reassign=True, removeShaders=False,
                       maintainConnections=True, assignedShadersOnly=True, message=True):
    """Converts all shaders in the scene to a new shader type, supports attributes and no textures atm.

    If shaders are found who's shader type is not supported then the shader will be ignored.

    Supports shdm.SHADER_TYPE_LIST:

        "standardSurface" "lambert", "blinn", "phong", "phongE", "aiStandardSurface",
        "VRayMtl", "RedshiftMaterial", "PxrSurface"

    :param convertToShaderType: The new shader type eg "aiStandardSurface" see shdm.SHADERTYPE_SUFFIX_DICT
    :type convertToShaderType: str
    :param reassign: Reassign the shader assignments to geometry after creating?
    :type reassign: bool
    :param removeShaders: Delete the previous shaders after converting?
    :type removeShaders: bool
    :param maintainConnections: Maintains any previous connections, copy pastes old textures into new shader.
    :type maintainConnections: bool
    :param assignedShadersOnly: Only converts shaders that are assigned to geo
    :type assignedShadersOnly: bool
    :param message: Report a message to the user?
    :type message: bool

    :return shaderInstances: A list of zoo shader instance of the newly created shader
    :rtype shaderInstances: list(shaderbase.ShaderBase)
    """
    allShaders = shaderutils.getAllShaders()

    if assignedShadersOnly:  # Only use shaders with geo assignments
        assignedShaders = list()
        for shader in allShaders:
            if shaderutils.getObjectsFacesAssignedToShader(shader, longName=True):
                assignedShaders.append(shader)
        allShaders = assignedShaders

    # Convert the shaders --------------------------------
    return convertShaderList(allShaders,
                             convertToShaderType=convertToShaderType,
                             reassign=reassign,
                             removeShaders=removeShaders,
                             maintainConnections=maintainConnections,
                             message=message)


# -------------------
# CONVERT SHADERS OPEN & SAVE SCENE
# -------------------


def convertShaderSaveScene(fileName, convertToShaderType, removeShaders=False, maintainConnections=True, message=True):
    """Saves the current file to a full path filename and converts all shaders in the scene.

    Any shaders that cannot be converted are ignored.

    Supports shdm.SHADER_TYPE_LIST:

        "standardSurface" "lambert", "blinn", "phong", "phongE", "aiStandardSurface",
        "VRayMtl", "RedshiftMaterial", "PxrSurface"

    :param fileName: The full path filename to save
    :type fileName: str
    :param shaderType: The new shader to convert to type eg "aiStandardSurface" see shdm.SHADERTYPE_SUFFIX_DICT
    :type shaderType: str
    :param removeShaders: Remove the old shaders from the saved file?
    :type removeShaders: bool
    :param maintainConnections: Maintains any previous connections, copy pastes old textures into new shader.
    :type maintainConnections: bool
    :param message: Report a message to the user
    :type message: bool
    """
    print("Converting Shaders")
    renderer = shdm.SHADERTYPE_RENDERER[convertToShaderType]
    if renderer != MAYA:
        cmds.loadPlugin(RENDERER_PLUGIN[renderer])
    shadInsts = convertShaderScene(convertToShaderType=convertToShaderType,
                                   reassign=True,
                                   removeShaders=removeShaders,
                                   maintainConnections=maintainConnections,
                                   message=message)
    # Save the new file -----------------------
    print("Saving: {}".format(fileName))
    cmds.file(rename=fileName)
    cmds.file(save=True, type='mayaAscii', force=True)

    # Report message ---------------
    if message:
        convertedShaders = list()
        for inst in shadInsts:
            convertedShaders.append(inst.shaderName())
        output.displayInfo('Success: Shaders Converted "{}"'.format(convertedShaders))
        output.displayInfo('Success: File Saved "{}"'.format(fileName))


def openConvertFileSave(openPath, shaderType, oldRenderer="Maya", removeShaders=False, maintainConnections=True,
                        useRendererSuffix=True, message=True):
    """Opens an existing file and saves out a new file with new shaders.

        - c:\APath\someFile_STRD.ma
        - c:\APath\someFile_arnold.ma

    Supports shdm.SHADER_TYPE_LIST:

        "standardSurface" "lambert", "blinn", "phong", "phongE", "aiStandardSurface",
        "VRayMtl", "RedshiftMaterial", "PxrSurface"

    :param openPath: The path of the file to open and convert
    :type openPath: str
    :param shaderType: The new shader type to convert to eg "aiStandardSurface" see shdm.SHADERTYPE_SUFFIX_DICT
    :type shaderType: str
    :param oldRenderer: Usually "Maya" removed the suffix from the name while saving.
    :type oldRenderer: str
    :param removeShaders: Remove the old shaders from the saved file?
    :type removeShaders: bool
    :param maintainConnections: Maintains any previous connections, copy pastes old textures into new shader.
    :type maintainConnections: bool
    :param useRendererSuffix: Save the file with the renderer suffix lowercase "_arnold" or use the shader "_ARN"
    :type useRendererSuffix: bool
    :param message: Report a message to the user
    :type message: bool
    """
    # Open the file ----------------------------
    cmds.file(openPath, open=True, force=True)
    print("File Opened: {}".format(openPath))
    # get the renderer and split the file name apart -------------------
    renderer = shdm.SHADERTYPE_RENDERER[shaderType]
    directoryPath = os.path.dirname(openPath)
    fileName = os.path.basename(openPath)
    name, ext = os.path.splitext(fileName)

    # Remove any potential suffix from the name -----------------
    shaderTypes = RENDERER_SHADERS_DICT[oldRenderer]
    for type in shaderTypes:
        shaderSuffix = SHADERTYPE_SUFFIX_DICT[type]
        name = namehandling.stripSuffixExact(name, shaderSuffix)
    name = namehandling.stripSuffixExact(name, renderer)
    name = namehandling.stripSuffixExact(name, renderer.lower())

    # Create the new name -----------------------
    if useRendererSuffix:
        newName = "_".join([name, renderer.lower()])
    else:  # Use a shader suffix instead of renderer name
        newName = "_".join([name, SHADERTYPE_SUFFIX_DICT[shaderType]])
    newSavePath = os.path.join(directoryPath, "".join([newName, ext]))
    print("New Save Path: ", newSavePath)

    # Convert and save the new scene -----------------------
    convertShaderSaveScene(newSavePath,
                           shaderType,
                           removeShaders=removeShaders,
                           maintainConnections=maintainConnections,
                           message=message)


# -------------------
# CONVERT RENDERING SPACE SHADERS
# -------------------


def swatchColorsToNewRenderSpace(shaderName, originalRenderSpace="scene-linear Rec.709-sRGB", message=True):
    """Upgrades swatch colors for a single shader from the originalRenderSpace to the scene current space.

    Used to upgrade scenes from old linear space in 2020 to new ACES color space.

    Affects supported zoo shaders only.

    Upgrades attributes

        - diffuse color
        - specular color
        - coat color
        - emission color

    Default Rendering Spaces:

        - scene-linear Rec.709-sRGB
        - ACEScg
        - ACES2065-1
        - scene-linear DCI-P3 D65
        - Rec.2020

    :param shaderName: Then name of the shader to upgrade/convert swatch colors
    :type shaderName: str
    :param originalSpace: The original color space usually "linear"
    :type originalSpace: str
    :param message: Report a message to the user?
    :type message: bool
    :return success: True if successfully converted
    :rtype success: False
    """
    currentRenderSpace = cmds.colorManagementPrefs(query=True, renderingSpaceName=True)

    if originalRenderSpace == currentRenderSpace:
        if message:
            output.displayWarning("The render color space is already set to `{}`".format(originalRenderSpace))
        return "break"

    # Create Instance of the "from" shader ------------------------------------------------------
    shaderInst = shadermulti.shaderInstanceFromShader(shaderName)
    if shaderInst is None:
        if message:
            output.displayWarning("Shader `{}` could not be matched, "
                                  "it is not supported".format(shaderName))
        return False

    # set to original space to copy display colors
    cmds.colorManagementPrefs(edit=True, renderingSpaceName=originalRenderSpace)

    # Record colors in display space ---------------------
    diffuseDisplayColor = shaderInst.diffuseDisplay()
    specDisplayColor = shaderInst.specColorDisplay()
    coatDisplayColor = shaderInst.coatColorDisplay()
    emissionDisplayColor = shaderInst.emissionDisplay()

    cmds.colorManagementPrefs(edit=True, renderingSpaceName=currentRenderSpace)  # set back to current rendering space

    # Now convert the old display colors to new rendering space and set colors in rendering space
    if diffuseDisplayColor:
        shaderInst.setDiffuse(mayacolors.displayColorToCurrentRenderingSpace(diffuseDisplayColor))
    if specDisplayColor:
        shaderInst.setSpecColor(mayacolors.displayColorToCurrentRenderingSpace(specDisplayColor))
    if coatDisplayColor:
        shaderInst.setCoatColor(mayacolors.displayColorToCurrentRenderingSpace(coatDisplayColor))
    if emissionDisplayColor:
        shaderInst.setEmission(mayacolors.displayColorToCurrentRenderingSpace(emissionDisplayColor))

    # Message ------------------------------------------------------
    if message:
        output.displayInfo("Shader `{}` attributes have been matched to the current rendering "
                           "space.".format(shaderInst.shaderName()))
    return True


def swatchColorsToNewRenderSpaceScene(originalRenderSpace="scene-linear Rec.709-sRGB", message=True):
    """Upgrades swatch colors for all shaders in the scene from the originalRenderSpace to the scene current space.

    Affects supported zoo shaders only.

    Upgrades attributes

        - diffuse color
        - specular color
        - coat color
        - emission color

    :param message: Report messages to the user
    :type message: bool
    """
    if MAYA_VERSION < 2023:  # then just return the linear color of the display srgb color
        output.displayWarning("Swatch Color Conversion only supports Maya 2023 and above.")
        return

    allShaders = shaderutils.getAllShaders()

    if not allShaders:
        output.displayWarning("No shaders found in scene")
        return

    for shader in allShaders:
        status = swatchColorsToNewRenderSpace(shader,
                                              originalRenderSpace=originalRenderSpace,
                                              message=message)
        if status == "break":  # break in case renderer match
            return

    if message:
        output.displayInfo("Shaders upgraded, see the Script Editor for full details")


def swatchColorsToNewRenderSpaceSel(originalRenderSpace="scene-linear Rec.709-sRGB", message=True):
    """Upgrades swatch colors for selected shaders usually from the originalRenderSpace to the scene current space.

    Affects supported zoo shaders only.

    Upgrades attributes

        - diffuse color
        - specular color
        - coat color
        - emission color

    :param message: Report messages to the user
    :type message: bool
    """
    if MAYA_VERSION < 2023:  # then just return the linear color of the display srgb color
        output.displayWarning("Swatch Color Conversion only supports Maya 2023 and above.")
        return

    shaders = selectedShaders(message=message)
    if not shaders:
        return None

    for shader in shaders:
        status = swatchColorsToNewRenderSpace(shader,
                                              originalRenderSpace=originalRenderSpace,
                                              message=message)
        if status == "break":  # break in case renderer match
            return

    if message:
        output.displayInfo("Shaders upgraded, see the Script Editor for full details")
