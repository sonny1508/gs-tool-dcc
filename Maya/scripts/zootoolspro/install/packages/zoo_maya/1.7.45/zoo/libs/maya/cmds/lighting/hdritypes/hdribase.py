"""This module is the base class for hdri skydomes

This class needs to be extended/overridden by each renderer type.  Provides base functionality.

A HDRI Skydome has these properties:

    - name: The name of the light (str)
    - shapeName: The name of the light (str)
    - nodetype: The node type of the HDRI Skydome (str)
    - lightSuffix: The optional suffix of the light
    - intensity: The intensity of the light
    - rotate: The rotation values in 3d space
    - translate: The translation values in 3d space
    - scale: The scale values in 3d space
    - imagePath: The path to the skydome image on disk
    - invert: Is the HDRI image inverted for text etc?
    - backgroundVis: Is the skydome visible in the scene?
    - tintColor: The tint offset of the skydome


Example use (base class will not build lights):

.. code-block:: python

    from zoo.libs.maya.cmds.lighting.hdritypes import hdribase
    hdriInst = hdribase.HdriBase("hdriSkydomeName", create=True, suffix=False)  # creates a new HDRI Skydome light

    hdriInst.setName("myHdriSkydomeLight")  # sets name of the light
    hdriInst.setIntensity(1.5)
    hdriInst.setBackgroundVis(False)  # sets the background to be invisible in renders
    hdriInst.setRotate([0.0, 95.3, 0.0])  # rotates the HDRI light 90 degrees

    hdriInst = hdribase.HdriBase(name="existingSkydome", create=False, ingest=True)  # ingest an existing skydome


Default HDRI dictionary example from zoo.libs.maya.cmds.lighting.lightconstants:

    HDRI_DEFAULT_VALUES = {HDRI_NAME: "hdriSkydome",
                           HDRI_INTENSITY: 1.0,
                           HDRI_ROTATE: [0.0, 0.0, 0.0],
                           HDRI_TRANSLATE: [0.0, 0.0, 0.0],
                           HDRI_SCALE: [1.0, 1.0, 1.0],
                           HDRI_TEXTURE: "",
                           HDRI_INVERT: False,
                           HDRI_LIGHTVISIBILITY: True,
                           HDRI_TINT: [1.0, 1.0, 1.0]}

Author: Andrew Silke
"""
from maya import cmds

from zoo.libs.utils import output
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.lighting import lightingutils, lightsbase
from zoo.libs.maya.cmds.lighting.lightconstants import HDRI_NAME, HDRI_INTENSITY, HDRI_LIGHTVISIBILITY, \
    HDRI_TEXTURE, HDRI_ROTATE, HDRI_TRANSLATE, HDRI_SCALE, HDRI_INVERT, HDRI_TINT, HDRI_DEFAULT_VALUES

# Attribute And Type Specific Information ---------------
NODE_TYPE = ""
LIGHT_SUFFIX = ""
INTENSITY_ATTR = ""
ROTATE_ATTR = "rotate"
TRANSLATE_ATTR = "translate"
SCALE_ATTR = "scale"
IMAGE_PATH_ATTR = ""
INVERT_ATTR = ""
BACKGROUND_VIS_ATTR = ""
TINT_COLOR_ATTR = ""
INTENSITY_MULTIPLY_ATTR = "zooIntensityMultiply"
ROTATE_OFFSET_ATTR = "zooRotateOffset"


class HdriBase(lightsbase.LightsBase):
    """Main class that manages a HDRI Skydome Light
    """
    nodetype = NODE_TYPE
    lightSuffix = LIGHT_SUFFIX
    intensityAttr = INTENSITY_ATTR
    rotateAttr = ROTATE_ATTR
    translateAttr = TRANSLATE_ATTR
    scaleAttr = SCALE_ATTR
    imagePathAttr = IMAGE_PATH_ATTR
    invertAttr = INVERT_ATTR
    backgroundVisAttr = BACKGROUND_VIS_ATTR
    tintColorAttr = TINT_COLOR_ATTR
    intensityMultiplyAttr = INTENSITY_MULTIPLY_ATTR
    rotateOffsetAttr = ROTATE_OFFSET_ATTR

    rotOffset = 0.0
    intensityOffset = 0.0
    scaleMultiply = 1.0

    def __init__(self, name="", genAttrDict=None, node=None, create=False, ingest=False, suffixName=False,
                 message=True):
        """Either loads a HDRI skydome light or creates it.

        To create a new Skydome:
            create=True and node=False to create a new shader

        To load a skydome by zapiNode name
            node="zapiNode" (should be a shader node) and ingest=True

        To load a skydome by string:
            shaderName="shaderName" and ingest=True

        :param name: The string name of the skydome to load or create
        :type name: str
        :param node: Optional zapi node object and will ingest and not create a new skydome
        :type node: :class:`zapi.DGNode`
        :param genAttrDict: The generic attribute dictionary with attribute values to set only if creating
        :type genAttrDict: dict(str)
        :param create: If True then create a new skydome False will load the skydome into the instance
        :type create: bool
        :param ingest: If True then ingest the skydome into the instance
        :type ingest: bool
        :param suffixName: If True automatically suffix's the given name with the renderer's suffix
        :type suffixName: bool
        :param message: Report a message to the user only if creating
        :type message: bool
        """
        super(HdriBase, self).__init__()

        if name:
            self.nameStr = name
        else:
            self.nameStr = HDRI_DEFAULT_VALUES[HDRI_NAME]

        if suffixName and self.lightSuffix:
            self.nameStr = "_".join([self.nameStr, self.lightSuffix])
            self.nameStr = self._renameUniqueSuffixName(self.nameStr)  # handles unique names light_01_ARN

        self.setDefaults(apply=False, setName=False)  # sets self.xxxVal values, can be changed later in __init___

        if not genAttrDict:  # no dictionary given so setup a network with default values
            genAttrDict = dict(HDRI_DEFAULT_VALUES)
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

    def createSkydomeLight(self):
        """Creates the skydome light with no settings. Designed to be changed after creation.

        :return lightTransformName: The light's transform name
        :rtype lightTransformName: str
        :return shapeNodeName:  The light's shape node name
        :rtype shapeNodeName: str
        """
        lightTransformName, shapeNodeName = lightingutils.createLight("skydomeTempNameXX", self.nodetype)
        # must connect to default light set
        cmds.connectAttr("{}.instObjGroups".format(lightTransformName),
                         "defaultLightSet.dagSetMembers",
                         nextAvailable=True)
        return lightTransformName, shapeNodeName

    def create(self, message=True):
        """Creates the HDRI Skydome light

        :param message: Report a message to the user?
        :type message: bool
        """
        lightTransformName, shapeNodeName = self.createSkydomeLight()
        self.node = zapi.nodeByName(lightTransformName)
        self.shapeNode = zapi.nodeByName(shapeNodeName)
        self.rename(self.nameStr)  # Rename from a temp name to handle name complexity
        if message:
            output.displayInfo("{} HDRI Skydome created: {} ".format(self.renderer(), lightTransformName))

    # -------------------
    # Dictionary Setters and Getters
    # -------------------

    def shapeAttributeNames(self):
        """Generic attributes are the keys and the shader's attributes are the values.

        :return: A dictionary with strings as keys and attribute string names as values.
        :rtype: dict
        """
        return {HDRI_INTENSITY: self.intensityAttr,
                HDRI_TEXTURE: self.imagePathAttr,
                HDRI_INVERT: self.invertAttr,
                HDRI_LIGHTVISIBILITY: self.backgroundVisAttr,
                HDRI_TINT: self.tintColorAttr
                }

    def transformAttributeNames(self):
        """Generic attributes are the keys and the HDRI's attributes are the values.

        :return: A dictionary with strings as keys and attribute string names as values.
        :rtype: dict
        """
        return {HDRI_ROTATE: self.rotateAttr,
                HDRI_SCALE: self.scaleAttr}

    def setDefaults(self, apply=True, setName=False):
        """Sets the defaults internally, the shader does not need to be created unless apply=True

        :param apply: If True then apply the settings to the shader, otherwise is just changed in the class instance.
        :type apply: bool
        """
        if setName:
            self.nameVal = HDRI_DEFAULT_VALUES[HDRI_NAME]
        self.intensityVal = HDRI_DEFAULT_VALUES[HDRI_INTENSITY]
        self.rotateVal = HDRI_DEFAULT_VALUES[HDRI_ROTATE]
        self.translateVal = HDRI_DEFAULT_VALUES[HDRI_TRANSLATE]
        self.scaleVal = HDRI_DEFAULT_VALUES[HDRI_SCALE]
        self.imagePathVal = HDRI_DEFAULT_VALUES[HDRI_TEXTURE]
        self.invertVal = HDRI_DEFAULT_VALUES[HDRI_INVERT]
        self.backgroundVisVal = HDRI_DEFAULT_VALUES[HDRI_LIGHTVISIBILITY]
        self.tintVal = HDRI_DEFAULT_VALUES[HDRI_TINT]
        if apply:
            self.applyCurrentSettings()

    def setFromDict(self, genAttrDict, setName=False, apply=True, noneIsDefault=True):
        """Sets the hdri light from a generic attribute dictionary. Values as attribute values.

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
                                               HDRI_NAME,
                                               self.nameVal,
                                               HDRI_DEFAULT_VALUES[HDRI_INTENSITY],
                                               noneIsDefault)
        self.intensityVal = self._setDictSingle(genAttrDict,
                                                HDRI_INTENSITY,
                                                self.intensityVal,
                                                HDRI_DEFAULT_VALUES[HDRI_INTENSITY],
                                                noneIsDefault)
        self.rotateVal = self._setDictSingle(genAttrDict,
                                             HDRI_ROTATE,
                                             self.rotateVal,
                                             HDRI_DEFAULT_VALUES[HDRI_ROTATE],
                                             noneIsDefault)
        self.translateVal = self._setDictSingle(genAttrDict,
                                                HDRI_TRANSLATE,
                                                self.translateVal,
                                                HDRI_DEFAULT_VALUES[HDRI_TRANSLATE],
                                                noneIsDefault)
        self.scaleVal = self._setDictSingle(genAttrDict,
                                            HDRI_SCALE,
                                            self.scaleVal,
                                            HDRI_DEFAULT_VALUES[HDRI_SCALE],
                                            noneIsDefault)
        self.imagePathVal = self._setDictSingle(genAttrDict,
                                                HDRI_TEXTURE,
                                                self.imagePathVal,
                                                HDRI_DEFAULT_VALUES[HDRI_TEXTURE],
                                                noneIsDefault)
        self.invertVal = self._setDictSingle(genAttrDict,
                                             HDRI_INVERT,
                                             self.invertVal,
                                             HDRI_DEFAULT_VALUES[HDRI_INVERT],
                                             noneIsDefault)
        self.backgroundVisVal = self._setDictSingle(genAttrDict,
                                                    HDRI_LIGHTVISIBILITY,
                                                    self.backgroundVisVal,
                                                    HDRI_DEFAULT_VALUES[HDRI_LIGHTVISIBILITY],
                                                    noneIsDefault)
        self.tintVal = self._setDictSingle(genAttrDict,
                                           HDRI_TINT,
                                           self.tintVal,
                                           HDRI_DEFAULT_VALUES[HDRI_TINT],
                                           noneIsDefault)
        if apply:
            self.applyCurrentSettings()

    def applyCurrentSettings(self, applyName=False):
        """Applies the current settings to the normal map's texture network"""
        if applyName:
            self.setName(self.nameVal)
        self.setIntensity(self.intensityVal)
        self.setRotate(self.rotateVal)
        self.setTranslate(self.translateVal)
        self.setScale(self.scaleVal, invert=self.invertVal)  # Scale sometimes needs invert
        self.setImagePath(self.imagePathVal)
        self.setInvert(self.invertVal)
        self.setBackgroundVis(self.backgroundVisVal)
        self.setTint(self.tintVal)

    def pullSettings(self, includeName=False):
        """Pulls the current attributes from the current shader, shader must exist"""
        if includeName:
            self.nameVal = self.name()
        self.intensityVal = self.intensity()
        self.rotateVal = self.rotate()
        self.translateVal = self.translate()
        self.scaleVal = self.scale()
        self.imagePathVal = self.imagePath()
        self.invertVal = self.invert()
        self.backgroundVisVal = self.backgroundVis()
        self.tintVal = self.tint()

    # -------------------
    # Setters and Getters
    # -------------------

    def setIntensity(self, intensity):
        pass

    def intensity(self):
        pass

    def setRotate(self, rotate):
        """Sets the rotation of the HDRI Skydome light.

        Note values are in generic units to account for offsets between renderers.

        :param rotate: The rotation values in degrees [0.0, 90.0, 0.0]
        :type rotate: list(float)
        """
        self._setAttrVector(ROTATE_ATTR, rotate)

    def setRotateLean(self, rotate, transform):
        """Fast hardcoded rotate code run for slider code so its as lean as possible. No safety checks.

        :param rotate: The rotation values in degrees [0.0, 90.0, 0.0]
        :type rotate: list(float)
        """
        cmds.setAttr("{}.rotate".format(transform),
                     rotate[0],
                     rotate[1] + self.rotOffset,
                     rotate[2],
                     type="double3")

    def rotate(self):
        return self._getAttrVector(ROTATE_ATTR)

    def setTranslate(self, translate):
        self._setAttrVector(TRANSLATE_ATTR, translate)

    def translate(self):
        return self._getAttrVector(ROTATE_ATTR)

    def setScale(self, scale, invert=False):
        if invert:  # Set scaleZ to be a negative value
            scale = [scale[0], scale[1], -abs(scale[2])]
        else:
            scale = [scale[0], scale[1], abs(scale[2])]
        self._setAttrVector(SCALE_ATTR, scale)

    def scale(self):
        return self._getAttrVector(SCALE_ATTR)

    def setImagePath(self, imagePath):
        pass

    def imagePath(self):
        pass

    def setInvert(self, invert):
        scale = self.scale()
        if not scale:
            return
        if invert:  # Set scaleZ to be a negative value
            scale = [scale[0], scale[1], -abs(scale[2])]
        else:
            scale = [scale[0], scale[1], abs(scale[2])]
        self._setAttrVector(SCALE_ATTR, scale)

    def invert(self):
        scale = self.scale()
        if scale is None:
            return None
        if scale[2] < 0.0:  # If scaleZ is a negative number then is inverted
            return True
        return False

    def setBackgroundVis(self, backgroundVis):
        pass

    def backgroundVis(self):
        pass

    def setTint(self, tint):
        pass

    def tint(self):
        pass

    # -------------------
    # Intensity Multiplier --- Optional custom zoo attributes added to the HDRI shape node
    # -------------------

    def setIntensityMultiply(self, intensityMultiply):
        """Sets the zoo intensity multiply attribute, this is a custom attribute and will create it if it doesn't exist.

        IntensityMultiply is an optional custom attribute controlled by the Zoo HDRI Skydome UI

        :param intensityMultiply: The value of the intensityMultiply attribute
        :type intensityMultiply: float
        """
        if not cmds.attributeQuery(INTENSITY_MULTIPLY_ATTR, node=self.shapeName(), exists=True):  # if attribute exists
            cmds.addAttr(self.shapeName(), longName=INTENSITY_MULTIPLY_ATTR, attributeType='double')
        cmds.setAttr(".".join([self.shapeName(), INTENSITY_MULTIPLY_ATTR]), intensityMultiply)

    def intensityMultiply(self):
        """Returns the value of the zoo intensity multiply custom attribute.  Will return None if it doesn't exist.

        IntensityMultiply is an optional custom attribute controlled by the Zoo HDRI Skydome UI

        :return intensityMultiply: The value of the intensityMultiply attribute, will be None if doesn't exist
        :rtype intensityMultiply: float
        """
        if not cmds.attributeQuery(INTENSITY_MULTIPLY_ATTR, node=self.shapeName(), exists=True):  # if attribute exists
            return None
        return cmds.getAttr(".".join([self.shapeName(), INTENSITY_MULTIPLY_ATTR]))

    def setIntensityAndMultiply(self, intensity, intensityMultiply):
        """Sets both the intensity and the intensity multiply values usually from a UI

        IntensityMultiply is an optional custom attribute controlled by the Zoo HDRI Skydome UI

        :param intensity: The intensity value from a UI
        :type intensity: float
        :param intensityMultiply: The intensity multiply value from a UI
        :type intensityMultiply: float
        """
        self.setIntensity(intensity * intensityMultiply)
        self.setIntensityMultiply(intensityMultiply)

    def intensityAndMultiply(self):
        """Returns both the intensity and intensity multiply value. Usually for a UI.

        IntensityMultiply is an optional custom attribute controlled by the Zoo HDRI Skydome UI

        :return intensity: The intensity value of the light divided by intensityMultiply
        :rtype intensity: float
        :return intensityMultiply: The multiplication value of the intensity
        :rtype intensityMultiply: float
        """
        intensity = self.intensity()
        intensityMultiply = self.intensityMultiply()
        if intensityMultiply:
            intensity /= intensityMultiply
        elif intensityMultiply == 0.0:
            intensity = 0.0
        else:
            intensityMultiply = 1.0
        return intensity, intensityMultiply

    # -------------------
    # Rotation Offset --- Optional custom zoo attributes added to the HDRI shape node
    # -------------------

    def setRotateOffset(self, rotateOffset):
        """Sets the zoo rotate offset attribute, this is a custom attribute and will create it if it doesn't exist.

        RotateOffset is an optional custom attribute controlled by the Zoo HDRI Skydome UIs

        :param rotateOffset: The value of the rotateOffset attribute
        :type rotateOffset: float
        """
        if not cmds.attributeQuery(ROTATE_OFFSET_ATTR, node=self.shapeName(), exists=True):  # if attribute exists
            cmds.addAttr(self.shapeName(), longName=ROTATE_OFFSET_ATTR, attributeType='double')
        cmds.setAttr(".".join([self.shapeName(), ROTATE_OFFSET_ATTR]), rotateOffset)

    def rotateOffset(self):
        """Returns the value of the zoo rotate offset custom attribute.  Will return None if it doesn't exist.

        RotateOffset is an optional custom attribute controlled by the Zoo HDRI Skydome UIs

        :return rotateOffset: The value of the rotateOffset attribute, will be None if it doesn't exist
        :rtype rotateOffset: float
        """
        if not cmds.attributeQuery(ROTATE_OFFSET_ATTR, node=self.shapeName(), exists=True):  # if attribute exists
            return None
        return cmds.getAttr(".".join([self.shapeName(), ROTATE_OFFSET_ATTR]))

    def setRotateAndOffset(self, rotate, rotateOffset):
        """Sets both the rotate and rotate offset values, usually from a UI.

        RotateOffset is an optional custom attribute controlled by the Zoo HDRI Skydome UIs

        :param rotate: The rotation value usually from a UI
        :type rotate: list(float)
        :param rotateOffset: The rotate offset value
        :type rotateOffset: float
        """
        self.setRotate([rotate[0], rotate[1] + rotateOffset, rotate[2]])
        self.setRotateOffset(rotateOffset)

    def rotateAndOffset(self):
        """Returns both the rotate and rotate offset values, usually for a UI.

        RotateOffset is an optional custom attribute controlled by the Zoo HDRI Skydome UIs

        :return rotate: The rotate value with the rotate offset value taken from the y rotation
        :rtype rotate: list(float)
        :return rotateOffset: The Y Rotate offset value
        :rtype rotateOffset: float
        """
        rotate = self.rotate()
        rotateOffset = self.rotateOffset()
        if rotateOffset:
            rotate = [rotate[0], rotate[1] - rotateOffset, rotate[2]]
        if rotateOffset is None:
            rotateOffset = 0.0
        return rotate, rotateOffset

    # --------------------------
    # CONNECTIONS
    # --------------------------

    def connectedAttrs(self):
        """Checks if any of the supported attributes have connections, if so returns:

        connectionDict: generic attributes as the keys and "node.attr" as connection values.

        :return connectionDict: Dictionary with generic attributes as the keys and "node.attr" as connection values
        :rtype connectionDict: dict(str)
        """
        connectionDict = dict()

        hdriShape = self.shapeName()
        hdriTransform = self.name()
        if not hdriTransform:
            return None

        shapeAttrDict = self.shapeAttributeNames()
        transformAttrDict = self.transformAttributeNames()

        # Check Shape node attributes intensity, bgVis etc -----------
        for key in shapeAttrDict:
            attr = shapeAttrDict[key]
            if not attr:
                continue
            if key == HDRI_TEXTURE:
                continue  # don't disable texture attributes as should always be connected
            if cmds.listConnections(".".join([hdriShape, attr]), destination=False, source=True):
                connectionDict[key] = cmds.listConnections(".".join([hdriShape, attr]), plugs=True)[0]

        # Check transforms so Rotation and Scale -----------
        for key in transformAttrDict:
            attr = transformAttrDict[key]
            if not attr:
                continue
            # test vector is connected
            if cmds.listConnections(".".join([hdriTransform, attr]), destination=False, source=True):
                connectionDict[key] = cmds.listConnections(".".join([hdriTransform, attr]), plugs=True)[0]
            # test each axis of the vector is connected
            for axis in ("X", "Y", "Z"):  # must check each axis for constraint connections.
                if cmds.listConnections(".".join([hdriTransform, "".join([attr, axis])]),
                                        destination=False, source=True):
                    connectionDict[key] = cmds.listConnections(".".join([hdriTransform, "".join([attr, axis])]),
                                                               plugs=True)[0]
                    break

        return connectionDict