macroScript HW3_Tools
Category:"GSTools"
toolTip:"HW3 Tools"
buttonText:"HW3 Tools"
(
    -- Derive this tool's deployed Python entry point. Resolve the scripts root
    -- via getDir #userScripts directly so the macro never depends on a global
    -- existing at its own compile time (load order vs. startup is not guaranteed).
    local root = (getDir #userScripts) + "\\gstools\\"
    local p = root + "projects\\hw3_tools\\hw3_tools_ui.py"
    if doesFileExist p then python.ExecuteFile p
    else messageBox ("HW3 Tools script not found:\n" + p) title:"HW3 Tools"
)
