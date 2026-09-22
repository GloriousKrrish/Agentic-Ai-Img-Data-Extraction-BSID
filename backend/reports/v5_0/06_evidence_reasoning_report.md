# v5.0 Source Evidence Reasoning Report

## Fact Grounding & Provenance
The `EvidenceReasoningEngine` binds extracted key-value pairs to exact visual coordinates and source text snippets:
- **OCR Exact Matches**: Binds fields found directly in OCR text with 100.0% verification confidence.
- **Digit Substring Matching**: Finds numeric digit matches in source text with 85.0% confidence.
- **Hallucination Protection**: Flags ungrounded/hallucinated fields if extracted values cannot be proven in source layer.
