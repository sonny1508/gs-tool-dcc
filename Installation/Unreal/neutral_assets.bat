@echo off
setlocal enabledelayedexpansion
:: Get the current batch file directory
set "BAT_DIR=%~dp0"
:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"
:: Source path for assets
set "source_path=%GSTOOLS_ROOT%\Environment\Unreal\Assets"
:: Common path structure for all games
set "common_path=Engine\Plugins\ignition\ignitiongameplay\content\assets"
:: Define games and their folder names (without drive letter)
set "games_count=4"
set "game[1]=Ride6"
set "game[2]=unrealProjects\SCR1"
set "game[3]=MGP25"
set "game[4]=unrealProjects\HW3"

:: Define drives to scan
set "drives=D E G T"

:: Ensure source_path doesn't have a trailing backslash
if "%source_path:~-1%" == "\" set "source_path=%source_path:~0,-1%"

:: Check if source directory exists
if not exist "%source_path%" (
    echo Source directory does not exist: %source_path%
    exit /b 1
)

:: Process each game
for /L %%i in (1,1,%games_count%) do (
    echo Processing !game[%%i]!...
    set "found_folder=0"
    
    :: Check each drive for the game folder
    for %%d in (%drives%) do (
        set "game_dir=%%d:\!game[%%i]!"
        if exist "!game_dir!" (
            echo Found !game[%%i]! at !game_dir!
            set "destination_base=!game_dir!\%common_path%"
            
            :: Create destination base directory if it doesn't exist
            if not exist "!destination_base!" (
                mkdir "!destination_base!"
                echo Created base directory: !destination_base!
            )
            
            :: Delete existing files in specific subfolders
            echo Deleting existing files in GSTools and UnrealToolKit2\Scripts folders...
            if exist "!destination_base!\GSTools" (
                echo Removing files in !destination_base!\GSTools
                rd /s /q "!destination_base!\GSTools"
            )
            if exist "!destination_base!\UnrealToolKit2\Scripts" (
                echo Removing files in !destination_base!\UnrealToolKit2\Scripts
                rd /s /q "!destination_base!\UnrealToolKit2\Scripts"
            )
            
            :: Copy files with directory structure
            echo Copying files from %source_path% to !destination_base!...
            xcopy "%source_path%" "!destination_base!" /E /I /Y
            
            set "found_folder=1"
        )
    )
    
    if !found_folder!==0 (
        echo !game[%%i]! not found on any of the specified drives.
    )
    
    echo Finished processing !game[%%i]!
    echo.
)

echo All operations completed successfully.
endlocal