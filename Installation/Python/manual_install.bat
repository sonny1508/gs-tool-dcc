@echo off
setlocal enabledelayedexpansion

echo ===================================
echo Python and PySide Installer
echo ===================================

:: Get the current batch file directory
set "BAT_DIR=%~dp0"
:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"
:: Source path for packages
set "source_path=%GSTOOLS_ROOT%\Library\Python\Packages"
:: Temp directory for installation
set "temp_dir=%TEMP%\pyside_install"

echo Creating temporary directory...
if not exist "%temp_dir%" mkdir "%temp_dir%"

echo Copying installation files...
xcopy /Y "%source_path%\python-3.9.13-amd64.exe" "%temp_dir%\"
xcopy /Y "%source_path%\PySide2-5.15.2.1-5.15.2-cp39-cp39-win_amd64.whl" "%temp_dir%\"
xcopy /Y "%source_path%\PySide6-6.5.2-6.5.2-cp39-cp39-win_amd64.whl" "%temp_dir%\"
if not exist "%temp_dir%\dependencies" mkdir "%temp_dir%\dependencies"
xcopy /Y /E "%source_path%\dependencies\*" "%temp_dir%\dependencies\"

echo Installing Python 3.9...
start /wait "" "%temp_dir%\python-3.9.13-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1

:: Check if Python was installed successfully
if not exist "C:\Program Files\Python39\python.exe" (
    echo Python installation failed!
    goto cleanup
)

echo Setting up environment paths...
set "PYTHON_PATH=C:\Program Files\Python39"
set "PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%"

echo Installing PySide2...
"%PYTHON_PATH%\python.exe" -m pip install "%temp_dir%\PySide2-5.15.2.1-5.15.2-cp39-cp39-win_amd64.whl" --no-index --find-links="%temp_dir%\dependencies"
if %ERRORLEVEL% NEQ 0 (
    echo PySide2 installation failed!
    goto cleanup
)

echo Installing PySide6...
"%PYTHON_PATH%\python.exe" -m pip install "%temp_dir%\PySide6-6.5.2-6.5.2-cp39-cp39-win_amd64.whl" --no-index --find-links="%temp_dir%\dependencies"
if %ERRORLEVEL% NEQ 0 (
    echo PySide6 installation failed!
    goto cleanup
)

echo Verifying installations...
"%PYTHON_PATH%\python.exe" -c "import sys; print('Python Version:', sys.version)"
"%PYTHON_PATH%\python.exe" -c "import PySide2; print('PySide2 Version:', PySide2.__version__)"
"%PYTHON_PATH%\python.exe" -c "import PySide6; print('PySide6 Version:', PySide6.__version__)"

echo Installation completed successfully!
goto cleanup

:cleanup
echo Cleaning up temporary files...
rmdir /S /Q "%temp_dir%"

echo Done.
pause