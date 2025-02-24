"""This module is for a standard Qt tree model
"""
from zoovendor import six
from zoovendor.Qt import QtCore, QtCompat
from zoovendor.six.moves import cPickle
from zoo.libs.pyqt.models import constants


def pprintTree(model, item, _prefix="", _last=True):
    treeSep = "`- " if _last else "|- "

    values = [_prefix, treeSep] + [item.data(0) if not item.isRoot() else "root"]
    msg = "".join(values)
    print(msg)
    _prefix += "   " if _last else "|  "
    child_count = item.rowCount()
    for i, child in enumerate(item.children):
        _last = i == (child_count - 1)
        pprintTree(model, child, _prefix, _last)


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, root, parent=None):
        """ Tree Model
        
        :param root: 
        :type root: zoo.libs.pyqt.models.datasources.BaseDataSource
        :param parent: 
        """
        super(TreeModel, self).__init__(parent)
        self.root = root
        if self.root:
            self.root.model = self

    def pprintItemTree(self, item):
        pprintTree(self, item)

    def setRoot(self, root, refresh=False):
        self.root = root
        self.root.model = self
        if refresh:
            self.reload()

    def reload(self):
        """Hard reloads the model, we do this by the modelReset slot, the reason why we do this instead of insertRows()
        is because we expect that the tree structure has already been rebuilt with its children so by calling insertRows
        we would in turn create duplicates.
        """
        self.modelReset.emit()

    def itemFromIndex(self, index):
        """Returns the datasource for the index.

        :param index: The Qt Model index
        :type index: :class:`QtCore.QModelIndex`
        :return:
        :rtype: :class:`zoo.libs.pyqt.models.datasources.BaseDataSource`
        """
        return index.data(constants.userObject) if index.isValid() else self.root

    def rowCount(self, parent):
        if self.root is None:
            return 0
        parentItem = self.itemFromIndex(parent)
        return parentItem.rowCount()

    def columnCount(self, parent):
        if self.root is None:
            return 0
        return self.root.columnCount()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        item = index.internalPointer()
        column = index.column()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return item.data(column)
        elif role == QtCore.Qt.ToolTipRole:
            return item.toolTip(column)
        elif role == QtCore.Qt.DecorationRole:
            return item.icon(column)
        elif role == constants.textMarginRole:
            return item.textMargin(column)
        elif role == QtCore.Qt.CheckStateRole and item.isCheckable(column):
            if item.data(column):
                return QtCore.Qt.Checked
            return QtCore.Qt.Unchecked
        elif role == QtCore.Qt.BackgroundRole:
            color = item.backgroundColor(column)
            if color:
                return color
        elif role == QtCore.Qt.ForegroundRole:
            color = item.foregroundColor(column)
            if color:
                return color
        elif role == QtCore.Qt.TextAlignmentRole:
            return item.alignment(index)
        elif role == QtCore.Qt.FontRole:
            return item.font(column)
        elif role in (constants.sortRole, constants.filterRole):
            return item.data(column)
        elif role == constants.enumsRole:
            return item.enums(column)
        elif role == constants.userObject:
            return item
        elif role == constants.uidRole:
            return item.uid
        elif role in item.customRoles(column):
            return item.dataByRole(column, role)

    def hasChildren(self, index):
        if not index.isValid():
            return super(TreeModel, self).hasChildren(index)
        item = self.itemFromIndex(index)
        return item.hasChildren()

    def canFetchMore(self, index):
        if not index.isValid():
            return False
        item = self.itemFromIndex(index)
        if item is None:
            return False
        return item.canFetchMore()

    def fetchMore(self, index):
        if not index.isValid():
            return

        item = self.itemFromIndex(index)
        if item is not None:
            item.fetchMore()

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False
        pointer = index.internalPointer()
        column = index.column()
        hasChanged = False
        if role == QtCore.Qt.EditRole:
            hasChanged = pointer.setData(column, value)
        elif role == QtCore.Qt.ToolTipRole:
            hasChanged = pointer.setToolTip(column, value)
        elif role in pointer.customRoles(column):
            hasChanged = pointer.setDataByCustomRole(column, value, role)
        if hasChanged:
            QtCompat.dataChanged(self, index, index, [role])
            return True
        return False

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled
        column = index.column()
        pointer = index.internalPointer()
        flags = QtCore.Qt.ItemIsEnabled
        if pointer.supportsDrag(column):
            flags |= QtCore.Qt.ItemIsDragEnabled
        if pointer.supportsDrop(column):
            flags |= QtCore.Qt.ItemIsDropEnabled
        if pointer.isEditable(column):
            flags |= QtCore.Qt.ItemIsEditable
        if pointer.isSelectable(column):
            flags |= QtCore.Qt.ItemIsSelectable
        if pointer.isEnabled(column):
            flags |= QtCore.Qt.ItemIsEnabled
        if pointer.isCheckable(column):
            flags |= QtCore.Qt.ItemIsUserCheckable
        return flags

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def mimeTypes(self):
        return ["application/x-datasource"]

    def mimeData(self, indices):
        """Encode serialized data from the item at the given index into a QMimeData object."""
        data = []
        for i in indices:
            item = self.itemFromIndex(i)
            pickleData = item.mimeData(i)
            if pickleData:
                data.append(pickleData)

        mimedata = QtCore.QMimeData()
        if data:
            mimedata.setData("application/x-datasource", cPickle.dumps(data))

        return mimedata

    def dropMimeData(self, mimeData, action, row, column, parentIndex):
        if action == QtCore.Qt.IgnoreAction:
            return False
        if not mimeData.hasFormat("application/x-datasource"):
            return super(TreeModel, self).dropMimeData(mimeData, action, row, column, parentIndex)
        data = six.binary_type(mimeData.data("application/x-datasource"))
        items = cPickle.loads(data)
        if not items:
            return False

        dropParent = self.itemFromIndex(parentIndex)
        returnKwargs = dropParent.dropMimeData(items, action)
        if not returnKwargs:
            return False
        self.insertRows(row, len(items), parentIndex, **returnKwargs)
        if action == QtCore.Qt.CopyAction:
            return False  # don't delete just copy over
        return True

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return self.root.headerText(section)
            elif role == QtCore.Qt.DecorationRole:
                icon = self.root.headerIcon()
                if icon.isNull:
                    return
                return icon.pixmap(icon.availableSizes()[-1])
        return None

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parentItem = self.itemFromIndex(parent)

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)

        return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parentSource()
        if parentItem == self.root or parentItem is None:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.index(), 0, parentItem)

    def insertRow(self, position, parent=QtCore.QModelIndex(), **kwargs):
        parentItem = self.itemFromIndex(parent)
        position = max(0, min(parentItem.rowCount(), position))
        self.beginInsertRows(parent, position, position)
        parentItem.insertRowDataSource(position, **kwargs)
        self.endInsertRows()

        return True

    def insertRows(self, position, count, parent=QtCore.QModelIndex(), **kwargs):
        parentItem = self.itemFromIndex(parent)
        position = max(0, min(parentItem.rowCount(), position))
        lastRow = max(0, position + count - 1)

        self.beginInsertRows(parent, position, lastRow)
        parentItem.insertRowDataSources(int(position), int(count), **kwargs)
        self.endInsertRows()

        return True

    def removeRows(self, position, count, parent=QtCore.QModelIndex(), **kwargs):
        parentNode = self.itemFromIndex(parent)

        position = max(0, min(parentNode.rowCount(), position))
        lastRow = max(0, position + count - 1)
        self.beginRemoveRows(parent, position, lastRow)
        result = parentNode.removeRowDataSources(int(position), int(count), **kwargs)
        self.endRemoveRows()

        return result

    def removeRow(self, position, parent=QtCore.QModelIndex()):
        return self.removeRows(position, 1, parent=parent)

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
