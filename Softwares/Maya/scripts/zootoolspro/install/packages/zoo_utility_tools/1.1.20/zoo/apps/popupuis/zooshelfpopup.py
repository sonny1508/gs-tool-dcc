"""" Zoo Tools Floating Shelf Window by Cosmo Park

from zoo.apps.popupuis import zooshelfpopup
zooshelfpopup.main()

"""


from functools import partial

from zoo.core.plugin import pluginmanager
from zoo.apps.toolpalette.palette import PluginTypeBase
from zoo.apps.toolpalette.palette import ActionType

from zoo.libs.pyqt.widgets import elements

from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoo.apps.toolpalette import run
from zoo.core import engine


WINDOW_HEIGHT = 64
BTN_COUNT = 17

WINDOW_OFFSET_X = int(-(BTN_COUNT / 2 * 32))
WINDOW_OFFSET_Y = -10


class MyPopupToolbar(elements.ZooWindowThin):

    def __init__(self, name="", title="", parent=None, resizable=True, width=BTN_COUNT * 32, height=WINDOW_HEIGHT,
                 modal=False, alwaysShowAllTitle=False, minButton=False, maxButton=False, onTop=False,
                 saveWindowPref=False, titleBar=None, overlay=True, minimizeEnabled=True, initPos=None, qtPopup=False):
        super(MyPopupToolbar, self).__init__(name, title, parent, resizable, width, height, modal, alwaysShowAllTitle,
                                             minButton, maxButton, onTop, saveWindowPref, titleBar, overlay,
                                             minimizeEnabled, initPos)
        if qtPopup:
            self.parentContainer.setWindowFlags(self.parentContainer.defaultWindowFlags | QtCore.Qt.Popup)
        self._buildPluginMap()
        self.widgets()
        self.layout()

    def _buildPluginMap(self):
        self.typeRegistry = pluginmanager.PluginManager(interface=[PluginTypeBase],
                                                        variableName="id", name="ToolPaletteType")
        self.typeRegistry.registerByEnv("ZOO_TOOLPALETTE_PLUGINTYPE_PATH")
        self.typeRegistry.registerPlugin(ActionType)
        for p in self.typeRegistry.plugins.keys():
            self.typeRegistry.loadPlugin(p, toolPalette=self)
        self._pluginIdMap = {}  # pluginId, pluginType ie. definition

        for pluginId, pluginType in self.typeRegistry.loadedPlugins.items():
            for toolPluginId in pluginType.plugins():
                self._pluginIdMap[toolPluginId] = pluginId

    # -------------
    # CREATE A BUTTON
    # -------------

    def _icon(self, iconName, path=False, iconColor=None, overlayName=None, overlayColor=(255, 255, 255)):
        iconSize = utils.dpiScale(32)
        if path:
            return iconlib.iconPathForName(iconName, size=iconSize)
        if iconColor:
            icon = iconlib.iconColorized(iconName, size=iconSize, color=iconColor, overlayName=overlayName,
                                         overlayColor=overlayColor)
        else:
            icon = iconlib.icon(iconName, size=iconSize)

        if icon is None:
            return
        elif not icon.isNull():
            return icon

    def createIconButton(self, icon, toolTip=None):
        btn = QtWidgets.QToolButton(parent=self)
        btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        icon = self._icon(icon)
        btn.setIcon(icon)

        btn.setText(toolTip)
        btn.setToolTip(toolTip)
        iconSize = utils.dpiScale(32)
        btn.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        btn.setIconSize(QtCore.QSize(iconSize, iconSize))

        btn.setStyleSheet('::QToolTip { color: #FFFFFF; background-color: #1E1E1E; }')
        btn.setStyleSheet("background-color: transparent;")
        btn.setStyleSheet("::menu-indicator { image: none; }")

        menu = QtWidgets.QMenu()
        self.menuList.append(menu)
        return btn

    def createMenuItem(self, label, icon, color, button, menu, pluginId):
        # Create the menu items with icons
        menuItem = QtWidgets.QAction(label, self)
        menuItemIcon = self._icon(icon, iconColor=color)
        menuItem.setIcon(menuItemIcon)
        menuItem.setObjectName(pluginId)
        menu.addAction(menuItem)
        button.setMenu(menu)
        return menuItem

    def executePluginById(self, pluginId, *args, **kwargs):
        """Executes the tool definition plugin by the id string.

        :param pluginId: The tool definition id.
        :type pluginId: str
        :param args: The arguments to pass to the execute method
        :type args: tuple
        :param kwargs: The keyword arguments to pass to the execute method
        :type kwargs: dict
        :return: The executed tool definition instance or none
        :rtype: :class:`ActionPlugin` or None
        """
        pluginType = self._pluginIdMap.get(pluginId)
        if pluginType is None:
            return
        pluginCls = self.typeRegistry.getPlugin(pluginType)
        return pluginCls.executePlugin(pluginId, *args, **kwargs)

    # -------------
    # MAKE ALL BUTTONS
    # -------------

    def widgets(self):
        self.buttonList = list()
        self.menuList = list()

        instance = run.currentInstance()
        for shelf in instance.shelfManager.shelves:
            if shelf.label != "ZooToolsPro":
                continue
            for i, shelfIcon in enumerate(shelf.children):  # shelf buttons
                if shelfIcon.isShelfButton():
                    btn = self.createIconButton(shelfIcon.icon, shelfIcon.tooltip)
                    btn.clicked.connect(partial(self.executePluginById, shelfIcon.id, **shelfIcon.arguments))
                    self.buttonList.append(btn)
                elif shelfIcon.isSeparator():
                    btn = self.createIconButton("separator_shlf")
                    self.buttonList.append(btn)
                else:
                    btn = self.createIconButton(shelfIcon.icon, shelfIcon.tooltip)
                    btn.clicked.connect(partial(self.executePluginById, shelfIcon.id, **shelfIcon.arguments))
                    self.buttonList.append(btn)
                for menuItem in shelfIcon.children:
                    if menuItem.type == "action":
                        MI = self.createMenuItem(menuItem.label, menuItem.icon, menuItem.iconColor,
                                                 self.buttonList[i], self.menuList[i], menuItem.id)
                        MI.triggered.connect(partial(self.executePluginById, menuItem.id, **menuItem.arguments))
                    elif menuItem.type == "toolset":
                        MI = self.createMenuItem(menuItem.label, menuItem.icon, menuItem.iconColor,
                                                 self.buttonList[i], self.menuList[i], menuItem.id)
                        MI.triggered.connect(partial(self.executePluginById, menuItem.id, **menuItem.arguments))
                    elif menuItem.isSeparator():
                        self.menuList[i].addSeparator()
                    else:  # Variants -----------------
                        MI = self.createMenuItem(menuItem.label, menuItem.icon, menuItem.iconColor,
                                                 self.buttonList[i], self.menuList[i], menuItem.id)
                        MI.triggered.connect(partial(self.executePluginById, shelfIcon.id, **menuItem.arguments))

    # -------------
    # LAYOUT UI
    # -------------

    def layout(self):
        self.mainLayout = elements.hBoxLayout(spacing=3, margins=(2, 2, 2, 2))
        for btn in self.buttonList:
            self.mainLayout.addWidget(btn)

        self.setMainLayout(self.mainLayout)


def main():
    point = QtGui.QCursor.pos()
    point.setX(point.x() + WINDOW_OFFSET_X)
    point.setY(point.y() + WINDOW_OFFSET_Y)

    eng = engine.currentEngine()
    win = eng.showDialog(MyPopupToolbar, "zooFloatingShelf", show=False)
    win.show(point)
