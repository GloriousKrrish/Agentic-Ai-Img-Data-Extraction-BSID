import requests
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def process_testing_xlsx():
    file_path = Path("testing.xlsx")
    if not file_path.exists():
        print("[FAIL] testing.xlsx not found!")
        return

    print("=========================================================================")
    print("STARTING LIVE EXTRACTION OF testing.xlsx")
    print("=========================================================================\n")

    with open(file_path, "rb") as f:
        files = {"file": ("testing.xlsx", f.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    print("[1] Uploading testing.xlsx to AI Extraction Engine...")
    r = requests.post(f"{BASE_URL}/api/jobs", files=files)
    if r.status_code != 201:
        print(f"[FAIL] Upload failed: HTTP {r.status_code} - {r.text}")
        return

    res = r.json()
    job_id = res.get("jobId")
    print(f"[OK] Uploaded! Created Job ID: '{job_id}'")
    print("\n--- LIVE PROCESSING STREAM ---")

    prev_progress = -1
    completed_job = None

    for _ in range(45):
        time.sleep(1.5)
        r_job = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
        if r_job.status_code == 200:
            j = r_job.json()
            progress = j.get("progress", 0.0)
            stage = j.get("current_stage", "")
            status = j.get("status", "")

            if progress != prev_progress or status in ["Completed", "Failed"]:
                print(f"  [LIVE TELEMETRY] Status: {status:<10} | Progress: {progress:5.1f}% | Stage: {stage}")
                prev_progress = progress

            if status in ["Completed", "Failed"]:
                completed_job = j
                break

    if not completed_job:
        print("\n[TIMEOUT] Processing took longer than expected.")
        return

    if completed_job.get("status") != "Completed":
        print(f"\n[FAIL] Job completed with status '{completed_job.get('status')}'. Error: {completed_job.get('error')}")
        return

    print("\n=========================================================================")
    print("[PASS] AI EXTRACTION COMPLETED SUCCESSFULLY!")
    print(f"Total Extracted Rows: {len(completed_job.get('rows', []))}")
    print(f"Schema Columns Discovered: {len(completed_job.get('schema', []))}")
    print("=========================================================================\n")

    # Download and rewrite into new Excel file
    print("[2] Downloading extracted structured data into new Excel file...")
    r_excel = requests.get(f"{BASE_URL}/api/jobs/{job_id}/download/excel")
    if r_excel.status_code == 200:
        out_name = "extracted_testing_results_v2.xlsx"
        with open(out_name, "wb") as f_out:
            f_out.write(r_excel.content)
        print(f"[SUCCESS] Saved extracted data into brand new Excel file: '{out_name}' ({len(r_excel.content)} bytes)")
    else:
        print(f"[FAIL] Download failed with HTTP {r_excel.status_code}")

if __name__ == "__main__":
    process_testing_xlsx()
