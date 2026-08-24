Set-Location $PSScriptRoot
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'JobPilot\career-os.ps1')
exit $LASTEXITCODE
