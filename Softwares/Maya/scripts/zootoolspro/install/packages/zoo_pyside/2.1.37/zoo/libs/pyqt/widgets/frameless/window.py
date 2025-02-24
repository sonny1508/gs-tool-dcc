from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets.frameless.resizers import WindowResizer
from zoo.libs.pyqt.widgets.frameless.containerwidgets import DockingContainer, FramelessWindow
from zoo.libs.pyqt.widgets.frameless.widgets import FramelessOverlay, TitleBar, WindowContents
from zoo.core.util import env
from zoovendor.Qt import QtWidgets, QtCore
from zoo.libs.pyqt.widgets import layouts
from zoo.preferences.interfaces import coreinterfaces

MINIMIZED_WIDTH = 390


class KeyboardModifierFilter(QtCore.QObject):
    modifierPressed = QtCore.Signal()
    windowEvent = QtCore.Signal(object)

    currentEvent = None

    def eventFilter(self, obj, event):
        self.currentEvent = event
        self.windowEvent.emit(event)

        if FramelessOverlay is None:
            self.deleteLater()
            return False

        if FramelessOverlay.isModifier():
            self.modifierPressed.emit()

        result = super(KeyboardModifierFilter, self).eventFilter(obj, event)
        if result is None:
            return False
        return result


class ZooWindow(QtWidgets.QWidget):
    closed = QtCore.Signal()
    beginClosing = QtCore.Signal()
    minimized = QtCore.Signal()
    # The web url to use when displaying the help documentation for this window.
    helpUrl = ""
    # window settings registry path ie. "zoo/toolsetsui"
    windowSettingsPath = ""
    # internal use only. Specifies the position key name used to store the window position.
    _windowsSettingsPosName = "pos"

    def _savedWindowPosition(self):
        """Returns the Window position settings path.

        .. note: Internal use only.

        :rtype: str
        """
        return "/".join((self.windowSettingsPath, self._windowsSettingsPosName))

    def __init__(self, name="", title="", parent=None, resizable=True,
                 width=None, height=None, modal=False, alwaysShowAllTitle=False,
                 minButton=False, maxButton=False, onTop=False, saveWindowPref=False,
                 titleBar=None, overlay=True, minimizeEnabled=True,
                 initPos=None, titleBarVisible=True):
        """ The frameless widget that will be subclassed by anything in zoo

        Will be attached to frameless widget or the docking container.

        :param name:
        :param title:
        :param parent:
        :param resizable:
        :param width:
        :param height:
        :param modal:
        :param alwaysShowAllTitle:
        :param minButton:
        :param maxButton:
        :param onTop:
        :param saveWindowPref:
        :param titleBar:
        :param overlay:
        :param minimizeEnabled:
        """
        super(ZooWindow, self).__init__(parent=None)
        self.setObjectName(name or title)
        # configure initial position based on the settings
        width, height = utils.dpiScale(width or 0), utils.dpiScale(height or 0)

        self._settings = QtCore.QSettings()
        self.titleBarVisible = titleBarVisible
        print("titleBarVisible", titleBarVisible)
        if self.windowSettingsPath:
            position = QtCore.QPoint(*(initPos or ()))
            initPos = position or self._settings.value(self._savedWindowPosition())

        self._initPos = initPos
        self._minimized = False
        if titleBar is not None:  # todo: Maybe can do better?
            self.titleBar = titleBar(self, alwaysShowAll=alwaysShowAllTitle)
        else:
            self.titleBar = TitleBar(self, alwaysShowAll=alwaysShowAllTitle)

        self._saveWindowPref = saveWindowPref
        self._parentContainer = None  # type: FramelessWindow or DockingContainer
        self._minimizeEnabled = minimizeEnabled

        self.name = name
        self.title = title
        self._onTop = onTop

        self._modal = modal
        self._parent = parent
        self._initWidth = width
        self._initHeight = height
        self.savedSize = QtCore.QSize()
        self._alwaysShowAllTitle = alwaysShowAllTitle
        self.filter = KeyboardModifierFilter()
        self._initUi()
        self.setTitle(title)
        self._connections()
        self.setResizable(resizable)
        self.overlay = None  # type: FramelessOverlay or None
        self.prevStyle = self.titleStyle()

        self._connectThemeUpdate()

        if overlay:
            self.overlay = FramelessOverlay(self, self.titleBar,
                                            topLeft=self.windowResizer.topLeftResize,
                                            topRight=self.windowResizer.topRightResize,
                                            botLeft=self.windowResizer.botLeftResize,
                                            botRight=self.windowResizer.botRightResize,
                                            resizable=resizable)
            self.overlay.widgetMousePress.connect(self.mousePressEvent)
            self.overlay.widgetMouseMove.connect(self.mouseMoveEvent)
            self.overlay.widgetMouseRelease.connect(self.mouseReleaseEvent)

        if not minButton:
            self.setMaxButtonVisible(False)

        if not maxButton:
            self.setMinButtonVisible(False)

        self.filter.modifierPressed.connect(self.showOverlay)
        self.installEventFilter(self.filter)

    @property
    def windowEvent(self):
        return self.filter.windowEvent

    def _connectThemeUpdate(self):
        try:
            coreInterface = coreinterfaces.coreInterface()
            coreInterface.themeUpdated.connect(self._updateTheme)
        except ImportError:
            pass

    def _updateTheme(self, event):
        self.setStyleSheet(event.stylesheet)

    def setDefaultStyleSheet(self):
        """Try to set the default stylesheet, if not, just ignore it

        :return:
        """
        try:

            coreInterface = coreinterfaces.coreInterface()
            result = coreInterface.stylesheet()
            self.setStyleSheet(result.data)
        except ImportError:
            pass

    @property
    def titleContentsLayout(self):
        return self.titleBar.contentsLayout

    @property
    def cornerLayout(self):
        return self.titleBar.cornerContentsLayout

    def showOverlay(self):
        """ Show overlay

        :return:
        """
        if self.overlay:
            self.overlay.show()

    def setOnTop(self, t):
        self.parentContainer.setOnTop(t)

    def move(self, *args, **kwargs):
        """ Move window, offset the resizers if they are visible

        :param args:
        :param kwargs:
        :return:
        """
        arg1 = args[0]

        if isinstance(arg1, QtCore.QPoint) and self.windowResizer.isVisible():
            arg1.setX(arg1.x() - self.resizerWidth() * 0.5)
            arg1.setY(arg1.y() - self.resizerHeight() * 0.5)
        self.parentContainer.move(*args, **kwargs)

    @classmethod
    def getZooWindow(cls, widget):
        """ Gets the zoo window based on the widget

        :param widget:
        :type widget: QtWidgets.QWidget
        :return:
        :rtype: ZooWindow
        """
        while widget is not None:
            if isinstance(widget.parentWidget(), ZooWindow):
                return widget.parentWidget()
            widget = widget.parentWidget()

    def _initFramelessLayout(self):
        """ Initialise the frameless layout

        :return:
        :rtype:
        """
        self.setLayout(self._framelessLayout)

        self.mainContents = WindowContents(self)
        self.titleBar.setTitleText(self.title)

        self._framelessLayout.setHorizontalSpacing(0)
        self._framelessLayout.setVerticalSpacing(0)
        self._framelessLayout.setContentsMargins(0, 0, 0, 0)

        self.titleBar.setVisible(self.titleBarVisible)
        self._framelessLayout.addWidget(self.titleBar, 1, 1, 1, 1)
        self._framelessLayout.addWidget(self.mainContents, 2, 1, 1, 1)

        self._framelessLayout.setColumnStretch(1, 1)  # Title column
        self._framelessLayout.setRowStretch(2, 1)  # Main contents row

    @property
    def docked(self):
        """ Docked signal

        :return:
        :rtype: QtCore.Signal
        """

        return self.titleBar.logoButton.docked

    @property
    def undocked(self):
        """ Undocked signal

        :return:
        :rtype: QtCore.Signal
        """
        return self.titleBar.logoButton.undocked

    def setMainLayout(self, layout):
        """ Set the main layout

        :param layout:
        :type layout:
        :return:
        :rtype:
        """
        self.mainContents.setLayout(layout)

    def mainLayout(self):
        """ Main Layout

        Will generate a vBoxLayout if it is empty.

        :return:
        :rtype:
        """
        if self.mainContents.layout() is None:
            self.mainContents.setLayout(layouts.vBoxLayout())

        return self.mainContents.layout()

    def _connections(self):
        self.docked.connect(self.dockEvent)
        self.undocked.connect(self.undockedEvent)
        self.titleBar.doubleClicked.connect(self.titleDoubleClicked)

    def titleDoubleClicked(self):
        """ Title double-clicked """
        if not self.isMinimized():
            self.minimize()
        else:
            self.maximize()

    def isMinimized(self):
        """ Window is minimized

        :return: 
        :rtype: bool
        """
        return self._minimized

    def setMinimizeEnabled(self, enabled):
        """

        :param enabled:
        :type enabled: bool
        """
        self._minimizeEnabled = enabled

    def dockEvent(self, container):
        """ Dock event

        :return:
        :rtype:
        """
        if self.isMinimized():
            self.setUiMinimized(False)

        self.setMovable(False)
        self.hideResizers()
        self._parentContainer = container

    def undockedEvent(self):
        """ Undocked event

        :return:
        :rtype:
        """
        self.showResizers()
        self.setMovable(True)

    def maximize(self):
        """ Maximize UI """
        self.setUiMinimized(False)

        # Use the resized height
        self.window().resize(self.savedSize)

    def minimize(self):
        """ Minimize UI """
        if not self._minimizeEnabled:
            return

        self.savedSize = self.window().size()
        self.setUiMinimized(True)
        utils.processUIEvents()
        utils.singleShotTimer(lambda: self.window().resize(utils.dpiScale(MINIMIZED_WIDTH), 0))

    def setUiMinimized(self, minimize):
        """ Resizes the spacing, icons and hides only. 
        It doesn't resize the window.


        :param minimize:
        :type minimize: bool
        """
        self._minimized = minimize

        if minimize:
            if not self._minimizeEnabled:
                return

            self.prevStyle = self.titleStyle()
            self.setTitleStyle(TitleBar.TitleStyle.Thin)
            self.mainContents.hide()
            self.titleBar.leftContents.hide()
            self.titleBar.rightContents.hide()
            self.minimized.emit()
        else:
            self.mainContents.show()
            self.setTitleStyle(self.prevStyle)
            self.titleBar.leftContents.show()
            self.titleBar.rightContents.show()

    def showResizers(self):
        """ Show resizers

        :return:
        :rtype:
        """
        self.windowResizer.show()

    def hideResizers(self):
        """ Hide resizers

        :return:
        :rtype:
        """
        self.windowResizer.hide()

    def hide(self):
        """ Hide the window """
        self.parentContainer.hide()
        return super(ZooWindow, self).hide()

    def show(self, move=None):
        """ Show the window """
        self.parentContainer.show()
        result = super(ZooWindow, self).show()
        if move:
            self.move(move)
        else:
            self._moveToInitPos()
        return result

    def setTitleStyle(self, style):
        """ Set title style

        :param style: TitleStyle.Default or TitleStyle.Thin
        :type style: 
        """
        self.titleBar.setTitleStyle(style)

    def titleStyle(self):
        """ Get title style

        :return:
        """
        return self.titleBar.titleStyle()

    def setLogoColor(self, color):
        self.titleBar.logoButton.setIconColor(color)

    def setMaxButtonVisible(self, vis):
        self.titleBar.setMaxButtonVisible(vis)

    def setMinButtonVisible(self, vis):
        self.titleBar.setMinButtonVisible(vis)

    def _initUi(self):
        """ Initialize the UI

        :return:
        :rtype:
        """

        self.attachFramelessWindow(saveWindowPref=self._saveWindowPref)  # Initialized attached to the frameless

        self._minimized = False
        self._framelessLayout = QtWidgets.QGridLayout()
        self._initFramelessLayout()
        self.windowResizer = WindowResizer(parent=self, installToLayout=self._framelessLayout)

        self.setDefaultStyleSheet()

    def centerToParent(self):
        """ Center widget to parent

        :return:
        """

        utils.updateWidgetSizes(self.parentContainer)
        size = self.rect().size()
        if self._parent:
            widgetCenter = utils.widgetCenter(self._parent)
            pos = self._parent.pos()
        else:
            widgetCenter = utils.currentScreenGeometry().center()
            pos = QtCore.QPoint(0, 0)

        self.parentContainer.move(widgetCenter +
                                  pos -
                                  QtCore.QPoint(size.width() / 2, size.height() / 3))


    def showWindow(self):
        self.parentContainer.show()

    def setName(self, name):
        """ Set the name of the widget

        :param name:
        :type name:
        :return:
        :rtype:
        """
        self.name = name

    def setTitle(self, text):
        """ Set the title text

        :param text:
        :type text:
        :return:
        :rtype:
        """
        self.titleBar.setTitleText(text)
        self.title = text

    @property
    def windowResizedFinished(self):
        return self.windowResizer.resizeFinished

    def setResizable(self, active):
        """ Window is resizable

        :param active:
        :type active:
        :return:
        :rtype:
        """
        self.windowResizer.setEnabled(active)

    def resizerHeight(self):
        """ Resizer height

        :return:
        :rtype:
        """
        return self.windowResizer.resizerHeight()

    def resizerWidth(self):
        """ Resizer Width

        :return:
        :rtype:
        """
        return self.windowResizer.resizerWidth()

    def attachFramelessWindow(self, show=False, saveWindowPref=True):
        """ Attach widget to frameless window

        :param show:
        :type show:
        :param saveWindowPref: Restores positions from saved settings
        :type saveWindowPref:
        :return:
        :rtype: FramelessWindow
        """
        self._parent = self._parent or parentWindow()

        self._parentContainer = FramelessWindow(self._parent,
                                                width=self._initWidth,
                                                height=self._initHeight,
                                                saveWindowPref=saveWindowPref,
                                                onTop=self._onTop)
        self._parentContainer.setWidget(self)
        if self._modal:
            self._parentContainer.setWindowModality(QtCore.Qt.ApplicationModal)

        if self._initPos:
            self._moveToInitPos()
        else:
            self.centerToParent()

        return self._parentContainer

    def resizeWindow(self, width=-1, height=-1):
        """

        :param width:
        :type width: float
        :param height:
        :type height: float

        :return:
        """
        if width == -1:
            width = self.width()
        if height == -1:
            height = self.height()

        width += self.resizerWidth() * 2
        height += self.resizerHeight() * 2

        super(ZooWindow, self).resize(width, height)

    def keyPressEvent(self, event):
        """ Key Press event


        :param event:
        :return:
        """

        if self.overlay and event.modifiers() == QtCore.Qt.AltModifier:
            self.overlay.show()

        return super(ZooWindow, self).keyPressEvent(event)

    @property
    def parentContainer(self):
        """

        :return:
        :rtype: :class:`FramelessWindow` or :class:`DockingContainer`
        """
        return self._parentContainer

    def isDocked(self):
        """

        :return:
        :rtype:
        """

        return self.parentContainer.isDockingContainer()

    def setMovable(self, movable):
        """ Movable through the titlebar

        :param movable:
        :type movable: bool
        :return:
        :rtype:
        """

        self.titleBar.setMoveEnabled(movable)

    def movable(self):
        return self.titleBar.moveEnabled()

    def close(self):
        """ Close window

        :return:
        :rtype:
        """
        self.hide()
        self.beginClosing.emit()  # Send begin closing event, usually reserved for hiding first before closing

        utils.processUIEvents()

        if not self.isDocked() and self.windowSettingsPath:
            self._settings.setValue(self._savedWindowPosition(), self.parentContainer.pos())

        super(ZooWindow, self).close()
        self.removeEventFilter(self.filter)

        self.closed.emit()

        self._parentContainer.close()

    def _moveToInitPos(self):
        """ Center widget to parent

        :return:
        """
        utils.updateWidgetSizes(self.parentContainer)
        self._initPos = utils.containWidgetInScreen(self, self._initPos)
        self.parentContainer.move(self._initPos)


class ZooWindowThin(ZooWindow):
    """ Same as ZooWindow with modified title style

    """

    def _initFramelessLayout(self):
        super(ZooWindowThin, self)._initFramelessLayout()
        self.setTitleStyle(TitleBar.TitleStyle.Thin)
        self.titleBar.setTitleAlign(QtCore.Qt.AlignCenter)


def parentWindow():
    """

    :return:
    :rtype: QtWidgets.QWidget
    """
    if env.isMaya():
        from zoo.libs.maya.qt import mayaui
        return mayaui.getMayaWindow()
    return None


def getZooWindows():
    """ Gets all frameless windows in the scene

    :return: All found window widgets under the Maya window
    """
    windows = []
    from zoo.libs.maya.qt import mayaui
    for child in mayaui.getMayaWindow().children():
        # if it has a zootoolsWindow property set, use that otherwise just use the child
        # w = child.property("zootoolsWindow") or child
        if isinstance(child, FramelessWindow):
            # windows.append(child.zooWindow)
            windows.append(child)

        # todo: add docked

    return windows
