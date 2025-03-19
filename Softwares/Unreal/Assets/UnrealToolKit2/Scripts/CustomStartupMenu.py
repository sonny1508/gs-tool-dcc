import unreal
import json
import os

# Load menu configuration from JSON file
def load_menu_config(file_path):
    with open(file_path, 'r') as json_file:
        return json.load(json_file)

# Recursively add sub-menus and commands from the configuration
def add_menus_from_config(parent_menu, config):
    for menu in config.get('sub_menus', []):
        sub_menu = parent_menu.add_sub_menu(owner=parent_menu.menu_name, section_name=menu['section_name'], name=menu['name'], label=menu['label'])
        add_menus_from_config(sub_menu, menu)
    for command in config.get('commands', []):
        # Embed the logic to execute the command directly in the command string
        if 'is_blutility' in command.keys() and command['is_blutility']==True:
            command_string = f"import unreal; editor_utility_subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem); asset = unreal.EditorAssetLibrary.load_asset('{command['path']}'); editor_utility_subsystem.try_run(asset)"
        else:
            command_string = f"import unreal; editor_utility_subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem); asset = unreal.EditorAssetLibrary.load_asset('{command['path']}'); editor_utility_subsystem.spawn_and_register_tab(asset)"
        menu_entry = unreal.ToolMenuEntry(name=command['name'], type=unreal.MultiBlockType.MENU_ENTRY)
        menu_entry.set_label(command['label'])
        if 'tool_tip' in command.keys():
            menu_entry.set_tool_tip(command['tool_tip'])
        menu_entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, '', command_string)
        parent_menu.add_menu_entry(parent_menu.menu_name, menu_entry)

# Main function to setup menus from JSON file
def setup_menus_from_json(file_path):
    config = load_menu_config(file_path)
    menus = unreal.ToolMenus.get()
    main_menu = menus.find_menu("LevelEditor.MainMenu")

    if main_menu != None:
        for menu in config['menus']:
            my_menu = main_menu.add_sub_menu(owner="UnrealPythonScripts", section_name=menu['section_name'], name=menu['name'], label=menu['label'])
            add_menus_from_config(my_menu, menu)

        # Refresh UI to apply changes
        menus.refresh_all_widgets()

# Setup the path to your JSON configuration file
if unreal.is_editor():
    executionPath = os.getcwd()
    scriptPath = executionPath.split("Engine")[0] + '\\Engine\\Plugins\\ignition\\ignitiongameplay\\content\\assets\\UnrealToolKit2\\Scripts\\CustomStartupMenuEntries.json'
    setup_menus_from_json(scriptPath)
