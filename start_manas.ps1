# MANAS PowerShell Startup Script
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  MANAS (मनस्) - Starting Local Web Platform" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Locate Python
$PyCmd = "python"
if (Test-Path "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe") {
    $PyCmd = "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe"
} elseif (Test-Path "$env:LOCALAPPDATA\Python\bin\python.exe") {
    $PyCmd = "$env:LOCALAPPDATA\Python\bin\python.exe"
}

Write-Host "`n[1/3] Starting Backend API Server on http://127.0.0.1:8005 ..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$ScriptDir`" && `"$PyCmd`" -m uvicorn backend.main:app --host 127.0.0.1 --port 8005"

Start-Sleep -Seconds 3

Write-Host "[2/3] Starting Frontend Web Server on http://localhost:3005 ..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$ScriptDir\frontend`" && npm run dev"

Write-Host "`n===================================================" -ForegroundColor Cyan
Write-Host "  MANAS Platform is running!" -ForegroundColor Cyan
Write-Host "  - Frontend:     http://localhost:3005" -ForegroundColor Yellow
Write-Host "  - Backend API:  http://127.0.0.1:8005" -ForegroundColor Yellow
Write-Host "  - Swagger Docs: http://127.0.0.1:8005/api/docs" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

Start-Sleep -Seconds 4
Start-Process "http://localhost:3005"
