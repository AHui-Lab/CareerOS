@echo off
cd /d %~dp0
where py >nul 2>nul
if %errorlevel%==0 (
  py -m venv .venv
) else (
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env >nul
if not exist data\profile.json copy data\profile.example.json data\profile.json >nul
echo.
echo JobPilot installation complete.
echo Run start.bat next.
pause
