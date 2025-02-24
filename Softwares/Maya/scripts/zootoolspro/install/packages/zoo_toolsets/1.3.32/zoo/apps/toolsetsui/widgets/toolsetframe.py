from functools import partial

from zoovendor.Qt import QtWidgets, QtCore, QtGui


from zoo.apps.toolsetsui.widgets import toolsettoolbar, toolsettree
from zoo.apps.toolsetsui.widgets import toolsetwidgetitem
from zoo.apps.toolsetsui.widgets.menubutton import ToolsetMenuButton
from zoo.libs.pyqt import  utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import iconmenu


class ToolsetFrame(QtWidgets.QFrame):
    """ ToolsetFrame which has the main body of the toolset ui.

    Includes the toolbar
    (:class:`zoo.apps.toolsetsui.widgets.toolsettoolbar.ToolsetToolBar`)

    which is moved to the frameless window header area later
    (:class:`zoo.apps.toolsetsui.widgets.frameless.TitleBar`),


    """
    resizeRequested = QtCore.Signal()
    toolsetToggled = QtCore.Signal()
    toolsetClosed = QtCore.Signal(object)

    def __init__(self, parent, toolsetRegistry, window, iconColor=(255, 255, 255), 
                 hueShift=-30, showMenuBtn=True, initialGroup=None, iconSize=20, 
                 iconPadding=2, startHidden=False, switchOnClick=True, toolbarHidden=False):
        """ Initialise ToolsetFrame which has the main body of the toolset ui. Includes
        the toolbar which is moved to the frameless window header area later, and the
        toolset menus.

        Usage. Place frame in intended area for toolbar, and move the tree into the desired layout location

        :type window: :class:`zoo.apps.toolsetsui.toolsetui.ToolsetsUI`
        :type parent:
        :param toolsetRegistry:
        :type toolsetRegistry: :class:`zoo.apps.toolsetsui.registry.ToolsetRegistry`

        :param iconColor:
        :param hueShift:
        """
        super(ToolsetFrame, self).__init__(parent=parent)
        if startHidden:
            self.hide()
        self.toolsetUi = window 
        self.toolsetRegistry = toolsetRegistry
        self.mainLayout = elements.vBoxLayout(self)
        self.topbarLayout = elements.hBoxLayout()
        self.toolbar = toolsettoolbar.ToolsetToolBar(toolbarFrame=self, parent=self, toolsetRegistry=self.toolsetRegistry,
                                                     iconSize=iconSize, iconPadding=iconPadding, startHidden=toolbarHidden)
        self.tree = toolsettree.ToolsetTreeWidget(self, self.toolsetRegistry)
        self.currentGroup = None  # type: str  # groupType as string
        self.menuBtn = ToolsetMenuButton(self, size=16, toolsetRegistry=self.toolsetRegistry)
        self.menuBtn.setVisible(showMenuBtn)

        self.iconColor = iconColor
        self.hueShift = hueShift
        self.switchOnClick = switchOnClick

        # Set to first
        gTypes = self.toolsetRegistry.groupTypes()
        if gTypes:
            gTypes = gTypes[0]
        self.setGroup(initialGroup or gTypes)

        # Add toolset frame to global list. Tad hacky may revisit
        from zoo.apps.toolsetsui import toolsetui
        toolsetui.addToolsetFrame(self)

        self.initUi()
        self.initMenuBtn()

    def showToolbar(self):
        """ Show the toolbar

        :return:
        """
        self.toolbar.show()

    def hideToolbar(self):
        """ Hide the toolbar

        :return:
        """
        self.toolbar.hide()

    def initMenuBtn(self):
        """ Init menu button

        :return:
        """
        self.menuBtn.setMenuAlign(QtCore.Qt.AlignRight)

    def setDebugColors(self, debug):
        """ Set debug colors

        :param debug:
        :return:
        """
        if debug:
            self.setStyleSheet("background-color: darkred")
        else:
            self.setStyleSheet("")

    def initUi(self):
        """ Initialise UI

        :return:
        """
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.topbarLayout.addWidget(self.toolbar)
        self.topbarLayout.setContentsMargins(*utils.marginsDpiScale(0, 3, 0, 0))
        self.topbarLayout.addSpacing(0)
        self.toolbar.setIconSize(18)
        self.toolbar.setIconPadding(1)
        self.toolbar.flowLayout.setSpacingY(utils.dpiScale(3))


        self.menuBtn.setMenuAlign(QtCore.Qt.AlignRight)
        self.mainLayout.addLayout(self.topbarLayout)
        self.mainLayout.addWidget(self.tree)

    def toolset(self, toolsetId):
        """ Retrieves toolset object in the toolsetTree by its name if it exists

        :return:
        :rtype: toolsetwidgetitem.ToolsetWidgetItem
        """
        return self.tree.toolset(toolsetId)

    def toolsetById(self, toolsetId):
        """ Get toolset by id

        :param toolsetId:
        :type toolsetId:
        :return:
        :rtype: zoo.apps.toolsetsui.widgets.toolsetwidget.ToolsetWidget
        """
        if self.tree:
            toolset = self.tree.toolset(toolsetId)
            if toolset:
                return toolset.widget

    def calcSizeHint(self):
        """ Calculate height based on the contents of the tree
        :rtype self.mainLayout:
        :return:
        """
        size = self.sizeHint()
        width = size.width()
        height = self.tree.calculateContentHeight()
        return QtCore.QSize(width, height)

    def lastHidden(self):
        return self.tree.lastHidden

    def setGroup(self, groupType):
        """ Update the icons in the toolbar based on groupType.
        Toolset groups are found in toolsetgroups.py

        :param groupType: If group type is none, just get currently selected in ui
        :return:
        """
        if not groupType:
            # output.displayWarning("No group type specified for toolsets")
            return

        if self.currentGroup == groupType:
            # If its already the same group then just return
            return

        self.toolbar.clear()
        toolsets = self.toolsetRegistry.toolsets(groupType)
        color = self.toolsetRegistry.groupColor(groupType)
        self.currentGroup = groupType

        self.iconColor = color

        # Add new button
        for t in toolsets:
            self.addToolset(t)

        QtCore.QTimer.singleShot(0, self.forceRefresh)

    def forceRefresh(self):
        """ Force window refresh

        :return:
        :rtype:
        """
        QtWidgets.QApplication.processEvents()  # To make sure the toolbar dimensions is updated first
        self.toolbar.updateWidgetsOverflow()
        self.setUpdatesEnabled(False)
        # Hacky way of forcing a refresh since window().updateGeometry() isn't enough
        window = self.toolsetUi.parentContainer
        size = window.size()
        window.setUpdatesEnabled(False)
        window.resize(size.width() + 1, size.height())
        window.resize(size.width(), size.height())
        window.setUpdatesEnabled(True)
        self.setUpdatesEnabled(True)
        self.updateColors()

    def addToolset(self, toolset):
        """ Add toolset to toolbar

        :param toolset:
        :type toolset: class def or subclass of toolsetwidgetitem.ToolsetWidgetItem
        :return:
        """

        newButton = self.toolbar.addToolset(toolset, toggleConnect=self.toggleToolset)
        newButton.rightClicked.disconnect()
        newButton.rightClicked.connect(lambda: self.toolsetRightClickMenu(newButton.property("toolsetId"), newButton))

    def toolsetRightClickMenu(self, toolsetId, button):
        """ The toolset right click menu

        :param toolsetId:
        :type toolsetId:
        :param button:
        :type button: iconmenu.IconMenuButton
        :return:
        :rtype:
        """

        item = self.toolset(toolsetId)

        # Create a toolset if no toolset is found. This might be slow on first right click
        if item is None:
            item = self.toggleToolset(toolsetId, hidden=True)

        widget = item.widget
        actions = widget.actions()
        button.clearMenu(QtCore.Qt.RightButton)
        for a in actions:
            button.addAction(a['label'],
                             mouseMenu=QtCore.Qt.RightButton,
                             connect=partial(widget.executeActions, a),
                             icon=a.get('icon'))

        button.contextMenu(QtCore.Qt.RightButton)

    def toggleToolset(self, toolsetId, activate=True, hidden=False, keepOpen=False):
        """ Add toolset by toolsetId (their ID) or toggle

        This should be moved to toolsetframe

        :param keepOpen: Keep the toolset open
        :type keepOpen: bool
        :param toolsetId: The toolset to add
        :type toolsetId: basestring
        :param activate: Toggle Toolset activated true or flase
        :type activate: bool
        :param hidden: Show the toolset widget hidden
        :return:
        :rtype: toolsetwidgetitem.ToolsetWidgetItem
        """

        item = self.tree.toolset(toolsetId)  # type: ToolsetWidgetItem

        if item:
            if not keepOpen or item.hidden:
                item.toggleHidden(activate=activate)
        else:
            item = self.tree.addToolset(toolsetId, activate=activate)

            if self.switchOnClick:
                groupType = self.toolsetRegistry.groupFromToolset(toolsetId)
                self.setGroup(groupType)

        # Hide it if we need to
        if hidden:
            item.setHidden(True)

        self.resizeRequested.emit()
        self.toolsetToggled.emit()
        self.updateColors()

        return item

    def toolsets(self):
        return self.tree.toolsets()

    def openToolset(self, toolsetId, activate=True):
        self.toggleToolset(toolsetId, keepOpen=True)

    def setIconColour(self, iconColour):
        """ Set Icon colour

        :param iconColour:
        :type iconColour:
        :return:
        :rtype:
        """
        self.iconColor = iconColour

    def setGroupFromToolset(self, toolsetId):
        """ Sets the group based on toolset ID given

        :param toolsetId:
        :type toolsetId:
        :return:
        :rtype:
        """
        groupType = self.toolsetRegistry.groupFromToolset(toolsetId)
        self.setGroup(groupType)

        utils.singleShotTimer(self.groupUpdateUi)

    def groupUpdateUi(self):
        """ Update ui for set group

        :return:
        :rtype:
        """
        self.updateColors()
        self.update()
        utils.processUIEvents()

    def updateColors(self):
        """ Update colors of the toolbar buttons and toolset icon popup

        :return:
        """

        # Get flow toolbar buttons
        widgets = [r.widget() for r in self.toolbar.flowLayout.itemList] + \
            utils.layoutWidgets(self.toolbar.overflowLayout)

        activeItems = self.tree.activeItems()

        actives = []
        for a in activeItems:
            item = a[0]

            if a[1] != toolsettree.ToolsetTreeWidget.ActiveItem_Hidden:
                actives.append(item.widget.id)

        self.menuBtn.toolsetPopup.updateColors(actives)

        # Change colours based on if active
        for w in widgets:
            if w.property('toolsetId') in actives:
                w.setIconColor(tuple(w.property('color')))
            else:
                col = w.property('colorDisabled') or (128, 128, 128)
                w.setIconColor(tuple(col))