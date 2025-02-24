from functools import partial

from zoovendor.Qt import QtWidgets, QtCore, QtCompat
from zoo.libs.pyqt.extended.menu import MenuCreateClickMethods
from zoovendor.six import iteritems

from zoo.libs.pyqt.widgets.layouts import hBoxLayout


class CheckBox(QtWidgets.QWidget, MenuCreateClickMethods):
    leftClicked = QtCore.Signal()
    middleClicked = QtCore.Signal()
    rightClicked = QtCore.Signal()
    stateChanged = QtCore.Signal(object)

    def __init__(self, label=None, checked=False, parent=None, toolTip="", enableMenu=True, menuVOffset=20, right=False,
                 labelRatio=0, boxRatio=0):
        """This class adds the capacity for a middle/right click menu to be added to the QCheckBox

        Note: This class disables the regular left click button states of a checkbox so has to handle them manual
        Inherits from QtWidgets.QCheckBox and MenuCreateClickMethods

        Menus are not added by default they must be set in the ui code. QMenu's can be passed in via setMenu():

            zooQtWidget.setMenu(myQMenu, mouseButton=QtCore.Qt.RightButton)

        If using zoocore_pro's ExtendedMenu() you can pass that in instead of a QMenu for extra functionality

        See the class docs for MenuCreateClickMethods() for more information

        :param parent: the parent widget
        :type parent: QWidget
        :param menuVOffset:  The vertical offset (down) menu drawn from widget top corner.  DPI is handled
        :type menuVOffset: int
        :type right: bool
        :param right: Move the checkbox to the right side, otherwise leave to the left

        """
        super(CheckBox, self).__init__(parent=parent)
        self._checkBox = QtWidgets.QCheckBox(label or "", parent=self)
        self._checkBox.stateChanged.connect(self.stateChanged.emit)  # so self.sender() picks up the correct widget
        self._right = right
        self._labelRatio = labelRatio
        self._boxRatio = boxRatio

        if toolTip:
            self.setToolTip(toolTip)

        self._initUi()
        self.setChecked(checked)
        self.setText(label)

        if enableMenu:
            self.setupMenuClass(menuVOffset=menuVOffset)
            self.leftClicked.connect(partial(self.contextMenu, QtCore.Qt.LeftButton))
            self.middleClicked.connect(partial(self.contextMenu, QtCompat.Qt.MidButton))
            self.rightClicked.connect(partial(self.contextMenu, QtCore.Qt.RightButton))
            # TODO: the setDown should turn off as soon as the mouse moves off the widget, like a hover state, looks tricky

    def _initUi(self):
        """ Initialise UI

        :return:
        :rtype:
        """
        self.boxLayout = hBoxLayout(self)
        self.setLayout(self.boxLayout)

        if self._right:
            self._label = QtWidgets.QLabel(self)
            self.boxLayout.addWidget(self._label, self._labelRatio)
        self.boxLayout.addWidget(self._checkBox, self._boxRatio)

    def setText(self, text):
        if self._label:
            self._label.setText(text)

        if self._right:
            self._checkBox.setText("")
        else:
            self._checkBox.setText(text)

    def text(self):
        if self._label:
            return self._label.text()

        return self._checkBox.text()

    def __getattr__(self, item):
        """ Map to the widgets checkbox

        :param item:
        :type item:
        :return:
        :rtype:
        """
        if hasattr(self._checkBox, item):
            return getattr(self._checkBox, item)
        # return getattr(self, item)

    def mousePressEvent(self, event):
        """ mouseClick emit

        Checks to see if a menu exists on the current clicked mouse button, if not, use the original Qt behaviour

        :param event: the mouse pressed event from the QLineEdit
        :type event: QEvent
        """
        if self.clickMenu:
            for mouseButton, menu in iteritems(self.clickMenu):
                if menu and event.button() == mouseButton:  # if a menu exists and that mouse has been pressed
                    if mouseButton == QtCore.Qt.LeftButton:
                        return self.leftClicked.emit()
                    if mouseButton == QtCompat.Qt.MidButton:
                        return self.middleClicked.emit()
                    if mouseButton == QtCore.Qt.RightButton:
                        return self.rightClicked.emit()
        super(CheckBox, self).mousePressEvent(event)

    def setCheckedQuiet(self, value):
        """Sets the checkbox in quiet box without emitting a signal

        :param value: True if checked, False if not checked
        :type value: bool
        """
        self._checkBox.blockSignals(True)
        self._checkBox.setChecked(value)
        self._checkBox.blockSignals(False)
