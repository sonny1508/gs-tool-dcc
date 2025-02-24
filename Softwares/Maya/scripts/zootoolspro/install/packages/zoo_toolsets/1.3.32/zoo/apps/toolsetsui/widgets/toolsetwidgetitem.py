import uuid

from zoovendor.Qt import QtWidgets, QtCore
from zoo.libs.pyqt.widgets import groupedtreewidget
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)

itemData = {}


class ToolsetWidgetItem(QtWidgets.QTreeWidgetItem):
    StartLargest = -1
    StartSmallest = 0
    uiData = {}

    def __init__(self, parent=None, toolsetId="", color=(255, 255, 255), toolsetRegistry=None, treeWidget=None,
                 strings=None,
                 toolsetWidget=None):
        """ The TreeWidgetItem which is placed in the rows of the TreeWidget

        :param parent:
        :type parent:
        :param toolsetId:
        :type toolsetId:
        :param color:
        :type color:
        :param toolsetRegistry:
        :type toolsetRegistry:
        :param treeWidget:
        :type treeWidget:
        :param strings:
        :type strings:
        :param toolsetWidget:
        :type toolsetWidget: zoo.apps.toolsetsui.widgets.toolsetwidget.ToolsetWidget
        """
        super(ToolsetWidgetItem, self).__init__(parent, strings)

        self.toolsetRegistry = toolsetRegistry
        self.toolsetId = toolsetId

        newToolsetWidget = self.toolsetRegistry.toolset(toolsetId)

        self.widget = toolsetWidget or newToolsetWidget(iconColor=color, widgetItem=self, treeWidget=treeWidget)

        self.color = color

        self.treeItem = self
        self.initialRowHeight = -1
        self.stackedLayout = self.widget.stackedWidget
        self.displayMode = self.initDisplaySize(ToolsetWidgetItem.StartSmallest)  # Start compact
        self.widgetContents = None

        self.initUi()

    def __hash__(self):
        return hash(id(self))

    @property
    def hidden(self):
        """Returns whether the current item is hidden.

        ..note:: This is for backwards compatibility, you should use item.isHidden()

        :rtype: bool
        """
        return self.isHidden()

    def initUi(self):
        self.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicator)
        self.setIconColour(self.color)
        self.setData(groupedtreewidget.DATA_COL, QtCore.Qt.EditRole,
                     groupedtreewidget.GroupedTreeWidget.ITEMTYPE_WIDGET)  # Data set to column 2, which is not visible

    def initDisplaySize(self, displaySize=StartLargest):
        """ Initial display size for the toolsets

        Can only be smallest or largest.

        :param displaySize: Smallest (compact) toolset size or largest (advanced) size
        :type displaySize: ToolsetWidgetItem.StartLargest or ToolsetWidgetItem.StartLargest
        :return:
        """
        self.displayMode = displaySize
        return displaySize

    def id(self):
        """ Widget ID

        :return:
        :rtype:
        """
        return self.widget.id

    def setCurrentIndex(self, index, activate=True):
        """ Display the contents widget by index

        :param index: Index of widget. -1 = last index
        :param activate:
        :type index:
        :return:
        """

        if index == -1:
            index = self.widget.count() - 1
            self.widget.displayModeButton.initialDisplay = self.widget.displayModeButton.LastIndex
        self.widget.saveProperties()  # save current widgets' properties before switching
        self.widget.setCurrentIndex(index)
        self.displayMode = index

        if self.treeWidget() is not None:
            self.treeWidget().activateItem(self, activate=activate)

    def widgetConnections(self):
        try:
            self.widget.maximized.disconnect()
        except (RuntimeError, TypeError):
            pass
        try:
            self.widget.deletePressed.disconnect()
        except (RuntimeError, TypeError):
            pass

        self.widget.deletePressed.connect(self.toggleHidden)
        self.widget.deletePressed.connect(lambda: self.treeWidget().toolsetHidden.emit(self.id()))

        self.widget.maximized.connect(lambda: self.treeWidget().activateItem(self, activate=True))
        self.widget.minimized.connect(lambda: self.treeWidget().activateItem(self, activate=False))

    def setContents(self, widget):
        self.widget = widget

    def setIconColour(self, col=(255, 255, 255)):
        self.color = col
        self.widget.setIconColor(col)

    def savePropertiesToData(self):
        """ Save the toolset widget data to the widgetItem's data column.

        :return:
        :rtype:
        """
        self.widget.savePropertyRequested.emit()
        dataUuid = str(uuid.uuid4())
        itemData[dataUuid] = self.widgetData()
        self.setData(groupedtreewidget.ITEMWIDGETINFO_COL, QtCore.Qt.EditRole, str(dataUuid))

    def setPropertiesData(self, data, update=True):
        """ ToolsetWidget data (or toolset properties) to be stored into the toolsetWidgetItem so it can be loaded up

        Usually its data straight from self.widgetData()

        :param update: Call for an update for the properties
        :type update:
        :param data: Usually its data straight from self.widgetData()
        :type data: dict
        :return:
        :rtype:
        """

        dataUuid = uuid.uuid4()
        itemData[str(dataUuid)] = data
        self.setData(groupedtreewidget.ITEMWIDGETINFO_COL, QtCore.Qt.EditRole, str(dataUuid))

        if update:
            QtCore.QTimer.singleShot(0, self.updatePropertiesFromData)

    def updatePropertiesFromData(self):
        """ Get the properties from the toolsetWidgetItem Data

        :return:
        :rtype:
        """

        dataUuid = str(self.data(groupedtreewidget.ITEMWIDGETINFO_COL, QtCore.Qt.EditRole))
        properties = itemData[dataUuid]['properties']
        self.widget.properties.update(properties, convertDict=True)
        self.widget.updatePropertyRequested.emit()

    def applyWidget(self, activate=True, recreateWidget=False):
        """ Applies the itemWidget to the TreeWidgetItem.

        Can only be done to be done after it is added to the tree.
        :return:
        """

        if recreateWidget:
            toolsetWidget = self.toolsetRegistry.toolset(self.toolsetId)

            self.widget = toolsetWidget(iconColor=self.color, treeWidget=self.treeWidget(),
                                        widgetItem=self)

        self.widget.setParent(self.treeWidget())

        self.treeWidget().setItemWidget(self, 0, self.widget)
        self.initialRowHeight = self.treeWidget().rowHeight(self.treeWidget().indexFromItem(self))

        self.widgetConnections()

        self.widget.preContentSetup()
        self.widgetContents = self.widget.contents()
        for contentWidget in self.widgetContents:
            self.widget.addStackedWidget(contentWidget)

        self.widget.autoLinkProperties(self.widgetContents)
        self.setData(groupedtreewidget.DATA_COL, QtCore.Qt.EditRole,
                     groupedtreewidget.GroupedTreeWidget.ITEMTYPE_WIDGET)  # Data set to column 2, which is not visible

        dataUuid = str(uuid.uuid4())

        itemData[dataUuid] = self.widgetData()
        savedData = self.data(groupedtreewidget.ITEMWIDGETINFO_COL, QtCore.Qt.EditRole) or str(dataUuid)
        self.setData(groupedtreewidget.ITEMWIDGETINFO_COL, QtCore.Qt.EditRole, savedData)

        self.updatePropertiesFromData()
        self.widget.populateWidgets()
        self.widget.postContentSetup()
        self.widget.updatePropertyRequested.emit()  # seems to updateFromProperties() on self.setCurrentIndex() next line
        self.setCurrentIndex(self.displayMode, activate)
        self.widget.updateDisplayButton()

    def widgetData(self):
        return {"toolsetId": self.widget.id, "properties": self.widget.properties}

    def collapse(self):
        self.widget.collapse()

    def expand(self, emit=False):
        self.widget.expand(emit)

    def collapsed(self):
        return (self.widget.collapsed)

    def defaultAction(self):
        """ To be overridden by subclass

        :return:
        """
        pass

    def toggleHidden(self, activate=True):
        self.setHidden(not self.isHidden())
        self.widget.setActive(activate)

    def setVisible(self, vis):
        pass

    def setHidden(self, hidden):
        """ Hides the ToolsetWidgetItem

        :param hidden:
        :return:
        """
        super(ToolsetWidgetItem, self).setHidden(hidden)
        self.treeWidget().updateTreeWidget()

        if hidden:
            self.widget.toolsetHidden.emit()
        else:
            self.widget.toolsetShown.emit()
