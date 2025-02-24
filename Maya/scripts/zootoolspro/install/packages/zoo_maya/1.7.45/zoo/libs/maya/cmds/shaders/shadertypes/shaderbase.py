"""This module is the base class that creates and manages a shader with generic inputs.

This class is intended to be extended/overidden by each shader type.  Provides base functionality.

Example use overridden with mayastandardsurface:

.. code-block:: python

    from zoo.libs.maya.cmds.shaders.shadertypes import mayastandardsurface
    shadInst = mayastandardsurface.StandardSurface("shaderName", create=True)  # creates a new shader

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

    shadInst2 = mayastandardsurface.StandardSurface("rocketShader", ingest=True)  # Loads existing "rocketShader" as instance

    shadInst2.assignSelected()

    shadInst2.setShaderName("newNameY")
    print(shadInst2.shaderName())

    # Textures
    shadInst2.setDiffuseTexture("c:/somePath/aTexture.jpg", colorSpace="sRGB")

"""

import maya.cmds as cmds

from zoo.libs.utils import output
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.objutils import filtertypes, selection, namehandling, connections, nodemultibase
from zoo.libs.maya.utils import mayacolors
from zoo.libs.utils import color

from zoo.libs.maya.cmds.shaders import shaderutils, shdmultconstants
from zoo.libs.maya.cmds.shaders.shdmultconstants import DIFFUSE, DIFFUSEWEIGHT, SPECWEIGHT, SPECCOLOR, \
    SPECROUGHNESS, SPECIOR, COATCOLOR, COATWEIGHT, COATROUGHNESS, COATIOR, METALNESS, DIFFUSEROUGHNESS, EMISSION, \
    EMISSIONWEIGHT, DIFFUSE_DEFAULT, DIFFUSE_WEIGHT_DEFAULT, DIFFUSE_ROUGHNESS_DEFAULT, METALNESS_DEFAULT, \
    SPECULAR_DEFAULT, SPECULAR_WEIGHT_DEFAULT, ROUGHNESS_DEFAULT, IOR_DEFAULT, COAT_COLOR_DEFAULT, COAT_ROUGH_DEFAULT, \
    COAT_WEIGHT_DEFAULT, COAT_IOR_DEFAULT, EMISSION_DEFAULT, EMISSION_WEIGHT_DEFAULT

from zoo.libs.maya.cmds.textures import textures

NODE_TYPE = ""
SHADER_SUFFIX = ""
DIFFUSE_WEIGHT_ATTR = ""
DIFFUSE_COLOR_ATTR = ""
DIFFUSE_ROUGHNESS_ATTR = ""
METALNESS_ATTR = ""
SPECULAR_WEIGHT_ATTR = ""
SPECULAR_COLOR_ATTR = ""
SPECULAR_ROUGHNESS_ATTR = ""
SPECULAR_IOR_ATTR = ""
COAT_WEIGHT_ATTR = ""
COAT_COLOR_ATTR = ""
COAT_ROUGHNESS_ATTR = ""
COAT_IOR_ATTR = ""
EMISSION_ATTR = ""
EMISSION_WEIGHT_ATTR = ""
NORMAL_ATTR = ""
BUMP_ATTR = ""

OUT_COLOR = ""


class ShaderBase(nodemultibase.NodeMultiBase):
    """Main class that manages the creation setting and getting of attrs for a shader with generic inputs
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

        :param shader: The string name of the shader to load or create
        :type shader: str
        :param node: Optional zapi node object and will load not create the instance
        :type node: :class:`zapi.DGNode`
        :param genAttrDict: The generic attribute dictionary with attribute values to set only if creating
        :type genAttrDict: dict(str)
        :param create: If True then create a new shader False will load the shader nodes in the instance
        :type create: bool
        :param ingest: If True then create a new shader False will load the shader nodes in the instance
        :type ingest: bool
        :param suffixName: If True automatically suffix's the given name with the shader type suffix
        :type ingest: bool
        :param message: Report a message to the user only if creating
        :type message: bool
        """
        super(ShaderBase, self).__init__()
        self.attrDict = self.attributeNames()
        self.node = None
        # Ingest existing shader ----------------------------------
        if node and ingest:  # Passed in an existing zapi node
            self.shaderNameVal = node.fullPathName()
            self._allNodes(self.shaderNameVal)  # gets all nodes in the network and sets them
            self.pullShaderSettings()
            return
        if shaderName and ingest:  # Use the shader name to ingest into the instance
            self.shaderNameVal = shaderName
            self._allNodes(self.shaderNameVal)  # gets all nodes in the network and sets them
            self.pullShaderSettings()
            return
        # Naming ------------------------------------
        if not shaderName:
            self.shaderNameVal = "newShader"
        else:
            try:
                self.shaderNameVal = self._renameUniqueSuffixName(shaderName)  # handles unique names shad_01_SHD
            except AttributeError:  # No type set yet as shader not created
                self.shaderNameVal = shaderName
        # Create a new instance and possible new shader ------------------------------------
        # See also self.setDefaults()  # sets the shader default attributes.  Why don't I use the method?
        self.diffuseVal = DIFFUSE_DEFAULT
        self.diffuseWeightVal = DIFFUSE_WEIGHT_DEFAULT
        self.diffuseRoughnessVal = DIFFUSE_ROUGHNESS_DEFAULT
        self.metalnessVal = METALNESS_DEFAULT
        self.specColorVal = SPECULAR_DEFAULT
        self.specWeightVal = SPECULAR_WEIGHT_DEFAULT
        self.specRoughnessVal = ROUGHNESS_DEFAULT
        self.specIORVal = IOR_DEFAULT
        self.coatColorVal = COAT_COLOR_DEFAULT
        self.coatRoughnessVal = COAT_ROUGH_DEFAULT
        self.coatWeightVal = COAT_WEIGHT_DEFAULT
        self.coatIORVal = COAT_IOR_DEFAULT
        self.emissionVal = EMISSION_DEFAULT
        self.emissionWeightVal = EMISSION_WEIGHT_DEFAULT
        if suffixName:
            if not self.shaderNameVal.endswith("_{}".format(self.suffix)):  # already suffixed
                name = "_".join([self.shaderNameVal, self.suffix])
                self.shaderNameVal = self._renameUniqueSuffixName(name)
        if create:  # Create a new shader -----------------
            self.createShader(message=message)
        if genAttrDict:  # override the dictionary values
            self.setFromDict(genAttrDict, apply=False)
        if create:
            self.applyCurrentSettings()

    # -------------------
    # Base Methods
    # -------------------

    def exists(self):
        """Tests to see if the shader connected to the instance exists

        :return: True if the shader exists in the scene, False if not.
        :rtype: bool
        """
        try:
            self.node.fullPathName()
            return True
        except (AttributeError, RuntimeError) as e:  # shader has been deleted or not created
            return False

    def shaderType(self):
        """Returns the type of the shader node. Must have been created

        :return:  The type of the current shader, must be alive. Eg. "standardSurface"
        :rtype: str
        """
        return cmds.nodeType(self.node.fullPathName())

    def knownShader(self):
        """Returns True if the shader is supported by Zoo Tools, should be overridden

        :return: Returns True if the shader is supported by Zoo Tools, should be overridden
        :rtype: bool
        """
        return False

    def renderer(self):
        """Returns the current renderer as a string.  Should be overridden.

        :return: Returns the current renderer as a string, will be "" if the renderer unknown.
        :rtype:
        """
        return shdmultconstants.UNKNOWN

    def attributeNames(self):
        """Generic attributes are the keys and the shader's attributes are the values.

        :return: A dictionary with strings as keys and attribute string names as values.
        :rtype: dict
        """
        return {DIFFUSE: self.diffuseColorAttr,
                DIFFUSEWEIGHT: self.diffuseWeightAttr,
                DIFFUSEROUGHNESS: self.diffuseRoughnessAttr,
                METALNESS: self.metalnessAttr,
                SPECWEIGHT: self.specularWeightAttr,
                SPECCOLOR: self.specularColorAttr,
                SPECROUGHNESS: self.specularRoughnessAttr,
                SPECIOR: self.specularIorAttr,
                COATCOLOR: self.coatcolorAttr,
                COATWEIGHT: self.coatWeightAttr,
                COATROUGHNESS: self.coatRoughnessAttr,
                COATIOR: self.coatIorAttr,
                EMISSION: self.emissionAttr,
                EMISSIONWEIGHT: self.emissionWeightAttr
                }

    def unsupportedAttributes(self):
        """Returns the generic attribute keys that are not supported by this shader.

        :return: A list of generic attributes that are not supported by this shader.
        :rtype: list(str)
        """
        unsupportedAttrs = list()
        for key in self.attrDict:
            if not self.attrDict[key]:  # if ""
                unsupportedAttrs.append(key)
        return unsupportedAttrs

    def supportedAttributes(self):
        """Returns the generic attribute keys that are supported by this shader.

        :return: A list of generic attributes that are supported by this shader.
        :rtype: list(str)
        """
        supportedAttrs = list()
        for key in self.attrDict:
            if self.attrDict[key]:
                supportedAttrs.append(key)
        return supportedAttrs

    def setDefaults(self, apply=False):
        """Sets the shader to default values internally, the shader does not need to be created unless apply=True

        :param apply: If True then apply the settings to the shader, otherwise is just changed in the class instance.
        :type apply: bool
        """
        self.diffuseVal = DIFFUSE_DEFAULT
        self.diffuseWeightVal = DIFFUSE_WEIGHT_DEFAULT
        self.diffuseRoughnessVal = DIFFUSE_WEIGHT_DEFAULT
        self.metalnessVal = METALNESS_DEFAULT
        self.specColorVal = SPECULAR_DEFAULT
        self.specWeightVal = SPECULAR_WEIGHT_DEFAULT
        self.specRoughnessVal = ROUGHNESS_DEFAULT
        self.specIORVal = IOR_DEFAULT
        self.coatColorVal = COAT_COLOR_DEFAULT
        self.coatRoughnessVal = COAT_ROUGH_DEFAULT
        self.coatWeightVal = COAT_WEIGHT_DEFAULT
        self.coatIORVal = COAT_IOR_DEFAULT
        self.emissionVal = EMISSION_DEFAULT
        self.emissionWeightVal = EMISSION_WEIGHT_DEFAULT
        if apply:
            self.applyCurrentSettings()

    def applyCurrentSettings(self):
        """Applies the current class variables and sets them on the shader. """
        self.setDiffuse(self.diffuseVal)
        self.setDiffuseWeight(self.diffuseWeightVal)
        self.setDiffuseRoughness(self.diffuseRoughnessVal)
        self.setMetalness(self.metalnessVal)
        self.setSpecColor(self.specColorVal)
        self.setSpecWeight(self.specWeightVal)
        self.setSpecRoughness(self.specRoughnessVal)
        self.setSpecIOR(self.specIORVal)
        self.setCoatColor(self.coatColorVal)
        self.setCoatRoughness(self.coatRoughnessVal)
        self.setCoatWeight(self.coatWeightVal)
        self.setCoatIOR(self.coatIORVal)
        self.setEmission(self.emissionVal)
        self.setEmissionWeight(self.emissionWeightVal)

    def pullShaderSettings(self):
        """Pulls the current attribute values from the current shader. The shader must exist."""
        self.diffuseVal = self.diffuse()
        self.diffuseWeightVal = self.diffuseWeight()
        self.diffuseRoughnessVal = self.diffuseRoughness()
        self.metalnessVal = self.metalness()
        self.specColorVal = self.specColor()
        self.specWeightVal = self.specWeight()
        self.specRoughnessVal = self.specRoughness()
        self.specIORVal = self.specIOR()
        self.coatColorVal = self.coatColor()
        self.coatRoughnessVal = self.coatRoughness()
        self.coatWeightVal = self.coatWeight()
        self.coatIORVal = self.coatIOR()
        self.emissionVal = self.emission()
        self.emissionWeightVal = self.emissionWeight()

    def _allNodes(self, shader):
        """Gets all the node/s from the shader name and sets as class variables.

        :param shader: The name of the shader
        :type shader: str
        """
        if cmds.objExists(shader):
            self.node = zapi.nodeByName(shader)
        else:
            self.node = None
        self.node = self.node
        # override if need to add more nodes

    # -------------------
    # Attributes And Texture Checks
    # -------------------

    def setAttrColor(self, attributeName, color):
        """Sets a color attribute, returns None if textured or unusable.

        :param attributeName: The maya attribute name
        :type attributeName: str
        :param color: A color as rendering space float (0.5, 0.5, 0.5)
        :type color: list(float)
        :return: True if the attribute was set, False if not due to textured or locked
        :rtype: bool
        """
        if not self.attrSettable(attributeName):
            return False
        cmds.setAttr(".".join([self.node.fullPathName(), attributeName]),
                     color[0], color[1], color[2],
                     type="double3")
        return True

    def setAttrScalar(self, attributeName, value):
        """Sets a scalar single value attribute, returns None if textured/connected.

        :param attributeName: The maya attribute name
        :type attributeName: str
        :param value: A single float value
        :type value: float
        :return: True if the attribute was set, False if not due to textured or locked
        :rtype: bool
        """
        if not self.attrSettable(attributeName):
            return False
        cmds.setAttr(".".join([self.node.fullPathName(), attributeName]), value)
        return True

    def getAttrColor(self, attributeName):
        """Gets the color of an attribute, returns None if textured/connected.

        :param attributeName: The maya attribute name
        :type attributeName: str
        :return:  The color returned, if textured or locked returns None
        :rtype: list(float)
        """
        return cmds.getAttr(".".join([self.node.fullPathName(), attributeName]))[0]

    def getAttrScalar(self, attributeName):
        """Gets the value of an float or int attribute

        :param attributeName: The maya attribute name
        :type attributeName: str
        :return: The value returned, if textured of locked returns None
        :rtype: float or int
        """
        return cmds.getAttr(".".join([self.node.fullPathName(), attributeName]))

    def attrSettable(self, attributeName):
        """Tests if the attribute name is settable, if False it's textured or locked.

        :param attributeName: The maya attribute name
        :type attributeName: str
        :return settable: True and the attribute is settable, False and the attribute is locked or textured
        :rtype settable: str
        """
        return cmds.getAttr(".".join([self.node.fullPathName(), attributeName]), settable=True)

    def attrDisconnectTexture(self, attributeName):
        """Disconnects a texture.  Should be overridden.

        :param attributeName: The name of an attribute to disconnect.
        :type attributeName: str
        """
        pass

    # -------------------
    # Create Assign Delete Select
    # -------------------

    def createShader(self, message=True):
        """Creates the shader.  Should be overridden.

        :param message: Report a message to the user?
        :type message: bool
        """
        pass

    def deleteShader(self):
        """Deletes the shader.

        Should be overridden if multiple nodes in the shader need to be deleted.
        """
        cmds.delete(self.node.fullPathName())
        self.node = None

    def assign(self, objFaceList, message=False):
        """Assigns the current shader to an object list.

        :param objFaceList: A list of Maya objects
        :type objFaceList: list(str)
        :param message: report a message to the user?
        :type message: bool
        :return: returns True if the assign was successful
        :rtype: bool
        """
        if not self.exists():
            if message:
                output.displayWarning("Shader does not exist")
            return False
        shaderutils.assignShader(objFaceList, self.shaderName())

    def assignSelected(self, message=False):
        """Assign the shader to the current selection.

        :param message: report a message to the user?
        :type message: bool
        :return: returns True if the assign was successful
        :rtype: bool
        """
        if not self.exists():
            if message:
                output.displayWarning("Shader does not exist")
            return False
        selGeo = cmds.ls(selection=True)
        if selGeo:  # Filter just geometry
            meshObjs = filtertypes.filterTypeReturnTransforms(selGeo, children=False, shapeType="mesh")
            nurbsObjs = filtertypes.filterTypeReturnTransforms(selGeo, children=False, shapeType="nurbsSurface")
            faceSelection = selection.componentSelectionFilterType(selGeo, selectType="faces")
            selGeo = meshObjs + nurbsObjs + faceSelection
        if not selGeo:
            if message:
                output.displayWarning("No geometry objects are selected, please select.")
            return
        shaderutils.assignShaderSelected(self.shaderName())
        if message:
            output.displayInfo("Shader assigned `{}`.".format(self.shaderName()))

    def selectShader(self, message=True):
        """Selects the current shader inside Maya, can be viewed in the Attribute Editor.

        :param message: Report a message to the user?
        :type message: bool
        """
        if not self.exists():
            if message:
                output.displayWarning("This shader does not exist in the scene")
            return
        cmds.select(self.shaderName(), replace=True)
        if message:
            output.displayInfo("Shader selected")

    # -------------------
    # Setters Getters - Misc
    # -------------------

    def _setDictSingle(self, genAttrDict, dictKey, classValue, defaultValue, noneIsDefault):
        """Method for handling None or missing keys in a genAttrDict.

        :param genAttrDict: The generic attr dict
        :type genAttrDict: dict
        :param dictKey: dictionary keys eg "gDiffuse"
        :type dictKey: str
        :param classValue: the current class value eg. self.diffuseVal
        :type classValue: float or list(float)
        :param defaultValue: the default value for this attribute
        :type defaultValue: float or list(float)
        :param noneIsDefault: If None or not found then set the attribute to it's default value, if not leave it.
        :type noneIsDefault: bool
        :return: The value of the attribute now potentially corrected.
        :rtype: float or list(float)
        """
        if dictKey in genAttrDict:
            if genAttrDict[dictKey] is not None:
                classValue = genAttrDict[dictKey]
            elif noneIsDefault:
                classValue = defaultValue
        elif noneIsDefault:
            classValue = defaultValue
        return classValue

    def setFromDict(self, genAttrDict, apply=True, noneIsDefault=True, colorsAreSrgb=False):
        """Sets the shader from a generic attribute dictionary. Values as attribute values.

        Colors are linear by default, use the colorsAreSrgb flag if SRGB.

        Handles None-values in the dictionary and also missing keys.

        None-values and missing keys can either pass or be replaced with default values.

        :param genAttrDict: The generic attribute dictionary with values as attribute values
        :type genAttrDict: dict(str)
        :param apply: Will apply the dict to the current shader, must exist
        :type apply: bool
        :param noneIsDefault: Will apply defaults if the value of the key is None
        :type noneIsDefault: bool
        :param colorsAreSrgb: Set to True if the incoming colors are SRGB such as from a UI.
        :type colorsAreSrgb: bool
        """
        if colorsAreSrgb:
            genAttrDict = self.convertDictDisplay(genAttrDict)  # was previously SRGB but didn't handle ACES

        # BASE --------------------
        self.diffuseWeightVal = self._setDictSingle(genAttrDict,
                                                    DIFFUSEWEIGHT,
                                                    self.diffuseWeightVal,
                                                    DIFFUSE_WEIGHT_DEFAULT,
                                                    noneIsDefault)
        self.diffuseVal = self._setDictSingle(genAttrDict,
                                              DIFFUSE,
                                              self.diffuseVal,
                                              DIFFUSE_DEFAULT,
                                              noneIsDefault)
        self.diffuseRoughnessVal = self._setDictSingle(genAttrDict,
                                                       DIFFUSEROUGHNESS,
                                                       self.diffuseRoughnessVal,
                                                       DIFFUSE_ROUGHNESS_DEFAULT,
                                                       noneIsDefault)
        self.metalnessVal = self._setDictSingle(genAttrDict,
                                                METALNESS,
                                                self.metalnessVal,
                                                METALNESS_DEFAULT,
                                                noneIsDefault)
        # SPECULAR --------------------
        self.specWeightVal = self._setDictSingle(genAttrDict,
                                                 SPECWEIGHT,
                                                 self.specWeightVal,
                                                 SPECULAR_WEIGHT_DEFAULT,
                                                 noneIsDefault)
        self.specColorVal = self._setDictSingle(genAttrDict,
                                                SPECCOLOR,
                                                self.specColorVal,
                                                SPECULAR_DEFAULT,
                                                noneIsDefault)
        self.specRoughnessVal = self._setDictSingle(genAttrDict,
                                                    SPECROUGHNESS,
                                                    self.specRoughnessVal,
                                                    ROUGHNESS_DEFAULT,
                                                    noneIsDefault)
        self.specIORVal = self._setDictSingle(genAttrDict,
                                              SPECIOR,
                                              self.specIORVal,
                                              IOR_DEFAULT,
                                              noneIsDefault)
        # COAT --------------------
        self.coatColorVal = self._setDictSingle(genAttrDict,
                                                COATCOLOR,
                                                self.coatColorVal,
                                                COAT_COLOR_DEFAULT,
                                                noneIsDefault)
        self.coatRoughnessVal = self._setDictSingle(genAttrDict,
                                                    COATROUGHNESS,
                                                    self.coatRoughnessVal,
                                                    COAT_ROUGH_DEFAULT,
                                                    noneIsDefault)
        self.coatWeightVal = self._setDictSingle(genAttrDict,
                                                 COATWEIGHT,
                                                 self.coatWeightVal,
                                                 COAT_WEIGHT_DEFAULT,
                                                 noneIsDefault)
        self.coatIORVal = self._setDictSingle(genAttrDict,
                                              COATIOR,
                                              self.coatIORVal,
                                              COAT_IOR_DEFAULT,
                                              noneIsDefault)
        # EMISSION --------------------
        self.emissionVal = self._setDictSingle(genAttrDict,
                                               EMISSION,
                                               self.emissionVal,
                                               EMISSION_DEFAULT,
                                               noneIsDefault)
        self.emissionWeightVal = self._setDictSingle(genAttrDict,
                                                     EMISSIONWEIGHT,
                                                     self.emissionWeightVal,
                                                     EMISSION_WEIGHT_DEFAULT,
                                                     noneIsDefault)
        # APPLY ------------------------
        if apply:
            self.applyCurrentSettings()

    def shaderValues(self, removeNone=False, convertToDisplay=False):
        """Returns values of the shader attribute in a generic shader dictionary, keys are from shdmultconstants

        Color values are all as rendering space color.

        :return: A dictionary of generic shader keys with values as per shdmultconstants
        :rtype: dict(str)
        """
        genAttrDict = dict()
        genAttrDict[DIFFUSE] = self.diffuse()
        genAttrDict[DIFFUSEWEIGHT] = self.diffuseWeight()
        genAttrDict[DIFFUSEROUGHNESS] = self.diffuseRoughness()
        genAttrDict[METALNESS] = self.metalness()
        genAttrDict[SPECWEIGHT] = self.specWeight()
        genAttrDict[SPECCOLOR] = self.specColor()
        genAttrDict[SPECROUGHNESS] = self.specRoughness()
        genAttrDict[SPECIOR] = self.specIOR()
        genAttrDict[COATCOLOR] = self.coatColor()
        genAttrDict[COATWEIGHT] = self.coatWeight()
        genAttrDict[COATROUGHNESS] = self.coatRoughness()
        genAttrDict[COATIOR] = self.coatIOR()
        genAttrDict[EMISSION] = self.emission()
        genAttrDict[EMISSIONWEIGHT] = self.emissionWeight()

        if convertToDisplay:
            genAttrDict = self.convertDictRendering(genAttrDict)

        if removeNone:  # removes None key/values from dict
            filtered = {k: v for k, v in genAttrDict.items() if v is not None}
            genAttrDict.clear()
            genAttrDict.update(filtered)
        return genAttrDict

    def convertDictSrgb(self, genAttrDict):
        """Converts a shader value dictionary from linear to srgb colors.

        :return: A dictionary of generic shader keys with values as per shdmultconstants
        :rtype: dict(str)
        """
        if genAttrDict[DIFFUSE] is not None:
            genAttrDict[DIFFUSE] = color.convertColorLinearToSrgb(genAttrDict[DIFFUSE])
        if genAttrDict[SPECCOLOR] is not None:
            genAttrDict[SPECCOLOR] = color.convertColorLinearToSrgb(genAttrDict[SPECCOLOR])
        if genAttrDict[COATCOLOR] is not None:
            genAttrDict[COATCOLOR] = color.convertColorLinearToSrgb(genAttrDict[COATCOLOR])
        if EMISSION in genAttrDict:
            if genAttrDict[EMISSION] is not None:
                genAttrDict[EMISSION] = color.convertColorLinearToSrgb(genAttrDict[EMISSION])
        return genAttrDict

    def convertDictLinear(self, genAttrDict):
        """Converts a shader value dictionary from srgb to linear colors

        :return: A dictionary of generic shader keys with values as per shdmultconstants
        :rtype: dict(str)
        """
        if genAttrDict[DIFFUSE] is not None:
            genAttrDict[DIFFUSE] = color.convertColorSrgbToLinear(genAttrDict[DIFFUSE])
        if genAttrDict[SPECCOLOR] is not None:
            genAttrDict[SPECCOLOR] = color.convertColorSrgbToLinear(genAttrDict[SPECCOLOR])
        if genAttrDict[COATCOLOR] is not None:
            genAttrDict[COATCOLOR] = color.convertColorSrgbToLinear(genAttrDict[COATCOLOR])
        if EMISSION in genAttrDict:
            if genAttrDict[EMISSION] is not None:
                genAttrDict[EMISSION] = color.convertColorSrgbToLinear(genAttrDict[EMISSION])
        return genAttrDict

    def convertDictRendering(self, genAttrDict):
        """Converts a shader value dictionary from rendering color to display space colors

        :return: A dictionary of generic shader keys with values as per shdmultconstants
        :rtype: dict(str)
        """
        if genAttrDict[DIFFUSE] is not None:
            genAttrDict[DIFFUSE] = mayacolors.renderingColorToDisplaySpace(genAttrDict[DIFFUSE])
        if genAttrDict[SPECCOLOR] is not None:
            genAttrDict[SPECCOLOR] = mayacolors.renderingColorToDisplaySpace(genAttrDict[SPECCOLOR])
        if genAttrDict[COATCOLOR] is not None:
            genAttrDict[COATCOLOR] = mayacolors.renderingColorToDisplaySpace(genAttrDict[COATCOLOR])
        if EMISSION in genAttrDict:
            if genAttrDict[EMISSION] is not None:
                genAttrDict[EMISSION] = mayacolors.renderingColorToDisplaySpace(genAttrDict[EMISSION])
        return genAttrDict

    def convertDictDisplay(self, genAttrDict):
        """Converts a shader value dictionary from display color to rendering space colors

        :return: A dictionary of generic shader keys with values as per shdmultconstants
        :rtype: dict(str)
        """
        if genAttrDict[DIFFUSE] is not None:
            genAttrDict[DIFFUSE] = mayacolors.displayColorToCurrentRenderingSpace(genAttrDict[DIFFUSE])
        if genAttrDict[SPECCOLOR] is not None:
            genAttrDict[SPECCOLOR] = mayacolors.displayColorToCurrentRenderingSpace(genAttrDict[SPECCOLOR])
        if genAttrDict[COATCOLOR] is not None:
            genAttrDict[COATCOLOR] = mayacolors.displayColorToCurrentRenderingSpace(genAttrDict[COATCOLOR])
        if EMISSION in genAttrDict:
            if genAttrDict[EMISSION] is not None:
                genAttrDict[EMISSION] = mayacolors.displayColorToCurrentRenderingSpace(genAttrDict[EMISSION])
        return genAttrDict

    def addSuffix(self):
        """Adds the automatic suffix of the renderer eg _STRD to the shaders name, suffixes are per shaderType

        :return renamed: True if the name was changed, False if not.
        :rtype renamed: bool
        """
        name = self.node.fullPathName()
        if name.endswith("_{}".format(self.suffix)):  # already suffixed
            return False
        newNameNotUnique = self._renameUniqueSuffixName(self.node.fullPathName())
        self.shaderNameVal = cmds.rename(self.node.fullPathName(), newNameNotUnique)
        return True

    def removeSuffix(self):
        """Removes the auto suffix on a shader name:

            shader_01_ARN if not unique becomes shader_01

        :return shaderName: The potentially changed shader name
        :rtype shaderName: str
        """
        if not self.suffix:  # is ""
            return self.node.fullPathName()
        name = self.node.fullPathName()
        name = name.removesuffix("_{}".format(self.suffix))
        self.shaderNameVal = cmds.rename(self.node.fullPathName(), name)
        return self.shaderNameVal

    def _renameUniqueSuffixName(self, newName, addSuffix=True):
        """Auto handles suffixing with the shader type and unique names:

            shader_01_ARN if not unique becomes shader_02_ARN

        :param newName: The name to rename the current shader
        :type newName: ste
        :param addSuffix: Make unique but don't worry about suffix names if they don't exist
        :type addSuffix: bool
        :return: The new name of the shader with auto suffix handled
        :rtype: str
        """
        if not self.suffix:  # is ""
            return newName
        if not newName.endswith("_{}".format(self.suffix)):  # not suffixed
            if not addSuffix:
                return namehandling.getUniqueNamePadded(newName)
            newName = "_".join([self.node.fullPathName(), self.suffix])
        return namehandling.getUniqueNameSuffix(newName, self.suffix, paddingDefault=2, nameAlreadySuffixed=True)

    def setShaderName(self, newName, uniqueNumberSuffix=True, addSuffix=True):
        """Renames the shader, auto handles suffixing with the shader type and unique names:

            shader_01_ARN if not unique becomes shader_02_ARN

        :param newName: The name to rename the current shader
        :type newName: ste
        :param uniqueNumberSuffix: shader_01_ARN if not unique becomes shader_02_ARN or next unique name
        :type uniqueNumberSuffix:
        :param addSuffix:
        :type addSuffix:
        :return: The new name of the shader
        :rtype: str
        """
        if self.exists():
            if uniqueNumberSuffix:
                newName = self._renameUniqueSuffixName(newName, addSuffix=addSuffix)
            shaderName = cmds.rename(self.node.fullPathName(), newName)
            self.shaderNameVal = shaderName
        else:
            if uniqueNumberSuffix:
                newName = self._renameUniqueSuffixName(newName)
            self.shaderNameVal = newName
        return self.shaderNameVal

    def shaderName(self):
        """Returns and updates the shader's name.

        :return: The name of the current shader
        :rtype: str
        """
        if self.exists():
            self.shaderNameVal = self.node.fullPathName()
            return self.shaderNameVal
        else:
            return self.shaderNameVal

    def shaderNameNoSuffix(self):
        """Returns and updates the shader's name with the type suffix removed if exists:

            "shaderName_PXR" becomes "shaderName"
            "shaderX" is ignored as not shaderType match so "shaderX"

        :return: The name of the current shader without it's type suffix
        :rtype: str
        """
        name = str(self.shaderName())  # duplicate for safety
        if not name:
            return name
        suffix = shdmultconstants.SHADERTYPE_SUFFIX_DICT[self.shaderType()]
        shaderList = name.split("_")
        if suffix == shaderList[-1]:
            return "_".join(shaderList[:-1])
        return name

    # -------------------
    # Setters Getters - Attributes
    # -------------------

    def srgbColor(self, linearColor):
        """Converts linear color to SRGB and handles potential None values.

        returns: SRGB Color float eg [0.0, 0.5, 1.0]

        :param linearColor: Float color as rendering space space eg [0.0, 0.5, 1.0]
        :type linearColor: list(float)
        :return: Color now converted to srgb space or None if was no color given. eg [0.0, 0.6, 0.9]
        :rtype: list(float)
        """
        if linearColor:
            return color.convertColorLinearToSrgb(linearColor)
        return None

    def displayColor(self, renderingColor):
        """Converts the rendering space color (Maya's default color) to the display space color.

        :param renderingColor: Maya's default color space for the current mode. Float color
        :type renderingColor: list(float)
        :return displayColor: The color converted to display space usually srgb.  Float color
        :rtype displayColor: list(float)
        """
        if renderingColor:
            return mayacolors.renderingColorToDisplaySpace(renderingColor)

    # ------------------
    # DIFFUSE COLOR
    # ------------------

    def setDiffuse(self, value):
        """Sets the diffuse color as rendering space color space.

        Should be overridden.

        :param value: Float color as rendering space space (0.5, 1.0, 0.0)
        :type value: list(float)
        """
        pass

    def setDiffuseSrgb(self, value):
        """Sets the diffuse color with srgb color space, converts to linear.

        Color space is handled as rendering space space by default inside the class.

        :param value: Float color in srgb space (0.5, 1.0, 0.0) will be converted to linear color
        :type value: list(float)
        """
        self.setDiffuse(color.convertColorSrgbToLinear(value))

    def setDiffuseDisplay(self, value):
        """Sets the diffuse color with the display color space, converts to rendering space.

        Maya 2023 and above otherwise will take the color as linear and set as srgb

        :param value: Float color in display space (0.5, 1.0, 0.0) will be converted to rendering space
        :type value: list(float)
        """
        self.setDiffuse(mayacolors.displayColorToCurrentRenderingSpace(value))

    def diffuse(self):
        """Returns the diffuse color in float linear color space or None if ignored.

        Should be overridden

        :param value: Diffuse color as rendering space space (0.5, 1.0, 0.0). None if not found.
        :type value: list(float)
        """
        return None

    def diffuseSrgb(self):
        """Returns the diffuse color in float srgb color space or None if ignored.

        :return: Float color in srgb space (0.5, 1.0, 0.0) or None if ignored
        :rtype: list(float)
        """
        return self.srgbColor(self.diffuse())

    def diffuseDisplay(self):
        """Returns the diffuse color in display space usually srgb or None if ignored.

        Maya 2023 and above otherwise will convert linear to srgb

        :return: Float color in monitor display space (0.5, 1.0, 0.0) or None if ignored
        :rtype: list(float)
        """
        return self.displayColor(self.diffuse())

    # ------------------
    # DIFFUSE WEIGHT
    # ------------------

    def setDiffuseWeight(self, value):
        """Sets the diffuse weight.

        Should be overridden.

        :param value: The numeric value of the diffuse weight.
        :type value: float
        """
        pass

    def diffuseWeight(self):
        """Returns the diffuse weight value or None if ignored.

        Should be overridden.

        :return: The Diffuse weight value, None if not found.
        :rtype: float
        """
        return None

    # ------------------
    # DIFFUSE ROUGHNESS
    # ------------------

    def setDiffuseRoughness(self, value):
        """Sets the diffuse roughness value.

        Should be overridden.

        :param value: The numeric value of the diffuse roughness.
        :type value: float
        """
        pass

    def diffuseRoughness(self):
        """Returns the diffuse roughness value or None if ignored.

        Should be overridden.

        :return: The Diffuse weight value, None if not found.
        :rtype: float
        """
        return None

    # ------------------
    # METALNESS
    # ------------------

    def setMetalness(self, value):
        """Sets the metalness value.

        Should be overridden.

        :param value: The numeric value of the metalness.
        :type value: float
        """
        pass

    def metalness(self):
        """Returns the metalness value or None if ignored.

        Should be overridden.

        :return: The Diffuse weight value, None if not found.
        :rtype: float
        """
        return None

    # ------------------
    # METALNESS
    # ------------------

    def setSpecWeight(self, value):
        """Sets the specular weight value.

        Should be overridden.

        :param value: The numeric value of the specular weight.
        :type value: float
        """
        pass

    def specWeight(self):
        """Returns the specular weight value or None if ignored.

        Should be overridden.

        :return: The specular weight weight value, None if not found.
        :rtype: float
        """
        return None

    # ------------------
    # SPECULAR COLOR
    # ------------------

    def setSpecColor(self, value):
        """Returns the specular color in float linear color space or None if ignored.

        :return: Float color as rendering space space (0.5, 1.0, 0.0) or None if ignored
        :rtype: list(float)
        """
        pass

    def setSpecColorSrgb(self, value):
        """Sets the spec color with srgb color space, converts to linear.

        Color space is handled as rendering space space by default inside the class.

        :param value: Float color in srgb space (0.5, 1.0, 0.0) will be converted to linear color.
        :type value: list(float)
        """
        self.setSpecColor(color.convertColorSrgbToLinear(value))

    def setSpecColorDisplay(self, value):
        """Sets the specular color with the display color space, converts to rendering space.

        Maya 2023 and above otherwise will take the color as linear and set as srgb

        :param value: Float color in display space (0.5, 1.0, 0.0) will be converted to rendering space
        :type value: list(float)
        """
        self.setSpecColor(mayacolors.displayColorToCurrentRenderingSpace(value))

    def specColor(self):
        """Sets the specular color as rendering space color space.

        Should be overridden.

        :param value: Float color as rendering space space (0.5, 1.0, 0.0)
        :type value: list(float)
        """
        return None

    def specColorSrgb(self):
        """Returns the specular color in float srgb color space or None if ignored.

        :return srgbColor: Float color in srgb space (0.5, 1.0, 0.0) or None if ignored
        :rtype srgbColor: list(float)
        """
        return self.srgbColor(self.specColor())

    def specColorDisplay(self):
        """Returns the diffuse color in monitor display space usually srgb or None if ignored.

        Maya 2023 and above otherwise will convert linear to srgb

        :return: Float color in display space (0.5, 1.0, 0.0) or None if ignored
        :rtype: list(float)
        """
        return self.displayColor(self.specColor())

    # ------------------
    # SPECULAR ROUGHNESS
    # ------------------

    def setSpecRoughness(self, value):
        """Sets the specular roughness value.

        Should be overridden.

        :param value: The numeric value of the specular roughness.
        :type value: float
        """
        pass

    def specRoughness(self):
        """Returns the specular roughness value or None if ignored.

        Should be overridden.

        :return: The specular roughness weight value, None if not found.
        :rtype: float
        """
        return None

    # ------------------
    # SPECULAR IOR
    # ------------------

    def setSpecIOR(self, value):
        """Sets the specular IOR value.

        Should be overridden.

        :param value: The numeric value of the specular IOR.
        :type value: float
        """
        pass

    def specIOR(self):
        """Returns the specular IOR value or None if ignored.

        Should be overridden.

        :return: The specular weight value, None if not found.
        :rtype: float
        """
        return None

    # ------------------
    # COAT COLOR
    # ------------------

    def setCoatColor(self, value):
        """Returns the clear coat color in float linear color space or None if ignored.

        :return: Float color as rendering space space (0.5, 1.0, 0.0) or None if ignored
        :rtype: list(float)
        """
        pass

    def setCoatColorSrgb(self, value):
        """Sets the coat color with srgb color space, converts to linear.
        Color space is handled as rendering space space by default inside the class.

        :param value: Float color in srgb space (0.5, 1.0, 0.0) will be converted to linear color
        :type value: list(float)
        """
        self.setCoatColor(color.convertColorSrgbToLinear(value))

    def setCoatColorDisplay(self, value):
        """Sets the coat color with the display color space, converts to rendering space.

        Maya 2023 and above otherwise will take the color as linear and set as srgb

        :param value: Float color in display space (0.5, 1.0, 0.0) will be converted to rendering space
        :type value: list(float)
        """
        self.setCoatColor(mayacolors.displayColorToCurrentRenderingSpace(value))

    def coatColor(self):
        """Sets the specular coat color as rendering space color space.

        Should be overridden.

        :param value: Float color as rendering space space (0.5, 1.0, 0.0)
        :type value: list(float)
        """
        return None

    def coatColorSrgb(self):
        """Returns the coat color in float srgb color space or None if ignored.

        :return srgbColor: Float color in srgb space (0.5, 1.0, 0.0) or None if ignored
        :rtype srgbColor: list(float)
        """
        return self.srgbColor(self.coatColor())

    def coatColorDisplay(self):
        """Returns the coat color in monitor display space usually srgb or None if ignored.

        Maya 2023 and above otherwise will convert linear to srgb

        :return: Float color in display space (0.5, 1.0, 0.0) or None if ignored
        :rtype: list(float)
        """
        return self.displayColor(self.coatColor())

    # ------------------
    # COAT WEIGHT
    # ------------------

    def setCoatWeight(self, value):
        """Sets the clear coat weight value.

        Should be overridden.

        :param value: The numeric value of the clear coat weight.
        :type value: float
        """
        pass

    def coatWeight(self):
        """Returns the clear coat weight value or None if ignored.

        Should be overridden.

        :return: The clear coat weight value, None if not found.
        :rtype: float
        """
        return None

    # ------------------
    # COAT ROUGHNESS
    # ------------------

    def setCoatRoughness(self, value):
        """Sets the clear coat roughness value.

        Should be overridden.

        :param value: The numeric value of the clear coat roughness.
        :type value: float
        """
        pass

    def coatRoughness(self):
        """Returns the clear coat roughness value or None if ignored.

        Should be overridden.

        :return: The clear coat roughness weight value, None if not found.
        :rtype: float
        """
        return None

    # ------------------
    # COAT IOR
    # ------------------

    def setCoatIOR(self, value):
        """Sets the clear coat IOR value.

        Should be overridden.

        :param value: The numeric value of the clear coat IOR.
        :type value: float
        """
        pass

    def coatIOR(self):
        """Returns the clear coat IOR value or None if ignored.

        Should be overridden.

        :return: The clear coat IOR weight value, None if not found.
        :rtype: float
        """
        return None

    # ------------------
    # EMISSION COLOR
    # ------------------

    def setEmission(self, value):
        """Returns the emission color in float linear color space or None if ignored.

        :return: Float color as rendering space space (0.5, 1.0, 0.0) or None if ignored
        :rtype: list(float)
        """
        pass

    def setEmissionSrgb(self, value):
        """Sets the emission color with srgb color space, converts to linear.

        Color space is handled as rendering space space by default inside the class.

        :param value: Float color in srgb space (0.5, 1.0, 0.0) will be converted to linear color
        :type value: list(float)
        """
        self.setEmission(color.convertColorSrgbToLinear(value))

    def setEmissionDisplay(self, value):
        """Sets the emission color with the display color space, converts to rendering space.

        Maya 2023 and above otherwise will take the color as linear and set as srgb

        :param value: Float color in display space (0.5, 1.0, 0.0) will be converted to rendering space
        :type value: list(float)
        """
        self.setEmission(mayacolors.displayColorToCurrentRenderingSpace(value))

    def emission(self):
        """Returns the emission color in rendering color space.

        Should be overridden.

        :param value: Float color as rendering space space (0.5, 1.0, 0.0)
        :type value: list(float)
        """
        return None

    def emissionSrgb(self):
        """Returns the emission color in float srgb color space.

        :return srgbColor: Float color in srgb space (0.5, 1.0, 0.0) or None if ignored
        :rtype srgbColor: list(float)
        """
        return self.srgbColor(self.emission())

    def emissionDisplay(self):
        """Returns the coat color in monitor display space usually srgb or None if ignored.

        Maya 2023 and above otherwise will convert linear to srgb

        :return: Float color in display space (0.5, 1.0, 0.0) or None if ignored
        :rtype: list(float)
        """
        return self.displayColor(self.emission())

    # ------------------
    # EMISSION WEIGHT
    # ------------------

    def setEmissionWeight(self, value):
        """Sets the emission weight value.

        Should be overridden.

        :param value: The numeric value of the emission weight.
        :type value: float
        """
        pass

    def emissionWeight(self):
        """Returns the emission weight value or None if ignored.

        Should be overridden.

        :return: The Diffuse weight value, None if not found.
        :rtype: float
        """
        return None

    # --------------------------
    # OUT CONNECTIONS
    # --------------------------

    def outNodeAttr(self, outType="color"):
        if outType == "color" or outType == "vector":
            return self.outAttrColor()

    def outAttrColor(self):
        return ".".join([self.name(), self.outColorAttr])

    # --------------------------
    # IN CONNECTIONS
    # --------------------------

    def inNodeAttr(self, inType=DIFFUSE):
        """

        :param inType: The generic inType for the attribute name
        :type inType: str
        :return: Returns the node and attribute name for in and out connections "node.attrname"
        :rtype: str
        """
        if inType == DIFFUSEWEIGHT:
            return self.inAttrDiffuseWeight()
        elif inType == DIFFUSE or inType == "vector" or inType == "color":
            return self.inAttrDiffuseColor()
        elif inType == DIFFUSEROUGHNESS:
            return self.inAttrDiffuseRoughness()
        elif inType == METALNESS:
            return self.inAttrMetalness()
        elif inType == SPECWEIGHT:
            return self.inAttrSpecularWeight()
        elif inType == SPECCOLOR:
            return self.inAttrSpecularColor()
        elif inType == SPECROUGHNESS:
            return self.inAttrSpecularRoughness()
        elif inType == SPECIOR:
            return self.inAttrSpecularIorAttr()
        elif inType == EMISSIONWEIGHT:
            return self.inAttrEmissionWeight()
        elif inType == EMISSION:
            return self.inAttrEmission()
        elif inType == "normal":
            return self.inAttrNormal()
        elif inType == "bump":
            return self.inAttrBump()

    def inAttrDiffuseWeight(self):
        return ".".join([self.name(), self.diffuseWeightAttr])

    def inAttrDiffuseColor(self):
        return ".".join([self.name(), self.diffuseColorAttr])

    def inAttrDiffuseRoughness(self):
        return ".".join([self.name(), self.diffuseRoughnessAttr])

    def inAttrMetalness(self):
        return ".".join([self.name(), self.metalnessAttr])

    def inAttrSpecularWeight(self):
        return ".".join([self.name(), self.specularWeightAttr])

    def inAttrSpecularColor(self):
        return ".".join([self.name(), self.specularColorAttr])

    def inAttrSpecularRoughness(self):
        return ".".join([self.name(), self.specularRoughnessAttr])

    def inAttrSpecularIorAttr(self):
        return ".".join([self.name(), self.specularIorAttr])

    def inAttrCoatWeight(self):
        return ".".join([self.name(), self.coatWeightAttr])

    def inAttrCoatcolor(self):
        return ".".join([self.name(), self.coatcolorAttr])

    def inAttrCoatRoughness(self):
        return ".".join([self.name(), self.coatRoughnessAttr])

    def inAttrCoatIor(self):
        return ".".join([self.name(), self.coatIorAttr])

    def inAttrEmission(self):
        return ".".join([self.name(), self.emissionAttr])

    def inAttrEmissionWeight(self):
        return ".".join([self.name(), self.emissionWeightAttr])

    def inAttrNormal(self):
        return ".".join([self.name(), self.normalAttr])

    def inAttrBump(self):
        return ".".join([self.name(), self.bumpAttr])

    # --------------------------
    # TEXTURES
    # --------------------------

    def connectedAttrs(self):
        """Checks if any of the supported attributes have connections, if so returns:

        connectionDict: generic attributes as the keys and "node.attr" as connection values.

        :return connectionDict: Dictionary with generic attributes as the keys and "node.attr" as connection values
        :rtype connectionDict: dict(str)
        """
        connectionDict = dict()
        genAttrsTextured = list()
        attrsTextured = list()
        shaderName = self.shaderName()
        if not shaderName:
            return None

        for key in self.attrDict:
            attr = self.attrDict[key]
            if not attr:
                continue
            if cmds.listConnections(".".join([shaderName, attr]), destination=False, source=True):
                connectionDict[key] = cmds.listConnections(".".join([shaderName, attr]), plugs=True)[0]

        return connectionDict

    def connectedAttrList(self):
        """Returns a list of connected attribute names.

        Should be overridden.

        :return: A list of connected attribute names
        :rtype: list(str)
        """
        pass

    def connectAttrs(self, connectionDict, message=False):
        """Connects generic attributes to node.attribute values given in a connectionDict:

        connectionDict: generic attributes as the keys and "node.attr" as connection values

        :param connectionDict: Dictionary with generic attributes as the keys and "node.attr" as connection values
        :type connectionDict: dict(str)
        :param message: Report the connections back to the user?
        :type message: bool
        """
        shaderName = self.shaderName()
        genConnectAttrs = connectionDict.keys()
        disabledAttrs = self.unsupportedAttributes()
        # TODO Skip bump and normal attrs when they are supported

        # Connect legitimate attributes --------------------------
        for genAttr in genConnectAttrs:
            if genAttr in disabledAttrs:  # Skip as not a legitimate attribute on this shader (depends on shader type)
                continue
            destinationNodeAttr = ".".join([shaderName, self.attrDict[genAttr]])
            sourceConnections = cmds.listConnections(destinationNodeAttr, destination=False, source=True, plugs=True)
            if sourceConnections:
                connections.breakAttr(destinationNodeAttr)
                if message:
                    output.displayInfo("Disconnected `{}` > `{}`".format(connectionDict[genAttr], destinationNodeAttr))
            cmds.connectAttr(connectionDict[genAttr], destinationNodeAttr)
            if message:
                output.displayInfo("Connected `{}` > `{}`".format(connectionDict[genAttr], destinationNodeAttr))

    # --------------------------
    # TEXTURES - COLOR CREATION
    # --------------------------

    def _colorTexture(self, path, attr, suffix="", colorSpace="sRGB"):
        """Creates a texture for a color (three values) input.

        :param path: Full path to the texture to assign
        :type path: str
        :param attr: The attribute to connect the texture to on the shader
        :type attr: str
        :param suffix: A suffix will be added on the nodes if one exists. diffuse would make shader01_diffuse
        :type suffix: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        shaderName = self.shaderName()
        name = "_".join([shaderName, suffix])
        fileNode, Place2d = textures.createFileTexture(imagePath=path,
                                                       colorSpace=colorSpace,
                                                       name=name)
        cmds.connectAttr("{}.outColor".format(fileNode), ".".join([shaderName, attr]))
        cmds.setAttr("{}.ignoreColorSpaceFileRules".format(fileNode), True)
        return fileNode, Place2d

    def setDiffuseTexture(self, path, colorSpace="sRGB"):
        """Creates/sets the texture nodes path for diffuse.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._colorTexture(path, self.diffuseColorAttr, suffix="diffuse", colorSpace=colorSpace)

    def setSpecColorTexture(self, path, colorSpace="sRGB"):
        """Creates/sets the texture nodes path for specular color.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._colorTexture(path, self.specularColorAttr, suffix="specColor", colorSpace=colorSpace)

    def setCoatColorTexture(self, path, colorSpace="sRGB"):
        """Creates/sets the texture nodes path for clear coat color.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._colorTexture(path, self.coatcolorAttr, suffix="coatColor", colorSpace=colorSpace)

    def setEmissionColorTexture(self, path, colorSpace="sRGB"):
        """Creates/sets the texture nodes path for emission color.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._colorTexture(path, self.emissionAttr, suffix="emission", colorSpace=colorSpace)

    # --------------------------
    # TEXTURES - SCALAR CREATION
    # --------------------------

    def _scalarTexture(self, path, attr, suffix="", colorSpace="Raw"):
        """Creates a texture for a scalar (single value bw) value.

        :param path: Full path to the texture to assign
        :type path: str
        :param attr: The attribute to connect the texture to on the shader
        :type attr: str
        :param suffix: A suffix will be added on the nodes if one exists. diffuse would make shader01_diffuse
        :type suffix: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        shaderName = self.shaderName()
        name = "_".join([shaderName, suffix])
        fileNode, place2d = textures.createFileTexture(imagePath=path,
                                                       colorSpace=colorSpace,
                                                       name=name)
        cmds.setAttr("{}.alphaIsLuminance".format(fileNode), True)
        cmds.setAttr("{}.ignoreColorSpaceFileRules".format(fileNode), True)
        cmds.connectAttr("{}.outAlpha".format(fileNode), ".".join([shaderName, attr]))
        return fileNode, place2d

    def setDiffuseWeightTexture(self, path, colorSpace="Raw"):
        """Creates/sets the texture nodes path for diffuse weight.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._scalarTexture(path, self.diffuseWeightAttr, suffix="difWeight", colorSpace=colorSpace)

    def setDiffuseRoughnessTexture(self, path, colorSpace="Raw"):
        """Creates/sets the texture nodes path for diffuse roughness.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._scalarTexture(path, self.diffuseRoughnessAttr, suffix="difRough", colorSpace=colorSpace)

    def setMetalnessTexture(self, path, colorSpace="Raw"):
        """Creates/sets the texture nodes path for metalness.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._scalarTexture(path, self.metalnessAttr, suffix="metalness", colorSpace=colorSpace)

    def setSpecWeightTexture(self, path, colorSpace="Raw"):
        """Creates/sets the texture nodes path for specular weight.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._scalarTexture(path, self.specularWeightAttr, suffix="specWeight", colorSpace=colorSpace)

    def setSpecRoughnessTexture(self, path, colorSpace="Raw"):
        """Creates/sets the texture nodes path for specular roughness.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._scalarTexture(path, self.specularRoughnessAttr, suffix="specRough", colorSpace=colorSpace)

    def setSpecIORTexture(self, path, colorSpace="Raw"):
        """Creates/sets the texture nodes path for specular IOR.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._scalarTexture(path, self.specularIorAttr, suffix="specIOR", colorSpace=colorSpace)

    def setCoatWeightTexture(self, path, colorSpace="Raw"):
        """Creates/sets the texture nodes path for clear coat weight.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._scalarTexture(path, self.coatWeightAttr, suffix="coatWeight", colorSpace=colorSpace)

    def setCoatRoughTexture(self, path, colorSpace="Raw"):
        """Creates/sets the texture nodes path for clear coat roughness.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._scalarTexture(path, self.coatRoughnessAttr, suffix="coatRough", colorSpace=colorSpace)

    def setCoatIORTexture(self, path, colorSpace="Raw"):
        """Creates/sets the texture nodes path for clear coat IOR.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._scalarTexture(path, self.coatIorAttr, suffix="coatIOR", colorSpace=colorSpace)

    def setEmissionWeightTexture(self, path, colorSpace="Raw"):
        """Creates/sets the texture nodes path for emission weight.

        :param path: Full path to the texture to assign
        :type path: str
        :param colorSpace: What color space should the texture be created in "sRGB" "Raw" "ACEScg" etc
        :type colorSpace: str

        :return: The maya file node and the place2d node that was created.
        :rtype: tuple(str, str)
        """
        return self._scalarTexture(path, self.emissionWeightAttr, suffix="emissWeight", colorSpace=colorSpace)
