"""Functions and constants related directly to Maya's color handling.

Example use:

.. code-block:: python

    from zoo.libs.maya.utils import mayacolors
    mayacolors.setColorSpaceAces()
    renderSpaceColor = mayacolors.displayColorToCurrentRenderingSpace(displaySpaceColor)
    displaySpaceColor = mayacolors.renderingColorToDisplaySpace(renderingSpaceColor)

"""

from maya import cmds
from maya import OpenMaya as om1
from maya import OpenMayaRender
from maya.api import OpenMaya as om2

from zoo.libs.maya.utils import mayaenv
from zoo.libs.utils import output, color

MAYA_VERSION = mayaenv.mayaVersion()  # whole numbers (int) 2020 etc:

# Maya calls these from the list integer 0-31, note this is not Linear (will not match the viewport), see linear below
MAYA_COLOR_SRGB = [(0.0, 0.0156, 0.3764),
                   (0.0, 0.0, 0.0),
                   (0.251, 0.251, 0.251),
                   (0.6, 0.6, 0.6),
                   (0.608, 0.0, 0.157),
                   (0.0, 0.0156, 0.3764),
                   (0.0, 0.0, 1.0),
                   (0.0, 0.275, 0.098),
                   (0.149, 0.0, 0.263),
                   (0.784, 0.0, 0.784),
                   (0.541, 0.282, 0.2),
                   (0.247, 0.137, 0.121),
                   (0.6, 0.149, 0.0),
                   (1.0, 0.0, 0.0),
                   (0.0, 1.0, 0.0),
                   (0.0, 0.255, 0.6),
                   (1.0, 1.0, 1.0),
                   (1.0, 1.0, 0.0),
                   (0.3921, 0.8627, 1.0),
                   (0.263, 1.0, 0.639),
                   (1.0, 0.650, 0.650),
                   (0.894, 0.674, 0.474),
                   (1.0, 1.0, 0.388),
                   (0.0, 0.6, 0.329),
                   (0.631, 0.416, 0.188),
                   (0.620, 0.631, 0.188),
                   (0.407, 0.631, 0.188),
                   (0.188, 0.631, 0.365),
                   (0.188, 0.631, 0.631),
                   (0.188, 0.404, 0.631),
                   (0.435, 0.188, 0.631),
                   (0.631, 0.188, 0.416)]

# linear Maya colors hardcoded, Maya calls these from the list integer 0-31
MAYA_COLOR_LINEAR_RGB = [(0.0000, 0.0012, 0.1169),
                         (0.0000, 0.0000, 0.0000),
                         (0.0513, 0.0513, 0.0513),
                         (0.3185, 0.3185, 0.3185),
                         (0.3280, 0.0000, 0.0213),
                         (0.0000, 0.0012, 0.1169),
                         (0.0000, 0.0000, 1.0000),
                         (0.0000, 0.0615, 0.0097),
                         (0.0194, 0.0000, 0.0562),
                         (0.5771, 0.0000, 0.5771),
                         (0.2540, 0.0646, 0.0331),
                         (0.0497, 0.0168, 0.0136),
                         (0.3185, 0.0194, 0.0000),
                         (1.0000, 0.0000, 0.0000),
                         (0.0000, 1.0000, 0.0000),
                         (0.0000, 0.0529, 0.3185),
                         (1.0000, 1.0000, 1.0000),
                         (1.0000, 1.0000, 0.0000),
                         (0.1274, 0.7156, 1.0000),
                         (0.0562, 1.0000, 0.3660),
                         (1.0000, 0.3801, 0.3801),
                         (0.7756, 0.4119, 0.1908),
                         (1.0000, 1.0000, 0.1246),
                         (0.0000, 0.3185, 0.0884),
                         (0.3559, 0.1444, 0.0295),
                         (0.3424, 0.3559, 0.0295),
                         (0.1378, 0.3559, 0.0295),
                         (0.0295, 0.3559, 0.1096),
                         (0.0295, 0.3559, 0.3559),
                         (0.0295, 0.1357, 0.3559),
                         (0.1587, 0.0295, 0.3559),
                         (0.3559, 0.0295, 0.1444)]

# Maya's index colors by name for objects, Maya calls these from the list integer 0-31
MAYA_COLOR_NICENAMES = ['none',
                        'black',
                        'lightGrey',
                        'midGrey',
                        'tomatoe',
                        'darkBlue',
                        'blue',
                        'darkGreen',
                        'darkPurple',
                        'pink',
                        'brownOrange',
                        'brown',
                        'orange',
                        'red',
                        'green',
                        'royalBlue',
                        'white',
                        'yellow',
                        'babyBlue',
                        'aqua',
                        'palePink',
                        'skin',
                        'paleYellow',
                        'paleGreen',
                        'orangeBrownLight',
                        'olive',
                        'citrus',
                        'forrestGreen',
                        'java',
                        'endeavourBlue',
                        'darkOrchid',
                        'mediumRedViolet']

VP_BG_COLORS_LINEAR = [[0.0, 0.0, 0.0],
                       [0.36, 0.36, 0.36],
                       [0.613, 0.613, 0.613]]
VP_BG_GRADIENT_TOP = [0.535, 0.617, 0.702]
VP_BG_GRADIENT_BOT = [0.052, 0.052, 0.052]
VP_GRADIENT_COLORS_LINEAR = [[VP_BG_GRADIENT_TOP, VP_BG_GRADIENT_BOT]]

ZOO_BG_COLORS_LINEAR = [VP_BG_COLORS_LINEAR[0],
                        [0.16, 0.16, 0.16],
                        [0.26, 0.26, 0.26],
                        VP_BG_COLORS_LINEAR[1],
                        VP_BG_COLORS_LINEAR[2]]


# -----------------------------
# COLOR MANAGEMENT
# -----------------------------


def setColorSpaceLinear(message=True):
    """Sets color space color management settings to be linear as per older versions of Maya in 2022 and above"""
    if mayaenv.mayaVersion() >= 2022:
        setRenderingSpace(renderSpace="linear", message=False)
        setViewTransform(view="noToneMap", message=False)
        if message:
            output.displayInfo("Success: Render space set to Linear sRGB, view transform set to No Tone-Map")
    else:
        output.displayWarning("This setting is for Maya 2022. "
                              "The Linear color management setting is the default in Maya 2020 and below.")


def setColorSpaceAces(message=True):
    """Sets color space color management settings to be ACES as per the new defaults in Maya in 2022 and above"""
    if mayaenv.mayaVersion() >= 2022:
        setRenderingSpace(renderSpace="aces", message=False)
        setViewTransform(view="sdrVideo", message=False)
        if message:
            output.displayInfo("Success: Render space set to ACES CG, view transform set to SDR-Video")
    else:
        output.displayWarning("ACES color management is only in Maya 2022 and above. ")


def setColorSpaceAcesNoTone(message=True):
    """Sets color space color management settings to be ACES (no tone map) in Maya in 2022 and above"""
    if mayaenv.mayaVersion() >= 2022:
        setRenderingSpace(renderSpace="aces", message=False)
        setViewTransform(view="noToneMap", message=False)
        if message:
            output.displayInfo("Success: Render space set to ACES CG, view transform set to No Tone-Map")
    else:
        output.displayWarning("ACES color management is only in Maya 2022 and above. ")


def setRenderingSpace(renderSpace="linear", message=True):
    """Sets the renderspace for Maya, use only in 2022 and above.

    :param renderSpace: linear or aces
    :type renderSpace: str
    :param message: Report a message to the user?
    :type message: bool
    """
    if renderSpace == "linear":
        cmds.colorManagementPrefs(edit=True, renderingSpaceName="scene-linear Rec.709-sRGB")
        if message:
            output.displayInfo("Success: Render space set to Linear sRGB")
    elif renderSpace == "aces":
        cmds.colorManagementPrefs(edit=True, renderingSpaceName="ACEScg")
        if message:
            output.displayInfo("Success: Render space set to ACES sRGB")
    else:
        output.displayError("color space {} not found".format(renderSpace))


def setViewTransform(view="noToneMap", message=True):
    """Sets the view transform (grade/tone-map) inside Maya.

    :param view: "noToneMap" or "sdrVideo"
    :type view: str
    :param message: Report a message to the user?
    :type message: bool
    """
    if view == "noToneMap":
        cmds.colorManagementPrefs(edit=True, viewTransformName="Un-tone-mapped (sRGB)")
        if message:
            output.displayInfo("Success: View Transform set to Un-Tone-Mapped")
    elif view == "sdrVideo":
        cmds.colorManagementPrefs(edit=True, viewTransformName="ACES 1.0 SDR-video (sRGB)")
        if message:
            output.displayInfo("Success: View Transform set to SDR-Video")
    elif view == "unity":
        cmds.colorManagementPrefs(edit=True, viewTransformName="Unity neutral tone-map (sRGB)")
        if message:
            output.displayInfo("Success: View Transform set to SDR-Video")
    else:
        output.displayError("View transform {} not found".format(view))


def displayColorToCurrentRenderingSpace(displayColor, setCurrentViewSpace=False, viewSpace="Un-tone-mapped"):
    """Converts display space color to the current rendering space using Maya's API

    The Maya commands function cmds.colorManagementConvert() is useless.

    Only works in Maya 2023 and above. Issues in 2022 unfortunately.

    If lower than 2023 will return the color linearized instead.

    viewSpace should be "Un-tone-mapped" if importing in JSON data, also for conversions to figure render space color.

    :param displayColor: display color (usually srgb color) as a float [0.1, 0.4, 0.6]
    :type displayColor: list(float)
    :param setCurrentViewSpace: Sets the viewspace as the current viewspace. If True kwarg viewSpace is ignored.
    :type setCurrentViewSpace: str
    :param viewSpace: What view to output? 'ACES 1.0 SDR-video', 'Un-tone-mapped', 'Unity neutral tone-map', 'Raw' etc
    :type viewSpace: str
    :return color: color in maya's native rendering space as a float
    :rtype color: list(float)
    """
    if MAYA_VERSION < 2023 or cmds.colorManagementPrefs(query=True, displayName=True) == "legacy":
        # then just return the linear color of the display srgb color
        return color.convertColorSrgbToLinear(displayColor)
    helper = OpenMayaRender.MColorMixingSpaceHelper()

    # Check Display Space exists in cases of redshift old scenes, weirdly there is no Display Space.
    if 'Display Space' not in helper.getMixingSpaceNames():
        return color.convertColorSrgbToLinear(displayColor)

    # spaces = helper.getMixingSpaceNames() ['Rendering Space', 'Display Space']
    # views = helper.getViewNames() ['ACES 1.0 SDR-video', 'Un-tone-mapped', 'Unity neutral tone-map', 'Log', 'Raw']
    helper.setMixingSpace('Display Space')  # set display space for the conversion

    if setCurrentViewSpace:
        viewSpace = cmds.colorManagementPrefs(query=True, viewName=True)
    helper.setView(viewSpace)  # "Un-tone-mapped" or 'ACES 1.0 SDR-video' etc

    renderingColorInst = helper.applyMixingTransform(om1.MColor(displayColor[0], displayColor[1], displayColor[2]),
                                                     OpenMayaRender.MColorMixingSpaceHelper.kInverse)
    # convert to om2 easier than om1, renderingSpaceColor includes alpha (r, g, b, a)
    renderingSpaceColor = om2.MColor((renderingColorInst.r, renderingColorInst.g, renderingColorInst.b))
    return [renderingSpaceColor[0], renderingSpaceColor[1], renderingSpaceColor[2]]


def renderingColorToDisplaySpace(renderColor, setCurrentViewSpace=False, viewSpace="Un-tone-mapped"):
    """Converts rendering space color to the current display space using Maya's API

    The Maya commands function cmds.colorManagementConvert() is useless.

    Only works in Maya 2023 and above. Display colors are Un-tone-mapped. Issues in 2022 unfortunately.

    If lower than 2023 will return the color linear to srgb instead.

    viewSpace should be "Un-tone-mapped" if importing in JSON data, also for conversions to figure render space color.

    :param displayColor: display color (usually srgb color) as a float [0.1, 0.4, 0.6]
    :type displayColor: list(float)
    :param viewSpace: what grade to output? 'ACES 1.0 SDR-video', 'Un-tone-mapped', 'Unity neutral tone-map', 'Raw' etc
    :type viewSpace: str
    :return color: color in maya's native rendering space as a float
    :rtype color: list(float)
    """
    if MAYA_VERSION < 2023 or cmds.colorManagementPrefs(query=True, displayName=True) == "legacy":
        # then just return the srgb color for safety
        return color.convertColorLinearToSrgb(renderColor)

    helper = OpenMayaRender.MColorMixingSpaceHelper()

    # Check Display Space exists in cases of redshift old scenes, weirdly there is no Display Space.
    if 'Display Space' not in helper.getMixingSpaceNames():
        return color.convertColorLinearToSrgb(renderColor)

    # spaces = helper.getMixingSpaceNames() ['Rendering Space', 'Display Space']
    # views = helper.getViewNames() ['ACES 1.0 SDR-video', 'Un-tone-mapped', 'Unity neutral tone-map', 'Log', 'Raw']
    helper.setMixingSpace('Display Space')  # set rendering space for the conversion

    if setCurrentViewSpace:
        viewSpace = cmds.colorManagementPrefs(query=True, viewName=True)

    helper.setView(viewSpace)  # "Un-tone-mapped" or 'ACES 1.0 SDR-video' etc
    displayColorInst = helper.applyMixingTransform(om1.MColor(renderColor[0], renderColor[1], renderColor[2]),
                                                   OpenMayaRender.MColorMixingSpaceHelper.kForward)
    # convert to om2 easier than om1, renderingSpaceColor includes alpha (r, g, b, a)
    displayColor = om2.MColor((displayColorInst.r, displayColorInst.g, displayColorInst.b))
    return [displayColor[0], displayColor[1], displayColor[2]]


def renderingColorToDisplaySpaceLegacy(renderingSpaceColor):
    """Converts rendering space color to the current display space color using cmds.colorManagementConvert (not great)

    This is depreciated, use renderingColorToDisplaySpace() as it supports the viewspace.

    :param renderingSpaceColor: color in maya's native rendering space as a float [0.1, 0.4, 0.6]
    :type renderingSpaceColor: list(float)
    :return displayColor: display color (usually srgb color) as a float [0.1, 0.4, 0.6]
    :rtype displayColor: list(float)
    """
    if MAYA_VERSION < 2023 or cmds.colorManagementPrefs(query=True, displayName=True) == "legacy":
        # then just return the srgb color for safety
        return color.convertColorLinearToSrgb(renderingSpaceColor)
    return cmds.colorManagementConvert(toDisplaySpace=renderingSpaceColor)

