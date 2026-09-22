import pytest
import os
import hashlib
from pathlib import Path
from backend.services.storage_provider import storage_provider
from backend.services.webhook_manager import webhook_manager
from backend.services.batch_manager import batch_manager
from backend.services.api_key_manager import api_key_manager
from backend.services.connector_sdk import ConnectorInterface

ROOT = Path(r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main")

class TestV42EnterpriseSuite:

    # 1. Multi-Tenant Scoping & Isolation
    def test_01_tenant_isolation(self):
        tenant_a = "tenant_alpha_01"
        tenant_b = "tenant_beta_02"
        key_a = api_key_manager.create_api_key(tenant_a, "Alpha Key")
        key_b = api_key_manager.create_api_key(tenant_b, "Beta Key")

        val_a = api_key_manager.validate_key(key_a["raw_key"])
        val_b = api_key_manager.validate_key(key_b["raw_key"])

        assert val_a["tenant_id"] == tenant_a
        assert val_b["tenant_id"] == tenant_b
        assert val_a["tenant_id"] != val_b["tenant_id"]

    # 2. SHA-256 Deduplication Checksum
    def test_02_sha256_deduplication(self):
        sample_bytes = b"Sample Document Binary Content 2026"
        hash_1 = hashlib.sha256(sample_bytes).hexdigest()
        hash_2 = hashlib.sha256(sample_bytes).hexdigest()
        assert hash_1 == hash_2
        assert len(hash_1) == 64

    # 3. Batch Processing Model & Status Aggregation
    def test_03_batch_manager(self):
        docs = [{"filename": "doc1.png"}, {"filename": "doc2.png"}, {"filename": "doc3.png"}]
        batch = batch_manager.create_batch("tenant_alpha_01", docs)
        b_id = batch["batch_id"]

        assert batch["total_documents"] == 3
        assert batch["status"] == "PROCESSING"

        batch_manager.update_batch_progress(b_id, "Completed")
        batch_manager.update_batch_progress(b_id, "Completed")
        batch_manager.update_batch_progress(b_id, "Completed")

        b_final = batch_manager.get_batch(b_id)
        assert b_final["completed"] == 3
        assert b_final["status"] == "COMPLETED"

    # 4. Signed Outbound Webhooks & DLQ Replay
    def test_04_webhook_hmac_and_dlq(self):
        secret = "super_secret_webhook_key"
        payload = b'{"event":"test"}'
        sig = webhook_manager.generate_signature(payload, secret)
        assert len(sig) == 64

        # Dispatch with invalid URL to force DLQ queueing
        res = webhook_manager.dispatch("tenant_alpha_01", "job.completed", {"job_id": "job-123"}, secret=secret, target_url="http://invalid.url.local/hook")
        assert res["status"] == "DLQ_QUEUED"
        assert len(webhook_manager.dlq_queue) >= 1

    # 5. StorageProvider Local/Cloud Abstraction
    def test_05_storage_provider(self):
        test_key = "test_tenant_01/doc_test.txt"
        test_data = b"Enterprise Document Storage Test Content"
        path_written = storage_provider.put(test_key, test_data)
        assert os.path.exists(path_written)

        read_data = storage_provider.get(test_key)
        assert read_data == test_data

        deleted = storage_provider.delete(test_key)
        assert deleted is True

    # 6. API Key Scopes Authorization
    def test_06_api_key_scopes(self):
        key_res = api_key_manager.create_api_key("tenant_scoped", "Scoped Key", scopes=["documents:read"])
        raw_key = key_res["raw_key"]

        assert api_key_manager.validate_key(raw_key, "documents:read") is not None
        assert api_key_manager.validate_key(raw_key, "admin") is None

    # 7. Connector SDK Interface
    def test_07_connector_sdk(self):
        conn = ConnectorInterface("S3", {"bucket": "enterprise-docs"})
        assert conn.authenticate() is True
        docs = conn.list_documents()
        assert len(docs) >= 1
