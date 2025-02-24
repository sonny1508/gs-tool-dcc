"""This module is the Redshift class for area lights

An Area Light has these properties:

    - name: The name of the light (str)
    - shapeName: The name of the light (str)
    - nodetype: The node type of the Area Light (str)
    - lightSuffix: The optional suffix of the light
    - intensity: The intensity of the light
    - exposure: The exposure of the light
    - rotate: The rotation values in 3d space
    - translate: The translation values in 3d space
    - scale: The scale values in 3d space
    - normalize: Is the Area Light normalized?
    - vis: Is the Area Light visible in the scene?
    - color: The color of the Area Light
    - tempBool: Is the temperature mode on or off?
    - temperature: The temperature of the area Light


Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.lighting.areatypes import redshiftarea
    areaInst = redshiftarea.RedshiftArea("areaLightName", create=True, suffixName=False)  # creates a new area light

    areaInst.setName("myAreaLight")  # sets name of the light
    areaInst.setIntensity(1.5)
    areaInst.setVisibility(False)  # sets the background to be invisible in renders
    areaInst.setRotate([0.0, 95.3, 0.0])  # rotates the Area light 90 degrees

    areaInst = redshiftarea.RedshiftArea(name="existingAreaLight", create=False, ingest=True)  # ingest existing light


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

from zoo.libs.maya import zapi

from zoo.libs.utils import output
from zoo.libs.maya.cmds.lighting import lightconstants
from zoo.libs.maya.cmds.lighting.areatypes import areabase

NODE_TYPE = "RedshiftPhysicalLight"


class RedshiftArea(areabase.AreaBase):
    """Main class that manages an area light
    """
    nodetype = NODE_TYPE
    lightSuffix = "RS"
    intensityAttr = "intensity"
    exposureAttr = "exposure"
    visAttr = "areaVisibleInRender"
    colorAttr = "color"
    normalizeAttr = "normalize"
    tempBoolAttr = "colorMode"
    temperatureAttr = "temperature"
    shapeAttr = "areaShape"

    intensityMultiply = 1.0
    scaleMultiply = 1.0

    def __init__(self, name="", genAttrDict=None, node=None, create=False, ingest=False, suffixName=False,
                 message=True):
        """Either loads an area light or creates it.

        To create a new Area Light:
            create=True and node=False to create a new shader

        To load an area Light by zapiNode name
            node="zapiNode" (should be a shader node) and ingest=True

        To load an area Light by string:
            shaderName="shaderName" and ingest=True

        :param name: The string name of the area light to load or create
        :type name: str
        :param node: Optional zapi node object and will ingest and not create a new Area Light
        :type node: :class:`zapi.DGNode`
        :param genAttrDict: The generic attribute dictionary with attribute values to set only if creating
        :type genAttrDict: dict(str)
        :param create: If True then create a new Area Light False will load the Area Light into the instance
        :type create: bool
        :param ingest: If True then ingest the Area Light into the instance
        :type ingest: bool
        :param suffixName: If True automatically suffix's the given name with the renderer's suffix
        :type suffixName: bool
        :param message: Report a message to the user only if creating
        :type message: bool
        """
        super(RedshiftArea, self).__init__(name=name,
                                           genAttrDict=genAttrDict,
                                           node=node,
                                           create=create,
                                           ingest=ingest,
                                           suffixName=suffixName,
                                           message=message)

    def renderer(self):
        """Returns the current renderer as a string"""
        return lightconstants.REDSHIFT

    # -------------------
    # Setters and Getters
    # -------------------
