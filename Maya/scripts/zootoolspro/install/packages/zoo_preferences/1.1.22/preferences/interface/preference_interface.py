import os

from zoovendor.Qt import QtCore

from zoo.libs.pyqt import stylesheet, utils
from zoo.libs.utils import color, filesystem, path
from zoo.core.util import zlogging
from zoo.preferences import prefinterface, preferencesconstants
from zoo.core import api
from zoovendor.six import string_types

from zoo.preferences.themedict import ThemeDict

logger = zlogging.getLogger(__name__)


class UpdateThemeEvent(object):
    def __init__(self, stylesheet, themeDict, preference):
        """ Update theme event

        :param stylesheet:
        :type stylesheet: str
        :param themeDict:
        :type themeDict: :class:`zoo.preferences.themedict.ThemeDict`
        :param preference:
        :type preference: :class:`ZooToolsPreference`
        """
        self.theme = None
        self.stylesheet = stylesheet
        self.themeDict = themeDict
        self.pref = preference


class ZooToolsPreference(prefinterface.PreferenceInterface):


    class ThemeUpdater(QtCore.QObject):
        """ Sends a signal when the theme is set. Allows widget-specific theme changes """
        update = QtCore.Signal(UpdateThemeEvent)  # stylesheet, themeDict, ZooToolsPreference

    # the unique identifier on which to be referred to in the registry
    id = "core_interface"
    # internal use only,  relative path from the root directories
    # for the stylesheet.pref file
    _relativePath = "prefs/global/stylesheet.pref"
    _preference_roots_path = "env/preference_roots.config"
    # internal use only, zoo preference package name
    _packageName = "zoo_preferences"
    _settings = None
    _themeUpdate = ThemeUpdater()

    def __init__(self, preference):
        """Main interface for zoo preferences. This class shouldn't be
            instanced directly but through the PreferenceManager instance.
        """
        super(ZooToolsPreference, self).__init__(preference=preference)

    @property
    def themeUpdated(self):
        """ Emits the theme and dictionary

        :return:  (theme, themeDict)
        :rtype:
        """

        return self._themeUpdate.update

    def emitUpdateSignal(self, styleSheet, themeDict):
        """ Do a manual update for the widgets that require it

        :param styleSheet:
        :type styleSheet:
        :param themeDict:
        :type themeDict: :class:`preferences.interface.themedict.ThemeDict`
        :return:
        :rtype:
        """

        self.themeUpdated.emit(UpdateThemeEvent(styleSheet, themeDict, self))

    def currentTheme(self):
        """Returns the current theme name for zootools.

        :return: The style sheet theme name
        :rtype: str
        """
        return self.preference.findSetting(self._relativePath, root=None, name="current_theme")

    def defaultPreferencesPath(self):
        return "~/zoo_preferences"

    def themes(self):
        """Returns the themes as a list

        :return: The style sheet theme name
        :rtype: str
        """
        return self.preference.findSetting(self._relativePath, root=None, name="themes").keys()

    def forceRefresh(self):
        """ Force a refresh

        :return:
        :rtype:
        """
        self._settings = None
        self.settings()

    def stylesheet(self, theme=None):
        """Loads and returns the stylesheet string

        :param theme: Themes name
        :type theme: basestring
        :return: The final composed stylesheet
        :rtype: :class:`zoo.libs.pyqt.stylesheet.StyleSheet`
        """
        if theme is None:
            theme = self.currentTheme()
        return self.stylesheetForTheme(theme)

    def stylesheetSetting(self, key, theme=None):
        """ Get one specific setting from a theme in the stylesheet.

        :param key: A key from the theme eg "$BTN_BACKGROUND_COLOR"
        :type key: str
        :param theme: Leave none to use default
        :type theme: str or None
        :return: The key value
        :rtype: str or tuple
        """
        try:
            settings = self.settings()['settings']
            theme = theme or settings['current_theme']
            ret = settings['themes'][theme].get(key)
        except KeyError:
            logger.error("Incorrectly formatted stylesheet: {}".format(self._relativePath))
            raise

        if ret is None:
            self.preference.defaultPreferenceSettings(self._packageName, self._relativePath)

        return ret

    def stylesheetSettingColour(self, key, theme=None):
        """ Return colour setting from current theme

        :param key: Get key eg '$EMBED_WINDOW_BORDER_COL'
        :param theme: from theme
        :return: Tuple(r,g,b)
        :rtype: tuple(float,float,float)
        """
        return color.hexToRGB(self.stylesheetSetting(key, theme))

    def revertThemeToDefault(self, theme=None, save=True):
        """ Reverts current theme to default

        :return:
        :rtype:
        """
        default = self.preference.defaultPreferenceSettings("zoo_preferences", "global/stylesheet")
        defaultTheme = default["settings"]["themes"][self.currentTheme()]
        userTheme = self.settings()["settings"]["themes"][self.currentTheme()]
        userTheme.update(defaultTheme)
        if save:
            self.settings().save(indent=True, sort=True)

    def __getattr__(self, item):
        """ Retrieve the current theme's key value

        :param item:
        :return:
        """

        setting = self.stylesheetSetting("$" + item)

        if setting is None:
            return super(ZooToolsPreference, self).__getattribute__(item)
        # Return the int value by itself
        elif isinstance(setting, int):
            return setting
        # May cause problems if stylesheet.pref has strings that arent colours
        elif isinstance(setting, string_types):
            if setting.startswith('^'):  # apply dpiScaling for '^' prefixed strings
                return utils.dpiScale(int(setting[1:]))

            if len(setting) in (3, 6, 8):  # Hex number
                return color.hexToRGBA(setting)

        return super(ZooToolsPreference, self).__getattribute__(item)

    def stylesheetForTheme(self, theme):
        """Return stylesheet from theme.

        :param theme: theme eg "dark" or "maya-toolkit"
        :type theme: str
        :rtype: :class:`zoo.libs.pyqt.stylesheet.StyleSheet`
        """

        data = self.themeDict(theme)
        if data is None:
            raise ValueError("Current styleSheet theme doesn't exist, Theme:{}".format(theme))
        return self.stylesheetFromData(data)

    def themeDict(self, theme):
        """ Retrieve the theme dict found in the stylesheet.pref for the corresponding theme

        The return usually looks like the following::

            themeDict = {
                            '$BROWSER_BG_COLOR': '1A1A1A',
                            '$BROWSER_BG_SELECTED_COLOR': '5E5E5E',
                            ...
                        }

        :param theme:
        :type theme:
        :return:
        :rtype: dict
        """
        stylePrefs = self.preference.findSetting(self._relativePath, root=None)
        if not stylePrefs:
            stylePrefs = self.preference.defaultPreferenceSettings(self._packageName, self._relativePath)

        themes = stylePrefs["settings"]["themes"]
        data = themes.get(theme)
        themeDict = ThemeDict(theme, data)
        return themeDict

    def stylesheetFromData(self, data):
        """ Generate stylesheet from data.

        Data is the dict usually from stylesheet.pref under one of the themes::

            {
                "$EMBED_WINDOW_BG": "2a2a2a",
                "$EMBED_WINDOW_BORDER_COL": "3c3c3c",
                "$DEBUG_1": "ff0000",
                "$DEBUG_2": "0012ff",
                "$TEAROFF_LINES": "AAAAAA"
            }

        :param data: Data is the dict usually from stylesheet.pref under one of the themes
        :type data: dict
        :return: :class:`zoo.libs.pyqt.stylesheet.StyleSheet`
        """
        preferenceLocation = preferencesconstants.__file__
        stylePath = os.path.join(os.path.dirname(preferenceLocation), "zootools_style.qss")
        return stylesheet.StyleSheet.fromPath(stylePath, **data)

    def bakePreferenceRoots(self):
        """ Bake Preference Roots
        Bakes the Preferences root paths and names to zootoolspro/config/env/preferences_root.config

        """
        rootConfig = api.currentConfig().preferenceRootsPath()
        rootPaths = {rootName: str(rootObject) for rootName, rootObject in self.preference.roots.items()}
        filesystem.saveJson(rootPaths, rootConfig)

    def defaultPreferencePath(self):
        return self.preference.defaultPreferencePath()

    def prefsPath(self):
        return self.preference.prefsPath()

    def assetPath(self):
        return self.preference.assetPath()

    def assetFolder(self, folder=""):
        """Returns the default folder paths as created from the global user preferences directory

        Example::

            assetFolder("model_assets")
            # Output: userPath/zoo_preferences/assets/model_assets


        :type folder: str
        :param folder: The folder to get within the asset path
        :return: The full path of the userPreferences + assets directory + model assets directory
        :rtype: str
        """
        return path.normpath(os.path.join(self.assetPath(), folder))

    def userPreferences(self):
        """ Get user preferences

        Retrieves the path to the Zoo Tools User Preferences,
        if '~/zoo_preferences' then displays full path

        :return:
        """


        return os.path.normpath(str(self.preference.root("user_preferences")))
