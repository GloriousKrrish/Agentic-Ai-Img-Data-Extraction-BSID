"""
v5.0 Central Agentic Document Intelligence Orchestrator
Connects intent parsing, policy gate, autonomous planner, extraction tools, critique critic,
evidence reasoning, multi-doc correlation, knowledge building, and action execution.
"""
import time
import uuid
from typing import Dict, Any, List, Optional

from backend.agents.intent_policy_agent import intent_policy_agent, UserIntent, PolicyValidationResult
from backend.agents.autonomous_planner import autonomous_planner, AutonomousExecutionPlan
from backend.services.agentic_engine import AgenticExecutionEngine
from backend.services.critique_correction_engine import critique_correction_engine, CritiqueDiagnosis
from backend.services.evidence_reasoning_engine import evidence_reasoning_engine
from backend.services.multi_doc_reasoning_engine import multi_doc_reasoning_engine, DocumentExtractionResult, CrossDocumentCorrelation
from backend.services.knowledge_building_engine import knowledge_building_engine
from backend.services.action_execution_engine import action_execution_engine, ActionResult

class V5AgenticOrchestrator:
    """
    Master v5.0 Orchestrator for Autonomous Document Intelligence.
    """

    def __init__(self):
        self.engine = AgenticExecutionEngine()

    def process_autonomous_document(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: str,
        tenant_id: str,
        raw_prompt: str = "Extract all fields accurately",
        mime_type: str = "image/png",
        user_permissions: Optional[List[str]] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes a document end-to-end through the complete v5.0 agentic pipeline.
        """
        # Stage 1: INTENT & POLICY GATE
        intent = intent_policy_agent.parse_intent(raw_prompt, user_id, tenant_id)
        policy_res = intent_policy_agent.validate_policy(intent, user_permissions=user_permissions)

        if not policy_res.is_allowed:
            return {
                "status": "Failed",
                "error_code": "SECURITY_POLICY_VIOLATION",
                "violations": policy_res.violations,
                "safety_score": policy_res.safety_score,
                "confidence": 0.0
            }

        # Stage 2: AUTONOMOUS PLANNER
        plan = autonomous_planner.create_plan(
            intent,
            policy_res,
            doc_metadata={"filename": filename, "mime_type": mime_type}
        )

        # Stage 3: EXECUTION (V4.2 Underlying Pipeline)
        exec_res = self.engine.execute_agentic_workflow(
            file_bytes=file_bytes,
            filename=filename,
            mime_type=mime_type,
            user_preset=intent.target_category
        )

        extracted_fields = exec_res.get("extractedFields", {}) or {}
        ocr_text = exec_res.get("text_content", "") or ""

        # Stage 4: CRITIQUE & SELF-CORRECTION LOOP
        critique_diag: CritiqueDiagnosis = critique_correction_engine.evaluate_extraction(
            extracted_fields=extracted_fields,
            category=exec_res.get("documentCategory", intent.target_category),
            ocr_text=ocr_text,
            current_attempt=1,
            max_attempts=plan.max_critique_attempts
        )

        # Stage 5: SOURCE EVIDENCE GROUNDING
        field_evidences = evidence_reasoning_engine.ground_extracted_fields(
            extracted_fields=extracted_fields,
            ocr_text=ocr_text
        )

        # Stage 6: TENANT KNOWLEDGE BUILDING
        knowledge_pattern = knowledge_building_engine.index_document_result(
            tenant_id=tenant_id,
            category=exec_res.get("documentCategory", "GENERAL"),
            extracted_fields=extracted_fields
        )

        # Stage 7: POST-EXTRACTION ACTION EXECUTION
        action_results: List[ActionResult] = action_execution_engine.execute_actions(
            intent=intent,
            policy_result=policy_res,
            canonical_result=exec_res,
            webhook_url=webhook_url
        )

        # Final Canonical Status Determination
        final_status = exec_res.get("status", "Completed")
        if critique_diag.has_anomalies and any(a.severity == "CRITICAL" for a in critique_diag.anomalies):
            final_status = "WaitingForReview"

        return {
            "intent_id": intent.intent_id,
            "plan_id": plan.plan_id,
            "status": final_status,
            "confidence": exec_res.get("confidence", 95.0),
            "documentCategory": exec_res.get("documentCategory", intent.target_category),
            "extractedFields": extracted_fields,
            "tableResult": exec_res.get("tableResult"),
            "critiqueDiagnosis": {
                "diagnosis_id": critique_diag.diagnosis_id,
                "has_anomalies": critique_diag.has_anomalies,
                "anomalies": [
                    {
                        "field": a.field_name,
                        "type": a.anomaly_type,
                        "severity": a.severity,
                        "description": a.description
                    } for a in critique_diag.anomalies
                ],
                "critique_score": critique_diag.critique_score,
                "retry_recommended": critique_diag.retry_recommended
            },
            "evidenceGroundings": {
                k: {
                    "extracted_value": v.extracted_value,
                    "verification_confidence": v.verification_confidence,
                    "is_grounded": v.is_grounded,
                    "snippet": v.evidence.snippet if v.evidence else ""
                } for k, v in field_evidences.items()
            },
            "tenantKnowledgePattern": {
                "pattern_id": knowledge_pattern.pattern_id,
                "tenant_id": knowledge_pattern.tenant_id,
                "category": knowledge_pattern.category,
                "schema_fields": knowledge_pattern.schema_fields,
                "sample_count": knowledge_pattern.sample_count
            },
            "actionResults": [
                {
                    "action_id": a.action_id,
                    "action_type": a.action_type,
                    "status": a.status,
                    "target": a.target,
                    "payload_summary": a.payload_summary
                } for a in action_results
            ],
            "executionLogs": exec_res.get("executionLogs", [])
        }

v5_agentic_orchestrator = V5AgenticOrchestrator()
