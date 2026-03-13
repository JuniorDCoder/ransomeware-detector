import time
from typing import Any, Dict, List

from server.database import Database


class AlertSystem:
    def __init__(self, db: Database):
        self.db = db

    def add_alert(self, alert: Dict[str, Any]) -> int:
        alert.setdefault("timestamp", time.time())
        return self.db.add_alert(alert)

    def recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.db.recent_alerts(limit)

    def acknowledge(self, alert_id: int, user: str) -> bool:
        return self.db.acknowledge_alert(alert_id, user)
