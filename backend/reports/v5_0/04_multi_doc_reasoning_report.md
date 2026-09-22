# v5.0 Multi-Document Reasoning Report

## Cross-Document Correlation Strategy
The `MultiDocReasoningEngine` provides batch-level entity alignment and discrepancy detection across document collections:
- **Matched Entities**: Identifies unanimous key-value matches (e.g. Vendor Name, PO Number).
- **Discrepancy Detection**: Flags conflicting values for financial totals, dates, or item descriptions across documents.
- **Batch Consensus Scoring**: Computes a normalized score (0.0 - 100.0%) indicating overall batch consistency.
