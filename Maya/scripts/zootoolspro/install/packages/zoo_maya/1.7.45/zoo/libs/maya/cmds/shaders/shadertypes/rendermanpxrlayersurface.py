"""This module creates and manages a Renderman pxr layer shader.

This class is a subclass of shaderbase and inherits all functionality where applicable.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.shaders.shadertypes import rendermanpxrlayersurface
    shadInst = rendermanpxrlayersurface.PxrLayerMetalness("shaderName", create=True)  # creates a new shader

    shadInst.setDiffuse([0.0, 0.0, 1.0])  # sets diffuse color to blue
    shadInst.setDiffuseWeight(1.0)

    shadInst.setMetalness(1.0)  # sets metalness to be on

    shadInst.setSpecWeight(1.0)
    shadInst.setSpecColor([1, 1, 1])
    shadInst.setSpecRoughness(1.0)
    shadInst.setSpecIOR(1.3)

    shadInst.setCoatWeight(0.0)
    shadInst.setCoatIOR(1.5)
    shadInst.setCoatRoughness(.1)
    shadInst.setCoatColor([1, 1, 1])

    shadInst2 = rendermanpxrlayersurface.PxrLayerMetalness("rocketShader", ingest=True)  # Loads existing "rocketShader" as instance

    shadInst2.assignSelected()

    shadInst2.setShaderName("newNameY")
    print(shadInst.shaderName())

"""

import maya.cmds as cmds

from zoo.libs.maya import zapi

from zoo.libs.maya.cmds.shaders import rendermanshaders, shdmultconstants
from zoo.libs.maya.cmds.shaders.shadertypes import shaderbase


class PxrLayerMetalness(shaderbase.ShaderBase):
    """Manages the creation and set/get attribute values for the PXR layer shader supporting a hacked metalness input
    """
    diffuseWeightAttr = ""
    diffuseColorAttr = ""
    diffuseRoughnessAttr = ""
    metalnessAttr = ""
    specularWeightAttr = ""
    specularColorAttr = ""
    specularRoughnessAttr = ""
    specularIorAttr = ""
    coatWeightAttr = ""
    coatcolorAttr = ""
    coatRoughnessAttr = ""
    coatIorAttr = ""
    emissionAttr = ""
    emissionWeightAttr = ""

    def __init__(self, shaderName="", node=None, genAttrDict=None, create=False, ingest=False, suffixName=False,
                 message=True):
        """Either loads a shader or creates it.

        This shader has two components:

        - Layer1 is the first layer (technically base layer) and is a regular shader usually with IOR of 1.5
        - Layer2 is the second layer (technically layer 1) and is a metal shader

        The mask of the two layers is the metalness attribute.


        To create a new shader:
            create=True and node=False to create a new shader

        To load a shader by zapiNode name
            node="zapiNode" (should be a shader node) and ingest=True

        To load a shader by string:
            shaderName="shaderName" and ingest=True

        :param shaderName: The name of the shader to load or create
        :type shaderName: str
        :param node: A zapi node as an object
        :type node: zoo.libs.maya.zapi.base.DGNode
        :param genAttrDict: The generic attribute dictionary with attribute values to set only if creating
        :type genAttrDict: dict(str)
        :param create: If True then create a new shader False will load the shader and nodes in the instance
        :type create: bool
        :param ingest: If True then shaders should be passed in as a string name (shaderName) or zapi node (node).
        :type ingest: bool
        :param message: Report a message to the user only if creating
        :type message: bool
        """
        super(PxrLayerMetalness, self).__init__(shader=shaderName,
                                                node=node,
                                                genAttrDict=genAttrDict,
                                                create=create,
                                                ingest=ingest,
                                                suffixName=suffixName,
                                                message=message)

    def knownShader(self):
        """Returns True as this shader is supported by Zoo Tools"""
        return True

    def renderer(self):
        """Returns the current renderer as a string"""
        return shdmultconstants.RENDERMAN

    def _allNodes(self, shader):
        """Gets all the nodes from the shader name and sets them as class variables.

        Overridden method.

        :param shader: The name of the shader
        :type shader: str
        """
        # todo switch to zapi code on the connections
        self.node = zapi.nodeByName(shader)
        layerMixer = cmds.listConnections('{}.inputMaterial'.format(shader), source=True)[0]
        self.layerMixerNode = zapi.nodeByName(layerMixer)
        layer1 = cmds.listConnections('{}.baselayer'.format(self.layerMixerNode), source=True)[0]
        self.layer1Node = zapi.nodeByName(layer1)
        layer2 = cmds.listConnections('{}.layer1'.format(self.layerMixerNode), source=True)[0]
        self.layer2Node = zapi.nodeByName(layer2)

    # -------------------
    # Create Assign Delete
    # -------------------

    def createShader(self, shaderName="shader_PXR", genAttrDict=None, message=True):
        """Creates a pxrLayeredShader node network and loads the nodes as class variables

        Overridden method.

        :param shaderName: The name of the shader
        :type shaderName: str
        :param genAttrDict: The generic attribute dictionary with attribute values to set (optional)
        :type genAttrDict: dict(str)
        :param message: Report a message to the user when the shader is created
        :type message: bool
        """
        shader, \
        layerMixer, \
        layer1, \
        layer2 = rendermanshaders.createPxrLayerSurface(shaderName=shaderName, message=message)
        self.shaderNode = zapi.nodeByName(shader)
        self.layerMixerNode = zapi.nodeByName(layerMixer)
        self.layer1Node = zapi.nodeByName(layer1)
        self.layer2Node = zapi.nodeByName(layer2)
        cmds.setAttr("{}.specularFresnelMode".format(shader), 1)  # physical primary spec
        cmds.setAttr("{}.roughSpecularFresnelMode".format(shader), 1)  # physical rough spec
        cmds.setAttr("{}.clearcoatFresnelMode".format(shader), 2)  # physical clearcoat
        cmds.setAttr("{}.specularIor".format(layer2), 12.0, 12.0, 12.0, type="double3")  # layer 2 IOR metal
        if genAttrDict:
            self.setFromDict(genAttrDict, apply=True)
            return
        self.applyCurrentSettings()

    def deleteShader(self):
        """Deletes the shader and all of it's nodes

        Overridden method.
        """
        cmds.delete([self.shaderNode.fullPathName(),
                     self.layerMixerNode.fullPathName(),
                     self.layer1Node.fullPathName(),
                     self.layer2Node.fullPathName()])
        self.shaderNode = None
        self.layerMixerNode = None
        self.layer1Node = None
        self.layer2Node = None

    def assign(self, objFaceList):
        """Assign the shader to a list of geometry or components.

        :param objFaceList: A list of objects or faces or both
        :type objFaceList: list(str)
        """
        super(PxrLayerMetalness, self).assign()

    def assignSelected(self):
        """Assign the shader to selected geo"""
        super(PxrLayerMetalness, self).assignSelected()

    def setFromDict(self, genAttrDict, apply=True, noneIsDefault=True):
        """Sets the shader with attribute values from a generic shader dictionary, keys are from shdmultconstants

        :param genAttrDict: The generic attribute dictionary with attribute values to set (optional)
        :type genAttrDict: dict(str)
        """
        super(PxrLayerMetalness, self).setFromDict(genAttrDict, apply=apply)

    def shaderValues(self):
        """Returns values of the shader attribute in a generic shader dictionary, keys are from shdmultconstants

        :return genAttrDict: A dictionary of generic shader keys with values as per shdmultconstants
        :rtype genAttrDict: dict(str)
        """
        return super(PxrLayerMetalness, self).shaderValues()

    def setShaderName(self, newName):
        """Renames the shader and all nodes in the network

        Overridden method.

        :param newName: The new name of the shader
        :type newName: str
        """
        cmds.rename(self.shaderNode.fullPathName(), newName)
        shader = self.shaderNode.fullPathName()
        cmds.rename(self.layerMixerNode.fullPathName(), "{}_mix".format(shader))
        cmds.rename(self.layer1Node.fullPathName(), "{}_lyr1".format(shader))
        cmds.rename(self.layer2Node.fullPathName(), "{}_lyr2".format(shader))
        return self.shaderNode.fullPathName()

    def shaderName(self):
        """Returns the shader's name as a string

        :return shaderName: The shader's name
        :rtype shaderName: str
        """
        return super(PxrLayerMetalness, self).shaderName()

    def setDiffuse(self, value):
        """Sets the diffuse color attr for both self.layer1Node and the metal node self.layer2Node

        :param value: The color as rendering space float color, (0.5, 1.0, 0.0)
        :type value: list(float)
        """
        cmds.setAttr("{}.diffuseColor".format(self.layer1Node.fullPathName()),
                     value[0], value[1], value[2], type="double3")
        cmds.setAttr("{}.diffuseColor".format(self.layer2Node.fullPathName()),
                     0.0, 0.0, 0.0, type="double3")
        cmds.setAttr("{}.specularEdgeColor".format(self.layer2Node.fullPathName()),
                     value[0], value[1], value[2], type="double3")

    def diffuse(self):
        """Returns the value of the diffuse color as rendering space float, (0.5, 1.0, 0.0)

        :return value: The diffuse color as linear float rgb (0.1, 0.5, 1.0)
        :rtype value: list(float)
        """
        return cmds.getAttr("{}.diffuseColor".format(self.layer1Node.fullPathName()))[0]

    def setDiffuseWeight(self, value):
        """Sets the diffuse weight, only on the layer1 node

        :param value: The diffuse weight value 0.0-1.0
        :type value: float
        """
        cmds.setAttr("{}.diffuseGain".format(self.layer1Node.fullPathName()), value)

    def diffuseWeight(self):
        """Returns the current diffuse weight

        :return value: The diffuse weight value 0-1.0
        :rtype value: float
        """
        return cmds.getAttr("{}.diffuseGain".format(self.layer1Node.fullPathName()))

    def setMetalness(self, value):
        """Sets the metalness value

        :param value: The metalness value 0-1.0
        :type value: float
        """
        cmds.setAttr("{}.layer1Mask".format(self.layerMixerNode.fullPathName()), value)
        cmds.setAttr("{}.specularGain".format(self.layer2Node.fullPathName()), 1.0)  # make sure spec is on for layer 2
        cmds.setAttr("{}.enableSpecular".format(self.layer2Node.fullPathName()),
                     1)  # Specular should always be on layer 2

    def metalness(self):
        """Returns the metalness value

        :return value: The metalness value 0-1.0
        :rtype value: float
        """
        return cmds.getAttr("{}.layer1Mask".format(self.layerMixerNode.fullPathName()))

    def setSpecWeight(self, value):
        """Sets the specular weight value

        :param value: Specular Weight value 0-1.0
        :type value: float
        """
        cmds.setAttr("{}.specularGain".format(self.layer1Node.fullPathName()), value)
        cmds.setAttr("{}.enableSpecular".format(self.layer1Node.fullPathName()), 1)  # Specular on
        cmds.setAttr("{}.specularFresnelMode".format(self.shaderNode.fullPathName()), 1)  # physical primary spec

    def specWeight(self):
        """Returns the specular weight value

        :return value:  Specular Weight value 0-1.0
        :rtype value: float
        """
        return cmds.getAttr("{}.specularGain".format(self.layer1Node.fullPathName()))

    def setSpecColor(self, value):
        """Sets the specular color as rendering space float rgb (0.5, 1.0, 0.0)

        :param value: Specular color as rendering space float rgb (0.5, 1.0, 0.0)
        :type value: list(float)
        """
        cmds.setAttr("{}.specularEdgeColor".format(self.layer1Node.fullPathName()),
                     value[0], value[1], value[2], type="double3")
        cmds.setAttr("{}.enableSpecular".format(self.layer1Node.fullPathName()),
                     1)  # Specular should always be on layer 1

    def specColor(self):
        """Returns the specular color as rendering space float rgb (0.5, 1.0, 0.0)

        :return value: Specular color as rendering space float rgb (0.5, 1.0, 0.0)
        :rtype value: list(float)
        """
        return cmds.getAttr("{}.specularEdgeColor".format(self.layer1Node.fullPathName()))[0]

    def setSpecRoughness(self, value):
        """Sets the specular roughness value

        :param value: The specular roughness value 0-1.0
        :type value: float
        """
        cmds.setAttr("{}.specularRoughness".format(self.layer1Node.fullPathName()), value)
        cmds.setAttr("{}.specularRoughness".format(self.layer2Node.fullPathName()), value)
        cmds.setAttr("{}.enableSpecular".format(self.layer1Node.fullPathName()), 1)  # Specular on
        cmds.setAttr("{}.enableSpecular".format(self.layer2Node.fullPathName()), 1)  # Specular on

    def specRoughness(self):
        """Returns the specular roughness value

        :return value: The specular roughness value 0-1.0
        :rtype value: float
        """
        return cmds.getAttr("{}.specularRoughness".format(self.layer1Node.fullPathName()))

    def setSpecIOR(self, value):
        """Sets the specular IOR value 1 - 20.0

        :param value: The specular IOR value, 1.0 - 20.0
        :type value: float
        """
        cmds.setAttr("{}.specularIor".format(self.layer1Node.fullPathName()), value, value, value, type="double3")
        cmds.setAttr("{}.enableSpecular".format(self.layer1Node.fullPathName()), 1)  # Specular on

    def specIOR(self):
        """Sets the specular IOR value 1 - 20.0

        :return value: The specular IOR value, 1.0 - 20.0
        :rtype value: float
        """
        return cmds.getAttr("{}.specularIor".format(self.layer1Node.fullPathName()))[0][0]  # just return the red as IOR

    def setCoatColor(self, value):
        """Sets the clear coat color as rendering space float rgb (0.5, 1.0, 0.0)

        :param value: Clear coat color as rendering space float rgb (0.5, 1.0, 0.0)
        :type value: list(float)
        """
        cmds.setAttr("{}.clearcoatEdgeColor".format(self.layer1Node.fullPathName()),
                     value[0], value[1], value[2], type="double3")
        cmds.setAttr("{}.clearcoatEdgeColor".format(self.layer2Node.fullPathName()),
                     value[0], value[1], value[2], type="double3")
        cmds.setAttr("{}.enableClearcoat".format(self.layer1Node.fullPathName()), 1)  # Coat on
        cmds.setAttr("{}.enableClearcoat".format(self.layer2Node.fullPathName()), 1)  # Coat on

    def coatColor(self):
        """Returns the clear coat color as rendering space float rgb (0.5, 1.0, 0.0)

        :return value: Clear coat color as rendering space float rgb (0.5, 1.0, 0.0)
        :rtype value: list(float)
        """
        return cmds.getAttr("{}.clearcoatEdgeColor".format(self.layer1Node.fullPathName()))[0]

    def setCoatWeight(self, value):
        """Sets the clear coat weight 0-1.0

        :param value: The clear coat weight value 0-1.0
        :type value: float
        """
        layer1 = self.layer1Node.fullPathName()
        layer2 = self.layer2Node.fullPathName()
        shader = self.shaderNode.fullPathName()
        cmds.setAttr("{}.clearcoatGain".format(layer1), value)
        cmds.setAttr("{}.clearcoatGain".format(layer2), value)
        cmds.setAttr("{}.enableClearcoat".format(layer1), 1)  # Coat on
        cmds.setAttr("{}.enableClearcoat".format(layer2), 1)  # Coat on
        cmds.setAttr("{}.clearcoatFresnelMode".format(shader), 2)  # physical clearcoat

    def coatWeight(self):
        """Returns the clear coat weight 0-1.0

        :return value: The clear coat weight value 0-1.0
        :rtype value: float
        """
        return cmds.getAttr("{}.clearcoatGain".format(self.layer1Node.fullPathName()))

    def setCoatRoughness(self, value):
        """Sets the clear coat roughness value 0 - 1.0

        :param value: The clear coat roughness value 0 -1.0
        :type value: float
        """
        layer1 = self.layer1Node.fullPathName()
        layer2 = self.layer2Node.fullPathName()
        cmds.setAttr("{}.clearcoatRoughness".format(layer1), value)
        cmds.setAttr("{}.clearcoatRoughness".format(layer2), value)
        cmds.setAttr("{}.enableClearcoat".format(layer1), 1)  # Coat should always be on layer 1
        cmds.setAttr("{}.enableClearcoat".format(layer2), 1)  # Coat should always be on layer 1

    def coatRoughness(self):
        """Returns the clear coat roughness value 0 - 1.0

        :return value: The clear coat roughness value 0 -1.0
        :rtype value: float
        """
        return cmds.getAttr("{}.clearcoatRoughness".format(self.layer1Node.fullPathName()))

    def setCoatIOR(self, value):
        """Sets the clear coat IOR value 1 - 20.0

        :param value: The clear coat IOR value, 1.0 - 20.0
        :type value: float
        """
        layer1 = self.layer1Node.fullPathName()
        layer2 = self.layer2Node.fullPathName()
        cmds.setAttr("{}.clearcoatIor".format(layer1), value, value, value, type="double3")
        cmds.setAttr("{}.clearcoatIor".format(layer2), value, value, value, type="double3")
        cmds.setAttr("{}.enableClearcoat".format(layer1), 1)  # Specular should always be on layer 1
        cmds.setAttr("{}.enableClearcoat".format(layer2), 1)  # Specular should always be on layer 2

    def coatIOR(self):
        """Returns the clear coat IOR value 1 - 20.0

        :return value: The clear coat IOR value, 1.0 - 20.0
        :rtype value: float
        """
        return cmds.getAttr("{}.specularIor".format(self.layer1Node.fullPathName()))[0][0]  # return the red as IOR
