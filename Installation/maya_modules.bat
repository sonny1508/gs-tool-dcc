@echo off
setlocal

:: Define source and destination paths
set "source_path=\\192.168.1.10\Softwares\GSTools\Softwares\Maya\modules"
set "destination_path=%USERPROFILE%\Documents\maya\modules"

:: Check if source directory exists
if not exist "%source_path%" exit /b 1

:: Create destination directory if it doesn't exist
mkdir "%destination_path%" 2>nul

:: Delete all existing content in the destination directory
if exist "%destination_path%\*" del /s /q "%destination_path%\*"
for /d %%i in ("%destination_path%\*") do rmdir /s /q "%%i"

:: Copy all files and subdirectories
xcopy "%source_path%\*" "%destination_path%"