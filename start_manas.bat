@echo off
title MANAS - Brain Disease Mapping Platform
echo ===================================================
echo   MANAS (मनस्) - Starting Local Web Platform
echo ===================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

rem Detect Python binary
set "PY_CMD=python"
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
) else if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\bin\python.exe"
)

echo [1/3] Starting Backend API Server on http://127.0.0.1:8005 ...
start "MANAS Backend" cmd /k "cd /d ^"%SCRIPT_DIR%^" && ^"%PY_CMD%^" -m uvicorn backend.main:app --host 127.0.0.1 --port 8005"

echo [2/3] Waiting 3 seconds for backend initialization...
timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend Web Server on http://localhost:3005 ...
start "MANAS Frontend" cmd /k "cd /d ^"%SCRIPT_DIR%frontend^" && npm run dev"

echo.
echo ===================================================
echo   MANAS Platform is running!
echo   - Frontend:     http://localhost:3005
echo   - Backend API:  http://127.0.0.1:8005
echo   - Swagger Docs: http://127.0.0.1:8005/api/docs
echo.
echo   Opening browser in 4 seconds...
echo ===================================================
timeout /t 4 /nobreak >nul
start http://localhost:3005
