"""This module is the Redshift class for directional lights

A directional light has these properties:

    - name: The name of the light (str)
    - shapeName: The name of the light (str)
    - nodetype: The node type of the directional light (str)
    - lightSuffix: The optional suffix of the light
    - intensity: The intensity of the light
    - rotate: The rotation values in 3d space
    - translate: The translation values in 3d space
    - scale: The scale values in 3d space
    - color: The color of the directional light
    - tempBool: Is the temperature mode on or off?
    - temperature: The temperature of the directional light
    - softAngle: The soft angle (shadow blur) of the directional light


Example use (Note: base class will not build lights, must use a subclass renderer):

.. code-block:: python

    from zoo.libs.maya.cmds.lighting.directionaltypes import redshiftdirectional
    directionalInst = redshiftdirectional.RedshiftDirectional("directionalLightName", create=True)  # creates a new Directional light

    directionalInst.setName("myDirectionalLight")  # sets name of the light
    directionalInst.setIntensity(1.5)
    directionalInst.setRotate([0.0, 95.3, 0.0])  # rotates the Directional light 90 degrees

    directionalInst = redshiftdirectional.RedshiftDirectional(name="existingDirectionalLight", create=False, ingest=True)  # ingest existing light


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

from zoo.libs.maya import zapi

from zoo.libs.utils import output
from zoo.libs.maya.cmds.lighting import lightconstants
from zoo.libs.maya.cmds.lighting.directionaltypes import directionalbase

NODE_TYPE = "RedshiftPhysicalLight"


class RedshiftDirectional(directionalbase.DirectionalBase):
    """Main class that manages a directional light
    """
    nodetype = NODE_TYPE
    lightSuffix = "RS"
    intensityAttr = "intensity"
    colorAttr = "color"
    tempBoolAttr = "colorMode"
    temperatureAttr = "temperature"
    softAngleAttr = "SAMPLINGOVERRIDES_shadowSamplesScale"

    intensityMultiply = 1.0
    scaleMultiply = 1.0

    def __init__(self, name="", genAttrDict=None, node=None, create=False, ingest=False, suffixName=False,
                 message=True):
        """Either loads a directional light or creates it.

        To create a new directional light:
            create=True and node=False to create a new shader

        To load a directional light by zapiNode name
            node="zapiNode" (should be a shader node) and ingest=True

        To load a directional light by string:
            shaderName="shaderName" and ingest=True

        :param name: The string name of the directional light to load or create
        :type name: str
        :param node: Optional zapi node object and will ingest and not create a new directional light
        :type node: :class:`zapi.DGNode`
        :param genAttrDict: The generic attribute dictionary with attribute values to set only if creating
        :type genAttrDict: dict(str)
        :param create: If True then create a new directional light False will load the directional light into the instance
        :type create: bool
        :param ingest: If True then ingest the directional light into the instance
        :type ingest: bool
        :param message: Report a message to the user only if creating
        :type message: bool
        """
        super(RedshiftDirectional, self).__init__(name=name,
                                                  genAttrDict=genAttrDict,
                                                  node=node,
                                                  create=create,
                                                  ingest=ingest,
                                                  suffixName=suffixName,
                                                  message=message)

    def create(self, message=True):
        super(RedshiftDirectional, self).create(message=True)
        cmds.setAttr("{}.lightType".format(self.shapeName()), 3)  # change to directional type

    def renderer(self):
        """Returns the current renderer as a string"""
        return lightconstants.REDSHIFT

    # -------------------
    # Setters and Getters
    # -------------------
