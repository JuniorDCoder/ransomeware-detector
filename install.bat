@echo off
:: ─────────────────────────────────────────────────────────────────────────────
::  Ransomware Detector — Windows Installer
:: ─────────────────────────────────────────────────────────────────────────────
setlocal enabledelayedexpansion

echo.
echo  Ransomware Detector — Installer (Windows)
echo  ==========================================
echo.

:: ── 1. Find Python 3.9+ ─────────────────────────────────────────────────────
set PYTHON=
for %%p in (python python3) do (
    where %%p >nul 2>&1 && (
        for /f "tokens=2" %%v in ('%%p --version 2^>^&1') do set PYVER=%%v
        set PYTHON=%%p
    )
)

if "!PYTHON!"=="" (
    echo [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)
echo [OK] Using !PYTHON! ^(!PYVER!^)

:: ── 2. Create virtual environment ────────────────────────────────────────────
if not exist ".venv" (
    !PYTHON! -m venv .venv
    echo [OK] Created .venv
) else (
    echo [OK] .venv already exists
)

call .venv\Scripts\activate.bat

:: ── 3. Upgrade pip and install ───────────────────────────────────────────────
pip install --quiet --upgrade pip
pip install --quiet -e .
echo [OK] Dependencies installed

:: ── 4. Copy config ───────────────────────────────────────────────────────────
if not exist "config.json" (
    copy config.example.json config.json >nul
    echo [OK] Created config.json — edit as needed
) else (
    echo [WARN] config.json already exists — not overwritten
)

echo.
echo  Installation complete!
echo.
echo  Start the app:  run.bat
echo  Or manually:
echo    rds-server
echo    rds-dashboard
echo    rds-agent --config config.json
echo.
pause
