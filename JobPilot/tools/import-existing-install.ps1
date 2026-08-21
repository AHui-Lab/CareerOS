param(
    [Parameter(Mandatory=$true)]
    [string]$Source
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Source = (Resolve-Path $Source).Path

if ($Source -eq $RepoRoot) {
    throw "Source and destination are the same directory."
}

$required = @(
    "jobpilot",
    "extension",
    "tests",
    "run.py",
    "requirements.txt"
)

foreach ($item in $required) {
    if (-not (Test-Path (Join-Path $Source $item))) {
        throw "Missing required source item: $item"
    }
}

Write-Host "Importing JobPilot source from:" -ForegroundColor Cyan
Write-Host "  $Source"
Write-Host "Into repository:" -ForegroundColor Cyan
Write-Host "  $RepoRoot"
Write-Host ""
Write-Host "The following are NEVER copied: .env, .venv, jobpilot.db, profile.json, backups, caches." -ForegroundColor Yellow

$dirs = @("jobpilot", "extension", "tests")
foreach ($dir in $dirs) {
    $src = Join-Path $Source $dir
    $dst = Join-Path $RepoRoot $dir
    if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
    Copy-Item $src $dst -Recurse -Force
}

$files = @(
    "run.py",
    "requirements.txt",
    ".env.example"
)
foreach ($file in $files) {
    $src = Join-Path $Source $file
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $RepoRoot $file) -Force
    }
}

$profileExample = Join-Path $Source "data\profile.example.json"
if (Test-Path $profileExample) {
    $dataDir = Join-Path $RepoRoot "data"
    New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
    Copy-Item $profileExample (Join-Path $dataDir "profile.example.json") -Force
}

Get-ChildItem $RepoRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem $RepoRoot -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Source import complete." -ForegroundColor Green
Write-Host "Next:" -ForegroundColor Cyan
Write-Host "  1. Run install.bat"
Write-Host "  2. Run tools\verify.ps1"
Write-Host "  3. Review: git status"
Write-Host "  4. git add ."
Write-Host "  5. git commit -m \"Import JobPilot V0.2.2 source\""
Write-Host "  6. git push"
