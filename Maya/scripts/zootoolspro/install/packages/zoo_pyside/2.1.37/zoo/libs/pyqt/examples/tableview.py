"""
from zoo.libs.pyqt.examples import tableview
win = tableview.TableViewExample()
win.show()
"""
from zoovendor.Qt import QtWidgets
from zoo.libs import iconlib
from zoo.libs.pyqt.extended import tableviewplus
from zoo.libs.pyqt.models import datasources
from zoo.libs.pyqt.models import tablemodel
from zoo.libs.pyqt.widgets.frameless import window


class TableViewExample(window.ZooWindow):
    def __init__(self, title="Tableview example", width=600, height=800, parent=None):
        super(TableViewExample, self).__init__(title, width=width, height=height, parent=parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.view = tableviewplus.TableViewPlus(True, manualReload=False, parent=self)
        self.setMainLayout(layout)
        layout.addWidget(self.view)
        self.qmodel = tablemodel.TableModel(parent=self)
        self.view.setModel(self.qmodel)

        self.rowDataSource = ExampleRowDataSource("rowHeader",
                                                  [Node('One'), Node("Two"), Node("Three")])

        self.columnDataSources = (ExampleColumnIntDataSource(headerText="column spinbox"),
                                  ExampleColumnEnumerationDataSource(headerText="combobox"),
                                  ExampleColumnEnumerationButtonDataSource(headerText="combobox button"))
        self.view.registerRowDataSource(self.rowDataSource)
        self.view.registerColumnDataSources(self.columnDataSources)

        self.view.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.view.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.view.tableView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.qmodel.reload()
        self.view.refresh()
        proxyModel = self.view.model()
        for row in range(self.rowDataSource.rowCount()):
            self.view.openPersistentEditor(proxyModel.index(row, 3))


class Node(object):
    def __init__(self, label):
        self.label = label
        self.dataField = 10
        self.icon = iconlib.icon("brick")
        self.values = ["translate", "rotate", "scale", "visibility"]
        self.currentIndex = 0

    def serialize(self):
        return {
            "label": self.label
        }


class ExampleRowDataSource(datasources.BaseDataSource):
    def __init__(self, headerText, nodes):
        super(ExampleRowDataSource, self).__init__(headerText=headerText)
        self._children = nodes

    def supportsDrop(self, index):
        return True

    def supportsDrag(self, index):
        return True

    def mimeData(self, indices):
        data = []
        for i in indices:
            data.append(self.child(i.row()).serialize())
        return data

    def dropMimeData(self, items, action):
        return {"items": items}

    def icon(self, index):
        if index < self.rowCount():
            return self.children[index].icon

    def data(self, index):
        if index < self.rowCount():
            return self.child(index).label

    def setData(self, index, value):
        if index < self.rowCount():
            self.child(index).label = value
            return True
        return False

    def insertRowDataSources(self, index, count, items):
        self.insertChildren(index, [Node(item["label"]) for item in items])
        return True


class ExampleColumnIntDataSource(datasources.ColumnIntNumericDataSource):

    def data(self, rowDataSource, index):
        node = rowDataSource.userObject(index)
        if node:
            return node.dataField

    def setData(self, rowDataSource, index, value):
        node = rowDataSource.userObject(index)
        if node:
            node.dataField = int(value)


class ExampleColumnEnumerationDataSource(datasources.ColumnEnumerationDataSource):
    def enums(self, rowDataSource, index):
        node = rowDataSource.userObject(index)
        if node:
            return node.values

    def data(self, rowDataSource, index):
        node = rowDataSource.userObject(index)
        if node:
            return node.values[node.currentIndex]

    def setData(self, rowDataSource, index, value):
        node = rowDataSource.userObject(index)
        if node:
            node.currentIndex = int(value)


class ExampleColumnEnumerationButtonDataSource(datasources.ColumnEnumerationButtonDataSource):
    def enums(self, rowDataSource, index):
        node = rowDataSource.userObject(index)
        if node:
            return node.values

    def data(self, rowDataSource, index):
        node = rowDataSource.userObject(index)
        if node:
            return node.values[node.currentIndex]

    def setData(self, rowDataSource, index, value):
        node = rowDataSource.userObject(index)
        if node:
            node.currentIndex = int(value)

    def dataByRole(self, rowDataSource, index, role):
        node = rowDataSource.userObject(index)
        if node:
            node.values = ["translate", "rotate", "scale", "visibility", "test"]
            return True
        return False
