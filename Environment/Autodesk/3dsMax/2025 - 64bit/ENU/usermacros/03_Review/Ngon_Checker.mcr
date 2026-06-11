macroScript Ngon_Checker
category:"GSTools"
tooltip:"N-Gon Checker"
buttonText:"N-Gon Checker"
(
	-- Global variables
	global arr_failed_items=#()
	global arr_succeeded_items=#()
	global arr_mesh_data = #() -- Store all analysis data as array of structs
	
	-- Structure to hold mesh analysis data
	struct MeshAnalysisData (
		name,
		ngon_count,
		ngon_faces = #()
	)
	
	-- Function to find mesh data by name
	fn findMeshData mesh_name =
	(
		for data in arr_mesh_data do
		(
			if data.name == mesh_name then
				return data
		)
		return undefined
	)
	
	fn NGONFinder selectobj =
	(
		max modify mode
		local int_subobject_level = subObjectLevel
		local NGonCounter = 0
		local ngon_faces = #()
		
		-- Switch to face mode to find ngons
		subObjectLevel = 4
		
		-- Find N-gons manually for better control
		local numFaces = polyop.getNumFaces selectobj
		for faceIdx = 1 to numFaces do
		(
			local faceVerts = polyop.getFaceVerts selectobj faceIdx
			if faceVerts != undefined and faceVerts.count > 4 then
			(
				append ngon_faces faceIdx
			)
		)
		
		NGonCounter = ngon_faces.count
		
		-- Create analysis data structure
		local analysis_data = MeshAnalysisData()
		analysis_data.name = selectobj.name
		analysis_data.ngon_count = NGonCounter
		analysis_data.ngon_faces = ngon_faces as bitArray
		
		-- Store in array (remove any existing data for this mesh first)
		for i = arr_mesh_data.count to 1 by -1 do
		(
			if arr_mesh_data[i].name == selectobj.name then
				deleteItem arr_mesh_data i
		)
		append arr_mesh_data analysis_data
		
		-- Restore original sub-object level
		subObjectLevel = int_subobject_level
		
		-- Determine if mesh failed or succeeded (check only for N-gons)
		if NGonCounter > 0 then
		(
			appendIfUnique arr_failed_items selectobj.name as string
		)
		else
		(
			appendIfUnique arr_succeeded_items selectobj.name as string
		)
	)
	
	rollout checker_roll "N-Gon Checker" width:438 height:280
	(
		button btn_refresh_sel "Refresh Selected" pos:[79,16] width:251 height:25 align:#left
		listBox lbx_failed_check "Meshes that Failed Check" pos:[7,47] width:205 height:10 align:#left
		listBox lbx_succeeded_check "Meshes that Succeeded Check" pos:[216,47] width:205 height:10 align:#left
		label lbl3 "Double-click on a mesh from the failed column to select it in viewport" pos:[47,244] width:416 height:18 align:#left
		label lbl4 "Mesh Name:" pos:[7,205] width:63 height:20 align:#left
		label lbl_mesh_name "Empty" pos:[73,205] width:106 height:20 align:#left
		label lbl12 "NGONs:" pos:[200,205] width:44 height:20 align:#left
		label lbl_ngon_count "0" pos:[248,205] width:82 height:20 align:#left
		button btn_select_NGONS "Select N-Gons" pos:[300,205] width:120 height:25 align:#left
	
		-- Function to update display with stored data
		fn updateDisplayFromStoredData mesh_name =
		(
			local data = findMeshData mesh_name
			if data != undefined then
			(
				lbl_mesh_name.text = data.name as string
				lbl_ngon_count.text = data.ngon_count as string
			)
			else
			(
				lbl_mesh_name.text = "Empty"
				lbl_ngon_count.text = "0"
			)
		)
	
		on btn_refresh_sel pressed do
		(
			arr_failed_items = #()
			arr_succeeded_items = #()
			arr_mesh_data = #() -- Clear previous data
			local arr_selection = selection as array
			local int_counter_of_items = 0
			
			for obj in arr_selection do
			(	
				select obj
				if classof obj == Editable_Poly then
				(
					int_counter_of_items += 1
					NGONFinder(obj)
				)
				else
				(	
					local str_name_conv_question = obj.name as string + " is not a Editable Poly, convert?"
					try 
					( 
						if queryBox str_name_conv_question title:"Warning!" beep:true icon:#warning then
						(
							convertTo obj Editable_Poly
							NGONFinder(obj)
						)
					)
					catch
					(
						print "Something went wrong, couldn't convert..."
					)
				)
			)
			
			lbx_failed_check.items = arr_failed_items
			lbx_succeeded_check.items = arr_succeeded_items
			select arr_selection
		)
	
		-- Handle single click to update display
		on lbx_failed_check selected sel do
		(
			if sel > 0 and sel <= lbx_failed_check.items.count then
			(
				local mesh_name = lbx_failed_check.items[sel]
				updateDisplayFromStoredData mesh_name
			)
		)
	
		-- Handle double click to select mesh in viewport
		on lbx_failed_check doubleClicked sel do
		(
			if sel > 0 and sel <= lbx_failed_check.items.count then
			(
				local mesh_name = lbx_failed_check.items[sel]
				local obj = getNodeByName mesh_name
				if obj != undefined then
				(
					select obj
				)
			)
		)
	
		on btn_select_NGONS pressed do
		(
			try
			(
				local sel = lbx_failed_check.selection
				if sel > 0 then
				(
					local mesh_name = lbx_failed_check.items[sel]
					local data = findMeshData mesh_name
					if data != undefined then
					(
						select (getNodeByName mesh_name)
						max modify mode
						subObjectLevel = 4
						
						-- Use multiple selection methods for reliability
						polyop.setFaceSelection $ data.ngon_faces
						if classof $ == Editable_Poly then
						(
							$.EditablePoly.SetSelection #Face data.ngon_faces
						)
						
						-- Force viewport updates
						update $
						redrawViews()
					)
				)
			)
			catch
			(
				print "Failed to select N-gons"
			)
		)
	)
	
	-- Main execution
	on execute do
	(
		-- Check if dialog already exists and close it
		try (destroyDialog checker_roll) catch()
		
		-- Create the dialog
		createDialog checker_roll
	)
)