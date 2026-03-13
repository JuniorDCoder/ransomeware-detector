# ─────────────────────────────────────────────────────────────────────────────
#  Ransomware Detector — PowerShell Installer (Windows)
# ─────────────────────────────────────────────────────────────────────────────
#  Usage: powershell -ExecutionPolicy Bypass -File install.ps1
# ─────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$PSStyle.OutputRendering = "PlainText" 2>$null

function Log   ($msg) { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Warn  ($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Fail  ($msg) { Write-Host "[ERR]  $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "  Ransomware Detector — Installer (PowerShell)" -ForegroundColor Cyan
Write-Host "  =============================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Find Python 3.9+ ─────────────────────────────────────────────────────
$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]; $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 9) { $python = $cmd; break }
        }
    } catch {}
}
if (-not $python) { Fail "Python 3.9+ not found. Install from https://python.org" }
Log "Using $python ($ver)"

# ── 2. Virtual environment ────────────────────────────────────────────────────
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv")) {
    & $python -m venv .venv
    Log "Created .venv"
} else {
    Log ".venv already exists"
}

& .venv\Scripts\Activate.ps1

# ── 3. Install package ────────────────────────────────────────────────────────
pip install --quiet --upgrade pip
pip install --quiet -e .
Log "Dependencies installed"

# ── 4. Config ─────────────────────────────────────────────────────────────────
if (-not (Test-Path "config.json")) {
    Copy-Item "config.example.json" "config.json"
    Log "Created config.json from config.example.json"
} else {
    Warn "config.json already exists — not overwritten"
}

Write-Host ""
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Start the app:    .\run.bat"
Write-Host "  Or individually:  rds-server | rds-dashboard | rds-agent --config config.json"
Write-Host ""
