from zoo.apps.toolpalette import palette
from zoo.core.plugin import pluginmanager

PALETTE_UI = None  # type: palette.ToolPalette or None
_REGISTRY_INSTANCE = None  # type: pluginmanager.PluginManager


def currentInstance():
    """

    :return:
    :rtype: :class:`zoo.apps.toolpalette.palette.ToolPalette` or None
    """
    global PALETTE_UI
    return PALETTE_UI


def _setCurrentInstance(instance):
    global PALETTE_UI
    PALETTE_UI = instance


def load(parent=None, applicationName=None):
    """ Returns the paletteUI

    :return:
    :rtype: :class:`palette.ToolPalette`
    """
    instance = currentInstance()
    global _REGISTRY_INSTANCE
    if instance is not None:
        return instance

    assert applicationName is not None, "Application Name required"

    if _REGISTRY_INSTANCE is None:
        _REGISTRY_INSTANCE = pluginmanager.PluginManager(interface=[palette.ToolPalette],
                                                         variableName="application",
                                                         name="ArtistPalette")
        _REGISTRY_INSTANCE.registerByEnv("ZOO_ARTIST_PALETTE_PATH")
        _REGISTRY_INSTANCE.loadPlugin(applicationName, parent=parent)

    instance = _REGISTRY_INSTANCE.getPlugin(applicationName)
    _setCurrentInstance(instance)
    return PALETTE_UI


# depreciated function
show = load


def close(deleteMenu=True, deleteShelves=True):
    instance = currentInstance()
    try:
        instance.shutdown(deleteMenu=deleteMenu, deleteShelves=deleteShelves)
    except AttributeError as er:
        # happens when zootoolsUi global is none
        raise
    finally:
        _setCurrentInstance(None)
