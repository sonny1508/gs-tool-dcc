from functools import partial

from zoovendor.Qt import QtWidgets, QtCore
from zoo.libs.pyqt.widgets import elements
from zoo.core.util import zlogging, strutils


logger = zlogging.getLogger(__name__)

# build script property types which auto generate if the buildscript specifies it
PROPERTY_WIDGETS = {"filePath": {"widget": elements.PathOpenWidget,
                                 "signal": "pathChanged",
                                 "getter": "path",
                                 "arguments": {"value": "path"}  # property key, widget kwargs
                                 },
                    "string": {"widget": elements.StringEdit,
                               "signal": "textModified",
                               "getter": "text",
                               "arguments": {"value": "editText",
                                             "displayName": "label"}  # property key, widget kwargs
                               },
                    "boolean": {
                        "widget": elements.CheckBox,
                        "signal": "stateChanged",
                        "getter": "checkState",
                        "arguments": {"value": "checked",
                                      "displayName": "label"}
                    }
                    }


class BuildScriptWidget(QtWidgets.QWidget):
    changed = QtCore.Signal()
    addedScript = QtCore.Signal(dict)
    removeScript = QtCore.Signal(dict)
    propertyChanged = QtCore.Signal(str, str, object)  # buildScript Name, propertyName, value

    def __init__(self, label, parent=None):
        """

        :param parent:
        :type parent:
        """
        super(BuildScriptWidget, self).__init__(parent)
        self.items = {}  # type: dict[str, dict[str, str]]
        self._currentItems = []  # type: list[str]
        self._initUi(label)

    def setItemList(self, items):
        """

        :param items:
        :type items:
        :return:
        :rtype:
        [{label:"", "id": ""}]
        """
        self.items = {i["id"]: i for i in items}
        self._updateList()

    def currentItems(self):
        return self._currentItems

    def setCurrentItems(self, itemIds):
        ids = []

        for itemId in itemIds:
            if itemId in self.items:
                ids.append(itemId)
        self._currentItems = ids
        self._updateList()

    def _initUi(self, label):

        mainLayout = elements.vBoxLayout(parent=self)
        tooltip = "Build scripts are python scripts that run during the rig build. \n\n" \
                  "Users can add their own, scripts live in the directory: \n" \
                  "(Documents)/zoo_preferences/assets/hive/buildscripts/"
        self.combo = elements.ComboBoxRegular(label,
                                              [''],
                                              labelRatio=5,
                                              toolTip=tooltip,
                                              boxRatio=16)
        self.combo.itemChanged.connect(self._comboChangedEvent)

        self.listLayout = elements.vBoxLayout()

        mainLayout.addWidget(self.combo)
        mainLayout.addLayout(self.listLayout)

    def addItem(self, key, itemInfo):
        properties = itemInfo["properties"]
        listItem = BuildScriptItem(strutils.titleCase(itemInfo["label"]), key, itemInfo, parent=self)
        self.listLayout.addWidget(listItem)
        listItem.closed.connect(self._onRemoveItem)
        if properties:
            listItem.propertyChanged.connect(partial(self._onBuildScriptItemPropertyChanged))
        self.changed.emit()

    def _updateList(self):
        self.combo.blockSignals(True)
        self.clear()
        self.combo.addItems([""] + [i["label"] for i in sorted(self.items.values(), key=lambda x: x["id"])])
        for item in self._currentItems:
            itemInfo = self.items[item]
            self.addItem(item, itemInfo)
        self.combo.blockSignals(False)
        self.changed.emit()

    def clear(self):
        layout = self.listLayout
        self.combo.clear()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _onBuildScriptItemPropertyChanged(self, itemKey, propertyName, propertyValue):
        self.propertyChanged.emit(itemKey, propertyName, propertyValue)

    def _onRemoveItem(self):
        widget = self.sender()
        index = self.listLayout.indexOf(widget)
        self._currentItems.remove(widget.key)
        self.removeScript.emit(self.items[widget.key])
        self.listLayout.takeAt(index)
        widget.deleteLater()

    def _comboChangedEvent(self, event=None):
        """

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        :return:
        :rtype:
        """
        text = self.combo.currentText()
        if not text:
            return
        if text not in self._currentItems:
            for k, v in self.items.items():
                if v["label"] == text:
                    self.addItem(text, v)
                    self._currentItems.append(v["id"])
                    self.addedScript.emit(v)
                    break
        self.combo.setToText("")


class BuildScriptItem(QtWidgets.QFrame):
    closed = QtCore.Signal()
    propertyChanged = QtCore.Signal(str, str, object)

    def __init__(self, name, key, buildScriptInfo, parent=None):
        super(BuildScriptItem, self).__init__(parent=parent)
        self.setObjectName("Hive{}".format(self.__class__.__name__))
        self.key = key
        self._label = elements.Label(name, parent=self)

        mainLayout = elements.vBoxLayout(parent=self, margins=(5, 2, 5, 2))
        layout = elements.hBoxLayout()
        self.propertyLayout = elements.GridLayout()

        closeButton = elements.ExtendedButton(parent=self)
        closeButton.setIconByName("xMark")
        closeButton.setFixedSize(QtCore.QSize(20, 20))
        closeButton.leftClicked.connect(self.closed.emit)

        layout.addWidget(self._label)
        layout.addWidget(closeButton)
        mainLayout.addLayout(layout)
        mainLayout.addLayout(self.propertyLayout)

        self.properties = buildScriptInfo["properties"]
        self.bakedProperties = buildScriptInfo["defaultPropertyValue"]
        self.generateProperties()

    def generateProperties(self):
        """Auto generates UI widgets based the properties on the build script plugin properties.
        """
        for prop in self.properties:
            propType = prop["type"]
            propWidgetClsMap = PROPERTY_WIDGETS.get(propType)  # type: dict
            if propWidgetClsMap is None:
                logger.warning("No Support for property: {}".format(prop))
                continue
            # retrieve the serialized property value from the rig configuration as this is the default
            defaultValue = self.bakedProperties.get(prop["name"])
            if defaultValue is not None:
                prop["value"] = defaultValue
            signalFuncName = propWidgetClsMap["signal"]
            kwargs = {}

            # map the widget mapping arguments to the widget __init__ arguments
            for propKey, widgetArg in propWidgetClsMap.get("arguments", {}).items():
                requestedValue = prop.get(propKey)
                if requestedValue is not None:
                    kwargs[widgetArg] = requestedValue

            propWidget = propWidgetClsMap["widget"](parent=self, **kwargs)
            toolTip = prop.get("toolTip", "")
            if toolTip:
                propWidget.setToolTip(toolTip)
            # connect the widgets matching signal pointer to self._propertyChanged.
            getattr(propWidget, signalFuncName).connect(
                partial(self._onPropertyChanged, widget=propWidget, property=prop))
            layout = prop["layout"]
            self.propertyLayout.addWidget(propWidget, layout[0], layout[1])

    def _onPropertyChanged(self, *args, **kwargs):
        """

        :param kwargs:
        :type kwargs: dict
        :return:
        :rtype:
        :keyword property (dict): The build script property dict.
        :keyword widget (:class:`QtWidgets.QWidget`): The Property widget type instance.
        """
        propertyInfo = kwargs["property"]
        propertyWidgetInstance = kwargs["widget"]
        propType = propertyInfo["type"]
        propWidgetClsMap = PROPERTY_WIDGETS.get(propType)
        propertyValue = getattr(propertyWidgetInstance, propWidgetClsMap["getter"])()
        propertyValue = _handlePropertyValue(propType, propertyValue)
        self.propertyChanged.emit(self.key, propertyInfo["name"], propertyValue)


def _handlePropertyValue(propType, propertyValue):
    if propType == "boolean":
        return bool(propertyValue)
    return propertyValue
