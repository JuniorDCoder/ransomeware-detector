r"""
Smoke test — verifies the core API server works end-to-end.
Usage:
    cd /path/to/ransomware-detector
    source .venv/bin/activate        # Linux/macOS
    # .venv\Scripts\activate.bat     # Windows
    python tests/smoke_test.py
"""
import json
import os
import subprocess
import sys
import time

import requests

HOST = os.getenv("RDS_SERVER_HOST", "127.0.0.1")
PORT = int(os.getenv("RDS_SERVER_PORT", "5000"))
BASE = f"http://{HOST}:{PORT}"

PASS = "\033[32m✔\033[0m"
FAIL = "\033[31m✗\033[0m"
SKIP = "\033[33m–\033[0m"


def ok(msg):  print(f"  {PASS}  {msg}")
def err(msg): print(f"  {FAIL}  {msg}"); sys.exit(1)


def wait_for_server(timeout=10):
    for _ in range(timeout * 4):
        try:
            requests.get(f"{BASE}/api/stats", timeout=1)
            return True
        except Exception:
            time.sleep(0.25)
    return False


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("\n  Ransomware Detector — Smoke Test\n  " + "─" * 34)

    # ── 1. Start server ──────────────────────────────────────────────────────
    env = {**os.environ, "RDS_SERVER_HOST": HOST, "RDS_SERVER_PORT": str(PORT)}
    proc = subprocess.Popen(
        [sys.executable, "-m", "server"],
        cwd=project_root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"\n  Starting server (PID {proc.pid})…", end="", flush=True)

    if not wait_for_server():
        proc.terminate()
        err("Server did not start in 10 seconds")
    print(" ready")
    ok(f"Server running at {BASE}")

    try:
        # ── 2. Heartbeat ─────────────────────────────────────────────────────
        r = requests.post(f"{BASE}/api/agents/heartbeat", json={
            "agent_id": "smoke-agent",
            "timestamp": time.time(),
            "data": {"system": {"platform": "smoke-test", "python": "3.x"}},
        }, timeout=5)
        assert r.status_code == 200 and r.json()["status"] == "ok", r.text
        ok("POST /api/agents/heartbeat → 200 OK")

        # ── 3. Agents list ───────────────────────────────────────────────────
        r = requests.get(f"{BASE}/api/agents", timeout=5)
        assert r.status_code == 200
        agents = r.json().get("agents", {})
        assert "smoke-agent" in agents, f"Expected smoke-agent in agents: {agents}"
        ok("GET  /api/agents → smoke-agent present")

        # ── 4. Post alert ────────────────────────────────────────────────────
        r = requests.post(f"{BASE}/api/alerts", json={
            "level": "CRITICAL",
            "type": "SMOKE_TEST",
            "message": "Automated smoke test alert",
            "agent_id": "smoke-agent",
        }, timeout=5)
        assert r.status_code == 200
        alert_id = r.json().get("id")
        assert alert_id is not None
        ok(f"POST /api/alerts → alert_id={alert_id}")

        # ── 5. Retrieve stats ─────────────────────────────────────────────────
        r = requests.get(f"{BASE}/api/stats", timeout=5)
        assert r.status_code == 200
        stats = r.json()
        assert "agents_online" in stats and "total_alerts" in stats
        assert stats["total_alerts"] >= 1
        ok(f"GET  /api/stats → agents_online={stats['agents_online']}, total_alerts={stats['total_alerts']}")

        # ── 6. Recent alerts ──────────────────────────────────────────────────
        r = requests.get(f"{BASE}/api/alerts/recent?limit=10", timeout=5)
        assert r.status_code == 200
        alerts_list = r.json().get("alerts", [])
        assert any(a.get("id") == alert_id for a in alerts_list)
        ok("GET  /api/alerts/recent → alert appears in list")

        # ── 7. Acknowledge alert ──────────────────────────────────────────────
        r = requests.post(f"{BASE}/api/alert/{alert_id}/acknowledge",
                          json={"user": "smoke-tester"}, timeout=5)
        assert r.status_code == 200 and r.json()["status"] == "ok"
        ok(f"POST /api/alert/{alert_id}/acknowledge → ok")

    finally:
        proc.terminate()
        proc.wait(timeout=5)
        print(f"\n  Server stopped.\n")

    print("  \033[32mAll smoke tests passed!\033[0m\n")


if __name__ == "__main__":
    main()
