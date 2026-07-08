macroScript Scene_Checker
category:"GSTools"
tooltip:"Scene Checker"
buttonText:"Scene Checker"
(
	-- Derive this tool's deployed Python entry point. Resolve the scripts root
	-- via getDir #userScripts directly so the macro never depends on a global
	-- existing at its own compile time (load order vs. startup is not guaranteed).
	local root = (getDir #userScripts) + "\\gstools\\"
	local p = root + "review\\scene_checker\\scene_checker_ui.py"
	if doesFileExist p then python.ExecuteFile p
	else messageBox ("Scene Checker script not found:\n" + p) title:"Scene Checker"
)
