Set-Location $PSScriptRoot

$Port = 8765
$PythonExe = ".venv\Scripts\python.exe"
$BaseUrl = "http://127.0.0.1:$Port"
$ForceRestart = $env:JOBPILOT_FORCE_RESTART -eq "1"

function Get-ExpectedVersion {
    $versionFile = Join-Path $PSScriptRoot "jobpilot\__init__.py"
    if (-not (Test-Path $versionFile)) { return "unknown" }
    $text = Get-Content $versionFile -Raw -ErrorAction SilentlyContinue
    if ($text -match '__version__\s*=\s*["'']([^"'']+)["'']') {
        return [string]$Matches[1]
    }
    return "unknown"
}

$ExpectedVersion = Get-ExpectedVersion

if (-not (Test-Path $PythonExe)) {
    Write-Host "JobPilot is not installed. Please run install.bat first." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

function Get-JobPilotHealth {
    try {
        return Invoke-RestMethod -Uri "$BaseUrl/api/health" -TimeoutSec 1 -ErrorAction Stop
    }
    catch {
        return $null
    }
}

function Get-PortOwnerPid {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $connection) {
        return [int]$connection.OwningProcess
    }
    return $null
}

function Get-ProcessIdentity {
    param([int]$ProcessId)
    try {
        return Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop
    }
    catch {
        return $null
    }
}

function Test-LooksLikeJobPilotProcess {
    param([int]$ProcessId)
    $process = Get-ProcessIdentity $ProcessId
    if ($null -eq $process) { return $false }

    $root = ([System.IO.Path]::GetFullPath($PSScriptRoot)).TrimEnd('\').ToLowerInvariant()
    $exe = [string]$process.ExecutablePath
    $cmd = [string]$process.CommandLine
    $haystack = "$exe $cmd".ToLowerInvariant()

    # Safest case: the listener was launched from this checkout / virtualenv.
    if ($haystack.Contains($root)) { return $true }

    # Compatibility with an older JobPilot checkout, e.g. C:\jobpilot-v0.1\.venv\Scripts\python.exe run.py.
    if ($haystack.Contains("jobpilot") -and (
        $haystack.Contains("run.py") -or
        $haystack.Contains("jobpilot.main") -or
        $haystack.Contains("uvicorn")
    )) {
        return $true
    }

    return $false
}

function Wait-PortFree {
    param([int]$Seconds = 5)
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        if ($null -eq (Get-PortOwnerPid)) {
            return $true
        }
        Start-Sleep -Milliseconds 200
    }
    return $false
}

function Stop-ExistingJobPilot {
    param([int]$ProcessId, [string]$Description)
    Write-Host "Stopping $Description (PID $ProcessId)..." -ForegroundColor Yellow
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    if (-not (Wait-PortFree 5)) {
        Write-Host "Could not release port $Port automatically." -ForegroundColor Red
        Write-Host "Run doctor.bat for process details, or close PID $ProcessId manually." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 3
    }
}

$health = Get-JobPilotHealth
$listenerPid = Get-PortOwnerPid

if ($null -ne $health) {
    $runningVersion = [string]$health.version

    if (($runningVersion -eq $ExpectedVersion) -and (-not $ForceRestart)) {
        Write-Host "JobPilot $ExpectedVersion is already running. Opening it now." -ForegroundColor Green
        Start-Process $BaseUrl
        exit 0
    }

    if ($null -eq $listenerPid) {
        Write-Host "A JobPilot service answered the health check, but its process could not be located." -ForegroundColor Yellow
        Write-Host "Run doctor.bat for details." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 2
    }

    $label = if ($runningVersion) { "existing JobPilot $runningVersion" } else { "existing JobPilot" }
    Stop-ExistingJobPilot $listenerPid $label
    Write-Host "Old JobPilot stopped. Starting $ExpectedVersion..." -ForegroundColor Green
}
elseif ($null -ne $listenerPid) {
    if (Test-LooksLikeJobPilotProcess $listenerPid) {
        Write-Host "Port $Port is held by a JobPilot-looking process, but its health endpoint is not responding." -ForegroundColor Yellow
        Write-Host "Treating it as a stalled/older JobPilot process." -ForegroundColor Yellow
        Stop-ExistingJobPilot $listenerPid "stalled JobPilot"
        Write-Host "Stalled JobPilot stopped. Starting $ExpectedVersion..." -ForegroundColor Green
    }
    else {
        $process = Get-ProcessIdentity $listenerPid
        Write-Host "Port $Port is occupied by PID $listenerPid, and it does not look like JobPilot." -ForegroundColor Red
        if ($null -ne $process) {
            Write-Host ("Process: {0}" -f $process.Name) -ForegroundColor Yellow
            Write-Host ("Path:    {0}" -f $process.ExecutablePath) -ForegroundColor Yellow
        }
        Write-Host "For safety, this launcher will not terminate that process." -ForegroundColor Yellow
        Write-Host "Run doctor.bat for a full diagnosis." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 4
    }
}

$env:JOBPILOT_FORCE_RESTART = ""
Start-Process $BaseUrl
& $PythonExe "run.py"
