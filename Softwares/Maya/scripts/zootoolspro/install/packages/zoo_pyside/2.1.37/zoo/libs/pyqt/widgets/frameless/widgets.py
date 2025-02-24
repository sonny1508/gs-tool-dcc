import webbrowser
from zoo.libs.pyqt.widgets.frameless.resizers import CornerResize, ResizeDirection
from zoo.libs.utils import output
from zoovendor.Qt import QtCore, QtWidgets, QtGui
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.extended.clippedlabel import ClippedLabel
from zoo.libs.pyqt.widgets import layouts, buttons, overlay
from zoo.libs.pyqt.widgets.frameless.containerwidgets import SpawnerIcon
from zoo.preferences.interfaces import coreinterfaces
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)
MODIFIER = QtCore.Qt.AltModifier


class TitleBar(QtWidgets.QFrame):
    doubleClicked = QtCore.Signal()
    moving = QtCore.Signal(object, object)

    class TitleStyle:
        Default = "DEFAULT"
        Thin = "THIN"

    def __init__(self, parent=None, showTitle=True, alwaysShowAll=False):
        """ Title bar of the frameless window. 

        Click drag this widget to move the window widget

        :param parent:
        :type parent: zoo.libs.pyqt.widgets.window.ZooWindow
        """
        super(TitleBar, self).__init__(parent=parent)

        self.titleBarHeight = 40
        self.pressedAt = None
        self.leftContents = QtWidgets.QFrame(self)
        # self.titleWidget = QtWidgets.QWidget(self)
        self._mainLayout = layouts.hBoxLayout(self)
        self.rightContents = QtWidgets.QWidget(self)

        self._mainRightLayout = layouts.hBoxLayout()
        self.contentsLayout = layouts.hBoxLayout()
        self.cornerContentsLayout = layouts.hBoxLayout()
        self.titleLayout = layouts.hBoxLayout()
        self._titleStyle = self.TitleStyle.Default

        self.zooWindow = parent
        self.mousePos = None  # type: QtCore.QPoint
        self.widgetMousePos = None  # type: QtCore.QPoint
        self.themePref = coreinterfaces.coreInterface()

        # Title bar buttons
        self.logoButton = SpawnerIcon(zooWindow=parent, parent=self)

        self.windowButtonsLayout = layouts.hBoxLayout()

        self.toggle = True

        self.iconSize = 13 # note: iconSize gets dpiScaled in internally
        self.closeButton = buttons.ExtendedButton(parent=self, themeUpdates=False)
        self.minimizeButton = buttons.ExtendedButton(parent=self, themeUpdates=False)
        self.maxButton = buttons.ExtendedButton(parent=self, themeUpdates=False)
        self.helpButton = buttons.ExtendedButton(parent=self, themeUpdates=False)
        self.titleLabel = TitleLabel(parent=self, alwaysShowAll=alwaysShowAll)
        self._splitLayout = layouts.hBoxLayout()
        self._moveEnabled = True

        if not showTitle:
            self.titleLabel.hide()

        self.initUi()
        self.connections()

    def setDebugColors(self, debug):
        if debug:
            self.leftContents.setStyleSheet("background-color: green")
            self.titleLabel.setStyleSheet("background-color: red")
            self.rightContents.setStyleSheet("background-color: blue")
        else:
            self.leftContents.setStyleSheet("")
            self.titleLabel.setStyleSheet("")
            self.rightContents.setStyleSheet("")

    def initUi(self):
        """ Init UI """

        self.setFixedHeight(utils.dpiScale(self.titleBarHeight))

        col = self.themePref.FRAMELESS_TITLELABEL_COLOR
        self.closeButton.setIconByName("xMark", colors=col, size=self.iconSize, colorOffset=80)
        self.minimizeButton.setIconByName("minus", colors=col, size=self.iconSize, colorOffset=80)
        self.maxButton.setIconByName("checkbox", colors=col, size=self.iconSize, colorOffset=80)
        toolTip = "Open the help URL for this window."
        if self.zooWindow.helpUrl:
            toolTip = "{} \n{}  ".format(toolTip, self.zooWindow.helpUrl)
        self.helpButton.setIconByName("help", colors=col, size=self.iconSize, colorOffset=80)
        self.helpButton.setToolTip(toolTip)
        self.setLayout(self._mainLayout)

        # _mainLayout: The whole titlebar main layout

        # Button Settings
        btns = [self.helpButton, self.closeButton, self.minimizeButton, self.maxButton]
        for b in btns:
            b.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            b.setDoubleClickEnabled(False)

        ''' The widget layout is laid out into the following:
        
        _mainLayout
            logoButton
            _mainRightLayout
                _splitLayout
                    leftContents
                    titleLayoutWgt -> titleLayout
                    rightContents   
                
                windowButtonsLayout
                    helpButton
                    minimizeButton
                    maxButton
                    closeButton
        '''

        # Layout setup
        self._mainRightLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 6, 0))
        self.contentsLayout.setContentsMargins(0, 0, 0, 0)
        self.cornerContentsLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        self.rightContents.setLayout(self.cornerContentsLayout)

        # Window buttons (Min, Max, Close button)
        self.windowButtonsLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 0, 0))
        self.windowButtonsLayout.addWidget(self.helpButton)
        self.windowButtonsLayout.addWidget(self.minimizeButton)
        self.windowButtonsLayout.addWidget(self.maxButton)
        self.windowButtonsLayout.addWidget(self.closeButton)

        # Split Layout
        self._splitLayout.addWidget(self.leftContents)
        self._splitLayout.addLayout(self.titleLayout, 1)
        self._splitLayout.addWidget(self.rightContents)

        # Title Layout
        self.leftContents.setLayout(self.contentsLayout)
        self.contentsLayout.setSpacing(0)
        self.titleLayout.addWidget(self.titleLabel)
        self.titleLayout.setSpacing(0)
        self.titleLayout.setContentsMargins(*utils.marginsDpiScale(0, 8, 0, 7))
        self.titleLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.titleLabel.setMinimumWidth(1)

        # The main title layout (Logo | Main Right Layout)
        self._mainLayout.setContentsMargins(*utils.marginsDpiScale(4, 0, 0, 0))
        self._mainLayout.setSpacing(0)
        self.spacingItem = QtWidgets.QSpacerItem(8, 8)
        self.spacingItem2 = QtWidgets.QSpacerItem(6, 6)

        self._mainLayout.addSpacerItem(self.spacingItem)
        self._mainLayout.addWidget(self.logoButton)
        self._mainLayout.addSpacerItem(self.spacingItem2)
        self._mainLayout.addLayout(self._mainRightLayout)

        # The Main right layout (Title, Window buttons)
        self._mainRightLayout.addLayout(self._splitLayout)
        # self._mainRightLayout.addWidget(self.rightContents)
        self._mainRightLayout.addLayout(self.windowButtonsLayout)
        self._mainRightLayout.setAlignment(QtCore.Qt.AlignVCenter)
        self.windowButtonsLayout.setAlignment(QtCore.Qt.AlignVCenter)

        # Left right margins have to be zero otherwise the title toolbar will flicker (eg toolsets)
        self._mainRightLayout.setStretch(0, 1)
        QtCore.QTimer.singleShot(0, self.refreshTitleBar)
        self.setTitleSpacing(False)

        if not self.zooWindow.helpUrl:
            self.helpButton.hide()

    def setTitleSpacing(self, spacing):
        """

        :param spacing:
        :return:
        """
        if spacing:
            self.spacingItem.changeSize(8, 8)
            self.spacingItem2.changeSize(6, 6)
        else:
            self.spacingItem.changeSize(0, 0)
            self.spacingItem2.changeSize(0, 0)
            self._splitLayout.setSpacing(0)

    def setTitleAlign(self, align):
        """ Set Title Align

        :param align:
        :type align:
        """
        if align == QtCore.Qt.AlignCenter:
            self._splitLayout.setStretch(1, 0)
        else:
            self._splitLayout.setStretch(1, 1)

    def setDockable(self, dockable):
        if dockable:
            pass

    def setMoveEnabled(self, enabled):
        """ Window moving enabled

        :param enabled:
        :type enabled:
        :return:
        :rtype:
        """
        self._moveEnabled = enabled

    def setTitleStyle(self, style):
        """ Set the title style

        :param style:
        :type style: TitleStyle
        :return: TitleStyle.Default or TitleStyle.Thin
        :rtype:
        """
        self._titleStyle = style

        if style == self.TitleStyle.Default:
            utils.setStylesheetObjectName(self.titleLabel, "")
            self.setFixedHeight(utils.dpiScale(self.titleBarHeight))

            self.titleLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 0, 7))
            self._mainRightLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 6, 0))
            self.logoButton.setIconSize(QtCore.QSize(24, 24))
            self.logoButton.setFixedSize(QtCore.QSize(30, 24))
            self.minimizeButton.setFixedSize(QtCore.QSize(28, 24))
            self.maxButton.setFixedSize(QtCore.QSize(28, 24))
            self.maxButton.setIconSize(QtCore.QSize(24, 24))
            self.closeButton.setFixedSize(QtCore.QSize(28, 24))
            self.closeButton.setIconSize(QtCore.QSize(16, 16))
            if self.zooWindow.helpUrl:
                self.helpButton.show()

            self.windowButtonsLayout.setSpacing(utils.dpiScale(6))

        elif style == self.TitleStyle.Thin:

            self.logoButton.setIconSize(QtCore.QSize(12, 12))
            self.logoButton.setFixedSize(QtCore.QSize(10, 12))
            self.minimizeButton.setFixedSize(QtCore.QSize(10, 18))
            self.maxButton.setFixedSize(QtCore.QSize(10, 18))
            self.maxButton.setIconSize(QtCore.QSize(12, 12))
            self.closeButton.setFixedSize(QtCore.QSize(10, 18))
            self.closeButton.setIconSize(QtCore.QSize(12, 12))
            self.setFixedHeight(utils.dpiScale(int(self.titleBarHeight / 2)))
            self.titleLabel.setFixedHeight(utils.dpiScale(20))
            self.windowButtonsLayout.setSpacing(utils.dpiScale(6))
            self.helpButton.hide()

            utils.setStylesheetObjectName(self.titleLabel, "Minimized")

            self.titleLayout.setContentsMargins(*utils.marginsDpiScale(0, 3, 15, 7))
            self._mainRightLayout.setContentsMargins(*utils.marginsDpiScale(0, 0, 6, 0))
        else:
            output.displayError("'{}' style doesn't exist for {}.".format(style, self.zooWindow.__class__.__name__))

    def moveEnabled(self):
        """ If the titlebar can drive movement.

        :return:
        :rtype:
        """
        return self._moveEnabled

    def setMaxButtonVisible(self, vis):
        """ Set max button visible

        :param vis:
        :type vis:
        :return:
        :rtype:
        """
        self.maxButton.setVisible(vis)

    def setMinButtonVisible(self, vis):
        """ Set Minimize button visible

        :param vis:
        :type vis:
        :return:
        :rtype:
        """
        self.minimizeButton.setVisible(vis)

    def titleStyle(self):
        """ Return the title style

        :return:
        :rtype:
        """
        return self._titleStyle

    def mouseDoubleClickEvent(self, event):
        """ Mouse double clicked event

        :param event:
        :type event: :class:`QtGui.QMouseEvent`
        :return:
        :rtype:
        """
        super(TitleBar, self).mouseDoubleClickEvent(event)
        self.doubleClicked.emit()

    def setLogoHighlight(self, highlight):
        """ Set logo highlight.

        Highlight the logo

        :param highlight:
        :type highlight:
        :return:
        :rtype:
        """
        self.logoButton.setLogoHighlight(highlight)

    def refreshTitleBar(self):
        """ Workaround for mainLayout not showing

        :return:
        """
        QtWidgets.QApplication.processEvents()
        self.updateGeometry()
        self.update()

    def setTitleClosesFirst(self, closeFirst):
        """ Enabled means the title will disappear first after resizing if the width is too small

        If its disabled, the contentsLayout will resize at the same speed as the titleLayout

        :param closeFirst:
        :return:
        """
        widgets = []
        firstWgt = self._splitLayout.itemAt(0).widget()

        # Use Splitter
        if closeFirst is True and not isinstance(firstWgt, TitleSplitter):
            widgets.append(self._splitLayout.takeAt(0).widget())

            for i in range(self._splitLayout.count()):
                widgets.append(self._splitLayout.takeAt(0).widget())

            split = TitleSplitter()

            for w in widgets:
                split.addWidget(w)

            self._splitLayout.addWidget(split)

        # Use Layout
        elif closeFirst is False and isinstance(firstWgt, TitleSplitter):
            split = firstWgt  # type: QtWidgets.QSplitter

            for i in range(split.count()):
                wgt = split.widget(i)
                if wgt is None:
                    continue

                self._splitLayout.addWidget(wgt)

    def setTitleText(self, value=""):
        """ The text of the title bar in the window

        :param value:
        :type value:
        :return:
        :rtype:
        """
        self.titleLabel.setText(value.upper())

    def connections(self):
        """

        :return:
        """
        self.closeButton.leftClicked.connect(self.closeWindow)
        self.minimizeButton.leftClicked.connect(self._onMinimizeButtonClicked)
        self.maxButton.leftClicked.connect(self._onMaximizeButtonClicked)
        self.helpButton.leftClicked.connect(self.openHelp)

    def openHelp(self):
        """ Open help url

        :return:
        """
        webbrowser.open(self.zooWindow.helpUrl)

    def closeWindow(self):
        """ Close the window.

        :return:
        :rtype:
        """
        self.zooWindow.close()

    def setWindowIconSize(self, size):
        """
        Sets the icon size of the titlebar icons
        :param size:
        :return:
        """
        self.iconSize = size

    def setMaximiseVisible(self, show=True):
        """Set Maximise button visible

        :param show:
        """
        if show:
            self.maxButton.show()
        else:
            self.maxButton.hide()

    def setMinimiseVisible(self, show=True):
        """Set minimize button visibility

        :param show:
        """
        if show:
            self.minimizeButton.show()
        else:
            self.minimizeButton.hide()

    def toggleContents(self):
        """Show or hide the additional contents in the titlebar
        """
        if self.contentsLayout.count() > 0:
            for i in range(1, self.contentsLayout.count()):
                widget = self.contentsLayout.itemAt(i).widget()
                if widget.isHidden():
                    widget.show()
                else:
                    widget.hide()

    def mousePressEvent(self, event):
        """Mouse click event to start the moving of the window

        :type event: :class:`QtGui.QMouseEvent`
        """
        if event.buttons() & QtCore.Qt.LeftButton:
            self.startMove()

        event.ignore()

    def mouseReleaseEvent(self, event):
        """Mouse release for title bar

        :type event: :class:`QtGui.QMouseEvent`
        """
        self.endMove()

    def startMove(self):
        if self._moveEnabled:
            self.widgetMousePos = self.zooWindow.mapFromGlobal(QtGui.QCursor.pos())

    def endMove(self):
        if self._moveEnabled:
            self.widgetMousePos = None

    def mouseMoveEvent(self, event):
        """Move the window based on if the titlebar has been clicked or not

        :type event: :class:`QtGui.QMouseEvent`
        """
        if self.widgetMousePos is None or not self._moveEnabled:
            return

        pos = QtGui.QCursor.pos()
        newPos = pos

        newPos.setX(pos.x() - self.widgetMousePos.x())
        newPos.setY(pos.y() - self.widgetMousePos.y())
        delta = newPos - self.window().pos()
        self.moving.emit(newPos, delta)

        self.window().move(newPos)

    def _onMinimizeButtonClicked(self):
        self.zooWindow.minimize()

    def _onMaximizeButtonClicked(self):
        self.zooWindow.maximize()


class TitleSplitter(QtWidgets.QSplitter):

    def __init__(self):
        """ Splitter to make sure the right widget closes before the left.

        Used for title to hide the TitleLabel first before hiding the title contents layout

        """
        super(TitleSplitter, self).__init__()
        self.setHandleWidth(0)

    def resizeEvent(self, event):
        """ Makes sure the right widget closes first by keeping the left most widget size constant

        :param event:
        :return:
        """

        if self.count() > 1:
            w = self.widget(0).sizeHint().width()
            self.setSizes([w, self.width() - w])
        return super(TitleSplitter, self).resizeEvent(event)

    def addWidget(self, *args, **kwargs):
        """ Hides the handles on widget add

        :param args:
        :param kwargs:
        :return:
        """
        super(TitleSplitter, self).addWidget(*args, **kwargs)
        self.hideHandles()

    def hideHandles(self):
        """ Hides the handles and disable them

        :return:
        """
        for i in range(self.count()):
            handle = self.handle(i)
            handle.setEnabled(False)
            handle.setCursor(QtCore.Qt.ArrowCursor)
            handle.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)


class FramelessOverlay(overlay.OverlayWidget):
    MOVEBUTTON = QtCore.Qt.MiddleButton
    RESIZEBUTTON = QtCore.Qt.RightButton

    def __init__(self, parent, titleBar, topLeft=None, topRight=None,
                 botLeft=None, botRight=None, resizable=True):
        """ Handles linux like window movement.

        Eg Alt-Middle click to move entire window
        Alt Left Click corner to resize

        """
        super(FramelessOverlay, self).__init__(parent=parent)
        self.resizable = resizable

        # self.setProperty("saveWindowPref", True)
        self.titleBar = titleBar

        self.topLeft = topLeft  # type: CornerResize
        self.topRight = topRight  # type: CornerResize
        self.botLeft = botLeft  # type: CornerResize
        self.botRight = botRight  # type: CornerResize

        self.resizeDir = 0

    def mousePressEvent(self, event):
        """ Alt-Middle click to move window

        :param event:
        :return:
        """
        self.pressedAt = QtGui.QCursor.pos()

        if not self.isEnabled():
            event.ignore()
            super(FramelessOverlay, self).mousePressEvent(event)
            return

        if self.isModifier() and event.buttons() & self.MOVEBUTTON:
            self.titleBar.startMove()
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)

        if self.isModifier() and event.buttons() & self.RESIZEBUTTON and self.resizable:
            self.resizeDir = self.quadrant()

            if self.resizeDir == ResizeDirection.Top | ResizeDirection.Right:
                self.topRight.windowResizeStart()
                self.setCursor(QtCore.Qt.CursorShape.SizeBDiagCursor)
            elif self.resizeDir == ResizeDirection.Top | ResizeDirection.Left:
                self.topLeft.windowResizeStart()
                self.setCursor(QtCore.Qt.CursorShape.SizeFDiagCursor)
            elif self.resizeDir == ResizeDirection.Bottom | ResizeDirection.Left:
                self.botLeft.windowResizeStart()
                self.setCursor(QtCore.Qt.CursorShape.SizeBDiagCursor)
            elif self.resizeDir == ResizeDirection.Bottom | ResizeDirection.Right:
                self.botRight.windowResizeStart()
                self.setCursor(QtCore.Qt.CursorShape.SizeFDiagCursor)

        if (not self.isModifier() and event.buttons() & self.MOVEBUTTON) or \
                (not self.isModifier() and event.buttons() & self.RESIZEBUTTON):
            self.hide()

        event.ignore()
        return super(FramelessOverlay, self).mousePressEvent(event)

    @classmethod
    def isModifier(cls):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        # return modifiers == QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier
        return modifiers == MODIFIER

    def mouseReleaseEvent(self, event):

        if not self.isEnabled():
            event.ignore()
            super(FramelessOverlay, self).mouseReleaseEvent(event)
            return

        self.titleBar.endMove()
        self.topLeft.windowResizedFinished.emit()
        self.topRight.windowResizedFinished.emit()
        self.botLeft.windowResizedFinished.emit()
        self.botRight.windowResizedFinished.emit()
        self.resizeDir = 0
        event.ignore()

        # If there is no difference in position at all, let the mouse click through
        if self.pressedAt - QtGui.QCursor.pos() == QtCore.QPoint(0, 0):
            utils.clickUnder(QtGui.QCursor.pos(), 1, modifier=MODIFIER)
            # self.hide()

        super(FramelessOverlay, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """ 

        :param event:
        :type event:
        """
        if not self.isEnabled():
            event.ignore()
            super(FramelessOverlay, self).mouseMoveEvent(event)
            return

        if not self.isModifier():
            self.hide()
            return

        self.titleBar.mouseMoveEvent(event)

        if self.resizeDir != 0:
            if self.resizeDir == ResizeDirection.Top | ResizeDirection.Right:
                self.topRight.windowResized.emit()
            elif self.resizeDir == ResizeDirection.Top | ResizeDirection.Left:
                self.topLeft.windowResized.emit()
            elif self.resizeDir == ResizeDirection.Bottom | ResizeDirection.Left:
                self.botLeft.windowResized.emit()
            elif self.resizeDir == ResizeDirection.Bottom | ResizeDirection.Right:
                self.botRight.windowResized.emit()

        event.ignore()

        super(FramelessOverlay, self).mouseMoveEvent(event)

    def quadrant(self):
        """ Get the quadrant of where the mouse is pointed, and return the direction

        :return: The direction ResizeDirection
        :rtype: ResizeDirection
        """
        midX = self.geometry().width() / 2
        midY = self.geometry().height() / 2
        ret = 0

        pos = self.mapFromGlobal(QtGui.QCursor.pos())

        if pos.x() < midX:
            ret = ret | ResizeDirection.Left
        elif pos.x() > midX:
            ret = ret | ResizeDirection.Right

        if pos.y() < midY:
            ret = ret | ResizeDirection.Top
        elif pos.y() > midY:
            ret = ret | ResizeDirection.Bottom

        return ret

    def show(self):
        self.updateStyleSheet()
        if self.isEnabled():
            super(FramelessOverlay, self).show()
        else:
            logger.warning("FramelessOverlay.show() was called when it is disabled")

    def setEnabled(self, enabled):
        self.setDebugMode(not enabled)
        self.setVisible(enabled)
        super(FramelessOverlay, self).setEnabled(enabled)

    def updateStyleSheet(self):
        """ Set style sheet

        :return:
        """
        self.setDebugMode(self._debug)


class WindowContents(QtWidgets.QFrame):
    """ For CSS purposes """


class TitleLabel(ClippedLabel):
    """ For CSS purposes """

    def __init__(self, *args, **kwargs):
        super(TitleLabel, self).__init__(*args, **kwargs)
        self.setAlignment(QtCore.Qt.AlignRight)
