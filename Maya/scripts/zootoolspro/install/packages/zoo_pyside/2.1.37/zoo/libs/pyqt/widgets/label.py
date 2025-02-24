from functools import partial

from zoovendor.Qt import QtWidgets, QtCore, QtCompat
from zoo.libs.pyqt.extended.menu import MenuCreateClickMethods
from zoovendor.six import iteritems
from zoo.libs.pyqt.widgets.layouts import hBoxLayout
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets.spacer import Divider
from zoo.libs.pyqt.extended.checkbox import CheckBox


class Label(QtWidgets.QLabel, MenuCreateClickMethods):
    """This class adds the capacity for a left/middle/right click menu to be added to a QLabel

    Inherits from zoo's QtWidgets.QLabel and MenuCreateClickMethods

    Menus are not added by default they must be set in the ui code. QMenu's can be passed in via setMenu():

       zooQtWidget.setMenu(myQMenu, mouseButton=QtCore.Qt.RightButton)

    Recommended to use zoocore_pro's extendedmenu.ExtendedMenu(). Pass that in instead of a QMenu for extra
    functionality

    See the class docs for MenuCreateClickMethods() for more information

    :param parent: the parent widget
    :type parent: QWidget
    :param menuVOffset:  The vertical offset (down) menu drawn from widget top corner.  DPI is handled
    :type menuVOffset: int
    """
    leftClicked = QtCore.Signal()
    middleClicked = QtCore.Signal()
    rightClicked = QtCore.Signal()

    def __init__(self, text="", parent=None, toolTip="", upper=False, bold=False, enableMenu=True, menuVOffset=20):

        self.enableMenu = enableMenu
        if upper:
            text = text.upper()

        super(Label, self).__init__(text, parent=parent)

        self.setToolTip(toolTip)
        if bold:
            font = self.font()
            font.setBold(True)
            self.setFont(font)

        if self.enableMenu:
            self.setupMenuClass(menuVOffset=menuVOffset)
            self.leftClicked.connect(partial(self.contextMenu, QtCore.Qt.LeftButton))
            self.middleClicked.connect(partial(self.contextMenu, QtCompat.Qt.MidButton))
            self.rightClicked.connect(partial(self.contextMenu, QtCore.Qt.RightButton))

    def mousePressEvent(self, event):
        """ mouseClick emit

        Checks to see if a menu exists on the current clicked mouse button, if not, use the original Qt behaviour

        :param event: the mouse pressed event from the QLineEdit
        :type event: QEvent
        """
        if not self.enableMenu:  # There's no menu so ignore
            super(Label, self).mousePressEvent(event)
            return
        # Potential Menu
        for mouseButton, menu in iteritems(self.clickMenu):
            if menu and event.button() == mouseButton:  # if a menu exists and that mouse has been pressed
                if mouseButton == QtCore.Qt.LeftButton:
                    return self.leftClicked.emit()
                if mouseButton == QtCompat.Qt.MidButton:
                    return self.middleClicked.emit()
                if mouseButton == QtCore.Qt.RightButton:
                    return self.rightClicked.emit()
        super(Label, self).mousePressEvent(event)


class HeaderLabel(Label):

    def __init__(self, text="", parent=None, toolTip="", upper=True, bold=False, enableMenu=True, menuVOffset=20):
        super(HeaderLabel, self).__init__(text=text, parent=parent, toolTip=toolTip, upper=upper, bold=bold,
                                          enableMenu=enableMenu, menuVOffset=menuVOffset)
        utils.setStylesheetObjectName(self, "HeaderLabel")  # set title stylesheet


class LabelDivider(QtWidgets.QWidget):
    """Builds a label and a divider with options for Bold and Uppercase

    :param text: The label text
    :type text: str
    :param parent: The parent widget
    :type parent: QWidget
    :param margins: Margins of the layout in pixels DPI handled, (right, top, left, bottom)
    :type margins: tuple(int)
    :param spacing: The spacing in pixels between widgets DPI handled
    :type spacing: int
    :param bold: Make the label bold if True
    :type bold: bool
    :param upper: Make the label all uppercase if True
    :type upper: bool
    """

    def __init__(self, text="", parent=None, margins=(0, uic.SREG, 0, uic.SSML), spacing=uic.SREG, bold=True,
                 upper=False, toolTip=""):
        super(LabelDivider, self).__init__(parent=parent)
        mainLayout = hBoxLayout(parent=self, margins=margins, spacing=spacing)
        if text:
            label = Label(text=text, bold=bold, upper=upper, toolTip=toolTip)
            mainLayout.addWidget(label, 1)
        divider = Divider()
        divider.setToolTip(toolTip)
        mainLayout.addWidget(divider, 10)


class LabelDividerCheckBox(LabelDivider):
    def __init__(self, text="", parent=None, margins=(0, uic.SREG, 0, uic.SSML),
                 spacing=uic.SREG, bold=True, upper=False, toolTip="", checked=False):
        super(LabelDividerCheckBox, self).__init__(text=text, parent=parent,
                                                   margins=margins,
                                                   spacing=spacing, bold=bold, upper=upper, toolTip=toolTip)

        self.checkbox = CheckBox(label="", checked=checked, toolTip=toolTip)
        self.layout().addWidget(self.checkbox)

        # todo: make usable in toolset properties


class IconLabel(QtWidgets.QWidget):
    """Widget which contains a horizontal layout with an icon and a label
    """
    def __init__(self, icon, text="", parent=None, toolTip="", upper=False, bold=False, enableMenu=True,
                 menuVOffset=20):
        super(IconLabel, self).__init__(parent=parent)
        layout = utils.hBoxLayout(parent=self, margins=(0, 0, 0, 0), spacing=utils.dpiScale(4))
        self.label = Label(text, self, toolTip, upper, bold, enableMenu, menuVOffset)
        # determine the icon size by the label height that way it aligns correctly
        iconSize = self.label.sizeHint().height()

        self.iconPixmap = icon.pixmap(iconSize, iconSize)
        self.iconLabel = QtWidgets.QLabel(parent=self)
        self.iconLabel.setPixmap(self.iconPixmap)

        layout.addWidget(self.iconLabel)
        layout.addWidget(self.label)
        layout.setAlignment(self.iconLabel, QtCore.Qt.AlignLeft)
        layout.addStretch()

        self.setLayout(layout)


class TitleLabel(QtWidgets.QLabel):
    """ For CSS Purposes """
    pass
