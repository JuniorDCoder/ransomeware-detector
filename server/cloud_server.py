import json
import threading
import time
from typing import Dict

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import firebase_admin
    from firebase_admin import credentials, messaging, db as firebase_db
except Exception:
    firebase_admin = None
    credentials = None
    messaging = None
    firebase_db = None

try:
    import redis
except Exception:
    redis = None


class CloudSyncServer:
    def __init__(self, local_server_url: str = "http://localhost:5000"):
        self.local_server_url = local_server_url
        self.cloud_server = Flask(__name__)
        self.cloud_server.config["SECRET_KEY"] = "change-me"
        self.cloud_server.config["JWT_SECRET_KEY"] = "change-me-too"

        CORS(self.cloud_server)
        self.socketio = SocketIO(self.cloud_server, cors_allowed_origins="*")
        self.jwt = JWTManager(self.cloud_server)

        self.users: Dict[str, Dict] = {}

        self.init_firebase()
        self.redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True) if redis else None

        self.remote_clients = {}
        self.setup_routes()

        self.sync_thread = threading.Thread(target=self.sync_with_local, daemon=True)
        self.sync_thread.start()

    def init_firebase(self):
        if not firebase_admin:
            return
        try:
            cred = credentials.Certificate("firebase-service-account.json")
            firebase_admin.initialize_app(cred, {"databaseURL": "https://your-project.firebaseio.com/"})
        except Exception:
            pass

    def setup_routes(self):
        @self.cloud_server.route("/api/register", methods=["POST"])
        def register():
            data = request.json or {}
            username = data.get("username")
            password = data.get("password")
            email = data.get("email")

            if not username or not password:
                return jsonify({"status": "error", "message": "missing credentials"}), 400

            pw_hash = generate_password_hash(password)

            if firebase_db:
                users_ref = firebase_db.reference("users")
                users_ref.child(username).set(
                    {
                        "email": email,
                        "password": pw_hash,
                        "created_at": time.time(),
                        "devices": [],
                    }
                )
            else:
                self.users[username] = {"email": email, "password": pw_hash}

            access_token = create_access_token(identity=username)
            return jsonify({"status": "success", "access_token": access_token})

        @self.cloud_server.route("/api/login", methods=["POST"])
        def login():
            data = request.json or {}
            username = data.get("username")
            password = data.get("password")

            if firebase_db:
                user = firebase_db.reference(f"users/{username}").get()
                if user and check_password_hash(user.get("password", ""), password):
                    access_token = create_access_token(identity=username)
                    return jsonify({"status": "success", "access_token": access_token})
            else:
                user = self.users.get(username)
                if user and check_password_hash(user.get("password", ""), password):
                    access_token = create_access_token(identity=username)
                    return jsonify({"status": "success", "access_token": access_token})

            return jsonify({"status": "error", "message": "invalid credentials"}), 401

        @self.cloud_server.route("/api/remote/alerts", methods=["GET"])
        @jwt_required()
        def get_remote_alerts():
            current_user = get_jwt_identity()
            try:
                response = requests.get(f"{self.local_server_url}/api/alerts/recent?limit=50")
                if response.status_code == 200:
                    alerts = response.json().get("alerts", [])
                    self.log_remote_access(current_user, "viewed_alerts")
                    return jsonify({"status": "success", "alerts": alerts, "timestamp": time.time()})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.cloud_server.route("/api/remote/stats", methods=["GET"])
        @jwt_required()
        def get_remote_stats():
            try:
                response = requests.get(f"{self.local_server_url}/api/stats")
                if response.status_code == 200:
                    return jsonify(response.json())
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.cloud_server.route("/api/remote/devices", methods=["GET"])
        @jwt_required()
        def get_remote_devices():
            try:
                response = requests.get(f"{self.local_server_url}/api/agents")
                if response.status_code == 200:
                    return jsonify(response.json())
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.cloud_server.route("/api/remote/device/<device_id>/isolate", methods=["POST"])
        @jwt_required()
        def isolate_device(device_id):
            current_user = get_jwt_identity()
            try:
                response = requests.post(
                    f"{self.local_server_url}/api/device/{device_id}/isolate",
                    json={"command": "isolate", "initiated_by": current_user},
                )
                if response.status_code == 200:
                    self.log_remote_action(current_user, "isolate_device", device_id)
                    return jsonify({"status": "success", "message": "device isolated"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.socketio.on("connect")
        def handle_connect():
            client_id = request.sid
            self.remote_clients[client_id] = {"connected_at": time.time(), "ip": request.remote_addr}

        @self.socketio.on("subscribe_updates")
        @jwt_required()
        def handle_subscribe():
            current_user = get_jwt_identity()
            client_id = request.sid
            self.remote_clients[client_id]["user"] = current_user
            self.remote_clients[client_id]["subscribed"] = True
            emit("subscribed", {"status": "Receiving real-time updates"})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            client_id = request.sid
            if client_id in self.remote_clients:
                del self.remote_clients[client_id]

    def sync_with_local(self):
        while True:
            try:
                response = requests.get(f"{self.local_server_url}/api/alerts/recent?limit=100")
                if response.status_code == 200:
                    alerts = response.json().get("alerts", [])
                    if firebase_db:
                        alerts_ref = firebase_db.reference("alerts")
                        for alert in alerts:
                            alert_id = alert.get("id", str(time.time()))
                            alerts_ref.child(str(alert_id)).set(alert)
                    if alerts:
                        self.socketio.emit("alerts_update", {"alerts": alerts[:10]})

                response = requests.get(f"{self.local_server_url}/api/stats")
                if response.status_code == 200:
                    stats = response.json()
                    self.socketio.emit("stats_update", stats)

                time.sleep(5)
            except Exception:
                time.sleep(10)

    def log_remote_access(self, user: str, action: str):
        if not self.redis_client:
            return
        log_entry = {
            "user": user,
            "action": action,
            "timestamp": time.time(),
            "ip": request.remote_addr if hasattr(request, "remote_addr") else "unknown",
        }
        self.redis_client.lpush("access_logs", json.dumps(log_entry))
        self.redis_client.ltrim("access_logs", 0, 999)

    def log_remote_action(self, user: str, action: str, target: str):
        if not self.redis_client:
            return
        log_entry = {"user": user, "action": action, "target": target, "timestamp": time.time()}
        self.redis_client.lpush("action_logs", json.dumps(log_entry))

    def start(self, host: str = "0.0.0.0", port: int = 5002):
        self.socketio.run(
            self.cloud_server, host=host, port=port, debug=False, allow_unsafe_werkzeug=True
        )


if __name__ == "__main__":
    CloudSyncServer().start()
