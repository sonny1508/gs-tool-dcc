from collections import OrderedDict
from functools import partial

from zoovendor.Qt import QtWidgets, QtCore, QtGui, QtCompat
from zoo.libs.pyqt import utils, validators
from zoo.libs.pyqt.extended.menu import MenuCreateClickMethods
from zoo.libs.pyqt.widgets.layouts import hBoxLayout
from zoovendor.six import iteritems
from zoo.libs.pyqt import uiconstants as uic
from zoo.core.util import env


class LineEdit(QtWidgets.QLineEdit, MenuCreateClickMethods):
    textModified = QtCore.Signal(object)  # Maya style update, on return and switching out of the text box use for GUIs
    leftClicked = QtCore.Signal()  # For menus
    middleClicked = QtCore.Signal()  # For menus
    rightClicked = QtCore.Signal()  # For menus
    mousePressed = QtCore.Signal(object)
    mouseReleased = QtCore.Signal(object)
    mouseMoved = QtCore.Signal(object)
    _textTouched = None  # Same as original textChanged behaviour of firing if any changes were made to the text, even if the text is the same.

    def __init__(self, text="", parent=None, enableMenu=False, placeholder="", toolTip="", editWidth=None,
                 fixedWidth=None, menuVOffset=20):
        """ Line Edit

        :param text:
        :type text:
        :param parent:
        :type parent:
        :param enableMenu:
        :type enableMenu:
        :param placeholder:
        :type placeholder:
        :param toolTip:
        :type toolTip:
        :param editWidth:
        :type editWidth:
        :param fixedWidth:
        :type fixedWidth:
        :param menuVOffset:
        :type menuVOffset:
        """
        super(LineEdit, self).__init__(parent=parent)

        self._value = None
        self._textChangedBefore = None  # The before for text changed

        self.initValidator()

        if editWidth:  # limit the width of the textbox
            self.setFixedWidth(utils.dpiScale(editWidth))
        if fixedWidth:
            self.setFixedWidth(utils.dpiScale(fixedWidth))
        self.setPlaceholderText(str(placeholder))
        self.setValue(text)
        self._textFinishedModified(text)
        self.setToolTip(toolTip)
        self.enterPressed = False


        self.textEdited.connect(self._updateValue)
        self.textModified.connect(self._textFinishedModified)
        self.editingFinished.connect(self._handleEditingFinished)

        self.textTouched.connect(self._handleTextTouched)

        self.returnPressed.connect(self._handleReturnPressed)
        self._beforeFinished = self.value()

        if enableMenu:
            self.setupMenuClass(menuVOffset=menuVOffset)
            self.leftClicked.connect(partial(self.contextMenu, QtCore.Qt.LeftButton))
            self.middleClicked.connect(partial(self.contextMenu, QtCompat.Qt.MidButton))
            self.rightClicked.connect(partial(self.contextMenu, QtCore.Qt.RightButton))
        else:
            self.clickMenu = None

    @property
    def textTouched(self):
        return self._textTouched or super(LineEdit, self).textChanged

    @textTouched.setter # for some reason this parent signals need a setter as well
    def textTouched(self, value):
        self._textTouched = value


    def _textFinishedModified(self, value):
        """ For when the text is finished mod

        :param value:
        :type value:
        :return:
        :rtype:
        """
        self._updateValue(value)


    def initValidator(self):
        """ To be overridden in subclass

        :return:
        :rtype:
        """
        pass

    def _updateValue(self, newValue):
        """ Update value

        :param newValue:
        :type newValue:
        :return:
        :rtype:
        """
        self.setValue(newValue, updateText=False)

    def _getBeforeAfterFinished(self):
        """Returns the before state and the after. Only for finished

        Checks if the textbox is a float, if so compare the numbers to account for irrelevant decimal differences"""
        return self._beforeFinished, self.value()

    def _handleTextTouched(self, text):
        """If text has changed update self._before
        """
        self._textChangedBefore = text

        if not self.hasFocus():
            self._beforeFinished = text

    def _handleEditingFinished(self):
        """if text has changed and editingFinished emit textModified
        """
        before, after = self._getBeforeAfterFinished()
        if before != after and not self.enterPressed:
            self._beforeFinished = after
            self.textModified.emit(after)

        self.enterPressed = False

    def _handleReturnPressed(self):
        """if text hasn't changed and returnPressed emit textModified
        """

        before, after = self._getBeforeAfterFinished()
        if before != after:
            self.textModified.emit(after)
            self.enterPressed = True  # a bit hacky to use this, maybe use a queuing system here

    def value(self):
        """ Get Value

        :return:
        :rtype:
        """
        return self._value

    def focusInEvent(self, event):
        """ Mouse enter event

        :param event:
        :return:
        """
        # Update the before value, as the before value should be used in between textChanged signals
        self._beforeFinished = self.value()
        return super(LineEdit, self).focusInEvent(event)

    def setAlphanumericValidator(self):
        """ Only allow numbers and letters.

        :return:
        :rtype:
        """
        validator = validators.createRegexValidator("[a-zA-Z0-9]+", self)
        self.setValidator(validator)

    def setValue(self, value, updateText=True):
        """ Set the value of the line edit

        :param value:
        :type value:
        :param updateText:
        :type updateText:
        :return:
        :rtype:
        """
        self._value = value

        if updateText:
            with utils.blockSignalsContext((self, )):
                self.setText(str(value))

    def mousePressEvent(self, event):
        """ mouseClick emit

        Checks to see if a menu exists on the current clicked mouse button, if not, use the original Qt behaviour

        :param event: the mouse pressed event from the QLineEdit
        :type event: Qt.QtGui.QMouseEvent
        """
        self.mousePressed.emit(event)
        if not self.clickMenu:
            super(LineEdit, self).mousePressEvent(event)
            return
        for mouseButton, menu in iteritems(self.clickMenu):
            if menu and event.button() == mouseButton:  # if a menu exists and that mouse has been pressed
                if mouseButton == QtCore.Qt.LeftButton:
                    return self.leftClicked.emit()
                if mouseButton == QtCompat.Qt.MidButton:
                    return self.middleClicked.emit()
                if mouseButton == QtCore.Qt.RightButton:
                    return self.rightClicked.emit()
        super(LineEdit, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """

        :param event:
        :type event: Qt.QtGui.QMouseEvent
        :return:
        :rtype:
        """
        self.mouseReleased.emit(event)
        super(LineEdit, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """

        :param event:
        :type event: Qt.QtGui.QMouseEvent
        :return:
        :rtype:
        """
        self.mouseMoved.emit(event)
        super(LineEdit, self).mouseMoveEvent(event)


class FloatLineEdit(LineEdit):
    def __init__(self, text="", parent=None, enableMenu=False, placeholder="", toolTip="", editWidth=None,
                 fixedWidth=None, menuVOffset=20, rounding=3,
                 slideDist=0.01, smallSlideDist=0.001, largeSlideDist=0.1, scrollDist=1, updateOnSlideTick=True):
        """ The Float Line edit that accepts only floats. To set value don't use setText, but use setValue instead.


        :param text:
        :type text:
        :param parent:
        :type parent:
        :param enableMenu:
        :type enableMenu:
        :param placeholder:
        :type placeholder:
        :param toolTip:
        :type toolTip:
        :param editWidth:
        :type editWidth:
        :param fixedWidth:
        :type fixedWidth:
        :param menuVOffset:
        :type menuVOffset:
        :param rounding:
        :type rounding:
        """
        self._rounding = rounding
        super(FloatLineEdit, self).__init__(text, parent, enableMenu, placeholder, toolTip, editWidth,
                                            fixedWidth, menuVOffset)
        if env.isMaya():
            self.mode = "Maya"
        elif env.isInBlender():
            self.mode = "Blender"

        self.mouseSlider = MouseSlider(self, slideDist=slideDist, smallSlideDist=smallSlideDist, largeSlideDist=largeSlideDist,
                                       updateOnTick=updateOnSlideTick, scrollDistance=scrollDist)

    def initValidator(self):
        """ Initialize the validator (in our case float)

        :return:
        :rtype:
        """
        self.setValidator(QtGui.QDoubleValidator())

    def _textFinishedModified(self, value):
        """ Text finished modified. Set the value and update the text based on the rounding


        :param value:
        :type value:
        :return:
        :rtype:
        """
        value = self.convertValue(self.value())

        self.blockSignals(True)
        self.setText(str(round(value, self._rounding)))
        self.blockSignals(False)
        self.clearFocus()

    def _getBeforeAfterFinished(self):
        """ Same as super class except returns float

        :return:
        :rtype:
        """
        return [float(v) for v in super(FloatLineEdit, self)._getBeforeAfterFinished()]

    def _updateValue(self, newValue):
        self.setValue(newValue, False)

    def setValue(self, value, updateText=True):
        """ Set value for float event

        :param value:
        :type value: float
        :param updateText:
        :type updateText:
        :return:
        :rtype:
        """
        self._value = self.convertValue(value)

        if updateText:
            self.blockSignals(True)
            self.updateRoundText()
            self.blockSignals(False)

    @classmethod
    def convertValue(cls, value):
        """ Converts value to float

        :param value:
        :type value:
        :return:
        :rtype:
        """
        ret = 0.0
        if value == ".":
            return ret
        elif value != "":
            try:
                ret = float(value)
            except ValueError:
                pass
        else:
            ret = 0.0

        return ret

    def setText(self, text):
        return super(FloatLineEdit, self).setText(text)

    def value(self):
        """ Get float value

        :return:
        :rtype: float
        """
        value = super(FloatLineEdit, self).value()
        return value or 0.0

    def focusInEvent(self, event):
        """ Focus In event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        if self.mode == "Blender":
            self.blockSignals(True)
            self.setText(str(self.value()))
            self.setFocus()
            self.selectAll()
            self.blockSignals(False)
        super(FloatLineEdit, self).focusInEvent(event)

    def focusOutEvent(self, event):
        """ Focus out event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        self._textFinishedModified(self.value())
        super(FloatLineEdit, self).focusOutEvent(event)

    def setRounding(self, rounding):
        """ Sets the padding of the text (usually for floats)
        """
        self._rounding = rounding

    def clearFocus(self):
        """ On clear focus run some code

        :return:
        :rtype:
        """
        ret = super(FloatLineEdit, self).clearFocus()
        self.updateRoundText()
        return ret

    def updateRoundText(self):
        """ Round the text

        :return:
        :rtype:
        """
        self.setText(str(round(self.value(), self._rounding)))


class IntLineEdit(LineEdit):

    def __init__(self, text="", parent=None, enableMenu=False, placeholder="", toolTip="", editWidth=None,
                 fixedWidth=None, menuVOffset=20,
                 slideDist=1, smallSlideDist=1, largeSlideDist=5, scrollDist=15, updateOnSlideTick=True):

        super(IntLineEdit, self).__init__(text, parent, enableMenu, placeholder, toolTip, editWidth, fixedWidth, menuVOffset)

        self.mouseSlider = MouseSlider(self, slideDist=slideDist, smallSlideDist=smallSlideDist, largeSlideDist=largeSlideDist,
                                       updateOnTick=updateOnSlideTick, scrollDistance=scrollDist)


    def initValidator(self):
        """ Set validator, in this case Integer

        :return:
        :rtype:
        """
        self.setValidator(QtGui.QIntValidator())

    def _textFinishedModified(self, value):
        """ Usually ran when the edit box has been modified. It will set the value and set the text

        :param value:
        :type value:
        :return:
        :rtype:
        """
        value = self.convertValue(value)

        self.blockSignals(True)
        self.setText(str(int(float(value))))
        self.clearFocus()
        self.blockSignals(False)

    def setValue(self, value, updateText=True):
        """ Set the value to an integer. Update the text as well if true

        :param value:
        :type value:
        :param updateText:
        :type updateText:
        :return:
        :rtype:
        """
        self._value = self.convertValue(value)
        if updateText:
            self.blockSignals(True)
            self.setText(str(self.value()))
            self.blockSignals(False)

    @classmethod
    def convertValue(cls, value):
        """ Converts value to int

        :param value:
        :type value:
        :return:
        :rtype:
        """
        if value == "0.0" or value == "-":
            ret = 0
        elif value != "":
            ret = int(float(value))
        else:
            ret = 0
        return ret

    def value(self):
        """ Get value as int

        :return:
        :rtype:
        """
        return super(IntLineEdit, self).value() or 0



class VectorLineEdit(QtWidgets.QWidget):
    """A label with multiple QLineEdits (text boxes), no spin boxes usually for x y z numeric input
    use inputMode="float" to restrict the data entry to decimal numbers
    """
    textChanged = QtCore.Signal(tuple)
    textModified = QtCore.Signal(tuple)

    def __init__(self, label, value, axis=("x", "y", "z"), parent=None, toolTip="", inputMode="float", labelRatio=1,
                 editRatio=1, spacing=uic.SREG, rounding=3, updateOnSlideTick=False):
        """A label with multiple QLineEdits (text boxes), no spin boxes usually for x y z numeric input
        use inputMode="float" to restrict the data entry to decimal numbers

        :param label: the label for the vector eg. translate, if the label is None or "" then it will be excluded
        :type label: str
        :param value: n floats corresponding with axis param
        :type value: tuple(float)
        :param axis: every axis ("x", "y", "z") or ("x", "y", "z", "w")
        :type axis: tuple(str)
        :param parent: the widget parent
        :type parent: QtWidget
        :param inputMode: restrict the user to this data entry, "string" text, "float" decimal or "int" no decimal
        :type inputMode: str
        :param labelRatio: the width ratio of the label/edit boxes, the "label" ratio when compared to the "edit boxes"
        :type labelRatio: int
        :param editRatio: the width ratio of the label/edit boxes, the "edit boxes" ratio when compared to the label
        :type editRatio: int
        :param spacing: the spacing of each widget
        :type spacing: int
        """
        super(VectorLineEdit, self).__init__(parent=parent)
        self.mainLayout = hBoxLayout(parent=self, margins=(0, 0, 0, 0), spacing=spacing)
        self.axis = axis
        if label:
            self.label = QtWidgets.QLabel(label, parent=self)
            self.label.setToolTip(toolTip)
            self.mainLayout.addWidget(self.label, labelRatio)
        self._widgets = OrderedDict()
        vectorEditLayout = hBoxLayout(margins=(0, 0, 0, 0), spacing=spacing)
        for i, v in enumerate(axis):
            if inputMode == "int":
                edit = IntLineEdit(text=value[i],
                                   placeholder="",
                                   parent=parent,
                                   toolTip=toolTip,
                                   updateOnSlideTick=updateOnSlideTick)
            else:
                edit = FloatLineEdit(text=value[i],
                                     placeholder="",
                                     parent=parent,
                                     toolTip=toolTip,
                                     rounding=rounding,
                                     updateOnSlideTick=updateOnSlideTick)
            # edit.setObjectName("".join([label, v]))  # might not need a label name?  Leave this line in case

            edit.textModified.connect(self._onTextModified)
            edit.textChanged.connect(self._onTextChanged)
            self._widgets[v] = edit
            vectorEditLayout.addWidget(edit)
        self.mainLayout.addLayout(vectorEditLayout, editRatio)

    def _onTextChanged(self):
        """updates the text, should also update the dict
        """
        valueList = [self._widgets[axis].value() for axis in self._widgets]
        self.textChanged.emit(tuple(valueList))

    def _onTextModified(self):
        """updates the text, should also update the dict
        """
        valueList = [self._widgets[axis].value() for axis in self._widgets]
        self.textModified.emit(tuple(valueList))

    def widget(self, axis):
        """Gets the widget from the axis string name

        :param axis: the single axis eg. "x"
        :type axis: tuple(str)
        :return widget: the LineEdit as a widget
        :rtype widget: QWidget
        """
        return self._widgets.get(axis)

    def value(self):
        """Gets the tuple values (text) of all the QLineEdits

        :return textValues: a tuple of string values from each QLineEdit textbox
        :rtype textValues: tuple(str)
        """
        valueList = [self._widgets[axis].value() for axis in self._widgets]
        if type(self._widgets[self.axis[0]].validator()) == QtGui.QDoubleValidator:  # float
            return [float(value) for value in valueList]
        elif type(self._widgets[self.axis[0]].validator()) == QtGui.QIntValidator:  # int:
            return [int(value) for value in valueList]
        return tuple(valueList)

    def setValue(self, value):
        """Sets the text values of all the QLineEdits, can be strings floats or ints depending on the inputMode

        :param value: the value of all text boxes, as a list of strings (or floats, ints depending on inputMode)
        :type value: tuple[float] or list[float]
        """
        # get the widgets in order
        keys = list(self._widgets.keys())
        for i, v in enumerate(value):
            self._widgets[keys[i]].setValue(v)

    def setLabelFixedWidth(self, width):
        """Set the fixed width of the label"""
        self.label.setFixedWidth(utils.dpiScale(width))

    def hideLineEdit(self, axisInt):
        """hides one of the lineEdits from by index from self.axis list

        :param axisInt: the index of the lineEdit to hide
        :type axisInt: int
        """
        self._widgets[self.axis[axisInt]].hide()

    def showLineEdit(self, axisInt):
        """shows one of the lineEdits from by index from self.axis list

        :param axisInt: the index of the lineEdit to hide
        :type axisInt: int
        """
        self._widgets[self.axis[axisInt]].show()



class MouseSlider(QtCore.QObject):
    tickEvent = QtCore.Signal(object)
    deltaChanged = QtCore.Signal(object)
    sliderStarted = QtCore.Signal()
    sliderFinished = QtCore.Signal()
    sliderChanged = QtCore.Signal(object)


    def __init__(self, parentEdit,
                 slideDist=1, smallSlideDist=0.1, largeSlideDist=5,
                 scrollDistance=1, updateOnTick=False):
        """ Mouse slider for number edits

        :param parentEdit: The parent edit to install into
        :type parentEdit: StringEdit or LineEdit
        :param slideDist:
        :type slideDist: float or int
        :param smallSlideDist:
        :type smallSlideDist:  float or int
        :param largeSlideDist:
        :type largeSlideDist:  float or int
        :param scrollDistance: The distance in pixels to scroll before registering a tick
        :type scrollDistance: int
        """
        super(MouseSlider, self).__init__()
        self.startValue = 0
        self._edit = parentEdit
        self.updateOnTick = updateOnTick
        # self.edit = stringEdit.edit
        self.slideDist = slideDist
        self.smallSlideDist = smallSlideDist
        self.largeSlideDist = largeSlideDist
        self.scrollDistance = utils.dpiScale(scrollDistance)
        self.pressPos = None  # type: QtCore.QPoint
        self._mouseDelta = 0
        self.deltaX = 0
        self.prevDeltaX = 0
        self._enabled = True
        self._connections()

    def setEnabled(self, enabled):
        """ Set enabled

        :type enabled: bool
        """
        self._enabled = enabled

    def _connections(self):
        """ Connections

        :return:
        :rtype:
        """
        self._edit.mouseMoved.connect(self.mouseMoveEvent)
        self._edit.mousePressed.connect(self.mousePressEvent)
        self._edit.mouseReleased.connect(self.mouseReleaseEvent)

        self.tickEvent.connect(self.tick)

    def tick(self, delta):
        """ Ran per tick

        :param delta:
        :type delta:
        :return:
        :rtype:
        """
        if not self._enabled:
            return

        value = self.startValue + float(delta)
        self._edit.setValue(value)
        self._edit.update()

        if self.updateOnTick:
            self._edit.textChanged.emit(self._edit.text())
            self._edit.textModified.emit(self._edit.text())
            self.sliderChanged.emit(self._edit.text())

    def mouseMoveEvent(self, event):
        """ Mouse move event

        :param event:
        :type event: Qt.QtGui.QMouseEvent
        :return:
        :rtype:
        """
        if not self._enabled:
            return

        if self.pressPos:
            self._mouseDelta = event.pos().x() - self.pressPos.x()
            if self._mouseDelta % self.scrollDistance == 0:
                self.deltaX = self._mouseDelta / self.scrollDistance

                if self.deltaX != self.prevDeltaX:
                    self.deltaChanged.emit(self.deltaX - self.prevDeltaX)

                    ctrl = int(event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier)
                    shift = int(event.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier)

                    if ctrl:
                        self.tickEvent.emit(self.deltaX * self.smallSlideDist)
                    elif shift:
                        self.tickEvent.emit(self.deltaX * self.largeSlideDist)
                    else:
                        self.tickEvent.emit(self.deltaX * self.slideDist)
                self.prevDeltaX = self.deltaX

    def mousePressEvent(self, event):
        """ mouse press event

        :param event:
        :type event: Qt.QtGui.QMouseEvent
        :return:
        :rtype:
        """
        if not self._enabled:
            return

        if event.button() == QtCore.Qt.MiddleButton:
            self.pressPos = event.pos()
            self.startValue = self._edit.value()
            self.sliderStarted.emit()

    def mouseReleaseEvent(self, event):
        """ mouse release event

        :param event:
        :type event: Qt.QtGui.QMouseEvent
        :return:
        :rtype:
        """
        if not self._enabled:
            return

        if event.button() == QtCore.Qt.MiddleButton:
            self.pressPos = None

            self._edit.setValue(self._edit.value())
            self._edit.textChanged.emit(self._edit.text())
            self._edit.textModified.emit(self._edit.text())
            self.sliderFinished.emit()