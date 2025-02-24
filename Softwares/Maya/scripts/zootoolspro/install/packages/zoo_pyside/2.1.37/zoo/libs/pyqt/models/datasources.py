"""This Module contains generic classes for handle table model data items
Broken into to main base classes:

    BaseDataSource - Used to represent Table rows
    ColumnDataSource - Used to represent Table columns

Subclasses defined here contain linked delegates based on dataType i.e list == combobox

"""
import uuid

from zoo.libs.pyqt.models import delegates, constants
from zoo.libs.pyqt import utils
from zoovendor.Qt import QtCore, QtGui


class BaseDataSource(QtCore.QObject):
    enabledColor = QtGui.QColor("#C4C4C4")
    disabledColor = QtGui.QColor("#5E5E5E")

    def __init__(self, headerText=None, model=None, parent=None):
        super(BaseDataSource, self).__init__()
        self._parent = parent  # type: BaseDataSource
        self._children = []  # type: list[BaseDataSource]
        self.model = model
        self._columnIndex = 0
        self._headerText = headerText or ""
        self._font = None
        self.uid = str(uuid.uuid4())
        self._defaultTextMargin = utils.dpiScale(5)

    def __eq__(self, other):
        return isinstance(other, BaseDataSource) and self.uid == other.uid

    @property
    def children(self):
        return self._children

    def iterChildren(self, recursive=True):
        for child in self._children:
            yield child
            if not recursive:
                continue
            for subChild in child.iterChildren(recursive=recursive):
                yield subChild

    def modelIndex(self):
        if self.model is None:
            return QtCore.QModelIndex()
        indices = self.model.match(self.model.index(0, 0),
                                   constants.uidRole,
                                   self.uid, 1, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
        if indices:
            return indices[0]
        return QtCore.QModelIndex()

    def width(self):
        return 0

    def userObject(self, index):
        if index < self.rowCount():
            return self.userObjects()[index]

    def userObjects(self):
        return self._children

    def setUserObjects(self, objects):
        self._children = objects

    def hasChildren(self):
        return self.rowCount() != 0

    def canFetchMore(self):
        return False

    def fetchMore(self):
        pass

    def isRoot(self):
        """Determines if this item is the root of the tree

        :return:
        :rtype:
        """
        return self._parent is None

    def rowCount(self):
        """Returns the total row count for the dataSource defaults to the len of the dataSource children

        :rtype: int
        """
        return len(self._children)

    def columnCount(self):
        return 1

    def parentSource(self):
        """Returns the parent of this node

        :rtype: Node
        """
        return self._parent

    def setParentSource(self, parentSource):
        if self._parent is not None:
            try:
                self._parent.children.remove(self)
            except ValueError:
                pass
        self.model = parentSource.model
        self._parent = parentSource
        parentSource.addChild(self)

    def index(self):
        parent = self.parentSource()
        if parent is not None and parent.children:
            return parent.children.index(self)
        return 0

    def child(self, index):
        """
        :param index: the column index
        :type index: int
        """
        if index < self.rowCount():
            return self._children[index]

    def addChild(self, child):
        if child not in self._children:
            child.model = self.model
            self._children.append(child)
            return child

    def insertChild(self, index, child):
        if child not in self._children:
            child.model = self.model
            self._children.insert(index, child)
            return True
        return False

    def insertChildren(self, index, children):
        for child in children:
            child.model = self.model
        self._children[index:index] = children

    def setData(self, index, value):
        """Sets the text value of this node at the specified column

        :param index: The column index
        :type index: int
        :return: the new text value for this nodes column index
        :rtype: str
        """
        pass

    def data(self, index):
        """The text for this node or column. index parameter with a value of 0 is
        the first column.

        :param index: The column index for the item
        :type index: int
        :return: the column text
        :rtype: str
        """
        return ""

    def customRoles(self, index):
        return []

    def dataByRole(self, index, role):
        return

    def setDataByCustomRole(self, index, data, role):
        return False

    def toolTip(self, index):
        """The tooltip for the index.

        :param index: The column index for the item
        :type index: int
        :rtype: str
        """
        model = self.model
        if model is None:
            return ""
        msg = self.headerText(index) + ":" + str(self.data(index)) + "\n"
        return msg

    def setToolTip(self, index, value):
        return False

    def icon(self, index):
        """The icon for the index.

        :param index: The column index for the item.
        :type index: int
        :rtype: QtGui.QIcon
        """
        pass

    def iconSize(self, index):
        return QtCore.QSize(16, 16)

    def headerIcon(self):
        """Returns the column header icon.

        :rtype: QtGui.QIcon
        """
        return QtGui.QIcon()

    def headerText(self, index):
        """Returns the column header text

        :return: the header value
        :rtype: str
        """
        return self._headerText

    def headerVerticalText(self, index):
        """The Vertical header text, if the return type is None then no text is displayed, an empty string will
        produce a gap in the header.

        :param index: The column index for the item.
        :type index: int
        :rtype: str or None
        """
        return None

    def headerVerticalIcon(self, index):
        """The Vertical header icon.

        :param index: The column index for the item
        :type index: int
        :rtype: QtGui.QIcon()
        """
        return QtGui.QIcon()

    def isEditable(self, index):
        """Determines if this node can be editable e.g set text. Defaults to False.

        :param index: The column index for the item.
        :type index: int
        :return: whether this node is editable, defaults to False
        :rtype: bool
        """
        return self.isEnabled(index)

    def isEnabled(self, index):
        """Determines if this node is enabled.

        :param index: The column index for the item
        :type index: int
        :return: whether this node is enabled, defaults to True
        :rtype: bool
        """
        return True

    def supportsDrag(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def supportsDrop(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def mimeData(self, indices):
        return {}

    def dropMimeData(self, items, action):
        """
        :param items: the column index
        :type items: list[value]
        """
        return []

    def isSelectable(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return True

    def foregroundColor(self, index):
        """
        :param index: the column index
        :type index: int
        """
        if self.isEnabled(index) and self.isEditable(index):
            return self.enabledColor
        return self.disabledColor

    def backgroundColor(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return None

    def displayChangedColor(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return None

    def textMargin(self, index):
        return self._defaultTextMargin

    def alignment(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return QtCore.Qt.AlignVCenter

    def font(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return self._font

    def isCheckable(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def insertColumnDataSources(self, index, count):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def removeColumnDataSources(self, index, count):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def removeRowDataSource(self, index):
        """
        :param index: the column index
        :type index: int
        """
        if index < self.rowCount():
            del self._children[index]
            return True
        return False

    def removeRowDataSources(self, index, count):
        """
        :param index: the column index
        :type index: int
        """

        if index < self.rowCount():
            self._children = self._children[:index] + self._children[index + count:]
            return True
        return False

    def insertRowDataSources(self, index, count):
        """
        :param index: the column index
        :type index: int
        """
        return None

    def insertRowDataSource(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return False

    def onVerticalHeaderSelection(self, index):
        """Triggered by the table view(if this source is attached to one) when the vertical header is clicked.

        :param index: the row index
        :type index: int
        """
        pass

    def contextMenu(self, selection, menu):
        pass

    def sort(self, index=0, order=QtCore.Qt.DescendingOrder):
        """This sort function purpose is for sorting the data by column.

        :param index: the column index to sort
        :type index: int
        :param order: The Qt order
        :type order: int
        """

        def element(key):
            return key[1]

        toSort = [(obj, self.data(i)) for i, obj in enumerate(self.userObjects())]

        if order == QtCore.Qt.DescendingOrder:
            results = [i[0] for i in sorted(toSort, key=element, reverse=True)]
        else:
            results = [i[0] for i in sorted(toSort, key=element)]
        self.setUserObjects(results)

    def delegate(self, parent):
        return delegates.HtmlDelegate(parent)


class ColumnDataSource(BaseDataSource):
    def __init__(self, headerText=None, model=None, parent=None):
        super(ColumnDataSource, self).__init__(headerText, model, parent)

    def sort(self, rowDataSource, index=0, order=QtCore.Qt.DescendingOrder):
        """This sort function purpose is for sorting the data by column.

        :param index: the column index to sort
        :type index: int
        :param order: The Qt order
        :type order: int
        """

        def element(key):
            return key[1] or ""

        toSort = [(obj, self.data(rowDataSource, i)) for i, obj in enumerate(rowDataSource.userObjects())]

        if order == QtCore.Qt.DescendingOrder:
            results = [i[0] for i in sorted(toSort, key=element, reverse=True)]
        else:
            results = [i[0] for i in sorted(toSort, key=element)]
        rowDataSource.setUserObjects(results)

    def setData(self, rowDataSource, index, value):
        """Sets the text value of this node at the specified column.

        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: The column index
        :type index: int
        :return: the new text value for this nodes column index
        :rtype: str
        """
        pass

    def data(self, rowDataSource, index):
        """The text for this node or column. index parameter with a value of 0 is
        the first column.

        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: The column index for the text
        :type index: int
        :return: the column text
        :rtype: str
        """
        return ""

    def dataByRole(self, rowDataSource, index, role):
        return False

    def customRoles(self, rowDataSource, index):
        return []

    def textMargin(self, rowDataSource, index):
        return rowDataSource.textMargin(index)

    def toolTip(self, rowDataSource, index):
        """The tooltip for this node.

        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :rtype: str
        """
        return ""

    def icon(self, rowDataSource, index):
        """The icon for this node.

        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :rtype: QtGui.QIcon
        """
        pass

    def isCheckable(self, rowDataSource, index):
        """The icon for this node.

        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :rtype: QtGui.QIcon
        """
        return False

    def isEditable(self, rowDataSource, index):
        """Determines if this node can be editable e.g set text. Defaults to False.

        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        :return: whether or not this node is editable, defaults to False
        :rtype: bool
        """
        return rowDataSource.isEditable(index)

    def isEnabled(self, rowDataSource, index):
        """Determines if this node is enabled.

        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        :return: whether or not this node is enabled, defaults to True
        :rtype: bool
        """
        return rowDataSource.isEnabled(index)

    def supportsDrag(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        :return: whether or not this node supports drag
        :rtype: bool
        """
        return False

    def supportsDrop(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        :return: whether or not this node supports drop
        :rtype: bool
        """
        return False

    def mimeData(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        :return: The mime data for drag drop features
        :rtype: QtCore.QMimeData
        """
        return {}

    def dropMimeData(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return False

    def mimeText(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return

    def isSelectable(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return True

    def foregroundColor(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """

        if self.isEnabled(rowDataSource, index) and self.isEditable(rowDataSource, index):
            return self.enabledColor
        return self.disabledColor

    def backgroundColor(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return rowDataSource.backgroundColor(index)

    def displayChangedColor(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return None

    def alignment(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return QtCore.Qt.AlignVCenter

    def font(self, rowDataSource, index):
        """
        :param rowDataSource: The rowDataSource model for the column index
        :type rowDataSource: BaseDataSource
        :param index: the column index
        :type index: int
        """
        return super(ColumnDataSource, self).font(index)

    def removeRowDataSources(self, rowDataSource, index, count):
        pass


class RowDoubleDataSource(BaseDataSource):
    def delegate(self, parent):
        return delegates.NumericDoubleDelegate(parent)

    def minimum(self, index):
        return -99999.0

    def maximum(self, index):
        return 99999.0


class RowIntNumericDataSource(BaseDataSource):
    def delegate(self, parent):
        return delegates.NumericIntDelegate(parent)

    def minimum(self, index):
        return -99999

    def maximum(self, index):
        return 99999


class RowEnumerationDataSource(BaseDataSource):
    def delegate(self, parent):
        return delegates.EnumerationDelegate(parent)

    def enums(self, index):
        return []


class IconRowDataSource(BaseDataSource):
    def delegate(self, parent):
        return delegates.PixmapDelegate(parent)

    def isEditable(self, index):
        return False


class RowBooleanDataSource(ColumnDataSource):
    def isCheckable(self, rowDataSource, index):
        return False


class ColumnDoubleDataSource(ColumnDataSource):
    def delegate(self, parent):
        return delegates.NumericDoubleDelegate(parent)

    def minimum(self, rowDataSource, index):
        return -99999.0

    def maximum(self, rowDataSource, index):
        return 99999.0


class ColumnIntNumericDataSource(ColumnDataSource):
    def delegate(self, parent):
        return delegates.NumericIntDelegate(parent)

    def minimum(self, rowDataSource, index):
        return -99999

    def maximum(self, rowDataSource, index):
        return 99999

class ColumnEnumerationDataSource(ColumnDataSource):
    def __init__(self, headerText=None, model=None, parent=None):
        super(ColumnEnumerationDataSource, self).__init__(headerText, model, parent)
        self._enums = {}
        self._currentIndex = {}

    def delegate(self, parent):
        return delegates.EnumerationDelegate(parent)

    def data(self, rowDataSource, index):
        enums = self._enums.get(index, [])
        if enums and index in self._currentIndex:
            return enums[self._currentIndex[index]]

    def setData(self, rowDataSource, index, value):
        enums = self._enums.get(index, [])
        if value < len(enums):
            self._currentIndex[index] = value
            return True
        return False

    def enums(self, rowDataSource, index):
        return self._enums.get(index, [])

    def setEnums(self, rowDataSource, index, enums):
        currentEnums = self._enums.get(index, [])
        newIndex = 0
        if currentEnums and index in self._currentIndex:
            currentEnumValue = currentEnums[self._currentIndex[index]]
            try:
                newIndex = enums.index(currentEnumValue)
            except ValueError:
                pass  # happens when the previous enum no longer exists
        self._currentIndex[index] = newIndex
        self._enums[index] = enums
        return True

    def setCurrentIndex(self, rowDataSource, index, newIndex):
        self._currentIndex[index] = newIndex

    def clearEnums(self):
        self._enums = {}
        self._currentIndex = {}

    def removeRowDataSources(self, rowDataSource, index, count):
        indices = self._currentIndex
        nextIndex = index + count
        values = list(indices.values())
        keys = list(indices.keys())

        for i, val in enumerate(values[nextIndex:]):
            indices[index + i] = val
        for val in keys[nextIndex - 1:]:
            del indices[val]


class RowEnumerationButtonDataSource(BaseDataSource):

    def __init__(self, headerText=None, model=None, parent=None):
        super(RowEnumerationButtonDataSource, self).__init__(headerText, model, parent)
        # enums by row number
        self._enums = {}  # type: dict[int: list[str]]
        # current enum index by row number
        self.currentIndex = {}  # type: dict[int: int]

    def delegate(self, parent):
        return delegates.ButtonEnumerationDelegate(parent)

    def data(self, index):
        enums = self._enums.get(index, [])
        if enums and index in self.currentIndex:
            return enums[self.currentIndex[index]]

    def setData(self, index, value):
        enums = self._enums.get(index, [])
        if value < len(enums):
            self.currentIndex[index] = value
            return True
        return False

    def enums(self, index):
        return self._enums.get(index, [])

    def setEnums(self, index, enums):
        currentEnums = self._enums.get(index, [])
        newIndex = 0
        if currentEnums and index in self.currentIndex:
            currentEnumValue = currentEnums[self.currentIndex[index]]
            try:
                newIndex = enums.index(currentEnumValue)
            except ValueError:
                pass  # happens when the previous enum no longer exists
        self.currentIndex[index] = newIndex
        self._enums[index] = enums
        return True

    def setCurrentIndex(self, index, newIndex):
        self.currentIndex[index] = newIndex

    def clearEnums(self):
        self._enums = {}
        self.currentIndex = {}

    def removeRowDataSources(self, index, count):
        indices = self.currentIndex
        nextIndex = index + count

        for i, val in enumerate(list(indices.values())[nextIndex:]):
            indices[index + i] = val
        for val in list(indices.keys())[nextIndex - 1:]:
            del indices[val]

    def customRoles(self, index):
        return (constants.buttonClickedRole,)

    def dataByRole(self, index, role):
        return False
class ColumnEnumerationButtonDataSource(ColumnDataSource):

    def __init__(self, headerText=None, model=None, parent=None):
        super(ColumnEnumerationButtonDataSource, self).__init__(headerText, model, parent)
        # enums by row number
        self._enums = {}  # type: dict[int: list[str]]
        # current enum index by row number
        self.currentIndex = {}  # type: dict[int: int]

    def delegate(self, parent):
        return delegates.ButtonEnumerationDelegate(parent)

    def data(self, rowDataSource, index):
        enums = self._enums.get(index, [])
        if enums and index in self.currentIndex:
            return enums[self.currentIndex[index]]

    def setData(self, rowDataSource, index, value):
        enums = self._enums.get(index, [])
        if value < len(enums):
            self.currentIndex[index] = value
            return True
        return False

    def enums(self, rowDataSource, index):
        return self._enums.get(index, [])

    def setEnums(self, rowDataSource, index, enums):
        currentEnums = self._enums.get(index, [])
        newIndex = 0
        if currentEnums and index in self.currentIndex:
            currentEnumValue = currentEnums[self.currentIndex[index]]
            try:
                newIndex = enums.index(currentEnumValue)
            except ValueError:
                pass  # happens when the previous enum no longer exists
        self.currentIndex[index] = newIndex
        self._enums[index] = enums
        return True

    def setCurrentIndex(self, rowDataSource, index, newIndex):
        self.currentIndex[index] = newIndex

    def clearEnums(self):
        self._enums = {}
        self.currentIndex = {}

    def removeRowDataSources(self, rowDataSource, index, count):
        indices = self.currentIndex
        nextIndex = index + count

        for i, val in enumerate(list(indices.values())[nextIndex:]):
            indices[index + i] = val
        for val in list(indices.keys())[nextIndex - 1:]:
            del indices[val]

    def customRoles(self, rowDataSource, index):
        return (constants.buttonClickedRole,)

    def dataByRole(self, rowDataSource, index, role):
        return False


class ColumnBooleanDataSource(ColumnDataSource):
    def delegate(self, parent):
        return delegates.CheckBoxDelegate(parent)

    def isCheckable(self, rowDataSource, index):
        return True


class IconColumnDataSource(ColumnDataSource):
    def delegate(self, parent):
        return delegates.PixmapDelegate(parent)

    def isEditable(self, rowDataSource, index):
        return False
