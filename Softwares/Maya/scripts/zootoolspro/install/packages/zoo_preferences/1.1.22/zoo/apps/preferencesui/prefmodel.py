import os

from zoo.libs.utils import general
from zoovendor.Qt import QtWidgets, QtCore

from zoo.core.plugin import pluginmanager
from zoo.libs.pyqt.models import datasources
from zoo.libs.pyqt.widgets import elements
from zoo.preferences.core import preference


class PrefModel(QtCore.QObject):
    def __init__(self, qmodel, order=None):
        """ Gathers the available preferences from the different packages

        :param qmodel:
        :type qmodel:
        :param order: The order in which the preferences should be shown.
        todo: maybe order this should be preference id rather than preference title
        :type order: list[basestring]
        """
        self.pluginManager = pluginmanager.PluginManager(interface=[SettingWidget])
        self.model = qmodel
        self.root = None  # type: PathDataSource
        self.order = order or []
        self.reload()

    def _reloadDataSources(self):
        # sort by category title
        validResults = sorted(self.pluginManager.plugins.values(), key=lambda x: x.categoryTitle)
        self.root = PathDataSource("root", model=self.model, parent=None)

        # Move the ones specified by order to the top
        for o in reversed(self.order):
            for v in validResults:
                if v.categoryTitle == o:
                    validResults.insert(0, validResults.pop(validResults.index(v)))
                    break

        i = 0
        # Add the data sources
        for wid in validResults:
            i += 1
            categoryTitle = wid.categoryTitle
            if not categoryTitle:
                continue
            # slice the relativePath which will end up being a tree in the view
            slicedpath = categoryTitle.split("/")
            # skip the last value as that's going to hold our widget, others are just text
            parent = self.root
            for name in slicedpath[:-1]:
                source = PathDataSource(name.title(), model=self.model, parent=parent)
                source.model = self.model
                parent.children.append(source)
                parent = source
            # now add the leaf
            try:
                source = SettingDataSource(slicedpath[-1].title(), widget=wid, model=self.model, parent=parent)
                source.model = self.model
                parent.children.append(source)
            except:
                general.printException()

    def reload(self):
        # if we already have loaded the inital plugins just refresh the dataSources
        if self.pluginManager.plugins:
            self._reloadDataSources()
            return
        # loop the zootools package preferences and find the widgets
        pluginPaths = set()
        for preferencePath in preference.iterPackagePreferenceRoots():

            widgets = os.path.join(preferencePath, "widgets")
            # skip if widgets py package wasn't found
            if not os.path.exists(widgets):
                continue
            pluginPaths.add(str(widgets))

        if pluginPaths:
            self.pluginManager.registerPaths(pluginPaths)
            self._reloadDataSources()

        self.model.root = self.root


class SettingWidget(QtWidgets.QWidget):
    """ Main inheritance widget for preference UI which will appear on the right
    """
    categoryTitle = ""

    def __init__(self, parent=None, setting=None):
        """ Setting widget. The ui widget that displays the things inside the settings

        :param parent:
        :type parent:
        :param setting: SettingDataSource
        :type setting: zoo.apps.preferencesui.prefmodel.SettingDataSource
        """
        self.setting = setting
        super(SettingWidget, self).__init__(parent)

    def serialize(self):
        """ Serialize

        :return: Return true if save successful
        :rtype: bool
        """
        return True

    def applySettings(self, settings):
        pass

    def revert(self):
        pass

    def setModified(self, modified):
        """ If it's set to modified set the setting to modified

        :param modified:
        :type modified:
        :return:
        :rtype:
        """
        self.setting.setModified(modified)

    def isModified(self):
        return self.setting.isModified()

    def cancelSaveEvent(self):
        """ If save event was cancelled. Put any behaviour for the cancel here.

        :return:
        :rtype:
        """
        pass

    def showSavedMessageBox(self, parent=None):
        """ Show saved message box
        It already does the saving/reverting so just pass through for "A"=OK "B"=No

        :param parent: The parent widget
        :type parent: QtWidgets.QWidget
        :return: Returns the result from the message box
        :rtype: bool
        """
        msg = "There are unsaved changes for '{}'. Do you wish to save?".format(self.setting.label)
        result = elements.MessageBox.showQuestion(title="Save Preference", parent=parent, message=msg,
                                                  buttonA="OK", buttonB="No", buttonC="Cancel")
        if result == "A":
            self.serialize()
            self.setModified(False)
        elif result == "B":
            self.revert()
            self.setModified(False)
        else:
            self.cancelSaveEvent()

        return result


class PathDataSource(datasources.BaseDataSource):
    """A data source that contains no widget, basically just an item with text
    """

    def __init__(self, label, model=None, parent=None):
        super(PathDataSource, self).__init__(model, parent)
        self._text = label

    def data(self, index):
        return self._text

    def columnCount(self):
        return 1

    def isEnabled(self, index):
        return True

    def isEditable(self, *args, **kwargs):
        return False

    def widget(self):
        pass

    def save(self):
        pass
    def hasWidget(self):
        pass


class SettingDataSource(datasources.BaseDataSource):
    def __init__(self, label, widget, model=None, parent=None):
        """ Main SettingsDataSource, this class should be linked to a preferences widget
        from the library

        :param label:
        :type label:
        :param widget:
        :type widget: zoo.apps.preferencesui.prefmodel.SettingWidget
        :param model:
        :type model:
        :param parent:
        :type parent:
        """
        super(SettingDataSource, self).__init__(headerText=label, model=model, parent=parent)
        self._modified = False
        self.label = label
        self._widgetCls = widget
        self._widget = None


    def __repr__(self):
        return super(SettingDataSource, self).__repr__().replace("<", "<label=\"{}\" ".format(self.label))

    def save(self):
        serialized = self._widget.serialize()
        if serialized is not False:
            self.setModified(False)

    def data(self, *args, **kwargs):
        return self.label

    def setModified(self, modified):
        self._modified = modified

    def revert(self):
        self._widget.revert()
        self.setModified(False)

    def isEditable(self, *args, **kwargs):
        return False

    def widget(self):
        """ Preferences ui setting widget

        :return:
        :rtype: zoo.apps.preferencesui.prefmodel.SettingWidget
        """
        return self._widget

    def hasWidget(self):
        return self._widgetCls is not None

    def createWidget(self, parent):
        if self._widget is not None:
            return self._widget
        if self._widgetCls is None:
            return
        self._widget = self._widgetCls(setting=self, parent=parent)
        return self._widget

    def isModified(self):
        """ Returns true if modified

        :return:
        :rtype:
        """
        return self._modified
