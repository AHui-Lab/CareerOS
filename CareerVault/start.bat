@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo CareerVault is not installed yet. Running install.bat...
  call install.bat
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
if errorlevel 1 pause
