from zoovendor import six
from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import utils

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import layouts
from zoo.libs.pyqt.widgets import label as lbl
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class ExtendedComboBox(QtWidgets.QComboBox):
    """Extended combobox to also have a filter
    """
    itemSelected = QtCore.Signal(str)
    checkStateChanged = QtCore.Signal(int, int)

    def __init__(self, items=None, parent=None):
        super(ExtendedComboBox, self).__init__(parent)

        self.setEditable(True)

        # add a filter model to filter matching items
        self.pFilterModel = QtCore.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.complete = QtWidgets.QCompleter(self)
        self.complete.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)
        # bug thats been around for at 3 years where in pyside you need to set the completer model like this instead
        # of passing into the init lol
        self.complete.setModel(self.pFilterModel)
        self.setCompleter(self.complete)
        if not isinstance(self.model(), QtGui.QStandardItem):  # todo:
            self.pFilterModel.setSourceModel(self.model())
        else:
            logger.warning("ExtendedComboBox.model() returning QStandardItem. Filter model wont work for this widget")

        # connect signals
        self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
        self.complete.activated.connect(self.onCompleterActivated)
        if items:
            self.addItems(items)
        self.view().pressed.connect(self.handleItemPressed)
        self._isCheckable = False

    def addItem(self, text, isCheckable=False):
        super(ExtendedComboBox, self).addItem(text)
        model = self.model()
        item = model.item(model.rowCount() - 1, 0)
        if item and isCheckable:
            self._isCheckable = isCheckable
            item.setCheckState(QtCore.Qt.Checked)

    def keyPressEvent(self, event):
        super(ExtendedComboBox, self).keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
            self.parent().setFocus()
        elif event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.itemSelected.emit(self.currentText())
            self.parent().setFocus()

    def onCompleterActivated(self, text):
        """On selection of an item from the completer, this method will select the item from the combobox
        """
        # on selection of an item from the completer, select the corresponding item from combobox
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            self.activated.emit(str(self.itemText(index)))

    def setModel(self, model):
        """Overridden to set the filter and completer models
        """
        super(ExtendedComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.complete.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        # on model column change, update the model column of the filter and completer as well
        self.complete.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(ExtendedComboBox, self).setModelColumn(column)

    def handleItemPressed(self, index):
        if not self._isCheckable:
            return
        item = self.model().itemFromIndex(index)
        if item.checkState() == QtCore.Qt.Checked:
            state = QtCore.Qt.Unchecked
        else:
            state = QtCore.Qt.Checked
        item.setCheckState(state)
        self.checkStateChanged.emit(item.row(), state)

    def stateList(self):
        model = self.model()
        items = []
        for index in range(model.rowCount()):
            item = model.itemFromIndex(index)
            if item.isValid():
                items.append(item)
        return items

    def checkedItems(self):
        model = self.model()
        items = []
        for index in range(model.rowCount()):
            item = model.itemFromIndex(index)
            if item.isValid():
                items.append(item)
        return items


class ComboItemChangedEvent(object):
    def __init__(self, prevIndex, currIndex, parent):
        """ Combobox Item changed event

        :type parent: zoo.libs.pyqt.extended.combobox.ComboBox
        :param prevIndex:
        :type prevIndex:
        :param currIndex:
        :type currIndex:
        """
        self._parent = parent
        self.index = currIndex
        self.prevIndex = prevIndex

    @property
    def text(self):
        return self._parent.itemText(self.index)

    @property
    def prevText(self):
        return self._parent.itemText(self.prevIndex)

    @property
    def data(self):
        return self._parent.itemData(self.index)

    @property
    def prevData(self):
        return self._parent.itemData(self.prevIndex)


class ComboBox(QtWidgets.QWidget):
    itemChanged = QtCore.Signal(object)
    prevIndex = None

    def __init__(self, parent=None):
        """Combo box methods only, do not directly use this class, it is designed to be used by:

            ComboBoxRegular()
            ComboBoxSearchable()

        Passes in methods for those widgets.

        :param parent: the qt parent
        :type parent: class
        """
        super(ComboBox, self).__init__(parent=parent)
        self.label = ""  # designed to be used by subclasses
        self.box = None  # type: QtWidgets.QComboBox # Used by subclasses

    def __getattr__(self, item):
        if hasattr(self.box, item):
            return getattr(self.box, item)

    def clear(self):
        """ Clear all items. Method used for autocomplete
        """
        self.box.clear()

    def addItem(self, item, sortAlphabetically=False, userData=None):
        """Adds an item to the combobox with the given text , and containing the specified userData
        (stored in the UserRole ).
        The item is appended to the list of existing items.

        :param item: the name to add to the combo box
        :type item: str
        :param sortAlphabetically: sorts the full combo box alphabetically after adding
        :type sortAlphabetically: bool
        :param userData: The userData to set if any.
        :type userData: object
        """
        self.box.addItem(item, userData)
        if sortAlphabetically:
            self.box.model().sort(0)

    def currentData(self, role=QtCore.Qt.UserRole):
        return self.box.currentData(role)

    @property
    def activated(self):
        return self.box.activated

    @property
    def currentIndexChanged(self):
        return self.box.currentIndexChanged

    def setItemText(self, index, text):
        return self.box.setItemText(index, text)

    def currentIndex(self):
        """Returns the int value of the combo box. Method used for autocomplete

        :return currentIndex: the int value of the combo box
        :rtype currentIndex: int
        """
        return int(self.box.currentIndex())

    def value(self):
        """Returns the literal value of the combo box

        :return value: the literal value of the combo box
        :rtype value: str
        """
        return str(self.box.currentText())

    def currentText(self):
        """Method used for autocomplete"""
        return self.box.currentText()

    def count(self):
        """Method used for autocomplete"""
        return self.box.count()

    def addItems(self, items, sortAlphabetically=False):
        """ Add items to combobox

        :param items:
        :param sortAlphabetically:
        :return:
        """
        self.box.addItems(items)
        if sortAlphabetically:
            self.box.model().sort(0)

    def itemData(self, index, role=QtCore.Qt.UserRole):
        """Method used for autocomplete"""
        return self.box.itemData(index, role)

    def iterItemData(self):
        for i in range(self.box.count()):
            yield self.box.itemData(i)

    def onItemChanged(self):
        """when the items changed return the tuple of values
        """
        event = ComboItemChangedEvent(int(self.prevIndex if self.prevIndex is not None else -1),
                                      int(self.box.currentIndex()), parent=self)
        self.itemChanged.emit(event)
        self.prevIndex = self.box.currentIndex()

    def setToText(self, text, flags=QtCore.Qt.MatchFixedString):
        """Sets the index based on the text

        :param text: Text to search and switch the comboxBox to
        :type text: str
        """
        index = self.box.findText(text, flags)

        if index >= 0:
            self.setCurrentIndex(index)

    def removeItemByText(self, text, flags=QtCore.Qt.MatchFixedString):
        """removes the index based on the text from the combo box (box.removeItem)

        :param text: Text to search and delete it's entire entry from the combo box (removeItem)
        :type text: str
        """
        index = self.box.findText(text, flags)
        if index >= 0:
            self.box.removeItem(index)

    def setToTextQuiet(self, text):
        """Sets the index based on the text and stops comboBox from emitting signals while being changed

        :param text: Text to search and switch the comboxBox to
        :type text: str
        """
        self.box.blockSignals(True)
        self.setToText(text)
        self.box.blockSignals(False)

    def setIndex(self, index, quiet=False):
        """Sets the combo box to the current index number

        :param index: Sets the combo box to the current index
        :type index: int
        """
        index = index or 0
        if quiet:
            self.box.blockSignals(True)
        self.box.setCurrentIndex(index)
        if quiet:
            self.box.blockSignals(False)

    def setIndexQuiet(self, index):
        """Sets the combo box to the current index number, stops comboBox from emitting signals while being changed

        :param index: the index item number of the comboBox
        :type index: int
        """
        self.box.blockSignals(True)
        self.box.setCurrentIndex(index)
        self.box.blockSignals(False)

    def setLabelFixedWidth(self, width):
        """Set the fixed width of the label

        :param width: the width in pixels, DPI is handled
        :type width: int
        """
        self.label.setFixedWidth(utils.dpiScale(width))

    def setBoxFixedWidth(self, width):
        """Set the fixed width of the lineEdit

        :param width: the width in pixels, DPI is handled
        :type width: int
        """
        self.box.setFixedWidth(utils.dpiScale(width))

    def setItemData(self, index, value):
        """Sets the data role for the item on the given index in the combobox to the specified value.
        Good for metadata assigned to the name

        :param index: the index to assign the value
        :type index: int
        :param value: the value to assign, can be any object or string etc
        :type value: object
        """
        self.box.setItemData(index, value)

    def itemText(self, index):
        """ Get current text from combobox

        :param index:
        :return:
        """
        return self.box.itemText(index)

    def itemTexts(self):
        """ Get all the items in the combobox

        :return:
        :rtype:
        """
        for i in range(self.box.count()):
            yield self.itemText(i)

    def blockSignals(self, blocked=False):
        """Manually block the combobox and label"""
        self.box.blockSignals(blocked)
        if self.label:
            self.label.blockSignals(blocked)


class ComboBoxRegular(ComboBox):
    """Creates a regular "not searchable" combo box (drop down menu) with a label

    TODO: this class should be combined with ComboBox, no need to have them apart?
    """

    def __init__(self, label="", items=(), parent=None, labelRatio=None, boxRatio=None, toolTip="", setIndex=0,
                 sortAlphabetically=False, margins=(0, 0, 0, 0), spacing=uic.SREG, boxMinWidth=None, itemData=(),
                 supportMiddleMouseScroll=True):
        """initialize class

        :param label: the label of the combobox
        :type label: str
        :param items: the item list of the combobox
        :type items: list
        :param parent: the qt parent
        :type parent: class
        :param toolTip: the tooltip info to display with mouse hover
        :type toolTip: str
        :param setIndex: set the combo box value as an int - 0 is the first value, 1 is the second
        :type setIndex: int
        :param boxMinWidth: set the combo box to be a minimum width in pixels, dpi handled
        :type boxMinWidth: int
        """
        super(ComboBoxRegular, self).__init__(parent=parent)
        self._supportMiddleMouseScroll = supportMiddleMouseScroll
        self.box = ComboBoxRegular.setupComboBox(items=items, itemData=itemData, parent=parent, setIndex=setIndex,
                                                 sortAlphabetically=sortAlphabetically,
                                                 supportMiddleMouseScroll=supportMiddleMouseScroll)
        self.box.setToolTip(toolTip)  # set here as doesn't set in setup method
        layout = layouts.hBoxLayout(parent=self, margins=margins, spacing=spacing)
        if label != "":
            self.label = lbl.Label(label, parent=parent, toolTip=toolTip)
            if labelRatio:
                layout.addWidget(self.label, labelRatio)
            else:
                layout.addWidget(self.label)
        else:
            self.label = ""
        if boxRatio:
            layout.addWidget(self.box, boxRatio)
        else:
            layout.addWidget(self.box)
        if boxMinWidth:
            self.box.setMinimumWidth(utils.dpiScale(boxMinWidth))
        # connections
        self.box.currentIndexChanged.connect(self.onItemChanged)  # elements uses this, emits itemChanged is not Qt

    @classmethod
    def setupComboBox(cls, parent=None, items=(), itemData=(), toolTip="", setIndex=0, sortAlphabetically=False,
                      supportMiddleMouseScroll=True):
        """Simple qComboBox with no label

        :param items: the item list of the combobox
        :type items: list
        :param parent: the qt parent
        :type parent: object
        :param toolTip: the tooltip info to display with mouse hover
        :type toolTip: str
        :param setIndex: set the combo box value as an int - 0 is the first value, 1 is the second
        :type setIndex: int
        :return: the QComboBox Qt widget
        :type: :class:`QtWidgets.QComboBox`
        """
        if not supportMiddleMouseScroll:
            comboBx = HumbleComboBox(parent)
        else:
            comboBx = QtWidgets.QComboBox(parent)
        if sortAlphabetically:
            comboBx.setInsertPolicy(QtWidgets.QComboBox.InsertAlphabetically)
            if items:
                items = list(items)
                items = [six.ensure_str(x) for x in items]  # if unicode convert to str
                items.sort(key=lambda x: x.lower())  # sort list alphabetically case-insensitive

        if itemData != ():
            for i, item in enumerate(items):
                comboBx.addItem(item, itemData[i])
        else:
            comboBx.addItems(items)
        comboBx.setToolTip(toolTip)
        if setIndex:
            comboBx.setCurrentIndex(setIndex)
        return comboBx


class HumbleComboBox(QtWidgets.QComboBox):
    """QComboBox which ignores the wheelEvent"""

    def __init__(self, *args, **kwargs):
        super(HumbleComboBox, self).__init__(*args, **kwargs)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, event):
        event.ignore()


class ComboBoxSearchable(ComboBox):
    def __init__(self, text="", items=(), parent=None, labelRatio=None, boxRatio=None, toolTip="", setIndex=0,
                 sortAlphabetically=False):
        """Creates a searchable combo box (drop down menu) with a label

        todo: this needs to be rewritten, why is it inheriting from ComboBox and yet it uses ExtendedComboBox?

        :param text: the label of the combobox
        :type text: str
        :param items: the item list of the combobox
        :type items: list or tuple
        :param parent: the qt parent
        :type parent: class
        """
        # TODO needs to stylesheet the lineEdit text entry
        super(ComboBoxSearchable, self).__init__(parent=parent)
        layout = layouts.hBoxLayout(parent=self, margins=(0, 0, 0, 0),
                                    spacing=utils.dpiScale(uic.SPACING))  # margins kwarg should be added
        self.box = ExtendedComboBox(items, parent)
        self.box.setToolTip(toolTip)
        # note: not a fan of this hardcoding but it keeps things consistent with other widgets ie. lineedit
        # + handle OS DPI though lower maya dpi not so much
        self.box.setFixedHeight(utils.dpiScale(20))
        if sortAlphabetically:
            self.box.setInsertPolicy(QtWidgets.QComboBox.InsertAlphabetically)  # Not working so do manually
            self.box.clear()
            self.addItems(items)

        if setIndex:
            self.box.setCurrentIndex(setIndex)
        if text:
            self.label = lbl.Label(text, parent, toolTip)
            if labelRatio:
                layout.addWidget(self.label, labelRatio)
            else:
                layout.addWidget(self.label)
        if boxRatio:
            layout.addWidget(self.box, boxRatio)
        else:
            layout.addWidget(self.box)
        # connections
        self.box.currentIndexChanged.connect(self.onItemChanged)  # elements uses this, emits itemChanged is not Qt

