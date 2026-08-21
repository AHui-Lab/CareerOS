param(
    [string]$CareerVaultHome = $env:CAREERVAULT_HOME
)

$ErrorActionPreference = 'Stop'
$JobPilotHome = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $CareerVaultHome) {
    $CareerVaultHome = Join-Path (Split-Path -Parent $JobPilotHome) 'CareerVault'
}
$CareerVaultHome = [System.IO.Path]::GetFullPath($CareerVaultHome)
$JobPilotHome = [System.IO.Path]::GetFullPath($JobPilotHome)

function Get-JsonHealth([string]$Url) {
    try {
        return Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 2
    } catch {
        return $null
    }
}

function Get-PortOwner([int]$Port) {
    try {
        $row = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        if ($row) { return [int]$row.OwningProcess }
    } catch {}
    return $null
}

function Wait-Health([string]$Url, [string]$Name, [int]$Seconds = 15) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $health = Get-JsonHealth $Url
        if ($health -and $health.ok) { return $health }
        Start-Sleep -Milliseconds 350
    } while ((Get-Date) -lt $deadline)
    throw "$Name did not become healthy within $Seconds seconds."
}

function Start-LocalService(
    [string]$Name,
    [string]$Root,
    [int]$Port,
    [string]$HealthUrl
) {
    $health = Get-JsonHealth $HealthUrl
    if ($health -and $health.ok) {
        Write-Host "[OK] $Name already running on $Port (version $($health.version))."
        return $health
    }

    $owner = Get-PortOwner $Port
    if ($owner) {
        throw "Port $Port is already occupied by PID $owner, but $Name health is unavailable. For safety CareerOS will not terminate it."
    }
    if (-not (Test-Path $Root)) {
        throw "$Name directory not found: $Root"
    }
    $python = Join-Path $Root '.venv\Scripts\python.exe'
    $runPy = Join-Path $Root 'run.py'
    if (-not (Test-Path $python)) {
        throw "$Name virtual environment not found: $python. Run install.bat in $Root first."
    }
    if (-not (Test-Path $runPy)) {
        throw "$Name run.py not found: $runPy"
    }

    Write-Host "[START] $Name from $Root"
    $command = '"' + $python + '" "' + $runPy + '"'
    Start-Process -FilePath 'cmd.exe' -ArgumentList '/k', $command -WorkingDirectory $Root | Out-Null
    return Wait-Health $HealthUrl $Name
}

Write-Host '=== CareerOS ==='
Write-Host "CareerVault: $CareerVaultHome"
Write-Host "CareerOS:    $JobPilotHome"
Write-Host ''

try {
    $cv = Start-LocalService 'CareerVault' $CareerVaultHome 8766 'http://127.0.0.1:8766/api/health'
    $jp = Start-LocalService 'CareerOS 求职管理' $JobPilotHome 8765 'http://127.0.0.1:8765/api/health'
    Write-Host ''
    Write-Host "[READY] CareerOS 已连接：经历资产 $($cv.version) <-> 求职管理 $($jp.version)"
    Write-Host '[OPEN] http://127.0.0.1:8765'
    Start-Process 'http://127.0.0.1:8765'
} catch {
    Write-Host ''
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'CareerOS did not kill any unrelated process.'
    Read-Host 'Press Enter to exit'
    exit 1
}
