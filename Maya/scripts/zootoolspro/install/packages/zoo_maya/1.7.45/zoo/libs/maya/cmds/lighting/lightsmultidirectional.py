"""The new class for creating and ingesting Directional Lights with multiple renderer support.


DIRECTIONAL LIGHT EXAMPLES

# Create Directional Light (Arnold):

.. code-block:: python

    from zoo.libs.maya.cmds.lighting import lightsmultidirectional
    directionalInst = lightsmultidirectional.createDefaultDirectionalRenderer("Arnold", directionalName="")


# Ingest Directional Light:

.. code-block:: python

    from zoo.libs.maya.cmds.lighting import lightsmultidirectional
    directionalInst = lightsmultidirectional.directionalInstanceFromShape("aDirectionalLightShape")


# Change Directional Light Settings:

.. code-block:: python

    directionalInst.setName("aDirectionalLight2")  # sets name of the light
    directionalInst.setIntensity(1.5)
    directionalInst.setRotate([0.0, 95.3, 0.0])  # rotates the directional light 90 degrees


# Set values from a dictionary
Default Directional dictionary example from zoo.libs.maya.cmds.lighting.lightconstants:

.. code-block:: python

    DIR_DEFAULT_VALUES = {DIR_NAME: "directional",
                          DIR_INTENSITY: 1.0,
                          DIR_ROTATE: [0.0, 0.0, 0.0],
                          DIR_TRANSLATE: [0.0, 0.0, 0.0],
                          DIR_SCALE: [1.0, 1.0, 1.0],
                          DIR_SHAPE: 0,
                          DIR_ANGLE_SOFT: 2.0,
                          DIR_LIGHTCOLOR: [1.0, 1.0, 1.0],
                          DIR_TEMPONOFF: False,
                          DIR_TEMPERATURE: 6500.0}

Author: Andrew Silke
"""

from maya import cmds

from zoo.libs.utils import output

from zoo.libs.maya.cmds.lighting import lightingutils, lightconstants as lgtcn
from zoo.libs.maya.cmds.renderer import multirenderersettings
from zoo.libs.maya.cmds.lighting.directionaltypes import directionalbase, arnolddirectional, redshiftdirectional, \
    rendermandirectional, vraydirectional, mayadirectional

RENDERMAN = lgtcn.RENDERMAN
REDSHIFT = lgtcn.REDSHIFT
ARNOLD = lgtcn.ARNOLD
MAYA = lgtcn.MAYA
VRAY = lgtcn.VRAY


# --------------------------
# CREATE LOAD DIRECTIONAL INSTANCES
# --------------------------


def emptyInstance(directionalName=""):
    """Creates an empty directional light instance for use when no light is selected"""
    return directionalbase.DirectionalBase(directionalName, node=None, genAttrDict=None, create=False,
                                           ingest=True)  # no instance


def rendererFromZooAttr(directionalShape):
    """Given a shape type of "directionalLight" the node may be Arnold or VRay.

    This function checks for a tracking attribute "zooRendererTracker" and if it exists it returns the renderer.

    :param directionalShape:
    :type directionalShape:
    :return renderer:  Returns "Arnold" or "VRay" if the tracker attr found, otherwise ""
    :rtype renderer: str
    """
    if not cmds.attributeQuery(lgtcn.DIRECTIONAL_TRACKER_ATTR, node=directionalShape, exists=True):
        return ""  # No tracker attribute found, assumes is Arnold
    return cmds.getAttr(".".join([directionalShape, lgtcn.DIRECTIONAL_TRACKER_ATTR]))


def directionalInstancer(directionalType, directionalName="", forceRenderer="", create=False, ingest=True,
                         suffixName=False, message=False):
    """Creates or ingests (loads) a directional instance of a specific renderer.

    :param directionalType: The type of directional to create eg "PxrDistantLight" see lgtcn.RENDERERDIRECTIONALLIGHTS.
    :type directionalType: str
    :param directionalName: The transform name of the directional light to create.
    :type directionalName: str
    :param forceRenderer: Forces the renderer as directional lights for VRay and Arnold can share type
    :type forceRenderer: str
    :param create: True if creating a new directional, False if using an existing directional light.
    :type create: bool
    :param ingest: False if creating a new directional, True if using an existing directional light.
    :type ingest: bool
    :param suffixName: If True automatically suffix's the given name with the renderer's suffix
    :type suffixName: bool
    :return: A zoo directional instance of the specified light.
    :rtype: :class:`directionalbase.DirectionalBase`
    """
    if forceRenderer == "":  # if forceRenderer is "" or "Arnold" and type is "directionalLight"
        forceRenderer = ARNOLD  # Note only used if directionalType is "directionalLight"

    if directionalType == arnolddirectional.NODE_TYPE and forceRenderer == ARNOLD:
        return arnolddirectional.ArnoldDirectional(name=directionalName, create=create, ingest=ingest,
                                                   suffixName=suffixName, message=message)
    elif directionalType == redshiftdirectional.NODE_TYPE:
        return redshiftdirectional.RedshiftDirectional(name=directionalName, create=create, ingest=ingest,
                                                       suffixName=suffixName, message=message)
    elif directionalType == rendermandirectional.NODE_TYPE:
        return rendermandirectional.RendermanDirectional(name=directionalName, create=create, ingest=ingest,
                                                         suffixName=suffixName, message=message)
    elif directionalType == vraydirectional.NODE_TYPE:  # Type shares with Arnold/Maya
        return vraydirectional.VRayDirectional(name=directionalName, create=create, ingest=ingest,
                                               suffixName=suffixName, message=message)
    elif directionalType == mayadirectional.NODE_TYPE and forceRenderer == MAYA:  # Type shares with Arnold/Maya
        return mayadirectional.MayaDirectional(name=directionalName, create=create, ingest=ingest,
                                               suffixName=suffixName, message=message)
    else:
        return directionalbase.DirectionalBase(name=directionalName, node=None, genAttrDict=None, create=False,
                                               ingest=True, suffixName=suffixName, message=message)  # no instance


def directionalInstanceFromShape(directionalShape, message=True):
    """Loads a directional instance from an existing directional light's shape node.  Auto-detects the node type.

    Supports lgtcn.DIRECTIONAL_RENDERER_SUPPORTED:

        "Arnold" "Redshift", "VRay", "Renderman"

    if no directional light exists then returns None

    :param directionalShape: The shape node name of a directional light
    :type directionalShape: str
    :param message: Report a message to the user?
    :type message: bool
    :return: A zoo directional instance of the specified directional light, None if the light does not exist
    :rtype: :class:`directionalbase.DirectionalBase`
    """
    if not cmds.objExists(directionalShape):
        if message:
            output.displayWarning("The node `{}` does not exists in the scene".format(directionalShape))
        return None

    forceRenderer = ""  # only used in the case of Arnold or Maya
    directionalType = cmds.nodeType(directionalShape)

    if directionalType not in lgtcn.RENDERERDIRECTIONALLIGHTS.values():
        if message:
            output.displayWarning("The node type `{}` is not a Zoo supported directional light".format(directionalType))
        return None

    if directionalType == "directionalLight":  # could be Arnold or VRay or Maya
        forceRenderer = rendererFromZooAttr(directionalShape)

    directionalTransform = cmds.listRelatives(directionalShape, parent=True, type="transform", fullPath=True)[0]
    return directionalInstancer(directionalType,
                                directionalName=directionalTransform,
                                forceRenderer=forceRenderer,
                                create=False,
                                ingest=True)


def directionalInstanceFromTransform(directionalTransform, message=True):
    """Loads a directional instance from an existing directional light.  Auto-detects the node type.

    Supports lgtcn.DIRECTIONAL_RENDERER_SUPPORTED:

        "Arnold" "Redshift", "VRay", "Renderman"

    if no directional light exists then returns None

    :param directionalTransform: The transform name of a directional light
    :type directionalTransform:
    :param message: Report a message to the user?
    :type message: bool
    :return: A zoo directional instance of the specified directional light, None if the light does not exist
    :rtype: :class:`directionalbase.DirectionalBase`
    """
    directionalShapes = cmds.listRelatives(directionalTransform, shapes=True, fullPath=True)
    if not directionalShapes:
        return None
    return directionalInstanceFromShape(directionalShapes[0], message=message)


# ------------------------
# CREATE DIRECTIONAL LIGHT
# ------------------------


def createDirectionalInstanceType(directionalType, directionalName="", forceRenderer="", suffixName=False,
                                  message=True):
    """Creates a new directional light of directional type with a name and returns the directional instance.

    :param directionalType: The type of directional to create eg "PxrDistantLight" see lgtcn.RENDERERDIRECTIONALLIGHTS.
    :type directionalType: str
    :param directionalName: The name of the directional light
    :type directionalName: str
    :param forceRenderer: Forces the renderer as directional lights for VRay and Arnold can share type
    :type forceRenderer: str
    :param suffixName: If True automatically suffix's the given name with the renderer's suffix
    :type suffixName: bool
    :param message: Report the message to the user?
    :type message: bool

    :return: A zoo directional instance of the specified directional type
    :rtype: :class:`directionalbase.DirectionalBase`
    """
    directionalInstance = directionalInstancer(directionalType,
                                               directionalName=directionalName,
                                               create=True,
                                               forceRenderer=forceRenderer,
                                               ingest=False,
                                               suffixName=suffixName,
                                               message=False)
    if message:
        renderer = directionalInstance.renderer()
        output.displayInfo("{} directional light created: {}".format(renderer, directionalInstance.shortName()))
    return directionalInstance


def createDefaultDirectionalRenderer(renderer, directionalName="", lightGroup=True, select=True, suffixName=False,
                                     position="selected", message=True):
    """Creates a default directional light of the current renderer type

    :param renderer: The render nice name "Arnold" "Redshift" etc.
    :type renderer: str
    :param directionalName: The name of the directional light, if "" will be a default light name
    :type directionalName: str
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

    :param message: Report the message to the user?
    :type message: bool

    :return: A zoo directional instance of the specified light
    :rtype: :class:`directionalbase.DirectionalBase`
    """
    sel = cmds.ls(selection=True, long=True)
    directionalInstance = createDirectionalInstanceType(lgtcn.RENDERERDIRECTIONALLIGHTS[renderer],
                                                        directionalName=directionalName,
                                                        forceRenderer=renderer,
                                                        suffixName=suffixName,
                                                        message=message)

    if lightGroup:
        directionalInstance.parentZooLightGroup()

    if sel:
        cmds.select(sel, replace=True)
    else:
        cmds.select(deselect=True)
    if position:
        directionalInstance.matchTo(position)

    if select:
        directionalInstance.selectTransform()
    return directionalInstance


def createDefaultDirectionalRendererAuto(directionalName="", lightGroup=True, select=True, suffixName=False,
                                         position="selected", message=True):
    """Creates a default directional light with the renderer set automatically as per the internal zoo setting at:

        multirenderersettings.currentRenderer()

    :param directionalName: The name of the directional light, if "" will be a default light name
    :type directionalName: str
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

    :return: A zoo directional instance of the specified light
    :rtype: :class:`directionalbase.DirectionalBase`
    """
    return createDefaultDirectionalRenderer(multirenderersettings.currentRenderer(),
                                            directionalName=directionalName,
                                            lightGroup=lightGroup,
                                            select=select,
                                            suffixName=suffixName,
                                            position=position,
                                            message=message)


# ----------------------------------
# GET INSTANCES FROM SCENE/SELECTION
# ----------------------------------


def directionalInstancesFromNodes(nodeTransforms, directionalTypes=lgtcn.DIRECTIONAL_TYPES, message=True):
    """From the given nodes load directional instances

    :param nodeTransforms: A list of objects, should be transforms
    :type nodeTransforms: list(str)
    :param message: Report warnings to the user?
    :type message: bool

    :return: A list of zoo directional instances
    :rtype: list(:class:`directionalbase.DirectionalBase`)
    """
    directionalInstList = list()
    lightTransforms = lightingutils.filterAllLightTypesFromNodes(nodeTransforms, directionalTypes)
    if not lightTransforms:
        if message:
            output.displayWarning("No directional lights found.")
        return list()
    for light in lightTransforms:
        directionalShape = cmds.listRelatives(light, shapes=True, fullPath=True)[0]
        directionalInstList.append(directionalInstanceFromShape(directionalShape))
    return directionalInstList


def directionalInstancesFromSelected(directionalTypes=lgtcn.DIRECTIONAL_TYPES, message=True):
    """From selected directional lights return a list of associated zoo directional instances

    :param directionalTypes: A list of light types of the node type of the directional light's shape node
    :type directionalTypes: list(str)
    :param message: Report warnings to the user?
    :type message: bool

    :return: A list of zoo directional instances
    :rtype: list(:class:`directionalbase.DirectionalBase`)
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if message:
            output.displayWarning("Nothing selected. Please select a directional light.")
        return list()
    return directionalInstancesFromNodes(selObjs, directionalTypes=directionalTypes, message=message)


def directionalInstancesFromScene(directionalTypes=lgtcn.DIRECTIONAL_TYPES, message=True):
    """Returns all the directional lights in a scene as directional instances.

    :param message: Report warnings to the user?
    :type message: bool

    :return: A list of zoo directional instances
    :rtype: list(:class:`directionalbase.DirectionalBase`)
    """
    directionalInstances = list()
    lightsShapes = lightingutils.getAllLightShapesInScene(directionalTypes)
    if not lightsShapes:
        if message:
            output.displayWarning("No Directional Lights found in the scene.")
        return list()
    for shape in lightsShapes:
        directionalInstances.append(directionalInstanceFromShape(shape))
    return directionalInstances


def directionalInstancesRenderer(renderer, message=True):
    """Return all the directional lights in the scene from a particular renderer.

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
    :return: A list of zoo directional instances
    :rtype: list(:class:`directionalbase.DirectionalBase`)
    """
    return directionalInstancesFromScene(directionalTypes=[lgtcn.RENDERERDIRECTIONALLIGHTS[renderer]], message=message)


def directionalInstanceRenderer(renderer, message=True):
    """Returns a single directional instance in the scene from a particular renderer.

    Tries selection and then searches the scene for matching directional lights.

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
    :return: A zoo directional instance or None if none found.
    :rtype: :class:`directionalbase.DirectionalBase`
    """
    directionalInstances = directionalInstancesFromSelected(
        directionalTypes=[lgtcn.RENDERERDIRECTIONALLIGHTS[renderer]], message=False)
    if directionalInstances:
        return directionalInstances[0]
    directionalInstances = directionalInstancesRenderer(renderer, message=message)
    if directionalInstances:
        return directionalInstances[0]
    return None
