from datetime import datetime

import requests
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

mobile_bp = Blueprint("mobile", __name__)


@mobile_bp.route("/api/mobile/dashboard", methods=["GET"])
@jwt_required()
def mobile_dashboard():
    current_user = get_jwt_identity()
    _ = current_user
    server_url = "http://localhost:5000"

    try:
        alerts_response = requests.get(f"{server_url}/api/alerts/recent?limit=20")
        stats_response = requests.get(f"{server_url}/api/stats")
        agents_response = requests.get(f"{server_url}/api/agents")

        alerts = alerts_response.json().get("alerts", []) if alerts_response.status_code == 200 else []
        stats = stats_response.json() if stats_response.status_code == 200 else {}
        agents = agents_response.json().get("agents", {}) if agents_response.status_code == 200 else {}

        return jsonify(
            {
                "summary": {
                    "critical_alerts": stats.get("alerts_by_level", {}).get("CRITICAL", 0),
                    "warning_alerts": stats.get("alerts_by_level", {}).get("WARNING", 0),
                    "info_alerts": stats.get("alerts_by_level", {}).get("INFO", 0),
                    "agents_online": stats.get("agents_online", 0),
                    "total_alerts": stats.get("total_alerts", 0),
                    "system_health": "good" if stats.get("agents_online", 0) > 0 else "warning",
                },
                "recent_alerts": [
                    {
                        "id": a.get("id"),
                        "level": a.get("level"),
                        "message": a.get("message"),
                        "time": datetime.fromtimestamp(a.get("timestamp", 0)).isoformat(),
                        "agent": a.get("agent_id"),
                    }
                    for a in alerts[:10]
                ],
                "devices": [
                    {
                        "id": device_id,
                        "status": "online"
                        if (datetime.now().timestamp() - info.get("last_seen", 0)) < 60
                        else "offline",
                        "risk_score": info.get("data", {}).get("stats", {}).get("risk_score", 0),
                        "alerts": info.get("data", {}).get("stats", {}).get("alert_count", 0),
                    }
                    for device_id, info in agents.items()
                ],
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mobile_bp.route("/api/mobile/alert/<alert_id>/acknowledge", methods=["POST"])
@jwt_required()
def acknowledge_alert(alert_id):
    current_user = get_jwt_identity()
    server_url = "http://localhost:5000"

    try:
        response = requests.post(
            f"{server_url}/api/alert/{alert_id}/acknowledge", json={"user": current_user}
        )
        if response.status_code == 200:
            return jsonify({"status": "acknowledged"})
        return jsonify({"error": "failed to acknowledge"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mobile_bp.route("/api/mobile/device/<device_id>/details", methods=["GET"])
@jwt_required()
def device_details(device_id):
    server_url = "http://localhost:5000"

    try:
        response = requests.get(f"{server_url}/api/agents")
        if response.status_code == 200:
            agents = response.json().get("agents", {})
            device_info = agents.get(device_id, {})

            alerts_response = requests.get(f"{server_url}/api/alerts/recent?limit=50")
            device_alerts = []
            if alerts_response.status_code == 200:
                all_alerts = alerts_response.json().get("alerts", [])
                device_alerts = [a for a in all_alerts if a.get("agent_id") == device_id]

            return jsonify(
                {
                    "device_info": {
                        "id": device_id,
                        "last_seen": device_info.get("last_seen"),
                        "status": "online"
                        if (datetime.now().timestamp() - device_info.get("last_seen", 0)) < 60
                        else "offline",
                        "stats": device_info.get("data", {}).get("stats", {}),
                        "system": device_info.get("data", {}),
                    },
                    "alerts": [
                        {
                            "id": a.get("id"),
                            "level": a.get("level"),
                            "message": a.get("message"),
                            "time": a.get("timestamp"),
                            "type": a.get("type"),
                        }
                        for a in device_alerts[:20]
                    ],
                }
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@mobile_bp.route("/api/mobile/scan/external", methods=["POST"])
@jwt_required()
def mobile_scan_external():
    _ = get_jwt_identity()
    data = request.json or {}
    device_path = data.get("device_path")
    return jsonify({"status": "scan_started", "device": device_path, "estimated_time": "2-5 minutes"})


@mobile_bp.route("/api/mobile/notifications/register", methods=["POST"])
@jwt_required()
def register_push_notification():
    _ = get_jwt_identity()
    _ = request.json or {}
    return jsonify({"status": "registered"})


@mobile_bp.route("/api/mobile/settings", methods=["GET", "POST"])
@jwt_required()
def mobile_settings():
    _ = get_jwt_identity()
    if request.method == "GET":
        return jsonify(
            {
                "notifications": {
                    "critical_alerts": True,
                    "warning_alerts": True,
                    "info_alerts": False,
                    "device_connected": True,
                    "scan_completed": True,
                },
                "scan_settings": {"auto_scan_usb": True, "deep_scan": False, "scan_on_connect": True},
            }
        )

    _ = request.json or {}
    return jsonify({"status": "updated"})
