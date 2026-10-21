macroScript Scene_Checker
category:"GSTools"
tooltip:"Scene Checker"
buttonText:"Scene Checker"
(
	-- The tool lives in the version-less common tree, deployed beside the version
	-- folders (...\Autodesk\3dsMax\common). #userScripts is
	-- ...\3dsMax\<year> - 64bit\ENU\scripts, so three leaves up is that 3dsMax
	-- folder. Resolved here rather than from a startup-script global, because
	-- macro and startup load order is not guaranteed.
	local maxRoot = pathConfig.removePathLeaf (pathConfig.removePathLeaf (pathConfig.removePathLeaf (getDir #userScripts)))
	local p = pathConfig.appendPath maxRoot "common\\gstools\\review\\scene_checker\\scene_checker_ui.py"
	if doesFileExist p then python.ExecuteFile p
	else messageBox ("Scene Checker script not found:\n" + p) title:"Scene Checker"
)
