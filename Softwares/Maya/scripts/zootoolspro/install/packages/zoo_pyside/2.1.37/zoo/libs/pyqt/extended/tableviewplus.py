from zoovendor.six.moves import range

from zoo.libs import iconlib
from zoo.libs.pyqt.extended import viewfilterwidget
from zoo.libs.pyqt.models import sortmodel, modelutils
from zoo.libs.pyqt.widgets import tableview, elements
from zoovendor.Qt import QtWidgets, QtCore


class TableViewPlus(QtWidgets.QFrame):
    selectionChanged = QtCore.Signal(object)
    contextMenuRequested = QtCore.Signal(list, object)
    refreshRequested = QtCore.Signal()

    def __init__(self, searchable=False, manualReload=True, parent=None):
        super(TableViewPlus, self).__init__(parent)
        self._refreshing = False
        self._model = None
        self.rowDataSource = None
        self.columnDataSources = []
        self._setupLayouts()
        self.connections()
        self.setSearchable(searchable)
        self.setAllowsManualRefresh(manualReload)

    def registerRowDataSource(self, dataSource):
        self.rowDataSource = dataSource
        dataSource._columnIndex = 0
        if hasattr(dataSource, "delegate"):
            delegate = dataSource.delegate(self.tableView)
            self.tableView.setItemDelegateForColumn(0, delegate)

        self.rowDataSource.model = self._model
        self._model.rowDataSource = dataSource
        self.tableView.verticalHeader().sectionClicked.connect(self.rowDataSource.onVerticalHeaderSelection)
        self.searchWidget.setVisibilityItems(self.rowDataSource.headerText(0))
        width = dataSource.width()
        if width > 0:
            self.tableView.setColumnWidth(0, width)

    def registerColumnDataSources(self, dataSources):
        if not self.rowDataSource:
            raise ValueError("Must assign rowDataSource before columns")
        self.columnDataSources = dataSources
        visItems = []
        for i in range(len(dataSources)):
            source = dataSources[i]
            source.model = self._model
            source._columnIndex = i + 1
            if hasattr(source, "delegate"):
                delegate = source.delegate(self.tableView)
                self.tableView.setItemDelegateForColumn(i + 1, delegate)
            visItems.append(source.headerText(i))
            width = source.width()
            if width > 0:
                self.tableView.setColumnWidth(i + 1, width)

        self._model.columnDataSources = dataSources
        self.searchWidget.setVisibilityItems([self.rowDataSource.headerText(0)] + visItems)

    def setSearchable(self, value):
        self.searchWidget.setVisible(value)

    def setAllowsManualRefresh(self, state):
        if state:
            self.reloadBtn.show()
        else:
            self.reloadBtn.hide()

    def setDragDropMode(self, mode):
        self.tableView.setDragDropMode(mode)
        self.tableView.setDragEnabled(True)
        self.tableView.setDropIndicatorShown(True)
        self.tableView.setAcceptDrops(True)
        self.tableView.setDragDropOverwriteMode(False)
        self.tableView.setDefaultDropAction(QtCore.Qt.MoveAction)

    def _setupFilter(self):
        self.reloadBtn = elements.ExtendedButton(iconlib.icon("reload"),
                                                 parent=self)

        self.searchLayout = elements.hBoxLayout(spacing=0)
        self.searchLayout.addWidget(self.reloadBtn)
        self.searchLayout.addItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        # setup the column search widget
        self.searchWidget = viewfilterwidget.ViewSearchWidget(parent=self)
        self.searchLayout.addWidget(self.searchWidget)
        self.mainLayout.addLayout(self.searchLayout)

    def _setupLayouts(self):

        self.mainLayout = elements.vBoxLayout(self)
        self.tableView = tableview.TableView(parent=self)
        self.tableView.contextMenuRequested.connect(self.contextMenu)
        self._setupFilter()

        self.mainLayout.addWidget(self.tableView)

        self.proxySearch = sortmodel.TableFilterProxyModel(self)
        self.tableView.setModel(self.proxySearch)

    def selectionModel(self):
        return self.tableView.selectionModel()

    def connections(self):
        # self.searchWidget.searchTextedCleared.connect(self.searchEdit.clear)
        self.searchWidget.columnFilterIndexChanged.connect(self.onSearchBoxChanged)
        self.searchWidget.searchTextedChanged.connect(self.proxySearch.setFilterRegularExpression)
        self.searchWidget.columnVisibilityIndexChanged.connect(self.toggleColumn)
        self.reloadBtn.clicked.connect(self.refresh)
        selModel = self.selectionModel()  # had to assign a var otherwise the c++ object gets deleted in PySide1
        selModel.selectionChanged.connect(self.onSelectionChanged)

    def onSelectionChanged(self, current, previous):
        indices = current.indexes()
        self.selectionChanged.emit([self._model.itemFromIndex(i) for i in indices])

    def onSearchBoxChanged(self, index, text):
        self.proxySearch.setFilterKeyColumn(index)

    def model(self):
        return self.tableView.model()

    def setModel(self, model):
        self.proxySearch.setSourceModel(model)
        self.proxySearch.setDynamicSortFilter(True)

        self._model = model
        if self.rowDataSource:
            self.rowDataSource.model = model
        for i in iter(self.columnDataSources):
            i.model = model

    def refresh(self):
        if self._refreshing:
            return
        self._refreshing = True
        try:
            self.refreshRequested.emit()
            rowDataSource = self._model.rowDataSource
            columnDataSources = self._model.columnDataSources
            headerItems = []
            for i in range(len(columnDataSources)):
                headerItems.append(columnDataSources[i].headerText(i))
            self.searchWidget.setHeaderItems([rowDataSource.headerText(0)] + headerItems)
        finally:
            self._refreshing = False

    def contextMenu(self, position):
        menu = QtWidgets.QMenu(self)
        selection = self.selectedRows()
        if self.rowDataSource:
            self.rowDataSource.contextMenu(selection, menu)
        self.contextMenuRequested.emit(selection, menu)
        menu.exec_(self.tableView.viewport().mapToGlobal(position))

    def openPersistentEditor(self, index):
        """ Opens a persistent editor on the item at the given index.
        If no editor exists, the delegate will create a new editor.

        :param index: The index to open.
        :type index: :class:`QModelIndex`
        """
        self.tableView.openPersistentEditor(index)

    def selectedRows(self):
        """From all the selectedIndices grab the row numbers, this use selectionModel.selectedIndexes() to pull the rows
        out
        :return: A list of row numbers
        :rtype: list(int)
        """
        return list(set([i.row() for i in self.selectionModel().selectedIndexes()]))

    def selectedColumns(self):
        return list(set([i.column() for i in self.selectionModel().selectedColumns()]))

    def selectedItems(self):
        indices = self.selectionModel().selection()
        modelIndices = self.proxySearch.mapSelectionToSource(indices).indexes()
        model = self._model
        return list(map(model.itemFromIndex, modelIndices))

    def selectedRowsIndices(self):
        """From all the selectedIndices grab the row numbers, this use selectionModel.selectedIndexes() to pull the rows
        out
        :return: A list of row numbers
        :rtype: list(:class:`QModelIndex`)
        """

        selectedRows = set([i.row() for i in self.selectionModel().selectedIndexes()])
        indices = []
        for row in selectedRows:
            index, _ = modelutils.dataModelIndexFromIndex(self._model.index(row, 0))
            indices.append(index)
        return sorted(indices, key=lambda x: x.row())

    def selectedQIndices(self):
        return self.proxySearch.mapSelectionToSource(self.selectionModel().selection()).indexes()

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        self.tableView.sortByColumn(column, order)

    def toggleColumn(self, column, state):
        if state == QtCore.Qt.Checked:
            self.tableView.showColumn(column)
        else:
            self.tableView.hideColumn(column)
