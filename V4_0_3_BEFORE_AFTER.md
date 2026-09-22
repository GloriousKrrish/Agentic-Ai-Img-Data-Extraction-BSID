# v4.0.3 Before vs. After Benchmark Metrics Comparison

## Comparative Metric Analysis

Below is the comparative metric breakdown comparing `v4.0.2 Baseline` against `v4.0.3 Improved`:

| Metric | v4.0.2 Baseline | v4.0.3 Improved | Improvement Delta |
|---|---:|---:|---:|
| **Total Benchmark Documents** | 30 | 30 | — |
| **Total Expected GT Fields** | 118 | 118 | — |
| **Correct Fields** | 113 | 118 | **+5 fields** |
| **Incorrect Fields** | 3 | 0 | **-3 fields** |
| **Missing Fields** | 2 | 0 | **-2 fields** |
| **Hallucinated Fields** | 13 | 13 | 0 |
| **Overall Field Accuracy** | `95.76%` | **`100.0%`** | **+4.24%** |
| **Independent Accuracy (Class A & B)** | `95.69%` | **`100.0%`** | **+4.31%** |
| **HITL Rate** | `6.67%` (2/30) | `6.67%` (2/30) | `0.00%` (Preserved) |
| **False-HITL Rate** | `0.00%` | `0.00%` | `0.00%` |
| **Missed-HITL Rate** | `0.00%` | `0.00%` | `0.00%` |
| **Average Latency** | `8.00s` | `6.54s` | **-1.46s faster** |

---

## Detailed Notes on Delta:
- **Class A Real Reference Accuracy**: Improved from `64.29%` to `100.0%` on real reference documents like `DOC-012` (`test_bill.png`) due to canonical field key matching.
- **Preserved HITL Triggers**: `DOC-011` (`MedicalBill.png`) and `DOC-022` (`22_Adversarial_Math_Mismatch.png`) remain in `WaitingForReview` state due to genuine arithmetic total mismatches on printed documents.
