# v5.0 Regression & Benchmark Report

## Test Suite Execution Results

| Test Suite | Total Tests | Passed | Skipped | Failed | Pass Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tests/v4_0_3/test_v403_regression.py` | 16 | 14 | 2 | 0 | 100.0% |
| `tests/v4_1/security/test_v41_security.py` | 5 | 5 | 0 | 0 | 100.0% |
| `tests/v4_2/test_v42_enterprise.py` | 7 | 7 | 0 | 0 | 100.0% |
| `tests/v5_0/test_v50_agentic_intelligence.py` | 8 | 8 | 0 | 0 | 100.0% |
| **TOTAL** | **36** | **34** | **2** | **0** | **100.0%** |

## Extraction Behavior Freeze Audit
- **30-Document Stage 1 Benchmark Accuracy**: Maintained at 100.0%.
- **Preserved Source Fidelity**: `MedicalBill.png` printed `$745.00` subtotal preserved; arithmetic mismatch triggers `WaitingForReview` (HITL).
- **Regression**: 0 failures.
