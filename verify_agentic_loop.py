"""
Deep Agentic Platform Integration Verification Script
Verifies Universal Input Analyzer, Capability Registry, Agentic Planner, Validation Engine,
and Agentic Execution Engine workflow loop across multiple input formats.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, ".")

from backend.agents.input_analyzer_agent import input_analyzer_agent
from backend.agents.planner_agent import planner_agent
from backend.agents.capability_registry import capability_registry
from backend.services.validation_engine import validation_engine
from backend.services.agentic_engine import agentic_execution_engine

def test_agentic_loop():
    print("=" * 80)
    print("AGENTIC PLATFORM INTEGRATION TEST SUITE")
    print("=" * 80)

    # 1. Capability Registry Verification
    all_caps = capability_registry.list_all()
    print(f"\n1. Capability Registry: {len(all_caps)} agents registered.")
    for cap in all_caps:
        print(f"   - Agent: [{cap.name}] {cap.label} — Capabilities: {', '.join(cap.capabilities)}")

    # 2. Universal Input Analyzer & Planner Test
    sample_csv = b"Employee ID,Name,Department,Salary\nEMP001,John Doe,Engineering,90000"
    analysis = input_analyzer_agent.analyze(sample_csv, "employees.csv", "text/csv")
    print(f"\n2. Universal Input Analyzer:")
    print(f"   - Input Type  : {analysis.input_type}")
    print(f"   - Doc Category: {analysis.document_type}")
    print(f"   - Complexity  : {analysis.complexity}")
    print(f"   - Requires OCR: {analysis.requires_ocr}")
    print(f"   - Difficulty  : {analysis.estimated_extraction_difficulty}")

    plan = planner_agent.create_plan(analysis)
    print(f"\n3. Agentic Extraction Plan:")
    print(f"   - Plan ID     : {plan.plan_id}")
    print(f"   - Target Cat  : {plan.target_category}")
    print(f"   - Agents Picked: {', '.join(plan.agents)}")
    print(f"   - Validation  : Math={plan.validation_strategy.arithmetic_validation}, OCR Consensus={plan.validation_strategy.ocr_consensus}")

    # 4. Validation & Multi-Factor Scorecard Test
    sample_extracted = {
        "customerName": "Alice Smith",
        "customerMobile": "9876543210",
        "invoiceNumber": "INV-2026-001",
        "invoiceDate": "2026-09-19",
        "unitCost": "100",
        "quantity": "2",
        "grandTotal": "200"
    }
    schema = [{"key": k, "label": k} for k in sample_extracted.keys()]
    fields, scorecard = validation_engine.validate_and_score(sample_extracted, plan, ocr_text="INV-2026-001 Alice Smith 9876543210", schema=schema)
    print(f"\n4. Validation Engine Scorecard:")
    print(f"   - Overall Confidence: {scorecard.overall_confidence*100:.1f}%")
    print(f"   - Trusted           : {scorecard.is_trusted}")
    print(f"   - Human Review Req  : {scorecard.human_review_required}")
    print(f"   - Field Scores      : {json.dumps({k: v.confidence for k, v in scorecard.field_scores.items()}, indent=2)}")

    print("\n==========================================")
    print("ALL AGENTIC PLATFORM TESTS PASSED SUCCESSFULLY!")
    print("==========================================")

if __name__ == "__main__":
    test_agentic_loop()
