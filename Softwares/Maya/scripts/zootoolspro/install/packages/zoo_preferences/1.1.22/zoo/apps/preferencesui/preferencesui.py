from zoovendor.Qt import QtWidgets

from zoo.apps.preferencesui import prefmodel
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.extended import treeviewplus
from zoo.libs.pyqt.models import treemodel
from zoo.preferences.interfaces import coreinterfaces
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic


class PreferencesUI(elements.ZooWindow):
    windowSettingsPath = "zoo/preferencesui"
    def __init__(self, title="Zoo Preferences",
                 width=850,
                 height=700, parent=None,
                 **kwargs):

        self.windowWidth = width
        super(PreferencesUI, self).__init__(parent=parent, name=title, title=title, width=width, height=height,
                                            saveWindowPref=False,
                                            **kwargs)
        self.themePref = coreinterfaces.coreInterface()
        self.treeModel = treemodel.TreeModel(None)

        self.model = prefmodel.PrefModel(qmodel=self.treeModel, order=["Theme Colors", "General"])

        self.prefTreeView.setModel(self.treeModel)
        self.prefTreeView.expandAll()

        firstWgtSource = self.firstDataSourceWithWidget(self.model.root)
        if firstWgtSource is not None:
            self.prefStackedWgt.addSource(firstWgtSource)

        self.connections()

    def _initUi(self):
        super(PreferencesUI, self)._initUi()
        self.mainLayout = elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=0)

        toolTipBtn = "Save only the current section's preferences settings, and close the window. "
        self.saveBtn = elements.styledButton(text="Save", icon="save", parent=self, textCaps=True,
                                             style=uic.BTN_DEFAULT, toolTip=toolTipBtn)
        toolTipBtn = "Save only the current section's preferences settings. "
        self.applyBtn = elements.styledButton(text="Apply", icon="checkMark", parent=self, textCaps=True,
                                              style=uic.BTN_DEFAULT, toolTip=toolTipBtn)
        toolTipBtn = "Revert this section's preferences settings to the previous (not default) settings. "
        self.resetBtn = elements.styledButton(text="Revert", icon="reload2", parent=self, textCaps=True,
                                              style=uic.BTN_DEFAULT, toolTip=toolTipBtn)
        toolTipBtn = "Cancel the current changes and close the window. "
        self.cancelBtn = elements.styledButton(text="Cancel", icon="xCircleMark", parent=self, textCaps=True,
                                               style=uic.BTN_DEFAULT, toolTip=toolTipBtn)

        self.prefStackedWgt = PrefStackedWidget(parent=self)
        self.prefTreeView = PrefTreeView(parent=self, stackedWidget=self.prefStackedWgt)

        splitter = QtWidgets.QSplitter(parent=self)

        scrollArea = QtWidgets.QScrollArea(self)
        scrollArea.setWidget(self.prefStackedWgt)
        scrollArea.setWidgetResizable(True)
        scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)

        splitter.addWidget(self.prefTreeView)
        splitter.addWidget(scrollArea)
        treeWidgetSize = utils.dpiScale(165)
        splitter.setSizes([treeWidgetSize, self.windowWidth - treeWidgetSize])

        self.mainLayout.addWidget(splitter)

        # Bottom buttons
        botButtonsLayout = elements.hBoxLayout(margins=(uic.SMLPAD, uic.SMLPAD, uic.SMLPAD, uic.SMLPAD))

        botButtonsLayout.addWidget(self.saveBtn)
        botButtonsLayout.addWidget(self.applyBtn)
        botButtonsLayout.addWidget(self.resetBtn)
        botButtonsLayout.addWidget(self.cancelBtn)

        self.mainLayout.addLayout(botButtonsLayout)

        self.setMainLayout(self.mainLayout)

    def firstDataSourceWithWidget(self, dataSource):
        """ Recursively gets the first datasource with a widget

        :type dataSource: model.SettingDataSource, model.PathDataSource
        :return:
        """

        if dataSource is None:
            return
        wgt = None
        if dataSource.hasWidget():
            wgt = dataSource.createWidget(parent=self.parent())
        if wgt is not None:
            return dataSource
        for child in dataSource.children:
            source = self.firstDataSourceWithWidget(child)
            if source is not None and source.widget() is not None:
                return source

    def connections(self):
        self.saveBtn.clicked.connect(self.savePressed)
        self.applyBtn.clicked.connect(self.applyPressed)
        self.cancelBtn.clicked.connect(self.cancelPressed)
        self.resetBtn.clicked.connect(self.resetPressed)

    def savePressed(self):
        self.window().hide()
        self.prefStackedWgt.apply()
        self.close()

    def applyPressed(self):
        self.prefStackedWgt.apply()

    def resetPressed(self):
        self.prefStackedWgt.revert()

    def cancelPressed(self):
        self.window().hide()
        self.prefStackedWgt.revert()
        self.close()


class PrefStackedWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(PrefStackedWidget, self).__init__(parent)
        self.titleLabel = elements.TitleLabel(parent=self)
        self._initUi()
        self.source = None  # type: prefmodel.SettingDataSource

    def _initUi(self):
        layout = elements.vBoxLayout(parent=self, margins=(0, 0, 0, 0), spacing=0)
        self._stackedWidget = QtWidgets.QStackedWidget(self)
        titleLayout = elements.vBoxLayout(margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINBOTPAD, uic.WINSIDEPAD),
                                          spacing=0)
        titleLayout.addWidget(self.titleLabel)
        layout.addLayout(titleLayout)
        layout.addWidget(self._stackedWidget)

    def __getattr__(self, item):
        """ Use PrefStackedWidget as if it is using self._stackedWidget

        :param item:
        :return:
        """
        try:
            return getattr(self._stackedWidget, item)
        except:
            raise AttributeError(item)

    def addSource(self, source, activate=True):
        self.addWidget(source.widget())

        if activate:
            self.setSource(source)

    def setSource(self, source):
        self.setTitle(source.label)
        self.setCurrentWidget(source.widget())
        self.source = source

    def setTitle(self, text):
        self.titleLabel.setText(text.upper())

    def apply(self):
        self.source.save()

    def revert(self):
        self.source.revert()


class PrefTreeView(treeviewplus.TreeViewPlus):
    def __init__(self, parent, stackedWidget):
        """ Preference tree view

        :param parent:
        :type parent: PreferencesUI
        :param stackedWidget:
        :type stackedWidget:
        """
        super(PrefTreeView, self).__init__(parent=parent,
                                           expand=True, sorting=False)
        self.setSearchable(True)

        self.prefUi = parent
        self.stackedWidget = stackedWidget  # type: PrefStackedWidget
        self.treeView.setHeaderHidden(True)
        self.treeView.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
        self.selectionChanged.connect(self.onSelectionChangedEvent)
        self.setAlternatingColorEnabled(False)
        self.themePrefs = coreinterfaces.coreInterface()

    def onSelectionChangedEvent(self, event):
        """ Selection changed event

        :param event:
        :type event: zoo.libs.pyqt.extended.treeviewplus.TreeViewPlusSelectionChangedEvent
        :return:
        :rtype:
        """
        # Show the confirmation message box if the settings have been modified.
        if event.prevItems:
            prevSetting = event.prevItems[0]
            if prevSetting.isModified():
                widget = prevSetting.widget()
                if widget is not None:
                    result = widget.showSavedMessageBox(parent=self.parent())
                    if result == 'C':  # it already does the saving/reverting so just pass through for yes or no
                        self.treeView.setCurrentIndex(event.prevIndices[0])
                        return  # dont switch if cancelled, everything else can be let through

        self.switchToSelected()

    def switchToSelected(self):
        """ Sets the ui to widget based on the selected data source

        :return:
        :rtype:
        """
        # Switch
        for dataSource in self.selectedItems():
            wgt = dataSource.createWidget(parent=self.parent())
            if wgt is None:
                return

            if self.stackedWidget.indexOf(wgt) == -1:
                self.stackedWidget.addSource(dataSource)
                break

            self.stackedWidget.setCurrentWidget(wgt)
            self.stackedWidget.setTitle(dataSource.label)
            self.stackedWidget.setSource(dataSource)

            break
