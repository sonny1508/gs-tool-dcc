from zoo.apps.toolpalette import palette
from zoo.apps.toolsetsui import toolsetui
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class ToolsetType(palette.PluginTypeBase):
    id = "toolset"

    def __init__(self, toolPalette):
        super(ToolsetType, self).__init__(toolPalette)
        from zoo.apps.toolsetsui import registry  # temp local
        self._toolsetRegistry = registry.ToolsetRegistry()

    def plugins(self):
        for p in self._toolsetRegistry._manager.plugins.keys():
            yield p

    def pluginUiData(self, pluginId, overrides=None):
        uiData = {}
        try:
            p = self._toolsetFromId(pluginId)
            uiData.update(p.uiData)
            uiData["clsName"] = p.__class__.__name__
            uiData["iconColor"] = self._toolsetRegistry.toolsetColor(pluginId)
        except AttributeError:
            logger.warning("Missing Toolset plugin: {}".format(pluginId))
        finally:
            uiData.update(overrides or {})
            return uiData

    def executePlugin(self, pluginId, *args, **kwargs):
        actionClass = self.toolPalette.typeRegistry.getPlugin("action")

        kwargs["toolsetIds"] = [pluginId]
        toolOpened = toolsetui.runToolset(pluginId, logWarning=False)
        if not toolOpened:
            return actionClass.executePlugin("zoo.toolsets", *args, **kwargs)

    def generateCommand(self, pluginId, arguments):
        # returns a list of dict
        args = arguments or {}
        args["pluginId"] = pluginId
        actionClass = self.toolPalette.typeRegistry.getPlugin("action")

        command = actionClass.commandString.format(args)
        cmd = palette.ItemCommand(pluginId, arguments=args)
        cmd.string = command
        return cmd

    def shutdown(self):
        pass

    def _toolsetFromId(self, toolId):
        """ Finds and returns a toolset class.

        :param toolId: The toolset id value
        :type toolId: str
        :return:
        :rtype:
        :note: toolset raises a key error, but we ignore it here and just log a warning
        this way the menus and shelf continue to build but skips creating actions.
        :note: if an Import error occurs it's because toolsets isn't part of the environment
        and someone left a toolset in the env.
        """
        try:
            return self._toolsetRegistry.toolset(toolId)
        except KeyError:
            logger.warning("Missing Toolset by id: {}".format(toolId),
                           exc_info=True)