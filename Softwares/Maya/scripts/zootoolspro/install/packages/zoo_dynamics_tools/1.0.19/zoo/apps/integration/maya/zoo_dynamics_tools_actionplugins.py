from zoo.apps.toolpalette import palette


class DynamicsIconShelf(palette.ActionPlugin):
    id = "zoo.shelf.dynamics"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "fxDynamicsMenu_shlf",
              "label": "Dynamics Menu",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        pass