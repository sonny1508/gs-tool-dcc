macroScript Material_ID_Remapper
Category:"GSTools"
toolTip:"Material ID Remapper"
buttonText:"Material ID Remapper"
(
	/*
		Material ID Remapper for 3ds Max 2023
		======================================
		Fixes Material ID mismatches when importing FBX from Maya.
		
		Problem: Maya assigns materials by name, not ID. When importing to Max,
		IDs are assigned sequentially (1, 2, 3...) regardless of where they should
		sit in your master Multi/Sub-Object material.
		
		Solution: This tool remaps face Material IDs to match your master material
		based on sub-material NAME matching.
		
		Usage:
		1. Select the imported mesh
		2. Pick your master Multi/Sub-Object material
		3. Click "Remap Material IDs"
	*/

	try(destroyDialog MaterialIDRemapper) catch()

	rollout MaterialIDRemapper "Material ID Remapper" width:320
	(
		-- UI Elements
		group "1. Select Mesh"
		(
			label lblObjName "No mesh selected" align:#left
			label lblObjMat "Current Material: None" align:#left
			label lblSubMatCount "Sub-materials: --" align:#left
		)
		
		group "2. Pick Master Material"
		(
			materialButton btnMasterMat "Click to Pick Master Material" width:290 height:28 toolTip:"Pick your target Multi/Sub-Object material"
			label lblMasterInfo "Sub-materials: --" align:#left
		)
		
		group "3. Preview Mapping"
		(
			dotNetControl lvMapping "System.Windows.Forms.ListView" width:290 height:120
			label lblMatchCount "" align:#left
		)
		
		button btnRemap "Remap Material IDs" width:290 height:36 enabled:false toolTip:"Apply the ID remapping to selected mesh"
		checkbox chkAssignMaster "Assign master material to mesh after remap" checked:true
		
		progressBar pbProgress value:0 width:290 height:8 visible:false
		label lblStatus "" align:#center style_sunkenedge:true width:290 height:18
		
		-- Variables
		local masterMat = undefined
		local idMappings = #()  -- Array of #(oldID, newID, matName)
		
		-- Initialize ListView
		fn initListView =
		(
			lvMapping.View = (dotNetClass "System.Windows.Forms.View").Details
			lvMapping.FullRowSelect = true
			lvMapping.GridLines = true
			lvMapping.HeaderStyle = (dotNetClass "System.Windows.Forms.ColumnHeaderStyle").Nonclickable
			lvMapping.Columns.Add "Sub-Material" 140
			lvMapping.Columns.Add "Current ID" 70
			lvMapping.Columns.Add "New ID" 70
		)
		
		-- Build name-to-ID mapping from a Multi/Sub-Object material
		fn getMaterialNameToID mat =
		(
			local result = #()
			if classof mat == Multimaterial then
			(
				for i = 1 to mat.numsubs do
				(
					local subMat = mat.materialList[i]
					if subMat != undefined then
					(
						local matID = mat.materialIDList[i]
						local matName = subMat.name
						append result #(matName, matID)
					)
				)
			)
			result
		)
		
		-- Update the mapping preview
		fn updateMappingPreview =
		(
			lvMapping.Items.Clear()
			idMappings = #()
			
			if selection.count != 1 then return false
			local obj = selection[1]
			if obj.material == undefined then return false
			if masterMat == undefined then return false
			if classof masterMat != Multimaterial then return false
			
			-- Get master material name-to-ID mapping
			local masterNameToID = getMaterialNameToID masterMat
			
			-- Get mesh material and build remapping
			local meshMat = obj.material
			local matchCount = 0
			
			if classof meshMat == Multimaterial then
			(
				for i = 1 to meshMat.numsubs do
				(
					local subMat = meshMat.materialList[i]
					if subMat != undefined then
					(
						local currentID = meshMat.materialIDList[i]
						local matName = subMat.name
						local newID = undefined
						
						-- Find matching name in master
						for pair in masterNameToID where pair[1] == matName do
						(
							newID = pair[2]
							exit
						)
						
						if newID != undefined then
						(
							append idMappings #(currentID, newID, matName)
							
							-- Add to ListView
							local item = dotNetObject "System.Windows.Forms.ListViewItem" matName
							item.SubItems.Add (currentID as string)
							item.SubItems.Add (newID as string)
							
							-- Highlight if IDs differ
							if currentID != newID then
								item.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 255 255 200
							else
								item.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 200 255 200
							
							lvMapping.Items.Add item
							matchCount += 1
						)
					)
				)
			)
			else if meshMat != undefined then
			(
				-- Single material on mesh
				local matName = meshMat.name
				for pair in masterNameToID where pair[1] == matName do
				(
					append idMappings #(1, pair[2], matName)
					
					local item = dotNetObject "System.Windows.Forms.ListViewItem" matName
					item.SubItems.Add "1"
					item.SubItems.Add (pair[2] as string)
					
					if pair[2] != 1 then
						item.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 255 255 200
					else
						item.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 200 255 200
					
					lvMapping.Items.Add item
					matchCount += 1
					exit
				)
			)
			
			lblMatchCount.text = (matchCount as string) + " matching sub-material(s) found"
			
			-- Enable remap button if we have mappings
			btnRemap.enabled = (idMappings.count > 0)
			
			return (idMappings.count > 0)
		)
		
		-- Update selection info display
		fn updateSelectionInfo =
		(
			if selection.count == 1 and isValidNode selection[1] then
			(
				local obj = selection[1]
				lblObjName.text = "Mesh: " + obj.name
				
				if obj.material != undefined then
				(
					lblObjMat.text = "Current Material: " + obj.material.name
					
					if classof obj.material == Multimaterial then
						lblSubMatCount.text = "Sub-materials: " + (obj.material.numsubs as string)
					else
						lblSubMatCount.text = "Sub-materials: 1 (single material)"
				)
				else
				(
					lblObjMat.text = "Current Material: None"
					lblSubMatCount.text = "Sub-materials: --"
				)
			)
			else
			(
				lblObjName.text = "No mesh selected (select one object)"
				lblObjMat.text = "Current Material: None"
				lblSubMatCount.text = "Sub-materials: --"
			)
			
			updateMappingPreview()
		)
		
		-- Master material picker handler
		on btnMasterMat picked mat do
		(
			masterMat = mat
			
			if mat != undefined then
			(
				btnMasterMat.text = mat.name
				
				if classof mat == Multimaterial then
					lblMasterInfo.text = "Sub-materials: " + (mat.numsubs as string)
				else
					lblMasterInfo.text = "Warning: Not a Multi/Sub-Object material!"
			)
			else
			(
				btnMasterMat.text = "Click to Pick Master Material"
				lblMasterInfo.text = "Sub-materials: --"
			)
			
			updateMappingPreview()
		)
		
		-- Main remap function
		on btnRemap pressed do
		(
			if selection.count != 1 then
			(
				messageBox "Please select exactly one mesh object." title:"Selection Error"
				return undefined
			)
			
			local obj = selection[1]
			
			if idMappings.count == 0 then
			(
				messageBox "No matching materials found to remap." title:"No Mappings"
				return undefined
			)
			
			-- Confirm action
			local confirmMsg = "This will remap " + (idMappings.count as string) + " Material ID(s) on \"" + obj.name + "\".\n\n"
			for m in idMappings do
				confirmMsg += m[3] + ": ID " + (m[1] as string) + " -> ID " + (m[2] as string) + "\n"
			confirmMsg += "\nProceed?"
			
			if (queryBox confirmMsg title:"Confirm Remap" beep:false) == false then
				return undefined
			
			pbProgress.visible = true
			pbProgress.value = 0
			lblStatus.text = "Remapping..."
			
			local success = false
			local faceCount = 0
			local remappedFaces = 0
			
			undo "Remap Material IDs" on
			(
				-- Handle Editable Poly
				if classof obj.baseObject == Editable_Poly or (classof obj.baseObject == PolyMeshObject) then
				(
					faceCount = polyop.getNumFaces obj
					
					for f = 1 to faceCount do
					(
						local currentFaceID = polyop.getFaceMatID obj f
						
						-- Find if this ID needs remapping
						for mapping in idMappings where mapping[1] == currentFaceID do
						(
							polyop.setFaceMatID obj f mapping[2]
							remappedFaces += 1
							exit
						)
						
						-- Update progress every 1000 faces
						if mod f 1000 == 0 then
						(
							pbProgress.value = (f as float / faceCount * 100)
							windows.processPostedMessages()
						)
					)
					
					success = true
				)
				-- Handle Editable Mesh
				else if classof obj.baseObject == Editable_Mesh then
				(
					faceCount = obj.numfaces
					
					for f = 1 to faceCount do
					(
						local currentFaceID = getFaceMatID obj f
						
						for mapping in idMappings where mapping[1] == currentFaceID do
						(
							setFaceMatID obj f mapping[2]
							remappedFaces += 1
							exit
						)
						
						if mod f 1000 == 0 then
						(
							pbProgress.value = (f as float / faceCount * 100)
							windows.processPostedMessages()
						)
					)
					
					success = true
				)
				-- Try to convert or work with modifier stack
				else
				(
					-- Check if there's an Edit Poly modifier
					local editPolyMod = undefined
					for m in obj.modifiers where classof m == Edit_Poly do
					(
						editPolyMod = m
						exit
					)
					
					if editPolyMod != undefined then
					(
						messageBox "Object has Edit Poly modifier. Please collapse the stack first,\nor convert to Editable Poly." title:"Cannot Process"
					)
					else
					(
						local convertChoice = queryBox "Object is not Editable Poly or Editable Mesh.\n\nConvert to Editable Poly to proceed?" title:"Convert Object?"
						
						if convertChoice then
						(
							convertToPoly obj
							
							faceCount = polyop.getNumFaces obj
							
							for f = 1 to faceCount do
							(
								local currentFaceID = polyop.getFaceMatID obj f
								
								for mapping in idMappings where mapping[1] == currentFaceID do
								(
									polyop.setFaceMatID obj f mapping[2]
									remappedFaces += 1
									exit
								)
								
								if mod f 1000 == 0 then
								(
									pbProgress.value = (f as float / faceCount * 100)
									windows.processPostedMessages()
								)
							)
							
							success = true
						)
					)
				)
				
				-- Assign master material if checkbox is checked
				if success and chkAssignMaster.checked then
					obj.material = masterMat
			)
			
			pbProgress.value = 100
			
			if success then
			(
				lblStatus.text = "Done! Remapped " + (remappedFaces as string) + " faces."
				
				local resultMsg = "Material ID Remap Complete!\n\n"
				resultMsg += "Faces processed: " + (faceCount as string) + "\n"
				resultMsg += "Faces remapped: " + (remappedFaces as string) + "\n"
				if chkAssignMaster.checked then
					resultMsg += "\nMaster material assigned to mesh."
				
				messageBox resultMsg title:"Success"
				
				-- Refresh the preview
				updateMappingPreview()
			)
			else
			(
				lblStatus.text = "Remap cancelled or failed."
			)
			
			pbProgress.visible = false
		)
		
		-- Initialize and set up selection change callback
		on MaterialIDRemapper open do
		(
			initListView()
			updateSelectionInfo()
			
			-- Register callback for selection changes
			callbacks.removeScripts id:#MatIDRemapperCallback
			callbacks.addScript #selectionSetChanged "try(MaterialIDRemapper.updateSelectionInfo())catch()" id:#MatIDRemapperCallback
		)
		
		on MaterialIDRemapper close do
		(
			callbacks.removeScripts id:#MatIDRemapperCallback
		)
	)

	createDialog MaterialIDRemapper style:#(#style_toolwindow, #style_sysmenu)
)
