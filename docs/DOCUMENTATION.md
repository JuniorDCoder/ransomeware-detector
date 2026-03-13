# Ransomware Detector — Complete Documentation

**Version:** 1.0.0 | **Audience:** Final Year Project Users & Evaluators

---

## Table of Contents

1. [What This Project Does](#1-what-this-project-does)
2. [How It Works — System Architecture](#2-how-it-works--system-architecture)
3. [Requirements](#3-requirements)
4. [Installation — Step by Step](#4-installation--step-by-step)
   - [Linux/macOS](#a-linuxmacos)
   - [Windows (Script)](#b-windows-script)
   - [Windows (EXE Installer)](#c-windows-exe-installer--recommended-)
   - [Docker (any OS)](#d-docker-any-os)
5. [Running the Application](#5-running-the-application)
6. [The Dashboard — What You See](#6-the-dashboard--what-you-see)
7. [Configuration Reference](#7-configuration-reference)
8. [API Reference](#8-api-reference)
9. [Components Deep Dive](#9-components-deep-dive)
10. [Troubleshooting](#10-troubleshooting)
11. [Project Structure](#11-project-structure)

---

## 1. What This Project Does

**Ransomware Detector** is a security tool that monitors computers for signs of ransomware activity — the kind of malware that encrypts your files and demands payment.

It works by watching:

| What It Monitors | What It Looks For |
|---|---|
| **Files** | Suspicious file extensions (`.locked`, `.encrypted`), unusually high-entropy (scrambled) file content, rapid bulk file changes |
| **Network** | Unusually high numbers of outgoing connections (data exfiltration) |
| **USB Drives** | Automatically scans removable devices when they are plugged in |

When something suspicious is found, it sends an **alert** to a central server, which stores it and shows it in a **real-time web dashboard**. An administrator can view all alerts, see which machines (agents) are online, and acknowledge resolved issues.

### Key Capabilities

- ✅ Monitors multiple machines from a single dashboard
- ✅ Real-time alerts with severity levels (INFO / WARNING / CRITICAL)
- ✅ Works on Linux, macOS, and Windows
- ✅ No internet required — runs fully locally
- ✅ Optional Firebase push notifications, Telegram bot, VirusTotal integration

---

## 2. How It Works — System Architecture

The project has three main parts that run simultaneously:

```
┌─────────────────────────────────────────────────────────┐
│  Machine 1 (any OS)              Machine 2 (any OS)     │
│  ┌────────────────┐              ┌────────────────┐     │
│  │   RDS Agent    │              │   RDS Agent    │     │
│  │  • File watch  │              │  • File watch  │     │
│  │  • Net monitor │              │  • USB scan    │     │
│  └───────┬────────┘              └───────┬────────┘     │
│          │   HTTP POST alerts/heartbeat  │              │
└──────────┼───────────────────────────────┼──────────────┘
           │                               │
           ▼                               ▼
┌────────────────────────────────────────────────────────┐
│              Central Server  (port 5000)               │
│  • Receives alerts from all agents                    │
│  • Stores everything in a SQLite database             │
│  • Broadcasts real-time events via WebSocket          │
│  • REST API for querying alerts, stats, agents        │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│              Web Dashboard  (port 5001)                │
│  Opens in your browser — shows live stats, alerts,    │
│  agent status, charts. Updated every 5 seconds.       │
└────────────────────────────────────────────────────────┘
```

### Flow of an Alert

1. The **Agent** is running on a monitored machine and detects a file being renamed to `.locked`
2. The Agent calls `POST /api/alerts` on the Central Server with the alert details
3. The Server saves it to the database and broadcasts it via WebSocket
4. The **Dashboard** receives the WebSocket event and shows a pop-up toast notification
5. On the next poll (every 5 seconds), the Dashboard updates the alert table
6. An administrator clicks **Acknowledge** on the dashboard to mark it as resolved

---

## 3. Requirements

### Minimum Requirements

| Item | Requirement |
|---|---|
| **Python** | Version **3.9 or higher** (3.11 recommended) |
| **RAM** | 256 MB minimum (512 MB recommended) |
| **Disk** | 500 MB (for Python + dependencies) |
| **OS** | Linux, macOS, or Windows |
| **Network** | The Agent machine must be able to reach the Server machine |

### Check Your Python Version

Open a terminal and type:

```bash
python3 --version
```

You should see something like `Python 3.11.5`. If you see `Python 2.x`, try `python3 --version`. If Python is not installed, download it from [python.org](https://python.org).

---

## 4. Installation — Step by Step

### A. Linux/macOS

**Step 1 — Download the project**

Open a terminal and clone the repository:
```bash
git clone https://github.com/JuniorDCoder/ransomeware-detector.git
cd ransomeware-detector
```

**Step 2 — Run the installer:**
```bash
bash install.sh
```

This script will:
- ✔ Detect your Python version
- ✔ Create a virtual environment (`.venv`) — an isolated Python install just for this project
- ✔ Install all required packages from `requirements.runtime.txt`
- ✔ Install the package so the `rds-server`, `rds-agent`, and `rds-dashboard` commands work
- ✔ Copy the default config (`config.example.json` → `config.json`)

**You only need to run this once.**

If you need the full feature set (ML/Telegram/VirusTotal), run:
```bash
bash install.sh --full
```

---

**Step 3 — Start the application:**
```bash
bash run.sh
```

This will:
- Start the **API Server** on `http://localhost:5000`
- Start the **Dashboard** on `http://localhost:5001`
- Open your browser automatically to the Dashboard

Press `Ctrl + C` to stop everything.

---

### B. Windows (Script)

**Step 1 — Download the project**

Open Command Prompt (search "cmd" in the Start menu) and clone the repository:

```bat
git clone https://github.com/JuniorDCoder/ransomeware-detector.git
cd ransomeware-detector
```

**Step 2 — Run the installer:**
```bat
install.bat
```

> If you prefer PowerShell, right-click and "Run as Administrator", then:
> ```powershell
> powershell -ExecutionPolicy Bypass -File install.ps1
> ```

**Step 3 — Start the application:**
```bat
run.bat
```

This opens two separate Command Prompt windows (one for the server, one for the dashboard) and then opens your browser to the dashboard.

---

### C. Windows EXE Installer *(Recommended)*

This is the **easiest Windows option** — produces a single `RansomGuard-Setup.exe` that anyone can double-click to install the full application with no technical knowledge required.

**What it does:** Bundles everything (Python, Flask, all dependencies, the server, dashboard, and agent) into one self-contained exe. Users never need to install Python or run any command.

#### Prerequisites (on the Windows build machine)

| Tool | Download |
|---|---|
| Python 3.9+ | [python.org](https://python.org) |
| Inno Setup 6 | [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php) |

#### Build the EXE Installer

From the project root on Windows:
```bat
python windows\build.py
```

This auto-installs PyInstaller, builds the app bundle, and compiles `windows\dist\RansomGuard-Setup.exe`.

#### What the User Experience Looks Like

1. **Double-click** `RansomGuard-Setup.exe`
2. Standard "Next / Install" wizard — takes ~30 seconds
3. Files installed to `C:\Program Files\RansomGuard\`
4. Start Menu shortcut created. Optional: Desktop shortcut + auto-start on Windows boot
5. App **launches automatically** after install
6. A **🛡️ shield icon** appears in the system tray (notification area, bottom-right)
7. Browser opens to the dashboard at `http://localhost:5001`

#### Using the System Tray App

| Action | How |
|---|---|
| Open Dashboard | Double-click tray icon, or right-click → Open Dashboard |
| Stop the app | Right-click → Stop RansomGuard |
| Start after reboot | Click Start Menu → RansomGuard (or enable at-boot option during install) |

> **Note:** The server, dashboard, and agent all run invisibly in the background — no command prompts appear.

#### Distribute to Others

Send them just the one file: `RansomGuard-Setup.exe`. They run it, click Next, and they're done.

---

### D. Docker (any OS)

Docker lets you run the whole system in a container — no Python install needed.

**Requirements:** [Install Docker Desktop](https://docs.docker.com/get-docker/)

**Step 1 — Build and run:**
```bash
docker compose up
```

**Step 2 — Open your browser to:**
- Dashboard: `http://localhost:5001`
- API Server: `http://localhost:5000`

**Step 3 — Stop:**
```bash
docker compose down
```

The database (`data.db`) is saved in a Docker volume and persists between restarts.

---

## 5. Running the Application

### What Needs to Run

To use the full system, you need **three things running at the same time**:

| Process | Command | What it does |
|---|---|---|
| **Server** | `rds-server` | Central API + database |
| **Dashboard** | `rds-dashboard` | Web interface (browser) |
| **Agent(s)** | `rds-agent --config config.json` | Monitoring on each machine |

`bash run.sh` (Linux/macOS) and `run.bat` (Windows) start the Server and Dashboard for you automatically.

### Starting the Agent on the Same Machine

Open a **third terminal** after running `run.sh`:

```bash
source .venv/bin/activate     # Linux/macOS
# or: .venv\Scripts\activate.bat    # Windows

rds-agent --config config.json
```

### Starting the Agent on a Different Machine

1. Copy the project folder to the other machine (or just the `agents/`, `utils/`, `requirements.runtime.txt`, `config.json` and `pyproject.toml` files)
2. Run `bash install.sh` on that machine too
3. Edit `config.json` on that machine — change `server_url` to the IP address of the server machine:
   ```json
   {
     "server_url": "http://192.168.1.100:5000",
     "agent_id": "laptop-01"
   }
   ```
4. Start the agent: `rds-agent --config config.json`

The agent will appear in the Dashboard under "Agents Online" within a few seconds.

---

## 6. The Dashboard — What You See

Open `http://localhost:5001` in your browser.

### Sidebar Navigation

| Icon | Section | Contains |
|---|---|---|
| 📊 | **Dashboard** | Overview cards + alert chart + agents table |
| 🖥️ | **Agents** | All connected machines and their status |
| 🔔 | **Alerts** | Full alerts table with all recent alerts |

### Metric Cards (top row)

| Card | Meaning |
|---|---|
| **Agents Online** | Number of agents that sent a heartbeat in the last 60 seconds |
| **Total Alerts** | Total alerts stored in the database |
| **Warnings** | Count of WARNING-level alerts |
| **Critical** | Count of CRITICAL-level alerts — these need immediate attention |

### Alert Levels

| Level | Color | Meaning |
|---|---|---|
| **INFO** | Teal | Low severity — note-worthy event, no immediate action required |
| **WARNING** | Amber | Medium severity — potential threat, investigate soon |
| **CRITICAL** | Red | High severity — active threat, act immediately |

### Real-time Updates

- The dashboard **polls the server every 5 seconds** for new data
- If the server is running Socket.IO, the dashboard also receives **instant push notifications** — a toast (pop-up) appears in the top-right corner when a new alert arrives
- The **connection badge** (bottom-left of sidebar) shows whether the WebSocket connection is live

### Acknowledging Alerts

Click the **Acknowledge** button on any alert row to mark it as reviewed. This does not delete the alert — it just flags it as seen, and the button changes to `✔ Done`.

---

## 7. Configuration Reference

The `config.json` file controls agent behaviour. Edit it with any text editor.

```json
{
  "server_url":                   "http://localhost:5000",
  "agent_id":                     "agent-001",
  "watch_paths":                  ["/home", "/Documents"],
  "scan_on_connect":              true,
  "heartbeat_interval":           5,
  "entropy_threshold":            7.5,
  "file_change_rate_threshold":   120,
  "file_change_window_seconds":   60,
  "network_connection_threshold": 200,
  "enable_external_device_monitor": true,
  "enable_network_monitor":       true,
  "enable_file_monitor":          true
}
```

| Setting | Default | Meaning |
|---|---|---|
| `server_url` | `http://localhost:5000` | Address of the central server |
| `agent_id` | hostname | Unique name for this agent (use something descriptive like `"office-pc"`) |
| `watch_paths` | `["."]` | Folders to monitor for file changes. Add important paths like `["/home", "/var"]` |
| `scan_on_connect` | `true` | Automatically scan USB drives when plugged in |
| `heartbeat_interval` | `5` | How often (seconds) the agent checks in with the server |
| `entropy_threshold` | `7.5` | Files with entropy above this value are flagged (7.5–8.0 = highly encrypted content) |
| `file_change_rate_threshold` | `120` | Alert if more than 120 files change within the window |
| `file_change_window_seconds` | `60` | The time window (seconds) for counting file changes |
| `network_connection_threshold` | `200` | Alert if more than 200 network connections are open simultaneously |
| `enable_*` | `true` | Toggle individual monitors on or off |

### Environment Variables (overrides)

You can set these in your shell or in a `.env` file — they override `config.json`:

```bash
export RDS_SERVER_URL=http://192.168.1.100:5000   # point agent at remote server
export RDS_AGENT_ID=my-laptop                      # override agent name
export RDS_SERVER_HOST=0.0.0.0                     # bind server to all interfaces
export RDS_SERVER_PORT=5000
export RDS_DASHBOARD_HOST=0.0.0.0
export RDS_DASHBOARD_PORT=5001
export RDS_USER=admin                              # API login username
export RDS_PASSWORD=admin                          # API login password
export RDS_SECRET_KEY=your-long-random-key         # Flask session secret (set in production!)
export VIRUS_TOTAL_API_KEY=your-key                # Optional VirusTotal integration
export TELEGRAM_BOT_TOKEN=your-token               # Optional Telegram notifications
```

---

## 8. API Reference

The server exposes a REST API on port 5000. You can call these with `curl` or any HTTP client.

### Authentication

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

Returns a JWT token. Pass it as `Authorization: Bearer <token>` for protected routes.

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/agents/heartbeat` | Agent check-in with system stats |
| `GET`  | `/api/agents` | List all registered agents and last-seen time |
| `POST` | `/api/alerts` | Submit a new alert |
| `GET`  | `/api/alerts/recent?limit=50` | Get the most recent alerts |
| `POST` | `/api/alert/<id>/acknowledge` | Mark an alert as acknowledged |
| `GET`  | `/api/stats` | Summary statistics (agents online, alert counts) |
| `POST` | `/api/device/<id>/isolate` | Queue an ISOLATE command for an agent |
| `POST` | `/api/scan/external` | Queue an external device scan for an agent |
| `GET`  | `/api/commands/<agent_id>` | Agent polls for pending commands |

### Example — Send a Test Alert

```bash
curl -X POST http://localhost:5000/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "level": "CRITICAL",
    "type": "RANSOMWARE_DETECTED",
    "message": "File renamed to document.pdf.locked",
    "agent_id": "office-pc"
  }'
```

---

## 9. Components Deep Dive

### `agents/` — The Monitoring Agent

The agent runs on each machine you want to protect. It has three monitors:

**File Monitor** (`file_monitor.py`)
- Uses the `watchdog` library to watch folders in real time
- Flags files with suspicious extensions and high entropy
- Alerts on mass file changes (a hallmark of ransomware encryption)

**Network Monitor** (`network_monitor.py`)
- Uses `psutil` to count active network connections every heartbeat
- Alerts when the connection count exceeds the configured threshold

**External Device Monitor** (`external_device_monitor.py`)
- Listens for USB drive insertions
- On Linux: uses `pyudev`; on Windows: uses `WMI`; fallback: polls every 5 seconds
- Optionally scans the drive immediately on connect

### `server/` — The Central Server

- **`main_server.py`**: Flask app with all REST endpoints and WebSocket support (via Socket.IO)
- **`database.py`**: SQLite3 wrapper. Three tables: `alerts`, `agents`, `commands`
- **`alert_system.py`**: Thin wrapper around database alert operations
- **`detection_engine.py`**: Computes aggregate statistics (agents online, alert counts, risk score)

### `dashboard/` — The Web Interface

- **`app.py`**: Tiny Flask server that just serves the HTML template
- **`templates/index.html`**: Self-contained single-page dashboard (vanilla JS + Chart.js + Socket.IO)
- **`mobile_api.py`**: Additional API endpoints for mobile clients

### `utils/`

- **`config.py`**: Loads and merges `config.json` with environment variable overrides
- **`entropy_calculator.py`**: Shannon entropy calculation — high entropy = likely encrypted content
- **`portable_scanner.py`**: Scans a folder for suspicious files (extensions + entropy)

### `ml_detector/`

- **`realtime_scanner.py`**: Optional ML-based scanning hook (requires `scikit-learn`)
- **`train_model.py`**: Train a classifier on labelled file samples
- **`virus_total_api.py`**: Submit hashes to VirusTotal API for cloud-based scanning

### Database Schema

The SQLite database (`data.db`) has three tables:

```
alerts:   id, level, type, message, agent_id, timestamp, details, acknowledged, realtime
agents:   agent_id, last_seen, data (JSON system info)
commands: id, agent_id, command, status, created_at, payload, result
```

---

## 10. Troubleshooting

### The install takes forever / hangs

The basic `install.sh` now only installs lightweight runtime dependencies. If it's still slow, check your internet connection or use a VPN/mirror. You can also install manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.runtime.txt
pip install --no-deps -e .
```

---

### "Address already in use" error

Another process is using port 5000 or 5001. Either stop the other process or change ports:

```bash
RDS_SERVER_PORT=5050 rds-server
RDS_DASHBOARD_PORT=5051 rds-dashboard
```

---

### Dashboard shows "No agents yet"

1. Make sure the agent is running (`rds-agent --config config.json`)
2. Check that `server_url` in `config.json` matches where the server is actually running
3. Wait 5–10 seconds — agents appear after the first heartbeat

---

### Dashboard shows "Update failed — retrying…"

The server is not reachable from the dashboard browser. Check that `rds-server` is still running in another terminal.

---

### On Windows: "pywin32 not installed" warning

Run the full install:
```bat
pip install pywin32
```

---

### Port binding permission denied on Linux

On Linux, binding to ports below 1024 requires root. The app uses 5000/5001 by default which should work without root. If you see this error, check something else isn't claiming those ports.

---

### I want to wipe all alerts and start fresh

Stop the server, then delete the database:
```bash
rm data.db
```
The server will create a fresh one on next start.

---

## 11. Project Structure

```
ransomware-detector/
│
├── install.sh / install.bat / install.ps1   ← One-time setup (Linux/macOS/Windows)
├── run.sh / run.bat                          ← Start everything + open browser
├── pyproject.toml                            ← Python package definition
├── config.json                               ← Your working configuration
├── config.example.json                       ← Template (do not edit directly)
├── data.db                                   ← SQLite database (auto-created)
├── Dockerfile / docker-compose.yml           ← Container deployment
│
├── launcher/
│   └── main.py                               ← Windows tray app entry point
│
├── windows/                                  ← Windows EXE build files
│   ├── build.py                              ← Run this on Windows to build the exe
│   ├── RansomGuard.spec                      ← PyInstaller configuration
│   ├── setup.iss                             ← Inno Setup installer script
│   └── WINDOWS_BUILD.md                      ← Windows build instructions
│
├── agents/                                   ← Agent (runs on monitored machines)
│   ├── agent_client.py                       ← Main agent loop
│   ├── file_monitor.py                       ← File system watcher
│   ├── network_monitor.py                    ← Connection count monitor
│   └── external_device_monitor.py            ← USB drive scanner
│
├── server/                                   ← Central API server
│   ├── main_server.py                        ← Flask app + all endpoints
│   ├── database.py                           ← SQLite database layer
│   ├── alert_system.py                       ← Alert management
│   └── detection_engine.py                   ← Statistics computation
│
├── dashboard/                                ← Web dashboard
│   ├── app.py                                ← Flask server (serves HTML)
│   ├── mobile_api.py                         ← Mobile client endpoints
│   └── templates/index.html                  ← Single-page dashboard UI
│
├── ml_detector/                              ← Optional ML scanning
│   ├── realtime_scanner.py
│   ├── train_model.py
│   └── virus_total_api.py
│
├── utils/                                    ← Shared utilities
│   ├── config.py                             ← Configuration loader
│   ├── entropy_calculator.py                 ← File entropy analysis
│   └── portable_scanner.py                   ← Folder scanner
│
├── cloud/                                    ← Optional cloud integrations
│   ├── firebase_config.py                    ← Firebase push notifications
│   ├── telegram_bot.py                       ← Telegram alert bot
│   └── webhook_server.py                     ← Incoming webhook receiver
│
├── tests/
│   └── smoke_test.py                         ← Automated API smoke test
│
└── docs/
    └── DOCUMENTATION.md                      ← This file
```

---

*Last updated: March 2026 | MIT License*
