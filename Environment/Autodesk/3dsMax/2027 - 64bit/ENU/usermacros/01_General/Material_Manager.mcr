macroScript Material_Manager
Category:"GSTools"
toolTip:"Material Manager"
buttonText:"Material Manager"
(
	/*
		Material Manager for 3ds Max 2023+
		===================================
		Provides tools for managing Multi/Sub-Object materials:

		1. Reorder Material ID: Removes unused sub-materials and renumbers
		   remaining materials sequentially (1, 2, 3...) with optional face ID updates

		2. Update Skin Suffix (HW3): Removes old _SkinXX suffix and adds new
		   suffix based on Material ID minus 1

		Usage:
		1. Pick a Multi/Sub-Object material
		2. Use Cleanup or HW3 operations as needed
	*/

	try(destroyDialog MaterialManagerRoll) catch()

	rollout MaterialManagerRoll "Material Manager" width:360
	(
		-- Variables
		local selectedMaterial = undefined

		-- ===========================
		-- UI ELEMENTS
		-- ===========================

		group "Multi/Sub-Object Material"
		(
			materialButton btnMaterialPicker "Pick Material" width:330 height:32 toolTip:"Select a Multi/Sub-Object material to manage"
			label lblMatInfo "No material selected" align:#left style_sunkenedge:true width:330 height:18
		)

		group "Cleanup Operations"
		(
			button btnReorderMatID "Reorder Material ID" width:330 height:30 enabled:false toolTip:"Remove unused sub-materials and renumber sequentially"
			checkbox chkApplyToObjects "Apply to Assigned Objects" checked:true align:#left enabled:false offset:[10,5]
			label lblCleanupStatus "" align:#center style_sunkenedge:true width:330 height:18
		)

		group "HW3"
		(
			button btnUpdateSkinSuffix "Update Skin Suffix" width:330 height:30 enabled:false toolTip:"Remove old _SkinXX suffix and add new suffix based on Material ID"
			label lblHW3Status "" align:#center style_sunkenedge:true width:330 height:18
		)

		-- ===========================
		-- HELPER FUNCTIONS
		-- ===========================

		-- Find all objects in the scene using the specified material
		fn findObjectsUsingMaterial mat =
		(
			local objectsWithMaterial = #()

			for obj in objects do
			(
				if obj.material != undefined and obj.material == mat then
				(
					append objectsWithMaterial obj
				)
			)

			return objectsWithMaterial
		)

		-- Scan all faces in objects to find which material IDs are actually in use
		fn getUsedMaterialIDs objectList =
		(
			local usedIDs = #{}  -- Use bitArray for efficient set operations

			for obj in objectList do
			(
				-- Handle Editable Poly
				if classof obj.baseObject == Editable_Poly or classof obj.baseObject == PolyMeshObject then
				(
					-- Access base object directly to avoid counting faces from modifiers (e.g., Array)
					local faceCount = polyop.getNumFaces obj.baseObject

					for f = 1 to faceCount do
					(
						local faceMatID = polyop.getFaceMatID obj.baseObject f
						-- Guard: skip if getFaceMatID returned undefined or non-positive value
						if faceMatID != undefined and faceMatID > 0 then
							usedIDs[faceMatID] = true
					)
				)
				-- Handle Editable Mesh
				else if classof obj.baseObject == Editable_Mesh then
				(
					local faceCount = obj.baseObject.numfaces

					for f = 1 to faceCount do
					(
						local faceMatID = getFaceMatID obj.baseObject f
						-- Guard: skip if getFaceMatID returned undefined or non-positive value
						if faceMatID != undefined and faceMatID > 0 then
							usedIDs[faceMatID] = true
					)
				)
			)

			return usedIDs
		)

		-- Build mapping array of old ID -> new ID for sequential renumbering
		fn buildIDRemapping mat usedIDs =
		(
			local remapping = #()
			local newID = 1

			-- Iterate through sub-materials in order
			for i = 1 to mat.numsubs do
			(
				local oldID = mat.materialIDList[i]

				-- Guard: skip slots with undefined or invalid IDs (empty sub-material slots)
				if oldID == undefined or oldID == 0 then continue

				-- Check if this ID is actually used
				if usedIDs[oldID] then
				(
					local subMat = mat.materialList[i]
					local matName = if subMat != undefined then subMat.name else "Undefined"

					-- Store: #(oldID, newID, materialName, originalIndex)
					append remapping #(oldID, newID, matName, i)
					newID += 1
				)
			)

			return remapping
		)

		-- Update the material's sub-material list with only used materials
		fn updateMaterialList mat remapping =
		(
			local newMaterialList = #()
			local newIDList = #()

			for mapping in remapping do
			(
				local originalIndex = mapping[4]
				local newID = mapping[2]

				append newMaterialList mat.materialList[originalIndex]
				append newIDList newID
			)

			-- Update the Multi/Sub-Object material
			-- First copy materials to new positions
			for i = 1 to newMaterialList.count do
			(
				mat.materialList[i] = newMaterialList[i]
				mat.materialIDList[i] = newIDList[i]
			)

			-- Then reduce the count to remove unused slots at the end
			mat.materialList.count = newMaterialList.count
		)

		-- Get unique base objects (to handle instances correctly)
		fn getUniqueBaseObjects objectList =
		(
			local uniqueBaseObjects = #()
			local processedBaseObjects = #()

			for obj in objectList do
			(
				local baseObj = obj.baseObject
				local alreadyProcessed = false

				-- Check if this baseObject was already added
				for pObj in processedBaseObjects do
				(
					if pObj == baseObj then
					(
						alreadyProcessed = true
						exit
					)
				)

				-- If not processed, add it
				if not alreadyProcessed then
				(
					append uniqueBaseObjects obj
					append processedBaseObjects baseObj
				)
			)

			return uniqueBaseObjects
		)

		-- Update face material IDs on all objects to match new sequential numbering
		fn updateFaceMaterialIDs objectList remapping =
		(
			local totalFaces = 0
			local updatedFaces = 0

			-- Build lookup array: oldID -> newID
			local idMap = #()
			for i = 1 to 256 do idMap[i] = 0  -- Initialize lookup array

			for mapping in remapping do
			(
				local oldID = mapping[1]
				local newID = mapping[2]
				idMap[oldID] = newID
			)

			-- Get unique base objects to avoid processing instances multiple times
			local uniqueObjects = getUniqueBaseObjects objectList

			for obj in uniqueObjects do
			(
				-- Handle Editable Poly
				if classof obj.baseObject == Editable_Poly or classof obj.baseObject == PolyMeshObject then
				(
					-- Access base object directly to avoid counting faces from modifiers (e.g., Array)
					local faceCount = polyop.getNumFaces obj.baseObject
					totalFaces += faceCount

					for f = 1 to faceCount do
					(
						local currentID = polyop.getFaceMatID obj.baseObject f
						if currentID == undefined or currentID == 0 then continue

						local newID = idMap[currentID]

						if newID != 0 and newID != currentID then
						(
							polyop.setFaceMatID obj.baseObject f newID
							updatedFaces += 1
						)
					)
				)
				-- Handle Editable Mesh
				else if classof obj.baseObject == Editable_Mesh then
				(
					local faceCount = obj.baseObject.numfaces
					totalFaces += faceCount

					for f = 1 to faceCount do
					(
						local currentID = getFaceMatID obj.baseObject f
						if currentID == undefined or currentID == 0 then continue

						local newID = idMap[currentID]

						if newID != 0 and newID != currentID then
						(
							setFaceMatID obj.baseObject f newID
							updatedFaces += 1
						)
					)
				)
			)

			return #(totalFaces, updatedFaces)
		)

		-- Enable/disable all operation controls based on material selection
		fn enableControls enabled =
		(
			-- Cleanup controls
			btnReorderMatID.enabled = enabled
			chkApplyToObjects.enabled = enabled

			-- HW3 controls
			btnUpdateSkinSuffix.enabled = enabled
		)

		-- ===========================
		-- EVENT HANDLERS
		-- ===========================

		-- Material picker handler
		on btnMaterialPicker picked mat do
		(
			if mat != undefined then
			(
				-- Validate it's a Multi/Sub-Object material
				if classof mat == Multimaterial then
				(
					selectedMaterial = mat
					btnMaterialPicker.text = mat.name
					lblMatInfo.text = "Sub-materials: " + (mat.numsubs as string)

					-- Enable controls
					enableControls true
				)
				else
				(
					messageBox "Please select a Multi/Sub-Object material." title:"Invalid Material" beep:true
					btnMaterialPicker.material = undefined
					selectedMaterial = undefined
					lblMatInfo.text = "Material must be Multi/Sub-Object type"
					enableControls false
				)
			)
			else
			(
				selectedMaterial = undefined
				btnMaterialPicker.text = "Pick Material"
				lblMatInfo.text = "No material selected"
				enableControls false
			)
		)

		-- Reorder Material ID button handler
		on btnReorderMatID pressed do
		(
			if selectedMaterial == undefined then
			(
				messageBox "Please select a Multi/Sub-Object material first." title:"No Material" beep:true
				return undefined
			)

			-- Step 1: Find objects using this material
			lblCleanupStatus.text = "Finding objects..."
			windows.processPostedMessages()

			local objsWithMat = findObjectsUsingMaterial selectedMaterial

			if objsWithMat.count == 0 then
			(
				messageBox "No objects in the scene are using this material." title:"No Objects Found" beep:true
				lblCleanupStatus.text = ""
				return undefined
			)

			-- Step 2: Scan faces to find used IDs
			lblCleanupStatus.text = "Scanning faces..."
			windows.processPostedMessages()

			local usedIDs = getUsedMaterialIDs objsWithMat

			-- Step 3: Build remapping
			lblCleanupStatus.text = "Building ID mapping..."
			windows.processPostedMessages()

			local remapping = buildIDRemapping selectedMaterial usedIDs

			if remapping.count == 0 then
			(
				messageBox "No material IDs are currently assigned to faces." title:"No IDs Used" beep:true
				lblCleanupStatus.text = ""
				return undefined
			)

			-- Show confirmation dialog
			local confirmMsg = "Reorder Material ID Operation:\n\n"
			confirmMsg += "Objects using material: " + (objsWithMat.count as string) + "\n"
			confirmMsg += "Current sub-materials: " + (selectedMaterial.numsubs as string) + "\n"
			confirmMsg += "Sub-materials after cleanup: " + (remapping.count as string) + "\n\n"
			confirmMsg += "Mapping:\n"
			for m in remapping do
			(
				confirmMsg += "  " + m[3] + ": ID " + (m[1] as string) + " -> " + (m[2] as string) + "\n"
			)
			if chkApplyToObjects.checked then
				confirmMsg += "\nFace IDs on objects will be updated to match.\n"
			confirmMsg += "\nProceed with reordering?"

			if (queryBox confirmMsg title:"Confirm Reorder" beep:false) == false then
			(
				lblCleanupStatus.text = "Cancelled"
				return undefined
			)

			undo "Reorder Material ID" on
			(
				-- Step 4: Update material list
				lblCleanupStatus.text = "Updating material list..."
				windows.processPostedMessages()

				updateMaterialList selectedMaterial remapping

				-- Step 5: Update face IDs (if checkbox enabled)
				if chkApplyToObjects.checked then
				(
					lblCleanupStatus.text = "Updating face IDs..."
					windows.processPostedMessages()

					local result = updateFaceMaterialIDs objsWithMat remapping
					local totalFaces = result[1]
					local updatedFaces = result[2]

					lblCleanupStatus.text = "Complete! Updated " + (updatedFaces as string) + " of " + (totalFaces as string) + " faces."
				)
				else
				(
					lblCleanupStatus.text = "Complete! Material list updated."
				)
			)

			-- Update material info
			lblMatInfo.text = "Sub-materials: " + (selectedMaterial.numsubs as string)

			-- Refresh material editor
			matEditor.Open()
		)

		-- Update Skin Suffix button handler (HW3)
		on btnUpdateSkinSuffix pressed do
		(
			if selectedMaterial == undefined then
			(
				messageBox "Please select a Multi/Sub-Object material first." title:"No Material" beep:true
				return undefined
			)

			local count = 0

			undo "Update Skin Suffix" on
			(
				for i = 1 to selectedMaterial.numsubs do
				(
					local subMat = selectedMaterial.materialList[i]
					if subMat != undefined then
					(
						local matID = selectedMaterial.materialIDList[i]

						-- Guard: skip slots with undefined or invalid IDs
						if matID == undefined or matID == 0 then continue
						local oldName = subMat.name
						local baseName = oldName

						-- Remove any existing _SkinXX suffix (XX is 2 digits at the end)
						-- _SkinXX is 7 characters total: _ + Skin + XX (2 digits)
						if oldName.count >= 7 then
						(
							-- Check last 7 characters for _SkinXX pattern
							local last7 = substring oldName (oldName.count - 6) 7
							if (substring last7 1 5) == "_Skin" then
							(
								-- Check if characters 6 and 7 are digits
								local digit1 = substring last7 6 1
								local digit2 = substring last7 7 1
								local isDigit1 = findString "0123456789" digit1 != undefined
								local isDigit2 = findString "0123456789" digit2 != undefined

								if isDigit1 and isDigit2 then
								(
									-- Remove the _SkinXX suffix (7 characters)
									baseName = substring oldName 1 (oldName.count - 7)
								)
							)
						)

						-- Add new _SkinXX suffix where XX = (Material ID - 1) in 2 digits
						local skinNumber = matID - 1
						local skinSuffix = if skinNumber < 10 then ("0" + (skinNumber as string)) else (skinNumber as string)
						local newName = baseName + "_Skin" + skinSuffix

						if newName != oldName then
						(
							subMat.name = newName
							count += 1
						)
					)
				)
			)

			lblHW3Status.text = "Updated " + (count as string) + " sub-material(s) with Skin suffix"
			matEditor.Open()
		)

		-- Initialize rollout
		on MaterialManagerRoll open do
		(
			enableControls false
			lblCleanupStatus.text = ""
			lblHW3Status.text = ""
		)
	)

	-- Create persistent floater
	global MaterialManagerFloater
	if MaterialManagerFloater != undefined then
	(
		try(closeRolloutFloater MaterialManagerFloater) catch()
	)

	MaterialManagerFloater = newRolloutFloater "Material Manager" 380 300
	addRollout MaterialManagerRoll MaterialManagerFloater border:false
)
