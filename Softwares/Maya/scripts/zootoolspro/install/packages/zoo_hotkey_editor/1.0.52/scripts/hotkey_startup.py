
from zoo.core.util import env


def startup(package):
    """ Updates the hotkeys on start up if it has already been installed.

    :param package:
    :return:
    """
    try:
        from zoo.apps.hotkeyeditor.core import keysets
        if env.isInMaya():
            keysets.KeySetManager()
    except ImportError:
        pass

