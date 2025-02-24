@echo off
setlocal

:: Define source and destination paths
set "source_path=\\192.168.1.10\Softwares\GSTools\Library\Maya\pymel"
set "destination_path=%USERPROFILE%\Documents\maya\pymel"

:: Check if source directory exists
if not exist "%source_path%" exit /b 1

:: Check if destination directory exists
if not exist "%destination_path%" mkdir "%destination_path%"

:: Copy all files and subdirectories
xcopy "%source_path%\*" "%destination_path%" /E /I /Y /Q

:: Install PyMel using mayapy
"C:\Program Files\Autodesk\Maya2023\bin\mayapy.exe" -m pip install "%destination_path%\pymel-1.5.0-py2.py3-none-any.whl"