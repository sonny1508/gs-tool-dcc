@echo off
setlocal enabledelayedexpansion

:: Get the current batch file directory
set "BAT_DIR=%~dp0"

:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"

:: Define source and paths
set "source_path=%GSTOOLS_ROOT%\Library\Blender\opencv"
set "blender_base_path=%APPDATA%\Blender Foundation\Blender"

echo Installing OpenCV for Blender...
echo Source: %source_path%

:: Check if source directory exists
if not exist "%source_path%" (
    echo Error: Source directory does not exist!
    pause
    exit /b 1
)

:: Check if cv2.zip exists
set "zip_path=%source_path%\cv2.zip"
if not exist "%zip_path%" (
    echo Error: cv2.zip not found in %source_path%
    pause
    exit /b 1
)

:: Check if Blender base path exists
if not exist "%blender_base_path%" (
    echo Blender directory not found. Creating directory for version 3.6 only.
    mkdir "%blender_base_path%\3.6\scripts\modules"
    set "found_versions=3.6"
) else (
    :: Look for Blender version directories
    set "found_versions="
    set "found_any=false"
    
    :: Check for specific version directories
    for /d %%D in ("%blender_base_path%\*") do (
        :: Extract the version number from the directory name
        for %%I in ("%%~nxD") do set "version=%%~nxI"
        
        :: Check if the directory is a version number (should at least have a digit)
        echo !version! | findstr /R "[0-9]" >nul
        if not errorlevel 1 (
            :: Only add if scripts\modules exists or we can create it
            if exist "%%D\scripts\modules" (
                set "found_versions=!found_versions! !version!"
                set "found_any=true"
            ) else (
                :: Create the scripts\modules directory for this version
                mkdir "%%D\scripts\modules"
                set "found_versions=!found_versions! !version!"
                set "found_any=true"
            )
        )
    )
    
    :: If no version directories were found, default to 3.6
    if "!found_any!"=="false" (
        echo No Blender version directories found. Creating directory for version 3.6.
        mkdir "%blender_base_path%\3.6\scripts\modules"
        set "found_versions=3.6"
    )
)

:: Install for each found Blender version
echo Found Blender versions:!found_versions!

for %%V in (!found_versions!) do (
    set "version_path=%blender_base_path%\%%V\scripts\modules"
    
    echo Installing OpenCV for Blender %%V...
    
    :: Remove existing cv2 directory if it exists
    if exist "!version_path!\cv2" (
        echo Removing existing cv2 directory from Blender %%V...
        rmdir /s /q "!version_path!\cv2"
    )
    
    :: Extract the ZIP file directly to the modules directory
    echo Extracting cv2.zip to Blender %%V modules directory...
    powershell -command "Expand-Archive -Path '%zip_path%' -DestinationPath '!version_path!' -Force"
    
    if !errorlevel! neq 0 (
        echo Failed to extract cv2.zip to Blender %%V.
    ) else (
        echo OpenCV installation for Blender %%V completed.
    )
    echo.
)

echo OpenCV installation completed for all found Blender versions.
echo.

endlocal