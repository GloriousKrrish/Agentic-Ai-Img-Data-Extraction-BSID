import os
import json
import shutil
from pathlib import Path

ROOT = Path(r"c:\Users\admin\OneDrive\Desktop\PROJECTS\Agentic-Ai-Img-Data-Extraction-BSID-main")
V403_DIR = ROOT / "backend" / "benchmark" / "v4_0_3"

BASELINE_DIR = V403_DIR / "baseline"
IMPROVED_DIR = V403_DIR / "improved"
TAXONOMY_DIR = V403_DIR / "failure_taxonomy"
REPORTS_DIR = V403_DIR / "reports"
REGRESSION_DIR = V403_DIR / "regression"

for d in [BASELINE_DIR, IMPROVED_DIR, TAXONOMY_DIR, REPORTS_DIR, REGRESSION_DIR]:
    os.makedirs(d, exist_ok=True)

# Copy baseline metrics snapshot
src_baseline_doc = ROOT / "V4_0_2_DOCUMENT_RESULTS.json"
src_baseline_field = ROOT / "V4_0_2_FIELD_ACCURACY.json"

if src_baseline_doc.exists():
    shutil.copy(src_baseline_doc, BASELINE_DIR / "v4_0_2_document_results.json")
if src_baseline_field.exists():
    shutil.copy(src_baseline_field, BASELINE_DIR / "v4_0_2_field_accuracy.json")

# Create failure_taxonomy.json
taxonomy_data = [
    {
        "failure_id": "FAIL-001",
        "category": "Schema mapping failure",
        "document_type": "medical_invoice",
        "format": "png",
        "field_type": "string / currency",
        "observed_behavior": "Field key casing variation (subTotal vs subtotal) led to key mismatch in automated ground truth comparison.",
        "expected_behavior": "Canonical key normalization maps camelCase, snake_case, and space-separated keys transparently.",
        "root_cause": "Strict case-sensitive string matching in evaluator ground-truth comparison without key canonicalization.",
        "impact": "HIGH",
        "frequency": 1,
        "proposed_fix": "Implement normalize_key helper in validator and evaluator to map keys canonically.",
        "evidence_source": "benchmark/ground_truth/DOC-012_test_bill.png.json"
    },
    {
        "failure_id": "FAIL-002",
        "category": "Validation failure",
        "document_type": "medical_invoice",
        "format": "png",
        "field_type": "currency",
        "observed_behavior": "Printed document subtotal 745.00 + line item 1000.00 = 1745.00, which differs from printed subtotal 745.00.",
        "expected_behavior": "Preserve printed source value 745.00, set mathematical_consistency = FAIL, route job to WaitingForReview.",
        "root_cause": "Adversarial document printing error in source image MedicalBill.png.",
        "impact": "CRITICAL",
        "frequency": 2,
        "proposed_fix": "Separate SOURCE_FIDELITY from MATHEMATICAL_CONSISTENCY in validation engine, enforcing HITL state.",
        "evidence_source": "MedicalBill.png & 22_Adversarial_Math_Mismatch.png"
    },
    {
        "failure_id": "FAIL-003",
        "category": "Hallucination / Extra field extraction",
        "document_type": "tax_statement",
        "format": "png",
        "field_type": "transient_metadata",
        "observed_behavior": "Extra transient keys (e.g. serNo, lineItems) extracted by Vision engine.",
        "expected_behavior": "Strictly filter non-schema metadata keys or mark as UNVERIFIED.",
        "root_cause": "Default vision extraction schema includes optional metadata fields.",
        "impact": "LOW",
        "frequency": 1,
        "proposed_fix": "Filter non-schema metadata keys in validation engine scorecard output.",
        "evidence_source": "04_Annual_Property_Tax.png"
    }
]

with open(V403_DIR / "failure_taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(taxonomy_data, f, indent=2)

with open(TAXONOMY_DIR / "failure_taxonomy.json", "w", encoding="utf-8") as f:
    json.dump(taxonomy_data, f, indent=2)

print("v4.0.3 directory snapshot & failure_taxonomy.json created successfully.")
