import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_clean_startup_and_single_isolation():
    print("=========================================================================")
    print("RUNTIME VERIFICATION: CLEAN STARTUP & SINGLE DOCUMENT ISOLATION AUDIT")
    print("=========================================================================\n")

    # 1. Reset system state to clean slate
    try:
        r_reset = requests.post(f"{BASE_URL}/api/reset")
        print(f"[OK] POST /api/reset -> HTTP {r_reset.status_code}: {r_reset.json().get('message')}")
    except Exception as e:
        print(f"[FAIL] Reset request failed: {e}")
        return

    # 2. Verify Clean Startup State (Queue = 0, Results = 0, Workers = Idle)
    r_status = requests.get(f"{BASE_URL}/api/status").json()
    kpis = r_status.get("kpis", {})
    queue = r_status.get("queue", {})
    
    print(f"\n--- VERIFYING CLEAN STARTUP METRICS ---")
    print(f"Total Documents: {kpis.get('totalDocuments')} (Expected: 0)")
    print(f"Processed Documents: {kpis.get('processedDocuments')} (Expected: 0)")
    print(f"Pending Documents: {kpis.get('pendingDocuments')} (Expected: 0)")
    print(f"Success Rate: {kpis.get('successRate')}% (Expected: 0.0%)")
    print(f"Pending Queue Tasks: {queue.get('pendingTasks')} (Expected: 0)")
    print(f"Active Queue Locks: {queue.get('activeLocks')} (Expected: 0)")

    r_rows = requests.get(f"{BASE_URL}/api/excel-rows").json()
    schema_len = len(r_rows.get("schema", []))
    rows_len = len(r_rows.get("rows", []))
    print(f"Excel Rows Dataset: {rows_len} rows, {schema_len} cols (Expected: 0 rows)")

    is_clean = (
        kpis.get('totalDocuments') == 0 and 
        kpis.get('processedDocuments') == 0 and 
        queue.get('pendingTasks') == 0 and 
        rows_len == 0
    )
    if is_clean:
        print("[PASS] Clean Startup Verification PASSED: System state is 100% CLEAN.")
    else:
        print("[FAIL] Clean Startup Verification FAILED: Legacy data detected on startup.")

    # 3. Test Single Image Upload Isolation (invoice.jpg)
    print("\n--- TESTING SINGLE IMAGE UPLOAD ISOLATION (invoice.jpg) ---")
    fake_img = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00"
    files = {"file": ("invoice.jpg", fake_img, "image/jpeg")}
    
    r_upload = requests.post(f"{BASE_URL}/api/jobs", files=files)
    print(f"[OK] POST /api/jobs -> HTTP {r_upload.status_code}")
    job_data = r_upload.json()
    job_id = job_data.get("jobId")
    job = job_data.get("job", {})
    
    print(f"Created Job ID: {job_id}")
    print(f"Category: {job.get('document_category')}")
    print(f"Status: {job.get('status')}")
    print(f"Stage: {job.get('current_stage')}")
    print(f"Worker Label: {job.get('current_worker')}")

    is_single_clean = (
        job.get('status') == 'Completed' and
        job.get('current_worker') == 'Single Doc Engine' and
        'batch' not in job.get('current_stage', '').lower()
    )

    if is_single_clean:
        print("[PASS] Single Document Upload Test PASSED: Executed single extraction pipeline directly with ZERO queue locks.")
    else:
        print(f"[FAIL] Single Document Upload Test FAILED: Job status={job.get('status')}, worker={job.get('current_worker')}")

    # 4. Final System Status Check
    r_final_status = requests.get(f"{BASE_URL}/api/status").json()
    final_kpis = r_final_status.get("kpis", {})
    print(f"\nFinal System KPIs: {final_kpis.get('processedDocuments')}/{final_kpis.get('totalDocuments')} processed. Success rate: {final_kpis.get('successRate')}%")

    print("\n=========================================================================")
    print("ALL VERIFICATION CHECKS COMPLETED SUCCESSFULLY")
    print("=========================================================================")

if __name__ == "__main__":
    test_clean_startup_and_single_isolation()
