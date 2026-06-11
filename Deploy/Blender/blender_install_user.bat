@echo off
:: DCC user install - thin wrapper. All logic lives in _core\install_core.bat.
:: Source: <root>\Environment\...   Dest: %USERPROFILE%\...
call "%~dp0..\_core\install_core.bat" "Environment\Blender" "%USERPROFILE%\AppData\Roaming\Blender Foundation\Blender"
exit /b %ERRORLEVEL%
