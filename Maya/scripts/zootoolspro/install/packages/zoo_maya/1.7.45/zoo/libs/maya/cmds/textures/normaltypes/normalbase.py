"""This module is the base class for normal and bump map creation.

This class is intended to be extended/overridden by each renderer type.  Provides base functionality.

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

A normal/bump object can be connected to a mixNormal object (built later)

For example two bump maps and a normal map can be used at once.

"""

from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.utils import output

from zoo.libs.maya.cmds.shaders import shdmultconstants
from zoo.libs.maya.cmds.objutils import nodemultibase
from zoo.libs.maya.cmds.textures.filetexturetypes import mayafiletexture

# Generic Keys for dictionaries ---------------
NORMAL_NAME = "normalName"
NORMAL_TYPE = "normalType"
NORMAL_SPACE = "normalSpace"
NORMAL_COL_SPACE = "normalColorSpace"
NORMAL_PATH = "normalFilePath"
NORMAL_STRENGTH = "normalStrength"

PLACE_TYPE = "placeType"  # For Triplanar, 3dPlacement or UVs
PLACE_REPEAT_UV = "placeRepeatUV"
PLACE_OFFSET_UV = "placeOffsetUV"
PLACE_ROTATE_UV = "placeRotateUV"
PLACE_3D_SCALE = "place3dScale"  # For Triplanar, 3dPlacement

DEFAULT_VALUES = {NORMAL_NAME: "normalBumpMap",
                  NORMAL_TYPE: "bump",
                  NORMAL_SPACE: "tangent",
                  NORMAL_COL_SPACE: "Raw",
                  NORMAL_PATH: "",
                  NORMAL_STRENGTH: 1.0,
                  PLACE_TYPE: "",
                  PLACE_REPEAT_UV: [1.0, 1.0],
                  PLACE_OFFSET_UV: [0.0, 0.0],
                  PLACE_ROTATE_UV: 0.0,
                  PLACE_3D_SCALE: [1.0, 1.0, 1.0]}

OUTPUT_ATTR = "outNormal"  # Maya default 2d
OUTPUT_TEXTURE_ATTR = "outAlpha"  # Maya default 2d

RENDERER = shdmultconstants.UNKNOWN
NODE_TYPE = ""
STRENGTH_ATTR = ""
NORMAL_TYPE_ATTR = ""
NORMAL_SPACE_ATTR = ""
TEXTURE_ATTR = ""


class NormalBase(nodemultibase.NodeMultiBase):
    """Main class that manages a single normal or bump map
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
        super(NormalBase, self).__init__()
        self.normalName = normalName  # Only part of the name for the node network, eg "nrml"
        self.bumpNode = None
        self.textureInst = None

        if not genAttrDict:  # no dictionary given so setup a network with default values
            genAttrDict = DEFAULT_VALUES
        self.setFromDict(genAttrDict, apply=False)

        # Ingest existing texture network ----------------------------------
        if node and ingest:  # Ingest the texture network
            pass
            return

        # Create a new texture network -----------------
        if create:
            if not self.normalName:  # set the name as none are given
                if normalType == "normal":
                    self.normalName = "nrml"
                else:
                    self.normalName = "bump"
            self.createNormalNetwork(normalType=normalType, message=message)
            self.typeVal = normalType  # needs to set for applyCurrentSettings
            self.applyCurrentSettings()

    def createNormalNetwork(self, normalType="normal", normalName="", message=True):
        """Creates a texture and place2d node controls via self.textureInst and adds a bump2d node for the normals.

        Can be overridden.  Expects a bump node with an input and a Maya file texture setup with a "file" texture node.

        Supports:
            - Maya
            - Redshift

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
        bumpNode = cmds.shadingNode(self.nodeType, asUtility=True,
                                    name="_".join([self.normalName, normalType, "node"]))
        self.node = zapi.nodeByName(bumpNode)
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

    def setBumpNormal(self, normalType, normalSpace=DEFAULT_VALUES[NORMAL_SPACE]):
        """Sets the node to be a normal or a bump map.  Can be overridden.

        Supports:
            - Maya
            - Redshift

        :param normalType: specify "normal" or "bump" map
        :type normalType: str
        :param normalSpace: For normal space define the normalSpace, "tangent", "object"
        :type normalSpace: str
        """
        if normalType == "normal":
            if normalSpace == "object":
                cmds.setAttr(".".join([self.node.fullPathName(), self.normalTypeAttr]), 2)  # object normal map
                return
            cmds.setAttr(".".join([self.node.fullPathName(), self.normalTypeAttr]), 1)  # tangent normal map
            return
        cmds.setAttr(".".join([self.node.fullPathName(), self.normalTypeAttr]), 0)  # bump map

    def delete(self):
        """Deletes the texture, placement and bump/normal nodes.  Can be overridden.

        Supports:
            - Maya
            - Redshift
        """
        if self.textureInst:
            self.textureInst.delete()  # deletes the texture and placement node
        super(NormalBase, self).delete()  # deletes the bump/normal node if exists

    def renderer(self):
        """Returns the current renderer as a string.

        :return renderer: "Arnold", "Maya" "Redshift" etc.
        :rtype renderer: str
        """
        return self.rendererStr

    def setFromDict(self, genAttrDict, apply=False):
        """Sets the normal network from the generic attribute dictionary.

        :param genAttrDict:
        :type genAttrDict:
        :param apply:
        :type apply:
        """
        self.nameVal = genAttrDict[NORMAL_NAME]
        self.typeVal = genAttrDict[NORMAL_TYPE]
        self.spaceVal = genAttrDict[NORMAL_SPACE]
        self.colorSpaceVal = genAttrDict[NORMAL_COL_SPACE]
        self.pathVal = genAttrDict[NORMAL_PATH]
        self.strengthVal = genAttrDict[NORMAL_STRENGTH]
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
        self.setNormalTypeSpace(self.typeVal, self.spaceVal)
        self.setColorSpace(self.colorSpaceVal)
        self.setPath(self.pathVal)
        self.setStrength(self.strengthVal)
        self.setPlaceType(self.placeTypeVal)
        self.setRepeatUV(self.repeatUVVal)
        self.setOffsetUV(self.offsetUVVal)
        self.setRotateUV(self.rotateUVVal)
        self.setScale3d(self.scale3dVal)

    def outAttr(self):
        """The name of the out attribute that plugs into a shader or layered texture

        :return outputNormalAttr: The name of the out attribute that plugs into a shader or layered texture
        :rtype outputNormalAttr: str
        """
        return self.outputNormalAttr

    # -------------------
    # Connect / Disconnect
    # -------------------

    def connectOut(self, inInst, inType="normal", outType="normal"):
        if outType != "vector" and outType != "normal" and outType != "bump":
            return
        cmds.connectAttr(".".join([self.name(), self.outputNormalAttr]),
                         inInst.inNodeAttr(inType=inType))

    def disconnectOut(self, outType="vector"):
        pass

    # -------------------
    # Setters and Getters Bump/Normal
    # -------------------

    def setStrength(self, value):
        """Sets the multiplier strength of the normal effect/depth. Can be overridden.

        Supports:
            - Maya
            - Redshift

        :param value: The value of the strength depth effect
        :type value: float
        """
        self._setAttrScalar(self.strengthAttr, value)

    def strength(self):
        """Gets the multiplier strength of the normal effect/depth. Can be overridden.

        Supports:
            - Maya
            - Redshift

        :return strength: The value of the strength depth effect
        :rtype strength: float
        """
        return self._getAttrScalar(self.strengthAttr)

    def setNormalTypeSpace(self, normalType="normal", normalSpace="tangent"):
        """Sets normalType (normal/bump) and normalSpace (tangent/object). Can be overridden.

        If bump the normalSpace is ignored.

        Supports:
            - Maya
            - Redshift

        :param normalType: Either "normal" or "bump" depending which mode is desired
        :type normalType: str
        :param normalSpace: The space of the normal effect, ignored if bump. "tangent" or "object"
        :type normalSpace: str
        """
        if normalType == "bump":
            self._setAttrScalar(self.normalTypeAttr, 0)
            return
        if normalSpace == "tangent":
            self._setAttrScalar(self.normalTypeAttr, 1)
        else:
            self._setAttrScalar(self.normalTypeAttr, 2)

    def normalTypeSpace(self):
        """Returns the multiplier strength of the normal effect/depth. Can be overridden.

        Supports:
            - Maya
            - Redshift

        :return: normalType (bump or normal) and normalSpace (tangent or object)
        :rtype: tuple
        """
        i = self._getAttrScalar(self.normalTypeAttr)
        if i == 0:
            return "bump", "tangent"
        elif i == 1:
            return "normal", "tangent"
        elif i == 2:
            return "normal", "object"
        return None, None

    # -------------------
    # Setters and Getters Texture
    # -------------------

    def setTextureName(self, name):
        if not self.textureInst:
            return
        self.textureInst.setName(name)

    def textureName(self):
        if not self.textureInst:
            return None
        return self.textureInst.name()

    def setColorSpace(self, colorSpace):
        if not self.textureInst:
            return
        self.textureInst.setColorSpace(colorSpace)

    def colorSpace(self):
        if not self.textureInst:
            return None
        self.textureInst.colorSpace()

    def setPath(self, path):
        if not self.textureInst:
            return
        self.textureInst.setPath(path)

    def path(self):
        if not self.textureInst:
            return None
        self.textureInst.path()

    def setPlaceType(self, placeType):
        if not self.textureInst:
            return
        self.textureInst.setPlaceType(placeType)

    def placeType(self):
        if not self.textureInst:
            return None
        self.textureInst.placeType()

    def setRepeatUV(self, repeatUV):
        if not self.textureInst:
            return
        self.textureInst.setRepeatUV(repeatUV)

    def repeatUV(self):
        if not self.textureInst:
            return None
        self.textureInst.repeatUV()

    def setOffsetUV(self, offsetUV):
        if not self.textureInst:
            return
        self.textureInst.setOffsetUV(offsetUV)

    def offsetUV(self):
        if not self.textureInst:
            return None
        self.textureInst.offsetUV()

    def setRotateUV(self, offsetUV):
        if not self.textureInst:
            return
        self.textureInst.setOffsetUV(offsetUV)

    def rotateUV(self):
        if not self.textureInst:
            return None
        self.textureInst.rotateUV()

    def setScale3d(self, scale3d):
        if not self.textureInst:
            return
        self.textureInst.setScale3d(scale3d)

    def scale3d(self):
        if not self.textureInst:
            return None
        self.textureInst.scale3d()

    def setUdim(self, style="mudbox"):
        if not self.textureInst:
            return
        self.textureInst.setUdim(style)

    def udim(self):
        if not self.textureInst:
            return None
        self.textureInst.scale3d()

