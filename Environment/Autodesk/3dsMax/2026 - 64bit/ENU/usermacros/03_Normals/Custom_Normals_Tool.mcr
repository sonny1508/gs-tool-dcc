macroScript Custom_Normals_Tool
category:	"GSTools"
tooltip:	"Custom Normals Tool"
buttonText:	"Custom Normals Tool"
silentErrors: true
icon:#("CustomNormalsToolIcon",1)
(
	Macro_File = (GetDir #userScripts) + "\\gstools\\normals\\N00BY_Scripts\\n00by_Custom_Normals_Tool_v1.2.mse"
	if (doesFileExist Macro_File) then fileIn Macro_File
	else messageBox "Unable to locate the script !" title:":o"
)