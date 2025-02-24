import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.renderer.rendererconstants import REDSHIFT, ARNOLD, RENDERMAN, MAYA, VRAY
from zoo.libs.maya.cmds.renderer import redshiftrendersettings, rendermanrendersettings, arnoldrendersettings, \
    vrayrendersettings
from zoo.libs.maya.qt.changerendererui import globalChangeRenderer
from zoo.libs.utils import output

from zoo.preferences.interfaces import coreinterfaces


def currentRenderer():
    """Returns the current renderer that is set in Zoo Tools.

    returns

        "Arnold" or Redshift" or "Renderman"

    :return renderer: Returns the nice name of the currently active renderer in Zoo Tools
    :rtype renderer: str
    """
    return coreinterfaces.generalInterface().primaryRenderer()


def changeRenderer(renderer, setDefault=True, load=True, message=True):
    """Change renderer for the whole of Zoo Tools Pro:

        "Arnold" or Redshift" or "Renderman"

    :param renderer: The renderer nice name
    :type renderer: str
    :param load: If True also try to load the renderer if it is not already loaded
    :type load: bool
    :param setDefault: If True set the renderer to the Zoo Tools default settings
    :type setDefault: bool
    :param message: Report he message to the user?
    :type message: bool
    :return generalSettingsPrefsData: The prefs data as a dict, now updated
    :rtype generalSettingsPrefsData: dict
    """
    from zoo.apps.toolsetsui import toolsetui
    generalPrefs = coreinterfaces.generalInterface()
    toolsets = toolsetui.toolsetsByAttr(attr="global_receiveRendererChange")
    globalChangeRenderer(renderer, toolsets)
    if load:  # Try to load the renderer
        if not loadRenderer(renderer):  # The renderer did not load so bail
            return dict()
    setRenderGlobals(renderer)  # sets the renderer as the default in the Render Settings window
    if setDefault:  # Set the Zoo Tools default render globals settings
        success = setDefaultRenderSettings(renderer)
        if message and success:
            output.displayInfo("Render `{}` loaded, and render globals changed to Zoo defaults".format(renderer))
        if message and not success:  # usually with Renderman
            output.displayWarning("Render `{}` loaded, but render globals not changed to Zoo defaults, please run "
                                       "`Default Render Settings` again.".format(renderer))
        return generalPrefs.settings()
    if message:
        output.displayInfo("Render `{}` loaded".format(renderer))
    return generalPrefs.settings()


def setDefaultRenderSettings(renderer, message=True):
    """Sets the default Zoo render settings for each renderer

    :param renderer: The renderer nice name
    :type renderer: str
    :param message: Report messages to the user
    :type message: bool
    """
    warnings = False
    if renderer == ARNOLD:
        arnoldrendersettings.setGlobalsArnold()
        arnoldrendersettings.setArnoldSamples()
    elif renderer == REDSHIFT:
        redshiftrendersettings.setGlobalsRedshift()
        redshiftrendersettings.setBounces()  # shouldn't fail
        redshiftrendersettings.setIPRMaxPasses()
        redshiftrendersettings.setMinMaxSamples()
    elif renderer == RENDERMAN:
        rendermanrendersettings.setGlobalsRenderman()
        warnings = not rendermanrendersettings.setMinMaxSamples()  # can fail
    if warnings:
        if message:
            om2.MGlobal.displayWarning("Renderer settings for `{}` did not finish, please run again".format(renderer))
        return False
    om2.MGlobal.displayInfo("`{}` zoo default renderer settings set.".format(renderer))
    return True


def setRenderGlobals(renderer):
    """

    :param renderer: The renderer nice name
    :type renderer: str
    :return:
    :rtype:
    """
    if renderer == ARNOLD:
        arnoldrendersettings.setGlobalsArnold()
    elif renderer == REDSHIFT:
        redshiftrendersettings.setGlobalsRedshift()
    elif renderer == RENDERMAN:
        rendermanrendersettings.setGlobalsRenderman()


def loadRenderer(renderer, bypassWindow=False):
    """Loads the given renderer with a confirmation popup window.

    :param renderer: The renderer nice name
    :type renderer: str
    :param bypassWindow: If True don't show the popup window, just return if the renderer is loaded or not
    :type bypassWindow: bool
    :return success: True if the renderer was loaded
    :rtype success: bool
    """
    from zoo.libs.pyqt.widgets import elements
    if not elements.checkRenderLoaded(renderer, bypassWindow=False):
        om2.MGlobal.displayWarning("Renderer `{}` is not loaded".format(renderer))
        return False
    return True


def setDefaultRenderSettingsAuto():
    """Sets the default render settings on the currently selected renderer
    """
    renderer = currentRenderer()
    if not loadRenderer(renderer):
        return
    setDefaultRenderSettings(renderer)


def openRenderview(renderer, final=False, ipr=False):
    """Opens a render view window and optionally starts rendering a final fame or IPR for the given renderer.

    :param renderer: The renderer nice name
    :type renderer: str
    :param final: True will immediately start final rendering an image
    :type final: bool
    :param ipr: True will immediately start IPR rendering an image
    :type ipr: bool
    """
    if renderer == ARNOLD or renderer == MAYA:
        arnoldrendersettings.openArnoldRenderview(final=final, ipr=ipr)
    elif renderer == REDSHIFT:
        redshiftrendersettings.openRedshiftRenderview(final=final, ipr=ipr)
    elif renderer == RENDERMAN:
        rendermanrendersettings.openRendermanRenderview(final=final, ipr=ipr)
    elif renderer == VRAY:
        vrayrendersettings.openVRayRenderview(final=final, ipr=ipr)


def openRenderviewAuto(final=False, ipr=False):
    """Opens a render view window and optionally starts rendering a final fame or IPR for the current renderer.

    :param final: True will immediately start final rendering an image
    :type final: bool
    :param ipr: True will immediately start IPR rendering an image
    :type ipr: bool
    """
    renderer = currentRenderer()
    if not loadRenderer(renderer):
        return
    openRenderview(renderer, final=final, ipr=ipr)
