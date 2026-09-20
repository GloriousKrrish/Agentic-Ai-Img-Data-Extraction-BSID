"""
Phase 4: Schema Intelligence Engine
Handles NL→Schema conversion, JSON Schema import, schema validation/normalization,
semantic coverage analysis, and schema diff.
"""
from __future__ import annotations
import json
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from backend.agents.schema_models import (
    CrossFieldRule, ExtractionSchema, FieldCoverage, RuleSeverity,
    SchemaCoverageAnalysis, SchemaField, SchemaFieldType, SchemaTable,
    SchemaTableColumn, SchemaVersion
)

# ---------------------------------------------------------------------------
# NL → Schema prompt
# ---------------------------------------------------------------------------
_NL_TO_SCHEMA_PROMPT = """You are an Enterprise Document Schema Architect.
The user wants to extract specific fields from a document.
Convert their description into a structured JSON extraction schema.

USER DESCRIPTION:
{nl_text}

Output STRICTLY valid JSON with this structure:
{{
  "name": "Schema name derived from description",
  "domain": "invoice|medical|kyc|academic|financial|legal|custom",
  "description": "Brief schema purpose",
  "fields": [
    {{
      "key": "camelCaseFieldKey",
      "label": "Human Readable Label",
      "field_type": "string|number|date|boolean|array|object|currency|percentage",
      "required": true|false,
      "description": "How to extract this field from the document",
      "regex_pattern": null,
      "min_value": null,
      "max_value": null,
      "allowed_values": [],
      "extraction_hint": "Where on the document to look"
    }}
  ],
  "tables": [],
  "cross_field_rules": []
}}

Rules:
- Use camelCase for all field keys
- Set required=true for primary identifiers (ID numbers, names, dates, totals)
- For monetary values use field_type "currency"
- For dates use field_type "date"  
- For counts/quantities use field_type "number"
- Add cross_field_rules if arithmetic relationships are obvious (e.g. total = subtotal + tax)
"""

_COVERAGE_ANALYSIS_PROMPT = """You are a Document Intelligence Analyst.
Analyze this document text and estimate how well the following schema fields can be extracted.

DOCUMENT TEXT (first 3000 chars):
{document_text}

SCHEMA FIELDS TO FIND:
{field_list}

For each field, estimate:
1. coverage (0.0 to 1.0): probability the value exists in the document
2. matching_snippets: 1-2 exact text snippets that would contain this value (empty list if not found)

Output strictly valid JSON:
{{
  "overall_coverage": 0.0-1.0,
  "document_summary": "One-sentence summary of the document",
  "field_coverages": [
    {{
      "field_key": "fieldKey",
      "estimated_coverage": 0.0-1.0,
      "matching_snippets": ["snippet1"],
      "confidence": 0.0-1.0
    }}
  ]
}}
"""


class SchemaIntelligenceEngine:
    """
    Central engine for all schema intelligence operations.
    """

    # ------------------------------------------------------------------
    # 1. Entry point: parse any schema input (dict / JSON string / NL)
    # ------------------------------------------------------------------
    def parse_schema(self, raw_input: Any, source: str = "user") -> ExtractionSchema:
        """
        Universal schema parser. Accepts:
        - dict          → treat as structured schema
        - JSON string   → parse then process
        - NL string     → convert via Gemini
        """
        if isinstance(raw_input, ExtractionSchema):
            return raw_input

        if isinstance(raw_input, dict):
            return self._from_dict(raw_input, source)

        if isinstance(raw_input, str):
            stripped = raw_input.strip()
            # Try JSON first
            if stripped.startswith("{") or stripped.startswith("["):
                try:
                    data = json.loads(stripped)
                    return self._from_dict(data, source)
                except json.JSONDecodeError:
                    pass
            # Otherwise treat as natural language
            return self.nl_to_schema(stripped)

        raise ValueError(f"Cannot parse schema from type {type(raw_input)}")

    # ------------------------------------------------------------------
    # 2. Natural Language → Schema via Gemini
    # ------------------------------------------------------------------
    def nl_to_schema(self, nl_text: str) -> ExtractionSchema:
        """Convert plain English field descriptions to ExtractionSchema."""
        from backend.services.job_manager import job_manager
        import backend.config as config
        import requests

        api_key = job_manager.get_api_key()
        if not api_key:
            return self._fallback_nl_schema(nl_text)

        prompt = _NL_TO_SCHEMA_PROMPT.format(nl_text=nl_text[:2000])
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
        }
        models = getattr(config, "MODELS_PRIORITY", []) or ["gemini-2.5-flash", "gemini-2.0-flash"]

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                res = requests.post(url, json=payload, timeout=20)
                if res.status_code == 200:
                    raw = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(raw)
                    data["created_by"] = "nl_converter"
                    schema = self._from_dict(data, "nl_converter")
                    schema = self.normalize_schema(schema)
                    return schema
                elif res.status_code == 429:
                    time.sleep(2)
                    continue
                else:
                    break
            except Exception as e:
                print(f"SchemaIntelligenceEngine NL→Schema error ({model}): {e}")
                break

        return self._fallback_nl_schema(nl_text)

    # ------------------------------------------------------------------
    # 3. JSON Schema import (standard JSON Schema spec → ExtractionSchema)
    # ------------------------------------------------------------------
    def from_json_schema(self, json_schema: Dict[str, Any]) -> ExtractionSchema:
        """Import a standard JSON Schema object into ExtractionSchema format."""
        fields: List[SchemaField] = []
        properties = json_schema.get("properties", {})
        required_keys = set(json_schema.get("required", []))

        for key, prop in properties.items():
            js_type = prop.get("type", "string")
            field_type = self._json_schema_type_map(js_type)
            fields.append(SchemaField(
                key=key,
                label=prop.get("title", key.replace("_", " ").replace("-", " ").title()),
                field_type=field_type,
                required=(key in required_keys),
                description=prop.get("description", ""),
                regex_pattern=prop.get("pattern"),
                min_value=prop.get("minimum"),
                max_value=prop.get("maximum"),
                allowed_values=prop.get("enum", []),
            ))

        schema = ExtractionSchema(
            name=json_schema.get("title", "Imported JSON Schema"),
            description=json_schema.get("description", ""),
            domain="custom",
            fields=fields,
            created_by="json_import"
        )
        return self.normalize_schema(schema)

    # ------------------------------------------------------------------
    # 4. Schema Validation
    # ------------------------------------------------------------------
    def validate_schema(self, schema: ExtractionSchema) -> Tuple[bool, List[str]]:
        """
        Validates an ExtractionSchema for structural correctness.
        Returns (is_valid, list_of_errors).
        """
        errors: List[str] = []

        # Check field key uniqueness
        seen_keys: set = set()
        for f in schema.fields:
            if f.key in seen_keys:
                errors.append(f"Duplicate field key: '{f.key}'")
            seen_keys.add(f.key)

        # Check at least one field
        if not schema.fields:
            errors.append("Schema must have at least one field")

        # Validate regex patterns
        for f in schema.fields:
            if f.regex_pattern:
                try:
                    re.compile(f.regex_pattern)
                except re.error as e:
                    errors.append(f"Invalid regex in field '{f.key}': {e}")

        # Validate cross-field rules reference valid field keys
        field_keys = {f.key for f in schema.fields}
        for rule in schema.cross_field_rules:
            for fk in rule.fields_involved:
                if fk not in field_keys:
                    errors.append(f"Rule '{rule.rule_id}' references unknown field '{fk}'")

        # Validate table column key uniqueness
        for tbl in schema.tables:
            seen_col_keys: set = set()
            for col in tbl.columns:
                if col.key in seen_col_keys:
                    errors.append(f"Duplicate column key '{col.key}' in table '{tbl.table_id}'")
                seen_col_keys.add(col.key)

        return (len(errors) == 0), errors

    # ------------------------------------------------------------------
    # 5. Schema Normalization
    # ------------------------------------------------------------------
    def normalize_schema(self, schema: ExtractionSchema) -> ExtractionSchema:
        """
        Normalizes field keys (camelCase), fills default labels,
        resolves duplicate keys, and fills missing descriptions.
        """
        seen: Dict[str, int] = {}
        normalized_fields: List[SchemaField] = []

        for f in schema.fields:
            # Normalize key to camelCase
            normalized_key = self._to_camel_case(f.key)

            # Handle duplicates by appending counter
            if normalized_key in seen:
                seen[normalized_key] += 1
                normalized_key = f"{normalized_key}_{seen[normalized_key]}"
            else:
                seen[normalized_key] = 0

            # Fill label if empty
            label = f.label or normalized_key.replace("_", " ").title()

            # Fill description if empty
            desc = f.description or f"Extract the {label} from the document."

            normalized_fields.append(f.model_copy(update={
                "key": normalized_key,
                "label": label,
                "description": desc
            }))

        schema = schema.model_copy(update={
            "fields": normalized_fields,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        return schema

    # ------------------------------------------------------------------
    # 6. Schema Semantic Coverage Analysis
    # ------------------------------------------------------------------
    def analyze_coverage(self, schema: ExtractionSchema, document_text: str) -> SchemaCoverageAnalysis:
        """
        Estimates field-by-field coverage of schema fields in the given document text.
        Uses Gemini for semantic analysis. Falls back to keyword matching if unavailable.
        """
        from backend.services.job_manager import job_manager
        import backend.config as config
        import requests

        field_list = "\n".join([
            f"- key: {f.key}, label: {f.label}, description: {f.description}"
            for f in schema.fields
        ])

        api_key = job_manager.get_api_key()
        if api_key:
            prompt = _COVERAGE_ANALYSIS_PROMPT.format(
                document_text=document_text[:3000],
                field_list=field_list
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.0}
            }
            models = getattr(config, "MODELS_PRIORITY", []) or ["gemini-2.5-flash"]
            for model in models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                try:
                    res = requests.post(url, json=payload, timeout=20)
                    if res.status_code == 200:
                        raw = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                        data = json.loads(raw)
                        coverages = []
                        for fc in data.get("field_coverages", []):
                            if isinstance(fc, dict):
                                if "label" not in fc or not fc["label"]:
                                    fc["label"] = fc.get("field_key", "")
                                coverages.append(FieldCoverage(**fc))
                        uncoverable = [
                            fc.field_key for fc in coverages if fc.estimated_coverage < 0.2
                        ]
                        return SchemaCoverageAnalysis(
                            schema_id=schema.schema_id,
                            overall_coverage=data.get("overall_coverage", 0.5),
                            field_coverages=coverages,
                            uncoverable_fields=uncoverable,
                            document_summary=data.get("document_summary", "")
                        )
                    elif res.status_code == 429:
                        time.sleep(2)
                    else:
                        break
                except Exception as e:
                    print(f"Coverage analysis error ({model}): {e}")
                    break

        # Fallback: keyword matching
        return self._keyword_coverage_analysis(schema, document_text)

    # ------------------------------------------------------------------
    # 7. Schema Diff
    # ------------------------------------------------------------------
    def schema_diff(self, schema_v1: ExtractionSchema, schema_v2: ExtractionSchema) -> SchemaVersion:
        """Compare two schema versions and produce a SchemaVersion diff record."""
        keys_v1 = {f.key for f in schema_v1.fields}
        keys_v2 = {f.key for f in schema_v2.fields}

        added = list(keys_v2 - keys_v1)
        removed = list(keys_v1 - keys_v2)
        common = keys_v1 & keys_v2

        modified = []
        v1_map = {f.key: f for f in schema_v1.fields}
        v2_map = {f.key: f for f in schema_v2.fields}
        for k in common:
            if v1_map[k].model_dump() != v2_map[k].model_dump():
                modified.append(k)

        changes = []
        if added:
            changes.append(f"Added fields: {', '.join(added)}")
        if removed:
            changes.append(f"Removed fields: {', '.join(removed)}")
        if modified:
            changes.append(f"Modified fields: {', '.join(modified)}")
        diff_summary = "; ".join(changes) if changes else "No changes"

        return SchemaVersion(
            schema_id=schema_v2.schema_id,
            version=schema_v2.version,
            diff_summary=diff_summary,
            fields_added=added,
            fields_removed=removed,
            fields_modified=modified,
            snapshot=schema_v2.model_dump()
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _from_dict(self, data: Dict[str, Any], source: str = "user") -> ExtractionSchema:
        """Build ExtractionSchema from a raw dictionary."""
        # Support both 'fields' list and flat field-key dict
        raw_fields = data.get("fields", [])
        parsed_fields: List[SchemaField] = []

        for f in raw_fields:
            if isinstance(f, dict):
                # Map 'type' key to 'field_type' if needed
                if "type" in f and "field_type" not in f:
                    f["field_type"] = f.pop("type")
                try:
                    parsed_fields.append(SchemaField(**f))
                except Exception:
                    # Best-effort: only require key+label
                    parsed_fields.append(SchemaField(
                        key=f.get("key", f"field_{len(parsed_fields)}"),
                        label=f.get("label", f.get("key", "Field")),
                        field_type=SchemaFieldType.STRING,
                        description=f.get("description", "")
                    ))

        # Tables
        raw_tables = data.get("tables", [])
        parsed_tables: List[SchemaTable] = []
        for t in raw_tables:
            if isinstance(t, dict):
                cols = [SchemaTableColumn(**c) for c in t.get("columns", [])]
                parsed_tables.append(SchemaTable(
                    table_id=t.get("table_id", f"tbl-{uuid.uuid4().hex[:6]}"),
                    label=t.get("label", "Table"),
                    description=t.get("description", ""),
                    columns=cols,
                    min_rows=t.get("min_rows", 0),
                    max_rows=t.get("max_rows")
                ))

        # Cross-field rules
        raw_rules = data.get("cross_field_rules", [])
        parsed_rules: List[CrossFieldRule] = []
        for r in raw_rules:
            if isinstance(r, dict):
                try:
                    parsed_rules.append(CrossFieldRule(**r))
                except Exception:
                    pass

        schema_id = data.get("schema_id", f"schema-{uuid.uuid4().hex[:8]}")
        return ExtractionSchema(
            schema_id=schema_id,
            name=data.get("name", "Custom Schema"),
            version=data.get("version", "1.0.0"),
            domain=data.get("domain", "custom"),
            description=data.get("description", ""),
            fields=parsed_fields,
            tables=parsed_tables,
            cross_field_rules=parsed_rules,
            created_by=source,
            tags=data.get("tags", [])
        )

    def _fallback_nl_schema(self, nl_text: str) -> ExtractionSchema:
        """Parse NL using regex/heuristics when Gemini is unavailable."""
        # Extract comma/newline/semicolon separated field names
        separators = r"[,\n;]+"
        raw_tokens = re.split(separators, nl_text)
        fields: List[SchemaField] = []
        for token in raw_tokens:
            token = token.strip().strip("- •").strip()
            if len(token) < 2:
                continue
            # Remove type hints in parens like "invoice_number (string)"
            token = re.sub(r"\(.*?\)", "", token).strip()
            # Normalize to camelCase key
            key = self._to_camel_case(re.sub(r"[^a-zA-Z0-9_\s]", "", token).strip())
            if not key:
                continue
            label = key.replace("_", " ").title()
            fields.append(SchemaField(key=key, label=label, field_type=SchemaFieldType.STRING,
                                      description=f"Extract the {label} from the document."))

        if not fields:
            fields = [SchemaField(key="extractedData", label="Extracted Data",
                                   field_type=SchemaFieldType.STRING,
                                   description="General extracted data")]

        return ExtractionSchema(
            name="Auto-parsed Schema",
            domain="custom",
            description=f"Schema auto-parsed from: {nl_text[:100]}",
            fields=fields,
            created_by="nl_fallback"
        )

    def _to_camel_case(self, s: str) -> str:
        """Convert any string to camelCase."""
        s = re.sub(r"[^a-zA-Z0-9\s_]", "", s).strip()
        parts = re.split(r"[\s_]+", s)
        if not parts:
            return s
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])

    def _json_schema_type_map(self, js_type: str) -> SchemaFieldType:
        mapping = {
            "string": SchemaFieldType.STRING,
            "number": SchemaFieldType.NUMBER,
            "integer": SchemaFieldType.NUMBER,
            "boolean": SchemaFieldType.BOOLEAN,
            "array": SchemaFieldType.ARRAY,
            "object": SchemaFieldType.OBJECT
        }
        return mapping.get(js_type, SchemaFieldType.STRING)

    def _keyword_coverage_analysis(self, schema: ExtractionSchema, document_text: str) -> SchemaCoverageAnalysis:
        """Fallback: simple keyword presence check for each field."""
        doc_lower = document_text.lower()
        coverages: List[FieldCoverage] = []
        total_coverage = 0.0

        for f in schema.fields:
            keywords = [f.key.lower(), f.label.lower()] + [w.lower() for w in f.label.split()]
            found = any(kw in doc_lower for kw in keywords if len(kw) > 3)
            cov = 0.7 if found else 0.1
            total_coverage += cov
            snippet: List[str] = []
            if found:
                for kw in keywords:
                    idx = doc_lower.find(kw)
                    if idx >= 0:
                        start = max(0, idx - 20)
                        end = min(len(document_text), idx + 60)
                        snippet = [document_text[start:end].strip()]
                        break
            coverages.append(FieldCoverage(
                field_key=f.key, label=f.label,
                estimated_coverage=cov, matching_snippets=snippet, confidence=cov
            ))

        overall = total_coverage / max(len(schema.fields), 1)
        uncoverable = [c.field_key for c in coverages if c.estimated_coverage < 0.2]
        return SchemaCoverageAnalysis(
            schema_id=schema.schema_id,
            overall_coverage=overall,
            field_coverages=coverages,
            uncoverable_fields=uncoverable,
            document_summary="Keyword-based coverage analysis (API unavailable)"
        )


# Singleton
schema_intelligence_engine = SchemaIntelligenceEngine()
