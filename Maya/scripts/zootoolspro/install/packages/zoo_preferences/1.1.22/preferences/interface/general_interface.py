import json
import os

from zoo.preferences.core import prefinterface
from zoo.libs.utils import output


class GeneralPreferences(prefinterface.PreferenceInterface):
    id = "general_interface"
    _relativePath = "prefs/maya/general_settings.pref"

    def primaryRenderer(self):
        """ Primary Renderer

        :return:
        :rtype: basestring
        """
        return self.settings()['primaryRenderer']

    def setPrimaryRenderer(self, renderer):
        self.settings()['primaryRenderer'] = renderer
        self.saveSettings(indent=True)

    def autoLoadPlugin(self):
        """ Auto Load Plugin

        :return:
        :rtype: bool
        """
        # local import because zoo_preferences gets loaded outside of maya at times.
        # this will change when we bring HostEngines into play
        startupPrefsPath = pluginPath()
        try:
            with open(startupPrefsPath, "r") as f:
                prefs = json.load(f)
            return prefs.get("autoload", False)
        except ValueError as er:
            output.displayError("Unable to load zootools startup file")
        return True

    def setAutoLoad(self, state):
        startupPrefsPath = pluginPath()
        try:
            with open(startupPrefsPath, "r") as f:
                prefs = json.load(f)
            prefs["autoload"] = state
            with open(startupPrefsPath, "w") as f:
                json.dump(prefs, f, indent=4)
            return True
        except ValueError as er:
            output.displayError("Unable to load zootools startup file")
        return False


def pluginPath():
    from maya import cmds
    pluginFolder = os.path.dirname(cmds.pluginInfo("zootools", path=True, q=True))
    return os.path.join(os.path.dirname(pluginFolder), "zootools_maya_startup.json")
