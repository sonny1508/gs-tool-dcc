from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants
from zoo.libs.pyqt.extended import treeviewplus
from zoo.libs.pyqt.models import datasources
from zoo.libs.pyqt.models import treemodel
from zoo.libs.pyqt.widgets import elements
from zoo.apps.toolpalette import run as toolpalette
from zoovendor.Qt import QtWidgets, QtCore, QtGui


class PresetView(treeviewplus.TreeViewPlus):
    def __init__(self, title="presets", parent=None, expand=True, sorting=True):
        super(PresetView, self).__init__(title, parent, expand, sorting)
        self.setSearchable(True)
        self.setAlternatingColorEnabled(False)
        self.treeView.setHeaderHidden(True)
        self._rootSource = PresetDataSource("")
        self.presetModel = treemodel.TreeModel(self._rootSource, parent=self)
        self.setModel(self.presetModel)

        self.spaceOptionsBtn = elements.ExtendedButton(parent=self, icon=iconlib.icon("menudots"))
        self.createPresetBtn = self.spaceOptionsBtn.addAction("Create Preset", icon="chain")
        self.removePresetBtn = self.spaceOptionsBtn.addAction("Remove Preset", icon="trash")
        self.toolbarLayout.addWidget(self.spaceOptionsBtn)

    def loadPreset(self, preset, includeRoot=True, parent=None):
        """ Loads the root preset

        :param preset:
        :type preset: :class:`zoo.libs.hive.base.namingpresets.presets.Preset`
        :type parent: :class:`PresetDataSource`
        """
        self._rootSource.setUserObjects([])
        if includeRoot:
            self._loadPreset(preset, parent=parent)
        else:
            for child in preset.children:
                self._loadPreset(child, parent=parent)
        self.presetModel.reload()
        self.refresh()
        self.expandAll()

    def _loadPreset(self, preset, parent=None):
        """
        :param preset:
        :type preset: :class:`zoo.libs.hive.base.namingpresets.presets.Preset`
        :type parent: :class:`PresetDataSource`
        """
        parent = parent or self._rootSource
        presetDataSource = PresetDataSource(preset.name, parent=parent)
        parent.addChild(presetDataSource)

        for child in preset.children:
            self._loadPreset(child, parent=presetDataSource)


class PresetDataSource(datasources.BaseDataSource):

    def __init__(self, label, previousLabel=None, headerText="Preset Name", model=None, parent=None):
        super(PresetDataSource, self).__init__(headerText, model, parent)
        self.label = label
        self.previousLabel = previousLabel or ""

    def mimeData(self, indices):
        return {"label": self.label,
                "previousLabel": self.previousLabel}
    def dropMimeData(self, items, actions):
        return {"items": items}

    def data(self, index):
        return self.label

    def setData(self, index, value):
        self.previousLabel = str(self.label)
        self.label = value
        return True

    def insertRowDataSource(self, index, label,previousLabel=""):
        return self.insertChild(index, PresetDataSource(label, previousLabel, parent=self))

    def insertRowDataSources(self, index, count, items):
        for item in items:
            self.insertRowDataSource(index, item["label"], item["previousLabel"])


class PresetChooser(QtWidgets.QWidget):
    presetSelectedSig = QtCore.Signal(str)
    beforeBrowseSig = QtCore.Signal()

    def __init__(self, parent):
        super(PresetChooser, self).__init__(parent)
        self.preset = None
        layout = elements.hBoxLayout(self)
        tooltip = "Click to browse and set a `naming convention` preset."
        self.browseBtn = elements.styledButton("Select Preset",
                                               icon="zooRename",
                                               toolTip=tooltip,
                                               parent=self,
                                               minWidth=uiconstants.BTN_W_ICN_REG)
        tooltip = "Opens the `Hive Naming Convention` window."
        self.conventionWindowOpenBtn = elements.styledButton("Naming Convention Window",
                                                             icon="windowBrowser",
                                                             parent=self,
                                                             toolTip=tooltip,
                                                             )
        layout.addWidget(self.browseBtn)
        layout.addWidget(self.conventionWindowOpenBtn)
        self.browseBtn.clicked.connect(self.onBrowse)
        self.conventionWindowOpenBtn.clicked.connect(self.onConventionBtnClicked)
        self._currentWin = None

    def setText(self, text):
        self.browseBtn.setText(text)

    def onBrowse(self):
        pos = QtGui.QCursor.pos()
        self.beforeBrowseSig.emit()
        assert self.preset is not None, "Missing Naming Preset assignment"
        if self._currentWin is not None:
            self._currentWin.move(pos)
            self._currentWin.loadPreset(self.preset)
            self._currentWin.show()
            return
        self._currentWin = PresetView(parent=self)

        self._currentWin.move(pos)
        self._currentWin.setWindowFlags(self._currentWin.windowFlags() | QtCore.Qt.Popup)
        self._currentWin.spaceOptionsBtn.setVisible(False)
        self._currentWin.resize(200, 400)
        self._currentWin.selectionChanged.connect(self.onSelectionChanged)

        self._currentWin.loadPreset(self.preset)
        self._currentWin.show()

    def onConventionBtnClicked(self):
        toolpalette.currentInstance().executePluginById("hive.namingConfig")

    def setPreset(self, preset):
        self.preset = preset

    def onSelectionChanged(self, selection):
        """

        :param selection:
        :type selection: :class:`treeviewplus.TreeViewPlusSelectionChangedEvent`
        """
        name = ""
        for sel in selection.currentItems:
            name = sel.data(0)
            break
        self._currentWin.close()
        self.presetSelectedSig.emit(name)
        self.setText(name)
