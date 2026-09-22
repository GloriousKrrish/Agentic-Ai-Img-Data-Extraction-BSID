# v4.0.3 Confidence Calibration & Scorecard Report

## Executive Calibration Assessment

> [!WARNING]
> **Calibration Status**: `CALIBRATION NOT YET ESTABLISHED`
> While confidence scores correlate strongly with field correctness across synthetic benchmark fixtures, formal probabilistic calibration (Platt scaling / Temperature scaling) across large-scale multi-domain real-world datasets has not been performed. Current field confidence uses a heuristic base score (`0.80`) supplemented by regex and OCR consensus bonuses.

---

## Confidence Band vs. Measured Accuracy Matrix

| Confidence Band | Total Fields | Correct Fields | Measured Accuracy | Calibration Status |
|---|---|---|---|---|
| **`0–50%`** | 0 | 0 | N/A | No fields produced in low band |
| **`50–70%`** | 0 | 0 | N/A | Triggers automatic replan retry |
| **`70–80%`** | 12 | 12 | **100.0%** | Single-pass vision extractions |
| **`80–90%`** | 0 | 0 | N/A | Intermediate band |
| **`90–95%`** | 80 | 75 | **93.75%** | High-confidence vision + regex pass |
| **`95–100%`** | 26 | 26 | **100.0%** | Multi-factor vision + regex + OCR consensus |

---

## HITL Optimization & Trigger Behavior

1. **High Confidence + Validated (`>= 0.70` & `Arithmetic PASS`)**: Automatically finalized as `Completed`.
2. **Low Confidence (`< 0.70`)**: Triggers up to `max_replans = 2`. If confidence remains low, routed to `WaitingForReview` (`HITL`).
3. **Arithmetic Mismatch (`Arithmetic FAIL`)**: Printed source value is preserved; job status is forced to `WaitingForReview` regardless of high vision confidence.
