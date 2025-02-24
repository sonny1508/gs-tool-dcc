"""" Zoo Tools Floating Shelf Window by Cosmo Park

from zoo.apps.popupuis import riggingshelfpopup
riggingshelfpopup.main()

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

BTN_COUNT = 19
WINDOW_WIDTH = (BTN_COUNT * 40)
WINDOW_OFFSET_X = int(-(WINDOW_WIDTH / 2))
WINDOW_OFFSET_Y = -10
LIGHT_BLUE = [0.6, 0.75, 0.82]
WHITE = [.8, .8, .8]

ICON = "icon"
TOOLTIP = "tooltip"
ID = "id"
TYPE = "type"
ARGUMENTS = "arguments"

SHELF_DICT = {
    "controlCreator": {ICON: "starControl", TOOLTIP: "Open Control Creator UI", ID: "zoo.controlCreator", TYPE: "action",
                       ARGUMENTS: {}},
    "editControls": {ICON: "pliers", TOOLTIP: "Open Edit Controls UI (Right-Click)", ID: "zoo.editControls", TYPE: "action",
                       ARGUMENTS: {}},
    "colorOverrides": {ICON: "paintLine", TOOLTIP: "Open Color Overrides UI (Right-Click)", ID: "zoo.colorOverrides", TYPE: "action",
                           ARGUMENTS: {}},
    "freezeMatrix": {ICON: "matrix", TOOLTIP: "FreezeMatrix (Right-Click)", ID: "zoo.freezeMatrix", TYPE: "action",
                           ARGUMENTS: {}},
    "selectMenu": {ICON: "cursorSelect", TOOLTIP: "Select Menu (Left-Click)", ID: "zoo.selectMenu", TYPE: "action",
                               ARGUMENTS: {}},
    "jointToolWindow": {ICON: "pliers", TOOLTIP: "Open The Joint Tool Window (Right-Click)", ID: "zoo.jointToolWindow", TYPE: "action",
                               ARGUMENTS: {}},
    "constraintToolbox": {ICON: "transfer", TOOLTIP: "Open The Constraint Toolbox (Right-Click)", ID: "zoo.constraintToolbox", TYPE: "action",
                     ARGUMENTS: {}},
    "zooRenamer": {ICON: "zooRenamer", TOOLTIP: "Open The Zoo Renamer UI (Right Click)", ID: "zoo.constraintToolbox", TYPE: "action",
                     ARGUMENTS: {}},
    "skinSelected": {ICON: "skinYoga", TOOLTIP: "Skin Selected (Right-Click)", ID: "zoo.skinSelected", TYPE: "action",
                      ARGUMENTS: {}},
    "transferSkinWeights": {ICON: "transfer", TOOLTIP: "Transfer Skin Weights (Right-Click)", ID: "zoo.skinSelected", TYPE: "action",
                      ARGUMENTS: {}},
    "mirrorSkinWeights": {ICON: "symmetryTri", TOOLTIP: "Mirror Skin Weights (Right-Click)", ID: "zoo.mirrorSkinWeights", TYPE: "action",
                     ARGUMENTS: {}},
    "duplicateOriginalMesh": {ICON: "duplicate", TOOLTIP: "Duplicate Original Mesh", ID: "zoo.duplicateOriginalMesh", TYPE: "action",
                     ARGUMENTS: {}},
    "addJoints": {ICON: "plus", TOOLTIP: "Add Joints (Right-Click)", ID: "zoo.keyVisToggle", TYPE: "action",
                     ARGUMENTS: {}},
    "hiveUI": {ICON: "hive", TOOLTIP: "Open The Hive UI (Right-Click)", ID: "zoo.hiveArtistUI", TYPE: "action",
                         ARGUMENTS: {}},
    "brSmoothSkinWeights": {ICON: "brSmoothSkinWeights", TOOLTIP: "Smooth Skin Weights - brave rabbit", ID: "zoo.brSmoothSkinWeights", TYPE: "action",
                  ARGUMENTS: {}},
    "skinWrangler": {ICON: "mergeVertex", TOOLTIP: "Skin Wrangler - Chris Evans", ID: "zoo.skinWrangler", TYPE: "action",
                   ARGUMENTS: {}},
    "brTransferSkinWeights": {ICON: "importArrow", TOOLTIP: "Import/Export Skinning - braverabbit", ID: "zoo.skinWrangler", TYPE: "action",
                       ARGUMENTS: {}},

}


class MyPopupToolbar(elements.ZooWindow):

    def __init__(self, name="", title="Zoo Rigging Shelf", parent=None, resizable=True, width=WINDOW_WIDTH,
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

        self.buttonList.append(self.buildShelfButton(SHELF_DICT["controlCreator"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["editControls"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["colorOverrides"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["freezeMatrix"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["selectMenu"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["jointToolWindow"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["constraintToolbox"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["skinSelected"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["addJoints"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["transferSkinWeights"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["mirrorSkinWeights"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["duplicateOriginalMesh"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["hiveUI"], colorRGB=LIGHT_BLUE))
        self.buttonList.append(self.createIconButton("separator_shlf"))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["skinWrangler"], colorRGB=WHITE))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["brSmoothSkinWeights"], colorRGB=WHITE))
        self.buttonList.append(self.buildShelfButton(SHELF_DICT["brTransferSkinWeights"], colorRGB=WHITE))
        self.buttonList.append(self.createIconButton("separator_shlf"))

        self.closeBtn = self.createIconButton("closeX")
        self.closeBtn.setToolTip("Close the floating shelf window.")
        self.closeBtn.clicked.connect(self.close)

    # -------------
    # LAYOUT UI
    # -------------

    def layout(self):
        self.mainLayout = elements.hBoxLayout(spacing=6, margins=(12, 6, 12, 2))
        for i, btn in enumerate(self.buttonList):
            self.mainLayout.addWidget(btn)
        self.mainLayout.addWidget(self.closeBtn)
        self.setMainLayout(self.mainLayout)


def main():
    point = QtGui.QCursor.pos()
    point.setX(point.x() + WINDOW_OFFSET_X)
    point.setY(point.y() + WINDOW_OFFSET_Y)

    eng = engine.currentEngine()
    win = eng.showDialog(MyPopupToolbar, "zooRiggingFloatingShelf", show=False)
    win.show(point)
