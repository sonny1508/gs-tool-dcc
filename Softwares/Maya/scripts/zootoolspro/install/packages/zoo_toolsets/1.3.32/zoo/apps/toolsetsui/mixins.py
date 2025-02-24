from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import general

if general.TYPE_CHECKING:
    from typing import Union
    from zoo.apps.toolsetsui.widgets.toolsetwidget import ToolsetWidget
    from zoo.libs.pyqt.extended.imageview.thumbnail.minibrowser import MiniBrowser


class MiniBrowserMixin(object):
    """ Some typical functions for minibrowsers to talk to prefs.
    Eg. set up connections

    """
    _browserPrefs = None

    def setMiniBrowsers(self, miniBrowsers):
        """

        :param miniBrowsers:
        :type miniBrowsers: list[MiniBrowser]
        :return:
        """

        self._minibrowsers = miniBrowsers


    def setAssetPreferences(self, prefs):
        """ Set the prefs that is going to be used by the minibrowser

        :param prefs:
        :type prefs: :zoo.preferences.prefinterface.BrowserPreference:
        :return:

        """
        self._browserPrefs = prefs

    def refreshThumbs(self):
        """Refreshes the GUI """
        self = self  # type: Union[ToolsetWidget, MiniBrowserMixin]
        self.currentWidget().miniBrowser.refreshThumbs()

    def uniformIconToggle(self, action):
        """Toggles the state of the uniform icons
        """

        self.prefs().setBrowserUniformIcons(action.isChecked())
        self.refreshThumbs()

    def uiconnections(self):
        """ UI connections to connect the minibrowser to the toolset

        :return:
        """
        self = self  # type: Union[ToolsetWidget, MiniBrowserMixin]

        for m in self._minibrowsers:
            m.refreshAction.connect(self.refreshThumbs)
            m.uniformIconAction.connect(self.uniformIconToggle)
            m.itemSelectionChanged.connect(self.browserSelectionChanged)

    def prefs(self):
        """

        :return:
        :rtype: zoo.preferences.assets.BrowserPreference
        """

        if self._browserPrefs is None:
            raise AttributeError("{}._browserPrefs must be set. eg. use .setPreferences()".format(self.__class__.__name__))

        return self._browserPrefs


    def browserSelectionChanged(self, image, item):
        """ Set the infoEmbedWindow nameEdit to disabled if its one of the default controls

        :param image:
        :type image:
        :param item:
        :type item:
        :return:
        :rtype:
        """
        self = self  # type: Union[ToolsetWidget, MiniBrowserMixin]
        miniBrowser = self.currentWidget().miniBrowser  # type: MiniBrowser

        defaultItems = self.prefs().defaultAssetItems()
        if self.prefs().defaultAssetItems():
            # todo: may be an issue here for non default asset items
            miniBrowser.infoEmbedWindow.nameEdit.setEnabled(not (item.name in defaultItems))
