"""This module is the base class for filepath texture map creation.
Color grading may be added later.

This class is intended to be extended/overridden by each renderer or file texture type.  Provides base functionality.

A texture node network will have these values

- Texture file path
- Color Space
- Output Connection
- 2d texture properties

    - repeat UV
    - Offset UV
    - Rotate UV
    - Scale 3d (triplanar and 3d placement)

A texture can be stacked into a layer texture and mixed. (later)

See subClasses for use.  For example mayafiletexture.py
"""
from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.utils import output
from zoo.libs.maya.cmds.shaders import shdmultconstants


# Generic Keys for dictionaries ---------------
TEXTURE_NAME = "normalName"
TEXTURE_PATH = "normalFilePath"
TEXTURE_COL_SPACE = "normalColorSpace"

PLACE_TYPE = "placeType"  # For Triplanar, 3dPlacement or UVs
PLACE_REPEAT_UV = "placeRepeatUV"
PLACE_OFFSET_UV = "placeOffsetUV"
PLACE_ROTATE_UV = "placeRotateUV"
PLACE_3D_SCALE = "place3dScale"  # For Triplanar, 3dPlacement

OUTPUT_ATTR = ""  # Overridden

DEFAULT_VALUES = {TEXTURE_NAME: "texture01",
                  TEXTURE_COL_SPACE: "sRGB",
                  TEXTURE_PATH: "",
                  PLACE_TYPE: "",
                  PLACE_REPEAT_UV: [1.0, 1.0],
                  PLACE_OFFSET_UV: [0.0, 0.0],
                  PLACE_ROTATE_UV: 0.0,
                  PLACE_3D_SCALE: [1.0, 1.0, 1.0]}


class FileTextureBase(object):
    """Main class that manages a single filepath texture node network
    """
    outputAttr = OUTPUT_ATTR

    def __init__(self, masterNode=None, masterAttribute="", textureName="", textureNode=None, genAttrDict=None,
                 scalar=False, autoCreate=True, create=False, ingest=False, message=True):
        """Either loads a file texture network or creates it.

        To Auto Create or Load an from an existing network use (from node.attribute)
            masterAttribute="color", masterNode=aZapiNode, textureName="aTextureName",
            autoCreate=True, create=False, ingest=False

        To create a new texture node network (from node.attribute):
            masterAttribute="color", masterNode=aZapiNode, textureName="aTextureName",
            autoCreate=False, create=True, ingest=False

        To ingest an existing node network (from node.attribute) use
            masterAttribute="color", masterNode=aZapiNode, textureName="aTextureName"
            autoCreate=False, create=False, ingest=True

        To load a texture network by from a known texture node as a string:
            textureName="aTextureName"
            autoCreate=False, create=False, ingest=True

        To load a texture network by from a known texture node as a zapi node:
            textureNode=aZapiNode,
            autoCreate=False, create=False, ingest=True

        :param masterNode: Optional zapi node master node that the texture network will be attached to  (optional)
        :type masterNode: :class:`zapi.DGNode`
        :param masterAttribute: optional name of the attr on the masterNode the texture network will be attached to
        :type masterAttribute: str
        :param textureName: The string name of the main texture node to load or create (optional)
        :type textureName: str
        :param textureNode: The zapi node of the main texture node to load (optional) only used while ingesting
        :type textureNode: :class:`zapi.DGNode`
        :param genAttrDict: Generic attribute dictionary with attribute values to set only if creating (optional)
        :type genAttrDict: dict(str)
        :param scalar: If True then connects to a scaler attribute (single) not a color (vector)
        :type scalar: bool
        :param create: If True then create a new skydome False will load the skydome into the instance
        :type create: bool
        :param autoCreate: If True then will create a new setup if one doesn't exist, ingests if one already exists.
        :type autoCreate: bool
        :param create: If True then will try to create a new texture node setup, autoCreate and ingest should be False
        :type create: bool
        :param ingest: If True will ingest an existing texture network.  autoCreate and create should be False
        :type ingest: bool
        :param message: Report a message to the user only if creating
        :type message: bool
        """
        super(FileTextureBase, self).__init__()
        self.masterNode = masterNode  # The node the texture network is connected to, can be "" if not connected
        self.masterAttr = masterAttribute  # The attribute the texture network is connected to, can be "" if not connected
        self.scalar = scalar  # is the texture a color (False) or a single scalar value (True)
        self.textureName = textureName
        self.initName(textureName)  # sets self.textureName to the incoming name or default
        self.textureNode = textureNode
        if textureNode:  # optional while ingesting if the texture node is known as a zapi object
            if textureNode.exists():
                self.nameVal = textureNode.fullPathName()
            else:
                if message:
                    output.displayWarning("textureNode, {} does not exist.".format(textureNode))
            return
        if autoCreate:  # If no existing texture network then create one
            if self.connectedAttr():
                self.ingest()  # Tries to load the current texture from node.attribute
                return
            self.create(genAttrDict=genAttrDict)  # creates the node network
            return
        elif ingest:
            self.ingest()  # tries to load the current texture from node.attribute
        elif create:
            self.create(genAttrDict=genAttrDict)  # creates the node network

    def initName(self, textureName):
        """Builds the name of the node network if given or will use the default name
        sets self.textureNameVal"""
        if textureName:
            self.nameVal = textureName
        else:
            self.nameVal = DEFAULT_VALUES[TEXTURE_NAME]

    def connectedAttr(self):
        """Returns the opposite attribute connected to the masterNode.masterAttribute

        :return oppositeAttr: the name of the connected attribute ie "outColor" will be empty string if none ""
        :rtype oppositeAttr: str
        """
        if not self.masterAttr or not self.masterNode:
            return ""
        objAttr = ".".join([self.masterNode.fullPathName(), self.masterAttr])
        oppositeAttrs = cmds.listConnections(objAttr, plugs=True)
        if not oppositeAttrs:
            return ""
        return oppositeAttrs[0]  # the incoming connected attribute

    def valid(self):
        """Checks if the main texture node exists, can be overridden for more checks

        :return valid:  True if the setup is valid
        :rtype valid: bool
        """
        if self.textureNode is None:
            return False
        elif not self.textureNode.exists():
            return False
        return True

    def exists(self):
        """Returns if the main texture node exists in the scene

        :return exists: True if the texture node exists False if not
        :rtype exists: bool
        """
        if not self.textureNode:
            return False
        return self.textureNode.exists()

    def ingest(self):
        """Should be overridden as will depend on the file texture type"""
        pass

    def create(self, genAttrDict=None):
        """Should be overridden and then call to self.setFromDictSafe(genAttrDict)"""

        # Set values
        if genAttrDict is None:  # no dictionary given so setup a network with default values
            genAttrDict = DEFAULT_VALUES
        self.setFromDict(genAttrDict)

    def delete(self):
        """Should be overridden as will depend on the file texture type"""
        pass

    def setFromDict(self, genAttrDict, apply=False):
        """Sets the normal network from the generic attribute (any renderer) dictionary.

        See DEFAULT_VALUES for an example of a genAttrDict

        :param genAttrDict: A dictionary of values that can be applied to the texture network see DEFAULT_VALUES
        :type genAttrDict: dict
        :param apply: Apply the values to the node network after setting the class variables
        :type apply:
        """
        self.nameVal = genAttrDict[TEXTURE_NAME]
        self.colorSpaceVal = genAttrDict[TEXTURE_COL_SPACE]
        self.pathVal = genAttrDict[TEXTURE_PATH]
        self.placeTypeVal = genAttrDict[PLACE_TYPE]
        self.repeatUVVal = genAttrDict[PLACE_REPEAT_UV]
        self.offsetUVVal = genAttrDict[PLACE_OFFSET_UV]
        self.rotateUVVal = genAttrDict[PLACE_ROTATE_UV]
        self.scale3dVal = genAttrDict[PLACE_3D_SCALE]
        if apply:
            self.applyCurrentSettings()

    def applyCurrentSettings(self):
        """Applies the current settings to the normal map's texture network"""
        self.setName(self.nameVal)
        self.setColorSpace(self.colorSpaceVal)
        self.setPath(self.pathVal)
        self.setPlaceType(self.placeTypeVal)
        self.setRepeatUV(self.repeatUVVal)
        self.setOffsetUV(self.offsetUVVal)
        self.setRotateUV(self.rotateUVVal)
        self.setScale3d(self.scale3dVal)

    def renderer(self):
        """Returns the current renderer as a string.

        Should be overridden.

        :return renderer: "Arnold", "Maya" "Redshift" etc.
        :rtype renderer: str
        """
        return shdmultconstants.UNKNOWN

    def textureType(self):
        """Returns the current texture type as a string.

        Should be overridden.

        :return textureType: The texture node type for example "file" (default maya fileTexture type)
        :rtype renderer: str
        """
        return ""

    # -------------------
    # Nodes
    # -------------------

    def _textureNodeStr(self):
        """Returns the string name of the main texture node with some error checks

        self.textureNode.fullPathName()

        :return textureName: The name of the main texture node.
        :rtype textureName: str
        """
        if not self.textureNode:
            return ""
        elif not self.textureNode.exists():
            return ""
        return self.textureNode.fullPathName()

    # -------------------
    # Setters and Getters
    # -------------------

    def setName(self, name):
        pass

    def name(self):
        pass

    def setPath(self, path):
        pass

    def path(self):
        pass

    def setColorSpace(self, colorSpace):
        # sRGB
        pass

    def colorSpace(self):
        pass

    def setPlaceType(self, placeType):
        pass

    def placeType(self):
        pass

    def setRepeatUV(self, repeatUV):
        pass

    def repeatUV(self):
        pass

    def setOffsetUV(self, offsetUV):
        pass

    def offsetUV(self):
        pass

    def setRotateUV(self, offsetUV):
        pass

    def rotateUV(self):
        pass

    def setScale3d(self, scale3d):
        pass

    def scale3d(self):
        pass