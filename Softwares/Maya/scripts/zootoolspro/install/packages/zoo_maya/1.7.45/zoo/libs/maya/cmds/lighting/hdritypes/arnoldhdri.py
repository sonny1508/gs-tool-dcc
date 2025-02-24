"""This module is the base class for Arnold HDRI Skydomes

HDRI Skydomes have these properties.

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
- tintColor: The tint offset of the skydome (not yet supported)


Example use (base class will not build lights):

.. code-block:: python

    from zoo.libs.maya.cmds.lighting.hdritypes import arnoldhdri
    hdriInst = arnoldhdri.ArnoldHdri("hdriSkydomeName", create=True, suffix=False)  # creates a new HDRI Skydome light

    hdriInst.setName("myHdriSkydomeLight")  # sets name of the light
    hdriInst.setIntensity(1.5)
    hdriInst.setBackgroundVis(False)  # sets the background to be invisible in renders
    hdriInst.setRotate([0.0, 95.3, 0.0])  # rotates the HDRI light 90 degrees

    hdriInst = arnoldhdri.ArnoldHdri(name="existingSkydome", create=False, ingest=True)  # ingest an existing skydome


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

from zoo.libs.maya import zapi

from zoo.libs.utils import output
from zoo.libs.maya.utils import mayaenv
from zoo.libs.maya.cmds.lighting import lightconstants
from zoo.libs.maya.cmds.textures.filetexturetypes import mayafiletexture
from zoo.libs.maya.cmds.lighting.hdritypes import hdribase

MAYA_VERSION = mayaenv.mayaVersion()

# Attribute And Type Specific Information ---------------
NODE_TYPE = "aiSkyDomeLight"


def arnoldVersionNumber():
    try:
        version = cmds.arnoldPlugins(getBuildID=True)
        number = version.split("-")[-1]
        number = number.split(")")[0]
        versionList = number.split(".")
        return int(versionList[0]), int(versionList[1]), int(versionList[2])
    except:  # fails in older versions of Maya
        return 4, 0, 0


class ArnoldHdri(hdribase.HdriBase):
    """Main class that manages a HDRI Skydome Light
    """
    nodetype = NODE_TYPE
    lightSuffix = "ARN"
    intensityAttr = "intensity"
    exposureAttr = "exposure"
    rotateAttr = "rotate"
    translateAttr = "translate"
    scaleAttr = "scale"
    imagePathAttr = "fileTextureName"
    invertAttr = ""
    backgroundVisAttr = "camera"
    tintColorAttr = ""

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
        self.txtrInst = None
        super(ArnoldHdri, self).__init__(name=name,
                                         genAttrDict=genAttrDict,
                                         node=node,
                                         create=create,
                                         ingest=ingest,
                                         suffixName=suffixName,
                                         message=message)
        arnoldMajor, arnoldMinor, arnoldPatch = arnoldVersionNumber()
        if arnoldMajor >= 5 and arnoldMinor >= 3:
            self.exposureAttr = "aiExposure"
        self.initTextureInstance(autoCreate=False, ingest=True)  # starts self.txtrInst (texture instance)

    def initTextureInstance(self, autoCreate=True, ingest=False):
        """Creates and starts the self.txtrInst instance that manages the texture connections.

        Arnold skydomes use Maya's file texture nodes for HDRI images.  Could add Arnold file textures later.

        :param autoCreate: If True will auto build the node network if nothing found otherwise ingest
        :type autoCreate: bool
        :param ingest: If True will only try and ingest an existing node network
        :type ingest: bool
        """
        self.txtrInst = mayafiletexture.MayaFileTexture(masterAttribute="color",
                                                        masterNode=self.shapeNode,
                                                        textureName="colorTexture",
                                                        autoCreate=autoCreate,
                                                        create=False,
                                                        ingest=ingest)

    def delete(self):
        """Deletes the transform node and any connected textures"""
        if self.txtrInst:
            if self.txtrInst.exists():
                self.txtrInst.delete()
        if self.node:
            if self.node.exists():
                cmds.delete(self.node.fullPathName())

    def renderer(self):
        """Returns the current renderer as a string"""
        return lightconstants.ARNOLD

    # -------------------
    # Setters and Getters
    # -------------------

    def setIntensity(self, intensity):
        """Sets the intensity (brightness) of the HDRI Skydome light.

        :param intensity: The intensity of the light in Zoo generic units
        :type intensity: float
        """
        self._setAttrScalar(self.intensityAttr, intensity, node=self.shapeName())

    def intensity(self):
        """Gets the intensity (brightness) of the HDRI Skydome light.

        :return intensity: The intensity of the light in generic Zoo units
        :rtype intensity: float
        """
        return self._getAttrScalar(self.intensityAttr, node=self.shapeName())

    def setExposure(self, intensity):
        """Sets the intensity (brightness) of the HDRI Skydome light.

        :param intensity: The intensity of the light in Zoo generic units
        :type intensity: float
        """
        self._setAttrScalar(self.intensityAttr, intensity, node=self.shapeName())

    def exposure(self):
        """Gets the intensity (brightness) of the HDRI Skydome light.

        :return intensity: The exposure of the light in generic Zoo units
        :rtype intensity: float
        """
        return self._getAttrScalar(self.intensityAttr, node=self.shapeName())

    def _setHDRIColorSpace(self):
        """Sets the colors space in the correct version of Maya.  Handles ACES in 2022 and above"""
        if MAYA_VERSION < 2022 or cmds.colorManagementPrefs(query=True, displayName=True) == "legacy":
            self.txtrInst.setColorSpace("Raw")
        else:
            self.txtrInst.setColorSpace("scene-linear Rec.709-sRGB")

    def setImagePath(self, imagePath):
        """Sets the image path while handling the texture connections

        :param imagePath: The fullpath to the image file
        :type imagePath: str"""
        # Autoload or create a texture network at "lambert2.color"
        if self.txtrInst:
            if self.txtrInst.exists():
                self.txtrInst.setPath(imagePath)
                self._setHDRIColorSpace()
                return
        # Build rebuild textures ---------------------------------------
        self.initTextureInstance(autoCreate=True)  # starts self.txtrInst
        # Check if texture is connected
        if not self.txtrInst.valid:
            output.displayWarning("The existing texture input to the `{}` attribute "
                                  "is not recognized by Zoo Tools".format(self.imagePathAttr))
            return
        self.txtrInst.setPath(imagePath)
        self._setHDRIColorSpace()

    def imagePath(self):
        """Returns the full path of the image texture on disk, can be "" if not used.

        :return imagePath: The full path of the image texture on disk, can be "" if not used.
        :rtype imagePath: str
        """
        if self.txtrInst:
            if self.txtrInst.exists():
                return self.txtrInst.path()
        # Try again possibly rebuilt manually.
        self.initTextureInstance(autoCreate=False, ingest=True)  # starts self.txtrInst (texture instance)
        if self.txtrInst.exists():
            return self.txtrInst.path()
        return ""

    def setBackgroundVis(self, backgroundVis):
        self._setAttrScalar(self.backgroundVisAttr, float(backgroundVis), node=self.shapeName())

    def backgroundVis(self):
        bgVisFloat = self._getAttrScalar(self.backgroundVisAttr, node=self.shapeName())
        return round(bgVisFloat)

    def setTint(self, tint):
        pass

    def tint(self):
        pass
