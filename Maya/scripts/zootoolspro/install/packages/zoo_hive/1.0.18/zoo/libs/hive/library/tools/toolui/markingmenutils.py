from maya.api import OpenMaya as om2
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


def logUnableToLoadComponentsMM():
    """Exception Log for when loading the rig and components as part of the
    marking menu.
    """
    message = "Marking-menu failed! This rig may need upgrading if built with Hive Alpha. " \
              "Marking-menus will now fail on older rigs.  Zoo default assets have been updated please upgrade." \
              "You may also roll back Zoo Tools to older versions."
    logger.debug(message, exc_info=True)
    om2.MGlobal.displayWarning(message)
