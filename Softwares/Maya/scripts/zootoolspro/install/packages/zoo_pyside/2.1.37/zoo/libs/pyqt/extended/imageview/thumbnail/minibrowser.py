import os

from collections import OrderedDict
from functools import partial

from zoo.core.util import env

from zoo.preferences.interfaces import coreinterfaces
from zoo.libs.pyqt.models import modelutils
from zoo.libs.pyqt.widgets.frameless.window import ZooWindow
from zoo.libs.pyqt.widgets.popups import MessageBox
from zoovendor.Qt import QtCore, QtWidgets, QtGui

from zoo.libs.pyqt import utils, uiconstants as uic
from zoo.libs.pyqt.extended.imageview.thumbnail import directorypopup
from zoo.libs.pyqt.extended.imageview.thumbnail.thumbnailwidget import ThumbnailWidget
from zoo.libs.pyqt.extended.imageview.thumbnail.virtualslider import VirtualSlider
from zoo.libs.pyqt.extended.imageview.thumbnail.infoembedwindow import InfoEmbedWindow
from zoo.libs.pyqt.extended.searchablemenu import TaggedAction
from zoo.libs.pyqt.extended.snapshotui import SnapshotUi
from zoo.libs.pyqt.widgets import searchwidget, layouts, buttons
from zoo.libs.pyqt.widgets.extendedbutton import ExtendedButton
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton
from zoo.libs.pyqt.widgets.layouts import hBoxLayout, vBoxLayout

from zoo.libs import iconlib
from zoo.libs.zooscene import zooscenefiles, constants
from zoo.libs.utils import general, application, output, filesystem
from zoo.core.util import zlogging

if general.TYPE_CHECKING:
    from zoo.libs.pyqt.extended.imageview import model as thumbnailmodel

logger = zlogging.zooLogger


class MiniBrowserThumbnail(ThumbnailWidget):

    def __init__(self, slider=False, sliderArgs=None, *args, **kwargs):
        """ Minibrowser Thumbnail Widget

        :param slider:
        :param sliderArgs:
        :param args:
        :param kwargs:
        """

        super(MiniBrowserThumbnail, self).__init__(*args, **kwargs)

        sliderArgs = sliderArgs or {}
        self.virtualSlider = None  # type: VirtualSlider
        if slider:
            self.virtualSlider = VirtualSlider(parent=self, **sliderArgs)

    def mousePressEvent(self, event):
        """ Mouse press event.
        Activates the virtual slider if virtual slider exists

        :param event:
        :return:
        """

        if self.virtualSlider:
            self.virtualSlider.mousePressed(event)

        return super(ThumbnailWidget, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """ Mouse move event.

        Runs the virtual slider code.

        :param event:
        :return:
        """

        if self.virtualSlider:

            moving = self.virtualSlider.mouseMoved(event)

            # Don't consume mouse move event if not moving
            if not moving:
                return super(ThumbnailWidget, self).mouseMoveEvent(event)
        else:
            return super(ThumbnailWidget, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """ Mouse release event

        Runs the virtual slider release code

        :param event:
        :return:
        """
        if self.virtualSlider:
            self.virtualSlider.mouseReleased(event)

        return super(ThumbnailWidget, self).mouseReleaseEvent(event)


class MiniBrowser(QtWidgets.QWidget):
    itemSelectionChanged = QtCore.Signal(object, object)  # Item selection changed of model
    infoToggled = QtCore.Signal(bool)  # When info embed window is toggled
    screenshotSaved = QtCore.Signal(object)
    savedHeight = None  # type: int
    infoEmbedWindow = None  # type: InfoEmbedWindow
    dirSelectionChanged = QtCore.Signal(object, object)
    dotsMenu = None  # type: DotsMenu
    thumbWidget = None  # type: ThumbnailWidget
    infoButton = None  # type: ExtendedButton
    searchWidget = None  # type: ThumbnailSearchWidget
    uniformIcons = True
    SNAPTYPE_NEW = 0
    SNAPTYPE_EDIT = 1
    _THEME_PREFS = None

    def __init__(self,
                 parent=None, listDelegate=None, toolsetWidget=None,
                 columns=None, iconSize=None, fixedWidth=None, fixedHeight=None, infoEmbedShift=200,
                 uniformIcons=False, itemName="", applyText="Apply", applyIcon="checkOnly", createText="New",
                 newActive=True, snapshotActive=False, clipboardActive=False, snapshotNewActive=False,
                 createThumbnailActive=False, selectDirectoriesActive=False, virtualSlider=False,
                 virtualSliderArgs=None):
        """ The main widget for viewing thumbnails

        :param parent: the parent widget
        :type parent: QtWidgets.QWidget
        :param toolsetWidget: Optional Toolset Ui
        :type toolsetWidget: zoo.apps.toolsetsui.widgets.toolsetwidget.ToolsetWidget
        :param infoEmbedShift: How many pixels to shift when info embed window activated
        :type infoEmbedShift: int
        :param listDelegate:
        :type listDelegate:

        :param columns: The number of square image columns, will vary for non-square images, overrides iconSize
        :type columns: int
        :param iconSize: Set the icon size in pixels, will be overridden by columns
        :type iconSize: QtCore.QSize
        :param fixedWidth: The fixed width of the widget in pixels, dpi handled
        :type fixedWidth: int
        :param fixedHeight: the fixed height of the widget in pixels, dpi handled
        :type fixedHeight: int
        :param uniformIcons: Will keep the icons square, images will be clipped if True, non square if False
        :type uniformIcons: bool
        """
        super(MiniBrowser, self).__init__(parent=parent)
        if MiniBrowser._THEME_PREFS is None:
            MiniBrowser._THEME_PREFS = coreinterfaces.coreInterface()
        self.virtualSlider = virtualSlider
        self._virtualSliderArgs = virtualSliderArgs or {}
        self.toolsetWidget = toolsetWidget
        self.infoEmbedShift = utils.dpiScale(infoEmbedShift)
        self.listDelegate = listDelegate
        self.uniformIcons = uniformIcons
        self.folderPopupButton = None  # type: ExtendedButton
        self.itemName = itemName
        self.applyText = applyText
        self.applyIcon = applyIcon
        self.createText = createText
        self.snapshotType = self.SNAPTYPE_EDIT
        self.hasRefreshedView = False
        self.autoResizeItems = True
        self.directoryPopup = directorypopup.DirectoryPopup(None)
        # save the Save location when a New snap shot or asset occurs that way when we save again
        # we can diff the previous save result and if it's the same we'll reuse the directory instead
        # of requesting for user selection

        self.previousSaveDirectories = {"to": None,
                                        "directories": []
                                        }

        self.snapshotWgt = None  # type: SnapshotUi  or None
        if snapshotActive:
            self.newSnapshotWidget()

        self.initUi()

        if not selectDirectoriesActive:
            self.folderPopupButton.hide()

        if iconSize is not None:
            self.setIconSize(iconSize)
        if columns:
            self.setColumns(columns)
        if fixedHeight:
            self.setFixedHeight(utils.dpiScale(fixedHeight), save=True)
        if fixedWidth:
            self.setFixedWidth(utils.dpiScale(fixedWidth))

        self.dotsMenu.setSnapshotActive(snapshotActive)
        self.dotsMenu.setFromClipboardActive(clipboardActive)
        self.dotsMenu.setFromSnapShotActive(snapshotNewActive)
        self.dotsMenu.setCreateThumbnailActive(createThumbnailActive)
        self.dotsMenu.setCreateActive(newActive)
        self.connections()

    def setSliderSettings(self, directions=VirtualSlider.DirectionClamp,
                          minValue=None, maxValue=None,
                          numType=float, step=10, pixelRange=None,
                          slowSpeed=0.01, speed=0.1, fastSpeed=1,
                          slowSpeedXY=(None, None),
                          speedXY=(None, None),
                          fastSpeedXY=(None, None),
                          minValueXY=(None, None),
                          maxValueXY=(None, None),
                          mouseButton=QtCore.Qt.MiddleButton,
                          slowModifier=QtCore.Qt.ControlModifier, fastModifier=QtCore.Qt.ShiftModifier):
        """ Set the virtual slider settings


        :param directions: Can be VirtualSlider.Horizontal, Vertical, DirectionClamp, Both
        :type directions: int
        :param minValue: The minimum value that gets returned when the signal is fired. None means not limited.
        :param minValue: float
        :param maxValue: The maximum value that gets returned when the signal is fired. None means not limited.
        :type maxValue: float
        :param numType: The num type that gets returned in the value. Returns float by default, but can return int.
        :type numType: float or int
        :param step: The step in pixels when dragging. A step of 10 means that it will fire a signal every 10 pixels
        :type step: int
        :param pixelRange: Pixel range where the mouse can move. If 100 is given it will move between -100 and 100.
        :type pixelRange: int
        :param speed: The speed of how fast the value will go up or down. 0.1 means the value will go up 0.1 per step
        :type speed: float
        :param slowSpeed: The slow speed, for when Ctrl (or whatever `slowModifier` is set to) is pressed
        :type slowSpeed: float
        :param fastSpeed: The slow speed, for when Shift (or whatever `shiftModifier` is set to) is pressed
        :type fastSpeed: float
        :param speedXY: The XY speed. This will override the speed. If any value is none, it will just use the `speed` arg
        :type speedXY:  tuple(float or None, float or None)
        :param slowSpeedXY: The slow speed XY. This will override the slowSpeed.
        :type slowSpeedXY:  tuple(float or None, float or None)
        :param fastSpeedXY: The fast speed XY. This will override the fastSpeed.
        :type fastSpeedXY: tuple(float or None, float or None)
        :param minValueXY: The minimum value returned for `value` if it's moving on the x-axis. Will override `minValue`
        :type minValueXY: tuple(float or None, float or None)
        :param maxValueXY: The maximum value returned for `value` if it's moving on the x-axis. Will override `minValue`
        :type maxValueXY: tuple(float or None, float or None)
        :param mouseButton: The mouse button that needs to be pressed to activate the slider. Default MiddleButton.
        :type mouseButton: QtCore.Qt.MouseButton
        :param slowModifier: The keyboard modifier for slow
        :type slowModifier: QtCore.Qt.KeyboardModifier
        :param fastModifier: The keyboard modifier for fast
        :type fastModifier: QtCore.Qt.KeyboardModifier
        :return:
        """
        args = general.getArgs(locals())
        self.thumbWidget.virtualSlider.setSettings(**args)

    def initUi(self):
        """ Initialize UI

        :return:
        :rtype:
        """

        layout = vBoxLayout()
        self.setLayout(layout)
        self.thumbWidget = MiniBrowserThumbnail(parent=self, delegate=self.listDelegate,
                                                uniformIcons=self.uniformIcons,
                                                slider=self.virtualSlider, sliderArgs=self._virtualSliderArgs)
        self.infoEmbedWindow = InfoEmbedWindow(parent=self,
                                               margins=(0, 0, 0, uic.SMLPAD), resizeTarget=self.thumbWidget)

        layout.addLayout(self.topBar())
        layout.addWidget(self.infoEmbedWindow)
        layout.addWidget(self.thumbWidget, 1)

        layout.setContentsMargins(0, 0, 0, 0)
        self.thumbWidget.setSpacing(utils.dpiScale(0))

    @property
    def sliderChanged(self):
        return self.thumbWidget.virtualSlider.scrolled

    @property
    def sliderReleased(self):
        return self.thumbWidget.virtualSlider.released

    @property
    def sliderPressed(self):
        return self.thumbWidget.virtualSlider.pressed

    def newSnapshotWidget(self):
        """ Create a new snapshot widget """
        self.snapshotWgt = SnapshotUi(application.mainWindow(), onSave=self.screenshotSaved.emit)
        self.snapshotWgt.saved.connect(self.snapshotSaved)
        self.snapshotWgt.closed.connect(self.newSnapshotWidget)
        return self.snapshotWgt

    def connections(self):
        """ Connections

        :return:
        :rtype:
        """

        # self.dotsMenu.snapshotNewAction.connect(self.setPathThumbnail)
        self.browseAction.connect(self.browseSelected)
        if self.toolsetWidget is not None:
            self.toolsetWidget.toolsetUi.closed.connect(self.directoryPopup.close)
            self.toolsetWidget.toolsetDragged.connect(self.directoryPopup.close)
            self.toolsetWidget.toolsetDeactivated.connect(self.directoryPopup.close)
            self.toolsetWidget.toolsetDropped.connect(self.directoryPopup.close)
            self.toolsetWidget.toolsetUi.beginClosing.connect(self.directoryPopup.close)

        zooWindow = ZooWindow.getZooWindow(self)

        if zooWindow:
            zooWindow.minimized.connect(self.directoryPopup.close)

    def browseSelected(self):
        """Opens a windows/osx/linux file browser with the model asset directory path"""
        currentItem = self.currentItem()
        directory = currentItem.directory if currentItem else self.model().activeDirectories[0].path
        filesystem.openDirectory(directory)

    @property
    def filterMenu(self):
        return self.searchWidget.filterMenu

    def topBar(self):
        """ Top Bar

        :return:
        :rtype:
        """
        topLayout = hBoxLayout(margins=(0, 0, 0, uic.SPACING), spacing=uic.SSML)
        self.folderPopupButton = buttons.styledButton(icon="closeFolder", style=uic.BTN_TRANSPARENT_BG,
                                                      toolTip="Folder")
        self.searchWidget = ThumbnailSearchWidget(self, themePref=MiniBrowser._THEME_PREFS)
        toolTip = "Thumbnail information and add meta data"
        self.infoButton = buttons.styledButton(icon="information", style=uic.BTN_TRANSPARENT_BG, toolTip=toolTip)
        self.searchWidget.searchChanged.connect(self.onSearchChanged)
        self.infoButton.leftClicked.connect(self.toggleInfoVisibility)
        self.dotsMenu = DotsMenu(self, uniformIcons=self.uniformIcons, itemName=self.itemName, applyText=self.applyText,
                                 applyIcon=self.applyIcon, createText=self.createText)
        self.dotsMenu.uniformIconAction.connect(self.updateUniformIcons)
        self.folderPopupButton.leftClicked.connect(self.selectDirectoriesPopup)

        topLayout.addWidget(self.folderPopupButton)
        topLayout.addWidget(self.searchWidget)
        topLayout.addWidget(self.infoButton)
        topLayout.addWidget(self.dotsMenu)
        return topLayout

    def selectDirectoriesPopup(self):
        """ Select directories popup

        :return:
        """
        if not self.directoryPopup.isVisible():
            self.updateDirectoryPopup()
            self.directoryPopup.show()
        else:
            self.directoryPopup.close()

    def updateDirectoryPopup(self):
        """

        :return:
        """
        model = self.model()
        logger.debug("Update Directory Popup")
        model.updateFromPrefs()
        self.directoryPopup.setAnchorWidget(self)
        self.directoryPopup.browserPreference = self.model().preference()
        self.directoryPopup.reset()
        self.directoryPopup.setActiveItems(model.activeDirectories, model.preference().activeCategories())

    def updateUniformIcons(self, taggedAction):
        """ Update the uniform icons

        :param taggedAction:
        :type taggedAction: TaggedAction
        :return:
        :rtype:
        """
        self.uniformIcons = taggedAction.isChecked()

    def setSnapshotType(self, snapType):
        """

        :param snapType:
        :type snapType: MiniBrowser.SNAPTYPE_NEW or MiniBrowser.SNAPTYPE_EDIT
        :return:
        :rtype:
        """

        self.snapshotType = snapType
        if self.snapshotWgt:
            if snapType == MiniBrowser.SNAPTYPE_NEW:
                self.snapshotWgt.setWindowTitle("Create New Item")
            else:
                self.snapshotWgt.setWindowTitle("Edit Thumbnail")

    def snapshotSaved(self, pixmap):
        """ Refresh thumbs on snapshot saved

        :return:
        :rtype:
        """
        screenShotPath = self._updatePathThumbnail()
        if self.snapshotType == self.SNAPTYPE_EDIT:
            indices = self.thumbWidget.selectedIndexes()
            if not indices:
                return
            dataModelIndex, dataModel = modelutils.dataModelIndexFromIndex(
                indices[0])  # type: QtCore.QModelIndex, thumbnailmodel.MiniBrowserFileModel
            if dataModelIndex.isValid():
                qTreeItem = dataModel.itemFromIndex(dataModelIndex)
                dataItem = qTreeItem.item()
                dataItem.thumbnail = screenShotPath
                filesystem.ensureFolderExists(os.path.dirname(screenShotPath))
                pixmap.save(screenShotPath, dataItem.imageExt)
                dataModel.setItemIconFromImage(qTreeItem, pixmap.toImage())
        else:
            filesystem.ensureFolderExists(os.path.dirname(screenShotPath))
            imageExt = os.path.splitext(os.path.basename(screenShotPath))[-1]
            pixmap.save(screenShotPath, imageExt[1:])
            qItem, _ = self.model().createItemFromFileAndDirectory(os.path.dirname(screenShotPath), screenShotPath,
                                                                   loadImage=True)
            self.thumbWidget.scrollTo(qItem.index())

    def setSnapshotActive(self, active):
        """ Helper function to set snapshot

        :param active:
        :type active:
        :return:
        :rtype:
        """
        self.dotsMenu.setSnapshotActive(active)

    def _updatePathThumbnail(self):
        """ Save the thumbnail path to get ready to save

        :return:
        :rtype:
        """

        if not self.snapshotWgt:
            return
        item = self.model().currentItem

        if self.snapshotType == MiniBrowser.SNAPTYPE_EDIT:
            if not os.path.dirname(item.thumbnail).endswith(constants.DEPENDENCY_FOLDER):
                dep = zooscenefiles.getDependencyFolder(item.fullPath(), create=False)[0]
                thumbPath = os.path.join(dep, os.path.extsep.join(("thumbnail", item.imageExt)))
                screenshotPath = thumbPath
            else:
                screenshotPath = item.thumbnailLookPath()
        else:  # MiniBrowser.SNAPTYPE_NEW
            dirs = self.activeDirectories()
            if not dirs:
                dirs = self.directories()
            previousSaveDirectories = self.previousSaveDirectories
            previousSave = previousSaveDirectories["to"]
            dirPath = None
            if previousSave:
                previousSaveDirectoriesIds = [i.id for i in previousSaveDirectories["directories"]]
                if all(i.id in previousSaveDirectoriesIds for i in dirs):
                    dirPath = previousSave
            if dirPath is None:
                if len(dirs) > 1:
                    dirPath = self.displaySavePopup(buttonA="Set Directory", directories=dirs)
                elif len(dirs) == 1:
                    dirPath = dirs[0]
            self.previousSaveDirectories["to"] = dirPath
            self.previousSaveDirectories["directories"] = dirs

            if dirPath:
                newName = self.newImageName() + ".png"
                screenshotPath = os.path.join(dirPath.path, newName)
            else:
                output.displayInfo("Save cancelled.")
                return
        return screenshotPath

    def displaySavePopup(self, message="Save to Location:", title="Save Location", buttonA="Save", buttonIconA="save",
                         directories=None):
        """ Display save Popup

        :param message:
        :param title:
        :param buttonA:
        :param buttonIconA:
        :return:
        """
        directories = directories or self.activeDirectories()
        if not directories:
            directories = self.directories()
        paths = [f.alias for f in directories]

        res = MessageBox.showCombo(title=title, message=message,
                                   items=paths, defaultItem=0, data=directories, buttonIconA=buttonIconA,
                                   buttonA=buttonA)
        if res[0] != -1:
            return res[2]

    def onSearchChanged(self, text, tag):
        """ Set the filter on search changed

        :param text:
        :type text:
        :param tag:
        :type tag:
        :return:
        :rtype:
        """
        self.filter(text, tag)

    def newImageName(self):
        """ Generate a new name

        :return:
        :rtype:
        """
        itemTexts = list(self.model().itemTexts())
        check = 1000
        for i in range(1, check):
            testName = "newimage{}".format(str(i).zfill(2))
            if testName not in itemTexts:
                return testName

    def setFixedHeight(self, h, save=False):
        """ Sets the fixed height of the widget

        :param h:
        :type h:
        :param save: save this height as a default when switching between infoembedwindows
        :type save:
        :return:
        :rtype:
        """

        super(MiniBrowser, self).setFixedHeight(h)
        if save:
            self.savedHeight = h

    def selectedMetadata(self):
        """ Gets the metadata of the currently selected item

        :return:
        :rtype: dict
        """
        return dict(self.infoEmbedWindow.metadata)

    def itemFilePath(self):
        """ Gets the current filepath from the currently selected items metadata

        :return:
        :rtype:
        """
        if self.infoEmbedWindow.metadata is None:
            return None

        return self.infoEmbedWindow.metadata['zooFilePath']

    def itemDependencyPath(self, create=False):
        """ Get dependency folder

        :return:
        :rtype:
        """
        try:
            if self.infoEmbedWindow.metadata is None:
                return None
            ret = self.infoEmbedWindow.metadata.get('zooFilePath')
            if ret is None:
                return None
        except TypeError:
            return None
        return zooscenefiles.getDependencyFolder(ret, create=create)[0]

    def directories(self):
        """ Get the directory

        :return:
        :rtype:
        """
        return self.model().directories

    def activeDirectories(self):
        return self.model().activeDirectories

    def itemFileName(self):
        """ Gets the current file name from the currently selected item's metadata

        :return:
        :rtype:
        """
        return self.infoEmbedWindow.metadata['name']

    def itemFileExt(self):
        """

        :return:
        :rtype: basestring
        """
        return self.infoEmbedWindow.metadata['extension']

    def setModel(self, model):
        """

        :param model:
        :type model: zoo.libs.pyqt.extended.imageview.model.FileModel
        :return:
        :rtype:
        """

        self.thumbWidget.setModel(model)
        self.infoEmbedWindow.setModel(model)
        model.refreshAssetFolders()
        model.refreshList()  # Does the refresh

        self.directoryPopup.selectionChanged.connect(self._setModelDirectories)
        model.itemSelectionChanged.connect(self.itemSelected)

    def _setModelDirectories(self, directories):
        """

        :param directories:
        :type directories: list[zoo.core.tooldata.tooldata.DirectoryPath]
        :return:
        """

        dirs = self.model().directories
        active = directories
        model = self.thumbWidget.rootModel()
        model.setDirectories(dirs, False)
        model.setActiveDirectories([], False)
        model.refreshList()
        self.thumbWidget.refresh()
        if not active:
            return
        self.thumbWidget.setCurrentIndexInt(0)  # select first on change

    def itemSelected(self, name, item):
        """ Item selected

        :param item:
        :type item:  :class:`zoo.libs.pyqt.extended.imageview.items.BaseItem`
        :return:
        :rtype:
        """
        self.dotsMenu.setSnapshotEnabled(True)
        self.itemSelectionChanged.emit(name, item)

    def currentItem(self):
        """Returns the currently active item

        :return:
        :rtype: :class:`zoo.libs.pyqt.extended.imageview.items.BaseItem`
        """
        return self.model().currentItem

    def model(self):
        """

        :rtype: :class:`zoo.libs.pyqt.extended.imageview.model.MiniBrowserFileModel`
        """
        return self.thumbWidget.rootModel()

    def refreshThumbs(self, scrollToItemName=-1):
        """ Refreshes the GUI

        :return:
        :rtype:
        """
        if not utils.widgetVisible(self):  # Don't need to refresh if invisible, also seems to crash in 2022
            return
        dataModel = self.model()

        itemName = dataModel.currentItem.name if dataModel.currentItem is not None else ""
        self.thumbWidget.threadPool.waitForDone()
        self.setUpdatesEnabled(False)
        self.searchWidget.setSearchText("")
        state = self.thumbWidget.state()
        dataModel.setUniformItemSizes(self.uniformIcons)
        dataModel.refreshAssetFolders()
        dataModel.refreshList()  # Does the refresh

        scrollTo = False
        if scrollToItemName != -1:  # todo: merge this with above
            state['selected'] = dataModel.indexFromText(scrollToItemName).row()
            scrollTo = True
        else:
            # Select the newest saved
            index = dataModel.findItems(itemName)
            if index:
                index = self.thumbWidget.model().mapFromSource(index[0].index())  # type: QtCore.QModelIndex
                state['selected'] = index.row()
                scrollTo = True
        self.setUpdatesEnabled(True)
        self.refreshListView()
        self.updateDirectoryPopup()
        self.thumbWidget.setState(state, scrollTo=scrollTo)

    def toggleInfoVisibility(self):
        """ Toggles the vis of the Information tags section

        :return:
        :rtype:
        """
        currentImage = self.model().currentImage
        if not currentImage:  # no image has been selected
            output.displayWarning("Please select an asset thumbnail image.")
            return
        vis = not self.infoEmbedWindow.isVisible()
        self.infoEmbedWindow.setEmbedVisible(vis)

        if vis:
            self.savedHeight = self.minimumHeight()
            # Use height of this widget or the embed window plus a little extra
            self.setFixedHeight(max(self.infoEmbedWindow.height() + self.infoEmbedShift,
                                    self.minimumHeight()))
        else:
            self.setFixedHeight(self.savedHeight)

        self.infoToggled.emit(not vis)

        if self.toolsetWidget:
            self.updateToolset(delayed=True)

    def refreshListView(self):
        """ Refresh List View
        Make sure the icons resize correctly

        :return:
        :rtype:
        """
        self.thumbWidget.refresh()

    def invisibleRootItem(self):
        """ Get the invisible root item of the thumbwidget

        :return:
        :rtype:
        """

        return self.thumbWidget.invisibleRootItem()

    def iconSize(self):
        return self.thumbWidget.iconSize()

    def setIconSize(self, size):
        self.thumbWidget.setIconSize(size)

    def setPersistentFilter(self, text, tags):
        self.thumbWidget.setPersistentFilter(text, tags)

    def filter(self, text, tag=None):
        """ Filter the text by the tag type (description, tags, creator, websites etc)

        :param text:
        :param tag:
        :return:
        """
        self.thumbWidget.filter(text, tag)

    def setColumns(self, col):
        """ Reset columns to default

        :param col:
        :type col:
        :return:
        :rtype:
        """
        self.thumbWidget.setColumns(col)

    def setIconMinMax(self, size):
        """ Sets the min and max icon size

        :param size: min and max of the the icon size
        :type size: tuple(int, int)
        """
        self.thumbWidget.setIconMinMax(size)

    def updateToolset(self, delayed=False):
        """ Update the toolset widget if it exists

        :param delayed:
        :type delayed:
        :return:
        :rtype:
        """
        if delayed:
            QtCore.QTimer.singleShot(0, self.updateToolset)
            return
        treeWidget = self.toolsetWidget.treeWidget
        toolsetUi = self.toolsetWidget.toolsetUi

        treeWidget.setUpdatesEnabled(False)
        treeWidget.updateTreeWidget()
        toolsetUi.resizeWindow()
        treeWidget.updateTreeWidget()  # needs to be done a second time for some reason
        treeWidget.setUpdatesEnabled(True)

    def resizeEvent(self, event):
        if self.hasRefreshedView:
            super(MiniBrowser, self).resizeEvent(event)
            return
        if self.thumbWidget is not None:
            self.thumbWidget.refresh()
            self.hasRefreshedView = True
        super(MiniBrowser, self).resizeEvent(event)

    def newItemFromClipboard(self):
        """ Create new item from clipboard

        :return:
        :rtype:
        """
        clipboard = QtWidgets.QApplication.clipboard()
        mimeData = clipboard.mimeData()

        if mimeData.hasImage():
            px = QtGui.QPixmap(mimeData.imageData())
            name = self.newImageName()
            saveDir = self.getSaveDirectory()
            if saveDir:
                path = os.path.join(saveDir, name + ".png")
                px.save(path)
                self.refreshThumbs(scrollToItemName=name)
        else:
            output.displayWarning("No Image found in clipboard")

    def getSaveDirectory(self):
        """ Get the save directory either from user or preferences

        :return:
        :rtype: str or None
        """
        model = self.model()
        dirs = model.activeDirectories
        if not dirs:
            dirs = model.directories
        if len(dirs) == 1:  # if there's only one active return that
            return dirs[0].path

        # todo: if user says "don't ask again", use the previous selected one.
        if not dirs:
            MessageBox.showWarning(title="No Directories found",
                                   message="No directories found! Please add a folder with the folder icon.",
                                   buttonB=None)
            return
        saveDir = self.displaySavePopup()
        if saveDir:
            return saveDir.path
        return ""

    @property
    def applyAction(self):
        return self.dotsMenu.applyAction

    @property
    def createAction(self):
        return self.dotsMenu.createAction

    @property
    def renameAction(self):
        return self.dotsMenu.renameAction

    @property
    def deleteAction(self):
        return self.dotsMenu.deleteAction

    @property
    def browseAction(self):
        return self.dotsMenu.browseAction

    @property
    def setDirectoryAction(self):
        return self.dotsMenu.setDirectoryAction

    @property
    def refreshAction(self):
        return self.dotsMenu.refreshAction

    @property
    def uniformIconAction(self):
        return self.dotsMenu.uniformIconAction

    @property
    def selectDirectoriesAction(self):
        return self.dotsMenu.selectDirectoriesAction


class ThumbnailSearchWidget(QtWidgets.QWidget):
    searchChanged = QtCore.Signal(object, object)

    def __init__(self, parent=None, themePref=None):
        """ Search Widget for the thumbnail view

        :param parent:
        :type parent:
        :param themePref:
        :type themePref: preferences.interface.preference_interface.ZooToolsPreference
        """
        super(ThumbnailSearchWidget, self).__init__(parent)
        self.themePref = themePref

        self.mainLayout = layouts.hBoxLayout(self)
        toolTip = "Search filter by meta data"
        self.filterMenu = IconMenuButton(parent=self,
                                         color=self.themePref.ICON_PRIMARY_COLOR,
                                         switchIconOnClick=True)
        self.filterMenu.setToolTip(toolTip)  # IconMenuButton must set after
        self.filterMenu.addAction("Name And Tags", icon="filter", data=["filename", "tags"])
        self.filterMenu.addAction("File Name", icon="file", data="filename")
        self.filterMenu.addAction("Description", icon="infoTags", data="description")
        self.filterMenu.addAction("Tags", icon="tag", data="tags")
        self.filterMenu.addAction("Creators", icon="creator", data="creators")
        self.filterMenu.addAction("Websites", icon="web", data="websites")
        self.filterMenu.addAction("All", icon="selectAll",
                                  data=["filename", "tags", "description", "creators", "websites"])

        self.filterMenu.setMenuName("Name And Tags")  # sets the default icon and menu states
        self.filterMenu.setMenuAlign(QtCore.Qt.AlignLeft)

        self.searchEdit = searchwidget.SearchLineEdit(parent=self)
        self.setFixedHeight(utils.dpiScale(22))
        self.searchEdit.setPlaceholderText("Search...")

        self.mainLayout.addWidget(self.filterMenu)
        self.mainLayout.addWidget(self.searchEdit)

        self.searchEdit.textChanged.connect(self.onSearchChanged)
        self.filterMenu.actionTriggered.connect(self.onActionTriggered)

    def onSearchChanged(self, text):
        """ On Search Changed

        :param text:
        :type text:
        :return:
        :rtype:
        """
        self.searchChanged.emit(text, self.filterMenuData())

    def filterMenuData(self):
        return self.filterMenu.currentAction().data()

    def onActionTriggered(self, action, mouseMenu):
        self.searchChanged.emit(self.searchEdit.text(), action.data())

    def setSearchText(self, text):
        """ Set the text of the search edit

        :param text:
        :type text:
        :return:
        :rtype:
        """
        self.searchEdit.setText(text)

    def state(self):
        """ Get the state of the widget

        :return:
        :rtype:
        """
        return {"filter": self.filterMenu.currentText(),
                "search": self.searchEdit.text()}

    def setState(self, state):
        """ Set the state of the widget

        :param state:
        :type state:
        :return:
        :rtype:
        """
        # Block signals so we can do it all at once after
        self.blockSignals(True)
        self.filterMenu.setMenuName(state['filter'])
        self.searchEdit.setText(state['search'])
        self.blockSignals(False)
        utils.singleShotTimer(partial(self.onSearchChanged, state['search']))


class DotsMenu(IconMenuButton):
    menuIcon = "menudots"
    applyAction = QtCore.Signal()
    createAction = QtCore.Signal()
    renameAction = QtCore.Signal()
    deleteAction = QtCore.Signal()
    browseAction = QtCore.Signal()
    setDirectoryAction = QtCore.Signal()
    selectDirectoriesAction = QtCore.Signal()
    refreshAction = QtCore.Signal()
    uniformIconAction = QtCore.Signal(object)
    snapshotAction = QtCore.Signal()
    snapshotNewAction = QtCore.Signal()
    createThumbnailAction = QtCore.Signal()
    newFromClipboard = QtCore.Signal()

    APPLY_ACTION = 0
    CREATE_ACTION = 1
    RENAME_ACTION = 2
    DELETE_ACTION = 3
    BROWSE_ACTION = 4
    SETDIRECTORY_ACTION = 5
    REFRESH_ACTION = 6
    UNIFORMICON_ACTION = 7
    SNAPSHOT_ACTION = 8
    SNAPSHOTNEW_ACTION = 9
    CREATE_THUMBNAIL_ACTION = 10
    NEWFROMCLIPBOARD_ACTION = 11
    DIRECTORYPOPUP_ACTION = 12

    def __init__(self, parent=None, uniformIcons=True, itemName="", applyText="Apply", applyIcon="checkOnly",
                 createText="New", newActive=True, renameActive=True, deleteActive=True, snapshotActive=False,
                 createThumbnailActive=False, itemFromSnapshotActive=False, newClipboardActive=False):
        """This class is the dots menu button and right click menu

        TODO:  Should add right clicks to buttons in an easier way

        :param parent: The Qt Widget parent
        :type parent: MiniBrowser
        """
        self.dotsMenuName = itemName
        self._uniformIcons = uniformIcons
        self.menuActions = None

        self.applyText = applyText
        self.applyIcon = applyIcon
        self.createText = createText
        self.menuActions = OrderedDict()  # type: dict[str or int, TaggedAction]
        super(DotsMenu, self).__init__(parent=parent)

        self.setCreateActive(newActive)
        self.setRenameActive(renameActive)
        self.setDeleteActive(deleteActive)
        self.setSnapshotActive(snapshotActive)
        self.setFromClipboardActive(newClipboardActive)
        self.setFromSnapShotActive(newClipboardActive)
        self.setCreateThumbnailActive(createThumbnailActive)

    def initUi(self):
        super(DotsMenu, self).initUi()

        iconColor = MiniBrowser._THEME_PREFS.ICON_PRIMARY_COLOR
        self.setIconByName(self.menuIcon, size=16, colors=iconColor)
        self.setToolTip("File menu. Manage {}".format(self.dotsMenuName))

        applyIcon = iconlib.iconColorized(self.applyIcon, utils.dpiScale(16))
        saveIcon = iconlib.iconColorized("save", utils.dpiScale(16))
        renameIcon = iconlib.iconColorized("editText", utils.dpiScale(16))
        deleteIcon = iconlib.iconColorized("trash", utils.dpiScale(16))
        browseIcon = iconlib.iconColorized("folder", utils.dpiScale(16))
        refreshIcon = iconlib.iconColorized("refresh", utils.dpiScale(16))
        setPrefsIcon = iconlib.iconColorized("addDir", utils.dpiScale(16))
        snapshotIcon = iconlib.iconColorized("cameraSolid", utils.dpiScale(16))

        if env.isWindows():
            fileBrowser = "Explorer"
        elif env.isMac():
            fileBrowser = "Finder"
        else:
            fileBrowser = "Explorer"

        # New Actions to add
        newActions = \
            [("DoubleClick", ("{} (Double Click)".format(self.applyText), self.applyAction.emit, applyIcon, False)),
             ("---", None),
             (DotsMenu.CREATE_ACTION,
              ("{} {}".format(self.createText, self.dotsMenuName), self.createAction.emit, saveIcon, False)),
             (DotsMenu.RENAME_ACTION,
              ("Rename {}".format(self.dotsMenuName), self.renameAction.emit, renameIcon, False)),
             (DotsMenu.DELETE_ACTION,
              ("Delete {}".format(self.dotsMenuName), self.deleteAction.emit, deleteIcon, False)),
             ("---", None),
             (DotsMenu.SETDIRECTORY_ACTION,
              ("Set {} Dir".format(self.dotsMenuName), self.setDirectoryAction.emit, setPrefsIcon, False)),
             (DotsMenu.DIRECTORYPOPUP_ACTION,
              ("Select Directories...", self.selectDirectoriesAction.emit, setPrefsIcon, False)),

             (DotsMenu.BROWSE_ACTION, ("Open in {}".format(fileBrowser), self.browseAction.emit, browseIcon, False)),
             (DotsMenu.REFRESH_ACTION, ("Refresh Thumbnails", self.refreshAction.emit, refreshIcon, False)),
             ("---", None),
             (DotsMenu.UNIFORMICON_ACTION, ("Square Icons", self.uniformActionClicked, None, True)),
             (DotsMenu.SNAPSHOTNEW_ACTION, ("Snapshot New", self.newItemSnapshotMenuClicked, snapshotIcon, False)),
             (DotsMenu.SNAPSHOT_ACTION,
              ("Replace Image (Please select an item)", self.snapshotMenuClicked, snapshotIcon, False)),
             (DotsMenu.NEWFROMCLIPBOARD_ACTION,
              ("Paste From Clipboard", self.parent().newItemFromClipboard, snapshotIcon, False)),
             (DotsMenu.CREATE_THUMBNAIL_ACTION, ("New Thumbnail", self.createThumbnailAction.emit, applyIcon, False))]

        # Add actions
        for key, value in newActions:
            if value is None and key == "---":  # add separators
                self.addSeparator()
            else:  # otherwise add the actions
                text, connect, icon, checkable = value
                self.menuActions[key] = self.addAction(text, connect=connect, icon=icon, checkable=checkable)

        # Extra settings for the actions
        self.menuActions[DotsMenu.SNAPSHOT_ACTION].setEnabled(False)
        self.menuActions[DotsMenu.UNIFORMICON_ACTION].setChecked(self._uniformIcons)
        self.setMenuAlign(QtCore.Qt.AlignRight)
        self.menuActions[DotsMenu.DIRECTORYPOPUP_ACTION].setVisible(False)

    def parent(self):
        """

        :return:
        :rtype: MiniBrowser
        """
        return super(DotsMenu, self).parent()

    def uniformActionClicked(self, action):
        """ Uniform action clicked

        :param action:
        :type action: TaggedAction
        :return:
        :rtype:
        """
        self._uniformIcons = action.isChecked()
        self.uniformIconAction.emit(action)

    def snapshotMenuClicked(self):
        """ On snapshot clicked

        :return:
        :rtype:
        """
        parent = self.parent()
        parent.setSnapshotType(MiniBrowser.SNAPTYPE_EDIT)
        parent.snapshotWgt.show()

    def newItemSnapshotMenuClicked(self):
        parent = self.parent()
        parent.setSnapshotType(MiniBrowser.SNAPTYPE_NEW)
        parent.snapshotWgt.show()

    def setActionActive(self, actionId, active):
        self.menuActions[actionId].setVisible(active)

    def setCreateActive(self, active):
        """ Show/Hide create/new menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.CREATE_ACTION, active)

    def setRenameActive(self, active):
        """ Show/Hide rename menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.RENAME_ACTION, active)

    def setDeleteActive(self, active):
        """ Show/Hide delete menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.DELETE_ACTION, active)

    def setSnapshotActive(self, active):
        """ Show/Hide snapshot menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.SNAPSHOT_ACTION, active)
        if not self.parent().snapshotWgt:
            self.parent().newSnapshotWidget()

    def setSnapshotEnabled(self, enabled):
        """ Set enabled

        :param enabled:
        :type enabled:
        :return:
        :rtype:
        """
        snapshotAction = self.menuActions[DotsMenu.SNAPSHOT_ACTION]
        snapshotAction.setEnabled(enabled)
        if snapshotAction.isEnabled():
            snapshotAction.setText("Snapshot Replace")
        else:
            snapshotAction.setText("Snapshot Replace (Please select an item)")

    def setFromClipboardActive(self, active):
        """ Show/Hide delete menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.NEWFROMCLIPBOARD_ACTION, active)

    def setFromSnapShotActive(self, active):
        """ Show/Hide delete menu item

        :param active:
        :type active: bool
        :return:
        :rtype:
        """
        self.setActionActive(DotsMenu.SNAPSHOTNEW_ACTION, active)

    def setCreateThumbnailActive(self, active):
        self.setActionActive(DotsMenu.CREATE_THUMBNAIL_ACTION, active)

    def setDirectoryActive(self, active):
        self.setActionActive(DotsMenu.SETDIRECTORY_ACTION, active)
