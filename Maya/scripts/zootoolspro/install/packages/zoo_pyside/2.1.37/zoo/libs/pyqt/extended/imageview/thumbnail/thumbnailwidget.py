import math

from zoo.libs.pyqt.models import modelutils
from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoovendor import six
from zoo.libs.pyqt.extended.imageview import model
from zoo.libs.pyqt.widgets import listview
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class ThumbnailWidget(listview.ListView):
    # QModelIndex, Treeitem
    requestDoubleClick = QtCore.Signal(object, object)
    requestSelectionChanged = QtCore.Signal(object, object)

    _defaultIconSize = QtCore.QSize(256, 256)
    defaultMinIconSize = 20
    defaultMaxIconSize = 512
    _maxThreadCount = 200
    # toolset relies on this for serializing the current state of the thumbnail widget
    # i.e. zoom amount
    stateChanged = QtCore.Signal()

    def __init__(self, parent=None, delegate=None, iconSize=_defaultIconSize, uniformIcons=False):
        """ Thumbnail widget

        :param parent:
        :param delegate:
        :param iconSize:
        :param uniformIcons:
        """
        super(ThumbnailWidget, self).__init__(parent=parent)
        iconSize = iconSize or self._defaultIconSize

        self._currentIconSize = QtCore.QSize(iconSize)
        self._defaultColumnCount = 4
        self._columnCount = self._defaultColumnCount

        self.zoomable = True
        self.pagination = True
        self._uniformIcons = uniformIcons
        self._persistentFilter = []  # type: list[str, list[str]]

        self.threadPool = QtCore.QThreadPool.globalInstance()
        self.threadPool.setMaxThreadCount(ThumbnailWidget._maxThreadCount)

        self.proxyFilterModel = model.MultipleFilterProxyModel(parent=self)
        self.proxyFilterModel.setDynamicSortFilter(True)
        self.proxyFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.setLayoutMode(self.LayoutMode.Batched)
        self._delegate = delegate(self) if delegate is not None else model.ThumbnailDelegate(self)
        self.setItemDelegate(self._delegate)
        self.initUi()
        self.connections()
        self.setIconSize(self._defaultIconSize)

    def initUi(self):
        """ Initialize the ui
        
        :return: 
        """
        self.setMouseTracking(True)
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setSelectionMode(QtWidgets.QListView.SingleSelection)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setUniformItemSizes(self._uniformIcons)

        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setUpdatesEnabled(True)
        self.verticalScrollBar().setSingleStep(5)  # scroll sensitivity

    def connections(self):
        verticalScrollBar = self.verticalScrollBar()
        verticalScrollBar.valueChanged.connect(self.paginationLoadNextItems)
        verticalScrollBar.rangeChanged.connect(self.paginationLoadNextItems)
        verticalScrollBar.sliderReleased.connect(self.stateChanged.emit)
        self.clicked.connect(lambda: self.stateChanged.emit())
        self.activated.connect(lambda: self.stateChanged.emit())
        self.entered.connect(lambda: self.stateChanged.emit())

    # --------------------------
    # EVENTS
    # --------------------------

    def mouseDoubleClickEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        index, dataModel = modelutils.dataModelIndexFromIndex(self.currentIndex())

        if model is not None:
            item = dataModel.itemFromIndex(index)
            dataModel.doubleClickEvent(index, item)
            self.requestDoubleClick.emit(index, item)
            event.accept()

    def wheelEvent(self, event):
        """ Overridden to deal with scaling the listview.

        :type event: :class:`QtGui.QWheelEvent`
        """
        modifiers = event.modifiers()
        if not self.zoomable or modifiers != QtCore.Qt.ControlModifier:
            super(ThumbnailWidget, self).wheelEvent(event)
            return
        indices = self.selectedIndexes()
        index = None
        if indices:
            index = indices[0]
            viewportRect = self.viewport().rect()
            if not viewportRect.intersects(self.visualRect(index)):
                index = None

        if index is None:
            eventPos = QtGui.QCursor.pos()
            index = self.indexAt(eventPos)

            # if it's an invalid index, find closest instead
            if not index.isValid():
                index_ = self.closestIndex(eventPos)
                if index_ is not None:
                    index = index_
        delta = event.angleDelta().y() / 8
        self._setZoomAmount(delta)
        self.scrollTo(index)
        event.accept()
        self.stateChanged.emit()

    def resizeEvent(self, event):
        """

        :param event:
        :type event: `QtGui.QResizeEvent`
        """

        super(ThumbnailWidget, self).resizeEvent(event)
        iconSize = self.iconSize()
        self._columnCount = math.floor(self.size().width() / iconSize.width())

    def keyPressEvent(self, event):
        """
        :type event: :class:`QtGui.QKeyEvent`
        """
        if event.key() == QtCore.Qt.Key_F and not event.modifiers():
            if self.underMouse():
                selection = self.selectedIndexes()
                if selection:
                    self.scrollTo(selection[0])
                    event.accept()
                    return
        else:
            super(ThumbnailWidget, self).keyPressEvent(event)

    def verticalSliderReleased(self):
        self.stateChanged.emit()

    def state(self):
        """ Returns useful settings to copy from one list view behaviour to another

        :return:
        :rtype: dict
        """
        selectedIndex = self.currentIndexInt()
        ret = {"sliderPos": self.verticalScrollBar().value(),
               "sliderMin": self.verticalScrollBar().minimum(),
               "sliderMax": self.verticalScrollBar().maximum(),
               "selected": selectedIndex,
               "columns": self._defaultColumnCount,
               "iconSize": self._currentIconSize,
               "initialIconSize": self._defaultIconSize,
               "fixedSize": self.parentWidget().minimumSize()
               }

        return ret

    def setState(self, state, scrollTo=False):
        """ Set the state of the listview with the new settings provided from ThumbListView.state()

        :param state:
        :type state: dict
        :return:
        :rtype:
        """
        self._defaultColumnCount = state['columns']
        self._currentIconSize = state['iconSize']
        self._defaultIconSize = state['initialIconSize']

        fixedSize = state['fixedSize']

        if fixedSize.width() != 0:
            self.parentWidget().setFixedWidth(fixedSize.width())
        if fixedSize.height() != 0:
            self.parentWidget().setFixedHeight(fixedSize.height())
        verticalScrollBar = self.verticalScrollBar()
        verticalScrollBar.setMinimum(state['sliderMin'])
        verticalScrollBar.setMaximum(state['sliderMax'])
        verticalScrollBar.setValue(state['sliderPos'])

        if not self.isVisible():  # avoid crashes in 2022
            return

        if state['selected'] != -1:
            QtCore.QTimer.singleShot(0, lambda: self.setCurrentIndexInt(state['selected'], scrollTo))

    def currentIndexInt(self):
        """ Get the current index of the selected item

        :return:
        :rtype:
        """
        return self.currentIndex().row()

    def setCurrentIndexInt(self, sel, scrollTo=False):
        """ Select index

        :param sel:
        :type sel: int
        :return:
        :rtype:
        """
        dataModel = self.rootModel()
        if not dataModel:
            return

        autoScroll = self.hasAutoScroll()
        self.setAutoScroll(scrollTo)
        self.selectionModel().setCurrentIndex(dataModel.index(sel, 0),
                                              QtCore.QItemSelectionModel.ClearAndSelect)
        self.setAutoScroll(autoScroll)

    def setPersistentFilter(self, text, tags):
        self._persistentFilter = [text, tags]
        self.filter(text, tags)

    def filter(self, text, tag=None):
        """ Filter by list by tag type

        :param text:
        :param tag:
        """
        tag = tag or "filename"  # Filter list by file name by default
        if isinstance(tag, six.string_types):
            tag = [tag]
        fixedFilterText, fixedFilterTags = self._persistentFilter or ["", []]
        tags = set(tag)
        if fixedFilterText:
            tags.update(fixedFilterTags)
            text = "".join(["(?=.*{})".format(text)] + ["(?=.*{})".format(fixedFilterText)])
        role = QtCore.Qt.DisplayRole
        for t in tag:
            tagRole = model.tagToRole.get(t)
            if tagRole is not None:
                role = role | tagRole
        self.proxyFilterModel.setFilterRole(role)
        self.proxyFilterModel.setFilterRegularExpression(QtCore.QRegularExpression(text,
                                                                                   QtCore.QRegularExpression.CaseInsensitiveOption))

    def visibleItems(self, pre=0, post=0):
        """ Gets visible items

        Set extra to 1 or more if you want extra indices at the beginning and at the end. It will only return
        valid indices.

        :param pre: Add extra items behind the currently visible items
        :type pre: int
        :param post: Add extra items after the currently visible items
        :type post: int
        :return: List of indices that are visible plus the pre and post. It only returns valid indices
        :rtype: list of QtCore.QModelIndex
        """
        for visibleIndex in self.visibleIndices(pre, post):
            index, dataModel = modelutils.dataModelIndexFromIndex(visibleIndex)
            yield dataModel.itemFromIndex(index)

    def setItemByText(self, text):
        """ Set the item by the text of the item

        :param text:
        :type text:
        :return:
        :rtype:
        """
        currentModel = self.model()
        for row in range(currentModel.rowCount()):
            modelIndex = currentModel.index(row, 0)
            if currentModel.data(modelIndex, QtCore.Qt.DisplayRole) == text:
                self.setCurrentIndex(modelIndex)
                return

    def setUniformItemSizes(self, enable):
        """ Show the items as uniform sizes (squares) or whatever aspect ratio it originally was.

        :param enable:
        :return:
        """
        self._uniformIcons = enable
        dataModel = self.rootModel()
        if dataModel:
            dataModel.setUniformItemSizes(enable)

    def setIconSize(self, size):
        self._currentIconSize = size
        super(ThumbnailWidget, self).setIconSize(size)

    def _setZoomAmount(self, value):
        """ Sets the zoom amount to this view by taking the view iconSize()*value

        :param value:
        :type value:
        :return:
        :rtype:
        """
        columnCount = self._columnCount
        if value > 0:
            _columnCount = columnCount - 1
        else:
            _columnCount = columnCount + 1
        if _columnCount <= 0:
            return
        self._updateImageSizeForColumnCount(_columnCount)

    def setColumns(self, col, refresh=False):
        """ Set number of columns based on current size of the widget

        :param col:
        :type col:
        :return:
        :rtype:
        """
        self._columnCount = col
        if not refresh:
            return
        self._updateImageSizeForColumnCount(col)

    def _updateImageSizeForColumnCount(self, columnCount):
        # the size of the view with or without the vertical scrollBar
        viewSize = self.size()
        viewWidth = viewSize.width() - self.verticalScrollBar().size().width() - 2
        imageWidth = viewWidth / float(columnCount)  # type: QtCore.QSize
        if imageWidth >= self.defaultMaxIconSize or imageWidth <= self.defaultMinIconSize:
            return
        self._columnCount = columnCount
        self.setIconSize(QtCore.QSize(imageWidth, imageWidth))
        self.paginationLoadNextItems()

    def refresh(self):
        """ Refresh so the icons show properly

        :return:
        :rtype:
        """
        logger.debug("Executing refresh logic")
        proxyModel = self.model()
        if proxyModel:
            proxyModel.layoutChanged.emit()
        self._updateImageSizeForColumnCount(self._columnCount)
        if not self.updatesEnabled():
            self.setUpdatesEnabled(True)

    def rootModel(self):
        return modelutils.dataModelFromProxyModel(self.model())

    def setModel(self, dataModel):
        """ Set the Model

        :param dataModel:
        :type dataModel:
        :return:
        :rtype:
        """
        self.proxyFilterModel.setSourceModel(dataModel)

        dataModel.setUniformItemSizes(self._uniformIcons)
        ret = super(ThumbnailWidget, self).setModel(self.proxyFilterModel)
        self.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        return ret

    def invisibleRootItem(self):
        currentModel = self.rootModel()
        if currentModel is not None:
            return currentModel.invisibleRootItem()

    def onSelectionChanged(self):
        index = self.currentIndex()
        dataModelIndex, dataModel = modelutils.dataModelIndexFromIndex(index)
        if dataModelIndex.isValid():
            item = dataModel.itemFromIndex(dataModelIndex)
            dataModel.onSelectionChanged(dataModelIndex, item)
            self.requestSelectionChanged.emit(dataModelIndex, item)

    def paginationLoadNextItems(self):
        """ Simple method to call the models loadData method when the vertical slider hits the max value, useful to load
        the next page of data on the model.

        :return:
        :rtype:
        """
        if not self.pagination:
            return

        currentModel = self.rootModel()
        if currentModel is None:
            return

        itemsToLoad = []
        vis = list(self.visibleItems(currentModel.chunkCount, currentModel.chunkCount))
        for visibleItem in vis:
            internalItem = visibleItem.item()
            if internalItem.iconLoaded() and not visibleItem.pixmap().isNull():
                continue
            thread = internalItem.iconThread
            if thread is None:
                itemsToLoad.append(visibleItem)
            elif not thread.isRunning():
                itemsToLoad.append(visibleItem)

        if itemsToLoad:
            currentModel.loadItems(itemsToLoad)
