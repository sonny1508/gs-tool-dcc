from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.extended import listviewplus, searchablemenu
from zoo.libs.pyqt.models import listmodel, datasources, modelutils, constants
from zoo.apps.toolpalette import layouts, run, qtmenu, utils
from zoovendor.Qt import QtCore, QtWidgets, QtGui


class ShelfWindow(elements.ZooWindowThin):
    windowSettingsPath = "zoo/qtshelf"

    def __init__(self, name="zooShelf", title="Zoo Shelf", parent=None, resizable=True, width=None, height=None,
                 saveWindowPref=True):
        super(ShelfWindow, self).__init__(name, title,
                                          parent=parent, resizable=resizable, width=width, height=height,
                                          saveWindowPref=saveWindowPref)

        layout = elements.vBoxLayout(spacing=0)
        self.setMainLayout(layout)
        self.toolPalette = run.currentInstance()
        self.shelfView = ShelfWidget(self.toolPalette, parent=self)

        layout.addWidget(self.shelfView)

        shelfItem = self.toolPalette.shelfManager.shelfById("ZooToolsPro")

        self.shelfView.refresh(shelfItem)


class ShelfWidget(listviewplus.ListViewPlus):
    """Reusable shelf widget which displays a single zoo tools shelf
    """

    def __init__(self, toolPalette, iconSize=32, parent=None):
        super(ShelfWidget, self).__init__("", searchable=False, parent=parent)
        self.toolPalette = toolPalette

        self.setToolBarVisible(False)
        self.setListViewSpacing(2)
        self.setMainSpacing(0)
        self.listview.setMouseTracking(True)
        self.listview.setViewMode(QtWidgets.QListView.IconMode)
        self.listview.setResizeMode(QtWidgets.QListView.Adjust)
        self.listview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listview.setUniformItemSizes(True)

        self.listview.setDragEnabled(False)
        self.listview.setAcceptDrops(False)
        self.listview.setUpdatesEnabled(True)
        self.listview.verticalScrollBar().setSingleStep(5)  # scroll sensitivity
        self.listview.setIconSize(QtCore.QSize(iconSize, iconSize))
        self.shelfModel = listmodel.ListModel(parent=self)
        self.setModel(self.shelfModel)
        self._uiConnections()

    def refresh(self, shelfItem):
        self.rowDataSource = ShelfItemDataSource(shelfItem.children, self.listview.iconSize().width(),
                                                 model=self)
        self.registerRowDataSource(self.rowDataSource)
        delegate = self.shelfModel.rowDataSource.delegate(self)
        self.listview.setItemDelegate(delegate)

        self.shelfModel.reload()
        self.refreshRequested.emit()

    def _uiConnections(self):
        self.listview.pressed.connect(self.iconPressed)

    def iconPressed(self, index):

        # index is from the proxy model ie. handles search, so we remap to our model before
        # getting values.
        sourceIndex, sourceModel = modelutils.dataModelIndexFromIndex(index)
        shelfItem = sourceModel.data(sourceIndex, role=constants.userObject)  # type: layouts.ShelfButton
        if shelfItem is None or shelfItem.isSeparator():
            return
        if not len(shelfItem):
            self.toolPalette.executePluginById(shelfItem.id, **shelfItem.arguments)
            return
        iconSize = self.listview.iconSize()
        rootMenu = searchablemenu.SearchableMenu(searchVisible=False, parent=self)

        qtmenu.generateMenuTree(shelfItem, rootMenu,
                                self.toolPalette.executePluginById,
                                self.toolPalette.typeRegistry,
                                iconSize=iconSize.width()
                                )
        rootMenu.exec_(QtGui.QCursor.pos())


class ShelfItemDataSource(datasources.IconRowDataSource):
    """DataSource which describes the data to show in the shelf.
    Only one of these exist for a listview
    """
    def __init__(self, shelfItems, iconSize,headerText=None, model=None, parent=None):
        super(ShelfItemDataSource, self).__init__(headerText, model, parent)
        self.zooShelfItems = shelfItems  # type: list[layouts.Item]
        self.iconCache = {}  # type: dict[int, QtGui.QIcon]
        self._iconSize = QtCore.QSize(iconSize, iconSize)

    def setIconSize(self, size):
        self._iconSize = size

    def userObjects(self):
        return self.zooShelfItems

    def setUserObjects(self, objects):
        self.zooShelfItems = objects

    def rowCount(self):
        return len(self.zooShelfItems)

    def isEditable(self, index):
        return False

    def isSelectable(self, index):
        return False

    def toolTip(self, index):
        return self.zooShelfItems[index].tooltip

    def icon(self, index):
        try:
            iconCacheInstance = self.iconCache[index]
        except KeyError:
            item = self.zooShelfItems[index]
            iconCacheInstance =  utils.iconForItem(item, iconSize=self._iconSize.width(),
                                                   ignoreSeparators=False)
            if item is not None:
                self.iconCache[index] = iconCacheInstance

        return iconCacheInstance

    def iconSize(self, index):
        return self._iconSize

