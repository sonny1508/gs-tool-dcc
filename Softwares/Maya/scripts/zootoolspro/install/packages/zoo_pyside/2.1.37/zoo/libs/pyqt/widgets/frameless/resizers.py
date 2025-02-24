from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import utils


class ResizeDirection:
    """Flag attributes to tell what position the resizer is"""

    Left = 1
    Top = 2
    Right = 4
    Bottom = 8


class WindowResizer(QtCore.QObject):
    resizeFinished = QtCore.Signal()

    def __init__(self, parent, installToLayout=None, debug=False):
        """Window Resizer

        :param parent:
        :type parent:
        :param installToLayout:
        :type installToLayout:
        """
        super(WindowResizer, self).__init__(parent=parent)
        self.layout = None
        self._debug = debug
        self._isVisible = True
        self.installToLayout(installToLayout, parent)
        self.connections()

    def installToLayout(self, layout, parent):
        """

        :param layout:
        :type layout: Qt.QtWidgets.QGridLayout
        :return:
        :rtype:
        """
        if not isinstance(layout, QtWidgets.QGridLayout):
            raise TypeError(
                "Resizer requires a GridLayout instead of: {}".format(
                    layout.__class__.__name__
                )
            )

        self.layout = layout

        self.topResize = VerticalResize(ResizeDirection.Top, parent=parent)
        self.botResize = VerticalResize(ResizeDirection.Bottom, parent=parent)
        self.rightResize = HorizontalResize(ResizeDirection.Right, parent=parent)
        self.leftResize = HorizontalResize(ResizeDirection.Left, parent=parent)
        self.topLeftResize = CornerResize(
            ResizeDirection.Left | ResizeDirection.Top, parent=parent
        )
        self.topRightResize = CornerResize(
            ResizeDirection.Right | ResizeDirection.Top, parent=parent
        )
        self.botLeftResize = CornerResize(
            ResizeDirection.Left | ResizeDirection.Bottom, parent=parent
        )
        self.botRightResize = CornerResize(
            ResizeDirection.Right | ResizeDirection.Bottom, parent=parent
        )
        # Corner Resizer's
        self.resizers = (
            self.topResize,
            self.topRightResize,
            self.rightResize,
            self.botRightResize,
            self.botResize,
            self.botLeftResize,
            self.leftResize,
            self.topLeftResize,
        )

        self.horizontalResizers = (self.leftResize, self.rightResize)
        self.verticalResizers = (self.topResize, self.botResize)
        self.cornerResizers = (
            self.topLeftResize,
            self.topRightResize,
            self.botLeftResize,
            self.botRightResize,
        )

        layout.addWidget(self.topLeftResize, 0, 0, 1, 1)
        layout.addWidget(self.topResize, 0, 1, 1, 1)
        layout.addWidget(self.topRightResize, 0, 2, 1, 1)

        layout.addWidget(self.leftResize, 1, 0, 2, 1)
        layout.addWidget(self.rightResize, 1, 2, 2, 1)

        layout.addWidget(self.botLeftResize, 3, 0, 1, 1)
        layout.addWidget(self.botResize, 3, 1, 1, 1)
        layout.addWidget(self.botRightResize, 3, 2, 1, 1)

    def hide(self):
        """Hide the resizers

        :return:
        :rtype:
        """
        self._isVisible = False
        for r in self.resizers:
            r.hide()

    def show(self):
        """Show the resizers

        :return:
        :rtype:
        """
        self._isVisible = True
        for r in self.resizers:
            r.show()

    def isVisible(self):
        """Returns true if resizers are visible, false otherwise

        :return:
        """
        return self._isVisible

    def connections(self):
        """Connections

        :return:
        :rtype:
        """
        for r in self.resizers:
            r.windowResizedFinished.connect(self.resizeFinished.emit)

    def resizerWidth(self):
        """Calculates the total width of the vertical resizers"""
        resizers = [self.leftResize, self.rightResize]
        ret = 0
        for r in resizers:
            if not r.isHidden():
                ret += r.minimumSize().width()

        return ret

    def setResizerActive(self, active):
        """Enable or disable the resizers

        :param active:
        """

        if active:
            self.show()
        else:
            self.hide()

    def resizerHeight(self):
        """Calculates the total height of the vertical resizers"""
        resizers = [self.topResize, self.botResize]
        ret = 0
        for r in resizers:
            if not r.isHidden():
                ret += r.minimumSize().height()

        return ret

    def setEnabled(self, enabled):
        """Set resizers enabled

        :param enabled:
        :type enabled:
        :return:
        :rtype:
        """
        [r.setEnabled(enabled) for r in self.resizers]


class ResizeBase(QtWidgets.QFrame):
    """
    The resize widgets for the sides of the windows and the corners to resize the parent window.

    """

    windowResized = QtCore.Signal()
    windowResizeStartEvent = QtCore.Signal()
    windowResizedFinished = QtCore.Signal()

    def __init__(self, direction, parent, debug=False):
        super(ResizeBase, self).__init__(parent=parent)

        self.direction = direction  # type: int
        self.widgetMousePos = None  # type: QtCore.QPoint
        self.widgetGeometry = None  # type: QtCore.QRect
        if not debug:
            self.setStyleSheet("background-color: transparent;")
        else:
            self.setStyleSheet("background-color: #88990000;")

        self.setResizeDirection(direction)

        self.windowResized.connect(self.windowResizeEvent)
        self.windowResizeStartEvent.connect(self.windowResizeStart)

    def paintEvent(self, event):
        """Mouse events seem to deactivate when its completely transparent. Hacky way to avoid that for now.

        :type event: :class:`QtCore.QEvent`
        """

        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(255, 0, 0, 0))
        painter.end()

    def windowResizeStart(self):
        self.widgetMousePos = self.mapFromGlobal(QtGui.QCursor.pos())
        self.widgetGeometry = self.window().frameGeometry()

    def mousePressEvent(self, event):
        self.windowResizeStartEvent.emit()

    def mouseMoveEvent(self, event):
        if self.widgetGeometry is not None:
            self.windowResized.emit()
        else:
            super(ResizeBase, self).mouseMoveEvent(event)

    def windowResizeEvent(self):
        """Resize based on the mouse position and the current direction"""
        pos = QtGui.QCursor.pos()
        newGeometry = self.window().frameGeometry()
        minSize = self.window().minimumSize()
        # Minimum Size
        mW = minSize.width()
        mH = minSize.height()

        # Check to see if the ResizeDirection flag is in self.direction
        if self.direction & ResizeDirection.Left == ResizeDirection.Left:
            left = newGeometry.left()
            newGeometry.setLeft(pos.x() - self.widgetMousePos.x())
            if newGeometry.width() <= mW:  # Revert back if too small
                newGeometry.setLeft(left)
        if self.direction & ResizeDirection.Top == ResizeDirection.Top:
            top = newGeometry.top()
            newGeometry.setTop(pos.y() - self.widgetMousePos.y())
            if newGeometry.height() <= mH:  # Revert back if too small
                newGeometry.setTop(top)
        if self.direction & ResizeDirection.Right == ResizeDirection.Right:
            newGeometry.setRight(
                pos.x() + (self.minimumSize().width() - self.widgetMousePos.x())
            )
        if self.direction & ResizeDirection.Bottom == ResizeDirection.Bottom:
            newGeometry.setBottom(
                pos.y() + (self.minimumSize().height() - self.widgetMousePos.y())
            )

        # Set new sizes
        x = newGeometry.x()
        y = newGeometry.y()
        w = max(newGeometry.width(), mW)  # Minimum Width
        h = max(newGeometry.height(), mH)  # Minimum height

        self.window().setGeometry(x, y, w, h)

    def setResizeDirection(self, direction):
        """Set the resize direction. Expects an int from ResizeDirection

        .. code-block:: python

            setResizeDirection(ResizeDirection.Left | ResizeDirection.Top)

        :param direction: ResizeDirection
        :type direction: int
        """
        self.direction = direction

    def mouseReleaseEvent(self, event):
        self.windowResizedFinished.emit()
        # resets to attached geometry so we don't activate resize on a mouse move with a click
        self.widgetGeometry = None


class CornerResize(ResizeBase):
    """Resizer's in the corner of the window"""

    def __init__(self, direction, parent=None):
        super(CornerResize, self).__init__(direction, parent=parent)
        self.setFixedSize(utils.sizeByDpi(QtCore.QSize(10, 10)))

    def setResizeDirection(self, direction):
        super(CornerResize, self).setResizeDirection(direction)
        # Top Left or Bottom Right
        if (
            direction == ResizeDirection.Left | ResizeDirection.Top
            or direction == ResizeDirection.Right | ResizeDirection.Bottom
        ):
            self.setCursor(QtCore.Qt.SizeFDiagCursor)

            # Top Right or Bottom Left
        elif (
            direction == ResizeDirection.Right | ResizeDirection.Top
            or direction == ResizeDirection.Left | ResizeDirection.Bottom
        ):
            self.setCursor(QtCore.Qt.SizeBDiagCursor)


class VerticalResize(ResizeBase):
    """Resizer's for the top, bottom,left and right of the window"""

    def __init__(self, direction=QtCore.Qt.SizeVerCursor, parent=None):
        super(VerticalResize, self).__init__(direction, parent=parent)

        self.setFixedHeight(utils.dpiScale(8))

    def setResizeDirection(self, direction):
        self.setCursor(QtCore.Qt.SizeVerCursor)


class HorizontalResize(ResizeBase):
    """Resizer's for the left and right of the window"""

    def __init__(self, direction=QtCore.Qt.SizeHorCursor, parent=None):
        super(HorizontalResize, self).__init__(direction, parent=parent)
        self.setFixedWidth(utils.dpiScale(8))

    def setResizeDirection(self, direction):
        self.setCursor(QtCore.Qt.SizeHorCursor)
