from zoovendor.Qt import QtWidgets, QtCore
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import frame, searchwidget
from zoo.libs.pyqt.widgets import slidingwidget
from zoo.libs.pyqt.extended import clippedlabel


class ListViewPlus(frame.QFrame):
    selectionChanged = QtCore.Signal(object)
    contextMenuRequested = QtCore.Signal(list, object)
    refreshRequested = QtCore.Signal()

    def __init__(self, title="", searchable=False, parent=None):
        super(ListViewPlus, self).__init__(parent)
        self._model = None
        self.rowDataSource = None
        self.searchEdit = searchwidget.SearchLineEdit(parent=self)
        self.titleLabel = clippedlabel.ClippedLabel(parent=self, text=title.upper())
        self.slidingWidget = slidingwidget.SlidingWidget(self)
        self.toolbarLayout = utils.hBoxLayout(margins=(10, 6, 6, 0), spacing=0)

        self._setupLayouts()
        self.connections()
        self.setSearchable(searchable)

    def registerRowDataSource(self, dataSource):
        self.rowDataSource = dataSource
        if hasattr(dataSource, "delegate"):
            delegate = dataSource.delegate(self.listview)
            self.listview.setItemDelegateForColumn(0, delegate)
        if self._model is not None:
            self._model.rowDataSource = dataSource

    def expandAll(self):
        self.listview.expandAll()

    def setSearchRole(self, role):
        self.proxySearch.setFilterRole(role)

    def setSearchable(self, value):
        self.searchEdit.setVisible(value)

    def setToolBarVisible(self, value):
        self.slidingWidget.setVisible(value)

    def setToolBarSearchSlidingActive(self, state):
        self.slidingWidget.setSlidingActive(state)

    def setShowTitleLabel(self, value):
        self.titleLabel.setVisible(value)

    def _setupFilter(self):
        self.searchEdit.setMinimumSize(utils.sizeByDpi(QtCore.QSize(21, 20)))
        self.slidingWidget.setWidgets(self.searchEdit, self.titleLabel)
        self.toolbarLayout.addWidget(self.slidingWidget)
        self.mainLayout.addLayout(self.toolbarLayout)
        self.setSearchable(False)

    def _setupLayouts(self):
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.mainLayout.setSpacing(1)
        self.listview = QtWidgets.QListView(parent=self)
        self.listview.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.listview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listview.customContextMenuRequested.connect(self.contextMenu)

        self._setupFilter()

        self.mainLayout.addWidget(self.listview)

        self.proxySearch = QtCore.QSortFilterProxyModel(parent=self)
        self.proxySearch.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.listview.setModel(self.proxySearch)
        # self.listview.setSortingEnabled(True)
        selModel = self.selectionModel()  # had to assign a var otherwise the c++ object gets deleted in PySide1
        selModel.selectionChanged.connect(self.onSelectionChanged)

    def setListViewSpacing(self, spacing):
        self.listview.setSpacing(utils.dpiScale(spacing))

    def setMainSpacing(self, spacing):
        self.mainLayout.setSpacing(utils.dpiScale(spacing))

    def setSearchMargins(self, left, top, right, bottom):
        self.toolbarLayout.setContentsMargins(utils.dpiScale(left),
                                              utils.dpiScale(top),
                                              utils.dpiScale(right),
                                              utils.dpiScale(bottom))

    def selectionModel(self):
        return self.listview.selectionModel()

    def model(self):
        return self.listview.model()

    def rootModel(self):
        return self._model

    def onSelectionChanged(self, current, previous):
        event = ListViewPlusSelectionChangedEvent(current=current, previous=previous, parent=self)
        self.selectionChanged.emit(event)

    def selectedItems(self):
        indices = self.selectionModel().selection()
        modelIndices = self.proxySearch.mapSelectionToSource(indices).indexes()
        model = self._model
        return list(map(model.itemFromIndex, modelIndices))

    def selectedQIndices(self):
        return self.proxySearch.mapSelectionToSource(self.selectionModel().selection()).indexes()

    def connections(self):
        self.searchEdit.textChanged.connect(self.proxySearch.setFilterRegularExpression)

    def setModel(self, model):
        self.proxySearch.setSourceModel(model)
        self._model = model
        self.listview.setModel(self.proxySearch)
        if self.rowDataSource:
            self.rowDataSource.model = model

        self.searchEdit.textChanged.connect(self.proxySearch.setFilterRegularExpression)

    def refresh(self):
        self.refreshRequested.emit()

    def contextMenu(self, position):
        menu = QtWidgets.QMenu(self)
        selection = [int(i.row()) for i in self.selectionModel().selectedIndexes()]
        if self.rowDataSource:
            self.rowDataSource.contextMenu(selection, menu)
        self.contextMenuRequested.emit(selection, menu)
        menu.exec_(self.listview.viewport().mapToGlobal(position))


class ListViewPlusSelectionChangedEvent(object):
    def __init__(self, current, previous, parent):
        """

        :param parent:
        :type parent: :class:`ListViewPlus`
        """
        self.indices = current.indexes()
        self.prevIndices = previous.indexes()
        model = parent.rootModel()
        self.currentItems = [model.itemFromIndex(parent.proxySearch.mapToSource(i)) for i in self.indices]
        self.prevItems = [model.itemFromIndex(parent.proxySearch.mapToSource(i)) for i in self.prevIndices]
