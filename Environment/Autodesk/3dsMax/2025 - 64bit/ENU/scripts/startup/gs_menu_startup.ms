-- Startup script to add GSTools to the 3ds Max 2025 menu using new CuiMenuManager API
-- Save this file as gs_menu_startup.ms in your 3ds Max startup scripts folder

-- Create a function to log messages
fn logMessage msg =
(
    format "[GSTools] %: %\n" (timestamp()) msg
)

-- Main callback function that creates the GSTools menu
fn createGSToolsMenuCallback =
(
    try
    (
        logMessage "====== STARTING MENU SETUP (3ds Max 2025) ======"

        -- Get the CuiMenuManager from the notification parameter
        local menuMgr = callbacks.notificationParam()

        if menuMgr == undefined then
        (
            logMessage "ERROR: Could not get CuiMenuManager from callback"
            return false
        )

        -- Get the main menu bar
        local mainMenuBar = menuMgr.mainMenuBar

        if mainMenuBar == undefined then
        (
            logMessage "ERROR: Could not get main menu bar"
            return false
        )

        logMessage "Got main menu bar successfully"

        -- Define folder structure with macros
        local folderStructure = #(
            #("01 General", #("Material_ID_Remapper", "Poly_Smoother", "Texel_Density", "Material_Manager")),
            #("02 UV", #("UV_Tools")),
            #("03 Review", #("Scene_Checker")),
            #("04 File I/O", #("GS_File_Exporter", "GS_File_Transfer")),
            #("05 Projects", #("HW3_File_Exporter"))
        )

        -- Create the main GSTools menu as a submenu on the main menu bar
        local gsMenuGuid = genGUID()
        local gsToolsMenu = mainMenuBar.CreateSubMenu gsMenuGuid "GSTools"

        if gsToolsMenu == undefined then
        (
            logMessage "ERROR: Failed to create GSTools menu"
            return false
        )

        logMessage "Created GSTools menu successfully"

        -- Create submenus for each folder
        for folderInfo in folderStructure do
        (
            local folderName = folderInfo[1]
            local macroNames = folderInfo[2]

            -- Skip empty folders
            if macroNames.count == 0 then continue

            try
            (
                -- Create submenu for this folder
                local folderMenuGuid = genGUID()
                local folderMenu = gsToolsMenu.CreateSubMenu folderMenuGuid folderName

                if folderMenu == undefined then
                (
                    logMessage ("WARNING: Could not create submenu for: " + folderName)
                    continue
                )
                -- Add each macro to the folder submenu
                for macroName in macroNames do
                (
                    try
                    (
                        -- Create action item for the macro
                        -- Format: CreateAction <guid> <actionTableId> <"MacroName`CategoryName">
                        -- 647394 is the MacroScript Action Table ID
                        local actionGuid = genGUID()
                        local actionRef = macroName + "`GSTools"
                        local actionItem = folderMenu.CreateAction actionGuid 647394 actionRef
                    )
                    catch
                    (
                        logMessage ("  Error adding macro " + macroName + ": " + (getCurrentException()))
                    )
                )
            )
            catch
            (
                logMessage ("Error creating submenu " + folderName + ": " + (getCurrentException()))
            )
        )

        logMessage "GSTools menu structure created successfully"
        return true
    )
    catch
    (
        logMessage ("CRITICAL ERROR in createGSToolsMenuCallback: " + (getCurrentException()))
        return false
    )
)

-- Remove any existing callback with our ID to prevent duplicates
try
(
    callbacks.removeScripts id:#gsToolsMenuSetup
    logMessage "Removed existing GSTools menu callback (if any)"
)
catch()

-- Register the callback for the #cuiRegisterMenus event
try
(
    callbacks.addScript #cuiRegisterMenus "createGSToolsMenuCallback()" id:#gsToolsMenuSetup persistent:true
    logMessage "Registered GSTools menu callback"
)
catch
(
    logMessage ("Error registering callback: " + (getCurrentException()))
)

-- Since this is a startup script and runs AFTER the #cuiRegisterMenus event,
-- we need to manually trigger a menu reload to execute our callback
try
(
    logMessage "Triggering menu reload to execute callback..."
    local menuMgr = maxops.GetICuiMenuMgr()

    if menuMgr != undefined then
    (
        local currentConfig = menuMgr.GetCurrentConfiguration()
        menuMgr.LoadConfiguration currentConfig
        logMessage "Menu configuration reloaded - GSTools menu should now be visible"
    )
)
catch
(
    logMessage ("Error reloading menu configuration: " + (getCurrentException()))
)

-- Print completion message
logMessage "GSTools menu script has completed execution"
