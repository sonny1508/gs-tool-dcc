"""This module is the class for Renderman normal and bump map creation with a PxrNormalMap/PxrBump node.

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
    from zoo.libs.maya.cmds.textures.normaltypes import normalrenderman

    normInst = normalrenderman.NormalRenderman(normalName="newNrml", normalType="bump", create=True)  # creates bump map network
    normInst.setPath(r"c:/path/texture.jpg")  # sets the texture path
    normInst.setStrength(2.0)  # sets the normal map strength to 2
    normInst.setNormalTypeSpace("normal", "tangent")

    # ingest shader to instance and connect ------------
    shadInst = shadermulti.shaderInstanceFromShader("shader_01_RS")  # Loads lambert1 as an instance
    normInst.connectOut(shadInst)  # connects the bump/normal map to the shader

"""
from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.utils import output

from zoo.libs.maya.cmds.textures.normaltypes import normalbase
from zoo.libs.maya.cmds.shaders import shdmultconstants
from zoo.libs.maya.cmds.textures.filetexturetypes import mayafiletexture

from zoo.libs.maya.cmds.textures.normaltypes.normalbase import DEFAULT_VALUES, NORMAL_SPACE

OUTPUT_ATTR = "resultN"  # Renderman out
OUTPUT_TEXTURE_ATTR = "outColor"  # Maya file color out
OUTPUT_TEXTURE_ATTR_BUMP = "outAlpha"  # Maya file bump out
TEXTURE_ATTR = "inputRGB"  # Renderman normal input
TEXTURE_ATTR_BUMP = "inputBump"  # Renderman bump input

RENDERER = shdmultconstants.REDSHIFT
NODE_TYPE = "PxrNormalMap"
BUMP_NODE_TYPE = "PxrBump"
STRENGTH_ATTR = "bumpScale"
BUMP_STRENGTH_ATTR = "scale"  # bump strength
NORMAL_TYPE_ATTR = ""  # Renderman has two node setups, one for bump and the other for normal maps.
NORMAL_SPACE_ATTR = ""  # Renderman is tangent only


class NormalRenderman(normalbase.NormalBase):
    """Main class that manages a single normal or bump map for Maya
    """
    outputNormalAttr = OUTPUT_ATTR
    outputTextureAttr = OUTPUT_TEXTURE_ATTR

    nodeType = NODE_TYPE
    strengthAttr = STRENGTH_ATTR
    normalTypeAttr = NORMAL_TYPE_ATTR
    normalSpaceAttr = NORMAL_SPACE_ATTR
    texture_attr = TEXTURE_ATTR
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
        super(NormalRenderman, self).__init__(normalName=normalName,
                                         normalType=normalType,
                                         genAttrDict=genAttrDict,
                                         node=node,
                                         create=create,
                                         ingest=ingest,
                                         message=message)

    def createNormalNetwork(self, normalType="normal", normalName="", message=True):
        """Creates a texture and place2d node controls via self.textureInst and adds a Renderman bump/normal map node.

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
        pass

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
        pass

    def normalTypeSpace(self):
        """Returns the multiplier strength of the normal effect/depth.

        :return: normalType (bump or normal) and normalSpace (tangent or object)
        :rtype: tuple
        """
        pass