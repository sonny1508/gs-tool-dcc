from zoovendor.Qt import QtCore, QtGui, QtWidgets
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import dpiscaling
from zoo.preferences.interfaces import coreinterfaces


class ClearToolButton(QtWidgets.QToolButton):
    """ For css purposes only """


class SearchToolButton(QtWidgets.QToolButton):
    """ For css purposes only """


class SearchLineEdit(QtWidgets.QLineEdit, dpiscaling.DPIScaling):
    """Search Widget with two icons one on either side, inherits from QLineEdit

    :param searchPixmap:
    :type searchPixmap:
    :param clearPixmap:
    :param parent:
    :param iconsEnabled:
    """
    textCleared = QtCore.Signal()

    def __init__(self, searchPixmap=None, clearPixmap=None, parent=None, iconsEnabled=True):
        super(SearchLineEdit, self).__init__(parent)
        self._iconsEnabled = iconsEnabled
        self._themePref = coreinterfaces.coreInterface()

        if searchPixmap is None:
            searchPixmap = iconlib.iconColorized("magnifier", utils.dpiScale(16),
                                                 (128, 128, 128))  # these should be in layouts

        if clearPixmap is None:
            clearPixmap = iconlib.iconColorized("close", utils.dpiScale(16), (128, 128, 128))

        self.clearButton = ClearToolButton(self)
        self.clearButton.setIcon(QtGui.QIcon(clearPixmap))

        self.searchButton = SearchToolButton(self)
        self.searchButton.setIcon(QtGui.QIcon(searchPixmap))
        self._backgroundColor = None
        self.initUi()
        self._themePref.themeUpdated.connect(self.updateTheme)

    def initUi(self):
        """ Init UI

        :return:
        :rtype:
        """
        self.clearButton.setCursor(QtCore.Qt.ArrowCursor)
        self.clearButton.setStyleSheet("QToolButton { border: none; padding: 1px; }")
        self.clearButton.hide()
        self.clearButton.clicked.connect(self.clear)
        self.textChanged.connect(self.updateCloseButton)

        self.searchButton.setStyleSheet("QToolButton { border: none; padding: 0px; }")

        self.setIconsEnabled(self._iconsEnabled)
        utils.setForcedClearFocus(self)

    def focusInEvent(self, event):
        """

        :param event:
        :type event: Qt.QtGui.QFocusEvent
        :return:
        :rtype:
        """
        QtWidgets.QLineEdit.focusInEvent(self, event)
        if event.reason() == QtCore.Qt.FocusReason.ActiveWindowFocusReason:
            self.clearFocus()  # Generally we dont want search widgets to be the first focus on window activate

    def setBackgroundColor(self, col):
        self._backgroundColor = col
        self.setIconsEnabled(self._iconsEnabled)

    def setIconsEnabled(self, enabled):
        if self._iconsEnabled:
            frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
            self.updateStyleSheet()
            msz = self.minimumSizeHint()
            self.setMinimumSize(max(msz.width(),
                                    self.searchButton.sizeHint().width() +
                                    self.clearButton.sizeHint().width() + frameWidth * 2 + 2),
                                max(msz.height(),
                                    self.clearButton.sizeHint().height() + frameWidth * 2 + 2))

        else:
            self.searchButton.hide()
            self.clearButton.hide()

            self.setStyleSheet("")

        self._iconsEnabled = enabled

    def updateTheme(self, event):
        """ Update the theme

        :type event: preferences.interface.preference_interface.UpdateThemeEvent
        :return:
        :rtype:
        """
        self._backgroundColor = event.themeDict.TEXT_BOX_BG_COLOR
        self.updateStyleSheet()

    def updateStyleSheet(self):
        if self._backgroundColor is None:
            self._backgroundColor = self._themePref.TEXT_BOX_BG_COLOR

        backgroundStyle = "background-color: rgba{}".format(
            str(self._backgroundColor)) if self._backgroundColor is not None else ""

        frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)

        if self.height() < utils.dpiScale(25):
            topPad = 0  # todo: could do this part better
        else:
            topPad = -2 if utils.dpiMult() == 1.0 else 0
        self.setStyleSheet("QLineEdit {{ padding-left: {}px; padding-right: {}px; {}; padding-top: {}px; }} ".
                           format(self.searchButton.sizeHint().width() + frameWidth + utils.dpiScale(1),
                                  self.clearButton.sizeHint().width() + frameWidth + utils.dpiScale(1),
                                  backgroundStyle,
                                  topPad))

    def resizeEvent(self, event):
        if self._iconsEnabled:
            sz = self.clearButton.sizeHint()
            frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
            rect = self.rect()
            yPos = abs(rect.bottom() - sz.height()) * 0.5 + utils.dpiScale(1)
            self.clearButton.move(self.rect().right() - frameWidth - sz.width(), yPos - 2)
            self.searchButton.move(self.rect().left() + utils.dpiScale(1), yPos)
            self.updateStyleSheet()

    def updateCloseButton(self, text):
        if text and self._iconsEnabled:
            self.clearButton.setVisible(True)
            return
        self.clearButton.setVisible(False)



if __name__ == "__name__":
    app = QtWidgets.QApplication([])
    searchIcon = QtGui.QPixmap(iconlib.icon("magnifier"), 16)
    closeIcon = QtGui.QPixmap(iconlib.icon("code", 16))
    w = SearchLineEdit(searchIcon, closeIcon)
    w.show()
    app.exec_()
