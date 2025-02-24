"""This module is the class for the default Maya texture "file" and "place2dTexture" nodes.

Color grading may be added later.

A texture node network can be modified with these values:

- Texture file path
- Color Space
- Output Connection
- 2d texture properties
- repeat UV
- Offset UV
- Rotate UV
- Scale 3d (triplanar and 3d placement)

A texture can be stacked into a layer texture and mixed. (later)

Example use, building a texture on a shader "lambert", attribute "color"

.. code-block:: python

    from zoo.libs.maya.cmds.textures.filetexturetypes import mayafiletexture
    from zoo.libs.maya import zapi
    shaderNode = zapi.nodeByName("lambert2")
    # autoload or create a texture network at "lambert2.color"
    txtrInst = mayafiletexture.MayaFileTexture(masterAttribute="color", masterNode=shaderNode,
                                                textureName="colorTexture",
                                                autoCreate=True, create=False, ingest=False)
    txtrInst.setName("newColorTexture")  # sets a new name of the texture network
    txtrInst.setPath("c:/aPath/toMy/texture.jpg")  # set the file texture path
    txtrInst.setColorSpace("sRGB")  # sets the incoming texture space
    txtrInst.setRepeatUV((2.0, 2.0)) # sets the repeating texture U and V values.
    txtrInst.rotateUV(45.0)  # rotates the texture by 45 degrees

"""

from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.utils import output
from zoo.libs.maya.cmds.textures import textures
from zoo.libs.maya.cmds.textures.filetexturetypes import filetexturebase as base
from zoo.libs.maya.cmds.shaders import shdmultconstants

INPUT_ATTR = "color"
OUTPUT_ATTR = "outColor"
OUTPUT_SCALAR_ATTR = "outAlpha"
TEXTURE_NODE_TYPE = "file"
RENDERER = shdmultconstants.MAYA


class MayaFileTexture(base.FileTextureBase):
    """Main class that manages a single filepath texture node network
    """
    inputAttr = INPUT_ATTR
    outputAttr = OUTPUT_ATTR
    outputScalarAttr = OUTPUT_SCALAR_ATTR
    textureNodeType = TEXTURE_NODE_TYPE

    def __init__(self, masterNode=None, masterAttribute="", textureName="", textureNode=None, genAttrDict=None,
                 scalar=False, autoCreate=True, create=False, ingest=False, message=True):
        """Either loads a file texture network or creates it.

        To Auto Create or Load an from an existing network use (from node.attribute)
            attribute="color", masterNode=aZapiNode, textureName="aTextureName",
            autoCreate=True, create=False, ingest=False

        To create a new texture node network (from node.attribute):
            attribute="color", masterNode=aZapiNode, textureName="aTextureName",
            autoCreate=False, create=True, ingest=False

        To ingest an existing node network (from node.attribute) use
            attribute="color", masterNode=aZapiNode, textureName="aTextureName"
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
        self.place2dNode = None
        super(MayaFileTexture, self).__init__(masterNode=masterNode,
                                              masterAttribute=masterAttribute,
                                              textureName=textureName,
                                              textureNode=textureNode,
                                              genAttrDict=genAttrDict,
                                              scalar=scalar,
                                              autoCreate=autoCreate,
                                              create=create,
                                              ingest=ingest,
                                              message=message)
        if self.scalar:
            cmds.setAttr("{}.alphaIsLuminance".format(self._textureNodeStr()), True)

    def valid(self):
        """Checks if the two texture node exist:

            self.textureNode
            self.place2dNode

        :return valid:  True if the setup is valid
        :rtype valid: bool
        """
        if self.textureNode is None or self.place2dNode is None:
            return False
        elif not self.textureNode.exists() or not self.place2dNode.exists():
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
        """Tries to ingest the file texture network of two nodes.

        This method will check in order:

            If self.masterNode and self.masterAttr are given: Will try to ingest from their connection
            If self.textureNode is given as a zapi node:  Tries to ingest the place2dNode too
            If self.textureName is given as a string name: Ingests self.textureNode and self.place2dNode

        If successful will register two zapi nodes:

            self.textureNode
            self.place2dNode

        :return success: Returns True if the file texture network was successfully ingested.
        :rtype success: bool
        """
        # Ingest via the connection from a masterNode.masterAttr ----------------------------
        if self.masterNode and self.masterAttr:
            if not self.masterNode.exists():
                output.displayWarning("The texture network could not be ingested.  Not found in scene.")
                return False
            self.textureNode = self._findConnection(self.masterNode, INPUT_ATTR, "file", OUTPUT_ATTR)
            if self.textureNode:
                self._ingestPlace2dNode()  # sets self.place2dNode

        # Zapi node given so ingest it by registering the self.place2dNode ------------------
        elif self.textureNode:
            self._ingestPlace2dNode()  # sets self.place2dNode

        # String texture name give so ingest it by registering the self.place2dNode ------------------
        elif self.textureName:
            if cmds.objExists(self.textureName):
                if cmds.objectType(self.textureName) != "file":
                    output.displayWarning("The texture {} is not a `file` texture node.".format(self.textureName))
                    return False
                self.textureNode = zapi.nodeByName(self.textureName)
                self._ingestPlace2dNode()  # sets self.place2dNode

        else:
            output.displayWarning("The texture network could not be ingested.  Not found.")
            return False
        return self.valid()  # checks both self.textureNode and self.place2dNode are valid nodes in the scene

    def _ingestPlace2dNode(self):
        """Finds the place2dTexture node connected to self.place2dNode (zapi node)
        """
        self.place2dNode = self._findConnection(self.textureNode, "coverage", "place2dTexture", "coverage")

    def _findConnection(self, destinationNode, destinationAttr, sourceNodeType, sourceAttr):
        """Returns the source node as a Zapi object, searching from the given criteria

        :param destinationNode: The node to search from
        :type destinationNode: :class:`zapi.DGNode`
        :param destinationAttr: The attribute to search from on the dstinationNode
        :type destinationAttr: str
        :param sourceNodeType: The node type expected to find
        :type sourceNodeType: str
        :param sourceAttr: The name of the source attribute expected at the source
        :type sourceAttr: str

        :return sourceNode: The zapi node found as the source that meets criteria, None if not found.
        :rtype sourceNode: :class:`zapi.DGNode`
        """
        sourceConnections = cmds.listConnections(".".join([destinationNode.fullPathName(), destinationAttr]),
                                                 destination=False,
                                                 source=True,
                                                 plugs=True)
        # sourceConnections should be ['sourceNode.sourceAttr']
        if not sourceConnections:
            return None
        elif ".{}".format(sourceAttr) not in sourceConnections[0]:
            return None
        nodeName = sourceConnections[0].split(".")[0]
        if cmds.objectType(nodeName) != sourceNodeType:
            return None
        # checks passed return the node
        return zapi.nodeByName(nodeName)

    def create(self, genAttrDict=None):
        """Creates and potentially connects the texture node network and assigns the dict or default values if None:
            - self.textureNode = Main texture node "file" type
            - self.place2dNode = Place texture node "place2dTexture" type

        Connects the texture to:
            - self.masterNode (zapi node)
            - self.masterAttribute (str)

        :param genAttrDict: A dictionary of values that can be applied to the texture network see base.DEFAULT_VALUES
        :type genAttrDict: dict
        """
        if genAttrDict is None:  # no dictionary given so setup a network with default values
            genAttrDict = base.DEFAULT_VALUES
        fileNode, place2dTextureNode = textures.createFileTexture(name=self.textureName,
                                                                  colorSpace=genAttrDict[base.TEXTURE_COL_SPACE],
                                                                  imagePath=genAttrDict[base.TEXTURE_PATH],
                                                                  ignoreColorSpace=True)
        self.textureNode = zapi.nodeByName(fileNode)
        self.place2dNode = zapi.nodeByName(place2dTextureNode)
        if self.masterNode and self.masterAttr:
            self._connectTextureNetwork()

    def _connectTextureNetwork(self):
        """Connects the texture node network to the masterNode and master attribute

        :return:
        :rtype:
        """
        outputAttr = self.outputAttr
        textureName = self._textureNodeStr()
        place2dName = self._place2dNodeStr()
        # todo can safely get self.masterNode.fullPathName() might be None may not exist etc.
        if place2dName and textureName:
            if self.scalar: # is color three values
                outputAttr = self.outputScalarAttr
            cmds.connectAttr(".".join([textureName, outputAttr]),
                             ".".join([self.masterNode.fullPathName(), self.masterAttr]))

    def _disconnectTextureNetwork(self):
        pass

    def delete(self):
        """Deletes the entire texture network, deletes all nodes"""
        place2dName = self._place2dNodeStr()
        if place2dName:
            cmds.delete(place2dName)
        textureName = self._textureNodeStr()
        if textureName:
            cmds.delete(textureName)

    def renderer(self):
        """Returns the current renderer as a string.

        Should be overridden.

        :return renderer: "Arnold", "Maya" "Redshift" etc.
        :rtype renderer: str
        """
        return RENDERER

    # -------------------
    # Extra Nodes
    # -------------------

    def _place2dNodeStr(self):
        """Returns the place2dTexture node as a string, or "" if it doesn't exist

        :return place2dNode: The name of the place2dTexture node or "" if it doesn't exist
        :rtype place2dNode: str
        """
        if self.place2dNode is None:
            return ""
        elif not self.place2dNode.exists():
            return ""
        return self.place2dNode.fullPathName()

    # -------------------
    # Setters and Getters
    # -------------------

    def setName(self, name):
        """Renames the node network to the new name.

        :param name: The new name of the texture network
        :type name: str
        :return newName: New name of the texture node
        :rtype newName: str
        :return newPlace2dName: New name of the texture node
        :rtype newPlace2dName: str
        """
        textureName = self._textureNodeStr()
        place2dName = self._place2dNodeStr()
        if not textureName or not place2dName:
            output.displayWarning("Could not set name as the network is broken or does not exist")
            return
        newName = cmds.rename(textureName, name)
        newPlace2dName = cmds.rename(place2dName, "{}_plc2d".format(name))
        return newName, newPlace2dName

    def rename(self, name):
        """Documentation see self.setName()"""
        return self.setName(name)

    def name(self):
        """Returns the name of the main texture node or "" if it doesn't exist.

        :return name:  The name of the main texture node, or "" if it doesn't exist
        :rtype name: str
        """
        return self._textureNodeStr()

    def setPath(self, path):
        """Sets the path of the texture image

        :param path: The path on disk to the texture image
        :type path: str
        """
        cmds.setAttr("{}.fileTextureName".format(self._textureNodeStr()), path, type="string")

    def path(self):
        """Gets the path on disk of the texture image

        :return path: The path on disk to the texture image can be "" if nothing set
        :rtype path: str
        """
        return cmds.getAttr("{}.fileTextureName".format(self._textureNodeStr()))

    def setColorSpace(self, colorSpace):
        """Sets the color space of the main texture node as a string, must match Maya's color space strings.

        eg "sRGB"

        :param colorSpace: The color space of the node, must match Maya's color space strings.
        :type colorSpace: str
        """
        cmds.setAttr("{}.colorSpace".format(self._textureNodeStr()), colorSpace, type='string')

    def colorSpace(self):
        """Gets the color space of the main texture node as a string

        eg "sRGB"

        :return colorSpace: The color space of the main texture node as a string
        :rtype colorSpace: str
        """
        return cmds.getAttr("{}.colorSpace".format(self._textureNodeStr()))

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
