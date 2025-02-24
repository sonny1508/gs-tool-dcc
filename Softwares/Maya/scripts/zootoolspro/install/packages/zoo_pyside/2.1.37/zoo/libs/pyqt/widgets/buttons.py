from zoo.preferences.interfaces import coreinterfaces
from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets import roundbutton, label, layouts, dpiscaling
from zoo.libs.pyqt.widgets.extendedbutton import ExtendedPushButton, ExtendedButton, ShadowedButton
from zoo.libs import iconlib
from zoo.preferences.core import preference

THEMEPREF = preference.interface("core_interface")


class OkCancelButtons(QtWidgets.QWidget):
    OkBtnPressed = QtCore.Signal()
    CancelBtnPressed = QtCore.Signal()

    def __init__(self, okText="OK", cancelTxt="Cancel", parent=None):
        """Creates OK Cancel Buttons bottom of window, can change the names

        :param okText: the text on the ok (first) button
        :type okText: str
        :param cancelTxt: the text on the cancel (second) button
        :type cancelTxt: str
        :param parent: the widget parent
        :type parent: class
        """
        super(OkCancelButtons, self).__init__(parent=parent)
        self._layout = utils.hBoxLayout(self)
        self.okBtn = QtWidgets.QPushButton(okText, parent=self)
        self.cancelBtn = QtWidgets.QPushButton(cancelTxt, parent=self)
        self._layout.addWidget(self.okBtn)
        self._layout.addWidget(self.cancelBtn)
        self.connections()

    def connections(self):
        self.okBtn.clicked.connect(self.OkBtnPressed.emit)
        self.cancelBtn.clicked.connect(self.CancelBtnPressed.emit)


def buttonRound(**kwargs):
    """Create a rounded button usually just an icon only button with icon in a round circle

    This function is usually called via buttonStyled()
    Uses stylesheet colors, and icon color via the stylesheet from buttonStyled()

    .. Note:: WIP, Will fill out more options with time

    :keyword parent (:class:`QtWidgets.QWidget`): The parent widget.
    :keyword text (str): The button text.
    :keyword icon (str): the icon name from the zoo tools iconlib.
    :keyword toolTip (str): The button tooltip
    :keyword iconSize (int): the icon size before dpi scaling.
    :keyword iconColor (tuple[int, int, int, int]): The icon color which will fill the masked area of the icon.
    :keyword btnWidth (int): The fixed width for the button.
    :keyword btnHeight (int): The fixed height for the button.
    :return: returns a qt button widget
    :rtype: :class:`RoundButton`
    """
    parent = kwargs.get("parent")
    text = kwargs.get("text")
    toolTip = kwargs.get("toolTip", "")
    icon = kwargs.get("icon", (255, 255, 255))  # returns the name of the icon as a string only
    iconSize = kwargs.get("iconSize", 16)
    iconColor = kwargs.get("iconColor", (255, 255, 255))
    # iconHoverColor = kwargs.get("iconHoverColor")  # TODO: add this functionality later
    btnWidth = kwargs.get("btnWidth", 24)
    btnHeight = kwargs.get("btnHeight", 24)

    iconObject = iconlib.iconColorized(icon, size=iconSize, color=iconColor)

    btn = roundbutton.RoundButton(parent=parent, text=text, icon=iconObject, toolTip=toolTip)
    btn.setFixedSize(QtCore.QSize(btnWidth, btnHeight))
    return btn


def styledButton(text=None, icon=None, parent=None, toolTip="", textCaps=False, iconColor=None, iconHoverColor=None,
                 minWidth=None, maxWidth=None, iconSize=16, overlayIconName=None, overlayIconColor=None, minHeight=None,
                 maxHeight=None, style=uic.BTN_DEFAULT, btnWidth=None, btnHeight=None, iconColorTheme=None,
                 themeUpdates=True):
    """ Create a button with text or an icon in various styles and options.::

        Style - 0 - uic.BTN_DEFAULT - Default zoo extended button with optional text or an icon.
        Style - 1 - uic.BTN_TRANSPARENT_BG - Default zoo extended button w transparent bg.
        Style - 2 - uic.BTN_ICON_SHADOW - Main zoo IconPushButton button (icon in a colored box) with shadow underline
        Style - 3 - uic.BTN_DEFAULT_QT - Default style uses vanilla QPushButton and not zoo's extended button
        Style - 4 - uic.BTN_ROUNDED - # Rounded button stylesheeted bg color and stylesheeted icon color
        Style - 5 - uic.BTN_LABEL_SML - A regular Qt label with a small button beside

    :param text: The button text
    :type icon: str
    :param icon: The icon image name, icon is automatically sized.
    :type icon: str
    :param parent: The parent widget.
    :type parent: object
    :param toolTip: The tooltip as seen with mouse over extra information.
    :type toolTip: str
    :param style: The style of the button, 0 default, 1 no bg. See pyside.uiconstants BTN_DEFAULT, BTN_TRANSPARENT_BG.
    :type style: int
    :param textCaps: Bool to make the button text all caps.
    :type textCaps: bool
    :param iconColor: The color of the icon in 255 color eg (255, 134, 23)
    :type iconColor: tuple
    :param minWidth: minimum width of the button in pixels, DPI handled.
    :type minWidth: int
    :param maxWidth: maximum width of the button in pixels, DPI handled.
    :type maxWidth: int
    :param iconSize: The size of the icon in pixels, always square, DPI handled.
    :type iconSize: int
    :param overlayIconName: The name of the icon image that will be overlayed on top of the original icon.
    :param overlayIconName: tuple
    :param overlayIconColor: The color of the overlay image icon (255, 134, 23) :note: Not implemented yet.
    :type overlayIconColor: tuple
    :param minHeight: minimum height of the button in pixels, DPI handled.  Overrides min and max settings
    :type minHeight: int
    :param maxHeight: maximum height of the button in pixels, DPI handled.
    :type maxHeight: int
    :param btnWidth: the fixed width of the button is there is one, DPI handled.  Overrides min and max settings
    :type btnWidth: int
    :param btnHeight: the fixed height of the button is there is one, DPI handled.
    :type btnHeight: int
    :return: returns a qt button widget.
    :rtype: :class:`ShadowedButton` or :class:`QtWidgets.QPushButton` or :class:`roundbutton.RoundButton` \
            or :class:`LabelSmlButton`
    """
    if not iconColor:
        iconColor = THEMEPREF.BUTTON_ICON_COLOR
    if not iconHoverColor:
        # todo: this is done automatically in extendedbuttons, this shouldn't be done here
        hoverOffset = 25
        iconHoverColor = iconColor
        iconHoverColor = tuple([min(255, c + hoverOffset) for c in iconHoverColor])
    retBtn = None
    if style == uic.BTN_DEFAULT or style == uic.BTN_TRANSPARENT_BG:
        retBtn = buttonExtended(text=text, icon=icon, parent=parent, toolTip=toolTip, textCaps=textCaps,
                                iconColor=iconColor, iconHoverColor=iconHoverColor, minWidth=minWidth,
                                maxWidth=maxWidth, iconSize=iconSize, overlayIconName=overlayIconName,
                                overlayIconColor=overlayIconColor, minHeight=minHeight, maxHeight=maxHeight,
                                style=style, iconColorTheme=iconColorTheme, themeUpdates=themeUpdates)

    elif style == uic.BTN_ICON_SHADOW:
        retBtn = iconShadowButton(text=text, icon=icon, parent=parent, toolTip=toolTip, textCaps=textCaps,
                                  iconColor=iconColor, iconHoverColor=iconHoverColor, minWidth=minWidth,
                                  maxWidth=maxWidth, iconSize=iconSize, overlayIconName=overlayIconName,
                                  overlayIconColor=overlayIconColor, minHeight=minHeight, maxHeight=maxHeight)
    elif style == uic.BTN_DEFAULT_QT:
        retBtn = regularButton(text=text, icon=icon, parent=parent, toolTip=toolTip, textCaps=textCaps,
                               iconColor=iconColor, iconHoverColor=iconHoverColor, minWidth=minWidth, maxWidth=maxWidth,
                               iconSize=iconSize, overlayIconName=overlayIconName, overlayIconColor=overlayIconColor,
                               minHeight=minHeight, maxHeight=maxHeight)
    elif style == uic.BTN_ROUNDED:
        retBtn = buttonRound(text=text, icon=icon, parent=parent, toolTip=toolTip, iconColor=iconColor,
                             iconHoverColor=iconHoverColor, iconSize=iconSize, overlayIconName=overlayIconName,
                             overlayIconColor=overlayIconColor, btnWidth=btnWidth, btnHeight=btnHeight)
    elif style == uic.BTN_LABEL_SML:
        retBtn = LabelSmlButton(text=text, icon=icon, parent=parent, toolTip=toolTip, textCaps=textCaps,
                                iconColor=iconColor, iconHoverColor=iconHoverColor, minWidth=uic.BTN_W_ICN_MED,
                                maxWidth=uic.BTN_W_ICN_MED, iconSize=iconSize, overlayIconName=overlayIconName,
                                overlayIconColor=overlayIconColor, minHeight=minHeight, maxHeight=maxHeight)
    if btnWidth:
        retBtn.setFixedWidth(btnWidth)
    if btnHeight:
        retBtn.setFixedHeight(btnHeight)
    return retBtn


def buttonExtended(**kwargs):
    """ Create an extended either transparent bg or regular style. Features all the extended button functionality

    Default Icon colour (None) is light grey and turns white (lighter in color) with mouse over.
    :Note: WIP, Will fill out more options with time

    :keyword parent (`QtWidgets.QWidget`): The parent widget.
    :keyword text (str): The button text.
    :keyword icon (str): the icon name from the zoo tools iconlib.
    :keyword toolTip (str): The button tooltip
    :keyword iconSize (int): the icon size before dpi scaling.
    :keyword iconColor (tuple[int, int, int, int]): The icon color which will fill the masked area of the icon.
    :keyword overlayIconName (str): the icon to overlay on top of the icon.
    :keyword overlayIconColor (tuple[int, int, int, int]): The icon color which will fill the masked area of the overlay icon.
    :keyword minWidth (int): The minimum button width.
    :keyword maxWidth (int): The minimum button height.
    :keyword minHeight (int): The maximum button width.
    :keyword maxHeight (int): The maximum button height.
    :keyword style (int): The style constant ie. uiconstants.BTN_DEFAULT
    :keyword themeUpdates (bool): Whether the button will react with a theme change from the preferences.
    :return qtBtn: returns a qt button widget
    :rtype qtBtn: object
    """
    parent = kwargs.get("parent")
    text = kwargs.get("text")
    icon = kwargs.get("icon", "")  # returns the name of the icon as a string only
    toolTip = kwargs.get("toolTip", "")
    iconSize = kwargs.get("iconSize", 16)
    iconColor = kwargs.get("iconColor")
    # iconHoverColor = kwargs.get("iconHoverColor")
    # overlayIconName = kwargs.get("overlayIconName")
    # overlayIconColor = kwargs.get("overlayIconColor")
    iconColorTheme = kwargs.get("iconColorTheme")
    minWidth = kwargs.get("minWidth")
    maxWidth = kwargs.get("maxWidth")
    # btnWidth = kwargs.get("btnWidth")
    # btnHeight = kwargs.get("btnWidth")
    minHeight = kwargs.get("maxHeight")
    maxHeight = kwargs.get("maxHeight")
    themeUpdates = kwargs.get("themeUpdates")
    style = kwargs.get("style")

    if icon:
        # todo: icon hover already gets done automatically use btn.setIconByName() instead
        if style == uic.BTN_DEFAULT:
            btn = ExtendedPushButton(parent=parent, text=text, iconColorTheme=iconColorTheme, themeUpdates=themeUpdates)
        else:
            btn = ExtendedButton(parent=parent, text=text, iconColorTheme=iconColorTheme, themeUpdates=themeUpdates)

        btn.setIconByName(icon, size=iconSize, colors=iconColor)  # todo add overlayIconName, overlayIconColor

    else:
        if style == uic.BTN_DEFAULT:
            btn = ExtendedPushButton(parent=parent, text=text, iconColorTheme=iconColorTheme)  # default style
        else:
            btn = ExtendedButton(parent=parent, text=text, iconColorTheme=iconColorTheme)  # transparent style
    btn.setToolTip(toolTip)

    if minWidth is not None:
        btn.setMinimumWidth(minWidth)
    if maxWidth is not None:
        btn.setMaximumWidth(maxWidth)
    if minHeight is not None:
        btn.setMinimumHeight(minHeight)
    if maxHeight is not None:
        btn.setMaximumHeight(maxHeight)

    return btn


def regularButton(**kwargs):
    """ Creates regular pyside button with text or an icon.

    :note: Will fill out more options with time.
    :note: Should probably override ExtendedButton and not QtWidgets.QPushButton for full options.

    :keyword parent (`QtWidgets.QWidget`): The parent widget.
    :keyword text (str): The button text.
    :keyword icon (str): the icon name from the zoo tools iconlib.
    :keyword toolTip (str): The button tooltip
    :keyword iconSize (int): the icon size before dpi scaling.
    :keyword iconColor (tuple[int, int, int, int]): The icon color which will fill the masked area of the icon.
    :keyword overlayIconName (str): the icon to overlay on top of the icon.
    :keyword overlayIconColor (tuple[int, int, int, int]): The icon color which will fill the masked area of the overlay icon.
    :keyword minWidth (int): The minimum button width.
    :keyword maxWidth (int): The minimum button height.
    :keyword minHeight (int): The maximum button width.
    :keyword maxHeight (int): The maximum button height.
    :return: returns a QPushButton button widget.
    :rtype: class:`QtWidgets.QPushButton`
    """
    parent = kwargs.get("parent")
    text = kwargs.get("text")
    icon = kwargs.get("icon")
    toolTip = kwargs.get("toolTip", "")
    iconSize = kwargs.get("iconSize", uic.BTN_W_ICN_REG)
    iconColor = kwargs.get("iconColor", THEMEPREF.BUTTON_ICON_COLOR)
    overlayIconName = kwargs.get("overlayIconName")
    overlayIconColor = kwargs.get("overlayIconColor")
    minWidth = kwargs.get("minWidth")
    maxWidth = kwargs.get("maxWidth")
    minHeight = kwargs.get("minHeight")
    maxHeight = kwargs.get("maxHeight")

    btn = QtWidgets.QPushButton(text, parent=parent)
    if icon:
        btn.setIcon(iconlib.iconColorized(icon, size=utils.dpiScale(iconSize), color=iconColor,
                                          overlayName=overlayIconName, overlayColor=overlayIconColor))

    btn.setToolTip(toolTip)
    if minWidth is not None:
        btn.setMinimumWidth(utils.dpiScale(minWidth))
    if maxWidth is not None:
        btn.setMaximumWidth(utils.dpiScale(maxWidth))
    if minHeight is not None:
        btn.setMinimumHeight(utils.dpiScale(minHeight))
    if maxHeight is not None:
        btn.setMaximumHeight(utils.dpiScale(maxHeight))
    return btn


def iconShadowButton(**kwargs):
    """ Create a button (ShadowedButton) with the icon in a coloured box and a button shadow at the bottom of the button.

    This function is usually called via buttonStyled()
    Uses stylesheet colors, and icon color via the stylesheet from buttonStyled()

    :Note: WIP, Will fill out more options with time

    :keyword parent (:class:`QtWidgets.QWidget`): The parent widget.
    :keyword text (str): The button text.
    :keyword icon (str): the icon name from the zoo tools iconlib.
    :keyword toolTip (str): The button tooltip
    :keyword iconSize (int): the icon size before dpi scaling.
    :keyword iconColor (tuple[int, int, int, int]): The icon color which will fill the masked area of the icon.
    :keyword overlayIconName (str): the icon to overlay on top of the icon.
    :keyword overlayIconColor (tuple[int, int, int, int]): The icon color which will fill the masked area of the overlay icon.
    :keyword minWidth (int): The minimum button width.
    :keyword maxWidth (int): The minimum button height.
    :keyword minHeight (int): The maximum button width.
    :keyword maxHeight (int): The maximum button height.

    :return: returns a ShadowedButton widget instance
    :rtype: :class:`ShadowedButton`
    """
    parent = kwargs.get("parent")
    text = kwargs.get("text")
    textCaps = kwargs.get("textCaps")
    icon = kwargs.get("icon", THEMEPREF.BUTTON_ICON_COLOR)  # returns the name of the icon as a string only
    toolTip = kwargs.get("toolTip", "")
    iconSize = kwargs.get("iconSize")
    iconColor = kwargs.get("iconColor")
    # iconHoverColor = kwargs.get("iconHoverColor")  # TODO: add this functionality later
    minWidth = kwargs.get("minWidth")
    maxWidth = kwargs.get("maxWidth")
    # minHeight = kwargs.get("minHeight")  # TODO: add this functionality later
    maxHeight = kwargs.get("maxHeight")
    btn = ShadowedButton(text=text, parent=parent, forceUpper=textCaps, toolTip=toolTip)
    btn.setIconByName(icon, colors=iconColor, size=iconSize)
    if maxHeight:
        btn.setFixedHeight(maxHeight)
    if maxWidth:
        btn.setMaximumWidth(maxWidth)
    if minWidth:
        btn.setMinimumWidth(minWidth)
    return btn


class LabelSmlButton(QtWidgets.QWidget):
    clicked = QtCore.Signal()

    def __init__(self, text="", icon=None, parent=None, toolTip="", textCaps=False, iconColor=None, iconHoverColor=None,
                 minWidth=None, maxWidth=None, iconSize=16, overlayIconName=None, overlayIconColor=None, minHeight=None,
                 maxHeight=None, style=uic.BTN_DEFAULT, btnWidth=None, btnHeight=None):
        """Creates a Qt label and a small button with icon, can be called as though it's a button with StyledButton()

        See StyledButton() for kwarg documentation
        """
        super(LabelSmlButton, self).__init__(parent=parent)
        self.text = text
        if text:
            self.label = label.Label(text, self, toolTip=toolTip, upper=textCaps)
        self.btn = buttonExtended(text="", icon=icon, parent=self, toolTip=toolTip, textCaps=textCaps,
                                  iconColor=iconColor, iconHoverColor=iconHoverColor, minWidth=minWidth,
                                  maxWidth=maxWidth, iconSize=iconSize, overlayIconName=overlayIconName,
                                  overlayIconColor=overlayIconColor, minHeight=minHeight, maxHeight=maxHeight,
                                  style=style)
        btnLayout = layouts.hBoxLayout(parent=self)
        if text:
            btnLayout.addWidget(self.label, 5)
        btnLayout.addWidget(self.btn, 1)
        self.connections()

    def _onClicked(self):
        """If the button is clicked emit"""
        self.clicked.emit()

    def setDisabled(self, state):
        """Disable the text (make it grey)"""
        self.btn.setDisabled(state)
        if self.text:
            self.label.setDisabled(state)

    def connections(self):
        self.btn.clicked.connect(self._onClicked)


class AlignedButton(ExtendedButton, dpiscaling.DPIScaling):
    def __init__(self, text="", parent=None, icon=None,
                 align=QtCore.Qt.AlignLeft, margins=(8, 0, 8, 0), spacing=3,
                 toolTip=None):
        self._kwargs = locals()
        self._icon = None
        self._label = None

        super(AlignedButton, self).__init__("", parent=parent)
        self._initUi()

    def _initUi(self):
        """ Initialize the ui

        :return:
        """
        self.setToolTip(self._kwargs['toolTip'])
        self._icon = AlignedButtonImage(self)
        self._label = QtWidgets.QLabel(self._kwargs['text'], parent=self)
        self.setLayout(layouts.hBoxLayout(margins=self._kwargs['margins'], spacing=self._kwargs['spacing']))

        self._iconSize = utils.sizeByDpi(QtCore.QSize(16, 16))

        self.iconPixmap = None  # type: QtGui.QPixmap
        self.iconHoveredPixmap = None  # type: QtGui.QPixmap
        self.iconPressedPixmap = None  # type: QtGui.QPixmap
        self.themePref = coreinterfaces.coreInterface()
        self.setFixedHeight(24)

        if self._kwargs['align'] == QtCore.Qt.AlignRight:
            self.layout().addStretch(1)
        self.layout().addWidget(self._icon)
        self.layout().addWidget(self._label)
        if self._kwargs['align'] == QtCore.Qt.AlignLeft:
            self.layout().addStretch(1)
        self.setIconByName(self._kwargs['icon'], uic.DEFAULT_ICON_COLOR)

    def updateTheme(self, event):
        """ Update the theme

        :type event: preferences.interface.preference_interface.UpdateThemeEvent
        :return:
        :rtype:
        """
        pass

    def setIcon(self, icon):
        """

        :param icon:
        :type  icon: zoovendor.Qt.QtGui.QIcon
        :return:
        """
        if not self._icon:
            return

        if icon:
            self._icon.setPixmap(icon.pixmap(self._icon.size()))
            self._icon.show()
        else:
            self._icon.hide()

    def setText(self, text):
        if self._label:
            self._label.setText(text)

    def setIconSize(self, size):
        """ Set the icon size

        :param size:
        :return:
        """
        self._iconSize = utils.sizeByDpi(size)
        self._icon.setFixedSize(self._iconSize)

    def mouseDoubleClickEvent(self, event):
        event.ignore()
        return super(AlignedButton, self).mouseDoubleClickEvent(event)

    def setFixedHeight(self, height):
        """ Set Fixed Height

        :param height: Height in pixels of the button
        :type height: int
        :return:
        """
        self.updateImageWidget(height)
        super(AlignedButton, self).setFixedHeight(height)

    def setFixedSize(self, size):
        """ Set the fixed size

        :param size: New fixed size of the widget
        :type size: QtCore.QSize

        :return:
        """
        self.updateImageWidget(size.height())
        super(AlignedButton, self).setFixedSize(size)

    def updateImageWidget(self, newHeight):
        """ Make sure the image widget is always square

        :param newHeight: The new height of the widget to update to
        :type newHeight: int
        :return:
        """

        self._icon.setFixedSize(utils.sizeByDpi(QtCore.QSize(newHeight, newHeight)))

    def setIconByName(self, iconNames, colors, size=None, hoverColor=None, pressedColor=None, iconScaling=None):
        """ Set Icon Size by name

        todo: needs additional features similar to the ButtonIcons.setIconByName() method

        :param size: Size of the icon in pixels
        :type size: int
        :param iconNames: Names of the icons
        :type iconNames: list or basestring
        :param colors: Colors of the icons
        :type colors: list of tuple or tuple
        :return:
        """
        self._icon.show()
        if size is not None:
            self.setIconSize(QtCore.QSize(size, size))

        hoverColor = hoverColor or colors
        pressedColor = pressedColor or colors

        colors = [colors]
        hoverColor = [hoverColor]
        pressedColor = [pressedColor]
        self.iconNames = iconNames

        # if self.isMenu and isinstance(iconNames, string_types):
        #     self.iconNames = [iconNames, self._menuIndicatorIcon]
        #     colors += colors
        #     hoverColor += hoverColor
        #     pressedColor += pressedColor

        newSize = self._iconSize.width()
        self.iconPixmap = iconlib.iconColorizedLayered(self.iconNames, colors=colors, size=newSize,
                                                       iconScaling=iconScaling). \
            pixmap(QtCore.QSize(newSize, newSize))

        self.iconHoveredPixmap = iconlib.iconColorizedLayered(self.iconNames, colors=hoverColor, size=newSize,
                                                              iconScaling=iconScaling). \
            pixmap(QtCore.QSize(newSize, newSize))

        self.iconPressedPixmap = iconlib.iconColorizedLayered(self.iconNames, colors=pressedColor, size=newSize,
                                                              iconScaling=iconScaling). \
            pixmap(QtCore.QSize(newSize, newSize))

        self._icon.setPixmap(self.iconPixmap)

    def enterEvent(self, event):
        self._icon.setPixmap(self.iconHoveredPixmap)

    def leaveEvent(self, event):
        self._icon.setPixmap(self.iconPixmap)

    def mousePressEvent(self, event):
        super(AlignedButton, self).mousePressEvent(event)
        self._icon.setPixmap(self.iconPressedPixmap)

    def mouseReleaseEvent(self, event):
        super(AlignedButton, self).mouseReleaseEvent(event)
        self._icon.setPixmap(self.iconPixmap)

class AlignedButtonImage(QtWidgets.QLabel, dpiscaling.DPIScaling):
    """ CSS Purposes """


class LeftAlignedButtonBase(QtWidgets.QPushButton):
    """Simple button that is left aligned with text and icon.
    """

    def __init__(self, text="", parent=None, icon=None, toolTip=None):
        if text:
            text = " {}".format(text)  # adds spacing with spaces
        super(LeftAlignedButtonBase, self).__init__(text, parent)
        # pass the icon only if it's not none otherwise this break the text
        if icon is not None:
            iconSize = icon.availableSizes()[0]
            self.setIconSize(iconSize)
            self.setIcon(icon)

        if toolTip:
            self.setToolTip(toolTip)
        self.setStyleSheet(
            "QPushButton {} text-align: left; padding-left: {}px; {}".format("{", str(utils.dpiScale(7)), "}"))
        # menu cache
        self.mouseButtons = {}  # type: dict[QtCore.Qt.MouseButton, QtWidgets.QMenu]

    def menu(self, button=QtCore.Qt.LeftButton):
        """Returns the menu for the given button.

        :param button: The button to get the menu for.
        :type button: :class:`QtCore.Qt.MouseButton`
        :return: The menu for the given button.
        :rtype: :class:`QtWidgets.QMenu`
        """
        return self.mouseButtons.get(button)

    def setMenu(self, menu, mouseButton):
        assert mouseButton in (QtCore.Qt.LeftButton, QtCore.Qt.RightButton), \
            "unsupported mouse button: {}".format(mouseButton)
        menu.setParent(self)
        self.mouseButtons[mouseButton] = menu
        # relay on built in QT context menu.
        if mouseButton == QtCore.Qt.RightButton:
            self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._showContextMenu)
        # relay on built in QT left click menu.
        elif mouseButton == QtCore.Qt.LeftButton:
            super(LeftAlignedButtonBase, self).setMenu(menu)

    def _showContextMenu(self, pos):
        """Shows the right click context menu at the given position.

        :param pos: The position to show the context menu at.
        :type pos: :class:`QtCore.QPoint`
        """
        menu = self.mouseButtons[QtCore.Qt.RightButton]
        menu.exec_(self.mapToGlobal(pos))

    def createMenuItem(self, text="", icon=None, connection=None, mouseClick=QtCore.Qt.RightButton):
        """Helper function to easily create a menu item, automatically creates the menu if it doesn't exist.

        :param text: The menu item text label
        :type text: str
        :param icon: The menu item icon.
        :type icon: :class:`QtGui.QIcon`
        :param connection: The menu item connection
        :type connection: function
        :param mouseClick: The mouse button to create the menu item for
        :type mouseClick: QtCore.Qt.RightButton or QtCore.Qt.LeftButton or QtCore.Qt.MiddleButton
        :return: The menu item as an action object
        :rtype: QtWidgets.QMenu.action
        """
        # Create menu, if it doesn't exist ------------------------------
        menu = self.menu(mouseClick)
        if not menu:
            menu = QtWidgets.QMenu(self)
            self.setMenu(menu, mouseClick)

        # Add the action ------------------------------
        action = menu.addAction(text)

        # Icon ------------------------------
        if icon:
            action.setIcon(icon)

        # Connection ------------------------------
        if connection:
            action.triggered.connect(connection)

        return action


def leftAlignedButton(text, icon=None, toolTip="", parent=None, transparentBg=False,
                      padding=(), alignment="left", showLeftClickMenuIndicator=False):
    """Creates a left aligned button, passes in the icon name and text, and sets the stylesheet.

    Can take two icons as strings, resource buttons ie Software Default Icons are specified with a colon in the name.

        icon = ":polyRemesh"

    Zoo icons are specified without a colon in the name.

        icon = "save"

    :param text: The button label text
    :type text: str
    :param icon: The icon name, ":iconName" is resource icon, "save" is from Zoo icon library
    :type icon: :class:`QtGui.QIcon`
    :param toolTip: The tooltip text
    :type toolTip: str
    :param parent: The parent widget
    :type parent: object
    :param transparentBg: True if the background is transparent
    :type transparentBg: bool
    :param padding: The padding of the button (left, top, right, bottom), empty tuple if no override
    :type padding: tuple(int, int, int, int)
    :param alignment: the alignment of the icon and text, default is "left", can use "right" or "center"
    :type alignment: str
    :param showLeftClickMenuIndicator: If True allow the left-click menu indicator to show, default is False
    :type showLeftClickMenuIndicator: bool
    :return: The button as a Qt widget
    :rtype: LeftAlignedButtonBase
    """
    stylesheet = "QPushButton {"

    # Set Padding ---------------------------------------------------------------
    if not padding:
        padding = uic.ZOO_BTN_PADDING
    padding = list(map(utils.dpiScale, padding))

    # Alignment -------------------------------------------------------------------
    stylesheet += "text-align: {};".format(alignment)
    stylesheet += "padding-left: {}px; padding-top: {}px; padding-right: {}px; padding-bottom: {}px;".format(
        str(padding[0]), str(padding[1]), str(padding[2]), str(padding[3]))

    # BG Transparency -------------------------------------------------------------
    if transparentBg:
        stylesheet += "background-color: transparent;"
    # Create Button ---------------------------------------------------------------
    btn = LeftAlignedButtonBase(text, parent=parent, icon=icon, toolTip=toolTip)
    stylesheet += "}"
    if not showLeftClickMenuIndicator:
        stylesheet += "QPushButton::menu-indicator { image: none; };"  # disables the automatic triangle menu indicator

    # Do the alignment ---------------------------------------------------------------
    btn.setStyleSheet(stylesheet)
    return btn
