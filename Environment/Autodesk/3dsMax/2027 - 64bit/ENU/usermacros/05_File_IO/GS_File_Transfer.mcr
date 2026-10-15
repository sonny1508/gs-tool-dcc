macroScript GS_File_Transfer
Category:"GSTools"
toolTip:"GS File Transfer"
buttonText:"GS File Transfer"

(
	-- Get current Windows username
	local username = sysInfo.username
	local computerName = sysInfo.computername
	
	-- Use system temp directory to support domain usernames (e.g. user.LOCALDOMAIN)
	local tempDir = sysInfo.tempDir
	local localExportPath = tempDir + "fileTransferFbx\\"
	local localExportPathIndividual = tempDir + "fileTransferFbxIndividual\\"

	local serverPath = "\\\\192.168.1.210\\Temp\\File_Transfer\\"
	
	-- Function to clean directory
	fn cleanDirectory dirPath =
	(
		if (doesFileExist dirPath) then
		(
			local files = getFiles (dirPath + "*.*")
			for f in files do
			(
				try (deleteFile f)
				catch (print ("Failed to delete: " + f))
			)
		)
	)
	
	-- Create the directories if they don't exist
	if (doesFileExist localExportPath) == false then (
		makeDir localExportPath recursive:true
		if (doesFileExist localExportPath) == false then
			messageBox ("Failed to create directory: " + localExportPath) title:"Error" beep:true
		else
			print ("Created directory: " + localExportPath)
	)
	
	if (doesFileExist localExportPathIndividual) == false then (
		makeDir localExportPathIndividual recursive:true
		if (doesFileExist localExportPathIndividual) == false then
			messageBox ("Failed to create directory: " + localExportPathIndividual) title:"Error" beep:true
		else
			print ("Created directory: " + localExportPathIndividual)
	)
	
	-- Generate user list from CSV file
	local gsFolderList = #()
	local csvPath = "\\\\192.168.1.210\\Pipeline\\Library\\Data\\Data_Users.csv"

	try
	(
		if (doesFileExist csvPath) then
		(
			local file = openFile csvPath mode:"r"
			if file != undefined then
			(
				local headerLine = readLine file
				local headers = filterString headerLine ","
				local userColumnIndex = 0
				
				-- Find the "users" column index
				for i = 1 to headers.count do
				(
					local trimmedHeader = trimLeft (trimRight headers[i])
					if (toLower trimmedHeader) == "users" then
					(
						userColumnIndex = i
						exit
					)
				)
				
				if userColumnIndex > 0 then
				(
					-- Read the rest of the file and extract user values
					while not eof file do
					(
						local line = readLine file
						if line != undefined and line != "" then
						(
							local values = filterString line ","
							if values.count >= userColumnIndex then
							(
								local userValue = trimLeft (trimRight values[userColumnIndex])
								if userValue != "" then
									append gsFolderList userValue
							)
						)
					)
				)
				else
				(
					print "Warning: 'users' column not found in CSV file"
				)
				
				close file
			)
			else
			(
				print "Error: Could not open CSV file"
			)
		)
		else
		(
			print "Warning: CSV file not found, using default gs01-99 list"
		)
	)
	catch
	(
		print ("Error reading CSV file: " + (getCurrentException()))
	)
	
	rollout GS_File_Transfer_Rollout "GS_File_Transfer" 
	(
		-------------------------------------------------------------------
		-- Mode Radio Buttons at the top
		radioButtons 'radio_export_mode' "Mode:" pos:[10,10] width:230 height:40 labels:#("All", "Individual") default:1 columns:2 align:#center
		
		-------------------------------------------------------------------
		-- Smoothing Groups Toggles
		checkbox 'chk_import_smoothing_groups' "Import Smoothing Groups" pos:[10,55] width:150 height:20 checked:false align:#left
		-- checkbox 'chk_export_smoothing_groups' "Export Smoothing Groups" pos:[10,75] width:150 height:20 checked:true align:#left
		
		-------------------------------------------------------------------		
		groupBox 'groupBox_local' "Local" pos:[10,100] width:230 height:112 align:#center

		groupBox 'groupBox_local_blender' "Blender" pos:[15,120] width:105 height:82 align:#center
		button 'button_local_blender_import' "Import" pos:[20,140] width:95 height:25 align:#center
		button 'button_local_blender_export' "Export" pos:[20,173] width:95 height:25 align:#center
		
		groupBox 'groupBox_local_maya' "Maya" pos:[130,120] width:105 height:82 align:#center
		button 'button_local_maya_import' "Import" pos:[135,140] width:95 height:25 align:#center
		button 'button_local_maya_export' "Export" pos:[135,173] width:95 height:25 align:#center

		--------------------------------------------------------------------
		groupBox 'groupBox_server' "Server" pos:[10,218] width:230 height:198 align:#center

		groupBox 'groupBox_server_import' "Import" pos:[15,235] width:220 height:85 align:#center
		dropDownList 'dropDownList_server_import_app' "" pos:[20,255] width:95 height:25 items:#("Blender", "Maya", "Max") align:#center
		dropDownList 'dropDownList_server_import_person' "" pos:[135,255] width:95 height:25 items:gsFolderList align:#center
		button 'button_server_import' "Import" pos:[20,283] width:210 height:25 align:#center

		groupBox 'groupBox_server_export' "Export" pos:[15,322] width:220 height:85 align:#center
		dropDownList 'dropDownList_server_export_app' "" pos:[20,342] width:95 height:25 items:#("Blender", "Maya", "Max") align:#center
		dropDownList 'dropDownList_server_export_person' "" pos:[135,342] width:95 height:25 items:gsFolderList align:#center
		button 'button_server_export' "Export" pos:[20,370] width:210 height:25 align:#center
		
		-- Add username display at bottom (adjusted position)
		label label_user "User: " pos:[10,425] width:100 height:20 align:#left
		label label_username username pos:[140,425] width:95 height:20 align:#left
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
				
				-- Set FBX import parameters (use checkbox value for smoothing groups)
				FBXImporterSetParam "Mode" #create
				FBXImporterSetParam "SmoothingGroups" chk_import_smoothing_groups.checked		
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
		
		fn GS_File_Transfer_Import_Individual dirPath pattern =
		(
			if (doesFileExist dirPath) == false then
			(
				messageBox ("Directory does not exist: " + dirPath) title:"Import Error" beep:off
				return false
			)
			
			-- Find all FBX files matching the pattern
			local searchPattern = dirPath + "*" + pattern + "*.fbx"
			local fbxFiles = getFiles searchPattern
			
			if fbxFiles.count == 0 then
			(
				messageBox ("No FBX files found with pattern: " + pattern + " in " + dirPath) title:"Import Error" beep:off
				return false
			)
			
			local importedCount = 0
			for fbxFile in fbxFiles do
			(
				if (GS_File_Transfer_Import fbxFile) then
					importedCount += 1
			)
			
			messageBox ("Successfully imported " + (importedCount as string) + " file(s)") title:"Import Complete" beep:off
			return (importedCount > 0)
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
				FBXExporterSetParam "Animation" false
				FBXExporterSetParam "SmoothingGroups" true
				FBXExporterSetParam "SmoothMeshExport" false
				FBXExporterSetParam "Shape" false
				FBXExporterSetParam "Skin" false
				FBXExporterSetParam "Triangulate" false
				FBXExporterSetParam "PreserveEdgeOrientation" true

				FBXExporterSetParam "Preserveinstances" true

				FBXExporterSetParam "EmbedTextures" false

				FBXExporterSetParam "ASCII" false
				FBXExporterSetParam "FileVersion" "FBX202000"
				
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
		
		fn GS_File_Transfer_Export_Individual dirPath targetApp =
		(
			-- Check if there's anything selected
			if selection.count == 0 then
			(
				messageBox "Please select objects to export!" title:"Warning" beep:off
				return false
			)
			
			-- Clean directory before export
			cleanDirectory dirPath
			
			-- Create export directory if it doesn't exist
			if (doesFileExist dirPath) == false then
			(
				makeDir dirPath recursive:true
				if (doesFileExist dirPath) == false then
				(
					messageBox ("Failed to create directory: " + dirPath) title:"Export Error" beep:off
					return false
				)
			)
			
			local savedSelection = getCurrentSelection()
			local exportedCount = 0
			
			-- Export each selected object individually
			for obj in selection do
			(
				if (superClassOf obj == geometryClass and ClassOf obj != Targetobject) then
				(
					-- Create safe filename from object name
					local safeName = obj.name
					safeName = substituteString safeName " " "_"
					safeName = substituteString safeName ":" "_"
					safeName = substituteString safeName "\\" "_"
					safeName = substituteString safeName "/" "_"
					safeName = substituteString safeName "*" "_"
					safeName = substituteString safeName "?" "_"
					safeName = substituteString safeName "\"" "_"
					safeName = substituteString safeName "<" "_"
					safeName = substituteString safeName ">" "_"
					safeName = substituteString safeName "|" "_"
					
					local fileName = dirPath + safeName + "_max_to_" + targetApp + ".fbx"
					
					-- Select only this object
					max select none
					select obj
					
					-- Export this object
					if (GS_File_Transfer_Export fileName) then
						exportedCount += 1
				)
			)
			
			-- Restore original selection
			select savedSelection
			
			messageBox ("Successfully exported " + (exportedCount as string) + " object(s) individually") title:"Export Complete" beep:off
			return (exportedCount > 0)
		)
		
		on button_local_blender_import pressed do 
		(	
			if radio_export_mode.state == 1 then -- All mode
			(
				local importFile = localExportPath + "blender_to_max.fbx"
				print ("Attempting to import: " + importFile)
				GS_File_Transfer_Import importFile
			)
			else -- Individual mode
			(
				print ("Attempting to import individual files from: " + localExportPathIndividual)
				GS_File_Transfer_Import_Individual localExportPathIndividual "blender_to_max"
			)
		)
		
		on button_local_blender_export pressed do 		
		(	
			if radio_export_mode.state == 1 then -- All mode
			(
				local exportFile = localExportPath + "max_to_blender.fbx"
				print ("Attempting to export to: " + exportFile)	
				GS_File_Transfer_Export exportFile
			)
			else -- Individual mode
			(
				print ("Attempting to export individual files to: " + localExportPathIndividual)
				GS_File_Transfer_Export_Individual localExportPathIndividual "blender"
			)
		)
		
		on button_local_maya_import pressed do 
		(	
			if radio_export_mode.state == 1 then -- All mode
			(
				local importFile = localExportPath + "maya_to_max.fbx"
				print ("Attempting to import: " + importFile)
				GS_File_Transfer_Import importFile
			)
			else -- Individual mode
			(
				print ("Attempting to import individual files from: " + localExportPathIndividual)
				GS_File_Transfer_Import_Individual localExportPathIndividual "maya_to_max"
			)
		)
		
		on button_local_maya_export pressed do 		
		(	
			if radio_export_mode.state == 1 then -- All mode
			(
				local exportFile = localExportPath + "max_to_maya.fbx"
				print ("Attempting to export to: " + exportFile)
				GS_File_Transfer_Export exportFile
			)
			else -- Individual mode
			(
				print ("Attempting to export individual files to: " + localExportPathIndividual)
				GS_File_Transfer_Export_Individual localExportPathIndividual "maya"
			)
		)
		
		on button_server_import pressed do 		
		(	
			app1 = dropDownList_server_import_app.selected as string
            app1_lowercase = toLower app1
			app2 = "max" as string
			gsFolder = dropDownList_server_import_person.selected as string
			
			-- Build the path with new folder structure
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
      local filePath = serverPath + username + "\\" + username + "_" + app1 + "_to_" + app2_lowercase + "_" + gsFolder + ".fbx"
			
			print ("Attempting to export to server: " + filePath)
			GS_File_Transfer_Export filePath
		)
	)

	createDialog GS_File_Transfer_Rollout 250 450 style:#(#style_titlebar, #style_sysmenu, #style_toolwindow)
)