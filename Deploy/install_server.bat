@echo off
:: Server push - thin wrapper. All logic lives in _core\install_core.bat.
:: Pushes the whole GSTools root to the server share. Dev-only cruft (.git, .claude,
:: editor/config folders, __pycache__, *.pyc, Library) is excluded by install_core.
:: Source: <root>   Dest: \\192.168.1.210\Pipeline\Tool\gs-tool-dcc
call "%~dp0\_core\install_core.bat" "\" "\\192.168.1.210\Pipeline\Tool\gs-tool-dcc"
exit /b %ERRORLEVEL%
