@echo off
setlocal

:: Get the current batch file directory
set "BAT_DIR=%~dp0"

:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"

:: Construct the path to modules
set "source_path=%GSTOOLS_ROOT%\Softwares\Unreal\Assets"
set "destination_path_ride6=D:\Ride6\Engine\Plugins\ignition\ignitiongameplay\content\assets"
set "destination_path_screamer1=D:\SCR 1\Engine\Plugins\ignition\ignitiongameplay\content\assets"
set "destination_path_screamer1=D:\MGP25\Engine\Plugins\ignition\ignitiongameplay\content\assets"

:: Check if source directory exists
if not exist "%source_path%" exit /b 1

:: Create destination directory if it doesn't exist
if not exist "%destination_path_ride6%" mkdir "%destination_path_ride6%"
if not exist "%destination_path_screamer1%" mkdir "%destination_path_screamer1%"

:: Delete all existing content in the destination directory
:: if exist "%destination_path%\*" del /s /q "%destination_path%\*"
:: for /d %%i in ("%destination_path%\*") do rmdir /s /q "%%i"

:: Copy all files and subdirectories (including empty ones)
xcopy "%source_path%\*" "%destination_path_ride6%\" /E /I /Y
xcopy "%source_path%\*" "%destination_path_screamer1%\" /E /I /Y
