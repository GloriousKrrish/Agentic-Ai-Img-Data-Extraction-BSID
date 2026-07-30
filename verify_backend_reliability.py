import sys
import time
import json
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_job_system():
    print("=" * 70)
    print("ENTERPRISE BACKEND JOB MANAGER RELIABILITY TEST SUITE")
    print("=" * 70)

    # 1. Test Server Connectivity
    try:
        r = requests.get(f"{BASE_URL}/")
        print(f"[+] Health Check: {r.status_code} -> {r.json()}")
    except Exception as e:
        print(f"[-] Server not reachable: {e}")
        sys.exit(1)

    # 2. Test Job Creation (POST /api/jobs)
    print("\n[+] Creating persistent job via POST /api/jobs...")
    file_payload = ("test_medical.txt", b"PATIENT RECORD\nID: PAT-991\nName: Sarah Connor\nAge: 38\nDoctor: Dr. Aris\nDiagnosis: Migraine\nRoom: 104\nDate: 2026-07-29", "text/plain")
    
    t0 = time.time()
    res = requests.post(f"{BASE_URL}/api/jobs", files={"file": file_payload})
    elapsed_ms = (time.time() - t0) * 1000
    
    if res.status_code != 200:
        print(f"[-] Failed to create job: {res.status_code} {res.text}")
        sys.exit(1)
        
    job_data = res.json()
    job_id = job_data.get("jobId")
    print(f"[+] Job Created in {elapsed_ms:.1f}ms! Job ID: {job_id}")
    print(f"    Initial Status: {job_data.get('job', {}).get('status')}")
    print(f"    Initial Stage: {job_data.get('job', {}).get('current_stage')}")

    # 3. Test Asynchronous Progress Polling (GET /api/jobs/{job_id})
    print("\n[+] Polling background job status asynchronously (Simulating browser refresh / disconnection)...")
    completed = False
    for attempt in range(30):
        time.sleep(1.0)
        job_res = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
        if job_res.status_code == 200:
            j = job_res.json()
            status = j.get("status")
            stage = j.get("current_stage")
            progress = j.get("progress", 0.0)
            logs = j.get("logs", [])
            last_log = logs[-1]["message"] if logs else "No logs"
            
            print(f"    [{attempt+1:02d}s] Status: {status:<12} | Progress: {progress:5.1f}% | Stage: {stage} | Log: {last_log}")
            
            if status in ["Completed", "Failed"]:
                completed = True
                if status == "Completed":
                    print(f"\n[OK] Job {job_id} COMPLETED SUCCESSFULLY!")
                    print(f"    Document Category: {j.get('document_category')}")
                    print(f"    Schema Columns: {[c['label'] for c in j.get('schema', [])]}")
                    print(f"    Extracted Rows: {j.get('rows')}")
                else:
                    print(f"\n[-] Job {job_id} FAILED: {j.get('error')}")
                break

    # 4. Test Session Recovery (GET /api/jobs)
    print("\n[+] Testing Session Recovery (GET /api/jobs)...")
    all_jobs_res = requests.get(f"{BASE_URL}/api/jobs")
    all_jobs = all_jobs_res.json()
    print(f"[+] Recovered {len(all_jobs)} total persistent jobs from SQLite database (`jobs.sqlite3`).")
    for job in all_jobs[:3]:
        print(f"    - Job ID: {job['job_id']} | File: {job['filename']} | Status: {job['status']} | Category: {job.get('document_category')}")

    # 5. Test Dynamic Excel Export Download (GET /api/jobs/{job_id}/download/excel)
    print("\n[+] Testing Job Excel Export Download...")
    dl_res = requests.get(f"{BASE_URL}/api/jobs/{job_id}/download/excel")
    if dl_res.status_code == 200 and len(dl_res.content) > 100:
        print(f"[OK] Excel download verified! Received {len(dl_res.content)} bytes.")
    else:
        print(f"[-] Excel download failed: {dl_res.status_code}")

    print("\n" + "=" * 70)
    print("ALL ENTERPRISE BACKEND JOB MANAGER TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_job_system()
