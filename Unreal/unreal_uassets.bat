@echo off
setlocal

:: Define source and destination paths
set "source_path=\\192.168.1.10\Softwares\Technical_Script\Unreal\Tools"
set "destination_path=G:\Ride6\Engine\Plugins\ignition\ignitiongameplay\content\assets\GlendaStudio"

:: Check if source directory exists
if not exist "%source_path%" exit /b 1

:: Create destination directory if it doesn't exist
if not exist "%destination_path%" mkdir "%destination_path%"

:: Delete all existing content in the destination directory
if exist "%destination_path%\*" del /s /q "%destination_path%\*"
for /d %%i in ("%destination_path%\*") do rmdir /s /q "%%i"

:: Copy all files and subdirectories (including empty ones)
xcopy "%source_path%\*" "%destination_path%\" /E /I /Y

