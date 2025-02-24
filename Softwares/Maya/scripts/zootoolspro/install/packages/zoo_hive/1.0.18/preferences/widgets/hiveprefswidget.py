from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants

from zoo.apps.preferencesui import prefmodel

from zoo.libs.hive.library.tools.toolui import buildscriptwidget
from zoo.libs.hive import api as hiveapi
from zoo.preferences.interfaces import hiveinterfaces
try:
    from zoo.apps.hiveartistui import uiinterface
except ImportError:
    uiinterface = None


class HivePreferencesWidget(prefmodel.SettingWidget):
    categoryTitle = "Hive"  # The main title of the General preferences section and also side menu item

    def __init__(self, parent=None, setting=None):
        """Builds the General Section of the preferences window.

        :param parent: the parent widget
        :type parent: :class:`zoovendor.Qt.QtWidgets.QWidget`
        """
        super(HivePreferencesWidget, self).__init__(parent, setting)
        self.hiveInterface = hiveinterfaces.hiveInterface()
        self._mainLayout = elements.vBoxLayout(self,
                                               margins=(uiconstants.WINSIDEPAD,
                                                        uiconstants.WINTOPPAD,
                                                        uiconstants.WINSIDEPAD,
                                                        uiconstants.WINBOTPAD),
                                               spacing=uiconstants.SREG)
        self.componentPathWidget = None  # type: elements.DirectoryPathListWidget
        self.templatePathsWidget = None  # type: elements.DirectoryPathListWidget
        self.templateSavePathsWidget = None  # type: elements.DirectoryPathWidget
        self.buildScriptsWidget = None  # type: elements.DirectoryPathListWidget
        self.namingWidget = None  # type: elements.DirectoryPathListWidget
        self.hiveConfig = hiveapi.Configuration()
        self.uiLayout()  # Adds widgets to the layouts

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        generalFrameWidget = elements.CollapsableFrame("General", parent=self, collapsed=False)
        componentPathFrameWidget = elements.CollapsableFrame("Component Paths", parent=self, collapsed=False)
        templatePathsFrameWidget = elements.CollapsableFrame("Template Paths", parent=self, collapsed=False)
        buildScriptsFrameWidget = elements.CollapsableFrame("Build Script Paths", parent=self, collapsed=False)
        namingFrameWidget = elements.CollapsableFrame("Naming Configuration", parent=self, collapsed=False)
        self._mainLayout.addWidget(generalFrameWidget)
        self._mainLayout.addWidget(componentPathFrameWidget)
        self._mainLayout.addWidget(templatePathsFrameWidget)
        self._mainLayout.addWidget(buildScriptsFrameWidget)
        self._mainLayout.addWidget(namingFrameWidget)
        self._mainLayout.addStretch(1)
        self._setupGeneralSettingsWidget(generalFrameWidget)
        self._setupComponentPathsWidget(componentPathFrameWidget)
        self._setupBuildScriptPathsWidget(buildScriptsFrameWidget)
        self._setupTemplatePathsWidget(templatePathsFrameWidget)
        self._setupNamingPresetPathsWidget(namingFrameWidget)
        self._setPaths()

    def _setupComponentPathsWidget(self, parent):
        self.componentPathWidget = elements.DirectoryPathListWidget(parent=self)
        parent.addWidget(self.componentPathWidget)

    def _setupBuildScriptPathsWidget(self, parent):
        self.defaultBuildScripts = buildscriptwidget.BuildScriptWidget(label="Default Build Scripts:", parent=self)
        self.buildScriptsWidget = elements.DirectoryPathListWidget(parent=self)

        self.defaultBuildScripts.setItemList(
            [{"label": i, "id": i, "properties": {},
              "defaultPropertyValue": {}} for i in self.hiveConfig.buildScriptRegistry().plugins])
        self.defaultBuildScripts.setCurrentItems([i.id for i in self.hiveConfig.buildScripts])
        parent.addWidget(self.buildScriptsWidget)
        parent.addWidget(self.defaultBuildScripts)

    def _setupTemplatePathsWidget(self, parent):
        self.templateSavePathsWidget = elements.DirectoryPathWidget(parent=self, label="Save Path")
        self.templatePathsWidget = elements.DirectoryPathListWidget(parent=self)

        parent.addWidget(self.templateSavePathsWidget)
        parent.addWidget(self.templatePathsWidget)

    def _setupNamingPresetPathsWidget(self, parent):
        self.namingPresetSavePathsWidget = elements.DirectoryPathWidget(parent=self, label="Save Path:")
        self.namingPresetPathsWidget = elements.DirectoryPathListWidget(parent=self)

        parent.addWidget(self.namingPresetSavePathsWidget)
        parent.addWidget(self.namingPresetPathsWidget)

    def _setPaths(self):
        # templates
        paths = self.hiveInterface.userTemplatePaths()
        savePath = self.hiveInterface.userTemplateSavePath()
        for p in paths:
            self.templatePathsWidget.addPath(p)
        self.templatePathsWidget.addPath()
        self.templateSavePathsWidget.pathText.blockSignals(True)
        self.templateSavePathsWidget.setPathText(savePath)
        self.templateSavePathsWidget.pathText.blockSignals(False)

        # build scripts
        paths = self.hiveInterface.userBuildScriptPaths()
        for p in paths:
            self.buildScriptsWidget.addPath(p)
        self.buildScriptsWidget.addPath()

        # components
        paths = self.hiveInterface.userComponentPaths()
        for p in paths:
            self.componentPathWidget.addPath(p)
        self.componentPathWidget.addPath()

        # naming presets
        savePath = self.hiveInterface.namingPresetSavePath()
        loadPaths = self.hiveInterface.namingPresetPaths()
        self.namingPresetSavePathsWidget.setPathText(savePath)
        for p in loadPaths:
            self.namingPresetPathsWidget.addPath(p)
        self.namingPresetPathsWidget.addPath()

    def _setupGeneralSettingsWidget(self, frameWidget):
        self.includeDefaultAssetsBox = elements.CheckBox("Include Default Assets",
                                                         checked=self.hiveInterface.settings(
                                                             name="includeDefaultAssets"),
                                                         parent=self,
                                                         enableMenu=False)
        frameWidget.addWidget(self.includeDefaultAssetsBox)

    def serialize(self):
        """ Save the current settings to the preference file, used for both Apply and Save buttons

        Automatically connected to the preferences window buttons via model.SettingWidget

        :return: Returns true if successful in saving, false otherwise
        :rtype: bool
        """
        includeAssets = self.includeDefaultAssetsBox.isChecked()
        templateSavePath = self.templateSavePathsWidget.path()
        templatePaths = self.templatePathsWidget.paths()
        componentPaths = self.componentPathWidget.paths()
        scriptPaths = self.buildScriptsWidget.paths()
        self.hiveInterface.settings()["settings"]["includeDefaultAssets"] = includeAssets
        self.hiveInterface.setUserBuildScriptPaths(scriptPaths, False)
        self.hiveInterface.setUserComponentPaths(componentPaths, False)
        self.hiveInterface.setUserTemplatePaths(templatePaths, False)
        self.hiveInterface.setUserTemplateSavePath(templateSavePath, False)
        self.hiveInterface.setUserBuildScripts(self.defaultBuildScripts.currentItems(), False)
        self.hiveInterface.setNamingPresetSavePath(self.namingPresetSavePathsWidget.path())
        self.hiveInterface.setNamingPresetPaths(self.namingPresetPathsWidget.paths())
        self.hiveInterface.saveSettings()
        if includeAssets:
            self.hiveInterface.upgradeAssets()
        registry = hiveapi.Configuration.templateRegistry()
        if registry:
            registry.refresh()
        if uiinterface:
            uiInstance = uiinterface.instance()
            if uiInstance:
                uiInstance.templateLibrary().refresh()


    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """

        self.templatePathsWidget.clear()
        self.componentPathWidget.clear()
        self.buildScriptsWidget.clear()
        self._setPaths()
