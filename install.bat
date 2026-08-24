@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
  echo.
  echo [ERROR] 安装失败，请根据上面的提示排查。
  pause
  exit /b 1
)
echo.
pause
