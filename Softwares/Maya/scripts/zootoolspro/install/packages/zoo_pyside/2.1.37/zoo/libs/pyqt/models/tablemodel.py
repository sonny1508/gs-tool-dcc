from zoovendor.Qt import QtCore, QtCompat
from zoo.libs.pyqt.models import constants
from zoovendor import six
from zoovendor.six.moves import cPickle


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        """first element is the rowDataSource

        :param parent:
        :type parent: :class:`QtWidgets.QWidget`
        """
        super(TableModel, self).__init__(parent=parent)
        self._rowDataSource = None
        self.columnDataSources = []

    @property
    def rowDataSource(self):
        return self._rowDataSource

    @rowDataSource.setter
    def rowDataSource(self, source):
        self._rowDataSource = source

    def columnDataSource(self, index):
        if not self._rowDataSource or not self.columnDataSources:
            return

        return self.columnDataSources[index - 1]

    def dataSource(self, index):
        """
        :param index: The column index
        :type index: int
        :return:
        :rtype: :class:`zoo.libs.pyqt.models.datasources.BaseDataSource`
        """
        if index == 0:
            return self._rowDataSource
        return self.columnDataSources[index - 1]

    def reload(self):
        """Hard reloads the model, we do this by the modelReset slot, the reason why we do this instead of insertRows()
        is because we expect that the tree structure has already been rebuilt with its children so by calling insertRows
        we would in turn create duplicates.
        """
        self.modelReset.emit()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.column() > 0 or not self._rowDataSource or not self.columnDataSources:
            return 0
        return self._rowDataSource.rowCount()

    def columnCount(self, parent=QtCore.QModelIndex()):
        if not self._rowDataSource or not self.columnDataSources:
            return 0
        return len(self.columnDataSources) + 1

    def data(self, index, role):
        if not index.isValid():
            return None

        column = int(index.column())
        row = int(index.row())
        dataSource = self.dataSource(column)

        if dataSource is None:
            return
        if column == 0:
            kwargs = {"index": row}
        else:
            kwargs = {"rowDataSource": self._rowDataSource,
                      "index": row}
        roleToFunc = {QtCore.Qt.DisplayRole: dataSource.data,
                      QtCore.Qt.EditRole: dataSource.data,
                      QtCore.Qt.ToolTipRole: dataSource.toolTip,
                      QtCore.Qt.DecorationRole: dataSource.icon,
                      constants.textMarginRole: dataSource.textMargin,
                      constants.editChangedRole: dataSource.displayChangedColor,
                      QtCore.Qt.TextAlignmentRole: dataSource.alignment,
                      QtCore.Qt.FontRole: dataSource.font,
                      QtCore.Qt.BackgroundRole: dataSource.backgroundColor,
                      QtCore.Qt.ForegroundRole: dataSource.foregroundColor,

                      }
        func = roleToFunc.get(role)
        if func is not None:
            return func(**kwargs)
        elif role == QtCore.Qt.CheckStateRole and dataSource.isCheckable(**kwargs):
            if dataSource.data(**kwargs):
                return QtCore.Qt.Checked
            return QtCore.Qt.Unchecked
        elif role == constants.minValue:
            return dataSource.minimum(**kwargs)
        elif role == constants.maxValue:
            return dataSource.maximum(**kwargs)
        elif role == constants.enumsRole:
            return dataSource.enums(**kwargs)
        elif role == constants.userObject:
            return dataSource.userObject(row)
        elif role in dataSource.customRoles(**kwargs):
            return dataSource.dataByRole(role=role, **kwargs)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or not self._rowDataSource:
            return False
        if role == QtCore.Qt.EditRole:
            column = index.column()
            rowDataSource = self._rowDataSource
            if column == 0:
                result = rowDataSource.setData(index.row(), value)
            else:
                result = self.columnDataSources[column - 1].setData(rowDataSource, index.row(), value)
            if result:
                QtCompat.dataChanged(self, index, index)
                return True
        elif role == constants.enumsRole:
            column = index.column()
            rowDataSource = self._rowDataSource
            if column == 0:
                result = rowDataSource.setEnums(index.row(), value)
            else:
                result = self.columnDataSources[column - 1].setEnums(rowDataSource, index.row(), value)
            if result:
                QtCompat.dataChanged(self, index, index)
                return True
        return False

    def flags(self, index):
        rowDataSource = self._rowDataSource
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled if rowDataSource.supportsDrop(-1) else QtCore.Qt.NoItemFlags
        row = index.row()
        column = index.column()
        dataSource = self.dataSource(column)

        if column == 0:
            kwargs = {"index": row}
        else:
            kwargs = {"rowDataSource": self._rowDataSource,
                      "index": row}
        flags = QtCore.Qt.ItemIsEnabled
        if rowDataSource.supportsDrag(row):
            flags |= QtCore.Qt.ItemIsDragEnabled
        if rowDataSource.supportsDrop(row):
            flags |= QtCore.Qt.ItemIsDropEnabled
        if dataSource.isEditable(**kwargs):
            flags |= QtCore.Qt.ItemIsEditable
        if dataSource.isSelectable(**kwargs):
            flags |= QtCore.Qt.ItemIsSelectable
        if dataSource.isEnabled(**kwargs):
            flags |= QtCore.Qt.ItemIsEnabled
        if dataSource.isCheckable(**kwargs):
            flags |= QtCore.Qt.ItemIsUserCheckable
        return flags

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            dataSource = self.dataSource(section)

            if role == QtCore.Qt.DisplayRole:
                return dataSource.headerText(section)
            elif role == QtCore.Qt.DecorationRole:
                icon = dataSource.headerIcon()
                if icon.isNull:
                    return
                return icon.pixmap(icon.availableSizes()[-1])

        elif orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                return self._rowDataSource.headerVerticalText(section)
            elif role == QtCore.Qt.DecorationRole:
                icon = self._rowDataSource.headerVerticalIcon(section)
                if icon.isNull():
                    return
                return icon.pixmap(icon.availableSizes()[-1])
        return None

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def mimeTypes(self):
        return ["application/x-datasource"]

    def mimeData(self, indices):
        """Encode serialized data from the item at the given index into a QMimeData object."""
        rowDataSource = self._rowDataSource
        # grab only the rows #todo: we should technically support columns but it's more common
        # in vfx etc to only move data around.
        visited = set()
        indexes = []
        for index in indices:
            if index.row() in visited:
                continue
            visited.add(index.row())
            indexes.append(index)
        data = rowDataSource.mimeData(indexes)
        mimedata = QtCore.QMimeData()
        if data:
            mimedata.setData("application/x-datasource", cPickle.dumps(data))
        return mimedata

    def dropMimeData(self, mimeData, action, row, column, parent):
        if action == QtCore.Qt.IgnoreAction:
            return False
        if not mimeData.hasFormat("application/x-datasource"):
            return super(TableModel, self).dropMimeData(mimeData, action, row, column, parent)
        data = six.binary_type(mimeData.data("application/x-datasource"))
        items = cPickle.loads(data)
        if not items:
            return False
        rowDataSource = self._rowDataSource
        returnKwargs = rowDataSource.dropMimeData(items, action)
        if not returnKwargs:
            return False
        beginRow = row
        if row == -1:
            if parent.isValid():
                beginRow = parent.row() + 1  # insert above the current row
            else:
                beginRow = self.rowCount(parent)
        # when dropping onto a row and between rows the parent is the row which isn't valid in tables
        # since indexes don't have children in tables so insert to the rootIndex
        self.insertRows(beginRow, len(items), QtCore.QModelIndex(), **returnKwargs)

        if action == QtCore.Qt.CopyAction:
            return False  # don't delete just copy over
        return True

    def insertRow(self, position, parent=QtCore.QModelIndex(), **kwargs):
        return self.insertRows(position, 1, parent, **kwargs)

    def insertRows(self, position, count, parent=QtCore.QModelIndex(), **kwargs):
        self.beginInsertRows(parent, position, position + count - 1)
        result = self._rowDataSource.insertRowDataSources(int(position), int(count), **kwargs)
        self.endInsertRows()

        return result

    def insertColumns(self, position, columns, parent=QtCore.QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        result = self._rowDataSource.insertColumnDataSources(int(position), int(columns))
        self.endInsertColumns()

        return result

    def removeRow(self, position, parent=QtCore.QModelIndex()):
        return self.removeRows(position, 1, parent)

    def removeRows(self, position, count, parent=QtCore.QModelIndex(), **kwargs):
        self.beginRemoveRows(parent, position, position + count - 1)
        result = self._rowDataSource.removeRowDataSources(int(position), int(count), **kwargs)
        for column in self.columnDataSources:
            column.removeRowDataSources(self._rowDataSource, int(position), int(count), **kwargs)
        self.endRemoveRows()
        return result

    def removeColumn(self, row, parent):
        return True

    def removeColumns(self, row, count, parent):
        return True

    def moveRow(self, sourceParent, sourceRow, destinationParent, destinationChild):
        return self.moveRows(sourceParent, sourceRow, 1, destinationParent, destinationChild)

    def moveRows(self, sourceParent, sourceRow, count,
                 destinationParent, destinationChild):
        indices = []
        for i in range(sourceRow, sourceRow + count):
            childIndex = self.index(i, 0, parent=sourceParent)
            if childIndex.isValid():
                indices.append(childIndex)
        mimeData = self.mimeData(indices)
        self.removeRows(sourceRow, count, parent=sourceParent)
        self.dropMimeData(mimeData, QtCore.Qt.MoveAction, destinationChild, 0, destinationParent)

    def itemFromIndex(self, index):
        """Returns the user Object from the rowDataSource
        :param index:
        :type index:
        :return:
        :rtype:
        """
        return index.data() if index.isValid() else self._rowDataSource.userObject(index.row())

    def sort(self, column, order):
        """Sort table by given column number.
        """

        self.layoutAboutToBeChanged.emit()
        if column == 0:
            self.rowDataSource.sort(index=column, order=order)
        else:
            self.columnDataSources[column - 1].sort(rowDataSource=self.rowDataSource, index=column, order=order)
        self.layoutChanged.emit()
