from zoo.apps.toolpalette import palette
from zoo.libs.maya.cmds.hotkeys import definedhotkeys


class ModelingIconShelf(palette.ActionPlugin):
    id = "zoo.shelf.animation"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "animationMenu_shlf",
              "label": "Animation Tools: \n"
                       "Assorted tools for animation, setting & editing keyframes and the graph editor.",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        name = kwargs["variant"]
        if name == "studioLibrary":
            definedhotkeys.open_studioLibrary()
