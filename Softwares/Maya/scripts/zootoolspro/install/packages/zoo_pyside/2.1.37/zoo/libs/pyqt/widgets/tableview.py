from zoovendor.Qt import QtWidgets, QtCore, QtCompat


class TableView(QtWidgets.QTableView):
    contextMenuRequested = QtCore.Signal()

    def __init__(self, parent):
        super(TableView, self).__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSortingEnabled(True)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        QtCompat.setSectionResizeMode(self.verticalHeader(), QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.customContextMenuRequested.connect(self.contextMenuRequested.emit)
