from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt.models import modelutils


class TreeView(QtWidgets.QTreeView):
    itemDoubleClicked = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(TreeView, self).__init__(parent)
        self.supportsShiftExpand = True
        self.expanded.connect(self.expandFrom)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            dataModelIndex, _ = modelutils.dataModelIndexFromIndex(index)
            self.itemDoubleClicked.emit(dataModelIndex)
        super(TreeView, self).mouseDoubleClickEvent(event)

    def expandFrom(self, index, expand=True):
        modifierPressed = QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier
        if not modifierPressed and self.supportsShiftExpand:
            return
        for i in range(self.model().rowCount(index)):
            childIndex = self.model().index(i, 0, index)
            self.setExpanded(childIndex, expand)
