<div align="center">

# 🛡️ RansomGuard

**Real-time ransomware detection — monitor files, network, and USB drives across multiple machines from a single dashboard.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](#installation)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)

</div>

---

## ✨ What It Does

RansomGuard watches your machines for ransomware activity and alerts you in real time:

| Monitor | What It Detects |
|---|---|
| 📁 **Files** | Suspicious extensions (`.locked`, `.encrypted`), high-entropy (encrypted) content, bulk file renames |
| 🌐 **Network** | Unusually high outbound connection counts |
| 🔌 **USB Drives** | Auto-scans removable devices on insert |

Alerts flow to a central server and appear instantly on a live web dashboard.

---

## 🚀 Quick Start

### 🐧 Linux / macOS

```bash
bash install.sh      # one-time setup (creates .venv, installs deps)
bash run.sh          # starts server + dashboard, opens browser
```

### 🪟 Windows — EXE Installer *(easiest)*

Build a one-click installer on any Windows machine (no Python knowledge needed):

```bat
python windows\build.py
```

Produces `windows\dist\RansomGuard-Setup.exe` — a standard wizard installer.  
After install, a 🛡️ **shield icon** appears in the system tray and the dashboard opens automatically.

> See [`windows/WINDOWS_BUILD.md`](windows/WINDOWS_BUILD.md) for full build instructions.

### 🪟 Windows — Script

```bat
install.bat    :: one-time setup
run.bat        :: start server + dashboard
```

### 🐳 Docker

```bash
docker compose up
# Dashboard → http://localhost:5001
# API       → http://localhost:5000
```

---

## 🖥️ Dashboard

Open **http://localhost:5001** after starting the app.

| Section | What You See |
|---|---|
| **Dashboard** | Live stat cards (agents online, alert counts) + chart + recent alerts |
| **Agents** | All connected machines with status, platform, last-seen time |
| **Alerts** | Full alert history with filter by level / status / text search + Acknowledge button |

Real-time WebSocket updates — new alerts pop up as toasts without refreshing.

---

## 🔧 CLI Commands

After `bash install.sh` (or `install.bat`):

| Command | Description |
|---|---|
| `rds-server` | Start the API server on port 5000 |
| `rds-dashboard` | Start the web dashboard on port 5001 |
| `rds-agent --config config.json` | Start monitoring on a machine |
| `bash run.sh` | Start server + dashboard together |
| `python tests/smoke_test.py` | Run automated smoke test (7 checks) |
| `python docs/generate_pdf.py` | Regenerate the PDF documentation |

---

## ⚙️ Configuration

Copy the example config and edit:

```bash
cp config.example.json config.json
```

Key settings in `config.json`:

| Setting | Default | Description |
|---|---|---|
| `server_url` | `http://localhost:5000` | Where agents send alerts |
| `agent_id` | hostname | Unique name for this machine |
| `watch_paths` | `["."]` | Folders to monitor |
| `heartbeat_interval` | `5` | Agent check-in interval (seconds) |
| `entropy_threshold` | `7.5` | Flag files above this entropy (0‒8) |
| `file_change_rate_threshold` | `120` | Alert above this many changes/minute |
| `enable_file_monitor` | `true` | Toggle file monitoring |
| `enable_network_monitor` | `true` | Toggle network monitoring |
| `enable_external_device_monitor` | `true` | Toggle USB monitoring |

### Environment Variables

```bash
RDS_SERVER_HOST=0.0.0.0        # bind server to all interfaces
RDS_SERVER_PORT=5000
RDS_DASHBOARD_HOST=0.0.0.0
RDS_DASHBOARD_PORT=5001
RDS_DATA_DIR=/path/to/data     # where data.db is stored
RDS_SECRET_KEY=your-secret     # set in production
RDS_USER=admin                 # API login
RDS_PASSWORD=admin
VIRUS_TOTAL_API_KEY=...        # optional
TELEGRAM_BOT_TOKEN=...         # optional
```

---

## 🏗️ Project Structure

```
ransomware-detector/
│
├── install.sh / install.bat / install.ps1  ← One-time setup
├── run.sh / run.bat                         ← Launch server + dashboard
├── pyproject.toml                           ← Python package (rds-* CLI commands)
├── config.example.json                      ← Default configuration template
│
├── launcher/
│   └── main.py                              ← Windows tray app (starts all services)
│
├── windows/                                 ← Windows EXE build pipeline
│   ├── build.py                             ← Run on Windows to produce Setup.exe
│   ├── RansomGuard.spec                     ← PyInstaller bundle config
│   ├── setup.iss                            ← Inno Setup installer script
│   └── WINDOWS_BUILD.md                     ← Build instructions
│
├── agents/                                  ← Monitoring agent
│   ├── agent_client.py                      ← Main agent loop
│   ├── file_monitor.py                      ← Watchdog file watcher
│   ├── network_monitor.py                   ← psutil connection monitor
│   └── external_device_monitor.py           ← USB scanner
│
├── server/                                  ← Central API server
│   ├── main_server.py                       ← Flask + Socket.IO + JWT
│   ├── database.py                          ← SQLite layer (alerts/agents/commands)
│   ├── alert_system.py                      ← Alert management
│   └── detection_engine.py                  ← Aggregate statistics
│
├── dashboard/                               ← Web UI
│   ├── app.py                               ← Flask server
│   └── templates/index.html                 ← Single-page dashboard
│
├── utils/                                   ← Shared helpers
│   ├── config.py                            ← Config loader (json + env vars)
│   ├── entropy_calculator.py                ← Shannon entropy scorer
│   └── portable_scanner.py                  ← Folder scanner
│
├── ml_detector/                             ← Optional ML scanning
│   ├── realtime_scanner.py
│   ├── train_model.py
│   └── virus_total_api.py
│
├── cloud/                                   ← Optional integrations
│   ├── firebase_config.py
│   ├── telegram_bot.py
│   └── webhook_server.py
│
├── tests/
│   └── smoke_test.py                        ← Automated API smoke test
│
├── docs/
│   ├── DOCUMENTATION.md                     ← Full user guide
│   ├── DOCUMENTATION.pdf                    ← Generated PDF
│   └── generate_pdf.py                      ← PDF generator script
│
└── Dockerfile / docker-compose.yml          ← Container deployment
```

---

## 📡 API Reference

Base URL: `http://localhost:5000`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/agents/heartbeat` | Agent check-in |
| `GET` | `/api/agents` | List all agents |
| `POST` | `/api/alerts` | Submit alert |
| `GET` | `/api/alerts/recent?limit=50` | Recent alerts |
| `POST` | `/api/alert/<id>/acknowledge` | Mark alert resolved |
| `GET` | `/api/stats` | Dashboard summary |
| `POST` | `/api/device/<id>/isolate` | Isolate an agent |
| `POST` | `/api/scan/external` | Trigger USB scan |
| `GET` | `/api/commands/<agent_id>` | Poll pending commands |

---

## 📄 Documentation

Full user guide with architecture diagrams, step-by-step installation, configuration reference, and troubleshooting:

- **Markdown:** [`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md)
- **PDF:** [`docs/DOCUMENTATION.pdf`](docs/DOCUMENTATION.pdf)

Regenerate the PDF anytime:
```bash
python docs/generate_pdf.py
```

---

## 📋 Notes

- Device isolation is a safe simulation — no destructive actions.
- VirusTotal scanning is optional and rate-limited by your API key.
- On Linux, USB detection uses `pyudev` if installed, otherwise falls back to polling.
- `install.sh --full` adds optional ML / cloud / Telegram packages.

---

## License

MIT — see [LICENSE](LICENSE) for details.
