import json
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

_DEFAULT_DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_db_path(path: str) -> str:
    """Resolve DB path to absolute. If relative, base it on RDS_DATA_DIR or project root."""
    if os.path.isabs(path):
        return path
    data_dir = os.getenv("RDS_DATA_DIR", _DEFAULT_DATA_DIR)
    return os.path.join(data_dir, path)


class Database:
    def __init__(self, path: str = "data.db"):
        self.path = _resolve_db_path(path)
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT,
                    type TEXT,
                    message TEXT,
                    agent_id TEXT,
                    timestamp REAL,
                    details TEXT,
                    acknowledged INTEGER DEFAULT 0,
                    realtime INTEGER DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    last_seen REAL,
                    data TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT,
                    command TEXT,
                    status TEXT,
                    created_at REAL,
                    payload TEXT,
                    result TEXT
                )
                """
            )

    def add_alert(self, alert: Dict[str, Any]) -> int:
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO alerts (level, type, message, agent_id, timestamp, details, acknowledged, realtime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert.get("level"),
                    alert.get("type"),
                    alert.get("message"),
                    alert.get("agent_id"),
                    alert.get("timestamp"),
                    json.dumps(alert.get("details", {})),
                    int(alert.get("acknowledged", 0)),
                    int(alert.get("realtime", 0)),
                ),
            )
            return int(cur.lastrowid)

    def recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
            rows = cur.fetchall()
        return [self._row_to_alert(r) for r in rows]

    def acknowledge_alert(self, alert_id: int, user: Optional[str] = None) -> bool:
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,)
            )
            return cur.rowcount > 0

    def update_agent(self, agent_id: str, timestamp: float, data: Dict[str, Any]):
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agents (agent_id, last_seen, data)
                VALUES (?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET last_seen=excluded.last_seen, data=excluded.data
                """,
                (agent_id, timestamp, json.dumps(data)),
            )

    def get_agents(self) -> Dict[str, Any]:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM agents")
            rows = cur.fetchall()
        agents: Dict[str, Any] = {}
        for r in rows:
            agents[r["agent_id"]] = {
                "last_seen": r["last_seen"],
                "data": json.loads(r["data"]) if r["data"] else {},
            }
        return agents

    def add_command(self, agent_id: str, command: str, payload: Dict[str, Any]):
        with self._lock, self._connect() as conn:
            created_at = payload.get("created_at") or time.time()
            cur = conn.execute(
                """
                INSERT INTO commands (agent_id, command, status, created_at, payload, result)
                VALUES (?, ?, 'pending', ?, ?, NULL)
                """,
                (agent_id, command, created_at, json.dumps(payload)),
            )
            return int(cur.lastrowid)

    def get_pending_commands(self, agent_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT * FROM commands
                WHERE agent_id = ? AND status = 'pending'
                ORDER BY created_at ASC
                """,
                (agent_id,),
            )
            rows = cur.fetchall()
        return [self._row_to_command(r) for r in rows]

    def complete_command(self, command_id: int, status: str, result: Dict[str, Any]):
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE commands SET status = ?, result = ? WHERE id = ?",
                (status, json.dumps(result), command_id),
            )

    @staticmethod
    def _row_to_alert(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "level": row["level"],
            "type": row["type"],
            "message": row["message"],
            "agent_id": row["agent_id"],
            "timestamp": row["timestamp"],
            "details": json.loads(row["details"]) if row["details"] else {},
            "acknowledged": bool(row["acknowledged"]),
            "realtime": bool(row["realtime"]),
        }

    @staticmethod
    def _row_to_command(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "command": row["command"],
            "status": row["status"],
            "created_at": row["created_at"],
            "payload": json.loads(row["payload"]) if row["payload"] else {},
            "result": json.loads(row["result"]) if row["result"] else {},
        }
