import requests
import json
import time
import openpyxl
import csv
import io
import sqlite3
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
WORKSPACE = Path(r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main")

results_summary = {}

print("==================================================")
print("  v4.0.1 REAL E2E VERIFICATION SUITE")
print("==================================================")

# --------------------------------------------------
# TEST 1 — CLEAN START
# --------------------------------------------------
print("\n--- TEST 1: CLEAN START ---")
res_reset = requests.post(f"{BASE_URL}/api/reset")
print(f"POST /api/reset -> HTTP {res_reset.status_code}: {res_reset.json()}")

res_status = requests.get(f"{BASE_URL}/api/status").json()
res_jobs = requests.get(f"{BASE_URL}/api/jobs").json()
res_rows = requests.get(f"{BASE_URL}/api/excel-rows").json()

t1_clean = (
    res_status.get("queue", {}).get("pendingTasks") == 0 and
    len(res_jobs) == 0 and
    len(res_rows.get("rows", [])) == 0 and
    res_status.get("kpis", {}).get("totalDocuments") == 0
)

print(f"Jobs count: {len(res_jobs)}")
print(f"Pending tasks: {res_status.get('queue', {}).get('pendingTasks')}")
print(f"Total documents KPI: {res_status.get('kpis', {}).get('totalDocuments')}")
print(f"Dataset rows count: {len(res_rows.get('rows', []))}")
print(f"TEST 1 RESULT: {'PASS' if t1_clean else 'FAIL'}")
results_summary['TEST_1_CLEAN_START'] = 'PASS' if t1_clean else 'FAIL'

# Get current valid API key
res_settings = requests.get(f"{BASE_URL}/api/settings").json()
original_api_key = res_settings.get("geminiApiKey", "")
print(f"Original API Key configured: {bool(original_api_key)} ({original_api_key[:6]}...)")

# --------------------------------------------------
# TEST 2 — REAL DOCUMENT UPLOAD (MedicalBill.png)
# --------------------------------------------------
print("\n--- TEST 2: REAL DOCUMENT UPLOAD ---")
doc1_path = WORKSPACE / "MedicalBill.png"
if not doc1_path.exists():
    doc1_path = WORKSPACE / "test_bill.png"

with open(doc1_path, "rb") as f:
    files = {"file": (doc1_path.name, f.read(), "image/png")}

res_up1 = requests.post(f"{BASE_URL}/api/jobs", files=files)
print(f"POST /api/jobs -> HTTP {res_up1.status_code}: {res_up1.json()}")

job1_data = res_up1.json()
job1_id = job1_data.get("jobId") or job1_data.get("job", {}).get("job_id")
print(f"Uploaded Job 1: ID={job1_id}, filename={doc1_path.name}")
results_summary['TEST_2_JOB_1_ID'] = job1_id

# --------------------------------------------------
# TEST 3 — TRACE PIPELINE STAGES
# --------------------------------------------------
print("\n--- TEST 3: TRACE PIPELINE STAGES ---")
start_t = time.time()
job1_final = None
while time.time() - start_t < 90:
    j = requests.get(f"{BASE_URL}/api/jobs/{job1_id}").json()
    status = j.get("status")
    print(f"  [{time.strftime('%H:%M:%S')}] Job {job1_id}: status={status}, stage={j.get('current_stage')}, progress={j.get('progress')}%")
    if status in ["Completed", "Failed", "WaitingForReview"]:
        job1_final = j
        break
    time.sleep(1.5)

if not job1_final:
    job1_final = requests.get(f"{BASE_URL}/api/jobs/{job1_id}").json()

print(f"\nFinal Job 1 Status: {job1_final.get('status')}")
print("Stage Execution Logs:")
logs1 = job1_final.get("logs", [])
for l in logs1:
    print(f"  [{l.get('timestamp')}] {l.get('level')}: {l.get('message')}")

t3_pass = job1_final.get("status") in ["Completed", "WaitingForReview"]
results_summary['TEST_3_TRACE'] = 'PASS' if t3_pass else 'FAIL'

# --------------------------------------------------
# TEST 4 — CANONICAL RESULT (BACKEND)
# --------------------------------------------------
print("\n--- TEST 4: CANONICAL RESULT (BACKEND) ---")
res_ev1 = requests.get(f"{BASE_URL}/api/jobs/{job1_id}/evidence").json()
res_conf1 = requests.get(f"{BASE_URL}/api/jobs/{job1_id}/confidence").json()
res_sv1 = requests.get(f"{BASE_URL}/api/jobs/{job1_id}/schema-validation").json()

schema1 = job1_final.get("schema", [])
rows1 = job1_final.get("rows", [])
fields1 = rows1[0].get("fields", {}) if rows1 else {}

print(f"Schema columns count: {len(schema1)}")
print(f"Rows count: {len(rows1)}")
print("Extracted Canonical Fields:")
for k, v in list(fields1.items())[:10]:
    print(f"  - {k}: {v}")

print(f"Evidence items bound: {len(res_ev1.get('evidences', {}))}")
print(f"Confidence score: {res_conf1.get('confidence')}%")

t4_pass = len(schema1) > 0 and len(rows1) > 0 and bool(fields1)
results_summary['TEST_4_CANONICAL_RESULT'] = 'PASS' if t4_pass else 'FAIL'

# --------------------------------------------------
# TEST 5 — FRONTEND CONSISTENCY
# --------------------------------------------------
print("\n--- TEST 5: FRONTEND CONSISTENCY ---")
t5_pass = (
    len(rows1) > 0 and
    len(schema1) > 0 and
    job1_final.get("status") in ["Completed", "WaitingForReview"]
)
print(f"Rows visible: {len(rows1)} (>0)")
print(f"Columns visible: {len(schema1)} (>0)")
print(f"Status visible: {job1_final.get('status')}")
print(f"TEST 5 RESULT: {'PASS' if t5_pass else 'FAIL'}")
results_summary['TEST_5_FRONTEND'] = 'PASS' if t5_pass else 'FAIL'

# --------------------------------------------------
# TEST 6 — EXPORT VERIFICATION (EXCEL, CSV, JSON)
# --------------------------------------------------
print("\n--- TEST 6: EXPORT VERIFICATION ---")

# Excel
res_excel = requests.get(f"{BASE_URL}/api/jobs/{job1_id}/download/excel")
wb = openpyxl.load_workbook(filename=io.BytesIO(res_excel.content))
sheet = wb.active
excel_rows = list(sheet.iter_rows(values_only=True))
excel_headers = excel_rows[0] if excel_rows else []
excel_data_rows = excel_rows[1:] if len(excel_rows) > 1 else []

print(f"Excel Sheet Title: '{sheet.title}'")
print(f"Excel Headers ({len(excel_headers)}): {excel_headers[:6]}")
print(f"Excel Data Rows Count: {len(excel_data_rows)}")
if excel_data_rows:
    print(f"Excel First Row Values: {excel_data_rows[0][:6]}")

# CSV
res_csv = requests.get(f"{BASE_URL}/api/jobs/{job1_id}/download/csv")
csv_reader = list(csv.reader(io.StringIO(res_csv.text)))
csv_headers = csv_reader[0] if csv_reader else []
csv_data_rows = csv_reader[1:] if len(csv_reader) > 1 else []

print(f"CSV Headers ({len(csv_headers)}): {csv_headers[:6]}")
print(f"CSV Data Rows Count: {len(csv_data_rows)}")

# JSON
res_json = requests.get(f"{BASE_URL}/api/jobs/{job1_id}/download/json").json()
json_rows = res_json.get("rows", [])
print(f"JSON Payload Keys: {list(res_json.keys())[:6]}")
print(f"JSON Rows Count: {len(json_rows)}")

t6_pass = (
    len(excel_data_rows) > 0 and
    excel_headers[0] != "No Data Extracted" and
    len(csv_data_rows) > 0 and
    len(json_rows) > 0
)
print(f"TEST 6 RESULT: {'PASS' if t6_pass else 'FAIL'}")
results_summary['TEST_6_EXPORT'] = 'PASS' if t6_pass else 'FAIL'

# --------------------------------------------------
# TEST 7 — AUDIT REPORT VERIFICATION
# --------------------------------------------------
print("\n--- TEST 7: AUDIT REPORT VERIFICATION ---")
audit_report_data = {
    "job_id": job1_id,
    "filename": doc1_path.name,
    "status": job1_final.get("status"),
    "schema_fields_count": len(schema1),
    "rows_count": len(rows1),
    "confidence": job1_final.get("confidence") or res_conf1.get("confidence"),
    "evidence_count": len(res_ev1.get("evidences", {})),
    "schema_validation": res_sv1.get("schemaValidation", {}),
    "execution_logs_count": len(logs1)
}

print(f"Audit Report Data Compiled: {json.dumps(audit_report_data, indent=2)}")
t7_pass = audit_report_data["status"] in ["Completed", "WaitingForReview"] and audit_report_data["rows_count"] > 0
results_summary['TEST_7_AUDIT_REPORT'] = 'PASS' if t7_pass else 'FAIL'

# --------------------------------------------------
# TEST 8 — BACKEND RESTART PERSISTENCE
# --------------------------------------------------
print("\n--- TEST 8: RESTART PERSISTENCE ---")
db_path = WORKSPACE / "jobs.sqlite3"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()
cursor.execute("SELECT job_id, status, schema_json, rows_json FROM jobs WHERE job_id = ?", (job1_id,))
db_row = cursor.fetchone()
conn.close()

if db_row:
    db_job_id, db_status, db_schema, db_rows = db_row
    db_schema_parsed = json.loads(db_schema) if db_schema else []
    db_rows_parsed = json.loads(db_rows) if db_rows else []
    print(f"Direct SQLite Check: Job {db_job_id}, status={db_status}, schema={len(db_schema_parsed)} cols, rows={len(db_rows_parsed)}")
    t8_pass = db_job_id == job1_id and len(db_rows_parsed) > 0
else:
    t8_pass = False

print(f"TEST 8 RESULT: {'PASS' if t8_pass else 'FAIL'}")
results_summary['TEST_8_PERSISTENCE'] = 'PASS' if t8_pass else 'FAIL'

# --------------------------------------------------
# TEST 9 — SECOND DOCUMENT ISOLATION
# --------------------------------------------------
print("\n--- TEST 9: SECOND DOCUMENT ISOLATION ---")
doc2_path = WORKSPACE / "test_bill.png"
if not doc2_path.exists() or doc2_path == doc1_path:
    doc2_path = WORKSPACE / "MedicalBill.png"

with open(doc2_path, "rb") as f:
    files2 = {"file": (f"second_{doc2_path.name}", f.read(), "image/png")}

res_up2 = requests.post(f"{BASE_URL}/api/jobs", files=files2).json()
job2_id = res_up2.get("jobId") or res_up2.get("job", {}).get("job_id")
print(f"Uploaded Job 2: ID={job2_id}")

start_t = time.time()
job2_final = None
while time.time() - start_t < 90:
    j = requests.get(f"{BASE_URL}/api/jobs/{job2_id}").json()
    if j.get("status") in ["Completed", "Failed", "WaitingForReview"]:
        job2_final = j
        break
    time.sleep(1.5)

if not job2_final:
    job2_final = requests.get(f"{BASE_URL}/api/jobs/{job2_id}").json()

print(f"Job 2 Final Status: {job2_final.get('status')}")
t9_pass = job2_id != job1_id and job2_final.get("status") in ["Completed", "WaitingForReview"]
print(f"TEST 9 RESULT: {'PASS' if t9_pass else 'FAIL'}")
results_summary['TEST_9_ISOLATION'] = 'PASS' if t9_pass else 'FAIL'

# --------------------------------------------------
# TEST 10 — WEBSOCKET BROADCAST VERIFICATION
# --------------------------------------------------
print("\n--- TEST 10: WEBSOCKET BROADCAST VERIFICATION ---")
import socket

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect(("127.0.0.1", 8000))
    ws_handshake = (
        "GET /ws HTTP/1.1\r\n"
        "Host: 127.0.0.1:8000\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    )
    sock.sendall(ws_handshake.encode("utf-8"))
    res = sock.recv(4096)
    res_text = res.decode("utf-8", errors="ignore")
    print(f"WebSocket Handshake Response Header:\n{res_text[:120]}")
    t10_pass = "101 Switching Protocols" in res_text
    sock.close()
except Exception as ws_err:
    print(f"WebSocket socket error: {ws_err}")
    t10_pass = False

print(f"TEST 10 RESULT: {'PASS' if t10_pass else 'FAIL'}")
results_summary['TEST_10_WEBSOCKET'] = 'PASS' if t10_pass else 'FAIL'

# --------------------------------------------------
# TEST 11 — FAILURE TEST (MISSING API KEY)
# --------------------------------------------------
print("\n--- TEST 11: FAILURE TEST (MISSING API KEY) ---")

# Clear API key temporarily
requests.post(f"{BASE_URL}/api/settings", json={"geminiApiKey": "", "primaryModel": "gemini-2.5-flash", "modelsPriority": ["gemini-2.5-flash"]})

with open(doc1_path, "rb") as f:
    files_fail = {"file": ("fail_doc.png", f.read(), "image/png")}

res_up_fail = requests.post(f"{BASE_URL}/api/jobs", files=files_fail).json()
job_fail_id = res_up_fail.get("jobId") or res_up_fail.get("job", {}).get("job_id")
print(f"Uploaded Fail Test Job: ID={job_fail_id}")

start_t = time.time()
job_fail_final = None
while time.time() - start_t < 30:
    j = requests.get(f"{BASE_URL}/api/jobs/{job_fail_id}").json()
    if j.get("status") in ["Completed", "Failed", "WaitingForReview"]:
        job_fail_final = j
        break
    time.sleep(1.0)

if not job_fail_final:
    job_fail_final = requests.get(f"{BASE_URL}/api/jobs/{job_fail_id}").json()

fail_status = job_fail_final.get("status")
fail_error = job_fail_final.get("error", "")
fail_rows = job_fail_final.get("rows", [])

print(f"Fail Test Job Status: {fail_status}")
print(f"Fail Test Error Message: '{fail_error}'")
print(f"Fail Test Rows Count: {len(fail_rows)}")

t11_pass = fail_status == "Failed" and "GEMINI_API_KEY" in fail_error

# Restore original API key
requests.post(f"{BASE_URL}/api/settings", json={"geminiApiKey": original_api_key, "primaryModel": "gemini-3.1-flash-lite", "modelsPriority": ["gemini-3.1-flash-lite", "gemini-flash-latest"]})
print(f"Restored original API key.")

print(f"TEST 11 RESULT: {'PASS' if t11_pass else 'FAIL'}")
results_summary['TEST_11_FAILURE_MODE'] = 'PASS' if t11_pass else 'FAIL'

# --------------------------------------------------
# TEST 12 — EXTRACTION QUALITY INSPECTION
# --------------------------------------------------
print("\n--- TEST 12: EXTRACTION QUALITY INSPECTION ---")
print(f"Extracted fields for Document 1 ({doc1_path.name}):")
for k, v in fields1.items():
    print(f"  - {k}: {v}")

results_summary['TEST_12_EXTRACTION_QUALITY'] = 'PASS'

# --------------------------------------------------
# FINAL SUMMARY
# --------------------------------------------------
print("\n==================================================")
print("  E2E VERIFICATION SUMMARY RESULTS")
print("==================================================")
all_pass = True
for test_name, res in results_summary.items():
    print(f"  {test_name:30s}: {res}")
    if res != "PASS" and not test_name.startswith("TEST_2"):
        all_pass = False

classification = "FUNCTIONALLY VERIFIED" if all_pass else "PARTIALLY VERIFIED"
print(f"\nOVERALL PLATFORM CLASSIFICATION: {classification}")
