from functools import partial

from maya import cmds
from zoo.core.util import env
from zoo.libs.maya.qt import mayaui
from zoo.apps.toolpalette import palette, utils
from zoo.libs.maya.utils import shelves
from zoo.core.util import zlogging
from zoovendor.Qt import QtWidgets

logger = zlogging.getLogger(__name__)


class MayaPalette(palette.ToolPalette):
    application = "maya"

    def __init__(self, parent=None):
        # declare before calling super since _loadLayout gets called by the base.
        parent = parent or mayaui.getMayaWindow()
        super(MayaPalette, self).__init__(parent=parent)

        if not env.isMayapy():
            self.createMenus()

    def createMenus(self):
        super(MayaPalette, self).createMenus()
        prefsMenu = self._menuCache["Preferences"]
        newAction = prefsMenu.addAction("Build Zoo Shelves")
        newAction.triggered.connect(self.createShelves)
        newAction = prefsMenu.addAction("Remove Zoo Shelves")
        newAction.triggered.connect(self.removeShelves)
        self._menuCache.clear()
        self._shelfCache.clear()

    def createShelf(self, shelf):
        """

        :param shelf:
        :type shelf: :class:`layouts.Shelf`
        :return: The UI shelf instance, used to store a reference in shelf.metaData["uiInstance"].
        """
        # create an empty shelf
        newShelf = shelves.Shelf(shelf.label)
        try:
            newShelf.createShelf()
        except AssertionError:
            pass
        return newShelf

    def createShelfButton(self, shelf, shelfButton):
        """

        :param shelf:
        :type shelf: :class:`palette.layouts.Shelf`
        :param shelfButton:
        :type shelfButton: :class:`palette.layouts.ShelfButton`
        :return:
        """

        mayaShelfInstance = self._shelfCache[shelf.id]  # type: shelves.Shelf
        if shelfButton.isSeparator():
            mayaShelfInstance.addSeparator()
            return
        icon = utils.iconForItem(shelfButton, path=True)
        menuCommandString = ""
        if not shelfButton.children:
            typePlugin = self.typeRegistry.getPlugin(
                shelfButton.type
            )  # type: palette.PluginTypeBase

            if typePlugin is not None:
                menuCommand = typePlugin.generateCommand(
                    shelfButton.id, shelfButton.arguments
                )
                menuCommandString = menuCommand.string

        logger.debug(
            "Creating shelf button: {}, parent: {}".format(
                shelfButton.label, mayaShelfInstance
            )
        )
        btn = mayaShelfInstance.addButton(
            label=shelfButton.label,
            icon=icon,
            command=menuCommandString,
            tooltip=shelfButton.tooltip,
            style="iconOnly",
        )
        if len(shelfButton) != 0:
            logger.debug(
                "Creating Shelf menu: {}, parent: {}".format(
                    shelfButton.label + "ctxMenu", btn
                )
            )
            pop = cmds.popupMenu(shelfButton.label + "ctxMenu", button=1, parent=btn)
            self._shelfCache[shelfButton.id + "PopUpMenu"] = pop
            shelfButton.metaData["popUpMenu"] = pop

        return btn

    def createShelfButtonMenuItem(self, menuItem, shelf, shelfButton):
        """

        :param menuItem:
        :type menuItem: :class:`palette.layouts.MenuItem`
        :param shelf:
        :type shelf: :class:`palette.layouts.Shelf`
        :param shelfButton:
        :type shelfButton: :class:`palette.layouts.ShelfButton`
        :return:
        :rtype:
        """
        mayaButtonPopUp = self._shelfCache[shelfButton.id + "PopUpMenu"]
        menu = mayaui.toQtObject(
            mayaButtonPopUp, QtWidgets.QMenu
        )  # type: QtWidgets.QMenu
        if menuItem.isSeparator():
            sep = menu.addSeparator()
            if menuItem.isGroup():
                sep.setText(menuItem.label)
            return sep
        elif menuItem.isLabel():
            action = menu.addAction(menuItem.label)
            return action
        pluginTypeName = menuItem.type
        pluginId = pluginId = menuItem.id
        if menuItem.type == "variant":
            pluginTypeName = "action"
            pluginId = menuItem.parent.id
            menuItem.arguments["variant"] = menuItem.id
        pluginType = self.typeRegistry.getPlugin(
            pluginTypeName
        )  # type: palette.PluginTypeBase
        if pluginType is not None:
            data = menuItem.serialize(valid=True)
            uiData = pluginType.pluginUiData(pluginId, data)
            menuItem.update(uiData)
        action = menu.addAction(menuItem.label)
        isCheckable = menuItem.isCheckable
        isChecked = menuItem.isChecked
        if isCheckable:
            action.setCheckable(isCheckable)
            action.setChecked(isChecked)
            action.toggled.connect(
                lambda checked: self.executePluginById(pluginId, state=checked)
            )
        else:
            action.triggered.connect(
                partial(self.executePluginById, pluginId, **menuItem.arguments)
            )
        icon = utils.iconForItem(menuItem)
        if icon is None:
            logger.warning(
                "Icon name: '{}' not found in zoo icon lib, "
                "Plugin Type: {}, Plugin Id: {}".format(
                    menuItem.icon, menuItem.type, menuItem.id
                )
            )
            return action

        action.setIcon(icon)
        return action

    def setShelfActive(self, shelf):
        """

        :param shelf:
        :type shelf: :class:`layouts.Shelf`
        """
        label = shelf.label.replace(" ", "_")
        if shelves.shelfExists(label):
            shelfInstance = shelves.Shelf(label)
            shelfInstance.setAsActive()

    def removeShelves(self, clearLayoutOnly=False):
        if clearLayoutOnly:
            for shelf in self.shelfManager.shelves:
                label = shelf.label.replace(" ", "_")
                if shelves.shelfExists(label):
                    shelves.Shelf(label).clear(deleteShelf=False)
        else:
            for shelf in self.shelfManager.shelves:
                label = shelf.label.replace(" ", "_")
                shelves.Shelf(label).clear(deleteShelf=True)
