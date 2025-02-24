from zoo.apps.toolpalette import palette
from zoo.apps.toolsetsui import run


class ToolsetsUi(palette.ActionPlugin):
    id = "zoo.toolsets"
    creator = "Keen Foong"
    tags = ["tools", "toolsets"]
    uiData = {"icon": "menu_toolsets",
              "tooltip": "Toolsets Window for tool browsing",
              "label": "Toolsets",
              "color": "",
              "backgroundColor": "",
              }

    def execute(self, *args, **kwargs):
        toolArgs = kwargs or {}
        return run.launch(toolArgs=toolArgs)
