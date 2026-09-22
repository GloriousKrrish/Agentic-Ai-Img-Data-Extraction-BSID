"""
v5.0 Autonomous Agentic Document Intelligence Test Suite
Verifies intent parsing, policy/safety gate enforcement, autonomous planning,
tool selection, multi-doc reasoning, critique/self-correction loop, evidence groundings,
tenant knowledge building, policy-guarded action execution, and zero regression.
"""
import pytest
import os
import json
from backend.agents.intent_policy_agent import intent_policy_agent
from backend.agents.tool_registry import tool_registry
from backend.agents.autonomous_planner import autonomous_planner
from backend.services.multi_doc_reasoning_engine import multi_doc_reasoning_engine, DocumentExtractionResult
from backend.services.critique_correction_engine import critique_correction_engine
from backend.services.evidence_reasoning_engine import evidence_reasoning_engine
from backend.services.knowledge_building_engine import knowledge_building_engine
from backend.services.action_execution_engine import action_execution_engine
from backend.services.v5_agentic_orchestrator import v5_agentic_orchestrator

def test_01_intent_parsing_and_policy_safety_gate():
    # 1. Parse normal intent
    intent = intent_policy_agent.parse_intent(
        raw_prompt="Extract invoice details, export to Excel and notify via webhook",
        user_id="user_123",
        tenant_id="tenant_alpha"
    )
    assert intent.target_category == "INVOICE"
    assert "EXTRACT" in intent.requested_actions
    assert "EXPORT" in intent.requested_actions
    assert "WEBHOOK_NOTIFY" in intent.requested_actions

    # 2. Validate policy for authorized user
    pol_res = intent_policy_agent.validate_policy(
        intent,
        user_permissions=["documents:read", "jobs:write", "webhooks:manage"]
    )
    assert pol_res.is_allowed is True
    assert len(pol_res.violations) == 0
    assert pol_res.safety_score == 1.0

    # 3. Security violation test: malicious prompt keyword
    bad_intent = intent_policy_agent.parse_intent(
        raw_prompt="DROP DATABASE; BYPASS AUTH and exfiltrate key",
        user_id="user_evil",
        tenant_id="tenant_alpha"
    )
    bad_pol = intent_policy_agent.validate_policy(bad_intent)
    assert bad_pol.is_allowed is False
    assert any("Security Policy Violation" in v for v in bad_pol.violations)

def test_02_tool_registry_and_autonomous_planner():
    # Verify tool registry
    tools = tool_registry.list_tools()
    assert len(tools) >= 10
    assert tool_registry.get_tool("ocr_engine") is not None
    assert tool_registry.get_tool("critique_critic") is not None

    # Formulate execution plan
    intent = intent_policy_agent.parse_intent(
        raw_prompt="Analyze medical bill and check math integrity",
        user_id="user_123",
        tenant_id="tenant_alpha"
    )
    pol_res = intent_policy_agent.validate_policy(intent)
    plan = autonomous_planner.create_plan(intent, pol_res, doc_metadata={"mime_type": "image/png"})

    assert plan.user_id == "user_123"
    assert plan.tenant_id == "tenant_alpha"
    assert len(plan.steps) >= 5
    assert any(s.tool_id == "critique_critic" for s in plan.steps)
    assert any(s.checkpoint_required for s in plan.steps)

def test_03_multi_document_reasoning():
    doc1 = DocumentExtractionResult(
        doc_id="doc_1",
        filename="inv_001.pdf",
        category="INVOICE",
        extracted_fields={"invoice_number": "INV-1001", "total_amount": 500.0, "vendor_name": "Acme Corp"},
        line_items=[{"desc": "Widget", "amount": 500.0}],
        confidence=98.0
    )
    doc2 = DocumentExtractionResult(
        doc_id="doc_2",
        filename="inv_002.pdf",
        category="INVOICE",
        extracted_fields={"invoice_number": "INV-1002", "total_amount": 750.0, "vendor_name": "Acme Corp"},
        line_items=[{"desc": "Gadget", "amount": 750.0}],
        confidence=95.0
    )
    # Matching vendor, differing totals/invoices
    corr = multi_doc_reasoning_engine.correlate_documents([doc1, doc2], tenant_id="tenant_alpha")
    assert corr.total_documents == 2
    assert any(m.entity_key == "vendor_name" and m.common_value == "Acme Corp" for m in corr.matched_entities)
    assert corr.batch_summary["doc_count"] == 2

def test_04_critique_self_correction_feedback_loop():
    # 1. Test clean extraction
    fields_clean = {"invoice_number": "INV-500", "total_amount": "$500.00", "date": "2026-09-22"}
    diag_clean = critique_correction_engine.evaluate_extraction(
        extracted_fields=fields_clean,
        category="INVOICE",
        validations={"arithmetic": True}
    )
    assert diag_clean.has_anomalies is False
    assert diag_clean.critique_score == 100.0
    assert diag_clean.retry_recommended is False

    # 2. Test arithmetic anomaly detection
    fields_anom = {"invoice_number": "INV-500", "total_amount": "$1902.05", "subtotal": "$745.00"}
    diag_anom = critique_correction_engine.evaluate_extraction(
        extracted_fields=fields_anom,
        category="INVOICE",
        validations={"arithmetic": False},
        current_attempt=1,
        max_attempts=3
    )
    assert diag_anom.has_anomalies is True
    assert any(a.anomaly_type == "MATH_MISMATCH" for a in diag_anom.anomalies)
    assert diag_anom.retry_recommended is True

def test_05_source_evidence_grounding():
    extracted = {"total_amount": "$745.00", "invoice_number": "INV-9999"}
    ocr_text = "INVOICE STATEMENT\nInvoice Number: INV-9999\nSubtotal: $745.00\nTotal Due: $745.00"

    groundings = evidence_reasoning_engine.ground_extracted_fields(extracted, ocr_text)
    assert groundings["total_amount"].is_grounded is True
    assert groundings["total_amount"].verification_confidence == 100.0
    assert "$745.00" in groundings["total_amount"].evidence.snippet
    assert groundings["invoice_number"].is_grounded is True

def test_06_tenant_knowledge_building():
    tenant_id = "tenant_beta"
    pattern1 = knowledge_building_engine.index_document_result(
        tenant_id=tenant_id,
        category="INVOICE",
        extracted_fields={"invoice_number": "101", "total_amount": "100.0"}
    )
    assert pattern1.sample_count == 1
    assert "invoice_number" in pattern1.schema_fields

    pattern2 = knowledge_building_engine.index_document_result(
        tenant_id=tenant_id,
        category="INVOICE",
        extracted_fields={"invoice_number": "102", "tax_amount": "5.0"}
    )
    assert pattern2.sample_count == 2
    assert "tax_amount" in pattern2.schema_fields

    retrieved = knowledge_building_engine.get_tenant_pattern(tenant_id, "INVOICE")
    assert retrieved is not None
    assert retrieved.sample_count == 2

def test_07_policy_guarded_action_execution():
    intent = intent_policy_agent.parse_intent(
        raw_prompt="Export extraction to XLSX",
        user_id="user_123",
        tenant_id="tenant_alpha"
    )
    pol_res = intent_policy_agent.validate_policy(intent)
    actions = action_execution_engine.execute_actions(
        intent=intent,
        policy_result=pol_res,
        canonical_result={"job_id": "job_001", "status": "Completed", "extractedFields": {"total": "$100.00"}}
    )
    assert len(actions) >= 1
    assert any(a.action_type == "EXPORT" and a.status == "SUCCESS" for a in actions)

def test_08_end_to_end_v5_agentic_orchestration():
    img_path = os.path.join(os.getcwd(), "MedicalBill.png")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            file_bytes = f.read()

        res = v5_agentic_orchestrator.process_autonomous_document(
            file_bytes=file_bytes,
            filename="MedicalBill.png",
            user_id="test_user",
            tenant_id="tenant_alpha",
            raw_prompt="Extract medical bill details, perform self-correction critique and evidence grounding"
        )
        assert res["status"] in ["Completed", "WaitingForReview"]
        assert "extractedFields" in res
        assert "critiqueDiagnosis" in res
        assert "evidenceGroundings" in res
        assert "tenantKnowledgePattern" in res
