"""This module is the VRay class for area lights

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

    from zoo.libs.maya.cmds.lighting.areatypes import vrayarea
    areaInst = vrayarea.VRayArea("areaLightName", create=True, suffixName=False)  # creates a new area light

    areaInst.setName("myAreaLight")  # sets name of the light
    areaInst.setIntensity(1.5)
    areaInst.setVisibility(False)  # sets the background to be invisible in renders
    areaInst.setRotate([0.0, 95.3, 0.0])  # rotates the Area light 90 degrees

    areaInst = vrayarea.VRayArea(name="existingAreaLight", create=False, ingest=True)  # ingest existing light


VRay Note: Vray has added code that changes values after the script is run.  In the case of VRay, you should only change values \
once as the code is being run.



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

from zoo.libs.maya.cmds.lighting import lightconstants, lightingutils as lu
from zoo.libs.maya.cmds.lighting.areatypes import areabase
from zoo.libs.utils import output

NODE_TYPE = "VRayLightRectShape"


class VRayArea(areabase.AreaBase):
    """Main class that manages an area light
    """
    nodetype = NODE_TYPE
    lightSuffix = "VRAY"
    intensityAttr = "intensityMult"
    exposureAttr = ""
    visAttr = "invisible"
    scaleAttr = ["uSize", "vSize"]
    colorAttr = "lightColor"
    normalizeAttr = "units"
    tempBoolAttr = "colorMode"
    temperatureAttr = "temperature"
    shapeAttr = "shapeType"

    intensityMultiply = 0.15657457415  # callibrated for lumens
    scaleMultiply = 1.0
    # VRay Unit Modes Control Both Normalize and Intensity settings. ---------
    # Modes = ["default", "Lumens", "lm/m/m/sr", "Watts", "w/m/m/s"]
    normalizeModes = [False, True, False, True, False]
    # VRay Unit calibration is light at scale of 1.0
    vrayUnitCalibrate = [1.5915493965148926, 1.0, 795.7747192382812, 0.0014641288435086608, 1.1651166677474976]

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
        super(VRayArea, self).__init__(name=name,
                                       genAttrDict=genAttrDict,
                                       node=node,
                                       create=create,
                                       ingest=ingest,
                                       suffixName=suffixName,
                                       message=message)

    def renderer(self):
        """Returns the current renderer as a string"""
        return lightconstants.VRAY

    def applyCurrentSettings(self, applyName=False):
        """Overridden and applies vray settings as VRays auto attribute changes cause havoc"""
        self._createZooIntExpAttr()  # creates the zoo tracker attrs

        if applyName:
            self.setName(self.nameVal)
        self.setRotate(self.rotateVal)
        self.setTranslate(self.translateVal)
        self.setScale(self.scaleVal)

        self.setTempOnOff(self.tempBoolVal)
        self.setTemperature(self.temperatureVal)
        self.setShape(self.shapeVal)
        self.setVisibility(self.visVal)
        self.setColor(self.colorVal)
        # Handle changing normalization ------------------------
        normalizeOld = self.normalize()
        if normalizeOld != self.normalizeVal:  # loads of trouble cause of vray fixing itself after the script is run.
            typeIndex = cmds.getAttr("{}.units".format(self.shapeName()))  # vray intensity type, used later
            self.setNormalize(self.normalizeVal)
            self.setExposure(self.exposureVal)
            # Set as default units, VRay converts to lumen units after the script has run :/
            self._setIntensityVrayType(self.intensityVal,
                                       self.exposureVal,
                                       typeIndex,
                                       normalize=not self.normalize(),
                                       unnormalize=self.normalize(),
                                       setZooAttrs=True)
        else:
            self.setExposure(self.exposureVal)
            self.setIntensity(self.intensityVal)

    # -------------------
    # Setters and Getters
    # -------------------

    def _setIntensityVrayType(self, intensity, exposure, index, normalize=False, unnormalize=False, setZooAttrs=True):
        """Sets Vray intensity by index of the Type combo box. Does the conversions from intensity and exposure.

             0: default
             1: Lumens
             2: lm/m/m/sr
             3: Watts
             4: w/m/m/s

        Can also normalize or un-normalize the values.

        :param intensity: Intensity in the generic UI values
        :type intensity: float
        :param exposure: Exposure in the generic UI values
        :type exposure: float
        :param index: index of the VRays "Type" combo box see description
        :type index: int
        :param normalize: Normalize the light intensity, assumes intensity is not normalized.
        :type normalize: bool
        :param unnormalize: Un-normalize the light intensity, assumes intensity is normalized.
        :type unnormalize: bool
        :param setZooAttrs: Also set the internal Zoo attrs in generic units
        :type setZooAttrs: bool
        """
        if setZooAttrs:
            self._createZooIntExpAttr()
            cmds.setAttr(".".join([self.shapeName(), self.zooIntensityAttr]), intensity)
            cmds.setAttr(".".join([self.shapeName(), self.zooExposureAttr]), exposure)
        # Convert and set Vray intensity attribute --------------------
        intensityGeneric = lu.convertExpAndIntToIntensity(intensity, exposure)[0]
        intensityGeneric *= self.intensityMultiply  # To Lumens
        intensityGeneric *= self.vrayUnitCalibrate[index]  # Now matches the VRay type

        if not normalize and not unnormalize:
            return self.setIntensityPure(intensityGeneric)  # sets directly to VRay Maya

        # Normalize/ unnormalize code ---------------------
        scale = self.scale()
        physShapeIndex = self.shape()
        physShapeName = lu.SHAPE_ATTR_ENUM_LIST_NICE[physShapeIndex]
        if normalize:
            intensityGeneric = lu.convertToNormalizedIntensity(intensityGeneric,
                                                               0.0,
                                                               scale[0], scale[1], scale[2],
                                                               physShapeName)[0]
        if unnormalize:
            intensityGeneric = lu.convertToNonNormalizedIntensity(intensityGeneric,
                                                                  0.0,
                                                                  scale[0], scale[1], scale[2],
                                                                  physShapeName)[0]
        self.setIntensityPure(intensityGeneric)  # Sets directly to VRay Maya

    def pureIntensityToGeneric(self):
        """Takes the literal value of maya's intensity and converts it to the generic intensity.

        Used by base class areabase.AreaBase()

        Designed to be overridden by the renderer if needed, eg VRay"""
        intensityVal = self.intensityPure()
        if not intensityVal:  # is 0.0
            return intensityVal
        # Convert to Lumens ---------
        intensityVal /= self.intensityMultiply
        # calibrate to be in matching current unit -------
        index = cmds.getAttr("{}.units".format(self.shapeName()))
        return intensityVal / self.vrayUnitCalibrate[index]

    def vrayUnitConversion(self, intensityVal):
        """Calibrates an incoming value in generic UI values to match the vray maya intensity.
        Includes normalization too.

            default = index 0, (not normalized), intensity multiply 1.5915493965148926
            Lumens = index 1, (normalized), intensity multiply 1.0
            lm/m/m/sr = index 2, (not normalized), intensity multiply 795.7747192382812
            Watts = index 3, (normalized), intensity multiply 0.0014641288435086608
            w/m/m/s = index 4, (not normalized), intensity multiply 1.1651166677474976

        :param intensityVal: The intensity value of the light in VRay lumen units.
        :type intensityVal: float

        :return intensityVal: The value of the light now calibrated to the current VRay Units
        :rtype intensityVal: float
        """
        intensityVal *= self.intensityMultiply  # to vray lumens

        # 1. Convert into the correct current unit type.
        unitsIndex = cmds.getAttr("{}.units".format(self.shapeName()))
        intensityVal *= self.vrayUnitCalibrate[unitsIndex]  # adjust non normalized intensity
        # 2. Handle normalization
        if self.normalize():  # if Lumens or Watts the value is already correct.
            return intensityVal
        # Value needs to be normalized
        shapeIndex = self.shape()
        scale = self.scale()
        return lu.convertToNonNormalizedIntensity(intensityVal,
                                                  0.0,
                                                  scale[0], scale[1], scale[2],
                                                  lu.SHAPE_ATTR_ENUM_LIST_NICE[shapeIndex])[0]

    def setIntensityPure(self, intensity):
        try:
            self._setAttrScalar(self.intensityAttr, intensity, node=self.shapeName())  # Sets directly to VRay Maya
        except RuntimeError:  # catch, rarely happens when UI is out of sync with VRay
            output.displayWarning("Setting VRay intensity failed `.intensityMult` likely set past its maximum value")

    def intensity(self):
        return self.intensityMissing()  # intensity is in generic units

    def setIntensity(self, intensity):
        intensityVal = self.setIntensityMissing(intensity)  # arg value is in generic units (UI)
        intensityVal = self.vrayUnitConversion(intensityVal)  # vray could be any unit system so convert to match
        try:
            self.setIntensityPure(intensityVal)  # ignores the zoo intensity tracker attrs, sets maya directly
        except RuntimeError:  # catch, rarely happens when UI is out of sync with VRay
            output.displayWarning("Setting VRay intensity failed `.intensityMult` likely set past its maximum value")

    def exposure(self):
        return self.exposureMissing()

    def setExposure(self, exposure):
        intensityVal = self.setExposureMissing(exposure)  # value is in generic units (intensity only)
        intensityVal = self.vrayUnitConversion(intensityVal)  # vray could be any unit system so convert to match
        try:
            self.setIntensityPure(intensityVal)  # ignores the zoo intensity tracker attrs, sets maya directly
        except RuntimeError:  # catch, rarely happens when UI is out of sync with VRay
            output.displayWarning("Setting VRay intensity may have failed `.intensityMult` "
                                  "likely set past its maximum value")

    def setScale(self, scale):
        uSize = scale[0] * self.scaleMultiply
        vSize = scale[1] * self.scaleMultiply
        self._setAttrScalar(self.scaleAttr[0], uSize, node=self.shapeName())
        self._setAttrScalar(self.scaleAttr[1], vSize, node=self.shapeName())

    def scale(self):
        uSize = self._getAttrScalar(self.scaleAttr[0], node=self.shapeName())
        vSize = self._getAttrScalar(self.scaleAttr[1], node=self.shapeName())
        if uSize:  # if not 0.0
            uSize /= self.scaleMultiply
        if vSize:
            vSize /= self.scaleMultiply
        return [uSize, vSize, 1.0]

    def setVisibility(self, visibility):
        # invert visibility as V-Ray is invisibility
        super(VRayArea, self).setVisibility(not visibility)

    def visibility(self):
        # invert visibility as V-Ray is invisibility
        return not super(VRayArea, self).visibility()

    def setShape(self, shape):
        if shape == 2:
            output.displayWarning("Cylinder Area Light are not available in VRay")
            return
        elif shape == 3:
            output.displayWarning("Sphere Area Light for VRay is not yet supported by Zoo Tools")
            return
        self._setAttrScalar(self.shapeAttr, shape, node=self.shapeName())

    def shape(self):
        return self._getAttrScalar(self.shapeAttr, node=self.shapeName())

    def setNormalize(self, normalize):
        """Set area light normalization.

        Note: VRay light normalize is controlled via the Unit dropdown.

            default = index 0, (not normalized)
            Lumens = index 1, (normalized)

        :param normalize: Normalized: Scaling does not affect intensity. Not Normalized: Scaling affects intensity
        :type normalize: bool
        """
        self._createZooIntExpAttr()
        intensityGeneric = self.intensity()
        exposureGeneric = self.exposure()
        currentNormalize = self.normalize()
        # Set the attribute default or Lumens
        cmds.setAttr("{}.units".format(self.shapeName()), normalize)  # vray callibrates iteself with script jobs.

        # Check if normalization has changed for the Zoo custom intensity attribute ----------
        newNormalize = self.normalize()
        if currentNormalize == newNormalize:  # normalize has not changed so return
            return

        # Normalization has changed, so set internal attributes ------------------
        physShapeIndex = self.shape()
        if physShapeIndex == 1:  # is a circle, instead use rect to match VRay auto-unit conversions.
            physShapeIndex = 0
        lightShapeName = lu.SHAPE_ATTR_ENUM_LIST_NICE[physShapeIndex]
        scale = self.scale()
        if newNormalize:
            intensityGeneric = lu.convertToNormalizedIntensity(intensityGeneric,
                                                               exposureGeneric,
                                                               scale[0], scale[1], scale[2],
                                                               shape=lightShapeName)[0]
        else:
            intensityGeneric = lu.convertToNonNormalizedIntensity(intensityGeneric,
                                                                  exposureGeneric,
                                                                  scale[0], scale[1], scale[2],
                                                                  shape=lightShapeName)[0]
        # Updates zoo intensity attr in generic units only, vray handles itself while changing units.
        cmds.setAttr(".".join([self.shapeName(), self.zooIntensityAttr]), intensityGeneric)

    def normalize(self):
        """Retuns the area light normalization.

        Note: VRay light normalize is controlled via the Unit dropdown.

            default = index 0, (not normalized)
            Lumens = index 1, (normalized)
            lm/m/m/sr = index 2, (not normalized)
            Watts = index 3, (normalized)
            w/m/m/s = index 4, (not normalized)

        :return: Normalized: Scaling does not affect intensity. Not Normalized: Scaling affects intensity
        :rtype: bool
        """
        index = cmds.getAttr("{}.units".format(self.shapeName()))
        return self.normalizeModes[index]  # returns True or False
