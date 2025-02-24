import os

from zoo.libs.pyqt.widgets import popups
from zoo.core.tooldata.tooldata import DirectoryPath
from zoovendor.Qt import QtCore, QtWidgets

from zoo.libs.pyqt.widgets.buttons import styledButton
from zoo.libs.pyqt.widgets.stringedit import StringEdit
from zoo.libs.pyqt.widgets.iconmenu import DotsMenu
from zoo.libs.pyqt.widgets.layouts import (hBoxLayout,
                                           vBoxLayout)

from zoo.libs.pyqt import uiconstants, utils

from zoo.libs.utils import filesystem, output, path as zpath


class DirectoryPathListWidget(QtWidgets.QWidget):
    pathAdded = QtCore.Signal(object)
    pathRemoved = QtCore.Signal(str)
    pathChanged = QtCore.Signal(object)
    aliasChanged = QtCore.Signal(object, str)
    cleared = QtCore.Signal()

    def __init__(self, parent=None, pathWidget=None, aliasActive=False):
        super(DirectoryPathListWidget, self).__init__(parent=parent)
        self._aliasActive = aliasActive
        self._pathWidget = pathWidget or DirectoryPathRemoveWidget

        self._pathWidgets = []

        self._mainLayout = vBoxLayout(parent=self)
        self._optionsLayout = hBoxLayout(margins=(0, 0, 0, 0))
        self._labelsLayout = hBoxLayout(margins=(3, 0, 0, 0))
        self._pathsLayout = vBoxLayout()

        if aliasActive:
            lbl = QtWidgets.QLabel("Alias")
            self._labelsLayout.addWidget(QtWidgets.QLabel("Paths"), 6)
            self._labelsLayout.addWidget(lbl)
            lbl.setFixedWidth(utils.dpiScale(242))

        self._mainLayout.addLayout(self._labelsLayout)
        self._mainLayout.addLayout(self._pathsLayout)
        self._mainLayout.addLayout(self._optionsLayout)

        self.addPathBtn = styledButton("  Add Path",
                                       "plusHollow",
                                       toolTip="",
                                       parent=self,
                                       minWidth=104)

        self._optionsLayout.addItem(QtWidgets.QSpacerItem(10, 10,
                                                          QtWidgets.QSizePolicy.Expanding,
                                                          QtWidgets.QSizePolicy.Minimum))
        self._optionsLayout.addWidget(self.addPathBtn)
        self.addPathBtn.clicked.connect(self.addPathClicked)

    def addPathClicked(self, path=None):
        """ Add path clicked button

        :param path:
        :return:
        """

        # directoryPath = self.pathText.text()
        directoryPath = ""
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.path.expanduser("~")
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Folder Path"
                                                                      "folder", directoryPath)
        if not newDirPath:
            return  # cancelled

        self.addPath(newDirPath)

    def addPath(self, path=None, alias=None):
        """ Add path widget

        :param path:
        :type path: str
        :param alias:
        :return:
        """

        if path and zpath.normpath(path) in self.paths():
            text = "'{}'\n path already exists. Path not added.".format(path)
            popups.MessageBox.showOK(title="Path Already Exists",
                                     message=text,
                                     icon=popups.MessageBox.Warning,
                                     buttonB=None)
            output.displayWarning(text)
            return

        path = path or ""
        widget = self._pathWidget(path=path, alias=alias, parent=self,
                                  aliasActive=self._aliasActive)  # type: DirectoryPathWidget

        if hasattr(widget, "onRemoveClicked"):
            widget.onRemoveClicked.connect(self._onRemovePath)

        widget.pathText.textChanged.connect(lambda x=widget: self.pathChanged.emit(x))
        widget.aliasChanged.connect(lambda alias, w=widget: self.aliasChanged.emit(w, alias))

        self._pathWidgets.append(widget)
        self._pathsLayout.addWidget(widget)

        if widget:
            self.pathAdded.emit(widget)

        return widget

    def paths(self):
        """ Return all the paths from the widgets

        :return:
        """
        return [zpath.normpath(wid.path()) for wid in self._pathWidgets if wid.path()]

    def clear(self, emit=True):
        """ Clear out the widgets and paths

        :return:
        """

        layout = self._pathsLayout
        self._pathWidgets[:] = []
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if emit:
            self.cleared.emit()

    def _onRemovePath(self):
        if len(self._pathWidgets) == 1:
            return
        widget = self.sender()
        self.pathRemoved.emit(widget.path())

        index = self._pathsLayout.indexOf(widget)
        self._pathsLayout.takeAt(index)
        widget.deleteLater()
        self._pathWidgets.remove(widget)

    def _onPathChanged(self):
        widget = self.sender()
        path = widget.path()
        if not path:
            return

        for widget in self._pathWidgets:
            if not widget.path():
                return


class PathWidget(QtWidgets.QWidget):
    pathChanged = QtCore.Signal(str)
    aliasChanged = QtCore.Signal(str)

    def __init__(self, parent=None, path=None, alias=None, aliasActive=False, toolTip="", label=None):
        super(PathWidget, self).__init__(parent)
        self._aliasActive = aliasActive
        self.mainLayout = hBoxLayout(parent=self, spacing=10)
        self._browserToolTip = toolTip
        self.defaultBrowserPath = os.path.expanduser("~")
        self.pathText = StringEdit(label=label or "",
                                   editText=path or "",
                                   toolTip="",
                                   parent=self,
                                   editRatio=8)
        self.pathText.setToolTip(toolTip)

        if self._aliasActive:
            self.aliasEdit = StringEdit(parent=self, label="", editRatio=3, editText=alias or "")
            self.aliasEdit.setFixedWidth(130)
            self.aliasEdit.textModified.connect(self._onAliasChanged)

            self._updateAlias()

        self.browseBtn = styledButton("",
                                      "browse",
                                      toolTip=self._browserToolTip,
                                      parent=self,
                                      minWidth=uiconstants.BTN_W_ICN_REG)
        self.dotsMenu = DotsMenu()

        toolTip = "Explore, open the directory in your OS browser."
        self.dotsMenu.addAction("Open Folder location",
                                icon="webpage",
                                toolTip=toolTip,
                                connect=self.openPathFolder)
        self.mainLayout.addWidget(self.pathText)
        if self._aliasActive:
            self.mainLayout.addWidget(self.aliasEdit)
        self.mainLayout.addWidget(self.browseBtn)
        self.mainLayout.addWidget(self.dotsMenu)

        self.browseBtn.clicked.connect(self.onPathBrowseClicked)
        self.pathText.textModified.connect(self._onPathChanged)
        self._searchFilter = ""

    def setSearchFilter(self, searchFilter):
        self._searchFilter = searchFilter

    def _onAliasChanged(self):
        self.aliasChanged.emit(self.aliasEdit.text())

    def _onPathChanged(self):
        self.pathChanged.emit(self.pathText.text())

    def path(self):
        """

        :return:
        """
        return self.pathText.text()

    def alias(self):
        """

        :return:
        """
        return self.aliasEdit.text()

    def openPathFolder(self):
        """Opens an os window for browsing files on disk in the users operating system"""
        path = self.pathText.text()
        filesystem.openLocation(path)
        output.displayInfo("OS window opened to the Path: `{}` folder location".format(path))

    def onPathBrowseClicked(self):
        """ Browse button clicked

        :return:
        """

        directoryPath = self.pathText.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = self.defaultBrowserPath
        filePath, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Set the File Path",
                                                            directoryPath, self._searchFilter)
        if not filePath:
            return  # cancelled

        self.setPathText(filePath)

    def setPathText(self, path):
        """ Set the path text. Also generate an edit if need be

        :param path:
        :return:
        """
        self.pathText.setText(path)
        self._updateAlias()
        self._onPathChanged()

    def setAliasText(self, alias):
        if self.aliasEdit:
            self.aliasEdit.setText(alias)

    def _updateAlias(self):
        """ Update alias based on path text

        :return:
        """
        if not self._aliasActive:
            return
        path = self.pathText.text()

        # Use normal alias, use folder name or just use path
        alias = self.aliasEdit.text() or os.path.basename(path) or path
        self.aliasEdit.setPlaceHolderText(alias)


class PathOpenWidget(PathWidget):

    def __init__(self, parent=None, path=None, alias=None, aliasActive=False):
        super(PathOpenWidget, self).__init__(parent, path, alias, aliasActive)

    def onPathBrowseClicked(self):
        """ Browse button clicked

        :return:
        """

        directoryPath = self.pathText.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = self.defaultBrowserPath
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Set the File Path",
                                                            directoryPath, self._searchFilter)
        if not filePath:
            return  # cancelled

        self.setPathText(filePath)


class DirectoryPathWidget(PathWidget):

    def __init__(self, parent=None, path=None, alias=None, aliasActive=False, label=None):
        super(DirectoryPathWidget, self).__init__(parent, path, alias, aliasActive, label=label)

    def onPathBrowseClicked(self):
        """ Browse button clicked

        :return:
        """

        directoryPath = self.pathText.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.path.expanduser("~")
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Folder Path", directoryPath)
        if not newDirPath:
            return  # cancelled

        self.setPathText(newDirPath)


class DirectoryPathRemoveWidget(DirectoryPathWidget):
    onRemoveClicked = QtCore.Signal()

    def __init__(self, path, parent, alias=None, aliasActive=False):
        super(DirectoryPathRemoveWidget, self).__init__(parent=parent, path=path, alias=alias, aliasActive=aliasActive)
        self.removePathBtn = styledButton("",
                                          "xCircleMark2",
                                          toolTip="",
                                          parent=self,
                                          style=uiconstants.BTN_TRANSPARENT_BG,
                                          minWidth=uiconstants.BTN_W_ICN_REG)
        self.mainLayout.addWidget(self.removePathBtn)
        self.removePathBtn.clicked.connect(self._onRemovedClicked)

    def _onRemovedClicked(self):
        self.onRemoveClicked.emit()


class BrowserPathListWidget(DirectoryPathListWidget):

    def __init__(self, parent=None, defaultPath=None):
        super(BrowserPathListWidget, self).__init__(parent=parent, pathWidget=BrowserPathWidget, aliasActive=True)
        self._defaultPath = defaultPath
        toolTip = "Reset the browser folder to it's default location."
        self.factoryResetBtn = styledButton("",
                                            "arrowRotLeft",
                                            toolTip=toolTip,
                                            parent=self,
                                            style=uiconstants.BTN_TRANSPARENT_BG,
                                            # minWidth=500,
                                            iconColor=(120, 120, 120))

        self.factoryResetBtn.setFixedWidth(20)
        self.factoryResetBtn.leftClicked.connect(self.factoryResetClicked)
        self._optionsLayout.insertWidget(0, self.factoryResetBtn)

    def data(self):
        """

        :return:
        :rtype: list[DirectoryPath]
        """
        return [widget.data() for widget in self._pathWidgets]

    def factoryResetClicked(self):
        self.clear()
        self.addPath(self._defaultPath)

    def addByDirectoryPath(self, directoryPath):
        """

        :param directoryPath:
        :type directoryPath: :class:`zoo.core.tooldata.tooldata.DirectoryPath`
        :return:
        """

        widget = self.addPath(directoryPath.path, directoryPath.alias)
        widget.setData(directoryPath)

    def addPath(self, path=None, alias=None):
        """

        :param path:
        :param alias:
        :return:
        :rtype: :class:`BrowserPathWidget`
        """

        return super(BrowserPathListWidget, self).addPath(path, alias)


class BrowserPathWidget(DirectoryPathRemoveWidget):
    def __init__(self, parent=None, path=None, alias=None, directoryPath=None, aliasActive=True):
        """

        :param parent:
        :param directoryPath:
        :type directoryPath: :class:`zoo.core.tooldata.tooldata.DirectoryPath`
        """
        self._data = directoryPath
        if directoryPath:
            path = self._data.path
            alias = self._data.alias
        else:
            self._data = DirectoryPath(path=path, alias=alias)

        super(BrowserPathWidget, self).__init__(parent=parent, path=path, alias=alias, aliasActive=True)

    def _onAliasChanged(self):
        """ Update data to use the new alias

        :return:
        """
        self.data().alias = self.alias()
        super(DirectoryPathRemoveWidget, self)._onAliasChanged()

    def setData(self, directoryPath):
        """

        :param directoryPath:
        :type directoryPath: :class:`zoo.core.tooldata.tooldata.DirectoryPath`
        :return:
        """
        self._data = directoryPath
        self.setPathText(directoryPath.path)
        self.setAliasText(directoryPath.alias)

    def data(self):
        """

        :return:
        :rtype: :class:`zoo.core.tooldata.tooldata.DirectoryPath`
        """
        return self._data
