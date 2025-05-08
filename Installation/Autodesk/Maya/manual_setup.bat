@echo off
setlocal

:: Get the current batch file directory
set "BAT_DIR=%~dp0"

:: Move up to get to GSTools root
for %%I in ("%BAT_DIR%\..\..\..") do set "GSTOOLS_ROOT=%%~fI"

:: Construct the path to application plugins
set "source_path_autodesk=%GSTOOLS_ROOT%\Environment\Autodesk\ApplicationPlugins"

:: Construct the path to user setup
set "source_path_users=%GSTOOLS_ROOT%\Environment\Autodesk\Maya"

:: Define source and destination paths
set "destination_path_autodesk=C:\ProgramData\Autodesk\ApplicationPlugins"

:: Define source and destination paths
set "destination_path_users=%USERPROFILE%\Documents\maya"

:: Check if source directory exists
if not exist "%source_path_users%" exit /b 1

:: Create destination directory if it doesn't exist
mkdir "%destination_path_users%" 2>nul

:: Delete all existing content in the destination directory
:: if exist "%destination_path_modules%\*" del /s /q "%destination_path_modules%\*"
:: for /d %%i in ("%destination_path_modules%\*") do rmdir /s /q "%%i"

:: Copy all files and subdirectories for maya
xcopy "%source_path_users%\*" "%destination_path_users%" /Y /E /I

:: Copy all files and subdirectories for autodesk
xcopy "%source_path_autodesk%\*" "%destination_path_autodesk%" /Y /E /I