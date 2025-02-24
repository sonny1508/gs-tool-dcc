from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import extendedmenu, treeview, frame, searchwidget
from zoo.libs.pyqt.extended import clippedlabel
from zoo.libs.pyqt.models import sortmodel, modelutils
from zoovendor.Qt import QtWidgets, QtCore, QtCompat
from zoo.libs.pyqt.widgets import slidingwidget


class TreeViewPlus(frame.QFrame):
    selectionChanged = QtCore.Signal(object)  # TreeViewPlusSelectionChangedEvent
    contextMenuRequested = QtCore.Signal(list, object)
    refreshRequested = QtCore.Signal()

    def __init__(self, title="", parent=None, expand=True, sorting=True):
        super(TreeViewPlus, self).__init__(parent=parent)
        self.setFrameStyle(QtWidgets.QFrame.NoFrame | QtWidgets.QFrame.Plain)
        self.sorting = sorting
        self.model = None
        self.columnDataSources = []
        self.slidingWidget = slidingwidget.SlidingWidget(self)
        self.titleLabel = clippedlabel.ClippedLabel(parent=self, text=title.upper())
        self.toolbarLayout = utils.hBoxLayout(margins=(10, 6, 6, 0), spacing=0)
        self.searchEdit = searchwidget.SearchLineEdit(parent=self)
        self._setupLayouts()
        self.connections()
        if expand:
            self.expandAll()

    def resizeToContents(self):
        header = self.treeView.header()
        QtCompat.setSectionResizeMode(header, header.ResizeToContents)

    def setDragDropMode(self, mode):
        self.treeView.setDragDropMode(mode)
        self.treeView.setDragEnabled(True)
        self.treeView.setDropIndicatorShown(True)
        self.treeView.setAcceptDrops(True)

    def expandAll(self):
        self.treeView.expandAll()

    def collapseAll(self):
        self.treeView.collapseAll()

    def setToolBarVisible(self, value):
        self.slidingWidget.setVisible(value)

    def setSearchable(self, value):
        self.searchEdit.setVisible(value)

    def setShowTitleLabel(self, value):
        self.titleLabel.setVisible(value)

    def supportShiftExpansion(self, state):
        self.treeView.supportsShiftExpand = state

    def setAlternatingColorEnabled(self, alternating):
        """ Disable alternating color for the rows

        :type alternating: bool
        :return:
        """
        if alternating:
            utils.setStylesheetObjectName(self.treeView, "")
        else:
            utils.setStylesheetObjectName(self.treeView, "disableAlternatingColor")
        self.treeView.setAlternatingRowColors(alternating)

    def _setupFilter(self):
        self.searchEdit.setMinimumSize(utils.sizeByDpi(QtCore.QSize(21, 20)))
        self.slidingWidget.setWidgets(self.searchEdit, self.titleLabel)
        self.toolbarLayout.addWidget(self.slidingWidget)
        self.mainLayout.addLayout(self.toolbarLayout)

    def _setupLayouts(self):

        self.mainLayout = utils.vBoxLayout(self)
        self.treeView = treeview.TreeView(parent=self)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.treeView.customContextMenuRequested.connect(self.contextMenu)
        self._setupFilter()

        self.mainLayout.addWidget(self.treeView)

        self.proxySearch = sortmodel.LeafTreeFilterProxyModel(parent=self,
                                                              sort=False)  # sorting will be done in next line
        self.setSortingEnabled(self.sorting)
        self.setAlternatingColorEnabled(True)

    def selectionModel(self):
        return self.treeView.selectionModel()

    def setSortingEnabled(self, enabled):
        self.treeView.setModel(self.proxySearch)
        self.treeView.setSortingEnabled(enabled)
        self.treeView.sortByColumn(0 if enabled else -1, QtCore.Qt.AscendingOrder)
        self.proxySearch.setDynamicSortFilter(enabled)
        if enabled:
            self.proxySearch.setFilterKeyColumn(0)
        self.sorting = enabled

    def selectedItems(self):
        modelIndices = []
        for index in self.selectionModel().selection().indexes():
            modelIndices.append(modelutils.dataModelIndexFromIndex(index)[0])
        model = modelutils.dataModelFromProxyModel(self.model)
        return list(map(model.itemFromIndex, modelIndices))

    def selectedQIndices(self):
        return self.proxySearch.mapSelectionToSource(self.selectionModel().selection()).indexes()

    def openPersistentEditor(self, index):
        """ Opens a persistent editor on the item at the given index.
        If no editor exists, the delegate will create a new editor.

        :param index: The index to open.
        :type index: :class:`QModelIndex`
        """
        self.treeView.openPersistentEditor(index)

    def connections(self):
        self.searchEdit.textChanged.connect(self.proxySearch.setFilterRegularExpression)

        selModel = self.selectionModel()  # had to assign a var otherwise the c++ object gets deleted in PySide1
        selModel.selectionChanged.connect(self.onSelectionChanged)
        self.treeView.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.header().customContextMenuRequested.connect(self._headerMenu)

    def _headerMenu(self, pos):
        globalPos = self.mapToGlobal(pos)
        menu = QtWidgets.QMenu(parent=self)
        headers = self.headerItems()
        for i in range(len(headers)):
            item = QtWidgets.QAction(headers[i], menu, checkable=True)
            menu.addAction(item)
            item.setChecked(not self.treeView.header().isSectionHidden(i))
            item.setData({"index": i})
        selectedItem = menu.exec_(globalPos)
        self.toggleColumn(selectedItem.data()["index"],
                          QtCore.Qt.Checked if selectedItem.isChecked() else QtCore.Qt.Unchecked)

    def setModel(self, model):
        self.proxySearch.setSourceModel(model)
        self.proxySearch.setDynamicSortFilter(self.sorting)
        self.model = model

    def onSelectionChanged(self, current, previous):
        event = TreeViewPlusSelectionChangedEvent(current=current, previous=previous, parent=self)
        self.selectionChanged.emit(event)

    def onSearchBoxChanged(self, index, text):
        self.proxySearch.setFilterKeyColumn(index)

    def headerItems(self):
        headerItems = []
        for index in range(self.model.columnCount(QtCore.QModelIndex())):
            headerItems.append(self.model.root.headerText(index))
        return headerItems

    def refresh(self):
        if not self.model:
            return
        for index in range(self.model.columnCount(QtCore.QModelIndex())):
            self.treeView.resizeColumnToContents(index)
            newWidth = self.treeView.columnWidth(index) + 10
            self.treeView.setColumnWidth(index, newWidth)

    def contextMenu(self, position):
        menu = extendedmenu.ExtendedMenu(parent=self)
        selection = self.selectedItems()
        baseModel = modelutils.dataModelFromProxyModel(self.model)
        if baseModel.root is not None:
            baseModel.root.contextMenu(selection, menu)
        self.contextMenuRequested.emit(selection, menu)
        if max(len(menu.children()) - 4, 0) != 0:
            menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def toggleColumn(self, column, state):
        if column == 0:

            if state == QtCore.Qt.Checked:
                self.treeView.showColumn(0)
            else:
                self.treeView.hideColumn(0)
        else:
            if state == QtCore.Qt.Checked:
                self.treeView.showColumn(column)
            else:
                self.treeView.hideColumn(column)


class TreeViewPlusSelectionChangedEvent(object):
    def __init__(self, current, previous, parent):
        """

        :param parent:
        :type parent: :class:`TreeViewPlus`
        """
        self.indices = current.indexes()
        self.prevIndices = previous.indexes()
        self.parent = parent

    @property
    def currentItems(self):
        items = []
        for i in self.indices:
            sourceIndex, model = modelutils.dataModelIndexFromIndex(i)
            items.append(model.itemFromIndex(sourceIndex))
        return items

    @property
    def prevItems(self):
        items = []
        for i in self.prevIndices:
            sourceIndex, model = modelutils.dataModelIndexFromIndex(i)
            items.append(model.itemFromIndex(sourceIndex))
        return items
