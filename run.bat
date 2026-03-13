@echo off
:: ─────────────────────────────────────────────────────────────────────────────
::  Ransomware Detector — Start server + dashboard (Windows)
:: ─────────────────────────────────────────────────────────────────────────────
setlocal

if not exist ".venv" (
    echo [ERROR] .venv not found — run install.bat first
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

set SERVER_PORT=5000
set DASH_PORT=5001
if not "%RDS_SERVER_PORT%"=="" set SERVER_PORT=%RDS_SERVER_PORT%
if not "%RDS_DASHBOARD_PORT%"=="" set DASH_PORT=%RDS_DASHBOARD_PORT%

echo.
echo  Ransomware Detector — Starting
echo  Server    ^> http://127.0.0.1:%SERVER_PORT%
echo  Dashboard ^> http://127.0.0.1:%DASH_PORT%
echo  Press Ctrl+C to stop.
echo.

:: Start server in a new window
start "RDS Server" cmd /k "call .venv\Scripts\activate.bat && rds-server"

:: Brief pause then start dashboard
timeout /t 2 /nobreak >nul
start "RDS Dashboard" cmd /k "call .venv\Scripts\activate.bat && rds-dashboard"

:: Open browser after 3 seconds
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:%DASH_PORT%"
