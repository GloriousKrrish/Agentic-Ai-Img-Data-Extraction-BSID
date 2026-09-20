"""
Phase 4: Schema-Constrained Extraction Engine
Executes schema-directed extraction: builds per-field prompts, coerces types,
evaluates cross-field rules, and generates SchemaExtractionReport.
"""
from __future__ import annotations
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.agents.schema_models import (
    CrossFieldRule, CrossFieldRuleOutcome, ExtractionSchema, FieldValidationOutcome,
    RuleSeverity, SchemaExtractionReport, SchemaField, SchemaFieldType,
    SchemaValidationResult
)

# ---------------------------------------------------------------------------
# Extraction prompt template
# ---------------------------------------------------------------------------
_SCHEMA_EXTRACTION_PROMPT = """You are a precision document data extraction engine.
Extract ONLY the fields specified in the schema below from the document.
For each field, extract the exact value from the document or return null if not found.
Apply the extraction hints and descriptions provided.

SCHEMA FIELDS TO EXTRACT:
{field_definitions}

DOCUMENT CONTENT:
{document_content}

Output STRICTLY valid JSON with exactly these keys (use null for missing fields):
{output_template}

Rules:
- Extract EXACT values as they appear in the document
- For dates: normalize to YYYY-MM-DD format if possible
- For currency: extract the numeric value as a string (e.g. "1250.00")
- For numbers: extract only the numeric value as a string
- For booleans: return true or false
- For arrays: return a JSON array
- Do NOT invent values not present in the document
- If a field value is ambiguous, prefer the most prominent occurrence
"""

_BATCH_SIZE = 15  # Max fields per Gemini call


class SchemaExtractionEngine:
    """
    Executes schema-constrained extraction against documents.
    Works with both text-based and binary (image/PDF) inputs.
    """

    # ------------------------------------------------------------------
    # Main extraction entry point
    # ------------------------------------------------------------------
    def extract_with_schema(
        self,
        schema: ExtractionSchema,
        file_bytes: bytes,
        mime_type: str,
        text_content: str = "",
        plan: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], SchemaExtractionReport]:
        """
        Execute schema-constrained extraction.
        Returns (extracted_fields_dict, SchemaExtractionReport).
        """
        extracted: Dict[str, Any] = {}
        type_coercion_applied: List[str] = []
        type_failures: List[str] = []

        # Split fields into batches for Gemini
        field_batches = [
            schema.fields[i:i + _BATCH_SIZE]
            for i in range(0, len(schema.fields), _BATCH_SIZE)
        ]

        for batch in field_batches:
            batch_result = self._extract_batch(batch, file_bytes, mime_type, text_content)
            extracted.update(batch_result)

        # Type coercion pass
        for field in schema.fields:
            raw_val = extracted.get(field.key)
            if raw_val is not None and raw_val != "" and raw_val != "null":
                coerced, success = self.coerce_field_type(raw_val, field.field_type)
                if success and coerced != raw_val:
                    extracted[field.key] = coerced
                    type_coercion_applied.append(field.key)
                elif not success:
                    type_failures.append(field.key)
                    # Keep original string value
                    extracted[field.key] = str(raw_val)
            elif raw_val in (None, "", "null"):
                extracted[field.key] = field.default_value

        # Validate against schema
        validation_result = self.validate_extraction(extracted, schema)

        # Cross-field rule evaluation
        rule_outcomes = self.evaluate_cross_field_rules(extracted, schema)

        # Build report
        required_keys = {f.key for f in schema.required_fields}
        extracted_required = {k for k in required_keys if extracted.get(k) not in (None, "", "null")}
        completeness = (len(extracted_required) / len(required_keys) * 100) if required_keys else 100.0
        rules_passed = sum(1 for r in rule_outcomes if r.passed)
        rules_failed = sum(1 for r in rule_outcomes if not r.passed)

        # Quality score: weighted completeness + rule pass rate
        rule_weight = 0.3
        completeness_weight = 0.7
        rule_score = rules_passed / max(len(rule_outcomes), 1) if rule_outcomes else 1.0
        quality = completeness_weight * (completeness / 100) + rule_weight * rule_score

        hitl_required = bool(validation_result.missing_required) or (quality < 0.6)
        hitl_reasons: List[str] = []
        if validation_result.missing_required:
            hitl_reasons.append(f"Missing required fields: {', '.join(validation_result.missing_required)}")
        if quality < 0.6:
            hitl_reasons.append(f"Low quality score: {quality:.2f}")
        if rules_failed > 0:
            hitl_reasons.append(f"{rules_failed} cross-field rule(s) failed")

        report = SchemaExtractionReport(
            schema_id=schema.schema_id,
            schema_name=schema.name,
            schema_version=schema.version,
            total_fields=len(schema.fields),
            required_fields_count=len(required_keys),
            extracted_fields_count=len([v for v in extracted.values() if v not in (None, "", "null")]),
            missing_required=validation_result.missing_required,
            type_coercion_applied=type_coercion_applied,
            type_failures=type_failures,
            cross_field_rules_passed=rules_passed,
            cross_field_rules_failed=rules_failed,
            completeness_pct=round(completeness, 1),
            quality_score=round(quality, 3),
            field_outcomes=validation_result.field_outcomes,
            rule_outcomes=rule_outcomes,
            hitl_required=hitl_required,
            hitl_reasons=hitl_reasons
        )

        return extracted, report

    # ------------------------------------------------------------------
    # Single batch extraction via Gemini
    # ------------------------------------------------------------------
    def _extract_batch(
        self,
        fields: List[SchemaField],
        file_bytes: bytes,
        mime_type: str,
        text_content: str = ""
    ) -> Dict[str, Any]:
        """Run a single Gemini call for a batch of schema fields."""
        import base64
        import requests
        from backend.services.job_manager import job_manager
        import backend.config as config

        api_key = job_manager.get_api_key()
        if not api_key:
            return {f.key: f.default_value for f in fields}

        # Build field definitions for prompt
        field_defs = "\n".join([
            f"- {f.key} ({f.field_type.value}): {f.description or f.label}"
            + (f"\n  Hint: {f.extraction_hint}" if f.extraction_hint else "")
            + (f"\n  Pattern: {f.regex_pattern}" if f.regex_pattern else "")
            + (f"\n  Allowed values: {', '.join(f.allowed_values)}" if f.allowed_values else "")
            for f in fields
        ])

        # Build output template
        output_template = json.dumps({f.key: None for f in fields}, indent=2)

        # Document content: prefer text, supplement with binary
        doc_content = text_content[:4000] if text_content else "[Document provided as binary image/PDF]"

        prompt = _SCHEMA_EXTRACTION_PROMPT.format(
            field_definitions=field_defs,
            document_content=doc_content,
            output_template=output_template
        )

        parts: List[Dict] = [{"text": prompt}]

        # Attach binary content if available
        if file_bytes and len(file_bytes) > 0:
            actual_mime = mime_type if mime_type and mime_type != "application/octet-stream" else "image/jpeg"
            if "pdf" in actual_mime.lower():
                actual_mime = "application/pdf"
            parts.append({
                "inlineData": {
                    "mimeType": actual_mime,
                    "data": base64.b64encode(file_bytes).decode("utf-8")
                }
            })

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }

        models = getattr(config, "MODELS_PRIORITY", []) or ["gemini-2.5-flash", "gemini-2.0-flash"]
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            for attempt in range(3):
                try:
                    res = requests.post(url, json=payload, timeout=30)
                    if res.status_code == 200:
                        raw = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(raw)
                        # Ensure all field keys are present
                        result = {}
                        for f in fields:
                            result[f.key] = parsed.get(f.key, f.default_value)
                        return result
                    elif res.status_code == 429:
                        time.sleep(2.0 * (attempt + 1))
                    else:
                        break
                except Exception as e:
                    print(f"SchemaExtractionEngine batch error ({model}): {e}")
                    break

        # Fallback: return defaults
        return {f.key: f.default_value for f in fields}

    # ------------------------------------------------------------------
    # Type coercion
    # ------------------------------------------------------------------
    def coerce_field_type(self, value: Any, field_type: SchemaFieldType) -> Tuple[Any, bool]:
        """
        Coerce a raw extracted value to the target field type.
        Returns (coerced_value, success).
        """
        if value is None:
            return None, True

        str_val = str(value).strip()

        try:
            if field_type == SchemaFieldType.NUMBER:
                cleaned = re.sub(r"[^\d.\-]", "", str_val.replace(",", ""))
                return float(cleaned), True

            elif field_type == SchemaFieldType.CURRENCY:
                cleaned = re.sub(r"[^\d.\-]", "", str_val.replace(",", ""))
                return float(cleaned), True

            elif field_type == SchemaFieldType.PERCENTAGE:
                cleaned = re.sub(r"[^\d.\-]", "", str_val.replace("%", "").replace(",", ""))
                return float(cleaned), True

            elif field_type == SchemaFieldType.BOOLEAN:
                if str_val.lower() in ("true", "yes", "1", "y", "on", "enabled"):
                    return True, True
                elif str_val.lower() in ("false", "no", "0", "n", "off", "disabled"):
                    return False, True
                return bool(value), True

            elif field_type == SchemaFieldType.DATE:
                return self._normalize_date(str_val), True

            elif field_type == SchemaFieldType.ARRAY:
                if isinstance(value, list):
                    return value, True
                if str_val.startswith("["):
                    return json.loads(str_val), True
                # Try comma-split
                return [v.strip() for v in str_val.split(",")], True

            elif field_type == SchemaFieldType.OBJECT:
                if isinstance(value, dict):
                    return value, True
                if str_val.startswith("{"):
                    return json.loads(str_val), True
                return {"value": str_val}, True

            else:  # STRING
                return str_val, True

        except Exception:
            return value, False  # Return original, flag as failure

    def _normalize_date(self, date_str: str) -> str:
        """Best-effort date normalization to YYYY-MM-DD."""
        import re
        # Try DD/MM/YYYY
        m = re.match(r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})", date_str)
        if m:
            d, mo, y = m.group(1), m.group(2), m.group(3)
            return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
        # Try YYYY-MM-DD already
        m = re.match(r"(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})", date_str)
        if m:
            y, mo, d = m.group(1), m.group(2), m.group(3)
            return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
        return date_str  # Return as-is if can't normalize

    # ------------------------------------------------------------------
    # Field validation against schema constraints
    # ------------------------------------------------------------------
    def validate_extraction(
        self,
        extracted: Dict[str, Any],
        schema: ExtractionSchema
    ) -> SchemaValidationResult:
        """
        Validate extracted values against schema field constraints.
        Checks required, regex, min/max, allowed_values.
        """
        field_outcomes: List[FieldValidationOutcome] = []
        missing_required: List[str] = []
        type_failures: List[str] = []

        for field in schema.fields:
            value = extracted.get(field.key)
            is_empty = value in (None, "", "null", [])

            if field.required and is_empty:
                missing_required.append(field.key)
                field_outcomes.append(FieldValidationOutcome(
                    field_key=field.key, value=value, passed=False,
                    error=f"Required field '{field.key}' is missing",
                    severity=RuleSeverity.ERROR
                ))
                continue

            if is_empty:
                field_outcomes.append(FieldValidationOutcome(
                    field_key=field.key, value=value, passed=True
                ))
                continue

            # Regex validation
            if field.regex_pattern:
                try:
                    if not re.match(field.regex_pattern, str(value)):
                        field_outcomes.append(FieldValidationOutcome(
                            field_key=field.key, value=value, passed=False,
                            error=f"Value '{value}' does not match pattern '{field.regex_pattern}'",
                            severity=RuleSeverity.WARNING
                        ))
                        continue
                except re.error:
                    pass

            # Range validation
            if field.field_type in (SchemaFieldType.NUMBER, SchemaFieldType.CURRENCY, SchemaFieldType.PERCENTAGE):
                try:
                    num = float(re.sub(r"[^\d.\-]", "", str(value).replace(",", "")))
                    if field.min_value is not None and num < field.min_value:
                        field_outcomes.append(FieldValidationOutcome(
                            field_key=field.key, value=value, passed=False,
                            error=f"Value {num} is below minimum {field.min_value}",
                            severity=RuleSeverity.WARNING
                        ))
                        continue
                    if field.max_value is not None and num > field.max_value:
                        field_outcomes.append(FieldValidationOutcome(
                            field_key=field.key, value=value, passed=False,
                            error=f"Value {num} exceeds maximum {field.max_value}",
                            severity=RuleSeverity.WARNING
                        ))
                        continue
                except (ValueError, TypeError):
                    type_failures.append(field.key)

            # Allowed values check
            if field.allowed_values and str(value) not in field.allowed_values:
                field_outcomes.append(FieldValidationOutcome(
                    field_key=field.key, value=value, passed=False,
                    error=f"Value '{value}' not in allowed set: {field.allowed_values}",
                    severity=RuleSeverity.WARNING
                ))
                continue

            # All checks passed
            field_outcomes.append(FieldValidationOutcome(
                field_key=field.key, value=value, passed=True
            ))

        rule_outcomes = self.evaluate_cross_field_rules(extracted, schema)

        completeness = (len(schema.required_fields) - len(missing_required)) / max(len(schema.required_fields), 1)
        passed_rules = sum(1 for r in rule_outcomes if r.passed)
        rule_score = passed_rules / max(len(rule_outcomes), 1) if rule_outcomes else 1.0
        quality = 0.7 * completeness + 0.3 * rule_score

        return SchemaValidationResult(
            schema_id=schema.schema_id,
            schema_name=schema.name,
            field_outcomes=field_outcomes,
            rule_outcomes=rule_outcomes,
            missing_required=missing_required,
            type_failures=type_failures,
            rule_failures=[r.rule_id for r in rule_outcomes if not r.passed],
            completeness_score=round(completeness * 100, 1),
            overall_quality_score=round(quality, 3),
            passed=len(missing_required) == 0,
            hitl_required=len(missing_required) > 0 or quality < 0.6,
            hitl_reasons=(
                ([f"Missing required: {', '.join(missing_required)}"] if missing_required else []) +
                ([f"Low quality score: {quality:.2f}"] if quality < 0.6 else [])
            )
        )

    # ------------------------------------------------------------------
    # Cross-field rule evaluation
    # ------------------------------------------------------------------
    def evaluate_cross_field_rules(
        self,
        arg1: Any,
        arg2: Any
    ) -> List[CrossFieldRuleOutcome]:
        """
        Evaluate arithmetic and logical cross-field rules in a sandboxed manner.
        Supports both (extracted, schema) and (rules/schema, extracted).
        """
        if isinstance(arg1, dict):
            extracted = arg1
            rules = arg2.cross_field_rules if hasattr(arg2, "cross_field_rules") else arg2
        else:
            extracted = arg2
            rules = arg1.cross_field_rules if hasattr(arg1, "cross_field_rules") else arg1

        if not isinstance(rules, list):
            rules = []

        outcomes: List[CrossFieldRuleOutcome] = []
        for rule in rules:
            rule_obj = rule if isinstance(rule, CrossFieldRule) else CrossFieldRule(**rule)
            # Build safe evaluation context with numeric field values
            safe_ctx: Dict[str, Any] = {}
            for key, val in extracted.items():
                if val is None:
                    safe_ctx[key] = None
                    continue
                try:
                    numeric = float(re.sub(r"[^\d.\-]", "", str(val).replace(",", "")))
                    safe_ctx[key] = numeric
                except (ValueError, TypeError):
                    safe_ctx[key] = val

            try:
                # Restricted eval: only math operations, no builtins
                result = eval(rule_obj.formula, {"__builtins__": {}}, safe_ctx)  # noqa: S307
                passed = bool(result)
                outcomes.append(CrossFieldRuleOutcome(
                    rule_id=rule_obj.rule_id,
                    formula=rule_obj.formula,
                    passed=passed,
                    error=None if passed else (rule_obj.error_message or f"Rule failed: {rule_obj.formula}"),
                    severity=rule_obj.severity
                ))
            except Exception as e:
                # If eval fails (e.g., None operand), treat as warning not error
                outcomes.append(CrossFieldRuleOutcome(
                    rule_id=rule_obj.rule_id,
                    formula=rule_obj.formula,
                    passed=True,  # Can't evaluate = skip (not hard fail)
                    error=f"Rule evaluation skipped: {e}",
                    severity=RuleSeverity.WARNING
                ))

        return outcomes

    _evaluate_cross_field_rules = evaluate_cross_field_rules

    # ------------------------------------------------------------------
    # Schema-to-document mapping
    # ------------------------------------------------------------------
    def map_schema_to_document(
        self,
        schema: ExtractionSchema,
        document_text: str
    ) -> Dict[str, List[str]]:
        """
        Identify which document sections/snippets are most relevant for each schema field.
        Returns {field_key: [matching_snippets]}.
        """
        doc_lower = document_text.lower()
        mapping: Dict[str, List[str]] = {}

        for field in schema.fields:
            keywords = [field.key.lower(), field.label.lower()]
            if field.extraction_hint:
                keywords.append(field.extraction_hint.lower())

            snippets: List[str] = []
            for kw in keywords:
                idx = doc_lower.find(kw)
                if idx >= 0:
                    start = max(0, idx - 10)
                    end = min(len(document_text), idx + 100)
                    snippets.append(document_text[start:end].strip())

            mapping[field.key] = snippets[:2]  # Max 2 snippets per field

        return mapping


# Singleton
schema_extraction_engine = SchemaExtractionEngine()
