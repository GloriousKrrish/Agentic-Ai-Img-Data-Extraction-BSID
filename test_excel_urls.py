import openpyxl
import io
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_excel_with_image_urls():
    print("=========================================================================")
    print("TESTING EXCEL FILE UPLOAD CONTAINING IMAGE URLS")
    print("=========================================================================\n")

    # 1. Create a sample in-memory Excel file containing image URLs
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Image Links"

    # Add header
    ws.append(["ID", "Invoice_Image_URL", "Notes"])
    # Add rows with sample publicly accessible invoice/receipt image URLs
    ws.append(["1", "https://raw.githubusercontent.com/tesseract-ocr/test/main/testing/phototest.tif", "Sample receipt image"])

    excel_buffer = io.BytesIO()
    wb.save(excel_buffer)
    excel_bytes = excel_buffer.getvalue()

    # 2. Upload Excel file to /api/jobs
    files = {"file": ("test_url_list.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    try:
        r = requests.post(f"{BASE_URL}/api/jobs", files=files)
        print(f"[OK] Uploaded Excel file -> HTTP {r.status_code}")
        res = r.json()
        job_id = res.get("jobId")

        # Poll job until completed
        print(f"Job ID {job_id} created. Waiting for image link extraction...")
        job = {}
        for _ in range(15):
            time.sleep(1.0)
            r_job = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
            if r_job.status_code == 200:
                job = r_job.json()
                print(f"  Current Status: {job.get('status')} ({job.get('progress')}%) - Stage: {job.get('current_stage')}")
                if job.get("status") in ["Completed", "Failed"]:
                    break

        print(f"\nFinal Job Status: {job.get('status')}")
        print(f"Category: {job.get('document_category')}")
        print(f"Extracted Rows Count: {len(job.get('rows', []))}")
        print(f"Sample Row Fields: {job.get('rows', [{}])[0].get('fields') if job.get('rows') else 'None'}")

        if job.get('status') == 'Completed' and len(job.get('rows', [])) > 0:
            print("\n=========================================================================")
            print("[PASS] EXCEL IMAGE URL EXTRACTION TEST PASSED SUCCESSFUL!")
            print("=========================================================================")
        else:
            print(f"\n[FAIL] Job error: {job.get('error')}")

    except Exception as e:
        print(f"[FAIL] Error testing Excel URL upload: {e}")

if __name__ == "__main__":
    test_excel_with_image_urls()
