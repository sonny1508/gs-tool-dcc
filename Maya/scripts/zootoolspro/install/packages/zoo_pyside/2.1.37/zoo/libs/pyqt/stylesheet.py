import os
from zoovendor.Qt import QtGui
from zoovendor import six

from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.core.util import zlogging
from zoovendor.six import string_types

logger = zlogging.getLogger(__name__)

INT = 0
DPI_SCALE = 1
ICON = 2
COLOR = 3

loadedFonts = []


class StyleSheet(object):
    """

    .. code-block:: python

        styleSheetStr = "QToolTip{background - color: rgb(BACK_COLOR_R, BACK_COLOR_G, BACK_COLOR_B);\"
                         "color: black;border: blacksolid 1px;margins: 2px;}"
        settings = {"BACK_COLOR_R": 251, "BACK_COLOR_G": 15, "BACK_COLOR_B": 10}
        sheet = StyleSheet(styleSheetStr)
        sheet.format(settings)
        print(sheet.data)
        # result
        # QToolTip {
        #     background-color: rgb(251, 15, 10);
        #     color: black;
        #     border: black solid 1px;
        #     margins: 2px;
        # }

    """

    @classmethod
    def fromPath(cls, path, **kwargs):
        """

        :param path: The style stylesheet css file
        :type path: str
        :param kwargs: The settings to replace in the style sheet
        :type kwargs: dict
        :rtype: :class:`StyleSheet`
        """

        with open(path, "r") as f:
            styleSheet = cls(f.read())
        if kwargs:
            styleSheet.format(kwargs)

        return styleSheet

    def __init__(self, styleSheet=None):
        self.data = styleSheet or u""
        self.originalData = six.text_type(styleSheet)

    def __repr__(self):
        return str(self.data)

    def format(self, settings):
        """Formats the stylesheet str with the settings

        :param settings: A dict containing the str to replace and the value to replace with eg. {"BACK_COLOR_R": 251}
        :type settings: dict
        :return: True if successfully formatted
        :rtype: bool
        """
        if not self.data:
            return False

        data = six.text_type(self.data)

        items = reversed(sorted(list(settings.items()), key=lambda x: len(x[0])))  # sort by length, largest first
        for key, value in items:
            if valueType(value) == DPI_SCALE:
                value = six.text_type(utils.dpiScale(int(value[1:])))

            elif valueType(value) == ICON:
                path = iconlib.iconPathForName(value[5:])

                if path == "":
                    logger.warning("Warning: \"{}\" icon not found for key: \"{}\" in stylesheet.pref"
                                   .format(value[5:], key))

                value = os.path.normcase(path).replace("\\", "/")
            data = data.replace(key, six.text_type(value))
        self.data = data
        return True


def valueType(value):
    """
    Returns type of value for the stylesheet.pref key value

    :param value:
    :return:
    """
    if isinstance(value, int):
        return INT
    elif isinstance(value, string_types):
        if len(value) == 6 or len(value) == 8:
            return COLOR
        elif value[0] == '^':
            return DPI_SCALE

        elif len(value) > 5 and value[:5] == 'icon:':
            return ICON


def stylesheetFromDirectory(directory, name):
    """Recursively searches directory until the name.css file is found and a :class:`Stylesheet` instance is returned

    :param directory: The absolute path to the directory to search
    :type directory: str
    :param name: the file name to find
    :type name: str
    :return: The style sheet instance or None if no matching file is found
    :rtype: tuple(:class:`StyleSheet`, str)
    """
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".css") and f.startswith(name):
                path = os.path.join(root, f)
                return StyleSheet.fromPath(path), path


def stylesheetsFromDirectory(directory):
    """Recursively searches the directory for all .css files and returns :class:`StyleSheet` instances and file paths

    :param directory: The absolute path to the directory to search
    :type directory: str
    :return:
    :rtype: list(tuple(:class:`StyleSheet`, str))
    """
    sheets = list()
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".css"):
                path = os.path.join(root, f)
                sheets.append((StyleSheet.fromPath(path), path))
    return sheets


def loadFonts(fontPaths):
    """Loads the given '.ttf' font files into the QtGui.QFontDatabase

    :param fontPaths: A list of font files
    :type fontPaths: list(str)
    :return: the list of registered font ids from Qt
    :rtype: list(str)
    """
    # Use normal python instead because Qt locks up the ttf even if removeFonts is called for 2020
    fontIds = []
    for path in fontPaths:
        with open(path, 'rb') as f:
            fontIds.append(QtGui.QFontDatabase.addApplicationFontFromData(f.read()))
    return fontIds


def unloadFonts():
    """ Unload all loaded zoo fonts

    :return:
    """
    global loadedFonts
    for f in loadedFonts:
        QtGui.QFontDatabase.removeApplicationFont(f)


def loadDefaultFonts():
    """
    Loads the zoo core default fonts paths.

    :note: this only needs to be run once per QApplication
    """
    # load the zoo fonts
    global loadedFonts
    fontPath = os.path.join(os.path.dirname(__file__), "fonts")
    loadedFonts = loadFonts([os.path.join(fontPath, fontFile) for fontFile in os.listdir(fontPath)])
