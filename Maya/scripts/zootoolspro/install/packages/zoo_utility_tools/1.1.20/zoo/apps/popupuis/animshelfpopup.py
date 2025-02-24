"""" Zoo Tools Floating Shelf Window by Cosmo Park

from zoo.apps.popupuis import animshelfpopup
animshelfpopup.main()

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
from zoo.libs.utils import color
from zoo.libs.pyqt import uiconstants as uic

WINDOW_HEIGHT = 60

BTN_COUNT = 16
SLIDER_COUNT = 3
WINDOW_WIDTH = (BTN_COUNT * 40) + (SLIDER_COUNT * 100)
WINDOW_OFFSET_X = int(-(WINDOW_WIDTH / 2))
WINDOW_OFFSET_Y = -10
LIGHT_RED = [1.0, 0.6, 0.6]

ICON = "icon"
TOOLTIP = "tooltip"
ID = "id"
TYPE = "type"
ARGUMENTS = "arguments"

SHELF_DICT = {
    "tweenMachine": {ICON: "blender", TOOLTIP: "Tween Machine Options", ID: "zoo.tweenMachine", TYPE: "action",
                     ARGUMENTS: {}},
    "randomizeAnim": {ICON: "noise", TOOLTIP: "Randomize Animation Options", ID: "zoo.randomizeAnim", TYPE: "action",
                      ARGUMENTS: {}},
    "scaleTweener": {ICON: "scaleKeyCenter", TOOLTIP: "Scale Tweener Options", ID: "zoo.bakeAnim", TYPE: "action",
                     ARGUMENTS: {}},
    "makeAnimHold": {ICON: "animHold", TOOLTIP: "Make Anim Hold", ID: "zoo.makeAnimHold", TYPE: "action",
                     ARGUMENTS: {}},
    "keyVisToggle": {ICON: "eye", TOOLTIP: "Key Visibility Toggle", ID: "zoo.keyVisToggle", TYPE: "action",
                     ARGUMENTS: {}},
    "deleteKey": {ICON: "delKey", TOOLTIP: "Delete Key Current Time", ID: "zoo.delKey", TYPE: "action",
                  ARGUMENTS: {}},
    "resetAttrs": {ICON: "arrowBack", TOOLTIP: "Reset Selected Or All Attributes", ID: "zoo.resetAttr", TYPE: "action",
                   ARGUMENTS: {}},
    "bakeAnim": {ICON: "bake", TOOLTIP: "Bake Animation Selected", ID: "zoo.bakeAnim", TYPE: "action",
                 ARGUMENTS: {}},
    "limitCycleTime": {ICON: "clampTime", TOOLTIP: "Limit Cycle Time", ID: "zoo.limitCycleTime", TYPE: "action",
                       ARGUMENTS: {}},
    "snapToTime": {ICON: "snapTime", TOOLTIP: "Snap To Current Time", ID: "zoo.snapToTime", TYPE: "action",
                   ARGUMENTS: {}},
    "snapToWholeFrames": {ICON: "magnet", TOOLTIP: "Snap ToWhole Frames", ID: "zoo.snapTimeWholeFrames", TYPE: "action",
                          ARGUMENTS: {}},
    "timeToSelected": {ICON: "timeToSelected", TOOLTIP: "Move Time To Sel Key", ID: "zoo.bakeAnim", TYPE: "action",
                       ARGUMENTS: {}},
    "mirrorPose": {ICON: "symmetryTri", TOOLTIP: "Mirror Pose (right-click)", ID: "zoo.mirrorPose", TYPE: "action",
                   ARGUMENTS: {}},
    "flipPose": {ICON: "mirrorGeo", TOOLTIP: "Flip Pose (right-click)", ID: "zoo.flipPose", TYPE: "action",
                 ARGUMENTS: {}},
    "selectAnimation": {ICON: "cursorSelect", TOOLTIP: "Select Animated Objects", ID: "zoo.selAnim", TYPE: "action",
                        ARGUMENTS: {}},

}


class MyPopupToolbar(elements.ZooWindow):

    def __init__(self, name="zooAnimShelf", title="Zoo Anim Shelf", parent=None, resizable=True, width=WINDOW_WIDTH,
                 height=WINDOW_HEIGHT,
                 modal=False, alwaysShowAllTitle=False, minButton=False, maxButton=False, onTop=False,
                 saveWindowPref=False, titleBar=None, overlay=True, minimizeEnabled=True, initPos=None, qtPopup=False,
                 titleBarVisible=False):
        super(MyPopupToolbar, self).__init__(name, title, parent, resizable, width, height, modal, alwaysShowAllTitle,
                                             minButton, maxButton, onTop, saveWindowPref, titleBar, overlay,
                                             minimizeEnabled, initPos, titleBarVisible)

        self.setStyleSheet("background-color: rgba(60, 60, 60, 150);") # Set background transparent
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
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

    def createIconButton(self, icon, toolTip=None, colorRGB=None, size=16):
        btn = QtWidgets.QToolButton(parent=self)
        btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        if colorRGB:
            intColor = color.rgbFloatToInt(colorRGB)
            icon = self._icon(icon, iconColor=intColor)
        else:
            icon = self._icon(icon)
        btn.setIcon(icon)

        btn.setText(toolTip)
        btn.setToolTip(toolTip)
        iconSize = utils.dpiScale(size)
        btn.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        btn.setIconSize(QtCore.QSize(iconSize, iconSize))

        btn.setStyleSheet("background-color: transparent;")
        btn.setStyleSheet("::menu-indicator { image: none; }")
        btn.setStyleSheet("""QToolTip { 
                                   background-color: black; 
                                   color: white; 
                                   border: black solid 1px
                                   }""")
        # self.button.setStyleSheet("QToolTip { background-color: yellow; color: black; border: 1px solid black; }")

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

    def buildShelfButton(self, toolDict, colorRGB=None):
        btn = self.createIconButton(toolDict[ICON], toolDict[TOOLTIP], colorRGB=colorRGB)
        btn.clicked.connect(partial(self.executePluginById, toolDict[ID], toolDict[ARGUMENTS]))
        return btn

    def widgets(self):
        self.buttonList = list()
        self.menuList = list()

        self.buttonList.append(self.buildShelfButton(SHELF_DICT["tweenMachine"], colorRGB=LIGHT_RED))
        self.tweenSlider = elements.Slider(defaultValue=0.5,
                                           toolTip="Tween Machine Slider",
                                           minValue=-0.25,
                                           maxValue=1.25)
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["randomizeAnim"], colorRGB=LIGHT_RED))
        self.randomSlider = elements.Slider(defaultValue=0.5,
                                            toolTip="Randomize Animation Slider",
                                            minValue=-0.25,
                                            maxValue=1.25)
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["scaleTweener"], colorRGB=LIGHT_RED))
        self.scaleSlider = elements.Slider(defaultValue=0.5,
                                           toolTip="Scale Animation Slider",
                                           minValue=-0.25,
                                           maxValue=1.25)
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["selectAnimation"], colorRGB=LIGHT_RED))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["keyVisToggle"], colorRGB=LIGHT_RED))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["deleteKey"], colorRGB=LIGHT_RED))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["bakeAnim"], colorRGB=LIGHT_RED))
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["snapToTime"], colorRGB=LIGHT_RED))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["snapToWholeFrames"], colorRGB=LIGHT_RED))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["timeToSelected"], colorRGB=LIGHT_RED))
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["limitCycleTime"], colorRGB=LIGHT_RED))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["makeAnimHold"], colorRGB=LIGHT_RED))
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["mirrorPose"], colorRGB=LIGHT_RED))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["flipPose"], colorRGB=LIGHT_RED))

        self.closeBtn = self.createIconButton("closeX")
        self.closeBtn.setToolTip("Close the floating shelf window.")
        self.closeBtn.clicked.connect(self.close)

        return
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
        self.mainLayout = elements.hBoxLayout(spacing=6, margins=(12, 6, 12, 2))
        for i, btn in enumerate(self.buttonList):
            if i == 1:
                self.mainLayout.addWidget(self.tweenSlider)
                self.mainLayout.addWidget(btn)
            elif i == 3:
                self.mainLayout.addWidget(self.randomSlider)
                self.mainLayout.addWidget(btn)
            elif i == 5:
                self.mainLayout.addWidget(self.scaleSlider)
                self.mainLayout.addWidget(btn)
            else:
                self.mainLayout.addWidget(btn)
        self.mainLayout.addWidget(self.closeBtn)
        self.setMainLayout(self.mainLayout)


def main():
    point = QtGui.QCursor.pos()
    point.setX(point.x() + WINDOW_OFFSET_X)
    point.setY(point.y() + WINDOW_OFFSET_Y)

    eng = engine.currentEngine()
    win = eng.showDialog(MyPopupToolbar, "zooAnimFloatingShelf", show=False)
    win.show(point)
