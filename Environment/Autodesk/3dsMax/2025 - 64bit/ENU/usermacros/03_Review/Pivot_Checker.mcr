macroScript Pivot_Checker
category:"GSTools"
tooltip:"Pivot Checker"
buttonText:"Pivot Checker"
(
    -- Global variables
    global pivotData = #()
    global objectNames = #()
    global threshold = 0.01
    
    -- Create UI rollout with global scope to ensure proper cleanup
    global pivotReportRollout
    rollout pivotReportRollout "Pivot Checker" width:440 height:320 (
        label titleLbl "Objects with Pivot Points > threshold units from origin:" align:#left
        listbox pivotList "" items:#() height:18 width:420
        button checkBtn "Check Selection" width:120 height:25 align:#center
        
        on pivotList selected index do (
            -- Select the corresponding object in the scene when list item is clicked
            if index > 0 and index <= objectNames.count then (
                local objName = objectNames[index]
                local sceneObj = getNodeByName objName
                if sceneObj != undefined then (
                    select sceneObj
                    -- Optional: frame the selected object in viewport
                    -- max views redraw
                )
            )
        )
        
        on checkBtn pressed do (
            -- Collect pivot data
            pivotData = #()
            objectNames = #()
            
            -- Check if anything is selected
            if selection.count == 0 then (
                messagebox "Please select some objects first!" title:"No Selection"
            ) else (
                for obj in selection do (
                    -- Get the actual pivot point position in world space
                    -- This accounts for any pivot adjustments made to the object
                    local pivotPos = obj.pivot
                    
                    -- Check each axis individually against threshold using absolute values
                    local xExceeds = (abs pivotPos.x) > threshold
                    local yExceeds = (abs pivotPos.y) > threshold
                    local zExceeds = (abs pivotPos.z) > threshold
                    
                    if xExceeds or yExceeds or zExceeds then (
                        -- Format numbers to avoid floating point display issues
                        local xStr = formattedPrint pivotPos.x format:".4f"
                        local yStr = formattedPrint pivotPos.y format:".4f"
                        local zStr = formattedPrint pivotPos.z format:".4f"
                        local pivotStr = "[" + xStr + ", " + yStr + ", " + zStr + "]"
                        append pivotData (obj.name + ": " + pivotStr)
                        append objectNames obj.name  -- Store the object name for selection lookup
                    )
                )
                
                -- Update the listbox with results
                if pivotData.count > 0 then (
                    pivotList.items = pivotData
                ) else (
                    local thresholdStr = formattedPrint threshold format:".4f"
                    messagebox ("All selected object pivots are within " + thresholdStr + " units of [0,0,0]") title:"Pivot Check Complete"
                )
            )
        )
        
        on pivotReportRollout open do (
            -- Set the dynamic title text after the dialog opens
            titleLbl.text = "Objects with Pivot Points > " + (formattedPrint threshold format:".4f") + " units from origin:"
        )
        
        on pivotReportRollout close do (
            -- Clean up when dialog is closed
            pivotReportRollout = undefined
        )
    )
    
    -- Show the dialog
    try (destroyDialog pivotReportRollout) catch()
    createDialog pivotReportRollout
)