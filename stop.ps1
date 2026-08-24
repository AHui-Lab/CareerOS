Set-Location $PSScriptRoot
$ErrorActionPreference = 'Continue'
& (Join-Path $PSScriptRoot 'JobPilot\stop.ps1')
& (Join-Path $PSScriptRoot 'CareerVault\stop.ps1')
