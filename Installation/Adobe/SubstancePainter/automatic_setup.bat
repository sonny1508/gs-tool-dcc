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
set "source_path_users=!GSTOOLS_ROOT!\Softwares\Adobe\SubstancePainter"

:: Define source and destination paths
set "destination_path_users=%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter\python\plugins"

:: Get the IP address of this machine
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set "IP_ADDR=%%a"
    goto :ip_found
)

:ip_found
:: Remove spaces from IP address
set "IP_ADDR=%IP_ADDR: =%"
echo Found IP Address: %IP_ADDR%

:: Extract the last octet
for /f "tokens=4 delims=." %%a in ("%IP_ADDR%") do set "LAST_OCTET=%%a"
echo Last Octet: %LAST_OCTET%

:: Extract the last two digits
if %LAST_OCTET% LSS 10 (
    set "LAST_TWO_DIGITS=0%LAST_OCTET%"
) else (
    set "LAST_TWO_DIGITS=%LAST_OCTET:~-2%"
)
echo Last Two Digits: %LAST_TWO_DIGITS%

:: Set the real user to gs + last two digits
set "REAL_USER=gs%LAST_TWO_DIGITS%"

:: Fallback methods if the above doesn't work
if not exist "C:\Users\%REAL_USER%" (
    echo User %REAL_USER% not found, trying alternate detection methods
    
    :: Try to find gs* users
    for /d %%u in (C:\Users\gs*) do (
        set "REAL_USER=%%~nu"
        echo Found potential user: %REAL_USER%
        goto :user_found
    )
    
    :: Original methods as fallback
    for /f "tokens=1" %%u in ('query user ^| findstr /v "SESSIONNAME USERNAME" ^| findstr /v "Disc" ^| findstr /v "support"') do (
        set "REAL_USER=%%u"
        echo Found active user: %REAL_USER%
        goto :user_found
    )
    
    :: WMI method as last resort
    echo No active user session found, trying WMI method
    for /f "tokens=2 delims==" %%A in ('wmic computersystem get username /value ^| findstr "="') do set "TEMP_USER=%%A"
    :: Remove the domain if present (handles DOMAIN\User format)
    for /f "tokens=2 delims=\" %%A in ("%TEMP_USER%") do set "REAL_USER=%%A"
)

:user_found
:: Define source and destination paths
set "destination_path_users=C:\Users\%REAL_USER%\Documents\Adobe\Adobe Substance 3D Painter\python\plugins"

:: Debugging: Print the detected user
echo Detected user: %REAL_USER%
echo Installing to: %destination_path_users%

:: Check if user directory exists
if not exist "C:\Users\%REAL_USER%" (
    echo ERROR: User directory C:\Users\%REAL_USER% does not exist!
    exit /b 1
)

:: Create destination directories if they don't exist
mkdir "%destination_path_users%" 2>nul

:: Copy all files and subdirectories for maya
xcopy "%source_path_users%\*" "%destination_path_users%" /Y /E /I

:: Delete all existing content in the destination directory
if exist "%destination_path_users%\*" del /s /q "%destination_path_users%\*"
for /d %%i in ("%destination_path_users%\*") do rmdir /s /q "%%i"

echo Installation completed for user: %REAL_USER%