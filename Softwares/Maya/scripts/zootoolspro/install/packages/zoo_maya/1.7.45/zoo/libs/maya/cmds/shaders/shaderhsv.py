"""
from zoo.libs.maya.cmds.shaders import shaderhsv
hsvInstance = shaderhsv.ShaderHSV()
"""
from maya import cmds

from zoo.libs.maya.cmds.shaders import shaderutils, shadermulti, shdmultconstants as sc
from zoo.libs.utils import color
from zoo.libs.maya.utils import mayacolors


class ShaderHSV(object):
    """Class for managing diffuse color hsv offsets from zoo shader instances.
    """

    def __init__(self):
        """Creates:

        self.shdrInsts: A list of all the shader instances found in the selection
        self.shdrDifAttrs: ["shaderName.diffuse"] strings for setting colors later with cached strings
        self.shdrStartColors: [[1.0, 0.0, 0.0]] list of colors in rendering color space
        """
        self.shdrInsts = shadermulti.shaderInstancesFromSelected(message=False)
        self.shdrDifAttrs = list()
        self.shdrStartColors = list()
        if not self.shdrInsts:
            return
        self.selectShaders()
        for shdrInst in self.shdrInsts:  # set the color and shader attr lists
            attr = shdrInst.diffuseColorAttr
            node = shdrInst.node.fullPathName()
            shaderDict = shdrInst.connectedAttrs()
            if shaderDict:
                if sc.DIFFUSE in shaderDict:
                    continue
            self.shdrDifAttrs.append(".".join([node, attr]))
            col = shdrInst.diffuse()
            self.shdrStartColors.append(col)

    def selectShaders(self):
        shadList = shaderutils.getShadersSelected()
        cmds.select(shadList, replace=True)

    def firstStartColor(self):
        """Returns the first start color for UI startup or selection change

        :return: The first startup color. Start color of the first found shader.
        :rtype: list(float)
        """
        if not self.shdrStartColors:
            return list()
        return self.shdrStartColors[0]

    def setHueOffset(self, offset):
        """Offsets the hue with a 0.0-360.0 value

        :param offset: Offset value 0.0-1.0
        :type offset: float
        :return: The first color now offset, in linear space used for UIs
        :rtype: list(float)
        """
        firstCol = list()
        for i, shdrAttr in enumerate(self.shdrDifAttrs):
            col = self.shdrStartColors[i]
            hsv = color.convertRgbToHsv(col)
            hsv = color.offsetHueColor(hsv, offset)
            col = color.convertHsvToRgb(hsv)
            cmds.setAttr(shdrAttr, col[0], col[1], col[2], type="double3")
            if i == 0:
                firstCol = col  # For UIs
        return firstCol

    def setHueOffsetDisplay(self, offset):
        """Offsets the hue with a 0.0-360.0 value

        :param offset: Offset value 0.0-1.0
        :type offset: float
        :return: The first color now offset, in srgb space used for UIs
        :rtype: list(float)
        """
        col = self.setHueOffset(offset)
        if not col:
            return col
        return mayacolors.renderingColorToDisplaySpace(col)

    def setSaturationOffset(self, offset):
        """Offsets the saturation with a 0.0-1.0 value

        TODO: Could do some math depending on the current value like vibrance?

        :param offset: Offset value 0.0-1.0
        :type offset: float
        :return: The first color now offset, in linear space used for UIs
        :rtype: list(float)
        """
        firstCol = list()
        for i, shdrAttr in enumerate(self.shdrDifAttrs):
            col = self.shdrStartColors[i]
            hsv = color.convertRgbToHsv(col)
            hsv = color.offsetSaturation(hsv, offset)
            col = color.convertHsvToRgb(hsv)
            cmds.setAttr(shdrAttr, col[0], col[1], col[2], type="double3")
            if i == 0:
                firstCol = col  # For UIs
        return firstCol

    def setSaturationOffsetDisplay(self, offset):
        """Offsets the saturation with a 0.0-1.0 value

        :param offset: Offset value 0.0-1.0
        :type offset: float
        :return: The first color now offset, in display space used for UIs
        :rtype: list(float)
        """
        col = self.setSaturationOffset(offset)
        if not col:
            return col
        return mayacolors.renderingColorToDisplaySpace(col)

    def setValueOffset(self, offset):
        """Offsets the value (brightness) with a 0.0-1.0 value

        TODO: Could do some math depending on the current value as a multiplier as seems a bit odd when you use.

        :param offset: Offset value 0.0-1.0
        :type offset: float
        :return: The first color now offset, in linear space used for UIs
        :rtype: list(float)
        """
        firstCol = list()
        for i, shdrAttr in enumerate(self.shdrDifAttrs):
            col = self.shdrStartColors[i]
            displayCol = mayacolors.renderingColorToDisplaySpace(col)
            hsv = color.convertRgbToHsv(displayCol)
            hsv = color.offsetValue(hsv, offset)
            displayCol = color.convertHsvToRgb(hsv)
            col = mayacolors.displayColorToCurrentRenderingSpace(displayCol)
            cmds.setAttr(shdrAttr, col[0], col[1], col[2], type="double3")
            if i == 0:
                firstCol = col  # For UIs
        return firstCol

    def setValueOffsetDisplay(self, offset):
        """Offsets the value (brightness) with a 0.0-1.0 value

        :param offset: Offset value 0.0-1.0
        :type offset: float
        :return: The first color now offset, in display space used for UIs
        :rtype: list(float)
        """
        col = self.setValueOffset(offset)
        if not col:
            return col
        return mayacolors.renderingColorToDisplaySpace(col)
