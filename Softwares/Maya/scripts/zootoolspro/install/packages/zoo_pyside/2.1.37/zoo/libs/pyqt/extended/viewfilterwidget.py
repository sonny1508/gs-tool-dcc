from zoo.libs.pyqt.widgets import layouts
from zoo.libs.pyqt.extended import combobox
from zoo.libs.pyqt.widgets import searchwidget
from zoo.libs.pyqt import uiconstants
from zoovendor.Qt import QtCore, QtWidgets


class ViewSearchWidget(QtWidgets.QWidget):
    """Specialize widget for column row views eg. table view.

    Contains Widgets.

    #. column Visibility combobox,
    #. column Filter combobox,
    #. Search Widget

    Signals.

    #. ColumnVisibilityIndexChanged
    #. ColumnFilterIndexChanged
    #. SearchTextedChanged
    #. SearchTextedCleared

    """
    columnVisibilityIndexChanged = QtCore.Signal(int, int)
    columnFilterIndexChanged = QtCore.Signal(str)
    searchTextedChanged = QtCore.Signal(str)
    searchTextedCleared = QtCore.Signal()

    def __init__(self, showColumnVisBox=True, parent=None):
        super(ViewSearchWidget, self).__init__(parent=parent)
        self.searchLayout = layouts.hBoxLayout(self, spacing=uiconstants.SSML)
        self.searchLayout.setContentsMargins(0, 0, 0, 0)
        self.searchBoxLabel = QtWidgets.QLabel("Search By:", parent=self)
        self.searchHeaderBox = combobox.ExtendedComboBox(parent=self)
        self.searchWidget = searchwidget.SearchLineEdit(parent=self)
        self.searchWidget.setMaximumHeight(self.searchHeaderBox.size().height())
        self.searchWidget.setMinimumHeight(self.searchHeaderBox.size().height())
        self.searchHeaderBox.itemSelected.connect(self.columnFilterIndexChanged.emit)
        self.searchWidget.textCleared.connect(self.searchTextedCleared.emit)
        self.searchWidget.textChanged.connect(self.searchTextedChanged.emit)

        self.columnVisibilityBox = None
        if showColumnVisBox:
            self.columnVisibilityBox = combobox.ExtendedComboBox(parent=self)
            self.columnVisibilityBox.setMinimumWidth(100)
            self.columnVisibilityBox.checkStateChanged.connect(self.onVisibilityChanged)
            self.searchLayout.addWidget(self.columnVisibilityBox)

        self.searchLayout.addWidget(self.searchBoxLabel)
        self.searchLayout.addWidget(self.searchHeaderBox)
        self.searchLayout.addWidget(self.searchWidget)

    def setHeaderVisibility(self, state):
        self.searchHeaderBox.hide() if not state else self.searchHeaderBox.show()
        self.searchBoxLabel.hide() if not state else self.searchBoxLabel.show()

    def setVisibilityItems(self, items):
        self.columnVisibilityBox.clear()
        for i in items:
            self.columnVisibilityBox.addItem(i, isCheckable=True)

    def setHeaderItems(self, items):
        self.searchHeaderBox.clear()
        for i in items:
            self.searchHeaderBox.addItem(i, isCheckable=False)

    def onVisibilityChanged(self, index, state):
        self.columnVisibilityIndexChanged.emit(index, state)
