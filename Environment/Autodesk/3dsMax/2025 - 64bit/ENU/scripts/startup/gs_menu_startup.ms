-- Startup script to add GSTools to the 3ds Max menu bar
-- Save this file as gs_menu_startup.ms in your 3ds Max startup scripts folder
--
-- This file is identical in every 3ds Max version tree. 3ds Max 2025 replaced the
-- whole menu system, so there are two builders below fed by one shared layout:
--   * Max 2023-2024 : legacy menuMan (edits the live menu bar in place)
--   * Max 2025+     : CUI menu manager (#cuiRegisterMenus callback). menuMan does
--                     not exist there, which is what the "getMainMenuBar in
--                     undefined" error on 2025 was.

-- Expose the GSTools scripts root as a single global so any tool macro can
-- derive its own deployed path from it (e.g. _gstools_scripts_root +
-- "projects\\hw3_tools\\hw3_tools_ui.py"). Tool-agnostic: no per-tool wiring here.
global _gstools_scripts_root = (getDir #userScripts) + "\\gstools\\"

-- Create a function to log messages
fn logMessage msg =
(
    format "[GSTools] %: %\n" (timestamp()) msg
)

-- ============================================================================
--  MENU LAYOUT (shared by both builders)
-- ============================================================================
-- Each tool is the name of a macroScript registered under category:"GSTools" by
-- the .mcr files in usermacros/.
--
-- The GUIDs are only read on 2025+, where every menu and menu item is keyed by a
-- stable id (the user's saved menu customisations point at those ids). Once
-- deployed an id must never change; give every new folder or tool a fresh GUID.
global gsMacroCategory = "GSTools"
global gsMenuTitle = "GSTools"
global gsMenuId = "05f1db4d-4e7d-422c-aece-b33b8fdd48dc"

global gsMenuLayout = #(
    -- #("FolderName", "folder GUID", #( #("MacroName", "item GUID"), ... ))
    #("01_General", "fce4e591-5a6a-490e-89d3-bbfc58fdc5ac", #(
        #("Material_ID_Remapper", "6477e6f6-a69a-4a56-8c23-6da81fd4ee4f"),
        #("Poly_Smoother",        "fa3be31b-6e72-4170-b508-b66291c4d07a"),
        #("Texel_Density",        "27eda269-9269-47cb-84b6-e156811737a6"),
        #("Material_Manager",     "32ee7e30-d859-4197-8df8-02213cf61855")
    )),
    #("02_UV", "03f46d2b-39b1-4ac2-a20d-45c9df6af35d", #(
        #("UV_Tools",             "a071431a-7302-4935-842e-2ad8e587abe5")
    )),
    #("03_Normals", "beaf19f1-279c-4e32-b069-d0076fb685b2", #(
        #("Custom_Normals_Tool",  "f3dcba31-cc09-4110-9670-63a2f88c8dcb")
    )),
    #("04_Review", "2f84173d-b601-46a1-aaf6-ef288197e56c", #(
        #("Scene_Checker",        "e67dddad-0075-4dc8-be0d-b38e749314a5")
    )),
    #("05_File I/O", "8fbcfc1f-e300-4b14-998c-84ec5dbbe6b0", #(
        #("GS_File_Exporter",     "aba1dae5-4d29-4d79-a306-16451493422e"),
        #("GS_File_Transfer",     "3dc350fa-1fb6-462d-b341-16d80d9b01b6")
    )),
    #("06_Projects", "6084fbec-b16e-4320-bd16-aeea4aa7aaae", #(
        #("HW3_File_Exporter",    "4e4816c3-5f8a-4b1f-a8f1-bf827dbfc254"),
        #("HW3_Tools",            "92e142de-a615-4dfe-ad8f-bc059d40004b")
    ))
    -- Add more folders here as needed
)

-- ============================================================================
--  3ds Max 2023-2024 : legacy menuMan
-- ============================================================================

-- Function to remove existing GSTools menu
fn removeGSToolsMenu =
(
    logMessage "Attempting to remove existing GSTools menu"

    try
    (
        -- Get the main menu bar
        local mainMenuBar = menuMan.getMainMenuBar()

        if mainMenuBar == undefined then
        (
            logMessage "ERROR: Could not get main menu bar for removal"
            return false
        )

        -- STEP 1: Detach our top-level entries FROM THE MENU BAR.
        --
        -- mainMenuBar.numItems / getItem enumerate the items ON THE MENU BAR (not
        -- the global registry), and each bar entry is a SubMenuItem whose
        -- .getSubMenu gives the actual menu. unRegisterMenu alone does NOT reliably
        -- drop the visible bar entry, which is why a stale "GSTools" survived each
        -- restart and a fresh one got appended -> duplicate menus. We must remove
        -- the bar item by position.
        --
        -- Iterate in reverse so positions stay valid as we remove. Re-scan in a
        -- loop because removing shifts indices and there may be >1 duplicate.
        local removedAny = true
        local pass = 0
        while removedAny and pass < 50 do
        (
            removedAny = false
            pass += 1
            for i = (mainMenuBar.numItems()) to 1 by -1 do
            (
                local item = mainMenuBar.getItem i
                if item == undefined do continue

                local sub = item.getSubMenu()
                local title = if sub != undefined then sub.getTitle() else (item.getTitle())

                if title == gsMenuTitle then
                (
                    try
                    (
                        mainMenuBar.removeItemByPosition i
                        removedAny = true
                        logMessage ("Removed GSTools entry from menu bar at position " + i as string)
                    )
                    catch
                    (
                        logMessage ("Could not remove menu-bar item: " + (getCurrentException()))
                    )
                )
            )
        )

        -- STEP 2: Unregister the now-orphaned GSTools menu(s) AND submenus from the
        -- registry so createMenu starts clean. menuMan.findMenu returns the first
        -- match only, so loop until none of our owned names remain.
        try
        (
            logMessage "Unregistering orphaned GSTools menus from registry"

            local ownedMenuNames = #(gsMenuTitle)
            for folderInfo in gsMenuLayout do append ownedMenuNames folderInfo[1]

            removedAny = true
            pass = 0
            while removedAny and pass < 50 do
            (
                removedAny = false
                pass += 1
                for nm in ownedMenuNames do
                (
                    local m = menuMan.findMenu nm
                    if m != undefined then
                    (
                        try
                        (
                            menuMan.unRegisterMenu m
                            removedAny = true
                            logMessage ("Unregistered menu: " + nm)
                        )
                        catch
                        (
                            logMessage ("Could not unregister menu: " + (getCurrentException()))
                        )
                    )
                )
            )
        )
        catch
        (
            logMessage ("Error unregistering menu: " + (getCurrentException()))
        )

        -- Update the menu bar after removal
        try
        (
            menuMan.updateMenuBar()
            logMessage "Menu bar updated after removal"

            -- Clear the installation flag
            if getAppData rootNode 12345 == "GSToolsMenuInstalled" then
            (
                setAppData rootNode 12345 ""
                logMessage "Cleared GSToolsMenuInstalled flag"
            )

            return true
        )
        catch
        (
            logMessage ("Error updating menu bar after removal: " + (getCurrentException()))
            return false
        )
    )
    catch
    (
        logMessage ("CRITICAL ERROR in removeGSToolsMenu: " + (getCurrentException()))
        return false
    )
)

-- Function to create submenus with macros
fn createSubmenusWithMacros gsToolsMenu =
(
    try
    (
        -- Create each folder and add macros
        for folderInfo in gsMenuLayout do
        (
            local folderName = folderInfo[1]
            local toolList = folderInfo[3]

            -- Skip empty folders
            if toolList.count == 0 then continue

            -- Create folder submenu
            local folderMenu = menuMan.createMenu folderName
            logMessage ("Created submenu for folder: " + folderName)

            -- Add each macro to the folder menu
            for toolInfo in toolList do
            (
                local macroName = toolInfo[1]
                try
                (
                    local actionItem = menuMan.createActionItem macroName gsMacroCategory
                    if actionItem != undefined then
                    (
                        folderMenu.addItem actionItem -1
                        logMessage ("Added " + macroName + " to " + folderName + " submenu")
                    )
                    else
                        logMessage ("WARNING: Could not create menu item for: " + macroName)
                )
                catch
                (
                    logMessage ("Error adding macro " + macroName + " to menu: " + (getCurrentException()))
                )
            )

            -- Create submenu item and add to main GSTools menu
            local subMenuItem = menuMan.createSubMenuItem folderName folderMenu
            if subMenuItem != undefined then
            (
                gsToolsMenu.addItem subMenuItem -1
                logMessage ("Added " + folderName + " submenu to GSTools menu")
            )
        )

        return true
    )
    catch
    (
        logMessage ("Error creating submenus: " + (getCurrentException()))
        return false
    )
)

-- Create the GSTools menu with submenus
fn createGSToolsMenu =
(
    try
    (
        -- Always purge any existing GSTools menus/submenus first. This is a safe
        -- no-op when none exist, and unlike the old findMenu-based check it clears
        -- ALL duplicates that accumulate across restarts.
        logMessage "Removing any existing GSTools menus before rebuild"
        removeGSToolsMenu()

        logMessage "Creating new GSTools menu"

        -- Get the main menu bar
        logMessage "Getting main menu bar"
        local mainMenuBar = menuMan.getMainMenuBar()

        if mainMenuBar == undefined then
        (
            logMessage "ERROR: Could not get main menu bar"
            return false
        )

        -- Create a new menu
        logMessage "Creating new GSTools menu"
        local gsToolsMenu = undefined

        try
        (
            gsToolsMenu = menuMan.createMenu gsMenuTitle
            logMessage "GSTools menu object created"
        )
        catch
        (
            logMessage ("Error creating menu: " + (getCurrentException()))
            return false
        )

        if gsToolsMenu == undefined then
        (
            logMessage "ERROR: Failed to create GSTools menu object"
            return false
        )

        -- Create submenus and add macros
        createSubmenusWithMacros gsToolsMenu

        -- Create a submenu item for the main GSTools menu
        logMessage "Creating main GSTools submenu item"
        local subMenuItem = undefined

        try
        (
            subMenuItem = menuMan.createSubMenuItem gsMenuTitle gsToolsMenu
            logMessage "GSTools submenu item created"
        )
        catch
        (
            logMessage ("Error creating main submenu item: " + (getCurrentException()))
            return false
        )

        if subMenuItem == undefined then
        (
            logMessage "ERROR: Failed to create main submenu item"
            return false
        )

        -- Add submenu to main menu bar
        logMessage "Adding GSTools submenu to main menu bar"

        try
        (
            mainMenuBar.addItem subMenuItem -1
            logMessage "Added GSTools menu to main menu bar"
        )
        catch
        (
            logMessage ("Error adding submenu to main menu bar: " + (getCurrentException()))
            return false
        )

        -- Update the menu bar
        logMessage "Updating menu bar"

        try
        (
            menuMan.updateMenuBar()
            logMessage "Menu bar updated successfully"

            -- Set a flag to indicate menu has been installed
            setAppData rootNode 12345 "GSToolsMenuInstalled"
            logMessage "Set GSToolsMenuInstalled flag"

            return true
        )
        catch
        (
            logMessage ("Error updating menu bar: " + (getCurrentException()))
            return false
        )
    )
    catch
    (
        -- Print the error message for debugging
        logMessage ("CRITICAL ERROR in createGSToolsMenu: " + (getCurrentException()))
        return false
    )
)

-- ============================================================================
--  3ds Max 2025+ : CUI menu manager
-- ============================================================================
-- Menus are no longer edited in place. Every time Max loads its menus (startup,
-- workspace switch, menu-editor reset) it rebuilds the whole tree from its config
-- and fires #cuiRegisterMenus so scripts can add their items to that fresh tree.
-- So there is nothing to purge and no duplicates to chase: register a callback
-- that adds GSTools, and Max calls it every time it rebuilds.

-- Action table id of macroScripts; their action ids are "MacroName`Category".
global gsMacroActionTable = 647394
global gsCuiMenuBuilt = false

fn gsBuildCuiMenu =
(
    try
    (
        local menuMgr = callbacks.notificationParam()
        local gsToolsMenu = menuMgr.mainMenuBar.CreateSubMenu gsMenuId gsMenuTitle

        for folderInfo in gsMenuLayout do
        (
            local folderName = folderInfo[1]
            local toolList = folderInfo[3]
            if toolList.count == 0 then continue

            local folderMenu = gsToolsMenu.CreateSubMenu folderInfo[2] folderName
            for toolInfo in toolList do
            (
                local macroName = toolInfo[1]
                try
                (
                    local item = folderMenu.CreateAction toolInfo[2] gsMacroActionTable (macroName + "`" + gsMacroCategory)
                    if item == undefined do
                        logMessage ("WARNING: Could not create menu item for: " + macroName)
                )
                catch
                (
                    logMessage ("Error adding macro " + macroName + " to menu: " + (getCurrentException()))
                )
            )
        )

        gsCuiMenuBuilt = true
        logMessage "GSTools menu added to main menu bar"
    )
    catch
    (
        logMessage ("CRITICAL ERROR in gsBuildCuiMenu: " + (getCurrentException()))
    )
)

-- Safety net, runs once Max has finished starting. Max is expected to load its
-- menus after startup scripts run, so gsBuildCuiMenu has normally fired by now.
-- If it has not, the menus were loaded before this script registered, so reload
-- them to make #cuiRegisterMenus fire again. CuiMenuMgr is the interface name in
-- MenuMan.dll; if it is not reachable as a global, the log line below says so.
fn gsCheckCuiMenu =
(
    if not gsCuiMenuBuilt then
    (
        logMessage "#cuiRegisterMenus has not fired since registration, forcing a menu reload"
        try
        (
            CuiMenuMgr.LoadConfiguration (CuiMenuMgr.GetCurrentConfiguration())
        )
        catch
        (
            logMessage ("Could not reload menus: " + (getCurrentException()))
        )
    )
)

fn gsRegisterCuiMenu =
(
    -- Replace any earlier registration so re-running this script never stacks callbacks.
    callbacks.removeScripts id:#GSToolsMenu
    callbacks.addScript #cuiRegisterMenus gsBuildCuiMenu id:#GSToolsMenu
    callbacks.addScript #postSystemStartup gsCheckCuiMenu id:#GSToolsMenu
    logMessage "Registered GSTools menu callback"
)

-- ============================================================================
--  ENTRY POINT
-- ============================================================================

logMessage "====== STARTING MENU SETUP ======"

-- 27000 = 3ds Max 2025, the release that replaced menuMan.
if (maxVersion())[1] >= 27000 then
    gsRegisterCuiMenu()
else
    createGSToolsMenu()

-- Print a message to confirm the script has run
logMessage "GSTools menu script has completed execution"
