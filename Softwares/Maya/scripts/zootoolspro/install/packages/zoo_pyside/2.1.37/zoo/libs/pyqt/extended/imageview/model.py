import os
from functools import partial

from zoo.libs.pyqt.models import modelutils
from zoo.libs.pyqt.uiconstants import QT_SUPPORTED_EXTENSIONS
from zoo.core.tooldata.tooldata import DirectoryPath
from zoo.libs.utils.general import uniqify
from zoo.libs.utils import path
from zoo.libs.zooscene import zooscenefiles
from zoo.preferences.interfaces import coreinterfaces
from zoo.core.util import zlogging, env

from zoovendor import six
from zoovendor.Qt import QtGui, QtCore, QtWidgets, QtCompat

from zoo.libs.pyqt.extended.imageview import items
from zoo.libs.pyqt.extended.imageview.items import TreeItem

logger = zlogging.getLogger(__name__)

IMAGE_EXTENSIONS = QT_SUPPORTED_EXTENSIONS
tagRole = QtCore.Qt.UserRole + 1
descriptionRole = QtCore.Qt.UserRole + 2
filenameRole = QtCore.Qt.UserRole + 3
websitesRole = QtCore.Qt.UserRole + 4
creatorRole = QtCore.Qt.UserRole + 5
rendererRole = QtCore.Qt.UserRole + 6
tagToRole = {
    "filename": filenameRole,
    "tags": tagRole,
    'description': descriptionRole,
    'creators': creatorRole,
    'websites': websitesRole,
    'renderer': rendererRole
}


class MultipleFilterProxyModel(QtCore.QSortFilterProxyModel):
    def filterAcceptsRow(self, sourceRow, sourceParent):
        filterRegExp = self.filterRegularExpression()
        # if there is no search criteria, exit early!
        if not filterRegExp.isValid():
            return True
        requestedRole = self.filterRole()
        consolidatedData = ""
        sourceModel = self.sourceModel()
        rowIndex = sourceModel.index(sourceRow, 0)
        if requestedRole == filenameRole:
            data = sourceModel.data(rowIndex, tagRole)
            consolidatedData += str(data)
        for role in (QtCore.Qt.DisplayRole, tagRole,
                     descriptionRole,
                     filenameRole,
                     websitesRole,
                     creatorRole):

            if requestedRole == role:
                data = sourceModel.data(rowIndex, role)
                consolidatedData += str(data)
        return filterRegExp.match(consolidatedData).capturedStart() != -1


class ThumbnailDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super(ThumbnailDelegate, self).__init__(parent)

    def sizeHint(self, option, index):
        sourceIndex, dataModel = modelutils.dataModelIndexFromIndex(index)
        item = dataModel.itemFromIndex(sourceIndex)
        if not item:
            return
        return item.sizeHint()

    def paint(self, painter, options, index):
        sourceIndex, dataModel = modelutils.dataModelIndexFromIndex(index)
        item = dataModel.itemFromIndex(sourceIndex)
        if not item:
            return
        item.paint(painter, options, index)


class ItemModel(QtGui.QStandardItemModel):
    """Main Data Model for the thumbnail widget, this is the main class to handle data access between the core and the view
    """
    # total number of items to load a time
    chunkCount = 20

    def __init__(self, parent=None):
        super(ItemModel, self).__init__(parent)
        self.lastFilterTag = None
        self.loadedCount = 0

    def reset(self):
        self.beginResetModel()
        self.endResetModel()

    def loadData(self, chunkCount=0):
        """Intended to be overridden by subclasses, This method should deal with loading a chunk of the items to display.
        Use self.loadedCount and self.chunkCount variable to determine the amount to load

        :Example:

            if len(self.currentFilesList) < self.loadedCount:
                filesToLoad = self.mylist
            else:
                filesToLoad = self.mylist[self.loadedCount: self.loadedCount + self.chunkCount]

        :rtype: None
        """
        raise NotImplementedError()

    def data(self, index, role):
        """
        :type index: :class:`QtCore.QModelIndex`
        :type role: int
        :return:
        :rtype:
        """
        if not index.isValid():
            return

        item = self.itemFromIndex(index)
        baseItem = item.item()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return item.itemText()
        elif role == filenameRole:
            return baseItem.fileName
        elif role == descriptionRole:
            return baseItem.description()
        elif role == tagRole:
            return baseItem.tags()
        elif role == websitesRole:
            return baseItem.websites()
        elif role == creatorRole:
            return baseItem.creators()
        elif role == QtCore.Qt.ToolTipRole:
            return item.toolTip()
        elif role == QtCore.Qt.DecorationRole:
            return item.icon()

        return super(ItemModel, self).data(index, role)

    def doubleClickEvent(self, modelIndex, item):
        pass


class FileModel(ItemModel):
    refreshRequested = QtCore.Signal()
    doubleClicked = QtCore.Signal(str)
    parentClosed = QtCore.Signal(bool)
    itemSelectionChanged = QtCore.Signal(str, object)

    def __init__(self, view, extensions, directories=None, activeDirs=None, chunkCount=0, uniformIcons=False,
                 includeSubdir=False):
        """ The model to get each file in the `directories` and add them as an item.

        :param view: The viewer to assign this model data?
        :type view: thumbwidget.ThumbListView
        :param directories: The directory full path where the .zooScenes live
        :type directories: list[str] or list[DirectoryPath]
        :param chunkCount: The number of images to load at a time into the ThumbnailView widget
        :type chunkCount: int
        :param extensions: The file extensions to find for each item eg. ["ma", "zooScene", "shape", etc]
        :type extensions: list[basestring]
        :param uniformIcons: False keeps the images non-square.  True the icons will be square, clipped on longest axis
        :type uniformIcons: bool
        """
        super(FileModel, self).__init__(parent=view)
        self.chunkCount = chunkCount or ItemModel.chunkCount
        if not env.isWindows():
            self.extensions = list(set([i.upper() for i in extensions] + [i.lower() for i in extensions])) + extensions
        else:
            self.extensions = extensions
        self.view = view
        self.threadPool = QtCore.QThreadPool.globalInstance()
        self.uniformIcons = uniformIcons
        self.directories = None  # type: list[DirectoryPath]
        self._activeDirectories = None  # type: list[DirectoryPath]
        self._includeSubdir = includeSubdir
        # the current image name selected (no image highlighted on creation)
        self.currentImage = None  # type:
        self.currentItem = None  # type: items.BaseItem
        self.themePref = coreinterfaces.coreInterface()

        self.fileItems = []  # type: list[items.BaseItem]
        # load the images
        if directories is not None:
            self.setDirectories(directories, False)

        self.setActiveDirectories(activeDirs, False)

    def setDirectories(self, directories, refresh=True):
        """Used to set or change the directory"""
        if isinstance(directories, list) and len(directories) > 0:
            if isinstance(directories[0], DirectoryPath):  # Use DirectoryPath() class directly
                self.directories = directories

            elif isinstance(directories[0], six.string_types):  # if it is a path then create a new DirectoryPath class
                self.directories = [DirectoryPath(path=d) for d in directories]
        else:
            self.directories = directories

        if refresh:
            self.refreshList()

    def setActiveDirectories(self, directories, refresh=True):
        if isinstance(directories, list) and len(directories) > 0:
            if isinstance(directories[0], DirectoryPath):  # Use DirectoryPath() class directly
                self._activeDirectories = directories
            elif isinstance(directories[0], six.string_types):  # if it is a path then create a new DirectoryPath class
                self._activeDirectories = [DirectoryPath(path=d) for d in directories]
        else:
            self._activeDirectories = directories

        if refresh:
            self.refreshList()

    @property
    def activeDirectories(self):
        """

        :return:
        :rtype: list[DirectoryPath]
        """
        # Get all directories if active directories is None.
        # This doesn't include [] on purpose as if an empty list was sent through we want nothing selected
        if self._activeDirectories is None and self._activeDirectories is not []:
            self._activeDirectories = self.directories

        return self._activeDirectories or []

    def setDirectory(self, directory, refresh=True):
        """ Set a single directory. Clears all directories

        :param directory:
        :param refresh:
        :return:
        """
        newDir = self._toDirectoryPath(directory)
        self.setDirectories([newDir], refresh=refresh)

    def _toDirectoryPath(self, directory):
        """ Converts directory to DirectoryPath

        :param directory:
        :return:
        """
        newDir = None
        if isinstance(directory, DirectoryPath):  # Use DirectoryPath() class directly
            newDir = directory
        elif isinstance(directory, six.string_types):  # if it is a path then create a new DirectoryPath class
            newDir = DirectoryPath(path=directory)

        return newDir

    def refreshList(self):
        """ Refreshes the icon list if contents have been modified, does not change the root directory
        """
        self.clear()
        self.refreshModelData()

    def refreshModelData(self):
        """Refreshes the model's data
        """
        self.refreshRequested.emit()

    def clear(self):
        """Clears the images and data from the model, usually used while refreshing
        """
        # remove any threads that haven't started yet
        self.threadPool.clear()

        while not self.threadPool.waitForDone():
            continue
        # clear any items, this is necessary to get python to GC alloc memory
        self.loadedCount = 0
        super(FileModel, self).clear()

    def itemTexts(self):
        """ Get all the item texts and put them into a generator

        :return:
        :rtype:
        """

        return (self.itemFromIndex(self.index(row, 0)).itemText() for row in range(self.rowCount()))

    def indexFromText(self, text):
        """ Get Item from text

        :param text:
        :type text:
        :return:
        :rtype:
        """
        matchedItems = self.findItems(text)
        if matchedItems:
            return matchedItems[0]

    def doubleClickEvent(self, modelIndex, item):
        """Gets called by the listview when an item is doubleclicked

        :param modelIndex:
        :type modelIndex: QtCore.QModelIndex
        :param item:
        :type item: :class:`TreeItem`
        :return:  The current image with it's name and file extension
        :rtype:  str
        """
        self.currentImage = item._item.name
        self.doubleClicked.emit(self.currentImage)
        return self.currentImage

    def createItem(self, item):
        """ Custom wrapper Method to create a ::class`items.TreeItem`, add it to the model items and class appendRow()

        :param item:
        :type item: :class:`zoo.libs.pyqt.extended.imageview.items.BaseItem`
        :return:
        :rtype: :class:`TreeItem`
        """
        tItem = TreeItem(item=item, themePref=self.themePref, squareIcon=self.uniformIcons)
        self.appendRow(tItem)
        return tItem

    def lazyLoadFilter(self, chunkCount=0):
        """Breaks up the lists self.currentFilesList, self.fileNameList, self.toolTipList for lazy loading.

        Can be overridden, usually to choose if the display names should have extensions or not
        Default is no extensions on display names

        :rtype: list[:class:`items.TreeItem`]
        """
        chunkCount = self.chunkCount if chunkCount == 0 else chunkCount
        if len(self.fileItems) < self.loadedCount:
            filesToLoad = [self.itemFromIndex(self.index(row, 0)) for row in range(self.rowCount())]
        else:
            filesToLoad = []
            for i in range(self.loadedCount, self.loadedCount + chunkCount):
                index = self.index(i, 0)
                if not index.isValid():
                    continue
                item = self.itemFromIndex(index)
                if item is not None:
                    filesToLoad.append(item)

        return filesToLoad

    def onSelectionChanged(self, modelIndex, item):
        """Gets called by the listview when an item is changed, eg left click or rightclick
        :param modelIndex:
        :type modelIndex: QtCore.QModelIndex
        :param item:
        :type item: TreeItem
        """
        try:  # can error while renaming files and the change no longer exists so ignore if so
            self.currentImage = item.item().name
            self.currentItem = item.item()
            self.itemSelectionChanged.emit(self.currentImage, item.item())
            return self.currentImage
        except AttributeError:
            pass

    def closeEvent(self, event):
        """Closes the model

        :param event:
        :type event:
        """
        # todo maybe this should be in the minibrowser instead?
        self.clear()
        self.parentClosed.emit(True)
        super(FileModel, self).closeEvent(event)


class MiniBrowserFileModel(FileModel):

    def __init__(self, view, extensions, directories=None, activeDirs=None, chunkCount=0, uniformIcons=False,
                 includeSubdir=False, assetPref=None):
        """

        :param view:
        :param extensions:
        :param directories:
        :param activeDirs:
        :param chunkCount:
        :param uniformIcons:
        :param includeSubdir:
        :param assetPref:
        :type assetPref: zoo.preferences.assets.BrowserPreference
        """
        self._assetPref = assetPref
        super(MiniBrowserFileModel, self).__init__(view=view, extensions=extensions, directories=directories,
                                                   activeDirs=activeDirs, chunkCount=chunkCount,
                                                   uniformIcons=uniformIcons,
                                                   includeSubdir=includeSubdir)

    def preference(self):
        return self._assetPref

    def setUniformItemSizes(self, enabled):
        """ Set uniform item sizes

        Make the items square if true, if false it will keep the images original aspect ratio for the items

        :param enabled:
        :type enabled:
        :return:
        :rtype:
        """
        self.uniformIcons = enabled
        for row in range(self.rowCount()):
            item = self.itemFromIndex(self.index(row, 0))
            item.squareIcon = enabled

    def updateFromPrefs(self, updateItems=True):
        """ Gets the updated preference information and updates the model's items

        :param updateItems:
        :return:
        """
        if not self._assetPref:
            logger.debug("assetPref not found")
            return

        self.directories = self._assetPref.browserFolderPaths()
        oldActives = self._activeDirectories
        self._activeDirectories = self._assetPref.activeBrowserPaths()

        # Check if the active items are the same
        if updateItems and \
                not set([path.normpath(a.path) for a in oldActives]) == set(
                    [path.normpath(a.path) for a in self._activeDirectories]):
            self.updateItems()
            logger.debug("Update MiniBrowserFileModel Items: {}".format(self._activeDirectories))

    def refreshAssetFolders(self):
        """ Refresh asset folders

        :return:
        """
        if self._assetPref:
            self._assetPref.refreshAssetFolders(setActive=True)

    def setItemIconFromImage(self, item, image):
        """Custom method that gets called by the thread

        :param item:
        :type item: :class:`TreeItem`
        :param image: The Loaded QImage
        :type image: QtGui.QImage
        """
        item.applyFromImage(image)
        index = item.index()
        QtCompat.dataChanged(self, index, index, [QtCore.Qt.DecorationRole])

    def loadData(self, chunkCount=0):
        """ Overridden method that prepares the images for loading and viewing.

        Is filtered first via self.lazyLoadFilter()

        From base class documentation:

            Lazy loading happens either on first class initialization and any time the vertical bar hits the max
            value, we then grab the current the new file chunk by files[self.loadedCount: loadedCount +
            self.chunkCount] that way we are only loading a small amount at a time. Since this is an example of how
            to use the method , you can approach it in any way you wish but for each item you add you must initialize
            a item.BaseItem() or custom subclass and a item.treeItem or subclass which handles the qt side of the
            data per item

        """
        filesToLoad = self.lazyLoadFilter(chunkCount)
        self.loadItems(filesToLoad)

    def loadItemThreaded(self, qItem, start=False):
        item = qItem.item()
        thumbnail = item.thumbnail
        if not os.path.exists(thumbnail):
            return
        workerThread = items.ThreadedIcon(iconPath=thumbnail)
        workerThread.signals.updated.connect(partial(self.setItemIconFromImage, qItem))
        self.parentClosed.connect(workerThread.finished)

        item.iconThread = workerThread
        if start:
            self.threadPool.start(item.iconThread)
            self.loadedCount += 1
        return item.iconThread

    def loadItems(self, itemsToLoad):
        # Load the files
        # stash the new workers we need to populate the thread pool
        threads = []
        for qItem in itemsToLoad:
            thread = self.loadItemThreaded(qItem)
            if thread is not None:
                threads.append(thread)
            self.loadedCount += 1
        # now run all workers we requested.
        # we do this here instead of the above loop due to crashes in maya 2018 which
        # is likely due to race conditions while workers are being added and removed
        # from the pool per loop.
        for thread in threads:
            self.threadPool.start(thread)

    def updateItems(self):
        """ Populate and adds to list of self.fileItems.

        self.fileItems is updated here, change this list if you'd like to change how it is added to the ui. EG sorting

        File items have all the information on the items before building into the ui
        """
        if not isinstance(self.extensions, list):
            raise ValueError("Extensions must be list of strings eg ['jpg', 'ma'] , \"{}\" type given \"{}\" ".format(
                type(self.extensions),
                self.extensions))

        # Retrieve all the directories
        dirs = [d.path for d in list(self.activeDirectories)]
        if self._includeSubdir:
            for d in list(dirs):
                if os.path.exists(d):
                    dirs += path.directories(d, absolute=True)

        dirs = uniqify(dirs)
        self.fileItems = []
        for d in dirs:
            for file in path.filesByExtension(d, self.extensions, sort=True):
                self.createItemFromFileAndDirectory(d, file)

    def createItemFromFileAndDirectory(self, directory, filePath, loadImage=False):
        """Creates a QItem and base data Item from the directory and filePath .
        If loadImage is true then the image will be loaded on a separate thread and displayed
        when ready.

        :param directory: The directory of the filePath.
        :type directory: str
        :param filePath: The absolute filePath under the directory.
        :type filePath: str
        :param loadImage: Whether to immediately load the image and display it.
        :type loadImage: bool
        :rtype: tuple[:class:`QtGui.QStandardItem`, :class:`BaseItem`]
        """
        item = self.generateItem(directory, filePath)
        item.metadata = zooscenefiles.infoDictionary(item.fileNameExt(), item.directory)
        self.fileItems.append(item)
        qItem = self.createItem(item)
        if loadImage:
            self.loadItemThreaded(qItem, start=True)

        return qItem, item

    def generateItem(self, directory, file):
        """ Creates a base item that will be added to the fileItems list. Which in turn will be added into the UI.

        Override this if you want to customize the BaseItem. Do this to customize things such as the  thumbnail

        If none is returned, the item with the file won't be added.
        Useful to filter certain files based on the file name. eg. exclude based on prefixes

        :rtype: :class:`items.BaseItem`
        """
        item = items.BaseItem(filePath=os.path.join(directory, file), description=None)
        item.toolTip = item.name
        return item

    def refreshModelData(self):
        """Refreshes the model's data
        """
        self.updateFromPrefs(False)
        self.updateItems()
        super(MiniBrowserFileModel, self).refreshModelData()
