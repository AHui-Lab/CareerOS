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
    if (-not (Test-Path $python)) { throw "$Name 的 Python 虚拟环境创建失败：$python" }
    & $python -m pip install --upgrade pip
    & $python -m pip install -r (Join-Path $Root 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw "$Name 依赖安装失败。" }
}

Install-Module 'CareerVault 经历和项目' (Join-Path $PSScriptRoot 'CareerVault')
Install-Module 'JobPilot 求职管理' (Join-Path $PSScriptRoot 'JobPilot')

if (-not (Test-Path 'JobPilot\.env') -and (Test-Path 'JobPilot\.env.example')) { Copy-Item 'JobPilot\.env.example' 'JobPilot\.env' }
Write-Host ''
Write-Host '[DONE] CareerOS 安装完成。以后只需要运行根目录 start.bat。' -ForegroundColor Green
