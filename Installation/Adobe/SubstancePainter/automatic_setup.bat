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

:: Construct the path to user setup
set "source_path_users=!GSTOOLS_ROOT!\Environment\Adobe\SubstancePainter"

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

:user_found
:: Define destination path
set "destination_path_users=C:\Users\%REAL_USER%\Documents\Adobe\Adobe Substance 3D Painter"

:: Check if user directory exists
if not exist "C:\Users\%REAL_USER%" (
    echo ERROR: User directory C:\Users\%REAL_USER% does not exist!
    exit /b 1
)

:: Create destination directories if they don't exist
if not exist "%destination_path_users%" (
    mkdir "%destination_path_users%" 2>nul
    if errorlevel 1 (
        echo ERROR: Failed to create destination directory!
        exit /b 1
    )
)

:: Check if source directory exists
if not exist "%source_path_users%" (
    echo ERROR: Source directory not found: %source_path_users%
    exit /b 1
)

:: Copy all files and subdirectories
echo Copying files from %source_path_users% to %destination_path_users%...
xcopy "%source_path_users%\*" "%destination_path_users%" /Y /E /I

echo Installation completed successfully for user: %REAL_USER%