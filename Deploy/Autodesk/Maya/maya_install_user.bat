@echo off
:: Maya user install - thin wrapper. All logic lives in _core\install_core.bat.
:: Source: <root>\Environment\Autodesk\Maya   Dest: %USERPROFILE%\Documents\maya
call "%~dp0..\..\_core\install_core.bat" "Environment\Autodesk\Maya" "%USERPROFILE%\Documents\maya"
exit /b %ERRORLEVEL%
