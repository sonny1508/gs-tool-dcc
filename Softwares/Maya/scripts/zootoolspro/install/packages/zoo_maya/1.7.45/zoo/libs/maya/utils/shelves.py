import os

from maya import cmds, mel
from zoo.core.util import zlogging
from zoo.libs.maya.utils import mayaenv

logger = zlogging.getLogger(__name__)


class Shelf(object):
    """A simple class to build shelves in maya. Since the build method is empty,
    it should be extended by the derived class to build the necessary shelf elements.
    By default, it creates an empty shelf called "customShelf".

    :param name: Name of the shelf
    :type name: str
    """

    def __init__(self, name="Animation"):
        """
        :param name: Name of the shelf
        :type name: str
        """
        self.name = name
        # the maya safe name e.g replaces  spaces with underscores for internal lookups
        self.safeName = name.replace(" ", "_")
        self.labelBackground = (0, 0, 0, 0)
        self.labelColour = (.9, .9, .9)

    def setAsActive(self):
        """Set the shelf as active in maya
        """
        cmds.tabLayout(primaryShelfLayout(), edit=True, selectTab=self.safeName)

    def shortName(self):
        """The shelf name without the full path.

        :rtype: str
        """
        return self.safeName.split("|")[-1]

    def createShelf(self):
        """Create the shelf in maya
        """
        assert not cmds.shelfLayout(self.safeName,
                                    exists=True, q=True), "Shelf by the name {} already exists".format(self.name)
        logger.debug("Creating shelf: {}".format(self.name))
        self.name = cmds.shelfLayout(self.name, parent="ShelfLayout")

    def addButton(self, label, tooltip=None, icon="commandButton.png", command=None, doubleCommand=None, Type="python",
                  style="iconOnly"):
        """Adds a shelf button with the specified label, command, double click command and image.

        :param label: label of the button
        :type label: str
        :param tooltip: tooltip text to display when hovering over the button
        :type tooltip: str
        :param icon: file path to image file for button icon
        :type icon: str
        :param command: command to execute on button press
        :type command: str
        :param doubleCommand: command to execute on button double-press
        :type doubleCommand: str
        :param Type: type of command (python or mel)
        :type Type: str
        :param style: the layout of the button (iconOnly, textOnly, or iconAndText)
        :type style: str
        :return: The shelfButton UI path
        :rtype: str
        """

        cmds.setParent(self.safeName)
        command = command or ""
        doubleCommand = doubleCommand or ""
        kwargs = dict(width=34, height=34, image=icon or "", label=label, command=command,
                      doubleClickCommand=doubleCommand, annotation=tooltip or "",
                      overlayLabelBackColor=self.labelBackground,
                      style=style,
                      overlayLabelColor=self.labelColour,
                      sourceType=Type,
                      scaleIcon=True)

        if mayaenv.mayaVersion() > 2018:
            kwargs["statusBarMessage"] = tooltip
        if style != "iconOnly":
            kwargs["imageOverlayLabel"] = label
        logger.debug("Adding Shelf button: {}".format(label), extra={"command": kwargs})
        return cmds.shelfButton(**kwargs)

    @staticmethod
    def addMenuItem(parent, label, command="", icon=""):
        """Adds a menu item with the specified label, command, and image.
        :param parent: The parent menu where the item should be added.
        :type parent: str
        :param label: The label of the menu item.
        :type label: str
        :param command: The command that should be executed when the menu item is clicked.
        :type command: str
        :param icon: The path to the icon that should be used for the menu item.
        :type icon: str
        :return: The menu item that has been created.
        :rtype: str
        """

        return cmds.menuItem(parent=parent, label=label, command=command, image=icon or "")

    @staticmethod
    def addSubMenu(parent, label, icon=None):
        """Adds a sub menu item with the specified label and icon to the specified parent popup menu.

        :param parent: The parent menu where the sub menu should be added.
        :type parent: str
        :param label: The label of the sub menu.
        :type label: str
        :param icon: The path to the icon that should be used for the sub menu.
        :type icon: str
        :return: The sub menu that has been created.
        :rtype: str
        """
        return cmds.menuItem(parent=parent, label=label, icon=icon or "", subMenu=1)

    @staticmethod
    def addMenuSeparator(parent, **kwargs):
        """Adds a separator(line) on the parent menu.

        This uses the cmds.menuItem to create the separator

        :param parent: The full UI path to the parent menu
        :type parent: str
        """
        arguments = dict(parent=parent,
                         divider=True)
        arguments.update(kwargs)
        cmds.menuItem(**arguments)

    def addSeparator(self):
        """ Adds a maya shelf separator to the parent shelf

        :return: The full path to the separator
        :rtype: str
        """
        cmds.separator(parent=self.safeName, manage=True, visible=True,
                       horizontal=True, style="shelf", enableBackground=False, preventOverride=False)

    def filePath(self):
        """Returns the appropriate path for the shelf file.

        :rtype: str
        """
        tempDir = cmds.internalVar(userShelfDir=True)
        return os.path.join(tempDir, "_".join(["Shelf", self.safeName]))

    def clear(self, deleteShelf=True):
        """Checks if the shelf exists and empties it if it does or creates it if it does not."""
        cleanOldShelf(self.safeName, deleteShelf)


def shelfExists(shelfName):
    """Checks if a shelf exists in maya

    :param shelfName: The name of the shelf
    :type shelfName: str
    :return: True if the shelf exists, False if it does not
    :rtype: bool
    """
    return cmds.shelfLayout(shelfName, exists=1)


def cleanOldShelf(shelfName, deleteShelf=True):
    """Checks if the shelf exists and empties it if it does"""
    if not cmds.shelfLayout(shelfName, exists=True):
        logger.debug("Shelf Doesn't exist: {}".format(shelfName))
        return
    if deleteShelf:
        logger.debug("Removing shelf: {}".format(shelfName))
        cmds.deleteUI(shelfName)
    else:
        for each in cmds.shelfLayout(shelfName, query=True, childArray=True) or []:
            cmds.deleteUI(each)


def primaryShelfLayout():
    """Returns the main maya shelf layer path.

    Have to mel globals here, the hell?

    :return: The shelf layout path
    :rtype: str
    """
    return mel.eval("$_tempVar = $gShelfTopLevel")


def activeShelf():
    """Returns the currently active maya shelf as a :class:`Shelf` object.

    :return:
    :rtype: :class:`Shelf`
    """
    return Shelf(cmds.tabLayout(primaryShelfLayout(), query=True, selectTab=True))
