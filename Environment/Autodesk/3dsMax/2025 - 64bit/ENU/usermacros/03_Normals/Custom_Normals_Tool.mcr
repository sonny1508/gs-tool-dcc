macroScript Custom_Normals_Tool
category:	"GSTools"
tooltip:	"Custom Normals Tool"
buttonText:	"Custom Normals Tool"
silentErrors: true
icon:#("CustomNormalsToolIcon",1)
(
	-- The tool lives in the version-less common tree; see Scene_Checker.mcr for
	-- why the path is walked up from #userScripts.
	local maxRoot = pathConfig.removePathLeaf (pathConfig.removePathLeaf (pathConfig.removePathLeaf (getDir #userScripts)))
	local p = pathConfig.appendPath maxRoot "common\\gstools\\normals\\N00BY_Scripts\\n00by_Custom_Normals_Tool_v1.2.mse"
	if doesFileExist p then fileIn p
	else messageBox ("Custom Normals Tool script not found:\n" + p) title:"Custom Normals Tool"
)
