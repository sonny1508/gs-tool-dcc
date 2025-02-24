from zoo.libs.hive import api
from zoo.libs.pyqt.models import datasources


class SpaceLabelDataSource(datasources.BaseDataSource):

    def __init__(self, controller, headerText=None, model=None, parent=None):
        super(SpaceLabelDataSource, self).__init__(headerText, model, parent)
        self.controller = controller

    def supportsDrag(self, index):
        return True

    def supportsDrop(self, index):
        return True

    def mimeData(self, indices):
        return [self._children[index.row()] for index in indices]

    def dropMimeData(self, items, action):
        return {"items": items}

    def isEditable(self, index):
        space = self.userObject(index)  # type: api.SpaceSwitchDriverDefinition
        return space.renameAllowed

    def data(self, index):
        spaceInfo = self.userObject(index)  # type: api.SpaceSwitchDriverDefinition
        if spaceInfo is not None:
            return spaceInfo.label

    def setData(self, index, value):
        if not value:
            return False
        spaceInfo = self.userObject(index)  # type: api.SpaceSwitchDriverDefinition
        if spaceInfo is not None and not self.controller.currentSpaceSwitch().hasDriver(value):
            spaceInfo.label = value
            self.controller.driverLabelChangedSig.emit(index, value)
            return True
        return False

    def insertChildren(self, index, children):
        self._children[index:index] = children
        return True

    def insertRowDataSources(self, index, count, items):
        return self.insertChildren(index, items)


class DriverComponentDataSource(datasources.ColumnEnumerationButtonDataSource):
    def isEditable(self, rowDataSource, index):
        space = rowDataSource.userObject(index)  # type: api.SpaceSwitchDriverDefinition
        return space.driverChangeAllowed

    def enums(self, rowDataSource, index):
        return [i.label for i in super(DriverComponentDataSource, self).enums(rowDataSource, index)]

    def data(self, rowDataSource, index):
        data = super(DriverComponentDataSource, self).data(rowDataSource, index)
        if data:
            return data.label

    def setData(self, rowDataSource, index, value):
        spaceInfo = rowDataSource.userObject(index)  # type: api.SpaceSwitchDriverDefinition
        if spaceInfo is None:
            return False
        currentEnum = self._enums[index][self.currentIndex[index]]
        enum = self._enums[index][value]

        if enum == currentEnum:
            return False
        expr = enum.id
        spaceInfo.driver = expr
        componentToken = api.componentTokenFromExpression(expr)
        if componentToken:
            if api.pathAsDefExpression(componentToken) in (api.constants.ATTR_EXPR_SELF_TOKEN,
                                                                api.constants.ATTR_EXPR_INHERIT_TOKEN):
                component = rowDataSource.controller.componentModel.component
            else:
                component = rowDataSource.controller.rigModel.rig.component(*componentToken)
            rowDataSource.controller.driverComponentChangedSig.emit(self.model.index(index, 1), component, expr)

        result = super(DriverComponentDataSource, self).setData(rowDataSource, index, value)
        return result

    def dataByRole(self, rowDataSource, index, role):
        return rowDataSource.controller.setDriverComponentFromSelection(index)


class DriverDataSource(datasources.ColumnEnumerationDataSource):
    def isEditable(self, rowDataSource, index):
        space = rowDataSource.userObject(index)  # type: api.SpaceSwitchDriverDefinition
        return space.driverChangeAllowed

    def enums(self, rowDataSource, index):
        return [i.label for i in super(DriverDataSource, self).enums(rowDataSource, index)]

    def data(self, rowDataSource, index):
        data = super(DriverDataSource, self).data(rowDataSource, index)
        if data:
            return data.label

    def setData(self, rowDataSource, index, value):
        spaceInfo = rowDataSource.userObject(index)  # type: api.SpaceSwitchDriverDefinition
        if spaceInfo is None:
            return False
        # happens when the combobox has no values ie localSpace
        try:
            currentEnum = self._enums[index][self._currentIndex[index]]
        except (ValueError, KeyError, IndexError):
            return False
        enum = self._enums[index][value]
        if enum == currentEnum:
            return False
        try:
            chosenDriver = enum.id

        except IndexError:  # occurs when we set driver component to inherit which is basically resets the enums to []
            return
        parts = api.splitAttrExpression(spaceInfo.driver)  # driverComponent
        chosenDriverParts = api.splitAttrExpression(chosenDriver)
        parts = [parts[0]] + chosenDriverParts[1:]

        expr = api.pathAsDefExpression(parts)

        componentToken = api.componentTokenFromExpression(expr)
        if not componentToken:
            return
        spaceInfo.driver = expr
        rowDataSource.controller.driverChangedSig.emit(index, expr)
        return super(DriverDataSource, self).setData(rowDataSource, index, value)
