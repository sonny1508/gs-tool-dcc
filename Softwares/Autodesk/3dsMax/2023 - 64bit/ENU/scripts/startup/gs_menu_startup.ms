-- Startup script to add GS_File_Transfer to the 3ds Max menu
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
        
        -- METHOD 2: Check global persistent flag via user properties
        if getAppData rootNode 12345 == "GSToolsMenuInstalled" then
        (
            logMessage "Found flag indicating GSTools menu was previously installed"
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

-- Create the GSTools menu
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
        
        -- Create a menu item for the existing macro
        logMessage "Creating GS_File_Transfer menu item"
        local fileTransferItem = undefined
        
        try
        (
            fileTransferItem = menuMan.createActionItem "GS_File_Transfer" "GSTools"
            logMessage "File transfer item created"
        )
        catch
        (
            logMessage ("Error creating menu item: " + (getCurrentException()))
            -- Continue anyway, as this might not be critical
        )
        
        -- Add the menu item to the menu if it was created
        if fileTransferItem != undefined then
        (
            try
            (
                gsToolsMenu.addItem fileTransferItem -1
                logMessage "Added GS_File_Transfer item to menu"
            )
            catch
            (
                logMessage ("Error adding item to menu: " + (getCurrentException()))
                -- Continue anyway
            )
        )
        else
            logMessage "WARNING: Could not create GS_File_Transfer menu item"
        
        -- Create a submenu item
        logMessage "Creating submenu item"
        local subMenuItem = undefined
        
        try
        (
            subMenuItem = menuMan.createSubMenuItem "GSTools" gsToolsMenu
            logMessage "Submenu item created"
        )
        catch
        (
            logMessage ("Error creating submenu item: " + (getCurrentException()))
            return false
        )
        
        if subMenuItem == undefined then
        (
            logMessage "ERROR: Failed to create submenu item"
            return false
        )
        
        -- Add submenu to main menu bar
        logMessage "Adding submenu to main menu bar"
        
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
            -- Using rootNode appData instead of globalVars
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