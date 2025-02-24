"""The new class for creating and ingesting Area Lights with multiple renderer support.

AREA LIGHT EXAMPLES

# Create Area Light (Arnold):

.. code-block:: python

    from zoo.libs.maya.cmds.lighting import lightsmultiarea
    areaInst = lightsmultiarea.createDefaultAreaRenderer("Arnold", areaName="")


# Ingest Area Light:

.. code-block:: python

    from zoo.libs.maya.cmds.lighting import lightsmultiarea
    areaInst = lightsmultiarea.areaInstanceFromShape(areaName="anAreaLightShape")


# Change Area Light Settings:

.. code-block:: python

    areaInst.setName("anAreaLight")  # sets name of the light
    areaInst.setIntensity(1.5)
    areaInst.setRotate([0.0, 95.3, 0.0])  # rotates the area light 90 degrees


# Set values from a dictionary
Default area dictionary example from zoo.libs.maya.cmds.lighting.lightconstants:

.. code-block:: python

    AREA_DEFAULT_VALUES = {AREA_NAME: "area",
                           AREA_INTENSITY: 1.0,
                           AREA_EXPOSURE: 16.0,
                           AREA_ROTATE: [0.0, 0.0, 0.0],
                           AREA_TRANSLATE: [0.0, 0.0, 0.0],
                           AREA_SCALE: [1.0, 1.0, 1.0],
                           AREA_SHAPE: 0,
                           AREA_NORMALIZE: True,
                           AREA_LIGHTVISIBILITY: False,
                           AREA_LIGHTCOLOR: [1.0, 1.0, 1.0],
                           AREA_TEMPONOFF: False,
                           AREA_TEMPERATURE: 6500.0}

Author: Andrew Silke
"""
from maya import cmds

from zoo.libs.utils import output

from zoo.libs.maya.cmds.lighting import lightingutils, lightconstants as lgtcn
from zoo.libs.maya.cmds.lighting.areatypes import areabase, arnoldarea, redshiftarea, rendermanarea, vrayarea, mayaarea
from zoo.libs.maya.cmds.renderer import multirenderersettings

RENDERMAN = lgtcn.RENDERMAN
REDSHIFT = lgtcn.REDSHIFT
ARNOLD = lgtcn.ARNOLD
MAYA = lgtcn.MAYA
VRAY = lgtcn.VRAY


# --------------------------
# CREATE LOAD AREA LIGHT INSTANCES
# --------------------------


def emptyInstance(areaName=""):
    """Creates an empty area instance for use when no light is selected"""
    return areabase.AreaBase(areaName, node=None, genAttrDict=None, create=False, ingest=True)  # no instance


def areaInstancer(areaType, areaName="", genAttrDict=None, create=False, ingest=True, suffixName=False, message=False):
    """Creates or ingests (loads) a area instance of a specific renderer.

    :param areaType: The type of light to create eg "aiAreaLight" see lgtcn.RENDERERAREALIGHTS
    :type areaType: str
    :param areaName: The transform name of the area light to create.
    :type areaName: str
    :param genAttrDict: The optional generic attribute dictionary with attribute values to set only if creating
    :type genAttrDict: dict(str)
    :param create: True if creating a new area light, False if using an existing area light.
    :type create: bool
    :param ingest: False if creating a new area light, True if using an existing area light.
    :type ingest: bool
    :param suffixName: If True automatically suffix's the given name with the renderer's suffix
    :type suffixName: bool
    :param message: Report the message to the user?
    :type message: bool

    :return: A zoo area light instance of the specified light.
    :rtype: :class:`areabase.AreaBase`
    """
    if areaType == arnoldarea.NODE_TYPE:
        return arnoldarea.ArnoldArea(name=areaName, genAttrDict=genAttrDict, create=create, ingest=ingest,
                                     suffixName=suffixName, message=message)
    elif areaType == redshiftarea.NODE_TYPE:
        return redshiftarea.RedshiftArea(name=areaName, genAttrDict=genAttrDict, create=create, ingest=ingest,
                                         suffixName=suffixName, message=message)
    elif areaType == rendermanarea.NODE_TYPE:
        return rendermanarea.RendermanArea(name=areaName, genAttrDict=genAttrDict, create=create, ingest=ingest,
                                           suffixName=suffixName, message=message)
    elif areaType == vrayarea.NODE_TYPE:
        return vrayarea.VRayArea(name=areaName, genAttrDict=genAttrDict, create=create, ingest=ingest,
                                 suffixName=suffixName, message=message)
    elif areaType == mayaarea.NODE_TYPE:
        return mayaarea.MayaArea(name=areaName, genAttrDict=genAttrDict, create=create, ingest=ingest,
                                 suffixName=suffixName, message=message)
    else:
        return areabase.AreaBase(name=areaName, genAttrDict=genAttrDict, create=False, ingest=True,
                                 suffixName=suffixName, message=message)  # no instance


def areaInstanceFromShape(areaShape, message=True):
    """Loads an area instance from an existing area light shape node.  Auto-detects the node type.

    Supports lgtcn.AREA_RENDERER_SUPPORTED:

        "Arnold" "Redshift", "VRay", "Renderman"

    if no area light exists then returns None

    :param areaShape: The shape node name of an area light
    :type areaShape: str
    :param message: Report the message to the user?
    :type message: bool

    :return: A zoo area light instance of the specified light, None if the area light does not exist
    :rtype: :class:`areabase.AreaBase`
    """
    if not cmds.objExists(areaShape):
        return None

    if not cmds.objExists(areaShape):
        if message:
            output.displayWarning("The node `{}` does not exists in the scene".format(areaShape))
        return None

    areaType = cmds.nodeType(areaShape)

    if type(areaType) is list:  # Renderman has many
        areaType = areaType[0]  # use first type to build the light.

    if areaType not in lgtcn.AREA_TYPES:
        if message:
            output.displayWarning("The node type `{}` is not a Zoo supported area light".format(areaType))
        return None

    areaTransform = cmds.listRelatives(areaShape, parent=True, type="transform", fullPath=True)[0]
    return areaInstancer(areaType, areaName=areaTransform, create=False, ingest=True)


def areaInstanceFromTransform(areaTransform, message=True):
    """Loads an area instance from an existing area light transform node.  Auto-detects the node type.

    Supports lgtcn.AREA_RENDERER_SUPPORTED:

        "Arnold" "Redshift", "VRay", "Renderman"

    if no area light exists then returns None

    :param areaTransform: The transform node name of an area light
    :type areaTransform: str
    :param message: Report the message to the user?
    :type message: bool

    :return: A zoo area light instance of the specified light, None if the area light does not exist
    :rtype: :class:`areabase.AreaBase`
    """
    areaShapes = cmds.listRelatives(areaTransform, shapes=True, fullPath=True)
    if not areaShapes:
        return None
    return areaInstanceFromShape(areaShapes[0], message=message)


# ------------------------
# CREATE AREA LIGHTS
# ------------------------


def createAreaInstanceType(areaType, areaName="", genAttrDict=None, suffixName=False, message=True):
    """Creates a new area light of area type with a name and returns the area light instance.

    :param areaType: The type of light to create eg "aiAreaLight" see lgtcn.RENDERERAREALIGHTS
    :type areaType: str
    :param areaName: The name of the area light
    :type areaName: str
    :param suffixName: If True automatically suffix's the given name with the renderer's suffix
    :type suffixName: bool
    :param message: Report the message to the user?
    :type message: bool

    :return: A zoo area light instance of the specified light type
    :rtype: :class:`areabase.AreaBase`
    """
    if type(areaType) is list:  # Renderman has many types
        areaType = areaType[0]  # use first type to build the light.

    areaInstance = areaInstancer(areaType, areaName=areaName, genAttrDict=genAttrDict, create=True, ingest=False,
                                 suffixName=suffixName, message=False)
    if message:
        renderer = lgtcn.AREA_TYPES_RENDERER[areaType]
        output.displayInfo("{} Area light created: {}".format(renderer, areaInstance.shortName()))
    return areaInstance


def createDefaultAreaRenderer(renderer, areaName="", genAttrDict=None, lightGroup=True, select=True, suffixName=False,
                              position="selected", message=True):
    """Creates a default area light of the current renderer type

    Default light dictionary is found at:

        lgtcn.RENDERERAREALIGHTS

    :param renderer: The render nice name "Arnold" "Redshift" etc.
    :type renderer: str
    :param areaName: The name of the area light, if "" will be a default light name
    :type areaName: str
    :param lightGroup: Creates/parents the light inside the group `ArnoldLights_grp` or equivalent renderer
    :type lightGroup: bool
    :param select: Selects the transform node of the light
    :type select: bool
    :param suffixName: If True automatically suffix's the given name with the renderer's suffix
    :type suffixName: bool
    :param position: "" ignores, "selected" created at the position of selobjs, "camera" drops from camera.
    :type position: bool
    :param message: Report the message to the user?
    :type message: bool

    :return: A zoo area light instance of the specified light
    :rtype: :class:`areabase.AreaBase`
    """
    sel = cmds.ls(selection=True, long=True)
    areaInstance = createAreaInstanceType(lgtcn.RENDERERAREALIGHTS[renderer], areaName=areaName,
                                          genAttrDict=genAttrDict, suffixName=suffixName, message=message)
    if lightGroup:
        areaInstance.parentZooLightGroup()

    if sel:
        cmds.select(sel, replace=True)
    else:
        cmds.select(deselect=True)
    if position:
        areaInstance.matchTo(position)

    if select:
        areaInstance.selectTransform()
    return areaInstance


def createDefaultAreaAutoRenderer(areaName="", genAttrDict=None, lightGroup=True, select=True, suffixName=False,
                                  position="selected", message=True):
    """Creates a default area light from the renderer that's currently loaded in Zoo Tools Pro.

        multirenderersettings.currentRenderer()

    :param areaName: The name of the Area light, if "" will be a default light name
    :type areaName: str
    :param lightGroup: Creates/parents the light inside the group `ArnoldLights_grp` or equivalent renderer
    :type lightGroup: bool
    :param select: Selects the transform node of the light
    :type select: bool
    :param suffixName: If True automatically suffix's the given name with the renderer's suffix
    :type suffixName: bool
    :param position: "" ignores, "selected" created at the position of selobjs, "camera" drops from camera.
    :type position: bool
    :param message: Report the message to the user?
    :type message: bool

    :return: A zoo Area instance of the specified light
    :rtype: :class:`areabase.AreaBase`
    """
    return createDefaultAreaRenderer(multirenderersettings.currentRenderer(),
                                     areaName=areaName,
                                     genAttrDict=genAttrDict,
                                     lightGroup=lightGroup,
                                     select=select,
                                     suffixName=suffixName,
                                     position=position,
                                     message=message)


# ----------------------------------
# GET INSTANCES FROM SCENE/SELECTION
# ----------------------------------


def areaInstancesFromNodes(nodeTransforms, areaTypes=lgtcn.AREA_TYPES, message=True):
    """From the given nodes load Area light instances

    :param nodeTransforms: A list of objects, should be transforms
    :type nodeTransforms: list(str)
    :param message: Report warnings to the user?
    :type message: bool

    :return: A list of zoo area light instances
    :rtype: list(:class:`areabase.AreaBase`)
    """
    areaInstList = list()
    lightTransforms = lightingutils.filterAllLightTypesFromNodes(nodeTransforms, areaTypes)
    if not lightTransforms:
        if message:
            output.displayWarning("No area lights found.")
        return list()
    for light in lightTransforms:
        areaShape = cmds.listRelatives(light, shapes=True, fullPath=True)[0]
        areaInstList.append(areaInstanceFromShape(areaShape))
    return areaInstList


def areaInstancesFromSelected(areaTypes=lgtcn.AREA_TYPES, message=True):
    """From selected lights return a list of associated zoo area light instances

    :param areaTypes: A list of light types of the node type of the area light's shape node
    :type areaTypes: list(str)
    :param message: Report warnings to the user?
    :type message: bool

    :return: A list of zoo area light instances
    :rtype: list(:class:`areabase.AreaBase`)
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if message:
            output.displayWarning("Nothing selected. Please select area light/s")
        return list()
    return areaInstancesFromNodes(selObjs, areaTypes=areaTypes, message=message)


def areaInstancesFromScene(areaTypes=lgtcn.AREA_TYPES, message=True):
    """Returns all the area lights in a scene as area Instances.

    :param message: Report warnings to the user?
    :type message: bool

    :return: A list of zoo area light instances
    :rtype: list(:class:`areabase.AreaBase`)
    """
    areaInstances = list()
    lightsShapes = lightingutils.getAllLightShapesInScene(areaTypes)
    if not lightsShapes:
        if message:
            output.displayWarning("No Area Lights found in the scene.")
        return list()
    for shape in lightsShapes:
        areaInstances.append(areaInstanceFromShape(shape))
    return areaInstances


def areaInstancesRenderer(renderer, message=True):
    """Return all the area lights in the scene from a particular renderer.

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
    :return: A list of zoo area light instances
    :rtype: list(:class:`areabase.AreaBase`)
    """
    return areaInstancesFromScene(areaTypes=[lgtcn.RENDERERAREALIGHTS[renderer]], message=message)


def areaInstanceRenderer(renderer, message=True):
    """Returns a single area light instance in the scene from a particular renderer.

    Tries selection and then searches the scene for matching area lights.

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
    :return: A zoo area light instance or None if none found.
    :rtype: :class:`areabase.AreaBase`
    """
    areaInstances = areaInstancesFromSelected(areaTypes=[lgtcn.RENDERERAREALIGHTS[renderer]], message=False)
    if areaInstances:
        return areaInstances[0]
    areaInstances = areaInstancesRenderer(renderer, message=message)
    if areaInstances:
        return areaInstances[0]
    return None
