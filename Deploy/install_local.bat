@echo off
:: Local install - runs every per-DCC user installer in one go: each
:: *_install_user.bat under Autodesk\, Blender\ and Adobe\, found by name, so a new
:: DCC's wrapper is picked up without touching this file.
::
:: Every installer copies from the tree it sits in (install_core walks up to the
:: nearest folder holding Environment\). Run this from the share for the published
:: tools, or from a working copy to try changes on this machine without publishing.
setlocal

set "FAILED=0"
:: FOR /R can't take a FOR variable as its root, so each folder goes through :run_all.
for %%D in (Autodesk Blender Adobe) do call :run_all "%~dp0%%D"

echo.
if %FAILED% GTR 0 (
    echo [ERROR] %FAILED% installer^(s^) failed - see above.
    set "RESULT=1"
) else (
    echo [OK] Every DCC installed.
    set "RESULT=0"
)

:: Keep the window open when started by double-click, so the result can be read.
echo %CMDCMDLINE% | "%SystemRoot%\System32\find.exe" /i "%~nx0" >nul && pause
endlocal & exit /b %RESULT%


:run_all
:: %1 = a DCC family folder under Deploy\ (Autodesk, Blender, Adobe)
if not exist "%~1\" exit /b 0
for /r "%~1" %%F in (*_install_user.bat) do call :run_one "%%F"
exit /b 0


:run_one
:: %1 = one per-DCC installer
echo.
echo === %~nx1
call "%~1"
if errorlevel 1 (
    echo [FAILED] %~nx1
    set /a FAILED+=1
)
exit /b 0
