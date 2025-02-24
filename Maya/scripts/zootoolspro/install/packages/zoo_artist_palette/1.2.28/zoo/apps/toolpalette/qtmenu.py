from functools import partial


from zoo.libs.pyqt.extended import searchablemenu
from zoo.core.util import zlogging
from zoo.apps.toolpalette import utils

from zoo.apps.toolpalette import layouts


logger = zlogging.getLogger(__name__)


def generateMenuTree(parentItem, qtParentMenu, triggeredFunc, typeRegistry, iconSize, createdItems_=None):
    """Recursively generate a menu tree in Qt from the given parentItem.

    :param parentItem: The parent item to generate the menu tree from.
    :type parentItem: :class:`layouts.Item`
    :param qtParentMenu: The Qt parent menu to create the menu tree in.
    :type qtParentMenu: :class:`QtWidgets.QMenu`
    :param triggeredFunc: The function to call when a menu item is triggered.
    :type triggeredFunc: callable
    :param typeRegistry: The plugin type registry for the menu items.
    :type typeRegistry: :class:`zoo.core.type.TypeRegistry`
    :param iconSize: The size of the icons to use in the menu.
    :type iconSize: int
    :param createdItems_: A dictionary of created Qt actions and menus.
    :type createdItems_: dict
    :return: A dictionary of the created items.
    :rtype: dict
    """
    createdItems_ = createdItems_ or {}
    for childItem in parentItem.children:
        childId = childItem.id
        childPluginType = childItem.type
        if childItem.isMenu():
            childMenu = createMenu(childItem, qtParentMenu, iconSize)
            nativeItem = generateMenuTree(childItem, childMenu, triggeredFunc, typeRegistry, iconSize, createdItems_)
            createdItems_[childItem.id] = nativeItem
            continue
        elif childItem.isSeparator() or childItem.isLabel() or childItem.isGroup():
            nativeItem = createMenuAction(childItem, qtParentMenu, triggeredFunc, iconSize)
            createdItems_[childItem.id] = nativeItem
            continue
        elif childItem.isVariant():
            childId = childItem.parent.id
            childPluginType = childItem.parent.type
        # temporary workaround for legacy until we migrate everything to the new system
        typePlugin = typeRegistry.getPlugin(childPluginType)  # type: PluginTypeBase

        if typePlugin is None:
            # skip any plugin which can't be found
            logger.warning("Failed to find Plugin: {}, type: {}".format(childId, childPluginType))
            return
        data = childItem.serialize(valid=True)
        uiData = typePlugin.pluginUiData(childId, data)
        childItem.update(uiData)
        nativeItem = createMenuAction(childItem, qtParentMenu, triggeredFunc, iconSize)
        createdItems_[childItem.id] = nativeItem
    return createdItems_


def createMenu(menuItem, parentMenu, iconSize):
    """Create a new Qt menu from the given menuItem.

    :param menuItem: The menu item to create the menu from.
    :type menuItem: layouts.MenuItem
    :param parentMenu: The Qt parent menu to create the menu in.
    :type parentMenu: QtWidgets.QMenu
    :param iconSize: The size of the icons to use in the menu.
    :type iconSize: int
    :return: The newly created Qt menu.
    :rtype: QtWidgets.QMenu
    """
    newMenu = parentMenu.addMenu(menuItem.label)  # porent is the MainWindow instance
    newMenu.setObjectName(menuItem.id)
    newMenu.setTearOffEnabled(True)
    icon = utils.iconForItem(menuItem, iconSize=iconSize)
    if icon is not None:
        newMenu.setIcon(icon)
    return newMenu


def createMenuAction(menuItem, nativeParentMenu, triggeredFunc, iconSize):
    """Create a new Qt menu action from the given menuItem.

    :param menuItem: The menu item to create the action from.
    :type menuItem: layouts.MenuItem
    :param nativeParentMenu: The Qt parent menu to create the action in.
    :type nativeParentMenu: QtWidgets.QMenu
    :param triggeredFunc: The function to call when the action is triggered.
    :type triggeredFunc: callable
    :param iconSize: The size of the icons to use in the action.
    :type iconSize: int
    :return: The newly created Qt menu action.
    :rtype: QtWidgets.QAction
    """
    if menuItem.isSeparator():
        nativeParentMenu.addSeparator()
        return
    elif menuItem.isGroup():
        sep = nativeParentMenu.addSeparator()
        sep.setText(menuItem.label)
        return
    elif menuItem.isLabel():
        nativeParentMenu.addAction(menuItem.label)
        return
    pluginId = menuItem.id
    if menuItem.isVariant():
        pluginId = menuItem.parent.id

    label = menuItem.label

    taggedAction = searchablemenu.TaggedAction(label, parent=nativeParentMenu)
    taggedAction.setObjectName(pluginId)
    isCheckable = menuItem.isCheckable
    isChecked = menuItem.isChecked
    if isCheckable:
        taggedAction.setCheckable(isCheckable)
        taggedAction.setChecked(isChecked)
        taggedAction.toggled.connect(lambda: triggeredFunc(pluginId, state=taggedAction.isChecked()))
    else:
        taggedAction.triggered.connect(partial(triggeredFunc, pluginId, **menuItem.arguments))

    if menuItem.loadOnStartup:
        triggeredFunc(pluginId, isChecked)

    icon = utils.iconForItem(menuItem, iconSize=iconSize)
    if icon:
        taggedAction.setIcon(icon)

    taggedAction.tags = menuItem.tags
    nativeParentMenu.addAction(taggedAction)
    return taggedAction

