@echo off
setlocal

:: Get the current batch file directory
set "BAT_DIR=%~dp0"

:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"

:: Construct the path to user setup 2018
set "source_path_users2018=%GSTOOLS_ROOT%\Softwares\Maya\2018"

:: Construct the path to application plugins
set "source_path_applicationplugins=%GSTOOLS_ROOT%\Softwares\Maya\ApplicationPlugins"

:: Construct the path to modules
set "source_path_modules=%GSTOOLS_ROOT%\Softwares\Maya\modules"

:: Define source and destination paths
set "destination_path_users2018=%USERPROFILE%\Documents\maya\2018"

set "destination_path_applicationplugins=C:\ProgramData\Autodesk\ApplicationPlugins"

set "destination_path_modules=%USERPROFILE%\Documents\maya\modules"

:: Check if source directory exists
if not exist "%source_path_modules%" exit /b 1

:: Create destination directory if it doesn't exist
mkdir "%destination_path_modules%" 2>nul

:: Delete all existing content in the destination directory
if exist "%destination_path_modules%\*" del /s /q "%destination_path_modules%\*"
for /d %%i in ("%destination_path_modules%\*") do rmdir /s /q "%%i"

:: Copy all files and subdirectories
xcopy "%source_path_users2018%\*" "%destination_path_users2018%" /Y /E /I

xcopy "%source_path_applicationplugins%\*" "%destination_path_applicationplugins%" /Y /E /I

xcopy "%source_path_modules%\*" "%destination_path_modules%" /Y /E /I

