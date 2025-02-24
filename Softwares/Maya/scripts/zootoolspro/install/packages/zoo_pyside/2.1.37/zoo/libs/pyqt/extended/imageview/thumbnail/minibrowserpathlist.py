from zoo.libs.pyqt.widgets.pathwidget import BrowserPathListWidget


class MiniBrowserPathList(BrowserPathListWidget):
    def __init__(self, assetPref, parent=None, toolTip=None):
        """ A browser path widget that is connected to the Preference asset

        :param assetPref:
        :type assetPref: zoo.preferences.assets.BrowserPreference
        :param parent:
        :param defaultPath:
        :param toolTip:
        """
        defaultPath = assetPref.zooPrefsDefaultsPath()
        super(MiniBrowserPathList, self).__init__(parent=parent, defaultPath=defaultPath)
        self.setToolTip(toolTip)
        self.assetPref = assetPref

        self._initUi()

    def revert(self):
        """ Clear path list and reset back to the asset preferences

        :return:
        """
        self.clear(emit=False)

        for bf in self.assetPref.browserFolderPaths():
            self.addByDirectoryPath(bf)

    def _initUi(self):
        """ Initialize the UI

        :return:
        """
        self.revert()

        self.pathRemoved.connect(self.directoryRemove)
        self.pathAdded.connect(self.directoryAddPath)
        self.cleared.connect(self.directoriesCleared)
        # self.controlsJointsFolders.aliasChanged.connect(self.directoryAliasChanged)

    def directoryRemove(self, path):
        """ Remove directory

        :param path:
        :return:
        """
        self.assetPref.removeBrowserDirectory(path, save=False)

    def directoryAddPath(self, w):
        """

        :param w:
        :type w: :class:`zoo.libs.pyqt.widgets.pathwidget.BrowserPathWidget`
        :return:
        """

        self.assetPref.addBrowserDirectory(w.data(), save=False)
        self.assetPref.addActiveDirectory(w.data(), save=False)

    def directoryAliasChanged(self, pathWidget, alias):
        """

        :param pathWidget:
        :type pathWidget: zoo.libs.pyqt.widgets.pathwidget.BrowserPathWidget
        :param alias:
        :return:
        """
        # print(pathWidget.data(), alias)


    def directoriesCleared(self):
        """ Clear directories

        :return:
        """
        self.assetPref.clearBrowserDirectories(save=False)

    def saveToPrefs(self):
        # maybe this should be done automatically?
        self.assetPref.setBrowserDirectories(self.data())

