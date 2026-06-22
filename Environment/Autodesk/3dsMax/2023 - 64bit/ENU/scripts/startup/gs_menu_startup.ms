-- Startup script to add GSTools to the 3ds Max menu with dynamic submenu loading
-- Save this file as gs_menu_startup.ms in your 3ds Max startup scripts folder

-- Expose the GSTools scripts root as a single global so any tool macro can
-- derive its own deployed path from it (e.g. _gstools_scripts_root +
-- "projects\\hw3_tools\\hw3_tools_ui.py"). Tool-agnostic: no per-tool wiring here.
global _gstools_scripts_root = (getDir #userScripts) + "\\gstools\\"

-- Create a function to log messages
fn logMessage msg =
(
    format "[GSTools] %: %\n" (timestamp()) msg
)

-- Function to check if GSTools menu already exists
fn checkGSToolsMenuExists = 
(
    try
    (
        -- Get the main menu bar
        local mainMenuBar = menuMan.getMainMenuBar()
        
        if mainMenuBar == undefined then
        (
            logMessage "ERROR: Could not get main menu bar"
            return false
        )
        
        -- METHOD 1: Try to find the menu by name in menuMan
        logMessage "Trying to find by menu name"
        local gsMenu = menuMan.findMenu "GSTools"
        
        if gsMenu != undefined then
        (
            logMessage "FOUND GSTools menu using findMenu!"
            return true
        )
        
        logMessage "GSTools menu not found by any method"
        return false
    )
    catch
    (
        logMessage ("Error checking for existing menu: " + (getCurrentException()))
        return false
    )
)

-- Names of the menus this script creates (top-level + submenus), so every
-- leftover from prior restarts gets purged, not just the first "GSTools" match.
global gsOwnedMenuNames = #("GSTools", "01 General", "02 UV", "03 Review", "04 File I/O", "05 Projects")

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
        -- This is the part the previous rewrite got wrong. mainMenuBar.numItems /
        -- getItem enumerate the items ON THE MENU BAR (not the global registry),
        -- and each bar entry is a SubMenuItem whose .getSubMenu gives the actual
        -- menu. unRegisterMenu alone does NOT reliably drop the visible bar entry,
        -- which is why a stale "GSTools" survived each restart and a fresh one got
        -- appended -> duplicate menus. We must remove the bar item by position.
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

                if title == "GSTools" then
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

            removedAny = true
            pass = 0
            while removedAny and pass < 50 do
            (
                removedAny = false
                pass += 1
                for nm in gsOwnedMenuNames do
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
        -- Create a list of folders and associated scripts
        local folderStructure = #(
            -- #("FolderName", #("MacroName1", "MacroName2", ...))
            #("01 General", #("Material_ID_Remapper", "Poly_Smoother", "Texel_Density", "Material_Manager")),
            #("02 UV", #("UV_Tools")),
            #("03 Review", #("Scene_Checker")),
            #("04 File I/O", #("GS_File_Exporter", "GS_File_Transfer")),
            #("05 Projects", #("HW3_File_Exporter", "HW3_Tools"))
            -- Add more folders here as needed
        )
        
        -- Create each folder and add macros
        for folderInfo in folderStructure do
        (
            local folderName = folderInfo[1]
            local macroNames = folderInfo[2]
            
            -- Skip empty folders
            if macroNames.count == 0 then continue
            
            -- Create folder submenu
            local folderMenu = menuMan.createMenu folderName
            logMessage ("Created submenu for folder: " + folderName)
            
            -- Add each macro to the folder menu
            for macroName in macroNames do
            (
                try
                (
                    local actionItem = menuMan.createActionItem macroName "GSTools"
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
    logMessage "====== STARTING MENU SETUP ======"
    
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
            gsToolsMenu = menuMan.createMenu "GSTools"
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
            subMenuItem = menuMan.createSubMenuItem "GSTools" gsToolsMenu
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

-- Execute the function directly
createGSToolsMenu()

-- Print a message to confirm the script has run
logMessage "GSTools menu script has completed execution"