from functools import partial

from zoo.libs.pyqt import keyboardmouse, utils
from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt.widgets import elements


class TabWidget(QtWidgets.QTabWidget):
    """
    Hotkey:
    Ctrl+T to add new Tab
    """
    # allow for custom actions, the qmenu instance is passed to the signal
    contextMenuRequested = QtCore.Signal(object)
    newTabRequested = QtCore.Signal(object, str)
    renameTabRequested = QtCore.Signal(int, str)  # tab index, new tab name
    removeTabRequested = QtCore.Signal(int)  # tab index, new tab name

    def __init__(self, name="", parent=None):
        super(TabWidget, self).__init__(parent=parent)
        self.setObjectName(name)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._contextMenu)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setIconSize(QtCore.QSize(utils.dpiScale(8), utils.dpiScale(8)))
        self.tabCloseRequested.connect(self.onTabCloseRequested)

    def addTabWidget(self, childWidget=None, dialog=False, name=None):
        """Will open dialog to get tab name and create a new tab with the childWidget set as the child of the
        new tab.

        :param childWidget: QtWidget

        """

        name = name or "TEMP"
        if dialog:
            # Open input window
            ret = elements.MessageBox.inputDialog(parent=self,
                                                  title=self.tr("Create new tab"),
                                                  message=self.tr('Tab name'),
                                                  text=self.tr(''))
            if ret is None or ret == "":
                return
            name = ret
        self.newTabRequested.emit(childWidget, name)

    def onTabCloseRequested(self, index=-1, dialog=True):
        """Creates a inputDialog for removing the tab
        """
        if self.count() == 1:
            return

        # Get current tab index
        index = self.currentIndex() if index < 0 else index
        if dialog:
            # Open confirmation
            reply = elements.MessageBox.showQuestion(self, 'Delete',
                                                     "Delete tab '{}'?".format(self.tabText(index)),
                                                     buttonA="Yes", buttonB="No",
                                                     default=1)
            if reply == "A":
                self.removeTabRequested.emit(index)
                self.removeTab(index)
            return reply != "B"
        else:
            self.removeTabRequested.emit(index)
            self.removeTab(index)
            return True

    def renameTab(self, index=-1):
        """Creates a inputDialog for renaming the tab name
        """
        # Get current tab index
        index = self.currentIndex() if index < 0 else index

        # Open input window
        name = elements.MessageBox.inputDialog(self,
                                               "Tab name",
                                               'New name',
                                               self.tabText(index))
        if not name:
            return

        self.setTabText(index, name)
        self.renameTabRequested.emit(index, name)

    def closeOtherTabs(self, index=-1):
        count = self.count()
        if count == 1:
            return
        # remove all tabs after current
        for i in range(index + 1, self.count()):
            self.removeTab(i)

        # current tab is now the last, therefore remove all but the last
        for i in range(self.count() - 1):
            self.removeTab(0)

    def _contextMenu(self, pos):
        """ Set up a custom context menu, the contextMenuRequested signal is called at the end of
        the function so the user can add their own actions/child menus without overriding the function. exec is Called
        after user mode.

        :param pos: the mouse position
        :type pos: QPoint
        """
        index = self.tabBar().tabAt(pos)

        menu = QtWidgets.QMenu(parent=self)
        renameAct = menu.addAction("Rename")
        addAct = menu.addAction("Add Tab")
        closeAct = menu.addAction("Close")
        closeOtherAct = menu.addAction("Close Other Tabs")

        renameAct.triggered.connect(partial(self.renameTab, index))
        addAct.triggered.connect(self.addTabWidget)
        closeAct.triggered.connect(partial(self.onTabCloseRequested, index, dialog=False))
        closeOtherAct.triggered.connect(partial(self.closeOtherTabs, index))
        self.contextMenuRequested.emit(menu)
        menu.exec_(self.mapToGlobal(pos))

    def keyPressEvent(self, event):
        sequenece = keyboardmouse.eventKeySequence(event)
        if sequenece == QtGui.QKeySequence("Ctrl+T"):
            self.addTabWidget(None, False, None)
            event.accept()
        super(TabWidget, self).keyPressEvent(event)
