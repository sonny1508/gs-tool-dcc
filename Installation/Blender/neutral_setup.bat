@echo off
setlocal enabledelayedexpansion

:: Get the current batch file directory
set "BAT_DIR=%~dp0"

:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"

:: Define source and destination paths
set "server_path=%GSTOOLS_ROOT%\Softwares\Blender"
set "blender_local_path=%APPDATA%\Blender Foundation\Blender"

echo Looking for startup_script.py files to copy...
echo Server path: %server_path%
echo Local path: %blender_local_path%

if not exist "%server_path%" (
    echo Error: Server path %server_path% does not exist!
    pause
    exit /b 1
)

:: Create local blender path if it doesn't exist
if not exist "%blender_local_path%" (
    echo Creating directory: %blender_local_path%
    mkdir "%blender_local_path%"
)

:: Find and copy only startup.py files
set "found_files=0"

for /r "%server_path%" %%F in (startup.py) do (
    set "source_file=%%F"
    
    :: Get the relative path from server_path to the file
    set "rel_path=!source_file:%server_path%=!"
    
    :: Create the destination path
    set "dest_file=%blender_local_path%!rel_path!"
    
    :: Create the destination directory if it doesn't exist
    set "dest_dir=%%~dpF"
    set "local_dir=%blender_local_path%!dest_dir:%server_path%=!"
    
    if not exist "!local_dir!" (
        echo Creating directory: !local_dir!
        mkdir "!local_dir!"
    )
    
    :: Copy the file
    echo Copying: !source_file! 
    echo To: !dest_file!
    copy "!source_file!" "!dest_file!" /Y >nul
    
    if !errorlevel! neq 0 (
        echo Error copying !source_file!
    ) else (
        echo Successfully copied startup_script.py
        set /a found_files+=1
    )
    echo.
)

if !found_files! equ 0 (
    echo No startup_script.py files found in %server_path%
    pause
    exit /b 1
) else (
    echo Successfully copied !found_files! startup_script.py file(s).
    echo This is a one-time setup. The startup script will now reference server paths when Blender starts.
)

echo.
echo Setup completed.
echo.

endlocal