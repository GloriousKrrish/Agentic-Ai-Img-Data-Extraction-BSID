"""
Phase 4 -- Schema Intelligence Verification Test Suite
verify_schema_intelligence.py

60 test scenarios covering:
  1.  Schema model creation and field validation (10 tests)
  2.  SchemaIntelligenceEngine: NL->schema, JSON import, normalization, diff (15 tests)
  3.  SchemaStore: CRUD, versioning, version history (10 tests)
  4.  SchemaExtractionEngine: constrained extraction, cross-field rules (15 tests)
  5.  End-to-end: planner -> engine -> validation path (10 tests)

Usage:
    cd <repo_root>
    python verify_schema_intelligence.py

Reports pass/fail per test. Does NOT fabricate metrics.
"""

import sys
import json
import uuid
import time
import traceback
from pathlib import Path

# --- Bootstrap path -----------------------------------------------------------
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# --- Colour helpers -----------------------------------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"

RESULTS = []

def run(name: str, fn):
    """Execute a test function, catch exceptions, record pass/fail."""
    try:
        fn()
        RESULTS.append((name, "PASS", None))
        print(f"  {GREEN}v PASS{RESET}  {name}")
    except AssertionError as e:
        RESULTS.append((name, "FAIL", str(e)))
        print(f"  {RED}x FAIL{RESET}  {name}\n         {RED}-> {e}{RESET}")
    except Exception as e:
        RESULTS.append((name, "ERROR", f"{type(e).__name__}: {e}"))
        print(f"  {YELLOW}! ERROR{RESET} {name}\n         {YELLOW}-> {type(e).__name__}: {e}{RESET}")
        traceback.print_exc()


# -----------------------------------------------------------------------------
# 1. SCHEMA MODELS (10 tests)
# -----------------------------------------------------------------------------
def test_schema_models():
    from backend.agents.schema_models import (
        SchemaField, SchemaFieldType, ExtractionSchema, CrossFieldRule,
        FieldValidationOutcome, SchemaExtractionReport
    )

    print(f"\n{CYAN}=== SECTION 1: Schema Models ==={RESET}")

    def t1():
        f = SchemaField(key="invoice_number", label="Invoice Number", field_type=SchemaFieldType.STRING)
        assert f.key == "invoice_number"
        assert f.required is False

    def t2():
        f = SchemaField(key="total", label="Total", field_type=SchemaFieldType.CURRENCY, required=True, min_value=0)
        assert f.required is True
        assert f.min_value == 0

    def t3():
        s = ExtractionSchema(
            schema_id=f"sch-{uuid.uuid4().hex[:8]}",
            name="Test Schema",
            fields=[
                SchemaField(key="a", label="A", field_type=SchemaFieldType.STRING, required=True),
                SchemaField(key="b", label="B", field_type=SchemaFieldType.NUMBER),
            ]
        )
        assert len(s.fields) == 2
        assert len(s.required_fields) == 1
        assert s.required_fields[0].key == "a"

    def t4():
        s = ExtractionSchema(
            schema_id=f"sch-{uuid.uuid4().hex[:8]}",
            name="Rule Test",
            fields=[
                SchemaField(key="sub", label="Subtotal", field_type=SchemaFieldType.NUMBER),
                SchemaField(key="tax", label="Tax", field_type=SchemaFieldType.NUMBER),
                SchemaField(key="total", label="Total", field_type=SchemaFieldType.NUMBER, required=True),
            ],
            cross_field_rules=[
                CrossFieldRule(
                    formula="total == sub + tax",
                    description="Total must equal subtotal + tax",
                    error_message="Total mismatch",
                    severity="error",
                    fields_involved=["sub", "tax", "total"]
                )
            ]
        )
        assert len(s.cross_field_rules) == 1
        assert s.cross_field_rules[0].severity == "error"

    def t5():
        # SchemaFieldType enum values
        assert SchemaFieldType.STRING.value == "string"
        assert SchemaFieldType.NUMBER.value == "number"
        assert SchemaFieldType.DATE.value == "date"
        assert SchemaFieldType.CURRENCY.value == "currency"

    def t6():
        # Field with allowed_values
        f = SchemaField(key="status", label="Status", field_type=SchemaFieldType.STRING, allowed_values=["active", "inactive"])
        assert "active" in f.allowed_values

    def t7():
        # SchemaExtractionReport defaults
        r = SchemaExtractionReport(
            schema_id="s1", schema_name="S", schema_version="1.0.0",
            total_fields=5, extracted_fields_count=3, missing_required=["x"],
            completeness_pct=60, quality_score=0.6, hitl_required=True
        )
        assert r.hitl_required is True
        assert r.completeness_pct == 60

    def t8():
        # FieldValidationOutcome
        o = FieldValidationOutcome(field_key="invoice_date", value="2024-01-01", passed=True, confidence=0.95)
        assert o.passed is True
        assert o.confidence == 0.95

    def t9():
        # FieldValidationOutcome failure case
        o = FieldValidationOutcome(field_key="total", value=None, passed=False, error="Required field missing", confidence=0.0)
        assert o.passed is False
        assert o.error == "Required field missing"

    def t10():
        # ExtractionSchema .model_dump() is serializable
        s = ExtractionSchema(schema_id=f"sch-test", name="Dump Test", fields=[])
        d = s.model_dump()
        assert isinstance(d, dict)
        json.dumps(d)  # must be JSON-serializable

    for idx, fn in enumerate([t1, t2, t3, t4, t5, t6, t7, t8, t9, t10], 1):
        run(f"Schema Models [{idx:02d}]: {fn.__doc__ or fn.__name__}", fn)


# -----------------------------------------------------------------------------
# 2. SCHEMA INTELLIGENCE ENGINE (15 tests)
# -----------------------------------------------------------------------------
def test_schema_intelligence_engine():
    from backend.services.schema_intelligence_engine import schema_intelligence_engine
    from backend.agents.schema_models import ExtractionSchema

    print(f"\n{CYAN}=== SECTION 2: Schema Intelligence Engine ==={RESET}")

    def t1():
        # parse_schema from dict
        raw = {
            "name": "Invoice Schema",
            "fields": [
                {"key": "invoice_number", "label": "Invoice Number", "field_type": "string", "required": True},
                {"key": "total", "label": "Total", "field_type": "currency"},
            ]
        }
        schema = schema_intelligence_engine.parse_schema(raw, source="test")
        assert isinstance(schema, ExtractionSchema)
        assert schema.name == "Invoice Schema"
        assert len(schema.fields) == 2

    def t2():
        # parse_schema assigns schema_id if none
        raw = {"name": "NoID Schema", "fields": []}
        schema = schema_intelligence_engine.parse_schema(raw, source="test")
        assert schema.schema_id  # non-empty

    def t3():
        # validate_schema: valid schema
        from backend.agents.schema_models import SchemaField, SchemaFieldType
        schema = ExtractionSchema(
            schema_id="s1", name="Valid",
            fields=[SchemaField(key="f1", label="F1", field_type=SchemaFieldType.STRING)]
        )
        is_valid, errors = schema_intelligence_engine.validate_schema(schema)
        assert is_valid is True, f"Errors: {errors}"

    def t4():
        # validate_schema: duplicate keys -> invalid
        from backend.agents.schema_models import SchemaField, SchemaFieldType
        schema = ExtractionSchema(
            schema_id="s2", name="Dupes",
            fields=[
                SchemaField(key="dup", label="A", field_type=SchemaFieldType.STRING),
                SchemaField(key="dup", label="B", field_type=SchemaFieldType.STRING),
            ]
        )
        is_valid, errors = schema_intelligence_engine.validate_schema(schema)
        assert is_valid is False
        assert any("duplicate" in e.lower() or "dup" in e.lower() for e in errors)

    def t5():
        # normalize_schema: keys become snake_case friendly
        from backend.agents.schema_models import SchemaField, SchemaFieldType
        schema = ExtractionSchema(
            schema_id="s3", name="Normalize",
            fields=[SchemaField(key="Invoice Number", label="Invoice Number", field_type=SchemaFieldType.STRING)]
        )
        normalized = schema_intelligence_engine.normalize_schema(schema)
        assert all(" " not in f.key for f in normalized.fields)

    def t6():
        # from_json_schema: standard JSON Schema format
        json_schema = {
            "title": "Payment",
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Payment amount"},
                "date": {"type": "string", "description": "Payment date"},
            },
            "required": ["amount"]
        }
        schema = schema_intelligence_engine.from_json_schema(json_schema)
        assert len(schema.fields) == 2
        req_keys = [f.key for f in schema.fields if f.required]
        assert "amount" in req_keys

    def t7():
        # from_json_schema: empty schema
        schema = schema_intelligence_engine.from_json_schema({"properties": {}})
        assert isinstance(schema, ExtractionSchema)

    def t8():
        # analyze_coverage: detects fields likely present in text
        from backend.agents.schema_models import SchemaField, SchemaFieldType
        schema = ExtractionSchema(
            schema_id="s4", name="Coverage",
            fields=[
                SchemaField(key="vendor_name", label="Vendor Name", field_type=SchemaFieldType.STRING),
                SchemaField(key="invoice_number", label="Invoice Number", field_type=SchemaFieldType.STRING),
                SchemaField(key="patient_id", label="Patient ID", field_type=SchemaFieldType.STRING),
            ]
        )
        text = "Invoice #INV-2024-001 from Acme Corp. Dated 2024-01-15."
        result = schema_intelligence_engine.analyze_coverage(schema, text)
        assert hasattr(result, 'field_coverages')
        assert hasattr(result, 'uncoverable_fields')

    def t9():
        # analyze_coverage: all fields missing in empty text
        from backend.agents.schema_models import SchemaField, SchemaFieldType
        schema = ExtractionSchema(
            schema_id="s5", name="Empty Coverage",
            fields=[SchemaField(key="magic_field", label="Magic Field", field_type=SchemaFieldType.STRING)]
        )
        result = schema_intelligence_engine.analyze_coverage(schema, "")
        assert isinstance(result.uncoverable_fields, list)

    def t10():
        # schema_diff: detects added fields
        from backend.agents.schema_models import SchemaField, SchemaFieldType
        s_a = ExtractionSchema(
            schema_id="da", name="V1",
            fields=[SchemaField(key="f1", label="F1", field_type=SchemaFieldType.STRING)]
        )
        s_b = ExtractionSchema(
            schema_id="da", name="V2",
            fields=[
                SchemaField(key="f1", label="F1", field_type=SchemaFieldType.STRING),
                SchemaField(key="f2", label="F2", field_type=SchemaFieldType.NUMBER),
            ]
        )
        diff = schema_intelligence_engine.schema_diff(s_a, s_b)
        assert hasattr(diff, 'fields_added')
        assert "f2" in diff.fields_added

    def t11():
        # schema_diff: detects removed fields
        from backend.agents.schema_models import SchemaField, SchemaFieldType
        s_a = ExtractionSchema(
            schema_id="db", name="V1",
            fields=[
                SchemaField(key="f1", label="F1", field_type=SchemaFieldType.STRING),
                SchemaField(key="f2", label="F2", field_type=SchemaFieldType.NUMBER),
            ]
        )
        s_b = ExtractionSchema(
            schema_id="db", name="V2",
            fields=[SchemaField(key="f1", label="F1", field_type=SchemaFieldType.STRING)]
        )
        diff = schema_intelligence_engine.schema_diff(s_a, s_b)
        assert "f2" in diff.fields_removed

    def t12():
        # schema_diff: no change
        from backend.agents.schema_models import SchemaField, SchemaFieldType
        s = ExtractionSchema(
            schema_id="dc", name="Same",
            fields=[SchemaField(key="f1", label="F1", field_type=SchemaFieldType.STRING)]
        )
        diff = schema_intelligence_engine.schema_diff(s, s)
        assert not diff.fields_added
        assert not diff.fields_removed

    def t13():
        # parse_schema preserves cross_field_rules
        raw = {
            "name": "Rule Schema",
            "fields": [
                {"key": "a", "label": "A", "field_type": "number"},
                {"key": "b", "label": "B", "field_type": "number"},
            ],
            "cross_field_rules": [
                {"formula": "a > b", "description": "A > B", "severity": "warning", "fields_involved": ["a", "b"], "error_message": "A must exceed B"}
            ]
        }
        schema = schema_intelligence_engine.parse_schema(raw, source="test")
        assert len(schema.cross_field_rules) == 1
        assert schema.cross_field_rules[0].formula == "a > b"

    def t14():
        # validate_schema: missing name -> invalid
        schema = ExtractionSchema(schema_id="s_noname", name="", fields=[])
        is_valid, errors = schema_intelligence_engine.validate_schema(schema)
        assert is_valid is False

    def t15():
        # normalize_schema returns ExtractionSchema type
        from backend.agents.schema_models import SchemaField, SchemaFieldType
        schema = ExtractionSchema(
            schema_id="norm2", name="Norm",
            fields=[SchemaField(key="x", label="X", field_type=SchemaFieldType.STRING)]
        )
        result = schema_intelligence_engine.normalize_schema(schema)
        assert isinstance(result, ExtractionSchema)

    for idx, fn in enumerate([t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15], 1):
        run(f"Intelligence Engine [{idx:02d}]: {fn.__doc__ or fn.__name__}", fn)


# -----------------------------------------------------------------------------
# 3. SCHEMA STORE (10 tests)
# -----------------------------------------------------------------------------
def test_schema_store():
    import tempfile, os
    from pathlib import Path
    from backend.services.schema_store import SchemaStore
    from backend.agents.schema_models import ExtractionSchema, SchemaField, SchemaFieldType

    print(f"\n{CYAN}=== SECTION 3: Schema Store ==={RESET}")

    # Use a fresh temp DB for isolation
    tmp_db = Path(tempfile.mkdtemp()) / "test_schemas.sqlite3"
    store = SchemaStore(db_path=tmp_db)

    def make_schema(name="Test"):
        return ExtractionSchema(
            schema_id=f"sch-{uuid.uuid4().hex[:8]}",
            name=name,
            fields=[SchemaField(key="f1", label="Field 1", field_type=SchemaFieldType.STRING, required=True)]
        )

    def t1():
        s = store.save_schema(make_schema("Schema A"))
        assert s.schema_id

    def t2():
        s = make_schema("Schema B")
        store.save_schema(s)
        retrieved = store.get_schema(s.schema_id)
        assert retrieved is not None
        assert retrieved.name == "Schema B"

    def t3():
        # List schemas
        store.save_schema(make_schema("List Test 1"))
        store.save_schema(make_schema("List Test 2"))
        schemas = store.list_schemas()
        assert len(schemas) >= 2

    def t4():
        # Update schema
        s = make_schema("Before Update")
        store.save_schema(s)
        updated = store.update_schema(s.schema_id, {"name": "After Update"}, previous_schema=s)
        assert updated.name == "After Update"

    def t5():
        # Delete schema
        s = make_schema("To Delete")
        store.save_schema(s)
        deleted = store.delete_schema(s.schema_id)
        assert deleted is True
        assert store.get_schema(s.schema_id) is None

    def t6():
        # Get non-existent schema returns None
        result = store.get_schema("nonexistent-id-99999")
        assert result is None

    def t7():
        # Delete non-existent schema returns False
        result = store.delete_schema("ghost-schema-99")
        assert result is False

    def t8():
        # Version history on update
        s = make_schema("Versioned Schema")
        store.save_schema(s)
        store.update_schema(s.schema_id, {"description": "v2"}, previous_schema=s)
        versions = store.get_schema_versions(s.schema_id)
        assert isinstance(versions, list)
        assert len(versions) >= 1

    def t9():
        # Schema is JSON-serializable after retrieval
        s = make_schema("Serializable")
        store.save_schema(s)
        retrieved = store.get_schema(s.schema_id)
        d = retrieved.model_dump()
        json.dumps(d)  # no exception

    def t10():
        # save_schema with cross-field rules preserved
        from backend.agents.schema_models import CrossFieldRule, SchemaField, SchemaFieldType
        s = ExtractionSchema(
            schema_id=f"sch-{uuid.uuid4().hex[:8]}",
            name="Rule Store Test",
            fields=[
                SchemaField(key="a", label="A", field_type=SchemaFieldType.NUMBER),
                SchemaField(key="b", label="B", field_type=SchemaFieldType.NUMBER),
            ],
            cross_field_rules=[
                CrossFieldRule(formula="a > 0", description="A positive", severity="error", fields_involved=["a"], error_message="A must be positive")
            ]
        )
        store.save_schema(s)
        retrieved = store.get_schema(s.schema_id)
        assert len(retrieved.cross_field_rules) == 1

    for idx, fn in enumerate([t1, t2, t3, t4, t5, t6, t7, t8, t9, t10], 1):
        run(f"Schema Store [{idx:02d}]: {fn.__doc__ or fn.__name__}", fn)


# -----------------------------------------------------------------------------
# 4. SCHEMA EXTRACTION ENGINE (15 tests)
# -----------------------------------------------------------------------------
def test_schema_extraction_engine():
    from backend.services.schema_extraction_engine import SchemaExtractionEngine
    from backend.agents.schema_models import (
        ExtractionSchema, SchemaField, SchemaFieldType, CrossFieldRule, SchemaExtractionReport
    )

    print(f"\n{CYAN}=== SECTION 4: Schema Extraction Engine ==={RESET}")

    engine = SchemaExtractionEngine()

    def make_invoice_schema():
        return ExtractionSchema(
            schema_id="inv-test",
            name="Invoice",
            fields=[
                SchemaField(key="invoice_number", label="Invoice Number", field_type=SchemaFieldType.STRING, required=True),
                SchemaField(key="vendor_name", label="Vendor Name", field_type=SchemaFieldType.STRING, required=True),
                SchemaField(key="invoice_date", label="Invoice Date", field_type=SchemaFieldType.DATE),
                SchemaField(key="subtotal", label="Subtotal", field_type=SchemaFieldType.CURRENCY),
                SchemaField(key="tax", label="Tax", field_type=SchemaFieldType.CURRENCY),
                SchemaField(key="grand_total", label="Grand Total", field_type=SchemaFieldType.CURRENCY, required=True),
            ],
            cross_field_rules=[
                CrossFieldRule(
                    formula="grand_total == subtotal + tax",
                    description="Grand total check",
                    error_message="Grand total mismatch",
                    severity="error",
                    fields_involved=["subtotal", "tax", "grand_total"]
                )
            ]
        )

    SAMPLE_TEXT = """
    INVOICE #INV-2024-001
    Vendor: Acme Corp
    Date: 2024-01-15
    Subtotal: 1000.00
    Tax: 100.00
    Grand Total: 1100.00
    """
    SAMPLE_BYTES = SAMPLE_TEXT.encode("utf-8")
    SAMPLE_MIME = "text/plain"

    def t1():
        schema = make_invoice_schema()
        fields, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        assert isinstance(fields, dict)
        assert isinstance(report, SchemaExtractionReport)

    def t2():
        schema = make_invoice_schema()
        _, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        assert report.total_fields == 6

    def t3():
        schema = make_invoice_schema()
        _, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        assert 0 <= report.completeness_pct <= 100

    def t4():
        schema = make_invoice_schema()
        _, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        assert 0.0 <= report.quality_score <= 1.0

    def t5():
        schema = make_invoice_schema()
        _, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        assert isinstance(report.field_outcomes, list)
        assert len(report.field_outcomes) == 6

    def t6():
        schema = make_invoice_schema()
        _, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        assert isinstance(report.missing_required, list)

    def t7():
        schema = make_invoice_schema()
        _, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        assert isinstance(report.hitl_required, bool)

    def t8():
        # cross-field rule: valid case
        schema = ExtractionSchema(
            schema_id="rule-val",
            name="Rule Valid",
            fields=[
                SchemaField(key="a", label="A", field_type=SchemaFieldType.NUMBER),
                SchemaField(key="b", label="B", field_type=SchemaFieldType.NUMBER),
                SchemaField(key="total", label="Total", field_type=SchemaFieldType.NUMBER, required=True),
            ],
            cross_field_rules=[
                CrossFieldRule(formula="total == a + b", description="Sum check", severity="error", fields_involved=["a", "b", "total"], error_message="Sum mismatch")
            ]
        )
        extracted = {"a": 100.0, "b": 200.0, "total": 300.0}
        outcomes = engine._evaluate_cross_field_rules(schema.cross_field_rules, extracted)
        assert len(outcomes) == 1
        assert outcomes[0].get("passed") is True

    def t9():
        # cross-field rule: violation case
        schema = ExtractionSchema(
            schema_id="rule-vio",
            name="Rule Violation",
            fields=[
                SchemaField(key="a", label="A", field_type=SchemaFieldType.NUMBER),
                SchemaField(key="total", label="Total", field_type=SchemaFieldType.NUMBER, required=True),
            ],
            cross_field_rules=[
                CrossFieldRule(formula="total == a * 2", description="Double check", severity="error", fields_involved=["a", "total"], error_message="Total must be 2x a")
            ]
        )
        extracted = {"a": 10.0, "total": 25.0}  # Should be 20, not 25
        outcomes = engine._evaluate_cross_field_rules(schema.cross_field_rules, extracted)
        assert len(outcomes) == 1
        assert outcomes[0].get("passed") is False

    def t10():
        # report has hitl_reasons list
        schema = make_invoice_schema()
        _, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        assert isinstance(report.hitl_reasons, list)

    def t11():
        # empty schema -> completeness=100 and quality_score=1.0 (no required fields missing)
        schema = ExtractionSchema(schema_id="empty-s", name="Empty", fields=[])
        _, report = engine.extract_with_schema(schema=schema, file_bytes=b"text", mime_type="text/plain", text_content="")
        # completeness is 100% since no fields need extracting
        assert report.completeness_pct == 100

    def t12():
        # Field outcome passed flag is boolean
        schema = make_invoice_schema()
        _, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        for fo in report.field_outcomes:
            assert isinstance(fo.passed, bool)

    def t13():
        # cross_field_rules_failed is an int
        schema = make_invoice_schema()
        _, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        assert isinstance(report.cross_field_rules_failed, int)

    def t14():
        # report schema_id matches
        schema = make_invoice_schema()
        _, report = engine.extract_with_schema(schema=schema, file_bytes=SAMPLE_BYTES, mime_type=SAMPLE_MIME, text_content=SAMPLE_TEXT)
        assert report.schema_id == "inv-test"

    def t15():
        # Extracted fields dict keys are schema field keys
        schema = ExtractionSchema(
            schema_id="key-check",
            name="Key Check",
            fields=[
                SchemaField(key="my_field_one", label="My Field One", field_type=SchemaFieldType.STRING),
                SchemaField(key="my_field_two", label="My Field Two", field_type=SchemaFieldType.STRING),
            ]
        )
        fields, _ = engine.extract_with_schema(schema=schema, file_bytes=b"Some text about nothing", mime_type="text/plain", text_content="Some text")
        for key in fields:
            assert key in ["my_field_one", "my_field_two"], f"Unexpected key: {key}"

    for idx, fn in enumerate([t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15], 1):
        run(f"Extraction Engine [{idx:02d}]: {fn.__doc__ or fn.__name__}", fn)


# -----------------------------------------------------------------------------
# 5. END-TO-END: Planner -> Engine -> Validation Path (10 tests)
# -----------------------------------------------------------------------------
def test_end_to_end():
    from backend.agents.schema_models import ExtractionSchema, SchemaField, SchemaFieldType

    print(f"\n{CYAN}=== SECTION 5: End-to-End Integration ==={RESET}")

    def make_e2e_schema():
        return ExtractionSchema(
            schema_id="e2e-test",
            name="E2E Test Schema",
            domain="invoice",
            fields=[
                SchemaField(key="invoice_number", label="Invoice Number", field_type=SchemaFieldType.STRING, required=True),
                SchemaField(key="vendor_name", label="Vendor", field_type=SchemaFieldType.STRING),
                SchemaField(key="amount", label="Amount", field_type=SchemaFieldType.CURRENCY, required=True),
            ]
        )

    def t1():
        # PlannerAgent sets schema_strategy='user_defined' with user_schema
        from backend.agents.planner_agent import planner_agent
        from backend.agents.input_analyzer_agent import input_analyzer_agent
        text = b"Invoice test document"
        analysis = input_analyzer_agent.analyze(text, "test.txt", "text/plain")
        schema = make_e2e_schema()
        plan = planner_agent.create_plan(analysis, user_schema=schema)
        assert plan.schema_strategy == "user_defined"

    def t2():
        # PlannerAgent includes schema_extraction_engine in agents list
        from backend.agents.planner_agent import planner_agent
        from backend.agents.input_analyzer_agent import input_analyzer_agent
        analysis = input_analyzer_agent.analyze(b"text", "test.txt", "text/plain")
        schema = make_e2e_schema()
        plan = planner_agent.create_plan(analysis, user_schema=schema)
        assert "schema_extraction_engine" in plan.agents

    def t3():
        # PlannerAgent without user_schema uses dynamic strategy
        from backend.agents.planner_agent import planner_agent
        from backend.agents.input_analyzer_agent import input_analyzer_agent
        analysis = input_analyzer_agent.analyze(b"text", "test.txt", "text/plain")
        plan = planner_agent.create_plan(analysis)
        assert plan.schema_strategy == "dynamic"
        assert "schema_extraction_engine" not in plan.agents

    def t4():
        # Plan input_classification contains user_schema_id when schema passed
        from backend.agents.planner_agent import planner_agent
        from backend.agents.input_analyzer_agent import input_analyzer_agent
        analysis = input_analyzer_agent.analyze(b"text", "test.txt", "text/plain")
        schema = make_e2e_schema()
        plan = planner_agent.create_plan(analysis, user_schema=schema)
        assert plan.input_classification.get("user_schema_id") == "e2e-test"
        assert plan.input_classification.get("user_schema_field_count") == 3

    def t5():
        # AgenticExecutionEngine runs without exception for user_schema (text/plain)
        from backend.services.agentic_engine import agentic_execution_engine
        schema = make_e2e_schema()
        result = agentic_execution_engine.execute_agentic_workflow(
            file_bytes=b"Invoice #INV-001 from Acme Corp. Amount: $500.00",
            filename="test.txt",
            mime_type="text/plain",
            user_schema=schema
        )
        assert "status" in result
        assert "extractedFields" in result

    def t6():
        # AgenticExecutionEngine returns schemaValidation when user_schema present
        from backend.services.agentic_engine import agentic_execution_engine
        schema = make_e2e_schema()
        result = agentic_execution_engine.execute_agentic_workflow(
            file_bytes=b"Invoice #INV-001 from Acme Corp. Amount: $500.00",
            filename="test.txt",
            mime_type="text/plain",
            user_schema=schema
        )
        assert "schemaValidation" in result
        assert isinstance(result["schemaValidation"], dict)

    def t7():
        # AgenticExecutionEngine returns empty schemaValidation when no user_schema
        from backend.services.agentic_engine import agentic_execution_engine
        result = agentic_execution_engine.execute_agentic_workflow(
            file_bytes=b"Any document text",
            filename="test.txt",
            mime_type="text/plain"
        )
        assert result.get("schemaValidation") == {}

    def t8():
        # schemaValidation contains completeness_pct and quality_score
        from backend.services.agentic_engine import agentic_execution_engine
        schema = make_e2e_schema()
        result = agentic_execution_engine.execute_agentic_workflow(
            file_bytes=b"Invoice #INV-001 from Acme Corp. Amount: $500.00",
            filename="test.txt",
            mime_type="text/plain",
            user_schema=schema
        )
        sv = result["schemaValidation"]
        assert "completeness_pct" in sv
        assert "quality_score" in sv

    def t9():
        # Extracted fields in result are a subset of schema field keys when schema used
        from backend.services.agentic_engine import agentic_execution_engine
        schema = make_e2e_schema()
        result = agentic_execution_engine.execute_agentic_workflow(
            file_bytes=b"Invoice #INV-001 from Acme Corp. Amount: $500.00",
            filename="test.txt",
            mime_type="text/plain",
            user_schema=schema
        )
        schema_keys = {f.key for f in schema.fields}
        extracted_keys = set(result.get("extractedFields", {}).keys())
        assert extracted_keys.issubset(schema_keys), f"Unexpected keys: {extracted_keys - schema_keys}"

    def t10():
        # executionLogs includes schema_extraction_engine step
        from backend.services.agentic_engine import agentic_execution_engine
        schema = make_e2e_schema()
        result = agentic_execution_engine.execute_agentic_workflow(
            file_bytes=b"Invoice #INV-001 from Acme Corp. Amount: $500.00",
            filename="test.txt",
            mime_type="text/plain",
            user_schema=schema
        )
        agents_used = [log.get("agent_or_tool") for log in result.get("executionLogs", [])]
        assert "schema_extraction_engine" in agents_used, f"schema_extraction_engine not in logs: {agents_used}"

    for idx, fn in enumerate([t1, t2, t3, t4, t5, t6, t7, t8, t9, t10], 1):
        run(f"End-to-End [{idx:02d}]: {fn.__doc__ or fn.__name__}", fn)


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"{CYAN}  PHASE 4 -- Schema Intelligence Verification Suite{RESET}")
    print(f"{CYAN}  60 Scenarios Across 5 Sections{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")

    t0 = time.time()
    test_schema_models()
    test_schema_intelligence_engine()
    test_schema_store()
    test_schema_extraction_engine()
    test_end_to_end()
    elapsed = time.time() - t0

    # -- Summary --------------------------------------------------------------
    passes  = [r for r in RESULTS if r[1] == "PASS"]
    fails   = [r for r in RESULTS if r[1] == "FAIL"]
    errors  = [r for r in RESULTS if r[1] == "ERROR"]

    print(f"\n{CYAN}{'-'*60}{RESET}")
    print(f"  Total : {len(RESULTS):3d}")
    print(f"  {GREEN}Pass  : {len(passes):3d}{RESET}")
    if fails:
        print(f"  {RED}Fail  : {len(fails):3d}{RESET}")
        for n, _, e in fails:
            print(f"    {RED}x{RESET} {n}: {e}")
    if errors:
        print(f"  {YELLOW}Error : {len(errors):3d}{RESET}")
        for n, _, e in errors:
            print(f"    {YELLOW}!{RESET} {n}: {e}")
    print(f"  Time  : {elapsed:.1f}s")
    print(f"{CYAN}{'-'*60}{RESET}\n")

    exit_code = 0 if not fails and not errors else 1
    sys.exit(exit_code)
