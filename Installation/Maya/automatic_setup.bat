@echo off
setlocal

:: Get the current batch file directory
set "BAT_DIR=%~dp0"

:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"

:: Construct the path to user setup 2018
set "source_path_users2018=%GSTOOLS_ROOT%\Softwares\Maya\2018"

:: Construct the path to application plugins
set "source_path_applicationplugins=%GSTOOLS_ROOT%\Softwares\Maya\ApplicationPlugins"

:: Construct the path to modules
set "source_path_modules=%GSTOOLS_ROOT%\Softwares\Maya\modules"

:: Get the active user by finding the user with an explorer.exe process
for /f "tokens=1" %%u in ('query user ^| findstr /v "SESSIONNAME USERNAME" ^| findstr /v "Disc" ^| findstr /v "support"') do (
    set "REAL_USER=%%u"
    goto :user_found
)

:user_found
:: If no user was found, use a fallback method
if "%REAL_USER%"=="" (
    echo No active user session found, trying WMI method
    for /f "tokens=2 delims==" %%A in ('wmic computersystem get username /value ^| findstr "="') do set "TEMP_USER=%%A"
    :: Remove the domain if present (handles DOMAIN\User format)
    for /f "tokens=2 delims=\" %%A in ("%TEMP_USER%") do set "REAL_USER=%%A"
)

:: Define source and destination paths
set "destination_path_users2018=C:\Users\%REAL_USER%\Documents\maya\2018"
set "destination_path_applicationplugins=C:\ProgramData\Autodesk\ApplicationPlugins"
set "destination_path_modules=C:\Users\%REAL_USER%\Documents\maya\modules"

:: Debugging: Print the detected user
echo Detected user: %REAL_USER%
echo Installing to: %destination_path_users2018%

:: Check if user directory exists
if not exist "C:\Users\%REAL_USER%" (
    echo ERROR: User directory does not exist for %REAL_USER%
    exit /b 1
)

:: Check if source directory exists
if not exist "%source_path_modules%" (
    echo ERROR: Source directory %source_path_modules% does not exist
    exit /b 1
)

:: Create destination directories if they don't exist
mkdir "%destination_path_users2018%" 2>nul
mkdir "%destination_path_modules%" 2>nul

:: Delete all existing content in the destination directory
if exist "%destination_path_modules%\*" del /s /q "%destination_path_modules%\*"
for /d %%i in ("%destination_path_modules%\*") do rmdir /s /q "%%i"

:: Copy all files and subdirectories
echo Copying user files...
xcopy "%source_path_users2018%\*" "%destination_path_users2018%" /Y /E /I

echo Copying application plugins...
xcopy "%source_path_applicationplugins%\*" "%destination_path_applicationplugins%" /Y /E /I

echo Copying modules...
xcopy "%source_path_modules%\*" "%destination_path_modules%" /Y /E /I

echo Installation completed for user: %REAL_USER%