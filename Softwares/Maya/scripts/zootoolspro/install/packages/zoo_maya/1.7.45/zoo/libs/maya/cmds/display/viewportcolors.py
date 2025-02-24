from maya import cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.utils.mayacolors import ZOO_BG_COLORS_LINEAR  # The color list to cycle cycleBackgroundColorsZoo()
from zoo.libs.utils import color as colorutils


def setBackgroundColorLinear(linearFloatColor):
    """Set the background color as with color in linearFloat format

    :param linearFloatColor: The color in linear float (0.01, 1.0, 0.543)
    :type linearFloatColor: list(float)
    """
    cmds.displayRGBColor('background', linearFloatColor[0], linearFloatColor[1], linearFloatColor[2])
    cmds.displayPref(displayGradient=False)


def backgroundColorLinear():
    """Gets the color of the background and returns in Linear float

    :return color: Color as a linear float.
    :rtype color: list(float)
    """
    return cmds.displayRGBColor("background", query=True)


def setBackgroundColorSrgb(srgbFloatColor):
    """Set the background color as with color in SrgbFloat format

    :param srgbFloatColor: The color in srgb float (0.01, 1.0, 0.543)
    :type srgbFloatColor: list(float)
    """
    color = colorutils.convertColorSrgbToLinear(srgbFloatColor)
    cmds.displayRGBColor('background', color[0], color[1], color[2])
    cmds.displayPref(displayGradient=False)


def backgroundColorSrgb():
    """Gets the color of the background and returns in srgb float

    :return color: Color as a srgb float.
    :rtype color: list(float)
    """
    color = cmds.displayRGBColor("background", query=True)
    return colorutils.convertColorLinearToSrgb(color)


def viewportList():
    """Returns the viewport displayRGBColor list of strings, a large Maya list with various color preferences

    :return displayRGBColorList: a large Maya list with various color preferences
    :rtype displayRGBColorList: list(str)
    """
    return cmds.displayRGBColor(list=True)


def stringToFloatList(txt, keyWord):
    """Converts text into a float color, annoying cause mel doesn't return dictionaries.

    .. code-block:: python

        result = stringToFloatList("background 0.613 0.613 0.613", "background")
        # [0.613, 0.613, 0.613]



    :param txt: one entry of unicode string from the viewportList
    :type txt:
    :param keyWord: The keyword to remove ie "background", "backgroundTop" or "backgroundBottom"
    :type keyWord:
    :return: [0.613, 0.613, 0.613]
    :rtype: list[float]
    """
    txt = txt.replace("{} ".format(keyWord), "")
    txt = txt.replace("\n", "")
    txtList = txt.split(" ")
    return [float(i) for i in txtList]


def backgroundColors():
    """Returns the background colors as a list in [bgColorLinear, topGradColorLinear, botGradColorLinear]

    :return backgroundColorList: background colors as a list in [bgColorLinear, topGradColorLinear, botGradColorLinear]
    :rtype backgroundColorList: list[list[float]]
    """
    bgColorLinear = list()
    topGradColorLinear = list()
    botGradColorLinear = list()
    for item in viewportList():
        if item.startswith('background '):
            bgColorLinear = stringToFloatList(item, "background")
        elif item.startswith('backgroundTop '):
            topGradColorLinear = stringToFloatList(item, "backgroundTop")
        elif item.startswith('backgroundBottom '):
            botGradColorLinear = stringToFloatList(item, "backgroundBottom")
    return [bgColorLinear, topGradColorLinear, botGradColorLinear]


def setNextColor(linearFloatColorList, currentInt):
    """Sets the next color given the current list Int and a linearFloatColorList

    :param linearFloatColorList: The color list in linear float (0.01, 1.0, 0.543)
    :type linearFloatColorList: list(list(float))
    :param currentInt: The current color as an int
    :type currentInt: int
    """
    if currentInt == len(linearFloatColorList) - 1:
        setBackgroundColorLinear(linearFloatColorList[0])
        om2.MGlobal.displayInfo("Setting Color 1")
    else:
        setBackgroundColorLinear(linearFloatColorList[currentInt + 1])
        om2.MGlobal.displayInfo("Setting Color {}".format(str(currentInt + 2)))


def cycleBackgroundColors(linearFloatColorList):
    """Cycles the background colors like maya alt b only with a custom list of linear float colors

    :param linearFloatColorList: The color list in linear float (0.01, 1.0, 0.543)
    :type linearFloatColorList: list(list(float))
    """
    colorSet = False
    bgColorList = backgroundColors()
    if cmds.displayPref(query=True, displayGradient=True):  # If gradient then switch to flat color
        setNextColor(linearFloatColorList, len(linearFloatColorList) - 1)  # Set to first color
        return
    elif linearFloatColorList[-1] == bgColorList[0]:  # Matches the last color so set to gradient background
        cmds.displayPref(displayGradient=True)
        om2.MGlobal.displayInfo("Setting Color To Gradient")
        return

    # Cycle through colors and set to the next color in the list
    for i, color in enumerate(linearFloatColorList):
        if color == bgColorList[0]:  # bgColorList[0] is the main bgColor
            setNextColor(linearFloatColorList, i)
            colorSet = True
            break
    if not colorSet:  # sets to the first color
        setNextColor(linearFloatColorList, len(linearFloatColorList) - 1)  # Set to first color


def cycleBackgroundColorsZoo():
    """Cycles the background colors like maya alt b only with two more dark background colors.

    See mayacolors.ZOO_BG_COLORS_LINEAR for the color list in linear float
    """
    cycleBackgroundColors(ZOO_BG_COLORS_LINEAR)
