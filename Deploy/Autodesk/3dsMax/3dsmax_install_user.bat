@echo off
:: 3ds Max user install - thin wrapper. All logic lives in _core\install_core.bat.
:: Source: <root>\Environment\Autodesk\3dsMax   Dest: %USERPROFILE%\AppData\Local\Autodesk\3dsMax
call "%~dp0..\..\_core\install_core.bat" "Environment\Autodesk\3dsMax" "%USERPROFILE%\AppData\Local\Autodesk\3dsMax"
exit /b %ERRORLEVEL%
