"""The new class for creating and ingesting HDRI Skydome Lights with multiple renderer support.

Author: Andrew Silke

SKYDOME EXAMPLES

# Create Skydome (Arnold):

.. code-block:: python

    from zoo.libs.maya.cmds.lighting import lightsmultihdri
    hdriInst = lightsmultihdri.createDefaultHdriRenderer("Arnold", hdriName="")


# Ingest Skydome:

.. code-block:: python

    from zoo.libs.maya.cmds.lighting import lightsmultihdri
    hdriInst = lightsmultihdri.hdriInstanceFromHdri(hdriName="mySkydomeLight")


# Change Skydome Settings:

.. code-block:: python

    hdriInst.setName("myHdriSkydomeLight")  # sets name of the light
    hdriInst.setIntensity(1.5)
    hdriInst.setBackgroundVis(False)  # sets the background to be invisible in renders
    hdriInst.setRotate([0.0, 95.3, 0.0])  # rotates the HDRI light 90 degrees
    hdriInst.setImagePath(r"C:/myImage/path/image.hdr")  # Sets the image of the skydome


# Set values from a dictionary

.. code-block:: python

    # Default HDRI dictionary example from zoo.libs.maya.cmds.lighting.lightconstants
    skydomeValues = {HDRI_NAME: "hdriSkydome",
                     HDRI_INTENSITY: 1.0,
                     HDRI_ROTATE: [0.0, 0.0, 0.0],
                     HDRI_TRANSLATE: [0.0, 0.0, 0.0],
                     HDRI_SCALE: [1.0, 1.0, 1.0],
                     HDRI_TEXTURE: "",
                     HDRI_INVERT: False,
                     HDRI_LIGHTVISIBILITY: True,
                     HDRI_TINT: [1.0, 1.0, 1.0]}
    hdriInst.setFromDict(genAttrDict, setName=False, apply=True, noneIsDefault=True)


"""
import os

from maya import cmds

from zoo.libs.utils import output, filesystem
from zoo.libs.zooscene import constants

from zoo.libs.maya.cmds.lighting import lightingutils, lightconstants as lgtcn
from zoo.libs.maya.cmds.lighting.hdritypes import hdribase, arnoldhdri, redshifthdri, rendermanhdri, vrayhdri
from zoo.libs.maya.cmds.renderer import multirenderersettings

RENDERMAN = lgtcn.RENDERMAN
REDSHIFT = lgtcn.REDSHIFT
ARNOLD = lgtcn.ARNOLD
MAYA = lgtcn.MAYA
VRAY = lgtcn.VRAY

HDRI_INTENSITY_MULTIPLIER = "hdri_intensityMultiplier"
HDRI_ROTATE_OFFSET = "hdri_rotateOffset"


# -------------------
# GENERIC
# -------------------


def removeLightSuffix(lightName):
    pass
    # renderertransferlights.removeRendererSuffix(lightName)[0]


# --------------------------
# CREATE LOAD HDRI INSTANCES
# --------------------------


def emptyInstance(hdriName=""):
    """Creates an empty hdri instance for use when no light is selected"""
    return hdribase.HdriBase(hdriName, node=None, genAttrDict=None, create=False, ingest=True)  # no instance


def hdriInstancer(hdriType, hdriName="", create=False, ingest=True, suffixName=False, message=False):
    """Creates or ingests (loads) a hdri instance of a specific renderer.

    :param hdriType: The type of hdri to create eg "aiSkyDomeLight" see lgtcn.RENDERERHDRILIGHTS.
    :type hdriType: str
    :param hdriName: The transform name of the hdri to create.
    :type hdriName: str
    :param create: True if creating a new hdri, False if using an existing hdri.
    :type create: bool
    :param ingest: False if creating a new hdri, True if using an existing hdri.
    :type ingest: bool
    :return: A zoo HDRI instance of the specified light.
    :rtype: :class:`hdribase.HdriBase`
    """
    if hdriType == arnoldhdri.NODE_TYPE:
        return arnoldhdri.ArnoldHdri(name=hdriName, create=create, ingest=ingest, suffixName=suffixName,
                                     message=message)
    elif hdriType == redshifthdri.NODE_TYPE:
        return redshifthdri.RedshiftHdri(name=hdriName, create=create, ingest=ingest, suffixName=suffixName,
                                         message=message)
    elif hdriType == rendermanhdri.NODE_TYPE:
        return rendermanhdri.RendermanHdri(name=hdriName, create=create, ingest=ingest, suffixName=suffixName,
                                           message=message)
    elif hdriType == vrayhdri.NODE_TYPE:
        return vrayhdri.VRayHdri(name=hdriName, create=create, ingest=ingest, suffixName=suffixName,
                                 message=message)
    else:
        return hdribase.HdriBase(name=hdriName, node=None, genAttrDict=None, create=False, ingest=True,
                                 suffixName=suffixName, message=message)  # no instance


def hdriInstanceFromHdri(hdriShape):
    """Loads a hdri instance from an existing hdri skydome.  Auto detects the node type.

    Supports lgtcn.SKYDOME_RENDERER_SUPPORTED:

        "Arnold" "Redshift", "VRay", "Renderman"

    if no hdri exists then returns None

    :param hdriShape: The shape node name of a hdri light
    :type hdriShape: str
    :return: A zoo hdri instance of the specified hdri, None if the hdri does not exist
    :rtype: :class:`hdribase.HdriBase`
    """
    if not cmds.objExists(hdriShape):
        return None
    hdriType = cmds.nodeType(hdriShape)
    hdriTransform = cmds.listRelatives(hdriShape, parent=True, type="transform", fullPath=True)[0]
    return hdriInstancer(hdriType, hdriName=hdriTransform, create=False, ingest=True)


# ------------------------
# CREATE HDRI
# ------------------------


def createHdriInstanceType(hdriType, hdriName="", imagePath="", suffixName=False, message=True):
    """Creates a new hdri of hdri type with a name and returns the hdri instance.

    :param hdriType: The type of hdri to create eg "aiSkyDomeLight" see lgtcn.RENDERERHDRILIGHTS.
    :type hdriType: str
    :param hdriName: The name of the HDRI light
    :type hdriName: str
    :param imagePath: Adds the image path to a HDRI texture image, if "auto" will use the default zoo lores HDRI
    :type imagePath: str
    :param message: Report a message to the user
    :type message: bool

    :return: A zoo hdri instance of the specified hdri type
    :rtype: :class:`hdribase.HdriBase`
    """
    hdriInstance = hdriInstancer(hdriType, hdriName=hdriName, create=True, ingest=False, suffixName=suffixName,
                                 message=False)
    if imagePath:
        if imagePath == "auto":
            hdriInstance.setImagePath(lgtcn.DEFAULT_SKYDOME_PATH)
        else:
            hdriInstance.setImagePath(imagePath)
    if message:
        renderer = lgtcn.SKYDOME_TYPES_RENDERER[hdriType]
        output.displayInfo("{} HDRI Skydome created: {}".format(renderer, hdriInstance.shortName()))
    return hdriInstance


def createDefaultHdriRenderer(renderer, hdriName="", imagePath="", lightGroup=True, select=True, suffixName=False,
                              message=True):
    """Creates a default hdri skydome of the current renderer

    :param renderer: The render nice name "Arnold" "Redshift" etc.
    :type renderer: str
    :param hdriName: The name of the HDRI light, if "" will be a default light name
    :type hdriName: str
    :param imagePath: Adds the image path to a HDRI texture image, if "auto" will use the default zoo lores HDRI
    :type imagePath: str
    :param lightGroup: Creates/parents the light inside the group `ArnoldLights_grp` or equivalent renderer
    :type lightGroup: bool
    :param select: Selects the transform node of the light
    :type select: bool
    :param message: Report a message to the user
    :type message: bool

    :return: A zoo HDRI instance of the specified light
    :rtype: :class:`hdribase.HdriBase`
    """
    if renderer == MAYA:  # if Maya then use Arnold HDRI skydome as Maya doesn't have one.
        renderer = ARNOLD
    hdriInstance = createHdriInstanceType(lgtcn.RENDERERSKYDOMELIGHTS[renderer], hdriName=hdriName,
                                          imagePath=imagePath, suffixName=suffixName, message=message)
    if lightGroup:
        hdriInstance.parentZooLightGroup()
    if select:
        hdriInstance.selectTransform()
    return hdriInstance


def createDefaultHdriAutoRenderer(hdriName="", imagePath="", lightGroup=True, select=True, suffixName=False,
                                  message=True):
    """Creates a default hdri skydome from the renderer that's currently loaded in Zoo Tools Pro.

        multirenderersettings.currentRenderer()

    :param hdriName: The name of the HDRI light, if "" will be a default light name
    :type hdriName: str
    :param imagePath: Adds the image path to a HDRI texture image, if "auto" will use the default zoo lores HDRI
    :type imagePath: str
    :param lightGroup: Creates/parents the light inside the group `ArnoldLights_grp` or equivalent renderer
    :type lightGroup: bool
    :param select: Selects the transform node of the light
    :type select: bool
    :param message: Report a message to the user
    :type message: bool

    :return: A zoo HDRI instance of the specified light
    :rtype: :class:`hdribase.HdriBase`
    """
    return createDefaultHdriRenderer(multirenderersettings.currentRenderer(),
                                     hdriName=hdriName,
                                     imagePath=imagePath,
                                     lightGroup=lightGroup,
                                     select=select,
                                     suffixName=suffixName,
                                     message=message)


# ----------------------------------
# GET INSTANCES FROM SCENE/SELECTION
# ----------------------------------


def hdriInstancesFromNodes(nodeTransforms, hdriTypes=lgtcn.SKYDOME_TYPES, message=True):
    """From the given nodes load HDRI instances

    :param nodeTransforms: A list of objects, should be transforms
    :type nodeTransforms: list(str)
    :param message: Report warnings to the user?
    :type message: bool

    :return: A list of zoo hdri instances
    :rtype: list(:class:`hdribase.HdriBase`)
    """
    hdriInstList = list()
    lightTransforms = lightingutils.filterAllLightTypesFromNodes(nodeTransforms, hdriTypes)
    if not lightTransforms:
        if message:
            output.displayWarning("No HDRI lights found.")
        return list()
    for light in lightTransforms:
        hdriShape = cmds.listRelatives(light, shapes=True, fullPath=True)[0]
        hdriInstList.append(hdriInstanceFromHdri(hdriShape))
    return hdriInstList


def hdriInstancesFromSelected(hdriTypes=lgtcn.SKYDOME_TYPES, message=True):
    """From selected HDRI lights return a list of associated zoo HDRI instances

    :param hdriTypes: A list of light types of the node type of the hdri light's shape node
    :type hdriTypes: list(str)
    :param message: Report warnings to the user?
    :type message: bool

    :return: A list of zoo hdri instances
    :rtype: list(:class:`hdribase.HdriBase`)
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if message:
            output.displayWarning("Nothing selected. Please select a HDRI light.")
        return list()
    return hdriInstancesFromNodes(selObjs, hdriTypes=hdriTypes, message=message)


def hdriInstancesFromScene(hdriTypes=lgtcn.SKYDOME_TYPES, message=True):
    """Returns all the HDRI lights in a scene as HDRI Instances.

    :param message: Report warnings to the user?
    :type message: bool

    :return: A list of zoo hdri instances
    :rtype: list(:class:`hdribase.HdriBase`)
    """
    hdriInstances = list()
    lightsShapes = lightingutils.getAllLightShapesInScene(hdriTypes, checkRendererLoaded=True)
    if not lightsShapes:
        if message:
            output.displayWarning("No Skydome Lights found in the scene.")
        return list()
    for shape in lightsShapes:
        hdriInstances.append(hdriInstanceFromHdri(shape))
    return hdriInstances


def hdriInstancesRenderer(renderer, message=True):
    """Return all the HDRIs in the scene from a particular renderer.

    Renderer types:

    .. code-block:: text

            lgtcn.MAYA
            lgtcn.REDSHIFT
            lgtcn.RENDERMAN
            lgtcn.ARNOLD
            lgtcn.VRAY

    :param renderer: The nice name of the renderer see lgtcn for renderer strings  "Arnold", "Renderman", "VRay" etc
    :type renderer: str
    :param message: Report warnings to the user?
    :type message: bool
    :return: A list of zoo hdri instances
    :rtype: list(:class:`hdribase.HdriBase`)
    """
    return hdriInstancesFromScene(hdriTypes=[lgtcn.RENDERERSKYDOMELIGHTS[renderer]], message=message)


def hdriInstanceRenderer(renderer, message=True):
    """Returns a single HDRI instance in the scene from a particular renderer.

    Tries selection and then searches the scene for matching HDRIS.  Usually only one HDRI in the scene per renderer.

    Renderer types:

    .. code-block:: text

            lgtcn.MAYA
            lgtcn.REDSHIFT
            lgtcn.RENDERMAN
            lgtcn.ARNOLD
            lgtcn.VRAY

    :param renderer: The nice name of the renderer see lgtcn for renderer strings  "Arnold", "Renderman", "VRay" etc
    :type renderer: str
    :param message: Report warnings to the user?
    :type message: bool
    :return: A zoo hdri instance or None if none found.
    :rtype: :class:`hdribase.HdriBase`
    """
    hdriInstances = hdriInstancesFromSelected(hdriTypes=[lgtcn.RENDERERSKYDOMELIGHTS[renderer]], message=False)
    if hdriInstances:
        return hdriInstances[0]
    hdriInstances = hdriInstancesRenderer(renderer, message=message)
    if hdriInstances:
        return hdriInstances[0]
    return None


# ----------------------------
# OFFSET DATA
# ----------------------------


def hdriDependencyPath(imageFilePath):
    """Returns the dependency folder of a HDRI Image and the extraDatafilePath.

    :param imageFilePath: The file path of a HDRI image to save the data inside the dependency folder
    :type imageFilePath: str
    :return dependencyPath: The full path to the dependency folder of the HDRI Image.
    :return: Fullpath to dependency Folder and zooinfo file.
    :rtype: tuple[str, str]
    """
    path = os.path.dirname(imageFilePath)
    nameOnly, extension = os.path.splitext(os.path.basename(imageFilePath))
    extension = extension.replace(".", "")
    directoryName = "_".join([nameOnly, extension, constants.DEPENDENCY_FOLDER])
    zooInfoFile = ".".join([nameOnly, constants.ZOO_INFO_EXT])
    return os.path.join(path, directoryName), os.path.join(path, directoryName, zooInfoFile)


def saveExtraDataJson(intensityMultiplier, rotationOffset, imageFilePath, message=True):
    """Saves a zooInfoFilePath JSON file with the intensity multiplier and rotation offset data given a HDRI image path.

    Will create a dependency folder and file if none exists.

    :param intensityMultiplier: The value of the intensity multiplier to store in the JSON file.
    :type intensityMultiplier: float
    :param rotationOffset: The value of the intensity multiplier to store in the JSON file.
    :type rotationOffset: float
    :param imageFilePath: The file path of a HDRI image to save the data inside the dependency folder
    :type imageFilePath: str
    :param message: Report a message to the user?
    :type message: str

    :return hdriExtraDataDict: The dictionary with the values HDRI_INTENSITY_MULTIPLIER and HDRI_ROTATE_OFFSET
    :rtype hdriExtraDataDict: dict
    :return zooInfoFilePath: The file path of the file saved
    :rtype zooInfoFilePath: str
    """
    dependencyPath, zooInfoFilePath = hdriDependencyPath(imageFilePath)
    if not os.path.exists(dependencyPath):
        os.mkdir(dependencyPath)
    if not os.path.exists(zooInfoFilePath):
        zooInfoDict = dict()
        filesystem.saveJson(zooInfoDict, zooInfoFilePath)  # save empty file
    else:
        zooInfoDict = filesystem.loadJson(zooInfoFilePath)
    zooInfoDict[HDRI_INTENSITY_MULTIPLIER] = intensityMultiplier
    zooInfoDict[HDRI_ROTATE_OFFSET] = rotationOffset
    filesystem.saveJson(zooInfoDict, zooInfoFilePath, indent=4, separators=(",", ":"), message=message)
    return zooInfoDict, zooInfoFilePath


def loadExtraDataJson(imageFilePath):
    """Loads a JSON file given a HDRI image and attempts to return the intensity multiplier and rotation offset.

    Will return None, None if no file named "HDRI_offsetData.json" exists.

    :param imageFilePath: The file path of a HDRI image to save the data inside the dependency folder
    :type imageFilePath: str

    :return intensityMultiplier: The value of the intensity multiplier in the JSON file. None if not found.
    :rtype intensityMultiplier: float
    :return rotationOffset: The value of the intensity multiplier in the JSON file. None if not found.
    :rtype rotationOffset: float
    """
    dependencyPath, zooInfoFilePath = hdriDependencyPath(imageFilePath)
    if not os.path.exists(zooInfoFilePath):
        return None, None
    zooInfoDict = filesystem.loadJson(zooInfoFilePath)
    if HDRI_INTENSITY_MULTIPLIER not in zooInfoDict:
        return None, None
    return zooInfoDict[HDRI_INTENSITY_MULTIPLIER], zooInfoDict[HDRI_ROTATE_OFFSET]
