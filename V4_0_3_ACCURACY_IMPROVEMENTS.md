# v4.0.3 Extraction Intelligence & Accuracy Improvements Report

## Summary of Engineering Improvements

Based strictly on empirical evidence gathered during the v4.0.2 benchmark run, the following targeted improvements were implemented in the extraction and validation pipeline:

### 1. Robust Field Key Normalization ([benchmark/evaluators/v402_evaluator.py](file:///c:/Users/admin/OneDrive/Desktop/PROJECTS/Agentic-Ai-Img-Data-Extraction-BSID-main/benchmark/evaluators/v402_evaluator.py))
* **Problem**: Casing and separator variations (`subTotal` vs `subtotal`, `invoiceDate` vs `date`) caused false-negative field mismatch errors on real reference documents like `DOC-012` (`test_bill.png`).
* **Fix**: Implemented key normalization (`normalize_key`) in the evaluator and schema matcher to map camelCase, snake_case, and space-separated keys canonically.

### 2. Hallucination Defense & Evidence Binding ([backend/services/validation_engine.py](file:///c:/Users/admin/OneDrive/Desktop/PROJECTS/Agentic-Ai-Img-Data-Extraction-BSID-main/backend/services/validation_engine.py))
* **Rule**: Extracted values must be backed by evidence bounding or OCR/Vision consensus. Calculated fields are tagged explicitly rather than asserting un-supported source text.

### 3. Preserved Arithmetic Inconsistency Defense ([backend/services/validation_engine.py](file:///c:/Users/admin/OneDrive/Desktop/PROJECTS/Agentic-Ai-Img-Data-Extraction-BSID-main/backend/services/validation_engine.py))
* **MedicalBill Golden Test**: Printed subtotal `$745.00` and total `$1902.05` are strictly preserved as source values. Arithmetic discrepancy (`745 + 157.05 = 902.05 != 1902.05`) correctly sets `validations["arithmetic"] = False` and routes the job to `WaitingForReview` state.
