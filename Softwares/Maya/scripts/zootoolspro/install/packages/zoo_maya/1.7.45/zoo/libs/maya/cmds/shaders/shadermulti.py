"""The new shadermultirenderer, will take over from shader multi renderer

Use this module to access shaders without knowing their renderer or shader type.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.shaders import shadermulti
    shaderInstances = shadermulti.shaderInstancesFromSelected()

    from zoo.libs.maya.cmds.shaders import shadermulti
    shaderInstances = shadermulti.shaderInstanceFromShader("shaderName")

Author: Andrew Silke
"""
from maya import cmds

from zoo.libs.utils import output

from zoo.libs.maya.utils import mayaenv

from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.renderer import multirenderersettings
from zoo.libs.maya.cmds.shaders import shaderutils
from zoo.libs.maya.cmds.shaders import shdmultconstants as shdcn
from zoo.libs.maya.cmds.shaders.shadertypes import arnoldstandardsurface, mayablinn, mayalambert, \
    mayastandardsurface, redshiftredshiftmaterial, rendermanpxrsurface, rendermanpxrlayersurface, mayaphong, \
    mayaphonge, vraymtl, shaderbase

MAYA_VERSION = mayaenv.mayaVersion()  # whole numbers (int) 2020 etc

RENDERMAN = shdcn.RENDERMAN
REDSHIFT = shdcn.REDSHIFT
ARNOLD = shdcn.ARNOLD
MAYA = shdcn.MAYA
VRAY = shdcn.VRAY


def removeShaderSuffix(shaderName):
    """removes a shader suffix of a shadername.
    Iterates through suffixes in the dictionary shdcn.SHADERTYPE_SUFFIX_DICT
    Does not rename an object, just a string operation.

    Supports suffixes in shdcn.SHADERTYPE_SUFFIX_DICT

    :param shaderName: The name of a shader
    :type shaderName: str
    :return shaderNoSuffix: The name with the suffix potentially removed
    :rtype shaderNoSuffix: str
    """
    shaderNoSuffix = str(shaderName)
    suffixDict = shdcn.SHADERTYPE_SUFFIX_DICT
    for shaderType in suffixDict:
        shaderNoSuffix = namehandling.stripSuffixExact(shaderNoSuffix, suffixDict[shaderType], seperator="_")
    return shaderNoSuffix


# -------------------
# CREATE LOAD SHADER INSTANCES
# -------------------


def emptyInstance(shaderName=""):
    """Creates an empty shader instance for use when no shader is selected"""
    return shaderbase.ShaderBase(shaderName, node=None, genAttrDict=None, create=False, ingest=True)  # no instance


def shaderInstance(shaderType, shaderName="", create=False, ingest=True, suffixName=False):
    """Creates or ingests (loads) a shader instance of a specific shader type.

    Supports shdcn.SHADER_TYPE_LIST:

        "standardSurface" "lambert", "blinn", "phong", "phongE", "aiStandardSurface",
        "VRayMtl", "RedshiftMaterial", "PxrSurface"

    :param shaderType: The type of shader to create eg "aiStandardSurface" see shdcn.SHADERTYPE_SUFFIX_DICT
    :type shaderType: str
    :param shaderName: The name of the shader to create
    :type shaderName: str
    :param suffixName: Add an autosuffix for the shader name?  Example shader_STRD
    :type suffixName: bool
    :param create: True if creating a new shader, False if using an existing shader
    :type create: bool
    :param ingest: False if creating a new shader, True if using an existing shader
    :type ingest: bool

    :return shaderInstance: A zoo shader instance of the specified shader
    :rtype shaderInstance: :class:`shaderbase.ShaderBase`
    """
    if shaderType == mayastandardsurface.NODE_TYPE:
        return mayastandardsurface.StandardSurface(shaderName=shaderName, create=create, ingest=ingest,
                                                   suffixName=suffixName)
    elif shaderType == arnoldstandardsurface.NODE_TYPE:
        return arnoldstandardsurface.AiStandardSurface(shaderName=shaderName, create=create, ingest=ingest,
                                                       suffixName=suffixName)
    elif shaderType == redshiftredshiftmaterial.NODE_TYPE:
        return redshiftredshiftmaterial.RedshiftMaterial(shaderName=shaderName, create=create, ingest=ingest,
                                                         suffixName=suffixName)
    elif shaderType == rendermanpxrsurface.NODE_TYPE:
        return rendermanpxrsurface.PxrSurface(shaderName=shaderName, create=create, ingest=ingest,
                                              suffixName=suffixName)
    elif shaderType == vraymtl.NODE_TYPE:
        return vraymtl.VRayMtl(shaderName=shaderName, create=create, ingest=ingest,
                               suffixName=suffixName)
    elif shaderType == mayalambert.NODE_TYPE:
        return mayalambert.Lambert(shaderName=shaderName, create=create, ingest=ingest,
                                   suffixName=suffixName)
    elif shaderType == mayablinn.NODE_TYPE:
        return mayablinn.Blinn(shaderName=shaderName, create=create, ingest=ingest,
                               suffixName=suffixName)
    elif shaderType == mayaphong.NODE_TYPE:
        return mayaphong.Phong(shaderName=shaderName, create=create, ingest=ingest,
                               suffixName=suffixName)
    elif shaderType == mayaphonge.NODE_TYPE:
        return mayaphonge.PhongE(shaderName=shaderName, create=create, ingest=ingest,
                                 suffixName=suffixName)
    else:
        return shaderbase.ShaderBase(shaderName, node=None, genAttrDict=None, create=False, ingest=True,
                                     suffixName=suffixName)  # no instance


def shaderInstanceFromShader(shaderName, suffixName=False):
    """Loads a shader instance from an existing shader.  Auto detects the shader type.

    Supports shdcn.SHADER_TYPE_LIST:

        "standardSurface" "lambert", "blinn", "phong", "phongE", "aiStandardSurface",
        "VRayMtl", "RedshiftMaterial", "PxrSurface"

    if no shader exists then returns None

    :param shaderName: The name of the shader
    :type shaderName: str
    :param suffixName: Add an autosuffix for the shader name?  Example shader_STRD
    :type suffixName: bool
    :return shaderInstance: A zoo shader instance of the specified shader, None if the shader does not exist
    :rtype shaderInstance: :class:`shaderbase.ShaderBase`
    """
    if not cmds.objExists(shaderName):
        return None
    shaderType = cmds.nodeType(shaderName)
    return shaderInstance(shaderType, shaderName=shaderName, create=False, ingest=True, suffixName=suffixName)


# ------------------------
# Create Shaders
# ------------------------


def createShaderInstanceType(shaderType, shaderName="", suffixName=False):
    """Creates a new shader of shader type with a shader name and returns the shader instance.

    :param shaderType: The type of shader to create eg "aiStandardSurface" see shdcn.SHADERTYPE_SUFFIX_DICT
    :type shaderType: str
    :param shaderName: The name of the shader
    :type shaderName: str
    :param suffixName: Add an autosuffix for the shader name?  Example shader_STRD
    :type suffixName: bool

    :return shaderInstance: A zoo shader instance of the specified shader
    :rtype shaderInstance: :class:`shaderbase.ShaderBase`
    """
    return shaderInstance(shaderType, shaderName=shaderName, create=True, ingest=False, suffixName=suffixName)


def createAssignShdInstType(shaderType, shaderName="", suffixName=False):
    """Creates and assigns a new shader to sel geo.  From shader type with a shader name and returns a shader instance.

    :param shaderType: The type of shader to create eg "aiStandardSurface" see shdcn.SHADERTYPE_SUFFIX_DICT
    :type shaderType: str
    :param shaderName: The optional name of the shader
    :type shaderName: str
    :param suffixName: Add an autosuffix for the shader name?  Example shader_STRD
    :type suffixName: bool

    :return shaderInstance: A zoo shader instance of the specified shader
    :rtype shaderInstance: :class:`shaderbase.ShaderBase`
    """
    selObjs = cmds.ls(selection=True)
    shaderInstance = createShaderInstanceType(shaderType, shaderName=shaderName, suffixName=suffixName)
    if selObjs:
        shaderutils.assignShader(selObjs, shaderInstance.shaderName())
    return shaderInstance


def createDefaultShadRenderer(renderer, shaderName="", suffixName=False, assignGeo=True, message=False):
    """Creates a default shader of the current renderer type

    :param renderer: The render nice name "Arnold" "Redshift" etc.
    :type renderer: str
    :param shaderName: The name of the shader, if "" will be a default shader name
    :type shaderName: str
    :param suffixName: Add an autosuffix for the shader name?  Example shader_STRD
    :type suffixName: bool
    :param assignGeo: Will assign to currently selected geo if Ture
    :type assignGeo: bool
    :param message: Report a message to the user?
    :type message: bool

    :return shaderInstance: A zoo shader instance of the specified shader
    :rtype shaderInstance: :class:`shaderbase.ShaderBase`
    """
    sel = cmds.ls(selection=True, long=True)
    shaderInstance = createShaderInstanceType(shdcn.RENDERER_DEFAULT_SHADER[renderer],
                                              shaderName=shaderName,
                                              suffixName=suffixName)
    if assignGeo:
        shaderInstance.assign(sel, message=message)
    return shaderInstance


def createDefaultShadRendererAuto(shaderName="", suffixName=False, assignGeo=True, message=False):
    """Creates a default shader and assigns to geo of the currently loaded renderer in Zoo Tools Pro

        multirenderersettings.currentRenderer()

    :param shaderName: The name of the shader, if "" will be a default shader name
    :type shaderName: str
    :param suffixName: Add an autosuffix for the shader name?  Example shader_STRD
    :type suffixName: bool
    :param assignGeo: Will assign to currently selected geo if Ture
    :type assignGeo: bool
    :param message: Report a message to the user?
    :type message: bool

    :return shaderInstance: A zoo shader instance of the specified shader
    :rtype shaderInstance: :class:`shaderbase.ShaderBase`
    """
    return createDefaultShadRenderer(multirenderersettings.currentRenderer(),
                                     shaderName=shaderName,
                                     suffixName=suffixName,
                                     assignGeo=assignGeo,
                                     message=message)


# ------------------------
# Get instances from objects
# ------------------------


def shaderInstancesFromNodes(nodes):
    """From shaders geometry or shading groups return a list of associated zoo shader instances

    :param nodes: Maya nodes, geometry, shaders or shading groups
    :type nodes: list(str)

    :return shaderInstances: A list of zoo shader instances
    :rtype shaderInstances: list(:class:`shaderbase.ShaderBase`)
    """
    shaderInstList = list()
    shaders = shaderutils.getShadersFromNodes(nodes)
    if not shaders:
        return list()
    for shader in shaders:
        shaderInstList.append(shaderInstanceFromShader(shader))
    return shaderInstList


def shaderInstancesFromSelected(message=True):
    """From selected shaders geometry or shading groups return a list of associated zoo shader instances

    :param message: Report warnings to the user?
    :type message: bool
    :return shaderInstances: A list of zoo shader instances
    :rtype shaderInstances: list(:class:`shaderbase.ShaderBase`)
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if message:
            output.displayWarning("Nothing selected. Please select object/s with shaders.")
        return list()
    return shaderInstancesFromNodes(selObjs)


# ------------------------
# Shader Type
# ------------------------


def getShadersSceneShaderType(shaderType):
    return cmds.ls(type=shaderType)


def getShaderType(shader):
    return cmds.nodeType(shader)


# ------------------------
# Assign Dict Values Selected
# ------------------------

def assignValuesSelected(shaderDict, noneIsDefault=False, message=True):
    """

    :param shaderDict: Generic shader dictionary with values.
    :type shaderDict: dict()
    :param noneIsDefault: Will apply defaults if the value of the key is None or doesn't exist
    :type noneIsDefault: bool
    :param message: Report a message to the user?
    :type message: bool

    :return dictApplied: Was the dictionary values applied?
    :rtype dictApplied: bool
    """
    shaderInstances = shaderInstancesFromSelected(message=False)
    if not shaderInstances:  # no shaders found
        if message:
            output.displayWarning("Please select meshes/shader to change, no shaders found.")
        return False
    for shaderInst in shaderInstances:
        shaderInst.setFromDict(shaderDict, noneIsDefault=noneIsDefault)


# ------------------------
# Copy Paste Shader
# ------------------------


def copyShaderSelected(message=True):
    """Copies a shaders name and zoo supported attributes to a singleton class:

        shaderTrackerInst = shaderutils.ZooShaderTrackerSingleton()

    Supports both selected shader and objects.  Finds the first instance and uses it to extract the name and values.

    :param message: Report a message to the user?
    :type message: bool

    :return shaderData: A shader dictionary with values and a shader name.
    :rtype shaderData: tuple(dict, str)
    """
    shaderInstances = shaderInstancesFromSelected(message=False)
    if not shaderInstances:  # no shaders found
        if message:
            output.displayWarning("Please select meshes or shaders, no shaders found.")
        return dict(), ""
    shaderDataSingleton = shaderutils.ZooShaderTrackerSingleton()  # tracks shader data in zoo session
    shaderValuesDict = shaderInstances[0].shaderValues(removeNone=False)  # the shader dictionary from first instance
    shaderName = shaderInstances[0].name()
    shaderDataSingleton.copiedShaderAttrs = shaderValuesDict
    shaderDataSingleton.copiedShaderName = shaderName
    if message:
        output.displayInfo("Shader copied `{}`".format(shaderName))
    return shaderValuesDict, shaderName


def pasteShaderSelected(message=True):
    """Pastes a shader from the shader name, the shader name must exist in the scene.

    Uses the shader tracker singleton class to paste from:

         shaderTrackerInst = shaderutils.ZooShaderTrackerSingleton()

    Existing shader assignments are replaced.

    :param message: Report a message to the user?
    :type message: bool

    :return shaderName:  The name of a shader
    :rtype shaderName:  str
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if message:
            output.displayWarning("No objects to assign shaders are selected")
        return ""
    shaderTrackerInst = shaderutils.ZooShaderTrackerSingleton()
    shaderName = shaderTrackerInst.copiedShaderName
    if not shaderName:
        if message:
            output.displayWarning("A shader has not been copied, please copy a shader to paste.")
        return ""
    if cmds.objExists(shaderName):
        shaderutils.assignShader(selObjs, shaderName)
    if message:
        output.displayInfo("Shader pasted `{}`".format(shaderName))
    return shaderName


def pasteShaderAttrsSelected(message=True):
    """Pastes shader data onto the currently selected shaders.
    Shader data is from a dictionary with zoo supported attributes.  Shaders remain with tweaked values.

    Uses the shader tracker singleton class to paste from:

         shaderTrackerInst = shaderutils.ZooShaderTrackerSingleton()

    :param message: Report a message to the user?
    :type message: bool

    :return shaderInstances: A list of shader instances with new values.
    :rtype shaderInstances: list(:class:`shaderbase.ShaderBase`)
    """
    shaderNames = list()
    shaderInstances = shaderInstancesFromSelected(message=False)
    if not shaderInstances:  # no shaders found
        if message:
            output.displayWarning("No compatible shaders found. Select meshes or shaders to paste onto.")
        return list()
    shaderTrackerInst = shaderutils.ZooShaderTrackerSingleton()
    shaderDict = shaderTrackerInst.copiedShaderAttrs
    if not shaderDict:
        output.displayWarning("A shader has not been copied, please copy a shader to paste.")
    for shaderInst in shaderInstances:
        shaderInst.setFromDict(shaderDict, apply=True)
        shaderNames.append(shaderInst.name())
    if message:
        output.displayInfo("Shader attributes pasted `{}`".format(shaderNames))
    return shaderInstances


