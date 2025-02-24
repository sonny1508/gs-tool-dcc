from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.preferences.interfaces import coreinterfaces


class Dialog(QtWidgets.QDialog):
    def __init__(
        self,
        title="",
        width=600,
        height=800,
        icon="",
        parent=None,
        showOnInitialize=True,
        transparent=False,
    ):
        super(Dialog, self).__init__(parent=parent)

        if transparent:
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self._themePref = coreinterfaces.coreInterface()
        self.setContentsMargins(2, 2, 2, 2)
        self.title = title
        self.setObjectName(title)
        self.setWindowTitle(title)
        self.resize(width, height)

        self._themePref.themeUpdated.connect(self.updateTheme)

        if icon:
            if isinstance(icon, QtGui.QIcon):
                self.setWindowIcon(icon)
            else:
                self.setWindowIcon(iconlib.icon(icon))

        if showOnInitialize:
            self.center()
            self.show()
        self.resize(width, height)

    def updateTheme(self, event):
        """Update the theme

        :type event: preferences.interface.preference_interface.UpdateThemeEvent
        :return:
        :rtype:
        """
        self.setStyleSheet(event.stylesheet)

    def center(self):
        frameGm = self.frameGeometry()
        centerPoint = utils.currentScreen().geometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def fillToParent(self, margins=(0, 0, 0, 0)):
        """Fill size to parent

        :return:
        :rtype:
        """
        self.setGeometry(
            margins[0],
            margins[1],
            self.window().geometry().width() - margins[0] - margins[2],
            self.window().geometry().height() - margins[1] - margins[3],
        )

    def toggleMaximized(self):
        """Toggles the maximized window state"""
        if self.windowState() and QtCore.Qt.WindowMaximized:
            self.showNormal()
        else:
            self.showMaximized()
