macroScript GS_File_Transfer
Category:"GSTools"
toolTip:"GS_File_Transfer"
buttonText:"GS_File_Transfer"

(
	-- Get current Windows username
	local username = sysInfo.username
	local computerName = sysInfo.computername
	
	-- Construct temp directory path directly using username
	local tempDir = "C:\\Users\\" + username + "\\AppData\\Local\\Temp\\"
	local localExportPath = tempDir + "fileTransferFbx\\"
	
	-- Create the directory if it doesn't exist
	if (doesFileExist localExportPath) == false then (
		makeDir localExportPath recursive:true
		-- Verify directory was created
		if (doesFileExist localExportPath) == false then
			messageBox ("Failed to create directory: " + localExportPath) title:"Error" beep:true
		else
			print ("Created directory: " + localExportPath)
	)
	
	-- Generate gs folder list
	local gsFolderList = #()
	for i = 1 to 99 do
	(
		local gsNum = formattedPrint i format:"02d"
		append gsFolderList ("gs" + gsNum)
	)
	
	rollout GS_File_Transfer_Rollout "GS_File_Transfer" 
	(
		-------------------------------------------------------------------		
		groupBox 'groupBox_local' "Local" pos:[10,5] width:180 height:112 align:#center

		groupBox 'groupBox_local_blender' "Blender" pos:[20,25] width:75 height:82 align:#center
		button 'button_local_blender_import' "Import" pos:[25,45] width:65 height:25 align:#center
		button 'button_local_blender_export' "Export" pos:[25,78] width:65 height:25 align:#center
		
		groupBox 'groupBox_local_maya' "Maya" pos:[105,25] width:75 height:82 align:#center
		button 'button_local_maya_import' "Import" pos:[110,45] width:65 height:25 align:#center
		button 'button_local_maya_export' "Export" pos:[110,78] width:65 height:25 align:#center

		--------------------------------------------------------------------
		groupBox 'groupBox_server' "Server" pos:[10,123] width:180 height:195 align:#center

		groupBox 'groupBox_server_import' "Import" pos:[20,140] width:160 height:80 align:#center
		dropDownList 'dropDownList_server_import_app' "" pos:[30,160] width:65 height:25 items:#("Blender", "Maya", "Max") align:#center
		dropDownList 'dropDownList_server_import_person' "" pos:[105,160] width:65 height:25 items:gsFolderList align:#center
		button 'button_server_import' "Import" pos:[30,188] width:140 height:25 align:#center

		groupBox 'groupBox_server_export' "Export" pos:[20,227] width:160 height:80 align:#center
		dropDownList 'dropDownList_server_export_app' "" pos:[30,247] width:65 height:25 items:#("Blender", "Maya", "Max") align:#center
		dropDownList 'dropDownList_server_export_person' "" pos:[105,247] width:65 height:25 items:gsFolderList align:#center
		button 'button_server_export' "Export" pos:[30,275] width:140 height:25 align:#center
		
		-- Add username display at bottom (with fixed syntax)
		label label_user "User: " pos:[10,325] width:100 height:20 align:#left
		label label_username username pos:[115,325] width:80 height:20 align:#left
		----------------------------------------------------------------------
		
		fn GS_File_Transfer_Import fileName =     
		(	
			-- Check if file exists first
			if (doesFileExist fileName) == false then
			(
				messageBox ("File does not exist: " + fileName) title:"Import Error" beep:off
				return false
			)
			
			-- Get current system units for conversion
			local systemtype_x
			case units.SystemType of
			(
				#meters: systemtype_x = "m"
				#inches: systemtype_x = "in"
				#centimeters: systemtype_x = "cm"
				#millimeters: systemtype_x = "mm"
				#kilometers: systemtype_x = "km"
				#miles: systemtype_x = "mi"
				#feet: systemtype_x = "ft"
				default: systemtype_x = "cm" -- Default to cm if none match
			)
			
			local systemunit_x = units.SystemScale
			local systemunit_x_ = 1/systemunit_x as float
			
			try
			(
				-- Load FBX importer plugin
				pluginManager.loadClass FBXIMP
				
				-- Set FBX import parameters
				FBXImporterSetParam "Mode" #create
				FBXImporterSetParam "SmoothingGroups" false		
				FBXImporterSetParam "ScaleFactor" systemunit_x_
				FBXImporterSetParam "ConvertUnit" systemtype_x
				FBXImporterSetParam "Animation" false
				
				-- Import the file
				local result = importFile fileName #noprompt usage:FBXIMP
				if result then print ("Successfully imported: " + fileName)
				return result
			)
			catch
			(
				messageBox ("Error importing file: " + (getCurrentException())) title:"Import Error" beep:off
				return false
			)
		)	
		
		fn GS_File_Transfer_Export fileName =
		(
			-- Check if there's anything selected
			if selection.count == 0 then
			(
				messageBox "Please select objects to export!" title:"Warning" beep:off
				return false
			)
			
			-- Create export directory if it doesn't exist
			local dirPath = getFilenamePath fileName
			if (doesFileExist dirPath) == false then
			(
				makeDir dirPath recursive:true
				if (doesFileExist dirPath) == false then
				(
					messageBox ("Failed to create directory: " + dirPath) title:"Export Error" beep:off
					return false
				)
			)
			
			-- Create copies of selected objects for export
			local expObjs = #()
			 
			for o in selection do
			(	
				if (superClassOf o == geometryClass and ClassOf o != Targetobject) then
				(	
					local objSnapshot = copy o	
					objSnapshot.name = o.name
					append expObjs objSnapshot
				)
			)
			
			if expObjs.count == 0 then
			(
				messageBox "No valid geometry objects in selection!" title:"Warning" beep:off
				return false
			)
			
			-- Store original selection
			local savedSelection = getCurrentSelection()
			
			-- Select the objects to export
			max select none
			select expObjs
			
			try
			(
				-- Load FBX exporter plugin
				pluginManager.loadClass FBXEXP
				
				-- Set FBX export parameters
				FBXExporterSetParam "SmoothingGroups" true
				FBXExporterSetParam "ASCII" false
				FBXExporterSetParam "Animation" false
				FBXExporterSetParam "Triangulate" false
				
				-- Export the file
				local result = exportFile fileName #noPrompt selectedOnly:true usage:FBXEXP
				if result then print ("Successfully exported to: " + fileName)
				
				-- Clean up temporary objects
				for n in expObjs do delete n
				
				-- Restore original selection
				select savedSelection
				
				return result
			)
			catch
			(
				-- Clean up on error
				for n in expObjs where (isValidNode n) do delete n
				select savedSelection
				
				messageBox ("Error exporting file: " + (getCurrentException())) title:"Export Error" beep:off
				return false
			)
		)
		
		on button_local_blender_import pressed do 
		(	
			local importFile = localExportPath + "blender_to_max.fbx"
			print ("Attempting to import: " + importFile)
			GS_File_Transfer_Import importFile
		)
		
		on button_local_blender_export pressed do 		
		(	
			local exportFile = localExportPath + "max_to_blender.fbx"
			print ("Attempting to export to: " + exportFile)	
			GS_File_Transfer_Export exportFile
		)
		
		on button_local_maya_import pressed do 
		(	
			local importFile = localExportPath + "maya_to_max.fbx"
			print ("Attempting to import: " + importFile)
			GS_File_Transfer_Import importFile	
		)
		
		on button_local_maya_export pressed do 		
		(	
			local exportFile = localExportPath + "max_to_maya.fbx"
			print ("Attempting to export to: " + exportFile)
			GS_File_Transfer_Export exportFile
		)
		
		on button_server_import pressed do 		
		(	
			app1 = dropDownList_server_import_app.selected as string
            app1_lowercase = toLower app1
			app2 = "max" as string
			gsFolder = dropDownList_server_import_person.selected as string
			
			-- Build the path with new folder structure
			local serverPath = "\\\\192.168.1.10\\Temp\\File_Transfer\\"
            local filePath = serverPath + gsFolder + "\\" + gsFolder + "_" + app1_lowercase + "_to_" + app2 + "_" + username + ".fbx"
			
			print ("Attempting to import from server: " + filePath)
			GS_File_Transfer_Import filePath
		)
		
		on button_server_export pressed do 		
		(	
			app2 = dropDownList_server_export_app.selected as string
            app2_lowercase = toLower app2
            app1 = "max" as string
			gsFolder = dropDownList_server_export_person.selected as string
			
			-- Build the path with new folder structure
			local serverPath = "\\\\192.168.1.10\\Temp\\File_Transfer\\"
            local filePath = serverPath + username + "\\" + username + "_" + app1 + "_to_" + app2_lowercase + "_" + gsFolder + ".fbx"
			
			print ("Attempting to export to server: " + filePath)
			GS_File_Transfer_Export filePath
		)
	)

	createDialog GS_File_Transfer_Rollout 200 350 style:#(#style_titlebar, #style_sysmenu, #style_toolwindow)
)