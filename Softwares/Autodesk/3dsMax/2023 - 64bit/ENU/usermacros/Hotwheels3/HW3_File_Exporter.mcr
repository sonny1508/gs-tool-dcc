macroScript HW3_File_Exporter
Category:"GSTools"
toolTip:"HW3_File_Exporter"
buttonText:"HW3_File_Exporter"

(
    -- We'll let the user define the export path via the UI
    global exportPath = ""
    
    -- Function to export objects as FBX
    fn exportPairedObjectsAsFBX sourceObj collisionObjs exportFileName =
    (
        -- Check if there are valid objects
        if sourceObj == undefined then
        (
            return #(false, "Source object is undefined!")
        )
        
        -- Create export directory if it doesn't exist
        local dirPath = getFilenamePath exportFileName
        if (doesFileExist dirPath) == false then
        (
            makeDir dirPath recursive:true
            if (doesFileExist dirPath) == false then
            (
                return #(false, "Failed to create directory: " + dirPath)
            )
        )
        
        -- Store original selection
        local savedSelection = getCurrentSelection()
        
        -- Select source object and collision objects for export
        local objectsToExport = #(sourceObj)
        if collisionObjs != undefined and collisionObjs.count > 0 then
        (
            join objectsToExport collisionObjs
        )
        
        try
        (
            -- Select the objects to export
            max select none
            select objectsToExport
            
            -- Load FBX exporter plugin
            pluginManager.loadClass FBXEXP
            
            -- Set FBX export parameters
            FBXExporterSetParam "SmoothingGroups" true
            FBXExporterSetParam "ASCII" false
            FBXExporterSetParam "Animation" false
            FBXExporterSetParam "Triangulate" false
            
            -- Export the file
            local result = exportFile exportFileName #noPrompt selectedOnly:true usage:FBXEXP
            
            -- Restore original selection
            select savedSelection
            
            if result then
                return #(true, "Successfully exported to: " + exportFileName, collisionObjs.count)
            else
                return #(false, "Failed to export to: " + exportFileName)
        )
        catch
        (
            -- Restore original selection on error
            select savedSelection
            
            return #(false, "Error exporting file: " + (getCurrentException()))
        )
    )
    
    -- Utility functions
    fn findSourceObjects =
    (
        local sourceLayers = #()
        local sourceObjects = #()
        
        -- First try to find source layers/containers by name
        for i = 0 to layerManager.count - 1 do
        (
            local layer = layerManager.getLayer i
            if layer != undefined and (matchPattern layer.name pattern:"*_Source") do
                append sourceLayers layer
        )
        
        -- If no source layers found, look for objects directly
        if sourceLayers.count == 0 then
        (
            -- Look for all objects with SM_ prefix, which match the source pattern
            for obj in objects where (matchPattern obj.name pattern:"SM_*") do
                append sourceObjects obj
        )
        else
        (
            -- Get objects from source layers
            for layer in sourceLayers do
            (
                local layerName = layer.name
                -- Get the layer's nodes
                local theNodes = #()
                layer.nodes &theNodes
                
                for obj in theNodes where (matchPattern obj.name pattern:"SM_*") do
                    append sourceObjects obj
            )
        )
        
        return sourceObjects
    )
    
    fn findCollisionObjects sourceName =
    (
        local collisionObjects = #()
        
        -- Extract base name (without SM_ prefix) for comparison
        local baseSourceName = sourceName
        if (matchPattern sourceName pattern:"??_*") then
            baseSourceName = substring sourceName 4 -1
        
        -- Look for matching collision objects with any UCX_ prefix
        for obj in objects do
        (
            local objName = obj.name
            
            -- Check if it starts with UCX_
            if (matchPattern objName pattern:"UCX_*") then
            (
                -- Remove UCX_ prefix
                local collBaseName = substring objName 5 -1
                
                -- Handle direct match first
                if collBaseName == sourceName then
                    append collisionObjects obj
                else
                (
                    -- Handle case where collision has a different prefix than source
                    -- For example: if source is SM_Object, collision might be UCX_WB_Object
                    local collStrippedName = collBaseName
                    if (matchPattern collBaseName pattern:"??_*") then
                        collStrippedName = substring collBaseName 4 -1
                    
                    if collStrippedName == baseSourceName then
                        append collisionObjects obj
                    else
                    (
                        -- Check for numbered variants - using sourceName directly
                        local basePattern = sourceName + "_"
                        if (matchPattern collBaseName pattern:(basePattern + "*")) then
                        (
                            -- Get the suffix after the base pattern
                            local suffixStart = basePattern.count + 1
                            if suffixStart <= collBaseName.count then
                            (
                                local suffix = substring collBaseName suffixStart -1
                                
                                -- Check if suffix contains ONLY digits and no underscores
                                local isValid = true
                                
                                -- Reject if it has underscores (like _Chunk_01)
                                if (findString suffix "_") != undefined then
                                    isValid = false
                                else
                                (
                                    -- Check if all characters are digits
                                    for i = 1 to suffix.count do
                                    (
                                        local char = substring suffix i 1
                                        if not (char >= "0" and char <= "9") then
                                        (
                                            isValid = false
                                            exit
                                        )
                                    )
                                )
                                
                                if isValid then
                                    append collisionObjects obj
                            )
                        )
                        else
                        (
                            -- Check for numbered variants - using baseSourceName for different prefixes
                            -- Example: source is SM_Object, collision is UCX_WB_Object_01
                            local basePattern = collStrippedName + "_"
                            local strippedBasePattern = baseSourceName + "_"
                            
                            if (matchPattern collStrippedName pattern:(strippedBasePattern + "*")) then
                            (
                                -- Get the suffix after the base pattern
                                local suffixStart = strippedBasePattern.count + 1
                                if suffixStart <= collStrippedName.count then
                                (
                                    local suffix = substring collStrippedName suffixStart -1
                                    
                                    -- Check if suffix contains ONLY digits and no underscores
                                    local isValid = true
                                    
                                    -- Reject if it has underscores (like _Chunk_01)
                                    if (findString suffix "_") != undefined then
                                        isValid = false
                                    else
                                    (
                                        -- Check if all characters are digits
                                        for i = 1 to suffix.count do
                                        (
                                            local char = substring suffix i 1
                                            if not (char >= "0" and char <= "9") then
                                            (
                                                isValid = false
                                                exit
                                            )
                                        )
                                    )
                                    
                                    if isValid then
                                        append collisionObjects obj
                                )
                            )
                        )
                    )
                )
            )
        )
        
        return collisionObjects
    )
    
    -- Create UI for the exporter
    rollout HW3_File_Exporter_Rollout "HW3 File Exporter" 
    (
        editText txt_exportPath "Export Path:" width:620 height:20 readonly:true
        button btn_browse "Browse..." width:60 height:20 align:#right offset:[3,-25]
        button btn_export "Export Source objects and Collisions" width:700 height:30
        
        -- Log display - make it bigger for the larger UI
        listBox lbx_log "Operation Logs:" height:25 width:700
        
        -- Custom function to add log messages with type indicators
        fn addLogEntry msg logType:"info" =
        (
            -- Add prefix based on log type
            local prefixedMsg = case logType of
            (
                "success": "[SUCCESS] " + msg
                "warning": "[WARNING] " + msg
                "error": "[ERROR] " + msg
                default: msg
            )
            
            -- Add item to listbox
            local idx = lbx_log.items.count + 1
            lbx_log.items = append lbx_log.items prefixedMsg
            
            -- Scroll to bottom
            lbx_log.selection = idx
        )
        
        on btn_browse pressed do
        (
            local path = getSavePath caption:"Select Export Directory" initialDir:(maxFilePath)
            if path != undefined then
            (
                exportPath = path + "\\"
                txt_exportPath.text = exportPath
                -- addLogEntry ("Export path set to: " + exportPath)
            )
        )
        
        on btn_export pressed do
        (
            -- Clear the log
            lbx_log.items = #()
            
            -- Check if an export path has been selected
            if exportPath == "" then
            (
                messageBox "Please select an export directory first!" title:"Warning" beep:true
                addLogEntry "No export path selected!" logType:"error"
                return false
            )
            
            -- Create the export directory if it doesn't exist
            if (doesFileExist exportPath) == false then
            (
                makeDir exportPath recursive:true
                if (doesFileExist exportPath) == false then
                (
                    messageBox ("Failed to create directory: " + exportPath) title:"Error" beep:true
                    addLogEntry ("Failed to create directory: " + exportPath) logType:"error"
                    return false
                )
            )
            
            -- Find source objects
            addLogEntry "Searching for source objects..."
            local sourceObjects = findSourceObjects()
            
            if sourceObjects.count == 0 then
            (
                messageBox "No source objects found (objects with 'SM_' prefix)!" title:"Warning" beep:true
                addLogEntry "No source objects found!" color:"red"
                return false
            )
            
            addLogEntry ("Found " + sourceObjects.count as string + " source objects")
            addLogEntry ("")
            
            -- Track export count
            local exportCount = 0
            local skippedCount = 0
            
            -- Process each source object
            for sourceObj in sourceObjects do
            (
                -- Get base name (without SM_ prefix)
                local baseName = sourceObj.name
                if (matchPattern baseName pattern:"SM_*") then
                    baseName = substring baseName 4 -1
                
                -- Find corresponding collision objects
                local collisionObjs = findCollisionObjects sourceObj.name
                
                -- Create export filename
                local exportFileName = exportPath + baseName + ".fbx"
                
                -- Log export attempt
                addLogEntry ("Processing: " + baseName)
                
                if collisionObjs.count > 0 then
                    addLogEntry ("  Found " + collisionObjs.count as string + " collision objects")
                else
                    addLogEntry ("  No collision objects found") logType:"warning"
                
                -- Export the objects
                local result = exportPairedObjectsAsFBX sourceObj collisionObjs exportFileName
                
                if result[1] then
                (
                    exportCount += 1
                    local successMsg = "  Exported: " + filenameFromPath exportFileName
                    if result[3] > 0 then
                        successMsg += " (with " + result[3] as string + " collision objects)"
                    else
                        successMsg += " (without collisions)"
                    
                    addLogEntry successMsg logType:"success"
                )
                else
                (
                    skippedCount += 1
                    addLogEntry ("  Failed: " + result[2]) logType:"error"
                )
            )
            
            -- Show completion message
            local message = "Export Complete!\n" + exportCount as string + " files exported to:\n" + exportPath
            if skippedCount > 0 then
                message += "\n" + skippedCount as string + " exports were skipped due to errors."
                
            messageBox message title:"HW3 File Exporter" beep:off
            addLogEntry ("")
            addLogEntry "--- Export operation completed ---"
            addLogEntry (exportCount as string + " files exported successfully") logType:"success"
            if skippedCount > 0 then
                addLogEntry (skippedCount as string + " files skipped") logType:"warning"
        )
    )
    
    -- Create the dialog
    createDialog HW3_File_Exporter_Rollout 720 480 style:#(#style_titlebar, #style_sysmenu, #style_toolwindow)
)