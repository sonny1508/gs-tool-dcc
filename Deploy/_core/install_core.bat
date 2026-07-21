@echo off
:: ============================================================================
::  install_core.bat  -  shared installer used by every per-DCC install_user.bat
::
::  Each DCC's install_user.bat is a thin wrapper that just calls this with:
::      call "<path>\install_core.bat" "<source subpath>" "<destination>"
::  e.g.
::      call "...\_core\install_core.bat" "Environment\Autodesk\Maya" "%USERPROFILE%\Documents\maya"
::
::  %1 = source subpath under the GSTools root (e.g. Environment\Autodesk\Maya)
::  %2 = destination directory                (e.g. %USERPROFILE%\Documents\maya)
::
::  The GSTools root is resolved by walking up from THIS file's own location until a
::  folder containing an "Environment" subfolder is found, so wrappers never need to
::  re-implement the walk-up logic. Run on login by the domain controller:
::  the robocopy is an additive one-way update (newer/missing files only), so it is
::  safe to merge into a user folder that also holds their personal files.
:: ============================================================================
setlocal EnableDelayedExpansion

if "%~1"=="" (
    echo [ERROR] install_core: missing source subpath argument.
    exit /b 1
)
if "%~2"=="" (
    echo [ERROR] install_core: missing destination argument.
    exit /b 1
)

:: GSTools root = the nearest ancestor of THIS file that contains an "Environment"
:: subfolder. We walk up from %~dp0 instead of assuming a fixed depth, so this keeps
:: working if the Deploy tree is moved/nested differently relative to the root.
set "ROOT="
for %%I in ("%~dp0.") do set "CURRENT=%%~fI"
:find_root
if exist "%CURRENT%\Environment\" (
    set "ROOT=%CURRENT%"
    goto :found_root
)
for %%I in ("%CURRENT%\..") do set "PARENT=%%~fI"
if /I "%PARENT%"=="%CURRENT%" (
    echo [ERROR] Could not find a folder containing 'Environment' above: %~dp0
    exit /b 1
)
set "CURRENT=%PARENT%"
goto :find_root
:found_root

set "SRC=%ROOT%\%~1"
set "DST=%~2"

if not exist "%SRC%" (
    echo [ERROR] Source not found: %SRC%
    exit /b 1
)

:: Dev-only cruft that must never be deployed: VCS metadata, agent config, editor
:: settings, Python bytecode caches, and the gitignored Library/ folder. Matched by
:: bare name so they're excluded wherever they appear in the tree. Harmless for the
:: per-DCC subtree copies (which don't contain these); essential for the full-root
:: server push in install_server.bat.
set "EXCLUDE_DIRS=.git .claude .vscode .idea __pycache__ __pycache_ Library"
set "EXCLUDE_FILES=.gitignore .gitattributes *.pyc"

:: robocopy flags:
::   /E       all subdirs incl. empty      /DCOPY:DA  copy dir timestamps+attrs
::   /XO      skip files older than dest   /R:2 /W:2  light retry on locked files
::   /XD/XF   exclude the dirs/files above /NP /NFL /NDL  quiet output
robocopy "%SRC%" "%DST%" /E /DCOPY:DA /R:2 /W:2 /NP /NFL /NDL /XD %EXCLUDE_DIRS% /XF %EXCLUDE_FILES%

:: robocopy exit codes 0-7 are success/informational; >=8 is a real failure
if %ERRORLEVEL% GEQ 8 (
    echo [ERROR] robocopy failed with exit code %ERRORLEVEL%
    endlocal & exit /b %ERRORLEVEL%
)

echo [OK] Synced "%~1" -^> "%DST%"
endlocal & exit /b 0
