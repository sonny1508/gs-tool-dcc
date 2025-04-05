macroScript Bk_Connector
Category:"Bk_Tools"
toolTip:"Bk_Connector"
buttonText:"Bk_Connector"

(
rollout Bk_Connector_Rollout "Bk_Connector" 
	(
	local ip =  getINISetting  ("$userscripts\\startup\\iplist.txt") "IPLIST" "ip" as string
	-------------------------------------------------------------------		
	groupBox 'groupBox_local' "Local" pos:[10,5] width:180 height:112 align:#center

	groupBox 'groupBox_local_blender' "Blender" pos:[20,25] width:75 height:82 align:#center
	button 'button_local_blender_import' "Import" pos:[25,45] width:65 height:23 align:#center
	button 'button_local_blender_export' "Export" pos:[25,78] width:65 height:23 align:#center
	
	groupBox 'groupBox_local_maya' "Maya" pos:[105,25] width:75 height:82 align:#center
	button 'button_local_maya_import' "Import" pos:[110,45] width:65 height:23 align:#center
	button 'button_local_maya_export' "Export" pos:[110,78] width:65 height:23 align:#center

	--------------------------------------------------------------------
	groupBox 'groupBox_server' "Server" pos:[10,123] width:180 height:195 align:#center

	groupBox 'groupBox_server_import' "Import" pos:[20,140] width:160 height:80 align:#center
	dropDownList 'dropDownList_server_import_app' "" pos:[30,160] width:65 height:23 items:#("Blender", "Maya", "Max") align:#center
	dropDownList 'dropDownList_server_import_person' "" pos:[105,160] width:65 height:23 items:#("Den", "Ha", "An", "Minh", "Loan", "Dung", "Trang") align:#center
	button 'button_server_import' "Import" pos:[30,188] width:140 height:23 align:#center

	groupBox 'groupBox_server_export' "Export" pos:[20,227] width:160 height:80 align:#center
	dropDownList 'dropDownList_server_export_app' "" pos:[30,247] width:65 height:23 items:#("Blender", "Maya", "Max") align:#center
	dropDownList 'dropDownList_server_export_person' "" pos:[105,247] width:65 height:23 items:#("Den", "Ha", "An", "Minh", "Loan", "Dung", "Trang") align:#center
	button 'button_server_export' "Export" pos:[30,275] width:140 height:23 align:#center
	----------------------------------------------------------------------
	
	fn Bk_Connector_Import fileName =     
	(	if units.SystemType == #meters do systemtype_x = #m as string
		if units.SystemType == #inches do systemtype_x = #in as string
		if units.SystemType == #centimeters do systemtype_x = #cm as string
		if units.SystemType == #millimeters do systemtype_x = #mm as string
		if units.SystemType == #kilometers do systemtype_x = #km as string
		if units.SystemType == #miles do systemtype_x = #mi as string
		if units.SystemType == #feet do systemtype_x = #ft as string
			
		systemunit_x = units.SystemScale
		systemunit_x_ = 1/systemunit_x as float
		pluginManager.loadClass FBXIMP			
		FBXImporterSetParam "Mode" #create
		FBXImporterSetParam "SmoothingGroups" true		
		FBXImporterSetParam "ScaleFactor" systemunit_x_
		FBXImporterSetParam "ConvertUnit" systemtype_x
		FBXImporterSetParam "Animation" false
		importFile fileName #noprompt usage:FBXIMP
	)	
	
	fn Bk_Connector_Export fileName =
	(
		local expObjs = #()
		 
		for o in selection do
		(	
			if superClassOf o == geometryClass and ClassOf o != Targetobject then
			(	
				local objSnapshot = copy o	
				objSnapshot.name = o.name + ""
				append expObjs objSnapshot
			)
		)
		
		max select none
		select expObjs
			
		if selection.count != 0 then
			(			
				pluginManager.loadClass FBXEXP
				FBXExporterSetParam "SmoothingGroups" true
				FBXExporterSetParam "ASCII" false
				
				-----------------------------------------------------------------------------------						
				exportFile fileName #noPrompt selectedOnly:true	usage:FBXEXP
				for n in expObjs do delete n
				max select none					
			)			
		else
			(
				messageBox "Please select object!!" title:"Warning" beep:off 
			)
	)
	
	on button_local_blender_import pressed do 
	(	
		Bk_Connector_Import ("C:\exportfbx\blender_to_max.fbx")		
	)
	
	on button_local_blender_export pressed do 		
	(		 
		Bk_Connector_Export ("C:\exportfbx\max_to_blender.fbx")	
	)
	
	on button_local_maya_import pressed do 
	(		 	
		Bk_Connector_Import ("C:\exportfbx\maya_to_max.fbx")		
	)
	
	on button_local_maya_export pressed do 		
	(		 
		Bk_Connector_Export ("C:\exportfbx\max_to_maya.fbx")	
	)
	
	on button_server_import pressed do 		
	(	
		
		app1 = dropDownList_server_import_app.selected as string
		app1_lowercase = toLower app1
		app2 = "max" as string
		person1 = dropDownList_server_import_person.selected as string
		person1_lowercase = toLower person1
		if ip == "192.168.0.21" do person2 = "den" as string
		if ip == "192.168.0.5" do person2 = "ha" as string
		if ip == "192.168.0.10" do person2 = "an" as string
		if ip == "192.168.0.7" do person2 = "minh" as string
		if ip == "192.168.0.20" do person2 = "loan" as string
		if ip == "192.168.0.12" do person2 = "dung" as string
		if ip == "192.168.0.203" do person2 = "trang" as string
			
		path = "T:\\exportfbx" + "\\" + app1_lowercase + "_" + person1_lowercase + "_to_" + app2 + "_" + person2 + ".fbx"
		
		Bk_Connector_Import path	
	)
	
	on button_server_export pressed do 		
	(	
		app1 = "max" as string
		app2 = dropDownList_server_export_app.selected as string
		app2_lowercase = toLower app2
		person2 = dropDownList_server_export_person.selected as string
		person2_lowercase = toLower person2
		if ip == "192.168.0.21" do person1 = "den" as string
		if ip == "192.168.0.5" do person1 = "ha" as string
		if ip == "192.168.0.10" do person1 = "an" as string
		if ip == "192.168.0.7" do person1 = "minh" as string
		if ip == "192.168.0.20" do person1 = "loan" as string
		if ip == "192.168.0.12" do person1 = "dung" as string
		if ip == "192.168.0.203" do person1 = "trang" as string
			
		path = "T:\\exportfbx" + "\\" + app1 + "_" + person1 + "_to_" + app2_lowercase + "_" + person2_lowercase + ".fbx"
		Bk_Connector_Export path
	)
	
	)

createDialog Bk_Connector_Rollout 200 330 style:#(#style_titlebar, #style_sysmenu, #style_toolwindow)
	
	
)
