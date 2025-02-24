from zoo.libs.pyqt import utils
from zoo.libs.utils import color
from zoovendor.six import string_types


class ThemeDict(dict):
    """ Theme Dict """
    name = ""

    def __init__(self, name='', dct=None):
        self.name = name
        super(ThemeDict, self).__init__(dct or {})

    def __getattr__(self, item):
        """ Retrieve the current theme's key value

        :param item:
        :return:
        """

        setting = self.get('$'+item)

        # Return the int value by itself
        if isinstance(setting, int):
            return setting
        # May cause problems if stylesheet.pref has strings that aren't colours
        elif isinstance(setting, string_types):
            if setting.startswith('^'):  # apply dpiScaling for '^' prefixed strings
                return utils.dpiScale(int(setting[1:]))

            if len(setting) in (3, 6, 8):  # Hex number
                return color.hexToRGBA(setting)

        return super(ThemeDict, self).__getattribute__(item)