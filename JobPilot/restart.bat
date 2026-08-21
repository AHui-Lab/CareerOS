@echo off
cd /d "%~dp0"
set JOBPILOT_FORCE_RESTART=1
call "%~dp0start.bat"
