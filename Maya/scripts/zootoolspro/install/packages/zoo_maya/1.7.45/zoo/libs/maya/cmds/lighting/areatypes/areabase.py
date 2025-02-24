"""This module is the base class for area lights

This class needs to be extended/overridden by each renderer type.  Provides base functionality.

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


Example use (Note: base class will not build lights, must use a subclass renderer):

.. code-block:: python

    from zoo.libs.maya.cmds.lighting.areatypes import areabase
    areaInst = areabase.AreaBase("areaLightName", create=True)  # creates a new Area light

    areaInst.setName("myAreaLight")  # sets name of the light
    areaInst.setIntensity(1.5)
    areaInst.setVisibility(False)  # sets the background to be invisible in renders
    areaInst.setRotate([0.0, 95.3, 0.0])  # rotates the Area light 90 degrees

    areaInst = areabase.AreaBase(name="existingAreaLight", create=False, ingest=True)  # ingest existing light


Default Area dictionary example from zoo.libs.maya.cmds.lighting.lightconstants:

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
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.lighting import lightingutils, lightsbase
from zoo.libs.maya.cmds.lighting.lightconstants import AREA_NAME, AREA_INTENSITY, AREA_EXPOSURE, AREA_LIGHTVISIBILITY, \
    AREA_ROTATE, AREA_TRANSLATE, AREA_SCALE, AREA_NORMALIZE, AREA_TEMPERATURE, AREA_TEMPONOFF, AREA_LIGHTCOLOR, \
    AREA_SHAPE, AREA_DEFAULT_VALUES

# Attribute And Type Specific Information ---------------
NODE_TYPE = ""
LIGHT_SUFFIX = ""
INTENSITY_ATTR = ""
EXPOSURE_ATTR = ""
ROTATE_ATTR = "rotate"
TRANSLATE_ATTR = "translate"
SCALE_ATTR = "scale"
VIS_ATTR = ""
COLOR_ATTR = ""
TYPE_ATTR = ""
NORMALIZE_ATTR = ""
TEMPBOOL_ATTR = ""
TEMPERATURE_ATTR = ""
SHAPE_ATTR = ""


def nearlyEqual(a, b, percentDifferent=0.001):
    """Checks if two float are nearly equal

    :param a: Float value a
    :type a: float
    :param b: Float Value b
    :type b: float
    :param differenceRange: Difference in values in order to be True
    :type differenceRange:

    :return: Values are nearly equal
    :rtype: bool
    """
    if a == b:
        return True
    if a == 0.0 or b == 0.0:  # Account for division error
        a += 1
        b += 1
    percentD = abs((a / b) - 1.0)
    if percentD < percentDifferent:
        return True
    return False


class AreaBase(lightsbase.LightsBase):
    """Main class that manages an Area Light
    """
    nodetype = NODE_TYPE
    lightSuffix = LIGHT_SUFFIX
    intensityAttr = INTENSITY_ATTR
    exposureAttr = EXPOSURE_ATTR
    rotateAttr = ROTATE_ATTR
    translateAttr = TRANSLATE_ATTR
    scaleAttr = SCALE_ATTR
    visAttr = VIS_ATTR
    colorAttr = COLOR_ATTR
    normalizeAttr = NORMALIZE_ATTR
    tempBoolAttr = TEMPBOOL_ATTR
    temperatureAttr = TEMPERATURE_ATTR
    shapeAttr = SHAPE_ATTR
    zooExposureAttr = "zoo_exposer_tracker"
    zooIntensityAttr = "zoo_intensity_tracker"

    intensityMultiply = 1.0
    scaleMultiply = 1.0

    def __init__(self, name="", genAttrDict=None, node=None, create=False, ingest=False, suffixName=False,
                 message=True):
        """Either loads an area light or creates it.

        To create a new area light:
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
        super(AreaBase, self).__init__()

        if name:
            self.nameStr = name
        else:
            self.nameStr = AREA_DEFAULT_VALUES[AREA_NAME]

        if suffixName and self.lightSuffix:
            self.nameStr = "_".join([self.nameStr, self.lightSuffix])
            self.nameStr = self._renameUniqueSuffixName(self.nameStr)  # handles unique names light_01_ARN

        self.setDefaults(apply=False, setName=False)  # sets self.xxxVal values, can be changed later in __init___

        if not genAttrDict:  # no dictionary given so setup a network with default values
            genAttrDict = dict(AREA_DEFAULT_VALUES)
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

    def createAreaLight(self):
        """Creates the Area light with no settings. Designed to be changed after creation.

        :return lightTransformName: The light's transform name
        :rtype lightTransformName: str
        :return shapeNodeName:  The light's shape node name
        :rtype shapeNodeName: str
        """
        lightTransformName, shapeNodeName = lightingutils.createLight("areaTempNameXX", self.nodetype)
        # must connect to default light set
        cmds.connectAttr("{}.instObjGroups".format(lightTransformName),
                         "defaultLightSet.dagSetMembers",
                         nextAvailable=True)
        return lightTransformName, shapeNodeName

    def create(self, message=True):
        """Creates the Area light

        :param message: Report a message to the user?
        :type message: bool
        """
        lightTransformName, shapeNodeName = self.createAreaLight()
        self.node = zapi.nodeByName(lightTransformName)
        self.shapeNode = zapi.nodeByName(shapeNodeName)
        self.rename(self.nameStr)  # Rename from a temp name to handle name complexity
        if message:
            output.displayInfo("{} Area created: {} ".format(self.renderer(), lightTransformName))

    # -------------------
    # Dictionary Setters and Getters
    # -------------------

    def shapeAttributeNames(self):
        """Generic attributes are the keys and the shader's attributes are the values.

        :return: A dictionary with strings as keys and attribute string names as values.
        :rtype: dict
        """
        return {AREA_INTENSITY: self.intensityAttr,
                AREA_EXPOSURE: self.exposureAttr,
                AREA_NORMALIZE: self.normalizeAttr,
                AREA_TEMPERATURE: self.temperatureAttr,
                AREA_TEMPONOFF: self.tempBoolAttr,
                AREA_SHAPE: self.shapeAttr,
                AREA_LIGHTVISIBILITY: self.visAttr,
                AREA_LIGHTCOLOR: self.colorAttr
                }

    def transformAttributeNames(self):
        """Generic attributes are the keys and the area light attributes are the values.

        :return: A dictionary with strings as keys and attribute string names as values.
        :rtype: dict
        """
        return {AREA_TRANSLATE: self.translateAttr,
                AREA_ROTATE: self.rotateAttr,
                AREA_SCALE: self.scaleAttr}

    def setDefaults(self, apply=True, setName=False):
        """Sets the defaults internally, the shader does not need to be created unless apply=True

        :param apply: If True then apply the settings to the shader, otherwise is just changed in the class instance.
        :type apply: bool
        """
        if setName:
            self.nameVal = AREA_DEFAULT_VALUES[AREA_NAME]
        self.intensityVal = AREA_DEFAULT_VALUES[AREA_INTENSITY]
        self.exposureVal = AREA_DEFAULT_VALUES[AREA_EXPOSURE]
        self.normalizeVal = AREA_DEFAULT_VALUES[AREA_NORMALIZE]
        self.colorVal = AREA_DEFAULT_VALUES[AREA_LIGHTCOLOR]
        self.tempBoolVal = AREA_DEFAULT_VALUES[AREA_TEMPONOFF]
        self.temperatureVal = AREA_DEFAULT_VALUES[AREA_TEMPERATURE]
        self.rotateVal = AREA_DEFAULT_VALUES[AREA_ROTATE]
        self.translateVal = AREA_DEFAULT_VALUES[AREA_TRANSLATE]
        self.scaleVal = AREA_DEFAULT_VALUES[AREA_SCALE]
        self.visVal = AREA_DEFAULT_VALUES[AREA_LIGHTVISIBILITY]
        self.shapeVal = AREA_DEFAULT_VALUES[AREA_SHAPE]
        if apply:
            self.applyCurrentSettings()

    def setFromDict(self, genAttrDict, setName=False, apply=True, noneIsDefault=True):
        """Sets the area light from a generic attribute dictionary. Values as attribute values.

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
                                               AREA_NAME,
                                               self.nameVal,
                                               AREA_DEFAULT_VALUES[AREA_NAME],
                                               noneIsDefault)
        self.intensityVal = self._setDictSingle(genAttrDict,
                                                AREA_INTENSITY,
                                                self.intensityVal,
                                                AREA_DEFAULT_VALUES[AREA_INTENSITY],
                                                noneIsDefault)
        self.rotateVal = self._setDictSingle(genAttrDict,
                                             AREA_ROTATE,
                                             self.rotateVal,
                                             AREA_DEFAULT_VALUES[AREA_ROTATE],
                                             noneIsDefault)
        self.translateVal = self._setDictSingle(genAttrDict,
                                                AREA_TRANSLATE,
                                                self.translateVal,
                                                AREA_DEFAULT_VALUES[AREA_TRANSLATE],
                                                noneIsDefault)
        self.scaleVal = self._setDictSingle(genAttrDict,
                                            AREA_SCALE,
                                            self.scaleVal,
                                            AREA_DEFAULT_VALUES[AREA_SCALE],
                                            noneIsDefault)
        self.normalizeVal = self._setDictSingle(genAttrDict,
                                                AREA_NORMALIZE,
                                                self.normalizeVal,
                                                AREA_DEFAULT_VALUES[AREA_NORMALIZE],
                                                noneIsDefault)
        self.tempBoolVal = self._setDictSingle(genAttrDict,
                                               AREA_TEMPONOFF,
                                               self.tempBoolVal,
                                               AREA_DEFAULT_VALUES[AREA_TEMPONOFF],
                                               noneIsDefault)
        self.temperatureVal = self._setDictSingle(genAttrDict,
                                                  AREA_TEMPERATURE,
                                                  self.temperatureVal,
                                                  AREA_DEFAULT_VALUES[AREA_TEMPERATURE],
                                                  noneIsDefault)
        self.visVal = self._setDictSingle(genAttrDict,
                                          AREA_LIGHTVISIBILITY,
                                          self.visVal,
                                          AREA_DEFAULT_VALUES[AREA_LIGHTVISIBILITY],
                                          noneIsDefault)
        self.colorVal = self._setDictSingle(genAttrDict,
                                            AREA_LIGHTCOLOR,
                                            self.colorVal,
                                            AREA_DEFAULT_VALUES[AREA_LIGHTCOLOR],
                                            noneIsDefault)
        self.shapeVal = self._setDictSingle(genAttrDict,
                                            AREA_SHAPE,
                                            self.shapeVal,
                                            AREA_DEFAULT_VALUES[AREA_SHAPE],
                                            noneIsDefault)
        if apply:
            self.applyCurrentSettings()

    def applyCurrentSettings(self, applyName=False):
        """Applies the current settings"""
        if applyName:
            self.setName(self.nameVal)
        self.setIntensity(self.intensityVal)
        self.setExposure(self.exposureVal)
        self.setRotate(self.rotateVal)
        self.setTranslate(self.translateVal)
        self.setScale(self.scaleVal)
        self.setNormalize(self.normalizeVal)
        self.setTempOnOff(self.tempBoolVal)
        self.setTemperature(self.temperatureVal)
        self.setShape(self.shapeVal)
        self.setVisibility(self.visVal)
        self.setColor(self.colorVal)

    def pullSettings(self, includeName=False):
        """Pulls the current attributes from the current shader, shader must exist"""
        if includeName:
            self.nameVal = self.name()
        self.intensityVal = self.intensity()
        self.exposureVal = self.exposure()
        self.rotateVal = self.rotate()
        self.translateVal = self.translate()
        self.scaleVal = self.scale()
        self.temperatureVal = self.temperature()
        self.tempBoolVal = self.tempOnOff()
        self.normalizeVal = self.normalize()
        self.shapeVal = self.shape()
        self.visVal = self.visibility()
        self.colorVal = self.color()

    # -------------------
    # Setters and Getters
    # -------------------

    def setIntensity(self, intensity):
        self._setAttrScalar(self.intensityAttr, intensity * self.intensityMultiply, node=self.shapeName())

    def intensity(self):
        intensity = self._getAttrScalar(self.intensityAttr, node=self.shapeName())
        if intensity:
            intensity /= self.intensityMultiply
        return intensity

    def setExposure(self, exposure):
        self._setAttrScalar(self.exposureAttr, exposure, node=self.shapeName())

    def exposure(self):
        return self._getAttrScalar(self.exposureAttr, node=self.shapeName())

    def setNormalize(self, normalize):
        self._setAttrScalar(self.normalizeAttr, normalize, node=self.shapeName())

    def normalize(self):
        return self._getAttrScalar(self.normalizeAttr, node=self.shapeName())

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

    def setShape(self, shape):
        self._setAttrScalar(self.shapeAttr, shape, node=self.shapeName())

    def shape(self):
        return self._getAttrScalar(self.shapeAttr, node=self.shapeName())

    def setVisibility(self, visibility):
        self._setAttrScalar(self.visAttr, visibility, node=self.shapeName())

    def visibility(self):
        return self._getAttrScalar(self.visAttr, node=self.shapeName())

    # --------------------------
    # MISSING INTENSITY/EXPOSURE
    # --------------------------

    def setIntensityPure(self, intensity):
        self._setAttrScalar(self.intensityAttr, intensity, node=self.shapeName())  # Sets directly to Maya

    def intensityPure(self):
        return self._getAttrScalar(self.intensityAttr, node=self.shapeName())  # Gets exactly from Maya

    def _createZooIntExpAttr(self):
        if not cmds.attributeQuery(self.zooExposureAttr, node=self.shapeName(), exists=True):
            cmds.addAttr(self.shapeName(), longName=self.zooIntensityAttr, attributeType='float')
            cmds.addAttr(self.shapeName(), longName=self.zooExposureAttr, attributeType='float')

    def pureIntensityToGeneric(self):
        """Takes the literal value of maya's intensity and converts it to the generic intensity.

        Designed to be overridden by the renderer if needed, eg VRay"""
        intensity = self.intensityPure()
        if not intensity:  # is 0.0
            return intensity
        return intensity / self.intensityMultiply

    def _intensityFromZooAttrs(self):
        """Gets the intensity in generic (UI) values and the zoo attr values.
        Compares if the zoo values match the user/Maya native values.

        :return: genericIntensity, intensity, exposure, zooAttrsMatch
        :rtype: tuple(float, float, float, bool)
        """
        self._createZooIntExpAttr()
        genericIntensity = self.pureIntensityToGeneric()
        exposure = cmds.getAttr(".".join([self.shapeName(), self.zooExposureAttr]))  # UI/TrackerValue
        intensity = cmds.getAttr(".".join([self.shapeName(), self.zooIntensityAttr]))  # UI/TrackerValue
        combinedZooAttrValue = lightingutils.convertExpAndIntToIntensity(intensity,
                                                                         exposure)[0]

        if nearlyEqual(genericIntensity, combinedZooAttrValue, percentDifferent=0.001):  # rounding issues
            return genericIntensity, intensity, exposure, True
        return genericIntensity, intensity, exposure, False

    def setExposureMissing(self, exposure):
        """Given exposure value, returns the intensity value in generic values after combining with intensity.
        Also sets tracker att.

        Used when the exposure attribute is missing on the area light type, eg. VRay and Maya.

        :param exposure: The exposure value to set
        :type exposure: float

        :return intensity: The intensity value in generic units now combine with exposure and intensity values.
        :rtype intensity: float
        """
        self._createZooIntExpAttr()
        cmds.setAttr(".".join([self.shapeName(), self.zooExposureAttr]), exposure)
        intensity = cmds.getAttr(".".join([self.shapeName(), self.zooIntensityAttr]))  # UI Tracker Intensity
        intensity, exposure = lightingutils.convertExpAndIntToIntensity(intensity, exposure)
        return intensity  # generic units

    def exposureMissing(self):
        """Returns the exposure value in cases where there is no exposure attribute VRay and Maya.

        Note: If VRay the value is in Lumen Units and is normalized

        This method is not perfect and can have troubles when the user updates via Maya's channel box or Attr Editor.

        If the zoo exposure values do not match the actual light's real intensity, the exposure is returned as zero.

        :return intensity: The intensity value of the light
        :rtype intensity: float
        """
        genericIntensity, intensity, exposure, matchBool = self._intensityFromZooAttrs()
        if matchBool:
            return exposure  # as per UI value
        else:
            shapeName = self.shapeName()
            cmds.setAttr(".".join([shapeName, self.zooIntensityAttr]), genericIntensity)
            cmds.setAttr(".".join([shapeName, self.zooExposureAttr]), 0.0)
            output.displayWarning("Exposure: Actual and UI values do not match")
            return 0.0  # doesn't match so return no exposure

    def setIntensityMissing(self, intensity):
        """Given intensity in generic (UI) units, returns the generic intensity value after combining with exposure.
        Also sets tracker att.

        Used when the exposure attribute is missing on the area light type, eg. VRay and Maya.

        :param intensity: The generic UI value of the intensity to set
        :type intensity: float

        :return intensity: The generic UI value of the intensity now combined with exposure
        :rtype intensity: float
        """
        self._createZooIntExpAttr()
        cmds.setAttr(".".join([self.shapeName(), self.zooIntensityAttr]), intensity)
        exposure = cmds.getAttr(".".join([self.shapeName(), self.zooExposureAttr]))  # UI Tracker Intensity
        intensity, exposure = lightingutils.convertExpAndIntToIntensity(intensity, exposure)
        return intensity  # generic units

    def intensityMissing(self):
        """Returns the intensity value in cases where there is no exposure attribute VRay and Maya.

        This method is not perfect and can have troubles when the user updates via Maya's channel box or Attr Editor.

        If the zoo exposure values do not match the actual light's real intensity, the pure intensity is returned.

        :return intensity: The generic intensity value of the light
        :rtype intensity: float
        """
        genericIntensity, intensity, exposure, matchBool = self._intensityFromZooAttrs()
        if matchBool:
            return intensity
        else:
            shapeName = self.shapeName()
            cmds.setAttr(".".join([shapeName, self.zooIntensityAttr]), genericIntensity)
            cmds.setAttr(".".join([shapeName, self.zooExposureAttr]), 0.0)
            output.displayWarning("Intensity: Actual and UI values do not match")
            return genericIntensity

    # --------------------------
    # INTENSITY/EXPOSURE & NORMALIZE CONVERSIONS
    # --------------------------

    def convertExpAndIntToExposure(self, setValues=True):
        """Converts light settings to mixing feature exposure and intensity of 1.0

        :param intensity: The intensity attr value
        :type intensity: float
        :param exposure: The exposure attribute value
        :type exposure: float

        :return values: the new intensity and exposure values after conversion
        :rtype values: tuple(floot)
        """
        newIntensity, newExposure = lightingutils.convertExpAndIntToExposure(self.intensity(), self.exposure())
        if setValues:
            self.setIntensity(newIntensity)
            self.setExposure(newIntensity)
        return newIntensity, newExposure

    def convertExpAndIntToIntensity(self, setValues=True):
        """Converts light settings to mixing feature exposure of 0.0 and and intensity with a new value

        :param intensity: The intensity attr value
        :type intensity: float
        :param exposure: The exposure attribute value
        :type exposure: float

        :return values: the new intensity and exposure values after conversion
        :rtype values: tuple(floot)
        """
        newIntensity, newExposure = lightingutils.convertExpAndIntToIntensity(self.intensity(), self.exposure())
        if setValues:
            self.setIntensity(newIntensity)
            self.setExposure(newIntensity)
        return newIntensity, newExposure

    def convertToNonNormalized(self, setValues=True):
        """Convert to non-normalized light usually from normalized, returned values are exposure dominant.

        :param setValues: Set the values on the light or just return?
        :type setValues: bool

        :return values: the new intensity and exposure values after conversion
        :rtype values: tuple(floot)
        """
        normalized = self.normalize()
        intensity = self.intensity()
        exposure = self.exposure()

        if not normalized:
            return intensity, exposure

        # Do the conversion ---------------
        shape = self.shape()  # returns int
        scale = self.scale()

        newIntensity, newExposure = lightingutils.convertToNormalizedExposure(intensity, exposure,
                                                                              scale[0], scale[1], scale[2],
                                                                              lightingutils.SHAPE_ATTR_ENUM_LIST_NICE[
                                                                                  shape])
        if setValues:
            self.setIntensity(newIntensity)
            self.setExposure(newIntensity)

        return newIntensity, newExposure

    def convertToNormalized(self, setValues=True):
        """Convert to non-normalized light usually from normalized, returned values are exposure dominant.

        :param setValues: Set the values on the light or just return?
        :type setValues: bool

        :return values: the new intensity and exposure values after conversion
        :rtype values: tuple(floot)
        """
        normalized = self.normalize()
        intensity = self.intensity()
        exposure = self.exposure()

        if not normalized:
            return intensity, exposure

        # Do the conversion ---------------
        shape = self.shape()  # returns int
        scale = self.scale()

        newIntensity, \
        newExposure = lightingutils.convertToNonNormalizedExposure(intensity, exposure,
                                                                   scale[0], scale[1], scale[2],
                                                                   lightingutils.SHAPE_ATTR_ENUM_LIST_NICE[shape])
        if setValues:
            self.setIntensity(newIntensity)
            self.setExposure(newIntensity)

        return newIntensity, newExposure
