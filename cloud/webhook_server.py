import os
import time
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

SERVER_URL = os.getenv("RDS_SERVER_URL", "http://localhost:5000")


@app.route("/webhook/alert", methods=["POST"])
def webhook_alert():
    payload = request.json or {}
    payload.setdefault("timestamp", time.time())
    try:
        requests.post(f"{SERVER_URL}/api/alerts", json=payload, timeout=5)
    except Exception:
        pass
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
