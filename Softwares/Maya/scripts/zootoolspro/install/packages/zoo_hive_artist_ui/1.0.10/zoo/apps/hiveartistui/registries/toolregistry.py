from zoo.apps.hiveartistui import hivetool
from zoo.core.plugin import pluginmanager
from zoo.core.util import zlogging
from zoovendor.Qt import QtCore

logger = zlogging.getLogger("hiveartistui")


class ToolRegistry(QtCore.QObject):
    """ Registry to handle getting the hive tools

    """
    toolenv = "HIVE_UI_TOOLS"

    def __init__(self):
        """ Hive tool registry
            
        """
        super(ToolRegistry, self).__init__()
        self.hiveTools = {}
        # for discovering the component models
        self._manager = pluginmanager.PluginManager(interface=[hivetool.HiveTool], variableName="id")
        self.reload()

    def reload(self):
        self._manager.plugins = {}
        self._manager.registerByEnv(self.toolenv)

    def toolNames(self):
        return self._manager.plugins.keys()

    def iterTools(self):
        for i in self._manager.plugins.values():
            yield i

    def iterToolsFromLayout(self, layout):
        """ Iterate from layout. Layout being a list of hivetool id strings

        :param layout:
        :type layout: list[basestring]
        :return:
        :rtype: collections.Iterable[hivetool.HiveTool]
        """
        for toolId in layout:
            variantId = ""
            ids = toolId.split(":")
            if len(ids) > 1:
                variantId = ids[1]
            tId = ids[0]
            plugin = self._manager.getPlugin(tId)
            if plugin is None:
                if toolId == "---":
                    yield None, "SEPARATOR", None
                    continue
                logger.warning("Missing Requested Plugin: {}".format(toolId))
                continue
            yield plugin, "PLUGIN", variantId

    def plugin(self, toolId):
        """ Retrieves plugin based on tool id

        :param toolId:
        :type toolId:
        :return:
        :rtype: callable[:class:`zoo.apps.hiveartistui.hivetool.HiveTool`]
        """
        return self._manager.getPlugin(toolId)
