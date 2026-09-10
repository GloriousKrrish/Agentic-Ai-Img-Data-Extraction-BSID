"""
Enterprise Pipeline Trace Diagnostic
Proves every stage of the pipeline, exactly what Gemini receives and returns,
and traces data through Sanitizer → Excel Writer.
"""
import os
import sys
import json
import time
import base64
import requests

sys.path.insert(0, ".")

# ── 0. Config & API key ──────────────────────────────────────────────────────
import backend.config as config

api_key = getattr(config, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
primary_model = getattr(config, "GEMINI_PRIMARY_MODEL", "gemini-2.5-flash")
models_priority = getattr(config, "MODELS_PRIORITY", [primary_model])

print("=" * 70)
print("STAGE 0 — ENVIRONMENT & CONFIGURATION")
print("=" * 70)
print(f"  GEMINI_PRIMARY_MODEL : {primary_model}")
print(f"  MODELS_PRIORITY      : {models_priority}")
print(f"  API key set          : {bool(api_key)}")
print(f"  API key preview      : {api_key[:14]}... (len={len(api_key)})")

from backend.services.job_manager import job_manager
jm_key = job_manager.get_api_key()
print(f"  JobManager key       : {jm_key[:14]}... (len={len(jm_key)})")
print()

# ── 1. Workbook Analysis ─────────────────────────────────────────────────────
print("=" * 70)
print("STAGE 1 — WORKBOOK ANALYSIS (WorkbookAgent)")
print("=" * 70)
from backend.agents.workbook_agent import WorkbookAgent
wb_agent = WorkbookAgent()
with open("testing.xlsx", "rb") as f:
    wb_bytes = f.read()

t0 = time.time()
analysis = wb_agent.analyze_workbook(wb_bytes, "testing.xlsx")
elapsed = time.time() - t0

print(f"  Filename          : {analysis['filename']}")
print(f"  Headers           : {analysis['headers']}")
print(f"  URL Column        : {analysis['url_column']}")
print(f"  Tasks Found       : {analysis['total_url_tasks']}")
print(f"  Analysis time     : {elapsed:.3f}s")

if not analysis["tasks"]:
    print("  ERROR: No URL tasks found. Exiting.")
    sys.exit(1)

for i, t in enumerate(analysis["tasks"][:3]):
    print(f"  Task[{i}]  row={t['rowIndex']}  url={t['url'][:80]}")
print()

# ── 2. Image Download ────────────────────────────────────────────────────────
print("=" * 70)
print("STAGE 2 — IMAGE DOWNLOAD (DownloaderAgent)")
print("=" * 70)
first_task = analysis["tasks"][0]
url = first_task["url"]
print(f"  URL               : {url[:100]}")

from backend.agents.downloader_agent import DownloaderAgent
dl = DownloaderAgent()
t0 = time.time()
res = dl.fetch(url, max_retries=2)
elapsed = time.time() - t0

print(f"  Success           : {res['success']}")
print(f"  MIME type         : {res.get('mime_type')}")
print(f"  Bytes received    : {len(res.get('bytes', b''))}")
print(f"  Download time     : {elapsed:.3f}s")

if not res["success"]:
    print(f"  ERROR             : {res.get('error')}")
    sys.exit(1)

doc_bytes = res["bytes"]
mime = res["mime_type"]
print()

# ── 3. Schema Used ───────────────────────────────────────────────────────────
print("=" * 70)
print("STAGE 3 — INVOICE SCHEMA (INVOICE_SEMANTIC_PROMPT_SCHEMA)")
print("=" * 70)
from backend.services.invoice_engine import INVOICE_SEMANTIC_PROMPT_SCHEMA
fields = INVOICE_SEMANTIC_PROMPT_SCHEMA["fields"]
print(f"  documentCategory  : {INVOICE_SEMANTIC_PROMPT_SCHEMA['documentCategory']}")
print(f"  Total fields      : {len(fields)}")
for f in fields:
    print(f"  Field  key={f['key']!r:25}  label={f['label']!r}")
print()

# ── 4. Build Gemini Prompt ──────────────────────────────────────────────────
print("=" * 70)
print("STAGE 4 — GEMINI PROMPT CONSTRUCTION")
print("=" * 70)

json_props = {}
req_keys = []
field_descs = []
for f in fields:
    k = f["key"]
    lbl = f.get("label", k)
    desc = f.get("description", lbl)
    json_props[k] = {"type": "string", "description": f"{lbl}: {desc}. Return null or empty string if not found."}
    req_keys.append(k)
    field_descs.append(f"- {k} ({lbl}): {desc}")

prompt = (
    "You are an Enterprise Expert Senior Business Data Analyst.\n"
    f'Analyzing a document classified as: "{INVOICE_SEMANTIC_PROMPT_SCHEMA["documentCategory"]}".\n\n'
    "Your mission is to extract EVERY SINGLE requested field from this invoice with 100% precision.\n\n"
    "Requested Fields:\n"
    + "\n".join(field_descs)
    + "\n\nStrict Field Guidelines:\n"
    "- Customer Name: Look for buyer, customer, M/S, to, or person name at the top.\n"
    "- Customer Mobile: Look for 10-digit mobile numbers (e.g. 9848022334, 9440121991).\n"
    "- Vehicle Number: Look for Indian license plates (e.g. AP39NT1461, MH12AB1234, DL01A1234).\n"
    "- Invoice Number & Date: Look for bill no, invoice no, cash memo no, and date.\n"
    "- Dealer Details: Extract shop name, dealer GSTIN (15 characters), and shop address.\n"
    "- Tyre Specs: Extract tyre size (e.g. 235/65R17, 205/65 R16), pattern name (e.g. Wanderer, B390, Sturdo), DOT code (e.g. DOT 4223), and serial numbers.\n"
    "- Financial Summary: Extract item quantity, unit cost, discount, tax, and final grand total amount.\n\n"
    "Inspect printed text, handwritten text, stamp seals, and line item tables very carefully.\n"
    "If a field is missing on the physical invoice, return null. Do not hallucinate fake values.\n"
)

gemini_schema = {"type": "object", "properties": json_props, "required": req_keys}

print(f"  Prompt length     : {len(prompt)} chars")
print(f"  Required keys     : {req_keys}")
print(f"  Image bytes       : {len(doc_bytes)}")
actual_mime = mime if mime and mime != "application/octet-stream" else "image/jpeg"
if "pdf" in actual_mime.lower():
    actual_mime = "application/pdf"
print(f"  Image MIME        : {actual_mime}")
print()

# ── 5. Gemini API Call ───────────────────────────────────────────────────────
print("=" * 70)
print("STAGE 5 — GEMINI API CALL")
print("=" * 70)

b64 = base64.b64encode(doc_bytes).decode("utf-8")
payload = {
    "contents": [{"parts": [
        {"text": prompt},
        {"inlineData": {"mimeType": actual_mime, "data": b64}}
    ]}],
    "generationConfig": {
        "responseMimeType": "application/json",
        "responseSchema": gemini_schema,
        "temperature": 0.0
    }
}

api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{primary_model}:generateContent?key={api_key}"
print(f"  Sending to model  : {primary_model}")
t0 = time.time()
resp = requests.post(api_url, json=payload, timeout=30)
elapsed = time.time() - t0

print(f"  HTTP Status       : {resp.status_code}")
print(f"  Response time     : {elapsed:.3f}s")

if resp.status_code != 200:
    print(f"  ERROR BODY        : {resp.text[:500]}")
    sys.exit(1)

data = resp.json()
raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
parsed_gemini = json.loads(raw_text)

print()
print("  RAW GEMINI JSON RESPONSE:")
for k, v in parsed_gemini.items():
    print(f"    {k:30s} : {v!r}")

# ── 6. Sanitizer Trace ───────────────────────────────────────────────────────
print()
print("=" * 70)
print("STAGE 6 — DATA SANITIZER (sanitize_extracted_dict)")
print("=" * 70)
from backend.services.data_sanitizer import sanitize_extracted_dict

print("  BEFORE sanitization:")
before_filled = 0
for k, v in parsed_gemini.items():
    if v and str(v).strip():
        before_filled += 1
    print(f"    {k:30s} : {v!r}")

sanitized = sanitize_extracted_dict(parsed_gemini, min_confidence=0.0)

print()
print("  AFTER sanitization:")
after_filled = 0
for k, v in sanitized.items():
    after_filled += 1
    print(f"    {k:30s} : {v!r}")

dropped = set(parsed_gemini.keys()) - set(sanitized.keys())
print()
print(f"  Fields before     : {before_filled}/{len(parsed_gemini)}")
print(f"  Fields after      : {after_filled}")
print(f"  Fields DROPPED    : {dropped if dropped else 'None — all fields preserved'}")

# Show what was dropped and WHY
if dropped:
    print()
    print("  DROP ANALYSIS:")
    from backend.services.data_sanitizer import clean_field_value, normalize_field
    for dk in dropped:
        raw_val = parsed_gemini.get(dk)
        cleaned = clean_field_value(raw_val)
        normed = normalize_field(dk, raw_val)
        print(f"    key={dk!r}  raw={raw_val!r}  cleaned={cleaned!r}  normalized={normed!r}")

# ── 7. Excel Column Mapping ───────────────────────────────────────────────────
print()
print("=" * 70)
print("STAGE 7 — EXCEL COLUMN MAPPING (ExcelWriterAgent)")
print("=" * 70)
from backend.agents.excel_writer_agent import PRIORITY_COLUMNS

sanitized["invoiceImageLink"] = url
sanitized["confidenceScore"] = "85.0%"
sanitized["processingStatus"] = "SUCCESS"

print("  Column → Key → Value mapping:")
print(f"  {'Col#':5s} {'Excel Header':30s} {'Key':25s} {'Value':40s}")
print(f"  {'-'*5} {'-'*30} {'-'*25} {'-'*40}")
for col_num, col in enumerate(PRIORITY_COLUMNS, 1):
    key = col["key"]
    label = col["label"]
    val = sanitized.get(key, "")
    indicator = "" if not val else "✓"
    print(f"  {col_num:<5} {label:30s} {key:25s} {str(val)[:40]:40s} {indicator}")

print()
filled_cols = sum(1 for c in PRIORITY_COLUMNS if sanitized.get(c["key"]))
print(f"  Columns populated : {filled_cols}/{len(PRIORITY_COLUMNS)}")

print()
print("=" * 70)
print("STAGE 8 — FULL PIPELINE SUCCESS VERDICT")
print("=" * 70)
print(f"  API key           : {'OK' if api_key else 'MISSING'}")
print(f"  Gemini model      : {primary_model}")
print(f"  Download          : OK ({len(doc_bytes)} bytes)")
print(f"  Gemini extraction : OK ({before_filled}/{len(parsed_gemini)} fields filled)")
print(f"  Sanitizer output  : OK ({after_filled} fields kept, {len(dropped)} dropped)")
print(f"  Excel columns     : {filled_cols}/{len(PRIORITY_COLUMNS)} populated")
print()

if after_filled >= 5:
    print("  RESULT: PIPELINE IS WORKING CORRECTLY.")
    print("  If output Excel is empty, the issue is in ExcelWriterAgent path,")
    print("  not in Gemini extraction or sanitization.")
else:
    print("  RESULT: EXTRACTION RETURNING FEW FIELDS. CHECK API KEY & MODEL.")
