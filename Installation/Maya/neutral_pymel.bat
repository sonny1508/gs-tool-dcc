@echo off
setlocal EnableDelayedExpansion

:: Get the current batch file directory
set "BAT_DIR=%~dp0"

:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"

:: Define source and destination paths
set "source_path=%GSTOOLS_ROOT%\Library\Maya\pymel"
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
        "!maya_path!" -m pip install --user "%destination_path%\pymel-1.5.0-py2.py3-none-any.whl"
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