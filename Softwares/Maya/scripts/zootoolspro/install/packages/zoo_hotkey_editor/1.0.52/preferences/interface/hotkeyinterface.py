from zoo.preferences.core import prefinterface

# 1. Rename filename
# 2. Set _relativePath to the location of your pref file


class HotkeyPreferences(prefinterface.PreferenceInterface):
    id = "hotkeys"
    _relativePath = "prefs/maya/example.pref"
    """
    Usage:
        from zoo.preferences.core import preference
        pref = preference.interface("example_interface")
        pref.exampleSetting()
    """

    def exampleSetting(self):
        """ Returns 'exampleSetting'

        For example: In zoo_example_custom_tools/prefs/maya/example.pref

        {
          "exampleSetting": "HelloWorld",
          "largeSetting": {
            "shaderPresetsFolder": "",
            "shaderPresetsUniformIcons": true,
            "mayaShadersFolder": "",
            "mayaShadersUniformIcons": true
          }
        }
        It would return 'HelloWorld'

        :return:
        """
        return self.settings()['exampleSetting']