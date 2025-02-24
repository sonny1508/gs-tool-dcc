from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import dialog, flowlayout, layouts
from zoo.libs.pyqt.widgets import iconmenu


class FlowToolBar(QtWidgets.QFrame):
    """
    A tool bar based off the FlowLayout. The buttons will flow from left to right and wrap to
    the next row if there is no space

    .. code-block:: python

        flowToolbar = FlowToolBar()
        flowToolbar.addTool("stream2", name="Tool Button Name", iconColor=(255,255,255))
        flowToolbar.addToolMenu("stream2", name="Tool Button Name", actions=[('Menu Item 1', func1),('Menu Item 2',
                                func2)])

        def func1():
            pass
        def func2():
            pass

    """
    overflowIcon = "sortDown"

    def __init__(self, parent=None, menuIndicatorIcon="arrowmenu", iconSize=20, iconPadding=2):
        super(FlowToolBar, self).__init__(parent)
        self.mainLayout = layouts.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=0)

        self.flowLayout = flowlayout.FlowLayout(margin=0, spacingX=1, spacingY=1)
        self.mainLayout.addLayout(self.flowLayout)

        self.setLayout(self.mainLayout)
        self.iconSize = iconSize
        self.iconPadding = iconPadding
        self.overflowBtnColor = (128, 128, 128)
        self.menuIndicatorIcon = menuIndicatorIcon

        self.overflowMenu = False
        self.overflowMenuBtn = None  # type: iconmenu.IconMenuButton
        self.overflowMenuDlg = FlowToolbarMenu(parent=self)
        self.overflowLayout = self.overflowMenuDlg.layout()

        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)

        self.initUi()

    def initUi(self):
        """ Initialise flow toolbar ui
        """
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.overflowMenuBtn = self.setupOverflowMenu()
        self.flowLayout.addWidget(self.overflowMenuBtn)

    def setDebugColors(self, debug):
        """ Set debug colors

        :param debug:
        :return:
        """
        if debug:
            self.setStyleSheet("background-color: #005522")
        else:
            self.setStyleSheet("")

    def setIconSize(self, size):
        """Set the size of the icons of the tools and toolmenus


        :param size: DPI scale is automatically calculated here so size does not need it here.
        """
        self.iconSize = size

        # Set the icon size, possibly will need to get them to get a new icon through iconColorized
        for i in range(0, self.flowLayout.count()):
            widget = self.flowLayout.itemAt(i).widget()
            widget.setIconSize(self.getIconSize())

        self.overflowMenuBtn = self.setupOverflowMenu(self.overflowMenuBtn)

    def setIconPadding(self, padding):
        """Sets the padding for the icons of the tools and the tool menus

        :param padding:
        """
        self.iconPadding = utils.dpiScale(padding)

    def overflowMenuActive(self, active):
        self.overflowMenu = active
        self.overflowMenuBtn.setVisible(active)

    def setOverflowButtonColor(self, col):
        """Sets the color for the overflow button

        :param col:
        :return:
        """
        self.overflowBtnColor = col

    def setupOverflowMenu(self, btn=None):
        """ Setup the overflow menu and connect it to btn. If there's no button yet create one.

        :param btn:
        :return:
        """
        col = self.overflowBtnColor
        icon = self.overflowIcon
        if btn is None:
            btn = iconmenu.IconMenuButton(parent=self)

        btn.setIconByName(icon, colors=col, size=self.iconSize, colorOffset=40)

        btn.setDoubleClickEnabled(False)
        btn.setProperty("name", "overflow")
        btn.setIconSize(self.getIconSize())
        btn.setVisible(False)
        btn.setFixedWidth(29)

        return btn

    def addToolButton(self, iconName, name="", iconColor=(255, 255, 255), doubleClickEnabled=False):
        """ Creates a new tool button based on the icon name, and the name.

        :param iconName: Name of the icon to retrieve
        :param name: Name of the tool
        :param iconColor: Color of the icon for the tool
        :param doubleClickEnabled: Enable doubleclick for button
        :return:
        :rtype: iconmenu.IconMenuButton
        """
        # Create an item with a caption
        btn = iconmenu.IconMenuButton(parent=self, themeUpdates=False)
        name = name or iconName

        btn.setIconByName(iconName, colors=iconColor, size=self.iconSize, colorOffset=40)

        btn.setDoubleClickEnabled(doubleClickEnabled)
        btn.setDoubleClickInterval(150)
        btn.setProperty("name", name)
        btn.setIconSize(self.getIconSize())
        btn.leftClicked.connect(self.toolsClicked)

        self.flowLayout.addWidget(btn)
        self.overflowMenuBtn.setParent(None)
        self.flowLayout.addWidget(self.overflowMenuBtn)  # add the overflowmenu button at the end
        self.flowLayout.setAlignment(btn, QtCore.Qt.AlignVCenter)

        # Avoid overflow button
        if name != "overflow":
            icon = iconlib.iconColorized(iconName, color=iconColor)
            self.overflowMenuBtn.addAction(name,
                                           icon=icon,
                                           connect=btn.leftClicked.emit)

        return btn

    def getIconSize(self):
        """ Returns the icon generated QSize

        :rtype: :class:`QtCore.QSize`
        """
        return QtCore.QSize(self.iconSize + self.iconPadding,
                            self.iconSize + self.iconPadding)

    def addToolMenu(self, iconName, name, actions, iconColor=(255, 255, 255), showIndicator=True):
        """ Adds a new tool menu.

        :param iconName: Name of the icon to retrieve
        :param name: Name of the tool
        :param actions: Actions is a list of tuples with the name and function to run eg ('Name', self.menuItemPressed)
        :param iconColor: The icon color
        :param showIndicator: Show the menu indicator (the arrow in the corner)
        """
        overlayName = None
        if showIndicator:
            overlayName = self.menuIndicatorIcon

        btn = iconmenu.IconMenuButton(parent=self)
        btn.setIconByName([iconName, overlayName], colors=iconColor, size=self.iconSize, colorOffset=40)
        btn.setProperty("name", name)
        btn.leftClicked.connect(self.toolsClicked)

        for a in actions:
            btn.addAction(a[0], connect=a[1])

        self.flowLayout.addWidget(btn)
        self.flowLayout.addWidget(self.overflowMenuBtn)

        # Avoid overflow button
        if name != "overflow":
            icon = iconlib.iconColorized(iconName, color=iconColor)
            self.overflowMenuBtn.addAction(name,
                                           icon=icon,
                                           connect=lambda x=btn: x.leftClicked.emit())
        return btn

    def clear(self):
        """Clear all widgets

        """
        self.overflowMenuBtn.clearMenu(QtCore.Qt.LeftButton)
        self.flowLayout.removeWidget(self.overflowMenuBtn)
        self.flowLayout.clear()
        utils.clearLayout(self.overflowLayout)

    def toolsClicked(self):
        """All buttons will run through here. It will then run a separate function telling which
        button was pressed, along with some other details

        """
        data = self.sender().property("name")
        self.buttonClicked(self.sender(), data)

    def resizeEvent(self, event):
        """ Resize event for the toolbar

        :param event:
        :return:
        """
        self.updateWidgetsOverflow(event.size())

    def sizeHint(self):
        """ Size hint for the flow toolbar

        :return:
        """
        spacingX = self.flowLayout.spacingX
        nextX = 0
        for item in self.flowLayout.itemList:
            wgt = item.widget()
            nextX += wgt.sizeHint().width() + spacingX

        return QtCore.QSize(nextX+3, super(FlowToolBar, self).sizeHint().height())

    def updateWidgetsOverflow(self, size=None):
        """ Hide or show widgets based on the size of the flow toolbar.

        If the flow toolbar is too small it will move widgets it to the overflow menu.

        If there are widgets in the overflow menu, place it back into the flow toolbar if there is space.

        :param size: new size
        :type size: QtCore.QSize
        :return:
        """
        if not self.overflowMenuBtn or self.overflowMenu is False:
            return
        items = self.itemList()

        if len(items) == 0:
            return

        if size is None:
            size = self.size()

        spacingX = self.flowLayout.spacingX
        spacingY = self.flowLayout.spacingY

        overflowBtnWidth = self.overflowMenuBtn.width()
        initWidth = size.width()
        menuWidth = initWidth - overflowBtnWidth - spacingX
        height = size.height()
        intoMenu = []

        # Reduce the flickering by disabling updates and processing first
        self.setUpdatesEnabled(False)

        nextX = 0
        nextY = items[0].widget().height()  # Height of the first item
        if self.overflowMenuBtn.isVisible():
            width = menuWidth
        else:
            width = initWidth

        for item in items:
            wgt = item.widget()
            wgtWidth = wgt.sizeHint().width() + spacingX
            nextX += wgtWidth

            if nextX > width:  # next level
                nextY += wgt.height()+(spacingY*2)
                nextX = 0

            if nextY > height:
                wgt.hide()
                intoMenu.append(wgt)
            else:
                wgt.show()

        # Set menu names visible
        names = [w.property('name') for w in intoMenu]
        self.setMenuItemsVisible(names)
        self.setUpdatesEnabled(True)

        return intoMenu

    def setMenuItemsVisible(self, texts):
        """ Set the texts visible in the menu.

        :param texts:
        :return:
        """
        menuVis = False
        menu = self.overflowMenuBtn.menu(mouseMenu=QtCore.Qt.LeftButton)
        # Show or hide menu items
        for a in reversed(menu.actions()):
            actionText = a.text()
            if actionText in texts:
                a.setVisible(True)
                menuVis = True
            else:
                a.setVisible(False)
        self.overflowMenuBtn.setVisible(menuVis)


    def itemList(self):
        """ Itemlist without the overflow menu button

        :return:
        """
        return self.flowLayout.itemList[:-1]

    def items(self):
        """ Flow layout items

        :return:
        """
        self.flowLayout.items()

    def buttonClicked(self, wgt, name):
        """O verridden by the subclass

        :param wgt: The widget that was pressed, typically a button
        :param name: The name of the tool
        """
        pass

    def setHeight(self, height):
        """ Set Fixed Height

        :param height:
        :return:
        """
        self.setFixedHeight(height)

    def setSpacingX(self, x):
        """ Set spacing of items in layout

        :param x:
        :return:
        """
        self.flowLayout.setSpacingX(x)

    def setSpacingY(self, y):
        """ Set spacing of items in layout

        :param y:
        :return:
        """
        self.flowLayout.setSpacingY(y)


class FlowToolbarMenu(dialog.Dialog):
    def __init__(self, parent=None):
        """ Icon Menu for flow toolbar. Creates a menu that only shows icons

        :param parent:
        """
        super(FlowToolbarMenu, self).__init__(parent=parent, showOnInitialize=False)
        self.mainLayout = utils.vBoxLayout(parent=self, margins=(0, 0, 0, 0), spacing=0)
        self.initUi()

    def initUi(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Popup)

    def layout(self):
        return self.mainLayout

    def sizeHint(self):
        return self.minimumSize()
    
    def show(self, *args, **kwargs):
        super(FlowToolbarMenu, self).show(*args, **kwargs)
        self.resize(self.sizeHint())
