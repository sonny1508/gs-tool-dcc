from zoo.apps.toolsetsui import toolsetui
from zoo.core.engine import currentEngine


def launch(toolArgs=None, parent=None):
    """Load the artist GUI for hive.

    :param toolArgs:
    :type toolArgs:
    :return:
    :rtype: :class:`toolsetui.ToolsetsUI`
    """
    engine = currentEngine()

    toolArgs = toolArgs or {}

    toolsetIds = toolArgs.get("toolsetIds", [])
    position = toolArgs.get("position")
    win = engine.showDialog(windowCls=toolsetui.ToolsetsUI,
                            name="toolsets",
                            allowsMultiple=True,
                            iconColor=(231, 133, 255),
                            hueShift=10,
                            parent=parent,
                            toolsetIds=toolsetIds, position=position,
                            )
    return win


def toolsetSetMode(toolsetId, modeInt=1):
    """Change an open toolset tool to

        compact mode 0
        advanced mode 1

    :param toolsetId: The id of the toolset that is already open ie "shaderManager"
    :type toolsetId: str
    :param modeInt: compact mode is 0, advanced mode is 1
    :type modeInt:
    """
    ui = toolsetui.toolsetsById(toolsetId)
    ui[0].setCurrentIndex(modeInt)
    ui[0].displayModeButton.setIconIndex(modeInt+1)
    ui[0].treeWidget.updateTree(True)


def openToolset(toolsetId, position=None, advancedMode=False):
    """ Opens a tool given the toolset ID name

    :param toolsetId: The name of the toolset ID eg "cleanObjects" or "createTube" etc
    :type toolsetId: string
    """
    ret = toolsetui.runToolset(toolsetId, logWarning=False)
    if not ret:
        ret = launch(toolArgs={"toolsetIds": [toolsetId], "position": position})

    if advancedMode:
        toolsetSetMode(toolsetId, modeInt=1)
    return ret
