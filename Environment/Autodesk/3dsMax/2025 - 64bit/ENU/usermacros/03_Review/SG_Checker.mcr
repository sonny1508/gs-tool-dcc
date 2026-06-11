macroScript SG_Checker
category:"GSTools"
tooltip:"Smoothing Groups Checker"
buttonText:"Smoothing Groups Checker"
(
    rollout flatSGRollout "Smoothing Groups Checker" width:280 height:220
    (
        group "Selection Tools"
        (
            button btnSelectFaces "Select Faces Without SG" width:250 height:35 tooltip:"Select all faces that don't have smoothing groups"
        )
        
        group "Processing Tools"
        (
            spinner spnAngleThreshold "Angle Threshold:" range:[0.1, 45.0, 5.0] type:#float fieldwidth:60 align:#left
            label lblAngleUnit "degrees" align:#left offset:[180, -20]
            button btnProcessFaces "Assign Smoothing Groups" width:250 height:35 tooltip:"Assign smoothing groups to selected faces"
        )
        
        group "Information"
        (
            label lblInfo "Select objects first, then use the tools above." align:#left
            label lblStatus "" align:#left
        )
        
        -- Helper functions
        fn isValidPolyObject obj =
        (
            if classOf obj == Editable_Poly then
                return true
            
            -- Check for Edit Poly modifier
            for i = 1 to obj.modifiers.count do
            (
                if classOf obj.modifiers[i] == Edit_Poly then
                    return true
            )
            
            return false
        )
        
        fn getFacesByVertex obj faceIdx =
        (
            local adjacentFaces = #()
            
            try
            (
                local faceVerts = polyop.getFaceVerts obj faceIdx
                for vertIdx in faceVerts do
                (
                    local facesAtVert = polyop.getFacesUsingVert obj vertIdx
                    for adjFaceIdx in facesAtVert do
                    (
                        if adjFaceIdx != faceIdx and (findItem adjacentFaces adjFaceIdx) == 0 then
                            append adjacentFaces adjFaceIdx
                    )
                )
            )
            catch
            (
                -- Return empty array if error
            )
            
            return adjacentFaces
        )
        
        fn computeFaceNormal obj faceIdx =
        (
            try
            (
                local faceVerts = polyop.getFaceVerts obj faceIdx
                if faceVerts.count >= 3 then
                (
                    local p1 = polyop.getVert obj faceVerts[1]
                    local p2 = polyop.getVert obj faceVerts[2]
                    local p3 = polyop.getVert obj faceVerts[3]
                    
                    local v1 = p2 - p1
                    local v2 = p3 - p1
                    local normal = normalize (cross v1 v2)
                    
                    return normal
                )
            )
            catch
            (
                -- Return default normal if error
            )
            
            return [0,0,1]
        )
        
        fn canUseSameGroup obj face1 face2 angleThreshold =
        (
            local normal1 = computeFaceNormal obj face1
            local normal2 = computeFaceNormal obj face2
            
            local dotProd = dot normal1 normal2
            dotProd = if dotProd > 1.0 then 1.0 else (if dotProd < -1.0 then -1.0 else dotProd)
            
            local angleDeg = radToDeg(acos(dotProd))
            
            return angleDeg <= angleThreshold
        )
        
        fn canReuseGroup obj faceIdx groupNum processedFaces assignments angleThreshold =
        (
            local adjacentFaces = getFacesByVertex obj faceIdx
            
            for adjFace in adjacentFaces do
            (
                local adjIndex = findItem processedFaces adjFace
                if adjIndex > 0 then
                (
                    -- Check processed face
                    if assignments[adjIndex] == groupNum then
                    (
                        if not (canUseSameGroup obj faceIdx adjFace angleThreshold) then
                            return false
                    )
                )
                else
                (
                    -- Check existing face
                    try
                    (
                        local existingGroup = polyop.getFaceSmoothGroup obj adjFace
                        if existingGroup > 0 then
                        (
                            -- Check if this group is used
                            local tempGroup = existingGroup
                            local bitPos = 1
                            while tempGroup > 0 do
                            (
                                if (bit.and tempGroup 1) != 0 and bitPos == groupNum then
                                (
                                    if not (canUseSameGroup obj faceIdx adjFace angleThreshold) then
                                        return false
                                )
                                tempGroup = bit.shift tempGroup -1
                                bitPos += 1
                            )
                        )
                    )
                    catch
                    (
                        -- Skip if error reading existing group
                    )
                )
            )
            
            return true
        )
        
        fn selectFacesWithoutSG =
        (
            if selection.count == 0 then
            (
                lblStatus.text = "Error: No objects selected!"
                return false
            )
            
            local totalSelectedFaces = 0
            local processedObjects = 0
            
            with undo "Select Faces Without SG" on
            (
                for obj in selection do
                (
                    if isValidPolyObject obj then
                    (
                        local numFaces = 0
                        try
                        (
                            numFaces = polyop.getNumFaces obj
                        )
                        catch
                        (
                            format "Error: Cannot access face data for %\n" obj.name
                            continue
                        )
                        
                        local facesWithoutSG = #{}
                        
                        -- Find faces without smoothing groups
                        for i = 1 to numFaces do
                        (
                            try
                            (
                                local currentGroup = polyop.getFaceSmoothGroup obj i
                                if currentGroup == 0 then
                                    facesWithoutSG[i] = true
                            )
                            catch
                            (
                                -- Skip face if error reading smoothing group
                            )
                        )
                        
                        if facesWithoutSG.count > 0 then
                        (
                            polyop.setFaceSelection obj facesWithoutSG
                            totalSelectedFaces += facesWithoutSG.count
                            processedObjects += 1
                            
                            -- Switch to face sub-object mode if not already
                            if (modPanel.getCurrentObject() == obj) and (subObjectLevel != 4) then
                                subObjectLevel = 4
                        )
                    )
                    else
                    (
                        format "Skipping %: Not a valid poly object\n" obj.name
                    )
                )
            )
            
            lblStatus.text = ("Selected " + totalSelectedFaces as string + " faces in " + processedObjects as string + " objects")
            format "Selected % faces without smoothing groups in % objects\n" totalSelectedFaces processedObjects
            
            return totalSelectedFaces > 0
        )
        
        fn processSelectedFaces angleThreshold =
        (
            if selection.count == 0 then
            (
                lblStatus.text = "Error: No objects selected!"
                return false
            )
            
            local processedObjects = 0
            local totalFaces = 0
            
            with undo "Process Smoothing Groups" on
            (
                for obj in selection do
                (
                    if isValidPolyObject obj then
                    (
                        format "\nProcessing: %\n" obj.name
                        
                        local numFaces = 0
                        local faceSelection = undefined
                        
                        try
                        (
                            numFaces = polyop.getNumFaces obj
                            faceSelection = polyop.getFaceSelection obj
                        )
                        catch
                        (
                            format "Error: Cannot access face data for %\n" obj.name
                            continue
                        )
                        
                        local selectedFaces = #()
                        
                        -- Get selected faces or all faces if none selected
                        for i = 1 to numFaces do
                        (
                            if faceSelection[i] then
                                append selectedFaces i
                        )
                        
                        if selectedFaces.count == 0 then
                        (
                            format "No faces selected, processing all % faces\n" numFaces
                            for i = 1 to numFaces do
                                append selectedFaces i
                        )
                        
                        -- Find faces without smoothing groups from selection
                        local facesToProcess = #()
                        for faceIdx in selectedFaces do
                        (
                            try
                            (
                                local currentGroup = polyop.getFaceSmoothGroup obj faceIdx
                                if currentGroup == 0 then
                                    append facesToProcess faceIdx
                            )
                            catch
                            (
                                -- Skip face if error reading smoothing group
                            )
                        )
                        
                        if facesToProcess.count == 0 then
                        (
                            format "All selected faces already have smoothing groups\n"
                            continue
                        )
                        
                        format "Processing % faces (angle threshold: %°)\n" facesToProcess.count angleThreshold
                        
                        -- Find highest existing smoothing group
                        local maxExistingGroup = 0
                        for i = 1 to numFaces do
                        (
                            try
                            (
                                local sg = polyop.getFaceSmoothGroup obj i
                                if sg > 0 then
                                (
                                    local tempSG = sg
                                    local bitPos = 1
                                    while tempSG > 0 do
                                    (
                                        if (bit.and tempSG 1) != 0 then
                                            maxExistingGroup = bitPos
                                        tempSG = bit.shift tempSG -1
                                        bitPos += 1
                                    )
                                )
                            )
                            catch
                            (
                                -- Skip if error
                            )
                        )
                        
                        local maxUsedGroup = if maxExistingGroup > 0 then maxExistingGroup else 0
                        local assignments = #()
                        for i = 1 to facesToProcess.count do
                            assignments[i] = 0
                        
                        -- Process each face
                        for i = 1 to facesToProcess.count do
                        (
                            local faceIdx = facesToProcess[i]
                            local assignedGroup = 0
                            
                            -- Try to reuse existing groups starting from 1
                            for groupNum = 1 to maxUsedGroup do
                            (
                                if canReuseGroup obj faceIdx groupNum facesToProcess assignments angleThreshold then
                                (
                                    assignedGroup = groupNum
                                    exit
                                )
                            )
                            
                            -- Create new group if needed
                            if assignedGroup == 0 then
                            (
                                assignedGroup = maxUsedGroup + 1
                                maxUsedGroup = assignedGroup
                            )
                            
                            assignments[i] = assignedGroup
                            
                            -- Apply smoothing group
                            try
                            (
                                local groupBitfield = bit.shift 1 (assignedGroup - 1)
                                polyop.setFaceSmoothGroup obj #{faceIdx} groupBitfield
                            )
                            catch
                            (
                                format "Warning: Failed to assign group % to face %\n" assignedGroup faceIdx
                            )
                        )
                        
                        -- Report results
                        if assignments.count > 0 then
                        (
                            local minGroup = amin assignments
                            local maxGroup = amax assignments
                            local totalGroups = maxGroup - minGroup + 1
                            format "Complete! Used % smoothing groups (% to %)\n" totalGroups minGroup maxGroup
                            
                            processedObjects += 1
                            totalFaces += facesToProcess.count
                            update obj
                        )
                    )
                    else
                    (
                        format "Skipping %: Not a valid poly object\n" obj.name
                    )
                )
            )
            
            lblStatus.text = ("Processed " + totalFaces as string + " faces in " + processedObjects as string + " objects")
            format "\n=== SUMMARY ===\n"
            format "Processed % objects, % total faces\n" processedObjects totalFaces
            
            return totalFaces > 0
        )
        
        -- Button event handlers
        on btnSelectFaces pressed do
        (
            selectFacesWithoutSG()
        )
        
        on btnProcessFaces pressed do
        (
            processSelectedFaces spnAngleThreshold.value
        )
        
        -- Update info when rollout opens
        on flatSGRollout open do
        (
            lblStatus.text = "Ready - Select objects and use tools above"
        )
    )
    
    -- Main execution - show the dialog
    on execute do
    (
        createDialog flatSGRollout
    )
)