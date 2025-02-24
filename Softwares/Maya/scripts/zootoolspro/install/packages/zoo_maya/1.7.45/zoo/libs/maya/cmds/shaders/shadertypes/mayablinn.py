"""This module creates and manages a blinn shader, many regular shader attributes are not used.

This class is a subclass of shaderbase and inherits all functionality where applicable.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.shaders.shadertypes import mayablinn
    shadInst = mayablinn.Blinn("shaderName", create=True)  # creates a new shader

    shadInst.setDiffuse([0.0, 0.0, 1.0])  # sets diffuse color to blue
    shadInst.setDiffuseWeight(1.0)

    shadInst2 = mayablinn.Blinn("rocketShader", ingest=True)  # Loads existing "rocketShader" as instance

    shadInst2.assignSelected()

    shadInst2.setShaderName("newNameY")
    print(shadInst2.shaderName())

Author: Andrew Silke

"""
from maya import cmds

from zoo.libs.maya import zapi

from zoo.libs.maya.cmds.shaders import shdmultconstants
from zoo.libs.maya.cmds.shaders.shadertypes import shaderbase

NODE_TYPE = "blinn"
SHADER_SUFFIX = "BLNN"
DIFFUSE_WEIGHT_ATTR = "diffuse"
DIFFUSE_COLOR_ATTR = "color"
DIFFUSE_ROUGHNESS_ATTR = ""
METALNESS_ATTR = ""
SPECULAR_WEIGHT_ATTR = "specularRollOff"
SPECULAR_COLOR_ATTR = "specularColor"
SPECULAR_ROUGHNESS_ATTR = "eccentricity"
SPECULAR_IOR_ATTR = ""
COAT_WEIGHT_ATTR = ""
COAT_COLOR_ATTR = ""
COAT_ROUGHNESS_ATTR = ""
COAT_IOR_ATTR = ""
EMISSION_ATTR = "incandescence"
EMISSION_WEIGHT_ATTR = ""
NORMAL_ATTR = "normalCamera"
BUMP_ATTR = "normalCamera"

OUT_COLOR = "outColor"


class Blinn(shaderbase.ShaderBase):
    """Manages the creation and set/get attribute values for the Blinn
    """
    nodetype = NODE_TYPE
    suffix = SHADER_SUFFIX

    outColorAttr = OUT_COLOR

    diffuseWeightAttr = DIFFUSE_WEIGHT_ATTR
    diffuseColorAttr = DIFFUSE_COLOR_ATTR
    diffuseRoughnessAttr = DIFFUSE_ROUGHNESS_ATTR
    metalnessAttr = METALNESS_ATTR
    specularWeightAttr = SPECULAR_WEIGHT_ATTR
    specularColorAttr = SPECULAR_COLOR_ATTR
    specularRoughnessAttr = SPECULAR_ROUGHNESS_ATTR
    specularIorAttr = SPECULAR_IOR_ATTR
    coatWeightAttr = COAT_WEIGHT_ATTR
    coatcolorAttr = COAT_COLOR_ATTR
    coatRoughnessAttr = COAT_ROUGHNESS_ATTR
    coatIorAttr = COAT_IOR_ATTR
    emissionAttr = EMISSION_ATTR
    emissionWeightAttr = EMISSION_WEIGHT_ATTR
    normalAttr = NORMAL_ATTR
    bumpAttr = BUMP_ATTR

    def __init__(self, shaderName="", node=None, genAttrDict=None, create=False, ingest=False, suffixName=False,
                 message=True):
        """Either loads a shader or creates it.

        To create a new shader:
            create=True and node=False to create a new shader

        To load a shader by zapiNode name
            node="zapiNode" (should be a shader node) and ingest=True

        To load a shader by string:
            shaderName="shaderName" and ingest=True

        :param shaderName: The name of the shader to load or create
        :type shaderName: str
        :param node: A zapi node as an object
        :type node: zoo.libs.maya.zapi.base.DGNode
        :param genAttrDict: The generic attribute dictionary with attribute values to set only if creating
        :type genAttrDict: dict(str)
        :param create: If True then create a new shader False will load the shader and nodes in the instance
        :type create: bool
        :param ingest: If True then shaders should be passed in as a string name (shaderName) or zapi node (node).
        :type ingest: bool
        :param message: Report a message to the user only if creating
        :type message: bool
        """
        super(Blinn, self).__init__(shaderName=shaderName,
                                    node=node,
                                    genAttrDict=genAttrDict,
                                    create=create,
                                    ingest=ingest,
                                    suffixName=suffixName,
                                    message=message)

    def knownShader(self):
        """Returns True as this shader is supported by Zoo Tools"""
        return True

    def renderer(self):
        """Returns the current renderer as a string"""
        return shdmultconstants.MAYA

    # -------------------
    # Create Assign Delete
    # -------------------

    def createShader(self, message=True):
        """Creates a blinn node network and loads the nodes as class variables

        Overridden method.

        :param message: Report a message to the user when the shader is created
        :type message: bool
        """
        shaderName = cmds.shadingNode('blinn', asShader=True, name=self.shaderNameVal)
        self.node = zapi.nodeByName(shaderName)
        self.shaderNameVal = shaderName
        self.applyCurrentSettings()

    # -------------------
    # Setters Getters - Attributes
    # -------------------

    def setDiffuseWeight(self, value):
        """Sets the diffuse weight

        :param value: The diffuse weight value 0.0-1.0
        :type value: float
        """
        if self.setAttrScalar(DIFFUSE_WEIGHT_ATTR, value) is None:  # None is not settable/textured
            return
        self.diffuseWeightVal = value

    def diffuseWeight(self):
        """Returns the current diffuse weight

        :return value: The diffuse weight value 0-1.0, None if textured/connected
        :rtype value: float
        """
        value = self.getAttrScalar(DIFFUSE_WEIGHT_ATTR)
        if value is not None:
            self.diffuseWeightVal = value
        return value

    def setDiffuse(self, color):
        """Sets the diffuse color

        :param color: The color as rendering space float color, (0.5, 1.0, 0.0)
        :type color: list(float)
        """
        if self.setAttrColor(DIFFUSE_COLOR_ATTR, color) is None:  # None is not settable/textured
            return
        self.diffuseVal = color

    def diffuse(self):
        """Returns the diffuse color

        :return color: The diffuse color as linear float rgb (0.1, 0.5, 1.0), None if textured/connected
        :rtype color: list(float)
        """
        color = self.getAttrColor(DIFFUSE_COLOR_ATTR)
        if color is not None:
            self.diffuseVal = color
        return color

    def setSpecColor(self, color):
        """Sets the specular color

        :param color: The specular color as rendering space float color, (0.5, 1.0, 0.0)
        :type color: list(float)
        """
        if self.setAttrColor(SPECULAR_COLOR_ATTR, color) is None:  # None is not settable/textured
            return
        self.diffuseVal = color

    def specColor(self):
        """Returns the specular color

        :return value: The specular color as linear float rgb (0.1, 0.5, 1.0), None if textured/connected
        :rtype value: list(float)
        """
        color = self.getAttrColor(SPECULAR_COLOR_ATTR)
        if color is not None:
            self.diffuseVal = color
        return color

    def setSpecRoughness(self, value):
        """Sets the specular roughness value.

        Blinn this is the eccentricity attribute.

        :param value: The specular roughness value 0-1.0, None if textured/connected
        :type value: float
        """
        if self.setAttrScalar(SPECULAR_ROUGHNESS_ATTR, value) is None:  # None is not settable/textured
            return
        self.diffuseWeightVal = value

    def specRoughness(self):
        """Returns the specular roughness value.

        Blinn this is the eccentricity attribute.

        :return value: The specular roughness value 0-1.0, None if textured/connected
        :rtype value: float
        """
        value = self.getAttrScalar(SPECULAR_ROUGHNESS_ATTR)
        if value is not None:
            self.diffuseWeightVal = value
        return value

    def setSpecWeight(self, value):
        """Sets the specular weight value

        Blinn this is the specularRollOff attribute.

        :param value: Specular Weight value 0-1.0
        :type value: float
        """
        if self.setAttrScalar(SPECULAR_WEIGHT_ATTR, value) is None:  # None is not settable/textured
            return
        self.specWeightVal = value

    def specWeight(self):
        """Returns the specular weight value

        Blinn this is the specularRollOff attribute.

        :return value:  Specular Weight value 0-1.0, None if textured/connected
        :rtype value: float
        """
        color = self.getAttrScalar(SPECULAR_WEIGHT_ATTR)
        if color is not None:
            self.specWeightVal = color
        return color

    def setEmission(self, color):
        """Sets the emission (self illumination) color

        :param color: Emission color as rendering space float rgb (0.5, 1.0, 0.0)
        :type color: list(float)
        """
        if self.setAttrColor(EMISSION_ATTR, color) is None:  # None is not settable/textured
            return
        self.emissionVal = color

    def emission(self):
        """Returns the emission (self illumination) color

        :return color: Emission color as rendering space float rgb (0.5, 1.0, 0.0), None if textured/connected
        :rtype color: list(float)
        """
        color = self.getAttrColor(EMISSION_ATTR)
        if color is not None:
            self.emissionVal = color
        return color
