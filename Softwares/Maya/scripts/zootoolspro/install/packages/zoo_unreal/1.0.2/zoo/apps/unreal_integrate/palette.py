import unreal

from zoo.apps.toolpalette import palette
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class UnrealPalette(palette.ToolPalette):
    application = "unreal"

    def __init__(self, parent=None):
        super(UnrealPalette, self).__init__(parent)
        self._menuCache = {}

    def removePreviousMenus(self):
        """Removes the previous menus from the Unreal Palette.
        """
        menus = unreal.ToolMenus.get()
        for menu in self.menuManager.menus:
            menus.remove_menu(menu.id)
            menus.unregister_owner_by_name(menu.id)

    def createMenus(self):
        """Create menus in the Unreal Palette Tool Palette.
        """
        super(UnrealPalette, self).createMenus()
        unreal.ToolMenus.get().refresh_all_widgets()
        self._menuCache = {}

    def createMenu(self, menuItem, parentMenu):
        """Creates the Unreal menu instance.

        :param menuItem: The information about the menu item being created.
        :type menuItem: :class:`zoo.apps.toolpalette.layouts.MenuItem`
        :param parentMenu: The parent menu that the new menu will be added to.
        :type parentMenu: :class:`zoo.apps.toolpalette.layouts.MenuItem`
        :return: The newly created Unreal menu.
        :rtype: :class:`unreal.ToolMenu`
        """
        parentMenuInstance = self._menuCache.get(parentMenu.id) if parentMenu is not None else None
        if parentMenuInstance is None:
            # toplevel menu
            menus = unreal.ToolMenus.get()
            mainMenu = menus.find_menu("LevelEditor.MainMenu")
            parentMenuInstance = mainMenu
        ueMenu = parentMenuInstance.add_sub_menu(owner=menuItem.id, section_name=menuItem.label,
                                                 name=menuItem.id, label=menuItem.label, tool_tip=menuItem.tooltip)
        ueMenu.searchable = True
        self._menuCache[menuItem.id] = ueMenu
        return ueMenu

    def createMenuAction(self, menuItem, command):
        """Creates the Unreal menu action instance.

        :param menuItem: The menu item to create an action for.
        :type menuItem: :class:`zoo.apps.toolpalette.layouts.MenuItem`
        :param command: The command to be executed when the action is triggered
        :type command: str
        :return: The created menu action.
        :rtype: :class:`unreal.ToolMenuEntry`
        """
        # itemType = menuItem.type
        parentItem = menuItem.parent
        parent = self._menuCache[menuItem.parent.id]
        actionType = unreal.MultiBlockType.MENU_ENTRY
        if menuItem.isSeparator() or menuItem.isGroup():
            actionType = unreal.MultiBlockType.SEPARATOR

        script = ZooMenuItemScript()
        script.id = menuItem.id
        script.toolTip = menuItem.tooltip
        script.label = menuItem.label

        isCheckable = menuItem.isCheckable
        isChecked = menuItem.isChecked
        interface_action_type = unreal.UserInterfaceActionType.NONE
        if isCheckable:
            interface_action_type = unreal.UserInterfaceActionType.TOGGLE_BUTTON
            script.value = unreal.CheckBoxState.CHECKED if isChecked else unreal.CheckBoxState.UNCHECKED
        else:
            script.value = unreal.CheckBoxState.UNDETERMINED

        e = unreal.ToolMenuEntry(
            name=menuItem.id,
            type=actionType,
            user_interface_action_type=interface_action_type,
            script_object=script
            # If you pass a type that is not supported Unreal will let you know,
        )
        parent.add_menu_entry(parentItem.label, e)
        self._menuCache[menuItem.id] = e


@unreal.uclass()
class ZooMenuItemScript(unreal.ToolMenuEntryScript):
    """Unreal Zoo tools menu item instance
    """
    id = unreal.uproperty(str)
    label = unreal.uproperty(str)
    toolTip = unreal.uproperty(str)
    checkState = unreal.uproperty(unreal.CheckBoxState)

    @unreal.ufunction(override=True)
    def execute(self, context):
        super(self.__class__, self).execute(context)
        from zoo.apps.toolpalette import run
        result = run.currentInstance().executePluginById(self.id)
        if self.checkState != unreal.CheckBoxState.UNDETERMINED:
            self.checkState = unreal.CheckBoxState.CHECKED if result else unreal.CheckBoxState.UNCHECKED

    @unreal.ufunction(override=True)
    def get_label(self, context):
        return self.label

    @unreal.ufunction(override=True)
    def get_check_state(self, context):
        return self.checkState

    def get_tool_tip(self, context):
        return self.toolTip
