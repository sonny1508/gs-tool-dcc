"""This module is the class for Arnold normal and bump map creation.

This class is a subclass of normalbase and nodemultibase and inherits functionality where applicable.

The normalbase class handles all the textureInstance functions, such as setPath and colorSpace

A single normal or bump map will have these properties:

- NormalBump type (normal or bump map)
- NormalSpace (tangent or object etc)
- Texture file path
- Strength (strength of the bump)
- Out Connection
- Color space
- 2d texture properties

    - repeat UV
    - Offset UV
    - Rotate UV
    - Scale 3d (triplanar and 3d placement)

A normal/bump object may later be connected to a mixer node (built later)
For example two bump maps and a normal map can be used at once.

Example use:

.. code-block:: python
    from zoo.libs.maya.cmds.shaders import shadermulti
    from zoo.libs.maya.cmds.textures.normaltypes import normalarnold

    normInst = normalarnold.NormalArnold(normalName="newNrml", normalType="normal", create=True)  # creates bump map network
    normInst.setPath(r"c:/path/texture.jpg")  # sets the texture path
    normInst.setStrength(2.0)  # sets the normal map strength to 2
    normInst.setNormalTypeSpace("normal", "tangent")  # do not use for bump maps

    # ingest shader to instance and connect ------------
    shadInst = shadermulti.shaderInstanceFromShader("shader_01_ARN")  # Loads existing aiStandardSurface as an instance
    normInst.connectOut(shadInst)  # connects the bump map to the shader

"""
from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.utils import output

from zoo.libs.maya.cmds.textures.normaltypes import normalbase
from zoo.libs.maya.cmds.shaders import shdmultconstants
from zoo.libs.maya.cmds.textures.filetexturetypes import mayafiletexture

from zoo.libs.maya.cmds.textures.normaltypes.normalbase import DEFAULT_VALUES, NORMAL_SPACE

OUTPUT_ATTR = "outValue"  # Arnold bump and normal nodes are the same out
OUTPUT_TEXTURE_ATTR = "outColor"  # normal 2d texture out
OUTPUT_TEXTURE_ATTR_BUMP = "outAlpha"  # bump 2d texture out
TEXTURE_ATTR = "input"
TEXTURE_ATTR_BUMP = "bumpMap"

RENDERER = shdmultconstants.ARNOLD
NODE_TYPE = "aiNormalMap"
BUMP_NODE_TYPE = "aiBump2d"
STRENGTH_ATTR = "strength"  # and if bump use BUMP_STRENGTH_ATTR
BUMP_STRENGTH_ATTR = "bumpHeight"  # bump strength
NORMAL_TYPE_ATTR = ""  # Arnold has two node setups, one for bump and the other for normal maps.
NORMAL_SPACE_ATTR = "tangentSpace"


class NormalArnold(normalbase.NormalBase):
    """Main class that manages a single normal or bump map for Maya
    """
    # Arnold self.texture_attr & self.outputTextureAttr are set depending on the node type in the __init__
    outputNormalAttr = OUTPUT_ATTR

    nodeType = NODE_TYPE
    strengthAttr = STRENGTH_ATTR
    normalTypeAttr = NORMAL_TYPE_ATTR
    normalSpaceAttr = NORMAL_SPACE_ATTR
    rendererStr = RENDERER

    def __init__(self, normalName="", normalType="normal", genAttrDict=None, node=None, create=False, ingest=False,
                 message=True):
        """
        """
        self.normalType = normalType
        if normalType == "normal":
            self.outputTextureAttr = OUTPUT_TEXTURE_ATTR
            self.texture_attr = TEXTURE_ATTR
        else:  # If "bump"
            self.outputTextureAttr = OUTPUT_TEXTURE_ATTR_BUMP
            self.texture_attr = TEXTURE_ATTR_BUMP
        super(NormalArnold, self).__init__(normalName=normalName,
                                           normalType=normalType,
                                           genAttrDict=genAttrDict,
                                           node=node,
                                           create=create,
                                           ingest=ingest,
                                           message=message)

    def createNormalNetwork(self, normalType="normal", normalName="", message=True):
        """Creates a texture and place2d node controls via self.textureInst and adds a Arnold bump/normal map node.

        :param normalType: "bump" or "normal"  the mode of the normal map.
        :type normalType: str
        :param normalName: Part of the name that will be named on all nodes, "nrml" by default
        :type normalName: str
        :param message: Report a message to the user?
        :type message: True
        :return: texture instance object and the bump2d node as a zapi object
        :rtype: tuple
        """
        if normalName:  # if empty use the current name "nrml"
            self.normalName = normalName

        if self.normalType == "normal":
            self._createNormal()  # creates self.node
        else:
            self._createBump()  # creates self.node

        self.textureInst = mayafiletexture.MayaFileTexture(masterAttribute="",
                                                           masterNode=None,
                                                           textureName="_".join([self.normalName, normalType]),
                                                           create=True,
                                                           scalar=True)
        self.setBumpNormal(normalType)
        cmds.connectAttr(".".join([self.textureInst.name(), self.outputTextureAttr]),
                         ".".join([self.name(), self.texture_attr]))
        if message:
            output.displayInfo("Success: {} network created `{}`".format(normalType, self.normalName))
        return self.textureInst, self.node

    def _createNormal(self):
        """Creates a aiNormalMap node"""
        node = cmds.shadingNode(self.nodeType, asUtility=True,
                                name="_".join([self.normalName, "normal", "node"]))
        self.node = zapi.nodeByName(node)

    def _createBump(self):
        """Creates a aiBump2d node"""
        node = cmds.shadingNode(BUMP_NODE_TYPE, asUtility=True,
                                name="_".join([self.normalName, "bump", "node"]))
        self.node = zapi.nodeByName(node)

    def setBumpNormal(self, normalType, normalSpace=DEFAULT_VALUES[NORMAL_SPACE]):
        """Sets the node to be a normal or a bump map.

        :param normalType: specify "normal" or "bump" map
        :type normalType: str
        :param normalSpace: For normal space define the normalSpace, "tangent", "object"
        :type normalSpace: str
        """
        # TODO: if wrong type will need to rebuild the bump/normal node to the opposite type
        if self.normalType != "normal":  # is bump so bail
            return
        if normalSpace == "object":
            cmds.setAttr(".".join([self.node.fullPathName(), self.normalSpaceAttr]), 0)  # object normal map
            return
        cmds.setAttr(".".join([self.node.fullPathName(), self.normalSpaceAttr]), 1)  # tangent normal map

    # -------------------
    # Setters and Getters Bump/Normal
    # -------------------

    def setStrength(self, value):
        """Sets the multiplier strength of the normal effect/depth.

        :param value: The value of the strength depth effect
        :type value: float
        """
        if self.normalType == "normal":
            self._setAttrScalar(self.strengthAttr, value)
        else:  # for bump node
            self._setAttrScalar(BUMP_STRENGTH_ATTR, value)

    def strength(self):
        """Gets the multiplier strength of the normal effect/depth.

        :return strength: The value of the strength depth effect
        :rtype strength: float
        """
        if self.normalType == "normal":
            return self._getAttrScalar(self.strengthAttr)
        else:  # for bump node
            return self._getAttrScalar(BUMP_STRENGTH_ATTR)

    def setNormalTypeSpace(self, normalType="normal", normalSpace="tangent"):
        """Sets normalType (normal/bump) and normalSpace (tangent/object).

        If bump the normalSpace is ignored.

        :param normalType: Either "normal" or "bump" depending which mode is desired
        :type normalType: str
        :param normalSpace: The space of the normal effect, ignored if bump. "tangent" or "object"
        :type normalSpace: str
        """
        if normalType != "normal":
            return
        if normalSpace == "tangent":
            self._setAttrScalar(self.normalSpaceAttr, 1)
        else:
            self._setAttrScalar(self.normalSpaceAttr, 0)

    def normalTypeSpace(self):
        """Returns the multiplier strength of the normal effect/depth.

        :return: normalType (bump or normal) and normalSpace (tangent or object)
        :rtype: tuple
        """
        if self.normalType != "normal":
            return "bump", "tangent"
        i = self._getAttrScalar(self.normalTypeAttr)
        if i == 0:
            return "normal", "object"
        elif i == 1:
            return "normal", "tangent"

