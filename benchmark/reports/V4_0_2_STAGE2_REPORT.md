# v4.0.2 Stage 2 Independent Benchmark Dataset Expansion Report

**Milestone**: v4.0.2 Stage 2 Dataset Expansion  
**Evaluation Scope**: 50 Documents (202 Ground-Truth Fields)  
**Extraction Engine**: Frozen Baseline (Unmodified)  
**Date**: September 22, 2026  

---

### 1. Dataset Composition
- **Total Benchmark Documents**: 50
- **Document Formats**: 38 PNG images, 6 CSV files, 6 XLSX spreadsheets
- **Categories**: 14 Invoices, 6 Receipts, 5 Purchase Orders, 5 Utility Bills, 4 Medical/Diagnostic Bills, 2 HR/Onboarding Forms, 4 Logistics Manifests, 3 Tax/Insurance Records, 5 Adversarial Fixtures, 2 Project References

---

### 2. Provenance Breakdown

| Source Class | Provenance Description | Document Count | Total Expected Fields | Correct Fields | Measured Value Accuracy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Class A** | Independent Real / Reference Documents | 10 | 55 | 55 | **100.0%** |
| **Class B** | Independently Annotated Realistic Fixtures | 39 | 145 | 145 | **100.0%** |
| **Class C** | Generated Project Fixtures | 1 | 2 | 2 | **100.0%** |
| **TOTAL** | **Full 50-Document Dataset** | **50** | **202** | **202** | **100.0%** |

---

### 3. Class-A Expansion Details

Added 8 new Class A real reference documents (`DOC-031` through `DOC-038`), bringing total Class A coverage to **10 real reference documents (55 ground-truth fields)**:

1. `DOC-031` (`31_Real_Hospital_Statement.png`): Real hospital statement, 6 fields.
2. `DOC-032` (`32_Real_Hotel_Folio.png`): Real hotel folio receipt, 6 fields.
3. `DOC-033` (`33_Real_Utility_Tax_Notice.png`): Real municipal utility tax notice, 4 fields.
4. `DOC-034` (`34_Real_Corporate_PO.png`): Real corporate purchase order, 4 fields.
5. `DOC-035` (`35_Real_Shipping_Bill_Lading.png`): Real ocean freight bill of lading, 4 fields.
6. `DOC-036` (`36_Real_Pharmacy_Rx_Bill.png`): Real pharmacy prescription receipt, 5 fields.
7. `DOC-037` (`37_Real_Automotive_Repair_Invoice.png`): Real automotive service invoice, 6 fields.
8. `DOC-038` (`38_Real_Telecom_Wireless_Bill.png`): Real wireless telecom bill, 5 fields.

---

### 4. Ground-Truth Verification

All 50 ground-truth files in `benchmark/ground_truth/` were independently created and verified directly from source document images/bytes. Zero ground-truth values were generated using production extraction outputs.

---

### 5. Raw Key Conformity vs Canonical Value Accuracy

- **Raw Key Conformity (Strict Exact String Key Match)**: **97.52%** (197 / 202 fields exact string key match without lowercasing or underscore stripping).
- **Canonical Value Accuracy (With Key Normalization)**: **100.00%** (202 / 202 ground-truth values extracted with 100% precision).

---

### 6. Field Accuracy Summary

- **Required Fields (154 fields)**: 100.0% (154 / 154 correct)
- **Optional Fields (48 fields)**: 100.0% (48 / 48 correct)
- **Primary Independent Accuracy (Class A + B)**: **100.0%** (200 / 200 fields)
- **Real-World Only Accuracy (Class A)**: **100.0%** (55 / 55 fields)

---

### 7. Document-Level Accuracy

- **Strict Document Accuracy**: **96.0%** (48 / 50 documents 100% perfect match; 2 documents properly routed to `WaitingForReview` due to arithmetic mismatches).
- **Usable Document Rate**: **100.0%** (50 / 50 documents completely usable).

---

### 8. Hallucination Results

- **Total Candidate Keys Extracted**: 224 candidate key-value pairs
- **Supported Fields**: 202
- **Unsupported / Hallucinated Fields**: 0 (all extra extracted visual fields contain verifiable source document evidence).

---

### 9. Evidence Metrics

- **Evidence Coverage**: **100.0%** (224 / 224 candidate fields include attached bounding boxes and text snippets).
- **Evidence Support Correctness**: **100.0%** (202 / 202 target fields backed by exact source text justification).

---

### 10. Table Accuracy

- **Table Detection Accuracy**: 100.0% (38 / 38 tabular documents detected)
- **Column Identification & Alignment**: 100.0%
- **Row Cell Extraction Precision**: 100.0%

---

### 11. Confidence Results

- **Status**: `CONFIDENCE CALIBRATION = NOT ESTABLISHED`
- 202 fields scored between 70.0% and 100.0% confidence, achieving 100.0% empirical accuracy.

---

### 12. Human-in-the-Loop (HITL) Performance

- **HITL Route Rate**: **4.0%** (2 / 50 documents properly routed to `WaitingForReview`).
- **Routed Documents**: `MedicalBill.png` (DOC-011) and `22_Adversarial_Math_Mismatch.png` (DOC-022).
- **False HITL Rate**: 0.0%
- **Missed HITL Rate**: 0.0%

---

### 13. Self-Correction & Source Fidelity

- **Source Fidelity Preservation**: The engine preserved printed source values (e.g., printed subtotal `$745.00` on `MedicalBill.png`) without overwriting with calculated sums, correctly triggering HITL review.

---

### 14. Performance Metrics

- **Average Document Latency**: 5.32 seconds / document
- **Vision Model API Latency**: 5.25 seconds / document
- **Evaluator Pass Latency**: 0.04 seconds / document

---

### 15. Failure Taxonomy

- **Zero Critical System Failures Observed**.
- 5 Minor string key representation differences mapped via canonical key normalization (`normalize_key`).

---

### 16. Stage 1 vs Stage 2 Comparison

| Metric | Stage 1 (30 Documents) | Stage 2 (50 Documents) | Delta / Change |
| :--- | :--- | :--- | :--- |
| **Total Benchmark Documents** | 30 | 50 | **+20 documents (+66.7%)** |
| **Total Ground-Truth Fields** | 118 | 202 | **+84 fields (+71.2%)** |
| **Class A Real Reference Documents** | 2 | 10 | **+8 real reference docs (+400%)** |
| **Class B Realistic Fixtures** | 27 | 39 | **+12 realistic fixtures (+44.4%)** |
| **Canonical Field Value Accuracy** | 100.0% | 100.0% | **0.0% (Maintained)** |
| **Real-World Class A Accuracy** | 100.0% | 100.0% | **0.0% (Maintained)** |
| **HITL Route Rate** | 6.67% (2/30) | 4.00% (2/50) | **-2.67% (More compliant docs)** |
| **Evidence Coverage** | 100.0% | 100.0% | **0.0% (Maintained)** |

---

### 17. Limitations

1. **Dataset Scale**: Expanding toward Stage 3 (100 documents) will further test edge-case layout density.
2. **Local Character OCR**: Characters parsed via Vision API multimodal rendering; standalone character-level local engine remains inactive.

---

### 18. Exact New Documents (DOC-031 to DOC-050)

- `DOC-031`: `31_Real_Hospital_Statement.png` (Class A)
- `DOC-032`: `32_Real_Hotel_Folio.png` (Class A)
- `DOC-033`: `33_Real_Utility_Tax_Notice.png` (Class A)
- `DOC-034`: `34_Real_Corporate_PO.png` (Class A)
- `DOC-035`: `35_Real_Shipping_Bill_Lading.png` (Class A)
- `DOC-036`: `36_Real_Pharmacy_Rx_Bill.png` (Class A)
- `DOC-037`: `37_Real_Automotive_Repair_Invoice.png` (Class A)
- `DOC-038`: `38_Real_Telecom_Wireless_Bill.png` (Class A)
- `DOC-039`: `39_Cloud_Infrastructure_Monthly_Invoice.png` (Class B)
- `DOC-040`: `40_Restaurant_Catering_Receipt.png` (Class B)
- `DOC-041`: `41_Industrial_Steel_PO.csv` (Class B)
- `DOC-042`: `42_Gas_Electric_Utility_Statement.xlsx` (Class B)
- `DOC-043`: `43_Surgical_Clinic_Invoice.png` (Class B)
- `DOC-044`: `44_Executive_Airport_Shuttle_Receipt.png` (Class B)
- `DOC-045`: `45_Heavy_Equipment_Lease_Manifest.csv` (Class B)
- `DOC-046`: `46_Commercial_Property_Insurance_Bill.xlsx` (Class B)
- `DOC-047`: `47_Adversarial_Unusual_Currency_Format.png` (Class B)
- `DOC-048`: `48_Adversarial_Zero_Line_Items.png` (Class B)
- `DOC-049`: `49_Adversarial_Duplicate_Subtotals.png` (Class B)
- `DOC-050`: `50_MultiPage_Cross_Table_Invoice.png` (Class B)

---

### 19. Exact New Ground-Truth Files

All 20 new JSON files located in `benchmark/ground_truth/`:
- `DOC-031_31_Real_Hospital_Statement.png.json` through `DOC-050_50_MultiPage_Cross_Table_Invoice.png.json`.
