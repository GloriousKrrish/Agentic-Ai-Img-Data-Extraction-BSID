import time
import hmac
import hashlib
import json
import uuid
import requests
from typing import Dict, Any, List, Optional

class WebhookManager:
    """
    v4.2 Outbound Webhook Engine.
    Supports payload HMAC SHA-256 signatures, retry tracking, and Dead Letter Queue (DLQ).
    """
    def __init__(self):
        self.webhook_configs: Dict[str, Dict[str, Any]] = {}
        self.dlq_queue: List[Dict[str, Any]] = []

    def register_webhook(self, tenant_id: str, url: str, secret: str = "webhook_secret_key") -> str:
        webhook_id = f"wh-{uuid.uuid4().hex[:8]}"
        self.webhook_configs[webhook_id] = {
            "webhook_id": webhook_id,
            "tenant_id": tenant_id,
            "url": url,
            "secret": secret,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        return webhook_id

    def generate_signature(self, payload_bytes: bytes, secret: str) -> str:
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    def dispatch(self, tenant_id: str, event_type: str, data: dict, secret: str = "webhook_secret_key", target_url: str = None) -> dict:
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        payload = {
            "event_id": event_id,
            "event_type": event_type,
            "tenant_id": tenant_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "data": data
        }
        payload_bytes = json.dumps(payload).encode("utf-8")
        signature = self.generate_signature(payload_bytes, secret)
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": event_type
        }

        if not target_url:
            return {"status": "SKIPPED", "message": "No target URL configured"}

        # Attempt HTTP delivery with retry
        for attempt in range(1, 3):
            try:
                res = requests.post(target_url, data=payload_bytes, headers=headers, timeout=5)
                if res.status_code == 200:
                    return {"status": "DELIVERED", "event_id": event_id, "attempts": attempt}
            except Exception:
                time.sleep(0.5)

        # Move to Dead Letter Queue (DLQ) if delivery fails
        dlq_entry = {
            "event_id": event_id,
            "tenant_id": tenant_id,
            "target_url": target_url,
            "payload": payload,
            "secret": secret,
            "failed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        self.dlq_queue.append(dlq_entry)
        return {"status": "DLQ_QUEUED", "event_id": event_id, "message": "Delivery failed; added to DLQ"}

    def replay_dlq(self) -> List[dict]:
        replayed = []
        for item in list(self.dlq_queue):
            res = self.dispatch(
                item["tenant_id"],
                item["payload"]["event_type"],
                item["payload"]["data"],
                secret=item["secret"],
                target_url=item["target_url"]
            )
            if res.get("status") == "DELIVERED":
                self.dlq_queue.remove(item)
                replayed.append(res)
        return replayed

webhook_manager = WebhookManager()
