macroScript HW3_Tools
category:"GSTools"
tooltip:"HW3 Tools"
buttonText:"HW3 Tools"
(
	-- The tool lives in the version-less common tree; see Scene_Checker.mcr for
	-- why the path is walked up from #userScripts.
	local maxRoot = pathConfig.removePathLeaf (pathConfig.removePathLeaf (pathConfig.removePathLeaf (getDir #userScripts)))
	local p = pathConfig.appendPath maxRoot "common\\gstools\\projects\\hw3_tools\\hw3_tools_ui.py"
	if doesFileExist p then python.ExecuteFile p
	else messageBox ("HW3 Tools script not found:\n" + p) title:"HW3 Tools"
)
