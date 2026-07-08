-- scene_checker.ms — GSTools Scene Checker backend for 3ds Max 2023
-- All checking / selection / fix logic lives here, lifted verbatim from the
-- original Scene_Checker.mcr rollout. Called from scene_checker_ui.py.
--
-- This file is fileIn'd fresh every time the tool is opened (see show() in the
-- .py), so editing it takes effect on the next launch — no Max restart needed,
-- unlike the .mcr macro it replaces.
--
-- Everything is prefixed SC_ to keep the global namespace clean. The UI only
-- ever calls the SC_* entry functions near the bottom of this file; the rest is
-- unchanged internal logic.

-- ── Data globals ─────────────────────────────────────────────────────────────
global SC_arr_ngon_objects = #()
global SC_arr_openedge_objects = #()
global SC_arr_sg_objects = #()
global SC_arr_transform_objects = #()
global SC_arr_mesh_data = #()
global SC_arr_openedge_data = #()
global SC_arr_sg_data = #()
global SC_arr_transform_data = #()
global SC_arr_uv_objects = #()
global SC_arr_uv_data = #()
global SC_current_check_type = ""
global SC_position_threshold = 0.01
global SC_rotation_threshold = 0.1  -- degrees
global SC_scale_threshold = 0.01

-- ── Structure definitions ────────────────────────────────────────────────────
struct SC_MeshAnalysisData (
	name,
	ngon_count,
	ngon_faces = #()
)

struct SC_OpenEdgeAnalysisData (
	name,
	open_edges = #()
)

struct SC_SGAnalysisData (
	name,
	faces_without_sg = #()
)

struct SC_TransformAnalysisData (
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

struct SC_UVAnalysisData (
	name,
	uv_channel_count,
	uv_channels = #()
)

-- ── Helper (lookup) functions ────────────────────────────────────────────────
fn SC_findMeshData mesh_name =
(
	for data in SC_arr_mesh_data do
	(
		if data.name == mesh_name then
			return data
	)
	return undefined
)

fn SC_findOpenEdgeData mesh_name =
(
	for data in SC_arr_openedge_data do
	(
		if data.name == mesh_name then
			return data
	)
	return undefined
)

fn SC_findSGData mesh_name =
(
	for data in SC_arr_sg_data do
	(
		if data.name == mesh_name then
			return data
	)
	return undefined
)

fn SC_findTransformData obj_name =
(
	for data in SC_arr_transform_data do
	(
		if data.name == obj_name then
			return data
	)
	return undefined
)

fn SC_findUVData mesh_name =
(
	for data in SC_arr_uv_data do
	(
		if data.name == mesh_name then
			return data
	)
	return undefined
)

-- ── Validation function ──────────────────────────────────────────────────────
fn SC_validateEditablePoly selection_array =
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

-- ── Open Edges checker function ──────────────────────────────────────────────
fn SC_checkOpenEdges selectobj =
(
	local open_edges = polyop.getOpenEdges selectobj

	local analysis_data = SC_OpenEdgeAnalysisData()
	analysis_data.name = selectobj.name
	analysis_data.open_edges = open_edges

	for i = SC_arr_openedge_data.count to 1 by -1 do
	(
		if SC_arr_openedge_data[i].name == selectobj.name then
			deleteItem SC_arr_openedge_data i
	)
	append SC_arr_openedge_data analysis_data

	if open_edges.numberSet > 0 then
	(
		appendIfUnique SC_arr_openedge_objects selectobj.name
	)
)

-- ── N-gon checker function ───────────────────────────────────────────────────
fn SC_checkNgons selectobj =
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

	local analysis_data = SC_MeshAnalysisData()
	analysis_data.name = selectobj.name
	analysis_data.ngon_count = ngon_faces.count
	analysis_data.ngon_faces = ngon_faces as bitArray

	for i = SC_arr_mesh_data.count to 1 by -1 do
	(
		if SC_arr_mesh_data[i].name == selectobj.name then
			deleteItem SC_arr_mesh_data i
	)
	append SC_arr_mesh_data analysis_data

	if ngon_faces.count > 0 then
	(
		appendIfUnique SC_arr_ngon_objects selectobj.name
	)
)

-- ── Smoothing groups checker function ────────────────────────────────────────
fn SC_checkSmoothingGroups selectobj =
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

	local sg_data = SC_SGAnalysisData()
	sg_data.name = selectobj.name
	sg_data.faces_without_sg = faces_without_sg as bitArray

	for i = SC_arr_sg_data.count to 1 by -1 do
	(
		if SC_arr_sg_data[i].name == selectobj.name then
			deleteItem SC_arr_sg_data i
	)
	append SC_arr_sg_data sg_data

	if faces_without_sg.count > 0 then
	(
		appendIfUnique SC_arr_sg_objects selectobj.name
	)
)

-- ── Transform checker function ───────────────────────────────────────────────
fn SC_checkTransform selectobj =
(
	local hasError = false
	local transform_data = SC_TransformAnalysisData()
	transform_data.name = selectobj.name

	-- Check position
	local objPos = selectobj.pos
	transform_data.position = objPos
	local posXExceeds = (abs objPos.x) > SC_position_threshold
	local posYExceeds = (abs objPos.y) > SC_position_threshold
	local posZExceeds = (abs objPos.z) > SC_position_threshold
	if posXExceeds or posYExceeds or posZExceeds then
	(
		transform_data.has_position_error = true
		hasError = true
	)

	-- Check rotation (convert to euler angles for easier threshold checking)
	local objRotation = selectobj.rotation
	transform_data.rotation = objRotation
	local eulerRot = objRotation as eulerAngles
	local rotXExceeds = (abs eulerRot.x) > SC_rotation_threshold
	local rotYExceeds = (abs eulerRot.y) > SC_rotation_threshold
	local rotZExceeds = (abs eulerRot.z) > SC_rotation_threshold
	if rotXExceeds or rotYExceeds or rotZExceeds then
	(
		transform_data.has_rotation_error = true
		hasError = true
	)

	-- Check scale
	local objScale = selectobj.scale
	transform_data.scale = objScale
	local scaleXExceeds = (abs (objScale.x - 1.0)) > SC_scale_threshold
	local scaleYExceeds = (abs (objScale.y - 1.0)) > SC_scale_threshold
	local scaleZExceeds = (abs (objScale.z - 1.0)) > SC_scale_threshold
	if scaleXExceeds or scaleYExceeds or scaleZExceeds then
	(
		transform_data.has_scale_error = true
		hasError = true
	)

	-- Check pivot
	local pivotPos = selectobj.pivot
	transform_data.pivot_position = pivotPos
	local pivotXExceeds = (abs pivotPos.x) > SC_position_threshold
	local pivotYExceeds = (abs pivotPos.y) > SC_position_threshold
	local pivotZExceeds = (abs pivotPos.z) > SC_position_threshold
	if pivotXExceeds or pivotYExceeds or pivotZExceeds then
	(
		transform_data.has_pivot_error = true
		hasError = true
	)

	if hasError then
	(
		-- Remove existing data for this object
		for i = SC_arr_transform_data.count to 1 by -1 do
		(
			if SC_arr_transform_data[i].name == selectobj.name then
				deleteItem SC_arr_transform_data i
		)
		append SC_arr_transform_data transform_data

		appendIfUnique SC_arr_transform_objects selectobj.name
	)
)

-- ── UV Channels checker function ─────────────────────────────────────────────
fn SC_checkUVChannels selectobj =
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

	local analysis_data = SC_UVAnalysisData()
	analysis_data.name = selectobj.name
	analysis_data.uv_channel_count = uv_channels.count
	analysis_data.uv_channels = uv_channels

	-- Remove existing data for this object
	for i = SC_arr_uv_data.count to 1 by -1 do
	(
		if SC_arr_uv_data[i].name == selectobj.name then
			deleteItem SC_arr_uv_data i
	)
	append SC_arr_uv_data analysis_data

	-- Only add objects with more than 1 UV channel
	if uv_channels.count > 1 then
	(
		appendIfUnique SC_arr_uv_objects selectobj.name
	)
)

-- ── Helper: enter Edit Poly mode (polygon level) ─────────────────────────────
fn SC_enterEditPolyMode obj =
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

-- ── Helper: enter Edit Poly edge mode ────────────────────────────────────────
fn SC_enterEditPolyEdgeMode obj =
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

-- ── Universal Select Error function ──────────────────────────────────────────
fn SC_selectErrors =
(
	case SC_current_check_type of
	(
		"openedges":
		(
			-- TOPOLOGY section - select open edges
			for obj_name in SC_arr_openedge_objects do
			(
				local obj = getNodeByName obj_name
				local data = SC_findOpenEdgeData obj_name
				if obj != undefined and data != undefined and data.open_edges.numberSet > 0 then
				(
					select obj
					if SC_enterEditPolyEdgeMode obj then
					(
						polyop.setEdgeSelection obj data.open_edges
						update obj
					)
				)
			)
			print ("Selected open edges in " + SC_arr_openedge_objects.count as string + " objects")
		)
		"ngons":
		(
			-- TOPOLOGY section - select error polygons
			for obj_name in SC_arr_ngon_objects do
			(
				local obj = getNodeByName obj_name
				local data = SC_findMeshData obj_name
				if obj != undefined and data != undefined and data.ngon_faces.count > 0 then
				(
					select obj
					if SC_enterEditPolyMode obj then
					(
						polyop.setFaceSelection obj data.ngon_faces
						update obj
					)
				)
			)
			print ("Selected N-gon faces in " + SC_arr_ngon_objects.count as string + " objects")
		)
		"sg":
		(
			-- TOPOLOGY section - select error polygons
			for obj_name in SC_arr_sg_objects do
			(
				local obj = getNodeByName obj_name
				local data = SC_findSGData obj_name
				if obj != undefined and data != undefined and data.faces_without_sg.count > 0 then
				(
					select obj
					if SC_enterEditPolyMode obj then
					(
						polyop.setFaceSelection obj data.faces_without_sg
						update obj
					)
				)
			)
			print ("Selected faces without smoothing groups in " + SC_arr_sg_objects.count as string + " objects")
		)
		"transform":
		(
			-- OBJECT section - select error objects
			local objects_to_select = #()
			for obj_name in SC_arr_transform_objects do
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

fn SC_canReuseGroup obj faceIdx groupNum facesToProcess assignments angleThreshold =
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

fn SC_processSelectedFaces obj angleThreshold =
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
			if SC_canReuseGroup obj faceIdx groupNum facesToProcess assignments angleThreshold then
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
fn SC_applyResetXForm obj =
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

-- ── UI entry points ──────────────────────────────────────────────────────────
-- These wrap the original rollout button handlers. Each returns the data the
-- PySide2 UI needs (a list of names, a list of display strings, or a count).
-- A return of `undefined` means "validation failed / nothing to do" — the UI
-- leaves its list unchanged, exactly like the original handlers' early return.

fn SC_CheckOpenEdges =
(
	-- Validate selection first
	if not (SC_validateEditablePoly (selection as array)) then
		return undefined

	SC_arr_openedge_objects = #()
	SC_arr_openedge_data = #()

	for obj in selection do
	(
		SC_checkOpenEdges obj
	)

	SC_current_check_type = "openedges"
	return SC_arr_openedge_objects
)

fn SC_CheckNgons =
(
	-- Validate selection first
	if not (SC_validateEditablePoly (selection as array)) then
		return undefined

	SC_arr_ngon_objects = #()
	SC_arr_mesh_data = #()

	for obj in selection do
	(
		SC_checkNgons obj
	)

	SC_current_check_type = "ngons"
	return SC_arr_ngon_objects
)

fn SC_CheckSmoothing =
(
	-- Validate selection first
	if not (SC_validateEditablePoly (selection as array)) then
		return undefined

	SC_arr_sg_objects = #()
	SC_arr_sg_data = #()

	for obj in selection do
	(
		SC_checkSmoothingGroups obj
	)

	SC_current_check_type = "sg"
	return SC_arr_sg_objects
)

fn SC_CheckTransform =
(
	SC_arr_transform_objects = #()
	SC_arr_transform_data = #()

	for obj in selection do
	(
		SC_checkTransform obj
	)

	SC_current_check_type = "transform"
	return SC_arr_transform_objects
)

-- Returns display strings formatted "ObjectName (NN maps)", matching the
-- original rollout's UV list formatting. The UI parses the name back out on
-- double-click.
fn SC_CheckUVChannels =
(
	if selection.count == 0 then
	(
		messageBox "Please select at least one object" title:"No Selection" beep:true
		return undefined
	)

	SC_arr_uv_objects = #()
	SC_arr_uv_data = #()

	for obj in selection do
	(
		SC_checkUVChannels obj
	)

	SC_current_check_type = "uv"

	local display_items = #()
	for obj_name in SC_arr_uv_objects do
	(
		local uv_data = SC_findUVData obj_name
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
	return display_items
)

fn SC_AutoFlatSG =
(
	if selection.count == 0 then
	(
		return undefined
	)

	if not (SC_validateEditablePoly (selection as array)) then
		return undefined

	local processed_count = 0
	with undo "Auto Flat SG" on
	(
		for obj in selection do
		(
			local faces_processed = SC_processSelectedFaces obj 5.0
			if faces_processed > 0 then
				processed_count += 1
		)
	)

	print ("Auto-assigned flat smoothing groups to " + processed_count as string + " objects")
	return processed_count
)

fn SC_ResetXForm =
(
	-- Always work on current selection
	if selection.count == 0 then
	(
		return undefined
	)

	local reset_count = 0
	local objects_to_reset = selection as array

	with undo "Reset XForm" on
	(
		for obj in objects_to_reset do
		(
			if SC_applyResetXForm obj then
				reset_count += 1
		)
	)

	print ("Applied Reset XForm to " + reset_count as string + " objects")
	return reset_count
)

fn SC_ResetPivot =
(
	-- Always work on current selection
	if selection.count == 0 then
	(
		return undefined
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
	return reset_count
)

-- Select the errors for the last-run check (used by the "Select Error" button).
fn SC_SelectError =
(
	SC_selectErrors()
)

-- Select a single scene object by name (used by list double-click).
fn SC_SelectByName obj_name =
(
	local obj = getNodeByName obj_name
	if obj != undefined then
	(
		select obj
		return true
	)
	return false
)
