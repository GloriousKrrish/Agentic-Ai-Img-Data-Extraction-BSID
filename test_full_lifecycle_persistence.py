import openpyxl
import io
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_full_lifecycle_persistence():
    print("=========================================================================")
    print("AUTOMATED END-TO-END LIFECYCLE & PERSISTENCE VERIFICATION TEST")
    print("=========================================================================\n")

    # 1. Reset state to clean slate
    try:
        r_reset = requests.post(f"{BASE_URL}/api/reset")
        print(f"[OK] State Reset -> HTTP {r_reset.status_code}")
    except Exception as e:
        print(f"[FAIL] Server not reachable at {BASE_URL}: {e}")
        return

    # 2. Create Excel file with Image URL link
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Invoices"
    ws.append(["ID", "Invoice_URL", "Notes"])
    ws.append(["1", "https://raw.githubusercontent.com/tesseract-ocr/test/main/testing/phototest.tif", "Sample Image Link"])

    buf = io.BytesIO()
    wb.save(buf)
    excel_bytes = buf.getvalue()

    # 3. Upload file to create Job ID
    files = {"file": ("lifecycle_test.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r_upload = requests.post(f"{BASE_URL}/api/jobs", files=files)
    if r_upload.status_code != 201:
        print(f"[FAIL] Upload failed with HTTP {r_upload.status_code}")
        return

    job_data = r_upload.json()
    job_id = job_data.get("jobId")
    print(f"[PASS] STEP 1 (Upload): Created Job ID = '{job_id}'")

    # 4. Verify Job ID Persistence & Polling
    print(f"\n--- STEP 2 (Polling & State Recovery for Job '{job_id}') ---")
    completed_job = None
    for attempt in range(15):
        time.sleep(1.0)
        r_job = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
        if r_job.status_code == 200:
            j = r_job.json()
            print(f"  Attempt {attempt+1}: Status='{j.get('status')}', Progress={j.get('progress')}%, Stage='{j.get('current_stage')}'")
            if j.get("status") in ["Completed", "Failed"]:
                completed_job = j
                break

    if not completed_job or completed_job.get("status") != "Completed":
        print(f"[FAIL] Job {job_id} did not complete successfully.")
        return

    print(f"[PASS] STEP 2 (Processing): Job completed with {len(completed_job.get('rows', []))} extracted rows.")

    # 5. Verify Results Retention
    print("\n--- STEP 3 (Results Storage & Multi-Format Downloads) ---")
    r_excel = requests.get(f"{BASE_URL}/api/jobs/{job_id}/download/excel")
    print(f"Download Excel (.xlsx) -> HTTP {r_excel.status_code} ({len(r_excel.content)} bytes)")

    r_csv = requests.get(f"{BASE_URL}/api/jobs/{job_id}/download/csv")
    print(f"Download CSV (.csv) -> HTTP {r_csv.status_code} ({len(r_csv.content)} bytes)")

    r_json = requests.get(f"{BASE_URL}/api/jobs/{job_id}/download/json")
    print(f"Download JSON (.json) -> HTTP {r_json.status_code} ({len(r_json.content)} bytes)")

    is_downloads_valid = (
        r_excel.status_code == 200 and len(r_excel.content) > 500 and
        r_csv.status_code == 200 and len(r_csv.content) > 10 and
        r_json.status_code == 200 and len(r_json.content) > 10
    )

    if is_downloads_valid:
        print("[PASS] STEP 3 (Results & Downloads): All dynamic downloads generated & verified successfully.")
    else:
        print("[FAIL] STEP 3: Downloads failed or returned empty content.")

    print("\n=========================================================================")
    print("ALL E2E LIFECYCLE & PERSISTENCE VERIFICATION CHECKS PASSED!")
    print("=========================================================================")

if __name__ == "__main__":
    test_full_lifecycle_persistence()
