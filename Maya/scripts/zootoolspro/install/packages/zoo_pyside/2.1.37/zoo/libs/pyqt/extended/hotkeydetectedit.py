from zoovendor.Qt import QtCore, QtGui, QtWidgets
from zoo.libs import iconlib
from zoo.libs.pyqt import utils, keyboardmouse
from zoo.libs.pyqt.widgets.searchwidget import SearchLineEdit


class HotkeyDetectEdit(SearchLineEdit):
    hotkeyEdited = QtCore.Signal()

    def __init__(self, text="", parent=None, prefix="", suffix="", iconsEnabled=False, searchIcon="key"):
        """ A line Edit which detects key combinations are being pressed(for hotkeys for instance).

        Usage: It works similarly to a QLineEdit. Type in a hotkey combination to show the hotkey.

        Example::

            # eg Type in Ctrl+Alt+P and it would set the text of the QLineEdit to "Ctrl+Alt+P"
            wgt = HotkeyDetectEdit()

        :param text:
        :param parent:
        :param prefix:
        :param suffix:
        """

        super(HotkeyDetectEdit, self).__init__(parent=parent,
                                               searchPixmap=iconlib.iconColorized(searchIcon, utils.dpiScale(16),
                                                                                  (128, 128, 128)),
                                               iconsEnabled=iconsEnabled)
        self.disabledKeys = ("backspace", "del", "esc")
        self.prefix = prefix
        self.suffix = suffix

        self.setText(text)
        self.backspaceClears = True

    def setText(self, text, resetCursor=True):
        """ Set text of HotKeyEdit

        :param text:
        :param resetCursor:
        :return:
        """
        text = self.prefix + text + self.suffix

        super(HotkeyDetectEdit, self).setText(text)

        if resetCursor:
            self.setCursorPosition(0)

    def keyPressEvent(self, e):
        """ Update the text edit to whatever the hotkey is inputted

        For example type in Ctrl+Alt+P and it would set the text of the QLineEdit to "Ctrl+Alt+P"

        :param e:
        :return:
        """
        seq = keyboardmouse.eventKeySequence(e)
        keyStr = seq.toString()
        if not keyStr:
            return
        if not self.isKeySupported(keyStr):
            keyStr = ""

        self.setText(keyStr)

        self.hotkeyEdited.emit()

    def isKeySupported(self, key):
        return not any(i in key.lower() for i in self.disabledKeys)

    def convertSpecChars(self, charInt):
        """ Converts special characters back to the original keyboard number

        :param charInt:
        :return:
        """
        if charInt in self.specialkeys:
            return self.specialkeys[charInt]
        return charInt
