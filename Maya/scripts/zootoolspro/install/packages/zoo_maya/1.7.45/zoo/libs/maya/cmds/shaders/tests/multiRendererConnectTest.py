"""
from zoo.libs.maya.cmds.shaders.tests import multiRendererConnectTest
multiRendererConnectTest.connectGridShaderNetwork("shader")

"""
from maya import cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.shaders import shadermulti
from zoo.libs.maya.cmds.objutils import attributes


def connectGridShaderNetwork(shader):
    """Connects a shader of any supported renderer to a pre-made grid node network

    Creates the proxy attributes and label attrs too.

    :param shader: Shader name
    :type shader: str
    """
    shaderInst = shadermulti.shaderInstanceFromShader(shader)

    cmds.connectAttr("gridColor_ramp.outColor", ".".join([shader, shaderInst.diffuseColorAttr]))
    if shaderInst.metalnessAttr:  # connect if metalness exists
        cmds.connectAttr("gridMetal_ramp.outAlpha", ".".join([shader, shaderInst.metalnessAttr]))
    elif shaderInst.specularWeightAttr:
        cmds.connectAttr("gridMetal_ramp.outAlpha", ".".join([shader, shaderInst.specularWeightAttr]))

    attributes.labelAttr("GridScale", shader)
    attributes.addProxyAttribute(shader, "grid_constants", "input1X", proxyAttr="gridSizeX", channelBox=True)
    attributes.addProxyAttribute(shader, "grid_constants", "input1Y", proxyAttr="gridSizeY", channelBox=True)
    attributes.addProxyAttribute(shader, "grid_constants", "input1Z", proxyAttr="gridSizeZ", channelBox=True)

    attributes.labelAttr("LineWidths", shader)
    attributes.addProxyAttribute(shader, "large_grid", "uWidth", proxyAttr="xWidthU", channelBox=True)
    attributes.addProxyAttribute(shader, "large_grid", "vWidth", proxyAttr="xWidthV", channelBox=True)
    attributes.addProxyAttribute(shader, "med_grid", "uWidth", proxyAttr="yWidthU", channelBox=True)
    attributes.addProxyAttribute(shader, "med_grid", "vWidth", proxyAttr="yWidthV", channelBox=True)
    attributes.addProxyAttribute(shader, "small_grid", "uWidth", proxyAttr="zWidthU", channelBox=True)
    attributes.addProxyAttribute(shader, "small_grid", "vWidth", proxyAttr="zWidthV", channelBox=True)

    attributes.labelAttr("Offsets", shader)
    attributes.addProxyAttribute(shader, "offsetU", "offsetU", proxyAttr="offsetU", channelBox=True)
    attributes.addProxyAttribute(shader, "offsetV", "offsetV", proxyAttr="offsetV", channelBox=True)

    attributes.labelAttr("Rotate", shader)
    attributes.addProxyAttribute(shader, "grid_constants", "rotateUV", proxyAttr="rotateUV", channelBox=True)

    output.displayInfo("Success: Grid Shader Connected")






