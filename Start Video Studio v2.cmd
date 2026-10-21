@echo off
setlocal
wsl.exe --cd "%~dp0." python3 -m studio_v2 menu
if errorlevel 1 pause
