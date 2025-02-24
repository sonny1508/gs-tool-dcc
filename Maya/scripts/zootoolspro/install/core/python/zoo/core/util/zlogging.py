import logging
import os

from zoovendor import six
from zoo.core.util import classtypes

LOG_PREFIX = "zootools"
CENTRAL_LOGGER_NAME = "zootools"
LOG_LEVEL_ENV_NAME = "ZOO_LOG_LEVEL"


@six.add_metaclass(classtypes.Singleton)
class CentralLogManager(object):
    """This class is a singleton object that globally handles logging, any log added will managed by the class.
    """

    def __init__(self):
        self.logs = {}  # type: dict[str, logging.Logger]
        self.jsonFormatter = "%(asctime) %(name) %(processName) %(pathname)  %(funcName) %(levelname) %(lineno) %(" \
                             "module) %(threadName) %(message)"
        self.rotateFormatter = "%(asctime)s: [%(process)d - %(name)s - %(levelname)s]: %(message)s"
        self.shellFormatter = "[%(name)s - %(module)s - %(funcName)s - %(levelname)s]: %(message)s"
        self.guiFormatter = "[%(name)s]: %(message)s"

    def addLog(self, logger):
        """Adds logger to this manager instance

        :param logger: the python logger instance.
        :type logger: :class:`logging.Logger`
        """
        if logger.name not in self.logs:
            self.logs[logger.name] = logger
        globalLogLevelOverride(logger)

    def removeLog(self, loggerName):
        """Remove's the logger instance by name

        :param loggerName: The logger instance name.
        :type: loggerName: str
        """
        if loggerName in self.logs:
            del self.logs[loggerName]

    def changeLevel(self, loggerName, level):
        """Changes the logger instance level.

        :param loggerName: The logger instance name.
        :type loggerName: str
        :param level: eg. logging.DEBUG.
        :type level: int
        """
        if loggerName in self.logs:
            log = self.logs[loggerName]
            if log.level != level:
                log.setLevel(level)

    def addRotateHandler(self, loggerName, filePath):
        """Add a rotating file handler to the logger with the specified name.

        :param loggerName: The name of the logger to which the handler will be added.
        :type loggerName: str
        :param filePath: The path to the log file to which the handler will write.
        :type filePath: str
        :return: The file handler object that was added to the logger.
        :rtype: logging.handlers.RotatingFileHandler or None
        """
        logger = self.logs.get(loggerName)
        if not logger:
            return

        handler = logging.handlers.RotatingFileHandler(filePath, maxBytes=1.5e6, backupCount=5)
        handler.setFormatter(logging.Formatter(self.rotateFormatter))
        logger.addHandler(handler)
        return handler

    def addShellHandler(self, loggerName):
        """Add a stream handler to the logger with the specified name that outputs to the shell.

        :param loggerName: The name of the logger to which the handler will be added.
        :type loggerName: str
        :return: The stream handler object that was added to the logger.
        :rtype: logging.StreamHandler or None
        """
        logger = self.logs.get(loggerName)
        if not logger:
            return
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(self.shellFormatter))
        logger.addHandler(handler)
        return handler

    def addNullHandler(self, loggerName):
        """Add a null handler to the logger with the specified name.

        :param loggerName: The name of the logger to which the handler will be added.
        :type loggerName: str
        :return: The null handler object that was added to the logger.
        :rtype: logging.NullHandler or None
        """
        logger = self.logs.get(loggerName)
        if not logger:
            return
        # Create an null handler
        handler = logging.NullHandler()
        # Create a logging formatter
        formatter = logging.Formatter(self.shellFormatter)
        # Assign the formatter to the io_handler
        handler.setFormatter(formatter)
        # Add the io_handler to the logger
        logger.addHandler(handler)
        return handler

    def addHandler(self, loggerName, handler):
        """
        :param loggerName:
        :param handler:
        :type handler: :class:`logging.StreamHandler`
        """
        log = self.logs.get(loggerName)
        if log is None:
            return
        formatter = logging.Formatter(self.shellFormatter)
        handler.setFormatter(formatter)
        log.addHandler(handler)

        return handler

    def removeHandlers(self, loggerName):
        log = self.logs.get(loggerName)
        if log is None:
            return False
        log.handlers = []  # could do clear() but py etc compat
        return True


def logLevels():
    """Returns a Map of stdlib logging levels.

    :rtype: Iterable[str]
    """
    return map(logging.getLevelName, range(0, logging.CRITICAL + 1, 10))


def levelsDict():
    """Returns the stdlib logging levels as a dict.

    The keys are the formal logging names and values are the logging constant value.

    :rtype: dict[str: int]
    """
    return {logging.getLevelName(i): i for i in range(0, logging.CRITICAL + 1, 10)}


def getLogger(name):
    """Returns the Zoo tools log name in the form of 'zootools.*.*'

    This is to ensure consistent logging names across all applications

    :param name: The logger name to format.
    :type name: str
    :return:
    :rtype: :class:`logging.Logger`
    """

    if name == CENTRAL_LOGGER_NAME:
        name = CENTRAL_LOGGER_NAME
    elif name.startswith("zoo."):
        name = ".".join((LOG_PREFIX, name[4:]))
    elif name.startswith("preferences."):
        name = ".".join((LOG_PREFIX, "preferences", name[len("preferences."):]))
    logger = logging.getLogger(name)
    CentralLogManager().addLog(logger)
    return logger


def globalLogLevelOverride(logger):
    """Override a logger's logging level with the value of an environment variable.

    :param logger: The logger object to override the logging level for.
    :type logger: logging.Logger
    """
    globalLoggingLevel = os.environ.get(LOG_LEVEL_ENV_NAME, "INFO")
    envLvl = logging.getLevelName(globalLoggingLevel)
    currentLevel = logger.getEffectiveLevel()

    if not currentLevel or currentLevel != envLvl:
        logger.setLevel(envLvl)


def reloadLoggerHierarchy():
    """Reload the hierarchy of the logging system by removing and re-adding loggers to their parents."""
    for log in logging.Logger.manager.loggingDict.values():
        if hasattr(log, "children"):
            del log.children
    for name, log in logging.Logger.manager.loggingDict.items():
        if not isinstance(log, logging.Logger):
            continue
        try:
            if log not in log.parent.children:
                log.parent.children.append(log)
        except AttributeError:
            log.parent.children = [log]


def iterLoggers():
    """Iterates through all zootools loggers.

    :return: generator(str, logging.Logger)
    """
    for name, logObject in sorted(logging.root.manager.loggerDict.items()):
        if name.startswith("zoo."):
            yield name, logObject


def rootLogger():
    """Retrieves the top most zootools logger instance in the zoo hierarchy
    """
    return logging.root.getChild("zootools")


def setGlobalDebug(state):
    """Toggles the root zoo tools logger between DEBUG and INFO
    """
    rootLog = rootLogger()
    if state:
        rootLog.setLevel(logging.DEBUG)
        os.environ[LOG_LEVEL_ENV_NAME] = "DEBUG"
        rootLog.info("{} has been set to debug mode".format(rootLog.name))
    else:
        rootLog.setLevel(logging.INFO)
        os.environ[LOG_LEVEL_ENV_NAME] = "INFO"
        rootLog.info("{} has been set to Info mode".format(rootLog.name))


def isGlobalDebug():
    """Returns whether the zootools logging level is set to DEBUG.

    :rtype: bool
    """
    return os.environ.get(LOG_LEVEL_ENV_NAME, "INFO") == "DEBUG"


zooLogger = getLogger(CENTRAL_LOGGER_NAME)
# to avoid log messages propagating upwards in the
# log hierarchy.
zooLogger.propagate = False
handlers = zooLogger.handlers
if not handlers:
    CentralLogManager().addShellHandler(zooLogger.name)
