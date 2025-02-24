from collections import namedtuple

from zoo.libs.pyqt import utils
from zoovendor.Qt import QtCore

MouseSlideEvent = namedtuple('MouseScrollEvent', 'value,direction,x,y,dx,dy,index,modifiers')


class VirtualSlider(QtCore.QObject):
    """ MouseScroller is a slider for thumbnail viewer items.

    Currently it is coupled with the thumbnail viewer, but it should be possible to change the code a bit to work
    with any widget.

    Direction can be Horizontal, Vertical, DirectionClamp or Both.
     - `Horizontal` will only scroll horizontally.
     - `Vertical` will only scroll vertically.
     - `DirectionClamp` can scroll horizontally OR vertically. It will be detected based on mouse direction.
     - `Both` can scroll both horizontally and vertically. It will return two values in the 'value' a x,y value.

    Speed is how much the value will go up or down per tick. For instance every tick it will go up 0.1 if speed is 0.1.

    Speed is the default speed, however this can be overridden for the X and Y values with speedX, speedY value.

    Slow speed is the speed of the value when the slow keyboard modifier is pressed. Default is 'ctrl'
    Fast speed is the speed of the value when the fast keyboard modifier is pressed. Default is 'shift'

    pixelRange is the range where the mouse can move. For instance x,y will stick between -pixelRange and pixelRange.

    To Install, run the functions in their respective events:

    .. code-block:: python

        def mousePressEvent(self, event):
            self.mouseSlider.mousePressed(event)

        def mouseMoveEvent(self, event):

            moving = self.mouseScroller.mouseMoved(event)

            if not moving:
                return super(ThumbnailWidget, self).mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):
            self.mouseSlider.mouseMoved(event)


    :param directions:  Can be VirtualSlider.DirectionClamp, VirtualSlider.Horizontal, VirtualSlider.Vertical, VirtualSlider.Both
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
    :param threshold: The approximate mouse distance before detecting horizontal or vertical
    :type threshold: int
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
    """

    scrolled = QtCore.Signal(MouseSlideEvent)
    pressed = QtCore.Signal()
    released = QtCore.Signal(MouseSlideEvent)
    DirectionClamp = 1
    Horizontal = 2
    Vertical = 3
    Both = 4

    def __init__(self, parent, directions=DirectionClamp,
                 minValue=None, maxValue=None,
                 numType=float, step=10, pixelRange=None,
                 slowSpeed=0.01, speed=0.1, fastSpeed=1,
                 slowSpeedXY=(None, None), speedXY=(None, None), fastSpeedXY=(None, None),
                 minValueXY=(None, None),
                 maxValueXY=(None, None),
                 mouseButton=QtCore.Qt.MiddleButton,
                 threshold=3,
                 slowModifier=QtCore.Qt.ControlModifier, fastModifier=QtCore.Qt.ShiftModifier):

        super(VirtualSlider, self).__init__(parent=parent)

        # The minimum or maximum value the return value can be. Defaults to minValue/maxValue
        self.setSettings(directions=directions,
                         minValue=minValue, maxValue=maxValue,
                         numType=numType, step=step, pixelRange=pixelRange,
                         slowSpeed=slowSpeed, speed=speed, fastSpeed=fastSpeed,
                         slowSpeedXY=slowSpeedXY, speedXY=speedXY,
                         fastSpeedXY=fastSpeedXY,
                         minValueXY=minValueXY,
                         maxValueXY=maxValueXY,
                         mouseButton=mouseButton,
                         slowModifier=slowModifier, fastModifier=fastModifier,
                         threshold=threshold
                         )

        self._pressedPos = None  # type: QtCore.QPoint
        self._currentDirection = None  # Current direction

        # The current scroll speed as bools
        self._fast = False
        self._slow = False

        # The last saved x,y positions
        self._lastX = 0  # type: int
        self._lastY = 0  # type: int

        self._modifiers = None

    def setSettings(self, directions=DirectionClamp,
                    minValue=None, maxValue=None,
                    numType=float, step=10, pixelRange=None,
                    slowSpeed=0.01, speed=0.1, fastSpeed=1,
                    slowSpeedXY=(None, None), speedXY=(None, None), fastSpeedXY=(None, None),
                    minValueXY=(None, None),
                    maxValueXY=(None, None),
                    threshold=3,
                    mouseButton=QtCore.Qt.MiddleButton,
                    slowModifier=QtCore.Qt.ControlModifier, fastModifier=QtCore.Qt.ShiftModifier):
        """ Set all the settings of the VirtualSlider. Similar to the VirtualSlider.__init__()

        :param directions: Can be VirtualSlider.DirectionClamp, VirtualSlider.Horizontal, VirtualSlider.Vertical, VirtualSlider.Both
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
        :param threshold: The approximate mouse distance before detecting horizontal or vertical
        :type threshold: int
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

        self.threshold = threshold  # The mouse distance before detecting the sliding
        self.minValue = minValue
        self.maxValue = maxValue
        self.minValueX = minValueXY[0] or minValue
        self.maxValueX = maxValueXY[0] or maxValue
        self.minValueY = minValueXY[1] or minValue
        self.maxValueY = maxValueXY[1] or maxValue
        self.direction = directions
        self.mouseButton = mouseButton
        self.pixelRange = pixelRange
        self.step = step

        # The speed of each tick when scrolling. Defaults to `speed` if the `speedX` is not found.
        self.slowSpeedX = slowSpeedXY[0] or slowSpeed
        self.normalSpeedX = speedXY[0] or speed
        self.fastSpeedX = fastSpeedXY[0] or fastSpeed

        self.slowSpeedY = slowSpeedXY[1] or slowSpeed
        self.normalSpeedY = speedXY[1] or speed
        self.fastSpeedY = fastSpeedXY[1] or fastSpeed
        self.numType = numType

        # Fast or slow keyboard modifiers
        self.fastModifier = fastModifier
        self.slowModifier = slowModifier

    def mousePressed(self, event):
        """ Mouse Pressed event.

        If mouse is pressed, save the position and emit any relevant signals.

        :param event: The normal mouse event from QtWidgets.QWidget.mousePressEvent(event)
        :type event: :class:`zoovendor.Qt.QtGui.QMouseEvent`
        :return:
        """
        if event.button() & self.mouseButton == self.mouseButton:
            index = self.parent().indexAt(event.pos())

            if index.row() >= 0:
                self.pressed.emit()
                self._pressedPos = event.pos()
                self._index = index

    def mouseMoved(self, event):
        """ Check if mouse is moving.
        If moving, return True.

        :param event: The normal mouse event from QtWidgets.QWidget.mouseMoveEvent(event)
        :type event: :class:`zoovendor.Qt.QtGui.QMouseEvent`
        :return:
        """

        self._updateModifiers()

        if self._pressedPos is not None:

            pos = event.pos() - self._pressedPos


            # Set the direction of the scroll based on the threshold
            newDir = self._calcDirection(pos)
            if newDir is not None:
                self._currentDirection = newDir

            if self._currentDirection is not None:
                # Calculate distance travelled since last

                self._calculateAndEmit(pos)

                return True
        return False

    def mouseReleased(self, event):
        """ Mouse released event

        :param event: The normal event from QtWidgets.QWidget.mouseReleaseEvent(event)
        :type event: :class:`zoovendor.Qt.QtGui.QMouseEvent`
        :return:
        """
        if event.button() & self.mouseButton == self.mouseButton:
            pos = event.pos() - self._pressedPos
            self._calculateAndEmit(pos, self.released, forceEmit=True)
            self._pressedPos = None
            self._currentDirection = None
            self._index = None
        self.parent().unsetCursor()

    def _updateModifiers(self):
        """ Update the _fast, _slow booleans based on what modifier is pressed. eg. Control or shift

        """
        kb = utils.keyboardModifiers()

        self._fast = kb == self.fastModifier
        self._slow = kb == self.slowModifier

        self._modifiers = kb

    def parent(self):
        """ The parent widget. For now typically the thumbnailWidget

        :return:
        :rtype: :class:`zoo.libs.pyqt.extended.imageview.thumbnail.thumbnailwidget.ThumbnailWidget`
        """
        return super(VirtualSlider, self).parent()

    def _calcDirection(self, pos):
        """ Set the currentDirection based on which direction the mouse has moved.

        If DirectionClamp set the direction based on the way the mouse is moving
            Eg if mouse moves up/down direction is 'vertical'
               if mouse moves left/right direction is 'horizontal'

        :param pos: The new position to calculate the direction from
        :type pos: :class:`QtCore.QPoint`
        :return: The direction
        """
        # If the mouse pos is far enough calculate the direction
        if self._absDist(pos) > self.threshold and self._currentDirection is None:
            absX = abs(pos.x())
            absY = abs(pos.y())

            # If both are supported, set the direction based on how far it's travelled in one direction
            if self.direction == self.DirectionClamp:
                if absX >= absY:
                    self.parent().setCursor(QtCore.Qt.SizeHorCursor)
                    return VirtualSlider.Horizontal
                else:
                    self.parent().setCursor(QtCore.Qt.SizeVerCursor)
                    return VirtualSlider.Vertical

            # If it's horizontal, just use horizontal
            elif self.direction == self.Horizontal:
                self.parent().setCursor(QtCore.Qt.SizeHorCursor)
                return VirtualSlider.Horizontal

            # If it's vertical, just use vertical
            elif self.direction == self.Vertical:
                self.parent().setCursor(QtCore.Qt.SizeVerCursor)
                return VirtualSlider.Vertical
            # If we want to use both
            elif self.direction == self.Both:
                self.parent().setCursor(QtCore.Qt.SizeAllCursor)
                if absX >= absY:
                    return VirtualSlider.Horizontal
                else:
                    return VirtualSlider.Vertical

    def _calculateAndEmit(self, pos, emitSignal=None, forceEmit=False):
        """ Calculate and emit the signal based on position

        Usually it will only emit if the number is different. If force emit is True, it will emit regardless.

        :param pos: The x,y position relative to the pressed position
        :type pos: :class:`QtCore.QPoint`
        :param emitSignal: The signal to emit. Default self.scrolled
        :type emitSignal: :class:`QtCore.Signal`
        :param forceEmit: Emit the signal regardless if the value is the same as the previous emitted signal.
        :type forceEmit: bool
        :return:
        """
        emitSignal = emitSignal or self.scrolled

        if self._currentDirection is not None:

            step = utils.dpiScale(self.step)

            # Pos calculated by dividing by step and rounding it off to remove the remainder, then mult step back in
            posX = self._clampPos(int(pos.x() * (1.0 / step)) * step)
            posY = self._clampPos(
                -int(pos.y() * (1.0 / step)) * step)  # -1 to Convert from qt coordinates to cartesian coordinates
            value = None

            # All directions emit
            if posY != self._lastY or posX != self._lastX or forceEmit:

                # Increment value based on the value given in the speed.
                valueX = self._getValue(posX, self._currentDirection)
                valueY = self._getValue(posY, self._currentDirection)

                valueX, valueY = self._clampValueX(valueX), self._clampValueY(valueY)
                value = self.numType(valueX), self.numType(valueY)
                x = posX
                y = posY
                dX = posY
                dY = posY - self._lastY

            if value:
                emitSignal.emit(MouseSlideEvent(value=value, direction=self._currentDirection,
                                                x=x, y=y,
                                                dx=dX, dy=dY, index=self._index,
                                                modifiers=self._modifiers))

                self._lastX, self._lastY = posX, posY

    def _clampValueX(self, x):
        """ Clamp x value based on minValueX, maxValueY

        :param x: The x value to clamp
        :type x: float
        :return:
        """

        if self.minValueX is not None:
            x = max(self.minValueX, x)

        if self.maxValueX is not None:
            x = min(self.maxValueX, x)

        return x

    def _clampValueY(self, y):
        """ Clamp y value based on minValueY, maxValueY

        :param y: The x value to clamp
        :type y: float
        """
        if self.minValueY is not None:
            y = max(self.minValueY, y)

        if self.maxValueY is not None:
            y = min(self.maxValueY, y)

        return y

    def _clampPos(self, pos):
        """ Clamp position based on pixelRange if it's not None.

        This will clamp pos in between -pixelRange and pixelRange.

        For instance if pixelRange = 100, pos will stay inbetween -100 and 100.

        :param pos: The x or y position to clamp.
        :type pos: float
        """
        if self.pixelRange is not None:
            pixelRange = utils.dpiScale(self.pixelRange)
            pos = min(max(-pixelRange, pos), pixelRange)

        return pos

    def _getValue(self, pos, direction):
        """ Get the value based on the position and the direction

        :param pos: Get the value based on this position as a float
        :type pos: float
        :param direction: The direction
        :type direction: int
        :return:
        """
        step = utils.dpiScale(self.step)
        speed = 0
        # Set speed based on direction and if any modifiers are pressed
        if direction in (VirtualSlider.Horizontal, VirtualSlider.Both):
            if self._fast:
                speed = self.fastSpeedX
            elif self._slow:
                speed = self.slowSpeedX
            else:
                speed = self.normalSpeedX

        elif direction in (VirtualSlider.Vertical, VirtualSlider.Both):
            if self._fast:
                speed = self.fastSpeedY
            elif self._slow:
                speed = self.slowSpeedY
            else:
                speed = self.normalSpeedY

        return pos * speed * (
                    1.0 / step)  # 1 / step to make sure the number stays consistent no matter what the step is set to

    def _absDist(self, pos):
        """ Rough distance from 0,0

        :param pos: :class:`QtCore.QPoint`
        :return: The rough distance from 0,0
        """
        return abs(pos.x()) + abs(pos.y())
