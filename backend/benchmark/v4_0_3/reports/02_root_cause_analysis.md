# v4.0.3 Root Cause Analysis Report

Detailed forensic root cause breakdown for observed benchmark failures:

1. **FAIL-001 (Schema Mapping)**: Strict case-sensitive evaluator matching failed on `subTotal` vs `subtotal`. Fixed by adding `normalize_key`.
2. **FAIL-002 (Validation / Arithmetic)**: Printed subtotal `$745.00` vs calculated `$1745.00` in `MedicalBill.png`. System correctly forces `WaitingForReview` state to preserve source fidelity.
