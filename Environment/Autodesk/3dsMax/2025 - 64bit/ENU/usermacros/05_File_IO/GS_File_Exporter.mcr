macroScript GS_File_Exporter
Category:"GSTools"
toolTip:"GS File Exporter"
buttonText:"GS File Exporter"

(
    global exportPath = ""
    
    fn exportObjectAsFBX obj exportFileName =
    (
        local dirPath = getFilenamePath exportFileName
        if (doesFileExist dirPath) == false then
        (
            makeDir dirPath recursive:true
            if (doesFileExist dirPath) == false then
            (
                return #(false, "Failed to create directory: " + dirPath)
            )
        )
        
        local savedSelection = getCurrentSelection()
        
        try
        (
            max select none
            select obj
            
            pluginManager.loadClass FBXEXP
            
            FBXExporterSetParam "SmoothingGroups" true
            FBXExporterSetParam "ASCII" false
            FBXExporterSetParam "Animation" false
            FBXExporterSetParam "Triangulate" false
            
            local result = exportFile exportFileName #noPrompt selectedOnly:true usage:FBXEXP
            
            select savedSelection
            
            if result then
                return #(true, "Successfully exported to: " + exportFileName)
            else
                return #(false, "Failed to export to: " + exportFileName)
        )
        catch
        (
            select savedSelection
            return #(false, "Error exporting file: " + (getCurrentException()))
        )
    )
    
    if (fileExporterFloater != undefined) do
        return false
    
    rollout file_Exporter_Main "GS File Exporter"
    (
        editText txt_exportPath "Export Path:" width:440 height:20
        button btn_browse "Browse..." width:60 height:20 align:#right offset:[3,-25]
        
        label lbl_mode "Export Mode:" align:#left
        radioButtons rad_mode "" labels:#("All", "Selection") default:2 columns:2 align:#left offset:[70,-20]
        
        button btn_export "Export Objects" width:510 height:30
        
        listBox lbx_log "Operation Logs:" height:18 width:505
        
        fn addLogEntry msg logType:"info" =
        (
            local prefixedMsg = case logType of
            (
                "success": "[SUCCESS] " + msg
                "warning": "[WARNING] " + msg
                "error": "[ERROR] " + msg
                default: msg
            )
            
            local idx = lbx_log.items.count + 1
            lbx_log.items = append lbx_log.items prefixedMsg
            lbx_log.selection = idx
        )
        
        on txt_exportPath changed text do
        (
            exportPath = text
            
            if exportPath != "" then
            (
                local lastChar = ""
                if exportPath.count > 0 do
                    lastChar = substring exportPath exportPath.count 1
                
                if lastChar != "\\" do
                    exportPath = exportPath + "\\"
            )
        )
        
        on btn_browse pressed do
        (
            local path = getSavePath caption:"Select Export Directory" initialDir:(maxFilePath)
            if path != undefined then
            (
                exportPath = path + "\\"
                txt_exportPath.text = exportPath
            )
        )
        
        on btn_export pressed do
        (
            lbx_log.items = #()
            
            if exportPath == "" then
            (
                messageBox "Please select an export directory first!" title:"Warning" beep:true
                addLogEntry "No export path selected!" logType:"error"
                return false
            )
            
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
            
            local objectsToExport = #()
            
            if rad_mode.state == 1 then
            (
                addLogEntry "Exporting all objects in scene..."
                objectsToExport = objects as array
            )
            else
            (
                addLogEntry "Exporting selected objects..."
                objectsToExport = getCurrentSelection() as array
            )
            
            if objectsToExport.count == 0 then
            (
                messageBox "No objects to export!" title:"Warning" beep:true
                addLogEntry "No objects to export!" logType:"error"
                return false
            )
            
            addLogEntry ("Found " + objectsToExport.count as string + " objects to export")
            addLogEntry ""
            
            local exportCount = 0
            local skippedCount = 0
            
            for obj in objectsToExport do
            (
                if obj != undefined and classOf obj.name == String then
                (
                    local exportFileName = exportPath + obj.name + ".fbx"
                    
                    addLogEntry ("Processing: " + obj.name)
                    
                    local result = exportObjectAsFBX obj exportFileName
                    
                    if result[1] then
                    (
                        exportCount += 1
                        addLogEntry ("  Exported: " + filenameFromPath exportFileName) logType:"success"
                    )
                    else
                    (
                        skippedCount += 1
                        addLogEntry ("  Failed: " + result[2]) logType:"error"
                    )
                )
                else
                (
                    skippedCount += 1
                    addLogEntry ("  Skipped invalid object") logType:"warning"
                )
            )
            
            local message = "Export Complete!\n" + exportCount as string + " files exported to:\n" + exportPath
            if skippedCount > 0 then
                message += "\n" + skippedCount as string + " exports were skipped due to errors."
                
            messageBox message title:"GS File Exporter" beep:off
            addLogEntry ""
            addLogEntry "--- Export operation completed ---"
            addLogEntry (exportCount as string + " files exported successfully") logType:"success"
            if skippedCount > 0 then
                addLogEntry (skippedCount as string + " files skipped") logType:"warning"
        )
    )
    
    global fileExporterFloater
    try (
        fileExporterFloater = newRolloutFloater "GS File Exporter" 540 380
        if fileExporterFloater != undefined then
            addRollout File_Exporter_Main fileExporterFloater
        else
            messageBox "Failed to create the rollout floater!" title:"Error"
    ) catch (
        messageBox ("Error creating floater: " + (getCurrentException())) title:"Error"
    )
)