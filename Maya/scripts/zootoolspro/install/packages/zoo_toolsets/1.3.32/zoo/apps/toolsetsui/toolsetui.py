from zoovendor.six.moves import cPickle
import time

from zoovendor import six
from zoovendor.Qt import QtCore, QtWidgets

from zoo.apps.toolsetsui.widgets import toolsettree, toolsetwidgetitem
from zoo.apps.toolsetsui.widgets.toolsetframe import ToolsetFrame
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets.frameless.widgets import TitleBar
from zoo.core.util import zlogging
from zoo.preferences.interfaces import coreinterfaces
from zoo.apps.toolsetsui import registry

logger = zlogging.getLogger(__name__)

_TOOLSETUI_INSTANCES = []
_TOOLSETFRAME_INSTANCES = []

TOOLSETUI_WIDTH = 390
TOOLSETUI_HEIGHT = 20
TOOLSETUI_MAXHEIGHT = 800
WINDOWHEIGHT_PADDING = 50


class ToolsetsUI(elements.ZooWindow):
    windowSettingsPath = "zoo/toolsetsui"

    def __init__(self, title="Toolsets", iconColor=(231, 133, 255), hueShift=-30,
                 width=TOOLSETUI_WIDTH,
                 height=TOOLSETUI_HEIGHT,
                 maxHeight=TOOLSETUI_MAXHEIGHT, parent=None,
                 toolsetIds=None, position=None):
        """ Toolsets UI

        :param title:
        :param iconColor: Color of the initial icons
        :param hueShift:
        :param width:
        :param height:
        :param maxHeight:
        :param parent:
        :param toolsetIds: Toolset Ids to run on start up
        :param position:
        """
        super(ToolsetsUI, self).__init__(title=title, width=width, height=height, parent=parent,
                                         titleBar=ToolsetTitleBar,
                                         alwaysShowAllTitle=True,
                                         saveWindowPref=False, initPos=position)

        self.setWindowTitle(title)
        self.hueShift = hueShift
        self.iconColor = iconColor
        self.mainLayout = elements.vBoxLayout()
        self.maxHeight = utils.dpiScale(maxHeight)
        self.resizedHeight = 0
        self.alwaysResizeToTree = True
        self.lastFocusedTime = time.time()

        self.toolsetRegistry = registry.instance()

        self.toolsetFrame = ToolsetFrame(self, window=self, toolsetRegistry=self.toolsetRegistry,
                                         iconColor=iconColor,
                                         hueShift=hueShift,
                                         startHidden=False,
                                         toolbarHidden=False)
        self.toolsetFrame.setUpdatesEnabled(False)
        self.initUi()
        self._initToolsets(toolsetIds)
        self.toolsetFrame.setUpdatesEnabled(True)
        self.setHighlight(True, updateUis=True)

        addToolsetUi(self)
        self.connections()

    def _initToolsets(self, toolsetIds):
        """ Init toolsets

        :param toolsetIds:
        :type toolsetIds:
        :return:
        :rtype:
        """
        toolsetIds = [] if toolsetIds is None else toolsetIds
        for t in toolsetIds:
            self.toggleToolset(t)

    def connections(self):
        self.toolsetFrame.resizeRequested.connect(self.resizeWindow)

    def maximize(self):
        """ Maximize """
        width = self.savedSize.width()
        calcHeight = self.calcHeight()
        self.setUiMinimized(False)
        self._minimized = False

        # Use the resized height
        if calcHeight < self.resizedHeight:
            self.window().resize(width, self.resizedHeight)
        else:
            self.window().resize(width, calcHeight)

    def setHighlight(self, highlight, updateUis=False):
        """ Set the logo highlight.

        Update the other toolset uis

        :param highlight:
        :param updateUis:
        :return:
        """
        # Always set this one to highlight and don't unhighlight the other toolsets
        if self.isMinimized() and not highlight:
            self.titleBar.setLogoHighlight(True)
            return

        self.lastFocusedTime = time.time()

        if highlight and updateUis:
            # Get the last visible toolset
            for t in toolsetUis():
                if not t.isMinimized():
                    t.titleBar.setLogoHighlight(False)
            self.titleBar.setLogoHighlight(True)

    def initUi(self):
        """ Init ui

        :return:
        :rtype:
        """
        self.toolsetFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self.setMainLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)  # this is the grey edge margin to the edge of the window

        self.titleBar.contentsLayout.addWidget(self.toolsetFrame)
        self.mainLayout.addWidget(self.toolsetFrame.tree)  # Pull out of toolsetFrame and add widget here instead
        self.mainLayout.setStretch(1, 1)

        self.titleBar.cornerContentsLayout.addWidget(self.toolsetFrame.menuBtn)
        self.windowResizedFinished.connect(self.resizeEndEvent)

        self.setMaxButtonVisible(False)

    def calcHeight(self):
        """ Calculate Height

        :return:
        :rtype:
        """
        self.maxHeight = self.maxWindowHeight()

        # Calc height
        newHeight = self.window().minimumSizeHint().height() + self.toolsetFrame.calcSizeHint().height()
        newHeight = self.maxHeight if newHeight > self.maxHeight else newHeight
        return newHeight

    def lastHidden(self):
        """ Get last hidden

        :return:
        :rtype: list
        """
        return self.toolsetFrame.tree.lastHidden

    def setLastHidden(self, lastHidden):
        self.toolsetFrame.tree.lastHidden = lastHidden

    def resizeWindow(self, disableScrollBar=True, delayed=False):
        """ Automatically resize the height based on the height of the tree

        :return:
        """

        if delayed:
            QtCore.QTimer.singleShot(0, lambda: self.resizeWindow(disableScrollBar))
            return

        # Max height
        if not self.isDocked():

            if disableScrollBar:
                self.toolsetFrame.tree.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

            self.maxHeight = self.maxWindowHeight()

            newHeight = self.window().minimumSizeHint().height() + self.toolsetFrame.calcSizeHint().height()
            newHeight = self.maxHeight if newHeight > self.maxHeight else newHeight  # Limit height
            width = self.window().rect().width()

            # Use the resized height
            if newHeight < self.resizedHeight and self.alwaysResizeToTree is False:
                self.window().resize(width, self.resizedHeight)
            else:
                # Resize the window based on the tree size
                self.window().resize(width, newHeight)
                self.resizedHeight = newHeight

            if disableScrollBar:
                self.toolsetFrame.tree.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        else:
            self.setMinimumSize(QtCore.QSize(self.width(), 300))
            self.setMinimumSize(QtCore.QSize(0, 0))

    def maxWindowHeight(self):
        """ Calculate max height depending on the height of the screen.

        :return:
        :rtype:
        """

        pos = self.mapToGlobal(QtCore.QPoint(0, 0))

        try:
            # Qt5 approach
            screen = QtWidgets.QApplication.screenAt(pos)
            if screen:
                sceneGeometry = screen.geometry()
            else:
                # Fallback to desktop if screen not found
                desktop = QtWidgets.QApplication.desktop()
                sceneGeometry = desktop.screenGeometry(desktop.screenNumber(pos))
        except AttributeError:
            # Qt4 fallback
            desktop = QtWidgets.QApplication.desktop()
            sceneGeometry = desktop.screenGeometry(desktop.screenNumber(pos))

        relativePos = pos - QtCore.QPoint(sceneGeometry.left(), sceneGeometry.top())

        return sceneGeometry.height() - relativePos.y() - WINDOWHEIGHT_PADDING

    def setDockedWidgetHeight(self, height):
        self.setFixedHeight(height)

    def resizeEndEvent(self):
        """ Save the height for us to use
        :return:
        """
        self.resizedHeight = self.rect().height()

    def toggleToolset(self, toolsetId, activate=True, keepOpen=False):
        """ Toggle toolset

        :param toolsetId:
        :type toolsetId:
        :param activate:
        :type activate:
        :param keepOpen:
        :type keepOpen:
        :return:
        :rtype: toolsetwidgetitem.ToolsetWidgetItem
        """
        return self.toolsetFrame.toggleToolset(toolsetId, activate=activate, keepOpen=keepOpen)

    def openLastToolset(self):
        """ Open last toolset

        :return:
        :rtype:
        """
        size = len(self.toolsetFrame.tree.lastHidden)
        if size > 0:
            last = self.toolsetFrame.tree.lastHidden.pop()
            self.toggleToolset(last)
            logger.info("Opening toolset '{}'".format(last))
        else:
            logger.info("openLastToolset(): No toolsets to left to open")

    def closeEvent(self, ev):

        self.toolsetFrame.tree.closeEvent(ev)
        super(ToolsetsUI, self).closeEvent(ev)
        try:
            _TOOLSETUI_INSTANCES.remove(self)  # remove itself from the toolset ui instances
            _TOOLSETFRAME_INSTANCES.remove(self.toolsetFrame)
        except ValueError:
            pass

    def toolsetUis(self):
        """ Get all toolsetUi instances. Useful to use if can't import toolsetui.py

        :return:
        :rtype:
        """
        return toolsetUis()


class ToolsetTitleBar(TitleBar):

    def __init__(self, *args, **kwargs):
        """ The Toolset Title bar
        The toolset buttons are loaded here. Some drag drop events are also done here.
        If a toolset is dragged into the title bar it will create a new toolset, with the settings copied.

        :param args:
        :param kwargs:
        """

        super(ToolsetTitleBar, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.logoInactive = coreinterfaces.coreInterface().stylesheetSettingColour("$TOOLSET_LOGO_INACTIVE_COLOR")
        self.toolsetUi = self.zooWindow  # type: ToolsetsUI

    def setFramelessEnabled(self, action=None):
        """ Get the settings and transfer to new ZooToolset

        :param action:
        :return:
        """

        tree = self.toolsetUi.toolsetFrame.tree  # type: toolsettree.ToolsetTreeWidget

        activeItems = tree.activeItems()
        lastHidden = self.toolsetUi.lastHidden()
        lastTime = self.toolsetUi.lastFocusedTime

        newTool = super(ToolsetTitleBar, self).setFramelessEnabled(action)  # type: ToolsetsUI

        newTool.window().setUpdatesEnabled(False)

        for item in activeItems:
            toolsetId = item[0].id()
            newItem = None
            if item[1] == toolsettree.ToolsetTreeWidget.ActiveItem_Active:
                newItem = newTool.toggleToolset(toolsetId)
            elif item[1] == toolsettree.ToolsetTreeWidget.ActiveItem_InActive:
                newItem = newTool.toggleToolset(toolsetId, activate=False)

            # Send the new properties
            if newItem:
                newItem.setPropertiesData(item[0].widgetData())

        newTool.window().setUpdatesEnabled(True)

        newTool.setLastHidden(lastHidden)
        newTool.lastFocusedTime = lastTime

    def dropEvent(self, event):
        """ On dropping toolset on title bar

        :param event:
        :type event:
        :return:
        :rtype:
        """
        ret = None
        source = event.source()  # type: toolsettree.ToolsetTreeWidget

        if self.toolsetUi.toolsetFrame.tree is not source:
            mData = event.mimeData().data("dragData")
            data = cPickle.loads(six.binary_type(mData))
            properties = toolsetwidgetitem.itemData[data['itemInfos'][0].data]
            toolsetId = properties['toolsetId']

            sourceItem = source._toolsetFrame.toggleToolset(toolsetId)

            targetItem = self.toolsetUi.toolsetFrame.toggleToolset(toolsetId)
            targetItem.setPropertiesData(sourceItem.widgetData())

            ret = super(ToolsetTitleBar, self).dropEvent(event)
            utils.singleShotTimer(
                lambda x=source, source=sourceItem, target=targetItem: self.dropFinish(x, source, target))

        if ret is None:
            super(ToolsetTitleBar, self).dropEvent(event)

        return ret

    def dropFinish(self, source, sourceItem, targetItem):
        """ Drop finish.
        On drop finish it will tell the source tree and the target tree that the widget has been dropped.


        :param source:
        :type source: toolsettree.ToolsetTreeWidget
        :type targetItem: toolsetwidgetitem.ToolsetWidgetItem
        """
        source.toolsetFrame.toolsetUi.resizeWindow()
        source.toolsetFrame.updateColors()
        # Tell the source tree and the target tree that the widget has been dropped
        targetItem.widget.toolsetDropped.emit()
        sourceItem.widget.toolsetDropped.emit()

    def dragEnterEvent(self, event):
        """ Drag enter event.

        :param event:
        :return:
        """
        event.accept()

    def setLogoHighlight(self, highlight):
        """ Set the logo colour based on highlight

        :param highlight:
        :return:
        """
        if hasattr(self, "logoInactive") is False:
            return

        if not highlight:
            super(ToolsetTitleBar, self).setLogoHighlight(None)
        else:
            super(ToolsetTitleBar, self).setLogoHighlight(self.logoInactive)


def toolsetUis():
    """ Return all the toolset uis as a list

    :return:
    :rtype: list[ToolsetsUI]
    """

    global _TOOLSETUI_INSTANCES
    return _TOOLSETUI_INSTANCES


def toolsetFrames():
    """ All toolset frames

    :return:
    :rtype: list[:class:`ToolsetFrame`]
    """
    global _TOOLSETFRAME_INSTANCES
    return _TOOLSETFRAME_INSTANCES


def addToolsetUi(toolsetUi):
    """ Adds toolset ui to global list so we can use later

    :param toolsetUi:
    :type toolsetUi: :class:`ToolsetsUI`
    :return:
    :rtype:
    """
    _TOOLSETUI_INSTANCES.append(toolsetUi)
    addToolsetFrame(toolsetUi.toolsetFrame)


def addToolsetFrame(toolsetFrame):
    """ Add toolset frame so we can use later

    :param toolsetFrame:
    :type toolsetFrame: :class:`ToolsetFrame`
    :return:
    :rtype:
    """
    _TOOLSETFRAME_INSTANCES.append(toolsetFrame) if toolsetFrame not in _TOOLSETFRAME_INSTANCES else None


def toolsets(visibleOnly=False):
    """ All toolsets in toolset uis

    :return:
    :rtype: list[`toolsetwidgetitem.ToolsetWidgetItem`]
    """
    ret = []
    for frame in toolsetFrames():
        if visibleOnly:
            for t in frame.tree.toolsets():
                ret.append(t) if t.isVisible() else None
        else:
            ret += frame.tree.toolsets()

    return ret


def toolsetsByAttr(attr, visibleOnly=False):
    """ Retrieve the toolset if it has a specific attribute

    :param attr:
    :type attr:
    :return:
    :rtype: list[:class:`zoo.apps.toolsetsui.widgets.toolsetwidget.ToolsetWidgetBase`]
    """
    return [t for t in toolsets(visibleOnly=visibleOnly) if hasattr(t, attr)]


def toolsetsById(tid):
    """ Get toolsets with id

    :param tid:
    :type tid:
    :return:
    :rtype:
    """
    return [t for t in toolsets() if t.id == tid]


def getLastOpenedToolsetUi():
    """ Get last opened toolset UI.

    Return as a tool

    :return:
    """
    uis = toolsetUis()

    # Get the last visible toolset
    tool = None
    for t in uis:
        if t.isVisible():
            tool = t

    return tool


def getLastFocusedToolsetUi(includeMinimized=True):
    """ Get last focused toolset ui

    :return:
    """
    tool = None
    max = 0

    uis = toolsetUis()
    for t in uis:

        if t.lastFocusedTime > max:
            if (not includeMinimized and not t.isMinimized()) or includeMinimized:
                tool = t
                max = t.lastFocusedTime

    return tool


def runToolset(toolsetId, logWarning=True):
    """ Runs a toolset tool, and loads it to the active toolset window

    Returns False if no toolset window is open

    :param toolsetId: the name of the toolSet by it's type (unique string)
    :type toolsetId: string
    :return taskCompleted: did the tool load?
    :rtype taskCompleted: bool
    """
    tool = getLastFocusedToolsetUi(includeMinimized=False)
    if tool is not None:
        tool.toggleToolset(toolsetId)
        return True
    else:
        if logWarning:
            logger.warning("Toolset Not found")
        return False


def runLastClosedToolset():
    """ Run last closed toolset

    :return:
    """
    tool = getLastFocusedToolsetUi()  # type: ToolsetsUI
    if tool is not None:
        tool.openLastToolset()
    else:
        logger.warning("Toolset Not found")
