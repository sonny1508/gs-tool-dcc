"""

Usage::

    First define to location of your commands and marking menu classes. 
    Next define the location of your layout files
    Now apply these locations to the MM environment variables, ZOO_MM_COMMAND_PATH, 
        ZOO_MM_MENU_PATH, ZOO_MM_LAYOUT_PATH, before zootools starts up.


"""
import os
from functools import partial

from zoovendor.Qt import QtWidgets
from zoo.libs import iconlib
from zoo.libs.maya.qt import mayaui
from zoo.libs.utils import filesystem
from zoo.core.util import classtypes, modules
from zoo.libs.utils import general
from zoo.core.util import zlogging
from zoo.core.plugin import plugin, pluginmanager
from zoovendor import six
from maya import cmds
from zoo.libs.utils.general import jsonToBool

logger = zlogging.getLogger(__name__)


class InvalidJsonFileFormat(Exception):
    """Raised in case of invalid formatted json file(.mmlayout)"""

    pass


class MissingMarkingMenu(Exception):
    pass


def findLayout(layoutId):
    """Finds the layout by Id(str) from the layout registry

    :param layoutId: the layout str id, "some.layout.id"
    :type layoutId: str
    :return: If the registry has the id then a :class:`Layout` object will be returned
    :rtype: :class:`Layout` or None
    """
    reg = Registry()
    if layoutId in reg.layouts:
        return reg.layouts[layoutId]


@six.add_metaclass(classtypes.Singleton)
class Registry(object):
    """This holds all currently available layout classes discovered in the environment
    use :func:`findLayout` to get the layout from this registry.

    To setup the environment you need to set the environment variable :env:'ZOO_MM_LAYOUT_PATH'
    to the directories of the layout, each path should be separated using :class:`os.pathsep`
    """

    LAYOUT_ENV = "ZOO_MM_LAYOUT_PATH"
    MENU_ENV = "ZOO_MM_MENU_PATH"
    COMMAND_ENV = "ZOO_MM_COMMAND_PATH"
    STATIC_LAYOUT_TYPE = 0
    DYNAMIC_TYPE = 1

    def __init__(self):
        self.layouts = {}
        self.activeMenus = {}  # type: dict[str, MarkingMenu]
        self.registerLayoutByEnv(Registry.LAYOUT_ENV)
        self.menuRegistry = pluginmanager.PluginManager(
            interface=[MarkingMenuDynamic], variableName="id"
        )
        self.commandRegistry = pluginmanager.PluginManager(
            interface=[MarkingMenuCommand], variableName="id"
        )
        self.menuRegistry.registerByEnv(Registry.MENU_ENV)
        self.commandRegistry.registerByEnv(Registry.COMMAND_ENV)

    def hasMenu(self, menuId):
        return menuId not in self.menuRegistry.plugins or menuId not in self.layouts

    def menuType(self, menuId):
        return (
            Registry.DYNAMIC_TYPE
            if self.menuRegistry.plugins.get(menuId) is not None
            else Registry.STATIC_LAYOUT_TYPE
        )

    def env(self):
        return {
            "layouts": self.layouts,
            "customMenus": self.menuRegistry.plugins,
            "commands": self.commandRegistry.plugins,
            "activeMenus": self.activeMenus,
        }

    def registerLayoutByEnv(self, env):
        """Recursively Registers all layout files with the extension .mmlayout and loads the json data with a layout
        instance then adds to the layouts cache

        :param env: the environment variable pointing to the parent directory
        :type env: str
        """
        paths = os.environ.get(env, "").split(os.pathsep)
        for p in paths:
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        layoutFile = os.path.join(root, f)
                        self.loadMMLayoutFile(layoutFile)
            elif p.endswith(".mmlayout"):
                self.loadMMLayoutFile(p)

    def loadMMLayoutFile(self, path):
        basename = os.path.basename(path)
        try:
            if path.endswith(".mmlayout"):
                if basename.startswith(modules.MODULE_EXCLUDE_PREFIXES):
                    return
                data = filesystem.loadJson(path)
                self.layouts[data["id"]] = Layout(**data)
        # If the Json data is invalid(formatted) it will raise a valueError without a file location
        # so raise something useful
        except ValueError:
            raise InvalidJsonFileFormat(
                "Layout file: {} is invalid possibly due to the "
                "formatting.".format(path)
            )

    def registerLayoutData(self, data):
        """Adds the layout data structure as a :class:`Layout` using the data["id"] as the
        key.

        :param data: see :class`Layout`
        :type data: dict
        """
        self.layouts[data["id"]] = Layout(**data)


class Layout(dict):
    """

    .. code-block:: python

        layoutData={"items":{"N": {},
                              "NW": {},
                              "W": {},
                              "SW": {},
                              "S": {},
                              "SE": {},
                              "E": {},
                              "NE": {},
                              "generic": [{"type": "menu",
                                          "name": "Testmenu",
                                          "children": [{"type": "command",
                                                        "id": ""}
                                                        ]
                                          ]

                              },
                    "id": "some.layout.id"}
        layoutObj = Layout(**layoutData)

    """

    def __init__(self, **kwargs):
        kwargs["sortOrder"] = kwargs.get("sortOrder", 0)
        super(Layout, self).__init__(**kwargs)
        self.solved = False

    def __getitem__(self, item):
        """
        :param item: The name of the layout region eg. "N", "S" etc
        :type item: str
        :return: Will return a dict in cases of marking menu region(n,s,w etc) being a nested after a layout has been \
        solved, a list will be returned for the generic region , str is return when the layout hasnt been solved but \
        references another layout.
        :rtype: list or dict or str
        """
        value = self.get(item)
        if value is None:
            return self.get("items", {})[item]
        return value

    def __iter__(self):
        """Generator that loops the layout items

        :rtype: tuple(str, dict value)
        """
        for name, data in iter(self["items"].items()):
            yield name, data

    def items(self):
        """Returns the item dict for this layout in the form of

        .. code-block:: json

            {"N": {},
            "NW": {},
            "W": {},
            "SW": {},
            "S": {},
            "SE": {},
            "E": {},
            "NE": {},
            "generic": [{"type": "menu",
                        "name": "Testmenu",
                        "children": [{"type": "command",
                                      "id": ""}
                                      ]]
            }

        :return: The layout items dict.
        :rtype: dict
        """
        return self.get("items", {}).items()

    def merge(self, layout):
        """Merges the layout items into this instance, only differences will be merged.

        :param layout: the layout to merge into the this class
        :type layout: :class:`Layout`
        """
        # merge modify self in place
        general.merge(self, layout["items"])

    def validate(self, layout=None):
        """Recursively validates the layout, returning all failed items, if an item references another layout that
        layout will used be validated.

        :param layout: The layout instance to solve
        :type layout: Layout
        :return: the failed items
        :rtype: list
        """
        layout = layout or self
        failed = []
        for item, data in iter(layout["items"].items()):
            if not data:
                continue
            # handle nested layouts
            elif isinstance(data, Layout):
                failed.extend(self.validate(data))
            # generic type is the linear list of action south of the radial menu
            elif item == "generic":
                failed.extend(self._validateGeneric(data))
            elif data.get("type", "") == "command":
                command = Registry().commandRegistry.getPlugin(data["id"])
                if not command:
                    failed.append(data)
            else:
                failed.append(data)
        return failed

    def _validateGeneric(self, data):
        """Validates the generic items list to ensure that all commands are valid within the executor

        :param data: the generic items list from the layout
        :type data: list
        :return: the invalid items
        :rtype: list
        """
        failed = []
        for item in iter(data):
            commandType = item["type"]
            # cant validate python commands without executing them?
            if commandType == "menu":
                failed.extend(self._validateGeneric(item["children"]))
            elif commandType == "command":
                command = Registry().commandRegistry.getPlugin(item["id"])
                if not command:
                    failed.append(item)
            else:
                failed.append(item)

        return failed

    def solve(self):
        """Recursively solves the layout by expanding any @layout.id references which will compose a single dict ready
        for use.

        A layout can contain deeply nested layouts which is referenced by the syntax @layout.id, in the case
        where there is a reference then that layout will be solved first.

        :return: Whether or not the layout was solved
        :rtype: bool
        """
        registry = Registry()
        solved = False
        for item, data in self.get("items", {}).items():
            if not data:
                continue
            elif item == "generic":
                solved = True
                continue
            elif data["type"] == "layout":
                subLayout = registry.layouts.get(data["id"])
                if not subLayout:
                    logger.warning("No layout with the id {}, skipping".format(data))
                    continue
                subLayout.solve()
                self["items"][item] = subLayout
                solved = True
        self.solved = solved
        return solved


class MarkingMenu(object):
    """Maya MarkingMenu wrapper object to support zoocommands and python executable code. MM layouts are defined by the
    Layout instance class
    """

    @staticmethod
    def removeExistingMenu(menuName):
        """Removes the menuName from the registry and deletes the menu from maya

        :param menuName: The menu name to remove.
        :type menuName: str

        """
        reg = Registry()
        menuObject = reg.activeMenus.get(menuName)
        if menuObject is not None:
            menuObject.kill()
            del reg.activeMenus[menuName]
            return True
        return False

    @staticmethod
    def removeAllActiveMenus():
        """Removes all current active zoo marking menus from the registry and deletes the Maya UI MM"""
        reg = Registry()
        for active in reg.activeMenus.values():
            active.kill()
        reg.activeMenus.clear()

    @classmethod
    def buildFromLayout(cls, layoutId, menuName, parent, options, globalArguments=None):
        """Build a menu directly from the menu registry based off of the
        layout Id.

        :param layoutId: The layout id defined in the registry
        :type layoutId: str
        :param menuName: The unique name for the menu
        :type menuName: str
        :param parent: The maya widget path for the menu parent i.e viewPanes
        :type parent: str
        :param options: The marking menu options, see :class:`MarkingMenu.__init__` \
        for more details
        :type options: dict
        :param globalArguments: The global Arguments to pass to all menu action commands.
        :type globalArguments: dict
        :return: The new markingMenu instance
        :rtype: :class:`MarkingMenu`
        :raise: ValueError, in the case the layout can't be found or already active.
        """
        layoutObject = findLayout(layoutId)
        if layoutObject is None:
            raise ValueError("Failed to find marking menu layout: {}".format(layoutId))
        reg = Registry()
        if menuName in reg.activeMenus:
            if not cmds.popupMenu(menuName, ex=True):
                del reg.activeMenus[menuName]
            else:
                raise ValueError(
                    "Menu: {} Already active can't create multiple "
                    "instances of the same menu".format(menuName)
                )
        mainMenu = cls(layoutObject, menuName, parent, reg)
        mainMenu.options.update(options)
        if cmds.popupMenu(parent, ex=True):
            mainMenu.attach(**globalArguments or {})
        else:
            mainMenu.create(**globalArguments or {})
        reg.activeMenus[menuName] = mainMenu

        return mainMenu

    @classmethod
    def buildFromLayoutData(cls, layoutData, menuName, parent, options, arguments=None):
        """Create a new :class:`MarkingMenu` instance from the layoutData, menuName, and options provided.

        If the menu already exists and is active, raise a ValueError.
        If the parent menu exists, attach the new menu to it.
        Otherwise, create the new menu.

        :param layoutData: the data that defines the layout of the menu.
        :type layoutData: :class:`Layout`
        :param menuName: the name of the menu.
        :type menuName: str
        :param parent: the parent menu, if any.
        :type parent: str
        :param options: additional options to be passed to the menu.
        :type options: dict
        :param arguments: additional arguments to be passed to the `attach()` or `create()` method.
        :type arguments: dict
        :return: the new menu instance.
        :rtype: :class:`MarkingMenu`
        """
        reg = Registry()
        if menuName in reg.activeMenus:
            if not cmds.popupMenu(menuName, ex=True):
                del reg.activeMenus[menuName]
            else:
                raise ValueError(
                    "Menu: {} Already active can't create multiple "
                    "instances of the same menu".format(menuName)
                )
        newMenu = cls(layoutData, name=menuName, parent=parent, registry=reg)
        newMenu.options.update(options)
        if cmds.popupMenu(parent, ex=True):
            newMenu.attach(**arguments or {})
        else:
            newMenu.create(**arguments or {})
        reg.activeMenus[menuName] = newMenu

        return newMenu

    @staticmethod
    def buildDynamicMenu(clsId, menuName, parent, arguments, options=None, layout=None):
        """Builds a marking menu from the clsId which should exist with our marking menu registry.

        :param clsId: the classId string
        :type clsId: str
        :param parent: The parent menu or widget fullPath ie. viewPanes for mayas viewport.
        :type parent: str
        :param arguments: The arguments to pass to the custom menu class
        :type arguments: dict
        :param options: additional options to be passed to the menu.
        :type options: dict
        :param layout: the base Layout data that defines the layout this will be modified by the dynamic class.
        :type layout: :class:`Layout` or None
        :return: If the classid exists then the newly created marking menu class will be returned
        :rtype: :class:`MarkingMenu` or None
        """
        layout = layout or Layout()  # todo: support args
        layout["id"] = clsId
        registry = Registry()

        menuCls = registry.menuRegistry.loadPlugin(clsId)  # type: MarkingMenuDynamic
        if menuCls is None:
            logger.error("Missing Dynamic menu class with id: {}".format(clsId))
            return
        layout = menuCls.execute(layout, arguments)
        layout.solve()
        return MarkingMenu.buildFromLayoutData(
            layout, menuName, parent, options, arguments
        )

    def __init__(self, layout, name, parent, registry):
        """
        :param layout: the markingMenu layout instance
        :type layout: :class:`Layout`
        :param name: The markingMenu name
        :type name: str
        :param parent: The full path to the parent widget
        :type parent: str
        :param registry: The command executor instance
        :type registry: :class:`Registry`
        """
        self.layout = layout
        self.name = name
        self.parent = parent
        self.popMenu = None  # the menu popup menu, gross thanks maya
        self.registry = registry
        # Arguments that will be passed to the menu item command to be executed
        self.commandArguments = {}
        if cmds.popupMenu(name, ex=True):
            cmds.deleteUI(name)

        self.options = {
            "allowOptionBoxes": True,
            "altModifier": False,
            "button": 1,
            "ctrlModifier": False,
            "postMenuCommandOnce": True,
            "shiftModifier": False,
        }

    def asQObject(self):
        """Returns this markingMenu as a PYQT object

        :return: Return this :class:`MarkingMenu` as a :class:`qt.QMenu` instance
        :rtype: QMenu
        """
        return mayaui.toQtObject(self.name, widgetType=QtWidgets.QMenu)

    def attach(self, **arguments):
        """Generates the marking menu using the parent marking menu.

        The arguments passed will be passed to ech and every menuItem command, for example if
        the menu item command is a zoocommand then the zoocommand will have the arguments passed to it.

        :param arguments: A Dict of arguments to pass to each menuItem command.
        :type arguments: dict
        :return: if the parent menu doesn't exist then False will be returned, True if successfully attached
        :rtype: bool
        """
        if cmds.popupMenu(self.parent, exists=True):
            self.commandArguments = arguments
            self._show(self.parent, self.parent)
            return True
        return False

    def create(self, **arguments):
        """Creates a new popup markingMenu parented to self.parent instance, use :func: `MarkingMenu:attach` if you
        need to add to existing markingmenu.

        :return: current instance
        :rtype: :class:`MarkingMenu`
        """
        if cmds.popupMenu(self.name, exists=True):
            cmds.deleteUI(self.name)
        self.commandArguments = arguments
        self.popMenu = cmds.popupMenu(
            self.name,
            parent=self.parent,
            markingMenu=True,
            postMenuCommand=self._show,
            **self.options
        )
        return self

    def _show(self, menu, parent):
        cmds.setParent(menu, menu=True)
        cmds.menu(menu, edit=True, deleteAllItems=True)
        self.show(self.layout, menu, parent)

    def kill(self):
        """Destroys the pop menu from maya."""
        if cmds.popupMenu(self.name, ex=True):
            cmds.deleteUI(self.name)

    def addCommand(self, item, parent, radialPosition=None):
        """Adds the specified command item to the parent menu.

        :param item: {"type": "command", "id": "myCustomCommand"}
        :type item: dict
        :param parent: The parent menu string
        :type parent: str
        :param radialPosition: The radial position i.e "N"
        :type radialPosition: str or None
        """
        command = self.registry.commandRegistry.loadPlugin(item["id"])
        if command is None:
            logger.warning("Failed To find Command: {}".format(item["id"]))
            return
        cmdArgOverride = dict(**self.commandArguments)
        cmdArgOverride.update(item.get("arguments", {}))
        uiData = command.uiData(cmdArgOverride)
        uiData.update(item)
        optionBox = uiData.get("optionBox", False)
        enable = uiData.get("enable", True)
        show = uiData.get("show", True)
        checkBox = jsonToBool(uiData.get("checkBox", None))
        radioButtonState = uiData.get("radioButtonState", False)
        try:
            label = uiData["label"]
        except KeyError:
            logger.error("Label key missing from marking menu command: {}".format(item))
            return
        if not show:
            return
        arguments = dict(
            label=label,
            parent=parent,
            command=partial(command._execute, cmdArgOverride, False),
            optionBox=False,
            enable=enable,
        )
        iconPath = uiData.get("icon", "")
        iconOptionBox = uiData.get("optionBoxIcon", "")
        if iconPath:
            newIconPath = iconlib.iconPathForName(
                iconPath
            )  # look for zoo icon, returns fullPath or "" if not found
            if (
                newIconPath
            ):  # if zoo icon path found use it, otherwise keep the original, could be a native Maya icon
                iconPath = newIconPath
            arguments["image"] = iconPath

        if uiData.get("isRadioButton", False):
            arguments["radioButton"] = radioButtonState
        if uiData.get("italic", False):
            arguments["italicized"] = True
        if uiData.get("bold", False):
            arguments["boldFont"] = True
        if radialPosition is not None:
            arguments["radialPosition"] = radialPosition
        if checkBox is not None:
            arguments["checkBox"] = checkBox

        cmds.menuItem(**arguments)
        if optionBox:
            iconOptionBox = iconlib.iconPathForName(iconOptionBox)
            if os.path.exists(iconOptionBox):
                arguments["optionBoxIcon"] = iconOptionBox
            arguments.update(
                dict(
                    optionBox=optionBox,
                    command=partial(command._execute, cmdArgOverride, True),
                )
            )
            cmds.menuItem(**arguments)

    def addSeparator(self, menu, item=None):
        """Adds separator to menu

        :param menu:
        :type menu:
        """
        if item and item.get(
            "id"
        ):  # If we need to do some extra stuff to the separator
            command = self.registry.commandRegistry.loadPlugin(item["id"])
            cmdArgOverride = dict(**self.commandArguments)
            cmdArgOverride.update(item.get("arguments", {}))
            uiData = command.uiData(cmdArgOverride)
            uiData.update(item)
            if uiData.get("show") is False:
                return
        cmds.menuItem(parent=menu, divider=True)

    def _buildGeneric(self, data, menu):
        for item in data:
            if item["type"] == "command":
                self.addCommand(item, menu)
                continue
            elif item["type"] == "menu":
                subMenu = cmds.menuItem(label=item["label"], subMenu=True, parent=menu)
                self._buildGeneric(item["children"], subMenu)
            elif item["type"] == "radioButtonMenu":
                subMenu = cmds.menuItem(label=item["label"], subMenu=True, parent=menu)
                cmds.radioMenuItemCollection(parent=subMenu)
                self._buildGeneric(item["children"], subMenu)
            elif item["type"] == "separator":
                self.addSeparator(menu, item)

    def show(self, layout, menu, parent):
        """Main Method that converts the layout to a maya marking menu.

        If implementing a subclass then super must be called.

        :param layout: The layout class to convert
        :type layout: :class:`Layout`
        :param menu: The menu fullPath which commands will be attached too.
        :type menu: str
        :param parent: The Parent full Path name.
        :type parent: str
        """
        for item, data in layout.items():
            if not data:
                continue
            # menu generic
            if item == "generic":
                self._buildGeneric(data, menu)
                continue
            # nested marking menu
            elif isinstance(data, Layout):
                radMenu = cmds.menuItem(
                    label=data["id"],
                    subMenu=True,
                    parent=menu,
                    radialPosition=item.upper(),
                )
                self.show(data, radMenu, parent)
            elif data["type"] == "command":
                self.addCommand(data, parent=menu, radialPosition=item.upper())

    def allowOptionBoxes(self):
        """Returns a boolean indicating if option boxes are enabled on the popupMenu.

        :rtype: bool
        """
        return cmds.popupMenu(self.name, q=True, allowOptionBoxes=True)

    def altModifier(self):
        """Returns a boolean indicating if the alt modifier is enabled on the popupMenu.

        :rtype: bool
        """
        return cmds.popupMenu(self.name, q=True, altModifier=True)

    def button(self):
        """Returns the button number that is associated with the popupMenu.

        :rtype: int
        """
        return cmds.popupMenu(self.name, q=True, button=True)

    def ctrlModifier(self):
        """returns a boolean indicating if the ctrl modifier is enabled on the popupMenu.

        :rtype: bool
        """
        return cmds.popupMenu(self.name, q=True, ctrlModifier=True)

    def deleteAllItems(self):
        """deletes all items in the popupMenu and returns True if successful.

        :rtype: bool
        """
        try:
            cmds.popupMenu(self.name, e=True, deleteAllItems=True)
        except Exception:
            return False
        return True

    def exists(self):
        """returns a boolean indicating if the popupMenu exists in the Maya UI.

        :rtype: bool
        """
        return cmds.popupMenu(self.name, exists=True)

    def itemArray(self):
        """Return string array of the menu item names.

        :rtype: list[str]
        """
        if self.exists():
            return cmds.popupMenu(self.name, q=True, itemArray=True)

    def markingMenu(self):
        """Returns a boolean indicating if the popupMenu is a marking menu.

        :rtype: bool
        """
        if self.exists():
            return cmds.popupMenu(self.name, q=True, markingMenu=True)
        return False

    def numberOfItems(self):
        """Returns the number of items in the popupMenu.

        :rtype: int
        """
        if self.exists():
            return cmds.popupMenu(self.name, q=True, numberOfItems=True)
        return 0

    def postMenuCommand(self, command):
        """Posts the given command to be executed after the popupMenu is created."""
        if self.exists():
            cmds.popupMenu(self.name, e=True, postMenuCommand=command)

    def postMenuCommandOnce(self, state):
        """Sets the state of postMenuCommandOnce on the popupMenu."""
        if self.exists():
            cmds.popupMenu(self.name, e=True, postMenuCommandOnce=state)

    def shiftModifier(self):
        """Returns a boolean indicating if the shift modifier is enabled on the popupMenu."""
        if self.exists():
            return cmds.popupMenu(self.name, q=True, shiftModifier=True)
        return False

    def setShiftModifier(self, value):
        """Sets the state of the shift modifier on the popupMenu."""
        if self.exists():
            return cmds.popupMenu(self.name, e=True, shiftModifier=value)

    def setParent(self, parent):
        """Sets the parent of the popupMenu to the given parent."""
        if self.exists():
            return cmds.popupMenu(self.name, e=True, parent=parent.objectName())

    def setCtrlModifier(self, value):
        """Sets the state of the ctrl modifier on the popupMenu."""
        if self.exists():
            return cmds.popupMenu(self.name, e=True, ctrlModifier=value)

    def setAltModifier(self, state):
        """Sets the state of the alt modifier on the popupMenu."""
        if self.exists():
            return cmds.popupMenu(self.name, e=True, altModifier=state)

    def setUseLeftMouseButton(self):
        """Sets the popupMenu to use the left mouse button."""
        self.options["button"] = 1
        if self.exists():
            return cmds.popupMenu(self.name, e=True, button=1)

    def setUseRightMouseButton(self):
        """Sets the popupMenu to use the right mouse button."""
        self.options["button"] = 3
        if self.exists():
            return cmds.popupMenu(self.name, e=True, button=3)

    def setUseMiddleMouseButton(self):
        """Sets the popupMenu to use the middle mouse button."""
        self.options["button"] = 2
        if self.exists():
            return cmds.popupMenu(self.name, e=True, button=2)


class MarkingMenuDynamic(plugin.Plugin):
    """Marking Menu Dynamic allows for subclasses to dynamic generate the marking menu layout."""

    documentation = __doc__
    id = ""

    def execute(self, layout, arguments):
        raise NotImplementedError("Execute method must be implement in subclasses")


class MarkingMenuCommand(plugin.Plugin):
    """Marking menu plugin which is used to define a single Marking menu action.

    Client code should subclass from this command class.

    Override the :meth:`MarkingMenuCommand.execute` method to customize standard
    left click execution.

    Override the :meth:`MarkingMenuCommand.executeUI` method to customize the option
    box on the action if the uiData["optionBox"] is True

    """

    # Specifying a Docstring for the class will act as the tooltip.
    documentation = __doc__
    # a unique identifier for a class, once release to public domain this /
    # id should never be changed due to being baked into the maya scene.
    id = ""
    # The developers name must be specified so it makes tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        """UiData defines the visuals of the command action.

        :param arguments: The global arguments passed to the command from the parent menu.
        :type arguments: dict
        :return:
        :rtype: dict
        """
        return {
            "icon": arguments.get("icon", ""),
            "label": arguments.get("label", ""),
            "bold": False,
            "italic": False,
            "optionBox": False,
            "enable": True,
            "checkBox": None,  # set True if checked, False if unchecked. To disable set to None.
        }

    def _execute(self, arguments, optionBox=False, *args):
        from zoo.libs.maya.triggers import triggercallbackutils

        with triggercallbackutils.blockSelectionCallback():
            if optionBox:
                self.executeUI(arguments)
            else:
                self.execute(arguments)

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI()
        for a optionBox.

        :type arguments: dict
        """
        pass

    def executeUI(self, arguments):
        """The executeUI method is called when the user triggering the box icon
        on the right handle side of the action item.

        For this method to be called you must specify in the UIData method "optionBox": True.

        :type arguments: dict
        """
        pass
