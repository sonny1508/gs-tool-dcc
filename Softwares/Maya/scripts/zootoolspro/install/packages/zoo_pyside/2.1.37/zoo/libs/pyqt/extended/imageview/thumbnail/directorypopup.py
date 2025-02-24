from zoo.libs import iconlib
from zoo.core.tooldata import tooldata
from zoo.core.util import zlogging

from zoovendor.Qt import QtCore, QtWidgets
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import layouts, buttons
from zoo.libs.pyqt.models import treemodel, datasources, delegates, constants as modelconstants
from zoo.libs.pyqt.extended import treeviewplus
from zoo.libs.pyqt.widgets.frameless.widgets import TitleBar
from zoo.libs.pyqt.widgets.frameless.window import ZooWindow
from zoo.libs.pyqt.widgets import popups

logger = zlogging.getLogger(__name__)


class DirectoryTitleBar(TitleBar):
    def __init__(self, *args, **kwargs):
        super(DirectoryTitleBar, self).__init__(*args, **kwargs)

    def setTitleStyle(self, style):
        """ Set title style for directory popup title bar

        :param style:
        :return:

        """

        if style != "POPUP":
            return
        self.setFixedHeight(utils.dpiScale(int(30)))
        self.titleLabel.setFixedHeight(utils.dpiScale(20))
        self.helpButton.hide()
        self.logoButton.hide()
        self.closeButton.hide()
        self.leftContents.hide()
        self.setTitleSpacing(False)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._splitLayout.setSpacing(0)
        utils.setHSizePolicy(self.rightContents, QtWidgets.QSizePolicy.Ignored)

        self.titleLayout.setContentsMargins(*utils.marginsDpiScale(7, 8, 20, 7))
        self._mainRightLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 8, 0))


class DirectoryPopup(ZooWindow):
    selectionChanged = QtCore.Signal(object)

    def __init__(self, browserPreference=None, parent=None, autoHide=False, attachToParent=True):
        super(DirectoryPopup, self).__init__(titleBar=DirectoryTitleBar, title="Directories",
                                             width=200, height=400, overlay=False, parent=parent,
                                             onTop=False, minimizeEnabled=False, maxButton=False,
                                             saveWindowPref=False)
        self.autoHide = autoHide
        self._browsing = False
        self._attached = True
        self._attachToParent = attachToParent
        self._anchorWidget = None
        self._browserPreference = browserPreference
        self._treeModel = FolderTreeModel(browserPreference, root=None, parent=self)
        self.initUi()

    def _initFramelessLayout(self):
        super(DirectoryPopup, self)._initFramelessLayout()
        self.setTitleStyle("POPUP")
        self.titleBar.setTitleAlign(QtCore.Qt.AlignLeft)

    @property
    def browserPreference(self):
        return self._browserPreference

    @browserPreference.setter
    def browserPreference(self, value):
        self._browserPreference = value
        self._treeModel.browserPreference = value

    @property
    def mouseReleased(self):
        return self.treeView.mouseReleased

    def initUi(self):
        self.treeView = treeviewplus.TreeViewPlus(parent=self)
        self.treeView.setSearchable(False)
        self.treeView.setShowTitleLabel(False)
        self.treeView.treeView.setHeaderHidden(True)
        self.treeView.slidingWidget.setVisible(False)
        self.treeView.treeView.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)  # Remove dotted line on selection
        self.treeView.treeView.setIndentation(utils.dpiScale(10))
        self.treeView.setAlternatingColorEnabled(False)
        self.treeView.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        delegate = delegates.HtmlDelegate(parent=self.treeView)
        self.treeView.treeView.setItemDelegateForColumn(0, delegate)


        self.treeView.setModel(self._treeModel)

        layout = layouts.vBoxLayout()
        self.setMainLayout(layout)
        headerLayout = layouts.hBoxLayout(margins=(0, 2, 5, 2), spacing=6)
        self.titleBar.cornerContentsLayout.addLayout(headerLayout)

        self._closeButton = buttons.ExtendedButton(parent=self)
        self._closeButton.setIconByName("xMark", size=10)  # close icon
        self._closeButton.setFixedSize(QtCore.QSize(10, 10))

        size = 13
        btnSize = QtCore.QSize(size, size)
        self._addDirectoryBtn = buttons.ExtendedButton(parent=self)
        self._addDirectoryBtn.setIconByName("plusHollow", size=size)  # add folder icon
        self._addDirectoryBtn.setIconSize(btnSize)
        self._addDirectoryBtn.setFixedSize(btnSize)
        self._minusButton = buttons.ExtendedButton(parent=self)
        self._minusButton.setIconByName("minusHollow", size=size)  # remove icon
        self._minusButton.setIconSize(QtCore.QSize(size, size))
        self._minusButton.setFixedSize(btnSize)

        ds = QtCore.QSize(size, size)
        self._dotsMenu = buttons.ExtendedButton(parent=self)
        self._dotsMenu.setIconByName("menudots", size=size)
        self._dotsMenu.setIconSize(ds)
        self._dotsMenu.setFixedSize(ds)
        self._dotsMenu.hide()

        self.titleBar.windowButtonsLayout.addWidget(self._addDirectoryBtn)
        self.titleBar.windowButtonsLayout.addWidget(self._minusButton)
        self.titleBar.windowButtonsLayout.addWidget(self._dotsMenu)
        self.titleBar.windowButtonsLayout.addWidget(self._closeButton)
        layout.addWidget(self.treeView)

        self.treeView.selectionChanged.connect(self._onSelectionChanged)

        self.filter.windowEvent.connect(self.windowEvents)
        self.titleBar.moving.connect(self._titleBarMoving)
        self._minusButton.leftClicked.connect(self.deleteButtonClicked)
        self._closeButton.leftClicked.connect(self.close)

        # Right Click Add Menu ------------
        self._addDirectoryBtn.addAction("Add Folder Alias From Disk...",
                                        mouseMenu=QtCore.Qt.LeftButton,
                                        icon=iconlib.icon("closeFolder"),
                                        connect=self.onNewDirectory)
        self._addDirectoryBtn.addAction("Add Category (Empty Container)",
                                        mouseMenu=QtCore.Qt.LeftButton,
                                        icon=iconlib.icon("triangleDownTiny"),
                                        connect=self.onNewCategory)

    def setAnchorWidget(self, widget):
        self._anchorWidget = widget

    def _titleBarMoving(self):
        """ Detach when moving

        :return:
        """
        self._attached = False
        self.window().activateWindow()

    def _onSelectionChanged(self, event):
        directories = []
        categories = []
        # using the selection as the event object only contains the difference between
        # each selection event not the entire selection
        currentSelection = self.treeView.selectedItems()
        for dataSource in currentSelection:
            if type(dataSource) == CategoryFolder:
                categories.append(dataSource.folderId())
                for child in dataSource.iterChildren():
                    if type(child) == FolderItem:
                        directories.append(child.internalData)
            else:
                directories.append(dataSource.internalData)
        outputIds = [d.id for d in directories]
        self.browserPreference.setActiveDirectories(directories)
        self.browserPreference.setActiveCategories(categories)
        self.selectionChanged.emit(outputIds)

    def windowEvents(self, event):
        """ Window events from the event filter

        :param event:
        :return:
        """
        # hide if window is deactivated
        if event.type() == QtCore.QEvent.WindowDeactivate and not self._browsing and self.autoHide:
            self.hide()

    def onNewCategory(self):
        self.treeView.blockSignals(True)
        selectedItems = self.treeView.selectedItems()  # type: list[CategoryFolder]
        if selectedItems:
            parent = selectedItems[0].parentSource()
        else:
            parent = self._treeModel.root
        text = popups.MessageBox.inputDialog(title="Category Name",
                                             text="", parent=self,
                                             message="Please Enter Name for the new Category.")
        if text is not None:
            data = {"alias": text}
            parentIndex = parent.modelIndex()
            inserted = self._treeModel.insertRow(parent.rowCount(), parent=parentIndex, data=data, itemType="category")
            if not inserted:
                return
            newParent = parent.children[-1]
            newParentIndex = newParent.modelIndex()
            for index, item in enumerate(selectedItems):
                parentSource = item.parentSource()  # type: # CategoryFolder
                self._treeModel.moveRows(parentSource.modelIndex(), item.index(), 1,
                                         newParentIndex, 0)
            self.treeView.expandAll()

        self.treeView.blockSignals(False)
        self.reset()

    def onNewDirectory(self):
        """ New button pressed

        :return:
        """
        self._browsing = True
        self.treeView.blockSignals(True)
        selectedItems = self.treeView.selectedItems()
        if selectedItems:
            selectedCategories = [item for item in selectedItems if type(item) == CategoryFolder]
            if not selectedCategories:
                logger.debug("No valid category selection, searching parents")
                parent = selectedItems[0].parentSource()
                while True:
                    if type(parent) == CategoryFolder or parent.isRoot():
                        break
                    parent = parent.parentSource()
            else:
                parent = selectedCategories[0]

        else:
            parent = self._treeModel.root
        path = popups.FileDialog_directory("Please select a directory",
                                           parent=self,
                                           defaultPath="")
        if path:
            data = {"path": path}
            self._treeModel.insertRow(parent.rowCount(), parent=parent.modelIndex(), data=data, itemType="path")
            self.treeView.expandAll()

        self._browsing = False
        self.treeView.blockSignals(False)

    def deleteButtonClicked(self):
        """ Delete button clicked

        :return:
        """

        items = self.treeView.selectedItems()
        if len(items) == 0:
            return
        self.treeView.blockSignals(True)
        itemLabels = set()
        for item in items:
            itemLabels.add(item.data(0))
            for child in item.iterChildren():
                itemLabels.add(child.data(0))
        result = popups.MessageBox.showWarning(title="Remove Directory",
                                               message="Are you sure you want to remove the following path from Zoo Tools?  "
                                                       "Files will remain on disk, only the zoo alias/s will be removed. \n\n- {}".
                                               format("\n - ".join(sorted(itemLabels))))
        if result == "A":
            for item in items:
                modelIndex = item.modelIndex()
                self._treeModel.removeRow(modelIndex.row(), parent=modelIndex.parent())

            self.browserPreference.saveSettings()
        self.treeView.blockSignals(False)

    def show(self, reattach=True):
        """ Move to widget's position on show

        :return:
        """
        if reattach:
            self._attached = True
        w = self.resizerWidth()
        newPos = self.moveAttached(offset=(-w, 0))
        super(DirectoryPopup, self).show(move=newPos)
        if self._anchorWidget is not None:
            ZooWindow.getZooWindow(self._anchorWidget).titleBar.moving.connect(self._parentMoved)

    def _parentMoved(self, newPos, delta):
        """ Called when parent window is moved

        :param newPos:
        :param delta:
        :return:
        """

        if self._attachToParent and self._attached:
            w = self.resizerWidth() * 0.5
            # add window moved delta for y, x is already done in moveAttached
            self.moveAttached(newPos, offset=(-w, -w + delta.y()))

    def moveAttached(self, windowPos=None, offset=(0, 0)):
        """ Move while attached to window

        :param windowPos: parent window position
        :param offset:
        :return:
        """
        anchorWidget = self._anchorWidget
        if anchorWidget is None:
            return
        if windowPos is None:
            windowPos = anchorWidget.mapToGlobal(QtCore.QPoint(0, 0))

        # todo figure out where the 4 comes from
        xPos = windowPos.x() - self.width() + (self.resizerWidth() * 2) + utils.dpiScale(4) + utils.dpiScale(offset[0])

        pos = QtCore.QPoint(anchorWidget.mapToGlobal(QtCore.QPoint(0, utils.dpiScale(offset[1]))))
        pos.setX(xPos)

        newPos = utils.containWidgetInScreen(self, pos)
        self.move(newPos)
        return newPos

    def moveLeftOfParent(self):
        """ Move popup left of the parent widget

        :return:
        """
        xPos = -self.width() + self._anchorWidget.width() * 0.5
        yPos = 0

        pos = self._anchorWidget.mapToGlobal(QtCore.QPoint(xPos, yPos))
        newPos = utils.containWidgetInScreen(self, pos)

        self.move(newPos)

    def setActiveItems(self, directories, categories):
        """ Set active directories

        """
        def iterProxyParentIndex(modelIndex):
            if not modelIndex.isValid():
                return
            parentIndex = modelIndex.parent()
            yield parentIndex
            for i in iterProxyParentIndex(parentIndex):
                if i is None:
                    return
                yield i
        model = self.treeView.model
        self.treeView.blockSignals(True)
        proxyModel = self.treeView.proxySearch

        selectionModel = self.treeView.selectionModel()
        selectionModel.clear()
        selectedIndexes = []
        for item in categories:
            matchedItems = proxyModel.match(model.index(0, 0),  # root model index
                                            modelconstants.uidRole + 1,
                                            item,
                                            hits=1,
                                            flags=QtCore.Qt.MatchRecursive
                                            )  # type: list[QtCore.QModelIndex]
            selectedIndexes.extend(matchedItems)
        for item in directories:
            matchedItems = proxyModel.match(model.index(0, 0),  # root model index
                                            modelconstants.uidRole + 1,
                                            item.id,
                                            hits=1,
                                            flags=QtCore.Qt.MatchRecursive
                                            )  # type: list[QtCore.QModelIndex]
            selectedIndexes.extend(matchedItems)
        # now do the selection skipping indexes which will have it's parent also be selected
        for selected in selectedIndexes:
            for parent in iterProxyParentIndex(selected):
                if parent in selectedIndexes:
                    break
            else:
                selectionModel.select(selected, QtCore.QItemSelectionModel.Select)
        self.treeView.blockSignals(False)

    def reset(self):
        self._treeModel.reload()
        self.treeView.expandAll()


class FolderTreeModel(treemodel.TreeModel):

    def __init__(self, preference, root, parent=None):
        super(FolderTreeModel, self).__init__(root, parent)
        self.browserPreference = preference
        self.dataChanged.connect(self.onAliasRenamed)
        self.rowsInserted.connect(self.saveToPreferences)
        self.rowsRemoved.connect(self.saveToPreferences)

    def onAliasRenamed(self, topLeft, bottomRight, role):
        """
        :param topLeft:
        :type topLeft:
        :param bottomRight:
        :type bottomRight:
        :param role:
        :type role:
        :return:
        :rtype:
        """
        dataSource = self.itemFromIndex(topLeft)

        if type(dataSource) == CategoryFolder:
            self.browserPreference.updateCategory(dataSource.folderId(), dataSource.internalData)
            return

        self.browserPreference.setDirectoryAlias(dataSource.internalData)

    def reload(self):
        categories, directories = self.browserPreference.categories(), self.browserPreference.browserFolderPaths()
        _root = CategoryFolder({}, model=self)
        tree = {d.id: FolderItem(d, model=self) for d in directories}
        for d in categories:
            tree[d["id"]] = CategoryFolder(d, model=self)
        for cat in categories:
            categoryItem = tree[cat["id"]]
            parent = tree.get(cat["parent"] or "")
            children = cat["children"] or []

            if parent is not None:
                categoryItem.setParentSource(parent)
            for child in children:
                existingChild = tree.get(child)
                if existingChild is None:
                    continue
                existingChild.setParentSource(categoryItem)
        for item in tree.values():
            if item.parentSource() is None:
                item.setParentSource(_root)
        self.setRoot(_root, refresh=False)
        super(FolderTreeModel, self).reload()

    def saveToPreferences(self):
        directories = []
        categories = []

        for item in self.root.iterChildren(recursive=True):
            if type(item) == FolderItem:
                directories.append(item.internalData)
                continue
            children = [i.folderId() for i in item.children]
            parent = item.parentSource()
            data = item.internalData
            parentId = ""
            if not parent.isRoot():
                parentId = parent.folderId()
            categories.append({"id": data["id"],
                               "alias": data["alias"],
                               "parent": parentId,
                               "children": children})
        self.browserPreference.clearBrowserDirectories(False)
        self.browserPreference.clearCategories(False)
        self.browserPreference.addBrowserDirectories(directories, save=False)
        self.browserPreference.addCategories(categories, save=True)


class CategoryFolder(datasources.BaseDataSource):
    """Category folder within the tree
    """

    def __init__(self, dirInfo, model=None, parent=None):
        super(CategoryFolder, self).__init__(headerText=None, model=model, parent=parent)
        self.internalData = dirInfo
        self._icon = None

    def supportsDrag(self, index):
        return True

    def supportsDrop(self, index):
        return True

    def mimeData(self, qIndex):
        data = dict(self.internalData)
        data["children"] = []
        for child in self.children:
            data["children"].append(child.mimeData(0))
        return data

    def dropMimeData(self, items, action):

        return {"items": items}

    def folderId(self):
        return self.internalData.get("id", "")

    def customRoles(self, index):
        return [modelconstants.uidRole + 1]

    def dataByRole(self, index, role):
        if role == modelconstants.uidRole + 1:
            return self.folderId()

    def data(self, index):
        if self.isRoot():
            return "root"
        return self.internalData["alias"]

    def icon(self, index):
        return self._icon

    def columnCount(self):
        return 1

    def setData(self, index, value):
        if not value or value == self.internalData["alias"]:
            return False
        self.internalData["alias"] = value
        return True

    def insertRowDataSources(self, index, count, items):
        for item in items:
            data = {}
            if item.get("path"):
                itemType = "path"
                data["path"] = item["path"]
                data["alias"] = item["alias"]
            else:
                itemType = "category"
                data["alias"] = item["alias"]
            childItem = self.insertRowDataSource(index, data, itemType)
            children = item.get("children", [])
            if children:
                childItem.insertRowDataSources(0, len(children), items=children)

        self.model.browserPreference.saveSettings()

    def insertRowDataSource(self, index, data, itemType):

        if itemType == "category":
            newItem = self.model.browserPreference.createCategory(categoryId=None, name=data["alias"],
                                                                  parent=self.folderId(),
                                                                  children=data.get("children", []))  # creates doesn't add
            newItem = CategoryFolder(newItem, model=self.model, parent=self)
            self.insertChild(index, newItem)
        else:
            directoryPath = tooldata.DirectoryPath(data["path"], alias=data.get("alias"))
            newItem = FolderItem(directoryPath, model=self.model, parent=self)
            self.insertChild(index, newItem)

        return newItem


class FolderItem(CategoryFolder):
    """A filesystem folder within the tree.
    """

    def __init__(self, dirInfo, model=None, parent=None):
        super(FolderItem, self).__init__(dirInfo, model=model, parent=parent)
        self.internalData = dirInfo
        self._icon = iconlib.icon("closeFolder")

    def toolTip(self, index):
        return self.internalData.path

    def folderId(self):
        return self.internalData.id

    def data(self, index):
        return self.internalData.alias

    def setData(self, index, value):
        if not value or value == self.internalData.alias:
            return False
        self.internalData.alias = value
        return True

    def supportsDrop(self, index):
        return False
