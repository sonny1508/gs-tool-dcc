from zoo.apps.toolpalette import palette
from zoo.core.engine import currentEngine
from zoo.apps.preferencesui import preferencesui


class PreferencesUi(palette.ActionPlugin):
    id = "zoo.preferencesui"
    creator = "Dave Sparrow"
    tags = ["preference"]
    uiData = {"icon": "menu_zoo_preferences",
              "tooltip": "Zoo Tools Preferences",
              "label": "Zoo Tools Preferences: \nOpens the Zoo Preferences Window.",
              "color": "",
              "backgroundColor": "",
              "multipleTools": False,
              "dock": {"dockable": True, "tabToControl": ("AttributeEditor", -1), "floating": False}
              }

    def execute(self, *args, **kwargs):
        engine = currentEngine()
        return engine.showDialog(windowCls=preferencesui.PreferencesUI,
                                 name="PreferencesUI",
                                 allowsMultiple=False)
