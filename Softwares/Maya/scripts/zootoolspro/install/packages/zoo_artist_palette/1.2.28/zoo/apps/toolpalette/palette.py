"""This Module handles the base class for the zootools main menu.

:todo: replace hardcoded tool types with a plugin system to better handle tool distribution
"""
import abc
import sys
import traceback

from zoovendor import six

from zoo.core.util import zlogging
from zoo.core.plugin import plugin, pluginmanager
from zoo.preferences import core
from zoo.preferences.core import preference
from zoo.apps.toolpalette import layouts, qtmenu
from zoovendor.Qt import QtWidgets

logger = zlogging.getLogger(__name__)


class ToolPalette(object):
    TOOLSENV = "ZOO_ACTIONPLUGIN_MODULES"
    LAYOUTENV = "ZOO_MENU_LAYOUTS"
    TYPE_ENV = "ZOO_TOOLPALETTE_PLUGINTYPE_PATH"
    SHELFLAYOUTENV = "ZOO_SHELF_LAYOUTS"
    application = "standalone"

    def __init__(self, parent=None):
        super(ToolPalette, self).__init__()
        self.parent = parent
        self.menuManager = layouts.MenuManager()
        self.shelfManager = layouts.ShelfManager()
        self.preferenceInterface = preference.interface("artistPalette")
        self.typeRegistry = pluginmanager.PluginManager(interface=[PluginTypeBase],
                                                        variableName="id", name="ToolPaletteType")
        self.typeRegistry.registerByEnv(self.TYPE_ENV)
        self.typeRegistry.registerPlugin(ActionType)
        for p in self.typeRegistry.plugins.keys():
            self.typeRegistry.loadPlugin(p, toolPalette=self)
        self._pluginIdMap = {}  # pluginId, pluginType ie. action

        for pluginId, pluginType in self.typeRegistry.loadedPlugins.items():
            for toolPluginId in pluginType.plugins():
                self._pluginIdMap[toolPluginId] = pluginId

        self.menuManager.loadFromEnv(ToolPalette.LAYOUTENV)
        self.shelfManager.loadFromEnv(ToolPalette.SHELFLAYOUTENV)
        # only valid while build the menu, this temporarily stores the native host menu instance by the zoo id
        self._menuCache = {}
        self._shelfCache = {}

    def removePreviousMenus(self):
        """Removes Any zoo plugin menu from maya by iterating through the children of the main window looking for any
        widget with the objectname Zoo Tools.
        """
        layoutMenusObjectNames = [menuItem.id for menuItem in self.menuManager.menus]
        if isinstance(self.parent, QtWidgets.QWidget):
            for childWid in self.parent.menuBar().children():
                if childWid.objectName() in layoutMenusObjectNames:
                    childWid.deleteLater()

    def removeShelves(self, clearLayoutOnly=False):
        """Removes any zoo shelves from the host application. If clearLayoutOnly is True then each shelf will be
        cleared of its buttons but the tab layout to be maintained.

        :param clearLayoutOnly: Whether to clear the shelf layout only or delete the shelf entirely
        :type clearLayoutOnly: bool
        """
        pass

    def createMenus(self):
        """Loops through all loadedPlugins and creates a menu/action for each. Uses the plugin class objects parent
        variable to determine where  it sits within the menu.
        """
        self.removePreviousMenus()

        for menu in self.menuManager.menus:
            self._menuCreator(menu, None)

        if self.preferenceInterface.loadShelfAtStartup():
            self.createShelves()

    def _menuCreator(self, menu, parentMenu=None):
        """

        :param menu:
        :type menu: :class:`layouts.MenuItem`
        :param parentMenu:
        :type parentMenu: :class:`MenuItem` or None
        :return:
        :rtype:
        """
        menuInstance = self.createMenu(menu, parentMenu)
        if menuInstance is None:
            return
        self._menuCache[menu.id] = menuInstance
        for childItem in menu.children:
            if childItem.isMenu():
                self._menuCreator(childItem, parentMenu=menu)
                continue
            elif childItem.isSeparator():
                self.createMenuAction(childItem, None)
                continue
            elif childItem.isLabel():
                self.createMenuAction(childItem, None)
                continue
            # temporary workaround for legacy until we migrate everything to the new system
            typePlugin = self.typeRegistry.getPlugin(childItem.type)  # type: PluginTypeBase

            if typePlugin is None:
                # skip any plugin which can't be found
                logger.warning("Failed to find Plugin: {}, type: {}".format(childItem.id, childItem.type))
                return

            data = childItem.serialize(valid=True)
            uiData = typePlugin.pluginUiData(childItem.id, data)
            childItem.update(uiData)
            command = typePlugin.generateCommand(childItem.id, childItem.arguments)
            self.createMenuAction(childItem, command)

    def createMenu(self, menuItem, parentMenu):
        """

        :param menuItem:
        :type menuItem: :class:`layouts.MenuItem`
        :param parentMenu:
        :type parentMenu: :class:`layouts.MenuItem` or None
        :return:
        :rtype: :class:`MenuItem`
        """

        parentQtMenu = self._menuCache.get(parentMenu.id) if parentMenu is not None else None
        if parentQtMenu is None:
            parentQtMenu = self.parent.menuBar()

        newMenu = qtmenu.createMenu(menuItem, parentQtMenu, iconSize=32)
        return newMenu

    def createMenuAction(self, menuItem, command):
        """

        :param menuItem:
        :type menuItem: :class:`layouts.MenuItem`
        :param command:
        :type command: :class:`ItemCommand`
        :return:
        :rtype:
        """

        parent = self._menuCache[menuItem.parent.id]
        newAction = qtmenu.createMenuAction(menuItem, parent, triggeredFunc=self.executePluginById, iconSize=32)
        self._menuCache[menuItem.id] = newAction
        logger.debug("Added action, {}".format(menuItem.label))

    def createShelves(self):
        self.removeShelves(clearLayoutOnly=True)
        for shelf in self.shelfManager.shelves:

            self.preShelfCreate(shelf)
            try:
                shelfInstance = self.createShelf(shelf)
                if shelfInstance is None:
                    continue
                self._shelfCache[shelf.id] = shelfInstance
                for child in shelf.children:

                    if not all((child.isShelfButton(), child.isSeparator(), child.isGroup(), child.isLabel())):
                        data = child.serialize(valid=True)
                        ui = self.typeRegistry.getPlugin(child.type)  # type: PluginTypeBase
                        if ui is not None:
                            uiData = ui.pluginUiData(child.id, data)
                            child.update(uiData)

                    shelfButton = self.createShelfButton(shelf, child)
                    if shelfButton is not None:
                        self._shelfCache[child.id] = shelfInstance
                        self._createShelfButtonMenu(shelf, child)
            finally:
                self.postShelfCreate(shelf)

        try:
            activeShelf = self.preferenceInterface.defaultShelf()
            if activeShelf and self.preferenceInterface.isActiveAtStartup():
                shelf = self.shelfManager.shelfById(activeShelf)
                if shelf is not None:
                    self.setShelfActive(shelf)

        except core.errors.SettingsNameDoesntExistError:
            # in the case where the default shelf key isn't defined just warning
            logger.warning("Couldn't set default shelf due to preference key not existing!")
            return

    def _createShelfButtonMenu(self, shelf, shelfButton):
        """

        :param shelf:
        :type shelf: :class:`layouts.Shelf`
        :param shelfButton:
        :type shelfButton: :class:`layouts.ShelfButton`
        :return:
        :rtype:
        """
        for child in shelfButton.children:
            pluginType = self.typeRegistry.getPlugin(child.type)  # type: PluginTypeBase
            if pluginType is not None:
                data = child.serialize(valid=True)
                uiData = pluginType.pluginUiData(child.id, data)
                child.update(uiData)

            childItem = self.createShelfButtonMenuItem(child, shelf, shelfButton)
            if childItem is not None:
                self._shelfCache[child.id] = childItem

    def createShelfButtonMenuItem(self, menuItem, shelf, shelfButton):
        """

        :param menuItem:
        :type menuItem: :class:`layouts.MenuItem`
        :param shelf:
        :type shelf: :class:`layouts.Shelf`
        :param shelfButton:
        :type shelfButton: :class:`layouts.ShelfButton`
        :return:
        :rtype:
        """
        pass

    def preShelfCreate(self, shelf):
        """

        :param shelf:
        :type shelf: :class:`layouts.Shelf`
        """
        pass

    def createShelf(self, shelf):
        """

        :param shelf:
        :type shelf: :class:`layouts.Shelf`
        :return: The UI shelf instance, used to store a reference in shelf.metaData["uiInstance"].
        """
        pass

    def createShelfButton(self, shelf, shelfButton):
        """

        :param shelf:
        :type shelf: :class:`layouts.Shelf`
        :param shelfButton:
        :type shelfButton: :class:`layouts.ShelfButton`
        :return:
        :rtype:
        """
        pass

    def setShelfActive(self, shelf):
        """

        :param shelf:
        :type shelf: :class:`layouts.Shelf`
        """
        pass

    def postShelfCreate(self, shelf):
        """Called once per shelf after all shelf items have been created

        :param shelf:
        :type shelf: :class:`layouts.Shelf`
        """
        pass

    def shutdown(self, deleteMenu=True, deleteShelves=True):
        """Shutdown's Tool palette, tool plugins, shelves, menus etc.
        """
        logger.debug("Attempting to teardown plugins")
        if deleteMenu:
            self.removePreviousMenus()
        if deleteShelves:
            self.removeShelves()
        for p in self.typeRegistry.loadedPlugins.values():
            p.shutdown()

    def executePluginById(self, pluginId, *args, **kwargs):
        """Executes the tool action plugin by the id string.

        :param pluginId: The tool action id.
        :type pluginId: str
        :param args: The arguments to pass to the execute method
        :type args: tuple
        :param kwargs: The keyword arguments to pass to the execute method
        :type kwargs: dict
        :return: The executed tool action instance or none
        :rtype: :class:`ActionPlugin` or None
        """
        pluginType = self._pluginIdMap.get(pluginId)
        if pluginType is None:
            return None, None
        pluginCls = self.typeRegistry.getPlugin(pluginType)
        return pluginCls.executePlugin(pluginId, *args, **kwargs)


class ItemCommand(object):
    """Contains the Item command which determines the string command to execute via maya shelf, unity menus etc.

    :param pluginId: The plugin id of the item which this command belongs too.
    :type pluginId: str
    :param arguments: The keyword arguments which was passed to the command string
    :type arguments: dict
    :param commandStr: The resolved command string.
    :type commandStr: str
    """

    def __init__(self, pluginId, arguments, commandStr=None):
        # the resolved command string which will be used to execute.
        self.string = commandStr or ""
        # the plugin id which this command belongs too.
        self.pluginId = pluginId
        # the keyword arguments for the command
        self.arguments = arguments  # type: dict


class PluginTypeBase(object):
    id = ""
    commandString = ""

    def __init__(self, toolPalette):
        self.toolPalette = toolPalette

    def plugins(self):
        return []

    def pluginUiData(self, pluginId, overrides=None):
        """

        :param pluginId:
        :type pluginId: str
        :param overrides:
        :type overrides: dict
        :return:
        :rtype: dict
        """
        return {}

    def pluginVariants(self, pluginId):
        return []

    def executePlugin(self, pluginId, *args, **kwargs):
        pass

    def shutdown(self):
        pass

    def generateCommand(self, pluginId, arguments):
        """

        :param pluginId:
        :type pluginId: str
        :param arguments:
        :type arguments: dict
        :return:
        :rtype: :class:`ItemCommand`
        """
        return


class ActionType(PluginTypeBase):
    id = "action"
    TOOLSENV = "ZOO_ACTIONPLUGIN_MODULES"
    commandString = """
from zoo.apps.toolpalette import run as _paletterun
_zooPalette = _paletterun.currentInstance()
_zooPalette.executePluginById(**{})
"""

    def __init__(self, toolPalette):
        super(ActionType, self).__init__(toolPalette)
        self._typeRegistry = pluginmanager.PluginManager(interface=[ActionPlugin],
                                                         variableName="id",
                                                         name="toolPaletteActionType")
        self._typeRegistry.registerByEnv(self.TOOLSENV)
        self._typeRegistry.loadAllPlugins(toolPalette=toolPalette)

    def plugins(self):
        for p in self._typeRegistry.plugins.keys():
            yield p

    def generateCommand(self, pluginId, arguments):
        # returns a list of dict
        args = arguments or {}
        args["pluginId"] = pluginId
        command = self.commandString.format(args)
        cmd = ItemCommand(pluginId, arguments=args)
        cmd.string = command
        return cmd

    def pluginUiData(self, pluginId, overrides=None):
        uiData = {}
        overrides = overrides or {}
        try:
            p = self._typeRegistry.getPlugin(pluginId)
            uiData.update(p.uiData)
            uiData["tags"] = set(p.tags)
            uiData["clsName"] = p.__class__.__name__
            uiData.update(overrides)
        except AttributeError:
            logger.error("Missing Action plugin: {}".format(pluginId), exc_info=True)
        finally:
            return uiData

    def executePlugin(self, pluginId, *args, **kwargs):
        p = self._typeRegistry.getPlugin(pluginId)
        result = p._execute(*args, **kwargs)
        logger.debug("{}, Execution time: {}".format(p, p.stats.executionTime))
        return p, result

    def shutdown(self):
        logger.debug("Attempting to teardown plugins")
        for plugName, plug in self._typeRegistry.loadedPlugins.items():
            logger.debug("shutting down tool -> {}".format(plug.id))
            plug.runTearDown()
        self._typeRegistry.unloadAllPlugins()


@six.add_metaclass(abc.ABCMeta)
class ActionPlugin(plugin.Plugin):
    uiData = {"icon": "",
              "tooltip": "",
              "label": "",
              "color": "",
              "backgroundColor": "",
              "dock": {"dockable": False, "area": "left"},
              "isCheckable": True,
              "isChecked": True,
              "multipleTools": False,
              "loadOnStartup": True
              }

    def __init__(self, manager=None, toolPalette=None):
        super(ActionPlugin, self).__init__(manager=manager)
        self.toolPalette = toolPalette

    @property
    @abc.abstractmethod
    def id(self):
        pass

    @property
    @abc.abstractmethod
    def creator(self):
        pass

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        pass

    def runTearDown(self):
        try:
            self.teardown()
        except RuntimeError:
            logger.error("Failed to teardown plugin: {}".format(self.id),
                         exc_info=True)

    def teardown(self):
        pass

    def _execute(self, *args, **kwargs):
        """ Modified version from ActionPlugin to allow multiple tools.

        :param args:
        :param kwargs:
        :return:
        """
        self.stats.start()
        exc_type, exc_value, exc_tb = None, None, None

        try:
            return self.execute(*args, **kwargs)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            raise
        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            self.stats.finish(tb)
