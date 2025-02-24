import copy

from zoo.core.util import typing

from zoo.core.util import zlogging
from zoo.preferences import constants, errors

logger = zlogging.getLogger(__name__)

if typing.TYPE_CHECKING:
    import zoo.core.tooldata.tooldata.SettingObject
    import zoo.preferences.core.PreferenceManager


class PreferenceInterface(object):
    """Preference interface class which is responsible for interfacing to .pref files within zoo.

    PreferenceInterface shouldn't be instanced directly but through
    :class:`zoo.preferences.core.PreferenceManager` instance.

    It's the intention for interface subclasses to handle creating and manipulating one
    or more .pref belonging to the installed zoo package.
    As a general rule of thumb the interface shouldn't manipulate a .pref outside it's
    own package but can request it from the external interface
    via self.preference.interface() method however do this at your own risk.

    The .pref internal data structure may change over the life of zootools so it is
    recommended that the interface provides the necessary methods to handle manipulating
    the data structure over the client directly making the changes.

    See :class:`preference.interface.preference_interface.ZooToolsPreference` for
    example usage.
    """
    # the unique identifier for the interface which will be used for lookup by
    # client code and for registry
    id = ""
    _relativePath = ""
    _settings = None

    def __init__(self, preference):
        """
        :param preference: The main zoo preference manager
        :type preference: :class:`zoo.preferences.core.PreferenceManager`
        """
        self.preference = preference  # type: zoo.preferences.core.PreferenceManager
        self._revertSettings = None  # type: zoo.core.tooldata.tooldata.SettingObject

    def settings(self, relativePath=None, root=None, name=None, refresh=False):
        """

        :param relativePath: eg. interface/stylesheet
        :type relativePath: str
        :param root: The root name to search, if None then all roots will be searched until the relativePath is found.
        :param name: The key within the nested "settings" dict within the file.
        :type name: str or None
        :param refresh: Whether or not to re-cache the queried settings back on this interface instance.
        :type refresh: bool
        :return: the settings value usually a standard python type
        :rtype: :class:`zoo.core.tooldata.tooldata.SettingObject`
        """
        relativePath = relativePath or self._relativePath
        if self._settings is None or refresh:
            self._settings = self.preference.findSetting(relativePath,
                                                         root=root)

        if name is not None:
            settings = self._settings.get(constants.SETTINGS_DEF_KEY, {})
            if name not in settings:
                raise errors.SettingsNameDoesntExistError(
                    "Failed to find setting: {} in file: {}".format(name, relativePath))
            return settings[name]
        self._setupRevert()
        return self._settings

    def refreshSettings(self):
        """ Refreshes the settings

        :return:
        """
        self.settings(refresh=True)

    def saveSettings(self, indent=True, sort=False):
        """ Save the settings

        :param indent: Add indent to the json file that will be saved
        :param sort: Sort the json file alphabetically
        :return:
        """
        logger.debug("Save settings for PreferenceInterface: '{}'".format(self))
        ret = self.settings().save(indent, sort)
        self._revertSettings = None
        return ret

    def _setupRevert(self):
        """ Set up revert settings.
        Only revert if _revertSettings has been cleared. Currently only cleared on settings saved.

        :return:
        """
        if not self._revertSettings:
            self._revertSettings = copy.deepcopy(self._settings)

    def settingsValid(self):
        """ Returns true if setting is valid. False otherwise
        """
        return self.settings().isValid()

    def refresh(self):
        """ Force a refresh

        :return:
        :rtype:
        """
        self.settings(refresh=True)

    def revertSettings(self):
        """ Revert the settings back to the previous settings

        :return:
        """
        if self._revertSettings:
            self._settings.clear()
            self._settings.update(self._revertSettings)
            self.saveSettings()



