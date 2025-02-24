import logging
from zoo.core.util import zlogging
from maya.OpenMaya import MGlobal


class MayaGuiLogHandler(logging.Handler):
    """
    A python logging handler that displays error and warning
    records with the appropriate color labels within the Maya GUI
    """

    def __init__(self):
        super(MayaGuiLogHandler, self).__init__()

    def emit(self, record):
        msg = self.format(record)
        if record.levelno > logging.WARNING:
            # Error (40) Critical (50)
            MGlobal.displayError(msg)
        elif record.levelno > logging.INFO:
            # Warning (30)
            MGlobal.displayWarning(msg)
        else:
            # Debug (10) and Info (20)
            MGlobal.displayInfo(msg)


def setupLogging():
    handler = MayaGuiLogHandler()
    handler.setFormatter(logging.Formatter(zlogging.CentralLogManager().shellFormatter))
    zlogging.zooLogger.addHandler(handler)
