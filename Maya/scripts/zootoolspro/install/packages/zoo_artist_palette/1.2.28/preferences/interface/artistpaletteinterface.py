from zoo.preferences import prefinterface
from zoo.core.tooldata import tooldata


class ArtistPaletteInterface(prefinterface.PreferenceInterface):
    """Class that loads the Zoo Tools menu and main ZooToolsPro shelf at startup
    """
    _relativePath = "prefs/maya/artistpalette.pref"
    id = "artistPalette"

    def menuName(self):
        data = self.preference.findSetting(self._relativePath, root=None)
        return data["settings"]["menu_name"]

    def loadShelfAtStartup(self):
        return self.preference.findSetting(self._relativePath,
                                           root=None,
                                           name="load_shelf_at_startup")

    def setLoadShelfAtStartup(self, value):
        self.settings()["settings"]["load_shelf_at_startup"] = value
        return True

    def defaultShelf(self):
        try:
            return self.preference.findSetting(self._relativePath,
                                               root=None,
                                               name="default")
        except tooldata.InvalidSettingsPath:
            settings = self.preference.defaultPreferenceSettings("zoo_artist_palette", "prefs/maya/artistPalette")
            return settings.settings["default"]

    def isActiveAtStartup(self):
        try:
            return self.preference.findSetting(self._relativePath,
                                               root=None,
                                               name="isActiveAtStartup")
        except tooldata.InvalidSettingsPath:
            settings = self.preference.defaultPreferenceSettings("zoo_artist_palette", "prefs/maya/artistPalette")
            return settings.settings.get("isActiveAtStartup", False)

    def setShelfActiveAtStartup(self, value):
        self.settings()["settings"]["isActiveAtStartup"] = value
        return True
