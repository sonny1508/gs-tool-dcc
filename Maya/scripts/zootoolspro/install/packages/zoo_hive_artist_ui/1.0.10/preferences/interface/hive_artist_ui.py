from zoo.preferences import prefinterface


class HiveArtistUiInterface(prefinterface.PreferenceInterface):
    id = "Hive.artist.ui"
    _relativePath = "prefs/maya/hive_artist_ui.pref"
    _packageName = "zoo_hive_artist_ui"
    
    def settings(self):
        data = self.preference.findSetting(self._relativePath, root=None)
        if not data:
            data = self.preference.defaultPreferenceSettings(self._packageName, self._relativePath)
        return data["settings"]

    def onOpenCreateRig(self):
        settings = self.settings()
        return settings.get("on_open_create_rig", False)

