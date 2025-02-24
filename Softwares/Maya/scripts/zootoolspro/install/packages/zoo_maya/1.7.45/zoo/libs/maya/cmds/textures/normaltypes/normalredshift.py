"""This module is the class for Redshift normal and bump map creation with a RedshiftNormalMap node.

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
    from zoo.libs.maya.cmds.textures.normaltypes import normalredshift

    normInst = normalredshift.NormalRedshift(normalName="newNrml", normalType="bump", create=True)  # creates bump map network
    normInst.setPath(r"c:/path/texture.jpg")  # sets the texture path
    normInst.setStrength(2.0)  # sets the normal map strength to 2
    normInst.setNormalTypeSpace("normal", "tangent")

    # ingest shader to instance and connect ------------
    shadInst = shadermulti.shaderInstanceFromShader("shader_01_RS")  # Loads lambert1 as an instance
    normInst.connectOut(shadInst)  # connects the bump/normal map to the shader

"""
from zoo.libs.maya.cmds.textures.normaltypes import normalbase
from zoo.libs.maya.cmds.shaders import shdmultconstants

OUTPUT_ATTR = "out"  # RedshiftBumpMap out
OUTPUT_TEXTURE_ATTR = "outColor"  # Maya default 2d
TEXTURE_ATTR = "input"

RENDERER = shdmultconstants.REDSHIFT
NODE_TYPE = "RedshiftBumpMap"
STRENGTH_ATTR = "scale"
NORMAL_TYPE_ATTR = "inputType"
NORMAL_SPACE_ATTR = "inputType"


class NormalRedshift(normalbase.NormalBase):
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
        super(NormalRedshift, self).__init__(normalName=normalName,
                                         normalType=normalType,
                                         genAttrDict=genAttrDict,
                                         node=node,
                                         create=create,
                                         ingest=ingest,
                                         message=message)

