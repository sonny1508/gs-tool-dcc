@echo off
setlocal EnableDelayedExpansion

:: Get the current batch file directory
set "BAT_DIR=%~dp0"
set "CURRENT_DIR=%BAT_DIR%"

:: Navigate up until we find GSTools directory
:find_gstools
for %%I in ("!CURRENT_DIR!") do set "PARENT_DIR=%%~dpI"
set "PARENT_DIR=!PARENT_DIR:~0,-1!"

for %%I in ("!PARENT_DIR!") do set "FOLDER_NAME=%%~nxI"
if "!FOLDER_NAME!"=="GSTools" (
    :: Found GSTools, set GSTOOLS_ROOT to its parent directory
    for %%J in ("!PARENT_DIR!") do set "GSTOOLS_ROOT=%%~dpJ"
    set "GSTOOLS_ROOT=!GSTOOLS_ROOT:~0,-1!"
    goto :found_gstools
)

:: Check if we're already in GSTools directory
for %%I in ("!CURRENT_DIR:~0,-1!") do set "CURRENT_FOLDER=%%~nxI"
if "!CURRENT_FOLDER!"=="GSTools" (
    for %%J in ("!CURRENT_DIR!") do set "GSTOOLS_ROOT=%%~dpJ"
    set "GSTOOLS_ROOT=!GSTOOLS_ROOT:~0,-1!"
    goto :found_gstools
)

:: Not found yet, move up one directory and try again
if "!PARENT_DIR!"=="!CURRENT_DIR!" (
    echo GSTools directory not found in parent path.
    exit /b 1
)
set "CURRENT_DIR=!PARENT_DIR!"
goto :find_gstools

:found_gstools
:: Define source and destination paths based on the directory structure you showed
set "source_path=!GSTOOLS_ROOT!\Library\Maya\pymel"
set "destination_path=C:\temp\Maya\pymel"

:: Check if source directory exists
if not exist "%source_path%" (
    echo Source directory not found: "%source_path%"
    exit /b 1
)

:: Check if destination directory exists
if not exist "%destination_path%" (
    echo Creating destination directory: "%destination_path%"
    mkdir "%destination_path%"
)

:: Copy all files and subdirectories
echo Copying PyMel files to "%destination_path%"...
xcopy "%source_path%\*" "%destination_path%" /E /I /Y /Q

:: Define Maya versions to check
set "maya_versions=2018 2022 2023"

:: Install PyMel for each available Maya version
for %%v in (%maya_versions%) do (
    set "maya_path=C:\Program Files\Autodesk\Maya%%v\bin\mayapy.exe"
    
    if exist "!maya_path!" (
        echo Installing PyMel for Maya %%v...
        "!maya_path!" -m pip install "%destination_path%\pymel-1.5.0-py2.py3-none-any.whl"
        if !errorlevel! neq 0 (
            echo Warning: Installation for Maya %%v failed with error code !errorlevel!
        ) else (
            echo Installation for Maya %%v completed successfully.
        )
    ) else (
        echo Maya %%v not found, skipping installation.
    )
)

echo PyMel installation process completed.