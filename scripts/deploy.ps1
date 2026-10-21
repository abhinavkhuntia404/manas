# ==============================================================================
# MANAS Automated Production Deployment Script (PowerShell for Windows)
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "MANAS — मनस्: Deploying Production Environment (Windows)" -ForegroundColor Cyan
Write-Host "======================================================================"

# 1. Preflight Checks
Write-Host "`n[1/6] Checking system prerequisites..." -ForegroundColor Yellow
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Warning "Docker CLI is not detected in PATH."
    Write-Host "For local testing without Docker, you can run:" -ForegroundColor Green
    Write-Host "  Backend:  uvicorn backend.main:app --port 8000" -ForegroundColor White
    Write-Host "  Frontend: cd frontend; npm run dev" -ForegroundColor White
    exit 0
}

# 2. Check Environment Configuration
Write-Host "`n[2/6] Verifying environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env") -and -not (Test-Path ".env.production")) {
    Write-Host "Copying .env.production.example to .env..."
    Copy-Item ".env.production.example" ".env"
}

# 3. Build Containers
Write-Host "`n[3/6] Building production containers..." -ForegroundColor Yellow
docker compose -f docker-compose.prod.yml build

# 4. Launch Services
Write-Host "`n[4/6] Launching containers..." -ForegroundColor Yellow
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# 5. Check Health
Write-Host "`n[5/6] Checking service health..." -ForegroundColor Yellow
$retries = 0
$maxRetries = 25
$healthy = $false

while ($retries -lt $maxRetries) {
    try {
        $res = Invoke-RestMethod -Uri "http://localhost/api/health" -TimeoutSec 2 -ErrorAction Stop
        if ($res.status -eq "ok") {
            $healthy = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 3
        $retries++
        Write-Host "  Waiting for health response ($retries/$maxRetries)..."
    }
}

if ($healthy) {
    Write-Host "`n[6/6] Production Deployment Verified Successfully!" -ForegroundColor Green
    Write-Host "  Web Interface:      http://localhost/" -ForegroundColor White
    Write-Host "  API Documentation:  http://localhost/api/docs" -ForegroundColor White
} else {
    Write-Warning "Service healthcheck timed out. Checking logs:"
    docker compose -f docker-compose.prod.yml logs --tail 30
}
