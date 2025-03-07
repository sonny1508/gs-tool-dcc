@echo off
setlocal

:: Get the current batch file directory
set "BAT_DIR=%~dp0"

:: Move up two levels to get to GSTools root
for %%I in ("%BAT_DIR%\..\..") do set "GSTOOLS_ROOT=%%~fI"

:: Define source and destination paths
set "source_path=%GSTOOLS_ROOT%\Library\Maya\pymel"
set "destination_path=c:\temp\Maya\pymel"

:: Check if source directory exists
if not exist "%source_path%" exit /b 1

:: Check if destination directory exists
if not exist "%destination_path%" mkdir "%destination_path%"

:: Copy all files and subdirectories
xcopy "%source_path%\*" "%destination_path%" /E /I /Y /Q

:: Install PyMel using mayapy
"C:\Program Files\Autodesk\Maya2018\bin\mayapy.exe" -m pip install --user "%destination_path%\pymel-1.5.0-py2.py3-none-any.whl"
"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe" -m pip install --user "%destination_path%\pymel-1.5.0-py2.py3-none-any.whl"
"C:\Program Files\Autodesk\Maya2023\bin\mayapy.exe" -m pip install --user "%destination_path%\pymel-1.5.0-py2.py3-none-any.whl"