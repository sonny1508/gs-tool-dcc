import os, uuid
from collections import OrderedDict

from zoo.libs.utils import filesystem
from zoo.core.util import zlogging
from zoo.preferences.core import preference
from zoo.core import api

logger = zlogging.getLogger(__name__)


class HierarchyItem(object):
    def __init__(self, data, parent=None):
        self._children = []  # type: list[HierarchyItem]
        self.parent = parent  # type: HierarchyItem
        self.label = data.get("label", "")
        self.type = data.get("type", "")

    def __len__(self):
        return len(self._children)

    def __iter__(self):
        return self.iterChildren(recursive=False)

    def path(self):
        if self.parent is not None:
            return "/".join((self.parent.path(), self.label))
        return self.label

    def root(self):
        """Returns the top level HierarchyItem item.

        :rtype: :class:`HierarchyItem`
        """
        if self.parent is None:
            return self
        return self.parent.root()

    def sortChildren(self, recursive=True):
        # first update the sort orders for any child which is 0
        sortOrder = 0
        for child in self._children:
            if child.sortOrder == 0:
                child.sortOrder = sortOrder
                sortOrder = sortOrder + 1

        self._children = sorted(self._children, key=lambda x: x.sortOrder)

        if recursive:
            for child in self._children:
                child.sortChildren(recursive=recursive)

    @property
    def children(self):
        """
        :rtype: list[:class:`HierarchyItem`]
        """
        return self._children

    @children.setter
    def children(self, newChildren):
        self._children = newChildren

    def iterChildren(self, recursive=False):
        for child in self._children:
            yield child
            if not recursive:
                continue
            for subChild in child.iterChildren(recursive):
                yield subChild

    def childById(self, childId, recursive=False):
        """

        :param childId:
        :type childId: str
        :param recursive:
        :type recursive: bool
        :return:
        :rtype: :class:`MenuItem` or None
        """
        for child in self.iterChildren(recursive):
            if child.id == childId:
                return child


class Item(HierarchyItem):
    # The specialized separator type which makes the item a single line for the item.
    kSeparatorType = "separator"
    # The specialized separator type which makes the item a single line with a label.
    kGroupType = "group"
    # makes the MenuItem a Menu type which contains other items.
    kMenuType = "menu"
    # a single menuItem with just a label and no executable command.
    kLabelType = "label"
    # Shelf Button type which contains a menu of Items
    kShelfButton = "button"

    @classmethod
    def createFromDict(cls, data, parent):
        menuItem = cls(data=data, parent=parent)
        if parent is not None:
            parent.children.append(menuItem)
        menuItem.updateChildren(data.get("children", []))
        return menuItem

    def __init__(self, data, parent=None):
        super(Item, self).__init__(data, parent=parent)
        self.type = data.get("type", "action")
        self.id = data.get("id", self.label.replace(" ", ""))
        if not self.id:
            self.id = str(uuid.uuid4())
        self.tooltip = data.get("tooltip", "")
        self.icon = data.get("icon", "")
        self.color = data.get("color", "")
        self.backgroundColor = data.get("backgroundColor", "")
        self.sortOrder = data.get("sortOrder", 0)
        self.isChecked = data.get("isChecked", False)
        self.isCheckable = data.get("isCheckable", False)
        self.loadOnStartup = data.get("loadOnStartup", False)
        self.iconColor = data.get("iconColor")
        self.overlayName = data.get("overlayName")
        self.overlayColor = data.get("overlayColor", (255, 255, 255))
        self.arguments = data.get("arguments", {})
        self.tags = []
        self.metaData = {}

    @property
    def children(self):
        """

        :return:
        :rtype: list[:class:`Item`]
        """
        return self._children

    @children.setter
    def children(self, newChildren):
        self._children = newChildren

    def isVariant(self):
        return self.type == "variant"

    def isSeparator(self):
        """

        :rtype: bool
        """
        return self.type == self.kSeparatorType

    def isGroup(self):
        """

        :rtype: bool
        """
        return self.type == self.kGroupType or self.isSeparator() and self.label

    def isMenu(self):
        """

        :rtype: bool
        """
        return self.type == self.kMenuType

    def isLabel(self):
        return self.type == self.kLabelType

    def isShelfButton(self):
        return self.type == self.kShelfButton

    def update(self, data):
        """Updates the current MenuItem fields and all children which are contained in data["children"].
        If there's any missing children then those will also be added

        :param data:
        :type data:
        """
        # start with the fields ignoring id and type which shouldn't change from the initial creation
        self.label = data.get("label", self.label)
        self.tooltip = data.get("tooltip", self.tooltip)
        self.icon = data.get("icon", self.icon)
        self.color = data.get("color", self.color)
        self.backgroundColor = data.get("backgroundColor", self.backgroundColor)
        self.sortOrder = data.get("sortOrder", self.sortOrder)
        self.isChecked = data.get("isChecked", self.isChecked)
        self.isCheckable = data.get("isCheckable", self.isCheckable)
        self.loadOnStartup = data.get("loadOnStartup", self.loadOnStartup)
        self.iconColor = data.get("iconColor", self.iconColor)
        self.overlayName = data.get("overlayName", self.overlayName)
        self.overlayColor = data.get("overlayColor", self.overlayColor)
        self.arguments = data.get("arguments", self.arguments)
        # now update the children
        self.updateChildren(data.get("children", []))

    def serialize(self, valid=False):
        keys = ("type",
                "label",
                "id",
                "tooltip",
                "icon",
                "color",
                "backgroundColor",
                "sortOrder",
                "isChecked",
                "isCheckable",
                "loadOnStartup",
                "iconColor",
                "overlayName",
                "overlayColor",
                "arguments",
                "tags")
        data = {}
        if valid:
            for k in keys:
                keyValue = getattr(self, k)
                if keyValue:
                    data[k] = keyValue

        else:
            for k in keys:
                data[k] = getattr(self, k)
        return data

    def updateChildren(self, childrenData):
        raise NotImplementedError()

    def pprintTree(self):
        pprintTree(self)


class MenuItem(Item):

    def updateChildren(self, childrenData):
        # now update the children
        existingChildren = {i.id: i for i in self.children}
        for dataChild in childrenData:
            childId = dataChild.get("id", dataChild.get("label", "").replace(" ", ""))
            matchedChild = existingChildren.get(childId)
            if matchedChild is None:
                menuItem = self.createFromDict(dataChild, parent=self)
                existingChildren[menuItem.id] = menuItem
            else:
                matchedChild.update(dataChild)


class ShelfButton(Item):
    @classmethod
    def createFromDict(cls, data, parent):
        menuItem = cls(data=data, parent=parent)
        if parent is not None:
            parent.children.append(menuItem)
        menuItem.updateChildren(data.get("children", []))
        return menuItem

    def __init__(self, data, parent=None):
        super(ShelfButton, self).__init__(data, parent)

    def updateChildren(self, childrenData):
        # now update the children
        existingChildren = {i.id: i for i in self.children}
        for dataChild in childrenData:
            childId = dataChild.get("id", dataChild.get("label", "").replace(" ", ""))
            matchedChild = existingChildren.get(childId)
            if matchedChild is None:
                menuItem = MenuItem.createFromDict(dataChild, parent=self)
                if not dataChild.get("type"):
                    menuItem.type = "variant"
                existingChildren[menuItem.id] = menuItem
            else:
                matchedChild.update(dataChild)

    def pprintTree(self):
        pprintTree(self)


class Shelf(HierarchyItem):

    @classmethod
    def createFromDict(cls, data):
        shelfId = data.get("id")
        shelfName = data.get("name")
        if shelfId is None:
            shelfId = shelfName.replace(" ", "")
        newShelf = cls(shelfId=shelfId, name=shelfName)
        newShelf.sortOrder = data.get("sortOrder", 0)
        newShelf.updateChildren(data.get("children", []))
        return newShelf

    def __init__(self, shelfId, name):
        super(Shelf, self).__init__({"label": name, "type": "shelf"}, parent=None)
        self.id = shelfId
        self.metaData = {}
        self.sortOrder = 0

    @property
    def children(self):
        """

        :return:
        :rtype: list[:class:`ShelfButton`]
        """
        return self._children

    @children.setter
    def children(self, newChildren):
        self._children = newChildren

    def updateChildren(self, childrenData):
        # now update the children
        existingChildren = {i.id: i for i in self.children}
        for dataChild in childrenData:
            childId = dataChild.get("id", dataChild.get("label", "").replace(" ", ""))
            matchedChild = existingChildren.get(childId)
            if matchedChild is None:
                shelfItem = ShelfButton.createFromDict(dataChild, parent=self)
                existingChildren[shelfItem.id] = shelfItem
            else:
                matchedChild.update(dataChild)

    def update(self, data):
        """Updates the current MenuItem fields and all children which are contained in data["children"].
        If there's any missing children then those will also be added

        :param data:
        :type data:
        """
        # start with the fields ignoring id and type which shouldn't change from the initial creation
        self.label = data.get("name", self.label)

        # now update the children
        self.updateChildren(data.get("children", []))

    def pprintTree(self):
        pprintTree(self)


class ShelfManager(object):
    def __init__(self):
        self.shelves = []  # type: list[Shelf]
        self._originalShelf = []  # type: list[dict]

    def shelfById(self, shelfId):
        assert shelfId is not None, "Provided shelfId is None, Please Provide a valid id as a string."
        for shelf in self.shelves:
            if shelf.id == shelfId:
                return shelf

    def mergeFromData(self, shelfData):
        """Merges the menu data so that any missing menus or menuItems in menuData is created and added to the assigned
        parent menu.

        :param shelfData: The raw dictionary form of the shelf for merge. If the Shelf already exists it'll be updated.
        :type shelfData: dict
        """
        existingMenu = self.shelfById(shelfData.get("id", shelfData["name"]))
        if existingMenu:
            existingMenu.update(shelfData)
            return
        newShelf = Shelf.createFromDict(shelfData)
        self.shelves.append(newShelf)

    def loadFromEnv(self, envVar):
        envpath = os.getenv(envVar, "")

        layouts = []
        for path in envpath.split(os.path.pathsep):
            path = os.path.normpath(path)
            if not os.path.exists(path) or path == ".":
                continue
            try:
                logger.debug("Loading Shelf Layout: {}".format(path))
                data = filesystem.loadJson(path, object_pairs_hook=OrderedDict)
                layouts.append(data)
                self._originalShelf.append({"path": path,
                                            "layout": data})
            except ValueError:
                logger.error("Failed to load Shelf layout file: {}".format(path), exc_info=True)
            except IOError:
                logger.error("Failed to load Shelf layout File: {}, due to permission issues?".format(path),
                             exc_info=True, extra={"layoutFile": path, "environ": envpath})
            except AssertionError:
                logger.error("Failed to load shelf: {}".format(path),
                             exc_info=True)
        # first sort and merge by the files sort order
        for sortedLayout in sorted(layouts, key=lambda x: x.get("sortOrder", 0)):
            for shelf in sortedLayout.get("shelves", []):
                shelf["sortOrder"] = sortedLayout.get("sortOrder", 0)
                self.mergeFromData(shelf)
        # Everything as been merged now recursively sort the shelves buttons and menu items.
        for shelf in self.shelves:
            shelf.sortChildren(recursive=True)


class MenuManager(object):
    """Management class for all Zoo tools Main Menus.
    """
    PRIMARY_MENU_TOKEN = "{zooToolsPro}"

    def __init__(self):
        # topLevel menu's
        self.menus = []  # type: list[MenuItem]
        # contains the original untouched menu layout file contents
        self._originalMenus = []  # list[dict]
        self.preferenceInterface = preference.interface("artistPalette")
        # Create the primary menu name from the preferences
        self.menuName = self.preferenceInterface.menuName()  # default menu Name
        self.menuObjectName = "{}_mainMenu".format(self.menuName.replace(" ", "_"))  # default menu internal object name

    def menuById(self, menuId):
        """Recursively searches all menus looking for the MenuItem by its I'd.

        :param menuId: The MenuId to search for.
        :type menuId: str
        :return: The MenuItem matched by its I'd or None if not found
        :rtype: :class:`MenuItem` or None
        """
        assert menuId is not None, "Provided MenuId is None, Please Provide a valid id as a string."
        for menu in self.menus:
            if menu.type == MenuItem.kMenuType and menu.id == menuId:
                return menu
            for subMenu in menu.iterChildren(recursive=True):
                if subMenu.type == MenuItem.kMenuType and subMenu.id == menuId:
                    return subMenu

    def mergeFromData(self, menuData):
        """Merges the menu data so that any missing menus or menuItems in menuData is created and added to the assigned
        parent menu.

        :param menuData: The raw dictionary form of the menu for merge. If the Menu already exists it'll be updated.
        :type menuData: dict
        """
        existingMenu = self.menuById(menuData["id"])
        if existingMenu:
            existingMenu.update(menuData)
            return
        newMenu = MenuItem.createFromDict(menuData, parent=None)
        self.menus.append(newMenu)

    def loadFromEnv(self, envVar):
        """
        :param envVar: The environment variable key to look up. The Value is a list of paths separated by os.pathsep.
        :type envVar: str
        :raise: ValueError: ValueError is raised if there's no layout paths defined to the menu provide envVar.
        """
        paletteLayout = os.getenv(envVar, "").split(os.pathsep)
        if not paletteLayout:
            raise ValueError("No Layout configuration has been defined")
        layouts = []
        for f in iter(paletteLayout):
            if os.path.exists(f) and f.endswith(".layout") and os.path.isfile(f):
                try:
                    logger.debug("Loading menu Layout: {}".format(f))
                    dataStruct = filesystem.loadJson(f, object_pairs_hook=OrderedDict)
                except ValueError:
                    logger.error("Failed to load menu layout file due to possible syntax issue, {}".format(f))
                    continue
                layouts.append(dataStruct)
                self._originalMenus.append({"path": f,
                                            "layout": dataStruct})

        for sortedLayout in sorted(layouts, key=lambda x: x.get("sortOrder", 0)):
            menus = sortedLayout.get("menus", [])
            legacyMenu = sortedLayout.get("menu")

            if legacyMenu:  # we have ported to the new system but let's check for the old as well
                menus.append({"label": self.menuName,
                              "type": "menu",
                              "id": self.menuObjectName,
                              "children": legacyMenu})
            for menu in menus:
                if menu.get("label", MenuManager.PRIMARY_MENU_TOKEN) == MenuManager.PRIMARY_MENU_TOKEN:
                    menu["label"] = self.menuName
                    menu["id"] = self.menuObjectName
                self.mergeFromData(menu)

        # Force in the logging and version number menu items.
        topLevelZooMenu = self.menuById(self.menuObjectName)

        devMenu = topLevelZooMenu.childById("Developer")
        devMenu.updateChildren([{"type": "action", "id": "zoo.logging"}])

        topLevelZooMenu.updateChildren([{"type": MenuItem.kSeparatorType},
                                        {"type": MenuItem.kLabelType,
                                         "label": "Zoo Tools PRO - {}".format(api.currentConfig().buildVersion()),
                                         "id": "zooToolsVersion"}
                                        ]
                                       )

        for menu in self.menus:
            menu.sortChildren(recursive=True)


def pprintTree(item, _prefix="", _last=True):
    treeSep = "`- " if _last else "|- "

    values = [_prefix, treeSep, ", ".join((item.label, ": ".join(("sortOrder", str(item.sortOrder),
                                                                  )),
                                           ": ".join(("type", str(item.type),
                                                      )),
                                           ": ".join(("id", str(item.id),
                                          ))
                                           )
                                          )
              ]
    msg = "".join(values)
    print(msg)
    _prefix += "   " if _last else "|  "
    childCount = len(item)
    for i, child in enumerate(item.children):
        _last = i == (childCount - 1)
        pprintTree(child, _prefix, _last)
