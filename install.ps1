Set-Location $PSScriptRoot
$ErrorActionPreference = 'Stop'

function Install-Module([string]$Name, [string]$Root) {
    Write-Host "[INSTALL] $Name" -ForegroundColor Cyan
    if (-not (Test-Path (Join-Path $Root '.venv\Scripts\python.exe'))) {
        $py = Get-Command py -ErrorAction SilentlyContinue
        if ($py) { & py -3 -m venv (Join-Path $Root '.venv') }
        else { & python -m venv (Join-Path $Root '.venv') }
    }
    $python = Join-Path $Root '.venv\Scripts\python.exe'
    if (-not (Test-Path $python)) { throw "$Name Python environment creation failed: $python" }
    & $python -m pip install --upgrade pip
    & $python -m pip install -r (Join-Path $Root 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw "$Name dependency installation failed." }
}

Install-Module 'CareerVault' (Join-Path $PSScriptRoot 'CareerVault')
Install-Module 'JobPilot' (Join-Path $PSScriptRoot 'JobPilot')

if (-not (Test-Path 'JobPilot\.env') -and (Test-Path 'JobPilot\.env.example')) { Copy-Item 'JobPilot\.env.example' 'JobPilot\.env' }
Write-Host ''
Write-Host '[DONE] CareerOS installation complete. Run start.bat next.' -ForegroundColor Green
