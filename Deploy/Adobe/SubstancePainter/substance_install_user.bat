@echo off
:: DCC user install - thin wrapper. All logic lives in _core\install_core.bat.
:: Source: <root>\Environment\...   Dest: %USERPROFILE%\...
call "%~dp0..\..\_core\install_core.bat" "Environment\Adobe\SubstancePainter" "%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter"
exit /b %ERRORLEVEL%