Set-Location $PSScriptRoot
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { py -m venv .venv } else { python -m venv .venv }
& ".venv\\Scripts\\python.exe" -m pip install --upgrade pip
& ".venv\\Scripts\\python.exe" -m pip install -r requirements.txt
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
if (-not (Test-Path "data\\profile.json")) { Copy-Item "data\\profile.example.json" "data\\profile.json" }
Write-Host "JobPilot 安装完成。下一步运行 start.ps1 或 start.bat。" -ForegroundColor Green
