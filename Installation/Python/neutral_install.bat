@echo off
setlocal enabledelayedexpansion

echo ===================================
echo Python and PySide Installer
echo ===================================

:: Get the current batch file directory
set "BAT_DIR=%~dp0"
:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"
:: Source path for packages - use the current directory for now since we're having path issues
set "source_path=%GSTOOLS_ROOT%\Library\Python\Packages"
:: Fixed temp directory
set "temp_dir=C:\temp\python_packages"

echo Current directory: %BAT_DIR%
echo Using packages from: %source_path%

echo Creating temporary directory...
if not exist "%temp_dir%" mkdir "%temp_dir%"

:: Check if files exist in the source path
if not exist "%source_path%\python-3.9.13-amd64.exe" (
    echo ERROR: Python installer not found at %source_path%\python-3.9.13-amd64.exe
    echo Looking in current directory...
    if exist "%BAT_DIR%\python-3.9.13-amd64.exe" (
        set "source_path=%BAT_DIR%"
        echo Found in current directory. Using %source_path%
    ) else (
        echo ERROR: Python installer not found at %BAT_DIR%\python-3.9.13-amd64.exe
        goto cleanup
    )
)

echo Copying installation files...
echo Source: %source_path%\python-3.9.13-amd64.exe
echo Destination: %temp_dir%\python-3.9.13-amd64.exe
copy /Y "%source_path%\python-3.9.13-amd64.exe" "%temp_dir%\" || echo Copy failed: python-3.9.13-amd64.exe
copy /Y "%source_path%\PySide2-5.15.2.1-5.15.2-cp39-cp39-win_amd64.whl" "%temp_dir%\" || echo Copy failed: PySide2-5.15.2.1-5.15.2-cp39-cp39-win_amd64.whl
copy /Y "%source_path%\PySide6-6.5.2-6.5.2-cp39-cp39-win_amd64.whl" "%temp_dir%\" || echo Copy failed: PySide6-6.5.2-6.5.2-cp39-cp39-win_amd64.whl

if not exist "%temp_dir%\dependencies" mkdir "%temp_dir%\dependencies"
if exist "%source_path%\dependencies\*" (
    xcopy /Y /E "%source_path%\dependencies\*" "%temp_dir%\dependencies\" || echo Copy failed: dependencies
) else (
    echo WARNING: Dependencies directory not found at %source_path%\dependencies
    if exist "%BAT_DIR%\dependencies\*" (
        xcopy /Y /E "%BAT_DIR%\dependencies\*" "%temp_dir%\dependencies\" || echo Copy failed: dependencies
    ) else (
        echo WARNING: Dependencies not found in current directory either
    )
)

:: Check if Python installer was copied successfully
if not exist "%temp_dir%\python-3.9.13-amd64.exe" (
    echo ERROR: Failed to copy Python installer to temp directory
    goto cleanup
)

echo Installing Python 3.9...
start /wait "" "%temp_dir%\python-3.9.13-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_launcher=1

:: Check if Python was installed successfully
if not exist "C:\Program Files\Python39\python.exe" (
    echo ERROR: Python installation failed!
    goto cleanup
)

echo Setting up environment paths...
set "PYTHON_PATH=C:\Program Files\Python39"
set "PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%"

:: Update system PATH to include the Scripts directory for PySide tools
echo Adding Python and Scripts directories to system PATH...
setx PATH "%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%" /M

echo Installing PySide2...
"%PYTHON_PATH%\python.exe" -m pip install "%temp_dir%\PySide2-5.15.2.1-5.15.2-cp39-cp39-win_amd64.whl" --no-warn-script-location --no-index --find-links="%temp_dir%\dependencies"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PySide2 installation failed!
    goto cleanup
)

echo Installing PySide6...
"%PYTHON_PATH%\python.exe" -m pip install "%temp_dir%\PySide6-6.5.2-6.5.2-cp39-cp39-win_amd64.whl" --no-warn-script-location --no-index --find-links="%temp_dir%\dependencies"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PySide6 installation failed!
    goto cleanup
)

echo Verifying installations...
"%PYTHON_PATH%\python.exe" -c "import sys; print('Python Version:', sys.version)" || echo ERROR: Python verification failed
"%PYTHON_PATH%\python.exe" -c "import PySide2; print('PySide2 Version:', PySide2.__version__)" || echo ERROR: PySide2 verification failed
"%PYTHON_PATH%\python.exe" -c "import PySide6; print('PySide6 Version:', PySide6.__version__)" || echo ERROR: PySide6 verification failed

echo Installation completed successfully!
goto cleanup

:cleanup
echo Cleaning up temporary files...
rmdir /S /Q "%temp_dir%"

echo Done.
pause