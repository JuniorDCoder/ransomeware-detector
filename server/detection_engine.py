import time
from typing import Dict, Any, List


class DetectionEngine:
    def compute_stats(self, agents: Dict[str, Any], alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        alerts_by_level = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
        for alert in alerts:
            level = alert.get("level", "INFO")
            alerts_by_level[level] = alerts_by_level.get(level, 0) + 1

        now = time.time()
        agents_online = 0
        for _, info in agents.items():
            if now - info.get("last_seen", 0) <= 60:
                agents_online += 1

        risk_score = alerts_by_level.get("CRITICAL", 0) * 3
        risk_score += alerts_by_level.get("WARNING", 0) * 2
        risk_score += alerts_by_level.get("INFO", 0)

        return {
            "agents_online": agents_online,
            "total_alerts": len(alerts),
            "alerts_by_level": alerts_by_level,
            "average_risk_score": risk_score / max(len(agents), 1),
        }
