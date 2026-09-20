"""Test frontend upload pipeline via backend API"""
import requests
import json
import time

# Upload test bill.png
with open("test_bill.png", "rb") as f:
    img_bytes = f.read()

print("Uploading test_bill.png via POST /api/jobs ...")
r = requests.post(
    "http://127.0.0.1:8000/api/jobs",
    files={"file": ("test bill.png", img_bytes, "image/png")},
    timeout=60
)
print(f"Upload HTTP Status: {r.status_code}")
data = r.json()
job_id = data.get("jobId")
print(f"Job ID: {job_id}")

# Poll until complete
print("Polling for completion...")
for i in range(90):
    time.sleep(1)
    jr = requests.get(f"http://127.0.0.1:8000/api/jobs/{job_id}", timeout=10)
    j = jr.json()
    status = j.get("status")
    stage = j.get("current_stage")
    progress = j.get("progress")
    print(f"  [{i+1}s] status={status!r}  stage={stage!r}  progress={progress}%")
    if status in ["Completed", "Failed"]:
        print()
        print("=" * 60)
        print("FINAL JOB RESULT")
        print("=" * 60)
        print(f"  Status    : {status}")
        doc_cat = j.get("document_category")
        doc_title = j.get("document_title")
        print(f"  Category  : {doc_cat}")
        print(f"  Title     : {doc_title}")
        schema = j.get("schema", [])
        rows = j.get("rows", [])
        print(f"  Schema    : {len(schema)} columns")
        print(f"  Rows      : {len(rows)}")
        if rows:
            fields = rows[0].get("fields", {})
            filled = {k: v for k, v in fields.items() if v}
            print(f"  Fields filled: {len(filled)}/{len(fields)}")
            print()
            print("  Extracted field values:")
            for k, v in fields.items():
                indicator = "OK" if v else "  "
                print(f"    [{indicator}] {k}: {v!r}")
        if j.get("error"):
            print(f"  Error: {j.get('error')}")
        break
