macroScript MGP27_Kerb_Height_Checker
category:"GSTools"
tooltip:"MGP27 Kerb Height Checker"
buttonText:"MGP27 Kerb Height Checker"
(
	-- The tool lives in the version-less common tree; see Scene_Checker.mcr for
	-- why the path is walked up from #userScripts.
	local maxRoot = pathConfig.removePathLeaf (pathConfig.removePathLeaf (pathConfig.removePathLeaf (getDir #userScripts)))
	local p = pathConfig.appendPath maxRoot "common\\gstools\\projects\\mgp27\\kerb_height_checker.py"
	if doesFileExist p then python.ExecuteFile p
	else messageBox ("MGP27 Kerb Height Checker script not found:\n" + p) title:"MGP27 Kerb Height Checker"
)
