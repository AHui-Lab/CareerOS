Set-Location $PSScriptRoot

$JobPilotPort = 8765
$CareerVaultPort = 8766
$JobPilotUrl = "http://127.0.0.1:$JobPilotPort"
$CareerVaultUrl = if ($env:CAREERVAULT_URL) { $env:CAREERVAULT_URL.TrimEnd('/') } else { "http://127.0.0.1:$CareerVaultPort" }

function Section([string]$Title) {
    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
}

function Get-Json([string]$Url, [int]$Timeout = 2) {
    try {
        return Invoke-RestMethod -Uri $Url -TimeoutSec $Timeout -ErrorAction Stop
    }
    catch {
        return $null
    }
}

function Get-PortOwner([int]$Port) {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $connection) { return $null }
    try {
        return Get-CimInstance Win32_Process -Filter "ProcessId=$($connection.OwningProcess)" -ErrorAction Stop
    }
    catch {
        return [pscustomobject]@{ ProcessId = [int]$connection.OwningProcess; Name = "unknown"; ExecutablePath = ""; CommandLine = "" }
    }
}

Section "Local checkout"
Write-Host "Root: $PSScriptRoot"
Write-Host ("Python venv: {0}" -f (Test-Path ".venv\Scripts\python.exe"))
if (Test-Path "jobpilot\__init__.py") {
    $versionText = Get-Content "jobpilot\__init__.py" -Raw
    if ($versionText -match '__version__\s*=\s*["'']([^"'']+)["'']') {
        Write-Host "Checkout version: $($Matches[1])"
    }
}

Section "Port 8765"
$jpProcess = Get-PortOwner $JobPilotPort
if ($null -eq $jpProcess) {
    Write-Host "No listener on port 8765." -ForegroundColor Yellow
}
else {
    Write-Host "PID:     $($jpProcess.ProcessId)"
    Write-Host "Process: $($jpProcess.Name)"
    Write-Host "Path:    $($jpProcess.ExecutablePath)"
    Write-Host "Command: $($jpProcess.CommandLine)"
}

Section "JobPilot health"
$jpHealth = Get-Json "$JobPilotUrl/api/health"
if ($null -eq $jpHealth) {
    Write-Host "JobPilot health check FAILED: $JobPilotUrl/api/health" -ForegroundColor Red
}
else {
    Write-Host "OK:      $($jpHealth.ok)" -ForegroundColor Green
    Write-Host "Version: $($jpHealth.version)"
    Write-Host "DB:      $($jpHealth.db)"
    if ($null -ne $jpHealth.careervault) {
        Write-Host "Backend sees CareerVault: $($jpHealth.careervault.available)"
        Write-Host "CareerVault URL:          $($jpHealth.careervault.url)"
        Write-Host "CareerVault version:      $($jpHealth.careervault.version)"
        if ($jpHealth.careervault.error) { Write-Host "CareerVault error:        $($jpHealth.careervault.error)" -ForegroundColor Yellow }
    }
}

Section "CareerVault health"
$cvHealth = Get-Json "$CareerVaultUrl/api/health"
if ($null -eq $cvHealth) {
    Write-Host "CareerVault health check FAILED: $CareerVaultUrl/api/health" -ForegroundColor Red
}
else {
    Write-Host "OK:      $($cvHealth.ok)" -ForegroundColor Green
    Write-Host "Version: $($cvHealth.version)"
    Write-Host "Root:    $($cvHealth.root)"
}

Section "CareerVault Resume Ready facts"
$cvExperiences = Get-Json "$CareerVaultUrl/api/jobpilot/experiences?resume_ready=true"
if ($null -eq $cvExperiences) {
    Write-Host "Could not read Resume Ready experiences." -ForegroundColor Red
}
else {
    $items = @()
    if ($cvExperiences -is [System.Array]) {
        $items = @($cvExperiences)
    }
    elseif ($null -ne $cvExperiences.items) {
        $items = @($cvExperiences.items)
    }
    elseif ($null -ne $cvExperiences.experiences) {
        $items = @($cvExperiences.experiences)
    }
    Write-Host "Resume Ready count: $($items.Count)" -ForegroundColor Green
    foreach ($item in ($items | Select-Object -First 5)) {
        Write-Host (" - {0}" -f $item.title)
    }
    if ($items.Count -gt 5) { Write-Host " - ..." }
}

Section "Result"
if (($null -ne $jpHealth) -and ($null -ne $cvHealth)) {
    Write-Host "JobPilot <-> CareerVault basic connectivity is healthy." -ForegroundColor Green
    exit 0
}
elseif ($null -eq $jpHealth) {
    Write-Host "Fix JobPilot startup/port 8765 first." -ForegroundColor Red
    exit 2
}
else {
    Write-Host "JobPilot is running, but CareerVault is not reachable." -ForegroundColor Yellow
    exit 3
}
