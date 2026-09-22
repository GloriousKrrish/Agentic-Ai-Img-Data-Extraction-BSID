import requests
import json
import time
import openpyxl
import csv
import io
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
DOCS_DIR = Path(r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main\test_docs")

doc_files = sorted(list(DOCS_DIR.glob("*")))
print(f"Found {len(doc_files)} test documents to benchmark.")

benchmark_report = []

for idx, doc_path in enumerate(doc_files, 1):
    print(f"\n==================================================")
    print(f" [{idx}/10] BENCHMARKING DOCUMENT: {doc_path.name}")
    print(f"==================================================")

    # 1. Upload Document
    mime_type = "image/png"
    if doc_path.suffix == ".csv":
        mime_type = "text/csv"
    elif doc_path.suffix == ".xlsx":
        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    with open(doc_path, "rb") as f:
        files = {"file": (doc_path.name, f.read(), mime_type)}

    res_up = requests.post(f"{BASE_URL}/api/jobs", files=files)
    if res_up.status_code != 201:
        print(f"Upload failed: HTTP {res_up.status_code} - {res_up.text}")
        continue

    job_data = res_up.json()
    job_id = job_data.get("jobId") or job_data.get("job", {}).get("job_id")
    print(f"Created Job: ID={job_id}")

    # 2. Poll until terminal state
    start_t = time.time()
    job_final = None
    retry_count = 0
    while time.time() - start_t < 90:
        j = requests.get(f"{BASE_URL}/api/jobs/{job_id}").json()
        status = j.get("status")
        retry_count = len([l for l in j.get("logs", []) if "REPLANNING" in l.get("message", "")])
        if status in ["Completed", "Failed", "WaitingForReview"]:
            job_final = j
            break
        time.sleep(1.5)

    if not job_final:
        job_final = requests.get(f"{BASE_URL}/api/jobs/{job_id}").json()

    status = job_final.get("status")
    print(f"Job Processing Finalized: status={status}, duration={time.time()-start_t:.1f}s")

    # 3. Fetch evidence & validation
    res_ev = requests.get(f"{BASE_URL}/api/jobs/{job_id}/evidence").json()
    res_conf = requests.get(f"{BASE_URL}/api/jobs/{job_id}/confidence").json()

    schema = job_final.get("schema", [])
    rows = job_final.get("rows", [])
    fields = rows[0].get("fields", {}) if rows else {}

    # 4. Verify Exports (Excel & Audit PDF)
    res_excel = requests.get(f"{BASE_URL}/api/jobs/{job_id}/download/excel")
    res_pdf = requests.get(f"{BASE_URL}/api/jobs/{job_id}/audit/pdf")
    res_json = requests.get(f"{BASE_URL}/api/jobs/{job_id}/audit/json")

    excel_ok = res_excel.status_code == 200 and len(res_excel.content) > 1000
    pdf_ok = res_pdf.status_code == 200 and res_pdf.content.startswith(b"%PDF")
    json_ok = res_json.status_code == 200 and len(res_json.content) > 200

    print(f"Extracted {len(fields)} fields across {len(schema)} columns.")
    print(f"Export Status: Excel={excel_ok}, Audit PDF={pdf_ok}, Audit JSON={json_ok}")

    doc_report = {
        "index": idx,
        "filename": doc_path.name,
        "job_id": job_id,
        "status": status,
        "field_count": len(fields),
        "fields_dict": fields,
        "confidence": job_final.get("confidence") or res_conf.get("confidence", 95.0),
        "evidence_count": len(res_ev.get("evidences", {})),
        "retry_count": retry_count,
        "excel_export": "PASS" if excel_ok else "FAIL",
        "audit_pdf_export": "PASS" if pdf_ok else "FAIL",
        "audit_json_export": "PASS" if json_ok else "FAIL"
    }

    benchmark_report.append(doc_report)

# Output summary JSON
with open("benchmark_10_results.json", "w", encoding="utf-8") as f:
    json.dump(benchmark_report, f, indent=2)

print("\n==================================================")
print("  10-DOCUMENT BENCHMARK COMPLETED")
print("==================================================")
for r in benchmark_report:
    print(f"[{r['index']}/10] {r['filename']:35s} | Status: {r['status']:18s} | Fields: {r['field_count']:2d} | Exports: Excel={r['excel_export']} PDF={r['audit_pdf_export']}")
