Set-Location $PSScriptRoot

$Port = 8766
$BaseUrl = "http://127.0.0.1:$Port"

$oldPreference = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
$health = Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 1
$connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
$ErrorActionPreference = $oldPreference

if ($null -eq $connection) {
    Write-Host "CareerVault is not running on port $Port." -ForegroundColor Yellow
    exit 0
}

$pidToStop = [int]$connection.OwningProcess

if ($null -eq $health) {
    Write-Host "Port $Port is owned by PID $pidToStop, but it does not look like CareerVault." -ForegroundColor Red
    Write-Host "For safety, this script will not terminate it." -ForegroundColor Yellow
    exit 2
}

Write-Host "Stopping CareerVault $($health.version) (PID $pidToStop)..." -ForegroundColor Yellow
Stop-Process -Id $pidToStop -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 400
Write-Host "CareerVault stopped." -ForegroundColor Green
