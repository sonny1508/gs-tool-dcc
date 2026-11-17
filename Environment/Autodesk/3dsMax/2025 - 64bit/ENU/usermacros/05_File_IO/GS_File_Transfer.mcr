macroScript GS_File_Transfer
Category:"GSTools"
toolTip:"GS File Transfer"
buttonText:"GS File Transfer"
(
	-- The tool lives in the version-less common tree; see Scene_Checker.mcr for
	-- why the path is walked up from #userScripts.
	local maxRoot = pathConfig.removePathLeaf (pathConfig.removePathLeaf (pathConfig.removePathLeaf (getDir #userScripts)))
	local p = pathConfig.appendPath maxRoot "common\\gstools\\file_io\\file_transfer\\gs_file_transfer.py"
	if doesFileExist p then python.ExecuteFile p
	else messageBox ("GS File Transfer script not found:\n" + p) title:"GS File Transfer"
)
