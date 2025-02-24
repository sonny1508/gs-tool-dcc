from zoo.libs.pyqt.widgets.popups import MessageBox
from zoo.libs.maya.cmds.renderer import rendererload

# ------------------------------------
# POPUP WINDOW
# ------------------------------------
from zoo.libs.utils import output
from zoo.preferences.interfaces import coreinterfaces


def ui_loadRenderer(renderer):
    """Popup window for loading a renderer

    :param renderer: Renderer nicename
    :type renderer: str
    :return okPressed: Was the ok button pressed or not
    :rtype okPressed: bool
    """
    message = "The {} renderer isn't loaded. Load now?".format(renderer)
    # parent is None to parent to Maya to fix stylesheet issues
    okPressed = MessageBox.showOK(title="Load Renderer", parent=None, message=message)
    return okPressed


def checkRenderLoaded(renderer, bypassWindow=False):
    """Checks that the renderer is loaded, if not opens a window asking the user to load it

    :param renderer: the nice name of the renderer "Arnold" or "Redshift" etc
    :type renderer: str
    :param bypassWindow: If True don't show the popup window, just return if the renderer is loaded or not
    :type bypassWindow: bool
    :return rendererLoaded: True if the renderer is loaded
    :rtype rendererLoaded: bool
    """
    if not rendererload.getRendererIsLoaded(renderer):
        if bypassWindow:
            return False
        okPressed = ui_loadRenderer(renderer)
        if okPressed:
            success = rendererload.loadRenderer(renderer)
            return success
        return False
    return True


# ------------------------------------
# RENDERER - AND SEND/RECEIVE ALL TOOLSETS
# ------------------------------------


def globalChangeRenderer(renderer, toolsets):
    """Updates all GUIs with the current renderer.

    From toolset code run:

    .. code-block:: python

        toolsets = toolsetui.toolsets(attr="global_receiveRendererChange")
        self.generalSettingsPrefsData = elements.globalChangeRenderer(self.properties.rendererIconMenu.value,
                                                                      toolsets,
                                                                      self.generalSettingsPrefsData,
                                                                      pc.PREFS_KEY_RENDERER)

    :param renderer: The renderer nice name to change to for all UIs
    :type renderer: str
    :param toolsets: A list of all the toolset UIs to change.  Should be strings but may be objects.
    :type toolsets: list
    :return: The preferences data file now updated
    :rtype: object
    """
    for tool in toolsets:  # todo possibly should be a ActionPlugin
        tool.global_receiveRendererChange(renderer)

    generalPrefs = coreinterfaces.generalInterface()
    # save renderer to the general settings preferences .pref json
    if not generalPrefs.settingsValid():  # should be very rare
        output.displayError("The preferences object is not valid")
        return



    generalPrefs.setPrimaryRenderer(renderer)
    output.displayInfo("Preferences Saved: Global renderer saved as "
                       "`{}`".format(renderer))
    return

