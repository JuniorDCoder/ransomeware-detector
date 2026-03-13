from datetime import datetime
from typing import Dict, Any, List

try:
    import firebase_admin
    from firebase_admin import credentials, db, messaging
except Exception:
    firebase_admin = None
    credentials = None
    db = None
    messaging = None


class FirebaseManager:
    def __init__(self, service_account_path: str = "firebase-service-account.json"):
        self.service_account_path = service_account_path
        self.initialized = False

        if not firebase_admin:
            return

        try:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(
                cred,
                {
                    "databaseURL": "https://your-project.firebaseio.com/",
                    "storageBucket": "your-project.appspot.com",
                },
            )
            self.initialized = True
        except Exception:
            self.initialized = False

    def sync_alert(self, alert: Dict[str, Any]) -> bool:
        if not self.initialized:
            return False
        try:
            ref = db.reference("alerts")
            alert_id = alert.get("id", str(datetime.now().timestamp()))
            ref.child(str(alert_id)).set({**alert, "synced_at": datetime.now().isoformat()})
            return True
        except Exception:
            return False

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.initialized:
            return []
        try:
            ref = db.reference("alerts")
            alerts = ref.order_by_key().limit_to_last(limit).get() or {}
            return [{"id": key, **value} for key, value in alerts.items()]
        except Exception:
            return []

    def update_device_status(self, device_id: str, status: Dict[str, Any]) -> bool:
        if not self.initialized:
            return False
        try:
            ref = db.reference(f"devices/{device_id}")
            ref.update({**status, "last_update": datetime.now().isoformat()})
            return True
        except Exception:
            return False

    def send_push_notification(self, title: str, body: str, data: Dict[str, Any] = None) -> bool:
        if not self.initialized:
            return False
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                topic="alerts",
            )
            messaging.send(message)
            return True
        except Exception:
            return False

    def send_to_device(self, device_token: str, title: str, body: str, data: Dict[str, Any] = None) -> bool:
        if not self.initialized:
            return False
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=device_token,
            )
            messaging.send(message)
            return True
        except Exception:
            return False
