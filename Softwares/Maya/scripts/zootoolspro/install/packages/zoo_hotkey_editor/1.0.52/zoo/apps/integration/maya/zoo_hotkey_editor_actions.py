from zoo.apps.toolpalette import palette


class HotkeyEditorUi(palette.ActionPlugin):
    id = "zoo.hotkeyeditorui"
    creator = "Keen Foong"
    tags = ["hotkey", "hotkeys", "editor"]
    uiData = {"icon": "menu_keyboard",
              "label": "Zoo Hotkey Editor",
              "tooltip": "Zoo Hotkey Editor: \nLoad, edit and create Zoo Tools hotkey sets.",
              "label": "Hotkey Editor"
              }

    def execute(self, *args, **kwargs):
        from zoo.apps.hotkeyeditor import hotkeyeditorui
        from zoo.core.engine import currentEngine

        engine = currentEngine()
        return engine.showDialog(windowCls=hotkeyeditorui.HotkeyEditorUI,
                                 name="HotkeyEditor",
                                 allowsMultiple=False)
