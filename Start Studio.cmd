@echo off
setlocal
wsl.exe --cd "%~dp0." python3 studio.py menu
if errorlevel 1 pause
