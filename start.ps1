###############################################################################
# ReviewSense Analytics — One-Click Start Script (PowerShell)
# Run from project root:  .\start.ps1
#
# This script can work two ways:
#   1. npm mode (preferred):  Uses the npm-based orchestration
#   2. native mode (fallback): Runs processes directly via PowerShell
#
# To force native mode:  .\start.ps1 -Native
###############################################################################

param(
    [switch]$Native
)

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  ReviewSense Analytics — Starting All Services" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition

# ── Try npm mode first (unless -Native flag passed) ───────────────────────
if (-not $Native) {
    $rootPkgJson = Join-Path $projectRoot "package.json"
    $nodeModules = Join-Path $projectRoot "node_modules"

    if ((Test-Path $rootPkgJson) -and (Test-Path $nodeModules)) {
        Write-Host "[npm] Using npm-based orchestration..." -ForegroundColor Green
        Write-Host "      Run 'npm run dev:full' from project root" -ForegroundColor Gray
        Write-Host ""
        Set-Location $projectRoot
        & npm run dev:full
        exit $LASTEXITCODE
    } else {
        Write-Host "[npm] Root node_modules not found. Falling back to native mode." -ForegroundColor Yellow
        Write-Host "      To enable npm mode, run:  npm install" -ForegroundColor Gray
        Write-Host ""
    }
}

# ── Native mode (original PowerShell-based startup) ───────────────────────

# Step 1: Kill anything already on ports 8000 / 5173 / 5174
Write-Host "[1/4] Clearing ports 8000, 5173, 5174..." -ForegroundColor Yellow
foreach ($port in @(8000, 5173, 5174)) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
Start-Sleep -Seconds 1
Write-Host "       Ports cleared." -ForegroundColor Green

# Step 2: Verify venv
$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[ERROR] Virtual environment not found at $venvPython" -ForegroundColor Red
    Write-Host "        Run:  python -m venv venv" -ForegroundColor Red
    Write-Host "        Then: .\venv\Scripts\pip install -r backend\requirements.txt" -ForegroundColor Red
    exit 1
}
Write-Host "[2/4] Virtual environment found." -ForegroundColor Green

# Step 3: Start Backend (FastAPI + Uvicorn)
Write-Host "[3/4] Starting Backend (FastAPI on port 8000)..." -ForegroundColor Yellow
$backendJob = Start-Process -FilePath $venvPython `
    -ArgumentList "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" `
    -WorkingDirectory $projectRoot `
    -PassThru -NoNewWindow

# Wait for backend to become healthy
$maxWait = 60
$waited = 0
$backendReady = $false
Write-Host "       Waiting for backend to start..." -ForegroundColor Gray
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 2
    $waited += 2
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 3 -ErrorAction Stop
        if ($response.status -eq "healthy" -or $response.status -eq "degraded") {
            $backendReady = $true
            break
        }
    } catch {
        Write-Host "       ... still starting ($waited s)" -ForegroundColor Gray
    }
}

if (-not $backendReady) {
    Write-Host "[ERROR] Backend did not become healthy within $maxWait seconds." -ForegroundColor Red
    Write-Host "        Check the terminal output for errors." -ForegroundColor Red
    exit 1
}
Write-Host "       Backend is HEALTHY!" -ForegroundColor Green

# Step 4: Start Frontend (Vite dev server)
Write-Host "[4/4] Starting Frontend (Vite)..." -ForegroundColor Yellow
$frontendDir = Join-Path $projectRoot "frontend"

# Ensure node_modules exist
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "       Installing npm dependencies..." -ForegroundColor Gray
    Start-Process -FilePath "npm" -ArgumentList "install" `
        -WorkingDirectory $frontendDir -Wait -NoNewWindow
}

Start-Process -FilePath "npm" -ArgumentList "run", "dev" `
    -WorkingDirectory $frontendDir -NoNewWindow

Start-Sleep -Seconds 4

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "  ALL SERVICES RUNNING" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Frontend:     http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Keep script alive so Ctrl+C can kill everything
try {
    while ($true) { Start-Sleep -Seconds 5 }
} finally {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    Stop-Process -Id $backendJob.Id -Force -ErrorAction SilentlyContinue
    foreach ($port in @(8000, 5173, 5174)) {
        Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
            ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    }
    Write-Host "All services stopped." -ForegroundColor Green
}
