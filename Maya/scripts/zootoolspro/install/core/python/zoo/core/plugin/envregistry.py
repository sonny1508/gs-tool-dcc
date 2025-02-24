import os
from zoo.core.plugin import pluginmanager
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class EnvRegistry(object):
    """ Registry class to register paths based on an environment variable. Should be overridden.

    Usage: Override

    """
    registryEnv = ""
    interface = None
    variableName = None

    def __init__(self):
        """
        """
        self.classes = []

        if self.interface is None:
            logger.error("{}.interface must not be none."
                         " Should be the class that the Registry is looking for.".format(self))

        self._manager = pluginmanager.PluginManager(interface=[self.interface], variableName=self.variableName)

    def discover(self):
        """ Searches for the classes in the environment variable in the registryEnv paths
        """
        if self.registryEnv == "":
            logger.error("{}.registryEnv must have an environment variable value".format(self))
            return False
        self.classes = []
        paths = os.environ[self.registryEnv].split(os.pathsep)
        if not paths:
            return False
        self._manager.registerPaths(paths)

        self.classes = list(self._manager.plugins.values())
        self.initPlugins(self.classes)

        return True

    def initPlugins(self, classes):
        """ To be overridden

        :param classes:
        :return:
        """
        pass
