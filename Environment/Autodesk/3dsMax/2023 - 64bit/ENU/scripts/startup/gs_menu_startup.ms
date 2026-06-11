-- Startup script to add GSTools to the 3ds Max menu with dynamic submenu loading
-- Save this file as gs_menu_startup.ms in your 3ds Max startup scripts folder

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
        
        -- Use menuMan to find and unregister the menu
        try
        (
            logMessage "Attempting to remove menu using menuMan methods"
            local gsMenu = menuMan.findMenu "GSTools"
            
            if gsMenu != undefined then
            (
                menuMan.unRegisterMenu gsMenu
                logMessage "Unregistered GSTools menu"
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
            #("05 Projects", #("HW3_File_Exporter"))
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
        -- Check if menu already exists with improved detection
        logMessage "Checking if GSTools menu already exists"
        local exists = checkGSToolsMenuExists()
        logMessage ("GSTools menu exists: " + exists as string)
        
        -- If the menu exists, remove it first
        if exists then
        (
            logMessage "GSTools menu already exists - removing it first"
            local removeResult = removeGSToolsMenu()
            
            if not removeResult then
                logMessage "WARNING: Could not completely remove existing menu, but will try to create anyway"
        )
        
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