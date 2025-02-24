from collections import OrderedDict

from zoo.apps.hiveartistui import uiinterface
from zoo.core.util import zlogging
from zoo.libs.hive import api
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.models import modelutils, constants
from zoovendor.Qt import QtCore

logger = zlogging.getLogger(__name__)


class HiveSpaceSwitchController(QtCore.QObject):
    """Class which handles all events for the spaceSwitch Hive view, initialized for each component.

    .. note::

        See :mod:`zoo.apps.hiveartistui.views.spaceswitching.model` for how the tablemodel handles the
        space switching drivers

    :param rigModel: The container class for the component model, this contains the hive component instance.
    :type rigModel: :class:`zoo.apps.hiveartistui.model.RigModel`
    :param componentModel: The container class for the component model, this contains the hive component instance.
    :type componentModel: :class:`zoo.apps.hiveartistui.model.ComponentModel`
    :param parent:
    :type parent: :class:`ComponentSettingsWidget`
    """
    driverComponentChangedSig = QtCore.Signal(object, object, str)  # QIndex, component, expression
    driverChangedSig = QtCore.Signal(int, str)  # rowIndex, expression string
    driverLabelChangedSig = QtCore.Signal(int, str)  # rowIndex, label

    _emptyDriver = api.SpaceSwitchUIDriver(id_="", label="Select Control")
    _emptyDriverComponent = api.SpaceSwitchUIDriver(id_="", label="")
    # local space driver which is displayed in the driver component column
    _localDriver = api.SpaceSwitchUIDriver(id_=api.constants.ATTR_EXPR_INHERIT_TOKEN, label="Local Space")

    newDriverLabel = "newDriver"
    # support constraint types.
    constraintTypes = OrderedDict((("parent", "Parent Constraint"),
                                   ("scale", "Scale Constraint"),
                                   ("orient", "Orient Constraint"),
                                   ("point", "Point Constraint")))

    def __init__(self, rigModel, componentModel, parent):
        super(HiveSpaceSwitchController, self).__init__(parent)
        self.rigModel = rigModel
        self.componentModel = componentModel
        self.view = None
        self._currentSpaceLabel = ""
        self._componentSpaceUiData = self.componentModel.component.spaceSwitchUIData()

    def bindView(self, view):
        """

        :param view:
        :type view: :class:`zoo.apps.hiveartistui.views.spaceswitching.view.SpaceSwitchWidget`
        """
        self.view = view
        container = view.spaceWidgetContainer
        self.view.spaceNameEdit.itemRenamed.connect(self.onSpaceRenamed)
        self.view.spaceNameEdit.itemChanged.connect(self.onSpaceChanged)
        self.view.createSpaceAction.triggered.connect(self.onAddSpaceClicked)
        self.view.removeSpaceAction.triggered.connect(self.onRemoveSpaceClicked)
        container.addDriverLabelBtn.leftClicked.connect(self.onAddSpaceDriverClicked)
        container.removeDriverLabelBtn.leftClicked.connect(self.onRemoveSpaceDriverClicked)
        container.driven.itemChanged.connect(self.onDrivenChanged)
        container.spaceModel.rowsRemoved.connect(self.onDriverRemoved)
        container.constraintType.itemChanged.connect(self.onConstraintTypeChanged)
        container.defaultDriver.itemChanged.connect(self.onDefaultDriverChanged)
        self.view.spaceNameEdit.aboutToShow.connect(self.updateSpaceLabels)

        self.driverComponentChangedSig.connect(self.driverComponentChanged)
        self.driverLabelChangedSig.connect(self.saveChanges)
        self.driverChangedSig.connect(self.saveChanges)

    def onDriverRemoved(self, parent, first, last):
        self.saveChanges()
        self.reloadTableModel()

    def reload(self):
        logger.debug("Reloading Controller")
        self._componentSpaceUiData = self.componentModel.component.spaceSwitchUIData()
        self.updateSpaceLabels()
        self._clearTableModel()
        self.reloadTableModel()

    def _clearTableModel(self):
        container = self.view.spaceWidgetContainer
        spaceModel = container.spaceModel
        spaceModel.rowDataSource.setUserObjects([])
        spaceModel.reload()
        container.refresh()

    def updateSpaceLabels(self):
        logger.debug("Updating current components space labels")
        text = self.view.spaceNameEdit.currentText()
        self._currentSpaceLabel = text
        self.view.spaceNameEdit.updateList(self.spaceLabels(), setName=text)

    def currentSpaceSwitch(self):
        if not self._currentSpaceLabel:
            return {}
        return self.componentModel.component.definition.spaceSwitchByLabel(self._currentSpaceLabel)

    def constraintType(self):
        if not self._currentSpaceLabel:
            return self.constraintTypes["parent"]
        spaceSwitch = self.currentSpaceSwitch()

        return self.constraintTypes.get(spaceSwitch.type, "")

    def spaceLabels(self):
        yield ""
        for space in self.componentModel.component.definition.spaceSwitching:
            yield space.label


    def setDriverComponentFromSelection(self, rowIndex):
        sceneSelection = api.componentsFromSelected()
        uiSelection = [i.component for i in uiinterface.instance().artistUi().core.selection.componentModels]
        selectionToActOn = sceneSelection or uiSelection
        proxyTableModel = self.view.spaceWidgetContainer.spaceDriverView.model()
        model = self.view.spaceWidgetContainer.spaceModel
        modelIndex = proxyTableModel.mapToSource(proxyTableModel.index(rowIndex, 1))
        for sel in selectionToActOn:
            enums = model.data(modelIndex, role=constants.enumsRole)
            matchedIndex = enums.index(" ".join((sel.name(), sel.side())))
            model.setData(modelIndex, matchedIndex, role=QtCore.Qt.EditRole)
            return True
        return False

    def driverComponents(self):
        models = self.rigModel.componentModels()
        current = self.componentModel
        internal = [i for i in current.component.spaceSwitchUIData().get("drivers", []) if i.internal]
        data = [api.SpaceSwitchUIDriver(id_=api.componentToAttrExpression(current.component,
                                                                          i.component),
                                        label=i.displayName()) for i in models if i.component is not None]
        data = list(sorted(data, key=lambda x: x.label))
        data = [HiveSpaceSwitchController._emptyDriverComponent,
                HiveSpaceSwitchController._localDriver] + internal + data

        return data

    def components(self):
        return [i.component for i in self.rigModel.componentModels()]

    def onSpaceChanged(self, event):
        """Called when the space switch name changes

        :param event:
        :type event: :class:`zoo.libs.pyqt.extended.combobox.comboeditwidget.IndexChangedEvent`
        """

        text = event.items[0].text()
        self.changeSpace(text)

    def onDefaultDriverChanged(self, event):
        """

        :param event:
        :type event: :class:`zoo.libs.pyqt.extended.combobox.combobox.ComboItemChangedEvent`
        """
        text = event.text
        spaceSwitch = self.currentSpaceSwitch()
        spaceSwitch.defaultDriver = text
        self.saveChanges()

    def changeSpace(self, text):
        self._currentSpaceLabel = text
        if not text and not self.view.spaceWidgetContainer.isHidden():
            self.view.spaceWidgetContainer.hide()
        else:
            self.view.spaceWidgetContainer.show()
        if not text:
            self.view.spaceChanged.emit()
            return
        spaceSwitch = self.currentSpaceSwitch()
        if spaceSwitch is not None:
            self.setUiStateForSpace(spaceSwitch)

        self.reloadTableModel()
        self.view.spaceChanged.emit()

    def setUiStateForSpace(self, spaceSwitch):
        container = self.view.spaceWidgetContainer
        protected = spaceSwitch.isProtected
        self.view.removeSpaceAction.setEnabled(not spaceSwitch.isProtected)
        with utils.blockSignalsContext((container.driven, )):
            container.driven.setToText(self.drivenLabelForExpression(spaceSwitch.driven))
        container.driven.setEnabled(not protected)

        self.view.spaceNameEdit.comboEdit.setDisabled(not spaceSwitch.renameAllowed)
        with utils.blockSignalsContext((container.constraintType,
                                        container.defaultDriver)):
            container.constraintType.setEnabled(not protected)
            container.constraintType.setToText(self.constraintType())
            # update the default driver combobox and set the models user objects
            logger.debug("Updating Default Driver List and current driver list")
            if spaceSwitch:
                container.defaultDriver.clear()
                container.defaultDriver.addItems([i.label for i in spaceSwitch.drivers])
                container.defaultDriver.setToText(spaceSwitch.defaultDriver)
            else:
                container.defaultDriver.clear()

    def reloadTableModel(self):
        logger.debug("Reload SpaceSwitch Table Model")
        spaceSwitch = self.currentSpaceSwitch()
        container = self.view.spaceWidgetContainer
        spaceModel = container.spaceModel
        if not spaceSwitch:
            logger.debug("Missing SpaceSwitch, nullifying table.")
            self._clearTableModel()
            return
        spaceModel.rowDataSource.setUserObjects(spaceSwitch.drivers)
        tableView = container.spaceDriverView

        for columnDataSource in tableView.columnDataSources:
            columnDataSource.clearEnums()
        # now update the drivers
        # pull the current space switches from the component definition
        with utils.blockSignalsContext((container.defaultDriver,)):

            drivers = self.driverComponents()

            hiveSpaceDrivers = spaceSwitch.drivers
            driverIds = [i.id for i in drivers]
            if not hiveSpaceDrivers:
                self._clearTableModel()
                return

            for row in range(spaceModel.rowCount()):
                rowDriver = hiveSpaceDrivers[row]
                driverLabel = rowDriver.driver
                cellIndex = spaceModel.index(row, 1)
                spaceModel.setData(cellIndex, drivers, role=constants.enumsRole)

                currentDriverComponentIndex, driverIndex = self._driverIndicesForDriverLabel(cellIndex,
                                                                                             driverIds,
                                                                                             driverLabel)
                tableView.columnDataSources[0].setCurrentIndex(tableView.rowDataSource, row,
                                                               currentDriverComponentIndex)
                tableView.columnDataSources[1].setCurrentIndex(tableView.rowDataSource, row, driverIndex)

        container.refresh()

    def _driverIndicesForDriverLabel(self, modelIndex, driverIds, driverLabel):

        componentToken = api.componentTokenFromExpression(driverLabel)
        if not componentToken:
            return 0, 0
        if api.pathAsDefExpression(componentToken) in (api.constants.ATTR_EXPR_SELF_TOKEN,
                                                       api.constants.ATTR_EXPR_INHERIT_TOKEN):
            component = self.componentModel.component
            expr = driverLabel
            try:
                currentDriverComponentIndex = driverIds.index(expr)
            except ValueError:
                currentDriverComponentIndex = driverIds.index(api.constants.ATTR_EXPR_SELF_TOKEN)
        else:
            expr = api.pathAsDefExpression((":".join(componentToken),))
            component = self.rigModel.rig.component(*componentToken)
            currentDriverComponentIndex = driverIds.index(expr)

        driverList = self.driverComponentChanged(modelIndex, component, driverLabel)
        driverIndex = driverIndexForDriverId(driverLabel, driverList)

        return currentDriverComponentIndex, driverIndex

    def saveChanges(self):
        spaceSwitch = self.currentSpaceSwitch()
        if not spaceSwitch:
            return
        model = self.view.spaceWidgetContainer.spaceModel
        drivers = model.rowDataSource.children
        spaceSwitch.drivers = drivers
        component = self.componentModel.component
        logger.debug("Saving {} SpaceSwitch definition".format(component.serializedTokenKey()))
        component.saveDefinition(self.componentModel.component.definition)
        container = self.view.spaceWidgetContainer
        currentIndex = container.defaultDriver.currentIndex()
        with utils.blockSignalsContext((container.defaultDriver,)):
            container.defaultDriver.clear()
            container.defaultDriver.addItems([i.label for i in spaceSwitch.drivers])
            container.defaultDriver.setCurrentIndex(currentIndex)

    def onSpaceRenamed(self, event):
        """

        :param event:
        :type event:
        :return:
        :rtype:
        """
        currentSpaceSwitch = self.componentModel.component.definition.spaceSwitchByLabel(self._currentSpaceLabel)
        if not currentSpaceSwitch:
            return
        currentSpaceSwitch.label = event.after
        self._currentSpaceLabel = event.after
        self.saveChanges()

    def onAddSpaceClicked(self):
        definition = self.componentModel.component.definition
        newSpace = definition.createSpaceSwitch(label="newSpace", drivenId="",
                                                constraintType="parent",
                                                controlPanelFilter={}, permissions={}, drivers=[])
        if newSpace:
            self.view.spaceNameEdit.addItems([newSpace.label])
            self.view.spaceNameEdit.setIndexInt(self.view.spaceNameEdit.count() - 1)
            self.view.spaceNameEdit.comboEdit.setDisabled(False)
            self.saveChanges()

    def onRemoveSpaceClicked(self):
        if not self.view.spaceNameEdit.currentText():
            return
        definition = self.componentModel.component.definition
        if definition.removeSpaceSwitch(self._currentSpaceLabel):
            labels = list(self.spaceLabels())
            self.saveChanges()
            self.view.spaceNameEdit.setIndexInt(len(labels) - 1)

    def onConstraintTypeChanged(self, event):
        """

        :param event:
        :type event: :class:`zoo.libs.pyqt.extended.combobox.combobox.ComboItemChangedEvent`
        """
        definition = self.componentModel.component.definition
        spaceSwitch = definition.spaceSwitchByLabel(self._currentSpaceLabel)
        if spaceSwitch:
            spaceSwitch.type = event.text.replace(" Constraint", "").lower()
            logger.debug("ConstraintType Changed: {}".format(spaceSwitch.type))
            self.saveChanges()

    def onAddSpaceDriverClicked(self):
        currentSpaceSwitch = self.currentSpaceSwitch()
        driverName = self.newDriverLabel
        index = 0
        while currentSpaceSwitch.hasDriver(driverName):
            driverName = self.newDriverLabel + str(index)
            index += 1
        spaceDefaults = api.SpaceSwitchDriverDefinition(label=driverName,
                                                        driver=None)
        model = self.view.spaceWidgetContainer.spaceModel
        currentCount = model.rowCount()
        model.insertRow(currentCount, items=[spaceDefaults])
        with utils.blockSignalsContext((self.view.spaceWidgetContainer.defaultDriver,)):
            model.setData(model.index(currentCount, 1), self.driverComponents(), role=constants.enumsRole)
            self.view.spaceWidgetContainer.defaultDriver.addItem(self.newDriverLabel)
        self.saveChanges()
        self.view.spaceWidgetContainer.refresh()

    def onRemoveSpaceDriverClicked(self):
        logger.debug("Removing driver")
        container = self.view.spaceWidgetContainer
        model = container.spaceModel
        indices = container.spaceDriverView.selectedQIndices()
        visitedRows = set()
        culledIndices = []
        for index in indices:
            if index.row() in visitedRows:
                continue
            visitedRows.add(index.row())
            culledIndices.append(index)
        for flattenedGroup in reversed(
                list(modelutils.groupModelRowIndexes(sorted(culledIndices, key=lambda x: x.row())))):
            indices = [i for i in flattenedGroup if not model.rowDataSource.children[i.row()].isProtected]
            if not indices:
                continue

            firstRow = min(indices, key=lambda x: x.row())
            count = len(indices)
            model.removeRows(firstRow.row(), count)

        with utils.blockSignalsContext((container.defaultDriver,)):
            currentText = container.defaultDriver.currentText()
            container.defaultDriver.clear()
            container.defaultDriver.addItems([i.label for i in self.currentSpaceSwitch().drivers])
            container.defaultDriver.setToText(currentText)

    def onDrivenChanged(self, event):
        """

        :param event:
        :type event: :class:`zoo.libs.pyqt.extended.combobox.combobox.ComboItemChangedEvent`
        """
        definition = self.componentModel.component.definition
        spaceSwitch = definition.spaceSwitchByLabel(self._currentSpaceLabel)
        if spaceSwitch:
            drivenId = event.data
            spaceSwitch.driven = drivenId
            logger.debug("Driven changed:{}".format(drivenId))
            self.saveChanges()

    def driverComponentChanged(self, index, component, driverExpression):
        logger.debug("Updating Drivers for row index: {}".format(index))
        driverData = []
        if component is not None:
            driverData = self.driversForComponent(component, driverExpression)

        self.setDriverEnumForRow(index.row(), driverData)
        self.saveChanges()
        return driverData

    def driversForComponent(self, component, driverExpression):
        componentNameToken = component.serializedTokenKey()

        if component == self.componentModel.component:
            if driverExpression == self._localDriver.id:
                return [self._localDriver]
            newDrivers = component.spaceSwitchUIData().get("drivers", [])
            driverIndex = driverIndexForDriverId(driverExpression, newDrivers)
            if driverIndex != -1:
                return [newDrivers[driverIndex]]
        else:
            # because driver ids always start with self we need to remap to use the component token instead
            newDrivers = []
            for driver in component.spaceSwitchUIData().get("drivers", []):
                if driver.internal:
                    continue
                driverId = driver.id
                driverIdParts = api.splitAttrExpression(driverId)
                driver.id = api.pathAsDefExpression([componentNameToken] + driverIdParts[1:])
                newDrivers.append(driver)

        driverData = [HiveSpaceSwitchController._emptyDriver]
        driverData += newDrivers
        return driverData

    def setDriverEnumForRow(self, row, drivers):
        model = self.view.spaceWidgetContainer.spaceModel
        with utils.blockSignalsContext((model,)):
            model.setData(model.index(row, 2),
                          drivers,
                          role=constants.enumsRole)

    def drivenLabels(self):
        return [api.SpaceSwitchUIDriven(id_="", label="")] + self._componentSpaceUiData["driven"]

    def drivenLabelForExpression(self, expression):
        for i in self._componentSpaceUiData["driven"]:
            if i.id == expression:
                return i.label
        return ""


def driverIndexForDriverId(driverId, drivers):
    for i, driver in enumerate(drivers):
        if driver.id == driverId:
            return i
    return -1
