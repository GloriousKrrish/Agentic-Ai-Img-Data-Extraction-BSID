# v4.0.3 Failure Taxonomy Report

Classified observed benchmark defects into standardized categories:

| Failure ID | Category | Document Type | Impact | Root Cause |
|---|---|---|---|---|
| FAIL-001 | Schema mapping failure | medical_invoice | HIGH | Field key casing mismatch in ground truth evaluation |
| FAIL-002 | Validation failure | medical_invoice | CRITICAL | Printed total differs from line item sum (MedicalBill.png) |
| FAIL-003 | Hallucination / Extra field | tax_statement | LOW | Transient metadata fields present in raw vision extraction |
