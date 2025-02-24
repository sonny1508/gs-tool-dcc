from functools import partial

from zoo.apps.hiveartistui import artistuicore
from zoo.apps.hiveartistui.registries import registry
from zoo.apps.hiveartistui.views import componentwidget
from zoo.apps.hiveartistui.views import treewidgetframe
from zoo.core.util import zlogging
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import extendedbutton, groupedtreewidget, elements
from zoo.preferences.interfaces import coreinterfaces
from zoovendor.Qt import QtWidgets, QtGui, QtCore


logger = zlogging.getLogger(__name__)


class ComponentTreeView(treewidgetframe.TreeWidgetFrame):
    """
    The main overarching view which shows the title, the search bar and the
    ComponentTreeWidget itself.

    ComponentTreeView
        SearchBar
        ComponentTreeWidget
            list(TreeWidgetItem)
    """

    def __init__(self, lib=None, parent=None, componentRegistry=None, uicore=None):
        super(ComponentTreeView, self).__init__(parent=parent, title="SETTINGS")
        self.preferences = coreinterfaces.coreInterface()
        toolTip = "Selects the selected scene components, in the UI."
        self.highlightBtn = extendedbutton.ExtendedButton(parent=parent)
        self.highlightBtn.setToolTip(toolTip)
        toolTip = "Selects the selected UI components, in the scene."
        self.selectInSceneBtn = extendedbutton.ExtendedButton(parent=parent)
        self.selectInSceneBtn.setToolTip(toolTip)
        self.groupBtn = extendedbutton.ExtendedButton(parent=parent)
        tooltip = "Click for more Component options."
        self.menuBtn = extendedbutton.ExtendedButton(parent=parent)
        self.menuBtn.setToolTip(tooltip)
        self.core = uicore  # type: artistuicore.HiveUICore
        self.treeWidget = None  # type: ComponentTreeWidget or None
        self.uiInterface = self.core.uiInterface

        self.componentRegistry = componentRegistry
        self.initUi(ComponentTreeWidget(lib, parent, componentRegistry, uicore))

        self.connections()

    def initUi(self, treeWidget):
        """
        Initialize Ui
        :return:
        """

        super(ComponentTreeView, self).initUi(treeWidget)
        self.setContentsMargins(0, 0, 0, 0)

    def setupToolbar(self):
        """
        The toolbar for the ComponentTreeView which will have widgets such as the searchbar,
        and other useful buttons.
        :return:
        """

        super(ComponentTreeView, self).setupToolbar()
        highlightTool = self.core.toolRegistry.plugin("highlightFromScene")(logger, uiInterface=self.uiInterface)
        selectInSceneTool = self.core.toolRegistry.plugin("selectInScene")(logger, uiInterface=self.uiInterface)
        foreColor = self.preferences.MAIN_FOREGROUND_COLOR
        size = 16
        selSceneUiData = selectInSceneTool.uiData
        highlghtUiData = highlightTool.uiData
        self.highlightBtn.setIconByName(highlghtUiData["icon"], colors=highlghtUiData["iconColor"], size=size)
        self.selectInSceneBtn.setIconByName(selSceneUiData["icon"], colors=selSceneUiData["iconColor"], size=size)
        self.groupBtn.setIconByName("folderadd", colors=foreColor, size=size)
        self.menuBtn.setIconByName("menudots", colors=foreColor, size=size)
        self.groupBtn.hide()  # todo: reimplement this

        self.toolbarLayout.addWidget(self.highlightBtn)
        self.toolbarLayout.addWidget(self.selectInSceneBtn)
        # self.toolbarLayout.addSpacing(sp)
        self.toolbarLayout.addWidget(self.groupBtn)
        # self.toolbarLayout.addSpacing(sp)
        self.toolbarLayout.addWidget(self.menuBtn)

        # Menu set up
        actions = self.menuActions()

        for toolObj, toolType, variantId in self.core.toolRegistry.iterToolsFromLayout(actions):
            if toolType == "PLUGIN":
                tool = toolObj(logger, uiInterface=self.uiInterface)
                self.addMenuActionTool(tool, self.menuBtn, variantId)
            elif toolType == "SEPARATOR":
                self.menuBtn.addSeparator()

        self.menuBtn.setMenuAlign(QtCore.Qt.AlignRight)

        # Toolbar layout setup in super.toolbar()
        self.highlightBtn.leftClicked.connect(partial(self._executeTool, highlightTool))
        self.selectInSceneBtn.leftClicked.connect(partial(self._executeTool, selectInSceneTool))
        self.groupBtn.leftClicked.connect(self.treeWidget.groupActionTriggered)

    def menuActions(self):
        """ Actions for the component tree menu

        :return:
        :rtype: list[basestring]
        """
        return ["selectInScene", "highlightFromScene", "minimizeAllComponents", "maximizeAllComponents",
                "selectAll", "invertSelection", "---",
                "duplicateComponent", "mirrorComponents", "mirrorComponents:all", "---",
                "deleteAllComponents"]

    def addMenuActionTool(self, hiveTool, menu, variantId=None):
        """ Add menu action tool

        :param variantId:
        :type variantId: basestring
        :param hiveTool:
        :type hiveTool: zoo.apps.hiveartistui.hivetool.HiveTool
        :param menu:
        :type menu: searchablemenu.SearchableMenu

        :return:
        :rtype:
        """

        uiData = hiveTool.uiData
        label = uiData["label"]
        icon = uiData["icon"]

        if variantId:
            try:
                variant = [x for x in hiveTool.variants() if x['id'] == variantId][0]
                label = variant['name']
                icon = variant['icon']
            except:
                raise Exception("variantId '{}' doesn't exist for '{}'".format(variantId, hiveTool))

        action = self.menuBtn.addAction(label, icon=hiveTool.icon(), connect=None)


        hiveTool.refreshRequested.connect(self.sync)

        action.setProperty("tool", hiveTool)
        action.setProperty("variant", variantId)

        # Icon
        try:
            icon = iconlib.iconColorizedLayered(icon)
            action.setIcon(icon)
        except AttributeError:
            pass

        action.triggered.connect(partial(self._executeTool, hiveTool, variantId))

    def _executeTool(self, tool, variantId=None):
        """ Execute Hive tool.
        Todo bit redundant, maybe replace this with self.core version

        :param tool:
        :type tool: zoo.apps.hiveartistui.hivetool.HiveTool
        :return:
        :rtype:
        """
        # override the tool models to be the current selection
        tool.setSelected(self.core.selection)
        # set the current model
        if len(self.core.selection.componentModels) > 0:
            tool.model = self.core.selection.componentModels[0]
        else:
            tool.model = None
        tool.process(variantId)

    def connections(self):
        self.searchEdit.textChanged.connect(self.onSearchChanged)

    def onRigModeChanged(self, rigMode):
        for widget in self.treeWidget.iterComponentWidgets():
            widget.onRigModeChanged(rigMode)

    def addComponent(self, component, group=None):
        """
        Adds the component to the ComponentTreeWidget
        :param group:
        :param component:
        :type component: hive.zoo.libs.hivebase.component.Component()
        :return:
        """
        self.treeWidget.addComponent(component, group=group)

    def sync(self):
        """ Synchronize to model
        :return:
        """

        self.treeWidget.sync()  # type: ComponentTreeWidget

    def applyRig(self, rigModel):
        """ Apply the current RigModel and build it out in the TreeView.

        The rigmodel may need grouping capabilities so when it rebuilds it in the ui we'll have groups

        :param rigModel:
        :type rigModel: zoo.apps.hiveartistui.model.RigModel
        :return:
        """

        self.setUpdatesEnabled(False)
        for c in rigModel.componentModels():
            self.addComponent(c)
        self.treeWidget.clearSelection()
        self.setUpdatesEnabled(True)

    def clear(self):
        """
        Clear out and empty the treewidget
        :return:
        """
        self.treeWidget.clear()


class ComponentTreeWidget(groupedtreewidget.GroupedTreeWidget):
    """
    The TreeWidget which will be placed in the ComponentTreeView.
    """

    def __init__(self, lib=None, parent=None, componentMdlReg=None, uicore=None):
        """

        :param lib:
        :param parent:
        :param componentMdlReg:
        :type componentMdlReg: registry.ComponentModelRegistry
        :param uicore:
        :type uicore: artistuicore.HiveUICore
        """
        super(ComponentTreeWidget, self).__init__(parent=parent, allowSubGroups=True)

        self.groupDrop = []
        self.registry = componentMdlReg

        self.lib = lib
        self.initUi()
        self.core = uicore  # type: artistuicore.HiveUICore

        self.headerItem = QtWidgets.QTreeWidgetItem(["Component"])

    def connections(self):
        """
        Connect events
        :return:
        """

        super(ComponentTreeWidget, self).connections()
        self.customContextMenuRequested.connect(self.contextMenu)
        # self.itemClicked.connect(self.itemClickedEvent)

    def componentWidgetByModel(self, componentModel):
        """ Retrieves component widget by model

        :param componentModel:
        :return:
        """
        for cw in self.componentWidgets():
            if cw.model == componentModel:
                return cw

    def itemClickedEvent(self, item, col):
        pass

    def treeSelectionChanged(self):
        """ When the selection is changed in the UI

        :return:
        """
        super(ComponentTreeWidget, self).treeSelectionChanged()

        componentModels = []

        for it in self.selectedItems():
            itemWidget = self.itemWidget(it)
            if self.itemType(it) == self.ITEMTYPE_WIDGET and itemWidget is not None:
                componentModels.append(itemWidget.model)
        self.updateSelectionColours()
        self.core.setSelectedComponents(componentModels)

    def updateSelectionColours(self):
        """ Go through each ComponentWidget and set the colours based on selection

        :return:
        """

        for i in range(self.invisibleRootItem().childCount()):
            treeItem = self.invisibleRootItem().child(i)
            itemWidget = self.itemWidget(treeItem)

            if itemWidget is not None:

                updateTargets = []
                # Depending on the type, we want to apply the object name differently
                if self.itemType(treeItem) == self.ITEMTYPE_WIDGET:
                    updateTargets = [itemWidget.titleFrame, itemWidget.widgetHider]
                elif self.itemType(treeItem) == self.ITEMTYPE_GROUP:
                    updateTargets = [itemWidget.titleFrame]

                # Apply object name
                if treeItem.isSelected():
                    [utils.setStylesheetObjectName(t, "selected") for t in updateTargets]

                elif not treeItem.isSelected():
                    [utils.setStylesheetObjectName(t, "") for t in updateTargets]

    def contextMenu(self, pos):
        """ The context menu for the ComponentTreeWidget.

        Some actions for the menu is handled here.

        :param pos:
        :return:
        """

        items = self.selectedItems()

        # Show component context menu
        if len(items) > 0:
            sel = self.selectedItems()[-1]
            wgt = self.itemWidget(sel, groupedtreewidget.WIDGET_COL)
            # Todo: work with groups as well
            if isinstance(wgt, componentwidget.ComponentWidget):
                m = wgt.contextMenu()
                m.exec_(QtGui.QCursor.pos())

    def componentHash(self, model):
        """ Hash of component model

        :param model:
        :return:
        """
        return hash(model)

    def startDrag(self, supportedActions, widget=None):
        """ Override the default start drag which is run in the mousePressEvent

        Here we get a pixmap of the itemWidget and use that as the drag

        :param widget:
        :param supportedActions:
        :return:
        """
        itemPos = self.mapFromGlobal(QtGui.QCursor.pos())
        item = self.itemAt(itemPos)

        titleFrame = self.itemWidget(item, groupedtreewidget.WIDGET_COL).titleFrame

        self.setDragWidget(titleFrame, hotspotAlign=QtCore.Qt.AlignVCenter)

        super(ComponentTreeWidget, self).startDrag(supportedActions, titleFrame)

    def collapseAll(self):
        """
        Collapses all ComponentWidgets in the TreeWidget
        :return:
        """
        self.sync()

        for itemWidget in self.itemWidgets():
            itemWidget.collapse()

    def expandAll(self):
        """
        Expands all ComponentWidgets in the TreeWidget
        :return:
        """
        self.sync()

        for itemWidget in self.itemWidgets():
            itemWidget.expand()

    def componentWidgets(self, group=None):
        """ Gets all the component widgets in group.

        If group is none, then get the root level
        :return:
        :rtype: list[:class:`componentwidget.ComponentWidget`]
        """

        return self.itemWidgets(group)

    def addComponent(self, componentModel, group=None):
        """Adds a ComponentWidget to the ComponentTreeWidget based on the component data given

        :param componentModel:
        :type componentModel: hive.zoo.libs.hivebase.component.Component()
        :param group:
        :return:
        """
        c = componentwidget.ComponentWidget(componentModel=componentModel, parent=self, core=self.core)
        c.syncRequested.connect(self.sync)
        self.addComponentWidget(c, group)

        if self.updatesEnabled():
            self.sync()

        return c

    def groupActionTriggered(self):
        """
        Event for when groupAction for the contextMenu is triggered
        :return:
        """

        name = self.getUniqueGroupName()
        groupWgt = groupedtreewidget.GroupWidget(name)

        self.addGroup(name=name, groupWgt=groupWgt)

    def addComponentWidget(self, componentWgt, group=None):
        """ Adds the ComponentWidget to the ComponentTreeWidget

        :param group:
        :param componentWgt: Must be a subclass of ComponentWidget
        :return:
        """
        newTreeItem = self.addNewItem(componentWgt.componentType, componentWgt, widgetInfo=hash(componentWgt.model),
                                      itemType=self.ITEMTYPE_WIDGET)

        if group is not None:
            self.addToGroup(newTreeItem, group)

    def updateWidget(self, item):
        """ Update the QTreeWidgetItem to its itemWidget.

        In this case it is the ComponentWidget

        :param item:
        :return:
        """
        # Retrieve the componentModel that is stored in the item
        modelHash = self.itemWidgetInfo(item)

        model = self.core.componentModelByHash(int(modelHash))

        self.setItemWidget(item, groupedtreewidget.WIDGET_COL, componentwidget.ComponentWidget(componentModel=model,
                                                                                               parent=self,
                                                                                               core=self.core))

    def dropEvent(self, event):
        if event.source() is not self:
            logger.info("Oops, dragging to components separate windows doesn't work yet!")
        else:
            super(ComponentTreeWidget, self).dropEvent(event)

        self.sync()

    def setupComponentConnections(self, widget, treeItem):
        """ Set up connections of the ComponentTreeWidget

        :param widget:
        :type widget: zoo.apps.hiveartistui.views.componentwidget.ComponentWidget
        :param treeItem:
        :type treeItem: QtWidgets.QTreeWidgetItem
        :return:
        """
        widget.minimized.connect(self.updateTreeWidget)
        widget.maximized.connect(self.updateTreeWidget)
        widget.deletePressed.connect(partial(self.componentDeleteItem, treeItem))
        widget.componentRenamed.connect(self.componentRenamed)

    def componentRenamed(self):
        for widget in self.iterComponentWidgets():
            widget.updateUi()

    def iterComponentWidgets(self):
        """ Iterate through the component widgets

        :return:
        :rtype:
        """
        for it in self.iterator():
            widget = self.itemWidget(it)
            if widget:
                yield widget

    def deleteActionTriggered(self):
        """
        Deletes all the selected items
        :return:
        """
        self.deleteSelected()
        self.sync()

    def deleteSelected(self):
        """ Deletes all the selected items

        :return:
        """
        componentStrList = ""
        # Get the text based on the type Component or Group
        for s in self.selectedItems():

            itemType = self.itemType(s)
            if itemType == self.ITEMTYPE_WIDGET:
                componentStrList += "    {}\n".format(self.itemWidget(s, groupedtreewidget.WIDGET_COL).model.name)
            elif itemType == self.ITEMTYPE_GROUP:
                componentStrList += "    {}\n".format(s.text(groupedtreewidget.WIDGET_COL))

        # Send out the message box
        ret = elements.MessageBox.showWarning(None,
                                              'Delete Components?',
                                              'Are you sure you want to delete the following components or groups?\n\n{}\n'.format(
                                                  componentStrList),
                                              buttonA="Yes", buttonB="Cancel")

        if ret == "A":
            # Get the rig to delete
            for s in self.selectedItems():
                self.deleteItem(s)

        elif ret == "B":
            logger.info("cancel was clicked")

    def minimizeActionTriggered(self):
        """
        Minimize action triggered by button in UI
        :return:
        """
        self.minimizeSelected()

    def selectAll(self):
        super(ComponentTreeWidget, self).selectAll()

    def maximizeActionTriggered(self):
        """ Maximize action triggered by button in UI

        :return:
        """
        self.maximizeSelected()

    def maximizeSelected(self):
        for s in self.selectedItems():
            self.itemWidget(s).expand()

    def maximizeAll(self):
        for treeItem in self.treeItems():
            self.itemWidget(treeItem).expand()

    def minimizeSelected(self):
        for s in self.selectedItems():
            self.itemWidget(s).collapse()

    def minimizeAll(self):
        for treeItem in self.treeItems():
            self.itemWidget(treeItem).collapse()

    def treeItems(self):
        """

        :return:
        :rtype: list[groupedtreewidget.TreeWidgetItem]
        """

        return list(self.iterator())

    def itemWidget(self, treeItem, col=None):
        """ Get the treeItem's widget

        :param treeItem:
        :type treeItem:
        :param col:
        :type col:
        :return:
        :rtype: componentwidget.ComponentWidget
        """
        return super(ComponentTreeWidget, self).itemWidget(treeItem, col)

    def getComponentWidget(self, treeItem):
        """
        Gets the ComponentWidget from the treeItem
        :param treeItem:
        :return: ComponentWidget
        :rtype: ComponentWidget
        """

        return self.itemWidget(treeItem)

    def componentDeleteItem(self, item):
        """
        Sent by the delete button on the component
        Some of this code may be redundant, will have to fix
        :return:
        """
        wgt = self.itemWidget(item)
        componentName = wgt.model.name

        ret = elements.MessageBox.showWarning(None,
                                              'Delete Component?',
                                              'Are you sure you want to delete '
                                              'the following component or group: "{}"?'.
                                              format(componentName),
                                              buttonA="Yes",
                                              buttonB="Cancel")

        if ret == "A":
            # Get the rig to delete
            self.deleteItem(item)

        elif ret == "B":
            logger.info("cancel was clicked")

    def deleteItem(self, item):
        """ Deletes the TreeWidgetItem from the ComponentTreeWidget.
        Can be the QTreeWidgetItem or the ComponentWidget itself
        :param item:
        :type item: QtWidgets.QTreeWidgetItem
        :return:
        """
        wgt = None
        if isinstance(item, QtWidgets.QTreeWidgetItem):
            wgt = self.itemWidget(item)

        # Delete by item type
        itemType = self.itemType(item)
        if itemType == self.ITEMTYPE_WIDGET:
            root = self.invisibleRootItem()

            if wgt is not None:
                self.core.deleteComponent(wgt.model)
                (item.parent() or root).removeChild(item)

        elif itemType == self.ITEMTYPE_GROUP:
            # Delete the children first before deleting the group
            children = [item.child(i) for i in range(0, item.childCount())]
            for c in children:
                self.deleteItem(c)

            index = self.indexFromItem(item).row()
            self.takeTopLevelItem(index)

    def setItemWidget(self, item, column, wgt):
        """ Set Item widget

        We want to add some additional stuff to the setItemWidget.
        :param item:
        :param column:
        :param wgt:
        :return:
        """
        if isinstance(wgt, componentwidget.ComponentWidget):
            # If it is a ComponentWidget
            self.setupComponentConnections(wgt, item)

        super(ComponentTreeWidget, self).setItemWidget(item, column, wgt)

    def duplicateItem(self, item):
        """
        Duplicates the item. It does this by duplicating the itemWidget inside the treeItem.

        TODO: This still needs work

        :param item:
        :rtype item: QtWidgets.QTreeWidgetItem
        :return:
        """
        # Todo: work on this
        pass

    def itemWidgets(self, itemType=None, treeItem=None):
        """

        :param itemType:
        :param treeItem:
        :return:
        :rtype: list[zoo.apps.hiveartistui.views.componentwidget.ComponentWidget]
        """
        return super(ComponentTreeWidget, self).itemWidgets(itemType, treeItem)

    def sync(self):
        """ Sync to model """
        for item in self.itemWidgets(itemType=self.ITEMTYPE_WIDGET):  # type: componentwidget.ComponentWidget
            item.sync()

    def updateTree(self, delayed=False):
        """ Update the tree

        Same as updateTreeWidget but if it needs some extra refreshes use this one.

        :param delayed: If delayed is true, it will do it after the timer of 0 seconds. Can help with some refresh issues
        :return:
        """
        if delayed:
            QtCore.QTimer.singleShot(0, self.updateTree)
            return
        self.setUpdatesEnabled(False)
        self.updateTreeWidget()
        self.core.uiInterface.artistUi().resizeWindow()
        self.updateTreeWidget()  # needs to be done a second time for some reason
        self.setUpdatesEnabled(True)
