"""This module is the base class for VRay HDRI Skydomes

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

    from zoo.libs.maya.cmds.lighting.hdritypes import vrayhdri
    hdriInst = vrayhdri.VRayHdri("hdriSkydomeName", create=True, suffix=False)  # creates a new HDRI light

    hdriInst.setName("myHdriSkydomeLight")  # sets name of the light
    hdriInst.setIntensity(1.5)
    hdriInst.setBackgroundVis(False)  # sets the background to be invisible in renders
    hdriInst.setRotate([0.0, 95.3, 0.0])  # rotates the HDRI light 90 degrees

    hdriInst = vrayhdri.VRayHdri(name="existingSkydome", create=False, ingest=True)  # ingest an existing skydome


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
from zoo.libs.maya.cmds.lighting import lightconstants
from zoo.libs.maya.cmds.textures.filetexturetypes import mayafiletexture
from zoo.libs.maya.cmds.lighting.hdritypes import hdribase

# Attribute And Type Specific Information ---------------
NODE_TYPE = "VRayLightDomeShape"


class VRayHdri(hdribase.HdriBase):
    """Main class that manages a HDRI Skydome Light
    """
    nodetype = NODE_TYPE
    lightSuffix = "VRAY"
    intensityAttr = "intensityMult"
    rotateAttr = "rotate"
    translateAttr = "translate"
    scaleAttr = "scale"
    imagePathAttr = "fileTextureName"
    invertAttr = ""
    backgroundVisAttr = "invisible"
    tintColorAttr = "lightColor"

    rotOffset = 90.0
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
        self.fileTextureNode = None
        self.placeEnvNode = None
        self.place2dNode = None
        super(VRayHdri, self).__init__(name=name,
                                       genAttrDict=genAttrDict,
                                       node=node,
                                       create=create,
                                       ingest=ingest,
                                       suffixName=suffixName,
                                       message=message)
        self._initTexture()  # sets self.fileTextureNode, self.placeEnvNode, self.place2dNode

    def _initTexture(self):
        """Creates the textures or ingests

        :param autoCreate: If True will auto build the node network if nothing found otherwise ingest
        :type autoCreate: bool
        :param ingest: If True will only try and ingest an existing node network
        :type ingest: bool
        """
        self._ingestTextureNetwork()  # ingests self.fileTextureNode, self.placeEnvNode and self.place2dNode
        if self.place2dNode:  # all texture nodes have been ingested
            return
        self._createTextureNetwork()

    def _createTextureNetwork(self):
        """Creates and connects the texture node setup for Vray.
        Builds a file texture, VRayPlaceEnv node and place2dTexture
        """
        # Create texture node network ------------------
        transformNode = self.node.fullPathName()
        shapeNode = self.shapeName()
        # Create Nodes ----------------------
        fileNode = cmds.shadingNode("file", name="skydomeTexture", asTexture=True, isColorManaged=True)
        vrayPlaceEnv = cmds.shadingNode("VRayPlaceEnvTex", name="skydomePlaceEnv", asTexture=True, isColorManaged=True)
        place2d = cmds.shadingNode("place2dTexture", name="skydomePlace2d", asTexture=True, isColorManaged=True)
        cmds.connectAttr("{}.uvCoord".format(place2d), "{}.outUV".format(vrayPlaceEnv))
        cmds.connectAttr("{}.worldMatrix".format(transformNode), "{}.transform".format(vrayPlaceEnv))
        cmds.connectAttr("{}.outUV".format(vrayPlaceEnv), "{}.uvCoord".format(fileNode))
        cmds.connectAttr("{}.outColor".format(fileNode), "{}.domeTex".format(shapeNode))
        # Set VRay Env Node to be controlled via the transform node for rotation ----------------------
        cmds.setAttr("{}.useTransform".format(vrayPlaceEnv), True)
        cmds.setAttr("{}.mappingType".format(vrayPlaceEnv), 2)  # spherical mapping
        # Set variables as zapi nodes -------------------------
        self.fileTextureNode = zapi.nodeByName(fileNode)
        self.placeEnvNode = zapi.nodeByName(vrayPlaceEnv)
        self.place2dNode = zapi.nodeByName(place2d)

    def _findZapiNodeConnected(self, destinationNode, destinationAttr, expectedNodeType):
        """Simple method for finding the zapi node connected to shapeNode.destinationAttr

        :param destinationAttr: The attribute naem to search the connection
        :type destinationAttr: str
        :param expectedNodeType: The type of node we are expecting to find
        :type expectedNodeType: str
        :return zapiNode: The connected zapi node or None if nothing found
        :rtype zapiNode: :class:`zapi.DGNode`
        """
        sourceConnections = cmds.listConnections(".".join([destinationNode.fullPathName(), destinationAttr]),
                                                 destination=False,
                                                 source=True,
                                                 plugs=True)
        if not sourceConnections:
            return None
        node = sourceConnections[0].split(".")[0]
        if cmds.objectType(node) != expectedNodeType:
            return None
        return zapi.nodeByName(node)

    def _ingestTextureNetwork(self):
        """VRay has its own node structure for Skydomes

        Ingest the VRay node network so textures can be changed and removed later.

        - self.fileTextureNode (type file)
        - self.placeEnvNode  (type VRayPlaceEnvTex)
        - self.place2dNode (type place2dTexture)

        These nodes will be zapi nodes or None if no texture network exists.
        """
        self.placeEnvNode = None
        self.place2dNode = None
        # Find the file node ------------------------------
        self.fileTextureNode = self._findZapiNodeConnected(self.shapeNode, "domeTex", "file")
        if not self.fileTextureNode:
            return
        # Find the env node ------------------------------
        self.placeEnvNode = self._findZapiNodeConnected(self.fileTextureNode, "uvCoord", "VRayPlaceEnvTex")
        if not self.placeEnvNode:
            return
        # Find the place 2d node ------------------------------
        self.place2dNode = self._findZapiNodeConnected(self.placeEnvNode, "outUV", "place2dTexture")
        if cmds.getAttr("{}.useTransform".format(self.placeEnvNode)) == False:
            cmds.setAttr("{}.useTransform".format(self.placeEnvNode), True)  # Use Transform to True

    def delete(self):
        """Deletes the transform node and any connected textures"""
        if self.place2dNode:
            if self.place2dNode.exists():
                self.place2dNode.delete()
        if self.placeEnvNode:
            if self.placeEnvNode.exists():
                self.placeEnvNode.delete()
        if self.fileTextureNode:
            if self.fileTextureNode.exists():
                self.fileTextureNode.delete()
        if self.node:
            if self.node.exists():
                cmds.delete(self.node.fullPathName())

    def renderer(self):
        """Returns the current renderer as a string"""
        return lightconstants.VRAY

    def create(self, message=True):
        super(VRayHdri, self).create(message)
        self._setAttrScalar("useDomeTex", 1)  # VRay must set to Use Dome Tex: On
        self._setAttrScalar("multiplyByTheLightColor", 1)  # Multiply by light color for Tint On

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
        """VRay is 90 degrees out from Arnold (generic) so compensate
        Full gimbal is not well supported so orientations can mismatch.

        :return rotate: The rotation value generic value for UIs
        :rtype rotate: list(float)
        """
        rotate = super(VRayHdri, self).rotate()
        if rotate:
            rotate = (rotate[0], rotate[1] - 90, rotate[2])
        return rotate

    def setRotate(self, rotate):
        """VRay is 90 degrees out from Arnold (generic)  so compensate
        Full gimbal is not well supported so orientations can mismatch.

        :param rotate: The rotation value generic value for UIs
        :type rotate: list(float)
        """
        if rotate is not None:
            rotate = (rotate[0], rotate[1] + 90, rotate[2])
        super(VRayHdri, self).setRotate(rotate)

    def setImagePath(self, imagePath):
        """Sets the image path while handling the texture connections"""
        # Autoload or create a texture network at "lambert2.color"
        self._ingestTextureNetwork()
        if not self.place2dNode:  # Node network does not exist so create
            self._initTexture()
            if not self.place2dNode:
                return
        cmds.setAttr("{}.fileTextureName".format(self.fileTextureNode.fullPathName()), imagePath, type="string")

    def imagePath(self):
        """Returns the full path of the image texture on disk, can be "" if not used.

        :return imagePath: The full path of the image texture on disk, can be "" if not used.
        :rtype imagePath: str
        """
        self._ingestTextureNetwork()
        if not self.place2dNode:
            return ""
        return cmds.getAttr("{}.fileTextureName".format(self.fileTextureNode.fullPathName()))

    def setBackgroundVis(self, backgroundVis):
        self._setAttrScalar(self.backgroundVisAttr, not backgroundVis, node=self.shapeName())

    def backgroundVis(self):
        return not self._getAttrScalar(self.backgroundVisAttr, node=self.shapeName())

    def setTint(self, tint):
        self._setAttrScalar("multiplyByTheLightColor", 1)  # Multiply by light color for Tint On
        self._setAttrVector(self.tintColorAttr, tint, node=self.shapeName())

    def tint(self):
        multLightColor = self._getAttrScalar("multiplyByTheLightColor")
        if not multLightColor:
            return [1.0, 1.0, 1.0]
        else:
            return self._getAttrVector(self.tintColorAttr, node=self.shapeName())
