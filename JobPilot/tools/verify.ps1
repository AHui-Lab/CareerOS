$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Missing .venv. Run install.bat first."
}

Write-Host "[1/4] Compile Python" -ForegroundColor Cyan
& $Python -m compileall -q jobpilot tests run.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/4] Run unit tests" -ForegroundColor Cyan
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Node = Get-Command node -ErrorAction SilentlyContinue
if ($Node) {
    Write-Host "[3/4] Check JobPilot browser JavaScript" -ForegroundColor Cyan
    node --check jobpilot/static/app.js
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "[4/4] Check extension JavaScript" -ForegroundColor Cyan
    node --check extension/popup.js
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "[3/4] Node.js not found; skipped JS syntax checks." -ForegroundColor Yellow
    Write-Host "[4/4] Node.js not found; skipped extension syntax check." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "JobPilot verification passed." -ForegroundColor Green
