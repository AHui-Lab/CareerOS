Set-Location $PSScriptRoot

$ExpectedVersion = "0.2.0"
$Port = 8766
$PythonExe = ".venv\Scripts\python.exe"
$BaseUrl = "http://127.0.0.1:$Port"
$ForceRestart = $env:CAREERVAULT_FORCE_RESTART -eq "1"

if (-not (Test-Path $PythonExe)) {
    Write-Host "CareerVault is not installed. Please run install.bat first." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

function Get-CareerVaultHealth {
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $result = Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 1
    $ErrorActionPreference = $oldPreference
    return $result
}

function Get-PortOwnerPid {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $connection) {
        return [int]$connection.OwningProcess
    }
    return $null
}

function Wait-PortFree {
    param([int]$Seconds = 4)
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        if ($null -eq (Get-PortOwnerPid)) {
            return $true
        }
        Start-Sleep -Milliseconds 200
    }
    return $false
}

$health = Get-CareerVaultHealth
$listenerPid = Get-PortOwnerPid

if ($null -ne $health) {
    $runningVersion = [string]$health.version

    if (($runningVersion -eq $ExpectedVersion) -and (-not $ForceRestart)) {
        Write-Host "CareerVault $ExpectedVersion is already running. Opening it now." -ForegroundColor Green
        Start-Process $BaseUrl
        exit 0
    }

    if ($null -eq $listenerPid) {
        Write-Host "A CareerVault service answered health check, but its process could not be located." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 2
    }

    Write-Host "Stopping existing CareerVault $runningVersion (PID $listenerPid)..." -ForegroundColor Yellow
    Stop-Process -Id $listenerPid -Force -ErrorAction SilentlyContinue

    if (-not (Wait-PortFree 4)) {
        Write-Host "Could not release port $Port automatically." -ForegroundColor Red
        Write-Host "Run stop.bat once, or close PID $listenerPid manually." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 3
    }

    Write-Host "Old CareerVault stopped. Starting $ExpectedVersion..." -ForegroundColor Green
}
elseif ($null -ne $listenerPid) {
    Write-Host "Port $Port is occupied by PID $listenerPid, but it does not look like CareerVault." -ForegroundColor Red
    Write-Host "For safety, this launcher will not terminate that process." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 4
}

$env:CAREERVAULT_FORCE_RESTART = ""
$runtime = Join-Path $PSScriptRoot ".runtime"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$stdout = Join-Path $runtime "careervault.out.log"
$stderr = Join-Path $runtime "careervault.err.log"
$process = Start-Process -FilePath (Join-Path $PSScriptRoot $PythonExe) -ArgumentList @((Join-Path $PSScriptRoot "run.py")) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
$deadline = (Get-Date).AddSeconds(15)
while ((Get-Date) -lt $deadline) {
    $health = Get-CareerVaultHealth
    if ($null -ne $health) { Start-Process $BaseUrl; exit 0 }
    Start-Sleep -Milliseconds 350
}
if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
Write-Host "CareerVault failed to become healthy. Check $stderr" -ForegroundColor Red
Read-Host "Press Enter to exit"
exit 5
