from zoovendor.Qt import QtCore
from zoovendor.Qt import _QtCore as noCompatQtCore


class RootIndexProxyModel(noCompatQtCore.QIdentityProxyModel):
    """A proxy model which filters out the root index of a model, so only the children of the root index are shown
    """
    rootIndexChanged = QtCore.Signal()

    def __init__(self, parent):
        super(RootIndexProxyModel, self).__init__(parent)

        # current root index for the model, we filter this out from the model so only the children of
        # the model exists in the proxyModel
        self._filterRole = QtCore.Qt.DisplayRole
        self._rootIndex = QtCore.QPersistentModelIndex()
        # model connections which get setup per setSourceModel
        self._sourceConnections = []
        self._layoutChangePersistentIndexes = []  # type QList<QPersistentModelIndex>
        self._proxyIndexes = []
        self._rootRowDeleted = False
        self._rootColumnDeleted = False

    def setRootIndex(self, index):
        if not index.isValid():
            self.beginResetModel()
            # ability to clear the model when we pass a invalid index
            self._rootIndex = QtCore.QPersistentModelIndex()
            self.endResetModel()
            self.rootIndexChanged.emit()
            return

        assert (index.model() == self.sourceModel()), "setRootIndex The Root index must be a index of the sourceModel"
        if self._rootIndex == index:
            return
        self.beginResetModel()
        self._rootIndex = QtCore.QPersistentModelIndex(index)
        self.endResetModel()
        self.rootIndexChanged.emit()

    def rootIndex(self):
        return self._rootIndex

    def index(self, row, column, parent):
        if not self.sourceModel() or not self._rootIndex.isValid():
            return QtCore.QModelIndex()

        sourceParent = self._rootIndex
        if parent.isValid():
            sourceParent = self.mapToSource(parent)

        sourceIndex = self.sourceModel().index(row, column, sourceParent)
        return self.mapFromSource(sourceIndex)

    def rowCount(self, parent=QtCore.QModelIndex()):

        if not self.sourceModel() or not self._rootIndex.isValid():
            return 0
        sourceParent = self._rootIndex
        if parent.isValid():
            sourceParent = self.mapToSource(parent)
        return self.sourceModel().rowCount(sourceParent)

    def columnCount(self, parent):
        _source = self.sourceModel()

        if not self.sourceModel():
            return 0

        sourceParent = self._rootIndex
        if parent.isValid():
            sourceParent = self.mapToSource(parent)

        return self.sourceModel().columnCount(sourceParent)

    def insertRows(self, row, count, parent):

        if not self.sourceModel():
            return False
        sourceParent = self._rootIndex
        if parent.isValid():
            sourceParent = self.mapToSource(parent)

        return self.sourceModel().insertRows(row, count, sourceParent)

    def insertColumns(self, column, count, parent):

        if not self.sourceModel():
            return False
        sourceParent = self._rootIndex
        if parent.isValid():
            sourceParent = self.mapToSource(parent)
        return self.sourceModel().insertColumns(column, count, sourceParent)

    def removeColumns(self, column, count, parent):

        if not self.sourceModel():
            return False
        sourceParent = self._rootIndex
        if parent.isValid():
            sourceParent = self.mapToSource(parent)

        return self.sourceModel().removeColumns(column, count, sourceParent)

    def removeRows(self, row, count, parent):

        if not self.sourceModel():
            return False
        sourceParent = self._rootIndex
        if parent.isValid():
            sourceParent = self.mapToSource(parent)

        return self.sourceModel().removeRows(row, count, sourceParent)

    def mapFromSource(self, sourceIndex):

        if not self.sourceModel() or not sourceIndex.isValid():
            return QtCore.QModelIndex()

        if self._rootIndex.isValid():
            if not self.isDescendant(sourceIndex, self._rootIndex):
                return QtCore.QModelIndex()

        return super(RootIndexProxyModel, self).mapFromSource(sourceIndex)

    def mapToSource(self, proxyIndex):

        if not self.sourceModel():
            return QtCore.QModelIndex()

        sourceIndex = super(RootIndexProxyModel, self).mapToSource(proxyIndex)
        return sourceIndex

    def isDescendant(self, childIdx, parentIdx):
        if not parentIdx.isValid():
            return True
        if childIdx.model() != parentIdx.model():
            raise TypeError("The child and parent index must be indexes of the same model")
        while childIdx.isValid():
            if childIdx == parentIdx:
                return True
            childIdx = childIdx.parent()
        return False

    def onRowsAboutToBeInserted(self, parent, first, last):

        if self._rootIndex.isValid():
            if self.isDescendant(self._rootIndex, parent):
                return
        self.beginInsertRows(self.mapFromSource(parent), first, last)

    def onRowsInserted(self, parent, first, last):
        if self._rootIndex.isValid() and self.isDescendant(self._rootIndex, parent):
            return
        self.endInsertRows()

    def onRowsAboutToBeRemoved(self, parent, first, last):
        if self._rootIndex.isValid() and self.isDescendant(self._rootIndex, parent):
            return
        self.beginRemoveRows(self.mapFromSource(parent), first, last)

    def onRowsRemoved(self, parent, first, last):
        if self._rootIndex.isValid() and self.isDescendant(self._rootIndex, parent):
            return
        if self._rootColumnDeleted:
            self._rootColumnDeleted = False
        else:
            self.endRemoveRows()

    def onColumnsAboutToBeInserted(self, parent, first, last):
        if self._rootIndex.isValid() and self.isDescendant(self._rootIndex, parent):
            return
        self.beginInsertColumns(self.mapFromSource(parent), first, last)

    def onColumnsInserted(self, parent, first, last):
        if self._rootIndex.isValid() and self.isDescendant(self._rootIndex, parent):
            return
        self.endInsertColumns()

    def onColumnsAboutToBeRemoved(self, parent, first, last):
        if self._rootIndex.isValid() and self.isDescendant(self._rootIndex, parent):
            return
        self.beginRemoveColumns(self.mapFromSource(parent), first, last)

    def onColumnsRemoved(self, parent, first, last):
        if self._rootIndex.isValid() and self.isDescendant(self._rootIndex, parent):
            self.endRemoveColumns()
            return

        if self._rootColumnDeleted:
            self._rootColumnDeleted = False
        else:
            self.endRemoveColumns()

    def onDataChanged(self, topLeft, bottomRight, roles):

        if self._rootIndex.isValid() and self.isDescendant(self._rootIndex, topLeft.parent()):
            return
        self.dataChanged(self.mapFromSource(topLeft), self.mapFromSource(bottomRight), roles)

    def onLayoutAboutToBeChanged(self, sourceParents, hint):
        parents = []
        addedInvalidIndex = False
        for parent in sourceParents:
            if not parent.isValid() or self.isDescendant(self._rootIndex, parent):
                if not addedInvalidIndex:
                    addedInvalidIndex = True
                    parents.append(QtCore.QPersistentModelIndex())

                continue

            mappedParent = self.mapFromSource(parent)
            parents.append(mappedParent)

        self.layoutAboutToBeChanged(parents, hint)
        proxyPersistentIndexes = self.persistentIndexList()
        for proxyPersistentIndex in proxyPersistentIndexes:
            self._proxyIndexes.append(proxyPersistentIndex)
            srcPersistentIndex = self.mapToSource(proxyPersistentIndex)
            self._layoutChangePersistentIndexes.append(srcPersistentIndex)

    def onLayoutChanged(self, sourceParents, hint):

        for i in range(len(self._proxyIndexes)):
            self.changePersistentIndex(self._proxyIndexes[i], self.mapFromSource(self.layoutChangePersistentIndexes[i]))

        self.layoutChangePersistentIndexes.clear()
        self.proxyIndexes.clear()
        parents = []
        addedInvalidIndex = False
        for parent in sourceParents:
            if not parent.isValid() or self.isDescendant(self._rootIndex, parent):
                if not addedInvalidIndex:
                    addedInvalidIndex = True
                    parents.append(QtCore.QPersistentModelIndex())
                continue

            mappedParent = self.mapFromSource(parent)
            parents.append(mappedParent)

        self.layoutChanged(parents, hint)

    def checkRootRowRemoved(self, parent, first, last):
        if not self._rootIndex.isValid() or not self.isDescendant(self._rootIndex, parent):
            return
        if first <= self._rootIndex.row() <= last:
            self._rootRowDeleted = True
            self.setRootIndex(QtCore.QModelIndex())

    def checkRootColumnsRemoved(self, parent, first, last):

        if not self._rootIndex.isValid() or not self.isDescendant(self._rootIndex, parent):
            return
        if first <= self._rootIndex.column() <= last:
            self._rootColumnDeleted = True
            self.setRootIndex(QtCore.QModelIndex())

    def moveColumns(self, sourceParent, sourceColumn, count, destinationParent, destinationChild):

        sourceModel = self.sourceModel()
        if not sourceModel:
            return False
        srcParent = self._rootIndex
        destParent = self._rootIndex

        if sourceParent.isValid():
            srcParent = self.mapToSource(sourceParent)
        if destinationParent.isValid():
            destParent = self.mapToSource(destinationParent)
        return sourceModel.moveColumns(srcParent, sourceColumn, count, destParent, destinationChild)

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):

        sourceModel = self.sourceModel
        if not sourceModel:
            return False
        srcParent = self._rootIndex
        destParent = self._rootIndex
        if sourceParent.isValid():
            srcParent = self.mapToSource(sourceParent)
        if destinationParent.isValid():
            destParent = self.mapToSource(destinationParent)
        return sourceModel.moveColumns(srcParent, sourceRow, count, destParent, destinationChild)

    def onRowsAboutToBeMoved(self, sourceParent, sourceStart, sourceEnd, destParent, dest):

        if self.isDescendant(self._rootIndex, destParent) == self.isDescendant(self._rootIndex, sourceParent):
            if self.isDescendant(self._rootIndex, destParent):
                return
            self.beginMoveRows(self.mapFromSource(sourceParent), sourceStart, sourceEnd, self.mapFromSource(destParent),
                               dest)

        elif self.isDescendant(self._rootIndex, destParent):
            self.beginRemoveRows(self.mapFromSource(sourceParent), sourceStart, sourceEnd)
        else:
            self.beginInsertRows(self.mapFromSource(destParent), dest, dest + sourceEnd - sourceStart)

    def onRowsMoved(self, sourceParent, sourceStart, sourceEnd, destParent, dest):

        if self.isDescendant(self._rootIndex, destParent) == self.isDescendant(self._rootIndex, sourceParent):
            if self.isDescendant(self._rootIndex, destParent):
                return
            self.endMoveRows()

        elif self.isDescendant(self._rootIndex, destParent):
            self.endRemoveRows()
        else:
            self.endInsertRows()

    def onColumnsMoved(self, sourceParent, sourceStart, sourceEnd, destParent, dest):

        if self.isDescendant(self._rootIndex, destParent) == self.isDescendant(self._rootIndex, sourceParent):
            if self.isDescendant(self._rootIndex, destParent):
                return
            self.endMoveColumns()
        elif self.isDescendant(self._rootIndex, destParent):
            self.endRemoveColumns()
        else:
            self.endInsertColumns()

    def onColumnsAboutToBeMoved(self, sourceParent, sourceStart, sourceEnd, destParent, dest):

        if self.isDescendant(self._rootIndex, destParent) == self.isDescendant(self._rootIndex, sourceParent):
            if self.isDescendant(self._rootIndex, destParent):
                return
            self.beginMoveColumns(self.mapFromSource(sourceParent), sourceStart, sourceEnd,
                                  self.mapFromSource(destParent), dest)

        elif self.isDescendant(self._rootIndex, destParent):
            self.beginRemoveColumns(self.mapFromSource(sourceParent), sourceStart, sourceEnd)
        else:
            self.beginInsertColumns(self.mapFromSource(destParent), dest, dest + sourceEnd - sourceStart)

    def _disconnectAllSignals(self):
        for connection in self._sourceConnections:
            if connection:
                self.disconnect(connection)
        self._sourceConnections = []

    def setSourceModel(self, sourceModel):
        self._disconnectAllSignals()
        if sourceModel is not None:
            self._sourceConnections = [
                sourceModel.rowsAboutToBeRemoved.connect(self.onRowsAboutToBeRemoved),
                sourceModel.columnsAboutToBeRemoved.connect(self.onColumnsAboutToBeRemoved),
                sourceModel.rowsRemoved.connect(self.onRowsRemoved),
                sourceModel.columnsRemoved.connect(self.onColumnsRemoved),
                sourceModel.rowsAboutToBeInserted.connect(self.onRowsAboutToBeInserted),
                sourceModel.columnsAboutToBeInserted.connect(self.onColumnsAboutToBeInserted),
                sourceModel.rowsInserted.connect(self.onRowsInserted),
                sourceModel.columnsInserted.connect(self.onColumnsInserted),
                sourceModel.dataChanged.connect(self.onDataChanged),
                sourceModel.layoutAboutToBeChanged.connect(self.onLayoutAboutToBeChanged),
                sourceModel.layoutChanged.connect(self.onLayoutChanged),
                sourceModel.rowsAboutToBeRemoved.connect(self.checkRootRowRemoved),
                sourceModel.columnsAboutToBeRemoved.connect(self.checkRootColumnsRemoved),
                sourceModel.rowsMoved.connect(self.onRowsMoved),
                sourceModel.columnsMoved.connect(self.onColumnsMoved)
            ]

        super(RootIndexProxyModel, self).setSourceModel(sourceModel)
