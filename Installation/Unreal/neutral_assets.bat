@echo off
setlocal enabledelayedexpansion
:: Get the current batch file directory
set "BAT_DIR=%~dp0"
:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"
:: Source path for assets
set "source_path=%GSTOOLS_ROOT%\Softwares\Unreal\Assets"
:: Common path structure for all games
set "common_path=Engine\Plugins\ignition\ignitiongameplay\content\assets"
:: Define games and their base directories
set "games_count=3"
set "game[1]=Ride6"
set "game[2]=SCR 1"
set "game[3]=MGP25"
set "basedir[1]=D:\Ride6"
set "basedir[2]=D:\SCR 1"
set "basedir[3]=D:\MGP25"

:: Ensure source_path doesn't have a trailing backslash
if "%source_path:~-1%" == "\" set "source_path=%source_path:~0,-1%"

:: Check if source directory exists
if not exist "%source_path%" (
    echo Source directory does not exist: %source_path%
    exit /b 1
)

:: Process each game
for /L %%i in (1,1,%games_count%) do (
    set "destination_base=!basedir[%%i]!\%common_path%"
    
    echo Processing !game[%%i]! at !destination_base!
    
    :: Create destination base directory if it doesn't exist
    if not exist "!destination_base!" (
        mkdir "!destination_base!"
        echo Created base directory: !destination_base!
    )
    
    :: Copy files with directory structure
    echo Copying files from %source_path% to !destination_base!...
    
    :: Use xcopy instead of manual directory creation + copy
    xcopy "%source_path%" "!destination_base!" /E /I /Y
    
    echo Finished processing !game[%%i]!
    echo.
)

echo All operations completed successfully.
endlocal