Set-Location $PSScriptRoot

$Port = 8765
$BaseUrl = "http://127.0.0.1:$Port"

$oldPreference = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
$health = Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 1
$ErrorActionPreference = $oldPreference

$connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1

if ($null -eq $connection) {
    Write-Host "JobPilot is not running." -ForegroundColor Green
    exit 0
}

$ownerPid = [int]$connection.OwningProcess

if ($null -eq $health) {
    Write-Host "Port $Port is used by PID $ownerPid, but it does not look like JobPilot." -ForegroundColor Red
    Write-Host "Nothing was terminated." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 2
}

$runningVersion = [string]$health.version
Write-Host "Stopping JobPilot $runningVersion (PID $ownerPid)..." -ForegroundColor Yellow
# 若用户开启了关闭自动同步，接口会在这里执行加密提交；未配置或失败不会阻止退出。
try { Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/sync/commit?reason=shutdown" -TimeoutSec 20 -ErrorAction SilentlyContinue | Out-Null } catch {}
Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

$remaining = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -ne $remaining) {
    Write-Host "JobPilot could not be stopped automatically." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 3
}

Write-Host "JobPilot stopped." -ForegroundColor Green
