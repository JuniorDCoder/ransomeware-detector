import os
import secrets
import time
from typing import Any, Dict

from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager, create_access_token
from flask_cors import CORS

from server.database import Database
from server.alert_system import AlertSystem
from server.detection_engine import DetectionEngine
from cloud.firebase_config import FirebaseManager
from dashboard.mobile_api import mobile_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("RDS_SECRET_KEY", secrets.token_hex(32))
app.config["JWT_SECRET_KEY"] = os.getenv("RDS_JWT_SECRET_KEY", secrets.token_hex(32))
CORS(app)
app.register_blueprint(mobile_bp)

socketio = SocketIO(app, cors_allowed_origins="*")
jwt = JWTManager(app)

DB = Database("data.db")
ALERTS = AlertSystem(DB)
ENGINE = DetectionEngine()
FIREBASE = FirebaseManager()

DEFAULT_USER = os.getenv("RDS_USER", "admin")
DEFAULT_PASS = os.getenv("RDS_PASSWORD", "admin")


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    if username == DEFAULT_USER and password == DEFAULT_PASS:
        token = create_access_token(identity=username)
        return jsonify({"access_token": token})
    return jsonify({"status": "error", "message": "invalid credentials"}), 401


@app.route("/api/agents/heartbeat", methods=["POST"])
def agent_heartbeat():
    payload = request.json or {}
    agent_id = payload.get("agent_id")
    timestamp = payload.get("timestamp", time.time())
    data = payload.get("data", {})

    if not agent_id:
        return jsonify({"status": "error", "message": "missing agent_id"}), 400

    DB.update_agent(agent_id, timestamp, data)
    return jsonify({"status": "ok"})


@app.route("/api/agents", methods=["GET"])
def get_agents():
    agents = DB.get_agents()
    return jsonify({"agents": agents})


@app.route("/api/alerts", methods=["POST"])
def add_alert():
    alert_data = request.json or {}
    alert_id = ALERTS.add_alert(alert_data)
    alert_data["id"] = alert_id

    socketio.emit("alert", alert_data)
    if alert_data.get("level") == "CRITICAL":
        FIREBASE.send_push_notification(
            title=f"CRITICAL: {alert_data.get('type')}",
            body=alert_data.get("message", ""),
            data={"alert_id": str(alert_id)},
        )

    return jsonify({"status": "ok", "id": alert_id})


@app.route("/api/alerts/recent", methods=["GET"])
def recent_alerts():
    limit = int(request.args.get("limit", 50))
    alerts = ALERTS.recent_alerts(limit)
    return jsonify({"alerts": alerts})


@app.route("/api/alert/<int:alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert(alert_id: int):
    data = request.json or {}
    user = data.get("user", "unknown")
    ok = ALERTS.acknowledge(alert_id, user)
    return jsonify({"status": "ok" if ok else "not_found"})


@app.route("/api/stats", methods=["GET"])
def stats():
    agents = DB.get_agents()
    alerts = ALERTS.recent_alerts(500)
    stats_data = ENGINE.compute_stats(agents, alerts)
    return jsonify(stats_data)


@app.route("/api/device/<device_id>/isolate", methods=["POST"])
def isolate_device(device_id: str):
    payload = request.json or {}
    command_payload: Dict[str, Any] = {
        "created_at": time.time(),
        "requested_by": payload.get("initiated_by", "unknown"),
        "source": payload.get("source", "api"),
    }
    cmd_id = DB.add_command(device_id, "ISOLATE", command_payload)
    return jsonify({"status": "queued", "command_id": cmd_id})


@app.route("/api/scan/external", methods=["POST"])
def scan_external():
    payload = request.json or {}
    device_id = payload.get("agent_id")
    command_payload = {
        "created_at": time.time(),
        "device_path": payload.get("device_path"),
    }
    if not device_id:
        return jsonify({"status": "error", "message": "missing agent_id"}), 400
    cmd_id = DB.add_command(device_id, "SCAN_EXTERNAL", command_payload)
    return jsonify({"status": "queued", "command_id": cmd_id})


@app.route("/api/commands/<agent_id>", methods=["GET"])
def get_commands(agent_id: str):
    cmds = DB.get_pending_commands(agent_id)
    return jsonify({"commands": cmds})


@app.route("/api/commands/<int:command_id>/complete", methods=["POST"])
def complete_command(command_id: int):
    payload = request.json or {}
    status = payload.get("status", "completed")
    result = payload.get("result", {})
    DB.complete_command(command_id, status, result)
    return jsonify({"status": "ok"})


@app.route("/api/alerts/realtime", methods=["POST"])
def realtime_alert():
    alert_data = request.json or {}
    alert_data["realtime"] = True
    alert_data["received_at"] = time.time()
    alert_id = ALERTS.add_alert(alert_data)
    alert_data["id"] = alert_id

    socketio.emit("critical_alert", alert_data)
    FIREBASE.sync_alert(alert_data)

    if alert_data.get("level") == "CRITICAL":
        FIREBASE.send_push_notification(
            title=f"CRITICAL: {alert_data.get('type')}",
            body=alert_data.get("message", ""),
            data={"alert_id": str(alert_id)},
        )

    return jsonify({"status": "realtime_alert_processed", "id": alert_id})


def main():
    host = os.getenv("RDS_SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("RDS_SERVER_PORT", "5000"))
    print(f"[RDS Server] Starting on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
