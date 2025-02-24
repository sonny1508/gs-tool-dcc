"""This module is the base class for Renderman HDRI Skydomes

Author: Andrew Silke

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
- tintColor: The tint offset of the skydome


Example use (base class will not build lights):

.. code-block:: python

    from zoo.libs.maya.cmds.lighting.hdritypes import rendermanhdri
    hdriInst = rendermanhdri.RendermanHdri("hdriSkydomeName", create=True, suffix=False)  # creates a new HDRI light

    hdriInst.setName("myHdriSkydomeLight")  # sets name of the light
    hdriInst.setIntensity(1.5)
    hdriInst.setBackgroundVis(False)  # sets the background to be invisible in renders
    hdriInst.setRotate([0.0, 95.3, 0.0])  # rotates the HDRI light 90 degrees

    hdriInst = rendermanhdri.RendermanHdri(name="existingSkydome", create=False, ingest=True)  # ingest a skydome


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
from zoo.libs.maya import zapi

from zoo.libs.utils import output
from zoo.libs.maya.cmds.lighting import rendermanlights, lightconstants
from zoo.libs.maya.cmds.lighting.hdritypes import hdribase
from zoo.libs.utils import color

# Attribute And Type Specific Information ---------------
NODE_TYPE = "PxrDomeLight"


class RendermanHdri(hdribase.HdriBase):
    """Main class that manages a HDRI Skydome Light
    """
    nodetype = NODE_TYPE
    lightSuffix = "PXR"
    intensityAttr = "intensity"
    rotateAttr = "rotate"
    translateAttr = "translate"
    scaleAttr = "scale"
    imagePathAttr = "lightColorMap"
    invertAttr = ""
    backgroundVisAttr = "primaryVisibility"
    tintColorAttr = "lightColor"

    rotOffset = 180
    scaleMultiply = 0.4

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
        super(RendermanHdri, self).__init__(name=name,
                                            genAttrDict=genAttrDict,
                                            node=node,
                                            create=create,
                                            ingest=ingest,
                                            suffixName=suffixName,
                                            message=message)

    def renderer(self):
        """Returns the current renderer as a string"""
        return lightconstants.RENDERMAN

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

    def rotate(self):
        """Old Renderman was out 180 degrees out from Arnold (generic) so compensate
        Full gimbal is not well supported so orientations can mismatch.

        Newer versions of Renderman match perfectly with Arnold so all good 22 and above.

        :return rotate: The rotation value generic value for UIs
        :rtype rotate: list(float)
        """
        rotate = super(RendermanHdri, self).rotate()
        if rendermanlights.getRendermanVersion() < 22.0 and rotate:  # Renderman had a rotated IBL offset pre v22
            rotate = (rotate[0], rotate[1] + self.rotOffset, rotate[2])
        return rotate

    def setRotate(self, rotate):
        """Old Renderman was out 180 degrees out from Arnold (generic) so compensate
        Full gimbal is not well supported so orientations can mismatch.

        Newer versions of Renderman match perfectly with Arnold so all good 22 and above.

        :param rotate: The rotation value generic value for UIs
        :type rotate: list(float)
        """
        if rendermanlights.getRendermanVersion() < 22.0 and rotate:  # Renderman had a rotated IBL offset pre v22
            return (rotate[0], rotate[1] - self.rotOffset, rotate[2])
        super(RendermanHdri, self).setRotate(rotate)
        return

    def scale(self):
        """Retrieves the scale value while compensating for Renderman's scale differences.  Result is generic units.

        :return scale: Scale of the light in generic units (UI)
        :return scale: list(float)
        """
        scale = super(RendermanHdri, self).scale()
        sm = self.scaleMultiply
        if not scale:
            return scale
        if rendermanlights.getRendermanVersion() < 22.0:  # renderman was inverted skydomes pre v22
            return (scale[0] * 2000, scale[1] * 2000, scale[2] * 2000 - 1)
        else:
            return (scale[0] * sm, scale[1] * sm, scale[2] * sm)

    def setScale(self, scale, invert=False):
        """Scales the HDRI light while compensating for Renderman's scale differences

        :param scale: Scale of the light in generic units (UI)
        :type scale: list(float)
        :param invert: Negatively scale the HDRI light on Z
        :type invert: bool
        """
        sm = self.scaleMultiply
        if scale:
            if rendermanlights.getRendermanVersion() < 22.0:  # renderman was inverted skydomes pre v22
                scale = (scale[0] / 2000, scale[1] / 2000, scale[2] / 2000 - 1)
            else:
                scale = (scale[0] / sm, scale[1] / sm, scale[2] / sm)
        super(RendermanHdri, self).setScale(scale)

    def setImagePath(self, imagePath):
        self._setAttrScalar(self.imagePathAttr, imagePath, node=self.shapeName(), type="string")

    def imagePath(self):
        return self._getAttrScalar(self.imagePathAttr, node=self.shapeName())

    def setBackgroundVis(self, backgroundVis):
        self._setAttrScalar(self.backgroundVisAttr, backgroundVis, node=self.shapeName())

    def backgroundVis(self):
        return self._getAttrScalar(self.backgroundVisAttr, node=self.shapeName())

    def setTint(self, tint):
        self._setAttrVector(self.tintColorAttr, tint, node=self.shapeName())

    def tint(self):
        return self._getAttrVector(self.tintColorAttr, node=self.shapeName())
