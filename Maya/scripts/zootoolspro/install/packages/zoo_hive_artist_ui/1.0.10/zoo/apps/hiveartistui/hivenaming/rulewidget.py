import re

from zoo.libs.pyqt import keyboardmouse
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets, QtCore, QtGui


class CompleterStringEdit(elements.StringEdit):

    def __init__(self, label="", editText="", editPlaceholder="", buttonText=None, parent=None, editWidth=None,
                 labelRatio=1, btnRatio=1, editRatio=5, toolTip="", orientation=QtCore.Qt.Horizontal,
                 enableMenu=True, rounding=3):
        super(CompleterStringEdit, self).__init__(label, editText, editPlaceholder, buttonText, parent, editWidth,
                                                  labelRatio, btnRatio,
                                                  editRatio, toolTip, orientation, enableMenu, rounding)

    def _initEdit(self, editText, placeholder, parent, toolTip, editWidth, enableMenu, rounding=None):
        return CompleterLineEdit(editText, parent=parent, toolTip=toolTip, editWidth=editWidth)


class CompleterLineEdit(elements.LineEdit):
    def __init__(self, text="", parent=None, enableMenu=False, placeholder="", toolTip="", editWidth=None,
                 fixedWidth=None, menuVOffset=20):
        super(CompleterLineEdit, self).__init__(text, parent, enableMenu, placeholder, toolTip, editWidth, fixedWidth,
                                                menuVOffset)
        self._completer = None  # type: QtWidgets.QCompleter

    def completer(self):
        """

        :return:
        :rtype: :class:`QtWidgets.QCompleter`
        """
        return self._completer

    def setCompleter(self, completer):
        """

        :param completer:
        :type completer: :class:`QtWidgets.QCompleter`
        :return:
        :rtype:
        """
        if self._completer:
            self._completer.disconnect(self)
        self._completer = completer
        self._completer.setWidget(self)
        self._completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self._completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._completer.setFilterMode(QtCore.Qt.MatchContains)
        self._completer.activated.connect(self.insertCompletion)

    def insertCompletion(self, word):
        if self._completer.widget() != self:
            return
        compLen = len(self._completer.completionPrefix())
        self.insert(word[compLen:])

    def textUnderCursor(self):
        text = self.text()
        if not text:
            return text
        match = re.search(r"[a-zA-Z]+?(?=\s*?[^\w]*?$)", text)
        if match is not None:
            return match.group()
        return ""

    def mousePressEvent(self, event):
        if not self._completer or self._completer.popup().isVisible():
            super(CompleterLineEdit, self).mousePressEvent(event)
            return
        if self._completer.popup().isVisible():
            super(CompleterLineEdit, self).mousePressEvent(event)
            return
        self._completer.complete()

    def keyPressEvent(self, event):
        """

        :param event:
        :type event: :class:`QtGui.QKeyEvent`
        :return:
        :rtype:
        """
        if not self._completer:
            super(CompleterLineEdit, self).keyPressEvent(event)
            return

        if keyboardmouse.eventKeySequence(event) == QtGui.QKeySequence("Ctrl+Tab"):
            self._completer.setCompletionPrefix("")
            self._completer.complete()
            return
        if event.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Enter,
                           QtCore.Qt.Key_Tab,
                           QtCore.Qt.Key_Backtab, QtCore.Qt.Key_Delete,
                           QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Return):
            super(CompleterLineEdit, self).keyPressEvent(event)
            return
        elif event.key() == QtCore.Qt.Key_Down:
            if not self._completer.isVisble():
                self._completer.complete()
            super(CompleterLineEdit, self).keyPressEvent(event)
            return
        text = event.text()
        if not text:
            super(CompleterLineEdit, self).keyPressEvent(event)
            return

        rejectedText = "~!@#$%^&*()+{}|:\"<>?,./;'[]\\-= "
        if text in rejectedText:
            return
        completionPrefix = self.textUnderCursor() + text
        popUp = self._completer.popup()
        if completionPrefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(completionPrefix)
            popUp.setCurrentIndex(self._completer.completionModel().index(0, 0))

        if self._completer.completionCount() == 0:
            if not text.isalpha():
                super(CompleterLineEdit, self).keyPressEvent(event)
                popUp.hide()
                return

            self.insert(text)
            popUp.hide()
            return
        self.insert(text)
        rect = self.cursorRect()
        rect.setWidth(popUp.sizeHintForColumn(0) + popUp.verticalScrollBar().sizeHint().width())
        self._completer.complete()

