"""This module creates and manages a Redshift Material shader.

This class is a subclass of shaderbase and inherits all functionality where applicable.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.shaders.shadertypes import redshiftredshiftmaterial
    shadInst = redshiftredshiftmaterial.RedshiftMaterial("shaderName", create=True)  # creates a new shader

    shadInst.setDiffuse([0.0, 0.0, 1.0])  # sets diffuse color to blue
    shadInst.setDiffuseWeight(1.0)

    shadInst.setMetalness(1.0)  # sets metalness to be on

    shadInst.setSpecWeight(1.0)
    shadInst.setSpecColor([1, 1, 1])
    shadInst.setSpecRoughness(1.0)
    shadInst.setSpecIOR(1.3)

    shadInst.setCoatWeight(0.0)
    shadInst.setCoatIOR(1.5)
    shadInst.setCoatRoughness(.1)
    shadInst.setCoatColor([1, 1, 1])

    shadInst2 = redshiftredshiftmaterial.RedshiftMaterial("rocketShader", ingest=True)  # Loads existing "rocketShader" as instance

    shadInst2.assignSelected()

    shadInst2.setShaderName("newNameY")
    print(shadInst2.shaderName())

"""

from maya import cmds

from zoo.libs.maya import zapi

from zoo.libs.maya.cmds.shaders import redshiftshaders, shdmultconstants
from zoo.libs.maya.cmds.shaders.shadertypes import shaderbase

NODE_TYPE = "RedshiftMaterial"
SHADER_SUFFIX = "RS"
DIFFUSE_WEIGHT_ATTR = "diffuse_weight"
DIFFUSE_COLOR_ATTR = "diffuse_color"
DIFFUSE_ROUGHNESS_ATTR = "diffuse_roughness"
METALNESS_ATTR = "refl_metalness"
SPECULAR_WEIGHT_ATTR = "refl_weight"
SPECULAR_COLOR_ATTR = "refl_color"
SPECULAR_ROUGHNESS_ATTR = "refl_roughness"
SPECULAR_IOR_ATTR = "refl_ior"
COAT_WEIGHT_ATTR = "coat_weight"
COAT_COLOR_ATTR = "coat_color"
COAT_ROUGHNESS_ATTR = "coat_roughness"
COAT_IOR_ATTR = "coat_ior"
EMISSION_ATTR = "emission_color"
EMISSION_WEIGHT_ATTR = "emission_weight"
NORMAL_ATTR = "normalCamera"
BUMP_ATTR = "normalCamera"

OUT_COLOR = "outColor"


class RedshiftMaterial(shaderbase.ShaderBase):
    """Manages the creation and set/get attribute values for the RedshiftMaterial
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
        super(RedshiftMaterial, self).__init__(shaderName=shaderName,
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
        return shdmultconstants.REDSHIFT

    # -------------------
    # Create Assign Delete
    # -------------------

    def createShader(self, message=True):
        """Creates a redshiftMaterial node network and loads the nodes as class variables

        Overridden method.

        :param message: Report a message to the user when the shader is created
        :type message: bool
        """
        shaderName = redshiftshaders.createRedshiftMaterial(shaderName=self.shaderNameVal, message=message)
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
        color = self.getAttrScalar(DIFFUSE_WEIGHT_ATTR)
        if color is not None:
            self.diffuseWeightVal = color
        return color

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

        :return value: The diffuse color as linear float rgb (0.1, 0.5, 1.0), None if textured/connected
        :rtype value: list(float)
        """
        color = self.getAttrColor(DIFFUSE_COLOR_ATTR)
        if color is not None:
            self.diffuseVal = color
        return color

    def setDiffuseRoughness(self, value):
        """Sets the diffuse weight

        :param value: The diffuse weight value 0.0-1.0
        :type value: float
        """
        if self.setAttrScalar(DIFFUSE_ROUGHNESS_ATTR, value) is None:  # None is not settable/textured
            return
        self.diffuseRoughnessVal = value

    def diffuseRoughness(self):
        """Returns the current diffuse weight

        :return value: The diffuse weight value 0-1.0, None if textured/connected
        :rtype value: float
        """
        color = self.getAttrScalar(DIFFUSE_ROUGHNESS_ATTR)
        if color is not None:
            self.diffuseRoughnessVal = color
        return color

    def setMetalness(self, value):
        """Sets the metalness value

        :param value: The metalness value 0-1.0
        :type value: float
        """
        if self.setAttrScalar(METALNESS_ATTR, value) is None:  # None is not settable/textured
            return
        self.metalnessVal = value
        shaderName = self.shaderName()
        if value > 0.001:
            cmds.setAttr("{}.refl_fresnel_mode".format(shaderName), 2)  # Turns shader mode to metalness
            self.setAttrColor("refl_reflectivity", (0.0, 0.0, 0.0))
        else:
            cmds.setAttr("{}.refl_fresnel_mode".format(shaderName), 3)  # Turns shader mode to IOR
            self.setAttrColor("refl_reflectivity", (0.0, 0.0, 0.0))

    def metalness(self):
        """Returns the metalness value

        :return value: The metalness value 0-1.0, None if textured/connected
        :rtype value: float
        """
        value = self.getAttrScalar(METALNESS_ATTR)
        if value is not None:
            self.metalnessVal = value
        if cmds.getAttr("{}.refl_fresnel_mode".format(self.shaderName())) != 2:
            return 0.0
        return value

    def setSpecWeight(self, value):
        """Sets the specular weight value

        :param value: Specular Weight value 0-1.0
        :type value: float
        """
        if self.setAttrScalar(SPECULAR_WEIGHT_ATTR, value) is None:  # None is not settable/textured
            return
        self.specWeightVal = value

    def specWeight(self):
        """Returns the specular weight value

        :return value:  Specular Weight value 0-1.0, None if textured/connected
        :rtype value: float
        """
        color = self.getAttrScalar(SPECULAR_WEIGHT_ATTR)
        if color is not None:
            self.specWeightVal = color
        return color

    def setSpecColor(self, color):
        """Sets the specular color

        :param color: Specular color as rendering space float rgb (0.5, 1.0, 0.0)
        :type color: list(float)
        """
        if self.setAttrColor(SPECULAR_COLOR_ATTR, color) is None:  # None is not settable/textured
            return
        self.specColorVal = color

    def specColor(self):
        """Returns the specular color

        :return color: Specular color as rendering space float rgb (0.5, 1.0, 0.0), None if textured/connected
        :rtype color: list(float)
        """
        color = self.getAttrColor(SPECULAR_COLOR_ATTR)
        if color is not None:
            self.specColorVal = color
        return color

    def setSpecRoughness(self, value):
        """Sets the specular roughness value

        :param value: The specular roughness value 0-1.0
        :type value: float
        """
        if self.setAttrScalar(SPECULAR_ROUGHNESS_ATTR, value) is None:  # None is not settable/textured
            return
        self.specRoughnessVal = value

    def specRoughness(self):
        """Returns the specular roughness value

        :return value: The specular roughness value 0-1.0, None if textured/connected
        :rtype value: float
        """
        color = self.getAttrScalar(SPECULAR_ROUGHNESS_ATTR)
        if color is not None:
            self.specRoughnessVal = color
        return color

    def setSpecIOR(self, value):
        """Sets the specular IOR value

        :param value: The specular IOR value, 1.0 - 20.0
        :type value: float
        """
        if self.setAttrScalar(SPECULAR_IOR_ATTR, value) is None:  # None is not settable/textured
            return
        self.specIORVal = value

    def specIOR(self):
        """Sets the specular IOR

        :return value: The specular IOR value, 1.0 - 20.0, None if textured/connected
        :rtype value: float
        """
        color = self.getAttrScalar(SPECULAR_IOR_ATTR)
        if color is not None:
            self.specIORVal = color
        return color

    def setCoatWeight(self, value):
        """Sets the clear coat weight

        :param value: The clear coat weight value 0-1.0
        :type value: float
        """
        if self.setAttrScalar(COAT_WEIGHT_ATTR, value) is None:  # None is not settable/textured
            return
        self.coatWeightVal = value

    def coatWeight(self):
        """Returns the clear coat weight

        :return value: The clear coat weight value 0-1.0, None if textured/connected
        :rtype value: float
        """
        color = self.getAttrScalar(COAT_WEIGHT_ATTR)
        if color is not None:
            self.coatWeightVal = color
        return color

    def setCoatColor(self, color):
        """Sets the clear coat color

        :param color: Clear coat color as rendering space float rgb (0.5, 1.0, 0.0)
        :type color: list(float)
        """
        if self.setAttrColor(COAT_COLOR_ATTR, color) is None:  # None is not settable/textured
            return
        self.coatColorVal = color

    def coatColor(self):
        """Returns the clear coat color

        :return color: Clear coat color as rendering space float rgb (0.5, 1.0, 0.0), None if textured/connected
        :rtype color: list(float)
        """
        color = self.getAttrColor(COAT_COLOR_ATTR)
        if color is not None:
            self.coatColorVal = color
        return color

    def setCoatRoughness(self, value):
        """Sets the clear coat roughness value

        :param value: The clear coat roughness value 0 -1.0
        :type value: float
        """
        if self.setAttrScalar(COAT_ROUGHNESS_ATTR, value) is None:  # None is not settable/textured
            return
        self.coatRoughnessVal = value

    def coatRoughness(self):
        """Returns the clear coat roughness value

        :return value: The clear coat roughness value 0 -1.0, None if textured/connected
        :rtype value: float
        """
        color = self.getAttrScalar(COAT_ROUGHNESS_ATTR)
        if color is not None:
            self.coatRoughnessVal = color
        return color

    def setCoatIOR(self, value):
        """Sets the clear coat IOR value

        :param value: The clear coat IOR value, 1.0 - 20.0
        :type value: float
        """
        if self.setAttrScalar(COAT_IOR_ATTR, value) is None:  # None is not settable/textured
            return
        self.coatIORVal = value

    def coatIOR(self):
        """Returns the clear coat IOR value

        :return value: The clear coat IOR value, 1.0 - 20.0, None if textured/connected
        :rtype value: float
        """
        color = self.getAttrScalar(COAT_IOR_ATTR)
        if color is not None:
            self.coatIORVal = color
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

    def setEmissionWeight(self, value):
        """Sets the emission weight value

        :param value: Emission weight value, 1.0 and above
        :type value: float
        """
        if self.setAttrScalar(EMISSION_WEIGHT_ATTR, value) is None:  # None is not settable/textured
            return
        self.emissionWeightVal = value

    def emissionWeight(self):
        """Returns the emission weight value

        :return value: Emission weight value, 1.0 and above, None if textured/connected
        :rtype value: float
        """
        value = self.getAttrScalar(EMISSION_WEIGHT_ATTR)
        if value is not None:
            self.emissionWeightVal = value
        return value
