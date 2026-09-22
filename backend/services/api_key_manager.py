import hashlib
import uuid
import time
from typing import Dict, Any, List, Optional

class ApiKeyManager:
    """
    v4.2 Tenant API Key & Scoped Permission Management Service.
    """
    def __init__(self):
        self.keys_store: Dict[str, Dict[str, Any]] = {}

    def create_api_key(self, tenant_id: str, name: str, scopes: List[str] = None) -> dict:
        raw_key = f"ak_{tenant_id[:4]}_{uuid.uuid4().hex}"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        key_record = {
            "key_id": f"key-{uuid.uuid4().hex[:8]}",
            "tenant_id": tenant_id,
            "name": name,
            "key_hash": key_hash,
            "scopes": scopes or ["documents:read", "jobs:write", "webhooks:manage"],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "last_used_at": None,
            "is_revoked": False
        }
        self.keys_store[key_hash] = key_record
        return {"raw_key": raw_key, "key_info": key_record}

    def validate_key(self, raw_key: str, required_scope: str = None) -> Optional[dict]:
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        key_info = self.keys_store.get(key_hash)
        if not key_info or key_info.get("is_revoked"):
            return None
        if required_scope and required_scope not in key_info.get("scopes", []) and "admin" not in key_info.get("scopes", []):
            return None
        key_info["last_used_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return key_info

api_key_manager = ApiKeyManager()
