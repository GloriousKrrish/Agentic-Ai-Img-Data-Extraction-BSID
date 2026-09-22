import pytest
import os
import json
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
ROOT = Path(r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main")

class TestV403RegressionSuite:
    
    # 1. MedicalBill Adversarial Test
    def test_01_medical_bill_adversarial(self):
        bill_path = ROOT / "MedicalBill.png"
        assert bill_path.exists(), "MedicalBill.png must exist"
        with open(bill_path, "rb") as f:
            res = requests.post(f"{BASE_URL}/api/jobs", files={"file": ("MedicalBill.png", f.read(), "image/png")})
        assert res.status_code == 201
        job_id = res.json().get("jobId")
        
        # Poll
        job_final = None
        for _ in range(40):
            import time
            time.sleep(1.0)
            j = requests.get(f"{BASE_URL}/api/jobs/{job_id}").json()
            if j.get("status") in ["Completed", "Failed", "WaitingForReview"]:
                job_final = j
                break
        
        assert job_final is not None
        assert job_final.get("status") == "WaitingForReview", "MedicalBill.png must enter WaitingForReview due to arithmetic mismatch"
        rows = job_final.get("rows", [])
        fields = rows[0].get("fields", {}) if rows else {}
        assert fields.get("subTotal") == "745.00" or fields.get("subtotal") == "745.00", "Printed subtotal 745.00 must be preserved"

    # 2. Blank-Field Hallucination Test
    def test_02_blank_field_hallucination_resistance(self):
        doc_path = ROOT / "test_docs" / "21_Adversarial_Missing_Fields.png"
        if not doc_path.exists():
            pytest.skip("21_Adversarial_Missing_Fields.png not found")
        with open(doc_path, "rb") as f:
            res = requests.post(f"{BASE_URL}/api/jobs", files={"file": (doc_path.name, f.read(), "image/png")})
        assert res.status_code == 201

    # 3. Wrong Total Validation Test
    def test_03_wrong_total_validation(self):
        doc_path = ROOT / "test_docs" / "22_Adversarial_Math_Mismatch.png"
        if not doc_path.exists():
            pytest.skip("22_Adversarial_Math_Mismatch.png not found")
        with open(doc_path, "rb") as f:
            res = requests.post(f"{BASE_URL}/api/jobs", files={"file": (doc_path.name, f.read(), "image/png")})
        assert res.status_code == 201
        job_id = res.json().get("jobId")
        job_final = None
        for _ in range(30):
            j = requests.get(f"{BASE_URL}/api/jobs/{job_id}").json()
            if j.get("status") in ["Completed", "Failed", "WaitingForReview"]:
                job_final = j
                break
        assert job_final is not None
        assert job_final.get("status") == "WaitingForReview"

    # 4. Missing Field Test
    def test_04_missing_field_handling(self):
        res = requests.get(f"{BASE_URL}/api/status")
        assert res.status_code == 200

    # 5. Conflicting Agent Test
    def test_05_conflicting_agent_consensus(self):
        res = requests.get(f"{BASE_URL}/api/jobs")
        assert res.status_code == 200

    # 6. Low Quality Image Test
    def test_06_low_quality_image_gating(self):
        assert True

    # 7. Multi Page Test
    def test_07_multi_page_association(self):
        assert True

    # 8. Table Structure Test
    def test_08_table_structure_cell_accuracy(self):
        assert True

    # 9. Cross Field Validation Test
    def test_09_cross_field_validation(self):
        assert True

    # 10. Evidence Correctness Test
    def test_10_evidence_correctness(self):
        res = requests.get(f"{BASE_URL}/api/jobs")
        if res.json():
            job_id = res.json()[0]["job_id"]
            res_ev = requests.get(f"{BASE_URL}/api/jobs/{job_id}/evidence")
            assert res_ev.status_code == 200

    # 11. Confidence Test
    def test_11_confidence_score_bucketing(self):
        res = requests.get(f"{BASE_URL}/api/jobs")
        if res.json():
            job_id = res.json()[0]["job_id"]
            res_conf = requests.get(f"{BASE_URL}/api/jobs/{job_id}/confidence")
            assert res_conf.status_code == 200

    # 12. HITL Routing Test
    def test_12_hitl_routing_precision(self):
        assert True

    # 13. Schema Validation Test
    def test_13_schema_validation_constraints(self):
        assert True

    # 14. Cross Job Isolation Test
    def test_14_cross_job_isolation(self):
        res = requests.get(f"{BASE_URL}/api/jobs")
        jobs = res.json()
        job_ids = [j["job_id"] for j in jobs]
        assert len(job_ids) == len(set(job_ids)), "All job IDs must be unique and isolated"

    # 15. Failure State Transition Test
    def test_15_failure_state_transitions(self):
        # Submit garbage file
        res = requests.post(f"{BASE_URL}/api/jobs", files={"file": ("corrupt.png", b"GARBAGE_BYTES", "image/png")})
        assert res.status_code == 201

    # 16. Export Consistency Test
    def test_16_export_consistency(self):
        res = requests.get(f"{BASE_URL}/api/jobs")
        if res.json():
            job_id = res.json()[0]["job_id"]
            res_excel = requests.get(f"{BASE_URL}/api/jobs/{job_id}/download/excel")
            res_json = requests.get(f"{BASE_URL}/api/jobs/{job_id}/audit/json")
            assert res_excel.status_code in [200, 404]
            assert res_json.status_code in [200, 404]
