-- Startup script to add GS_File_Transfer to the 3ds Max menu
-- Save this file as gs_menu_startup.ms in your 3ds Max startup scripts folder

-- Create a function to log messages
fn logMessage msg =
(
    format "[GSTools] %: %\n" (timestamp()) msg
)

-- Function to check if GSTools menu already exists using a more robust method
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
        
        -- METHOD 1: Safely look for the menu by title
        logMessage "METHOD 1: Checking menu by title"
        local menuCount = mainMenuBar.numItems()
        logMessage ("Found " + menuCount as string + " menu items to check")
        
        for i = 0 to (menuCount - 1) do
        (
            try
            (
                local item = mainMenuBar.getItem i
                
                if item != undefined and classOf item == SubMenuItem then
                (
                    try
                    (
                        local title = item.getTitle()
                        logMessage ("Menu #" + i as string + ": " + title)
                        
                        if title == "GSTools" then
                        (
                            logMessage "FOUND GSTools menu by title!"
                            return true
                        )
                    )
                    catch
                    (
                        -- Skip any items that cause errors when getting title
                        logMessage ("Error getting title for menu item " + i as string)
                    )
                )
            )
            catch
            (
                logMessage ("Error checking menu item " + i as string)
            )
        )
        
        -- METHOD 2: Try to find the menu by name in menuMan
        logMessage "METHOD 2: Trying to find by menu name"
        
        try
        (
            local gsMenu = menuMan.findMenu "GSTools"
            
            if gsMenu != undefined then
            (
                logMessage "FOUND GSTools menu using findMenu!"
                return true
            )
        )
        catch
        (
            logMessage "Error using findMenu method"
        )
        
        -- METHOD 3: Check if the persistent flag is present in user preferences
        logMessage "METHOD 3: Checking persistent flag in user preferences"
        
        try
        (
            local gsPreference = getINISetting (getMAXIniFile()) "GSTools" "MenuInstalled"
            
            if gsPreference == "true" then
            (
                logMessage "Found flag in user preferences indicating GSTools was installed"
                return true
            )
        )
        catch
        (
            logMessage "Error checking user preferences"
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
        
        if exists then
        (
            logMessage "GSTools menu already exists - skipping creation"
            return true
        )
        
        logMessage "No existing GSTools menu found - creating new one"
        
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
            
            -- Set a persistent flag in the INI file
            try
            (
                setINISetting (getMAXIniFile()) "GSTools" "MenuInstalled" "true"
                logMessage "Set persistent flag in user preferences"
            )
            catch
            (
                logMessage ("Error setting persistent flag: " + (getCurrentException()))
            )
        )
        catch
        (
            logMessage ("Error updating menu bar: " + (getCurrentException()))
            return false
        )
        
        return true
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