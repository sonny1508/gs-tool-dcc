from zoo.preferences.interfaces import coreinterfaces
from zoovendor.Qt import QtCore, QtWidgets

from zoo.apps.hotkeyeditor.hotkeyview import view
from zoo.apps.hotkeyeditor.core import utils as hotkeyutils
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements


class HotkeyEditorUI(elements.ZooWindow):
    helpUrl = "http://create3dcharacters.com/zoo2"
    windowSettingsPath = "zoo/hotkeyeditorui"

    def __init__(self, title="Zoo Hotkey Editor",
                 width=1000,
                 height=600, **kwargs):

        super(HotkeyEditorUI, self).__init__(title=title, width=width, height=height,
                                             saveWindowPref=False,
                                             **kwargs)
        self.windowWidth = width
        self.windowHeight = height
        self.adminMode = False
        self.hotkeyView = view.HotkeyView(parent=self)
        self.tabLayout = elements.hBoxLayout()
        self.themePref = coreinterfaces.coreInterface()

        # UI
        self.setWindowTitle(title)
        self.mainLayout = elements.hBoxLayout(self)
        self.mainLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        self.mainLayout.setSpacing(0)

        self.setMainLayout(self.mainLayout)
        self.resize(width, height)

        self.initUi()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def initUi(self):
        self.tabLayout.setContentsMargins(0, 0, 0, 0)
        self.tabLayout.addWidget(self.hotkeyView)
        self.mainLayout.addLayout(self.tabLayout)

        if hotkeyutils.isAdminMode():
            self.setLogoColor(self.themePref.HOTKEY_ADMIN_LOGO_COLOR)

    def resizeWindow(self):
        for i in range(0, 10):
            QtWidgets.QApplication.processEvents()  # this must be here otherwise the resize is calculated too quickly
        self.resize(self.width(), self.minimumSizeHint().height())

    def focusInEvent(self, event):
        self.hotkeyView.reloadActive()

