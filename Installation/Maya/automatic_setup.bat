@echo off
setlocal

:: Get the current batch file directory
set "BAT_DIR=%~dp0"

:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"

:: Construct the path to application plugins
set "source_path_autodesk=%GSTOOLS_ROOT%\Softwares\Autodesk\ApplicationPlugins"

:: Construct the path to user setup
set "source_path_users=%GSTOOLS_ROOT%\Softwares\Autodesk\Maya"

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
set "destination_path_users=C:\Users\%REAL_USER%\Documents\maya"

:: Define source and destination paths
set "destination_path_autodesk=C:\ProgramData\Autodesk\ApplicationPlugins"

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

:: Copy all files and subdirectories for autodesk
xcopy "%source_path_autodesk%\*" "%destination_path_autodesk%" /Y /E /I

echo Installation completed for user: %REAL_USER%