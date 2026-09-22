# v4.0.2 Independent Accuracy & Robustness Benchmark Framework

## Executive Overview
The **v4.0.2 Benchmark Subsystem** provides a standardized, reproducible, and verifiable testing engine designed to measure document data extraction accuracy, evidence precision, table structure intelligence, failure handling, and confidence score calibration against independently annotated ground truth datasets.

---

## Benchmark Directory Layout

```
benchmark/
├── datasets/         # Binary document files (.png, .jpg, .pdf, .csv, .xlsx, .docx)
├── ground_truth/     # Independent JSON ground-truth annotation files per document
├── schemas/          # Schema definitions for schema-constrained extraction
├── runners/          # Execution harness (run_v402_benchmark.py)
├── evaluators/       # Evaluation engine (v402_evaluator.py)
├── reports/          # Output JSON and Markdown report artifacts
└── fixtures/         # Regression fixtures and adversarial test cases
```

---

## Document Provenance Classification

Every benchmark document is tagged with strict provenance metadata in its ground truth JSON file:

| Source Class | Description | Role in Accuracy Claims |
|---|---|---|
| **`Source Class A` (`INDEPENDENT_REAL_REFERENCE`)** | Real-world documents gathered from independent reference sources. | Contributes to Independent Accuracy claims. |
| **`Source Class B` (`INDEPENDENTLY_ANNOTATED_FIXTURE`)** | Realistic synthetic or templated documents with independently verified ground truth annotations. | Contributes to Independent Accuracy claims. |
| **`Source Class C` (`GENERATED_PROJECT_FIXTURE`)** | Codebase-generated internal test fixtures. | Reported separately as Regression/Fixture metrics. **Never** combined with A/B for real-world accuracy claims. |

---

## Evaluation & Normalization Rules

### Field-Level Classification:
- **`CORRECT`**: Extracted value matches ground truth within normalized tolerances.
- **`INCORRECT`**: Extracted value differs meaningfully from ground truth (e.g., printed subtotal `$745.00` vs extracted `$1745.00`).
- **`MISSING`**: Field present in ground truth but omitted in extraction.
- **`HALLUCINATED`**: Extracted field key/value not present in ground truth.

### Controlled Normalization Rules:
1. **Currency/Numeric**: `$1,902.05`, `1902.05`, `1902.05 USD` normalize to numeric `1902.05` for numeric fields. Genuine value differences (e.g. `745` vs `1745`) are flagged as `INCORRECT`.
2. **String Trimming**: Leading/trailing whitespace and case differences in non-case-sensitive fields are normalized.
3. **Dates**: ISO standard (`YYYY-MM-DD`) and common localized date formats (`MM/DD/YYYY`, `DD/MM/YYYY`) are normalized for comparison.

---

## Metrics Definitions

* **Field Accuracy**: `(Correct Fields) / (Total Expected Ground Truth Fields)`
* **Missing Field Rate**: `(Missing Fields) / (Total Expected Ground Truth Fields)`
* **Hallucination Rate**: `(Hallucinated Fields) / (Total Extracted Fields)`
* **Evidence Coverage**: `(Fields with Valid Evidence Bounding) / (Total Extracted Fields)`
* **Evidence Correctness**: `(Fields with Valid & Accurate Location Evidence) / (Total Extracted Fields)`
* **HITL Rate**: `(Jobs in WaitingForReview State) / (Total Benchmark Jobs)`
* **False-HITL Rate**: `(Jobs in WaitingForReview State where Extraction is Correct) / (Total Correct Jobs)`
* **Missed-HITL Rate**: `(Jobs in Completed State where Extraction is Incorrect) / (Total Incorrect Jobs)`

---

## Execution Instructions

```bash
# Execute baseline benchmark run (v4.0.1 frozen code)
python benchmark/runners/run_v402_benchmark.py --mode baseline

# Execute improved benchmark run (post-fix evaluation)
python benchmark/runners/run_v402_benchmark.py --mode improved
```
