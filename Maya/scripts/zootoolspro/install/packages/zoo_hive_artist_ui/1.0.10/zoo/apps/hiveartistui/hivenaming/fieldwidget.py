from zoo.libs.naming import naming
from zoo.libs.pyqt import utils
from zoo.libs import iconlib
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants
from zoo.libs.pyqt.extended import tableviewplus, listviewplus
from zoo.libs.pyqt.models import tablemodel, listmodel, datasources, modelutils
from zoovendor.Qt import QtWidgets, QtCore


class FieldsWidget(QtWidgets.QSplitter):
    _defaultKeyValueName = "newKey"
    _defaultKeyValueValue = "NewValue"

    def __init__(self, parent):
        super(FieldsWidget, self).__init__(parent)
        # top level widget for the keyValue Layout
        keyValueWidget = QtWidgets.QWidget(parent=self)
        keyValueLayout = elements.vBoxLayout(spacing=1, parent=keyValueWidget)

        keyValueOpsEditLayout = elements.hBoxLayout(spacing=uiconstants.SPACING)
        self.addKeyValueLabelBtn = elements.ExtendedButton(parent=self, icon=iconlib.icon("plusHollow"))
        self.removeKeyValueLabelBtn = elements.ExtendedButton(parent=self, icon=iconlib.icon("minusHollow"))
        keyValueOpsEditLayout.addStretch(0)
        keyValueOpsEditLayout.addWidget(self.addKeyValueLabelBtn)
        keyValueOpsEditLayout.addWidget(self.removeKeyValueLabelBtn)

        self._setupViews()
        self._setupDataSources()

        keyValueLayout.addWidget(self.keyValueTable)
        keyValueLayout.addLayout(keyValueOpsEditLayout)
        self.addWidget(self.fieldList)
        self.addWidget(keyValueWidget)

        self.connections()

    def _setupViews(self):
        self.fieldList = listviewplus.ListViewPlus(searchable=False, parent=self)
        self.fieldList.setMaximumWidth(utils.dpiScale(150))
        self.keyValueTable = tableviewplus.TableViewPlus(searchable=False, manualReload=False,
                                                         parent=self)
        self.keyValueTable.tableView.verticalHeader().setVisible(False)
        self.fieldListModel = listmodel.ListModel(parent=self)
        self.keyValueModel = tablemodel.TableModel(parent=self)

        self.fieldList.setModel(self.fieldListModel)
        self.keyValueTable.setModel(self.keyValueModel)

    def _setupDataSources(self):
        self.fieldListDataSource = FieldDataSource(model=self.fieldListModel)
        self.fieldEditDataSource = FieldKeyValueKeySource(model=self.keyValueModel)

        self.fieldList.registerRowDataSource(self.fieldListDataSource)
        self.keyValueTable.registerRowDataSource(self.fieldEditDataSource)
        self.keyValueTable.registerColumnDataSources([FieldKeyValueValueSource(headerText="Value")])

    def connections(self):
        self.fieldList.selectionChanged.connect(self._onFieldListItemSelected)
        self.addKeyValueLabelBtn.leftClicked.connect(self._onAddKeyValue)
        self.removeKeyValueLabelBtn.leftClicked.connect(self._onRemoveKeyValue)

    def refresh(self):
        self.refreshFieldList()
        self.refreshFieldTable()

    def refreshFieldList(self):
        self.fieldListModel.reload()
        self.fieldList.refresh()

    def refreshFieldTable(self):
        self.keyValueModel.reload()
        self.keyValueTable.refresh()

    def reloadFromConfig(self, configInstance):
        """

        :param configInstance:
        :type configInstance: :class:`zoo.libs.naming.naming.NameManager`
        """
        fields = list(sorted(configInstance.fields(recursive=True), key=lambda x: x.name))
        self.fieldListDataSource.setUserObjects(fields)
        self.refreshFieldList()
        self.fieldList.selectionModel().setCurrentIndex(self.fieldList.model().index(0, 0),
                                                        QtCore.QItemSelectionModel.ClearAndSelect)

    def _onFieldListItemSelected(self, event):
        """

        :param event:
        :type event: :class:`listviewplus.ListViewPlusSelectionChangedEvent`
        :return:
        :rtype:
        """
        for item in event.currentItems:  # type: naming.Field
            self.fieldEditDataSource.setUserObjects(list(sorted(item.keyValues(), key=lambda x: x.name)))
            break
        self.refreshFieldTable()

    def activeField(self):
        selected = self.fieldList.selectedQIndices()
        if not selected:
            return
        return self.fieldListDataSource.userObject(selected[0].row())

    def activeKeyValue(self):
        """

        :return:
        :rtype: tuple[:class:`naming.Field`, list[:class:`naming.KeyValue`]]
        """
        field = self.activeField()
        rows = self.keyValueTable.selectedRows()
        keyValues = []
        for row in rows:
            keyValues.append(self.fieldEditDataSource.userObject(row))
        return field, keyValues

    def _onAddKeyValue(self):
        activeField = self.activeField()
        if not activeField:
            return
        newKey = activeField.add(self._defaultKeyValueName, self._defaultKeyValueValue)
        self.keyValueModel.insertRows(self.fieldEditDataSource.rowCount(), 1, keyValues=[newKey])

    def _onRemoveKeyValue(self):
        field, keyValues = self.activeKeyValue()
        for keyValue in keyValues:
            if keyValue.protected:
                continue
            modelIndex = self.keyValueModel.match(self.keyValueModel.index(0, 0),
                                                  QtCore.Qt.DisplayRole,
                                                  keyValue.name, 1, QtCore.Qt.MatchExactly)
            field.remove(keyValue.name)
            if modelIndex and modelIndex[0].isValid():
                self.keyValueModel.removeRow(modelIndex[0].row())


class FieldDataSource(datasources.BaseDataSource):

    def __init__(self, headerText=None, model=None, parent=None):
        super(FieldDataSource, self).__init__(headerText, model, parent)
        self._fields = []  # type: list[naming.Field]

    def userObject(self, index):
        return self._fields[index]

    def setUserObjects(self, objects):
        self._fields = objects

    def rowCount(self):
        return len(self._fields)

    def data(self, index):
        return self._fields[index].name

    def isEditable(self, index):
        return False

    def toolTip(self, index):
        return self._fields[index].description

    def foregroundColor(self, index):
        return self.enabledColor


class FieldKeyValueKeySource(datasources.BaseDataSource):

    def __init__(self, model=None, parent=None):
        super(FieldKeyValueKeySource, self).__init__("Name", model, parent)

    @property
    def children(self):
        """

        :return:
        :rtype: list[naming.KeyValue]
        """
        return self._children

    def columnCount(self):
        return 2

    def foregroundColor(self, index):
        return self.enabledColor

    def data(self, index):
        return self.userObject(index).name

    def setData(self, index, value):
        self.userObject(index).name = value

    def isEditable(self, index):
        return not self.userObject(index).protected

    def userObject(self, index):
        """

        :param index: The row index
        :type index: int
        :return:
        :rtype: :class:`naming.KeyValue`
        """
        return super(FieldKeyValueKeySource, self).userObject(index)
    def userObjects(self):
        """

        :return:
        :rtype: list[:class:`naming.KeyValue`]
        """
        return self._children

    def insertRowDataSources(self, index, count, keyValues):
        self.insertChildren(index, keyValues)
        return True


class FieldKeyValueValueSource(datasources.ColumnDataSource):

    def data(self, rowDataSource, index):
        keyValue = rowDataSource.userObject(index)  # type: naming.KeyValue
        return keyValue.value

    def setData(self, rowDataSource, index, value):
        keyValue = rowDataSource.userObject(index)  # type: naming.KeyValue
        keyValue.value = str(value)
        return True

    def isEditable(self, rowDataSource, index):
        return True
