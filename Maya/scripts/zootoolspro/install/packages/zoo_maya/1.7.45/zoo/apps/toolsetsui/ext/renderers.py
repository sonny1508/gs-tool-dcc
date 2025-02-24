from zoo.apps.toolsetsui import toolsetui

from zoo.core.util import zlogging
from zoo.preferences.interfaces import coreinterfaces
from zoo.libs.utils import general
from zoo.libs.maya.cmds.renderer import rendererconstants
from zoo.libs.maya.qt.changerendererui import globalChangeRenderer, checkRenderLoaded, ui_loadRenderer
from zoo.apps.toolsetsui.widgets.toolsetwidget import ToolsetWidget

if general.TYPE_CHECKING:
    from typing import Union


logger = zlogging.getLogger(__name__)


class RendererMixin(object):
    """ Toolset widget with additional functionality to get it to work with renderers.

    """
    def initRendererMixin(self, disableVray=False, disableMaya=False):
        generalPrefs = coreinterfaces.generalInterface()
        generalPrefs.refreshSettings()
        renderer = generalPrefs.primaryRenderer()
        if disableMaya and renderer == rendererconstants.MAYA:
            self.properties.rendererIconMenu.value = rendererconstants.ARNOLD
        elif disableVray and renderer == rendererconstants.VRAY:
            self.properties.rendererIconMenu.value = rendererconstants.ARNOLD
        else:
            self.properties.rendererIconMenu.value = renderer

    def global_changeRenderer(self):
        """Updates all GUIs with the current renderer"""
        generalPrefs = coreinterfaces.generalInterface()
        generalPrefs.refreshSettings()
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveRendererChange")
        toolsets.remove(self)

        globalChangeRenderer(self.properties.rendererIconMenu.value, toolsets)

    def global_receiveRendererChange(self, renderer,  ignoreVRay=False, ignoreMaya=False):
        """Receives from other GUIs, changes the renderer when it is changed"""
        if renderer == rendererconstants.VRAY and ignoreVRay:
            return  # Ignore as VRay not supported
        if renderer == rendererconstants.MAYA and ignoreMaya:
            return  # Ignore as Maya not supported
        self = self  # type: Union[ToolsetWidget, RendererMixin]
        self.properties.rendererIconMenu.value = renderer
        self.updateFromProperties()
        self.setRenderer(updateAllUIs=False)  # Refreshes the UI with new renderer

    def setRenderer(self, updateAllUIs=True):
        """Filter Maya Scenes by renderer and sets the renderer for all UIs and prefs (optional)

        Uses file suffixes so if set to Arnold then removes someFile_redshift.ma and someFile_renderman.ma from list
        Should switch this over to the info meta data later.

        :param updateAllUIs: If True updates all UIs with the current renderer and sets the renderer in prefs
        :type updateAllUIs: bool
        """
        renderer = self.properties.rendererIconMenu.value

        if hasattr(self, "updateShaderTypeList") and renderer is not rendererconstants.ALL:
            self.updateShaderTypeList()
        currentWidget = self.currentWidget()
        # Set filters only for .MA and .MB mini browsers ------------------------------
        if hasattr(currentWidget, "miniBrowser"):
            filteredList = list()
            if renderer != rendererconstants.ALL:  # If set to a renderer then filter other renderers
                filteredList = rendererconstants.RENDERER_BROWSER_FILTERS.get(renderer, [])
                # create a look behind regex for each renderer name
                filteredList = [i+"*" for i in filteredList]
            try:  # Do the browser filter
                currentWidget.miniBrowser.setPersistentFilter("|.*".join(filteredList), tags=["filename"])
                currentWidget.miniBrowser.refreshThumbs()  # Do the UI refresh
            except AttributeError:
                pass

        if renderer == rendererconstants.ALL:  # Bail as do not update preferences only for certain browsers.
            return

        if updateAllUIs:
            self.global_changeRenderer()

    def checkRenderLoaded(self, renderer):
        """Checks that the renderer is loaded, if not opens a window asking the user to load it

        :param renderer: the nice name of the renderer "Arnold" or "Redshift" etc
        :type renderer: str
        :return rendererLoaded: True if the renderer is loaded
        :rtype rendererLoaded: bool
        """
        return checkRenderLoaded(renderer)

    def ui_loadRenderer(self, renderer):
        return ui_loadRenderer(renderer)
