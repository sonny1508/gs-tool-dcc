from zoovendor.Qt import QtCore


class UiInterface(QtCore.QObject):
    _instance = None

    def __init__(self, parent=None):
        """ Ui Interface with all the important references for hive tools

        # :type artistUi: :class:`zoo.apps.hiveartistui.artistui.HiveArtistUI`
        # :param tree:
        # :type tree:  :class:`zoo.apps.hiveartistui.views.componenttree.ComponentTreeWidget`
        """
        super(UiInterface, self).__init__(parent=parent)
        self._tree = None
        self._artistui = None
        self._componentWidget = None
        self._core = None

    def core(self):
        """

        :return:
        :rtype: :class:`zoo.apps.hiveartistui.artistuicore.HiveUICore`
        """
        return self._core

    def setCore(self, core):
        """

        :param core:
        :type core: :class:`zoo.apps.hiveartistui.artistuicore.HiveUICore`
        """
        self._core = core

    def templateLibrary(self):
        """ Template library

        :return:
        :rtype: :class:`zoo.apps.hiveartistui.views.templatelibrary.TemplateLibrary
        """
        return self._artistUi.createUi.templateLibraryWgt

    def tree(self):
        """

        :return:
        :rtype: :class:`zoo.apps.hiveartistui.views.componenttree.ComponentTreeWidget`
        """

        return self._tree

    def setTree(self, tree):
        self._tree = tree

    def artistUi(self):
        """

        :return:
        :rtype: :class:`zoo.apps.hiveartistui.artistui.HiveArtistUI`
        """
        return self._artistUi

    def setArtistUi(self, artistUi):
        self._artistUi = artistUi

    def refreshUi(self, force=False):
        """ Refresh and synchronize the ui if needed

        :return:
        """
        if force:
            self._artistUi.refreshUi()
        else:
            self._artistUi.checkRefresh()


def createInstance(parent=None):
    if not UiInterface._instance:
        UiInterface._instance = UiInterface(parent=parent)
    return UiInterface._instance


def instance():
    """

    :return:
    :rtype: :class:`UiInterface`
    """

    return UiInterface._instance


def destroyInstance():
    UiInterface._instance = None
