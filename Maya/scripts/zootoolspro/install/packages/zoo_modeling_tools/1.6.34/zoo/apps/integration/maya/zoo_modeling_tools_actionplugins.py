from zoo.apps.toolpalette import palette
from zoo.libs.maya.cmds.hotkeys import definedhotkeys


class ModelingIconShelf(palette.ActionPlugin):
    id = "zoo.shelf.modeling"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "modelingMenu_shlf",
              "label": "Modeling Tools: \nTools related to polygon modelling.",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        name = kwargs["variant"]
        if name == "createZbrushGrid":
            from zoo.libs.maya.cmds.modeling import create
            create.createZBrushGridPlaneSize()
        elif name == "quadPatcher":
            definedhotkeys.open_quadPatcher()