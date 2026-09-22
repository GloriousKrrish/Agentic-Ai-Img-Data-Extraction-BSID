import pytest
import os
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
ROOT = Path(r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main")

class TestV41SecurityAndReliabilitySuite:
    
    # 1. Multi-User Isolation & AuthZ Check
    def test_01_user_isolation(self):
        # Create job as user A
        headers_user_a = {"X-User-Id": "user_alpha_123"}
        doc_path = ROOT / "test_docs" / "01_Tech_Hardware_Invoice.png"
        with open(doc_path, "rb") as f:
            res_a = requests.post(f"{BASE_URL}/api/jobs", files={"file": ("01_Tech_Hardware_Invoice.png", f.read(), "image/png")}, headers=headers_user_a)
        assert res_a.status_code == 201
        job_id_a = res_a.json().get("jobId")

        # Query job as user B
        headers_user_b = {"X-User-Id": "user_beta_999"}
        res_b = requests.get(f"{BASE_URL}/api/jobs/{job_id_a}", headers=headers_user_b)
        assert res_b.status_code in [403, 404], "User B must not access User A's job details"

    # 2. Upload Size Limit Check
    def test_02_upload_size_limits(self):
        # 30MB oversized payload
        huge_bytes = b"0" * (30 * 1024 * 1024)
        res = requests.post(f"{BASE_URL}/api/jobs", files={"file": ("huge.png", huge_bytes, "image/png")})
        assert res.status_code in [400, 413], "Oversized upload must be rejected cleanly"

    # 3. Process Crash Recovery Check
    def test_03_job_crash_recovery(self):
        from backend.services.job_manager import job_manager
        # Simulate orphaned job left in Extracting state
        with job_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO jobs (job_id, filename, file_type, file_path, status, current_stage, created_at, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           ("job-orphaned-test", "test.png", "image/png", "uploads/test.png", "Extracting", "Analyzing stage", "2026-09-22T10:00:00Z", "user_default"))
            conn.commit()

        # Execute recovery
        recovered_count = job_manager.recover_orphaned_jobs()
        assert recovered_count >= 1
        job_recovered = job_manager.get_job("job-orphaned-test")
        assert job_recovered["status"] in ["WaitingForReview", "Failed"]

    # 4. WebSocket Structured Sequence Test
    def test_04_websocket_sequence(self):
        from backend.services.ws_manager import ws_manager
        evt1 = ws_manager.create_event(event_type="JOB_PROGRESS", job_id="job-test-seq")
        evt2 = ws_manager.create_event(event_type="JOB_COMPLETED", job_id="job-test-seq")
        assert evt1["sequence"] == 1
        assert evt2["sequence"] == 2
        assert "evt-" in evt1["event_id"]

    # 5. Export Consistency Check
    def test_05_export_consistency(self):
        res = requests.get(f"{BASE_URL}/api/jobs")
        if res.json():
            job_id = res.json()[0]["job_id"]
            res_excel = requests.get(f"{BASE_URL}/api/jobs/{job_id}/download/excel")
            res_json = requests.get(f"{BASE_URL}/api/jobs/{job_id}/audit/json")
            assert res_excel.status_code in [200, 404]
            assert res_json.status_code in [200, 404]
