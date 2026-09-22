# v5.0 Critique & Self-Correction Feedback Loop Report

## Automated Critic & Retry Budget
The `CritiqueAndSelfCorrectionEngine` evaluates extraction outputs against domain rules, missing required keys, date formatting, and math consistency:
- **Math Mismatches**: Detects arithmetic mismatches (subtotal + tax != total) and marks severity as `CRITICAL`.
- **Targeted Re-Extraction**: Formulates specific field re-extraction directives.
- **Bounded Retry Budget**: Limits retries to `max_critique_attempts` (default 3) to prevent infinite execution loops.
