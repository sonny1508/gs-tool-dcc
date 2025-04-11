@echo off
setlocal EnableDelayedExpansion

:: Get the current batch file directory
set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=!CURRENT_DIR:~0,-1!"  :: Remove trailing backslash

:: Loop to find GSTools root directory
:find_gstools
for %%I in ("!CURRENT_DIR!") do set "DIRNAME=%%~nxI"
if /i "!DIRNAME!"=="GSTools" (
    set "GSTOOLS_ROOT=!CURRENT_DIR!"
    goto :found_gstools
)

:: Check if we've reached the drive root
if "!CURRENT_DIR:~-2!"==":" (
    echo GSTools directory not found.
    exit /b 1
)

:: Move up one directory level
for %%I in ("!CURRENT_DIR!\.") do set "CURRENT_DIR=%%~dpI"
set "CURRENT_DIR=!CURRENT_DIR:~0,-1!"  :: Remove trailing backslash
goto :find_gstools

:found_gstools
echo Found GSTools at: !GSTOOLS_ROOT!

:: Continue with the rest of your script using GSTOOLS_ROOT
:: Construct the path to user setup
set "source_path_users=!GSTOOLS_ROOT!\Softwares\Adobe\SubstancePainter\python\plugins"

:: Define source and destination paths
set "destination_path_users=%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter\python\plugins"

:: Check if source directory exists
if not exist "%source_path_users%" exit /b 1

:: Create destination directory if it doesn't exist
mkdir "%destination_path_users%" 2>nul

:: Delete all existing content in the destination directory
if exist "%destination_path_users%\*" del /s /q "%destination_path_users%\*"
for /d %%i in ("%destination_path_users%\*") do rmdir /s /q "%%i"

:: Copy all files and subdirectories for maya
xcopy "%source_path_users%\*" "%destination_path_users%" /Y /E /I