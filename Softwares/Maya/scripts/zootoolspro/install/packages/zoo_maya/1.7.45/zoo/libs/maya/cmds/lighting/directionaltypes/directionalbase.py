"""This module is the base class for directional lights

This class is intended to be extended/overridden by each renderer type.  Provides base functionality.

A Directional Light has these properties:

    - name: The name of the light (str)
    - shapeName: The name of the light (str)
    - nodetype: The node type of the Directional Light (str)
    - lightSuffix: The optional suffix of the light
    - intensity: The intensity of the light
    - rotate: The rotation values in 3d space
    - translate: The translation values in 3d space
    - scale: The scale values in 3d space
    - color: The color of the Directional Light
    - tempBool: Is the temperature mode on or off?
    - temperature: The temperature of the directional Light
    - softAngle: The soft angle (shadow blur) of the directional Light


Example use (Note: base class will not build lights, must use a subclass renderer):

.. code-block:: python

    from zoo.libs.maya.cmds.lighting.directionaltypes import directionalbase
    directionalInst = directionalbase.DirectionalBase("directionalLightName", create=True)  # creates a new Directional light

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

from zoo.libs.utils import output
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.lighting import lightingutils, lightsbase
from zoo.libs.maya.cmds.lighting.lightconstants import DIR_NAME, DIR_INTENSITY, DIR_ROTATE, DIR_TRANSLATE, DIR_SCALE, \
    DIR_ANGLE_SOFT, DIR_TEMPERATURE, DIR_TEMPONOFF, DIR_LIGHTCOLOR, DIR_SHAPE, DIR_DEFAULT_VALUES


NODE_TYPE = ""


class DirectionalBase(lightsbase.LightsBase):
    """Main class that manages a Directional Light
    """
    nodetype = NODE_TYPE
    lightSuffix = ""
    intensityAttr = ""
    softAngleAttr = ""
    rotateAttr = "rotate"
    translateAttr = "translate"
    scaleAttr = "scale"
    colorAttr = ""
    tempBoolAttr = ""
    temperatureAttr = ""

    intensityMultiply = 1.0
    scaleMultiply = 1.0

    def __init__(self, name="", genAttrDict=None, node=None, create=False, ingest=False, suffixName=False,
                 message=True):
        """Either loads a Directional light or creates it.

        To create a new Directional Light:
            create=True and node=False to create a new shader

        To load a Directional Light by zapiNode name
            node="zapiNode" (should be a shader node) and ingest=True

        To load a Directional Light by string:
            shaderName="shaderName" and ingest=True

        :param name: The string name of the Directional Light to load or create
        :type name: str
        :param node: Optional zapi node object and will ingest and not create a new Directional Light
        :type node: :class:`zapi.DGNode`
        :param genAttrDict: The generic attribute dictionary with attribute values to set only if creating
        :type genAttrDict: dict(str)
        :param create: If True then create a new Directional Light False will load the Directional Light into the instance
        :type create: bool
        :param ingest: If True then ingest the Directional Light into the instance
        :type ingest: bool
        :param message: Report a message to the user only if creating
        :type message: bool
        """
        super(DirectionalBase, self).__init__()
        if name:
            self.nameStr = name
        else:
            self.nameStr = DIR_DEFAULT_VALUES[DIR_NAME]

        if suffixName and self.lightSuffix:
            self.nameStr = "_".join([self.nameStr, self.lightSuffix])
            self.nameStr = self._renameUniqueSuffixName(self.nameStr)  # handles unique names light_01_ARN

        self.setDefaults(apply=False, setName=False)  # sets self.xxxVal values, can be changed later in __init___

        if not genAttrDict:  # no dictionary given so set up a network with default values
            genAttrDict = dict(DIR_DEFAULT_VALUES)
        self.setFromDict(genAttrDict, apply=False)

        # Ingest ----------------------------------
        if node and ingest:  # Passed in an existing zapi node
            self.node = node
            self._setShapeNode()  # sets self.shapeNode (zapi object) from self.node
            self.name = node.fullPathName()
            self.pullSettings()
            return
        elif name and ingest:  # Use the shader name to ingest into the instance
            self.nameVal = name
            self.node = zapi.nodeByName(name)
            self._setShapeNode()  # sets self.shapeNode (zapi object) from self.node
            self.pullSettings()
            return
        # Create -----------------
        if create:
            self.create(message=message)
            self.applyCurrentSettings()

    # -------------------
    # Create
    # -------------------

    def createDirectionalLight(self):
        """Creates the Directional light with no settings. Designed to be changed after creation.

        :return lightTransformName: The light's transform name
        :rtype lightTransformName: str
        :return shapeNodeName:  The light's shape node name
        :rtype shapeNodeName: str
        """
        lightTransformName, shapeNodeName = lightingutils.createLight("directionalTempNameXX", self.nodetype)
        # must connect to default light set
        cmds.connectAttr("{}.instObjGroups".format(lightTransformName),
                         "defaultLightSet.dagSetMembers",
                         nextAvailable=True)
        return lightTransformName, shapeNodeName

    def create(self, message=True):
        """Creates the Directional light

        :param message: Report a message to the user?
        :type message: bool
        """
        lightTransformName, shapeNodeName = self.createDirectionalLight()
        self.node = zapi.nodeByName(lightTransformName)
        self.shapeNode = zapi.nodeByName(shapeNodeName)
        self.rename(self.nameStr)  # Rename from a temp name to handle name complexity
        if message:
            output.displayInfo("{} Directional created: {} ".format(self.renderer(), lightTransformName))

    # -------------------
    # Dictionary Setters and Getters
    # -------------------

    def shapeAttributeNames(self):
        """Generic attributes are the keys and the shader's attributes are the values.

        :return: A dictionary with strings as keys and attribute string names as values.
        :rtype: dict
        """
        return {DIR_INTENSITY: self.intensityAttr,
                DIR_ANGLE_SOFT: self.softAngleAttr,
                DIR_TEMPERATURE: self.temperatureAttr,
                DIR_TEMPONOFF: self.tempBoolAttr,
                DIR_LIGHTCOLOR: self.colorAttr
                }

    def transformAttributeNames(self):
        """Generic attributes are the keys and the directional light attributes are the values.

        :return: A dictionary with strings as keys and attribute string names as values.
        :rtype: dict
        """
        return {DIR_TRANSLATE: self.translateAttr,
                DIR_ROTATE: self.rotateAttr,
                DIR_SCALE: self.scaleAttr}

    def setDefaults(self, apply=True, setName=False):
        """Sets the defaults internally, the shader does not need to be created unless apply=True

        :param apply: If True then apply the settings to the shader, otherwise is just changed in the class instance.
        :type apply: bool
        """
        if setName:
            self.nameVal = DIR_DEFAULT_VALUES[DIR_NAME]
        self.intensityVal = DIR_DEFAULT_VALUES[DIR_INTENSITY]
        self.softAngleVal = DIR_DEFAULT_VALUES[DIR_ANGLE_SOFT]
        self.colorVal = DIR_DEFAULT_VALUES[DIR_LIGHTCOLOR]
        self.tempBoolVal = DIR_DEFAULT_VALUES[DIR_TEMPONOFF]
        self.temperatureVal = DIR_DEFAULT_VALUES[DIR_TEMPERATURE]
        self.rotateVal = DIR_DEFAULT_VALUES[DIR_ROTATE]
        self.translateVal = DIR_DEFAULT_VALUES[DIR_TRANSLATE]
        self.scaleVal = DIR_DEFAULT_VALUES[DIR_SCALE]
        if apply:
            self.applyCurrentSettings()

    def setFromDict(self, genAttrDict, setName=False, apply=True, noneIsDefault=True):
        """Sets the directional light from a generic attribute dictionary. Values as attribute values.

        Handles None-values in the dictionary and also missing keys.

        None-values and missing keys can either pass or be replaced with default values.

        :param genAttrDict: The generic attribute dictionary with values as attribute values
        :type genAttrDict: dict(str)
        :param apply: Will apply the dict to the current shader, must exist
        :type apply: bool
        :param noneIsDefault: Will apply defaults if the value of the key is None
        :type noneIsDefault: bool
        """
        if setName:
            self.nameVal = self._setDictSingle(genAttrDict,
                                               DIR_NAME,
                                               self.nameVal,
                                               DIR_DEFAULT_VALUES[DIR_NAME],
                                               noneIsDefault)
        self.intensityVal = self._setDictSingle(genAttrDict,
                                                DIR_INTENSITY,
                                                self.intensityVal,
                                                DIR_DEFAULT_VALUES[DIR_INTENSITY],
                                                noneIsDefault)
        self.rotateVal = self._setDictSingle(genAttrDict,
                                             DIR_ROTATE,
                                             self.rotateVal,
                                             DIR_DEFAULT_VALUES[DIR_ROTATE],
                                             noneIsDefault)
        self.translateVal = self._setDictSingle(genAttrDict,
                                                DIR_TRANSLATE,
                                                self.translateVal,
                                                DIR_DEFAULT_VALUES[DIR_TRANSLATE],
                                                noneIsDefault)
        self.scaleVal = self._setDictSingle(genAttrDict,
                                            DIR_SCALE,
                                            self.scaleVal,
                                            DIR_DEFAULT_VALUES[DIR_SCALE],
                                            noneIsDefault)
        self.softAngleVal = self._setDictSingle(genAttrDict,
                                                DIR_ANGLE_SOFT,
                                                self.softAngleVal,
                                                DIR_DEFAULT_VALUES[DIR_ANGLE_SOFT],
                                                noneIsDefault)
        self.tempBoolVal = self._setDictSingle(genAttrDict,
                                               DIR_TEMPONOFF,
                                               self.tempBoolVal,
                                               DIR_DEFAULT_VALUES[DIR_TEMPONOFF],
                                               noneIsDefault)
        self.temperatureVal = self._setDictSingle(genAttrDict,
                                                  DIR_TEMPERATURE,
                                                  self.temperatureVal,
                                                  DIR_DEFAULT_VALUES[DIR_TEMPERATURE],
                                                  noneIsDefault)
        self.colorVal = self._setDictSingle(genAttrDict,
                                            DIR_LIGHTCOLOR,
                                            self.colorVal,
                                            DIR_DEFAULT_VALUES[DIR_LIGHTCOLOR],
                                            noneIsDefault)
        if apply:
            self.applyCurrentSettings()

    def applyCurrentSettings(self, applyName=False):
        """Applies the current settings"""
        if applyName:
            self.setName(self.nameVal)
        self.setIntensity(self.intensityVal)
        self.setRotate(self.rotateVal)
        self.setTranslate(self.translateVal)
        self.setScale(self.scaleVal)
        self.setTempOnOff(self.tempBoolVal)
        self.setTemperature(self.temperatureVal)
        self.setSoftAngle(self.softAngleVal)
        self.setColor(self.colorVal)

    def pullSettings(self, includeName=False):
        """Pulls the current attributes from the current shader, shader must exist"""
        if includeName:
            self.nameVal = self.name()
        self.intensityVal = self.intensity()
        self.rotateVal = self.rotate()
        self.translateVal = self.translate()
        self.scaleVal = self.scale()
        self.temperatureVal = self.temperature()
        self.tempBoolVal = self.tempOnOff()
        self.softAngleVal = self.softAngle()
        self.colorVal = self.color()

    # -------------------
    # Setters and Getters
    # -------------------

    def setIntensity(self, intensity):
        self._setAttrScalar(self.intensityAttr, self.intensityMultiply*intensity, node=self.shapeName())

    def intensity(self):
        intensity = self._getAttrScalar(self.intensityAttr, node=self.shapeName())
        if intensity:
            intensity = intensity / self.intensityMultiply
        return intensity

    def setTempOnOff(self, tempOnOff):
        self._setAttrScalar(self.tempBoolAttr, tempOnOff, node=self.shapeName())

    def tempOnOff(self):
        return self._getAttrScalar(self.tempBoolAttr, node=self.shapeName())

    def setTemperature(self, temperature):
        self._setAttrScalar(self.temperatureAttr, temperature, node=self.shapeName())

    def temperature(self):
        return self._getAttrScalar(self.temperatureAttr, node=self.shapeName())

    def setColor(self, color):
        self._setAttrVector(self.colorAttr, color, node=self.shapeName())

    def color(self):
        return self._getAttrVector(self.colorAttr, node=self.shapeName())

    def setSoftAngle(self, softAngle):
        self._setAttrScalar(self.softAngleAttr, softAngle, node=self.shapeName())

    def softAngle(self):
        return self._getAttrScalar(self.softAngleAttr, node=self.shapeName())


