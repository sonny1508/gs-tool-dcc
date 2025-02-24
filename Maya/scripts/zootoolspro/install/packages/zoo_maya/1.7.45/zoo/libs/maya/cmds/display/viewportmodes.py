""""
from zoo.libs.maya.cmds.display import viewportmodes
panel = viewportmodes.panelUnderPointerOrFocus(viewport3d=True)
viewportmodes.lookThroughSelected()

"""

from maya import cmds
import maya.mel as mel
import maya.api.OpenMaya as om2

from zoo.libs.utils import output


# --------------
# PANELS
# --------------


def panelUnderCursor(viewport3d=True):
    """Returns the panel under the pointer, with a check to filter for a viewport panel.  Returns "" if not found

    :param viewport3d: if True will test to see if the panel under the cursor is a 3d viewport with a camera
    :type viewport3d: bool
    :return mayaPanel: The name of the Maya panel, will be "" if no panel found
    :rtype mayaPanel: str
    """
    try:
        mayaPanel = cmds.getPanel(underPointer=True)
        if viewport3d:
            cmds.modelPanel(mayaPanel, query=True, camera=True)  # test if a 3d viewport, will error here if not
        return mayaPanel
    except RuntimeError:  # should always be an active viewport
        return ""


def panelWithFocus(viewport3d=True):
    """Returns the panel with focus, with a check to filter for a viewport panel.  Returns "" if not found

    :param viewport3d: if True will test to see if the panel under the cursor is a 3d viewport with a camera
    :type viewport3d: bool
    :return mayaPanel: The name of the Maya panel, will be "" if no panel found
    :rtype mayaPanel: str
    """
    focusPanel = cmds.getPanel(withFocus=True)
    try:
        if viewport3d:
            cmds.modelPanel(focusPanel, query=True, camera=True)  # test if a 3d viewport, will error here if not
    except RuntimeError:  # should always be an active viewport
        return ""
    return focusPanel


def firstViewportPanel():
    """Returns the first visible viewport panel it finds in the current Maya session

    :return viewportPanel: The name of the Maya panel that is a viewport, will be "" if not found (might be impossible)
    :rtype viewportPanel: str
    """
    panel = ""
    allPanels = cmds.getPanel(visiblePanels=True)
    for panel in allPanels:
        try:
            cmds.modelPanel(panel, query=True, camera=True)  # test if a 3d viewport, will error here if not
            break
        except RuntimeError:  # if not a 3d viewport, so set panel to ""
            panel = ""
    return panel


def panelUnderPointerOrFocus(viewport3d=False, prioritizeUnderCursor=True, message=True):
    """returns the mayaPanel that is either:

        1. Under the cursor
        2. The active panel (with focus)
        3. First visible viewport panel (only if viewport3d=True)

    If prioritizeUnderCursor=True then the active panel (with focus) will prioritize before under the cursor.

    In general use prioritizeUnderCursor=True for hotkeys and prioritizeUnderCursor=False for UIs.

    The "viewport3d" flag set to True will return only panels with 3d cameras, ie 3d viewports, otherwise None

    :param viewport3d: if True will test to see if the panel under the cursor is a 3d viewport with a camera
    :type viewport3d: bool
    :param prioritizeUnderCursor: if True return under cursor first, and if not then with focus
    :type prioritizeUnderCursor: bool
    :param message: report a potential fail message to the user?
    :type message: bool

    :return mayaPanel: The name of the Maya panel, will be "" if no panel found
    :rtype mayaPanel: str
    """
    if prioritizeUnderCursor:
        panel = panelUnderCursor(viewport3d=viewport3d)
        if panel:
            return panel
        panel = panelWithFocus(viewport3d=viewport3d)  # will be "" if no viewport found
        if panel:
            return panel
    else:
        panel = panelWithFocus(viewport3d=viewport3d)
        if panel:
            return panel
        panel = panelUnderCursor(viewport3d=viewport3d)  # will be "" if no viewport found
        if panel:
            return panel
    # No viewport panels in focus or under pointer so try to find the first open viewport panel in the scene.
    if viewport3d:
        panel = firstViewportPanel()
        if panel:
            return panel
    if message:
        om2.MGlobal.displayWarning("No viewport found, the active window must be under the cursor or the "
                                   "active window must be a 3d viewport.")
    return panel  # returns ""


def lookThroughSelected():
    """Works the same as Panels (viewport menu) > Look Through Selected.

    Compatible with both lights and cameras as uses the mel code.  Can map to a hotkey.
    """
    sel = cmds.ls(selection=True)
    if not sel:
        return
    panel = panelUnderPointerOrFocus(viewport3d=True)
    if panel:
        mel.eval('lookThroughModelPanel {} {};'.format(sel[0], panel))


def editorFromPanelType(scriptedPanelType="graphEditor"):
    """Returns the editors from the scriptedPanelType.

    eg. "graphEditor" returns the graph editor editors as a list:

        ["graphEditor1OutlineEd", "graphEditor1OutlineEdSecondary"]

    :param scriptedPanelType: The panel type to search for, eg. "graphEditor"
    :type scriptedPanelType: str
    :return: The editors from the scriptedPanelType
    :rtype: list(str)
    """
    editorsOfType = list()
    scriptedPanels = cmds.getPanel(type='scriptedPanel') or []

    graphPanels = set(
        panel for panel in scriptedPanels
        if cmds.scriptedPanel(panel, query=True, type=True) == scriptedPanelType)

    if not graphPanels:
        return editorsOfType

    editors = cmds.lsUI(editors=1)

    for panel in graphPanels:
        for editor in editors:
            if cmds.outlinerEditor(editor, ex=1) and cmds.outlinerEditor(editor, q=1, pnl=1) == panel:
                editorsOfType.append(editor)
    return editorsOfType


# --------------
# MODEL EDITOR DISPLAY TOGGLES (HOTKEYS)
# --------------


def displayToggleTextureMode():
    """Toggles the texture viewport mode, will invert. Eg. if "on" turns "off", usually on a hotkey"""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:
        return
    invertStatus = not cmds.modelEditor(mayaPanel, query=True, displayTextures=True)
    cmds.modelEditor(mayaPanel, edit=True, displayTextures=invertStatus)  # set as inverse of current texture mode


def displayToggleWireShadedMode():
    """Toggles the shaded viewport mode. Will invert. Eg. if "wireframe" turns "shaded",  usually on a hotkey"""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return
    displayAppearance = cmds.modelEditor(mayaPanel, query=True, displayAppearance=True)
    if displayAppearance == "wireframe":  # is currently wireframe so make shaded
        cmds.modelEditor(mayaPanel, edit=True, displayAppearance="smoothShaded")
    else:  # is currently shaded so make wireframe
        cmds.modelEditor(mayaPanel, edit=True, displayAppearance="wireframe")


def displayToggleLightingMode():
    """Toggles the light viewport mode. Will invert. Eg. if "lights on" turns "lights off",  usually on a hotkey"""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return
    displayAppearance = cmds.modelEditor(mayaPanel, query=True, displayLights=True)
    if displayAppearance == "all":  # is currently lights on so turn off
        cmds.modelEditor(mayaPanel, edit=True, displayLights="default")
    else:  # is currently lights off so turn on
        cmds.modelEditor(mayaPanel, edit=True, displayLights="all")


# --------------
# MODEL EDITOR DISPLAY SETTINGS
# --------------

def setDisplayTextureMode(textures=True):
    """Turns the textures of the viewport on or off"""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:
        return
    cmds.modelEditor(mayaPanel, edit=True, displayTextures=textures)


def displayTextureMode(message=True):
    """Returns whether textures are on or off in the active viewport, will return None if no viewports"""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True, message=message)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return None
    return cmds.modelEditor(mayaPanel, query=True, displayTextures=True)


def setDisplayLightingMode(display=True):
    """Turns on/off the light viewport mode."""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return None
    if display:
        cmds.modelEditor(mayaPanel, edit=True, displayLights="all")
    else:
        cmds.modelEditor(mayaPanel, edit=True, displayLights="default")


def displayLightingMode(message=True):
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True, message=message)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return None
    if cmds.modelEditor(mayaPanel, query=True, displayLights=True) == "all":
        return True
    return False


def setDisplayShadowMode(display=True):
    """Turns on/off the light viewport mode."""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return
    cmds.modelEditor(mayaPanel, edit=True, shadows=display)


def displayShadowMode(message=True):
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True, message=message)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return None
    return cmds.modelEditor(mayaPanel, query=True, shadows=True)


def displayToggleWireOnShadedMode():
    """Toggles the 'wireframe on shaded' viewport mode. Will invert. Eg. if "shaded" turns "wireframeOnShaded" """
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return
    invertStatus = not cmds.modelEditor(mayaPanel, query=True, wireframeOnShaded=True)
    cmds.modelEditor(mayaPanel, edit=True, wireframeOnShaded=invertStatus)  # set as inverse of current texture mode


def displayToggleXrayMode():
    """Toggles the xray viewport mode. Will invert. Eg. if "xray on" turns "xray off",  usually on a hotkey"""
    mayaPanel = panelUnderPointerOrFocus(viewport3d=True)
    if not mayaPanel:  # viewport isn't 3d, error message already sent
        return
    invertStatus = not cmds.modelEditor(mayaPanel, query=True, xray=True)
    cmds.modelEditor(mayaPanel, edit=True, xray=invertStatus)  # set as inverse of current texture mode


def setViewportSettingsAll(value=True):
    """Sets all the viewport settings on for high quality.

    Lights, occlusion, anti-alias, textures

    :param value: Settings either on True or off False
    :type value: bool
    """
    setDisplayLightingMode(value)
    setDisplayShadowMode(value)
    setDisplayOcclusion(value)
    setDisplayAntiAlias(value)
    setDisplayTextureMode(value)


# --------------
# HARDWARE DISPLAY SETTINGS
# --------------


def setDisplayOcclusion(enable=True):
    """Sets the value of the viewport sceen space ambient occlusion

    :param enable: True enables Ambient Occlusion in the viewport
    :type enable: bool
    """
    cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", enable)


def displayOcclusion():
    """Gets the value of the viewport sceen space ambient occlusion

    :return aoValue: AO on or off
    :rtype aoValue: bool
    """
    return cmds.getAttr("hardwareRenderingGlobals.ssaoEnable")


def setDisplayMotionBlur(enable=True):
    """Sets the value of the viewport motion blur

    :param enable: True enables Motion Blur in the viewport
    :type enable: bool
    """
    cmds.setAttr("hardwareRenderingGlobals.motionBlurEnable", enable)


def setAntiAliasVPSamples(samples=16):
    """Set VP2 anti-alias sample settings

    :param samples: Sample level of the viewport settings, 8 or 16 etc
    :type samples: int
    """
    cmds.setAttr("hardwareRenderingGlobals.aasc", samples)


def antiAliasVPSamples():
    """Gets anti-aliasing sample settings amount

    :return antiAlias: Sample level of the viewport settings, 8 or 16 etc
    :rtype antiAlias: int
    """
    return cmds.getAttr("hardwareRenderingGlobals.aasc")


def setDisplayAntiAlias(enable=True):
    """Sets anti-aliasing on or off in the viewports

    :param enable: True will set anti-aliasing
    :type enable: bool
    """
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", enable)


def displayAntiAlias():
    """Gets anti-aliasing on or off in the viewports

    :return antiAlias: Anti-Aliasing on or off for the viewports
    :rtype antiAlias: bool
    """
    return cmds.getAttr("hardwareRenderingGlobals.multiSampleEnable")


def setMaxLights(lightCount):
    """Sets anti-aliasing on or off in the viewports

    :param enable: True will set anti-aliasing
    :type enable: bool
    """
    cmds.setAttr("hardwareRenderingGlobals.maxHardwareLights", lightCount)


def maxLights():
    """Gets the maximum light setting from hardwareRenderingGlobals

    :return antiAlias: Anti-Aliasing on or off for the viewports
    :rtype antiAlias: bool
    """
    return cmds.getAttr("hardwareRenderingGlobals.maxHardwareLights")


# --------------
# EXPOSURE GAMMA
# --------------


def setViewportExposureGamma(exposure=0.0, gamma=1.0):
    """Sets the gamma and exposure of the current 3d viewport panel.

    :param exposure: The exposure of the current viewport panel
    :type exposure: float
    :param gamma: The gamma of the current viewport panel
    :type gamma: float
    """
    mPanel = panelUnderPointerOrFocus(viewport3d=True, prioritizeUnderCursor=True, message=True)
    cmds.modelEditor(mPanel, edit=True, gamma=gamma, exposure=exposure)


def setViewportContrastGamma(exposure=0.0, gamma=1.0, contrast=1.0):
    """Pseudo-fake contrast using exposure and gamma.

    :param exposure: The exposure value
    :type exposure: float

    :param gamma: The amount of pseudo contrast
    :type gamma: float
    :param contrast: The gamma value
    :type contrast: float
    """
    if contrast == 0.0:
        newGamma = 1.0
    else:
        newGamma = 1.0 + (-contrast / 2.0)
    exposure = (contrast * 2.5) + exposure
    gamma = newGamma + (1.0 - gamma)
    setViewportExposureGamma(exposure, gamma)


# --------------
# RELOAD
# --------------


def regenerateUdimTextures(message=True):
    """Regenerates UDIM textures as per Viewport Settings `Regernerate All UV Tile Preview Textures`
    """
    mel.eval("generateAllUvTilePreviews")
    if message:
        output.displayInfo("UDIM File Textures Generated")


def reloadViewport(message=False):
    """viewport reload
    If used then reset the entire OGS database for all viewports using it.
    """
    cmds.ogs(reset=True)
    if message:
        output.displayInfo("The viewport has been refreshed with `cmds.ogs(reset=True)`")
