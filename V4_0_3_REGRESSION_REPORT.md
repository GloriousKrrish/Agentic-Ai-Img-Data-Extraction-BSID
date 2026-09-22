# v4.0.3 Full Regression Suite Audit Report

## Summary of Executed Regression Suites

All core platform regression test suites were executed to verify zero regression across existing workflows:

| Regression Harness / Test Suite | Total Tests | Passed | Failed | Status |
|---|---|---|---|---|
| **E2E Core Subsystem Verification** ([run_e2e_verification.py](file:///c:/Users/admin/OneDrive/Desktop/PROJECTS/Agentic-Ai-Img-Data-Extraction-BSID-main/run_e2e_verification.py)) | 7 | 7 | 0 | **PASSED** |
| **30-Document Stage 1 Benchmark Suite** | 30 | 30 | 0 | **PASSED** |
| **MedicalBill Golden Test (`MedicalBill.png`)** | 1 | 1 | 0 | **PASSED** |
| **Failure Injection Suite (`FI-01` to `FI-15`)** | 15 | 15 | 0 | **PASSED** |
| **Canonical Export Parity Audit (XLSX/CSV/JSON/PDF)** | 3 | 3 | 0 | **PASSED** |
| **Persistence & Backend Restart Audit** | 1 | 1 | 0 | **PASSED** |
| **TOTAL REGRESSION TESTS** | **57** | **57** | **0** | **100% PASSED** |

---

## Key Verified Behavior

1. **MedicalBill.png**: Printed subtotal `$745.00` and total `$1902.05` preserved. Arithmetic mismatch detected -> job status `WaitingForReview`.
2. **Failure Injection Suite**: Zero unhandled crashes or silent successes across missing API keys, corrupted files, and blank images.
3. **Canonical Consistency**: Database, REST API, JSON/CSV/XLSX exports, and ReportLab PDF audits match 100%.
