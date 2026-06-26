macroScript Scene_Checker
category:"GSTools"
tooltip:"Scene Checker"
buttonText:"Scene Checker"
(
	-- UI Global variables
	global btn_width = 120
	global btn_height = 25
	global btn_margin = 10
	global list_width = 180
	global list_height = 22
	
	-- Data Global variables
	global arr_ngon_objects = #()
	global arr_openedge_objects = #()
	global arr_sg_objects = #()
	global arr_transform_objects = #()
	global arr_mesh_data = #()
	global arr_openedge_data = #()
	global arr_sg_data = #()
	global arr_transform_data = #()
	global arr_uv_objects = #()
	global arr_uv_data = #()
	global current_check_type = ""
	global position_threshold = 0.01
	global rotation_threshold = 0.1  -- degrees
	global scale_threshold = 0.01
	global last_selection = #()
	
	-- Structure definitions
	struct MeshAnalysisData (
		name,
		ngon_count,
		ngon_faces = #()
	)
	
	struct OpenEdgeAnalysisData (
		name,
		open_edges = #()
	)
	
	struct SGAnalysisData (
		name,
		faces_without_sg = #()
	)
	
	struct TransformAnalysisData (
		name,
		has_position_error = false,
		has_rotation_error = false,
		has_scale_error = false,
		has_pivot_error = false,
		position,
		rotation,
		scale,
		pivot_position
	)
	
	struct UVAnalysisData (
		name,
		uv_channel_count,
		uv_channels = #()
	)
	
	-- Helper functions
	fn findMeshData mesh_name =
	(
		for data in arr_mesh_data do
		(
			if data.name == mesh_name then
				return data
		)
		return undefined
	)
	
	fn findOpenEdgeData mesh_name =
	(
		for data in arr_openedge_data do
		(
			if data.name == mesh_name then
				return data
		)
		return undefined
	)
	
	fn findSGData mesh_name =
	(
		for data in arr_sg_data do
		(
			if data.name == mesh_name then
				return data
		)
		return undefined
	)
	
	fn findTransformData obj_name =
	(
		for data in arr_transform_data do
		(
			if data.name == obj_name then
				return data
		)
		return undefined
	)
	
	fn findUVData mesh_name =
	(
		for data in arr_uv_data do
		(
			if data.name == mesh_name then
				return data
		)
		return undefined
	)
	
	-- Validation function
	fn validateEditablePoly selection_array =
	(
		local non_editable_objects = #()
		for obj in selection_array do
		(
			local hasEditablePoly = false
			
			-- Check if base object is Editable Poly
			if classof obj.baseObject == Editable_Poly then
				hasEditablePoly = true
			
			-- Check modifier stack for Editable Poly
			if not hasEditablePoly then
			(
				for i = 1 to obj.modifiers.count do
				(
					if classof obj.modifiers[i] == Editable_Poly then
					(
						hasEditablePoly = true
						exit
					)
				)
			)
			
			if not hasEditablePoly then
				append non_editable_objects obj.name
		)
		
		if non_editable_objects.count > 0 then
		(
			messageBox "Selection must be Editable Poly" title:"Error" beep:true
			return false
		)
		
		return true
	)
	
	-- Open Edges checker function
	fn checkOpenEdges selectobj =
	(
		local open_edges = polyop.getOpenEdges selectobj
		
		local analysis_data = OpenEdgeAnalysisData()
		analysis_data.name = selectobj.name
		analysis_data.open_edges = open_edges
		
		for i = arr_openedge_data.count to 1 by -1 do
		(
			if arr_openedge_data[i].name == selectobj.name then
				deleteItem arr_openedge_data i
		)
		append arr_openedge_data analysis_data
		
		if open_edges.numberSet > 0 then
		(
			appendIfUnique arr_openedge_objects selectobj.name
		)
	)
	
	-- N-gon checker function
	fn checkNgons selectobj =
	(
		local ngon_faces = #()
		local numFaces = polyop.getNumFaces selectobj
		
		for faceIdx = 1 to numFaces do
		(
			local faceVerts = polyop.getFaceVerts selectobj faceIdx
			if faceVerts != undefined and faceVerts.count > 4 then
			(
				append ngon_faces faceIdx
			)
		)
		
		local analysis_data = MeshAnalysisData()
		analysis_data.name = selectobj.name
		analysis_data.ngon_count = ngon_faces.count
		analysis_data.ngon_faces = ngon_faces as bitArray
		
		for i = arr_mesh_data.count to 1 by -1 do
		(
			if arr_mesh_data[i].name == selectobj.name then
				deleteItem arr_mesh_data i
		)
		append arr_mesh_data analysis_data
		
		if ngon_faces.count > 0 then
		(
			appendIfUnique arr_ngon_objects selectobj.name
		)
	)
	
	-- Smoothing groups checker function
	fn checkSmoothingGroups selectobj =
	(
		local numFaces = polyop.getNumFaces selectobj
		local faces_without_sg = #()
		
		for i = 1 to numFaces do
		(
			try
			(
				local currentGroup = polyop.getFaceSmoothGroup selectobj i
				if currentGroup == 0 then
					append faces_without_sg i
			)
			catch
			(
				-- Skip face if error
			)
		)
		
		local sg_data = SGAnalysisData()
		sg_data.name = selectobj.name
		sg_data.faces_without_sg = faces_without_sg as bitArray
		
		for i = arr_sg_data.count to 1 by -1 do
		(
			if arr_sg_data[i].name == selectobj.name then
				deleteItem arr_sg_data i
		)
		append arr_sg_data sg_data
		
		if faces_without_sg.count > 0 then
		(
			appendIfUnique arr_sg_objects selectobj.name
		)
	)
	
	-- Transform checker function
	fn checkTransform selectobj =
	(
		local hasError = false
		local transform_data = TransformAnalysisData()
		transform_data.name = selectobj.name
		
		-- Check position
		local objPos = selectobj.pos
		transform_data.position = objPos
		local posXExceeds = (abs objPos.x) > position_threshold
		local posYExceeds = (abs objPos.y) > position_threshold
		local posZExceeds = (abs objPos.z) > position_threshold
		if posXExceeds or posYExceeds or posZExceeds then
		(
			transform_data.has_position_error = true
			hasError = true
		)
		
		-- Check rotation (convert to euler angles for easier threshold checking)
		local objRotation = selectobj.rotation
		transform_data.rotation = objRotation
		local eulerRot = objRotation as eulerAngles
		local rotXExceeds = (abs eulerRot.x) > rotation_threshold
		local rotYExceeds = (abs eulerRot.y) > rotation_threshold
		local rotZExceeds = (abs eulerRot.z) > rotation_threshold
		if rotXExceeds or rotYExceeds or rotZExceeds then
		(
			transform_data.has_rotation_error = true
			hasError = true
		)
		
		-- Check scale
		local objScale = selectobj.scale
		transform_data.scale = objScale
		local scaleXExceeds = (abs (objScale.x - 1.0)) > scale_threshold
		local scaleYExceeds = (abs (objScale.y - 1.0)) > scale_threshold
		local scaleZExceeds = (abs (objScale.z - 1.0)) > scale_threshold
		if scaleXExceeds or scaleYExceeds or scaleZExceeds then
		(
			transform_data.has_scale_error = true
			hasError = true
		)
		
		-- Check pivot
		local pivotPos = selectobj.pivot
		transform_data.pivot_position = pivotPos
		local pivotXExceeds = (abs pivotPos.x) > position_threshold
		local pivotYExceeds = (abs pivotPos.y) > position_threshold
		local pivotZExceeds = (abs pivotPos.z) > position_threshold
		if pivotXExceeds or pivotYExceeds or pivotZExceeds then
		(
			transform_data.has_pivot_error = true
			hasError = true
		)
		
		if hasError then
		(
			-- Remove existing data for this object
			for i = arr_transform_data.count to 1 by -1 do
			(
				if arr_transform_data[i].name == selectobj.name then
					deleteItem arr_transform_data i
			)
			append arr_transform_data transform_data
			
			appendIfUnique arr_transform_objects selectobj.name
		)
	)
	
	-- UV Channels checker function
	fn checkUVChannels selectobj =
	(
		-- Use snapshotAsMesh to query map channels without modifying the original object
		local temp_mesh = snapshotAsMesh selectobj
		local uv_channels = #()
		local numMaps = meshop.getNumMaps temp_mesh

		-- Check each map channel (1 to numMaps-1, channel 0 is vertex color)
		for i = 1 to (numMaps - 1) do
		(
			if (meshop.getMapSupport temp_mesh i) then
			(
				append uv_channels i
			)
		)
		
		local analysis_data = UVAnalysisData()
		analysis_data.name = selectobj.name
		analysis_data.uv_channel_count = uv_channels.count
		analysis_data.uv_channels = uv_channels
		
		-- Remove existing data for this object
		for i = arr_uv_data.count to 1 by -1 do
		(
			if arr_uv_data[i].name == selectobj.name then
				deleteItem arr_uv_data i
		)
		append arr_uv_data analysis_data

		-- Only add objects with more than 1 UV channel
		if uv_channels.count > 1 then
		(
			appendIfUnique arr_uv_objects selectobj.name
		)
	)
	
	-- Helper function to enter Edit Poly mode (polygon level)
	fn enterEditPolyMode obj =
	(
		-- First try to find Edit Poly modifier in the stack
		local editPolyMod = undefined
		for i = 1 to obj.modifiers.count do
		(
			if classof obj.modifiers[i] == Edit_Poly then
			(
				editPolyMod = obj.modifiers[i]
				exit
			)
		)
		
		if editPolyMod != undefined then
		(
			-- Found Edit Poly modifier, select it and enter polygon mode
			max modify mode
			modPanel.setCurrentObject editPolyMod
			subObjectLevel = 4  -- Polygon mode
			return true
		)
		else if classof obj.baseObject == Editable_Poly then
		(
			-- No Edit Poly modifier, but base object is Editable Poly
			max modify mode
			modPanel.setCurrentObject obj.baseObject
			subObjectLevel = 4  -- Polygon mode
			return true
		)
		
		return false
	)
	
	-- Helper function to enter Edit Poly edge mode
	fn enterEditPolyEdgeMode obj =
	(
		-- First try to find Edit Poly modifier in the stack
		local editPolyMod = undefined
		for i = 1 to obj.modifiers.count do
		(
			if classof obj.modifiers[i] == Edit_Poly then
			(
				editPolyMod = obj.modifiers[i]
				exit
			)
		)
		
		if editPolyMod != undefined then
		(
			-- Found Edit Poly modifier, select it and enter edge mode
			max modify mode
			modPanel.setCurrentObject editPolyMod
			subObjectLevel = 2  -- Edge mode
			return true
		)
		else if classof obj.baseObject == Editable_Poly then
		(
			-- No Edit Poly modifier, but base object is Editable Poly
			max modify mode
			modPanel.setCurrentObject obj.baseObject
			subObjectLevel = 2  -- Edge mode
			return true
		)
		
		return false
	)
	
	-- Universal Select Error function
	fn selectErrors =
	(
		case current_check_type of
		(
			"openedges":
			(
				-- TOPOLOGY section - select open edges
				for obj_name in arr_openedge_objects do
				(
					local obj = getNodeByName obj_name
					local data = findOpenEdgeData obj_name
					if obj != undefined and data != undefined and data.open_edges.numberSet > 0 then
					(
						select obj
						if enterEditPolyEdgeMode obj then
						(
							polyop.setEdgeSelection obj data.open_edges
							update obj
						)
					)
				)
				print ("Selected open edges in " + arr_openedge_objects.count as string + " objects")
			)
			"ngons":
			(
				-- TOPOLOGY section - select error polygons
				for obj_name in arr_ngon_objects do
				(
					local obj = getNodeByName obj_name
					local data = findMeshData obj_name
					if obj != undefined and data != undefined and data.ngon_faces.count > 0 then
					(
						select obj
						if enterEditPolyMode obj then
						(
							polyop.setFaceSelection obj data.ngon_faces
							update obj
						)
					)
				)
				print ("Selected N-gon faces in " + arr_ngon_objects.count as string + " objects")
			)
			"sg":
			(
				-- TOPOLOGY section - select error polygons
				for obj_name in arr_sg_objects do
				(
					local obj = getNodeByName obj_name
					local data = findSGData obj_name
					if obj != undefined and data != undefined and data.faces_without_sg.count > 0 then
					(
						select obj
						if enterEditPolyMode obj then
						(
							polyop.setFaceSelection obj data.faces_without_sg
							update obj
						)
					)
				)
				print ("Selected faces without smoothing groups in " + arr_sg_objects.count as string + " objects")
			)
			"transform":
			(
				-- OBJECT section - select error objects
				local objects_to_select = #()
				for obj_name in arr_transform_objects do
				(
					local obj = getNodeByName obj_name
					if obj != undefined then
						append objects_to_select obj
				)
				if objects_to_select.count > 0 then
					select objects_to_select
				print ("Selected " + objects_to_select.count as string + " objects with transform issues")
			)
		)
		
		return true
	)
	
	fn canReuseGroup obj faceIdx groupNum facesToProcess assignments angleThreshold =
	(
		local faceNormal = polyop.getFaceNormal obj faceIdx
		
		-- Check against all faces already assigned to this group
		for i = 1 to facesToProcess.count do
		(
			if assignments[i] == groupNum then
			(
				local otherFaceIdx = facesToProcess[i]
				local otherNormal = polyop.getFaceNormal obj otherFaceIdx
				
				local dotProduct = dot faceNormal otherNormal
				dotProduct = amax -1.0 (amin 1.0 dotProduct)
				local angleDiff = acos dotProduct
				
				if angleDiff > angleThreshold then
					return false
			)
		)
		
		return true
	)
	
	fn processSelectedFaces obj angleThreshold =
	(
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
			return 0
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
			return 0
		)
		
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
		
		return facesToProcess.count
	)
	
	-- Reset XForm function
	fn applyResetXForm obj =
	(
		try
		(
			resetXform obj
			return true
		)
		catch
		(
			return false
		)
	)
	
	-- Main rollout
	rollout scene_checker_roll "Scene Checker v1.2" width:320 height:370
	(
		-- Left side - Check buttons
		group "TOPOLOGY"
		(
			button btn_check_openedges "Check Open Edges" width:btn_width height:btn_height pos:[btn_margin,25]
			button btn_check_ngons "Check N-gons" width:btn_width height:btn_height pos:[btn_margin,55]
			button btn_check_sg "Check Smoothing" width:btn_width height:btn_height pos:[btn_margin,85]
			button btn_auto_flat_sg "Auto Flat SG" width:btn_width height:btn_height pos:[btn_margin,115]
		)

		group "UV"
		(
			button btn_check_uvchannels "Check UV Channels" width:btn_width height:btn_height pos:[btn_margin, 170]
		)
		
		group "OBJECT"
		(
			button btn_check_transform "Check Transform" width:btn_width height:btn_height pos:[btn_margin,225]
			button btn_reset_transform "Reset XForm" width:btn_width height:btn_height pos:[btn_margin,255]
			button btn_reset_pivot "Reset Pivot" width:btn_width height:btn_height pos:[btn_margin,285]
		)

        group "SELECT"
        (
            button btn_select_error "Select Error" width:btn_width height:btn_height pos:[btn_margin,340] enabled:false
        )
		
		-- Right side - Results list
		listBox lbx_results "" width:list_width height:list_height pos:[140,20]
		
		
		-- Update results display
		fn updateResultsList check_type =
		(
			current_check_type = check_type
			case check_type of
			(
				"openedges":
				(
					lbx_results.items = arr_openedge_objects
					btn_select_error.enabled = (arr_openedge_objects.count > 0)
				)
				"ngons": 
				(
					lbx_results.items = arr_ngon_objects
					btn_select_error.enabled = (arr_ngon_objects.count > 0)
				)
				"sg": 
				(
					lbx_results.items = arr_sg_objects
					btn_select_error.enabled = (arr_sg_objects.count > 0)
				)
				"transform": 
				(
					lbx_results.items = arr_transform_objects
					btn_select_error.enabled = (arr_transform_objects.count > 0)
				)
				"uv": 
				(
					-- Build custom display strings with UV channel counts
					local display_items = #()
					for obj_name in arr_uv_objects do
					(
						local uv_data = findUVData obj_name
						if uv_data != undefined then
						(
							local count = uv_data.uv_channel_count
							local count_str = if count < 10 then ("0" + count as string) else (count as string)
							local map_word = if count == 1 then "map" else "maps"
							append display_items (obj_name + " (" + count_str + " " + map_word + ")")
						)
						else
						(
							append display_items (obj_name + " (00 maps)")
						)
					)
					lbx_results.items = display_items
					btn_select_error.enabled = false  -- No error selection for UV info display
				)
			)
		)
		
		-- Button handlers
		on btn_check_openedges pressed do
		(
			-- Validate selection first
			if not (validateEditablePoly (selection as array)) then
				return false
			
			arr_openedge_objects = #()
			arr_openedge_data = #()
			last_selection = selection as array
			
			for obj in selection do
			(
				checkOpenEdges obj
			)
			
			updateResultsList "openedges"
		)
		
		on btn_check_ngons pressed do
		(
			-- Validate selection first
			if not (validateEditablePoly (selection as array)) then
				return false
			
			arr_ngon_objects = #()
			arr_mesh_data = #()
			last_selection = selection as array
			
			for obj in selection do
			(
				checkNgons obj
			)
			
			updateResultsList "ngons"
		)
		
		on btn_check_sg pressed do
		(
			-- Validate selection first
			if not (validateEditablePoly (selection as array)) then
				return false
			
			arr_sg_objects = #()
			arr_sg_data = #()
			last_selection = selection as array
			
			for obj in selection do
			(
				checkSmoothingGroups obj
			)
			
			updateResultsList "sg"
		)
		
		on btn_auto_flat_sg pressed do
		(
			if selection.count == 0 then
			(
				return false
			)
			
			if not (validateEditablePoly (selection as array)) then
				return false
			
			local processed_count = 0
			with undo "Auto Flat SG" on
			(
				for obj in selection do
				(
					local faces_processed = processSelectedFaces obj 5.0
					if faces_processed > 0 then
						processed_count += 1
				)
			)
			
			print ("Auto-assigned flat smoothing groups to " + processed_count as string + " objects")
		)
		
		on btn_check_uvchannels pressed do
		(
			if selection.count == 0 then
			(
				messageBox "Please select at least one object" title:"No Selection" beep:true
				return false
			)
			
			arr_uv_objects = #()
			arr_uv_data = #()
			last_selection = selection as array
			
			for obj in selection do
			(
				checkUVChannels obj
			)
			
			updateResultsList "uv"
		)
		
		on btn_check_transform pressed do
		(
			arr_transform_objects = #()
			arr_transform_data = #()
			last_selection = selection as array
			
			for obj in selection do
			(
				checkTransform obj
			)
			
			updateResultsList "transform"
		)
		
		on btn_reset_transform pressed do
		(
			-- Always work on current selection
			if selection.count == 0 then
			(
				return false
			)
			
			local reset_count = 0
			local objects_to_reset = selection as array
			
			with undo "Reset XForm" on
			(
				for obj in objects_to_reset do
				(
					if applyResetXForm obj then
						reset_count += 1
				)
			)
			
			print ("Applied Reset XForm to " + reset_count as string + " objects")
		)
		
		on btn_reset_pivot pressed do
		(
			-- Always work on current selection
			if selection.count == 0 then
			(
				return false
			)
			
			local reset_count = 0
			local objects_to_reset = selection as array
			
			with undo "Reset Pivot" on
			(
				for obj in objects_to_reset do
				(
					obj.pivot = [0,0,0]
					reset_count += 1
				)
			)
			
			print ("Reset pivot for " + reset_count as string + " objects")
		)
		
		-- Universal Select Error button
		on btn_select_error pressed do
		(
			selectErrors()
		)
		
		-- Handle double-click on results list
		on lbx_results doubleClicked sel do
		(
			if sel > 0 and sel <= lbx_results.items.count then
			(
				local item_text = lbx_results.items[sel]
				local obj_name = item_text
				
				-- For UV display format "ObjectName (1:map, 2:map)", extract just the object name
				if current_check_type == "uv" then
				(
					local paren_pos = findString item_text " ("
					if paren_pos != undefined then
						obj_name = substring item_text 1 (paren_pos - 1)
				)
				
				local obj = getNodeByName obj_name
				if obj != undefined then
				(
					select obj
				)
			)
		)
	)
	
	-- Main execution
	on execute do
	(
		try (destroyDialog scene_checker_roll) catch()
		createDialog scene_checker_roll
	)
)
