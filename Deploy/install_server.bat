@echo off
:: Maya user install - thin wrapper. All logic lives in _core\install_core.bat.
:: Source: <root>\Environment\Autodesk\Maya   Dest: %USERPROFILE%\Documents\maya
call "%~dp0\_core\install_core.bat" "\" "\\192.168.1.210\Pipeline\gs-tool-dcc"
exit /b %ERRORLEVEL%
