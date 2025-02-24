from zoovendor.Qt import QtCore, QtCompat
from zoo.libs.pyqt.models import constants


class ListModel(QtCore.QAbstractTableModel):
    sortRole = QtCore.Qt.UserRole
    filterRole = QtCore.Qt.UserRole + 1
    userObject = QtCore.Qt.UserRole + 2

    def __init__(self, parent=None):
        """first element is the rowDataSource
        :param parent:
        :type parent:
        """
        super(ListModel, self).__init__(parent=parent)
        self.rowDataSource = None

    def reload(self):
        """Hard reloads the model, we do this by the modelReset slot, the reason why we do this instead of insertRows()
        is because we expect that the tree structure has already been rebuilt with its children so by calling insertRows
        we would in turn create duplicates.

        """
        self.modelReset.emit()

    def rowCount(self, parent):
        if parent.column() > 0 or not self.rowDataSource:
            return 0
        return self.rowDataSource.rowCount()

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None

        row = int(index.row())
        dataSource = self.rowDataSource

        if dataSource is None:
            return
        kwargs = {"index": row}

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
                      constants.userObject: dataSource.userObject,
                      constants.iconSizeRole: dataSource.iconSize
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
        elif role in dataSource.customRoles(**kwargs):
            return dataSource.dataByRole(role=role, **kwargs)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or not self._rowDataSource:
            return False
        rowDataSource = self._rowDataSource
        hasChanged = False
        column = index.row()
        if role == QtCore.Qt.EditRole:
            hasChanged = rowDataSource.setData(column, value)
        elif role == constants.enumsRole:
            hasChanged = rowDataSource.setEnums(column, value)
        elif role == QtCore.Qt.ToolTipRole:
            hasChanged = rowDataSource.setToolTip(column, value)
        elif role in rowDataSource.customRoles(column):
            hasChanged = rowDataSource.setDataByCustomRole(column, value, role)
        if hasChanged:
            QtCompat.dataChanged(self, index, index, [role])
            return True
        return False

    def mimeTypes(self):
        return self.rowDataSource.mimeTypes()

    def mimeData(self, indices):
        return self.rowDataSource.mimeData(indices)

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def flags(self, index):
        if not index.isValid() or not self.rowDataSource:
            return QtCore.Qt.NoItemFlags
        row = index.row()
        dataSource = self.rowDataSource

        flags = QtCore.Qt.ItemIsEnabled
        if dataSource.supportsDrag(row):
            flags |= QtCore.Qt.ItemIsDragEnabled
        if dataSource.supportsDrop(row):
            flags |= QtCore.Qt.ItemIsDropEnabled
        if dataSource.isEditable(row):
            flags |= QtCore.Qt.ItemIsEditable
        if dataSource.isSelectable(row):
            flags |= QtCore.Qt.ItemIsSelectable
        if dataSource.isEnabled(row):
            flags |= QtCore.Qt.ItemIsEnabled
        if dataSource.isCheckable(row):
            flags |= QtCore.Qt.ItemIsUserCheckable
        return flags

    def headerData(self, section, orientation, role):
        dataSource = self.rowDataSource
        if role == QtCore.Qt.DisplayRole:
            return dataSource.headerText(section)
        elif role == QtCore.Qt.DecorationRole:
            icon = dataSource.headerIcon(section)
            if icon.isNull:
                return
            return icon.pixmap(icon.availableSizes()[-1])
        return None

    def insertRow(self, position, parent=QtCore.QModelIndex(), **kwargs):
        self.beginInsertRows(parent, position, position)
        result = self.rowDataSource.insertRowDataSource(int(position), **kwargs)
        self.endInsertRows()

        return result

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        self.rowDataSource.insertRowDataSources(int(position), int(rows))
        self.endInsertRows()
        return True

    def itemFromIndex(self, index):
        """Returns the user Object from the rowDataSource

        :param index:
        :type index: QtCore.Qt.QModelIndex
        :return:
        :rtype:
        """
        return index.data(self.userObject) if index.isValid() else self.rowDataSource.userObject(index.row())
